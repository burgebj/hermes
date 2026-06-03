---
sidebar_position: 12
sidebar_label: "Built-in Plugins"
title: "Built-in Plugins"
description: "Plugins shipped with Hermes Agent that run automatically via lifecycle hooks — disk-cleanup and friends"
---

# Built-in Plugins

Hermes ships a small set of plugins bundled with the repository. They live under `<repo>/plugins/<name>/` and load automatically alongside user-installed plugins in `~/.hermes/plugins/`. They use the same plugin surface as third-party plugins — hooks, tools, slash commands — just maintained in-tree.

See the [Plugins](/user-guide/features/plugins) page for the general plugin system, and [Build a Hermes Plugin](/guides/build-a-hermes-plugin) to write your own.

## How discovery works

The `PluginManager` scans four sources, in order:

1. **Bundled** — `<repo>/plugins/<name>/` (what this page documents)
2. **User** — `~/.hermes/plugins/<name>/`
3. **Project** — `./.hermes/plugins/<name>/` (requires `HERMES_ENABLE_PROJECT_PLUGINS=1`)
4. **Pip entry points** — `hermes_agent.plugins`

On name collision, later sources win — a user plugin named `disk-cleanup` would replace the bundled one.

`plugins/memory/` and `plugins/context_engine/` are deliberately excluded from bundled scanning. Those directories use their own discovery paths because memory providers and context engines are single-select providers configured through `hermes memory setup` / `context.engine` in config.

## Bundled plugins are opt-in

Bundled plugins ship disabled. Discovery finds them (they appear in `hermes plugins list` and the interactive `hermes plugins` UI), but none load until you explicitly enable them:

```bash
hermes plugins enable disk-cleanup
```

Or via `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - disk-cleanup
```

This is the same mechanism user-installed plugins use. Bundled plugins are never auto-enabled — not on fresh install, not for existing users upgrading to a newer Hermes. You always opt in explicitly.

To turn a bundled plugin off again:

```bash
hermes plugins disable disk-cleanup
# or: remove it from plugins.enabled in config.yaml
```

## Currently shipped

The repo ships these bundled plugins under `plugins/`. General plugins are opt-in — enable them via `hermes plugins enable <name>`. `SIMPLICIO_PROMPT` also supports a one-boolean activation path (`SIMPLICIO_PROMPT=true` or `simplicio_prompt.enabled: true`) because it is inert until that flag is set.

| Plugin | Kind | Purpose |
|---|---|---|
| `disk-cleanup` | hooks + slash command | Auto-track ephemeral files and clean them on session end |
| `security-guidance` | hooks | Pattern-match dangerous code on `write_file`/`patch` and append a security warning (or block) — 25 rules (Apache-2.0 fork of Anthropic's `claude-plugins-official` patterns) |
| `observability/langfuse` | hooks | Trace turns / LLM calls / tools to [Langfuse](https://langfuse.com) |
| `spotify` | backend (7 tools) | Native Spotify playback, queue, search, playlists, albums, library |
| `google_meet` | standalone | Join Meet calls, live-caption transcription, optional realtime duplex audio |
| `SIMPLICIO_PROMPT` | hook overlay | Inject the SIMPLICIO_PROMPT V2 tuple-space policy into every main-agent turn when enabled |
| `image_gen/openai` | image backend | OpenAI `gpt-image-2` image generation backend (alternative to FAL) |
| `image_gen/openai-codex` | image backend | OpenAI image generation via Codex OAuth |
| `image_gen/xai` | image backend | xAI `grok-2-image` backend |
| `hermes-achievements` | dashboard tab | Steam-style collectible badges generated from your real Hermes session history |
| `kanban/dashboard` | dashboard tab | Kanban board UI for the multi-agent dispatcher — tasks, comments, fan-out, board switching. See [Kanban Multi-Agent](./kanban.md). |

Memory providers (`plugins/memory/*`) and context engines (`plugins/context_engine/*`) are listed separately on [Memory Providers](./memory-providers.md) — they're managed through `hermes memory` and `hermes plugins` respectively. The full per-plugin detail for the two long-running hooks-based plugins follows.

### disk-cleanup

Auto-tracks and removes ephemeral files created during sessions — test scripts, temp outputs, cron logs, stale chrome profiles — without requiring the agent to remember to call a tool.

**How it works:**

| Hook | Behaviour |
|---|---|
| `post_tool_call` | When `write_file` / `terminal` / `patch` creates a file matching `test_*`, `tmp_*`, or `*.test.*` inside `HERMES_HOME` or `/tmp/hermes-*`, track it silently as `test` / `temp` / `cron-output`. |
| `on_session_end` | If any test files were auto-tracked during the turn, run the safe `quick` cleanup and log a one-line summary. Stays silent otherwise. |

**Deletion rules:**

| Category | Threshold | Confirmation |
|---|---|---|
| `test` | every session end | Never |
| `temp` | >7 days since tracked | Never |
| `cron-output` | >14 days since tracked | Never |
| empty dirs under HERMES_HOME | always | Never |
| `research` | >30 days, beyond 10 newest | Always (deep only) |
| `chrome-profile` | >14 days since tracked | Always (deep only) |
| files >500 MB | never auto | Always (deep only) |

**Slash command** — `/disk-cleanup` available in both CLI and gateway sessions:

```
/disk-cleanup status                     # breakdown + top-10 largest
/disk-cleanup dry-run                    # preview without deleting
/disk-cleanup quick                      # run safe cleanup now
/disk-cleanup deep                       # quick + list items needing confirmation
/disk-cleanup track <path> <category>    # manual tracking
/disk-cleanup forget <path>              # stop tracking (does not delete)
```

**State** — everything lives at `$HERMES_HOME/disk-cleanup/`:

| File | Contents |
|---|---|
| `tracked.json` | Tracked paths with category, size, and timestamp |
| `tracked.json.bak` | Atomic-write backup of the above |
| `cleanup.log` | Append-only audit trail of every track / skip / reject / delete |

**Safety** — cleanup only ever touches paths under `HERMES_HOME` or `/tmp/hermes-*`. Windows mounts (`/mnt/c/...`) are rejected. Well-known top-level state dirs (`logs/`, `memories/`, `sessions/`, `cron/`, `cache/`, `skills/`, `plugins/`, `disk-cleanup/` itself) are never removed even when empty — a fresh install does not get gutted on first session end.

**Enabling:** `hermes plugins enable disk-cleanup` (or check the box in `hermes plugins`).

**Disabling again:** `hermes plugins disable disk-cleanup`.

### security-guidance

Fast pattern-matched security warnings on file writes. When the agent's `write_file` / `patch` / `skill_manage` calls carry content matching a known-dangerous code pattern — `pickle.load`, `yaml.load` without `SafeLoader`, `eval(`, `os.system`, `subprocess(...,  shell=True)`, JS `child_process.exec`, React `dangerouslySetInnerHTML`, raw `.innerHTML =` / `.outerHTML =` / `document.write`, Node `crypto.createCipher`, AES ECB mode, TLS verification disabled, XXE-prone `xml.etree` / `minidom` parsers, `<script src="//..." >` without SRI, `torch.load` without `weights_only=True`, GitHub Actions `${{ github.event.* }}` injection — the plugin appends a `⚠️ Security guidance` block to the tool's result.

The file is still written. The model reads the warning in the next turn's tool message and can either fix the code or document why the construct is safe in this context. Pattern matching has a non-trivial false-positive rate, which is why warn (not block) is the default.

**Coverage:** 25 rules total, covering unsafe deserialization, command injection, XSS sinks, crypto footguns, XXE, supply-chain (SRI), and CI/CD workflow injection. The pattern data is a verbatim Apache-2.0 fork of [Anthropic's `claude-plugins-official`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance/hooks) — see the plugin's `LICENSE` and `NOTICE` files for attribution.

**Modes:**

| Env var | Effect |
|---|---|
| (unset) | **warn mode** (default) — file is written, warning appended to result |
| `SECURITY_GUIDANCE_BLOCK=1` | **block mode** — write refused, warning returned as the block reason |
| `SECURITY_GUIDANCE_DISABLE=1` | kill switch — plugin loads but does nothing |

**Enabling:** `hermes plugins enable security-guidance` (or check the box in `hermes plugins`).

**Disabling again:** `hermes plugins disable security-guidance`.

**What it does not do (yet):** the upstream Anthropic plugin has two more layers — an LLM diff review on each agent turn that touched files, and an agentic commit-time review that traces data flow across files. Neither is ported. The agent can already run those reviews on demand via `delegate_task`.

### observability/langfuse

Traces Hermes turns, LLM calls, and tool invocations to [Langfuse](https://langfuse.com) — an open-source LLM observability platform. One span per turn, one generation per API call, one tool observation per tool call. Usage totals, per-type token counts, and cost estimates come out of Hermes' canonical `agent.usage_pricing` numbers, so the Langfuse dashboard sees the same breakdown (input / output / `cache_read_input_tokens` / `cache_creation_input_tokens` / `reasoning_tokens`) that appears in `hermes logs`.

The plugin is fail-open: no SDK installed, no credentials, or a transient Langfuse error — all turn into a silent no-op in the hook. The agent loop is never impacted.

**Setup (interactive — recommended):**

```bash
hermes tools          # → Langfuse Observability → Cloud or Self-Hosted
```

The wizard collects your keys, `pip install`s the `langfuse` SDK, and adds `observability/langfuse` to `plugins.enabled` for you. Restart Hermes and the next turn ships a trace.

**Setup (manual):**

```bash
pip install langfuse
hermes plugins enable observability/langfuse
```

Then put the credentials in `~/.hermes/.env`:

```bash
HERMES_LANGFUSE_PUBLIC_KEY=pk-lf-...
HERMES_LANGFUSE_SECRET_KEY=sk-lf-...
HERMES_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

**How it works:**

| Hook | Behaviour |
|---|---|
| `pre_api_request` / `pre_llm_call` | Open (or reuse) a per-turn root span "Hermes turn". Start a `generation` child observation for this API call with serialized recent messages as input. |
| `post_api_request` / `post_llm_call` | Close the generation, attach `usage_details`, `cost_details`, `finish_reason`, assistant output + tool calls. If no tool calls and non-empty content, close the turn. |
| `pre_tool_call` | Start a `tool` child observation with sanitized `args`. |
| `post_tool_call` | Close the tool observation with sanitized `result`. `read_file` payloads get summarized (head + tail + omitted-line count) so a huge file read stays under `HERMES_LANGFUSE_MAX_CHARS`. |

Session grouping keys off the Hermes session ID (or task ID for sub-agents) via `langfuse.propagate_attributes`, so everything in a single `hermes chat` session lives under one Langfuse session.

**Verify:**

```bash
hermes plugins list                 # observability/langfuse should show "enabled"
hermes chat -q "hello"              # check the Langfuse UI for a "Hermes turn" trace
```

**Optional tuning** (in `.env`):

| Variable | Default | Purpose |
|---|---|---|
| `HERMES_LANGFUSE_ENV` | — | Environment tag on traces (`production`, `staging`, …) |
| `HERMES_LANGFUSE_RELEASE` | — | Release/version tag |
| `HERMES_LANGFUSE_SAMPLE_RATE` | `1.0` | Sampling rate passed to the SDK (0.0–1.0) |
| `HERMES_LANGFUSE_MAX_CHARS` | `12000` | Per-field truncation for message content / tool args / tool results |
| `HERMES_LANGFUSE_DEBUG` | `false` | Verbose plugin logging to `agent.log` |

Hermes-prefixed and standard SDK env vars (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`) are both accepted — Hermes-prefixed wins when both are set.

**Performance:** the Langfuse client is cached after the first hook call. If credentials or SDK are missing, that decision is also cached — subsequent hooks fast-return without re-checking env vars or reloading config.

**Disabling:** `hermes plugins disable observability/langfuse`. The plugin module is still discovered, but no module code runs until you re-enable.

### SIMPLICIO_PROMPT

Injects a SIMPLICIO_PROMPT V2 execution overlay into every main-agent turn
through `pre_llm_call`. It applies to any prompt or message, not only
implementation requests: questions, commands, code snippets, layout edits,
refactors, documentation work, and normal chat all get the overlay when enabled.
The user does not need to type "Implement"; Hermes adds the tuple-space policy
before the model call as ephemeral context loaded from the bundled local runtime
snapshot.

![YOOL V2 Safe-Speed Runtime reference infographic](/img/simplicio-prompt/yool-v2-safe-speed-infographic-en.png)

Bundled runtime snapshot:
`plugins/simplicio_prompt/vendor/simplicio_prompt/`.
Hermes does not fetch or consult an external GitHub repository to apply the
prompt. Here, V2 refers to the bundled SIMPLICIO_PROMPT runtime snapshot;
benchmark comparisons are against normal/V1 baselines.

**Enable with one boolean:**

```bash
SIMPLICIO_PROMPT=true hermes chat
```

Or in `~/.hermes/config.yaml`:

```yaml
simplicio_prompt:
  enabled: true
```

You can also opt in through the standard plugin allow-list:

```bash
hermes plugins enable SIMPLICIO_PROMPT
```

**What it does:**

| SIMPLICIO_PROMPT V2 item | Behaviour in Hermes |
|---|---|
| Automatic pass-through | Every enabled main-agent turn receives the overlay before the model call; any prompt/message is eligible and no trigger word such as "Implement", "Fix", or "Build" is required. |
| Local vendored runtime | The plugin ships the prompt, spec, reference kernel, guardrails, examples, benchmarks, PDFs, and assets under `plugins/simplicio_prompt/vendor/simplicio_prompt/`. |
| Tuple-space decomposition | Work is framed as root tuple plus Hilbert/HAMT graph, lanes, authority, receipts, and source pointers. |
| Massive-agent abstraction | `batch_spawn(depth, branching, compression_threshold)` is represented as a summarized hierarchy for 1,000,000+ subagents without enumerating them. |
| Safer speed | The model is steered toward local deterministic work first, input-hash caching, batching, context compression, stable prefixes, adaptive lanes, jittered backoff, circuit breakers, and idempotent-only speculation. |
| Rate-limit safety | The overlay explicitly preserves provider limits and terms; it is not a bypass. |
| Stable report shape | The default output contract includes tuple-space snapshot, active agents, total agents, next yool, and partial result. |

**Bundled SIMPLICIO_PROMPT V2 report highlights (vs normal/V1):**

| Area | Reported SIMPLICIO_PROMPT V2 result vs normal/V1 |
|---|---:|
| Scale representation | `2,833.75x` faster than normal/V1 instruction flow |
| Active execution | `26.93x` faster than normal/V1 sequential execution |
| Receipt/input cache | `4x` fewer provider calls, a `75%` reduction |
| Small-task batching | `32x` fewer small-task calls, a `96.88%` reduction |
| Circuit breaker | `64x` fewer failure attempts, a `98.44%` reduction |
| Token economy | `76.32%` estimated savings through context compression |

The plugin carries these as reference policy data from the bundled
SIMPLICIO_PROMPT V2 runtime. It does not bypass hosted-provider rate limits,
quotas, latency, or terms.

**Activation semantics:** `SIMPLICIO_PROMPT` is gated only by Hermes config or
environment flags, not by message text. After the plugin is enabled, every
prompt or message receives the same overlay automatically through
`pre_llm_call`: normal chat, questions, commands, code snippets, single-word
requests, layout edits, refactors, bug fixes, documentation tasks, benchmarks,
and implementation requests.

**Performance note:** the plugin is local-only. When disabled it is a no-op.
When enabled, it injects a cached context loaded from the bundled runtime
snapshot; it does not make extra model calls or GitHub fetches. See
`docs/simplicio-prompt-v2-benchmark.md` and run
`python scripts/benchmark_simplicio_prompt.py` for the local token and
preprocessing benchmark.

### google_meet

Lets the agent **join, transcribe, and participate in Google Meet calls** — take notes on a meeting, summarize the back-and-forth after, follow up on specific points, and (optionally) speak replies back into the call via TTS.

**What it adds:**

- A headless virtual participant that joins a Meet URL using browser automation
- Live transcription of the meeting audio via the configured STT provider
- A `meet_summarize` / `meet_speak` / `meet_followup` toolset the agent invokes to act on what it heard
- Post-meeting artifacts (transcript, speaker-attributed notes, action items) saved under `~/.hermes/cache/google_meet/<meeting_id>/`

**Setup:**

```bash
hermes plugins enable google_meet
# Prompts you to sign in via the plugin's OAuth flow on first use —
# needs a Google account with Meet access. Host approval may be required
# if the meeting enforces "only invited participants can join".
```

Usage from chat:

> "Join meet.google.com/abc-defg-hij and take notes. After the call, send me a summary with action items."

The agent kicks off the meeting join, streams the transcription back into its context as the call proceeds, and produces a structured summary when the meeting ends (or when you tell it to stop).

**When to use it:** recurring standups where you want a bot to transcribe + summarize for async attendees; deposition-style interviews where you want structured notes; any case where you'd otherwise need Fireflies / Otter / Grain. When you'd rather not have an AI listening in — don't enable it.

**Disabling:** `hermes plugins disable google_meet`. Any cached transcripts and recordings stay in `~/.hermes/cache/google_meet/` until you remove them.

### hermes-achievements

Adds a **Steam-style achievements tab to the dashboard** — 60+ collectible, tiered badges generated from your real Hermes session history. Tool-chain feats, debugging patterns, vibe-coding streaks, skill/memory usage, model/provider variety, lifestyle quirks (weekend and night sessions). Originally authored by [@PCinkusz](https://github.com/PCinkusz) as an external plugin; brought in-tree so it stays in lockstep with Hermes feature changes.

**How it works:**

- Scans your entire `~/.hermes/state.db` session history on the dashboard backend
- Per-session stats are cached by `(started_at, last_active)` fingerprint, so only new or changed sessions re-analyze on subsequent scans
- First-ever scan runs in a background thread — the dashboard never blocks waiting for it, even on databases with thousands of sessions
- Unlock state is persisted to `$HERMES_HOME/plugins/hermes-achievements/state.json`

**Tier progression:** Copper → Silver → Gold → Diamond → Olympian. Each card exposes a "What counts" section listing the exact metric being tracked.

**Achievement states:**

| State | Meaning |
|---|---|
| Unlocked | At least one tier achieved |
| Discovered | Known achievement, progress visible, not yet earned |
| Secret | Hidden until Hermes detects the first related signal in your history |

**API** — routes mount under `/api/plugins/hermes-achievements/`:

| Endpoint | Purpose |
|---|---|
| `GET /achievements` | Full catalog with per-badge unlock state (returns a pending placeholder while the first cold scan is running) |
| `GET /scan-status` | State of the background scanner: `idle` / `running` / `failed`, last duration, run count |
| `GET /recent-unlocks` | Twenty most recently unlocked badges, newest first |
| `GET /sessions/{id}/badges` | Badges earned primarily in one specific session |
| `POST /rescan` | Manual synchronous rescan (blocks; use when the user clicks the rescan button) |
| `POST /reset-state` | Clear unlock history and cached snapshot |

**State files** — live under `$HERMES_HOME/plugins/hermes-achievements/`:

| File | Contents |
|---|---|
| `state.json` | Unlock history: which badges you've earned and when. Stable across Hermes updates. |
| `scan_snapshot.json` | Last completed scan payload (served immediately on dashboard load) |
| `scan_checkpoint.json` | Per-session stats cache keyed by fingerprint (makes warm rescans fast) |

**Performance notes:**

- Cold scan on ~8,000 sessions takes a few minutes. It runs in a background thread on first dashboard request; the UI sees a pending placeholder and polls `/scan-status`.
- **Incremental results during a cold scan** — the scanner publishes a partial snapshot every ~250 sessions so each dashboard refresh shows more badges unlocked as the scan progresses. No minute-long stare at zeros.
- Warm rescan reuses per-session stats for every session whose `started_at` + `last_active` fingerprint matches the checkpoint — completes in seconds even on large histories.
- The in-memory snapshot TTL is 120s; stale requests serve the old snapshot immediately and kick a background refresh. You never wait on a spinner just because TTL expired.

**Enabling:** Nothing to enable — `hermes-achievements` is a dashboard-only plugin (no lifecycle hooks, no model-visible tools). It auto-registers as a tab in `hermes dashboard` on first launch. The `plugins.enabled` config only gates lifecycle/tool plugins; dashboard plugins are discovered purely via their `dashboard/manifest.json`.

**Opting out:** Delete or rename `plugins/hermes-achievements/dashboard/manifest.json`, or override it with a user plugin of the same name in `~/.hermes/plugins/hermes-achievements/` that ships no dashboard. The plugin's state files under `$HERMES_HOME/plugins/hermes-achievements/` survive — reinstalling preserves your unlock history.

## Adding a bundled plugin

Bundled plugins are written exactly like any other Hermes plugin — see [Build a Hermes Plugin](/guides/build-a-hermes-plugin). The only differences are:

- Directory lives at `<repo>/plugins/<name>/` instead of `~/.hermes/plugins/<name>/`
- Manifest source is reported as `bundled` in `hermes plugins list`
- User plugins with the same name override the bundled version

A plugin is a good candidate for bundling when:

- It has no optional dependencies (or they're already `pip install .[all]` deps)
- The behaviour benefits most users and is opt-out rather than opt-in
- The logic ties into lifecycle hooks that the agent would otherwise have to remember to invoke
- It complements a core capability without expanding the model-visible tool surface

Counter-examples — things that should stay as user-installable plugins, not bundled: third-party integrations with API keys, niche workflows, large dependency trees, anything that would meaningfully change agent behaviour by default.
