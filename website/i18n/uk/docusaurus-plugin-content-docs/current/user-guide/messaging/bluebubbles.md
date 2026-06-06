# BlueBubbles (iMessage)

Підключи Hermes до Apple iMessage через [BlueBubbles](https://bluebubbles.app/) — безкоштовний, open‑source сервер macOS, який мостить iMessage до будь‑якого пристрою.

## Вимоги

- **Mac** (завжди ввімкнений), на якому працює [BlueBubbles Server](https://bluebubbles.app/)
- Apple ID, ввійшовший у Messages.app на цьому Mac
- BlueBubbles Server v1.0.0+ (вебхуки потребують саме цієї версії)
- Мережева доступність між Hermes і сервером BlueBubbles

## Налаштування

### 1. Install BlueBubbles Server

Завантаж і встанови з [bluebubbles.app](https://bluebubbles.app/). Заверши майстер налаштування — увійди за допомогою Apple ID і налаштуй спосіб підключення (локальна мережа, Ngrok, Cloudflare або Dynamic DNS).

### 2. Get your Server URL and Password

У BlueBubbles Server → **Settings → API** запиши:
- **Server URL** (наприклад, `http://192.168.1.10:1234`)
- **Server Password**

### 3. Configure Hermes

Запусти майстер налаштування:

```bash
hermes gateway setup
```

Вибери **BlueBubbles (iMessage)** і введи URL сервера та пароль.

Або встанови змінні середовища безпосередньо у `~/.hermes/.env`:

```bash
BLUEBUBBLES_SERVER_URL=http://192.168.1.10:1234
BLUEBUBBLES_PASSWORD=your-server-password
```

### 4. Authorize Users

Обери один підхід:

**DM Pairing (рекомендовано):**
Коли хтось пише тобі в iMessage, Hermes автоматично надсилає код парингу. Підтверди його за допомогою:
```bash
hermes pairing approve bluebubbles <CODE>
```
Використай `hermes pairing list`, щоб переглянути очікуючі коди та схвалені облікові записи.

**Pre-authorize specific users** (у `~/.hermes/.env`):
```bash
BLUEBUBBLES_ALLOWED_USERS=user@icloud.com,+15551234567
```

**Open access** (у `~/.hermes/.env`):
```bash
BLUEBUBBLES_ALLOW_ALL_USERS=true
```

### 5. Start the Gateway

```bash
hermes gateway run
```

Hermes під’єднається до твого сервера BlueBubbles, зареєструє вебхук і почне слухати повідомлення iMessage.

## Як це працює

```
iMessage → Messages.app → BlueBubbles Server → Webhook → Hermes
Hermes → BlueBubbles REST API → Messages.app → iMessage
```

- **Inbound:** BlueBubbles надсилає події вебхука локальному слухачу, коли надходять нові повідомлення. Без опитування — миттєва доставка.
- **Outbound:** Hermes надсилає повідомлення через REST API BlueBubbles.
- **Media:** Підтримуються зображення, голосові повідомлення, відео та документи в обох напрямках. Вхідні вкладення завантажуються та кешуються локально для обробки агентом.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BLUEBUBBLES_SERVER_URL` | Yes | — | BlueBubbles server URL |
| `BLUEBUBBLES_PASSWORD` | Yes | — | Server password |
| `BLUEBUBBLES_WEBHOOK_HOST` | No | `127.0.0.1` | Webhook listener bind address |
| `BLUEBUBBLES_WEBHOOK_PORT` | No | `8645` | Webhook listener port |
| `BLUEBUBBLES_WEBHOOK_PATH` | No | `/bluebubbles-webhook` | Webhook URL path |
| `BLUEBUBBLES_HOME_CHANNEL` | No | — | Phone/email for cron delivery |
| `BLUEBUBBLES_ALLOWED_USERS` | No | — | Comma-separated authorized users |
| `BLUEBUBBLES_ALLOW_ALL_USERS` | No | `false` | Allow all users |

Автоматичне позначення повідомлень як прочитаних керується ключем `send_read_receipts` у `platforms.bluebubbles.extra` файлу `~/.hermes/config.yaml` (за замовчуванням: `true`). Відповідної змінної середовища немає.

## Features

### Text Messaging
Надсилай і отримуй iMessage. Markdown автоматично видаляється для чистої текстової доставки.

### Rich Media
- **Images:** Фото відображаються у розмові iMessage нативно
- **Voice messages:** Аудіофайли надсилаються як голосові повідомлення iMessage
- **Videos:** Відеовкладення
- **Documents:** Файли надсилаються як вкладення iMessage

### Tapback Reactions
Любов, лайк, дизлайк, сміх, підкреслення та запитання. Потрібен [Private API helper](https://docs.bluebubbles.app/helper-bundle/installation) BlueBubbles.

### Typing Indicators
Показує «typing…» у розмові iMessage, доки агент обробляє запит. Потрібен Private API.

### Read Receipts
Автоматично позначає повідомлення як прочитані після обробки. Потрібен Private API.

### Chat Addressing
Можеш адресувати чати за електронною поштою або номером телефону — Hermes автоматично перетворює їх у GUID‑и чатів BlueBubbles. Не потрібно використовувати сирий формат GUID.

## Private API

Деякі функції потребують [Private API helper](https://docs.bluebubbles.app/helper-bundle/installation):
- Tapback reactions
- Typing indicators
- Read receipts
- Створення нових чатів за адресою

Без Private API базовий текстовий обмін і медіа працюватимуть.

## Troubleshooting

### "Cannot reach server"
- Перевір, чи правильний URL сервера і чи ввімкнений Mac
- Переконайся, що BlueBubbles Server запущений
- Перевір мережеву доступність (фаєрвол, переадресація портів)

### Messages not arriving
- Переконайся, що вебхук зареєстрований у BlueBubbles Server → Settings → API → Webhooks
- Перевір, чи доступний URL вебхука з Mac
- Переглянь `hermes logs gateway` на предмет помилок вебхука (або `hermes logs -f` для реального часу)

### "Private API helper not connected"
- Встанови Private API helper: [docs.bluebubbles.app](https://docs.bluebubbles.app/helper-bundle/installation)
- Базовий обмін повідомленнями працює без нього — лише реакції, індикатори набору та підтвердження прочитання потребують його