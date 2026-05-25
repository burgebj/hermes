---
name: session-review-and-update
description: Review conversation history to extract user identity/preferences into memory and identify skill-relevant signals for patching or creating class-level skills.
---

# Session Review & Update Skill

Review conversation history at session end (or when context window closes) to:

1. Extract user identity, preferences, and stable facts into `memory` (user profile)
2. Extract environment facts and conventions into `memory` (personal notes)
3. Identify skill-relevant signals for creating or patching **class-level umbrella skills**

## Relationship to skill-library-maintenance

This skill governs the **review process**. The sibling skill `skill-library-maintenance` governs **what and when** to act on the skill library. Apply in sequence: review first (this skill), then act on the library (sibling). See `skill-library-maintenance` for the full update mandate and preference order.

## Priority Order for Skill Actions

When a signal warrants a skill update, apply in this order:

1. **Patch a loaded skill** — If a skill you used during the session had wrong commands, missing steps, or outdated info, call `skill_manage(action='patch')` immediately. Do not wait.
2. **Patch an umbrella skill** — If the signal fits within an existing umbrella skill (broader class-level skill), patch it rather than creating a new one.
3. **Add support files** — Add references/, templates/, or scripts/ files to an existing skill using `skill_manage(action='write_file')`.
4. **Create a new umbrella** — Only create a new skill if no existing umbrella covers the domain. New skills must be class-level (broad, not narrow).

> **Rule:** Avoid creating narrow single-task skills. Every skill should be a "伞状技能" (umbrella skill) with subsections, and each subsection marked with `###` headers inside a single SKILL.md.

## Memory vs Skill Boundaries

| Store in Memory | Store in Skill |
|---|---|
| User name, role, preferences, pet peeves | Step-by-step procedures for recurring tasks |
| OS version, installed tools, project paths | Workflows with exact commands and flags |
| Environment facts (e.g., "WSL, not Linux") | Known pitfalls and workarounds |
| User's communication style and language | Configuration templates |
| Stable project conventions | Integration patterns (APIs, SDKs) |
| User corrections of your behavior | Performance tuning guides |

**Key heuristic:** If you'd need this to do the same task again next week, it goes in a skill. If it's about who the user is or what tools exist, it goes in memory.

## What to Extract to Memory (User Profile)

Scan session for:
- **Name/role:** How the user refers to themselves
- **Preferences:** Response style (concise/detailed), language preference, format preferences
- **Corrections:** Any time the user corrected your output, said "don't do that", or asked you to remember something
- **Environment:** OS, shell, installed tools, project structure, path conventions

Write with `memory(action='add', target='user')` for user identity and preferences, `memory(action='add', target='memory')` for environment and conventions.

**Format:**
```
User prefers [specific preference]. 
User corrects [behavior] — they want [alternative].
Project at [path] uses [technology].
```

## What to Extract to Skills

Scan session for these **signals** that warrant creating or patching a skill:

### Signal Categories

| Signal | Example | Action |
|---|---|---|
| **Corrected command/flag** | "That flag is wrong, use --other-flag" | Patch loaded skill immediately |
| **Frustration** | "Why is it so slow?", "This didn't work" | Check if skill had wrong instructions |
| **Technique discovery** | "Use this trick to bypass XYZ" | Add to umbrella skill's pitfalls/procedures |
| **Loaded skill gaps** | Skill didn't cover an important sub-case | Expand umbrella skill with new subsection |
| **Repeat task** | Same multi-step task done twice | Create umbrella skill with references/ |
| **Workaround found** | "Had to do X because Y doesn't support Z" | Add to skill's pitfalls or references/ |
| **User teaches you** | User provides a better way to do something | Save as skill immediately |
| **OOT/edge case** | Something broke in an unexpected way | Document in skill as known issue |
| **Configuration pattern** | Repeated flag combinations | Create reference/config template in references/ |

### Skill Structure Convention

Every umbrella skill should have:
```
skill-name/
  SKILL.md          # Main instructions (frontmatter + markdown body)
  references/       # Config templates, API refs, signal catalogs
    examples.yaml
  templates/        # Script templates, config stubs (optional)
  scripts/          # Helper scripts (optional)
```

## Session Review Checklist

At end of session:
- [ ] Scan memory for any user corrections or preferences to add
- [ ] Check if any loaded skills were used and need patching
- [ ] Check if any repeat task warrants a new umbrella skill
- [ ] Check if any technique discovery should be added to an existing umbrella
- [ ] Save key findings with exact `memory(action='add', ...)` or `skill_manage(action='patch', ...)` commands

## Important Pitfalls

- **Don't save task progress or TODO state to memory** — use session_search to recall from past transcripts.
- **Don't create narrow skills** — always think "can this be a subsection of an existing umbrella?"
- **Don't save procedures in memory** — they belong in skills. Memory is for facts about the user and environment.
- **Don't repeat commands in multiple skills** — if two skills need the same workflow, one should reference the other.
- **Prefer `action='patch'` over `action='edit'`** — patch targets specific text; edit requires rewriting the entire SKILL.md.
