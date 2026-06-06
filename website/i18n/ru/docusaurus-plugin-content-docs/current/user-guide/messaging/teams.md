---
sidebar_position: 5
title: "Microsoft Teams"
description: "Настрой Hermes Agent как бот Microsoft Teams"
---

# Настройка Microsoft Teams

Подключи Hermes Agent к Microsoft Teams в виде бота. В отличие от Socket Mode в Slack, Teams доставляет сообщения, вызывая **публичный HTTPS‑вебхук**, поэтому твой экземпляр должен иметь публично доступный эндпоинт — либо через dev‑туннель (локальная разработка), либо через реальный домен (продакшн).

Нужны резюме встреч из событий Microsoft Graph, а не обычные разговоры бота? Используй специальную страницу настройки: [Teams Meetings](/user-guide/messaging/teams-meetings).

> Запусти `hermes gateway setup` и выбери **Microsoft Teams** для пошагового руководства.

## Как реагирует бот

| Контекст | Поведение |
|----------|-----------|
| **Личный чат (DM)** | Бот отвечает на каждое сообщение. Упоминание @ не требуется. |
| **Групповой чат** | Бот отвечает только при упоминании @. |
| **Канал** | Бот отвечает только при упоминании @. |

Teams передаёт упоминания @ как обычные сообщения с тегами `<at>BotName</at>`, которые Hermes автоматически удаляет перед обработкой.

---

## Шаг 1: Установи Teams CLI

`@microsoft/teams.cli` автоматизирует регистрацию бота — портал Azure не нужен.

```bash
npm install -g @microsoft/teams.cli@preview
teams login
```

Чтобы проверить вход в систему и узнать свой AAD‑object ID (нужен для `TEAMS_ALLOWED_USERS`):

```bash
teams status --verbose
```

---

## Шаг 2: Открой порт вебхука

Teams не может доставлять сообщения на `localhost`. Для локальной разработки используй любой туннельный инструмент, чтобы получить публичный HTTPS‑URL. Порт по умолчанию — `3978`; при необходимости его можно изменить с помощью `TEAMS_PORT`.

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

Скопируй URL, начинающийся с `https://`, из вывода — он понадобится в следующем шаге. Оставляй туннель запущенным во время разработки.

Для продакшна укажи эндпоинт бота на публичный домен твоего сервера (см. [Production Deployment](#production-deployment)).

---

## Шаг 3: Создай бота

```bash
teams app create \
  --name "Hermes" \
  --endpoint "https://<your-tunnel-url>/api/messages"
```

CLI выводит твой `CLIENT_ID`, `CLIENT_SECRET` и `TENANT_ID`, а также ссылку для установки на Шаг 6. Сохрани клиентский секрет — он больше не будет показан.

---

## Шаг 4: Настрой переменные окружения

Добавь в `~/.hermes/.env`:

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

## Шаг 5: Запусти шлюз

```bash
HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose up -d gateway
```

Это запустит шлюз. Порт вебхука по умолчанию — `3978` (можно переопределить через `TEAMS_PORT`). Проверь, что он работает:

```bash
curl http://localhost:3978/health   # should return: ok
docker logs -f hermes
```

Ищи:
```
[teams] Webhook server listening on 0.0.0.0:3978/api/messages
```

---

## Шаг 6: Установи приложение в Teams

```bash
teams app get <teamsAppId> --install-link
```

Открой выведенную ссылку в браузере — она откроется напрямую в клиенте Teams. После установки отправь боту личное сообщение — бот готов к работе.

---

## Справочник по конфигурации

### Переменные окружения

| Переменная | Описание |
|------------|----------|
| `TEAMS_CLIENT_ID` | ID приложения Azure AD (client) |
| `TEAMS_CLIENT_SECRET` | Секрет клиента Azure AD |
| `TEAMS_TENANT_ID` | ID тенанта Azure AD |
| `TEAMS_ALLOWED_USERS` | Список AAD‑object ID, разделённых запятыми, которым разрешено использовать бота |
| `TEAMS_ALLOW_ALL_USERS` | Установи `true`, чтобы отключить список разрешённых и позволить всем |
| `TEAMS_HOME_CHANNEL` | ID беседы для cron/проактивной доставки сообщений |
| `TEAMS_HOME_CHANNEL_NAME` | Отображаемое имя домашнего канала |
| `TEAMS_PORT` | Порт вебхука (по умолчанию: `3978`) |

### config.yaml

Либо настрой через `~/.hermes/config.yaml`:

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

## Возможности

### Интерактивные карточки подтверждения

Когда агенту нужно выполнить потенциально опасную команду, он отправляет Adaptive Card с четырьмя кнопками вместо запроса `/approve`:

- **Allow Once** — одобрить эту конкретную команду
- **Allow Session** — одобрить этот шаблон на всю сессию
- **Always Allow** — навсегда одобрить этот шаблон
- **Deny** — отклонить команду

Нажатие кнопки завершает подтверждение в‑строке и заменяет карточку результатом.

### Доставка резюме встреч (конвейер Teams Meeting)

Когда включён плагин [Teams meeting pipeline](/user-guide/messaging/msgraph-webhook), этот адаптер также обрабатывает исходящую доставку резюме встреч — один интеграционный слой Teams, а не два. После того как транскрипт встречи будет суммирован, писатель публикует резюме в выбранный тобой канал Teams.

Настройка доставки резюме конвейера находится в секции `teams` рядом с конфигурацией бота:

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

| Режим | Когда использовать | Компромисс |
|------|--------------------|-----------|
| `incoming_webhook` | Простой «опубликовать резюме в этом канале» со статическим URL, сгенерированным Teams. | Нет ветвления ответов, нет реакций, отображается как идентичность, настроенная в вебхуке. |
| `graph` | Сообщения в ветке канала или 1:1/групповые чаты от имени бота через Microsoft Graph. | Требует регистрации [Graph app](/guides/microsoft-graph-app-registration) с правами `ChannelMessage.Send` (канал) или `Chat.ReadWrite.All` (чат). |

Если плагин `teams_pipeline` **не** включён, эти настройки неактивны — они подключаются только когда среда конвейера привязывается к входу Graph‑вебхука.

---

## Продакшн‑развёртывание

Для постоянного сервера пропусти dev‑туннель и зарегистрируй бота с публичным HTTPS‑эндпоинтом твоего сервера:

```bash
teams app create \
  --name "Hermes" \
  --endpoint "https://your-domain.com/api/messages"
```

Если бот уже создан и нужно лишь обновить эндпоинт:

```bash
teams app update --id <teamsAppId> --endpoint "https://your-domain.com/api/messages"
```

Убедись, что настроенный порт (`TEAMS_PORT`, по умолчанию `3978`) доступен из интернета и TLS‑сертификат действителен — Teams отклоняет самоподписанные сертификаты.

---

## Устранение неполадок

| Проблема | Решение |
|----------|---------|
| Эндпоинт `health` работает, но бот не отвечает | Проверь, что туннель всё ещё запущен и эндпоинт сообщений бота совпадает с URL туннеля |
| `KeyError: 'teams'` в логах | Перезапусти контейнер — в текущей версии это исправлено |
| Бот отвечает ошибками аутентификации | Проверь, что `TEAMS_CLIENT_ID`, `TEAMS_CLIENT_SECRET` и `TEAMS_TENANT_ID` заданы правильно |
| `No inference provider configured` | Убедись, что `ANTHROPIC_API_KEY` (или ключ другого провайдера) установлен в `~/.hermes/.env` |
| Бот получает сообщения, но игнорирует их | Твой AAD‑object ID может отсутствовать в `TEAMS_ALLOWED_USERS`. Выполни `teams status --verbose`, чтобы найти его |
| URL туннеля меняется после перезапуска | URL dev‑туннеля сохраняются, если использовать именованный туннель (`devtunnel create hermes-bot`). ngrok и cloudflared генерируют новый URL каждый запуск, если нет платного плана — обнови эндпоинт бота с помощью `teams app update` |
| Teams показывает «This bot is not responding» | Вебхук вернул ошибку. Проверь `docker logs hermes` на наличие трассировок |
| `[teams] Failed to connect` в логах | SDK не смог аутентифицироваться. Дважды проверь учётные данные и соответствие tenant ID аккаунту, использованному в `teams login` |

---

## Безопасность

:::warning
**Всегда задавай `TEAMS_ALLOWED_USERS`** с AAD‑object ID авторизованных пользователей. Иначе любой, кто найдёт или установит твой бот, сможет с ним взаимодействовать.

Относись к `TEAMS_CLIENT_SECRET` как к паролю — периодически меняй его через портал Azure или Teams CLI.
:::

- Храни учётные данные в `~/.hermes/.env` с правами `600` (`chmod 600 ~/.hermes/.env`)
- Бот принимает сообщения только от пользователей, указанных в `TEAMS_ALLOWED_USERS`; неавторизованные сообщения отбрасываются без уведомления
- Твой публичный эндпоинт (`/api/messages`) аутентифицируется через Teams Bot Framework — запросы без валидного JWT отклоняются

## Связанные документы

- [Teams Meetings](/user-guide/messaging/teams-meetings)
- [Operate the Teams Meeting Pipeline](/guides/operate-teams-meeting-pipeline)