---
sidebar_position: 16
title: "Google Gemini"
description: "Використовуй Hermes Agent з Google Gemini — native AI Studio API, налаштування API-key, опція OAuth, виклик інструменту, потокова передача та рекомендації щодо квоти"
---

# Google Gemini

Hermes Agent підтримує Google Gemini як вбудованого провайдера, використовуючи **Google AI Studio / Gemini API** — не сумісну з OpenAI кінцеву точку. Це дозволяє Hermes перетворювати свій внутрішній цикл повідомлень і інструментів у форматі OpenAI у нативний API `generateContent` Gemini, зберігаючи виклик інструментів, потокову передачу, мультимодальні входи та специфічні метадані відповіді Gemini.

Hermes також підтримує окремий провайдер **Google Gemini (OAuth)**, який використовує той самий бекенд Cloud Code Assist, що й CLI Google Gemini. Використовуй провайдер API‑ключа (`gemini`) для найменш ризикованого офіційного шляху API.
## Prerequisites

- **Google AI Studio API key** — створити його на [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **Billing-enabled Google Cloud project** — рекомендовано для використання агента. Безкоштовний рівень Gemini занадто малий для довготривалих сесій агента, оскільки Hermes може робити кілька викликів моделі за один хід користувача.
- **Hermes installed** — додатковий Python‑пакет не потрібен для вбудованого провайдера `gemini`.

:::tip API key path
Встанови `GOOGLE_API_KEY` або `GEMINI_API_KEY`. Hermes перевіряє обидві назви для провайдера `gemini`.
:::
## Швидкий старт

```bash
# Add your Gemini API key
echo "GOOGLE_API_KEY=..." >> ~/.hermes/.env

# Select Gemini as your provider
hermes model
# → Choose "More providers..." → "Google AI Studio"
# → Hermes checks your key tier and shows Gemini models
# → Select a model

# Start chatting
hermes chat
```

Якщо ти віддаєш перевагу прямому редагуванню конфігурації, використай базовий URL API Gemini:

```yaml
model:
  default: gemini-3-flash-preview
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta
```
## Конфігурація

Після запуску `hermes model` ваш файл `~/.hermes/config.yaml` міститиме:

```yaml
model:
  default: gemini-3-flash-preview
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta
```

А у `~/.hermes/.env`:

⟟HOLD_3⟧

### Native Gemini API

Рекомендована кінцева точка:

```text
https://generativelanguage.googleapis.com/v1beta
```

Hermes виявляє цю кінцеву точку і створює власний адаптер Gemini. Внутрішньо Hermes і надалі тримає цикл агента у повідомленнях у форматі OpenAI, а потім перекладає кожен запит у рідну схему Gemini:

- `messages[]` → Gemini `contents[]`
- системні підказки → Gemini `systemInstruction`
- схеми інструментів → Gemini `functionDeclarations`
- результати інструментів → Gemini `functionResponse` частини
- потокові відповіді → фрагменти потоку у форматі OpenAI для циклу Hermes

:::note Gemini 3 thought signatures
Для використання інструментів Gemini 3 Hermes зберігає значення `thoughtSignature`, прикріплені до частин виклику функції, і відтворює їх у наступному ході інструменту. Це охоплює критичний шлях валідації для багатокрокових робочих процесів агента.

Gemini 3 може також прикріплювати підписи думок до інших частин відповіді. Нативний адаптер Hermes сьогодні оптимізований під цикли інструментів агента, тому ще не відтворює кожен підпис, не пов’язаний із викликом інструменту, з повною деталізацією на рівні частин.
:::

### Пріоритетне використання нативної кінцевої точки

Google також надає кінцеву точку, сумісну з OpenAI:

```text
https://generativelanguage.googleapis.com/v1beta/openai/
```

Для сесій агента Hermes надавай перевагу вищезгаданій нативній кінцевій точці Gemini. Hermes включає нативний адаптер Gemini, тому може безпосередньо відображати багатокрокове використання інструментів, результати викликів інструментів, потокові дані, мультимодальні входи та метадані відповіді Gemini у API `generateContent`. Кінцева точка, сумісна з OpenAI, все ще корисна, коли тобі спеціально потрібна сумісність з API OpenAI.

Якщо ти раніше встановив `GEMINI_BASE_URL` на URL `/openai`, видали його або зміни:

```bash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

### OAuth Provider

Hermes також має провайдера `google-gemini-cli`:

```bash
hermes model
# → Choose "Google Gemini (OAuth)"
```

Він використовує вхід у браузері за допомогою PKCE та бекенд Cloud Code Assist. Це може бути корисним для користувачів, які хочуть OAuth у стилі Gemini CLI, проте Hermes показує явне попередження, оскільки Google може розцінювати використання клієнта OAuth Gemini CLI у сторонньому програмному забезпеченні як порушення політики. Для продакшн‑використання або мінімального ризику надавай перевагу провайдеру API‑ключа, зазначеному вище.
## Доступні моделі

Вибірка `hermes model` показує моделі Gemini, які підтримуються в реєстрі провайдерів Hermes. Типові варіанти включають:

| Model | ID | Notes |
|-------|----|-------|
| Gemini 3.1 Pro Preview | `gemini-3.1-pro-preview` | Найпотужніша попередня модель, коли доступна |
| Gemini 3 Pro Preview | `gemini-3-pro-preview` | Модель зі сильними можливостями логічного мислення та кодування |
| Gemini 3 Flash Preview | `gemini-3-flash-preview` | Рекомендований баланс швидкості та потужності за замовчуванням |
| Gemini 3.1 Flash Lite Preview | `gemini-3.1-flash-lite-preview` | Найшвидший / найменш дорогий варіант, коли доступний |

Наявність моделей змінюється з часом. Якщо модель зникає або не ввімкнена для твого ключа, запусти `hermes model` ще раз і вибери одну зі актуального списку.

:::info Model IDs
Використовуй нативні ідентифікатори моделей Gemini, такі як `gemini-3-flash-preview`, а не ідентифікатори у стилі OpenRouter, наприклад `google/gemini-3-flash-preview`, коли `provider: gemini`.
:::

### Останні псевдоніми

Google публікує змінювані псевдоніми для сімей Pro і Flash Gemini. `gemini-pro-latest` і `gemini-flash-latest` корисні, коли ти хочеш, щоб Google автоматично оновлював модель без зміни конфігурації Hermes.

| Alias | Currently tracks | Notes |
|-------|------------------|-------|
| `gemini-pro-latest` | Остання модель Gemini Pro | Найкраще, коли потрібен поточний Pro‑за‑замовчуванням від Google |
| `gemini-flash-latest` | Остання модель Gemini Flash | Найкраще, коли потрібен поточний Flash‑за‑замовчуванням від Google |

```yaml
model:
  default: gemini-pro-latest
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta
```

Якщо потрібна сувора відтворюваність, віддавай перевагу явним ідентифікаторам моделей, таким як `gemini-3.1-pro-preview` або `gemini-3-flash-preview`.

### Gemma через Gemini API

Google також надає моделі Gemma через Gemini API. Hermes розпізнає їх як моделі Google, але приховує дуже низькопродуктивні записи Gemma у вибірці моделей за замовчуванням, щоб нові користувачі випадково не обрали модель оцінювального рівня для довготривалої сесії агента.

Корисні ідентифікатори для оцінки включають:

| Model | ID | Notes |
|-------|----|-------|
| Gemma 4 31B IT | `gemma-4-31b-it` | Більша модель Gemma; корисна для сумісності та оцінки якості |
| Gemma 4 26B A4B IT | `gemma-4-26b-a4b-it` | Менший варіант з активними параметрами, коли доступний |

Ці моделі найкраще розглядати як варіанти оцінки для ключів Gemini API. Ціноутворення Gemma API від Google доступне лише у безкоштовному тарифі, а обмеження використання низькі порівняно з виробничими моделями Gemini, тому тривале використання агента Hermes зазвичай переходить на платну модель Gemini, самостійне розгортання або інший провайдер з відповідною квотою.

Щоб використати модель Gemma, яка прихована у вибірці, встанови її безпосередньо:

```yaml
model:
  default: gemma-4-31b-it
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta
```
## Перемикання моделей під час сесії

Використовуй команду `/model` під час розмови:

```text
/model gemini-3-flash-preview
/model gemini-flash-latest
/model gemini-3-pro-preview
/model gemini-pro-latest
/model gemma-4-31b-it
/model gemini-3.1-flash-lite-preview
```

Якщо ти ще не налаштував Gemini, вийди з сесії та спочатку запусти `hermes model`. `/model` перемикає між вже налаштованими провайдерами та моделями; він не збирає нові API‑ключі.
## Діагностика

```bash
hermes doctor
```

Лікар перевіряє:

- Чи доступний `GOOGLE_API_KEY` або `GEMINI_API_KEY`
- Чи існують облікові дані Gemini OAuth для `google-gemini-cli`
- Чи можна розв’язати налаштовані облікові дані провайдера

Для перевірки використання квоти OAuth запусти це всередині сесії Hermes:

```text
/gquota
```

`/gquota` застосовується до OAuth‑провайдера `google-gemini-cli`, а не до провайдера API‑ключа AI Studio.
## Шлюз (Платформи обміну повідомленнями)

Gemini працює з усіма платформами шлюзу Hermes (Telegram, Discord, Slack, WhatsApp, LINE, Feishu тощо). Налаштуй Gemini як свого провайдера, а потім запусти шлюз звичайним способом:

```bash
hermes gateway setup
hermes gateway start
```

Шлюз читає `config.yaml` і використовує ту ж конфігурацію провайдера Gemini.
## Устранення проблем

### «Gemini native client requires an API key»

Hermes не зміг знайти придатний API‑ключ. Додай один із них у `~/.hermes/.env`:

```bash
GOOGLE_API_KEY=...
# or
GEMINI_API_KEY=...
```

Потім запусти `hermes model` ще раз.

### «This Google API key is on the free tier»

Hermes перевіряє Gemini API‑ключі під час налаштування. Квоти безкоштовного рівня можуть бути вичерпані вже після кількох ходів агента, оскільки використання інструментів, повторні спроби, стиснення та допоміжні завдання можуть вимагати кількох викликів моделі.

Увімкни білінг у проєкті Google Cloud, прив’язаному до твого ключа, за потреби згенеруй ключ заново, а потім виконай:

```bash
hermes model
```

### «404 model not found»

Вибрана модель недоступна для твого облікового запису, регіону або ключа. Запусти `hermes model` ще раз і обери іншу модель Gemini зі списку.

### Модель Gemma не показується у `hermes model`

Hermes може приховувати моделі Gemma з низькою пропускною здатністю у виборнику за замовчуванням. Якщо ти навмисно хочеш її оцінити, вкажи ідентифікатор моделі безпосередньо у `~/.hermes/config.yaml`.

### «429 quota exceeded» у Gemma

Моделі Gemma, доступні через Gemini API, корисні для оцінки, але їх безкоштовні квоти низькі. Використовуй їх для тестування сумісності, а потім переходь на платну модель Gemini або іншого провайдера для тривалих сесій агента.

### OpenAI‑compatible endpoint налаштовано

Перевір `~/.hermes/.env` на наявність:

```bash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

Зміни його на нативний endpoint або видали перевизначення:

```bash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

### Попередження під час OAuth‑входу

Провайдер `google-gemini-cli` використовує OAuth‑потік Gemini CLI / Cloud Code Assist. Hermes попереджає перед його запуском, оскільки це відрізняється від офіційного шляху API‑ключа AI Studio. Використовуй `provider: gemini` разом із `GOOGLE_API_KEY` для офіційної інтеграції за допомогою API‑ключа.

### Виклик інструменту завершується помилками схеми

Онови Hermes і повторно запусти `hermes model`. Нативний адаптер Gemini санітує схеми інструментів для суворішого формату оголошення функцій Gemini; старі збірки або кастомні endpoint‑и можуть не підтримувати це.
## Пов’язані

- [Постачальники ШІ](/integrations/providers)
- [Конфігурація](/user-guide/configuration)
- [Запасні постачальники](/user-guide/features/fallback-providers)
- [AWS Bedrock](/guides/aws-bedrock) — нативна інтеграція хмарного провайдера з використанням облікових даних AWS