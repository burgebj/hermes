---
title: "конвеєр зустрічей Teams"
sidebar_label: "Teams Meeting Pipeline"
description: "Керуй конвеєром підсумку зустрічей Teams через Hermes CLI — підсумовуй зустрічі, перевіряй статус конвеєра, відтворюй завдання, керуй підписками Microsoft Graph"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Конвеєр підсумків зустрічей Teams

Керуйте конвеєром підсумків зустрічей Teams за допомогою Hermes CLI — підсумовуйте зустрічі, перевіряйте статус конвеєра, відтворюйте завдання, керуйте підписками Microsoft Graph.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/teams-meeting-pipeline` |
| Version | `1.1.0` |
| Author | Hermes Agent + Teknium |
| License | MIT |
| Tags | `Teams`, `Microsoft Graph`, `Meetings`, `Productivity`, `Operations` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# Конвеєр підсумків зустрічей Teams

Використовуй цю навичку, коли користувач запитує про підсумки зустрічей Microsoft Teams, транскрипти, записи, дії, підписки Graph або будь‑яке операційне питання щодо конвеєра зустрічей Teams. Працює будь‑якою мовою — наведені тригери лише приклади, а не вичерпний список.

Все, що стосується оператора, — це підкоманда `hermes teams-pipeline`, що запускається в терміналі. Нових інструментів моделі для цього конвеєра немає — CLI є інтерфейсом.

## Коли використовувати цю навичку

Користувач просить:
- підсумувати зустріч Teams / виділити дії / отримати нотатки зустрічі
- перевірити статус конвеєра, переглянути збережене завдання зустрічі або подивитися останні зустрічі
- відтворити / повторно запустити збережене завдання, яке не вдалося або потребує нового підсумку
- перевірити налаштування Microsoft Graph після зміни середовища або конфігурації
- усунути проблему «підсумок зустрічі не надійшов» або «нові зустрічі не інжектуються»
- керувати підписками вебхуків Graph (створити, оновити, видалити, переглянути)
- налаштувати автоматичне оновлення підписок (див. підводний камінь нижче)

Багатомовні приклади тригерів (не вичерпний список):
- English: “summarize the Teams meeting”, “pipeline status”, “replay job X”
- Turkish: “Teams meeting özetle”, “action item çıkar”, “toplantı notu”, “pipeline durumu”, “replay job”

## Передумови

Перед використанням конвеєра переконайся, що в `~/.hermes/.env` встановлені такі змінні:

```bash
MSGRAPH_TENANT_ID=...
MSGRAPH_CLIENT_ID=...
MSGRAPH_CLIENT_SECRET=...
```

Якщо чогось не вистачає, направ користувача до посібника з реєстрації Azure‑додатку за адресою `/docs/guides/microsoft-graph-app-registration` — потрібна реєстрація Azure AD‑додатку з дозволами Graph, затвердженими адміністратором, перш ніж конвеєр почне працювати.

## Довідка по командах

### Статус і інспекція (почни тут)

```bash
hermes teams-pipeline validate              # config snapshot — run first after any change
hermes teams-pipeline token-health          # Graph token status
hermes teams-pipeline token-health --force-refresh   # force a fresh token acquisition
hermes teams-pipeline list                  # recent meeting jobs
hermes teams-pipeline list --status failed  # only failed jobs
hermes teams-pipeline show <job-id>         # full detail of one job
hermes teams-pipeline subscriptions         # current Graph webhook subscriptions
```

### Повторний запуск / налагодження

```bash
hermes teams-pipeline run <job-id>          # replay a stored job (re-summarize, re-deliver)
hermes teams-pipeline fetch --meeting-id <id>   # dry-run: resolve meeting + transcript without persisting
hermes teams-pipeline fetch --join-web-url "<url>"   # dry-run by join URL
```

### Керування підписками

```bash
hermes teams-pipeline subscribe \
  --resource communications/onlineMeetings/getAllTranscripts \
  --notification-url https://<your-public-host>/msgraph/webhook \
  --client-state "$MSGRAPH_WEBHOOK_CLIENT_STATE"

hermes teams-pipeline renew-subscription <sub-id> --expiration <iso-8601>
hermes teams-pipeline delete-subscription <sub-id>
hermes teams-pipeline maintain-subscriptions            # renew near-expiry ones
hermes teams-pipeline maintain-subscriptions --dry-run  # show what would be renewed
```

## Дерево рішень для типових запитів

- Користувач запитує «чому я не отримав підсумок сьогоднішньої зустрічі?» → почни з `list --status failed`, потім `show <job-id>` для відповідного рядка. Якщо завдання взагалі відсутнє, перевір `subscriptions` — можливо, вебхук прострочився (див. підводний камінь нижче).
- Користувач запитує «чи працює налаштування?» → `validate`, потім `token-health`, потім `subscriptions`. Якщо всі три проходять, запроси тестову зустріч і перевір `list` на наявність нового рядка.
- Користувач запитує «перезапустити підсумок для зустрічі X» → `list`, щоб знайти ID завдання, `run <job-id>` для відтворення. Якщо знову не вдається, `show <job-id>` для перегляду помилки і `fetch --meeting-id` для сухого запуску розв’язання артефакту.
- Користувач запитує «додати зустріч X до конвеєра» → зазвичай не треба — конвеєр працює за підписками, а не за окремими зустрічами. Якщо потрібен підсумок конкретної минулої зустрічі, використай `fetch` для отримання транскрипту + `run` після створення завдання.

## Критичний підводний камінь: підписки Graph закінчуються через 72 години

Microsoft Graph обмежує термін дії підписок вебхуків 72 годинами і **не оновлює їх автоматично**. Якщо `maintain-subscriptions` не заплановано, сповіщення про зустрічі тихо припиняються через 3 дні після будь‑якого ручного створення підписки.

Коли користувач повідомляє «вчора конвеєр працював, а сьогодні нічого не надходить»:
1. Запусти `hermes teams-pipeline subscriptions` — якщо список порожній або всі записи мають `expirationDateTime` у минулому, це причина.
2. Створи заново за допомогою `subscribe`, як показано вище.
3. **Негайно налаштуй автоматичне оновлення** через `hermes cron add`, systemd‑таймер або простий crontab. Операційний посібник за адресою `/docs/guides/operate-teams-meeting-pipeline#automating-subscription-renewal-required-for-production` містить усі три варіанти. Інтервал у 12 годин безпечний (6‑х кратний запас проти 72‑годинного ліміту).

## Інші підводні камені

- **Транскрипт ще недоступний.** Teams потребує деякого часу після завершення зустрічі, щоб згенерувати артефакт транскрипту. `fetch --meeting-id` для щойно завершеної зустрічі може повернути порожнє. Зачекай 2‑5 хвилин і спробуй ще раз, або дай вебхуку Graph сам інжектувати дані.
- **Невідповідність режиму доставки.** Якщо підсумки створені (`list` показує успіх), але нічого не з’являється в Teams, перевір `platforms.teams.extra.delivery_mode` та відповідну конфігурацію цілі (`incoming_webhook_url` АБО `chat_id` АБО `team_id`+`channel_id`). Записувач читає їх з `config.yaml` або змінних середовища `TEAMS_*`.
- **Дозволи додатку Graph.** Токен успішно отримано (`token-health` проходить), але виклики API Graph повертають 401/403, коли дозволи були додані, а згода адміністратора не була повторно надана. Попроси користувача зайти в реєстрацію додатку в Azure‑порталі та знову натиснути «Grant admin consent».

## Пов’язані документи

Напрям користувача до цих ресурсів, коли потрібна більш детальна інформація, ніж охоплює ця навичка:
- Посібник з реєстрації Azure‑додатку: `/docs/guides/microsoft-graph-app-registration`
- Повне налаштування конвеєра: `/docs/user-guide/messaging/teams-meetings`
- Операційний посібник (автоматизація оновлення, усунення проблем, чек‑лист запуску): `/docs/guides/operate-teams-meeting-pipeline`
- Налаштування прослуховувача вебхуків: `/docs/user-guide/messaging/msgraph-webhook`