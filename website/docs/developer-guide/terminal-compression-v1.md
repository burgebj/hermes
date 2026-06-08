---
title: Terminal Compression v1
---

# Terminal Compression v1

Hermes terminal compression v1 is a narrow plugin-driven rewrite layer for the `terminal` tool.

## Rules
- only rewrites `terminal`
- only rewrites foreground, non-PTY calls
- never rewrites chained commands, redirects, heredocs, or dangerous commands
- first valid `pre_tool_call` directive wins

## Supported actions
- `block`
- `rewrite_args`

## Why this exists
This gives Hermes one small RTK-style win without importing RTK's whole command universe.

## v1 allowlist
- `git status`
- `git diff`
- `git log`
- `pytest`
- `cargo test`
- `npm test`
- `pnpm test`
- `docker ps`
- `ls`
- `rg`

## Debugging
If project plugins are enabled, the `terminal_compact` plugin logs each rewrite with its reason.
