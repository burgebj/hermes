---
sidebar_position: 2
---

# Профілі: Запуск кількох агентів

Запусти кілька незалежних Hermes агентів на одному комп'ютері — кожен зі своїм **конфігом**, **API‑ключами**, **пам'яттю**, **сесіями**, **skills** та станом **gateway**.
## Що таке профілі?

Профіль — це окремий домашній каталог Hermes. Кожен профіль має власний каталог, що містить його власний `config.yaml`, `.env`, `SOUL.md`, пам’ять, сесії, навички, cron‑завдання та базу даних стану. Профілі дозволяють запускати окремі агенти для різних цілей — кодового помічника, особистого бота, дослідницького агента — без змішування стану Hermes.

Коли ти створюєш профіль, він автоматично стає власною командою. Створи профіль під назвою `coder`, і одразу матимеш `coder chat`, `coder setup`, `coder gateway start` тощо.
## Швидкий старт

```bash
hermes profile create coder       # creates profile + "coder" command alias
coder setup                       # configure API keys and model
coder chat                        # start chatting
```

Ось і все. `coder` тепер є власним профілем Hermes зі своєю конфігурацією, пам'яттю та станом.
## Створення профілю

:::tip
Найшвидше налаштування: запусти `hermes setup --portal` всередині нового профілю, щоб одразу підключити моделі + інструменти. Дивись [Nous Portal](/integrations/nous-portal).
:::

### Порожній профіль

```bash
hermes profile create mybot
```

Створює новий профіль з вбудованими навичками. Запусти `mybot setup`, щоб налаштувати API‑ключі, модель і токени шлюзу.

Якщо плануєш використовувати цей профіль як канбан‑робітника (або хочеш, щоб канбан‑оркестратор направляв роботу до нього), передай `--description "<role>"` під час створення, щоб оркестратор знав, у чому ти сильний:

```bash
hermes profile create researcher --description "Reads source code and external docs, writes findings."
```

Ти також можеш задати або автоматично згенерувати опис пізніше за допомогою `hermes profile describe` — дивись [Посібник з канбан](./features/kanban#auto-vs-manual-orchestration) для повної моделі маршрутизації.

### Клонування лише конфігурації (`--clone`)

```bash
hermes profile create work --clone
```

Копіює `config.yaml`, `.env` та `SOUL.md` твоєї поточної профілю у новий профіль. Ті ж API‑ключі та модель, але нові сесії та пам'ять. Відредагуй `~/.hermes/profiles/work/.env` для інших API‑ключів або `~/.hermes/profiles/work/SOUL.md` для іншої особистості.

### Клонування всього (`--clone-all`)

```bash
hermes profile create backup --clone-all
```

Копіює **все** — конфіг, API‑ключі, особистість, всю пам'ять, повну історію сесій, навички, cron‑завдання, плагіни. Повний знімок. Корисно для резервних копій або форку агента, який вже має контекст.

### Клонування з конкретного профілю

```bash
hermes profile create work --clone --clone-from coder
```

:::tip Honcho memory + profiles
Коли Honcho увімкнено, `--clone` автоматично створює виділеного AI‑партнера для нового профілю, залишаючись у тому ж користувацькому робочому просторі. Кожен профіль будує власні спостереження та ідентичність. Дивись [Honcho -- Multi-agent / Profiles](./features/memory-providers.md#honcho) для деталей.
:::
## Використання профілів

### Псевдоніми команд

Кожен профіль автоматично отримує псевдонім команди у `~/.local/bin/<name>`:

```bash
coder chat                    # chat with the coder agent
coder setup                   # configure coder's settings
coder gateway start           # start coder's gateway
coder doctor                  # check coder's health
coder skills list             # list coder's skills
coder config set model.default anthropic/claude-sonnet-4
```

Псевдонім працює з будь‑якою підкомандою hermes — це просто `hermes -p <name>` під капотом.

### Прапорець `-p`

Ти також можеш явно вказати профіль у будь‑якій команді:

```bash
hermes -p coder chat
hermes --profile=coder doctor
hermes chat -p coder -q "hello"    # works in any position
```

### Прив’язаний за замовчуванням (`hermes profile use`)

```bash
hermes profile use coder
hermes chat                   # now targets coder
hermes tools                  # configures coder's tools
hermes profile use default    # switch back
```

Встановлює профіль за замовчуванням, щоб прості команди `hermes` використовували його. Подібно до `kubectl config use-context`.

### Де ти знаходишся

CLI завжди показує, який профіль активний:

- **Підказка**: `coder ❯` замість `❯`
- **Банер**: Показує `Profile: coder` під час запуску
- **`hermes profile`**: Показує назву поточного профілю, шлях, модель, стан шлюзу.
## Профілі vs робочі простори vs пісочниці

Профілі часто плутають з робочими просторами або пісочницями, але це різні речі:

- **Профіль** надає Hermes власний каталог стану: `config.yaml`, `.env`, `SOUL.md`, сесії, пам'ять, логи, cron‑завдання та стан **gateway**.
- **Робочий простір** або **робочий каталог** — це місце, звідки стартують термінальні команди. Це контролюється окремо параметром `terminal.cwd`.
- **Пісочниця** — це те, що обмежує доступ до файлової системи. Профілі **не** ізолюють агента.

На бекенді терміналу `local` за замовчуванням агент має такий самий доступ до файлової системи, як і твій користувацький обліковий запис. Профіль не заважає йому отримувати доступ до папок поза каталогом профілю.

Якщо потрібно, щоб профіль запускався в конкретній папці проєкту, встанови явний абсолютний `terminal.cwd` у `config.yaml` цього профілю:

```yaml
terminal:
  backend: local
  cwd: /absolute/path/to/project
```

Використання `cwd: "."` на локальному бекенді означає «каталог, з якого був запущений Hermes», а не «каталог профілю».

Також зауваж:

- `SOUL.md` може направляти модель, але не встановлює межі робочого простору.
- Зміни в `SOUL.md` набувають чинності лише у новій сесії. Існуючі сесії можуть продовжувати використовувати старий стан підказки.
- Запитувати модель «у якому каталозі ти знаходишся?» не є надійним тестом ізоляції. Якщо потрібен передбачуваний стартовий каталог для інструментів, встанови `terminal.cwd` явно.
## Запуск шлюзів

Кожен профіль запускає свій власний шлюз як окремий процес зі своїм токеном бота:

```bash
coder gateway start           # starts coder's gateway
assistant gateway start       # starts assistant's gateway (separate process)
```

### Різні токени ботів

Кожен профіль має свій власний файл `.env`. Налаштуй різний токен бота Telegram/Discord/Slack у кожному:

```bash
# Edit coder's tokens
nano ~/.hermes/profiles/coder/.env

# Edit assistant's tokens
nano ~/.hermes/profiles/assistant/.env
```

### Безпека: блокування токенів

Якщо два профілі випадково використовують один і той самий токен бота, другий шлюз буде заблокований з чіткою помилкою, що вказує на конфліктний профіль. Підтримується для Telegram, Discord, Slack, WhatsApp та Signal.

### Постійні служби

```bash
coder gateway install         # creates hermes-gateway-coder systemd/launchd service
assistant gateway install     # creates hermes-gateway-assistant service
```

Кожен профіль отримує власну назву служби. Вони працюють незалежно.

:::note Inside the official Docker image
Per-profile gateways are supervised by [s6-overlay](https://github.com/just-containers/s6-overlay) (PID 1 in the container), so `hermes profile create <name>` automatically registers an s6 service slot at `/run/service/gateway-<name>/`. `hermes -p <name> gateway start/stop/restart` dispatches to `s6-svc` instead of spawning a bare process — crashes are auto-restarted and `docker restart` preserves the previously-running set of gateways. See [Per-profile gateway supervision](/user-guide/docker#per-profile-gateway-supervision) for details.
:::
## Налаштування профілів

Кожен профіль має власні:

- **`config.yaml`** — модель, провайдер, набори інструментів, усі налаштування
- **`.env`** — API‑ключі, токени ботів
- **`SOUL.md`** — особистість і інструкції

```bash
coder config set model.default anthropic/claude-sonnet-4
echo "You are a focused coding assistant." > ~/.hermes/profiles/coder/SOUL.md
```

Якщо ти хочеш, щоб цей профіль за замовчуванням працював у певному проєкті, також встанови його власний `terminal.cwd`:

```bash
coder config set terminal.cwd /absolute/path/to/project
```
## Оновлення

`hermes update` завантажує код один раз (спільний) і синхронізує нові вбудовані **skills** до **всіх** профілів автоматично:

```bash
hermes update
# → Code updated (12 commits)
# → Skills synced: default (up to date), coder (+2 new), assistant (+2 new)
```

**Skills**, змінені користувачем, ніколи не перезаписуються.
## Керування профілями

```bash
hermes profile list           # show all profiles with status
hermes profile show coder     # detailed info for one profile
hermes profile rename coder dev-bot   # rename (updates alias + service)
hermes profile export coder   # export to coder.tar.gz
hermes profile import coder.tar.gz   # import from archive
```
## Видалення профілю

```bash
hermes profile delete coder
```

Це зупиняє gateway, видаляє службу systemd/launchd, прибирає псевдонім команди та стирає всі дані профілю. Тебе попросять ввести назву профілю для підтвердження.

Використай `--yes`, щоб пропустити підтвердження: `hermes profile delete coder --yes`

:::note
Ти не можеш видалити профіль за замовчуванням (`~/.hermes`). Щоб видалити все, використай `hermes uninstall`.
:::
## Tab completion

```bash
# Bash
eval "$(hermes completion bash)"

# Zsh
eval "$(hermes completion zsh)"
```

Додай рядок у свій `~/.bashrc` або `~/.zshrc` для постійного автодоповнення. Додає автодоповнення імен профілів після `-p`, підкоманд профілю та команд верхнього рівня.
## Як це працює

Профілі використовують змінну середовища `HERMES_HOME`. Коли ти запускаєш `coder chat`, скрипт‑обгортка встановлює `HERMES_HOME=~/.hermes/profiles/coder` перед запуском hermes. Оскільки понад 119 файлів у кодовій базі отримують шляхи через `get_hermes_home()`, стан Hermes автоматично обмежується каталогом профілю — конфігурація, сесії, пам'ять, skills, база стану, PID шлюзу, журнали та cron‑завдання.

Це окремо від робочого каталогу терміналу. Виконання інструменту починається з `terminal.cwd` (або каталогу запуску, коли `cwd: "."` у локальному бекенді), а не автоматично з `HERMES_HOME`.

Типовим профілем є просто `~/.hermes`. Міграція не потрібна — існуючі інсталяції працюють ідентично.
## Поширення профілів як дистрибутиви

Профіль, який ти створив на одному комп’ютері, можна упакувати у **git‑репозиторій** і встановити однією командою на іншому комп’ютері — на твоїй власній робочій станції, ноутбуці колеги або в середовищі користувача спільноти. У спільному пакеті містяться SOUL, конфіг, skills, cron‑завдання та MCP connections. Облікові дані, пам’ять і сесії залишаються прив’язаними до конкретного комп’ютера.

```bash
# Install a whole agent from a git repo
hermes profile install github.com/you/research-bot --alias

# Update later when the author ships a new version (keeps your memories + .env)
hermes profile update research-bot
```

Дивись **[Profile Distributions: Share a Whole Agent](./profile-distributions.md)** для повного посібника — створення, публікація, семантика оновлень, модель безпеки та сценарії використання.