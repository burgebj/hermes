---
title: "Подписки на вебхуки — Подписки на вебхуки: запуск агента, управляемый событиями"
sidebar_label: "Webhook Subscriptions"
description: "Подписки на вебхуки: запуски событийного агента"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Подписки на вебхуки

Подписки на вебхуки: запуск агента по событию.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/devops/webhook-subscriptions` |
| Version | `1.1.0` |
| Platforms | linux, macos, windows |
| Tags | `webhook`, `events`, `automation`, `integrations`, `notifications`, `push` |

## Ссылка: полный SKILL.md

:::info
Ниже полное определение навыка, которое Hermes загружает, когда навык активирован. Это то, что агент видит как инструкции при работе навыка.
:::

# Подписки на вебхуки

Создай динамические подписки на вебхуки, чтобы внешние сервисы (GitHub, GitLab, Stripe, CI/CD, IoT‑датчики, инструменты мониторинга) могли запускать Hermes‑агент, отправляя POST‑запросы событий на URL.

## Настройка (обязательно сначала)

Платформа вебхуков должна быть включена, прежде чем можно создать подписки. Проверь:
```bash
hermes webhook list
```

Если выводит «Webhook platform is not enabled», настрой её:

### Вариант 1: Мастер настройки
```bash
hermes gateway setup
```
Следуй подсказкам, чтобы включить вебхуки, задать порт и глобальный HMAC‑секрет.

### Вариант 2: Ручная конфигурация
Добавь в `~/.hermes/config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "generate-a-strong-secret-here"
```

### Вариант 3: Переменные окружения
Добавь в `~/.hermes/.env`:
```bash
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8644
WEBHOOK_SECRET=generate-a-strong-secret-here
```

После конфигурации запусти (или перезапусти) шлюз:
```bash
hermes gateway run
# Or if using systemd:
systemctl --user restart hermes-gateway
```

Проверь, что он работает:
```bash
curl http://localhost:8644/health
```

## Команды

Всё управление происходит через CLI‑команду `hermes webhook`:

### Создать подписку
```bash
hermes webhook subscribe <name> \
  --prompt "Prompt template with {payload.fields}" \
  --events "event1,event2" \
  --description "What this does" \
  --skills "skill1,skill2" \
  --deliver telegram \
  --deliver-chat-id "12345" \
  --secret "optional-custom-secret"
```

Возвращает URL вебхука и HMAC‑секрет. Пользователь настраивает свой сервис на POST‑запросы по этому URL.

### Список подписок
```bash
hermes webhook list
```

### Удалить подписку
```bash
hermes webhook remove <name>
```

### Протестировать подписку
```bash
hermes webhook test <name>
hermes webhook test <name> --payload '{"key": "value"}'
```

## Шаблоны подсказок

Подсказки поддерживают `{dot.notation}` для доступа к вложенным полям полезной нагрузки:

- `{issue.title}` — заголовок задачи GitHub
- `{pull_request.user.login}` — автор PR
- `{data.object.amount}` — сумма платежа Stripe
- `{sensor.temperature}` — показание IoT‑датчика

Если подсказка не указана, весь JSON‑payload будет помещён в подсказку агента.

## Распространённые шаблоны

### GitHub: новые задачи
```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New GitHub issue #{issue.number}: {issue.title}\n\nAction: {action}\nAuthor: {issue.user.login}\nBody:\n{issue.body}\n\nPlease triage this issue." \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

Затем в GitHub → Settings → Webhooks → Add webhook:
- Payload URL: возвращённый `webhook_url`
- Content type: `application/json`
- Secret: возвращённый `secret`
- Events: «Issues»

### GitHub: обзоры PR
```bash
hermes webhook subscribe github-prs \
  --events "pull_request" \
  --prompt "PR #{pull_request.number} {action}: {pull_request.title}\nBy: {pull_request.user.login}\nBranch: {pull_request.head.ref}\n\n{pull_request.body}" \
  --skills "github-code-review" \
  --deliver github_comment
```

### Stripe: события платежей
```bash
hermes webhook subscribe stripe-payments \
  --events "payment_intent.succeeded,payment_intent.payment_failed" \
  --prompt "Payment {data.object.status}: {data.object.amount} cents from {data.object.receipt_email}" \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

### CI/CD: уведомления о сборках
```bash
hermes webhook subscribe ci-builds \
  --events "pipeline" \
  --prompt "Build {object_attributes.status} on {project.name} branch {object_attributes.ref}\nCommit: {commit.message}" \
  --deliver discord \
  --deliver-chat-id "1234567890"
```

### Универсальное оповещение мониторинга
```bash
hermes webhook subscribe alerts \
  --prompt "Alert: {alert.name}\nSeverity: {alert.severity}\nMessage: {alert.message}\n\nPlease investigate and suggest remediation." \
  --deliver origin
```

### Прямая доставка (без агента, нулевые затраты LLM)

Для сценариев, когда нужно просто отправить уведомление в чат пользователя — без рассуждений, без цикла агента — добавь `--deliver-only`. Шаблон `--prompt` будет использован как буквальное тело сообщения и отправлен напрямую в целевой адаптер.

Используй это для:
- Push‑уведомлений внешних сервисов (Supabase/Firebase webhooks → Telegram)
- Оповещений мониторинга, которые должны передаваться дословно
- Межагентных пингов, когда один агент сообщает пользователю другого агента
- Любого вебхука, где круговорот LLM был бы пустой тратой

```bash
hermes webhook subscribe antenna-matches \
  --deliver telegram \
  --deliver-chat-id "123456789" \
  --deliver-only \
  --prompt "🎉 New match: {match.user_name} matched with you!" \
  --description "Antenna match notifications"
```

POST возвращает `200 OK` при успешной доставке, `502` при ошибке цели — чтобы upstream‑сервисы могли повторять запросы интеллектуально. HMAC‑аутентификация, ограничения скорости и идемпотентность остаются в силе.

Требуется `--deliver` с реальной целью (telegram, discord, slack, github_comment и т.п.) — `--deliver log` отклоняется, потому что лог‑только прямая доставка бессмысленна.

## Безопасность

- Каждая подписка получает автоматически сгенерированный HMAC‑SHA256 секрет (или укажи свой через `--secret`)
- Адаптер вебхуков проверяет подписи каждого входящего POST
- Статические маршруты из `config.yaml` нельзя перезаписать динамическими подписками
- Подписки сохраняются в `~/.hermes/webhook_subscriptions.json`

## Как это работает

1. `hermes webhook subscribe` записывает в `~/.hermes/webhook_subscriptions.json`
2. Адаптер вебхуков горячо перезагружает этот файл при каждом входящем запросе (по mtime, почти без накладных расходов)
3. Когда приходит POST, соответствующий маршруту, адаптер формирует подсказку и запускает агент
4. Ответ агента доставляется в настроенную цель (Telegram, Discord, GitHub comment и т.п.)

## Устранение неполадок

Если вебхуки не работают:

1. **Запущен ли шлюз?** Проверь `systemctl --user status hermes-gateway` или `ps aux | grep gateway`
2. **Слушает ли сервер вебхуков?** `curl http://localhost:8644/health` должен вернуть `{"status": "ok"}`
3. **Логи шлюза:** `grep webhook ~/.hermes/logs/gateway.log | tail -20`
4. **Несоответствие подписи?** Убедись, что секрет в твоём сервисе совпадает с тем, что выдал `hermes webhook list`. GitHub отправляет `X-Hub-Signature-256`, GitLab — `X-Gitlab-Token`.
5. **Firewall/NAT?** URL вебхука должен быть доступен из сервиса. Для локальной разработки используй туннель (ngrok, cloudflared).
6. **Неправильный тип события?** Убедись, что фильтр `--events` соответствует тому, что отправляет сервис. Проверь маршрут командой `hermes webhook test <name>`.