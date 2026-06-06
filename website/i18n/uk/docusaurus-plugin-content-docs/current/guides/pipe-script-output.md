---
sidebar_position: 12
title: "Перенаправляй вивід скрипту в платформи обміну повідомленнями"
description: "Надсилай текст з будь‑якого shell‑скрипту, cron‑завдання, CI‑хука або демона моніторингу в Telegram, Discord, Slack, Signal та інші платформи за допомогою `hermes send`."
---

# Pipe Script Output to Messaging Platforms

`hermes send` — це невелика, скриптована CLI, яка надсилає повідомлення на будь‑яку
платформу обміну повідомленнями, яку вже налаштовано в Hermes. Уяви її як
крос‑платформенний `curl` для сповіщень — не потрібен запущений
gateway, не потрібен LLM і не треба повторно вставляти токени ботів
у кожен зі своїх скриптів.

Використовуй її для:

- Моніторингу системи (пам'ять, диск, температура GPU, завершення довготривалої задачі)
- Сповіщень CI/CD (деплой завершено, тест провалився)
- Cron‑скриптів, які мають повідомляти про результати
- Швидких одноразових повідомлень з терміналу
- Перенаправлення виводу будь‑якого інструмента куди завгодно (`make | hermes send --to slack:#builds`)

Команда повторно використовує ті ж облікові дані та адаптери платформ,
що й `hermes gateway`, тому не потрібно налаштовувати другий
конфігураційний шар.

---

## Quick Start

```bash
# Plain text to the home channel for a platform
hermes send --to telegram "deploy finished"

# Pipe in stdout from anything
echo "RAM 92%" | hermes send --to telegram:-1001234567890

# Send a file
hermes send --to discord:#ops --file /tmp/report.md

# Attach a subject/header line
hermes send --to slack:#eng --subject "[CI] build.log" --file build.log

# Thread target (Telegram topic, Discord thread)
hermes send --to telegram:-1001234567890:17585 "threaded reply"

# List every configured target
hermes send --list

# Filter by platform
hermes send --list telegram
```

---

## Argument Reference

| Flag | Description |
|------|-------------|
| `-t, --to TARGET` | Призначення. Див. [target formats](#target-formats). |
| `message` (positional) | Текст повідомлення. Пропусти, щоб прочитати з `--file` або stdin. |
| `-f, --file PATH` | Прочитати тіло з файлу. `--file -` примушує читати зі stdin. |
| `-s, --subject LINE` | Додати заголовок/тему перед тілом. |
| `-l, --list` | Перерахувати доступні цілі. Необов’язковий позиційний фільтр платформи. |
| `-q, --quiet` | Без виводу в stdout при успіху (лише код виходу — ідеально для скриптів). |
| `--json` | Вивести сирий JSON‑результат відправки. |
| `-h, --help` | Показати вбудовану довідку. |

### Target Formats

| Format | Example | Meaning |
|--------|---------|---------|
| `platform` | `telegram` | Надіслати у домашній канал, налаштований для платформи |
| `platform:chat_id` | `telegram:-1001234567890` | Конкретний числовий чат / група / користувач |
| `platform:chat_id:thread_id` | `telegram:-1001234567890:17585` | Конкретна гілка або тема форуму Telegram |
| `platform:#channel` | `discord:#ops` | Людсько‑зручна назва каналу (шукається у каталозі каналів) |
| `platform:+E164` | `signal:+15551234567` | Платформи, що адресуються телефоном: Signal, SMS, WhatsApp |

Будь‑яка платформа, для якої Hermes постачається адаптери, працює як ціль:
`telegram`, `discord`, `slack`, `signal`, `sms`, `whatsapp`, `matrix`,
`mattermost`, `feishu`, `dingtalk`, `wecom`, `weixin`, `email` та інші.

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Надсилання (або перелік) успішне |
| `1` | Помилка доставки на рівні платформи (автентифікація, дозволи, мережа) |
| `2` | Помилка використання / аргументу / конфігурації |

Коди виходу слідують стандартній Unix‑конвенції, тому твої скрипти можуть
гілкуватися за ними так само, як при використанні `curl` чи `grep`.

---

## Message Body Resolution

`hermes send` визначає тіло повідомлення у такому порядку:

1. **Позиційний аргумент** — `hermes send --to telegram "hi"`
2. **`--file PATH`** — `hermes send --to telegram --file msg.txt`
3. **Потік stdin** — `echo hi | hermes send --to telegram`

Коли stdin є TTY (без pipe), Hermes **не** чекає вводу — ти отримаєш
чітку помилку використання. Це запобігає зависанню скриптів, якщо вони
випадково пропустили тіло.

---

## Real-World Examples

### Monitoring: Memory / Disk Alerts

Замініть довільні виклики `curl https://api.telegram.org/...` у своїх watchdog‑ах
одним портативним рядком:

```bash
#!/usr/bin/env bash
ram_pct=$(free | awk '/^Mem:/ {printf "%d", $3 * 100 / $2}')
if [ "$ram_pct" -ge 85 ]; then
  hermes send --to telegram --subject "⚠ MEMORY WARNING" \
    "RAM ${ram_pct}% on $(hostname)"
fi
```

Оскільки `hermes send` повторно використовує твою конфігурацію Hermes, той самий
скрипт працює на будь‑якому хості, де встановлено Hermes — не треба експортувати
токени ботів у середовище кожної машини вручну.

:::tip Don't alert the gateway about itself
Для watchdog‑ів, які можуть спрацьовувати, коли сам gateway зазнає проблем
(OOM‑сповіщення, сповіщення про заповнений диск), продовжуй використовувати
мінімальний виклик `curl` замість `hermes send`. Якщо інтерпретатор Python не
зможе завантажитися через надмірне навантаження, ти все одно захочеш, щоб це
сповіщення вийшло.
:::

### CI / CD: Build and Test Results

```bash
# In .github/workflows/deploy.yml or any CI script
if ./scripts/deploy.sh; then
  hermes send --to slack:#deploys "✅ ${CI_COMMIT_SHA:0:7} deployed"
else
  tail -n 100 deploy.log | hermes send \
    --to slack:#deploys --subject "❌ deploy failed"
  exit 1
fi
```

### Cron: Daily Report

```bash
# Crontab entry
0 9 * * * /usr/local/bin/generate-metrics.sh \
  | /home/me/.hermes/bin/hermes send \
      --to telegram --subject "Daily metrics $(date +%Y-%m-%d)"
```

### Long-Running Tasks: Ping When Done

```bash
./train.py --epochs 200 && \
  hermes send --to telegram "training done" || \
  hermes send --to telegram "training failed (exit $?)"
```

### Scripting with `--json` and `--quiet`

```bash
# Hard-fail a script if delivery fails; don't clutter logs on success
hermes send --to telegram --quiet "keepalive" || {
  echo "Telegram delivery failed" >&2
  exit 1
}

# Capture the message ID for later editing / threading
msg_id=$(hermes send --to discord:#ops --json "build started" \
  | jq -r .message_id)
```

---

## Does `hermes send` Need the Gateway Running?

**Зазвичай ні.** Для будь‑якої платформи з токеном бота — Telegram, Discord,
Slack, Signal, SMS, WhatsApp Cloud API та більшості інших — `hermes send` викликає
REST‑endpoint платформи безпосередньо, використовуючи облікові дані з
`~/.hermes/.env` та `~/.hermes/config.yaml`. Це автономний підпроцес, який
завершується одразу після доставки повідомлення.

Живий gateway потрібен лише для **плагін‑платформ**, які покладаються на
постійне з’єднання адаптера (наприклад, кастомний плагін, що тримає відкритий
WebSocket). У цьому випадку ти отримаєш чітку помилку, що вказує на gateway;
запусти його `hermes gateway start` і спробуй ще раз.

---

## Listing and Discovering Targets

Перед відправкою у конкретний канал можна переглянути, що доступно:

```bash
# Every target across every configured platform
hermes send --list

# Just Telegram targets
hermes send --list telegram

# Machine-readable
hermes send --list --json
```

Список формується з `~/.hermes/channel_directory.json`, який gateway оновлює
кожні кілька хвилин під час роботи. Якщо бачиш «no channels discovered yet»,
запусти gateway один раз (`hermes gateway start`), щоб він заповнив кеш.

Людсько‑зручні назви (`discord:#ops`, `slack:#engineering`) розв’язуються
на основі цього кешу під час відправки, тому не треба запам’ятовувати
числові ідентифікатори.

---

## Comparison with Other Approaches

| Approach | Multi-platform | Reuses Hermes creds | Needs gateway | Best for |
|----------|----------------|---------------------|---------------|----------|
| `hermes send` | ✅ | ✅ | No (bot-token) | Everything below |
| Raw `curl` to each platform | Each scripted separately | Manual | No | Critical watchdogs |
| `cron` job with `--deliver` | ✅ | ✅ | No | Scheduled agent tasks |
| `send_message` agent tool | ✅ | ✅ | No | Inside an agent loop |

`hermes send` навмисно є найпростішим інтерфейсом. Якщо потрібен агент,
який вирішує, що сказати, використай інструмент `send_message` всередині
чату або cron‑завдання. Якщо потрібен запланований запуск з контентом,
згенерованим LLM, використай `cronjob(action='create', prompt=…)` з
`deliver='telegram:…'`. Якщо треба просто передати рядок, беріть `hermes send`.

---

## Related

- [Automate Anything with Cron](/guides/automate-with-cron) — заплановані
  завдання, чий вивід автоматично доставляється на будь‑яку платформу.
- [Gateway Internals](/developer-guide/gateway-internals) — роутер доставки,
  яким користується `hermes send` разом із cron‑доставкою.
- [Messaging Platform Setup](/user-guide/messaging/) — одноразове налаштування
  кожної платформи.