---
sidebar_position: 8
sidebar_label: "SMS (Twilio)"
title: "SMS (Twilio)"
description: "Налаштуй Hermes Agent як SMS‑чатбот через Twilio"
---

# Налаштування SMS (Twilio)

Hermes підключається до SMS через API [Twilio](https://www.twilio.com/). Люди надсилають SMS на ваш номер Twilio і отримують відповіді ШІ — той самий діалоговий досвід, що й у Telegram або Discord, лише через звичайні текстові повідомлення.

:::info Shared Credentials
SMS‑gateway використовує ті ж облікові дані, що й необов’язковий [telephony skill](/reference/skills-catalog). Якщо ви вже налаштували Twilio для голосових дзвінків або окремих SMS, gateway працюватиме з тим самим `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` та `TWILIO_PHONE_NUMBER`.
:::

---

## Передумови

- **Обліковий запис Twilio** — [Зареєструйся на twilio.com](https://www.twilio.com/try-twilio) (доступна безкоштовна пробна версія)
- **Номер телефону Twilio** з можливістю SMS
- **Публічно доступний сервер** — Twilio надсилає вебхуки на ваш сервер, коли надходить SMS
- **aiohttp** — `pip install 'hermes-agent[sms]'`

---

## Крок 1: Отримайте облікові дані Twilio

1. Перейдіть у [Twilio Console](https://console.twilio.com/)
2. Скопіюйте **Account SID** та **Auth Token** з панелі
3. Перейдіть у **Phone Numbers → Manage → Active Numbers** — запишіть ваш номер у форматі E.164 (наприклад, `+15551234567`)

---

## Крок 2: Налаштуйте Hermes

### Інтерактивне налаштування (рекомендовано)

```bash
hermes gateway setup
```

Виберіть **SMS (Twilio)** у списку платформ. Майстер запросить ваші облікові дані.

### Ручне налаштування

Додайте до `~/.hermes/.env`:

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

## Крок 3: Налаштуйте вебхук Twilio

Twilio має знати, куди надсилати вхідні повідомлення. У [Twilio Console](https://console.twilio.com/):

1. Перейдіть у **Phone Numbers → Manage → Active Numbers**
2. Клацніть ваш номер телефону
3. У розділі **Messaging → A MESSAGE COMES IN** встановіть:
   - **Webhook**: `https://your-server:8080/webhooks/twilio`
   - **HTTP Method**: `POST`

:::tip Exposing Your Webhook
Якщо ти запускаєш Hermes локально, використай тунель, щоб опублікувати вебхук:

```bash
# Using cloudflared
cloudflared tunnel --url http://localhost:8080

# Using ngrok
ngrok http 8080
```

Вкажи отриману публічну URL як Twilio webhook.
:::

**Встанови `SMS_WEBHOOK_URL` на ту ж URL, яку вказав у Twilio.** Це необхідно для перевірки підпису Twilio — адаптер відмовиться запускатися без цього параметра:

```bash
# Must match the webhook URL in your Twilio Console
SMS_WEBHOOK_URL=https://your-server:8080/webhooks/twilio
```

Порт вебхука за замовчуванням — `8080`. Перевизначити можна так:

```bash
SMS_WEBHOOK_PORT=3000
```

---

## Крок 4: Запусти gateway

```bash
hermes gateway
```

Ти повинен побачити:

```
[sms] Twilio webhook server listening on 127.0.0.1:8080, from: +1555***4567
```

Якщо бачиш `Refusing to start: SMS_WEBHOOK_URL is required`, встанови `SMS_WEBHOOK_URL` на публічну URL, налаштовану у Twilio Console (див. крок 3).

Надішли SMS на свій номер Twilio — Hermes відповість через SMS.

---

## Змінні середовища

| Variable | Required | Description |
|----------|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Yes | Twilio Account SID (починається з `AC`) |
| `TWILIO_AUTH_TOKEN` | Yes | Twilio Auth Token (використовується також для перевірки підпису вебхука) |
| `TWILIO_PHONE_NUMBER` | Yes | Твій номер Twilio (формат E.164) |
| `SMS_WEBHOOK_URL` | Yes | Публічна URL для перевірки підпису Twilio — має збігатися з URL вебхука у Twilio Console |
| `SMS_WEBHOOK_PORT` | No | Порт прослуховування вебхука (за замовчуванням: `8080`) |
| `SMS_WEBHOOK_HOST` | No | Адреса прив’язки вебхука (за замовчуванням: `0.0.0.0`) |
| `SMS_INSECURE_NO_SIGNATURE` | No | Встановити `true`, щоб вимкнути перевірку підпису (лише локальна розробка — **не для продакшн**) |
| `SMS_ALLOWED_USERS` | No | Список номерів у форматі E.164, розділених комами, яким дозволено спілкування |
| `SMS_ALLOW_ALL_USERS` | No | Встановити `true`, щоб дозволити всім (не рекомендовано) |
| `SMS_HOME_CHANNEL` | No | Номер телефону для cron‑завдань / доставки сповіщень |
| `SMS_HOME_CHANNEL_NAME` | No | Відображувана назва домашнього каналу (за замовчуванням: `Home`) |

---

## Специфічна поведінка SMS

- **Тільки простий текст** — Markdown автоматично видаляється, оскільки SMS відображає його як буквальні символи
- **Ліміт 1600 символів** — довгі відповіді розбиваються на кілька повідомлень у природних точках розриву (нові рядки, потім пробіли)
- **Запобігання ехо** — повідомлення з твого власного номера Twilio ігноруються, щоб уникнути циклів
- **Маскування номерів** — номери телефонів замінюються у логах для захисту приватності

---

## Безпека

### Перевірка підпису вебхука

Hermes перевіряє, що вхідні вебхуки дійсно надходять від Twilio, верифікуючи заголовок `X-Twilio-Signature` (HMAC‑SHA1). Це запобігає підмінам підроблених повідомлень.

**`SMS_WEBHOOK_URL` є обов’язковим.** Вкажи публічну URL, налаштовану у Twilio Console. Адаптер відмовиться запускатися без неї.

Для локальної розробки без публічної URL можна вимкнути валідацію:

```bash
# Local dev only — NOT for production
SMS_INSECURE_NO_SIGNATURE=true
```

### Дозволені користувачі

**Gateway за замовчуванням блокує всіх користувачів.** Налаштуй allowlist:

```bash
# Recommended: restrict to specific phone numbers
SMS_ALLOWED_USERS=+15559876543,+15551112222

# Or allow all (NOT recommended for bots with terminal access)
SMS_ALLOW_ALL_USERS=true
```

:::warning
SMS не має вбудованого шифрування. Не використовуйте SMS для чутливих операцій, якщо не розумієте наслідки безпеки. Для чутливих випадків краще обирати Signal або Telegram.
:::

---

## Устранення проблем

### Повідомлення не надходять

1. Перевір, чи правильна і публічно доступна URL вебхука Twilio
2. Переконайся, що `TWILIO_ACCOUNT_SID` та `TWILIO_AUTH_TOKEN` вірні
3. Переглянь Twilio Console → **Monitor → Logs → Messaging** для помилок доставки
4. Переконайся, що твій номер включений у `SMS_ALLOWED_USERS` (або `SMS_ALLOW_ALL_USERS=true`)

### Відповіді не надсилаються

1. Перевір, чи правильно вказано `TWILIO_PHONE_NUMBER` (формат E.164 з `+`)
2. Переконайся, що у твоєму обліковому записі Twilio є номери, здатні надсилати SMS
3. Переглянь логи gateway Hermes на предмет помилок API Twilio

### Конфлікти порту вебхука

Якщо порт 8080 вже зайнятий, зміни його:

```bash
SMS_WEBHOOK_PORT=3001
```

Онови URL вебхука у Twilio Console, щоб він відповідав новому порту.