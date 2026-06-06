---
sidebar_position: 8
sidebar_label: "SMS (Twilio)"
title: "SMS (Twilio)"
description: "Настрой Hermes Agent как SMS‑чатбот через Twilio"
---

# Настройка SMS (Twilio)

Hermes подключается к SMS через API [Twilio](https://www.twilio.com/). Люди отправляют сообщения на твой номер Twilio и получают ответы от ИИ — такой же диалоговый опыт, как в Telegram или Discord, но через обычные текстовые сообщения.

:::info Shared Credentials
Шлюз SMS использует те же учётные данные, что и опциональный [telephony skill](/reference/skills-catalog). Если ты уже настроил Twilio для голосовых звонков или разовых SMS, шлюз будет работать с теми же `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` и `TWILIO_PHONE_NUMBER`.
:::

---

## Предварительные требования

- **Учётная запись Twilio** — [зарегистрируйся на twilio.com](https://www.twilio.com/try-twilio) (доступна бесплатная пробная версия)
- **Номер телефона Twilio** с поддержкой SMS
- **Публично доступный сервер** — Twilio отправляет вебхуки на твой сервер, когда приходит SMS
- **aiohttp** — `pip install 'hermes-agent[sms]'`

---

## Шаг 1: Получи учётные данные Twilio

1. Перейди в [Twilio Console](https://console.twilio.com/)
2. Скопируй **Account SID** и **Auth Token** с панели
3. Открой **Phone Numbers → Manage → Active Numbers** — запиши свой номер в формате E.164 (например, `+15551234567`)

---

## Шаг 2: Настрой Hermes

### Интерактивная настройка (рекомендовано)

```bash
hermes gateway setup
```

Выбери **SMS (Twilio)** из списка платформ. Мастер запросит твои учётные данные.

### Ручная настройка

Добавь в `~/.hermes/.env`:

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567

# Security: restrict to specific phone numbers (recommended)
SMS_ALLOWED_USERS=+15559876543,+15551112222

# Optional: set a home channel for cron job delivery
SMS_HOME_CHANNEL=+15559876543
```

---

## Шаг 3: Настрой вебхук Twilio

Twilio должен знать, куда отправлять входящие сообщения. В [Twilio Console](https://console.twilio.com/):

1. Перейди в **Phone Numbers → Manage → Active Numbers**
2. Кликни по своему номеру
3. В разделе **Messaging → A MESSAGE COMES IN** укажи:
   - **Webhook**: `https://your-server:8080/webhooks/twilio`
   - **HTTP Method**: `POST`

:::tip Exposing Your Webhook
Если ты запускаешь Hermes локально, используй туннель, чтобы открыть вебхук наружу:

```bash
# Using cloudflared
cloudflared tunnel --url http://localhost:8080

# Using ngrok
ngrok http 8080
```

Укажи полученный публичный URL в качестве вебхука Twilio.
:::

**Установи `SMS_WEBHOOK_URL` в тот же URL, который указал в Twilio.** Это необходимо для проверки подписи Twilio — адаптер откажется запускаться без него:

```bash
# Must match the webhook URL in your Twilio Console
SMS_WEBHOOK_URL=https://your-server:8080/webhooks/twilio
```

Порт вебхука по умолчанию `8080`. Переопределить можно так:

```bash
SMS_WEBHOOK_PORT=3000
```

---

## Шаг 4: Запусти шлюз

```bash
hermes gateway
```

Ты должен увидеть:

```
[sms] Twilio webhook server listening on 127.0.0.1:8080, from: +1555***4567
```

Если появилось `Refusing to start: SMS_WEBHOOK_URL is required`, установи `SMS_WEBHOOK_URL` в публичный URL, настроенный в консоли Twilio (см. Шаг 3).

Отправь SMS на свой номер Twilio — Hermes ответит через SMS.

---

## Переменные окружения

| Variable | Required | Description |
|----------|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Yes | Twilio Account SID (начинается с `AC`) |
| `TWILIO_AUTH_TOKEN` | Yes | Twilio Auth Token (используется также для проверки подписи вебхука) |
| `TWILIO_PHONE_NUMBER` | Yes | Твой номер Twilio (формат E.164) |
| `SMS_WEBHOOK_URL` | Yes | Публичный URL для проверки подписи Twilio — должен совпадать с URL вебхука в консоли Twilio |
| `SMS_WEBHOOK_PORT` | No | Порт прослушивателя вебхука (по умолчанию: `8080`) |
| `SMS_WEBHOOK_HOST` | No | Адрес привязки вебхука (по умолчанию: `0.0.0.0`) |
| `SMS_INSECURE_NO_SIGNATURE` | No | Установи `true`, чтобы отключить проверку подписи (только для локальной разработки — **не для продакшна**) |
| `SMS_ALLOWED_USERS` | No | Список разрешённых номеров в формате E.164, разделённых запятыми |
| `SMS_ALLOW_ALL_USERS` | No | Установи `true`, чтобы разрешить всем (не рекомендуется) |
| `SMS_HOME_CHANNEL` | No | Номер телефона для cron‑задач / доставки уведомлений |
| `SMS_HOME_CHANNEL_NAME` | No | Отображаемое имя домашнего канала (по умолчанию: `Home`) |

---

## Особенности поведения SMS

- **Только простой текст** — Markdown автоматически удаляется, так как SMS отображает его как обычные символы
- **Ограничение 1600 символов** — более длинные ответы разбиваются на несколько сообщений по естественным границам (переводы строк, затем пробелы)
- **Предотвращение эхо** — сообщения, пришедшие с твоего собственного номера Twilio, игнорируются, чтобы избежать циклов
- **Редактирование номеров** — номера телефонов скрываются в логах для защиты конфиденциальности

---

## Безопасность

### Проверка подписи вебхука

Hermes проверяет, что входящие вебхуки действительно пришли от Twilio, проверяя заголовок `X-Twilio-Signature` (HMAC‑SHA1). Это защищает от подделки сообщений.

**`SMS_WEBHOOK_URL` обязателен.** Укажи публичный URL, настроенный в консоли Twilio. Адаптер откажется запускаться без него.

Для локальной разработки без публичного URL можно отключить проверку:

```bash
# Local dev only — NOT for production
SMS_INSECURE_NO_SIGNATURE=true
```

### Белые списки пользователей

**Шлюз по умолчанию отклоняет всех пользователей.** Настрой белый список:

```bash
# Recommended: restrict to specific phone numbers
SMS_ALLOWED_USERS=+15559876543,+15551112222

# Or allow all (NOT recommended for bots with terminal access)
SMS_ALLOW_ALL_USERS=true
```

:::warning
SMS не имеет встроенного шифрования. Не используй SMS для конфиденциальных операций, если не понимаешь рисков. Для чувствительных сценариев предпочтительнее Signal или Telegram.
:::

---

## Устранение неполадок

### Сообщения не приходят

1. Проверь, что URL вебхука в Twilio указан правильно и доступен публично
2. Убедись, что `TWILIO_ACCOUNT_SID` и `TWILIO_AUTH_TOKEN` корректны
3. Посмотри в Twilio Console → **Monitor → Logs → Messaging** на наличие ошибок доставки
4. Убедись, что твой номер включён в `SMS_ALLOWED_USERS` (или `SMS_ALLOW_ALL_USERS=true`)

### Ответы не отправляются

1. Проверь, что `TWILIO_PHONE_NUMBER` указан правильно (формат E.164 с `+`)
2. Убедись, что в твоей учётной записи Twilio есть номера, поддерживающие SMS
3. Проверь логи шлюза Hermes на наличие ошибок API Twilio

### Конфликт порта вебхука

Если порт 8080 уже занят, измени его:

```bash
SMS_WEBHOOK_PORT=3001
```

Обнови URL вебхука в консоли Twilio, чтобы он соответствовал новому порту.