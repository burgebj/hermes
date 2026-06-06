---
sidebar_position: 5
title: "Microsoft Teams"
description: "Налаштуй Hermes Agent як бот Microsoft Teams"
---

# Налаштування Microsoft Teams

Підключи Hermes Agent до Microsoft Teams як бота. На відміну від Socket Mode у Slack, Teams доставляє повідомлення, викликаючи **публічний HTTPS webhook**, тому твій екземпляр потребує публічно доступної кінцевої точки — або dev‑тунель (локальна розробка), або реальний домен (продакшн).

Потрібні підсумки зустрічей з подій Microsoft Graph, а не звичайні розмови бота? Використай спеціальну сторінку налаштування: [Teams Meetings](/user-guide/messaging/teams-meetings).

> Запусти `hermes gateway setup` і обери **Microsoft Teams** для покрокового налаштування.

## Як реагує бот

| Контекст | Поведінка |
|----------|-----------|
| **Особистий чат (DM)** | Бот відповідає на кожне повідомлення. Не потрібне @згадування. |
| **Груповий чат** | Бот відповідає лише коли його @згадують. |
| **Канал** | Бот відповідає лише коли його @згадують. |

Teams передає @згадування як звичайні повідомлення з тегами `<at>BotName</at>`, які Hermes автоматично видаляє перед обробкою.

---

## Крок 1: Встанови Teams CLI

`@microsoft/teams.cli` автоматизує реєстрацію бота — без потреби у Azure portal.

```bash
npm install -g @microsoft/teams.cli@preview
teams login
```

Щоб перевірити свій вхід і знайти власний AAD object ID (потрібний для `TEAMS_ALLOWED_USERS`):

```bash
teams status --verbose
```

---

## Крок 2: Відкрий порт webhook

Teams не може доставляти повідомлення на `localhost`. Для локальної розробки використай будь‑який інструмент тунелювання, щоб отримати публічний HTTPS URL. Порт за замовчуванням — `3978`; змінити його можна за допомогою `TEAMS_PORT`, якщо потрібно.

```bash
# devtunnel (Microsoft)
devtunnel create hermes-bot --allow-anonymous
devtunnel port create hermes-bot -p 3978 --protocol https  # replace 3978 with TEAMS_PORT if changed
devtunnel host hermes-bot

# ngrok
ngrok http 3978  # replace 3978 with TEAMS_PORT if changed

# cloudflared
cloudflared tunnel --url http://localhost:3978  # replace 3978 with TEAMS_PORT if changed
```

Скопіюй URL, що починається з `https://`, з виводу — він знадобиться у наступному кроці. Тримай тунель запущеним під час розробки.

Для продакшн‑середовища вкажи кінцеву точку бота на публічному домені твого сервера (див. [Production Deployment](#production-deployment)).

---

## Крок 3: Створи бота

```bash
teams app create \
  --name "Hermes" \
  --endpoint "https://<your-tunnel-url>/api/messages"
```

CLI виводить твої `CLIENT_ID`, `CLIENT_SECRET` та `TENANT_ID`, а також посилання для встановлення на кроці 6. Збережи client secret — його більше не буде показано.

---

## Крок 4: Налаштуй змінні середовища

Додай до `~/.hermes/.env`:

```bash
# Required
TEAMS_CLIENT_ID=<your-client-id>
TEAMS_CLIENT_SECRET=<your-client-secret>
TEAMS_TENANT_ID=<your-tenant-id>

# Restrict access to specific users (recommended)
# Use AAD object IDs from `teams status --verbose`
TEAMS_ALLOWED_USERS=<your-aad-object-id>
```

---

## Крок 5: Запусти шлюз

```bash
HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose up -d gateway
```

Це запускає шлюз. Порт webhook за замовчуванням — `3978` (можна перевизначити через `TEAMS_PORT`). Перевір, що він працює:

```bash
curl http://localhost:3978/health   # should return: ok
docker logs -f hermes
```

Шукай:
```
[teams] Webhook server listening on 0.0.0.0:3978/api/messages
```

---

## Крок 6: Встанови додаток у Teams

```bash
teams app get <teamsAppId> --install-link
```

Відкрий надруковане посилання у браузері — воно відкриється безпосередньо в клієнті Teams. Після встановлення надішли пряме повідомлення своєму боту — він готовий.

---

## Довідка з конфігурації

### Змінні середовища

| Змінна | Опис |
|--------|------|
| `TEAMS_CLIENT_ID` | Azure AD App (client) ID |
| `TEAMS_CLIENT_SECRET` | Azure AD client secret |
| `TEAMS_TENANT_ID` | Azure AD tenant ID |
| `TEAMS_ALLOWED_USERS` | Кома‑розділені AAD object ID, яким дозволено користуватися ботом |
| `TEAMS_ALLOW_ALL_USERS` | Встанови `true`, щоб пропустити whitelist і дозволити всім |
| `TEAMS_HOME_CHANNEL` | Conversation ID для cron/proactive доставки повідомлень |
| `TEAMS_HOME_CHANNEL_NAME` | Відображувана назва домашнього каналу |
| `TEAMS_PORT` | Порт webhook (за замовчуванням: `3978`) |

### config.yaml

Альтернативно, налаштуй через `~/.hermes/config.yaml`:

```yaml
platforms:
  teams:
    enabled: true
    extra:
      client_id: "your-client-id"
      client_secret: "your-secret"
      tenant_id: "your-tenant-id"
      port: 3978
```

---

## Фічі

### Інтерактивні картки схвалення

Коли агенту потрібно виконати потенційно небезпечну команду, він надсилає **Adaptive Card** з чотирма кнопками замість запиту `/approve`:

- **Allow Once** — схвалити цю конкретну команду
- **Allow Session** — схвалити цей шаблон на решту сесії
- **Always Allow** — постійно схвалити цей шаблон
- **Deny** — відхилити команду

Натискання кнопки вирішує схвалення в рядку і замінює картку результатом.

### Доставка підсумків зустрічей (Teams Meeting Pipeline)

Коли плагін [Teams meeting pipeline](/user-guide/messaging/msgraph-webhook) увімкнено, цей адаптер також обробляє вихідну доставку підсумків зустрічей — один інтерфейс інтеграції Teams, а не два. Після того, як транскрипт зустрічі підсумовано, записувач публікує підсумок у вибрану ціль у Teams.

Налаштування доставки підсумків здійснюється у розділі `teams` конфігурації платформи разом із налаштуванням бота:

```yaml
platforms:
  teams:
    enabled: true
    extra:
      # existing bot config (client_id, client_secret, tenant_id, port) ...

      # Meeting summary delivery (only used when the teams_pipeline plugin is enabled)
      delivery_mode: "graph"       # or "incoming_webhook"
      # For delivery_mode: graph — pick ONE of:
      chat_id: "19:meeting_..."    # post into a Teams chat
      # team_id: "..."             # OR post into a channel
      # channel_id: "..."
      # access_token: "..."        # optional; falls back to MSGRAPH_* app credentials
      # For delivery_mode: incoming_webhook:
      # incoming_webhook_url: "https://outlook.office.com/webhook/..."
```

| Режим | Коли використовувати | Компроміс |
|------|----------------------|-----------|
| `incoming_webhook` | Просте «надіслати підсумок у цей канал» зі статичним URL, згенерованим Teams. | Без підтримки потокових відповідей, без реакцій, відображається як користувач, вказаний у webhook. |
| `graph` | Пости у потоках каналу або 1:1/груповий чат від імені бота через Microsoft Graph. | Потрібна реєстрація [Graph app](/guides/microsoft-graph-app-registration) з дозволами `ChannelMessage.Send` (канал) або `Chat.ReadWrite.All` (чат). |

Якщо плагін `teams_pipeline` **не** увімкнено, ці налаштування неактивні — вони підключаються лише коли runtime pipeline прив’язується до Graph webhook.

---

## Продакшн‑розгортання

Для постійного сервера пропусти dev‑тунель і зареєструй бота з публічною HTTPS кінцевою точкою твого сервера:

```bash
teams app create \
  --name "Hermes" \
  --endpoint "https://your-domain.com/api/messages"
```

Якщо бот вже створений і треба лише оновити кінцеву точку:

```bash
teams app update --id <teamsAppId> --endpoint "https://your-domain.com/api/messages"
```

Переконайся, що налаштований порт (`TEAMS_PORT`, за замовчуванням `3978`) доступний з інтернету і що TLS‑сертифікат дійсний — Teams відхиляє самопідписані сертифікати.

---

## Устранення проблем

| Проблема | Рішення |
|----------|----------|
| `health` endpoint працює, а бот не відповідає | Перевір, чи тунель ще працює і чи кінцева точка бота збігається з URL тунелю |
| `KeyError: 'teams'` у логах | Перезапусти контейнер — це виправлено в поточній версії |
| Бот відповідає помилками автентифікації | Перевір, чи `TEAMS_CLIENT_ID`, `TEAMS_CLIENT_SECRET` і `TEAMS_TENANT_ID` встановлені правильно |
| `No inference provider configured` | Переконайся, що `ANTHROPIC_API_KEY` (або інший ключ провайдера) заданий у `~/.hermes/.env` |
| Бот отримує повідомлення, але ігнорує їх | Твій AAD object ID може не бути у `TEAMS_ALLOWED_USERS`. Запусти `teams status --verbose`, щоб знайти його |
| URL тунелю змінюється після перезапуску | URL dev‑тунелю залишаються постійними, якщо використовувати іменований тунель (`devtunnel create hermes-bot`). ngrok і cloudflared генерують новий URL кожен запуск, якщо немає платного плану — онови кінцеву точку бота за допомогою `teams app update` |
| Teams показує «This bot is not responding» | Webhook повернув помилку. Перевір `docker logs hermes` на traceback |
| `[teams] Failed to connect` у логах | SDK не зміг автентифікуватися. Перевір ще раз свої облікові дані і чи tenant ID відповідає обліковому запису, використаному в `teams login` |

---

## Безпека

:::warning
**Завжди встановлюй `TEAMS_ALLOWED_USERS`** з AAD object ID уповноважених користувачів. Без цього будь‑хто, хто знайде або встановить твого бота, зможе з ним взаємодіяти.

Обробляй `TEAMS_CLIENT_SECRET` як пароль — регулярно змінюй його через Azure portal або Teams CLI.
:::

- Зберігай облікові дані у `~/.hermes/.env` з правами `600` (`chmod 600 ~/.hermes/.env`)
- Бот приймає повідомлення лише від користувачів у `TEAMS_ALLOWED_USERS`; неавторизовані повідомлення тихо відкидаються
- Твоя публічна кінцева точка (`/api/messages`) автентифікована через Teams Bot Framework — запити без дійсного JWT відхиляються

## Пов’язані документи

- [Teams Meetings](/user-guide/messaging/teams-meetings)
- [Operate the Teams Meeting Pipeline](/guides/operate-teams-meeting-pipeline)