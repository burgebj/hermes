---
sidebar_position: 23
title: "Microsoft Graph Webhook слухач"
description: "Отримуй повідомлення про зміни Microsoft Graph (зустрічі, календар, чат тощо) у Hermes"
---

# Microsoft Graph Webhook Listener

Платформа шлюзу `msgraph_webhook` — це вхідний прослуховувач подій. Вона дозволяє Hermes отримувати **сповіщення про зміни** від Microsoft Graph — «завершено зустріч у Teams», «у цьому чаті з’явилося нове повідомлення», «оновлено подію календаря». На відміну від платформи `teams` (яка є чат‑ботом, до якого користувачі пишуть) — цей шлюз працює так, що M365 повідомляє Hermes про те, що сталося, а не людина.

Наразі основним споживачем є конвеєр підсумків зустрічей Teams: Graph надсилає сповіщення, коли зустріч створює транскрипт, конвеєр отримує його, і Hermes публікує підсумок у Teams. Інші ресурси Graph (`/chats/.../messages`, `/users/.../events`) використовують той самий прослуховувач — споживачі конвеєра додаються у власних PR.

## Вимоги

- Облікові дані застосунку Microsoft Graph — [Register a Microsoft Graph Application](/guides/microsoft-graph-app-registration)
- **Публічний HTTPS‑URL**, до якого може дістатися Microsoft Graph (Graph не викликає приватні кінцеві точки). Для тестування підходить dev‑тунель; у продакшн потрібен реальний домен з дійсним сертифікатом.
- Сильний спільний секрет, який використовується як значення `clientState`. Згенеруй його за допомогою `openssl rand -hex 32` і помісти у `~/.hermes/.env` як `MSGRAPH_WEBHOOK_CLIENT_STATE`.

## Швидкий старт

Мінімальний `~/.hermes/config.yaml`:

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

Або через змінні середовища у `~/.hermes/.env` (автоматично злиті під час запуску):

```bash
MSGRAPH_WEBHOOK_ENABLED=true
MSGRAPH_WEBHOOK_PORT=8646
MSGRAPH_WEBHOOK_CLIENT_STATE=<generate-with-openssl-rand-hex-32>
MSGRAPH_WEBHOOK_ACCEPTED_RESOURCES=communications/onlineMeetings
```

Примітка: хост прив’язки читається з `extra.host` у `config.yaml` (див. приклад вище); змінна середовища `MSGRAPH_WEBHOOK_HOST` не переважає.

Запусти шлюз: `hermes gateway run`. Прослуховувач відкриває:

- `POST /msgraph/webhook` — сповіщення про зміни від Graph
- `GET /msgraph/webhook?validationToken=...` — handshake валідації підписки Graph
- `GET /health` — проба готовності з лічильниками прийнятих/дубльованих запитів

Опублікуй прослуховувач (reverse proxy, dev‑тунель, ingress). Твій URL сповіщень для підписок Graph — це твій публічний HTTPS‑origin, доповнений `/msgraph/webhook`:

```
https://ops.example.com/msgraph/webhook
```

## Налаштування

Усі параметри розташовані під `platforms.msgraph_webhook.extra`:

| Параметр | Типово | Опис |
|---------|--------|------|
| `host` | `0.0.0.0` | Адреса прив’язки HTTP‑прослуховувача. Для не‑loopback прив’язок потрібен `allowed_source_cidrs`; прив’язка до loopback (`127.0.0.1` / `::1`) — найпростіший варіант для dev‑тунелю / reverse‑proxy. |
| `port` | `8646` | Порт прив’язки. |
| `webhook_path` | `/msgraph/webhook` | URL‑шлях, куди Graph надсилає POST. |
| `health_path` | `/health` | Точка готовності. |
| `client_state` | — | Спільний секрет, який Graph повертає в кожному сповіщенні. Порівнюється за допомогою `hmac.compare_digest` — згенеруй його `openssl rand -hex 32`. |
| `accepted_resources` | `[]` (accept all) | Білий список шляхів/шаблонів ресурсів Graph. Термінатор `*` працює як префіксний збіг. Початковий `/` допускається. Приклад: `["communications/onlineMeetings", "chats/*/messages"]`. |
| `max_seen_receipts` | `5000` | Розмір кешу дедуплікації ID сповіщень. Найстаріші записи видаляються при досягненні ліміту. |
| `allowed_source_cidrs` | `[]` | Обов’язково для не‑loopback прив’язок. Залишай порожнім лише коли прослуховувач прив’язений до loopback і передбачений локальним тунелем / reverse‑proxy. |

Кожен параметр має відповідну змінну середовища (`MSGRAPH_WEBHOOK_*`), яка зливається у конфіг під час старту шлюзу — див. [environment variables reference](/reference/environment-variables#microsoft-graph-teams-meetings).

## Посилення безпеки

### clientState — основна перевірка автентифікації

Кожне сповіщення Graph містить рядок `clientState`, який був вказаний під час реєстрації підписки. Прослуховувач відхиляє будь‑яке сповіщення, у якого `clientState` не збігається, використовуючи таймінгово‑безпечне порівняння. Це задокументований Microsoft механізм — розглядай це значення як сильний спільний секрет.

Якщо `client_state` не задано, прослуховувач відмовиться запускатися.

### Source‑IP allowlisting (продакшн)

Для продакшн‑середовища обмеж прослуховувач IP‑діапазонами webhook‑джерел Microsoft Graph. Microsoft публікує ці діапазони у [Office 365 IP Address and URL Web service](https://learn.microsoft.com/en-us/microsoft-365/enterprise/urls-and-ip-address-ranges). Налаштуй їх так:

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

Або як змінну середовища:

```bash
MSGRAPH_WEBHOOK_ALLOWED_SOURCE_CIDRS="52.96.0.0/14,52.104.0.0/14"
```

Прив’язка не‑loopback хоста, наприклад `0.0.0.0`, `::` або LAN‑IP без `allowed_source_cidrs`, відхиляється під час старту. Якщо ти користуєшся dev‑тунелем або reverse‑proxy на тій же машині, прив’яжи Hermes до `127.0.0.1` або `::1` і залиш список дозволених порожнім. Неправильні CIDR‑рядки логуються як попередження і ігноруються. **Переглядай список IP Microsoft щоквартально** — він змінюється.

### HTTPS termination

Прослуховувач працює по простому HTTP. TLS‑термінація здійснюється на твоєму reverse‑proxy (Caddy, Nginx, Cloudflare Tunnel, AWS ALB) і проксірує запити до прослуховувача по локальній мережі. Graph відмовляється доставляти дані на не‑HTTPS кінцеві точки, тому шлях для незашифрованого трафіку до тебе від Graph не існує.

### Response hygiene

При успішному обробленні прослуховувач повертає `202 Accepted` з порожнім тілом — внутрішні лічильники не потрапляють у відповідь. Оператори можуть спостерігати лічильники через `/health`, який захищений тими ж правилами Source‑IP, що й шлях webhook.

Таблиця статус‑кодів:

| Результат | Статус |
|-----------|--------|
| Сповіщення прийнято або дедупліковано | 202 |
| Handshake валідації (GET з `validationToken`) | 200 (повертає токен) |
| Усі елементи в батчі не пройшли clientState | 403 |
| Некоректний JSON / відсутній масив `value` / невідомий ресурс | 400 |
| IP‑адреса не у білому списку | 403 |
| GET без `validationToken` | 400 |

## Устранення проблем

| Проблема | Що перевіряти |
|----------|----------------|
| Валідація підписки Graph не проходить | Публічний URL доступний, шлях `/msgraph/webhook` збігається, GET з `validationToken` повертає токен як `text/plain` протягом 10 секунд. |
| POST‑запити надходять, але нічого не обробляється | `client_state` збігається з тим, що вказано при реєстрації підписки. Перезапусти `openssl rand -hex 32` і створи нову підписку, якщо значення змінилося. Перевір, чи `accepted_resources` включає шлях, який надсилає Graph. |
| Усі сповіщення повертають 403 | Невідповідність `clientState` (підробка або інша підписка). Створи підписку заново за допомогою `hermes teams-pipeline subscribe --client-state "$MSGRAPH_WEBHOOK_CLIENT_STATE" ...` (поставляється з runtime конвеєра). |
| Прослуховувач відмовляє запуск на `0.0.0.0` | Вкажи `allowed_source_cidrs` з актуальними діапазонами webhook Microsoft, або прив’яжи Hermes до `127.0.0.1` / `::1` за тунелем або reverse‑proxy. |
| Прослуховувач стартує, а `curl http://localhost:8646/health` зависає | Конфлікт прив’язки порту. Перевір `ss -tlnp \| grep 8646` і, за потреби, зміни `port:`. |
| Реальні запити Graph отримують 403 | Білий список IP занадто вузький. Розшир список, включивши актуальні діапазони egress Microsoft. Якщо ти ще тестуєш тунель, прив’яжи Hermes до loopback і дозволь тунелю займати публічну експозицію. |

## Пов’язані документи

- [Register a Microsoft Graph Application](/guides/microsoft-graph-app-registration) — передумова реєстрації Azure‑застосунку
- [Environment Variables → Microsoft Graph](/reference/environment-variables#microsoft-graph-teams-meetings) — повний список змінних середовища
- [Microsoft Teams bot setup](/user-guide/messaging/teams) — інша платформа, що дозволяє користувачам спілкуватися з Hermes у Teams