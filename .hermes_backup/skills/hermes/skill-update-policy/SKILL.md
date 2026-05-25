---
name: skill-update-policy
description: "Core policy for deciding whether and how to update the skill library at session end. Replaces ad-hoc judgment with a structured decision framework."
version: 1.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [hermes, skills, policy, workflow]
---

# skill-update-policy

Core policy for deciding whether and how to update the skill library at session end. Replaces ad-hoc judgment.

## Decision framework (priority order)

- Be ACTIVE — most sessions produce at least one skill update, even small. Doing nothing is a missed learning opportunity.
- Signals that ALWAYS warrant action:
  1. User corrected style/tone/format/legibility/verbosity — frustration signals are FIRST-CLASS skill signals, not just memory. Embed the preference in the governing skill's body.
  2. User corrected workflow/approach/sequence — encode as pitfall or explicit step in the governing skill.
  3. Non-trivial technique/fix/workaround/debugging path/tool-usage pattern emerged — capture for future sessions.
  4. Loaded skill found wrong/missing/outdated — patch NOW.

## Preference order for update target (pick earliest that fits)

1. **Patch currently-loaded skill** — if any loaded skill covers the territory of the new learning, extend it.
2. **Patch existing umbrella** (via skills_list + skill_view) — if no loaded skill fits but an existing class-level skill does, add subsection, pitfall, or broaden trigger.
3. **Add support file under existing umbrella** — use correct directory:
   - `references/<topic>.md` — session detail, condensed knowledge banks
   - `templates/<name>.<ext>` — starter files to copy and modify
   - `scripts/<name>.<ext>` — statically re-runnable actions
   - Update SKILL.md with one-line pointer to new support file.
4. **Create new class-level umbrella** — name must be class-level, NOT PR number, error string, feature codename, or today's task artifact. If name only makes sense for today, fall back to (1)-(3).

## User-preference embedding rule

Style/format/workflow preferences belong in SKILL.md body, not memory. Memory captures 'who the user is and state'; skills capture 'how to do task class for this user'. When user complains about task handling, update the governing skill.

## Mandatory post-session scan (aggressiveness policy)

After EVERY session, BEFORE concluding "nothing to save", perform a forced scan for at least ONE of the following:

1. **Unstated preference revealed by silence or repeated patterns** — user didn't correct you because you got it right; does that tacit approval encode a preference that should be recorded for next time?
2. **Technique that became smoother through repetition** — task X went faster than last time; is there a shorthand, alias, or optimized sequence worth capturing?
3. **Relevant pitfall that didn't trigger this session but WAS relevant** — you navigated around something that would have been a trap for a less-prepared agent; document the guardrail you carried in your head.
4. **Supporting-context gap** — was there a concept, command, or boundary you had to figure out at runtime that would have been obvious from a reference file?

**Threshold:** If you cannot find something within three reading passes of the conversation, only THEN is "Nothing to save." permissible. The default is "find one thing," not "assume nothing."

**Precedent for this rule:** This policy was added after a user directly stated: *"A pass that does nothing is a missed learning opportunity, not a neutral outcome"* and *"I should never default to 'nothing to save'".* Reference: `references/skill-update-aggressiveness-policy.md`.

## Edge cases

- 'Nothing to save' is valid only if you've exhausted the mandatory scan above AND genuinely found nothing. If session ran smoothly with no corrections and no new technique, you may still have uncovered (a) an unstated preference, (b) a technique that got smoother, or (c) a relevant but latent pitfall.
- If two existing skills overlap, note it in reply — background curator handles consolidation at scale.
