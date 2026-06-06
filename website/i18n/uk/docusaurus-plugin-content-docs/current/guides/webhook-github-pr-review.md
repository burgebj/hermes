---
sidebar_position: 11
sidebar_label: "GitHub PR Reviews via Webhook"
title: "Автоматичні коментарі PR у GitHub за допомогою Webhooks"
description: "Підключи Hermes до GitHub, щоб він автоматично отримував diff‑и PR, переглядав зміни коду та публікував коментарі — за тригером вебхуків без ручного запуску."
---

# Автоматичні коментарі до GitHub PR за допомогою Webhooks

Цей посібник проведе тебе через підключення Hermes Agent до GitHub, щоб він автоматично отримував diff запиту на злиття, аналізував зміни коду та публікував коментар — ініційований подією webhook без ручного втручання.

Коли PR відкривається або оновлюється, GitHub надсилає webhook POST до твого екземпляра Hermes. Hermes запускає агента з підказкою, яка інструктує його отримати diff за допомогою `gh` CLI, а відповідь публікується у гілці PR.

:::tip Хочеш простіше налаштування без публічної кінцевої точки?
Якщо у тебе немає публічної URL‑адреси або ти просто хочеш швидко розпочати, ознайомся з [Build a GitHub PR Review Agent](./github-pr-review-agent.md) — використовує cron‑задачі для опитування PR за розкладом, працює за NAT та міжфайрволами.
:::

:::info Довідка
Для повного довідника платформи webhook (усі параметри конфігурації, типи доставки, динамічні підписки, модель безпеки) дивись [Webhooks](/user-guide/messaging/webhooks).
:::

:::warning Ризик ін’єкції підказки
Payload webhook‑ів містить дані, контрольовані атакувальником — назви PR, повідомлення комітів та описи можуть містити шкідливі інструкції. Коли твоя кінцева точка webhook доступна в інтернеті, запускай шлюз у пісочниці (Docker, SSH‑бекенд). Дивись розділ [розділ безпеки](#security-notes) нижче.
:::

---
## Передумови

- Hermes Agent встановлений і працює (`hermes gateway`)
- [`gh` CLI](https://cli.github.com/) встановлений і автентифікований на хості шлюзу (`gh auth login`)
- Публічно доступна URL‑адреса твого Hermes‑екземпляра (див. [Local testing with ngrok](#local-testing-with-ngrok), якщо запускаєш локально)
- Адміністративний доступ до репозиторію GitHub (потрібен для керування веб‑хуками)

---
## Крок 1 — Увімкнути платформу веб‑хук

Додай наступне у свій `~/.hermes/config.yaml`:

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

**Ключові поля:**

| Поле | Опис |
|---|---|
| `secret` (route-level) | HMAC‑секрет для цього маршруту. Якщо пропущено, використовується глобальний `extra.secret`. |
| `events` | Список значень заголовка `X-GitHub-Event`, які слід приймати. Порожній список = приймати всі. |
| `prompt` | Шаблон; `{field}` і `{nested.field}` заповнюються даними з payload GitHub. |
| `deliver` | `github_comment` публікує через `gh pr comment`. `log` просто записує у журнал шлюзу. |
| `deliver_extra.repo` | Розв’язується, наприклад, у `org/repo` з payload. |
| `deliver_extra.pr_number` | Розв’язується у номер PR з payload. |

:::note Payload не містить код
Payload веб‑хука GitHub включає метадані PR (заголовок, опис, назви гілок, URL), але **не diff**. Наведений вище prompt інструктує агента виконати `gh pr diff`, щоб отримати фактичні зміни. Інструмент `terminal` входить до стандартного набору `hermes-webhook`, тому додаткова конфігурація не потрібна.
:::
## Крок 2 — Запустити шлюз

```bash
hermes gateway
```

Ти маєш бачити:

```
[webhook] Listening on 0.0.0.0:8644 — routes: github-pr-review
```

Перевір, що він працює:

```bash
curl http://localhost:8644/health
# {"status": "ok", "platform": "webhook"}
```

---
## Крок 3 — Зареєструй вебхук у GitHub

1. Перейди до свого репозиторію → **Settings** → **Webhooks** → **Add webhook**
2. Заповни:
   - **Payload URL:** `https://your-public-url.example.com/webhooks/github-pr-review`
   - **Content type:** `application/json`
   - **Secret:** те саме значення, яке ти вказав для `secret` у конфігурації маршруту
   - **Which events?** → **Select individual events** → познач **Pull requests**
3. Натисни **Add webhook**

GitHub одразу надішле подію `ping`, щоб підтвердити з’єднання. Вона безпечно ігнорується — `ping` не входить до твого списку `events` — і повертає `{"status": "ignored", "event": "ping"}`. Це лише записується на рівні DEBUG, тому не з’явиться у консолі за замовчуванням.
## Крок 4 — Відкрити тестовий PR

Створи гілку, запуши зміни та відкрий PR. Протягом 30–90 секунд (залежно від розміру PR та моделі) Hermes має залишити коментар‑огляд.

Щоб стежити за прогресом агента в режимі реального часу:

```bash
tail -f "${HERMES_HOME:-$HOME/.hermes}/logs/gateway.log"
```

---
## Локальне тестування за допомогою ngrok

Якщо Hermes працює на твоєму ноутбуці, використай [ngrok](https://ngrok.com/) для його експонування:

```bash
ngrok http 8644
```

Скопіюй URL `https://...ngrok-free.app` і використай його як GitHub Payload URL. На безкоштовному тарифі ngrok URL змінюється щоразу, коли ngrok перезапускається — оновлюй свій GitHub webhook кожну сесію. Платні акаунти ngrok отримують статичний домен.

Ти можеш швидко протестувати статичний маршрут безпосередньо за допомогою `curl` — без облікового запису GitHub чи реального PR.

:::tip Використовуй `deliver: log` під час локального тестування
Зміни `deliver: github_comment` на `deliver: log` у своїй конфігурації під час тестування. Інакше агент спробує опублікувати коментар у фіктивному репозиторії `org/repo#99` у тестовому payload, що призведе до помилки. Повернись до `deliver: github_comment`, коли будеш задоволений виводом.
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

Потім спостерігай за роботою агента:
```bash
tail -f "${HERMES_HOME:-$HOME/.hermes}/logs/gateway.log"
```

:::note
`hermes webhook test <name>` працює лише для **динамічних підписок**, створених за допомогою `hermes webhook subscribe`. Він не читає маршрути з `config.yaml`.
:::

---
## Фільтрація за конкретними діями

GitHub надсилає події `pull_request` для багатьох дій: `opened`, `synchronize`, `reopened`, `closed`, `labeled` тощо. Список `events` фільтрує лише за значенням заголовка `X-GitHub-Event` — він не може фільтрувати за підтипом дії на рівні маршрутизації.

Підказка у Кроці 1 вже обробляє це, інструктуючи агента зупинитися рано для подій `closed` та `labeled`.

:::warning Агент все одно працює і споживає токени
Інструкція «stop here» запобігає змістовному огляду, проте агент все одно працює до завершення для кожної події `pull_request` незалежно від дії. Вебхуки GitHub можуть фільтрувати лише за типом події (`pull_request`, `push`, `issues` тощо) — не за підтипом дії (`opened`, `closed`, `labeled`). Фільтрації на рівні маршрутизації для піддій немає. Для репозиторіїв з великим навантаженням прийми ці витрати або фільтруй вище за допомогою робочого процесу GitHub Actions, який умовно викликає твій URL вебхука.
:::

> Не існує синтаксису Jinja2 або умовних шаблонів. `{field}` і `{nested.field}` — це єдині підтримувані підстановки. Все інше передається агенту дослівно.

---
## Використання skill для послідовного стилю рецензії

Завантаж `Hermes skill` [/user‑guide/features/skills](/user-guide/features/skills), щоб надати агенту послідовну персональність рецензента. Додай `skills` у свій маршрут всередині `platforms.webhook.extra.routes` у `config.yaml`:

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

> **Note:** Only the first skill in the list that is found is loaded. Hermes does not stack multiple skills — subsequent entries are ignored.

---
## Надсилання відповідей у Slack або Discord замість

Замініть поля `deliver` та `deliver_extra` у вашому маршруті на потрібну платформу:

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

Цільова платформа також повинна бути ввімкнена та підключена в gateway. Якщо `chat_id` пропущено, відповідь буде надіслана у налаштований домашній канал цієї платформи.

Допустимі значення `deliver`: `log` · `github_comment` · `telegram` · `discord` · `slack` · `signal` · `sms`

---
## Підтримка GitLab

Той самий адаптер працює з GitLab. GitLab використовує `X-Gitlab-Token` для автентифікації (просте порівняння рядка, без HMAC) — Hermes обробляє це автоматично.

Для фільтрації подій GitLab встановлює `X-GitLab-Event` у значення типу `Merge Request Hook`, `Push Hook`, `Pipeline Hook`. Використовуй точне значення заголовка в `events`:

```yaml
events:
  - Merge Request Hook
```

Поля payload GitLab відрізняються від GitHub — наприклад `{object_attributes.title}` для назви MR і `{object_attributes.iid}` для номера MR. Найпростіший спосіб дізнатися повну структуру payload — це кнопка **Test** у налаштуваннях вашого вебхука в GitLab, разом із журналом **Recent Deliveries**. Альтернативно, можеш прибрати `prompt` з конфігурації маршруту — Hermes тоді передасть повний payload у вигляді форматованого JSON безпосередньно агенту, а відповідь агента (видима в журналі шлюзу за допомогою `deliver: log`) опише його структуру.
## Примітки щодо безпеки

- **Ніколи не використовуйте `INSECURE_NO_AUTH`** у продакшн‑середовищі — це повністю вимикає перевірку підпису. Воно призначене лише для локальної розробки.
- **Регулярно змінюйте ваш секрет вебхука** і оновлюйте його і в GitHub (налаштування вебхука), і у вашому `config.yaml`.
- **Обмеження швидкості** за замовчуванням становить 30 запитів/хв на маршрут (можна налаштувати через `extra.rate_limit`). При перевищенні повертається `429`.
- **Дублювання доставок** (повторні спроби вебхука) дедуплікуються за допомогою кешу ідемпотентності тривалістю 1 година. Ключ кешу — `X-GitHub-Delivery`, якщо він присутній, потім `X-Request-ID`, потім мітка часу в мілісекундах. Якщо жоден заголовок ідентифікатора доставки не встановлений, повторні спроби **не** дедуплікуються.
- **Prompt injection:** назви PR, їх опис та повідомлення комітів контролюються зловмисником. Шкідливі PR можуть спробувати маніпулювати діями агента. Запускай **шлюз інструментів** у пісочничому середовищі (Docker, VM), коли він доступний у публічному інтернеті.
## Устранення проблем

| Симптом | Перевірка |
|---|---|
| `401 Invalid signature` | Секрет у `config.yaml` не відповідає секрету вебхука GitHub |
| `404 Unknown route` | Ім’я маршруту в URL не збігається з ключем у `routes:` |
| `429 Rate limit exceeded` | Перевищено 30 запитів/хв на маршрут — часто трапляється при повторному надсиланні тестових подій з UI GitHub; зачекай хвилину або збільш `extra.rate_limit` |
| Коментар не опубліковано | `gh` не встановлено, не в PATH або не автентифіковано (`gh auth login`) |
| Агент працює, але коментару немає | Перевір журнал gateway — якщо вихід агента порожній або лише `"SKIP"`, доставка все одно здійснюється |
| Порт вже зайнятий | Зміни `extra.port` у `config.yaml` |
| Агент працює, але переглядає лише опис PR | Промпт не включає інструкцію `gh pr diff` — diff відсутній у навантаженні вебхука |
| Не видно події ping | Ігноровані події повертають `{"status":"ignored","event":"ping"}` лише на рівні журналу DEBUG — перевір журнал доставки GitHub (repo → Settings → Webhooks → ваш вебхук → Recent Deliveries) |

**Вкладка Recent Deliveries у GitHub** (repo → Settings → Webhooks → ваш вебхук) показує точні заголовки запиту, навантаження, HTTP‑статус та тіло відповіді для кожної доставки. Це найшвидший спосіб діагностувати помилки без перегляду журналів сервера.
## Повний довідник конфігурації

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
## Що далі?

- **[Cron-Based PR Reviews](./github-pr-review-agent.md)** — перевірка PR за розкладом, без потреби у публічній кінцевій точці
- **[Webhook Reference](/user-guide/messaging/webhooks)** — повна довідка щодо конфігурації платформи вебхуків
- **[Build a Plugin](/guides/build-a-hermes-plugin)** — упакувати логіку перевірки у поширюваний плагін
- **[Profiles](/user-guide/profiles)** — запустити спеціальний профіль оглядача зі своєю пам’яттю та конфігурацією