---
name: git-workflow
description: |
  End-to-end Git workflow assistant — branching, committing, rebasing,
  conflict resolution, PR preparation, and history cleanup. Works with
  any repo and any branching strategy (GitFlow, trunk-based, GitHub Flow).
version: 0.1.0
author: HeLLGURD
license: MIT
platforms: [linux, macos, windows]
category: software-development
triggers:
  - "help me with git"
  - "create a branch"
  - "commit my changes"
  - "rebase onto main"
  - "resolve merge conflict"
  - "squash my commits"
  - "prepare PR"
  - "clean up git history"
  - "undo last commit"
  - "stash my changes"
  - "cherry-pick"
  - "my branch is behind main"
toolsets:
  - terminal
  - file
metadata:
  hermes:
    tags: [Git, Workflow, Branching, Rebase, Merge, Commit, PR, Version-Control]
    related_skills: [changelog-generator, code-wiki]
---

# Git Workflow

A complete Git workflow assistant for everyday development tasks — from
creating branches to cleaning up history before a PR. Handles the full
lifecycle: branch → commit → sync → rebase → PR preparation.

Works with any branching strategy. No external services. Uses only the
`terminal` tool.

---

## When to Use

- User asks for help with any git operation
- Branch is behind main and needs syncing
- Commits are messy and need squashing before PR
- Merge conflict needs resolving
- Something went wrong and needs undoing

Do NOT use for:
- GitHub-specific operations (opening PRs, reviewing code) — use the
  `github-pr-reviewer` skill or `gh` CLI directly
- Generating changelogs from history — use the `changelog-generator` skill
- Setting up a repo from scratch — just run `git init` and answer inline

---

## Prerequisites

- `git` on PATH and working directory inside a git repo
- For remote operations: SSH key or HTTPS credential configured

---

## Quick Reference

| Task | Command |
|---|---|
| New branch | `git checkout -b feat/my-feature` |
| Stage all | `git add -p` (interactive) or `git add .` |
| Commit | `git commit -m "feat: description"` |
| Sync with main | `git fetch origin && git rebase origin/main` |
| Squash N commits | `git rebase -i HEAD~N` |
| Undo last commit | `git reset --soft HEAD~1` |
| Stash | `git stash push -m "description"` |
| Cherry-pick | `git cherry-pick <hash>` |
| Force push safely | `git push --force-with-lease` |

---

## Workflows

### 1 — Start a new feature branch

```bash
# Always branch from the latest main
git fetch origin
git checkout main
git pull origin main
git checkout -b feat/my-feature
```

Branch naming conventions (auto-suggest based on task type):

| Type | Pattern | Example |
|---|---|---|
| Feature | `feat/short-description` | `feat/dark-mode` |
| Bug fix | `fix/short-description` | `fix/login-crash` |
| Hotfix | `hotfix/short-description` | `hotfix/null-pointer` |
| Refactor | `refactor/short-description` | `refactor/auth-module` |
| Docs | `docs/short-description` | `docs/api-reference` |
| Chore | `chore/short-description` | `chore/update-deps` |

---

### 2 — Stage and commit

Always show the diff before staging:

```bash
git status
git diff
```

Prefer interactive staging to avoid committing unrelated changes:

```bash
git add -p
```

Commit with a clear message following Conventional Commits:

```bash
git commit -m "feat(auth): add OAuth2 PKCE flow support"
```

Commit message rules:
- Format: `type(scope): short description` (scope optional)
- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`
- Subject line ≤ 72 characters, imperative mood ("add" not "added")
- Add `!` for breaking changes: `feat!: drop Python 3.9 support`
- Body (optional): wrap at 72 chars, explain *why* not *what*

---

### 3 — Sync branch with main (rebase)

Rebase is preferred over merge for feature branches — keeps history linear:

```bash
git fetch origin
git rebase origin/main
```

If conflicts arise during rebase:

```bash
# See which files conflict
git status

# For each conflicted file: open it, resolve the conflict markers, then:
git add <resolved-file>

# Continue rebase after resolving all conflicts
git rebase --continue

# To abort and go back to original state
git rebase --abort
```

**Conflict resolution strategy:**

1. Run `git diff --diff-filter=U` to list all conflicted files
2. For each file, read both sides of the conflict markers:
   ```
   <<<<<<< HEAD (your branch)
   your changes
   =======
   incoming changes from main
   >>>>>>> origin/main
   ```
3. Decide which version to keep (or combine both)
4. Remove all conflict markers — the file must be valid after editing
5. `git add <file>` → `git rebase --continue`

---

### 4 — Clean up commits before PR (interactive rebase)

Squash messy WIP commits into clean logical units:

```bash
# See how many commits ahead of main you are
git log origin/main..HEAD --oneline

# Interactive rebase for last N commits
git rebase -i origin/main
```

In the interactive editor:
- `pick` — keep the commit as-is
- `reword` — keep the commit but edit the message
- `squash` — merge into the previous commit (combine messages)
- `fixup` — merge into previous commit (discard this message)
- `drop` — delete the commit entirely

**Common squash pattern:**
```
pick a1b2c3 feat: initial implementation
fixup d4e5f6 wip
fixup g7h8i9 fix typo
fixup j0k1l2 address review comments
```
→ Results in one clean commit with the first message.

---

### 5 — Undo operations

| Situation | Command | Notes |
|---|---|---|
| Undo last commit, keep changes staged | `git reset --soft HEAD~1` | Safest undo |
| Undo last commit, keep changes unstaged | `git reset HEAD~1` | Changes remain in working tree |
| Undo last commit, discard changes | `git reset --hard HEAD~1` | Destructive — ask user to confirm |
| Undo a pushed commit | `git revert <hash>` | Creates a new commit, safe for shared branches |
| Unstage a file | `git restore --staged <file>` | |
| Discard working tree changes | `git restore <file>` | Destructive — confirm first |
| Recover a deleted branch | `git reflog` then `git checkout -b <name> <hash>` | |

**Always confirm before running any `--hard` or destructive command.**
Show the user what will be lost:

```bash
# Show what would be discarded
git diff HEAD
git stash list
```

---

### 6 — Stash management

```bash
# Save current work with a description
git stash push -m "WIP: half-done auth refactor"

# List stashes
git stash list

# Apply latest stash (keep it in the list)
git stash apply

# Apply and remove from list
git stash pop

# Apply a specific stash
git stash apply stash@{2}

# Drop a stash
git stash drop stash@{0}

# Show what's in a stash
git stash show -p stash@{0}
```

---

### 7 — Cherry-pick

Move specific commits from one branch to another:

```bash
# Find the commit hash
git log --oneline other-branch

# Cherry-pick it
git cherry-pick <hash>

# Cherry-pick a range (exclusive..inclusive)
git cherry-pick a1b2c3..d4e5f6

# Cherry-pick without committing (stage only)
git cherry-pick --no-commit <hash>
```

If conflicts arise: resolve them, `git add`, then `git cherry-pick --continue`.

---

### 8 — Push and force-push safely

```bash
# First push (set upstream)
git push -u origin feat/my-feature

# Subsequent pushes
git push

# After a rebase (use --force-with-lease, NOT --force)
git push --force-with-lease
```

**Always use `--force-with-lease` instead of `--force`.** It fails if
someone else pushed to the branch since your last fetch — preventing
accidental overwrites. Never force-push to `main` or `master`.

---

### 9 — Prepare for PR

Run this checklist before pushing for review:

```bash
# 1. Make sure you're up to date
git fetch origin
git rebase origin/main

# 2. Review your own diff
git diff origin/main..HEAD

# 3. Check commit count and messages
git log origin/main..HEAD --oneline

# 4. Run tests (adapt to project)
# e.g.: pytest, npm test, cargo test, go test ./...

# 5. Check for debug artifacts
git diff origin/main..HEAD | grep -E "console\.log|debugger|pdb\.set_trace|breakpoint\(\)|TODO.*REMOVE"

# 6. Push
git push -u origin feat/my-feature
```

---

### 10 — Diagnose common problems

**"My branch has diverged from main"**
```bash
git fetch origin
git log --oneline --graph origin/main HEAD
# Use rebase, not merge: git rebase origin/main
```

**"I committed to main by accident"**
```bash
# Move the commit to a new branch
git branch fix/my-accidental-commit
git reset --hard origin/main
git checkout fix/my-accidental-commit
```

**"I need to split a commit into two"**
```bash
git rebase -i HEAD~1   # mark the commit as 'edit'
git reset HEAD~1       # unstage everything
git add -p             # stage the first logical change
git commit -m "first part"
git add -p             # stage the second logical change
git commit -m "second part"
git rebase --continue
```

**"I lost my stash / dropped commits"**
```bash
git reflog --all | head -30
# Find the commit hash and recover:
git checkout -b recovery/<name> <hash>
```

---

## Safety Rules

1. **Never `--force` push to main/master/develop** — always confirm the
   target branch before any force operation.
2. **Always confirm before `--hard` resets** — show the user what will be
   discarded.
3. **Prefer `revert` over `reset` on shared branches** — `reset` rewrites
   history, `revert` is safe for pushed commits.
4. **Check `git stash list` before a hard reset** — make sure WIP is stashed.
5. **Dry-run rebases mentally first** — `git log --oneline origin/main..HEAD`
   before `git rebase -i`.
