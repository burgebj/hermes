---
title: "Підписки на Webhook — Підписки на Webhook: запуск агента за подією"
sidebar_label: "Webhook Subscriptions"
description: "Підписки Webhook: запуск агентів, орієнтованих на події"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Підписки на вебхуки

Підписки на вебхуки: запуск агента за подією.

## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/devops/webhook-subscriptions` |
| Версія | `1.1.0` |
| Платформи | linux, macos, windows |
| Теги | `webhook`, `events`, `automation`, `integrations`, `notifications`, `push` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Підписки на вебхуки

Створюй динамічні підписки на вебхуки, щоб зовнішні сервіси (GitHub, GitLab, Stripe, CI/CD, IoT‑датчики, інструменти моніторингу) могли запускати виконання Hermes‑агента, надсилаючи POST‑запити з подіями на URL.

## Налаштування (спочатку обов’язково)

Платформу вебхуків потрібно ввімкнути, перш ніж можна створювати підписки. Перевір за допомогою:
```bash
hermes webhook list
```

Якщо виводиться «Webhook platform is not enabled», налаштуй її:

### Варіант 1: Майстер налаштування
```bash
hermes gateway setup
```
Слідуй підказкам, щоб увімкнути вебхуки, вказати порт і задати глобальний HMAC‑секрет.

### Варіант 2: Ручна конфігурація
Додай до `~/.hermes/config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "generate-a-strong-secret-here"
```

### Варіант 3: Змінні середовища
Додай до `~/.hermes/.env`:
```bash
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8644
WEBHOOK_SECRET=generate-a-strong-secret-here
```

Після конфігурації запусти (або перезапусти) gateway:
```bash
hermes gateway run
# Or if using systemd:
systemctl --user restart hermes-gateway
```

Перевір, що він працює:
```bash
curl http://localhost:8644/health
```

## Команди

Усе керування здійснюється через CLI‑команду `hermes webhook`:

### Створити підписку
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

Повертає URL вебхука та HMAC‑секрет. Користувач налаштовує свій сервіс надсилати POST‑запити за цим URL.

### Переглянути підписки
```bash
hermes webhook list
```

### Видалити підписку
```bash
hermes webhook remove <name>
```

### Протестувати підписку
```bash
hermes webhook test <name>
hermes webhook test <name> --payload '{"key": "value"}'
```

## Шаблони підказок

У підказках підтримується `{dot.notation}` для доступу до вкладених полів payload:

- `{issue.title}` — назва issue у GitHub
- `{pull_request.user.login}` — автор PR
- `{data.object.amount}` — сума платежу Stripe
- `{sensor.temperature}` — показання IoT‑датчика

Якщо підказка не вказана, повний JSON‑payload виводиться у підказку агента.

## Поширені шаблони

### GitHub: нові issue
```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New GitHub issue #{issue.number}: {issue.title}\n\nAction: {action}\nAuthor: {issue.user.login}\nBody:\n{issue.body}\n\nPlease triage this issue." \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

Потім у налаштуваннях репозиторію GitHub → Webhooks → Add webhook:
- Payload URL: повернутий `webhook_url`
- Content type: `application/json`
- Secret: повернутий `secret`
- Events: «Issues»

### GitHub: огляди PR
```bash
hermes webhook subscribe github-prs \
  --events "pull_request" \
  --prompt "PR #{pull_request.number} {action}: {pull_request.title}\nBy: {pull_request.user.login}\nBranch: {pull_request.head.ref}\n\n{pull_request.body}" \
  --skills "github-code-review" \
  --deliver github_comment
```

### Stripe: події платежів
```bash
hermes webhook subscribe stripe-payments \
  --events "payment_intent.succeeded,payment_intent.payment_failed" \
  --prompt "Payment {data.object.status}: {data.object.amount} cents from {data.object.receipt_email}" \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

### CI/CD: сповіщення про збірки
```bash
hermes webhook subscribe ci-builds \
  --events "pipeline" \
  --prompt "Build {object_attributes.status} on {project.name} branch {object_attributes.ref}\nCommit: {commit.message}" \
  --deliver discord \
  --deliver-chat-id "1234567890"
```

### Загальне сповіщення моніторингу
```bash
hermes webhook subscribe alerts \
  --prompt "Alert: {alert.name}\nSeverity: {alert.severity}\nMessage: {alert.message}\n\nPlease investigate and suggest remediation." \
  --deliver origin
```

### Пряме доставлення (без агента, нульова вартість LLM)

Для випадків, коли потрібно лише переслати сповіщення користувачу — без роздумів, без циклу агента — додай `--deliver-only`. Шаблон `--prompt` буде використаний як буквальний текст повідомлення і відправлений безпосередньо до цільового адаптера.

Використовуй це для:
- Сповіщень зовнішніх сервісів (Supabase/Firebase вебхуки → Telegram)
- Сповіщень моніторингу, які мають передаватися дослівно
- Пінгів між агентами, коли один агент інформує користувача іншого агента
- Будь‑якого вебхука, де круговий прохід LLM був би марним

```bash
hermes webhook subscribe antenna-matches \
  --deliver telegram \
  --deliver-chat-id "123456789" \
  --deliver-only \
  --prompt "🎉 New match: {match.user_name} matched with you!" \
  --description "Antenna match notifications"
```

POST повертає `200 OK` при успішному доставленні, `502` при помилці цілі — щоб зовнішні сервіси могли інтелектуально повторювати запит. HMAC‑автентифікація, обмеження швидкості та ідемпотентність залишаються в силі.

Потрібно `--deliver` з реальною ціллю (telegram, discord, slack, github_comment тощо) — `--deliver log` відхиляється, бо лог‑тільки пряме доставлення без сенсу.

## Безпека

- Кожна підписка отримує автоматично згенерований HMAC‑SHA256 секрет (або вкажи свій за допомогою `--secret`)
- Адаптер вебхука перевіряє підписи у кожному вхідному POST
- Статичні маршрути з `config.yaml` не можна перезаписати динамічними підписками
- Підписки зберігаються у `~/.hermes/webhook_subscriptions.json`

## Як це працює

1. `hermes webhook subscribe` записує у `~/.hermes/webhook_subscriptions.json`
2. Адаптер вебхука гаряче перезавантажує цей файл при кожному вхідному запиті (з урахуванням mtime, практично без накладних витрат)
3. Коли надходить POST, що відповідає маршруту, адаптер формує підказку і запускає виконання агента
4. Відповідь агента доставляється до налаштованої цілі (Telegram, Discord, GitHub comment тощо)

## Усунення проблем

Якщо вебхуки не працюють:

1. **Чи запущений gateway?** Перевір за допомогою `systemctl --user status hermes-gateway` або `ps aux | grep gateway`
2. **Чи слухає сервер вебхука?** `curl http://localhost:8644/health` має повернути `{"status": "ok"}`
3. **Переглянь логи gateway:** `grep webhook ~/.hermes/logs/gateway.log | tail -20`
4. **Не збігаються підписи?** Переконайся, що секрет у твоєму сервісі співпадає з тим, що показує `hermes webhook list`. GitHub надсилає `X-Hub-Signature-256`, GitLab — `X-Gitlab-Token`.
5. **Firewall/NAT?** URL вебхука має бути доступним з сервісу. Для локальної розробки використай тунель (ngrok, cloudflared).
6. **Неправильний тип події?** Переконайся, що фільтр `--events` відповідає тому, що надсилає сервіс. Використай `hermes webhook test <name>` для перевірки маршруту.