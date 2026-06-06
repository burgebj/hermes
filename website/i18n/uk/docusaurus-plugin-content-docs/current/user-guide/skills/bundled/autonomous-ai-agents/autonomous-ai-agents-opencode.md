---
title: "Opencode — Делегуй кодування до OpenCode CLI (features, PR review)"
sidebar_label: "Opencode"
description: "делегуй кодування OpenCode CLI (фічі, перегляд PR)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Opencode

Делегуй кодування OpenCode CLI (фічі, PR‑ревью).

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# OpenCode CLI

Використовуй [OpenCode](https://opencode.ai) як автономного кодувального робітника, оркестрованого інструментами терміналу/процесами Hermes. OpenCode — це провайдер‑агностичний, open‑source AI‑кодувальний агент з TUI та CLI.

## Коли використовувати

- Користувач явно просить використати OpenCode
- Потрібен зовнішній кодувальний агент для реалізації/рефакторингу/рев’ю коду
- Потрібні довгі кодувальні сесії з перевірками прогресу
- Потрібне паралельне виконання завдань в ізольованих workdirs/worktrees

## Попередні вимоги

- OpenCode встановлений: `npm i -g opencode-ai@latest` або `brew install anomalyco/tap/opencode`
- Налаштована автентифікація: `opencode auth login` або встановлені змінні середовища провайдера (OPENROUTER_API_KEY тощо)
- Перевірка: `opencode auth list` має показати принаймні один провайдер
- Git‑репозиторій для кодових завдань (рекомендовано)
- `pty=true` для інтерактивних TUI‑сесій

## Розв’язання бінарника (Important)

Shell‑оточення можуть підбирати різні бінарники OpenCode. Якщо поведінка відрізняється між твоїм терміналом і Hermes, перевір:

```
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

За потреби зафіксуй явний шлях до бінарника:

```
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## Одноразові завдання

Використовуй `opencode run` для обмежених, неінтерактивних завдань:

```
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Прикріпи файли контексту за допомогою `-f`:

```
terminal(command="opencode run 'Review this config for security issues' -f config.yaml -f .env.example", workdir="~/project")
```

Показати мислення моделі за допомогою `--thinking`:

```
terminal(command="opencode run 'Debug why tests fail in CI' --thinking", workdir="~/project")
```

Примусово вказати конкретну модель:

```
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## Інтерактивні сесії (Background)

Для ітеративної роботи, що вимагає кількох обмінів, запусти TUI у фоні:

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

**Important:** Не використовуйте `/exit` — це не дійсна команда OpenCode і відкриє діалог вибору агента. Використовуйте Ctrl+C (`\x03`) або `process(action="kill")` для виходу.

### Клавіші TUI

| Key | Action |
|-----|--------|
| `Enter` | Надіслати повідомлення (за потреби натиснути двічі) |
| `Tab` | Перемикання між агентами (build/plan) |
| `Ctrl+P` | Відкрити палітру команд |
| `Ctrl+X L` | Перемкнути сесію |
| `Ctrl+X M` | Перемкнути модель |
| `Ctrl+X N` | Нова сесія |
| `Ctrl+X E` | Відкрити редактор |
| `Ctrl+C` | Вийти з OpenCode |

### Відновлення сесій

Після виходу OpenCode виводить ID сесії. Віднови її за допомогою:

```
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # Continue last session
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # Specific session
```

## Поширені прапорці

| Flag | Use |
|------|-----|
| `run 'prompt'` | Одноразове виконання та вихід |
| `--continue` / `-c` | Продовжити останню сесію OpenCode |
| `--session <id>` / `-s` | Продовжити конкретну сесію |
| `--agent <name>` | Вибрати агента OpenCode (build або plan) |
| `--model provider/model` | Примусово вказати модель |
| `--format json` | Машинозчитуваний вивід/події |
| `--file <path>` / `-f` | Прикріпити файл(и) до повідомлення |
| `--thinking` | Показати блоки мислення моделі |
| `--variant <level>` | Рівень роздумів (high, max, minimal) |
| `--title <name>` | Назвати сесію |
| `--attach <url>` | Підключитися до запущеного сервера opencode |

## Процедура

1. Перевір готовність інструмента:
   - `terminal(command="opencode --version")`
   - `terminal(command="opencode auth list")`
2. Для обмежених завдань використай `opencode run '...'` (pty не потрібен).
3. Для ітеративних завдань запусти `opencode` з `background=true, pty=true`.
4. Моніторинг довгих завдань за допомогою `process(action="poll"|"log")`.
5. Якщо OpenCode запитує ввід, відповідай через `process(action="submit", ...)`.
6. Вихід за допомогою `process(action="write", data="\x03")` або `process(action="kill")`.
7. Підбивай підсумки змін файлів, результатів тестів та наступних кроків користувачу.

## Робочий процес PR‑ревью

OpenCode має вбудовану команду PR:

```
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Або рев’ю в тимчасовому клонах для ізоляції:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main. Report bugs, security risks, test gaps, and style issues.' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## Паралельний шаблон роботи

Використовуй окремі workdirs/worktrees, щоб уникнути колізій:

```
terminal(command="opencode run 'Fix issue #101 and commit'", workdir="/tmp/issue-101", background=true, pty=true)
terminal(command="opencode run 'Add parser regression tests and commit'", workdir="/tmp/issue-102", background=true, pty=true)
process(action="list")
```

## Управління сесіями та витратами

Список минулих сесій:

```
terminal(command="opencode session list")
```

Перевірка використання токенів та витрат:

```
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

## Підводні камені

- Інтерактивні сесії `opencode` (TUI) потребують `pty=true`. Команда `opencode run` pty не потребує.
- `/exit` НЕ є дійсною командою — вона відкриває селектор агента. Використовуй Ctrl+C для виходу з TUI.
- Невідповідність PATH може вибрати неправильний бінарник/конфіг моделі OpenCode.
- Якщо OpenCode здається «завислим», переглянь логи перед вбивством процесу:
  - `process(action="log", session_id="<id>")`
- Уникай спільного використання одного робочого каталогу між паралельними сесіями OpenCode.
- У TUI може знадобитися двічі натиснути Enter, щоб відправити (один раз — завершити текст, другий — надіслати).

## Верифікація

Smoke‑тест:

```
terminal(command="opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'")
```

Критерії успіху:
- Вивід містить `OPENCODE_SMOKE_OK`
- Команда завершується без помилок провайдера/моделі
- Для кодових завдань: очікувані файли змінені і тести проходять

## Правила

1. Віддавай перевагу `opencode run` для одноразової автоматизації — це простіше і не потребує pty.
2. Використовуй інтерактивний режим у фоні лише коли потрібна ітерація.
3. Завжди обмежуй сесії OpenCode одним репозиторієм/workdir.
4. Для довгих завдань надавай оновлення прогресу з логів `process`.
5. Повідомляй конкретні результати (змінені файли, тести, залишкові ризики).
6. Виходь з інтерактивних сесій за допомогою Ctrl+C або kill, ніколи не використовуючи `/exit`.