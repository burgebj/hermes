---
name: codex
description: "Delegate coding to OpenAI Codex CLI (features, PRs)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) via the Hermes terminal. Codex is OpenAI's autonomous coding agent CLI.

## When to use

- Building features
- Refactoring
- PR reviews
- Batch issue fixing

Requires the codex CLI and a git repository.

## Prerequisites

- Codex installed: `npm install -g @openai/codex`
- OpenAI API key configured
- **Must run inside a git repository** — Codex refuses to run outside one
- Use `pty=true` in terminal calls — Codex is an interactive terminal app

### Installation Troubleshooting

**Codex binary not found (`command not found`):**
- Installed with `npm`? Check `npm bin -g` is in your PATH
- Installed with `bun`? Bun places binaries in `~/.bun/bin/codex` (a JS wrapper). If `bun` itself isn't on the non-interactive PATH, create a wrapper:
  ```bash
  cat > ~/.local/bin/codex << 'EOF'
  #!/bin/bash
  exec /home/jianliu/.bun/bin/bun /home/jianliu/.bun/install/global/node_modules/@openai/codex/dist/cli.js "$@"
  EOF
  chmod +x ~/.local/bin/codex
  ```

**Codex works interactively but fails from Hermes terminal:**
Same issue — `codex` binary resolves via interactive PATH but the non-interactive Hermes terminal shell may not have bun's bin directory. Use the wrapper above or add `export PATH="$HOME/.bun/bin:$PATH"` to a script entry point.

**`codex exec resume` does NOT support `-C`/`--cd` flag:**
Unlike `codex exec <prompt>`, the resume subcommand doesn't accept `--cd`. You must `cd` to the target directory before calling resume:
```bash
# CORRECT:
cd /path/to/repo && codex exec resume --last "Continue the task"

# WRONG (will error):
codex exec resume --last -C /path/to/repo "Continue the task"

# The companion script codex_session.sh handles this correctly with `cd` before resume.
```

## One-Shot Tasks

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Session Continuity (Default: Reuse Same Session)

Each call to `codex exec` starts a **fresh** session by default, losing context. For multi-step tasks (design → implement → test → fix), use session continuity:

### Automatic Session Script

Save as `scripts/codex_session.sh` alongside this skill:

```bash
#!/bin/bash
# codex_session.sh — Call Codex with automatic session continuity
set -euo pipefail
MARKER="$HOME/.codex/last_session_for_hermes"
WORKDIR=""; MODEL=""; JSON_FLAG=""
while [[ $# -gt 0 ]]; do
  case "$1" in --workdir) WORKDIR="$2"; shift 2 ;; --model) MODEL="$2"; shift 2 ;;
    -j|--json) JSON_FLAG="--json"; shift ;; --) shift; break ;; *) break ;; esac
done
PROMPT="$*"
if [ -z "$PROMPT" ]; then echo "ERROR: prompt required"; exit 1; fi

if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "active" ]; then
  echo "[Codex-Session] Resuming last session..." >&2
  if [ -n "$WORKDIR" ]; then cd "$WORKDIR"; fi
  codex exec resume --last ${JSON_FLAG} ${MODEL:+-m "$MODEL"} "$PROMPT"
  EC=$?; if [ $EC -ne 0 ]; then rm -f "$MARKER"; fi; exit $EC
fi

echo "[Codex-Session] Starting new session..." >&2
ARGS=(); [ -n "$WORKDIR" ] && ARGS=(-C "$WORKDIR"); [ -n "$MODEL" ] && ARGS+=(-m "$MODEL")
[ -n "$JSON_FLAG" ] && ARGS+=("$JSON_FLAG")
codex exec --full-auto "${ARGS[@]}" "$PROMPT"
EC=$?; if [ $EC -eq 0 ]; then echo "active" > "$MARKER"; fi; exit $EC
```

**How it works:**
1. **First call** → `codex exec --full-auto <prompt>` — starts a new session, saves a marker
2. **Subsequent calls** → `codex exec resume --last <prompt>` — resumes the last session, carrying over full context (files read, changes made, decisions)
3. **Resume failure** → marker is auto-cleared, next call starts fresh

**Usage from Hermes:**
```bash
# First call — creates session
bash ~/.hermes/skills/autonomous-ai-agents/codex/scripts/codex_session.sh --workdir /path/to/repo "Add input validation to API"

# Second call — same session, Codex remembers context
bash ~/.hermes/skills/autonomous-ai-agents/codex/scripts/codex_session.sh --workdir /path/to/repo "Now add unit tests for that validation"

# JSON output (use -j, adds --json flag)
bash ~/.hermes/skills/autonomous-ai-agents/codex/scripts/codex_session.sh -j --workdir /path "Describe the project structure"

# Start fresh (ignore previous session)
rm -f ~/.codex/last_session_for_hermes

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --yolo exec 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --yolo exec 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Rules

1. **Always use `pty=true`** — Codex is an interactive terminal app and hangs without a PTY
2. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
4. **`--full-auto` for building** — auto-approves changes within the sandbox
5. **Background for long tasks** — use `background=true` and monitor with `process` tool
6. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
7. **Parallel is fine** — run multiple Codex processes at once for batch work
