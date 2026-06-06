---
sidebar_position: 6
title: "Встречи Teams"
description: "Настрой конвейер резюмирования встреч Microsoft Teams с вебхуками Microsoft Graph"
---

# Microsoft Teams Meetings

Используй конвейер встреч Teams, когда нужно, чтобы Hermes получал события встреч Microsoft Graph, сначала получал транскрипты, а при необходимости переключался на записи + STT и доставлял структурированное резюме в downstream‑приёмники.

Предварительные требования: смотри [Microsoft Teams](./teams.md) для настройки бота/учётных данных.

> Выполни `hermes gateway setup` и выбери **Teams Meetings** для пошагового руководства.

Эта страница посвящена настройке и включению:
- учётных данных Graph
- конфигурации слушателя вебхуков
- режимов доставки Teams
- формы конфигурации конвейера

Для операций day‑2, проверок перед запуском и рабочего листа оператора используй отдельное руководство: [Operate the Teams Meeting Pipeline](/guides/operate-teams-meeting-pipeline).

## Что делает эта функция

Конвейер:
1. получает события вебхуков Microsoft Graph;
2. определяет встречу и сначала предпочитает артефакты транскриптов;
3. переключается на загрузку записи + STT, если пригодный транскрипт недоступен;
4. сохраняет долговременное состояние задания и записи приёмников локально;
5. может записывать резюме в Notion, Linear и Microsoft Teams.

Действия оператора остаются в CLI (подкоманда `teams-pipeline` регистрируется плагином `teams_pipeline` — включи её через `hermes plugins enable teams_pipeline` или добавь `plugins.enabled: [teams_pipeline]` в `config.yaml`):

```bash
hermes teams-pipeline validate
hermes teams-pipeline list
hermes teams-pipeline maintain-subscriptions
```

## Предварительные требования

Перед включением конвейера встреч убедись, что у тебя есть:

- рабочая установка Hermes;
- существующая [Microsoft Teams bot setup](/user-guide/messaging/teams), если нужна исходящая доставка в Teams;
- учётные данные приложения Microsoft Graph с правами, необходимыми для ресурсов встреч, на которые планируешь подписаться;
- публичный HTTPS‑URL, который Microsoft Graph сможет вызвать для доставки вебхуков;
- установленный `ffmpeg`, если нужен запасной вариант запись + STT.

## Шаг 1: Добавить учётные данные Microsoft Graph

Добавь учётные данные приложения только для Graph в `~/.hermes/.env`:

```bash
MSGRAPH_TENANT_ID=<tenant-id>
MSGRAPH_CLIENT_ID=<client-id>
MSGRAPH_CLIENT_SECRET=<client-secret>
```

Эти учётные данные используются:
- фундаментом клиента Graph;
- командами обслуживания подписок;
- разрешением встреч и получением артефактов;
- исходящей доставкой Teams через Graph, если ты не предоставляешь отдельный токен доступа Teams.

## Шаг 2: Включить слушатель вебхуков Graph

Слушатель вебхуков — это платформа шлюза под именем `msgraph_webhook`. Как минимум, включи её и задай значение `client_state`:

```bash
MSGRAPH_WEBHOOK_ENABLED=true
MSGRAPH_WEBHOOK_HOST=127.0.0.1
MSGRAPH_WEBHOOK_PORT=8646
MSGRAPH_WEBHOOK_CLIENT_STATE=<random-shared-secret>
MSGRAPH_WEBHOOK_ACCEPTED_RESOURCES=communications/onlineMeetings
```

Слушатель открывает:
- `/msgraph/webhook` для уведомлений Graph;
- `/health` для простой проверки работоспособности.

Тебе нужно направить свой публичный HTTPS‑endpoint к этому слушателю. Например, если твой публичный домен — `https://ops.example.com`, твой URL уведомления Graph обычно будет:

```text
https://ops.example.com/msgraph/webhook
```

## Шаг 3: Настроить доставку Teams и поведение конвейера

Конвейер встреч читает свою конфигурацию во время выполнения из существующей записи платформы `teams`. Параметры, специфичные для конвейера, находятся под `teams.extra.meeting_pipeline`. Исходящая доставка Teams остаётся в обычной конфигурации платформы Teams.

Пример `~/.hermes/config.yaml`:

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

Если ты привязываешь слушатель к хосту, отличному от loopback, например `0.0.0.0`, также необходимо задать `allowed_source_cidrs` в диапазоны исходящего трафика вебхуков Microsoft. Привязки к loopback (`127.0.0.1` / `::1`) предназначены для dev‑туннеля и локальной обратной прокси‑настройки.

## Режимы доставки Teams

Конвейер поддерживает два режима доставки резюме в Teams внутри существующего плагина Teams.

### `incoming_webhook`

Используй, когда нужен простой POST вебхука в Teams без создания сообщения в канале через Graph.

Требуемая конфигурация:

```yaml
platforms:
  teams:
    enabled: true
    extra:
      delivery_mode: "incoming_webhook"
      incoming_webhook_url: "https://..."
```

### `graph`

Используй, когда Hermes должен отправлять резюме через Microsoft Graph в чат или канал Teams.

Поддерживаемые цели:
- `chat_id`;
- `team_id` + `channel_id`;
- `team_id` + запасной `home_channel` для существующей платформы Teams.

Пример:

```yaml
platforms:
  teams:
    enabled: true
    extra:
      delivery_mode: "graph"
      team_id: "team-id"
      channel_id: "channel-id"
```

## Шаг 4: Запустить шлюз

Запусти Hermes обычным способом после обновления конфигурации:

```bash
hermes gateway run
```

Или, если ты запускаешь Hermes в Docker, запусти шлюз так же, как делал это для своей развертки.

Проверь слушатель:

```bash
curl http://localhost:8646/health
```

## Шаг 5: Создать подписки Graph

Используй CLI плагина для создания и проверки подписок.

Примеры:

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

Microsoft Graph ограничивает подписки вебхуков 72‑часовым сроком и не будет автоматически их продлять. Тебе **обязательно** запланировать `hermes teams-pipeline maintain-subscriptions` перед запуском в продакшн, иначе уведомления тихо прекратятся через три дня после любой ручной создания подписки. Смотри [Automating subscription renewal](/guides/operate-teams-meeting-pipeline#automating-subscription-renewal-required-for-production) в руководстве оператора — три варианта (Hermes cron, systemd timer, обычный crontab).

:::

Для обслуживания подписок и потоков day‑2 оператора продолжай с руководством: [Operate the Teams Meeting Pipeline](/guides/operate-teams-meeting-pipeline).

## Проверка

Запусти встроенный снимок проверки:

```bash
hermes teams-pipeline validate
```

Полезные сопутствующие проверки:

```bash
hermes teams-pipeline token-health
hermes teams-pipeline subscriptions
```

## Устранение проблем

| Проблема | Что проверить |
|----------|----------------|
| Не проходит валидация вебхука Graph | Убедись, что публичный URL корректен и доступен, и что Graph вызывает точный путь `/msgraph/webhook` |
| Задания не появляются в `hermes teams-pipeline list` | Проверь, что `msgraph_webhook` включён и что подписки указывают на правильный URL уведомления |
| `transcript-first` никогда не succeeds | Проверь права Graph для ресурсов транскриптов и наличие артефакта транскрипта для встречи |
| Запасной вариант записи не срабатывает | Убедись, что `ffmpeg` установлен и приложение Graph может получить доступ к артефактам записи |
| Доставка резюме в Teams не удалась | Перепроверь `delivery_mode`, идентификаторы целей и конфигурацию аутентификации Teams |

## Связанные документы

- [Microsoft Teams bot setup](/user-guide/messaging/teams)
- [Operate the Teams Meeting Pipeline](/guides/operate-teams-meeting-pipeline)