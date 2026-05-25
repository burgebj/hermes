# Skill Update Aggressiveness Policy — Precedent

## Origin

This policy was established after a session where the user explicitly corrected a "nothing to save" conclusion
at session end. The user's critique revealed a pattern of excessive passivity in post-session skill scanning.

## User's exact language (verbatim)

> "A pass that does nothing is a missed learning opportunity, not a neutral outcome"

> "I should never default to 'nothing to save'"

## Implication for agent behavior

- The pass/no-pass threshold should be asymmetric: **find-at-least-one** by default,
  **save-nothing** only after three honest scanning passes.
- Silence is not proof of absence — a quiet session may contain unstated preferences
  (user didn't correct you because you guessed right — encode the guess so next agent
  doesn't have to guess).
- The user values concision and expects **action**. They would rather have a small,
  imperfect skill update than a wimp-out. When in doubt, write something small and real
  rather than nothing.

## How to use this file

After every session, run the scan from `SKILL.md` section "Mandatory post-session scan".
If you're about to write "Nothing to save.", re-read this file first.
If you still conclude "nothing", you must be able to articulate why each of the four
scan categories came up empty.
