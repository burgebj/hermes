---
title: "Blackbox — Делегировать задачи кодирования Blackbox AI CLI агенту"
sidebar_label: "Blackbox"
description: "Делегировать задачи кодирования агенту Blackbox AI CLI"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Blackbox

Делегируй задачи кодирования агенту Blackbox AI CLI. Мульти‑модельный агент со встроенным судейским механизмом, который запускает задачи через несколько LLM и выбирает лучший результат. Требуется CLI Blackbox и API‑ключ Blackbox AI.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/autonomous-ai-agents/blackbox` |
| Path | `optional-skills/autonomous-ai-agents/blackbox` |
| Version | `1.0.0` |
| Author | Hermes Agent (Nous Research) |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Coding-Agent`, `Blackbox`, `Multi-Agent`, `Judge`, `Multi-Model` |
| Related skills | [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Reference: full SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при работе навыка.
:::

# Blackbox CLI

Делегируй задачи кодирования в [Blackbox AI](https://www.blackbox.ai/) через терминал Hermes. Blackbox — это мульти‑модельный CLI‑агент кодирования, который распределяет задачи между несколькими LLM (Claude, Codex, Gemini, Blackbox Pro) и использует судью для выбора лучшей реализации.

CLI является [open-source](https://github.com/blackboxaicode/cli) (GPL‑3.0, TypeScript, форк Gemini CLI) и поддерживает интерактивные сессии, неинтерактивные одноразовые запросы, контрольные точки, MCP и переключение моделей зрения.

## Prerequisites

- Node.js 20+ установлен
- CLI Blackbox установлен: `npm install -g @blackboxai/cli`
- Или установить из исходников:
  ```
  git clone https://github.com/blackboxaicode/cli.git
  cd cli && npm install && npm install -g .
  ```
- API‑ключ из [app.blackbox.ai/dashboard](https://app.blackbox.ai/dashboard)
- Настроено: выполните `blackbox configure` и введите ваш API‑ключ
- Используйте `pty=true` в вызовах терминала — Blackbox CLI — интерактивное терминальное приложение

## One-Shot Tasks

```
terminal(command="blackbox --prompt 'Add JWT authentication with refresh tokens to the Express API'", workdir="/path/to/project", pty=true)
```

Для быстрой «черновой» работы:
```
terminal(command="cd $(mktemp -d) && git init && blackbox --prompt 'Build a REST API for todos with SQLite'", pty=true)
```

## Background Mode (Long Tasks)

Для задач, которые занимают минуты, используйте фоновый режим, чтобы можно было отслеживать прогресс:

```
# Start in background with PTY
terminal(command="blackbox --prompt 'Refactor the auth module to use OAuth 2.0'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Blackbox asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Checkpoints & Resume

CLI Blackbox имеет встроенную поддержку контрольных точек для паузы и возобновления задач:

```
# After a task completes, Blackbox shows a checkpoint tag
# Resume with a follow-up task:
terminal(command="blackbox --resume-checkpoint 'task-abc123-2026-03-06' --prompt 'Now add rate limiting to the endpoints'", workdir="~/project", pty=true)
```

## Session Commands

Во время интерактивной сессии используйте эти команды:

| Command | Effect |
|---------|--------|
| `/compress` | Сократить историю разговора, чтобы сэкономить токены |
| `/clear` | Очистить историю и начать заново |
| `/stats` | Просмотреть текущий расход токенов |
| `Ctrl+C` | Отменить текущую операцию |

## PR Reviews

Клонируйте в временный каталог, чтобы не изменять рабочее дерево:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && blackbox --prompt 'Review this PR against main. Check for bugs, security issues, and code quality.'", pty=true)
```

## Parallel Work

Запускайте несколько экземпляров Blackbox для независимых задач:

```
terminal(command="blackbox --prompt 'Fix the login bug'", workdir="/tmp/issue-1", background=true, pty=true)
terminal(command="blackbox --prompt 'Add unit tests for auth'", workdir="/tmp/issue-2", background=true, pty=true)

# Monitor all
process(action="list")
```

## Multi-Model Mode

Уникальная особенность Blackbox — выполнение одной и той же задачи через несколько моделей и оценка результатов. Настройте, какие модели использовать, через `blackbox configure` — выберите несколько провайдеров, чтобы включить workflow Chairman/judge, где CLI оценивает выводы разных моделей и выбирает лучший.

## Key Flags

| Flag | Effect |
|------|--------|
| `--prompt "task"` | Неинтерактивный одноразовый запуск |
| `--resume-checkpoint "tag"` | Возобновить из сохранённой контрольной точки |
| `--yolo` | Автоматически одобрять все действия и переключения моделей |
| `blackbox session` | Запустить интерактивную чат‑сессию |
| `blackbox configure` | Изменить настройки, провайдеры, модели |
| `blackbox info` | Показать информацию о системе |

## Vision Support

Blackbox автоматически обнаруживает изображения во входных данных и может переключаться на мультимодальный анализ. Режимы VLM:
- `"once"` — переключить модель только для текущего запроса
- `"session"` — переключить модель на всю сессию
- `"persist"` — оставаться на текущей модели (без переключения)

## Token Limits

Контролируйте расход токенов через `.blackboxcli/settings.json`:
```json
{
  "sessionTokenLimit": 32000
}
```

## Rules

1. **Always use `pty=true`** — Blackbox CLI — интерактивное терминальное приложение и зависнет без PTY
2. **Use `workdir`** — держи агента сфокусированным на нужной директории
3. **Background for long tasks** — используй `background=true` и отслеживай с помощью инструмента `process`
4. **Don't interfere** — мониторь с помощью `poll`/`log`, не убивай сессии, потому что они медленные
5. **Report results** — после завершения проверь, что изменилось, и подведи итог пользователю
6. **Credits cost money** — Blackbox использует кредитную систему; мульти‑модельный режим расходует кредиты быстрее
7. **Check prerequisites** — убедись, что CLI `blackbox` установлен перед попыткой делегировать задачу