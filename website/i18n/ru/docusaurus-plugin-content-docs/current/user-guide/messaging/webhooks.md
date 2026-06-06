---
sidebar_position: 13
title: "Вебхуки"
description: "Получай события от GitHub, GitLab и других сервисов, чтобы инициировать запуск Hermes agent."
---

# Вебхуки

Получай события от внешних сервисов (GitHub, GitLab, JIRA, Stripe и др.) и автоматически запускай выполнение Hermes‑агента. Адаптер вебхуков запускает HTTP‑сервер, который принимает POST‑запросы, проверяет подписи HMAC, преобразует полезные данные в подсказки агенту и направляет ответы обратно к источнику или на другую настроенную платформу.

Агент обрабатывает событие и может ответить, разместив комментарии в PR, отправив сообщения в Telegram/Discord или записав результат в журнал.
## Видео‑урок

<div style={{position: 'relative', width: '100%', aspectRatio: '16 / 9', marginBottom: '1.5rem'}}>
  <iframe
    src="https://www.youtube.com/embed/WNYe5mD4fY8"
    title="Hermes Agent — Webhooks Tutorial"
    style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 0}}
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowFullScreen
  />
</div>

---
## Быстрый старт

1. Включи через `hermes gateway setup` или через переменные окружения
2. Определи маршруты в `config.yaml` **или** создай их динамически с помощью `hermes webhook subscribe`
3. Укажи сервису `http://your-server:8644/webhooks/<route-name>`

---
## Настройка

Существует два способа включить адаптер вебхуков.

### Через мастер настройки

```bash
hermes gateway setup
```

Следуй подсказкам, чтобы включить вебхуки, задать порт и установить глобальный секрет HMAC.

### Через переменные окружения

Добавь в `~/.hermes/.env`:

```bash
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8644        # default
WEBHOOK_SECRET=your-global-secret
```

### Проверка сервера

После запуска gateway:

```bash
curl http://localhost:8644/health
```

Ожидаемый ответ:

```json
{"status": "ok", "platform": "webhook"}
```

---
## Настройка маршрутов {#configuring-routes}

Маршруты определяют, как обрабатываются разные источники веб‑хуков. Каждый маршрут — это именованная запись в `platforms.webhook.extra.routes` вашего `config.yaml`.

### Свойства маршрута

| Property | Required | Description |
|----------|----------|-------------|
| `events` | No | Список типов событий, которые принимать (например `["pull_request"]`). Если пусто, принимаются все события. Тип события читается из `X-GitHub-Event`, `X-GitLab-Event` или `event_type` в payload. |
| `secret` | **Yes** | HMAC‑секрет для проверки подписи. При отсутствии в маршруте используется глобальный `secret`. Установите `"INSECURE_NO_AUTH"` только для тестов (пропускает проверку). |
| `prompt` | No | Строка‑шаблон с доступом к полям payload через точечную нотацию (например `{pull_request.title}`). Если опущено, весь JSON‑payload будет помещён в запрос. |
| `skills` | No | Список названий навыков, которые нужно загрузить для выполнения агента. |
| `deliver` | No | Куда отправлять ответ: `github_comment`, `telegram`, `discord`, `slack`, `signal`, `sms`, `whatsapp`, `matrix`, `mattermost`, `homeassistant`, `email`, `dingtalk`, `feishu`, `wecom`, `weixin`, `bluebubbles`, `qqbot` или `log` (по умолчанию). |
| `deliver_extra` | No | Дополнительные параметры доставки — ключи зависят от типа `deliver` (например `repo`, `pr_number`, `chat_id`). Значения поддерживают те же шаблоны `{dot.notation}`, что и `prompt`. |
| `deliver_only` | No | Если `true`, полностью пропустить агента — отрендеренный шаблон `prompt` становится буквальным сообщением, которое доставляется. Нулевые затраты LLM, доставка за доли секунды. См. [Direct Delivery Mode](#direct-delivery-mode) для примеров использования. Требует, чтобы `deliver` указывал реальную цель (не `log`). |

### Полный пример

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      port: 8644
      secret: "global-fallback-secret"
      routes:
        github-pr:
          events: ["pull_request"]
          secret: "github-webhook-secret"
          prompt: |
            Review this pull request:
            Repository: {repository.full_name}
            PR #{number}: {pull_request.title}
            Author: {pull_request.user.login}
            URL: {pull_request.html_url}
            Diff URL: {pull_request.diff_url}
            Action: {action}
          skills: ["github-code-review"]
          deliver: "github_comment"
          deliver_extra:
            repo: "{repository.full_name}"
            pr_number: "{number}"
        deploy-notify:
          events: ["push"]
          secret: "deploy-secret"
          prompt: "New push to {repository.full_name} branch {ref}: {head_commit.message}"
          deliver: "telegram"
```

### Шаблоны запросов

В запросах используется точечная нотация для доступа к вложенным полям payload веб‑хука:

- `{pull_request.title}` раскрывается как `payload["pull_request"]["title"]`
- `{repository.full_name}` раскрывается как `payload["repository"]["full_name"]`
- `{__raw__}` — специальный токен, который выводит **всю полезную нагрузку** в виде отформатированного JSON (обрезается до 4000 символов). Полезно для мониторинговых алертов или общих веб‑хуков, когда агенту нужен полный контекст.
- Отсутствующие ключи оставляются как буквальная строка `{key}` (без ошибки)
- Вложенные словари и списки сериализуются в JSON и обрезаются до 2000 символов

Можно комбинировать `{__raw__}` с обычными переменными шаблона:

```yaml
prompt: "PR #{pull_request.number} by {pull_request.user.login}: {__raw__}"
```

Если для маршрута не задан шаблон `prompt`, весь payload выводится как отформатированный JSON (обрезается до 4000 символов).

Те же шаблоны точечной нотации работают и в значениях `deliver_extra`.

### Доставка в тему форума

При доставке ответов веб‑хуков в Telegram можно указать конкретную тему форума, добавив `message_thread_id` (или `thread_id`) в `deliver_extra`:

```yaml
webhooks:
  routes:
    alerts:
      events: ["alert"]
      prompt: "Alert: {__raw__}"
      deliver: "telegram"
      deliver_extra:
        chat_id: "-1001234567890"
        message_thread_id: "42"
```

Если `chat_id` не указан в `deliver_extra`, доставка будет выполнена в основной канал, настроенный для целевой платформы.
## Обзор PR на GitHub (Шаг за шагом) {#github-pr-review}

Этот пошаговый гид настраивает автоматический код‑ревью для каждого pull‑request.

### 1. Создай webhook в GitHub

1. Перейди в свой репозиторий → **Settings** → **Webhooks** → **Add webhook**
2. Укажи **Payload URL**: `http://your-server:8644/webhooks/github-pr`
3. Выбери **Content type**: `application/json`
4. Укажи **Secret**, совпадающий с конфигурацией маршрута (например, `github-webhook-secret`)
5. В разделе **Which events?** выбери **Let me select individual events** и отметь **Pull requests**
6. Нажми **Add webhook**

### 2. Добавь конфигурацию маршрута

Добавь маршрут `github-pr` в свой `~/.hermes/config.yaml`, как показано в примере выше.

### 3. Убедись, что `gh` CLI аутентифицирован

Тип доставки `github_comment` использует GitHub CLI для публикации комментариев:

```bash
gh auth login
```

### 4. Проверь работу

Открой pull‑request в репозитории. Webhook сработает, Hermes обработает событие и опубликует комментарий‑ревью в PR.
## Настройка веб‑хука GitLab {#gitlab-webhook-setup}

Веб‑хуки GitLab работают аналогично, но используют иной механизм аутентификации. GitLab отправляет секрет в виде простого заголовка `X‑Gitlab‑Token` (точное совпадение строки, без HMAC).

### 1. Создай веб‑хук в GitLab

1. Перейди в свой проект → **Settings** → **Webhooks**
2. Укажи **URL** `http://your-server:8644/webhooks/gitlab-mr`
3. Введи свой **Secret token**
4. Выбери **Merge request events** (и любые другие события, которые нужны)
5. Нажми **Add webhook**

### 2. Добавь конфигурацию маршрута

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      routes:
        gitlab-mr:
          events: ["merge_request"]
          secret: "your-gitlab-secret-token"
          prompt: |
            Review this merge request:
            Project: {project.path_with_namespace}
            MR !{object_attributes.iid}: {object_attributes.title}
            Author: {object_attributes.last_commit.author.name}
            URL: {object_attributes.url}
            Action: {object_attributes.action}
          deliver: "log"
```

---
## Параметры доставки {#delivery-options}

Поле `deliver` определяет, куда будет отправлен ответ агента после обработки события webhook.

| Тип доставки | Описание |
|-------------|----------|
| `log` | Записывает ответ в вывод журнала **gateway**. Это значение по умолчанию и удобно для тестирования. |
| `github_comment` | Публикует ответ как комментарий к PR/issue через CLI `gh`. Требует `deliver_extra.repo` и `deliver_extra.pr_number`. CLI `gh` должен быть установлен и аутентифицирован на хосте **gateway** (`gh auth login`). |
| `telegram` | Направляет ответ в Telegram. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `discord` | Направляет ответ в Discord. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `slack` | Направляет ответ в Slack. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `signal` | Направляет ответ в Signal. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `sms` | Направляет ответ в SMS через Twilio. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `whatsapp` | Направляет ответ в WhatsApp. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `matrix` | Направляет ответ в Matrix. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `mattermost` | Направляет ответ в Mattermost. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `homeassistant` | Направляет ответ в Home Assistant. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `email` | Направляет ответ на Email. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `dingtalk` | Направляет ответ в DingTalk. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `feishu` | Направляет ответ в Feishu/Lark. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `wecom` | Направляет ответ в WeCom. Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `weixin` | Направляет ответ в Weixin (WeChat). Использует домашний канал или указывает `chat_id` в `deliver_extra`. |
| `bluebubbles` | Направляет ответ в BlueBubbles (iMessage). Использует домашний канал или указывает `chat_id` в `deliver_extra`. |

Для кроссплатформенной доставки целевая платформа также должна быть включена и подключена в **gateway**. Если `chat_id` не указан в `deliver_extra`, ответ будет отправлен в настроенный домашний канал этой платформы.
## Режим прямой доставки {#direct‑delivery‑mode}

По умолчанию каждый POST‑запрос веб‑хука запускает выполнение агента — полезная нагрузка становится подсказкой, агент её обрабатывает, и ответ агента доставляется. Это расходует токены LLM при каждом событии.

Для сценариев, когда нужно просто **отправить обычное уведомление** — без рассуждений, без цикла агента, просто доставить сообщение — установи `deliver_only: true` в маршруте. Отрендеренный шаблон `prompt` становится буквальным телом сообщения, и адаптер отправляет его напрямую в настроенную цель доставки.

### Когда использовать прямую доставку

- **Отправка внешнего сервиса** — веб‑хук Supabase/Firebase срабатывает при изменении базы данных → мгновенно уведомить пользователя в Telegram
- **Оповещения мониторинга** — веб‑хук Datadog/Grafana → отправить в канал Discord
- **Взаимные пинги агентов** — Агент A уведомляет пользователя Агент B о завершении длительной задачи
- **Завершение фоновой задачи** — Cron‑задача завершилась → отправить результат в Slack

Преимущества:

- **Ноль токенов LLM** — агент никогда не вызывается
- **Доставка за доли секунды** — один вызов адаптера, без цикла рассуждений
- **Та же безопасность, что и в режиме агента** — HMAC‑аутентификация, ограничения скорости, идемпотентность и ограничения размера тела продолжают действовать
- **Синхронный ответ** — POST возвращает `200 OK`, когда доставка успешна, или `502`, если цель отклонила запрос, позволяя вашему upstream‑сервису повторять попытки разумно

### Пример: отправка в Telegram из Supabase

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      port: 8644
      secret: "global-secret"
      routes:
        antenna-matches:
          secret: "antenna-webhook-secret"
          deliver: "telegram"
          deliver_only: true
          prompt: "🎉 New match: {match.user_name} matched with you!"
          deliver_extra:
            chat_id: "{match.telegram_chat_id}"
```

Твоя edge‑функция Supabase подписывает полезную нагрузку с помощью HMAC‑SHA256 и делает POST на `https://your-server:8644/webhooks/antenna-matches`. Адаптер веб‑хука проверяет подпись, рендерит шаблон из полезной нагрузки, доставляет в Telegram и возвращает `200 OK`.

### Пример: динамическая подписка через CLI

```bash
hermes webhook subscribe antenna-matches \
  --deliver telegram \
  --deliver-chat-id "123456789" \
  --deliver-only \
  --prompt "🎉 New match: {match.user_name} matched with you!" \
  --description "Antenna match notifications"
```

### Коды ответов

| Статус | Значение |
|--------|----------|
| `200 OK` | Успешно доставлено. Тело: `{"status": "delivered", "route": "...", "target": "...", "delivery_id": "..."}` |
| `200 OK` (status=duplicate) | Дублирующий `X‑GitHub‑Delivery` ID в пределах TTL идемпотентности (1 час). Не переотправлено. |
| `401 Unauthorized` | HMAC‑подпись недействительна или отсутствует. |
| `400 Bad Request` | Неправильный JSON в теле запроса. |
| `404 Not Found` | Неизвестное имя маршрута. |
| `413 Payload Too Large` | Тело превысило `max_body_bytes`. |
| `429 Too Many Requests` | Превышен лимит запросов для маршрута. |
| `502 Bad Gateway` | Адаптер‑цель отклонил сообщение или сгенерировал ошибку. Ошибка записана в журнал сервера; тело ответа — общее `Delivery failed`, чтобы не раскрывать внутренности адаптера. |

### Подводные камни конфигурации

- `deliver_only: true` требует, чтобы `deliver` указывал на реальную цель. `deliver: log` (или отсутствие `deliver`) отклоняется при запуске — адаптер отказывается стартовать, если обнаружит некорректный маршрут.
- Поле `skills` игнорируется в режиме прямой доставки (агент не запускается, поэтому нечего внедрять).
- Рендеринг шаблона использует тот же синтаксис `{dot.notation}` что и в режиме агента, включая токен `{__raw__}`.
- Идемпотентность использует те же заголовки `X‑GitHub‑Delivery` / `X‑Request‑ID` — повторные запросы с тем же ID возвращают `status=duplicate` и НЕ переотправляются.
## Динамические подписки (CLI) {#dynamic-subscriptions}

В дополнение к статическим маршрутам в `config.yaml` ты можешь создавать подписки на веб‑хуки динамически с помощью команды CLI `hermes webhook`. Это особенно полезно, когда агенту самому нужно настраивать триггеры, основанные на событиях.

### Создать подписку

```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New issue #{issue.number}: {issue.title}\nBy: {issue.user.login}\n\n{issue.body}" \
  --deliver telegram \
  --deliver-chat-id "-100123456789" \
  --description "Triage new GitHub issues"
```

Это возвращает URL веб‑хука и автоматически сгенерированный HMAC‑секрет. Настрой свой сервис так, чтобы он делал `POST` на этот URL.

### Список подписок

```bash
hermes webhook list
```

### Удалить подписку

```bash
hermes webhook remove github-issues
```

### Протестировать подписку

```bash
hermes webhook test github-issues
hermes webhook test github-issues --payload '{"issue": {"number": 42, "title": "Test"}}'
```

### Как работают динамические подписки

- Подписки хранятся в `~/.hermes/webhook_subscriptions.json`
- Адаптер веб‑хуков автоматически перезагружает этот файл при каждом входящем запросе (по времени изменения файла, пренебрежимо небольшие накладные расходы)
- Статические маршруты из `config.yaml` всегда имеют приоритет над динамическими с тем же именем
- Динамические подписки используют тот же формат маршрутов и возможности, что и статические (события, шаблоны подсказок, инструменты, доставка)
- Перезапуск шлюза не требуется — подпишись, и подписка сразу активна

### Подписки, управляемые агентом

Агент может создавать подписки через терминальный инструмент, когда его направляет навык `webhook-subscriptions`. Попроси агента «настроить веб‑хук для задач GitHub», и он выполнит соответствующую команду `hermes webhook subscribe`.
## Security {#security}

The webhook adapter includes multiple layers of security:

### HMAC signature validation

The adapter validates incoming webhook signatures using the appropriate method for each source:

- **GitHub**: `X-Hub-Signature-256` header — HMAC‑SHA256 hex digest prefixed with `sha256=`
- **GitLab**: `X-Gitlab-Token` header — plain secret string match
- **Generic**: `X-Webhook-Signature` header — raw HMAC‑SHA256 hex digest

If a secret is configured but no recognized signature header is present, the request is rejected.

### Secret is required

Every route must have a secret — either set directly on the route or inherited from the global `secret`. Routes without a secret cause the adapter to fail at startup with an error. For development/testing only, you can set the secret to `"INSECURE_NO_AUTH"` to skip validation entirely.

`INSECURE_NO_AUTH` is only accepted when the gateway is bound to a loopback host (`127.0.0.1`, `localhost`, `::1`). If it is combined with a non-loopback bind such as `0.0.0.0` or a LAN IP, the adapter refuses to start — this prevents accidentally exposing an unauthenticated endpoint on a public interface.

### Rate limiting

Each route is rate‑limited to **30 requests per minute** by default (fixed‑window). Configure this globally:

```yaml
platforms:
  webhook:
    extra:
      rate_limit: 60  # requests per minute
```

Requests exceeding the limit receive a `429 Too Many Requests` response.

### Idempotency

Delivery IDs (from `X-GitHub-Delivery`, `X-Request-ID`, or a timestamp fallback) are cached for **1 hour**. Duplicate deliveries (e.g. webhook retries) are silently skipped with a `200` response, preventing duplicate agent runs.

### Body size limits

Payloads exceeding **1 MB** are rejected before the body is read. Configure this:

```yaml
platforms:
  webhook:
    extra:
      max_body_bytes: 2097152  # 2 MB
```

### Prompt injection risk

:::warning
Webhook payloads contain attacker‑controlled data — PR titles, commit messages, issue descriptions, etc. can all contain malicious instructions. Run the gateway in a sandboxed environment (Docker, VM) when exposed to the internet. Consider using the Docker or SSH terminal backend for isolation.
:::

---
## Устранение неполадок {#troubleshooting}

### Webhook не приходит

- Убедись, что порт открыт и доступен из источника webhook
- Проверь правила брандмауэра — порт `8644` (или твой настроенный порт) должен быть открыт
- Убедись, что путь URL совпадает: `http://your-server:8644/webhooks/<route-name>`
- Используй эндпоинт `/health`, чтобы подтвердить, что сервер работает

### Ошибка проверки подписи

- Убедись, что секрет в конфигурации маршрута точно совпадает с секретом, настроенным в источнике webhook
- Для GitHub секрет основан на HMAC — проверь `X-Hub-Signature-256`
- Для GitLab секрет — простое совпадение токена — проверь `X-Gitlab-Token`
- Проверь логи gateway на предупреждения `Invalid signature`

### Событие игнорируется

- Проверь, что тип события присутствует в списке `events` твоего маршрута
- События GitHub используют значения вроде `pull_request`, `push`, `issues` (значение заголовка `X-GitHub-Event`)
- События GitLab используют значения вроде `merge_request`, `push` (значение заголовка `X-GitLab-Event`)
- Если `events` пустой или не задан, принимаются все события

### Агент не отвечает

- Запусти gateway в foreground, чтобы увидеть логи: `hermes gateway run`
- Убедись, что шаблон подсказки рендерится корректно
- Проверь, что цель доставки настроена и подключена

### Дублирующиеся ответы

- Кеш идемпотентности должен предотвращать это — проверь, что источник webhook отправляет заголовок ID доставки (`X-GitHub-Delivery` или `X-Request-ID`)
- ID доставки кэшируются в течение 1 часа

### Ошибки `gh` CLI (доставка комментариев GitHub)

- Выполни `gh auth login` на хосте gateway
- Убедись, что аутентифицированный пользователь GitHub имеет права записи в репозиторий
- Проверь, что `gh` установлен и находится в `PATH`

---
## Переменные окружения {#environment-variables}

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBHOOK_ENABLED` | Включить адаптер платформы webhook | `false` |
| `WEBHOOK_PORT` | Порт HTTP‑сервера для получения webhook‑ов | `8644` |
| `WEBHOOK_SECRET` | Глобальный HMAC‑секрет (используется как запасной вариант, когда маршруты не задают собственный) | _(none)_ |