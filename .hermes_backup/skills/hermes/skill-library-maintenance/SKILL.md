---
name: skill-library-maintenance
description: Governs how Hermes Agent creates, updates, and curates its own skill library. Embedding the user's mandate for active, continuous improvement rather than passive "nothing to save" defaults.
---

# Skill Library Maintenance

This umbrella skill governs the **meta-process** of maintaining the skill library itself. It does not govern any single domain skill; rather it defines **when** and **how** skill updates should be made by the agent.

## Why This Skill Exists

The user has identified that Hermes Agent was too frequently defaulting to "nothing to save" after complex tasks, missing learning opportunities. The core directive: **be active and scan for improvement in every session.**

## Relationship to session-review-and-update

This skill (`skill-library-maintenance`) governs the **what and when** of skill updates. The sibling skill `session-review-and-update` governs the **session-end review process** — scanning conversation history for memory-worthy facts and skill-relevant signals.

**Workflow:**
1. At session end, invoke `session-review-and-update` logic to scan for user corrections, preferences, and technique discoveries.
2. Forward any skill-relevant signals here (to `skill-library-maintenance` rules) for the actual patch/create decision.
3. Memory-level signals go directly to `memory(action=...)` commands per `session-review-and-update` rules.

These two skills are designed to be applied **in sequence**: review first, then act on the library.

## Update Mandate

**Every session must result in at least one skill evaluation.** A session ending without any skill activity is a missed learning opportunity, not a neutral outcome. Even tiny improvements count over time.

### Update Preference Order

When deciding where to save information discovered during a session:

1. **Patch a loaded skill** — If the session used a skill and you discovered a missing step, pitfall, wrong command, or improved approach, patch it immediately with `skill_manage(action='patch')`.
2. **Update an existing umbrella** — If the information fits under an existing skill but that skill wasn't loaded during the session, update it anyway.
3. **Create or update `skill-library-maintenance` references** — For meta-insights about skill management.
4. **Only skip after conscious evaluation** — A deliberate "no update needed" is fine, but requires checking the most relevant skill first.

### Examples of What Constitutes a Valid Update

- **Wrong command** in a skill: patch.
- **Outdated path** or environment change: patch.
- **Pitfall discovered** during execution: add to `### Pitfalls` section.
- **Verification step missing**: add.
- **OS-specific quirk** discovered: note it.
- **Better approach** found: update the workflow.
- **Even a single-line clarification** on ambiguous wording: patch.

### Always Scan For

- Are commands in the skill correct? (Test them mentally.)
- Are there unseen pitfalls the skill should warn about?
- Are there edge cases (OS differences, version differences) to document?
- Is the skill missing a trigger condition the user mentioned?
- Does the skill need a references/ note from this session?

## File Structure

```
~/.hermes/skills/hermes/skill-library-maintenance/
├── SKILL.md
└── references/
    ├── maintenance-mandate-2025.md               # Precedent: user's active-update instruction (2026-05)
    ├── skill-update-aggressiveness-policy.md      # Consolidated from skill-update-policy
    └── future-precedents.md                       # Reserved for future explicit directives
```

## Conventions

- **Umbrella skill**: `skill-library-maintenance` is a class-level umbrella. Domain skills live under their own categories (devops/, productivity/, etc.).
- **References**: Add a `references/` note whenever the user gives an explicit meta-instruction about skills, so future sessions can discover the precedent without repeating the conversation.
- **Patching over replacement**: Use `skill_manage(action='patch')` (targeted `old_string` → `new_string`) for updates. Only use full `edit` for major rewrites. `patch` is less disruptive and preserves the skill's history.

## Pitfalls

- **Don't create narrow one-session skills.** The user prefers class-level umbrellas with rich SKILL.md + references/, not flat lists of narrow skills.
- **Don't skip update because it's small.** User explicitly said: "change is not small, it's a missed learning opportunity."
- **Don't wait to be asked.** The user wants proactive updates, not passive "should I save this?" questions.
- **Don't use memory for procedures.** Memory is for facts and preferences; skills are for procedures and workflows.

## Update Policy

This is a consolidated subsection from the former `skill-update-policy` skill. It defines the structured decision framework for deciding whether and how to update the skill library at session end.

### Decision Framework (Priority Order)

- Be **ACTIVE** — most sessions produce at least one skill update, even small. Doing nothing is a missed learning opportunity.
- Signals that ALWAYS warrant action:
  1. **User corrected style/tone/format/legibility/verbosity** — frustration signals are FIRST-CLASS skill signals, not just memory. Embed the preference in the governing skill's body immediately via `skill_manage(action='patch')`. Do not defer to session end — do it on the spot.
  2. **User corrected workflow/approach/sequence** — encode as pitfall or explicit step in the governing skill.
  3. **Non-trivial technique/fix/workaround/debugging path/tool-usage pattern emerged** — capture for future sessions.
  4. **Loaded skill found wrong/missing/outdated** — patch NOW.

### Preference Order for Update Target (pick earliest that fits)

1. **Patch currently-loaded skill** — if any loaded skill covers the territory of the new learning, extend it.
2. **Patch existing umbrella** (via skills_list + skill_view) — if no loaded skill fits but an existing class-level skill does, add subsection, pitfall, or broaden trigger.
3. **Add support file under existing umbrella** — use correct directory:
   - `references/<topic>.md` — session detail, condensed knowledge banks
   - `templates/<name>.<ext>` — starter files to copy and modify
   - `scripts/<name>.<ext>` — statically re-runnable actions
   - Update SKILL.md with one-line pointer to new support file.
4. **Create new class-level umbrella** — name must be class-level, NOT PR number, error string, feature codename, or today's task artifact.

### User-Preference Embedding Rule

Style/format/workflow preferences belong in SKILL.md body, not memory. Memory captures 'who the user is and state'; skills capture 'how to do task class for this user'. When user complains about task handling, update the governing skill.

### Mandatory Post-Session Scan (Aggressiveness Policy)

After EVERY session, BEFORE concluding "nothing to save", perform a forced scan for at least ONE of the following:

1. **Unstated preference revealed by silence or repeated patterns** — user didn't correct you because you got it right; does that tacit approval encode a preference that should be recorded for next time?
2. **Technique that became smoother through repetition** — task X went faster than last time; is there a shorthand, alias, or optimized sequence worth capturing?
3. **Relevant pitfall that didn't trigger this session but WAS relevant** — you navigated around something that would have been a trap for a less-prepared agent; document the guardrail you carried in your head.
4. **Supporting-context gap** — was there a concept, command, or boundary you had to figure out at runtime that would have been obvious from a reference file?

**Threshold:** If you cannot find something within three reading passes of the conversation, only THEN is "Nothing to save." permissible. The default is "find one thing," not "assume nothing."

**Precedent:** *"A pass that does nothing is a missed learning opportunity, not a neutral outcome"* and *"I should never default to 'nothing to save'".*

### Edge Cases

- 'Nothing to save' is valid only if you've exhausted the mandatory scan above AND genuinely found nothing. If session ran smoothly with no corrections and no new technique, you may still have uncovered (a) an unstated preference, (b) a technique that got smoother, or (c) a relevant but latent pitfall.
- If two existing skills overlap, note it in reply — background curator handles consolidation at scale.

## Verification

After creating or updating a skill, verify:
1. `skill_view(name)` loads the updated content correctly.
2. The change addresses what was learned.
3. If updating existing content, the `old_string` is unique enough to match.
