---
title: "Blackbox — Делегуй завдання кодування Blackbox AI CLI агенту"
sidebar_label: "Blackbox"
description: "Делегуй завдання з кодування Blackbox AI CLI агенту"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Blackbox

Делегуй завдання кодування Blackbox AI CLI агенту. Багатомодельний агент із вбудованим суддею, який виконує завдання через кілька LLM і обирає найкращий результат. Потрібен CLI Blackbox та API‑ключ Blackbox AI.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Blackbox CLI

Делегуй завдання кодування [Blackbox AI](https://www.blackbox.ai/) через термінал Hermes. Blackbox — це багатомодельний CLI‑агент кодування, який розподіляє завдання між кількома LLM (Claude, Codex, Gemini, Blackbox Pro) і використовує суддю для вибору найкращої реалізації.

CLI є [open-source](https://github.com/blackboxaicode/cli) (GPL-3.0, TypeScript, форк Gemini CLI) і підтримує інтерактивні сесії, неінтерактивні одноразові запити, контрольні точки, MCP та перемикання візуальних моделей.

## Передумови

- Node.js 20+ встановлений
- CLI Blackbox встановлений: `npm install -g @blackboxai/cli`
- Або встанови з вихідного коду:
  ```
  git clone https://github.com/blackboxaicode/cli.git
  cd cli && npm install && npm install -g .
  ```
- API‑ключ з [app.blackbox.ai/dashboard](https://app.blackbox.ai/dashboard)
- Налаштовано: виконай `blackbox configure` і введи свій API‑ключ
- Використовуй `pty=true` у викликах терміналу — Blackbox CLI є інтерактивним термінальним застосунком

## Одноразові завдання

```
terminal(command="blackbox --prompt 'Add JWT authentication with refresh tokens to the Express API'", workdir="/path/to/project", pty=true)
```

Для швидкої нотатки:
```
terminal(command="cd $(mktemp -d) && git init && blackbox --prompt 'Build a REST API for todos with SQLite'", pty=true)
```

## Фоновий режим (довгі завдання)

Для завдань, що тривають кілька хвилин, використай фоновий режим, щоб можна було стежити за прогресом:

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

## Контрольні точки та відновлення

CLI Blackbox має вбудовану підтримку контрольних точок для паузи та відновлення завдань:

```
# After a task completes, Blackbox shows a checkpoint tag
# Resume with a follow-up task:
terminal(command="blackbox --resume-checkpoint 'task-abc123-2026-03-06' --prompt 'Now add rate limiting to the endpoints'", workdir="~/project", pty=true)
```

## Команди сесії

Під час інтерактивної сесії використай ці команди:

| Command | Effect |
|---------|--------|
| `/compress` | Стискає історію розмови, щоб заощадити токени |
| `/clear` | Очищає історію та починає заново |
| `/stats` | Показує поточне використання токенів |
| `Ctrl+C` | Скасовує поточну операцію |

## Огляд PR

Клонуй у тимчасову директорію, щоб не змінювати робоче дерево:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && blackbox --prompt 'Review this PR against main. Check for bugs, security issues, and code quality.'", pty=true)
```

## Паралельна робота

Запусти кілька інстанцій Blackbox для незалежних завдань:

```
terminal(command="blackbox --prompt 'Fix the login bug'", workdir="/tmp/issue-1", background=true, pty=true)
terminal(command="blackbox --prompt 'Add unit tests for auth'", workdir="/tmp/issue-2", background=true, pty=true)

# Monitor all
process(action="list")
```

## Багатомодельний режим

Унікальна особливість Blackbox — виконання того самого завдання через кілька моделей і оцінка результатів. Налаштуй, які моделі використовувати, за допомогою `blackbox configure` — обери кілька провайдерів, щоб увімкнути workflow Chairman/judge, де CLI оцінює вихідні дані різних моделей і обирає найкращу.

## Ключові прапорці

| Flag | Effect |
|------|--------|
| `--prompt "task"` | Неінтерактивне одноразове виконання |
| `--resume-checkpoint "tag"` | Відновити з збереженої контрольної точки |
| `--yolo` | Автоматично схвалювати всі дії та перемикання моделей |
| `blackbox session` | Запустити інтерактивну чат‑сесію |
| `blackbox configure` | Змінити налаштування, провайдери, моделі |
| `blackbox info` | Показати системну інформацію |

## Підтримка візуального режиму

Blackbox автоматично виявляє зображення у вхідних даних і може переключатися на мультимодальний аналіз. Режими VLM:
- `"once"` — Перемкнути модель лише для поточного запиту
- `"session"` — Перемкнути на всю сесію
- `"persist"` — Залишитися на поточній моделі (без перемикання)

## Ліміти токенів

Керуйте використанням токенів через `.blackboxcli/settings.json`:
```json
{
  "sessionTokenLimit": 32000
}
```

## Правила

1. **Завжди використовуй `pty=true`** — CLI Blackbox є інтерактивним термінальним застосунком і зависне без PTY
2. **Використовуй `workdir`** — тримай агента у правильному каталозі
3. **Фоновий режим для довгих завдань** — використай `background=true` і стеж за процесом за допомогою інструмента `process`
4. **Не втручайся** — стеж за процесом за допомогою `poll`/`log`, не завершуй сесії, бо вони повільні
5. **Повідомляй результати** — після завершення перевір, що змінилося, і підсумуй для користувача
6. **Кредити коштують грошей** — Blackbox працює за кредитною системою; багатомодельний режим споживає кредити швидше
7. **Перевір передумови** — переконайся, що CLI `blackbox` встановлений перед спробою делегування