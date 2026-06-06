---
title: "Claude Code — Делегировать кодирование Claude Code CLI (features, PRs)"
sidebar_label: "Claude Code"
description: "Делегировать кодинг Claude Code CLI (features, PRs)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Claude Code

Делегировать написание кода Claude Code CLI (фичи, PR).
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/autonomous-ai-agents/claude-code` |
| Версия | `2.2.0` |
| Автор | Hermes Agent + Teknium |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `Coding-Agent`, `Claude`, `Anthropic`, `Code-Review`, `Refactoring`, `PTY`, `Automation` |
| Связанные навыки | [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent), [`opencode`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-opencode) |
:::info
Следующий текст — полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Claude Code — Руководство по оркестрации Hermes

Делегируй задачи программирования [Claude Code](https://code.claude.com/docs/en/cli-reference) (автономный CLI‑агент по кодированию от Anthropic) через терминал Hermes. Claude Code v2.x умеет читать файлы, писать код, выполнять команды оболочки, создавать субагенты и самостоятельно управлять git‑рабочими процессами.
## Предварительные требования

- **Установка:** `npm install -g @anthropic-ai/claude-code`
- **Авторизация:** запусти `claude` один раз для входа (браузерный OAuth для Pro/Max или задай переменную `ANTHROPIC_API_KEY`)
- **Консольная авторизация:** `claude auth login --console` — для биллинга по API‑ключу
- **SSO‑авторизация:** `claude auth login --sso` — для Enterprise
- **Проверка статуса:** `claude auth status` (JSON) или `claude auth status --text` (читаемый человеком)
- **Проверка работоспособности:** `claude doctor` — проверяет автообновление и состояние установки
- **Проверка версии:** `claude --version` — требуется версия 2.x и выше
- **Обновление:** `claude update` или `claude upgrade`
## Два режима оркестрации

Hermes взаимодействует с Claude Code двумя принципиально разными способами. Выбирай в зависимости от задачи.

### Режим 1: Print Mode (`-p`) — Неинтерактивный (ПРЕДПОЧТИТЕЛЬНО для большинства задач)

Print Mode выполняет одноразовую задачу, возвращает результат и завершает работу. PTY не требуется. Нет интерактивных запросов. Это самый чистый путь интеграции.

```
terminal(command="claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10", workdir="/path/to/project", timeout=120)
```

**Когда использовать Print Mode:**
- Одноразовые задачи кодинга (исправление бага, добавление функции, рефакторинг)
- Автоматизация CI/CD и скрипты
- Извлечение структурированных данных с `--json-schema`
- Обработка входных данных через конвейер (`cat file | claude -p "analyze this"`)
- Любая задача, где не требуется многотуровый диалог

**Print Mode пропускает ВСЕ интерактивные диалоги** — нет запроса доверия к рабочему пространству, нет подтверждений разрешений. Это делает его идеальным для автоматизации.

### Режим 2: Interactive PTY через tmux — Многотуровые сессии

Interactive Mode предоставляет полноценный разговорный REPL, где можно отправлять последующие подсказки, использовать слеш‑команды и наблюдать за работой Claude в реальном времени. **Требуется оркестрация tmux.**

```
# Start a tmux session
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")

# Launch Claude Code inside it
terminal(command="tmux send-keys -t claude-work 'cd /path/to/project && claude' Enter")

# Wait for startup, then send your task
# (after ~3-5 seconds for the welcome screen)
terminal(command="sleep 5 && tmux send-keys -t claude-work 'Refactor the auth module to use JWT tokens' Enter")

# Monitor progress by capturing the pane
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -50")

# Send follow-up tasks
terminal(command="tmux send-keys -t claude-work 'Now add unit tests for the new JWT code' Enter")

# Exit when done
terminal(command="tmux send-keys -t claude-work '/exit' Enter")
```

**Когда использовать интерактивный режим:**
- Многотуровая итеративная работа (рефакторинг → ревью → исправление → цикл тестов)
- Задачи, требующие участия человека в процессе принятия решений
- Исследовательские сессии кодинга
- Когда необходимо использовать слеш‑команды Claude (`/compact`, `/review`, `/model`)
## Обработка диалогов PTY (КРИТИЧНО для интерактивного режима)

Claude Code показывает до двух диалогов подтверждения при первом запуске. Ты ДОЛЖЕН обрабатывать их с помощью `tmux send-keys`:

### Диалог 1: Доверие к рабочему пространству (первый визит в каталог)
```
❯ 1. Yes, I trust this folder    ← DEFAULT (just press Enter)
  2. No, exit
```
**Обработка:** `tmux send-keys -t <session> Enter` — вариант по умолчанию правильный.

### Диалог 2: Обход предупреждения о разрешениях (только с `--dangerously-skip-permissions`)
```
❯ 1. No, exit                    ← DEFAULT (WRONG choice!)
  2. Yes, I accept
```
**Обработка:** Сначала перемести выделение вниз, затем нажми Enter:
```
tmux send-keys -t <session> Down && sleep 0.3 && tmux send-keys -t <session> Enter
```

### Надёжный шаблон обработки диалогов
```
# Launch with permissions bypass
terminal(command="tmux send-keys -t claude-work 'claude --dangerously-skip-permissions \"your task\"' Enter")

# Handle trust dialog (Enter for default "Yes")
terminal(command="sleep 4 && tmux send-keys -t claude-work Enter")

# Handle permissions dialog (Down then Enter for "Yes, I accept")
terminal(command="sleep 3 && tmux send-keys -t claude-work Down && sleep 0.3 && tmux send-keys -t claude-work Enter")

# Now wait for Claude to work
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -60")
```

**Примечание:** После первого принятия доверия к каталогу диалог доверия больше не появляется. Только диалог разрешений повторяется каждый раз, когда ты используешь `--dangerously-skip-permissions`.
## Подкоманды CLI

| Подкоманда | Назначение |
|------------|------------|
| `claude` | Запустить интерактивный REPL |
| `claude "query"` | Запустить REPL с начальным запросом |
| `claude -p "query"` | Режим печати (неинтерактивный, завершает работу после выполнения) |
| `cat file \| claude -p "query"` | Передать содержимое через stdin как контекст |
| `claude -c` | Продолжить последнюю сессию в этом каталоге |
| `claude -r "id"` | Возобновить конкретную сессию по ID или имени |
| `claude auth login` | Войти (добавь `--console` для биллинга API, `--sso` для Enterprise) |
| `claude auth status` | Проверить статус входа (возвращает JSON; `--text` — человекочитаемый вывод) |
| `claude mcp add <name> -- <cmd>` | Добавить MCP‑сервер |
| `claude mcp list` | Показать список настроенных MCP‑серверов |
| `claude mcp remove <name>` | Удалить MCP‑сервер |
| `claude agents` | Показать список настроенных агентов |
| `claude doctor` | Выполнить проверку состояния установки и автообновления |
| `claude update` / `claude upgrade` | Обновить Claude Code до последней версии |
| `claude remote-control` | Запустить сервер для управления Claude из claude.ai или мобильного приложения |
| `claude install [target]` | Установить нативную сборку (stable, latest или конкретную версию) |
| `claude setup-token` | Настроить долгоживущий токен аутентификации (требуется подписка) |
| `claude plugin` / `claude plugins` | Управлять плагинами Claude Code |
| `claude auto-mode` | Просмотреть конфигурацию классификатора авто‑режима |
## Print Mode Deep Dive

### Structured JSON Output
```
terminal(command="claude -p 'Analyze auth.py for security issues' --output-format json --max-turns 5", workdir="/project", timeout=120)
```

Возвращает объект JSON со следующими полями:
```json
{
  "type": "result",
  "subtype": "success",
  "result": "The analysis text...",
  "session_id": "75e2167f-...",
  "num_turns": 3,
  "total_cost_usd": 0.0787,
  "duration_ms": 10276,
  "stop_reason": "end_turn",
  "terminal_reason": "completed",
  "usage": { "input_tokens": 5, "output_tokens": 603, ... },
  "modelUsage": { "claude-sonnet-4-6": { "costUSD": 0.078, "contextWindow": 200000 } }
}
```

**Ключевые поля:** `session_id` — для возобновления, `num_turns` — для подсчёта итераций агентного цикла, `total_cost_usd` — для отслеживания расходов, `subtype` — для определения успеха/ошибки (`success`, `error_max_turns`, `error_budget`).

### Streaming JSON Output
Для потоковой передачи токенов в реальном времени используй `stream-json` с `--verbose`:
```
terminal(command="claude -p 'Write a summary' --output-format stream-json --verbose --include-partial-messages", timeout=60)
```

Возвращает события JSON, разделённые переводом строки. Фильтруй их с помощью `jq` для получения живого текста:
```
claude -p "Explain X" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

События потока включают `system/api_retry` с полями `attempt`, `max_retries` и `error` (например, `rate_limit`, `billing_error`).

### Bidirectional Streaming
Для потоковой передачи ввода **и** вывода в реальном времени:
```
claude -p "task" --input-format stream-json --output-format stream-json --replay-user-messages
```
`--replay-user-messages` повторно выводит сообщения пользователя в `stdout` для подтверждения.

### Piped Input
```
# Pipe a file for analysis
terminal(command="cat src/auth.py | claude -p 'Review this code for bugs' --max-turns 1", timeout=60)

# Pipe multiple files
terminal(command="cat src/*.py | claude -p 'Find all TODO comments' --max-turns 1", timeout=60)

# Pipe command output
terminal(command="git diff HEAD~3 | claude -p 'Summarize these changes' --max-turns 1", timeout=60)
```

### JSON Schema for Structured Extraction
```
terminal(command="claude -p 'List all functions in src/' --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"functions\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}},\"required\":[\"functions\"]}' --max-turns 5", workdir="/project", timeout=90)
```

Разбирай `structured_output` из результата JSON. Claude проверяет вывод на соответствие схеме перед возвратом.

### Session Continuation
```
# Start a task
terminal(command="claude -p 'Start refactoring the database layer' --output-format json --max-turns 10 > /tmp/session.json", workdir="/project", timeout=180)

# Resume with session ID
terminal(command="claude -p 'Continue and add connection pooling' --resume $(cat /tmp/session.json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"session_id\"])') --max-turns 5", workdir="/project", timeout=120)

# Or resume the most recent session in the same directory
terminal(command="claude -p 'What did you do last time?' --continue --max-turns 1", workdir="/project", timeout=30)

# Fork a session (new ID, keeps history)
terminal(command="claude -p 'Try a different approach' --resume <id> --fork-session --max-turns 10", workdir="/project", timeout=120)
```

### Bare Mode for CI/Scripting
```
terminal(command="claude --bare -p 'Run all tests and report failures' --allowedTools 'Read,Bash' --max-turns 10", workdir="/project", timeout=180)
```

`--bare` пропускает хуки, плагины, обнаружение MCP и загрузку `CLAUDE.md`. Самый быстрый старт. Требуется `ANTHROPIC_API_KEY` (пропускает OAuth).

Чтобы выборочно загрузить контекст в bare‑режиме:

| Что загрузить | Флаг |
|---------------|------|
| Добавления к системному промпту | `--append-system-prompt "text"` или `--append-system-prompt-file path` |
| Настройки | `--settings <file-or-json>` |
| Серверы MCP | `--mcp-config <file-or-json>` |
| Пользовательские агенты | `--agents '<json>'` |

### Fallback Model for Overload
```
terminal(command="claude -p 'task' --fallback-model haiku --max-turns 5", timeout=90)
```
Автоматически переключается на указанную модель, когда стандартная перегружена (только print mode).
## Полный справочник флагов CLI

### Сессия и окружение
| Флаг | Эффект |
|------|--------|
| `-p, --print` | Неинтерактивный одноразовый режим (завершается после выполнения) |
| `-c, --continue` | Возобновить последнюю беседу в текущем каталоге |
| `-r, --resume <id>` | Возобновить конкретную сессию по ID или имени (интерактивный выбор, если ID не указан) |
| `--fork-session` | При возобновлении создать новый ID сессии вместо использования оригинального |
| `--session-id <uuid>` | Использовать конкретный UUID для беседы |
| `--no-session-persistence` | Не сохранять сессию на диск (только в режиме печати) |
| `--add-dir <paths...>` | Предоставить Claude доступ к дополнительным рабочим каталогам |
| `-w, --worktree [name]` | Запустить в изолированном git worktree по пути `.claude/worktrees/<name>` |
| `--tmux` | Создать tmux‑сессию для worktree (требуется `--worktree`) |
| `--ide` | Автоматически подключиться к доступному IDE при запуске |
| `--chrome` / `--no-chrome` | Включить/отключить интеграцию с браузером Chrome для веб‑тестирования |
| `--from-pr [number]` | Возобновить сессию, связанную с конкретным Pull Request в GitHub |
| `--file <specs...>` | Файловые ресурсы для загрузки при старте (формат: `file_id:relative_path`) |

### Модель и производительность
| Флаг | Эффект |
|------|--------|
| `--model <alias>` | Выбор модели: `sonnet`, `opus`, `haiku` или полное имя, например `claude-sonnet-4-6` |
| `--effort <level>` | Глубина рассуждений: `low`, `medium`, `high`, `max`, `auto` |
| `--max-turns <n>` | Ограничить количество агентных циклов (только в режиме печати; предотвращает бесконтрольный запуск) |
| `--max-budget-usd <n>` | Ограничить расход API в долларах (только в режиме печати) |
| `--fallback-model <model>` | Авто‑запасной вариант, когда основная модель перегружена (только в режиме печати) |
| `--betas <betas...>` | Beta‑заголовки, включаемые в запросы API (только для пользователей с API‑ключом) |

### Разрешения и безопасность
| Флаг | Эффект |
|------|--------|
| `--dangerously-skip-permissions` | Автоподтверждать ВСЕ использования инструментов (запись файлов, bash, сеть и т.д.) |
| `--allow-dangerously-skip-permissions` | Разрешить обход как *опцию* без включения по умолчанию |
| `--permission-mode <mode>` | `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` |
| `--allowedTools <tools...>` | Белый список конкретных инструментов (через запятую или пробел) |
| `--disallowedTools <tools...>` | Чёрный список конкретных инструментов |
| `--tools <tools...>` | Переопределить встроенный набор инструментов (`""` = нет, `"default"` = все, или имена инструментов) |

### Формат вывода и ввода
| Флаг | Эффект |
|------|--------|
| `--output-format <fmt>` | `text` (по умолчанию), `json` (один объект результата), `stream-json` (по строкам) |
| `--input-format <fmt>` | `text` (по умолчанию) или `stream-json` (потоковый ввод в реальном времени) |
| `--json-schema <schema>` | Принудительно формировать структурированный JSON‑вывод, соответствующий схеме |
| `--verbose` | Полный пошаговый вывод |
| `--include-partial-messages` | Включать частичные фрагменты сообщений по мере их поступления (stream‑json + print) |
| `--replay-user-messages` | Повторно выводить сообщения пользователя в stdout (двунаправленный stream‑json) |

### Системный запрос и контекст
| Флаг | Эффект |
|------|--------|
| `--append-system-prompt <text>` | **Добавить** к системному запросу по умолчанию (сохраняет встроенные возможности) |
| `--append-system-prompt-file <path>` | **Добавить** содержимое файла к системному запросу по умолчанию |
| `--system-prompt <text>` | **Заменить** полностью системный запрос (обычно лучше использовать `--append`) |
| `--system-prompt-file <path>` | **Заменить** системный запрос содержимым файла |
| `--bare` | Пропустить хуки, плагины, обнаружение MCP, CLAUDE.md, OAuth (самый быстрый старт) |
| `--agents '<json>'` | Динамически определить пользовательские подагенты в виде JSON |
| `--mcp-config <path>` | Загрузить серверы MCP из JSON‑файла (можно повторять) |
| `--strict-mcp-config` | Использовать только серверы MCP из `--mcp-config`, игнорируя остальные конфигурации MCP |
| `--settings <file-or-json>` | Загрузить дополнительные настройки из JSON‑файла или встроенного JSON |
| `--setting-sources <sources>` | Источники, разделённые запятыми, для загрузки: `user`, `project`, `local` |
| `--plugin-dir <paths...>` | Загружать плагины из каталогов только для этой сессии |
| `--disable-slash-commands` | Отключить все навыки/слеш‑команды |

### Отладка
| Флаг | Эффект |
|------|--------|
| `-d, --debug [filter]` | Включить отладочный журнал с необязательным фильтром категорий (например, `"api,hooks"`, `"!1p,!file"`) |
| `--debug-file <path>` | Записать отладочный журнал в файл (неявно включает режим отладки) |

### Команды командных групп агентов
| Флаг | Эффект |
|------|--------|
| `--teammate-mode <mode>` | Как отображать команды агентов: `auto`, `in-process` или `tmux` |
| `--brief` | Включить инструмент `SendUserMessage` для общения агент‑пользователь |

### Синтаксис названий инструментов для `--allowedTools` / `--disallowedTools`
```
Read                    # All file reading
Edit                    # File editing (existing files)
Write                   # File creation (new files)
Bash                    # All shell commands
Bash(git *)             # Only git commands
Bash(git commit *)      # Only git commit commands
Bash(npm run lint:*)    # Pattern matching with wildcards
WebSearch               # Web search capability
WebFetch                # Web page fetching
mcp__<server>__<tool>   # Specific MCP tool
```
## Настройки и конфигурация

### Иерархия настроек (от самого высокого к самому низкому приоритету)
1. **CLI flags** — переопределяют всё
2. **Локальный:** `.claude/settings.local.json` (личный, git‑ignored)
3. **Проект:** `.claude/settings.json` (общий, git‑tracked)
4. **Пользователь:** `~/.claude/settings.json` (глобальный)

### Разрешения в настройках
```json
{
  "permissions": {
    "allow": ["Bash(npm run lint:*)", "WebSearch", "Read"],
    "ask": ["Write(*.ts)", "Bash(git push*)"],
    "deny": ["Read(.env)", "Bash(rm -rf *)"]
  }
}
```

### Иерархия файлов памяти (CLAUDE.md)
1. **Глобальный:** `~/.claude/CLAUDE.md` — применяется ко всем проектам
2. **Проект:** `./CLAUDE.md` — контекст, специфичный для проекта (git‑tracked)
3. **Локальный:** `.claude/CLAUDE.local.md` — личные переопределения проекта (git‑ignored)

Используй префикс `#` в интерактивном режиме, чтобы быстро добавить в память: `# Always use 2-space indentation`.
## Интерактивная сессия: Slash‑команды

### Сессия и контекст
| Команда | Назначение |
|---------|------------|
| `/help` | Показать все команды (включая пользовательские и команды MCP) |
| `/compact [focus]` | Сжать контекст, чтобы сэкономить токены; файл CLAUDE.md сохраняется при сжатии. Например, `/compact focus on auth logic` |
| `/clear` | Очистить историю разговора для нового старта |
| `/context` | Визуализировать использование контекста в виде цветной сетки с советами по оптимизации |
| `/cost` | Показать использование токенов с разбивкой по моделям и кэш‑хитам |
| `/resume` | Переключиться на другую сессию или возобновить её |
| `/rewind` | Откат к предыдущей контрольной точке в разговоре или коде |
| `/btw <question>` | Задать побочный вопрос без добавления к стоимости контекста |
| `/status` | Показать версию, статус соединения и информацию о сессии |
| `/todos` | Вывести список отслеживаемых задач из разговора |
| `/exit` или `Ctrl+D` | Завершить сессию |

### Разработка и ревью
| Команда | Назначение |
|---------|------------|
| `/review` | Запросить код‑ревью текущих изменений |
| `/security-review` | Выполнить анализ безопасности текущих изменений |
| `/plan [description]` | Перейти в режим План с авто‑запуском для планирования задач |
| `/loop [interval]` | Запланировать повторяющиеся задачи в рамках сессии |
| `/batch` | Автоматически создать worktree для больших параллельных изменений (5‑30 worktree) |

### Конфигурация и инструменты
| Команда | Назначение |
|---------|------------|
| `/model [model]` | Сменить модель в середине сессии (используй стрелки для регулировки усилия) |
| `/effort [level]` | Установить уровень рассуждения: `low`, `medium`, `high`, `max` или `auto` |
| `/init` | Создать файл CLAUDE.md для памяти проекта |
| `/memory` | Открыть CLAUDE.md для редактирования |
| `/config` | Открыть интерактивную конфигурацию настроек |
| `/permissions` | Просмотр/обновление прав доступа к инструментам |
| `/agents` | Управление специализированными суб‑агентами |
| `/mcp` | Интерактивный UI для управления серверами MCP |
| `/add-dir` | Добавить дополнительные рабочие каталоги (полезно для монорепозиториев) |
| `/usage` | Показать лимиты плана и статус ограничения запросов |
| `/voice` | Включить режим push‑to‑talk (20 языков; удерживай Space для записи, отпусти — отправка) |
| `/release-notes` | Интерактивный выбор заметок к версии релиза |

### Пользовательские Slash‑команды
Создай `.claude/commands/<name>.md` (общий для проекта) или `~/.claude/commands/<name>.md` (личный):

```markdown
# .claude/commands/deploy.md
Run the deploy pipeline:
1. Run all tests
2. Build the Docker image
3. Push to registry
4. Update the $ARGUMENTS environment (default: staging)
```

Использование: `/deploy production` — `$ARGUMENTS` заменяется вводом пользователя.

### Навыки (вызов естественным языком)
В отличие от Slash‑команд (вызываются вручную), навыки в `.claude/skills/` — это markdown‑руководства, которые Claude вызывает автоматически через естественный язык, когда задача совпадает:

```markdown
# .claude/skills/database-migration.md
When asked to create or modify database migrations:
1. Use Alembic for migration generation
2. Always create a rollback function
3. Test migrations against a local database copy
```
## Интерактивная сессия: сочетания клавиш

### Общие управления
| Клавиша | Действие |
|-----|--------|
| `Ctrl+C` | Отменить текущий ввод или генерацию |
| `Ctrl+D` | Выйти из сессии |
| `Ctrl+R` | Обратный поиск в истории команд |
| `Ctrl+B` | Перевести задачу в фон |
| `Ctrl+V` | Вставить изображение в разговор |
| `Ctrl+O` | Режим транскрипции — увидеть процесс мышления Claude |
| `Ctrl+G` или `Ctrl+X Ctrl+E` | Открыть подсказку во внешнем редакторе |
| `Esc Esc` | Перемотать разговор или состояние кода / суммировать |

### Переключатели режимов
| Клавиша | Действие |
|-----|--------|
| `Shift+Tab` | Переключать режимы разрешений (Normal → Auto-Accept → Plan) |
| `Alt+P` | Сменить модель |
| `Alt+T` | Переключить режим мышления |
| `Alt+O` | Переключить быстрый режим |

### Многострочный ввод
| Клавиша | Действие |
|-----|--------|
| `\` + `Enter` | Быстрый перевод строки |
| `Shift+Enter` | Перевод строки (альтернатива) |
| `Ctrl+J` | Перевод строки (альтернатива) |

### Префиксы ввода
| Префикс | Действие |
|--------|--------|
| `!` | Выполнить bash напрямую, обходя ИИ (например, `!npm test`). Используй `!` отдельно, чтобы переключить режим оболочки. |
| `@` | Ссылка на файлы/каталоги с автодополнением (например, `@./src/api/`) |
| `#` | Быстро добавить в память CLAUDE.md (например, `# Use 2-space indentation`) |
| `/` | Команды со слешем |

### Совет профессионала: «ultrathink»
Используй ключевое слово «ultrathink» в подсказке для максимального усилия рассуждения на конкретном ходу. Это активирует самый глубокий режим мышления независимо от текущей настройки `/effort`.
## Шаблон обзора PR

### Быстрый обзор (Print Mode)
```
terminal(command="cd /path/to/repo && git diff main...feature-branch | claude -p 'Review this diff for bugs, security issues, and style problems. Be thorough.' --max-turns 1", timeout=60)
```

### Глубокий обзор (Interactive + Worktree)
```
terminal(command="tmux new-session -d -s review -x 140 -y 40")
terminal(command="tmux send-keys -t review 'cd /path/to/repo && claude -w pr-review' Enter")
terminal(command="sleep 5 && tmux send-keys -t review Enter")  # Trust dialog
terminal(command="sleep 2 && tmux send-keys -t review 'Review all changes vs main. Check for bugs, security issues, race conditions, and missing tests.' Enter")
terminal(command="sleep 30 && tmux capture-pane -t review -p -S -60")
```

### Обзор PR по номеру
```
terminal(command="claude -p 'Review this PR thoroughly' --from-pr 42 --max-turns 10", workdir="/path/to/repo", timeout=120)
```

### Claude Worktree с tmux
```
terminal(command="claude -w feature-x --tmux", workdir="/path/to/repo")
```
Создаёт изолированный git‑worktree в `.claude/worktrees/feature-x` и сеанс tmux для него. Использует нативные панели iTerm2, если они доступны; добавь `--tmux=classic` для традиционного tmux.
## Параллельные экземпляры Claude

Запусти несколько независимых задач Claude одновременно:

```
# Task 1: Fix backend
terminal(command="tmux new-session -d -s task1 -x 140 -y 40 && tmux send-keys -t task1 'cd ~/project && claude -p \"Fix the auth bug in src/auth.py\" --allowedTools \"Read,Edit\" --max-turns 10' Enter")

# Task 2: Write tests
terminal(command="tmux new-session -d -s task2 -x 140 -y 40 && tmux send-keys -t task2 'cd ~/project && claude -p \"Write integration tests for the API endpoints\" --allowedTools \"Read,Write,Bash\" --max-turns 15' Enter")

# Task 3: Update docs
terminal(command="tmux new-session -d -s task3 -x 140 -y 40 && tmux send-keys -t task3 'cd ~/project && claude -p \"Update README.md with the new API endpoints\" --allowedTools \"Read,Edit\" --max-turns 5' Enter")

# Monitor all
terminal(command="sleep 30 && for s in task1 task2 task3; do echo '=== '$s' ==='; tmux capture-pane -t $s -p -S -5 2>/dev/null; done")
```
## CLAUDE.md — Файл контекста проекта

Claude автоматически загружает `CLAUDE.md` из корня проекта. Используй его для сохранения контекста проекта:

```markdown
# Project: My API

## Architecture
- FastAPI backend with SQLAlchemy ORM
- PostgreSQL database, Redis cache
- pytest for testing with 90% coverage target

## Key Commands
- `make test` — run full test suite
- `make lint` — ruff + mypy
- `make dev` — start dev server on :8000

## Code Standards
- Type hints on all public functions
- Docstrings in Google style
- 2-space indentation for YAML, 4-space for Python
- No wildcard imports
```

**Будь конкретен.** Вместо «Write good code» используй «Use 2-space indentation for JS» или «Name test files with `.test.ts` suffix». Конкретные инструкции сокращают количество циклов исправления.

### Каталог правил (модульный CLAUDE.md)
Для проектов с большим количеством правил используй каталог правил вместо одного огромного CLAUDE.md:
- **Правила проекта:** `.claude/rules/*.md` — общие для команды, отслеживаются git
- **Правила пользователя:** `~/.claude/rules/*.md` — личные, глобальные

Каждый файл `.md` в каталоге правил загружается как дополнительный контекст. Это чище, чем запихивать всё в один CLAUDE.md.

### Автопамять
Claude автоматически сохраняет изученный контекст проекта в `~/.claude/projects/<project>/memory/`.
- **Ограничение:** 25 KB или 200 строк на проект
- Это отдельный от CLAUDE.md — собственные заметки Claude о проекте, накопленные за сессиями.
## Пользовательские суб‑агенты

Определяй специализированные агенты в `.claude/agents/` (проект), `~/.claude/agents/` (личные) или через флаг CLI `--agents` (сессия):

### Приоритет расположения агента
1. `.claude/agents/` — уровень проекта, общий для команды
2. Флаг CLI `--agents` — специфичный для сессии, динамический
3. `~/.claude/agents/` — уровень пользователя, личный

### Создание агента
```markdown
# .claude/agents/security-reviewer.md
---
name: security-reviewer
description: Security-focused code review
model: opus
tools: [Read, Bash]
---
You are a senior security engineer. Review code for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication/authorization flaws
- Secrets in code
- Unsafe deserialization
```

Вызов через: `@security-reviewer review the auth module`

### Динамические агенты через CLI
```
terminal(command="claude --agents '{\"reviewer\": {\"description\": \"Reviews code\", \"prompt\": \"You are a code reviewer focused on performance\"}}' -p 'Use @reviewer to check auth.py'", timeout=120)
```

Claude может координировать несколько агентов: «Используй @db-expert для оптимизации запросов, затем @security для аудита изменений».
## Hooks — Автоматизация по событиям

Настройка в `.claude/settings.json` (проект) или `~/.claude/settings.json` (глобально):

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write(*.py)",
      "hooks": [{"type": "command", "command": "ruff check --fix $CLAUDE_FILE_PATHS"}]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'rm -rf'; then echo 'Blocked!' && exit 2; fi"}]
    }],
    "Stop": [{
      "hooks": [{"type": "command", "command": "echo 'Claude finished a response' >> /tmp/claude-activity.log"}]
    }]
  }
}
```

### Все 8 типов хуков
| Hook | Когда срабатывает | Типичное применение |
|------|-------------------|--------------------|
| `UserPromptSubmit` | Перед тем как Claude обрабатывает запрос пользователя | Проверка ввода, логирование |
| `PreToolUse` | Перед выполнением инструмента | Защитные шлюзы, блокировка опасных команд (exit 2 = блок) |
| `PostToolUse` | После завершения работы инструмента | Автоформатирование кода, запуск линтеров |
| `Notification` | При запросах разрешений или ожидании ввода | Уведомления рабочего стола, оповещения |
| `Stop` | Когда Claude завершает ответ | Логирование завершения, обновление статуса |
| `SubagentStop` | Когда подагент завершает работу | Оркестрация агентов |
| `PreCompact` | Перед очисткой памяти контекста | Резервное копирование транскриптов сессии |
| `SessionStart` | При начале сессии | Загрузка контекста разработки (например, `git status`) |

### Переменные окружения хуков
| Variable | Содержание |
|----------|------------|
| `CLAUDE_PROJECT_DIR` | Текущий путь проекта |
| `CLAUDE_FILE_PATHS` | Файлы, которые изменяются |
| `CLAUDE_TOOL_INPUT` | Параметры инструмента в формате JSON |

### Примеры хуков безопасности
```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -qE 'rm -rf|git push.*--force|:(){ :|:& };:'; then echo 'Dangerous command blocked!' && exit 2; fi"}]
  }]
}
```
## Интеграция MCP

Добавь внешние серверы инструментов для баз данных, API и сервисов:

```
# GitHub integration
terminal(command="claude mcp add -s user github -- npx @modelcontextprotocol/server-github", timeout=30)

# PostgreSQL queries
terminal(command="claude mcp add -s local postgres -- npx @anthropic-ai/server-postgres --connection-string postgresql://localhost/mydb", timeout=30)

# Puppeteer for web testing
terminal(command="claude mcp add puppeteer -- npx @anthropic-ai/server-puppeteer", timeout=30)
```

### Области MCP
| Флаг | Область | Хранилище |
|------|---------|-----------|
| `-s user` | Global (all projects) | `~/.claude.json` |
| `-s local` | This project (personal) | `.claude/settings.local.json` (gitignored) |
| `-s project` | This project (team-shared) | `.claude/settings.json` (git-tracked) |

### MCP в режиме Print/CI
```
terminal(command="claude --bare -p 'Query database' --mcp-config mcp-servers.json --strict-mcp-config", timeout=60)
```
`--strict-mcp-config` игнорирует все серверы MCP, кроме тех, что указаны в `--mcp-config`.

Ссылка на ресурсы MCP в чате: `@github:issue://123`

### Ограничения и настройка MCP
- **Описание инструментов:** ограничение 2 KB на сервер для описаний инструментов и инструкций сервера
- **Размер результата:** по умолчанию ограничен; используй аннотацию `maxResultSizeChars`, чтобы разрешить до **500 K** символов для больших выводов
- **Токены вывода:** `export MAX_MCP_OUTPUT_TOKENS=50000` — ограничивает вывод серверов MCP, чтобы предотвратить переполнение контекста
- **Транспорты:** `stdio` (локальный процесс), `http` (удалённый), `sse` (server‑sent events)
## Мониторинг интерактивных сессий

### Чтение статуса TUI
```
# Periodic capture to check if Claude is still working or waiting for input
terminal(command="tmux capture-pane -t dev -p -S -10")
```

Ищи следующие индикаторы:
- `❯` внизу = ожидает твоего ввода (Claude завершил или задаёт вопрос)
- `●` строки = Claude активно использует инструменты (чтение, запись, выполнение команд)
- `⏵⏵ bypass permissions on` = строка состояния показывает режим разрешений
- `◐ medium · /effort` = текущий уровень усилий в строке состояния
- `ctrl+o to expand` = вывод инструмента был усечён (можно развернуть интерактивно)

### Состояние окна контекста
Используй `/context` в интерактивном режиме, чтобы увидеть цветную сетку использования контекста. Ключевые пороги:
- **< 70 %** — нормальная работа, полная точность
- **70‑85 %** — точность начинает падать, рассмотр `/compact`
- **> 85 %** — риск галлюцинаций резко возрастает, используй `/compact` или `/clear`
## Переменные окружения

| Variable | Effect |
|----------|--------|
| `ANTHROPIC_API_KEY` | API‑ключ для аутентификации (альтернатива OAuth) |
| `CLAUDE_CODE_EFFORT_LEVEL` | Уровень усилий по умолчанию: `low`, `medium`, `high`, `max` или `auto` |
| `MAX_THINKING_TOKENS` | Ограничивает количество токенов для размышлений (установи `0`, чтобы полностью отключить размышления) |
| `MAX_MCP_OUTPUT_TOKENS` | Ограничивает вывод от серверов MCP (значение по умолчанию различается; например, установи `50000`) |
| `CLAUDE_CODE_NO_FLICKER=1` | Включает рендеринг в альтернативном экране, чтобы устранить мерцание терминала |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | Удаляет учётные данные из подпроцессов для повышения безопасности |
## Советы по стоимости и производительности

1. **Используй `--max-turns`** в режиме печати, чтобы предотвратить бесконечные циклы. Начинай с 5‑10 для большинства задач.
2. **Используй `--max-budget-usd`** для ограничения расходов. Учти: минимум ≈ $0.05 для создания кеша системного промпта.
3. **Используй `--effort low`** для простых задач (быстрее, дешевле). `high` или `max` — для сложных рассуждений.
4. **Используй `--bare`** в CI/скриптах, чтобы пропустить поиск плагинов/хуков.
5. **Используй `--allowedTools`**, чтобы ограничить набор только необходимыми инструментами (например, `Read` — только для обзоров).
6. **Используй `/compact`** в интерактивных сессиях, когда контекст становится большим.
7. **Передавай ввод через конвейер**, вместо того чтобы заставлять Claude читать файлы, если нужен лишь анализ известного содержимого.
8. **Используй `--model haiku`** для простых задач (дешевле) и `--model opus` — для сложной многошаговой работы.
9. **Используй `--fallback-model haiku`** в режиме печати, чтобы плавно обрабатывать перегрузку модели.
10. **Запускай новые сессии для разных задач** — сессии живут 5 часов; свежий контекст более эффективен.
11. **Используй `--no-session-persistence`** в CI, чтобы не накапливать сохранённые сессии на диске.
## Подводные камни и нюансы

1. **Интерактивный режим ТРЕБУЕТ tmux** — Claude Code — это полноценное TUI‑приложение. Использование только `pty=true` в терминале Hermes работает, но tmux предоставляет `capture-pane` для мониторинга и `send-keys` для ввода, что необходимо для оркестрации.
2. **Диалог `--dangerously-skip-permissions` по умолчанию «No, exit»** — нужно нажать Down, а затем Enter, чтобы принять. Режим печати (`-p`) полностью пропускает этот диалог.
3. **Минимальное значение `--max-budget-usd` ≈ $0.05** — создание кэша системного промпта уже стоит столько. Установка меньшего значения приведёт к немедленной ошибке.
4. **`--max-turns` работает только в режиме печати** — игнорируется в интерактивных сессиях.
5. **Claude может использовать `python` вместо `python3`** — на системах без ссылки `python` команды Bash от Claude не выполнятся с первой попытки, но он сам исправит это.
6. **Возобновление сессии требует той же директории** — `--continue` ищет самую последнюю сессию для текущей рабочей директории.
7. **Для `--json-schema` требуется достаточное значение `--max-turns`** — Claude должен прочитать файлы перед тем, как сформировать структурированный вывод, что занимает несколько ходов.
8. **Диалог доверия появляется только один раз для каждой директории** — только при первом запуске, затем кэшируется.
9. **Фоновые tmux‑сессии сохраняются** — всегда очищай их командой `tmux kill-session -t <name>` после завершения работы.
10. **Команды со слешем (например, `/commit`) работают только в интерактивном режиме** — в режиме `-p` опиши задачу естественным языком вместо этого.
11. **`--bare` пропускает OAuth** — требует переменную окружения `ANTHROPIC_API_KEY` или `apiKeyHelper` в настройках.
12. **Ухудшение контекста реально** — качество вывода ИИ заметно падает при использовании более 70 % окна контекста. Следи за этим с помощью `/context` и проактивно вызывай `/compact`.
## Правила для Hermes Agents

1. **Отдавай предпочтение режиму печати (`-p`) для одиночных задач** — чище, без обработки диалогов, структурированный вывод
2. **Используй tmux для многошаговой интерактивной работы** — единственный надёжный способ оркестровать TUI
3. **Всегда задавай `workdir`** — держит Claude сосредоточенным на нужном каталоге проекта
4. **Устанавливай `--max-turns` в режиме печати** — предотвращает бесконечные циклы и неконтролируемые расходы
5. **Отслеживай tmux‑сессии** — используй `tmux capture-pane -t <session> -p -S -50` для проверки прогресса
6. **Ищи подсказку `❯`** — указывает, что Claude ждёт ввода (завершения или вопроса)
7. **Очищай tmux‑сессии** — завершай их после использования, чтобы избежать утечек ресурсов
8. **Отчитывайся пользователю** — после завершения подведи итог того, что сделал Claude и какие изменения произошли
9. **Не завершай медленные сессии** — Claude может выполнять многошаговую работу; вместо этого проверяй прогресс
10. **Используй `--allowedTools`** — ограничивай возможности только теми, что действительно нужны задаче