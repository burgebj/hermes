---
sidebar_position: 13
title: "Вебхуки"
description: "Отримуй події від GitHub, GitLab та інших сервісів, щоб запускати Hermes Agent."
---

# Webhooks

Отримуй події від зовнішніх сервісів (GitHub, GitLab, JIRA, Stripe тощо) і автоматично запускай виконання Hermes agent. Адаптер веб‑хук запускає HTTP‑сервер, який приймає POST‑запити, перевіряє HMAC‑підписи, перетворює дані у промпти для агента та маршрутизує відповіді назад до джерела або до іншої налаштованої платформи.

Агент обробляє подію і може відповісти, розміщуючи коментарі у PR, надсилаючи повідомлення в Telegram/Discord або записуючи результат у журнал.
## Відео‑підручник

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
## Швидкий старт

1. Увімкни за допомогою `hermes gateway setup` або змінних середовища
2. Визнач маршрути у `config.yaml` **або** створюй їх динамічно за допомогою `hermes webhook subscribe`
3. Вкажи свій сервіс за адресою `http://your-server:8644/webhooks/<route-name>`

---
## Налаштування

Існує два способи ввімкнути адаптер веб‑хук.

### Через майстер налаштувань

```bash
hermes gateway setup
```

Слідуй підказкам, щоб ввімкнути веб‑хуки, встановити порт і задати глобальний HMAC‑секрет.

### Через змінні середовища

Додай до `~/.hermes/.env`:

```bash
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8644        # default
WEBHOOK_SECRET=your-global-secret
```

### Перевірка сервера

Коли шлюз працює:

```bash
curl http://localhost:8644/health
```

Очікувана відповідь:

```json
{"status": "ok", "platform": "webhook"}
```

---
## Налаштування маршрутів {#configuring-routes}

Маршрути визначають, як обробляються різні джерела webhook‑ів. Кожен маршрут — це іменований запис у `platforms.webhook.extra.routes` вашого `config.yaml`.

### Властивості маршруту

| Властивість | Обов’язково | Опис |
|------------|--------------|------|
| `events` | Ні | Список типів подій, які приймаються (наприклад `["pull_request"]`). Якщо порожньо, приймаються всі події. Тип події читається з `X‑GitHub‑Event`, `X‑GitLab‑Event` або `event_type` у payload. |
| `secret` | **Так** | HMAC‑секрет для перевірки підпису. Якщо не вказано в маршруті, використовується глобальний `secret`. Встанови `"INSECURE_NO_AUTH"` лише для тестування (пропускає валідацію). |
| `prompt` | Ні | Шаблонний рядок з доступом до payload через dot‑notation (наприклад `{pull_request.title}`). Якщо не вказано, весь JSON‑payload виводиться у prompt. |
| `skills` | Ні | Список назв skill, які треба завантажити для запуску агента. |
| `deliver` | Ні | Куди надсилати відповідь: `github_comment`, `telegram`, `discord`, `slack`, `signal`, `sms`, `whatsapp`, `matrix`, `mattermost`, `homeassistant`, `email`, `dingtalk`, `feishu`, `wecom`, `weixin`, `bluebubbles`, `qqbot` або `log` (за замовчуванням). |
| `deliver_extra` | Ні | Додаткова конфігурація доставки — ключі залежать від типу `deliver` (наприклад `repo`, `pr_number`, `chat_id`). Значення підтримують ті ж шаблони `{dot.notation}`, що й `prompt`. |
| `deliver_only` | Ні | Якщо `true`, агент повністю пропускається — сформований шаблоном `prompt` текст надсилається без виклику LLM. Нульова вартість LLM, доставка за субсекунду. Дивись [Direct Delivery Mode](#direct-delivery-mode) для прикладів використання. Потрібно, щоб `deliver` був реальним цільовим каналом (не `log`). |

### Повний приклад

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

### Шаблони prompt

Prompt‑и використовують dot‑notation для доступу до вкладених полів у payload webhook‑а:

- `{pull_request.title}` розв’язується в `payload["pull_request"]["title"]`
- `{repository.full_name}` розв’язується в `payload["repository"]["full_name"]`
- `{__raw__}` — спеціальний токен, який виводить **весь payload** у вигляді відформатованого JSON (скорочено до 4000 символів). Корисно для моніторингових алертів або загальних webhook‑ів, коли агент потребує повного контексту.
- Відсутні ключі залишаються як буквальний рядок `{key}` (без помилки)
- Вкладені словники та списки серіалізуються у JSON і скорочуються до 2000 символів

Можна комбінувати `{__raw__}` із звичайними змінними шаблону:

```yaml
prompt: "PR #{pull_request.number} by {pull_request.user.login}: {__raw__}"
```

Якщо для маршруту не налаштовано шаблон `prompt`, весь payload виводиться у вигляді відформатованого JSON (скорочено до 4000 символів).

Ті ж шаблони dot‑notation працюють у значеннях `deliver_extra`.

### Доставка у тему форуму

При доставці відповідей webhook‑а в Telegram можна вказати конкретну тему форуму, додавши `message_thread_id` (або `thread_id`) у `deliver_extra`:

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

Якщо `chat_id` не вказано в `deliver_extra`, доставка повертається до домашнього каналу, налаштованого для цільової платформи.
## Огляд PR на GitHub (крок за кроком) {#github-pr-review}

Цей посібник налаштовує автоматичний перегляд коду для кожного pull‑request.

### 1. Створи webhook у GitHub

1. Перейди до свого репозиторію → **Settings** → **Webhooks** → **Add webhook**
2. Встанови **Payload URL** на `http://your-server:8644/webhooks/github-pr`
3. Встанови **Content type** на `application/json`
4. Встанови **Secret**, щоб він відповідав конфігурації маршруту (наприклад, `github-webhook-secret`)
5. У розділі **Which events?** вибери **Let me select individual events** і познач **Pull requests**
6. Натисни **Add webhook**

### 2. Додай конфігурацію маршруту

Додай маршрут `github-pr` у файл `~/.hermes/config.yaml`, як показано у прикладі вище.

### 3. Переконайся, що CLI `gh` автентифіковано

Тип доставки `github_comment` використовує GitHub CLI для публікації коментарів:

```bash
gh auth login
```

### 4. Перевір

Відкрий pull‑request у репозиторії. Webhook спрацює, Hermes обробить подію та опублікує коментар‑огляд у PR.

---
## Налаштування Webhook у GitLab {#gitlab-webhook-setup}

GitLab webhook‑и працюють подібно, але використовують інший механізм автентифікації. GitLab надсилає секрет у вигляді простого заголовка `X‑Gitlab‑Token` (точний збіг рядка, без HMAC).

### 1. Створи webhook у GitLab

1. Перейди до свого проєкту → **Settings** → **Webhooks**
2. Вкажи **URL** `http://your-server:8644/webhooks/gitlab-mr`
3. Введи свій **Secret token**
4. Вибери **Merge request events** (та будь‑які інші події, які потрібні)
5. Натисни **Add webhook**

### 2. Додай конфігурацію маршруту

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
## Параметри доставки {#delivery-options}

Поле `deliver` визначає, куди надсилати відповідь агента після обробки події вебхука.

| Тип доставки | Опис |
|-------------|------|
| `log` | Записує відповідь у журнал виводу шлюзу. Це типово і корисно для тестування. |
| `github_comment` | Публікує відповідь як коментар до PR/issue за допомогою CLI `gh`. Потрібні `deliver_extra.repo` та `deliver_extra.pr_number`. CLI `gh` має бути встановлений і автентифікований на хості шлюзу (`gh auth login`). |
| `telegram` | Надсилає відповідь у Telegram. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `discord` | Надсилає відповідь у Discord. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `slack` | Надсилає відповідь у Slack. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `signal` | Надсилає відповідь у Signal. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `sms` | Надсилає відповідь у SMS через Twilio. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `whatsapp` | Надсилає відповідь у WhatsApp. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `matrix` | Надсилає відповідь у Matrix. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `mattermost` | Надсилає відповідь у Mattermost. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `homeassistant` | Надсилає відповідь у Home Assistant. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `email` | Надсилає відповідь у Email. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `dingtalk` | Надсилає відповідь у DingTalk. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `feishu` | Надсилає відповідь у Feishu/Lark. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `wecom` | Надсилає відповідь у WeCom. Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `weixin` | Надсилає відповідь у Weixin (WeChat). Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |
| `bluebubbles` | Надсилає відповідь у BlueBubbles (iMessage). Використовує домашній канал або вказує `chat_id` у `deliver_extra`. |

Для крос‑платформенної доставки цільова платформа також має бути увімкнена та підключена у шлюзі. Якщо `chat_id` не вказано у `deliver_extra`, відповідь надсилається у налаштований домашній канал цієї платформи.
## Режим прямої доставки {#direct-delivery-mode}

За замовчуванням кожен POST‑запит вебхука запускає виконання агента — дані стають підказкою, агент їх обробляє, і відповідь агента доставляється. Це витрачає токени LLM на кожну подію.

Для випадків, коли потрібно **надіслати просте сповіщення** — без роздумів, без циклу агента, просто доставити повідомлення — встанови `deliver_only: true` у маршруті. Відрендерений шаблон `prompt` стає буквальним тілом повідомлення, а адаптер відправляє його безпосередньо до налаштованого цільового пункту доставки.

### Коли використовувати пряму доставку

- **Надсилання зовнішньому сервісу** — вебхук Supabase/Firebase спрацьовує при зміні бази даних → миттєво повідомити користувача в Telegram
- **Сповіщення моніторингу** — вебхук сповіщення Datadog/Grafana → надсилання в канал Discord
- **Пінги між агентами** — агент A повідомляє користувача агента B, що довготривала задача завершилась
- **Завершення фонового завдання** — Cron‑задача завершилась → опублікувати результат у Slack

**Переваги**

- **Нуль токенів LLM** — агент ніколи не викликається
- **Доставка за субсекунду** — один виклик адаптера, без циклу роздумів
- **Така ж безпека, як у режимі агента** — HMAC‑автентифікація, обмеження швидкості, ідемпотентність і обмеження розміру тіла залишаються діючими
- **Синхронна відповідь** — POST повертає `200 OK`, коли доставка успішна, або `502`, якщо ціль відхилила запит, тож твій upstream‑сервіс може інтелектуально повторювати спроби

### Приклад: надсилання в Telegram з Supabase

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

Твоя edge‑функція Supabase підписує дані HMAC‑SHA256 і надсилає POST‑запит на `https://your-server:8644/webhooks/antenna-matches`. Адаптер вебхука перевіряє підпис, рендерить шаблон з даних, доставляє в Telegram і повертає `200 OK`.

### Приклад: динамічна підписка через CLI

```bash
hermes webhook subscribe antenna-matches \
  --deliver telegram \
  --deliver-chat-id "123456789" \
  --deliver-only \
  --prompt "🎉 New match: {match.user_name} matched with you!" \
  --description "Antenna match notifications"
```

### Коди відповідей

| Статус | Значення |
|--------|----------|
| `200 OK` | Успішно доставлено. Тіло: `{"status": "delivered", "route": "...", "target": "...", "delivery_id": "..."}` |
| `200 OK` (status=duplicate) | Дублікат ID `X‑GitHub‑Delivery` протягом TTL ідемпотентності (1 година). Не повторно доставлено. |
| `401 Unauthorized` | Неправильний або відсутній HMAC‑підпис. |
| `400 Bad Request` | Некоректне JSON‑тіло. |
| `404 Not Found` | Невідоме ім’я маршруту. |
| `413 Payload Too Large` | Тіло перевищило `max_body_bytes`. |
| `429 Too Many Requests` | Перевищено ліміт швидкості маршруту. |
| `502 Bad Gateway` | Адаптер‑ціль відхилив повідомлення або згенерував помилку. Помилка логуються на сервері; тіло відповіді — загальне `Delivery failed`, щоб не розкривати внутрішні деталі адаптера. |

### Підводні камені конфігурації

- `deliver_only: true` вимагає, щоб `deliver` був реальним цільовим пунктом. `deliver: log` (або відсутність `deliver`) відхиляється під час запуску — адаптер не стартує, якщо знайде неправильно налаштований маршрут.
- Поле `skills` ігнорується в режимі прямої доставки (не запускаються агенти, отже немає чого інжектити).
- Рендеринг шаблону використовує той самий синтаксис `{dot.notation}`, що й у режимі агента, включаючи токен `{__raw__}`.
- Ідемпотентність працює з тими ж заголовками `X‑GitHub‑Delivery` / `X‑Request‑ID` — повторні запити з тим самим ID повертають `status=duplicate` і НЕ повторно доставляються.
## Динамічні підписки (CLI) {#dynamic-subscriptions}

На додачу до статичних маршрутів у `config.yaml` ти можеш створювати підписки на вебхуки динамічно за допомогою команди CLI `hermes webhook`. Це особливо корисно, коли самому агенту потрібно налаштувати тригер‑події.

### Створити підписку

```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New issue #{issue.number}: {issue.title}\nBy: {issue.user.login}\n\n{issue.body}" \
  --deliver telegram \
  --deliver-chat-id "-100123456789" \
  --description "Triage new GitHub issues"
```

Це повертає URL вебхука та автоматично згенерований HMAC‑секрет. Налаштуй свій сервіс надсилати POST‑запит на цей URL.

### Переглянути підписки

```bash
hermes webhook list
```

### Видалити підписку

```bash
hermes webhook remove github-issues
```

### Протестувати підписку

```bash
hermes webhook test github-issues
hermes webhook test github-issues --payload '{"issue": {"number": 42, "title": "Test"}}'
```

### Як працюють динамічні підписки

- Підписки зберігаються у `~/.hermes/webhook_subscriptions.json`
- Адаптер вебхука автоматично перезавантажує цей файл при кожному вхідному запиті (з урахуванням часу зміни, практично без накладних витрат)
- Статичні маршрути з `config.yaml` завжди мають пріоритет над динамічними з однаковою назвою
- Динамічні підписки використовують той самий формат маршруту та можливості, що й статичні (події, шаблони запитів, інструменти, доставка)
- Перезапуск шлюзу не потрібен — підписка одразу активна

### Підписки, ініційовані агентом

Агент може створювати підписки через термінальний інструмент, коли його направляє навичка `webhook-subscriptions`. Попроси агента «налаштувати вебхук для GitHub issues», і він виконає відповідну команду `hermes webhook subscribe`.
## Security {#security}

Адаптер вебхуків включає кілька рівнів безпеки:

### HMAC signature validation

Адаптер перевіряє підписи вхідних вебхуків, використовуючи відповідний метод для кожного джерела:

- **GitHub**: заголовок `X-Hub-Signature-256` — HMAC‑SHA256 hex‑digest з префіксом `sha256=`
- **GitLab**: заголовок `X-Gitlab-Token` — просте порівняння секретного рядка
- **Generic**: заголовок `X-Webhook-Signature` — необроблений HMAC‑SHA256 hex‑digest

Якщо секрет налаштовано, але не виявлено розпізнаного заголовка підпису, запит відхиляється.

### Secret is required

Кожен маршрут повинен мати секрет — або встановлений безпосередньо на маршруті, або успадкований від глобального `secret`. Маршрути без секрету змушують адаптер завершити запуск з помилкою. Для розробки/тестування можна встановити секрет у значення `"INSECURE_NO_AUTH"`, щоб повністю пропустити валідацію.

`INSECURE_NO_AUTH` приймається лише коли **gateway** прив’язаний до loopback‑host (`127.0.0.1`, `localhost`, `::1`). Якщо його поєднати з небезпечною прив’язкою, наприклад `0.0.0.0` або LAN‑IP, адаптер відмовиться запуститися — це запобігає випадковому відкриттю неавтентифікованого кінцевого пункту на публічному інтерфейсі.

### Rate limiting

Кожен маршрут за замовчуванням обмежений **30 запитами за хвилину** (fixed‑window). Налаштуй це глобально:

```yaml
platforms:
  webhook:
    extra:
      rate_limit: 60  # requests per minute
```

Запити, що перевищують ліміт, отримують відповідь `429 Too Many Requests`.

### Idempotency

Ідентифікатори доставки (з `X-GitHub-Delivery`, `X-Request-ID` або запасний варіант з мітки часу) кешуються **1 годину**. Дублікати доставок (наприклад, повторні спроби вебхука) тихо пропускаються з відповіддю `200`, запобігаючи дублюванню запусків агента.

### Body size limits

Навантаження, що перевищують **1 MB**, відхиляються ще до читання тіла. Налаштуй це:

```yaml
platforms:
  webhook:
    extra:
      max_body_bytes: 2097152  # 2 MB
```

### Prompt injection risk

:::warning
Навантаження вебхука містять дані, контрольовані атакувальником — назви PR, повідомлення комітів, описи задач тощо можуть містити шкідливі інструкції. Запускай **gateway** у пісочничому середовищі (Docker, VM), коли він доступний в інтернеті. Розглянь використання бекенду Docker або SSH‑терміналу для ізоляції.
:::
## Усунення проблем {#troubleshooting}

### Webhook не надходить

- Перевір, чи порт відкритий і доступний з джерела webhook
- Перевір правила брандмауера — порт `8644` (або твій налаштований порт) має бути відкритим
- Переконайся, що шлях URL збігається: `http://your-server:8644/webhooks/<route-name>`
- Використай кінцеву точку `/health`, щоб підтвердити, що сервер працює

### Помилка перевірки підпису

- Переконайся, що секрет у конфігурації маршруту точно збігається з секретом, налаштованим у джерелі webhook
- Для GitHub секрет базується на HMAC — перевір `X-Hub-Signature-256`
- Для GitLab секрет — простий токен — перевір `X-Gitlab-Token`
- Переглянь логи шлюзу на предмет попереджень `Invalid signature`

### Подія ігнорується

- Перевір, чи тип події присутній у списку `events` твого маршруту
- Події GitHub мають значення типу `pull_request`, `push`, `issues` (значення заголовка `X-GitHub-Event`)
- Події GitLab мають значення типу `merge_request`, `push` (значення заголовка `X-GitLab-Event`)
- Якщо `events` порожній або не встановлений, приймаються всі події

### Агент не відповідає

- Запусти шлюз у передньому плані, щоб бачити логи: `hermes gateway run`
- Переконайся, що шаблон підказки рендериться правильно
- Перевір, чи ціль доставки налаштована і підключена

### Дублювання відповідей

- Кеш ідемпотентності має запобігати цьому — перевір, чи джерело webhook надсилає заголовок ідентифікатора доставки (`X-GitHub-Delivery` або `X-Request-ID`)
- Ідентифікатори доставки кешуються протягом 1 години

### Помилки `gh` CLI (доставка коментаря GitHub)

- Запусти `gh auth login` на хості шлюзу
- Переконайся, що автентифікований користувач GitHub має права запису в репозиторій
- Перевір, чи `gh` встановлений і присутній у `PATH`

---
## Змінні середовища {#environment-variables}

| Змінна | Опис | За замовчуванням |
|----------|-------------|---------|
| `WEBHOOK_ENABLED` | Увімкнути адаптер платформи webhook | `false` |
| `WEBHOOK_PORT` | Порт HTTP‑сервера для отримання webhook‑ів | `8644` |
| `WEBHOOK_SECRET` | Глобальний HMAC‑секрет (використовується як запасний (варіант), коли маршрути не вказують власний) | _(none)_ |