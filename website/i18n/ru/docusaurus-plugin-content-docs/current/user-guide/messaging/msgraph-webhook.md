---
sidebar_position: 23
title: "Microsoft Graph прослушиватель вебхуков"
description: "Получать уведомления об изменениях Microsoft Graph (встречи, календарь, чат и т.д.) в Hermes"
---

# Microsoft Graph Webhook Listener

Платформа шлюза `msgraph_webhook` — это входной обработчик событий. Именно так Hermes получает **уведомления об изменениях** от Microsoft Graph — «завершилось собрание Teams», «в этот чат пришло новое сообщение», «это событие календаря было обновлено». В отличие от платформы `teams` (которая представляет собой чат‑бота, к которому пишут пользователи) — здесь M365 сообщает Hermes, что что‑то произошло, а не человек.

Сейчас основным потребителем является конвейер сводки собраний Teams: Graph посылает уведомление, когда собрание генерирует транскрипт, конвейер получает его, а Hermes публикует сводку обратно в Teams. Другие ресурсы Graph (`/chats/.../messages`, `/users/.../events`) используют тот же обработчик — потребители конвейеров добавляют свои PR‑ы.

## Prerequisites

- Учётные данные приложения Microsoft Graph — [Register a Microsoft Graph Application](/guides/microsoft-graph-app-registration)
- **Публичный HTTPS‑URL**, доступный для Microsoft Graph (Graph не вызывает приватные эндпоинты). Для тестов подходит dev‑туннель; в продакшене нужен реальный домен с действительным сертификатом.
- Сильный общий секрет, который будет использоваться в качестве значения `clientState`. Сгенерировать его можно командой `openssl rand -hex 32` и поместить в `~/.hermes/.env` как `MSGRAPH_WEBHOOK_CLIENT_STATE`.

## Quick Start

Минимальный `~/.hermes/config.yaml`:

```yaml
platforms:
  msgraph_webhook:
    enabled: true
    extra:
      host: 127.0.0.1
      port: 8646
      client_state: "replace-with-a-strong-secret"
      accepted_resources:
        - "communications/onlineMeetings"
```

Или через переменные окружения в `~/.hermes/.env` (автоматически объединяются при старте):

```bash
MSGRAPH_WEBHOOK_ENABLED=true
MSGRAPH_WEBHOOK_PORT=8646
MSGRAPH_WEBHOOK_CLIENT_STATE=<generate-with-openssl-rand-hex-32>
MSGRAPH_WEBHOOK_ACCEPTED_RESOURCES=communications/onlineMeetings
```

> Примечание: хост привязки читается из `extra.host` в `config.yaml` (см. пример выше); переменная окружения `MSGRAPH_WEBHOOK_HOST` переопределять не будет.

Запусти шлюз: `hermes gateway run`. Обработчик открывает:

- `POST /msgraph/webhook` — уведомления об изменениях от Graph
- `GET /msgraph/webhook?validationToken=...` — рукопожатие проверки подписки Graph
- `GET /health` — проверка готовности с счётчиками принятых/дублированных запросов

Опубликуй обработчик публично (reverse proxy, dev‑туннель, ingress). Твой URL‑адрес уведомлений для подписок Graph — это публичный HTTPS‑origin, к которому добавлен путь `/msgraph/webhook`:

```
https://ops.example.com/msgraph/webhook
```

## Configuration

Все настройки находятся под `platforms.msgraph_webhook.extra`:

| Setting | Default | Description |
|---------|---------|-------------|
| `host` | `0.0.0.0` | Адрес привязки HTTP‑обработчика. Для неблокирующих (не‑loopback) привязок требуется `allowed_source_cidrs`; привязка к loopback (`127.0.0.1` / `::1`) — самый простой вариант для dev‑туннеля / reverse‑proxy. |
| `port` | `8646` | Порт привязки. |
| `webhook_path` | `/msgraph/webhook` | URL‑путь, на который Graph делает POST. |
| `health_path` | `/health` | Эндпоинт проверки готовности. |
| `client_state` | — | Общий секрет, который Graph отсылает в каждом уведомлении. Сравнивается с помощью `hmac.compare_digest` — генерировать `openssl rand -hex 32`. |
| `accepted_resources` | `[]` (принимать все) | Белый список путей/шаблонов ресурсов Graph. Суффикс `*` работает как префикс‑соответствие. Начальный `/` допускается. Пример: `["communications/onlineMeetings", "chats/*/messages"]`. |
| `max_seen_receipts` | `5000` | Размер кэша дедупликации по ID уведомлений. При достижении лимита самые старые записи удаляются. |
| `allowed_source_cidrs` | `[]` | Требуется для неблокирующих привязок. Оставляй пустым только когда обработчик привязан к loopback и находится за локальным туннелем / reverse‑proxy. |

Каждая настройка имеет соответствующую переменную окружения (`MSGRAPH_WEBHOOK_*`), которая объединяется с конфигом при старте шлюза — см. [справочник переменных окружения](/reference/environment-variables#microsoft-graph-teams-meetings).

## Security Hardening

### clientState — основной механизм аутентификации

Каждое уведомление Graph содержит строку `clientState`, указанную при регистрации подписки. Обработчик отклоняет любые уведомления, у которых `clientState` не совпадает, используя сравнение, устойчивое к тайминговым атакам. Это задокументированный механизм Microsoft — рассматривай значение как сильный общий секрет.

Если `client_state` не задан, обработчик откажется запускаться.

### Белый список IP‑адресов источника (продакшн‑развёртывания)

Для продакшна ограничь обработчик IP‑диапазонами webhook‑источников Microsoft Graph. Microsoft публикует эти диапазоны в сервисе [Office 365 IP Address and URL Web service](https://learn.microsoft.com/en-us/microsoft-365/enterprise/urls-and-ip-address-ranges). Настрой их так:

```yaml
platforms:
  msgraph_webhook:
    enabled: true
    extra:
      host: 0.0.0.0
      client_state: "..."
      allowed_source_cidrs:
        - "52.96.0.0/14"
        - "52.104.0.0/14"
        # ...add the current Microsoft 365 "Common" + "Teams" category egress ranges
```

Или через переменную окружения:

```bash
MSGRAPH_WEBHOOK_ALLOWED_SOURCE_CIDRS="52.96.0.0/14,52.104.0.0/14"
```

Привязка к неблокирующему хосту, например `0.0.0.0`, `::` или LAN‑IP без `allowed_source_cidrs`, приводит к отказу при старте. Если используешь dev‑туннель или reverse‑proxy на той же машине, привязывай Hermes к `127.0.0.1` или `::1` и оставляй список пустым. Неправильные CIDR‑строки выводятся в лог как предупреждение и игнорируются. **Проверяй список IP Microsoft каждый квартал** — он меняется.

### Завершение TLS

Обработчик работает по обычному HTTP. TLS‑терминацию делай на reverse‑proxy (Caddy, Nginx, Cloudflare Tunnel, AWS ALB) и проксируй запросы к обработчику по локальной сети. Graph отказывает в доставке на не‑HTTPS эндпоинты, поэтому путь без шифрования к тебе от Graph просто не существует.

### Гигиена ответов

При успешной обработке возвращается `202 Accepted` с пустым телом — внутренние счётчики не попадают в ответ. Операторы могут наблюдать метрики через `/health`, который защищён теми же правилами IP‑белого списка, что и путь webhook.

Таблица кодов статусов:

| Outcome | Status |
|---------|--------|
| Уведомление(я) принято(ы) или дедуплицировано | 202 |
| Проверка подписки (GET с `validationToken`) | 200 (отдаёт токен) |
| Все элементы в батче не прошли проверку clientState | 403 |
| Некорректный JSON / отсутствует массив `value` / неизвестный ресурс | 400 |
| IP‑адрес источника не в белом списке | 403 |
| Простой GET без `validationToken` | 400 |

## Troubleshooting

| Problem | What to check |
|---------|---------------|
| Проверка подписки Graph не проходит | Публичный URL доступен, путь `/msgraph/webhook` совпадает, GET с `validationToken` отдает токен как `text/plain` в течение 10 секунд. |
| POST‑уведомления приходят, но ничего не обрабатывается | `client_state` совпадает с тем, что указан при регистрации подписки. Сгенерируй новый `openssl rand -hex 32` и создай новую подписку, если значение изменилось. Проверь, что `accepted_resources` включает путь, который отправляет Graph. |
| Все уведомления получают 403 | Несоответствие `clientState` (подделано или подписка зарегистрирована с другим значением). Пересоздай подписку командой `hermes teams-pipeline subscribe --client-state "$MSGRAPH_WEBHOOK_CLIENT_STATE" ...` (команда входит в runtime PR конвейера). |
| Обработчик отказывается запускаться на `0.0.0.0` | Укажи `allowed_source_cidrs` с текущими диапазонами webhook Microsoft, либо привязывай Hermes к `127.0.0.1` / `::1` за туннелем или reverse‑proxy. |
| Обработчик запущен, но `curl http://localhost:8646/health` зависает | Конфликт привязки порта. Проверь `ss -tlnp \| grep 8646` и при необходимости измени `port:`. |
| Реальные запросы от Microsoft получают 403 | Белый список IP‑адресов слишком узок. Расширь его, включив текущие диапазоны egress Microsoft. Если ты всё ещё проверяешь путь туннеля, привязывай Hermes к loopback и позволяй туннелю обеспечивать публичный доступ. |

## Related Docs

- [Register a Microsoft Graph Application](/guides/microsoft-graph-app-registration) — предварительные условия регистрации Azure‑приложения
- [Environment Variables → Microsoft Graph](/reference/environment-variables#microsoft-graph-teams-meetings) — полный список переменных окружения
- [Microsoft Teams bot setup](/user-guide/messaging/teams) — другая платформа, позволяющая пользователям общаться с Hermes в Teams