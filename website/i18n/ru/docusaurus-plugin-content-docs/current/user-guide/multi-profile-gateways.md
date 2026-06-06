---
sidebar_position: 4
---

# Запуск нескольких шлюзов одновременно

Эксплуатируй несколько [профилей](./profiles.md) — каждый со своими токенами ботов, сессиями и памятью — как управляемые сервисы на одной машине. На этой странице рассматриваются операционные вопросы: одновременный запуск всех, просмотр логов по профилям, предотвращение сна хоста и восстановление после типичных особенностей launchd/systemd.

Если ты запускаешь только один Hermes‑агент, эта страница тебе не нужна — смотри [Profiles](./profiles.md) для базовой информации.

## Когда использовать

Тебе нужен такой набор, когда у тебя два и более Hermes‑агентов, которые должны быть онлайн одновременно. Частые причины:

- Личный помощник в одном боте Telegram и агент‑программист в другом
- По одному агенту на члена семьи или по одному на рабочее пространство Slack
- Инстансы «песочница» + «продакшн» одной конфигурации
- Исследовательский агент + писательский агент + бот, запускаемый cron — каждый с изолированной памятью и инструментами

Каждый профиль уже получает собственный LaunchAgent (`ai.hermes.gateway-<name>.plist`) или сервис пользователя systemd (`hermes-gateway-<profile>.service`). В этом руководстве добавлены шаблоны для их коллективного управления.

## Быстрый старт

```bash
# Create profiles (once)
hermes profile create coder
hermes profile create personal-bot
hermes profile create research

# Configure each
coder setup
personal-bot setup
research setup

# Install each gateway as a managed service
coder gateway install
personal-bot gateway install
research gateway install

# Start them all
coder gateway start
personal-bot gateway start
research gateway start
```

Вот и всё — три независимых агента, каждый в собственном процессе, автоматически перезапускающихся при падении и при входе пользователя в систему.

## Запуск, остановка или перезапуск всех шлюзов одновременно

CLI поставляется с командами жизненного цикла для отдельного профиля. Чтобы выполнить их для всех профилей, оберни их в цикл оболочки. Помести фрагмент ниже в `~/.local/bin/hermes-gateways` и сделай его исполняемым (`chmod +x`):

```sh
#!/bin/sh
set -eu

# Add or remove profile names here as you create / delete profiles.
profiles="default coder personal-bot research"

usage() {
  echo "Usage: hermes-gateways {start|stop|restart|status|list}"
}

run_for_profile() {
  profile="$1"
  action="$2"
  if [ "$profile" = "default" ]; then
    hermes gateway "$action"
  else
    hermes -p "$profile" gateway "$action"
  fi
}

action="${1:-}"
case "$action" in
  start|stop|restart|status)
    for profile in $profiles; do
      echo "==> $action $profile"
      run_for_profile "$profile" "$action"
    done
    ;;
  list)
    hermes gateway list
    ;;
  *)
    usage
    exit 2
    ;;
esac
```

Затем:

```bash
hermes-gateways start      # start every configured profile
hermes-gateways stop       # stop every configured profile
hermes-gateways restart    # restart all
hermes-gateways status     # status across all
hermes-gateways list       # delegates to `hermes gateway list`
```

:::tip
Профиль `default` вызывается командой `hermes gateway <action>` (без `-p`), а не `hermes -p default gateway <action>`. Обёртка выше поддерживает обе формы.
:::

## Управление отдельным профилем

Команды‑ярлыки, которые устанавливает каждый профиль:

```bash
coder gateway run        # foreground (Ctrl-C to stop)
coder gateway start      # start the managed service
coder gateway stop       # stop the managed service
coder gateway restart    # restart
coder gateway status     # status
coder gateway install    # create the LaunchAgent / systemd unit
coder gateway uninstall  # remove the service file
```

Они эквивалентны `hermes -p coder gateway <action>` — удобно, если псевдоним профиля не находится в `PATH` или если ты выбираешь профили динамически из скрипта.

## Файлы сервисов

Каждый профиль устанавливает свой сервис с уникальным именем, поэтому установки никогда не конфликтуют:

| Platform | Path                                                              |
| -------- | ----------------------------------------------------------------- |
| macOS    | `~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist`        |
| Linux    | `~/.config/systemd/user/hermes-gateway-<profile>.service`         |

Профиль по умолчанию сохраняет исторические имена: `ai.hermes.gateway.plist` / `hermes-gateway.service`.

## Просмотр логов

Каждый профиль пишет в свои файлы журналов:

```bash
# Default profile
tail -f ~/.hermes/logs/gateway.log
tail -f ~/.hermes/logs/gateway.error.log

# Named profile
tail -f ~/.hermes/profiles/<name>/logs/gateway.log
tail -f ~/.hermes/profiles/<name>/logs/gateway.error.log
```

Потоковый вывод логов всех профилей одновременно:

```bash
tail -f ~/.hermes/logs/gateway.log ~/.hermes/profiles/*/logs/gateway.log
```

У CLI также есть структурированный просмотрщик журналов:

```bash
hermes logs --tail              # follow default profile
hermes -p coder logs --tail     # follow one profile
hermes logs --help              # filters, levels, JSON output
```

## Определение, что именно запущено

```bash
hermes profile list             # profiles + model + gateway state
hermes-gateways status          # full status across every profile
launchctl list | grep hermes    # macOS — PIDs and labels
systemctl --user list-units 'hermes-gateway-*'   # Linux — units
```

## Редактирование конфигурации

Каждый профиль хранит конфигурацию в собственном каталоге:

```
~/.hermes/profiles/<name>/
├── .env              # API keys, bot tokens (chmod 600)
├── config.yaml       # model, provider, toolsets, gateway settings
└── SOUL.md           # personality / system prompt
```

Профиль по умолчанию использует директорию `~/.hermes/` напрямую с теми же тремя файлами.

Редактировать их можно любым редактором или через CLI:

```bash
hermes config set model.model anthropic/claude-sonnet-4    # default profile
coder config set model.model openai/gpt-5                  # named profile
```

После изменения `.env` или `config.yaml` перезапусти затронутый шлюз:

```bash
coder gateway restart
# or, for everything:
hermes-gateways restart
```

## Не давать хосту засыпать

Процесс шлюза может работать весь день, но ОС всё равно будет пытаться перейти в спящий режим при бездействии. Два подхода:

### macOS — `caffeinate`

`caffeinate` встроен в macOS и предотвращает сон, пока он запущен. Установки не требуются.

```bash
caffeinate -dis                    # block display, idle, and system sleep
caffeinate -dis -t 28800           # same, auto-exit after 8 hours
caffeinate -i -w $(cat ~/.hermes/gateway.pid) &   # awake while default gateway runs

# Persistent: run in background and forget
nohup caffeinate -dis >/dev/null 2>&1 &
disown

# Inspect / stop
pmset -g assertions | grep -iE 'caffeinate|prevent|user is active'
pkill caffeinate
```

| Flag   | Effect                                            |
| ------ | ------------------------------------------------- |
| `-d`   | блокировать сон дисплея                           |
| `-i`   | блокировать сон системы при бездействии (по умолчанию) |
| `-m`   | блокировать сон диска                              |
| `-s`   | блокировать системный сон (только на Mac с питанием от сети) |
| `-u`   | имитировать активность пользователя (не позволяет заблокировать экран) |
| `-t N` | автоматически выйти через `N` секунд               |
| `-w P` | выйти, когда процесс с PID `P` завершится          |

:::warning Закрытие крышки всё равно переводит Mac в сон
`caffeinate` не может переопределить аппаратный сон при закрытой крышке ноутбуков Mac. Чтобы работать с закрытой крышкой, измени настройки Energy Saver / Battery или используй сторонний инструмент.
:::

### Linux — `systemd-inhibit` или `loginctl`

```bash
# Inhibit suspend while a command runs
systemd-inhibit --what=idle:sleep --who=hermes --why="gateways running" \
  sleep infinity &

# Allow user services to keep running after logout (recommended)
sudo loginctl enable-linger "$USER"
```

После включения «lingering» пользовательские юниты systemd (включая `hermes-gateway-<profile>.service`) продолжают работать после отключения SSH и перезагрузок.

## Безопасность конфликтов токенов

Каждый профиль должен использовать уникальные токены ботов для каждой платформы. Если два профиля используют один и тот же токен Telegram, Discord, Slack, WhatsApp или Signal, второй шлюз откажется запускаться с ошибкой, указывающей конфликтующий профиль.

Для аудита:

```bash
grep -H 'TELEGRAM_BOT_TOKEN\|DISCORD_BOT_TOKEN' \
     ~/.hermes/.env ~/.hermes/profiles/*/.env
```

## Обновление кода

`hermes update` один раз скачивает последнюю версию кода и синхронно добавляет новые встроенные инструменты во все профили:

```bash
hermes update
hermes-gateways restart
```

Модифицированные пользователем инструменты никогда не перезаписываются.

## Устранение неполадок

### «Could not find service in domain for user gui: 501»

Ты выполнил `hermes gateway start` после предыдущего `hermes gateway stop`. Команда `stop` в CLI полностью выполняет `launchctl unload`, удаляя сервис из реестра launchd. CLI перехватывает эту конкретную ошибку при `start` и автоматически перезагружает plist (`↻ launchd job was unloaded; reloading service definition`). Сервис запускается нормально. Исправлять ничего не нужно.

### Устаревший PID после краха

Если шлюз профиля показывает `not running`, но процесс всё ещё жив:

```bash
ps -ef | grep "hermes_cli.*-p <profile>"
cat ~/.hermes/profiles/<profile>/gateway.pid
kill -TERM <pid>          # graceful
kill -KILL <pid>          # if that fails after a few seconds
<profile> gateway start
```

### Принудительный жёсткий сброс одного сервиса

```bash
# macOS
launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist
launchctl load   ~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist

# Linux
systemctl --user restart hermes-gateway-<profile>.service
```

### Проверка состояния

```bash
hermes doctor                  # default profile
hermes -p <profile> doctor     # one profile
```