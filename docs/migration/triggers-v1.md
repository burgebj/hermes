# Migration Guide — Unified Skill Trigger Framework v1

## TL;DR

Existing skills require **no changes**. The new `metadata.hermes.triggers`
field is opt-in; absent triggers preserve all pre-framework behavior on
every adapter. Adopt it incrementally, one skill at a time, when you want
that skill to receive reactions, mentions, or platform-specific events.

## What changed

Hermes now ships an **adapter-agnostic skill event resolver**
(`gateway/skill_resolver.py`) plus a **Discord interactions handler**
(`gateway/platforms/discord_interactions.py`). Together they route inbound
gateway events (reactions, mentions, slash commands, and — via a future
bridge to PR #19413's components — buttons) to skills whose frontmatter
declares matching triggers.

Two LLM-callable outbound tools complete the loop so skills can emit
the same reaction surfaces they receive:

- `discord_add_reaction` — bot pre-attaches an emoji on a message,
  enabling 1-tap UX where users complete an action with a single
  reaction click.
- `discord_remove_reaction` — bot removes its own reaction for cleanup
  (e.g., when a recommendation expires).

Discord button emission + interaction dispatch is intentionally scoped
out: PR #19413 (interactive components — buttons, select menus, REST +
WebSocket paths) provides that layer. The framework retains `button` as
a first-class trigger type in the schema and resolver so a follow-up
bridge PR can plug PR #19413's component dispatch into
`resolve_event_skills('button', payload, skills)`.

This is purely an extension. The existing prompt-builder skill injection
path, slash command registration, and message handling pipelines are all
unchanged. Skills not using the new schema behave exactly as they did
before this PR.

## Schema (Schema α — type-keyed dict)

```yaml
metadata:
  hermes:
    triggers:
      mention:
        regex: "approve\\s+\\d+"
        channel_filter: ["bot-commands"]   # optional
      slash:
        name: "approve"
      button:
        custom_id_pattern: "skill_approve_*"
      reaction:
        emoji: "✅"
        channel_filter: ["bot-commands"]   # optional
        age_limit: "14d"                    # optional, units: s/m/h/d/w
      cron:
        schedule: "0 9 * * *"
```

Each trigger type lives at a separate top-level key under `triggers:`. A
single skill can declare any combination. Unknown trigger types are
silently skipped — adding new types in future PRs will not break existing
skills.

**Note on schema shape**: this PR ships Schema α (type-keyed dict). Two
alternatives — Schema β (list of typed objects) and Schema γ (hybrid dict
with array values) — were considered and documented in the spec at
`/Users/arkstar/Projects/.omc/specs/deep-interview-hermes-discord-interactions-rfc.md`
section "Schema Design Strategy". α was picked as the default because it
is the most readable; if reviewers prefer β or γ, the parser at
`agent/skill_utils.extract_skill_triggers` is the only place to update —
the resolver and adapter wiring are schema-shape agnostic.

## Discord — opt-in inbound reactions

Inbound Discord reaction events (`MESSAGE_REACTION_ADD`,
`MESSAGE_REACTION_REMOVE`) are **disabled by default** to avoid forcing
existing deployments to re-handshake with the Discord gateway (enabling the
`reactions` intent changes the bot's connection).

To enable, set in your gateway YAML:

```yaml
gateway:
  platforms:
    discord:
      reactions:
        inbound_routing: true
```

Or via env override (where supported by your config layer). The flag is
read **once at adapter init**; toggling it at runtime requires a bot
restart for the new event handlers to bind.

When the flag is true, the bot enables `intents.reactions = True`, registers
`on_raw_reaction_add` / `on_raw_reaction_remove` handlers, and routes the
events through the resolver. When false (the default), nothing changes —
inbound reactions are not delivered to skills.

## Discord — buttons (deferred to PR #19413)

Discord button emission, REST/WebSocket interaction handling, and select-
menu support are provided by **PR #19413 (interactive components)**, not
this PR. The trigger framework retains a `button` schema entry so a future
bridge PR can route PR #19413's component interactions back to skills via
`resolve_event_skills('button', payload, skills)` — for example, by
matching component custom_ids against `metadata.hermes.triggers.button.custom_id_pattern`.

Skills can declare button trigger patterns today; the resolver will match
them as soon as the bridge lands:

```yaml
metadata:
  hermes:
    triggers:
      button:
        custom_id_pattern: "skill_approver_*"
```

The `make_skill_custom_id` and `is_skill_custom_id` helpers in
`gateway/platforms/discord_interactions.py` remain as the bridge's hook
points (canonical `skill_<name>_<action>` shape).

### LLM-callable reaction emit — `discord_add_reaction` / `discord_remove_reaction` tools

The framework already routes inbound Discord reaction events to skills
that declare `triggers.reaction` (see *Discord — opt-in inbound reactions*
above). Two companion outbound tools close the asymmetry so skills can
emit reactions of their own — most usefully, a bot pre-attaches `✅` to
its freshly-sent message so the user can complete an action with a single
tap on the existing reaction:

```json
{
  "name": "discord_add_reaction",
  "arguments": {
    "channel_id": "1496609306995458048",
    "message_id": "1497123456789012345",
    "emoji": "✅"
  }
}
```

Returns:

```json
{
  "message_id": "1497123456789012345",
  "channel_id": "1496609306995458048",
  "emoji": "✅"
}
```

`discord_remove_reaction` has the same signature and removes the **bot's
own** reaction (the tool passes `client.user` to discord.py's
`message.remove_reaction`); it is not a generic admin operation and
cannot remove other users' reactions. Use it for cleanup when a
recommendation expires or an action is reversed.

```json
{
  "name": "discord_remove_reaction",
  "arguments": {
    "channel_id": "1496609306995458048",
    "message_id": "1497123456789012345",
    "emoji": "✅"
  }
}
```

**1-tap UX pattern.** After a skill sends a message — via plain
`channel.send` or the cross-platform `send_message` tool from the
`messaging` toolset — call `discord_add_reaction` with the returned
`message_id` to pre-attach the affordance. When the user clicks it, the
inbound reaction routing dispatches the same skill via
`triggers.reaction.emoji`, closing the loop.

**Add+remove timing.** discord.py processes reaction add/remove on the
gateway WebSocket; calling `discord_remove_reaction` within milliseconds
of `discord_add_reaction` may surface a `NotFound` because the add has
not yet propagated to Discord. The tool wraps the error structurally
(returns `{"error": ...}` JSON, never raises), so callers can retry
or accept the no-op — design rapid-toggle flows expecting that case
rather than relying on strict ordering.

## Feishu — backward-compatibility fallback

Feishu's existing reaction routing built a synthetic text event of the form
`reaction:<add|remove>:<emoji>` and broadcast it to all loaded skills. The
unified framework introduces explicit per-skill matching but **preserves
the broadcast fallback** for corpora that have not opted into the new
schema:

| Corpus state | Resolver outcome | Routing |
|---|---|---|
| ≥1 skill matches | non-empty | dispatch with `auto_skill=<matched>` (NEW behavior) |
| no match, no skill in corpus has explicit `triggers:` | empty | broadcast (LEGACY behavior preserved) |
| no match, ≥1 skill has explicit `triggers:` | empty | skip (opt-in semantics: corpus declared what it wants) |

So an existing Feishu deployment with no explicit triggers anywhere will
continue to broadcast every `reaction:` synthetic event exactly as before.
You opt **into** strict routing skill-by-skill by adding `triggers:` to
the skills that should receive it.

The Feishu adapter's existing filters (`_FEISHU_ACK_EMOJI` skip,
`bot/app sender_type` filter) run upstream of the resolver and are
unchanged.

## Example skills (current corpus)

The current Hermes skill corpus does NOT use the new schema yet. A few
representative skills that could opt in:

- **`skills/research/llm-wiki/`** — currently has no derivable triggers
  (no `slash_command:` field, no `triggers:` field). To opt in, add an
  explicit `triggers:` block — e.g., a button or reaction trigger.
- **`skills/github/github-issues/`** — same as above. Could opt in with a
  `mention.regex` trigger to handle "@bot create issue ..." patterns.

These illustrate the **opt-in** nature of the schema: existing skills do
not auto-derive triggers from their frontmatter. The migration path is
"add explicit `triggers:` when you want the skill to receive events" —
nothing happens until you do.

## Backward compatibility summary

- **Existing skills**: no changes required. All behavior preserved.
- **Existing Discord deployments**: no changes required. Inbound reactions
  remain off by default. Outbound reactions (👀 / ✅ / ❌ processing
  feedback) are unchanged.
- **Existing Feishu deployments**: no changes required. Reaction broadcast
  preserved when no skill in the corpus uses the new schema.
- **Existing slash commands**: unchanged. The 24 hardcoded gateway slash
  commands (`/new`, `/reset`, `/model`, etc.) are not user-skill-derivable
  and are not affected by `triggers:`.
- **Existing prompt-builder injection**: unchanged. Skills continue to be
  injected into the system prompt regardless of whether they declare
  triggers.

## Resolver implementation reference

- `gateway/skill_resolver.py` — adapter-agnostic resolver:
  - `resolve_event_skills(event_type, payload, skills) -> List[str]`
  - `has_explicit_triggers(skills) -> bool`
  - `snapshot_skills() -> List[SkillEntry]` — lazy walker shared across
    Discord and Feishu adapter wrappers.
- `gateway/platforms/discord_interactions.py` — Discord composition handler:
  - `DiscordInteractionsHandler` — receives inbound reactions + mentions
  - `make_skill_custom_id(name, action)` / `is_skill_custom_id(custom_id)` —
    canonical custom_id helpers retained as bridge hook points for a future
    PR connecting #19413's component dispatch to this resolver
- `agent/skill_utils.py` — frontmatter parser:
  - `extract_skill_triggers(frontmatter)` — explicit triggers
  - `derive_implicit_triggers(frontmatter)` — slash from `slash_command` field
  - `get_skill_triggers(frontmatter)` — combined accessor

## Testing

Test files for this PR:

- `tests/agent/test_skill_utils_triggers.py` — parser + derivation (button schema preserved)
- `tests/gateway/test_skill_resolver.py` — resolver (all event types including button matcher)
- `tests/gateway/test_discord_interactions.py` — handler unit tests (custom_id helpers + reactions + mentions)
- `tests/gateway/test_discord_inbound_reactions.py` — reaction integration
- `tests/gateway/test_feishu_reactions_bc.py` — Feishu BC fork
- `tests/tools/test_discord_reaction_tool.py` — outbound reaction tools

All pass under both `pytest -n auto` (parallel) and `pytest -n 0` (serial).
The existing Discord adapter test files continue to pass without
modification.

## Future work (not in this PR)

- **Button bridge to PR #19413**: PR #19413 (interactive components) lands
  the Discord button + select-menu emission and REST/WebSocket interaction
  handling. A follow-up PR can connect #19413's component dispatch to this
  framework by calling `resolve_event_skills('button', payload, skills)`
  with the interaction's `custom_id`, completing the round-trip from skill
  declaration → component emission → click → skill dispatch.
- **Matrix uplift**: `gateway/platforms/matrix.py:1528` `_on_reaction` is
  currently stub-only (logs reactions, no skill routing). Refactoring to
  use the unified resolver is mechanically identical to the Feishu uplift
  in this PR. Deferred to keep the diff focused; the resolver is ready.
- **Slack components**: Slack's Block Kit interactive components could route
  through the same resolver with a Slack-side handler companion file.
- **Cron registrar**: cron triggers are recognized by the parser but not
  yet wired through the resolver — cron firings are dispatched by the
  cron registrar with the skill already resolved. The schema is forward-
  compatible.
