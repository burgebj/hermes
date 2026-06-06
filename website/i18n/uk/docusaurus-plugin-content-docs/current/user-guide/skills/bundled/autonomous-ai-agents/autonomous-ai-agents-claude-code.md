---
title: "Claude Code — Делегуй кодування до Claude Code CLI (features, PRs)"
sidebar_label: "Claude Code"
description: "Делегуй кодування Claude Code CLI (можливості, PRs)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Claude Code

Делегуй кодування Claude Code CLI (фічі, PR‑и).
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлюється за замовчуванням) |
| Шлях | `skills/autonomous-ai-agents/claude-code` |
| Версія | `2.2.0` |
| Автор | Hermes Agent + Teknium |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `Coding-Agent`, `Claude`, `Anthropic`, `Code-Review`, `Refactoring`, `PTY`, `Automation` |
| Пов’язані навички | [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent), [`opencode`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-opencode) |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Claude Code — Посібник з оркестрування Hermes

Делегуй завдання кодування [Claude Code](https://code.claude.com/docs/en/cli-reference) (автономний CLI‑агент кодування від Anthropic) через термінал Hermes. Claude Code v2.x може читати файли, писати код, виконувати shell‑команди, створювати підагенти та автономно керувати git‑робочими процесами.
## Передумови

- **Install:** `npm install -g @anthropic-ai/claude-code`
- **Auth:** запусти `claude` один раз, щоб увійти (браузерний OAuth для Pro/Max або встанови `ANTHROPIC_API_KEY`)
- **Console auth:** `claude auth login --console` – авторизація в консолі для білінгу за API‑ключем
- **SSO auth:** `claude auth login --sso` – авторизація SSO для Enterprise
- **Check status:** `claude auth status` (JSON) або `claude auth status --text` (людсько‑читабельно)
- **Health check:** `claude doctor` — перевіряє автооновлювач та стан інсталяції
- **Version check:** `claude --version` (вимагає v2.x+)
- **Update:** `claude update` або `claude upgrade`
## Два режими оркестрування

Hermes взаємодіє з Claude Code у два фундаментально різних способи. Обирай залежно від завдання.

### Режим 1: Print Mode (`-p`) — Не‑інтерактивний (ПРЕДПОЧТАНИЙ для більшості завдань)

Print mode виконує одноразове завдання, повертає результат і завершується. Не потрібен PTY. Ніяких інтерактивних підказок. Це найчистіший шлях інтеграції.

```
terminal(command="claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10", workdir="/path/to/project", timeout=120)
```

**Коли використовувати Print Mode:**
- Одноразові завдання кодування (виправлення помилки, додавання функції, рефакторинг)
- CI/CD‑автоматизація та скрипти
- Структуроване вилучення даних за допомогою `--json-schema`
- Обробка даних через конвеєр (`cat file | claude -p "analyze this"`)
- Будь‑яке завдання, де не потрібна багатокрокова розмова

**Print Mode пропускає ВСІ інтерактивні діалоги** — немає запиту про довіру до робочого простору, немає підтверджень дозволів. Це робить його ідеальним для автоматизації.

### Режим 2: Interactive PTY via tmux — Багатокрокові сесії

Інтерактивний режим надає повний розмовний REPL, у якому можна надсилати подальші підказки, використовувати слеш‑команди та спостерігати за роботою Claude у реальному часі. **Потрібна оркестрація tmux.**

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

**Коли використовувати інтерактивний режим:**
- Багатокрокова ітеративна робота (рефакторинг → огляд → виправлення → цикл тестування)
- Завдання, що вимагають рішень людина‑в‑циклі
- Дослідницькі сесії кодування
- Коли потрібно використовувати слеш‑команди Claude (`/compact`, `/review`, `/model`)
## Обробка діалогів PTY (КРИТИЧНО для інтерактивного режиму)

Claude Code показує до двох діалогових вікон підтвердження під час першого запуску. ТИ ПОВИНЕН обробляти їх за допомогою `tmux send-keys`:

### Діалог 1: Довіра до робочого простору (перший візит у каталог)
```
❯ 1. Yes, I trust this folder    ← DEFAULT (just press Enter)
  2. No, exit
```
**Обробка:** `tmux send-keys -t <session> Enter` — типово вибрана правильна опція.

### Діалог 2: Обхід попередження про дозволи (лише з `--dangerously-skip-permissions`)
```
❯ 1. No, exit                    ← DEFAULT (WRONG choice!)
  2. Yes, I accept
```
**Обробка:** Спочатку треба перейти вниз (DOWN), потім натиснути Enter:
```
tmux send-keys -t <session> Down && sleep 0.3 && tmux send-keys -t <session> Enter
```

### Надійний шаблон обробки діалогів
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

**Примітка:** Після першого прийняття довіри до каталогу діалог довіри більше не з’являтиметься. Лише діалог про дозволи повторюється щоразу, коли ти використовуєш `--dangerously-skip-permissions`.
## CLI Subcommands

| Підкоманда | Призначення |
|------------|-------------|
| `claude` | Запустити інтерактивний REPL |
| `claude "query"` | Запустити REPL з початковим запитом |
| `claude -p "query"` | Режим виводу (неінтерактивний, завершується після виконання) |
| `cat file \| claude -p "query"` | Передати вміст через stdin як контекст |
| `claude -c` | Продовжити останню розмову в цьому каталозі |
| `claude -r "id"` | Відновити конкретну сесію за ID або назвою |
| `claude auth login` | Увійти (додайте `--console` для білінгу API, `--sso` для Enterprise) |
| `claude auth status` | Перевірити статус входу (повертає JSON; `--text` — для читабельного формату) |
| `claude mcp add <name> -- <cmd>` | Додати сервер MCP |
| `claude mcp list` | Переглянути налаштовані сервери MCP |
| `claude mcp remove <name>` | Видалити сервер MCP |
| `claude agents` | Переглянути налаштованих агентів |
| `claude doctor` | Запустити перевірки стану встановлення та автооновлювача |
| `claude update` / `claude upgrade` | Оновити Claude Code до останньої версії |
| `claude remote-control` | Запустити сервер для керування Claude з claude.ai або мобільного додатку |
| `claude install [target]` | Встановити нативну збірку (stable, latest або конкретну версію) |
| `claude setup-token` | Налаштувати довготривалий токен автентифікації (вимагає підписки) |
| `claude plugin` / `claude plugins` | Керувати плагінами Claude Code |
| `claude auto-mode` | Переглянути конфігурацію класифікатора режиму автопрацювання |
## Режим друку: глибоке занурення

### Структурований JSON‑вивід
```
terminal(command="claude -p 'Analyze auth.py for security issues' --output-format json --max-turns 5", workdir="/project", timeout=120)
```

Повертає JSON‑об’єкт з:
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

**Ключові поля:** `session_id` для відновлення, `num_turns` для підрахунку кількості циклів агента, `total_cost_usd` для відстеження витрат, `subtype` для визначення успіху/помилки (`success`, `error_max_turns`, `error_budget`).

### Потоковий JSON‑вивід
Для потокової передачі токенів у реальному часі використай `stream-json` з `--verbose`:
```
terminal(command="claude -p 'Write a summary' --output-format stream-json --verbose --include-partial-messages", timeout=60)
```

Повертає події JSON, розділені новим рядком. Фільтруй за допомогою `jq` для отримання живого тексту:
```
claude -p "Explain X" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

Події потоку включають `system/api_retry` з полями `attempt`, `max_retries` та `error` (наприклад, `rate_limit`, `billing_error`).

### Двостороннє потокове передавання
Для потокового передавання вводу **і** виведення у реальному часі:
```
claude -p "task" --input-format stream-json --output-format stream-json --replay-user-messages
```
`--replay-user-messages` повторно виводить повідомлення користувача у `stdout` для підтвердження.

### Вхід через конвеєр
```
# Pipe a file for analysis
terminal(command="cat src/auth.py | claude -p 'Review this code for bugs' --max-turns 1", timeout=60)

# Pipe multiple files
terminal(command="cat src/*.py | claude -p 'Find all TODO comments' --max-turns 1", timeout=60)

# Pipe command output
terminal(command="git diff HEAD~3 | claude -p 'Summarize these changes' --max-turns 1", timeout=60)
```

### JSON‑схема для структурованого вилучення
```
terminal(command="claude -p 'List all functions in src/' --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"functions\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}},\"required\":[\"functions\"]}' --max-turns 5", workdir="/project", timeout=90)
```

Розбери `structured_output` із результату JSON. Claude валідовує виведення за схемою перед поверненням.

### Продовження сесії
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

### Режим Bare для CI/скриптів
```
terminal(command="claude --bare -p 'Run all tests and report failures' --allowedTools 'Read,Bash' --max-turns 10", workdir="/project", timeout=180)
```

`--bare` пропускає хуки, плагіни, виявлення MCP та завантаження CLAUDE.md. Найшвидший запуск. Потрібен `ANTHROPIC_API_KEY` (пропускає OAuth).

Щоб вибірково завантажити контекст у режимі bare:

| Що завантажити | Прапорець |
|----------------|-----------|
| Додатки системного підказника | `--append-system-prompt "text"` або `--append-system-prompt-file path` |
| Налаштування | `--settings <file-or-json>` |
| Сервери MCP | `--mcp-config <file-or-json>` |
| Користувацькі агенти | `--agents '<json>'` |

### Запасний (фолбек) варіант моделі при перевантаженні
```
terminal(command="claude -p 'task' --fallback-model haiku --max-turns 5", timeout=90)
```
Автоматично переходить на вказану модель, коли типова перевантажена (лише режим друку).
## Повний довідник прапорців CLI

### Сесія та середовище
| Прапорець | Ефект |
|------|--------|
| `-p, --print` | Не‑інтерактивний одноразовий режим (виходить після завершення) |
| `-c, --continue` | Відновити останню розмову в поточному каталозі |
| `-r, --resume <id>` | Відновити конкретну сесію за ID або назвою (інтерактивний вибір, якщо ID не вказано) |
| `--fork-session` | При відновленні створює новий ID сесії замість використання оригінального |
| `--session-id <uuid>` | Використати конкретний UUID для розмови |
| `--no-session-persistence` | Не зберігати сесію на диск (лише режим друку) |
| `--add-dir <paths...>` | Надати Claude доступ до додаткових робочих каталогів |
| `-w, --worktree [name]` | Запустити в ізольованому git worktree у `.claude/worktrees/<name>` |
| `--tmux` | Створити tmux‑сесію для worktree (вимагає `--worktree`) |
| `--ide` | Автопідключення до дійсного IDE під час запуску |
| `--chrome` / `--no-chrome` | Увімкнути/вимкнути інтеграцію з браузером Chrome для веб‑тестування |
| `--from-pr [number]` | Відновити сесію, пов’язану з конкретним GitHub PR |
| `--file <specs...>` | Файлові ресурси для завантаження під час запуску (формат: `file_id:relative_path`) |

### Модель та продуктивність
| Прапорець | Ефект |
|------|--------|
| `--model <alias>` | Вибір моделі: `sonnet`, `opus`, `haiku` або повна назва типу `claude-sonnet-4-6` |
| `--effort <level>` | Глибина міркувань: `low`, `medium`, `high`, `max`, `auto` |
| `--max-turns <n>` | Обмежити кількість агентних циклів (лише режим друку; запобігає неконтрольованому виконанню) |
| `--max-budget-usd <n>` | Обмежити витрати API у доларах (лише режим друку) |
| `--fallback-model <model>` | Авто‑запасний варіант, коли типова модель перевантажена (лише режим друку) |
| `--betas <betas...>` | Beta‑заголовки, які слід включити в запити API (лише для користувачів API‑ключа) |

### Дозволи та безпека
| Прапорець | Ефект |
|------|--------|
| `--dangerously-skip-permissions` | Автопідтвердження ВСЬОГО використання інструментів (запис файлів, bash, мережа тощо) |
| `--allow-dangerously-skip-permissions` | Дозволити обхід як *опцію* без увімкнення за замовчуванням |
| `--permission-mode <mode>` | `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` |
| `--allowedTools <tools...>` | Білий список конкретних інструментів (через кому або пробіл) |
| `--disallowedTools <tools...>` | Чорний список конкретних інструментів |
| `--tools <tools...>` | Перезапис вбудованого набору інструментів (`""` = жодного, `"default"` = всі, або назви інструментів) |

### Формат виводу та вводу
| Прапорець | Ефект |
|------|--------|
| `--output-format <fmt>` | `text` (за замовчуванням), `json` (один об’єкт результату), `stream-json` (по рядку) |
| `--input-format <fmt>` | `text` (за замовчуванням) або `stream-json` (реальний потоковий ввід) |
| `--json-schema <schema>` | Примусово сформований JSON‑вивід, що відповідає схемі |
| `--verbose` | Повний покроковий вивід |
| `--include-partial-messages` | Включати часткові фрагменти повідомлень у міру надходження (stream‑json + print) |
| `--replay-user-messages` | Повторно виводити повідомлення користувача у stdout (stream‑json двосторонній) |

### Системна підказка та контекст
| Прапорець | Ефект |
|------|--------|
| `--append-system-prompt <text>` | **Додати** до типової системної підказки (зберігає вбудовані можливості) |
| `--append-system-prompt-file <path>` | **Додати** вміст файлу до типової системної підказки |
| `--system-prompt <text>` | **Замінити** всю системну підказку (зазвичай краще використати `--append`) |
| `--system-prompt-file <path>` | **Замінити** системну підказку вмістом файлу |
| `--bare` | Пропустити хуки, плагіни, виявлення MCP, CLAUDE.md, OAuth (найшвидший запуск) |
| `--agents '<json>'` | Динамічно визначити користувацькі підагенти у форматі JSON |
| `--mcp-config <path>` | Завантажити сервери MCP з JSON‑файлу (можна повторювати) |
| `--strict-mcp-config` | Використовувати лише сервери MCP з `--mcp-config`, ігноруючи інші конфігурації MCP |
| `--settings <file-or-json>` | Завантажити додаткові налаштування з JSON‑файлу або inline‑JSON |
| `--setting-sources <sources>` | Джерела, розділені комами, для завантаження: `user`, `project`, `local` |
| `--plugin-dir <paths...>` | Завантажити плагіни з каталогів лише для цієї сесії |
| `--disable-slash-commands` | Вимкнути всі навички/слеш‑команди |

### Налагодження
| Прапорець | Ефект |
|------|--------|
| `-d, --debug [filter]` | Увімкнути журнал налагодження з необов’язковим фільтром категорій (наприклад, `"api,hooks"`, `"!1p,!file"`) |
| `--debug-file <path>` | Записувати журнал налагодження у файл (неявно вмикає режим налагодження) |

### Команди агентних команд
| Прапорець | Ефект |
|------|--------|
| `--teammate-mode <mode>` | Як відображати команди агентних команд: `auto`, `in-process` або `tmux` |
| `--brief` | Увімкнути інструмент `SendUserMessage` для спілкування агент‑користувач |

### Синтаксис назви інструменту для `--allowedTools` / `--disallowedTools`
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
## Налаштування та конфігурація

### Ієрархія налаштувань (від найвищого до найнижчого пріоритету)
1. **CLI flags** — перевизначає все
2. **Local project:** `.claude/settings.local.json` (особистий, gitignored)
3. **Project:** `.claude/settings.json` (спільний, git-tracked)
4. **User:** `~/.claude/settings.json` (глобальний)

### Дозволи в налаштуваннях
```json
{
  "permissions": {
    "allow": ["Bash(npm run lint:*)", "WebSearch", "Read"],
    "ask": ["Write(*.ts)", "Bash(git push*)"],
    "deny": ["Read(.env)", "Bash(rm -rf *)"]
  }
}
```

### Ієрархія файлів пам'яті (CLAUDE.md)
1. **Global:** `~/.claude/CLAUDE.md` — застосовується до всіх проєктів
2. **Project:** `./CLAUDE.md` — контекст, специфічний для проєкту (git-tracked)
3. **Local:** `.claude/CLAUDE.local.md` — особисті перевизначення проєкту (gitignored)

Використовуй префікс `#` в інтерактивному режимі, щоб швидко додати до пам'яті: `# Always use 2-space indentation`.
## Інтерактивна сесія: Slash‑команди

### Сесія та контекст
| Команда | Призначення |
|---------|-------------|
| `/help` | Показати всі команди (включаючи власні та MCP‑команди) |
| `/compact [focus]` | Стиснути контекст, щоб заощадити токени; `CLAUDE.md` зберігається після стискання. Приклад: `/compact focus on auth logic` |
| `/clear` | Очистити історію розмови для нового старту |
| `/context` | Візуалізувати використання контексту у вигляді кольорової сітки з порадами щодо оптимізації |
| `/cost` | Переглянути використання токенів з розбивкою за моделями та кеш‑хітами |
| `/resume` | Переключитися або відновити іншу сесію |
| `/rewind` | Повернутися до попередньої контрольної точки в розмові або коді |
| `/btw <question>` | Задати бокове питання без додавання до вартості контексту |
| `/status` | Показати версію, підключення та інформацію про сесію |
| `/todos` | Список відстежуваних дій з розмови |
| `/exit` або `Ctrl+D` | Завершити сесію |

### Розробка та огляд
| Команда | Призначення |
|---------|-------------|
| `/review` | Запитати код‑рев’ю поточних змін |
| `/security-review` | Провести аналіз безпеки поточних змін |
| `/plan [description]` | Увійти в режим Плану з автозапуском для планування завдань |
| `/loop [interval]` | Запланувати повторювані завдання в межах сесії |
| `/batch` | Автоматично створити worktree‑и для великих паралельних змін (5‑30 worktree‑ів) |

### Конфігурація та інструменти
| Команда | Призначення |
|---------|-------------|
| `/model [model]` | Перемкнути модель під час сесії (використовуй клавіші‑стрілки для регулювання зусиль) |
| `/effort [level]` | Встановити рівень роздумів: `low`, `medium`, `high`, `max` або `auto` |
| `/init` | Створити файл `CLAUDE.md` для пам’яті проєкту |
| `/memory` | Відкрити `CLAUDE.md` для редагування |
| `/config` | Відкрити інтерактивну конфігурацію налаштувань |
| `/permissions` | Переглянути/оновити дозволи інструментів |
| `/agents` | Керувати спеціалізованими під‑агентами |
| `/mcp` | Інтерактивний UI для керування MCP‑серверами |
| `/add-dir` | Додати додаткові робочі каталоги (корисно для монорепозиторіїв) |
| `/usage` | Показати ліміти плану та статус обмежень швидкості |
| `/voice` | Увімкнути режим push‑to‑talk (20 мов; утримуй Space для запису, відпусти — відправити) |
| `/release-notes` | Інтерактивний вибір нотаток про випуск версії |

### Кастомні Slash‑команди
Створи `.claude/commands/<name>.md` (спільний для проєкту) або `~/.claude/commands/<name>.md` (особистий):

```markdown
# .claude/commands/deploy.md
Run the deploy pipeline:
1. Run all tests
2. Build the Docker image
3. Push to registry
4. Update the $ARGUMENTS environment (default: staging)
```

Використання: `/deploy production` — `$ARGUMENTS` замінюється на ввід користувача.

### Навички (виклик природною мовою)
На відміну від slash‑команд (викликаються вручну), навички в `.claude/skills/` — це markdown‑підручники, які Claude викликає автоматично через природну мову, коли завдання відповідає:

```markdown
# .claude/skills/database-migration.md
When asked to create or modify database migrations:
1. Use Alembic for migration generation
2. Always create a rollback function
3. Test migrations against a local database copy
```
## Інтерактивна сесія: клавіатурні скорочення

### Загальні керування
| Клавіша | Дія |
|-----|--------|
| `Ctrl+C` | Скасувати поточний ввід або генерацію |
| `Ctrl+D` | Вийти з сесії |
| `Ctrl+R` | Зворотний пошук історії команд |
| `Ctrl+B` | Перевести запущене завдання у фон |
| `Ctrl+V` | Вставити зображення в розмову |
| `Ctrl+O` | Режим транскрипції — переглянути процес мислення Claude |
| `Ctrl+G` або `Ctrl+X Ctrl+E` | Відкрити підказку в зовнішньому редакторі |
| `Esc Esc` | Перемотати розмову або стан коду / підсумувати |

### Перемикачі режимів
| Клавіша | Дія |
|-----|--------|
| `Shift+Tab` | Перемикання режимів дозволу (Normal → Auto-Accept → Plan) |
| `Alt+P` | Перемкнути модель |
| `Alt+T` | Перемкнути режим мислення |
| `Alt+O` | Перемкнути швидкий режим |

### Багаторядковий ввід
| Клавіша | Дія |
|-----|--------|
| `\` + `Enter` | Швидкий новий рядок |
| `Shift+Enter` | Новий рядок (альтернатива) |
| `Ctrl+J` | Новий рядок (альтернатива) |

### Префікси вводу
| Префікс | Дія |
|--------|--------|
| `!` | Виконати bash безпосередньо, минаючи AI (наприклад, `!npm test`). Використовуй лише `!` для перемикання режиму shell. |
| `@` | Посилання на файли/директорії з автодоповненням (наприклад, `@./src/api/`) |
| `#` | Швидке додавання до пам'яті CLAUDE.md (наприклад, `# Use 2-space indentation`) |
| `/` | Команди зі слешем |

### Професійна порада: «ultrathink»
Використай ключове слово «ultrathink» у своєму запиті для максимального зусилля роздуму на конкретному кроці. Це активує найглибший режим мислення незалежно від поточного налаштування `/effort`.
## Шаблон огляду PR

### Швидкий огляд (Print Mode)
```
terminal(command="cd /path/to/repo && git diff main...feature-branch | claude -p 'Review this diff for bugs, security issues, and style problems. Be thorough.' --max-turns 1", timeout=60)
```

### Глибокий огляд (Interactive + Worktree)
```
terminal(command="tmux new-session -d -s review -x 140 -y 40")
terminal(command="tmux send-keys -t review 'cd /path/to/repo && claude -w pr-review' Enter")
terminal(command="sleep 5 && tmux send-keys -t review Enter")  # Trust dialog
terminal(command="sleep 2 && tmux send-keys -t review 'Review all changes vs main. Check for bugs, security issues, race conditions, and missing tests.' Enter")
terminal(command="sleep 30 && tmux capture-pane -t review -p -S -60")
```

### Огляд PR за номером
```
terminal(command="claude -p 'Review this PR thoroughly' --from-pr 42 --max-turns 10", workdir="/path/to/repo", timeout=120)
```

### Claude Worktree з tmux
```
terminal(command="claude -w feature-x --tmux", workdir="/path/to/repo")
```
Створює ізольований git worktree у `.claude/worktrees/feature-x` та tmux‑сесію для нього. Використовує вбудовані панелі iTerm2, якщо доступно; додай `--tmux=classic` для традиційного tmux.
## Паралельні екземпляри Claude

Запусти кілька незалежних завдань Claude одночасно:

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
## CLAUDE.md — Файл контексту проєкту

Claude автоматично завантажує `CLAUDE.md` з кореня проєкту. Використовуй його для збереження контексту проєкту:

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

**Будь конкретним.** Замість «Write good code» використай «Use 2-space indentation for JS» або «Name test files with `.test.ts` suffix». Конкретні інструкції скорочують цикли виправлень.

### Директорія правил (модульний CLAUDE.md)
Для проєктів з великою кількістю правил використай директорію правил замість одного великого CLAUDE.md:
- **Правила проєкту:** `.claude/rules/*.md` — спільні для команди, відстежуються git‑ом
- **Правила користувача:** `~/.claude/rules/*.md` — особисті, глобальні

Кожен файл `.md` у директорії правил завантажується як додатковий контекст. Це чистіше, ніж запаковувати все в один CLAUDE.md.

### Авто‑пам'ять
Claude автоматично зберігає вивчений контекст проєкту у `~/.claude/projects/<project>/memory/`.
- **Ліміт:** 25 KB або 200 рядків на проєкт
- Це окремо від CLAUDE.md — це власні нотатки Claude про проєкт, накопичені протягом сесій
## Користувацькі підагенти

Визначай спеціалізовані агенти у `.claude/agents/` (проект), `~/.claude/agents/` (особисто) або за допомогою прапорця CLI `--agents` (сесія):

### Пріоритет розташування агента
1. `.claude/agents/` — рівень проекту, спільний для команди
2. `--agents` CLI flag — специфічний для сесії, динамічний
3. `~/.claude/agents/` — рівень користувача, особистий

### Створення агента
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

Викликати за допомогою: `@security-reviewer review the auth module`

### Динамічні агенти через CLI
```
terminal(command="claude --agents '{\"reviewer\": {\"description\": \"Reviews code\", \"prompt\": \"You are a code reviewer focused on performance\"}}' -p 'Use @reviewer to check auth.py'", timeout=120)
```

Claude може оркеструвати кілька агентів: «Використай @db-expert для оптимізації запитів, потім @security для аудиту змін».
## Hooks — Автоматизація подій

Налаштуй у `.claude/settings.json` (проєкт) або `~/.claude/settings.json` (глобально):

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

### Усі 8 типів Hook
| Hook | Коли спрацьовує | Типове використання |
|------|----------------|----------------------|
| `UserPromptSubmit` | Перед тим, як Claude обробляє запит користувача | Перевірка введення, логування |
| `PreToolUse` | Перед виконанням інструменту | Шлюзи безпеки, блокування небезпечних команд (exit 2 = блок) |
| `PostToolUse` | Після завершення роботи інструменту | Автоформатування коду, запуск лінтерів |
| `Notification` | При запитах дозволу або очікуванні вводу | Сповіщення на робочому столі, повідомлення |
| `Stop` | Коли Claude завершує відповідь | Логування завершення, оновлення статусу |
| `SubagentStop` | Коли підагент завершує роботу | Оркестрація агентів |
| `PreCompact` | Перед очищенням пам'яті контексту | Резервне копіювання транскриптів сесії |
| `SessionStart` | Коли починається сесія | Завантаження контексту розробки (наприклад, `git status`) |

### Змінні середовища Hook
| Змінна | Вміст |
|----------|---------|
| `CLAUDE_PROJECT_DIR` | Шлях до поточного проєкту |
| `CLAUDE_FILE_PATHS` | Файли, що змінюються |
| `CLAUDE_TOOL_INPUT` | Параметри інструменту у форматі JSON |

### Приклади безпечних Hook
```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -qE 'rm -rf|git push.*--force|:(){ :|:& };:'; then echo 'Dangerous command blocked!' && exit 2; fi"}]
  }]
}
```
## Інтеграція MCP

Додати зовнішні сервери інструментів для баз даних, API та сервісів:

```
# GitHub integration
terminal(command="claude mcp add -s user github -- npx @modelcontextprotocol/server-github", timeout=30)

# PostgreSQL queries
terminal(command="claude mcp add -s local postgres -- npx @anthropic-ai/server-postgres --connection-string postgresql://localhost/mydb", timeout=30)

# Puppeteer for web testing
terminal(command="claude mcp add puppeteer -- npx @anthropic-ai/server-puppeteer", timeout=30)
```

### MCP Scopes
| Прапорець | Область | Сховище |
|------|-------|---------|
| `-s user` | Глобальна (всі проєкти) | `~/.claude.json` |
| `-s local` | Цей проєкт (особистий) | `.claude/settings.local.json` (gitignored) |
| `-s project` | Цей проєкт (спільний для команди) | `.claude/settings.json` (git-tracked) |

### MCP у режимі Print/CI
```
terminal(command="claude --bare -p 'Query database' --mcp-config mcp-servers.json --strict-mcp-config", timeout=60)
```
`--strict-mcp-config` ігнорує всі сервери MCP, крім тих, що вказані у `--mcp-config`.

Посилання на ресурси MCP у чаті: `@github:issue://123`

### Обмеження та налаштування MCP
- **Опис інструментів:** ліміт 2 KB на сервер для описів інструментів та інструкцій сервера
- **Розмір результату:** за замовчуванням обмежений; використай анотацію `maxResultSizeChars`, щоб дозволити до **500K** символів для великих виводів
- **Токени виводу:** `export MAX_MCP_OUTPUT_TOKENS=50000` — обмежує вивід серверів MCP, запобігаючи переповненню контексту
- **Транспорти:** `stdio` (локальний процес), `http` (віддалений), `sse` (події, надіслані сервером)
## Моніторинг інтерактивних сесій

### Читання статусу TUI
```
# Periodic capture to check if Claude is still working or waiting for input
terminal(command="tmux capture-pane -t dev -p -S -10")
```

Шукай ці індикатори:
- `❯` внизу = чекає твій ввід (Claude завершив або задає питання)
- `●` рядки = Claude активно використовує інструменти (читає, пише, виконує команди)
- `⏵⏵ bypass permissions on` = рядок стану, що показує режим дозволів
- `◐ medium · /effort` = поточний рівень зусиль у рядку стану
- `ctrl+o to expand` = вивід інструменту був скорочений (можна розгорнути інтерактивно)

### Стан вікна контексту
Використовуй `/context` в інтерактивному режимі, щоб побачити кольорову сітку використання контексту. Ключові пороги:
- **&lt; 70%** — Нормальна робота, повна точність
- **70-85%** — Точність починає падати, розглянь `/compact`
- **> 85%** — Ризик галюцинацій різко зростає, використай `/compact` або `/clear`
## Змінні середовища

| Змінна | Вплив |
|----------|--------|
| `ANTHROPIC_API_KEY` | API‑ключ для автентифікації (альтернатива OAuth) |
| `CLAUDE_CODE_EFFORT_LEVEL` | Типовий рівень зусиль: `low`, `medium`, `high`, `max` або `auto` |
| `MAX_THINKING_TOKENS` | Обмеження токенів мислення (встанови `0`, щоб повністю вимкнути мислення) |
| `MAX_MCP_OUTPUT_TOKENS` | Обмеження кількості токенів виводу з серверів MCP (за замовчуванням різне; наприклад, встанови `50000`) |
| `CLAUDE_CODE_NO_FLICKER=1` | Увімкнути рендеринг alt‑screen для усунення мерехтіння терміналу |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | Видалити облікові дані з підпроцесів для підвищення безпеки |
## Поради щодо вартості та продуктивності

1. **Використовуй `--max-turns`** у режимі `print`, щоб запобігти нескінченним циклам. Починай з 5‑10 для більшості завдань.
2. **Використовуй `--max-budget-usd`** для обмеження витрат. Зауваж: мінімум ~0,05 $ для створення кешу системного prompt.
3. **Використовуй `--effort low`** для простих завдань (швидше, дешевше). `high` або `max` — для складного міркування.
4. **Використовуй `--bare`** у CI/скриптах, щоб пропустити накладні витрати на виявлення плагінів/хукiв.
5. **Використовуй `--allowedTools`**, щоб обмежити лише потрібними інструментами (наприклад, лише `Read` для оглядів).
6. **Використовуй `/compact`** у інтерактивних сесіях, коли контекст стає великим.
7. **Передавай вхідні дані через pipe**, замість того, щоб Claude читав файли, коли потрібен лише аналіз відомого вмісту.
8. **Використовуй `--model haiku`** для простих завдань (дешевше) і `--model opus` для складної багатокрокової роботи.
9. **Використовуй `--fallback-model haiku`** у режимі `print`, щоб плавно обробляти перевантаження моделі.
10. **Створюй нові сесії для різних завдань** — сесії тривають 5 годин; свіжий контекст ефективніший.
11. **Використовуй `--no-session-persistence`** у CI, щоб уникнути накопичення збережених сесій на диску.
## Підводні камені та нюанси

1. **Інтерактивний режим ВИМАГАЄ tmux** — Claude Code — це повноцінний TUI‑застосунок. Використання `pty=true` лише в терміналі Hermes працює, але tmux надає `capture-pane` для моніторингу та `send-keys` для вводу, що є необхідним для оркестрації.
2. **Діалог `--dangerously-skip-permissions` за замовчуванням «No, exit»** — потрібно натиснути ↓, а потім Enter, щоб прийняти. У режимі друку (`-p`) цей діалог пропускається повністю.
3. **Мінімальне значення `--max-budget-usd` ≈ $0.05** — лише створення кешу системного запиту вартує таку суму. Встановлення меншого значення викличе помилку одразу.
4. **`--max-turns` працює лише в режимі друку** — ігнорується в інтерактивних сесіях.
5. **Claude може використовувати `python` замість `python3`** — на системах без символьного посилання `python` команди Bash від Claude не спрацюють з першої спроби, але він самостійно виправить це.
6. **Відновлення сесії вимагає тієї ж директорії** — `--continue` знаходить найновішу сесію для поточної робочої директорії.
7. **`--json-schema` потребує достатньої кількості `--max-turns`** — Claude має спочатку прочитати файли, перш ніж генерувати структурований вихід, що займає кілька ходів.
8. **Діалог довіри з’являється лише один раз для директорії** — лише при першому запуску, далі кешується.
9. **Фонові tmux‑сесії залишаються активними** — завжди очищай їх за допомогою `tmux kill-session -t <name>` після завершення.
10. **Команди зі слешем (наприклад `/commit`) працюють лише в інтерактивному режимі** — у режимі `-p` опиши завдання природною мовою.
11. **`--bare` пропускає OAuth** — вимагає змінної середовища `ANTHROPIC_API_KEY` або `apiKeyHelper` у налаштуваннях.
12. **Зниження контексту — реальна проблема** — якість вихідних даних ШІ вимірювано погіршується при використанні понад 70 % вікна контексту. Слід стежити за цим за допомогою `/context` і проактивно застосовувати `/compact`.
## Правила для Hermes Agents

1. **Віддавай перевагу режиму друку (`-p`) для одиночних завдань** — чистіший вивід, без обробки діалогу, структурований результат
2. **Використовуй tmux для багатокрокової інтерактивної роботи** — єдиний надійний спосіб оркеструвати TUI
3. **Завжди встановлюй `workdir`** — тримай Claude у правильному каталозі проєкту
4. **Встанови `--max-turns` у режимі друку** — запобігає нескінченним циклам і неконтрольованим витратам
5. **Слідкуй за сесіями tmux** — використай `tmux capture-pane -t <session> -p -S -50` для перевірки прогресу
6. **Шукай підказку `❯`** — вказує, що Claude чекає вводу (завершення або запитання)
7. **Очищуй сесії tmux** — заверши їх, коли роботу завершено, щоб уникнути витоків ресурсів
8. **Повідомляй результати користувачеві** — після завершення підбий підсумок того, що зробив Claude і що змінилося
9. **Не заверши повільні сесії** — Claude може виконувати багатокрокову роботу; перевіряй прогрес замість цього
10. **Використовуй `--allowedTools`** — обмежуй можливості лише тим, що дійсно потрібне для завдання