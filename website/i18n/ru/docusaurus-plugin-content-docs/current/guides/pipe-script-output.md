---
sidebar_position: 12
title: "Перенаправлять вывод скрипта в платформы обмена сообщениями"
description: "Отправляй текст из любого shell‑скрипта, cron‑задачи, CI‑хука или демона мониторинга в Telegram, Discord, Slack, Signal и другие платформы с помощью `hermes send`."
---

# Вывод скрипта в мессенджеры

`hermes send` — небольшой, скриптуемый CLI, который отправляет сообщение в любой мессенджер, уже настроенный в Hermes. Можно сравнить с кроссплатформенным `curl` для уведомлений — не нужен запущенный шлюз, не нужен LLM и не нужно каждый раз вставлять токены ботов в свои скрипты.

Используй его для:

- Мониторинга системы (память, диск, температура GPU, завершение длительной задачи)
- Уведомлений CI/CD (деплой завершён, тест упал)
- Cron‑скриптов, которым нужно прислать результат
- Быстрых одноразовых сообщений из терминала
- Перенаправления вывода любого инструмента (`make | hermes send --to slack:#builds`)

Команда переиспользует те же учётные данные и адаптеры платформ, что и `hermes gateway`, поэтому не требуется отдельная конфигурация.

---

## Быстрый старт

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

## Справочник аргументов

| Флаг | Описание |
|------|----------|
| `-t, --to TARGET` | Куда отправлять. См. [форматы целей](#target-formats). |
| `message` (позиционный) | Текст сообщения. Пропусти, чтобы прочитать из `--file` или stdin. |
| `-f, --file PATH` | Читать тело сообщения из файла. `--file -` принудительно читает stdin. |
| `-s, --subject LINE` | Добавить заголовок/тему перед телом сообщения. |
| `-l, --list` | Вывести список доступных целей. Необязательный позиционный фильтр платформы. |
| `-q, --quiet` | Не выводить ничего в stdout при успехе (только код выхода — удобно для скриптов). |
| `--json` | Вывести сырые JSON‑результаты отправки. |
| `-h, --help` | Показать встроенную справку. |

### Форматы целей

| Формат | Пример | Значение |
|--------|--------|----------|
| `platform` | `telegram` | Отправить в домашний канал, настроенный для платформы |
| `platform:chat_id` | `telegram:-1001234567890` | Конкретный числовой чат / группа / пользователь |
| `platform:chat_id:thread_id` | `telegram:-1001234567890:17585` | Конкретный тред или тема форума в Telegram |
| `platform:#channel` | `discord:#ops` | Человекочитаемое имя канала (разрешается через каталог каналов) |
| `platform:+E164` | `signal:+15551234567` | Платформы, адресуемые по телефону: Signal, SMS, WhatsApp |

Любая платформа, для которой Hermes имеет адаптер, может использоваться в качестве цели: `telegram`, `discord`, `slack`, `signal`, `sms`, `whatsapp`, `matrix`, `mattermost`, `feishu`, `dingtalk`, `wecom`, `weixin`, `email` и другие.

### Коды выхода

| Код | Значение |
|------|----------|
| `0` | Отправка (или список) завершилась успешно |
| `1` | Ошибка доставки на уровне платформы (авторизация, права, сеть) |
| `2` | Ошибка использования / аргументов / конфигурации |

Коды выхода следуют стандартному Unix‑соглашению, поэтому скрипты могут ветвиться по ним так же, как при работе с `curl` или `grep`.

---

## Разрешение тела сообщения

`hermes send` определяет тело сообщения в следующем порядке:

1. **Позиционный аргумент** — `hermes send --to telegram "hi"`
2. **`--file PATH`** — `hermes send --to telegram --file msg.txt`
3. **Поток stdin** — `echo hi | hermes send --to telegram`

Когда stdin — это TTY (нет пайпа), Hermes **не** ждёт ввода — вместо этого будет выдано чёткое сообщение об ошибке использования. Это предотвращает зависание скриптов, если тело сообщения случайно не указано.

---

## Примеры из реального мира

### Мониторинг: оповещения о памяти / диске

Замените разрозненные вызовы `curl https://api.telegram.org/...` в своих watchdog‑скриптах одной переносимой строкой:

```bash
#!/usr/bin/env bash
ram_pct=$(free | awk '/^Mem:/ {printf "%d", $3 * 100 / $2}')
if [ "$ram_pct" -ge 85 ]; then
  hermes send --to telegram --subject "⚠ MEMORY WARNING" \
    "RAM ${ram_pct}% on $(hostname)"
fi
```

Поскольку `hermes send` переиспользует конфигурацию Hermes, тот же скрипт будет работать на любой машине, где установлен Hermes — не нужно вручную экспортировать токены ботов в окружение каждой машины.

:::tip Не отправляй оповещения о самом шлюзе
Для watchdog‑ов, которые могут срабатывать, когда сам шлюз испытывает проблемы (OOM‑оповещения, переполнение диска), лучше использовать минимальный вызов `curl`, а не `hermes send`. Если интерпретатор Python не может загрузиться из‑за сильной нагрузки, ты всё равно захочешь, чтобы это оповещение дошло.
:::

### CI / CD: результаты сборки и тестов

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

### Cron: ежедневный отчёт

```bash
# Crontab entry
0 9 * * * /usr/local/bin/generate-metrics.sh \
  | /home/me/.hermes/bin/hermes send \
      --to telegram --subject "Daily metrics $(date +%Y-%m-%d)"
```

### Длительные задачи: пинг по завершении

```bash
./train.py --epochs 200 && \
  hermes send --to telegram "training done" || \
  hermes send --to telegram "training failed (exit $?)"
```

### Скрипты с `--json` и `--quiet`

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

## Нужно ли запускать шлюз для `hermes send`?

**Обычно — нет.** Для любой платформы, использующей токен бота — Telegram, Discord, Slack, Signal, SMS, WhatsApp Cloud API и большинства остальных — `hermes send` обращается напрямую к REST‑конечному пункту платформы, используя учётные данные из `~/.hermes/.env` и `~/.hermes/config.yaml`. Это отдельный подпроцесс, который завершается сразу после доставки сообщения.

Запущенный шлюз требуется только для **плагин‑платформ**, которые полагаются на постоянное соединение адаптера (например, пользовательский плагин, поддерживающий длительный WebSocket). В этом случае будет выдано чёткое сообщение об ошибке, указывающее на шлюз; запусти его командой `hermes gateway start` и повтори попытку.

---

## Просмотр и поиск целей

Перед отправкой в конкретный канал можно посмотреть, что доступно:

```bash
# Every target across every configured platform
hermes send --list

# Just Telegram targets
hermes send --list telegram

# Machine-readable
hermes send --list --json
```

Список формируется из `~/.hermes/channel_directory.json`, который шлюз обновляет каждые несколько минут, пока работает. Если ты видишь «no channels discovered yet», запусти шлюз один раз (`hermes gateway start`), чтобы он заполнил кэш.

Человекочитаемые имена (`discord:#ops`, `slack:#engineering`) разрешаются через этот кэш во время отправки, так что запоминать числовые ID не требуется.

---

## Сравнение с другими подходами

| Подход | Мультиплатформенный | Переиспользует учётные данные Hermes | Требует шлюз | Лучшее применение |
|--------|--------------------|----------------------------------------|-------------|-------------------|
| `hermes send` | ✅ | ✅ | Нет (бот‑токен) | Всё ниже |
| Прямой `curl` к каждой платформе | Каждый скрипт отдельно | Вручную | Нет | Критические watchdog‑ы |
| Cron‑задача с `--deliver` | ✅ | ✅ | Нет | Плановые задачи агента |
| Инструмент агента `send_message` | ✅ | ✅ | Нет | Внутри цикла агента |

`hermes send` — преднамеренно самая простая поверхность. Если нужен агент, решающий, что сказать, используй инструмент `send_message` из чата или cron‑задачи. Если требуется запланированный запуск с контентом, сгенерированным LLM, используй `cronjob(action='create', prompt=…)` с `deliver='telegram:…'`. Если нужно просто пропустить строку в пайп, выбирай `hermes send`.

---

## Смежные материалы

- [Автоматизировать всё с помощью Cron](/guides/automate-with-cron) — запланированные задачи, чей вывод автоматически доставляется в любой мессенджер.
- [Внутреннее устройство шлюза](/developer-guide/gateway-internals) — роутер доставки, которым пользуется `hermes send` совместно с доставкой из cron.
- [Настройка мессенджеров](/user-guide/messaging/) — одноразовая конфигурация каждой платформы.