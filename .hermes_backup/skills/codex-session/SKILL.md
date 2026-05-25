---
name: codex-session
description: "Call OpenAI Codex explicitly with automatic session continuity — first call starts a new session, subsequent calls auto-resume the same session so context carries over."
version: 1.0.0
trigger: codex
---

# Codex Session — Explicit Codex Calling with Continuity

Call OpenAI Codex from within Hermes. The first call creates a fresh session; subsequent calls **automatically resume the same session**, so Codex remembers previous context (files read, changes made, etc.).

## When to use

- Building features (multi-step: design → implement → test → fix)
- Complex refactoring (spans multiple subtasks)
- Batch PR reviews
- Any coding task where you want Codex to keep context across calls

## Prerequisites

- Codex installed (`npm install -g @openai/codex`) ✓
- OpenAI API key configured ✓
- **Must run inside a git repository** — Codex refuses to run outside one
- Working directory should be a git repo

## Session Continuity Logic

The companion script `scripts/codex_session.sh` handles continuity:

1. **First call** → `codex exec --sandbox workspace-write <prompt>` — starts a new session, saves a marker
2. **Subsequent calls** → `codex exec resume --last <prompt>` — resumes the last session, preserving context
3. **If resume fails** (session expired/deleted) → marker is cleared, next call starts fresh

Session marker: `~/.codex/last_session_for_hermes`

## Usage from Hermes

### One-shot (foreground, waits for result)

```bash
# Default: resume same session
bash ~/.hermes/skills/codex-session/scripts/codex_session.sh --workdir /path/to/repo "Add input validation to the API endpoints"

# Specify model
bash ~/.hermes/skills/codex-session/scripts/codex_session.sh --workdir /path/to/repo --model o4-mini "Fix the bug in auth.py"

# JSON output
bash ~/.hermes/skills/codex-session/scripts/codex_session.sh -j --workdir /path/to/repo "Refactor database layer"
```

### Background (long tasks, non-blocking)

```bash
terminal(
  command="bash ~/.hermes/skills/codex-session/scripts/codex_session.sh --workdir /home/jianliu/work/project 'Write comprehensive unit tests for the auth module'",
  workdir="/home/jianliu/work/project",
  background=true,
  pty=true
)
# → returns session_id, use process(action="poll", session_id="...") to check progress
```

### Start a fresh session (ignore previous context)

```bash
# Delete the marker to force a fresh session
rm -f ~/.codex/last_session_for_hermes
# Then call as usual
```

## Tips

- Use `--workdir` to point to the git repo — Codex needs a git repo to function
- For long-running tasks, use `background=true` and monitor with `process(action="poll")`
- If Codex hangs waiting for approval, use `--model o4-mini` or `--full-auto` flags (already default in the script)
- Session continuity works per-machine; the marker file tracks the most recent Codex session
- To reset and start fresh: `rm -f ~/.codex/last_session_for_hermes`

## Pitfalls

### Model Version Incompatibility on Resume

If you see: `ERROR: {"detail":"The 'gpt-5.5' model requires a newer version of Codex. Please upgrade..."}`

This can happen when **the previous session used a newer model** than your current Codex CLI supports. The resume attempt picks up the old model from the stored session metadata gateway, and fails.

**First, try upgrading Codex itself** (this is often the root cause):
```bash
npm install -g @openai/codex
# After upgrade, clear stale marker and retry
rm -f ~/.codex/last_session_for_hermes
```

If upgrade doesn't help (session is stale even on latest Codex):
1. `rm -f ~/.codex/last_session_for_hermes` — clear the session marker
2. Call again with an explicit compatible model:
   ```bash
   bash ~/.hermes/skills/codex-session/scripts/codex_session.sh --workdir /path/to/repo --model gpt-5.4 "Your prompt"
   ```
3. To check which models your Codex version supports:
```bash
codex --sandbox workspace-write --version  # e.g. "codex-cli-exec 0.107.0"
# Then test: codex --sandbox workspace-write --model gpt-5.4 "hello"
```

The companion script handles resume failure gracefully (auto-clears the marker), but you still need to pass `--model <compatible-version>` on the fresh start.

### Upgrading Codex

```bash
npm update -g @openai/codex
# Or latest: npm install -g @openai/codex
# Check current version:
codex --version
```

### Checking Available Models

```bash
# Test which models your current Codex version supports:
codex exec --sandbox workspace-write --model gpt-5.4 "hello" 2>&1 | head -5
codex exec --sandbox workspace-write --model gpt-5.5 "hello" 2>&1 | head -5

# If a model fails with "requires a newer version of Codex",
# upgrade first, then clear marker and retry.
```
