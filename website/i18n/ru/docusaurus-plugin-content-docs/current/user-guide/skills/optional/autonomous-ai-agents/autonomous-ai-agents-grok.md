---
title: "Grok — Делегировать кодирование xAI Grok Build CLI (фичи, PRs)"
sidebar_label: "Grok"
description: "Делегировать кодирование xAI Grok Build CLI (features, PRs)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Grok

Делегировать написание кода xAI Grok Build CLI (фичи, PR‑ы).
## Метаданные навыка

| | |
|---|---|
| **Источник** | Optional — install with `hermes skills install official/autonomous-ai-agents/grok` |
| **Путь** | `optional-skills/autonomous-ai-agents/grok` |
| **Версия** | `0.1.0` |
| **Автор** | Matt Maximo (MattMaximo), Hermes Agent |
| **Лицензия** | MIT |
| **Платформы** | linux, macos, windows |
| **Теги** | `Coding-Agent`, `Grok`, `xAI`, `Code-Review`, `Refactoring`, `Automation` |
| **Связанные навыки** | [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |
:::info
Следующее — полное определение навыка, которое Hermes загружает при его срабатывании. Это то, что агент видит как инструкции, когда навык активен.
:::

# Grok Build CLI — Руководство по оркестрации Hermes

Делегируй задачи кодирования [Grok Build](https://docs.x.ai/build/overview) (автономный агент кодирования CLI от xAI, команда `grok`) через терминал Hermes. Grok умеет читать файлы, писать код, выполнять shell‑команды, порождать подагенты и управлять git‑рабочими процессами. Он запускается тремя способами: интерактивный TUI, **headless** (`-p`) и как **ACP‑агент** по JSON‑RPC.

Это третий «брат» для `codex` и `claude-code`. Паттерн оркестрации почти идентичен — **предпочитай headless `-p` для одноразовых запусков**, используй PTY для интерактивных сессий.
## Когда использовать

- Разработка функций
- Рефакторинг
- Обзор PR
- Массовое исправление проблем
- Любая задача, для которой ты обычно использовал бы Codex / Claude Code, но хочешь использовать Grok
## Предварительные требования

- **Установка (рекомендовано):** `npm install -g @xai-official/grok`
  - Официальный установщик `curl -fsSL https://x.ai/cli/install.sh | bash` тоже работает, но хост `x.ai` защищён Cloudflare в некоторых окружениях. Путь npm полностью избавляет от этой зависимости.
- **Авторизация — подписка SuperGrok / X Premium+ (основной путь):**
  - Выполни `grok login` один раз → откроется браузер для OAuth → токен кэшируется в `~/.grok/auth.json`. Это использует твою подписку **SuperGrok или X Premium+** (без отдельного биллинга за токен API).
  - Проверь состояние входа, посмотрев наличие `~/.grok/auth.json`, или запусти недорогой безголовый smoke‑test: `grok --no-auto-update -p "Say ok."`
  - В TUI команда `/logout` выходит из системы, а `/login` (или перезапуск) снова входит.
- **Git‑репозиторий не требуется** — в отличие от Codex, Grok работает без git‑каталога (удобно для одноразовых задач).
- **Совместимость с Claude Code / AGENTS.md без конфигурации** — Grok автоматически читает `CLAUDE.md`, `.claude/` (skills, agents, MCPs, hooks, rules) и семейство `AGENTS.md`. Существующий контекст проекта просто работает.

> **Запасной вариант API‑ключа (не используется по умолчанию для этого пользователя):** Grok также поддерживает установку переменной окружения `XAI_API_KEY` для оплаты по мере использования через `api.x.ai`. Используй её только если `grok login` / авторизация SuperGrok недоступны. Путь через подписку (`grok login`) является предполагаемым способом настройки.
## Два режима оркестрации

### Режим 1: Headless (`-p`) — Неинтерактивный (РЕКОМЕНДУЕМО)

Запускает однократную задачу, выводит результат и завершает работу. Нет PTY, нет интерактивных диалогов для навигации. Это самый чистый путь интеграции — аналог `claude -p` и `codex exec`.

```
terminal(command="grok --no-auto-update -p 'Add a dark mode toggle to settings'", workdir="/path/to/project", timeout=180)
```

Всегда передавай `--no-auto-update` в автоматизации, чтобы пропустить проверки фоновых обновлений.

**Когда использовать headless:**
- Однократные задачи программирования (исправление бага, добавление функции, рефакторинг)
- Автоматизация CI/CD и скрипты
- Структурный разбор вывода с `--output-format json`
- Любая задача, не требующая многократного диалога

### Режим 2: Interactive PTY — Многократные TUI‑сессии

TUI — это полноэкранное приложение с поддержкой мыши. Включай его с `pty=true`. Для надёжного мониторинга/ввода используй tmux (тот же шаблон, что и в навыке `claude-code`).

```
# Launch in a tmux session for capture-pane monitoring
terminal(command="tmux new-session -d -s grok-work -x 140 -y 40")
terminal(command="tmux send-keys -t grok-work 'cd /path/to/project && grok' Enter")

# Wait for startup, then send a task
terminal(command="sleep 5 && tmux send-keys -t grok-work 'Refactor the auth module to use JWT' Enter")

# Monitor progress
terminal(command="sleep 15 && tmux capture-pane -t grok-work -p -S -50")

# Exit when done
terminal(command="tmux send-keys -t grok-work '/quit' Enter && sleep 1 && tmux kill-session -t grok-work")
```

**Подсказка для headless‑output в строке:** если нужен вывод в стиле TUI без захвата полноэкранного альтернативного экрана (например, для более чистых логов), добавь `--no-alt-screen`. Для чистой автоматизации headless `-p` всё равно предпочтительнее, чем TUI.
## Headless Deep Dive

### Общие флаги

| Флаг | Эффект |
|------|--------|
| `-p, --single <PROMPT>` | Отправить один запрос, запустить в headless‑режим, выйти |
| `-m, --model <MODEL>` | Выбрать модель |
| `-s, --session-id <ID>` | Создать или возобновить именованную headless‑сессию |
| `-r, --resume <ID>` | Возобновить существующую сессию |
| `-c, --continue` | Продолжить последнюю сессию в текущем каталоге |
| `--cwd <PATH>` | Установить рабочий каталог |
| `--output-format <FMT>` | `plain` (по умолчанию), `json` или `streaming-json` |
| `--always-approve` | Автоодобрять все выполнения инструментов (эквивалент `--full-auto` / `--yolo`) |
| `--no-alt-screen` | Запускать inline, без захвата полноэкранного TUI |
| `--no-auto-update` | Пропустить проверку фоновых обновлений (использовать во всей автоматизации) |

### Форматы вывода

- `plain` — читаемый человеком текст (по умолчанию)
- `json` — один объект JSON в конце выполнения (чистый парсинг результата)
- `streaming-json` — события JSON, разделённые переводами строки, по мере поступления

```
# Structured result for parsing
terminal(command="grok --no-auto-update -p 'List all TODO comments in src/' --output-format json", workdir="/project", timeout=120)

# Auto-approve for autonomous building
terminal(command="grok --no-auto-update --always-approve -p 'Refactor the database layer and run the tests'", workdir="/project", timeout=300)
```

### Фоновый режим (длительные задачи)

```
# Start headless in background
terminal(command="grok --no-auto-update --always-approve -p 'Refactor the auth module'", workdir="/project", background=true, notify_on_complete=true)
# Returns session_id

# Monitor
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Kill if needed
process(action="kill", session_id="<id>")
```

Для интерактивной (TUI) фоновой сессии используйте `pty=true` + tmux и наблюдайте с помощью `tmux capture-pane`, точно так же, как в навыках `claude-code` / `codex`.

### Продолжение сессии

```
# Start a named session
terminal(command="grok --no-auto-update -s refactor-db -p 'Start refactoring the database layer' --always-approve", workdir="/project", timeout=240)

# Resume it later
terminal(command="grok --no-auto-update -r refactor-db -p 'Now add connection pooling' --always-approve", workdir="/project", timeout=180)

# Or continue the most recent session in this directory
terminal(command="grok --no-auto-update -c -p 'What did you change last time?'", workdir="/project", timeout=60)
```
## Read‑Only Audit → Шаблон заметки Markdown

Чтобы Grok проверил локальные артефакты и вернул чистую заметку в формате markdown (для Obsidian или репозитория) без изменения чего‑либо:

1. Сначала подготовь стабильные входные файлы с помощью инструментов Hermes (`read_file`, `write_file`). Снимай снимок только релевантного контекста во временный файл, а не выгружай сырые пути.
2. Запусти Grok в headless‑режиме **без** `--always-approve`, чтобы он не мог автоматически писать, и требуй `markdown only, no preamble`.
3. Сохрани stdout Grok напрямую в целевую заметку с помощью `write_file()`.

```
grok --no-auto-update -p "Read /tmp/current.md and /tmp/inventory.md. Produce markdown only, no preamble. Output a clean note titled 'Cleanup Review'." --output-format plain
```

**Подводный камень (как у Claude Code):** для переписывания документов свободный запрос «rewrite this» может вернуть лишь сводку изменений вместо полного файла. Вместо этого передай файл во входной поток и требуй `Return ONLY the full revised markdown document. No intro, no explanation, no code fences. Start immediately with '# Title'.` Проверь первые строки с помощью `read_file()` перед тем, как перезаписать назначение.
## Шаблоны обзора PR

### Быстрый обзор (headless)

```
terminal(command="cd /path/to/repo && git diff main...feature-branch | grok --no-auto-update -p 'Review this diff for bugs, security issues, and style problems. Be thorough.'", timeout=120)
```

### Обзор с клонированием во временный каталог (безопасно, без изменения репозитория)

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && grok --no-auto-update -p 'Review the changes vs origin/main. Check bugs, security, race conditions, missing tests.'", pty=true, timeout=300)
```

### Опубликовать обзор

```
terminal(command="gh pr comment 42 --body '<review text>'", workdir="/path/to/repo")
```
## Параллельное исправление проблем с помощью worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Grok headless in each (background)
terminal(command="grok --no-auto-update --always-approve -p 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, notify_on_complete=true)
terminal(command="grok --no-auto-update --always-approve -p 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, notify_on_complete=true)

# Monitor
process(action="list")

# After completion: push and open PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```
## Полезные подкоманды и команды TUI

| Команда | Назначение |
|---------|------------|
| `grok` | Запустить интерактивный TUI |
| `grok -p "query"` | Однократный запуск без интерфейса |
| `grok login` / `grok logout` | Войти / выйти (SuperGrok / X Premium+ OAuth) |
| `grok inspect` | Показать, что Grok обнаружил в текущей директории: источники конфигурации, инструкции, skills, плагины, хуки, MCP‑серверы |
| `grok agent stdio` | Запустить как ACP‑agent через JSON‑RPC (для интеграции с IDE/инструментами) |
| `grok update` | Обновить CLI (требуется хост `x.ai`; пропустить в автоматизации) |

Команды‑слеш в TUI (только в интерактивном режиме): `/model <name>`, `/always-approve`, `/plan`, `/context`, `/compact`, `/resume`, `/sessions`, `/fork`, `/usage`, `/quit`. `Shift+Tab` переключает режимы сессии (включая режим План, который блокирует инструменты записи, кроме файла плана сессии).
## Конфигурация (`~/.grok/config.toml`)

```toml
[cli]
auto_update = false          # skip background update checks persistently

[ui]
permission_mode = "ask"      # or "always-approve" to skip tool prompts by default

[models]
default = "grok-build-0.1"
```

Размести глобальные настройки в `~/.grok/config.toml` (а не в файл проекта
`.grok/config.toml`). Ключ `permission_mode` заменяет устаревшие ключи `approval_mode` /
`yolo = true`.
## Подводные камни и нюансы

1. **Авторизация доступна только по подписке.** `grok login` требует подписку SuperGrok или X Premium+. Если вход не удался или отсутствует `~/.grok/auth.json`, убедись, что подписка активна, прежде чем переходить к `XAI_API_KEY`.
2. **Не путай аутентификацию xAI Hermes с аутентификацией CLI `grok`.** `x_search` Hermes использует собственный OAuth xAI; отдельный CLI `grok` хранит токен в `~/.grok/auth.json`. Рабочий `x_search` НЕ означает, что `grok` вошёл в систему.
3. **Всегда передавай `--no-auto-update` в автоматизации** — иначе Grok будет проверять обновления (и `x.ai`/`storage.googleapis.com` могут быть недоступны).
4. **Отдавай предпочтение установке через npm вместо curl‑инсталлятора** — `npm install -g @xai-official/grok` избегает хоста `x.ai`, защищённого Cloudflare.
5. **`--always-approve` — переключатель автономной сборки.** Без него безголовые запуски могут зависать, ожидая подтверждения инструментов. Отключай его намеренно для работы только с чтением/аудита, чтобы Grok не мог изменять файлы.
6. **Безголовый `-p` пропускает диалоги TUI**; TUI требует `pty=true` (+ tmux для мониторинга), как в Claude Code.
7. **Используй `--no-alt-screen`**, если запускаешь TUI встроенно и полноэкранный режим alt‑screen искажает захваченный вывод.
8. **Git‑репозиторий не обязателен**, но для рабочих процессов с PR/коммитами он всё же нужен — используй `mktemp -d && git init` для временных задач коммита.
9. **Очисти сеансы tmux** с помощью `tmux kill-session -t <name>` после завершения.
## Правила для Hermes Agents

1. **Отдавай предпочтение безголовому `-p`** для одиночных задач — самая чистая интеграция, структурированный вывод через `--output-format json`.
2. **Всегда указывай `workdir`** (или `--cwd`), чтобы Grok ориентировался на правильный проект.
3. **Передавай `--no-auto-update`** при каждом автоматическом вызове.
4. **Используй `--always-approve` только когда Grok должен писать автономно**; опускай его для обзоров и аудитов в режиме только чтения.
5. **Фоновые длительные задачи** задавай через `background=true, notify_on_complete=true` и отслеживай их с помощью инструмента `process`.
6. **Применяй tmux для многошаговой интерактивной работы** и контролируй её с помощью `tmux capture-pane -t <session> -p -S -50`.
7. **Проверяй аутентификацию перед её использованием** — проверяй `~/.grok/auth.json` или запускай недорогой smoke‑test `grok -p "Say ok."`; не полагайся на то, что аутентификация xAI от Hermes сохраняется.
8. **Отчитывайся перед пользователем** — подводи итог тому, что изменил Grok и что осталось.