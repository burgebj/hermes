# Codex Session — Session Continuity Reference

> This document was absorbed from the standalone `codex-session` skill. It describes how to call OpenAI Codex from within Hermes with automatic session continuity.

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
```

### Start a fresh session (ignore previous context)

```bash
rm -f ~/.codex/last_session_for_hermes
```

## Tips

- Use `--workdir` to point to the git repo — Codex needs a git repo to function
- For long-running tasks, use `background=true` and monitor with `process(action="poll")`
- If Codex hangs waiting for approval, use `--model o4-mini` or `--full-auto` flags
- Session continuity works per-machine; the marker file tracks the most recent Codex session
- To reset: `rm -f ~/.codex/last_session_for_hermes`

## Pitfalls

### Model Version Incompatibility on Resume

If you see: `ERROR: {"detail":"The 'gpt-5.5' model requires a newer version of Codex. Please upgrade..."}`

This can happen when the previous session used a newer model than your current Codex CLI supports.

**First, try upgrading Codex itself:**
```bash
npm install -g @openai/codex
rm -f ~/.codex/last_session_for_hermes
```

If upgrade doesn't help, clear marker and retry with a compatible model:
```bash
bash ~/.hermes/skills/codex-session/scripts/codex_session.sh --workdir /path/to/repo --model gpt-5.4 "Your prompt"
```

### Upgrading Codex

```bash
npm update -g @openai/codex
codex --version
```
