---
title: "Opencode — Делегировать кодинг OpenCode CLI (фичи, PR‑ревью)"
sidebar_label: "Opencode"
description: "Делегировать кодинг OpenCode CLI (фичи, ревью PR)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Opencode

Делегировать написание кода OpenCode CLI (фичи, ревью PR).

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/autonomous-ai-agents/opencode` |
| Version | `1.2.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Coding-Agent`, `OpenCode`, `Autonomous`, `Refactoring`, `Code-Review` |
| Related skills | [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# OpenCode CLI

Используй [OpenCode](https://opencode.ai) как автономного рабочего кодера, управляемого терминальными/процессными инструментами Hermes. OpenCode — провайдер‑агностичный, открытый AI‑агент для кодинга с TUI и CLI.

## Когда использовать

- Пользователь явно просит использовать OpenCode
- Нужно внешний агент для реализации/рефакторинга/ревью кода
- Требуются длительные сессии кодинга с проверками прогресса
- Нужно параллельное выполнение задач в изолированных workdirs/worktrees

## Предварительные требования

- OpenCode установлен: `npm i -g opencode-ai@latest` или `brew install anomalyco/tap/opencode`
- Настроена аутентификация: `opencode auth login` или заданы переменные окружения провайдера (OPENROUTER_API_KEY и др.)
- Проверка: `opencode auth list` должен показать хотя бы один провайдер
- Git‑репозиторий для задач с кодом (рекомендовано)
- `pty=true` для интерактивных TUI‑сессий

## Разрешение бинарника (Важно)

Среды оболочки могут находить разные бинарники OpenCode. Если поведение отличается между твоим терминалом и Hermes, проверь:

```
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

При необходимости зафиксируй явный путь к бинарнику:

```
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## Одноразовые задачи

Используй `opencode run` для ограниченных, неинтерактивных задач:

```
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Прикрепляй файлы контекста с помощью `-f`:

```
terminal(command="opencode run 'Review this config for security issues' -f config.yaml -f .env.example", workdir="~/project")
```

Показывай рассуждения модели с `--thinking`:

```
terminal(command="opencode run 'Debug why tests fail in CI' --thinking", workdir="~/project")
```

Принудительно укажи конкретную модель:

```
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## Интерактивные сессии (Фоновый режим)

Для итеративной работы, требующей множества обменов, запусти TUI в фоне:

```
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Returns session_id

# Send a prompt
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow and add tests")

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send follow-up input
process(action="submit", session_id="<id>", data="Now add error handling for token expiry")

# Exit cleanly — Ctrl+C
process(action="write", session_id="<id>", data="\x03")
# Or just kill the process
process(action="kill", session_id="<id>")
```

**Важно:** Не используй `/exit` — это невалидная команда OpenCode и откроет диалог выбора агента. Используй Ctrl+C (`\x03`) или `process(action="kill")` для выхода.

### Привязки клавиш TUI

| Клавиша | Действие |
|-----|--------|
| `Enter` | Отправить сообщение (при необходимости нажать дважды) |
| `Tab` | Переключить между агентами (build/plan) |
| `Ctrl+P` | Открыть палитру команд |
| `Ctrl+X L` | Переключить сессию |
| `Ctrl+X M` | Переключить модель |
| `Ctrl+X N` | Новая сессия |
| `Ctrl+X E` | Открыть редактор |
| `Ctrl+C` | Выход из OpenCode |

### Возобновление сессий

После выхода OpenCode выводит ID сессии. Возобнови её с помощью:

```
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # Continue last session
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # Specific session
```

## Общие флаги

| Флаг | Использование |
|------|-----|
| `run 'prompt'` | Одноразное выполнение и выход |
| `--continue` / `-c` | Продолжить последнюю сессию OpenCode |
| `--session <id>` / `-s` | Продолжить конкретную сессию |
| `--agent <name>` | Выбрать агент OpenCode (build или plan) |
| `--model provider/model` | Принудительно задать модель |
| `--format json` | Машиночитаемый вывод/события |
| `--file <path>` / `-f` | Прикрепить файл(ы) к сообщению |
| `--thinking` | Показать блоки рассуждений модели |
| `--variant <level>` | Интенсивность рассуждений (high, max, minimal) |
| `--title <name>` | Задать имя сессии |
| `--attach <url>` | Подключиться к работающему серверу opencode |

## Процедура

1. Проверь готовность инструмента:
   - `terminal(command="opencode --version")`
   - `terminal(command="opencode auth list")`
2. Для ограниченных задач используй `opencode run '...'` (pty не нужен).
3. Для итеративных задач запусти `opencode` с `background=true, pty=true`.
4. Отслеживай длительные задачи через `process(action="poll"|"log")`.
5. Если OpenCode запрашивает ввод, отвечай через `process(action="submit", ...)`.
6. Выходи с помощью `process(action="write", data="\x03")` или `process(action="kill")`.
7. Своди изменения файлов, результаты тестов и дальнейшие шаги обратно пользователю.

## Рабочий процесс ревью PR

OpenCode имеет встроенную команду PR:

```
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Или ревью в временном клоне для изоляции:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main. Report bugs, security risks, test gaps, and style issues.' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## Параллельный рабочий паттерн

Используй отдельные workdirs/worktrees, чтобы избежать конфликтов:

```
terminal(command="opencode run 'Fix issue #101 and commit'", workdir="/tmp/issue-101", background=true, pty=true)
terminal(command="opencode run 'Add parser regression tests and commit'", workdir="/tmp/issue-102", background=true, pty=true)
process(action="list")
```

## Управление сессиями и затратами

Список прошлых сессий:

```
terminal(command="opencode session list")
```

Проверка использования токенов и затрат:

```
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

## Подводные камни

- Интерактивные сессии `opencode` (TUI) требуют `pty=true`. Команда `opencode run` **не** нуждается в pty.
- `/exit` НЕ является валидной командой — она открывает селектор агента. Для выхода из TUI используй Ctrl+C.
- Несоответствие PATH может привести к выбору неправильного бинарника OpenCode/конфигурации модели.
- Если OpenCode «завис», проверь логи перед убийством процесса:
  - `process(action="log", session_id="<id>")`
- Избегай совместного использования одного рабочего каталога между параллельными сессиями OpenCode.
- В TUI может потребоваться два нажатия Enter для отправки (одно — завершить ввод, второе — отправить).

## Верификация

Smoke‑тест:

```
terminal(command="opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'")
```

Критерии успеха:
- Вывод содержит `OPENCODE_SMOKE_OK`
- Команда завершается без ошибок провайдера/модели
- Для задач с кодом: ожидаемые файлы изменены и тесты проходят

## Правила

1. Предпочитай `opencode run` для одноразовой автоматизации — это проще и не требует pty.
2. Используй интерактивный фоновый режим только когда нужна итерация.
3. Всегда ограничивай сессии OpenCode одним репозиторием/рабочим каталогом.
4. Для длительных задач предоставляй обновления прогресса из логов `process`.
5. Сообщай конкретные результаты (изменённые файлы, тесты, оставшиеся риски).
6. Выходи из интерактивных сессий через Ctrl+C или kill, никогда через `/exit`.