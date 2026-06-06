---
name: cmd-hookify-configure
description: ECC Command: /hookify-configure -- slash command instructions from ECC
---

# Command: /hookify-configure

This skill teaches the agent how to handle the `/hookify-configure` slash command.
When the user invokes this command, follow the instructions below.

---
description: Enable or disable hookify rules interactively
---

Interactively enable or disable existing hookify rules.

## Steps

1. Find all `.claude/hookify.*.local.md` files
2. Read the current state of each rule
3. Present the list with current enabled / disabled status
4. Ask which rules to toggle
5. Update the `enabled:` field in the selected rule files
6. Confirm the changes

