---
name: python-automation
description: "Python automation coding conventions — bare output, no commentary, ready-to-run code blocks."
---

# Python Automation

## Style Preferences
- **Output format**: When providing code solutions, output only the code block with no surrounding explanation, commentary, or markdown headers unless the user explicitly asks for reasoning.
- **Conciseness**: Default to minimal verbosity. Do not explain the steps you took or why a solution works unless the user asks.
- **Code presentation**: Present Python scripts as ready-to-run files with no additional meta-commentary. Omit "here's the code" or "I've updated the script" introductions.

## Workflow
- When the user requests a modification to a script, apply the change and output the full updated script in a single code block. Do not show diffs, ask for confirmation, or describe the change unless prompted.

## Pitfalls
- Do not preface code with explanations like "slight change needed" or "here's the corrected version." Just output the code.
- If the user expresses frustration with verbosity (e.g., "stop explaining things — just give me the answer"), immediately switch to bare output mode for the remainder of the task and encode the preference as a permanent rule in the relevant skill.
