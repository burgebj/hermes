---
name: coding-go
description: Go development — project structure, debugging, build systems, and tooling best practices.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Go Development Skill

## Overview
Development and debugging of Go applications, including project structure, build systems, and tooling.

## Workflow
1. Understand the user's task and gather context from the current conversation and any loaded files.
2. For debugging: reproduce the issue, identify the root cause, propose a fix, test it.
3. Avoid overly verbose explanations — focus on precise, actionable code changes.
4. When providing code changes, use `diff` format or direct file edits rather than long explanations unless asked.
5. If the user expresses frustration about verbosity, style, or format, immediately adapt and note the preference in this skill for future sessions.

## Preferences (User-Specific)
- Prefer concise, direct answers. Avoid explaining basic concepts unless asked.
- Do not restate the user's code block unless needed for context — provide only the change or diff.
- Use standard Go formatting and idioms; do not suggest workarounds without necessity.
- When the user says "stop doing X", embed the correction here — do not treat it as a one-off memory.

## Pitfalls
- Do not propose `go mod tidy` as a catch-all fix without checking if dependency versions are relevant.
- Avoid suggesting command-line tools the user has not explicitly mentioned unless they are standard Go development tools.
- Do not restate the problem or summarize conversation history unless requested — get straight to the solution.
