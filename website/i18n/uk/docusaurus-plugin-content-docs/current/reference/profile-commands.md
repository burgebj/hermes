---
sidebar_position: 7
---

# Довідник команд профілю

Ця сторінка охоплює всі команди, пов’язані з [профілями Hermes](../user-guide/profiles.md). Для загальних CLI‑команд дивись [довідник команд CLI](./cli-commands.md).
## `hermes profile`

```bash
hermes profile <subcommand>
```

Команда верхнього рівня для керування профілями. Запуск `hermes profile` без підкоманди показує довідку.

| Підкоманда | Опис |
|------------|------|
| `list` | Переглянути всі профілі. |
| `use` | Встановити активний (за замовчуванням) профіль. |
| `create` | Створити новий профіль. |
| `delete` | Видалити профіль. |
| `show` | Показати деталі профілю. |
| `alias` | Перегенерувати shell‑alias для профілю. |
| `rename` | Перейменувати профіль. |
| `export` | Експортувати профіль у архів tar.gz. |
| `import` | Імпортувати профіль з архіву tar.gz. |
| `install` | Встановити дистрибутив профілю з git‑URL або локальної теки. Дивись [Profile Distributions](../user-guide/profile-distributions.md). |
| `update` | Повторно отримати дистрибутив‑керований профіль і повторно застосувати його пакет. |
| `info` | Показати метадані дистрибутиву профілю (URL‑джерело, коміт, останнє оновлення). |
## `hermes profile list`

```bash
hermes profile list
```

Виводить список усіх профілів. Поточний активний профіль позначений `*`.

**Приклад:**

```bash
$ hermes profile list
  default
* work
  dev
  personal
```

Без параметрів.
## `hermes profile use`

```bash
hermes profile use <name>
```

Встановлює `<name>` як активний профіль. Усі наступні команди `hermes` (без `-p`) будуть використовувати цей профіль.

| Аргумент | Опис |
|----------|------|
| `<name>` | Ім'я профілю для активації. Використай `default`, щоб повернутися до базового профілю. |

**Example:**

```bash
hermes profile use work
hermes profile use default
```
## `hermes profile create`

```bash
hermes profile create <name> [options]
```

Створює новий профіль.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Ім’я нового профілю. Має бути коректною назвою каталогу (латинські літери, цифри, дефіси, підкреслення). |
| `--clone` | Скопіювати `config.yaml`, `.env` і `SOUL.md` з поточного профілю. |
| `--clone-all` | Скопіювати все (config, memory, skills, sessions, state) з поточного профілю. |
| `--clone-from <profile>` | Клонувати з вказаного профілю замість поточного. Використовується разом з `--clone` або `--clone-all`. |
| `--no-alias` | Пропустити створення скрипту‑обгортки. |
| `--description "<text>"` | Опис у один‑ або два‑речення, що характеризує, у чому цей профіль сильний. Використовується оркестратором kanban для маршрутизації завдань за роллю, а не лише за назвою профілю. Пропусти і додай пізніше за допомогою `hermes profile describe`. Зберігається у `<profile_dir>/profile.yaml`. |
| `--no-skills` | Створити **порожній** профіль без вбудованих навичок. У профіль записується маркер `.no-skills`, щоб майбутні запуски `hermes update` не відновлювали набір навичок, і команда не комбінується з `--clone`/`--clone-all` (які все одно копіювали б навички). Корисно для вузькоспеціалізованих оркестраторських або пісочничних профілів, які не повинні успадковувати повний каталог навичок. |

Створення профілю **не** робить його каталог каталогом проєкту/робочим простором за замовчуванням для команд терміналу. Якщо потрібно, щоб профіль відкривався в певному проєкті, встанови `terminal.cwd` у `config.yaml` цього профілю.

**Приклади:**

```bash
# Blank profile — needs full setup
hermes profile create mybot

# Clone config only from current profile
hermes profile create work --clone

# Clone everything from current profile
hermes profile create backup --clone-all

# Clone config from a specific profile
hermes profile create work2 --clone --clone-from work
```
## `hermes profile describe`

```bash
hermes profile describe [<name>] [options]
```

Прочитати або встановити опис профілю. Опис використовується оркестратором kanban для маршрутизації завдань на основі того, у чому кожен профіль сильний, а не лише за назвою профілю. Зберігається у `<profile_dir>/profile.yaml`, тому зберігається після перезавантаження та доступний шлюзу.

Якщо не вказано жодних прапорців, виводить поточний опис (або `(no description set for '<name>')`, якщо він порожній).

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Профіль, який потрібно описати. Обов’язковий, якщо не використано `--all --auto`. |
| `--text "<text>"` | Встановити опис саме цим текстом (створений користувачем). Перезаписує будь‑який існуючий опис. |
| `--auto` | Автоматично згенерувати 1‑2‑реченний опис за допомогою допоміжного LLM, виходячи з встановлених навичок профілю, налаштованої моделі та назви. Налаштуй модель у `auxiliary.profile_describer` у `config.yaml`. Автогенеровані описи позначаються `description_auto: true`, щоб дашборд міг позначити їх для перегляду. |
| `--overwrite` | Разом з `--auto` замінює також описи, створені користувачем (за замовчуванням: пропускати профілі, у яких опис був встановлений явно). |
| `--all` | Разом з `--auto` обробляє кожен профіль, у якого відсутній опис. |

**Приклади:**

```bash
# Read the current description
hermes profile describe researcher

# Set it explicitly
hermes profile describe researcher --text "Reads source code and writes findings."

# Let the LLM generate one
hermes profile describe researcher --auto

# Fill in descriptions for every profile that doesn't have one
hermes profile describe --all --auto
```
## `hermes profile delete`

```bash
hermes profile delete <name> [options]
```

Видаляє профіль і його shell‑аліас.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Профіль, який треба видалити. |
| `--yes`, `-y` | Пропустити запит підтвердження. |

**Example:**

```bash
hermes profile delete mybot
hermes profile delete mybot --yes
```

:::warning
Це назавжди видалить весь каталог профілю, включаючи всю конфігурацію, пам'ять, сесії та навички. Не можна видалити поточний активний профіль.
:::
## `hermes profile show`

```bash
hermes profile show <name>
```

Відображає деталі профілю, включаючи його домашній каталог, налаштовану модель, статус **gateway**, кількість **skills** та стан файлу конфігурації.

Показується домашній каталог Hermes профілю, а не робочий каталог терміналу. Команди терміналу стартують з `terminal.cwd` (або з каталогу запуску на локальному бекенді, коли `cwd: "."`).

| Argument | Description |
|----------|-------------|
| `<name>` | Профіль для перегляду. |

**Example:**

```bash
$ hermes profile show work
Profile: work
Path:    ~/.hermes/profiles/work
Model:   anthropic/claude-sonnet-4 (anthropic)
Gateway: stopped
Skills:  12
.env:    exists
SOUL.md: exists
Alias:   ~/.local/bin/work
```
## `hermes profile alias`

```bash
hermes profile alias <name> [options]
```

Перегенерує скрипт‑аліас оболонки у `~/.local/bin/<name>`. Корисно, якщо аліас випадково видалено або потрібно оновити його після переміщення встановлення Hermes.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Профіль, для якого створюється/оновлюється аліас. |
| `--remove` | Видалити скрипт‑обгортку замість його створення. |
| `--name <alias>` | Користувацька назва аліасу (за замовчуванням: назва профілю). |

**Example:**

```bash
hermes profile alias work
# Creates/updates ~/.local/bin/work

hermes profile alias work --name mywork
# Creates ~/.local/bin/mywork

hermes profile alias work --remove
# Removes the wrapper script
```
## `hermes profile rename`

```bash
hermes profile rename <old-name> <new-name>
```

Перейменовує профіль. Оновлює директорію та аліас оболонки.

| Аргумент | Опис |
|----------|------|
| `<old-name>` | Поточна назва профілю. |
| `<new-name>` | Нова назва профілю. |

**Приклад:**

```bash
hermes profile rename mybot assistant
# ~/.hermes/profiles/mybot → ~/.hermes/profiles/assistant
# ~/.local/bin/mybot → ~/.local/bin/assistant
```
## `hermes profile export`

```bash
hermes profile export <name> [options]
```

Експортує профіль у вигляді стисненого архіву tar.gz.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Профіль для експорту. |
| `-o`, `--output <path>` | Шлях до вихідного файлу (за замовчуванням: `<name>.tar.gz`). |

**Example:**

```bash
hermes profile export work
# Creates work.tar.gz in the current directory

hermes profile export work -o ./work-2026-03-29.tar.gz
```
## `hermes profile import`

```bash
hermes profile import <archive> [options]
```

Імпортує профіль з архіву tar.gz.

| Argument / Option | Description |
|-------------------|-------------|
| `<archive>` | Шлях до архіву tar.gz, який потрібно імпортувати. |
| `--name <name>` | Ім'я для імпортованого профілю (за замовчуванням: визначається з архіву). |

**Example:**

```bash
hermes profile import ./work-2026-03-29.tar.gz
# Infers profile name from the archive

hermes profile import ./work-2026-03-29.tar.gz --name work-restored
```
## Команди розповсюдження

:::tip
**Новачок у розповсюдженнях?** Почни з [користувацького посібника «Розповсюдження профілів»](../user-guide/profile-distributions.md) — він охоплює чому, коли і як з повними прикладами. Нижче наведено суху довідку CLI для випадків, коли ти вже знаєш, чого хочеш.
:::

Розповсюдження перетворює профіль у придатний до спільного використання, версіонований артефакт, опублікований як **git‑репозиторій**. Одержувач встановлює розповсюдження однією командою і може оновити його на місці пізніше, не торкаючись своїх локальних пам’ятей, сесій чи облікових даних.

`auth.json` і `.env` ніколи не входять до розповсюдження — вони залишаються на машині користувача, який встановлює.

Дані користувача одержувача (пам’яті, сесії, auth, його власні правки до `.env`) завжди зберігаються під час початкової інсталяції та подальших оновлень.

:::info
`hermes profile export` / `import` залишаються правильними командами для **локального резервного копіювання та відновлення** профілю на твоїй машині. Розповсюдження (`install` / `update` / `info`) — це окрема концепція: доставити профіль через git, щоб інша особа могла його встановити.
:::

### `hermes profile install`

```bash
hermes profile install <source> [--name <name>] [--alias] [--force] [--yes]
```

Встановлює розповсюдження профілю з git‑URL або локального каталогу.

| Параметр | Опис |
|----------|------|
| `<source>` | Git‑URL (`github.com/user/repo`, `https://...`, `git@...`, `ssh://`, `git://`) або локальний каталог, що містить `distribution.yaml` у корені. |
| `--name NAME` | Перезаписати назву профілю з маніфесту. |
| `--alias` | Також створити оболонковий скрипт (наприклад, `telemetry` → `hermes -p telemetry`). |
| `--force` | Перезаписати існуючий профіль з такою ж назвою. Дані користувача все одно зберігаються. |
| `-y`, `--yes` | Пропустити підтверджувальний запит попереднього перегляду маніфесту. |

Інсталятор показує маніфест, перелік необхідних змінних середовища та попереджає про cron‑завдання перед запитом підтвердження. Необхідні змінні середовища записуються у файл `.env.EXAMPLE`, який треба скопіювати в `.env` і заповнити.

**Приклади:**

```bash
# Install from a GitHub repo (shorthand)
hermes profile install github.com/kyle/telemetry-distribution --alias

# Install from a full HTTPS git URL
hermes profile install https://github.com/kyle/telemetry-distribution.git

# Install from SSH
hermes profile install git@github.com:kyle/telemetry-distribution.git

# Install from a local directory during development
hermes profile install ./telemetry/
```

### `hermes profile update`

```bash
hermes profile update <name> [--force-config] [--yes]
```

Переклонує розповсюдження з його зафіксованого джерела та застосовує оновлення. Файли, що належать розповсюдженню (SOUL.md, skills/, cron/, mcp.json) перезаписуються; дані користувача (пам’яті, сесії, auth, .env) не торкаються.

`config.yaml` зберігається за замовчуванням, щоб залишити твої локальні перевизначення. Передай `--force-config`, щоб скинути його до конфігурації, що постачається з розповсюдженням.

### `hermes profile info`

```bash
hermes profile info <name>
```

Виводить маніфест розповсюдження профілю — назву, версію, вимоги до Hermes, автора, вимоги до змінних середовища, URL/шлях джерела та мітку часу `Installed:`, записану під час останньої `install`‑ації або `update`‑у. Корисно, щоб перевірити, що потрібне спільному профілю перед встановленням, і щоб помітити «цей профіль був встановлений 6 місяців тому і не оновлювався».

`hermes profile list` також показує назву та версію розповсюдження у колонці `Distribution`, а `hermes profile show <name>` / `delete <name>` виводять URL джерела, щоб ти одразу бачив, які профілі походять з git‑репозиторію, а які створені локально.

### Приватні розповсюдження

Приватний git‑репозиторій працює як джерело розповсюдження без додаткових налаштувань — інсталяція викликає твою звичну `git`‑бінарну, тому будь‑яка автентифікація, яку вже налаштовано в оболонці (SSH‑ключ, допоміжна програма `git credential`, збережені HTTPS‑облікові дані GitHub CLI) застосовується прозоро.

```bash
# Uses your SSH key, the same as any other `git clone`
hermes profile install git@github.com:your-org/internal-assistant.git

# Uses your git credential helper
hermes profile install https://github.com/your-org/internal-assistant.git
```

Якщо клонування запитує облікові дані інтерактивно в терміналі під час інсталяції, цей запит проходить. Спочатку налаштуй автентифікацію так, як зазвичай використовуєш `git clone` до того ж репозиторію, а потім виконуй інсталяцію.

### Маніфест розповсюдження (`distribution.yaml`)

Кожне розповсюдження має `distribution.yaml` у корені свого репозиторію:

```yaml
name: telemetry
version: 0.1.0
description: "Compliance monitoring harness"
hermes_requires: ">=0.12.0"
author: "Your Name"
license: "MIT"
env_requires:
  - name: OPENAI_API_KEY
    description: "OpenAI API key"
    required: true
  - name: GRAPHITI_MCP_URL
    description: "Memory graph URL"
    required: false
    default: "http://127.0.0.1:8000/sse"
distribution_owned:   # optional; defaults to SOUL.md, config.yaml,
                      #   mcp.json, skills/, cron/, distribution.yaml
  - SOUL.md
  - skills/compliance/
  - cron/
```

`hermes_requires` підтримує `>=`, `<=`, `==`, `!=`, `>`, `<` або «голу» версію (вважається `>=`). Якщо поточна версія Hermes не задовольняє специфікацію, інсталяція завершується з чіткою помилкою.

`distribution_owned` — необов’язковий параметр. Якщо задано, лише ці шляхи замінюються під час оновлення; все інше в профілі залишається користувацьким. Якщо не вказано, застосовуються значення за замовчуванням, зазначені вище.

### Публікація розповсюдження

Створення розповсюдження — це просто `git push`:

1. У каталозі профілю створити `distribution.yaml` принаймні з полями `name` і `version`.
2. Ініціалізувати git‑репозиторій (або використати існуючий) і запушити його на GitHub / GitLab / будь‑який хост, з якого Hermes може клонувати.
3. Попросити одержувачів виконати `hermes profile install <your-repo-url>`.

Використовуй git‑теги для версіонованих випусків — одержувачі, які клонують `HEAD`, отримають твою останню стану, а ти завжди можеш підвищити `version:` у маніфесті.
## `hermes -p` / `hermes --profile`

```bash
hermes -p <name> <command> [options]
hermes --profile <name> <command> [options]
```

Глобальний прапорець, що дозволяє запускати будь‑яку команду Hermes під конкретним профілем, не змінюючи «липкого» профілю за замовчуванням. Перевизначає активний профіль на час виконання команди.

| Option | Description |
|--------|-------------|
| `-p <name>`, `--profile <name>` | Профіль, який слід використати для цієї команди. |

**Examples:**

```bash
hermes -p work chat -q "Check the server status"
hermes --profile dev gateway start
hermes -p personal skills list
hermes -p work config edit
```
## `hermes completion`

```bash
hermes completion <shell>
```

Генерує скрипти автодоповнення для оболонки. Включає автодоповнення імен профілів та підкоманд профілю.

| Argument | Description |
|----------|-------------|
| `<shell>` | Оболочка, для якої генеруються автодоповнення: `bash`, `zsh` або `fish`. |

**Приклади:**

```bash
# Install completions
hermes completion bash >> ~/.bashrc
hermes completion zsh >> ~/.zshrc
hermes completion fish > ~/.config/fish/completions/hermes.fish

# Reload shell
source ~/.bashrc
```

Після встановлення автодоповнення працює для:
- `hermes profile <TAB>` — підкоманди (list, use, create тощо)
- `hermes profile use <TAB>` — імена профілів
- `hermes -p <TAB>` — імена профілів
## Дивись також

- [Посібник користувача профілів](../user-guide/profiles.md)
- [Довідник команд CLI](./cli-commands.md)
- [FAQ — розділ «Профілі»](./faq.md#profiles)