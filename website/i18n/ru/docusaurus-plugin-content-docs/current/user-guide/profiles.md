---
sidebar_position: 2
---

# Профили: запуск нескольких агентов

Запусти несколько независимых Hermes‑agents на одной машине — каждый со своей конфигурацией, API‑ключами, памятью, сессиями, skills и состоянием gateway.
## Что такое профили?

Профиль — это отдельный домашний каталог Hermes. Каждый профиль получает собственный каталог, содержащий свой `config.yaml`, `.env`, `SOUL.md`, память, сессии, **skills**, cron jobs и базу данных состояния. Профили позволяют запускать отдельные агенты для разных целей — помощник‑программист, личный бот, исследовательский агент — без смешения состояния Hermes.

Когда ты создаёшь профиль, он автоматически получает собственную команду. Создай профиль с именем `coder`, и сразу получишь `coder chat`, `coder setup`, `coder gateway start` и т.д.
## Быстрый старт

```bash
hermes profile create coder       # creates profile + "coder" command alias
coder setup                       # configure API keys and model
coder chat                        # start chatting
```

Готово. `coder` теперь стал собственным профилем Hermes со своей конфигурацией, памятью и состоянием.
## Создание профиля

:::tip
Самый быстрый способ настройки: выполнить `hermes setup --portal` внутри нового профиля, чтобы сразу подключить модели + инструменты. См. [Nous Portal](/integrations/nous-portal).
:::

### Пустой профиль

```bash
hermes profile create mybot
```

Создаёт новый профиль с предустановленными навыками. Выполни `mybot setup`, чтобы настроить API‑ключи, модель и токены шлюза.

Если планируешь использовать этот профиль как kanban‑worker (или хочешь, чтобы оркестратор kanban направлял работу к нему), передай `--description "<role>"` при создании, чтобы оркестратор знал, в чём он хорош:

```bash
hermes profile create researcher --description "Reads source code and external docs, writes findings."
```

Позже можно задать или автоматически сгенерировать описание с помощью `hermes profile describe` — см. [руководство по Kanban](./features/kanban#auto-vs-manual-orchestration) для полной модели маршрутизации.

### Клонирование только конфигурации (`--clone`)

```bash
hermes profile create work --clone
```

Копирует `config.yaml`, `.env` и `SOUL.md` текущего профиля в новый профиль. Те же API‑ключи и модель, но новые сессии и память. Отредактируй `~/.hermes/profiles/work/.env` для изменения API‑ключей или `~/.hermes/profiles/work/SOUL.md` для изменения личности.

### Клонирование всего (`--clone-all`)

```bash
hermes profile create backup --clone-all
```

Копирует **всё** — конфигурацию, API‑ключи, личность, всю память, полную историю сессий, навыки, cron‑задачи, плагины. Полный снимок. Полезно для резервного копирования или форка агента, у которого уже есть контекст.

### Клонирование из конкретного профиля

```bash
hermes profile create work --clone --clone-from coder
```

:::tip Honcho memory + profiles
Когда включён Honcho, `--clone` автоматически создаёт выделенного AI‑пира для нового профиля, при этом используя тот же пользовательский рабочий каталог. Каждый профиль формирует свои наблюдения и идентичность. См. [Honcho — Multi-agent / Profiles](./features/memory-providers.md#honcho) для подробностей.
:::
## Использование профилей

### Псевдонимы команд

Каждому профилю автоматически назначается псевдоним команды в `~/.local/bin/<name>`:

```bash
coder chat                    # chat with the coder agent
coder setup                   # configure coder's settings
coder gateway start           # start coder's gateway
coder doctor                  # check coder's health
coder skills list             # list coder's skills
coder config set model.default anthropic/claude-sonnet-4
```

Псевдоним работает с любой подкомандой `hermes` — это просто `hermes -p <name>` «под капотом».

### Флаг `-p`

Можно явно указать профиль в любой команде:

```bash
hermes -p coder chat
hermes --profile=coder doctor
hermes chat -p coder -q "hello"    # works in any position
```

### Прикреплённый профиль по умолчанию (`hermes profile use`)

```bash
hermes profile use coder
hermes chat                   # now targets coder
hermes tools                  # configures coder's tools
hermes profile use default    # switch back
```

Устанавливает профиль по умолчанию, так что обычные команды `hermes` используют его. Аналогично `kubectl config use-context`.

### Как узнать, какой профиль активен

CLI всегда показывает, какой профиль активен:

- **Подсказка**: `coder ❯` вместо `❯`
- **Баннер**: При запуске отображает `Profile: coder`
- **`hermes profile`**: Показывает имя текущего профиля, путь, модель, статус шлюза.
## Профили vs рабочие пространства vs sandboxing

Профили часто путают с рабочими пространствами или sandbox‑ами, но это разные вещи:

- **Профиль** предоставляет Hermes собственный каталог состояния: `config.yaml`, `.env`, `SOUL.md`, сессии, память, логи, cron‑задачи и состояние шлюза.
- **Рабочее пространство** или **рабочий каталог** — это место, откуда стартуют команды терминала. Оно управляется отдельно параметром `terminal.cwd`.
- **Sandbox** — это то, что ограничивает доступ к файловой системе. Профили **не** sandbox‑ят агент.

На бэкенде терминала `local` по умолчанию агент имеет тот же доступ к файловой системе, что и твой пользовательский аккаунт. Профиль не препятствует доступу к папкам за пределами каталога профиля.

Если нужно, чтобы профиль запускался в конкретной папке проекта, задай явный абсолютный `terminal.cwd` в `config.yaml` этого профиля:

```yaml
terminal:
  backend: local
  cwd: /absolute/path/to/project
```

Использование `cwd: "."` на локальном бэкенде означает «каталог, из которого был запущен Hermes», а не «каталог профиля».

Также обрати внимание:

- `SOUL.md` может направлять модель, но не устанавливает границу рабочего пространства.
- Изменения в `SOUL.md` вступают в силу чисто при новой сессии. Существующие сессии могут продолжать использовать старое состояние подсказки.
- Спрашивать модель «в каком каталоге ты находишься?» — ненадёжный тест изоляции. Если нужен предсказуемый стартовый каталог для инструментов, задавай `terminal.cwd` явно.
## Запуск шлюзов

Каждый профиль запускает свой шлюз как отдельный процесс со своим токеном бота:

```bash
coder gateway start           # starts coder's gateway
assistant gateway start       # starts assistant's gateway (separate process)
```

### Разные токены ботов

У каждого профиля есть свой файл `.env`. Настрой в нём отдельный токен бота Telegram/Discord/Slack:

```bash
# Edit coder's tokens
nano ~/.hermes/profiles/coder/.env

# Edit assistant's tokens
nano ~/.hermes/profiles/assistant/.env
```

### Безопасность: блокировки токенов

Если два профиля случайно используют один и тот же токен бота, второй шлюз будет заблокирован с чёткой ошибкой, указывающей конфликтующий профиль. Поддерживается для Telegram, Discord, Slack, WhatsApp и Signal.

### Постоянные сервисы

```bash
coder gateway install         # creates hermes-gateway-coder systemd/launchd service
assistant gateway install     # creates hermes-gateway-assistant service
```

Каждому профилю присваивается собственное имя сервиса. Они работают независимо.

:::note В официальном Docker‑образе
Шлюзы per‑profile контролируются [s6-overlay](https://github.com/just-containers/s6-overlay) (PID 1 в контейнере), поэтому `hermes profile create <name>` автоматически регистрирует слот s6‑service по пути `/run/service/gateway-<name>/`. `hermes -p <name> gateway start/stop/restart` передаёт управление `s6-svc` вместо запуска отдельного процесса — краши автоматически перезапускаются, а `docker restart` сохраняет ранее запущенный набор шлюзов. См. «Per‑profile gateway supervision» (/user-guide/docker#per-profile-gateway-supervision) для подробностей.
:::
## Настройка профилей

Каждый профиль имеет собственные:

- **`config.yaml`** — модель, провайдер, наборы инструментов, все настройки
- **`.env`** — API‑ключи, токены ботов
- **`SOUL.md`** — персональность и инструкции

```bash
coder config set model.default anthropic/claude-sonnet-4
echo "You are a focused coding assistant." > ~/.hermes/profiles/coder/SOUL.md
```

Если ты хочешь, чтобы этот профиль по умолчанию использовался в конкретном проекте, также задай значение `terminal.cwd` для него:

```bash
coder config set terminal.cwd /absolute/path/to/project
```
## Обновление

`hermes update` один раз получает код (общий) и автоматически синхронизирует новые встроенные навыки **для всех** профилей:

```bash
hermes update
# → Code updated (12 commits)
# → Skills synced: default (up to date), coder (+2 new), assistant (+2 new)
```

Навыки, изменённые пользователем, никогда не перезаписываются.
## Управление профилями

```bash
hermes profile list           # show all profiles with status
hermes profile show coder     # detailed info for one profile
hermes profile rename coder dev-bot   # rename (updates alias + service)
hermes profile export coder   # export to coder.tar.gz
hermes profile import coder.tar.gz   # import from archive
```
## Удаление профиля

```bash
hermes profile delete coder
```

Это останавливает gateway, удаляет службу systemd/launchd, удаляет псевдоним команды и удаляет все данные профиля. Тебя попросят ввести имя профиля для подтверждения.

Используй `--yes`, чтобы пропустить подтверждение: `hermes profile delete coder --yes`

:::note
Нельзя удалить профиль по умолчанию (`~/.hermes`). Чтобы удалить всё, используй `hermes uninstall`.
:::
## Автодополнение по Tab

```bash
# Bash
eval "$(hermes completion bash)"

# Zsh
eval "$(hermes completion zsh)"
```

Добавь строку в свой `~/.bashrc` или `~/.zshrc` для постоянного автодополнения. Дополняет имена профилей после `-p`, подкоманды, относящиеся к профилю, и команды верхнего уровня.
## Как это работает

Профили используют переменную окружения `HERMES_HOME`. Когда ты запускаешь `coder chat`, обёртка‑скрипт задаёт `HERMES_HOME=~/.hermes/profiles/coder` перед запуском hermes. Поскольку более 119 файлов в кодовой базе получают пути через `get_hermes_home()`, состояние Hermes автоматически ограничивается каталогом профиля — конфигурация, сессии, память, навыки, база данных состояния, PID шлюза, журналы и задания cron.

Это отдельный механизм от текущего рабочего каталога терминала. Выполнение инструмента начинается из `terminal.cwd` (или из каталога запуска, когда `cwd: "."` на локальном бэкенде), а не автоматически из `HERMES_HOME`.

Профиль по умолчанию — это просто `~/.hermes`. Миграция не требуется — существующие установки работают идентично.
## Совместное использование профилей как дистрибутивов

Профиль, который ты создал на одной машине, можно упаковать в **git repository** и установить одной командой на другой машине — на своей рабочей станции, ноутбуке коллеги или в окружении пользователя сообщества. В общий пакет входят SOUL, конфигурация, навыки, задания cron и подключения MCP. Учётные данные, память и сессии остаются привязанными к конкретной машине.

```bash
# Install a whole agent from a git repo
hermes profile install github.com/you/research-bot --alias

# Update later when the author ships a new version (keeps your memories + .env)
hermes profile update research-bot
```

См. **[Распределения профилей: поделиться целым агентом](./profile-distributions.md)** для полного руководства — создание, публикация, семантика обновлений, модель безопасности и варианты использования.