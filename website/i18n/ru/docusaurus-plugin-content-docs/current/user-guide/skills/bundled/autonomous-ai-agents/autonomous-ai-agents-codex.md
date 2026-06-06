---
title: "Делегировать кодинг OpenAI Codex CLI (features, PRs)"
sidebar_label: "Codex"
description: "Делегировать кодинг OpenAI Codex CLI (features, PRs)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Codex

Делегировать написание кода OpenAI Codex CLI (фичи, PR‑ы).

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при работе навыка.
:::

# Codex CLI

Делегировать задачи кодирования [Codex](https://github.com/openai/codex) через терминал Hermes. Codex — автономный агент кодирования от OpenAI в виде CLI.

## Когда использовать

- Создание функций
- Рефакторинг
- Обзор PR‑ов
- Пакетное исправление проблем

Требуется CLI Codex и git‑репозиторий.

## Предварительные требования

- Codex установлен: `npm install -g @openai/codex`
- Настроена аутентификация OpenAI: либо `OPENAI_API_KEY`, либо учётные данные OAuth Codex из процесса входа в CLI Codex
- **Необходимо запускать внутри git‑репозитория** — Codex отказывается работать вне репозитория
- Использовать `pty=true` в вызовах терминала — Codex является интерактивным терминальным приложением

Для самого Hermes параметр `model.provider: openai-codex` использует управляемый Hermes OAuth Codex из `~/.hermes/auth.json` после `hermes auth add openai-codex`. Для автономного CLI Codex действительная OAuth‑сессия может находиться в `~/.codex/auth.json`; отсутствие только `OPENAI_API_KEY` не считается доказательством отсутствия аутентификации Codex.

## Одноразовые задачи

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

Для работы «на лету» (Codex требует git‑репозиторий):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Фоновый режим (длительные задачи)

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

## Ключевые флаги

| Flag | Effect |
|------|--------|
| `exec "prompt"` | Одноразовое выполнение, завершает работу после выполнения |
| `--full-auto` | Песочница, но автоматически одобряет изменения файлов в рабочей области |
| `--yolo` | Без песочницы, без одобрений (самый быстрый, но самый опасный) |

## Обзор PR‑ов

Клонировать во временный каталог для безопасного обзора:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Параллельное исправление проблем с помощью worktrees

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

## Пакетный обзор PR‑ов

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

1. **Всегда использовать `pty=true`** — Codex — интерактивное терминальное приложение и зависает без PTY
2. **Требуется git‑репозиторий** — Codex не запустится вне git‑каталога. Для «на лету» используйте `mktemp -d && git init`
3. **Для одноразовых задач используйте `exec`** — `codex exec "prompt"` выполняется и корректно завершает работу
4. **`--full-auto` для сборки** — автоматически одобряет изменения внутри песочницы
5. **Фоновый режим для длительных задач** — используйте `background=true` и контролируйте с помощью инструмента `process`
6. **Не вмешиваться** — контролируйте с помощью `poll`/`log`, будьте терпеливы к длительно работающим задачам
7. **Параллельность допустима** — запускайте несколько процессов Codex одновременно для пакетной работы