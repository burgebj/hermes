---
sidebar_position: 7
---

# Справочник команд профиля

Эта страница охватывает все команды, связанные с [профилями Hermes](../user-guide/profiles.md). Для общих команд CLI смотри [Справочник команд CLI](./cli-commands.md).
## `hermes profile`

```bash
hermes profile <subcommand>
```

Команда верхнего уровня для управления профилями. Запуск `hermes profile` без подкоманды выводит справку.

| Подкоманда | Описание |
|------------|----------|
| `list` | Вывести список всех профилей. |
| `use` | Установить активный (по умолчанию) профиль. |
| `create` | Создать новый профиль. |
| `delete` | Удалить профиль. |
| `show` | Показать детали профиля. |
| `alias` | Сгенерировать заново shell‑alias для профиля. |
| `rename` | Переименовать профиль. |
| `export` | Экспортировать профиль в архив tar.gz. |
| `import` | Импортировать профиль из архива tar.gz. |
| `install` | Установить дистрибутив профиля из git‑URL или локального каталога. См. [Profile Distributions](../user-guide/profile-distributions.md). |
| `update` | Повторно получить профиль, управляемый дистрибутивом, и повторно применить его пакет. |
| `info` | Показать метаданные дистрибутива профиля (исходный URL, коммит, дата последнего обновления). |
## `hermes profile list`

```bash
hermes profile list
```

Выводит список всех профилей. Текущий активный профиль отмечен `*`.

**Пример:**

```bash
$ hermes profile list
  default
* work
  dev
  personal
```

Без параметров.
## `hermes profile use`

```bash
hermes profile use <name>
```

Устанавливает профиль `<name>` активным. Все последующие команды `hermes` (без `-p`) будут использовать этот профиль.

| Аргумент | Описание |
|----------|----------|
| `<name>` | Имя профиля для активации. Используй `default`, чтобы вернуться к базовому профилю. |

**Пример:**

```bash
hermes profile use work
hermes profile use default
```
## `hermes profile create`

```bash
hermes profile create <name> [options]
```

Создаёт новый профиль.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Имя нового профиля. Должно быть допустимым именем каталога (буквенно‑цифровое, дефисы, подчёркивания). |
| `--clone` | Скопировать `config.yaml`, `.env` и `SOUL.md` из текущего профиля. |
| `--clone-all` | Скопировать всё (config, memories, skills, sessions, state) из текущего профиля. |
| `--clone-from <profile>` | Клонировать из указанного профиля вместо текущего. Используется вместе с `--clone` или `--clone-all`. |
| `--no-alias` | Не создавать обёртку‑скрипт. |
| `--description "<text>"` | Одно‑ или двухпредложное описание того, в чём этот профиль хорош. Используется оркестратором kanban для маршрутизации задач по роли, а не только по имени профиля. Пропусти и добавь позже через `hermes profile describe`. Сохраняется в `<profile_dir>/profile.yaml`. |
| `--no-skills` | Создать **пустой** профиль без включённых встроенных skill. Записывает маркер `.no-skills` в профиль, чтобы будущие запуски `hermes update` не восстанавливали набор встроенных skill, и запрещает сочетание с `--clone` / `--clone-all` (которые всё равно копируют skill). Полезно для узкоспециализированных профилей оркестратора или песочничных профилей, которым не следует наследовать полный каталог skill. |

Создание профиля **не** делает каталог этого профиля каталогом проекта/рабочего пространства по умолчанию для терминальных команд. Если нужно, чтобы профиль открывался в конкретном проекте, укажи `terminal.cwd` в `config.yaml` этого профиля.

**Примеры:**

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

Читает или задаёт описание профиля. Описание используется оркестратором kanban для маршрутизации задач в зависимости от того, в чём каждый профиль силён, вместо того чтобы угадывать по названию профиля. Сохраняется в `<profile_dir>/profile.yaml`, поэтому сохраняется после перезагрузок и доступно шлюзу.

Без флагов выводит текущее описание (или `(no description set for '<name>')`, если оно пустое).

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Профиль для описания. Требуется, если не использованы `--all --auto`. |
| `--text "<text>"` | Устанавливает описание ровно этим текстом (создано пользователем). Перезаписывает любое существующее описание. |
| `--auto` | Автоматически генерирует 1‑2‑предложное описание с помощью вспомогательного LLM, исходя из установленных у профиля навыков, настроенной модели и имени. Настрой модель в `auxiliary.profile_describer` в `config.yaml`. Автогенерированные описания помечаются `description_auto: true`, чтобы дашборд мог пометить их для проверки. |
| `--overwrite` | При использовании `--auto` заменять также пользовательские описания (по умолчанию: пропускать профили, у которых описание было задано явно). |
| `--all` | При использовании `--auto` обрабатывать каждый профиль, у которого отсутствует описание. |

**Examples:**

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

Удаляет профиль и его псевдоним в оболочке.

| Аргумент / Параметр | Описание |
|-------------------|----------|
| `<name>` | Профиль для удаления. |
| `--yes`, `-y` | Пропустить запрос подтверждения. |

**Пример:**

```bash
hermes profile delete mybot
hermes profile delete mybot --yes
```

:::warning
Это навсегда удалит весь каталог профиля, включая все конфигурации, память, сессии и инструменты. Нельзя удалить текущий активный профиль.
:::
## `hermes profile show`

```bash
hermes profile show <name>
```

Отображает сведения о профиле, включая его домашний каталог, настроенную модель, статус шлюза, количество навыков и состояние файла конфигурации.

Показывается домашний каталог Hermes‑профиля, а не текущий рабочий каталог терминала. Команды терминала начинаются с `terminal.cwd` (или из каталога запуска на локальном бэкенде, когда `cwd: "."`).

| Argument | Description |
|----------|-------------|
| `<name>` | Профиль для просмотра. |

**Пример:**

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

Пересоздаёт скрипт‑обертку алиаса оболочки в `~/.local/bin/<name>`. Полезно, если алиас был случайно удалён или если нужно обновить его после перемещения установки Hermes.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Профиль, для которого создаётся/обновляется алиас. |
| `--remove` | Удалить скрипт‑обертку вместо его создания. |
| `--name <alias>` | Пользовательское имя алиаса (по умолчанию: имя профиля). |

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

Переименовывает профиль. Обновляет каталог и псевдоним командной оболочки.

| Argument | Description |
|----------|-------------|
| `<old-name>` | Текущее имя профиля. |
| `<new-name>` | Новое имя профиля. |

**Example:**

```bash
hermes profile rename mybot assistant
# ~/.hermes/profiles/mybot → ~/.hermes/profiles/assistant
# ~/.local/bin/mybot → ~/.local/bin/assistant
```
## `hermes profile export`

```bash
hermes profile export <name> [options]
```

Экспортирует профиль в виде сжатого архива tar.gz.

| Argument / Option | Описание |
|-------------------|----------|
| `<name>` | Профиль для экспорта. |
| `-o`, `--output <path>` | Путь к выходному файлу (по умолчанию: `<name>.tar.gz`). |

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

Импортирует профиль из архива tar.gz.

| Argument / Option | Description |
|-------------------|-------------|
| `<archive>` | Путь к архиву tar.gz для импорта. |
| `--name <name>` | Имя импортируемого профиля (по умолчанию: берётся из архива). |

**Example:**

```bash
hermes profile import ./work-2026-03-29.tar.gz
# Infers profile name from the archive

hermes profile import ./work-2026-03-29.tar.gz --name work-restored
```
## Команды распределения

:::tip
**Впервые работаешь с распределениями?** Начни с [руководства пользователя «Profile Distributions»](../user-guide/profile-distributions.md) — в нём объясняется, зачем, когда и как использовать распределения, с полными примерами. Ниже представлены сухие ссылки на CLI для тех случаев, когда ты уже знаешь, чего хочешь.
:::

Распределения превращают профиль в совместно используемый, версионированный артефакт, опубликованный как **git‑репозиторий**. Получатель устанавливает распределение одной командой и может позже обновлять его «на месте», не трогая свои локальные памяти, сессии или учётные данные.

`auth.json` и `.env` никогда не входят в распределение — они остаются на машине устанавливающего пользователя.

Пользовательские данные получателя (память, сессии, auth, их собственные правки в `.env`) всегда сохраняются при первоначальной установке и последующих обновлениях.

:::info
`hermes profile export` / `import` по‑прежнему являются правильными командами для **локального резервного копирования и восстановления** профиля на твоём собственном компьютере. Распределение (`install` / `update` / `info`) — отдельная концепция: отправляй профиль через git, чтобы кто‑то ещё мог его установить.
:::

### `hermes profile install`

```bash
hermes profile install <source> [--name <name>] [--alias] [--force] [--yes]
```

Устанавливает распределение профиля из git‑URL или локального каталога.

| Параметр | Описание |
|----------|----------|
| `<source>` | Git‑URL (`github.com/user/repo`, `https://...`, `git@...`, `ssh://`, `git://`) или локальный каталог, содержащий `distribution.yaml` в корне. |
| `--name NAME` | Переопределить имя профиля из манифеста. |
| `--alias` | Также создать оболочку (например, `telemetry` → `hermes -p telemetry`). |
| `--force` | Перезаписать существующий профиль с тем же именем. Пользовательские данные всё равно сохраняются. |
| `-y`, `--yes` | Пропустить запрос подтверждения предварительного просмотра манифеста. |

Установщик показывает манифест, перечисляет требуемые переменные окружения и предупреждает о cron‑задачах перед запросом подтверждения. Требуемые переменные окружения записываются в файл `.env.EXAMPLE`, который ты копируешь в `.env` и заполняешь.

**Примеры:**

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

Повторно клонирует распределение из его записанного источника и применяет обновления. Файлы, принадлежащие распределению (SOUL.md, skills/, cron/, mcp.json), перезаписываются; пользовательские данные (память, сессии, auth, .env) не трогаются.

`config.yaml` сохраняется по умолчанию, чтобы удержать твои локальные переопределения. Передай `--force-config`, чтобы сбросить его к конфигурации, поставляемой в распределении.

### `hermes profile info`

```bash
hermes profile info <name>
```

Выводит манифест распределения профиля — имя, версия, требуемая версия Hermes, автор, требования к переменным окружения, URL/путь источника и метку времени `Installed:`, зафиксированную при последнем `install` или `update`. Полезно для проверки того, что требуется общему профилю перед установкой, и для обнаружения «этот профиль был установлен 6 месяцев назад и не обновлялся».

`hermes profile list` также показывает имя и версию распределения в колонке `Distribution`, а `hermes profile show <name>` / `delete <name>` выводят URL источника, чтобы ты мог сразу увидеть, какие профили пришли из git‑репозитория, а какие созданы локально.

### Приватные распределения

Приватный git‑репозиторий работает как источник распределения без дополнительной конфигурации — установка вызывает твой обычный бинарный `git`, поэтому любая аутентификация, уже настроенная в твоей оболочке (SSH‑ключ, помощник `git credential`, сохранённые HTTPS‑учётные данные GitHub CLI), применяется прозрачно.

```bash
# Uses your SSH key, the same as any other `git clone`
hermes profile install git@github.com:your-org/internal-assistant.git

# Uses your git credential helper
hermes profile install https://github.com/your-org/internal-assistant.git
```

Если при клонировании в терминале появляется запрос учётных данных, он будет передан дальше. Настрой аутентификацию так же, как ты обычно используешь `git clone` для того же репозитория, а затем выполняй установку.

### Манифест распределения (`distribution.yaml`)

Каждое распределение имеет файл `distribution.yaml` в корне своего репозитория:

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

`hermes_requires` поддерживает `>=`, `<=`, `==`, `!=`, `>`, `<` или «голую» версию (рассматривается как `>=`). Установка завершится ошибкой с чётким сообщением, если текущая версия Hermes не удовлетворяет спецификации.

`distribution_owned` — необязательный параметр. Если указан, только перечисленные пути заменяются при обновлении; всё остальное в профиле остаётся пользовательским. Если опущен, применяются значения по умолчанию, указанные выше.

### Публикация распределения

Создание распределения — это просто `git push`:

1. В каталоге профиля создай `distribution.yaml` как минимум с полями `name` и `version`.
2. Инициализируй git‑репозиторий (или используй существующий) и отправь его на GitHub / GitLab / любой хост, откуда Hermes может клонировать.
3. Попроси получателей выполнить `hermes profile install <your-repo-url>`.

Используй git‑теги для версионных релизов — получатели, клонирующие `HEAD`, получат твоё последнее состояние, а ты всегда можешь увеличить `version:` в манифесте.
## `hermes -p` / `hermes --profile`

```bash
hermes -p <name> <command> [options]
hermes --profile <name> <command> [options]
```

Глобальный флаг для выполнения любой команды Hermes в контексте указанного профиля без изменения закреплённого профиля по умолчанию. Переопределяет активный профиль на время выполнения команды.

| Option | Description |
|--------|-------------|
| `-p <name>`, `--profile <name>` | Профиль, используемый для этой команды. |

**Примеры:**

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

Генерирует скрипты автодополнения для оболочки. Включает автодополнения для имён профилей и подкоманд профиля.

| Argument | Description |
|----------|-------------|
| `<shell>` | Оболочка, для которой генерировать автодополнение: `bash`, `zsh` или `fish`. |

**Примеры:**

```bash
# Install completions
hermes completion bash >> ~/.bashrc
hermes completion zsh >> ~/.zshrc
hermes completion fish > ~/.config/fish/completions/hermes.fish

# Reload shell
source ~/.bashrc
```

После установки автодополнение работает для:
- `hermes profile <TAB>` — подкоманды (list, use, create и т.д.)
- `hermes profile use <TAB>` — имена профилей
- `hermes -p <TAB>` — имена профилей
## См. также

- [Руководство пользователя по профилям](../user-guide/profiles.md)
- [Справочник команд CLI](./cli-commands.md)
- [FAQ — раздел «Профили»](./faq.md#profiles)