---
title: "Grok — Делегуй кодування xAI Grok Build CLI (фічі, PRs)"
sidebar_label: "Grok"
description: "Делегувати кодування xAI Grok Build CLI (features, PRs)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Grok

Делегуй кодування до xAI Grok Build CLI (фічі, PR‑и).
## Метадані навички

| | |
|---|---|
| Джерело | Необов’язково — встановити за допомогою `hermes skills install official/autonomous-ai-agents/grok` |
| Шлях | `optional-skills/autonomous-ai-agents/grok` |
| Версія | `0.1.0` |
| Автор | Matt Maximo (MattMaximo), Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `Coding-Agent`, `Grok`, `xAI`, `Code-Review`, `Refactoring`, `Automation` |
| Пов’язані навички | [`codex`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-codex), [`claude-code`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-claude-code), [`hermes-agent`](/docs/user-guide/skills/bundled/autonomous-ai-agents/autonomous-ai-agents-hermes-agent) |
:::info
Нижче наведено повне визначення skill, яке Hermes завантажує, коли цей skill активовано. Це інструкції, які бачить агент під час роботи skill.
:::

# Grok Build CLI — Посібник з оркестрації Hermes

Делегуй завдання кодування до [Grok Build](https://docs.x.ai/build/overview) (автономний агент кодування CLI від xAI, команда `grok`) через термінал Hermes. Grok може читати файли, писати код, виконувати shell‑команди, створювати підагенти та керувати git‑робочими процесами. Працює трьома способами: інтерактивний TUI, **headless** (`-p`) та як **ACP‑агент** через JSON‑RPC.

Це третій «брат» для `codex` і `claude-code`. Патерн оркестрації майже ідентичний — **надавай перевагу headless `-p` для одноразових запусків**, використай PTY для інтерактивних сесій.
## Коли використовувати

- Розробка функцій
- Рефакторинг
- Перегляд PR
- Масове виправлення проблем
- Будь‑яке завдання, для якого ти зазвичай використовував би Codex / Claude Code, але хочеш скористатися Grok
## Prerequisites

- **Install (preferred):** `npm install -g @xai-official/grok`
  - Офіційний інсталятор `curl -fsSL https://x.ai/cli/install.sh | bash` також працює, але хост `x.ai` захищений Cloudflare у деяких середовищах. Шлях npm усуває цю залежність повністю.
- **Auth — SuperGrok / X Premium+ subscription (primary path):**
  - Запусти `grok login` один раз → відкриває браузер для OAuth → токен кешується у `~/.grok/auth.json`. Це використовує твою підписку **SuperGrok або X Premium+** (без білінгу за токен API).
  - Перевір стан входу, шукаючи `~/.grok/auth.json`, або запусти недорогий безголовий тест: `grok --no-auto-update -p "Say ok."`
  - У TUI команда `/logout` виходить з системи, а `/login` (або перезапуск) входить назад.
- **No git repo required** — на відміну від Codex, Grok працює поза git‑директорією (зручно для швидких/тимчасових завдань).
- **Claude Code / AGENTS.md compatible with zero config** — Grok автоматично читає `CLAUDE.md`, `.claude/` (skills, agents, MCPs, hooks, rules) та сімейство `AGENTS.md`. Існуючий контекст проєкту просто працює.

> **API-key fallback (not the default for this user):** Grok також підтримує встановлення змінної середовища `XAI_API_KEY` для білінгу pay‑as‑you‑go через `api.x.ai`. Використовуй це лише якщо `grok login` / автентифікація SuperGrok недоступна. Шлях підписки (`grok login`) — це передбачена конфігурація.
## Два режими оркестрування

### Режим 1: Headless (`-p`) — Не‑інтерактивний (ПРЕДПОЧТАНИЙ)

Виконує одноразове завдання, виводить результат і завершується. Без PTY, без інтерактивних діалогів для навігації. Це найчистіший шлях інтеграції — аналог `claude -p` і `codex exec`.

```
terminal(command="grok --no-auto-update -p 'Add a dark mode toggle to settings'", workdir="/path/to/project", timeout=180)
```

Завжди передавай `--no-auto-update` в автоматизації, щоб пропускати перевірки фонових оновлень.

**Коли використовувати headless:**
- Одноразові завдання кодування (виправлення багу, додавання функції, рефакторинг)
- CI/CD‑автоматизація та скрипти
- Структурований парсинг виводу за допомогою `--output-format json`
- Будь‑яке завдання, яке не потребує багатократної розмови

### Режим 2: Інтерактивний PTY — Багатократні TUI‑сесії

TUI — це повноекранний, мишкою керований застосунок. Запусти його з `pty=true`. Для надійного моніторингу/введення використай tmux (те ж шаблон, що й у навичці `claude-code`).

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

**Порада для headless, але в‑лінії виводу:** якщо потрібен вивід у стилі TUI без захоплення повноекранного alt‑screen (наприклад, для чистіших логів), додай `--no-alt-screen`. Для чистої автоматизації headless `-p` все ще чистіший, ніж TUI.
## Глибоке занурення без інтерфейсу

### Загальні прапорці

| Прапорець | Ефект |
|------|--------|
| `-p, --single <PROMPT>` | Надіслати один запит, запустити без інтерфейсу, вийти |
| `-m, --model <MODEL>` | Вибрати модель |
| `-s, --session-id <ID>` | Створити або відновити іменовану headless‑сесію |
| `-r, --resume <ID>` | Відновити існуючу сесію |
| `-c, --continue` | Продовжити останню сесію у поточному каталозі |
| `--cwd <PATH>` | Встановити робочий каталог |
| `--output-format <FMT>` | `plain` (default), `json` або `streaming-json` |
| `--always-approve` | Автоматично схвалювати всі виконання інструментів (еквівалент `--full-auto` / `--yolo`) |
| `--no-alt-screen` | Запускати вбудовано, без захоплення повноекранного TUI |
| `--no-auto-update` | Пропустити перевірки оновлень у фоні (використовувати у всій автоматизації) |

### Формати виводу

- `plain` — текст, зрозумілий людині (за замовчуванням)
- `json` — один JSON‑об’єкт у кінці виконання (чисто розпарсити результат)
- `streaming-json` — події JSON, розділені новим рядком, у міру надходження

```
# Structured result for parsing
terminal(command="grok --no-auto-update -p 'List all TODO comments in src/' --output-format json", workdir="/project", timeout=120)

# Auto-approve for autonomous building
terminal(command="grok --no-auto-update --always-approve -p 'Refactor the database layer and run the tests'", workdir="/project", timeout=300)
```

### Фоновий режим (довгі завдання)

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

Для інтерактивної (TUI) фонова сесія використай `pty=true` + tmux і моніторити
за допомогою `tmux capture-pane`, точно так само, як у навичках `claude-code` / `codex`.

### Продовження сесії

```
# Start a named session
terminal(command="grok --no-auto-update -s refactor-db -p 'Start refactoring the database layer' --always-approve", workdir="/project", timeout=240)

# Resume it later
terminal(command="grok --no-auto-update -r refactor-db -p 'Now add connection pooling' --always-approve", workdir="/project", timeout=180)

# Or continue the most recent session in this directory
terminal(command="grok --no-auto-update -c -p 'What did you change last time?'", workdir="/project", timeout=60)
```
## Read-Only Audit → Шаблон нотатки Markdown

Щоб Grok переглянув локальні артефакти і повернув чисту нотатку у форматі markdown (для Obsidian або репозиторію), не змінюючи нічого:

1. Спочатку підготуй стабільні вхідні файли за допомогою інструментів Hermes (`read_file`, `write_file`). Збережи лише релевантний контекст у тимчасовий файл, а не виводь сирі шляхи.
2. Запусти Grok у headless‑режимі **без** `--always-approve`, щоб він не міг автоматично записувати, і вимагай `markdown only, no preamble`.
3. Запиши stdout Grok безпосередньо у цільову нотатку за допомогою `write_file()`.

```
grok --no-auto-update -p "Read /tmp/current.md and /tmp/inventory.md. Produce markdown only, no preamble. Output a clean note titled 'Cleanup Review'." --output-format plain
```

**Підводний камінь (те саме, що у Claude Code):** при перезаписі документів розпливчастий запит типу «rewrite this» може повернути лише резюме змін, а не повний файл. Замість цього передай файл у вхід і вимагай
`Return ONLY the full revised markdown document. No intro, no explanation, no code fences. Start immediately with '# Title'.`
Перевір перші рядки за допомогою `read_file()` перед тим, як перезаписувати цільовий файл.
## Шаблони огляду PR

### Швидкий огляд (Headless)

```
terminal(command="cd /path/to/repo && git diff main...feature-branch | grok --no-auto-update -p 'Review this diff for bugs, security issues, and style problems. Be thorough.'", timeout=120)
```

### Огляд у тимчасовій копії (безпечний, без зміни репозиторію)

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && grok --no-auto-update -p 'Review the changes vs origin/main. Check bugs, security, race conditions, missing tests.'", pty=true, timeout=300)
```

### Опублікувати огляд

```
terminal(command="gh pr comment 42 --body '<review text>'", workdir="/path/to/repo")
```
## Паралельне виправлення проблем за допомогою worktrees

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
## Корисні підкоманди та команди TUI

| Команда | Призначення |
|---------|-------------|
| `grok` | Запустити інтерактивний TUI |
| `grok -p "query"` | Одноразовий безголовий запуск |
| `grok login` / `grok logout` | Вхід / вихід (SuperGrok / X Premium+ OAuth) |
| `grok inspect` | Показати, що Grok виявив у поточному каталозі: джерела конфігурації, інструкції, **skills**, плагіни, хуки, сервери MCP |
| `grok agent stdio` | Запустити як ACP‑агент через JSON‑RPC (для інтеграції IDE/інструментів) |
| `grok update` | Оновити CLI (потрібен хост `x.ai`; пропускати в автоматизації) |

TUI slash commands (лише в інтерактивному режимі): `/model <name>`, `/always-approve`, `/plan`, `/context`, `/compact`, `/resume`, `/sessions`, `/fork`, `/usage`, `/quit`. `Shift+Tab` перемикає режими **session** (включаючи режим Plan, який блокує запис інструментів, окрім файлу плану **session**).
## Config (`~/.grok/config.toml`)

```toml
[cli]
auto_update = false          # skip background update checks persistently

[ui]
permission_mode = "ask"      # or "always-approve" to skip tool prompts by default

[models]
default = "grok-build-0.1"
```

Помісти глобальні налаштування у `~/.grok/config.toml` (не у `.grok/config.toml`, що прив’язаний до проєкту). Ключ `permission_mode` замінює застарілі ключі `approval_mode` / `yolo = true`.
## Підводні камені та нюанси

1. **Auth працює лише за підпискою.** `grok login` вимагає підписки SuperGrok або X Premium+. Якщо вхід не вдається або відсутній файл `~/.grok/auth.json`, переконайся, що підписка активна, перш ніж переходити до `XAI_API_KEY`.
2. **Не плутай аутентифікацію Hermes xAI з аутентифікацією CLI `grok`.** Hermes `x_search` працює на власному xAI OAuth; окремий CLI `grok` має інший токен у `~/.grok/auth.json`. Працюючий `x_search` НЕ означає, що `grok` залогінений.
3. **Завжди передавай `--no-auto-update` в автоматизації** — інакше Grok надсилатиме запити на оновлення (а `x.ai`/`storage.googleapis.com` можуть бути недоступні).
4. **Віддавай перевагу `npm install` над curl‑установником** — `npm install -g @xai-official/grok` уникає хосту `x.ai`, захищеного Cloudflare.
5. **`--always-approve` — це перемикач автономної збірки.** Без нього безголові запуски можуть зависнути, чекаючи підтвердження інструменту. Прибери його навмисно для режиму лише читання/аудиту, щоб Grok не міг змінювати файли.
6. **Headless `-p` пропускає діалоги TUI**; TUI потребує `pty=true` (+ tmux для моніторингу), так само як і Claude Code.
7. **Використовуй `--no-alt-screen`**, якщо запускаєш TUI в рядку, а повноекранний alt‑screen спотворює захоплений вивід.
8. **Git‑репозиторій не обов’язковий**, але для процесів PR/commit він все ж потрібен — використай `mktemp -d && git init` для тимчасових коміт‑завдань.
9. **Очисти сесії tmux** за допомогою `tmux kill-session -t <name>` після завершення.
## Правила для Hermes Agents

1. **Надавай перевагу безголовому `-p`** для окремих завдань — найчистіша інтеграція, структурований
   вивід через `--output-format json`.
2. **Завжди встановлюй `workdir`** (або `--cwd`), щоб Grok орієнтувався на правильний проєкт.
3. **Передавай `--no-auto-update`** у кожному автоматизованому виклику.
4. **Використовуй `--always-approve` лише коли Grok має писати автономно**; пропусти його
   для переглядів лише на читання та аудитів.
5. **Фонові довгі завдання** з `background=true, notify_on_complete=true` і
   моніторингом за допомогою інструмента `process`.
6. **Використовуй tmux для багатокрокової інтерактивної роботи** і моніторинг за допомогою
   `tmux capture-pane -t <session> -p -S -50`.
7. **Перевіряй автентифікацію перед її використанням** — перевір `~/.grok/auth.json` або запусти
   недорогий `grok -p "Say ok."` smoke‑test; не припускай, що автентифікація Hermes' xAI автоматично переноситься.
8. **Повідомляй результати користувачеві** — підсумовуй, що змінив Grok і що залишилося.