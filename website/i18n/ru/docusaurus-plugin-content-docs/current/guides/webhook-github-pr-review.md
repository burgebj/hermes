---
sidebar_position: 11
sidebar_label: "GitHub PR Reviews via Webhook"
title: "Автоматические комментарии к PR на GitHub с веб‑хуками"
description: "Подключи Hermes к GitHub, чтобы он автоматически получал diffs PR, проверял изменения кода и оставлял комментарии — по веб‑хукам без ручного запуска."
---

# Автоматические комментарии к PR в GitHub через вебхуки

Это руководство проведёт тебя через процесс подключения Hermes Agent к GitHub, чтобы он автоматически получал **diff** пул‑реквеста, анализировал изменения кода и публиковал комментарий — это происходит при событии вебхука без какого‑либо ручного запуска.

Когда PR открывается или обновляется, GitHub отправляет POST‑запрос вебхука в твой экземпляр Hermes. Hermes запускает агент с подсказкой, которая инструктирует его получить **diff** с помощью `gh` CLI, а ответ публикуется обратно в тему обсуждения PR.

:::tip Хочешь более простую настройку без публичного эндпоинта?
Если у тебя нет публичного URL или ты просто хочешь быстро начать, посмотри [Build a GitHub PR Review Agent](./github-pr-review-agent.md) — использует cron‑задачи для опроса PR по расписанию, работает за NAT и межсетевыми экранами.
:::

:::info Справочная документация
Для полного справочника по платформе вебхуков (все параметры конфигурации, типы доставки, динамические подписки, модель безопасности) смотри [Webhooks](/user-guide/messaging/webhooks).
:::

:::warning Риск инъекции подсказок
Полезные нагрузки вебхуков содержат данные, контролируемые атакующим — заголовки PR, сообщения коммитов и описания могут включать вредоносные инструкции. Когда твой эндпоинт вебхука доступен из интернета, запускай шлюз в изолированной среде (Docker, SSH‑бэкенд). См. раздел [security section](#security-notes) ниже.
:::

---
## Предварительные требования

- Hermes Agent установлен и запущен (`hermes gateway`)
- [`gh` CLI](https://cli.github.com/) установлен и аутентифицирован на хосте шлюза (`gh auth login`)
- Публично доступный URL для твоего экземпляра Hermes (см. [Локальное тестирование с ngrok](#local-testing-with-ngrok), если запускаешь локально)
- Административный доступ к репозиторию GitHub (необходим для управления веб‑хуками)
## Шаг 1 — Включить платформу веб‑хуков

Добавь следующее в свой `~/.hermes/config.yaml`:

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      port: 8644          # default; change if another service occupies this port
      rate_limit: 30      # max requests per minute per route (not a global cap)

      routes:
        github-pr-review:
          secret: "your-webhook-secret-here"   # must match the GitHub webhook secret exactly
          events:
            - pull_request

          # The agent is instructed to fetch the actual diff before reviewing.
          # {number} and {repository.full_name} are resolved from the GitHub payload.
          prompt: |
            A pull request event was received (action: {action}).

            PR #{number}: {pull_request.title}
            Author: {pull_request.user.login}
            Branch: {pull_request.head.ref} → {pull_request.base.ref}
            Description: {pull_request.body}
            URL: {pull_request.html_url}

            If the action is "closed" or "labeled", stop here and do not post a comment.

            Otherwise:
            1. Run: gh pr diff {number} --repo {repository.full_name}
            2. Review the code changes for correctness, security issues, and clarity.
            3. Write a concise, actionable review comment and post it.

          deliver: github_comment
          deliver_extra:
            repo: "{repository.full_name}"
            pr_number: "{number}"
```

**Ключевые поля:**

| Поле | Описание |
|---|---|
| `secret` (уровень маршрута) | HMAC‑секрет для этого маршрута. При отсутствии используется глобальный `extra.secret`. |
| `events` | Список значений заголовка `X‑GitHub‑Event`, которые принимаются. Пустой список = принимать все. |
| `prompt` | Шаблон; `{field}` и `{nested.field}` подставляются из полезной нагрузки GitHub. |
| `deliver` | `github_comment` публикует через `gh pr comment`. `log` просто пишет в журнал шлюза. |
| `deliver_extra.repo` | Разрешается, например, как `org/repo` из полезной нагрузки. |
| `deliver_extra.pr_number` | Разрешается в номер PR из полезной нагрузки. |

:::note Полезная нагрузка не содержит кода
Полезная нагрузка веб‑хука GitHub включает метаданные PR (заголовок, описание, имена веток, URL), но **не дифф**. Приведённый выше запрос инструктирует агента выполнить `gh pr diff` для получения фактических изменений. Инструмент `terminal` включён в набор инструментов `hermes-webhook` по умолчанию, поэтому дополнительная конфигурация не требуется.
:::

---
## Шаг 2 — Запусти шлюз

```bash
hermes gateway
```

Ты должен увидеть:

```
[webhook] Listening on 0.0.0.0:8644 — routes: github-pr-review
```

Убедись, что он работает:

```bash
curl http://localhost:8644/health
# {"status": "ok", "platform": "webhook"}
```

---
## Шаг 3 — Регистрация веб‑хука на GitHub

1. Перейди в свой репозиторий → **Settings** → **Webhooks** → **Add webhook**
2. Заполни:
   - **Payload URL:** `https://your-public-url.example.com/webhooks/github-pr-review`
   - **Content type:** `application/json`
   - **Secret:** то же значение, которое ты указал для `secret` в конфигурации маршрута
   - **Which events?** → **Select individual events** → отметь **Pull requests**
3. Нажми **Add webhook**

GitHub сразу отправит событие `ping` для подтверждения соединения. Оно безопасно игнорируется — `ping` нет в твоём списке `events` — и возвращает `{"status": "ignored", "event": "ping"}`. Оно записывается только на уровне DEBUG, поэтому не будет отображаться в консоли при уровне логирования по умолчанию.

---
## Шаг 4 — Открыть тестовый PR

Создай ветку, отправь изменения и открой PR. В течение 30–90 секунд (в зависимости от размера PR и модели) Hermes должен разместить комментарий‑обзор.

Чтобы следить за прогрессом агента в реальном времени:

```bash
tail -f "${HERMES_HOME:-$HOME/.hermes}/logs/gateway.log"
```

---
## Локальное тестирование с ngrok

Если Hermes запущен на твоём ноутбуке, используй [ngrok](https://ngrok.com/) для его доступности:

```bash
ngrok http 8644
```

Скопируй URL `https://...ngrok‑free.app` и используй его как GitHub Payload URL. На бесплатном тарифе ngrok URL меняется каждый раз при перезапуске ngrok — обновляй свой GitHub webhook каждую сессию. Платные аккаунты ngrok получают статический домен.

Ты можешь быстро проверить статический маршрут напрямую с помощью `curl` — без учётной записи GitHub и реального PR.

:::tip Используй `deliver: log` при локальном тестировании
Замени `deliver: github_comment` на `deliver: log` в конфигурации во время тестов. Иначе агент попытается разместить комментарий в фиктивный репозиторий `org/repo#99` в тестовом payload, что завершится ошибкой. Верни `deliver: github_comment`, когда будешь доволен выводом подсказки.
:::

```bash
SECRET="your-webhook-secret-here"
BODY='{"action":"opened","number":99,"pull_request":{"title":"Test PR","body":"Adds a feature.","user":{"login":"testuser"},"head":{"ref":"feat/x"},"base":{"ref":"main"},"html_url":"https://github.com/org/repo/pull/99"},"repository":{"full_name":"org/repo"}}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print "sha256="$2}')

curl -s -X POST http://localhost:8644/webhooks/github-pr-review \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-Hub-Signature-256: $SIG" \
  -d "$BODY"
# Expected: {"status":"accepted","route":"github-pr-review","event":"pull_request","delivery_id":"..."}
```

Затем наблюдай за работой агента:
```bash
tail -f "${HERMES_HOME:-$HOME/.hermes}/logs/gateway.log"
```

:::note
`hermes webhook test <name>` работает только для **динамических подписок**, созданных с помощью `hermes webhook subscribe`. Он не читает маршруты из `config.yaml`.
:::

---
## Фильтрация по конкретным действиям

GitHub отправляет события `pull_request` для множества действий: `opened`, `synchronize`, `reopened`, `closed`, `labeled` и т.д. Список `events` фильтрует только по значению заголовка `X-GitHub-Event` — он не может отфильтровать по подтипу действия на уровне маршрутизации.

Подсказка в Шаге 1 уже учитывает это, инструктируя агента остановиться сразу для событий `closed` и `labeled`.

:::warning Агент всё равно запускается и потребляет токены
Инструкция «stop here» препятствует проведению содержательного обзора, но агент всё равно выполняется до конца для каждого события `pull_request` независимо от действия. Веб‑хуки GitHub могут фильтровать только по типу события (`pull_request`, `push`, `issues` и т.п.) — не по подтипу действия (`opened`, `closed`, `labeled`). Фильтрации на уровне маршрутизации для поддействий нет. Для репозиториев с высоким объёмом трафика прими эту нагрузку или фильтруй на этапе upstream с помощью workflow GitHub Actions, который условно вызывает твой URL веб‑хука.
:::

> Синтаксис Jinja2 или условных шаблонов недоступен. Поддерживаются только подстановки `{field}` и `{nested.field}`. Всё остальное передаётся агенту дословно.

---
## Использование навыка для единообразного стиля обзора

Загрузи [Hermes skill](/user-guide/features/skills), чтобы задать агенту постоянную персональность обзора. Добавь `skills` в свой маршрут внутри `platforms.webhook.extra.routes` в `config.yaml`:

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      routes:
        github-pr-review:
          secret: "your-webhook-secret-here"
          events: [pull_request]
          prompt: |
            A pull request event was received (action: {action}).
            PR #{number}: {pull_request.title} by {pull_request.user.login}
            URL: {pull_request.html_url}

            If the action is "closed" or "labeled", stop here and do not post a comment.

            Otherwise:
            1. Run: gh pr diff {number} --repo {repository.full_name}
            2. Review the diff using your review guidelines.
            3. Write a concise, actionable review comment and post it.
          skills:
            - review
          deliver: github_comment
          deliver_extra:
            repo: "{repository.full_name}"
            pr_number: "{number}"
```

> **Примечание:** Загружается только первый найденный навык в списке. Hermes не комбинирует несколько навыков — последующие записи игнорируются.
## Отправка ответов в Slack или Discord вместо этого

Замените поля `deliver` и `deliver_extra` в вашем маршруте на целевую платформу:

```yaml
# Inside platforms.webhook.extra.routes.<route-name>:

# Slack
deliver: slack
deliver_extra:
  chat_id: "C0123456789"   # Slack channel ID (omit to use the configured home channel)

# Discord
deliver: discord
deliver_extra:
  chat_id: "987654321012345678"  # Discord channel ID (omit to use home channel)
```

Целевая платформа также должна быть включена и подключена в шлюзе. Если `chat_id` не указан, ответ будет отправлен в домашний канал, настроенный для этой платформы.

Допустимые значения `deliver`: `log` · `github_comment` · `telegram` · `discord` · `slack` · `signal` · `sms`

---
## Поддержка GitLab

Тот же адаптер работает с GitLab. GitLab использует `X-Gitlab-Token` для аутентификации (прямое сравнение строки, без HMAC) — Hermes обрабатывает его автоматически.

Для фильтрации событий GitLab устанавливает `X-GitLab-Event` со значениями вроде `Merge Request Hook`, `Push Hook`, `Pipeline Hook`. Используй точное значение заголовка в `events`:

```yaml
events:
  - Merge Request Hook
```

Поля полезной нагрузки GitLab отличаются от полей GitHub — например, `{object_attributes.title}` для заголовка MR и `{object_attributes.iid}` для номера MR. Самый простой способ узнать полную структуру полезной нагрузки — нажать кнопку **Test** в настройках веб‑хука GitLab, совместив её с журналом **Recent Deliveries**. Либо убери `prompt` из конфигурации маршрута — Hermes тогда передаст полную полезную нагрузку в виде отформатированного JSON напрямую агенту, а ответ агента (видимый в журнале gateway с `deliver: log`) опишет её структуру.
## Примечания по безопасности

- **Никогда не используй `INSECURE_NO_AUTH`** в продакшене — он полностью отключает проверку подписи. Предназначено только для локальной разработки.
- **Периодически меняй секрет вебхука** и обновляй его как в GitHub (настройки вебхука), так и в твоём `config.yaml`.
- **Ограничение скорости** по умолчанию составляет 30 запросов/минуту на каждый маршрут (настраивается через `extra.rate_limit`). При превышении возвращается `429`.
- **Повторные доставки** (повторные попытки вебхука) дедуплицируются с помощью кэша идемпотентности сроком в 1 час. Ключ кэша — `X‑GitHub‑Delivery`, если он присутствует, затем `X‑Request‑ID`, затем метка времени в миллисекундах. Когда ни один из заголовков идентификатора доставки не установлен, повторные попытки **не** дедуплицируются.
- **Инъекция подсказок:** заголовки PR, описания и сообщения коммитов контролируются атакующим. Зловредные PR могут попытаться манипулировать действиями агента. Запускай gateway в изолированной среде (Docker, VM), когда он доступен из публичного интернета.
## Устранение неполадок

| Симптом | Проверка |
|---|---|
| `401 Invalid signature` | Секрет в `config.yaml` не совпадает с секретом веб‑хука GitHub |
| `404 Unknown route` | Имя маршрута в URL не совпадает с ключом в `routes:` |
| `429 Rate limit exceeded` | Превышено 30 запросов/минуту на маршрут — часто происходит при повторной доставке тестовых событий из интерфейса GitHub; подожди минуту или увеличь `extra.rate_limit` |
| No comment posted | `gh` не установлен, не находится в `PATH` или не аутентифицирован (`gh auth login`) |
| Agent runs but no comment | Проверь лог **gateway** — если вывод агента пустой или содержит только «SKIP», попытка доставки всё равно производится |
| Port already in use | Измени `extra.port` в `config.yaml` |
| Agent runs but reviews only the PR description | В подсказке отсутствует инструкция `gh pr diff` — дифф не присутствует в payload веб‑хука |
| Can't see the ping event | Игнорируемые события возвращают `{"status":"ignored","event":"ping"}` только на уровне лога DEBUG — проверь лог доставки GitHub (repo → Settings → Webhooks → your webhook → Recent Deliveries) |

**Вкладка Recent Deliveries в GitHub** (repo → Settings → Webhooks → your webhook) показывает точные заголовки запроса, payload, HTTP‑статус и тело ответа для каждой доставки. Это самый быстрый способ диагностировать сбои, не просматривая журналы сервера.
## Полный справочник конфигурации

```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"         # bind address (default: 0.0.0.0)
      port: 8644               # listen port (default: 8644)
      secret: ""               # optional global fallback secret
      rate_limit: 30           # requests per minute per route
      max_body_bytes: 1048576  # payload size limit in bytes (default: 1 MB)

      routes:
        <route-name>:
          secret: "required-per-route"
          events: []            # [] = accept all; otherwise list X-GitHub-Event values
          prompt: ""            # {field} / {nested.field} resolved from payload
          skills: []            # first matching skill is loaded (only one)
          deliver: "log"        # log | github_comment | telegram | discord | slack | signal | sms
          deliver_extra: {}     # repo + pr_number for github_comment; chat_id for others
```

---
## Что дальше?

- **[Обзор PR на основе Cron](/github-pr-review-agent.md)** — опрос PR по расписанию, без необходимости публичного эндпоинта
- **[Справочник по вебхукам](/user-guide/messaging/webhooks)** — полная справка по конфигурации платформы вебхуков
- **[Создать плагин](/guides/build-a-hermes-plugin)** — упаковать логику обзора в совместно используемый плагин
- **[Профили](/user-guide/profiles)** — запуск отдельного профиля ревьюера со своей памятью и конфигурацией