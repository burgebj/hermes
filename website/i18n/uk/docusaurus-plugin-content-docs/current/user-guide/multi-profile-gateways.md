---
sidebar_position: 4
---

# Запуск багатьох шлюзів одночасно

Керуйте кількома [профілями](./profiles.md) — кожен зі своїми токенами бота, сесіями та пам’яттю — як керованими службами на одному комп’ютері. На цій сторінці розглядаються операційні питання: запуск усіх одночасно, перегляд логів за профілями, запобігання сплячому режиму хоста та відновлення після поширених особливостей launchd/systemd.

Якщо ти запускаєш лише одного Hermes‑агента, ця сторінка тобі не потрібна — дивись [Profiles](./profiles.md) для базової інформації.

## Коли це використовувати

Ти захочеш таку конфігурацію, коли маєш два або більше Hermes‑агентів, які повинні бути онлайн одночасно. Типові причини:

- Особистий асистент у одному Telegram‑боті і агент‑програміст у іншому
- Один агент на члена сім’ї або один на робочий простір Slack
- Пісочниця + продакшн‑екземпляри однієї конфігурації
- Дослідницький агент + письмовий агент + бот, керований cron — кожен з ізольованою пам’яттю та інструментами

Кожен профіль вже отримує свій LaunchAgent (`ai.hermes.gateway-<name>.plist`) або службу systemd користувача (`hermes-gateway-<name>.service`). У цьому посібнику додаються шаблони для їх колективного керування.

## Швидкий старт

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

Ось і все — три незалежних агенти, кожен у власному процесі, що автоматично перезапускаються при збоях і при вході користувача.

## Запуск, зупинка або перезапуск усіх шлюзів одночасно

CLI постачається з командами життєвого циклу для окремих профілів. Щоб виконати їх для всіх профілів, обгорни їх у цикл оболонки. Помісти фрагмент нижче у `~/.local/bin/hermes-gateways` і зроби його виконуваним `chmod +x`:

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

Потім:

```bash
hermes-gateways start      # start every configured profile
hermes-gateways stop       # stop every configured profile
hermes-gateways restart    # restart all
hermes-gateways status     # status across all
hermes-gateways list       # delegates to `hermes gateway list`
```

:::tip
Профіль `default` цілиться командою `hermes gateway <action>` (без `-p`), а не `hermes -p default gateway <action>`. Наведена вище обгортка обробляє обидві форми.
:::

## Керування одним профілем

Команди‑скорочення, які встановлює кожен профіль:

```bash
coder gateway run        # foreground (Ctrl-C to stop)
coder gateway start      # start the managed service
coder gateway stop       # stop the managed service
coder gateway restart    # restart
coder gateway status     # status
coder gateway install    # create the LaunchAgent / systemd unit
coder gateway uninstall  # remove the service file
```

Вони еквівалентні `hermes -p coder gateway <action>` — корисно, коли псевдонім профілю не знаходиться у `PATH` або коли ти динамічно цілиться профілями зі скрипту.

## Файли служб

Кожен профіль встановлює свою службу з унікальною назвою, тому установки ніколи не конфліктують:

| Платформа | Шлях                                                               |
| --------- | ----------------------------------------------------------------- |
| macOS     | `~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist`        |
| Linux     | `~/.config/systemd/user/hermes-gateway-<profile>.service`        |

Профіль за замовчуванням зберігає історичні назви: `ai.hermes.gateway.plist` / `hermes-gateway.service`.

## Перегляд логів

Кожен профіль записує у власні файли журналу:

```bash
# Default profile
tail -f ~/.hermes/logs/gateway.log
tail -f ~/.hermes/logs/gateway.error.log

# Named profile
tail -f ~/.hermes/profiles/<name>/logs/gateway.log
tail -f ~/.hermes/profiles/<name>/logs/gateway.error.log
```

Транслюй журнали всіх профілів одночасно:

```bash
tail -f ~/.hermes/logs/gateway.log ~/.hermes/profiles/*/logs/gateway.log
```

У CLI також є структурований переглядач журналу:

```bash
hermes logs --tail              # follow default profile
hermes -p coder logs --tail     # follow one profile
hermes logs --help              # filters, levels, JSON output
```

## Визначення, що саме запущено

```bash
hermes profile list             # profiles + model + gateway state
hermes-gateways status          # full status across every profile
launchctl list | grep hermes    # macOS — PIDs and labels
systemctl --user list-units 'hermes-gateway-*'   # Linux — units
```

## Редагування конфігурації

Кожен профіль зберігає свою конфігурацію у власному каталозі:

```
~/.hermes/profiles/<name>/
├── .env              # API keys, bot tokens (chmod 600)
├── config.yaml       # model, provider, toolsets, gateway settings
└── SOUL.md           # personality / system prompt
```

Профіль за замовчуванням використовує `~/.hermes/` безпосередньо з тими ж трьома файлами.

Редагуй їх будь‑яким редактором або через CLI:

```bash
hermes config set model.model anthropic/claude-sonnet-4    # default profile
coder config set model.model openai/gpt-5                  # named profile
```

Після зміни `.env` або `config.yaml` перезапусти відповідний шлюз:

```bash
coder gateway restart
# or, for everything:
hermes-gateways restart
```

## Підтримка хоста у стані «не спати»

Процес шлюзу може працювати цілий день, проте операційна система все ж намагатиметься перейти у сплячий режим під час бездіяльності. Два підходи:

### macOS — `caffeinate`

`caffeinate` вбудовано в macOS і запобігає сну, доки він працює. Встановлення не потрібне.

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

| Прапорець | Ефект                                            |
| --------- | ------------------------------------------------ |
| `-d`      | блокувати сон дисплея                            |
| `-i`      | блокувати бездіяльний системний сон (за замовчуванням) |
| `-m`      | блокувати сон диска                              |
| `-s`      | блокувати системний сон (тільки Mac на AC)       |
| `-u`      | імітувати активність користувача (запобігає блокуванню екрану) |
| `-t N`    | автоматичний вихід через `N` секунд               |
| `-w P`    | вихід, коли процес з PID `P` завершується          |

:::warning Закриття кришки все одно переводить Mac у сон
`caffeinate` не може переважити апаратний сон при закритій кришці MacBook‑ів. Для роботи з закритою кришкою змінюй налаштування Energy Saver / Battery або використовуй сторонній інструмент.
:::

### Linux — `systemd-inhibit` або `loginctl`

```bash
# Inhibit suspend while a command runs
systemd-inhibit --what=idle:sleep --who=hermes --why="gateways running" \
  sleep infinity &

# Allow user services to keep running after logout (recommended)
sudo loginctl enable-linger "$USER"
```

Після ввімкнення «lingering» твої юзер‑служби systemd (включаючи `hermes-gateway-<profile>.service`) продовжуватимуть працювати під час від’єднань SSH та перезавантажень.

## Безпека конфліктів токенів

Кожен профіль має використовувати унікальні токени ботів для кожної платформи. Якщо два профілі діляться одним токеном Telegram, Discord, Slack, WhatsApp або Signal, другий шлюз відмовиться запускатися, вивівши помилку з назвою конфліктного профілю.

Для аудиту:

```bash
grep -H 'TELEGRAM_BOT_TOKEN\|DISCORD_BOT_TOKEN' \
     ~/.hermes/.env ~/.hermes/profiles/*/.env
```

## Оновлення коду

`hermes update` завантажує останній код один раз і синхронізує нові вбудовані інструменти у кожен профіль:

```bash
hermes update
hermes-gateways restart
```

Модифіковані користувачем інструменти ніколи не перезаписуються.

## Усунення проблем

### «Could not find service in domain for user gui: 501»

Ти запустив `hermes gateway start` після попереднього `hermes gateway stop`. Команда `stop` у CLI виконує повний `launchctl unload`, який видаляє службу з реєстру launchd. CLI ловить цю конкретну помилку під час `start` і автоматично перезавантажує plist (`↻ launchd job was unloaded; reloading service definition`). Служба запускається нормально. Нічого виправляти не треба.

### Застарілий PID після збою

Якщо шлюз профілю показує `not running`, а процес все ще живий:

```bash
ps -ef | grep "hermes_cli.*-p <profile>"
cat ~/.hermes/profiles/<profile>/gateway.pid
kill -TERM <pid>          # graceful
kill -KILL <pid>          # if that fails after a few seconds
<profile> gateway start
```

### Примусове жорстке скидання однієї служби

```bash
# macOS
launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist
launchctl load   ~/Library/LaunchAgents/ai.hermes.gateway-<profile>.plist

# Linux
systemctl --user restart hermes-gateway-<profile>.service
```

### Перевірка стану здоров’я

```bash
hermes doctor                  # default profile
hermes -p <profile> doctor     # one profile
```