---
title: "Codex — Делегуй кодування OpenAI Codex CLI (фічі, PRs)"
sidebar_label: "Codex"
description: "Делегуй кодування OpenAI Codex CLI (фічі, PRs)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Codex

Делегуй кодування OpenAI Codex CLI (фічі, PR‑и).

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/autonomous-ai-agents/codex` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Coding-Agent`, `Codex`, `OpenAI`, `Code-Review`, `Refactoring` |
| Related skills | [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Codex CLI

Делегуй завдання кодування до [Codex](https://github.com/openai/codex) через термінал Hermes. Codex — це автономний агент кодування OpenAI у вигляді CLI.

## Коли використовувати

- Створення фіч
- Рефакторинг
- Огляд PR‑ів
- Пакетне виправлення проблем

Потрібен Codex CLI та git‑репозиторій.

## Передумови

- Codex встановлений: `npm install -g @openai/codex`
- Налаштована автентифікація OpenAI: або `OPENAI_API_KEY`, або облікові дані Codex OAuth з процесу входу Codex CLI
- **Потрібно запускати всередині git‑репозиторію** — Codex відмовляється працювати поза ним
- Використовуй `pty=true` у викликах терміналу — Codex є інтерактивним термінальним застосунком

Для самого Hermes, `model.provider: openai-codex` використовує керовану Hermes OAuth для Codex з `~/.hermes/auth.json` після `hermes auth add openai-codex`. Для окремого Codex CLI дійсна OAuth‑сесія CLI може зберігатися у `~/.codex/auth.json`; не вважай відсутність `OPENAI_API_KEY` доказом відсутності автентифікації Codex.

## Одноразові завдання

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

Для роботи «з нуля» (Codex потребує git‑репо):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Фоновий режим (довгі завдання)

```
# Start in background with PTY
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Ключові прапорці

| Flag | Effect |
|------|--------|
| `exec "prompt"` | Одноразове виконання, завершується після завершення |
| `--full-auto` | Пісочниця, але автоматично схвалює зміни файлів у робочій області |
| `--yolo` | Без пісочниці, без схвалень (найшвидше, найнебезпечніше) |

## Огляд PR‑ів

Клонувати у тимчасову директорію для безпечного огляду:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Паралельне виправлення проблем за допомогою worktrees

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

## Пакетний огляд PR‑ів

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Правила

1. **Завжди використовуйте `pty=true`** — Codex є інтерактивним термінальним застосунком і зависає без PTY
2. **Потрібен git‑репо** — Codex не працює поза git‑директорією. Використайте `mktemp -d && git init` для роботи «з нуля»
3. **Використовуйте `exec` для одноразових завдань** — `codex exec "prompt"` виконується і коректно завершується
4. **`--full-auto` для створення** — автоматично схвалює зміни у пісочниці
5. **Фоновий режим для довгих завдань** — використайте `background=true` і стежте за процесом за допомогою інструмента `process`
6. **Не втручайтеся** — стежте за `poll`/`log`, будьте терплячі до довготривалих завдань
7. **Паралельність допустима** — запускайте кілька процесів Codex одночасно для пакетної роботи