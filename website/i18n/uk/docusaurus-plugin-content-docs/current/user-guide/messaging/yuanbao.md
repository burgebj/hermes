---
sidebar_position: 16
title: "юанбао"
description: "Підключи Hermes Agent до корпоративної платформи обміну повідомленнями Yuanbao через WebSocket gateway"
---

# Yuanbao

Підключи Hermes до [Yuanbao](https://yuanbao.tencent.com/), корпоративної платформи обміну повідомленнями Tencent. Адаптер використовує шлюз WebSocket для доставки повідомлень у реальному часі та підтримує як прямі (C2C), так і групові розмови.

:::info
Yuanbao — це корпоративна платформа обміну повідомленнями, яка переважно використовується в Tencent та в корпоративному середовищі. Вона застосовує WebSocket для реального часу, аутентифікацію на основі HMAC та підтримує різноманітний медіа‑контент, включаючи зображення, файли та голосові повідомлення.
:::
## Передумови

- Обліковий запис Yuanbao з правами на створення ботів
- Yuanbao APP_ID та APP_SECRET (від адміністратора платформи)
- Пакети Python: `websockets` та `httpx`
- Для підтримки медіа: `aiofiles`

Встанови необхідні залежності:

```bash
pip install websockets httpx aiofiles
```
## Налаштування

### 1. Створи бота в Yuanbao

1. Завантаж додаток Yuanbao за адресою [https://yuanbao.tencent.com/](https://yuanbao.tencent.com/)
2. У додатку перейди до **PAI → My Bot** і створи нового бота
3. Після створення бота скопіюй **APP_ID** та **APP_SECRET**

### 2. Запусти майстер налаштування

Найпростіший спосіб налаштувати Yuanbao — через інтерактивний майстер:

```bash
hermes gateway setup
```

Вибери **Yuanbao**, коли буде запитано. Майстер виконає:

1. Запитає твій APP_ID
2. Запитає твій APP_SECRET
3. Автоматично збереже конфігурацію

:::tip
WebSocket URL та API Domain мають розумні значення за замовчуванням. Тобі потрібно вказати лише APP_ID і APP_SECRET, щоб розпочати.
:::

### 3. Налаштуй змінні середовища

Після початкового налаштування перевір ці змінні у `~/.hermes/.env`:

```bash
# Required
YUANBAO_APP_ID=your-app-id
YUANBAO_APP_SECRET=your-app-secret
YUANBAO_WS_URL=wss://api.yuanbao.example.com/ws
YUANBAO_API_DOMAIN=https://api.yuanbao.example.com

# Optional: bot account ID (normally obtained automatically from sign-token)
# YUANBAO_BOT_ID=your-bot-id

# Optional: internal routing environment (e.g. test/staging/production)
# YUANBAO_ROUTE_ENV=production

# Optional: home channel for cron/notifications (format: direct:<account> or group:<group_code>)
YUANBAO_HOME_CHANNEL=direct:bot_account_id
YUANBAO_HOME_CHANNEL_NAME="Bot Notifications"

# Optional: restrict access (legacy, see Access Control below for fine-grained policies)
YUANBAO_ALLOWED_USERS=user_account_1,user_account_2
```

### 4. Запусти gateway

```bash
hermes gateway
```

Адаптер підключиться до шлюзу Yuanbao WebSocket, автентифікується за допомогою підписів HMAC і почне обробляти повідомлення.
## Features

- **WebSocket gateway** — реальний двосторонній зв’язок
- **HMAC authentication** — безпечне підписання запитів за допомогою `APP_ID`/`APP_SECRET`
- **C2C messaging** — прямі розмови користувач‑бот
- **Group messaging** — розмови в групових чатах
- **Media support** — зображення, файли та голосові повідомлення через COS (Cloud Object Storage)
- **Markdown formatting** — повідомлення автоматично розбиваються на частини згідно з обмеженнями розміру Yuanbao
- **Message deduplication** — запобігає дублюванню обробки одного й того ж повідомлення
- **Heartbeat/keep-alive** — підтримує стабільність з’єднання WebSocket
- **Typing indicators** — показує статус «typing…», поки агент обробляє
- **Automatic reconnection** — обробляє розриви WebSocket з експоненціальним збільшенням інтервалу
- **Group information queries** — отримує деталі групи та списки учасників
- **Sticker/Emoji support** — надсилає наклейки TIMFaceElem та емодзі в розмовах
- **Auto-sethome** — перший користувач, що написав боту, автоматично встановлюється власником домашнього каналу
- **Slow-response notification** — надсилає повідомлення про очікування, коли агент працює довше, ніж очікувалося
## Параметри конфігурації

### Формати ідентифікаторів чатів

Yuanbao використовує префіксовані ідентифікатори залежно від типу розмови:

| Тип чату | Формат | Приклад |
|-----------|--------|---------|
| Пряме повідомлення (C2C) | `direct:<account>` | `direct:user123` |
| Групове повідомлення | `group:<group_code>` | `group:grp456` |

### Завантаження медіа

Адаптер Yuanbao автоматично обробляє завантаження медіа через COS (Tencent Cloud Object Storage):

- **Зображення**: підтримує JPEG, PNG, GIF, WebP
- **Файли**: підтримує всі поширені типи документів
- **Голос**: підтримує WAV, MP3, OGG

URL‑адреси медіа автоматично перевіряються та завантажуються перед завантаженням, щоб запобігти атакам SSRF.
## Канал дому

Використовуй команду `/sethome` у будь‑якому чаті Yuanbao (прямому чи груповому), щоб позначити його як **домашній канал**. Заплановані завдання (cron‑jobs) надсилатимуть свої результати в цей канал.

:::tip Auto-sethome
Якщо домашній канал не налаштовано, перший користувач, який напише боту, автоматично стане власником домашнього каналу. Якщо поточний домашній канал — це груповий чат, перше пряме повідомлення підвищить його до прямого каналу.
:::

Ти також можеш встановити його вручну у `~/.hermes/.env`:

```bash
YUANBAO_HOME_CHANNEL=direct:user_account_id
# or for a group:
# YUANBAO_HOME_CHANNEL=group:group_code
YUANBAO_HOME_CHANNEL_NAME="My Bot Updates"
```

### Приклад: встановлення домашнього каналу

1. Розпочни розмову з ботом у Yuanbao
2. Надішли команду: `/sethome`
3. Бот відповість: «Домашній канал встановлено на [chat_name] з ідентифікатором [chat_id]. Cron‑jobs будуть надсилати результати сюди».
4. Майбутні cron‑jobs та сповіщення будуть надсилатися в цей канал

### Приклад: доставка результатів cron‑job

Створи cron‑job:

```bash
/cron "0 9 * * *" Check server status
```

Запланований вивід буде доставлений у твій домашній канал Yuanbao щодня о 9:00.
## Поради щодо використання

### Початок розмови

Надішли будь‑яке повідомлення боту в Yuanbao:

```
hello
```

Бот відповідає у тому ж самому потоці розмови.

### Доступні команди

Усі стандартні команди Hermes працюють у Yuanbao:

| Command | Description |
|---------|-------------|
| `/new` | Розпочати нову розмову |
| `/model [provider:model]` | Показати або змінити модель |
| `/sethome` | Встановити цей чат як домашній канал |
| `/status` | Показати інформацію про сесію |
| `/help` | Показати доступні команди |

### Надсилання файлів

Щоб надіслати файл боту, просто прикріпи його безпосередньо в чаті Yuanbao. Бот автоматично завантажить і обробить вкладений файл.

Можеш також додати повідомлення до вкладення:

```
Please analyze this document
```

### Отримання файлів

Коли ти просиш бота створити або експортувати файл, він надсилає файл безпосередньо у твій чат Yuanbao.
## Усунення проблем

### Бот онлайн, але не відповідає на повідомлення

**Причина**: Не вдалося автентифікуватися під час WebSocket handshake.

**Виправлення**:
1. Перевір, що `APP_ID` і `APP_SECRET` правильні
2. Переконайся, що URL WebSocket доступний
3. Переконайся, що обліковий запис бота має необхідні дозволи
4. Переглянь логи шлюзу: `tail -f ~/.hermes/logs/gateway.log`

### Помилка «Connection refused»

**Причина**: URL WebSocket недоступний або неправильний.

**Виправлення**:
1. Перевір формат URL WebSocket (повинен починатися з `wss://`)
2. Перевір мережеве з’єднання з доменом Yuanbao API
3. Переконайся, що брандмауер дозволяє підключення WebSocket
4. Перевір URL за допомогою: `curl -I https://[YUANBAO_API_DOMAIN]`

### Не вдаються завантаження медіа

**Причина**: Облікові дані COS недійсні або медіа‑сервер недоступний.

**Виправлення**:
1. Перевір, що `API_DOMAIN` правильний
2. Переконайся, що дозволи на завантаження медіа увімкнені для твого бота
3. Переконайся, що медіафайл доступний і не пошкоджений
4. Перевір конфігурацію бакету COS у адміністратора платформи

### Повідомлення не доставляються у домашній канал

**Причина**: Формат ідентифікатора домашнього каналу неправильний або cron‑завдання не спрацювало.

**Виправлення**:
1. Перевір, що `YUANBAO_HOME_CHANNEL` у правильному форматі
2. Протестуй команду `/sethome` для автоматичного визначення правильного формату
3. Перевір розклад cron‑завдання за допомогою `/status`
4. Переконайся, що бот має дозволи на надсилання у цільовий чат

### Часті розриви з’єднання

**Причина**: З’єднання WebSocket нестабільне або мережа ненадійна.

**Виправлення**:
1. Переглянь логи шлюзу на предмет шаблонів помилок
2. Збільшити тайм‑аут heartbeat у налаштуваннях підключення
3. Забезпеч стабільне мережеве з’єднання з Yuanbao API
4. Розглянь можливість увімкнення докладного логування: `HERMES_LOG_LEVEL=debug`
## Контроль доступу

Yuanbao підтримує тонкий контроль доступу як для приватних (прямих) повідомлень, так і для групових розмов:

```bash
# DM policy: open (default) | allowlist | disabled
YUANBAO_DM_POLICY=open
# Comma-separated user IDs allowed to DM the bot (only used when DM_POLICY=allowlist)
YUANBAO_DM_ALLOW_FROM=user_id_1,user_id_2

# Group policy: open (default) | allowlist | disabled
YUANBAO_GROUP_POLICY=open
# Comma-separated group codes allowed (only used when GROUP_POLICY=allowlist)
YUANBAO_GROUP_ALLOW_FROM=group_code_1,group_code_2
```

Це також можна налаштувати у `config.yaml`:

```yaml
platforms:
  yuanbao:
    extra:
      dm_policy: allowlist
      dm_allow_from: "user1,user2"
      group_policy: open
      group_allow_from: ""
```
## Розширена конфігурація

### Розбиття повідомлень

Yuanbao має максимальний розмір повідомлення. Hermes автоматично розбиває великі відповіді за допомогою розумного розділення Markdown (поважає блоки коду, таблиці та межі абзаців).

### Параметри підключення

Наступні параметри підключення вбудовані в адаптер із розумними значеннями за замовчуванням:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| WebSocket connect timeout | 15 seconds | Time to wait for WS handshake |
| Heartbeat interval | 30 seconds | Ping frequency to keep connection alive |
| Max reconnect attempts | 100 | Maximum number of reconnection tries |
| Reconnect backoff | 1s → 60s (exponential) | Wait time between reconnect attempts |
| Reply heartbeat interval | 2 seconds | RUNNING status send frequency |
| Send timeout | 30 seconds | Timeout for outbound WS messages |

:::note
Ці значення наразі не можна налаштувати за допомогою змінних середовища. Вони оптимізовані для типових розгортань Yuanbao.
:::

### Детальне журналювання

Увімкни журналювання налагодження, щоб усунути проблеми зі з’єднанням:

```bash
HERMES_LOG_LEVEL=debug hermes gateway
```
## Інтеграція з іншими функціями

### Cron‑завдання

Заплануй завдання, які виконуються на Yuanbao:

```
/cron "0 */4 * * *" Report system health
```

Результати надсилаються у твій домашній канал.

### Фонові завдання

Виконуй довгі операції без блокування розмови:

```
/background Analyze all files in the archive
```

### Крос‑платформені повідомлення

Надішли повідомлення з CLI до Yuanbao:

```bash
hermes chat -q "Send 'Hello from CLI' to yuanbao:group:group_code"
```
## Пов’язана документація

- [Messaging Gateway Overview](./index.md)
- [Slash Commands Reference](/reference/slash-commands)
- [Cron Jobs](/user-guide/features/cron)
- [Background Sessions](/user-guide/cli#background-sessions)