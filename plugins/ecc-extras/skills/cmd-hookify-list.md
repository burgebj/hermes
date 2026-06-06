---
name: cmd-hookify-list
description: ECC Command: /hookify-list -- slash command instructions from ECC
---

# Command: /hookify-list

This skill teaches the agent how to handle the `/hookify-list` slash command.
When the user invokes this command, follow the instructions below.

---
description: List all configured hookify rules
---

Find and display all hookify rules in a formatted table.

## Steps

1. Find all `.claude/hookify.*.local.md` files
2. Read each file's frontmatter:
   - `name`
   - `enabled`
   - `event`
   - `action`
   - `pattern`
3. Display them as a table:

| Rule | Enabled | Event | Pattern | File |
|------|---------|-------|---------|------|

4. Show the rule count and remind the user that `/hookify-configure` can change state later.

