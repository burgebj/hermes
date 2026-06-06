---
sidebar_position: 6
title: "Teams зустрічі"
description: "Налаштуй конвеєр підсумків зустрічей Microsoft Teams за допомогою вебхуків Microsoft Graph"
---

# Microsoft Teams Meetings

Використовуй конвеєр Teams meeting, коли потрібно, щоб Hermes отримував події зустрічей Microsoft Graph, спочатку отримував транскрипти, а при потребі переходив до записів + STT і доставляв структуроване резюме до нижчестоячих сховищ.

Передумови: дивись [Microsoft Teams](./teams.md) для налаштування бота/облікових даних.

> Запусти `hermes gateway setup` і обери **Teams Meetings** для покрокового налаштування.

Ця сторінка зосереджена на налаштуванні та ввімкненні:
- облікових даних Graph
- конфігурації прослуховувача вебхука
- режимів доставки Teams
- формі конфігурації конвеєра

Для операцій day‑2, перевірок перед запуском та робочого листа оператора використай спеціальний посібник: [Operate the Teams Meeting Pipeline](/guides/operate-teams-meeting-pipeline).

## What This Feature Does

Конвеєр:
1. отримує події вебхука Microsoft Graph
2. розв’язує зустріч і спочатку надає перевагу артефактам транскрипту
3. переходить до завантаження запису + STT, коли немає придатного транскрипту
4. зберігає стійкий стан завдання та записи сховища локально
5. може записувати резюме в Notion, Linear та Microsoft Teams

Дії оператора залишаються в CLI (підкоманда `teams-pipeline` реєструється плагіном `teams_pipeline` — ввімкни її через `hermes plugins enable teams_pipeline` або встанови `plugins.enabled: [teams_pipeline]` у `config.yaml`):

```bash
hermes teams-pipeline validate
hermes teams-pipeline list
hermes teams-pipeline maintain-subscriptions
```

## Prerequisites

Перед ввімкненням конвеєра зустрічей переконайся, що у тебе є:

- працююча установка Hermes
- існуюче [Microsoft Teams bot setup](/user-guide/messaging/teams), якщо потрібна вихідна доставка Teams
- облікові дані застосунку Microsoft Graph з потрібними дозволами для ресурсів зустрічей, на які плануєш підписатися
- публічний HTTPS‑URL, який Microsoft Graph може викликати для доставки вебхука
- встановлений `ffmpeg`, якщо потрібен запасний варіант запис + STT

## Step 1: Add Microsoft Graph Credentials

Додай облікові дані Graph лише для застосунку у `~/.hermes/.env`:

```bash
MSGRAPH_TENANT_ID=<tenant-id>
MSGRAPH_CLIENT_ID=<client-id>
MSGRAPH_CLIENT_SECRET=<client-secret>
```

Ці облікові дані використовуються:
- фундаментом клієнта Graph
- командами підтримки підписок
- розв’язанням зустрічей та отриманням артефактів
- вихідною доставкою Teams на основі Graph, коли не вказано окремий токен доступу Teams

## Step 2: Enable the Graph Webhook Listener

Прослуховувач вебхука — це платформа шлюзу під назвою `msgraph_webhook`. Принаймні ввімкни її та встанови значення стану клієнта:

```bash
MSGRAPH_WEBHOOK_ENABLED=true
MSGRAPH_WEBHOOK_HOST=127.0.0.1
MSGRAPH_WEBHOOK_PORT=8646
MSGRAPH_WEBHOOK_CLIENT_STATE=<random-shared-secret>
MSGRAPH_WEBHOOK_ACCEPTED_RESOURCES=communications/onlineMeetings
```

Прослуховувач експонує:
- `/msgraph/webhook` для сповіщень Graph
- `/health` для простого health‑check

Треба направити свій публічний HTTPS‑endpoint до цього прослуховувача. Наприклад, якщо твій публічний домен `https://ops.example.com`, URL сповіщення Graph зазвичай буде:

```text
https://ops.example.com/msgraph/webhook
```

## Step 3: Configure Teams Delivery and Pipeline Behavior

Конвеєр зустрічей читає свою конфігурацію під час виконання з існуючого запису платформи `teams`. Параметри, специфічні для конвеєра, розташовані під `teams.extra.meeting_pipeline`. Вихідна доставка Teams залишається у звичній конфігурації платформи Teams.

Приклад `~/.hermes/config.yaml`:

```yaml
platforms:
  msgraph_webhook:
    enabled: true
    extra:
      host: 127.0.0.1
      port: 8646
      client_state: "replace-me"
      accepted_resources:
        - "communications/onlineMeetings"

  teams:
    enabled: true
    extra:
      client_id: "your-teams-client-id"
      client_secret: "your-teams-client-secret"
      tenant_id: "your-teams-tenant-id"

      # outbound summary delivery
      delivery_mode: "graph" # or incoming_webhook
      team_id: "team-id"
      channel_id: "channel-id"
      # incoming_webhook_url: "https://..."

      meeting_pipeline:
        transcript_min_chars: 80
        transcript_required: false
        transcription_fallback: true
        ffmpeg_extract_audio: true
        notion:
          enabled: false
        linear:
          enabled: false
```

Якщо прив’язуєш прослуховувач до не‑loopback хоста, наприклад `0.0.0.0`, треба також задати `allowed_source_cidrs` до діапазонів egress вебхуків Microsoft. Loopback‑прив’язки (`127.0.0.1` / `::1`) призначені для dev‑тунелю та локальної reverse‑proxy налаштування.

## Teams Delivery Modes

Конвеєр підтримує два режими доставки резюме в Teams у межах існуючого плагіну Teams.

### `incoming_webhook`

Використовуй, коли потрібен простий пост вебхука в Teams без створення повідомлення каналу через Graph.

Обов’язкова конфігурація:

```yaml
platforms:
  teams:
    enabled: true
    extra:
      delivery_mode: "incoming_webhook"
      incoming_webhook_url: "https://..."
```

### `graph`

Використовуй, коли треба, щоб Hermes опублікував резюме через Microsoft Graph у чат або канал Teams.

Підтримувані цілі:
- `chat_id`
- `team_id` + `channel_id`
- `team_id` + `home_channel` як запасний варіант для існуючої платформи Teams

Приклад:

```yaml
platforms:
  teams:
    enabled: true
    extra:
      delivery_mode: "graph"
      team_id: "team-id"
      channel_id: "channel-id"
```

## Step 4: Start the Gateway

Запусти Hermes звичайним способом після оновлення конфігурації:

```bash
hermes gateway run
```

Або, якщо запускаєш Hermes у Docker, запусти шлюз так само, як робиш це для свого розгортання.

Перевір прослуховувач:

```bash
curl http://localhost:8646/health
```

## Step 5: Create Graph Subscriptions

Використай CLI плагіну для створення та перегляду підписок.

Приклади:

```bash
hermes teams-pipeline subscribe \
  --resource communications/onlineMeetings/getAllTranscripts \
  --notification-url https://ops.example.com/msgraph/webhook \
  --client-state "$MSGRAPH_WEBHOOK_CLIENT_STATE"

hermes teams-pipeline subscribe \
  --resource communications/onlineMeetings/getAllRecordings \
  --notification-url https://ops.example.com/msgraph/webhook \
  --client-state "$MSGRAPH_WEBHOOK_CLIENT_STATE"
```

:::warning Graph subscriptions expire in 72 hours

Microsoft Graph обмежує підписки вебхука 72‑годинним терміном і не оновлює їх автоматично. ТИ ПОВИНЕН запланувати `hermes teams-pipeline maintain-subscriptions` перед запуском у продакшн, інакше сповіщення тихо припиняться через три дні після будь‑якого ручного створення підписки. Дивись [Automating subscription renewal](/guides/operate-teams-meeting-pipeline#automating-subscription-renewal-required-for-production) у посібнику оператора — три варіанти (Hermes cron, systemd timer, простий crontab).

:::

Для підтримки підписок та day‑2 потоків оператора продовжуй за посібником: [Operate the Teams Meeting Pipeline](/guides/operate-teams-meeting-pipeline).

## Validation

Запусти вбудований знімок валідації:

```bash
hermes teams-pipeline validate
```

Корисні додаткові перевірки:

```bash
hermes teams-pipeline token-health
hermes teams-pipeline subscriptions
```

## Troubleshooting

| Problem | What to check |
|---------|---------------|
| Graph webhook validation fails | Confirm the public URL is correct and reachable, and that Graph is calling the exact `/msgraph/webhook` path |
| Jobs do not appear in `hermes teams-pipeline list` | Confirm `msgraph_webhook` is enabled and that subscriptions point at the right notification URL |
| Transcript-first never succeeds | Check Graph permissions for transcript resources and whether the transcript artifact exists for that meeting |
| Recording fallback fails | Confirm `ffmpeg` is installed and the Graph app can access recording artifacts |
| Teams summary delivery fails | Re-check `delivery_mode`, target IDs, and Teams auth config |

## Related Docs

- [Microsoft Teams bot setup](/user-guide/messaging/teams)
- [Operate the Teams Meeting Pipeline](/guides/operate-teams-meeting-pipeline)