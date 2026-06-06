---
title: запасний (варіант) Providers
description: Налаштуй автоматичний відкат до резервних LLM providers, коли твоя основна модель недоступна.
sidebar_label: Fallback Providers
sidebar_position: 8
---

# Запасний (варіант) провайдерів

Hermes Agent має три рівні стійкості, які підтримують роботу твоїх сесій, коли провайдери стикаються з проблемами:

1. **[Credential pools](./credential-pools.md)** — чергує кілька API‑ключів одного *того ж* провайдера (використовується першим)
2. **Primary model fallback** — автоматично переключається на *інший* провайдер:модель, коли основна модель не працює
3. **Auxiliary task fallback** — незалежний запасний (варіант) провайдер для допоміжних завдань, таких як веб‑пошук, стиснення та генерація зображень

Credential pools забезпечують чергування в межах одного провайдера (наприклад, кілька ключів OpenRouter). Ця сторінка охоплює перехід між різними провайдерами. Обидва підходи є необов’язковими та працюють незалежно.
## Primary Model Fallback

Коли твій основний постачальник LLM стикається з помилками — обмеженнями швидкості, перевантаженням сервера, збоями автентифікації, розривами з’єднання — Hermes може автоматично переключитися на запасний постачальник : модель під час сесії, не втрачаючи розмову.

### Configuration

Найпростіший шлях — інтерактивний менеджер:

```bash
hermes fallback
```

`hermes fallback` повторно використовує вибір постачальника з `hermes model` — той самий список постачальників, ті ж підказки облікових даних, та ж валідація. Використовуй підкоманди `add`, `list` (alias `ls`), `remove` (alias `rm`) та `clear` для керування ланцюжком. Зміни зберігаються у верхньому рівні списку `fallback_providers:` у `config.yaml`.

Якщо ти віддаєш перевагу редагуванню YAML безпосередньо, додай розділ `fallback_model` у `~/.hermes/config.yaml`:

```yaml
fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
```

І `provider`, і `model` **обов’язкові**. Якщо будь‑яке з них відсутнє, запасний варіант вимикається.

:::note `fallback_model` vs `fallback_providers`
`fallback_model` (однина) — це застарілий ключ для одного запасного варіанту; Hermes все ще підтримує його задля зворотної сумісності. `fallback_providers` (множина, список) дозволяє вказати кілька запасних варіантів у порядку пріоритету; `hermes fallback` записує в цей ключ. Коли обидва налаштовані, Hermes об’єднує їх, причому пріоритет має `fallback_providers`.
:::

### Supported Providers

| Provider | Value | Requirements |
|----------|-------|-------------|
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` |
| Nous Portal | `nous` | `hermes setup --portal` (fresh) or `hermes auth add nous` (OAuth) |
| OpenAI Codex | `openai-codex` | `hermes model` (ChatGPT OAuth) |
| GitHub Copilot | `copilot` | `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, or `GITHUB_TOKEN` |
| GitHub Copilot ACP | `copilot-acp` | External process (editor integration) |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` or Claude Code credentials |
| z.ai / GLM | `zai` | `GLM_API_KEY` |
| Kimi / Moonshot | `kimi-coding` | `KIMI_API_KEY` |
| MiniMax | `minimax` | `MINIMAX_API_KEY` |
| MiniMax (China) | `minimax-cn` | `MINIMAX_CN_API_KEY` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` |
| NVIDIA NIM | `nvidia` | `NVIDIA_API_KEY` (optional: `NVIDIA_BASE_URL`) |
| GMI Cloud | `gmi` | `GMI_API_KEY` (optional: `GMI_BASE_URL`) |
| StepFun | `stepfun` | `STEPFUN_API_KEY` (optional: `STEPFUN_BASE_URL`) |
| Ollama Cloud | `ollama-cloud` | `OLLAMA_API_KEY` |
| Google Gemini (OAuth) | `google-gemini-cli` | `hermes model` (Google OAuth; optional: `HERMES_GEMINI_PROJECT_ID`) |
| Google AI Studio | `gemini` | `GOOGLE_API_KEY` (alias: `GEMINI_API_KEY`) |
| xAI (Grok) | `xai` (alias `grok`) | `XAI_API_KEY` (optional: `XAI_BASE_URL`) |
| xAI Grok OAuth (SuperGrok) | `xai-oauth` (alias `grok-oauth`) | `hermes model` → xAI Grok OAuth (browser login; SuperGrok subscription) |
| AWS Bedrock | `bedrock` | Standard boto3 auth (`AWS_REGION` + `AWS_PROFILE` or `AWS_ACCESS_KEY_ID`) |
| Qwen Portal (OAuth) | `qwen-oauth` | `hermes model` (Qwen Portal OAuth; optional: `HERMES_QWEN_BASE_URL`) |
| MiniMax (OAuth) | `minimax-oauth` | `hermes model` (MiniMax portal OAuth) |
| OpenCode Zen | `opencode-zen` | `OPENCODE_ZEN_API_KEY` |
| OpenCode Go | `opencode-go` | `OPENCODE_GO_API_KEY` |
| Kilo Code | `kilocode` | `KILOCODE_API_KEY` |
| Xiaomi MiMo | `xiaomi` | `XIAOMI_API_KEY` |
| Arcee AI | `arcee` | `ARCEEAI_API_KEY` |
| GMI Cloud | `gmi` | `GMI_API_KEY` |
| Alibaba / DashScope | `alibaba` | `DASHSCOPE_API_KEY` |
| Alibaba Coding Plan | `alibaba-coding-plan` | `ALIBABA_CODING_PLAN_API_KEY` (falls back to `DASHSCOPE_API_KEY`) |
| Kimi / Moonshot (China) | `kimi-coding-cn` | `KIMI_CN_API_KEY` |
| StepFun | `stepfun` | `STEPFUN_API_KEY` |
| Tencent TokenHub | `tencent-tokenhub` | `TOKENHUB_API_KEY` |
| Microsoft Foundry | `azure-foundry` | `AZURE_FOUNDRY_API_KEY` + `AZURE_FOUNDRY_BASE_URL` |
| LM Studio (local) | `lmstudio` | `LM_API_KEY` (or none for local) + `LM_BASE_URL` |
| Hugging Face | `huggingface` | `HF_TOKEN` |
| Custom endpoint | `custom` | `base_url` + `key_env` (see below) |

### Custom Endpoint Fallback

Для власної сумісної з OpenAI кінцевої точки додай `base_url` і, за потреби, `key_env`:

```yaml
fallback_model:
  provider: custom
  model: my-local-model
  base_url: http://localhost:8000/v1
  key_env: MY_LOCAL_KEY              # env var name containing the API key
```

### When Fallback Triggers

Запасний варіант активується автоматично, коли первинна модель не вдається через:

- **Обмеження швидкості** (HTTP 429) — після вичерпання спроб повтору
- **Помилки сервера** (HTTP 500, 502, 503) — після вичерпання спроб повтору
- **Збої автентифікації** (HTTP 401, 403) — одразу (не має сенсу повторювати)
- **Не знайдено** (HTTP 404) — одразу
- **Некоректні відповіді** — коли API повертає пошкоджені або порожні відповіді кілька разів

Після спрацювання Hermes:

1. Отримує облікові дані для запасного постачальника
2. Створює новий API‑клієнт
3. Замінює модель, постачальника та клієнта «на місці»
4. Скидає лічильник повторів і продовжує розмову

Перемикач прозорий — історія розмови, виклики інструментів та контекст зберігаються. Агент продовжує саме з того місця, лише використовуючи іншу модель.

:::info Per-Turn, Not Per-Session
Запасний варіант **обмежений ходом**: кожне нове повідомлення користувача починається з відновленої первинної моделі. Якщо первинна модель падає посеред ходу, запас активується лише для цього ходу. На наступному повідомленні Hermes знову пробує первинну. Протягом одного ходу запас може активуватись максимум один раз — якщо і запас не вдається, вступає звичайна обробка помилок (повторні спроби, потім повідомлення про помилку). Це запобігає каскадним циклам відмов у межах одного ходу, даючи первинній моделі новий шанс кожен хід.
:::

### Examples

**OpenRouter як запасний для Anthropic native:**
```yaml
model:
  provider: anthropic
  default: claude-sonnet-4-6

fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
```

**Nous Portal як запасний для OpenRouter:**
```yaml
model:
  provider: openrouter
  default: anthropic/claude-opus-4

fallback_model:
  provider: nous
  model: nous-hermes-3
```

**Локальна модель як запасна для хмари:**
```yaml
fallback_model:
  provider: custom
  model: llama-3.1-70b
  base_url: http://localhost:8000/v1
  key_env: LOCAL_API_KEY
```

**Codex OAuth як запасний:**
```yaml
fallback_model:
  provider: openai-codex
  model: gpt-5.3-codex
```

### Where Fallback Works

| Context | Fallback Supported |
|---------|-------------------|
| CLI sessions | ✔ |
| Messaging gateway (Telegram, Discord, etc.) | ✔ |
| Subagent delegation | ✘ (subagents do not inherit fallback config) |
| Cron jobs | ✘ (run with a fixed provider) |
| Auxiliary tasks (vision, compression) | ✘ (use their own provider chain — see below) |

:::tip
Для `fallback_model` не існує змінних середовища — його налаштовують виключно через `config.yaml`. Це навмисно: конфігурація запасного варіанту — свідомий вибір, а не те, що може бути перезаписане застарілим експортом змінної оболонки.
:::

---
## Запасний (варіант) допоміжного завдання

Hermes використовує окремі легкі моделі для допоміжних завдань. Кожне завдання має власний ланцюжок розв’язання провайдера, який діє як вбудована система запасного (варіанту).

### Завдання з незалежним розв’язанням провайдера

| Завдання | Що воно робить | Ключ конфігурації |
|------|-------------|-----------|
| Vision | Аналіз зображень, скріншоти браузера | `auxiliary.vision` |
| Web Extract | Підсумок веб‑сторінки | `auxiliary.web_extract` |
| Compression | Підсумки стискання контексту | `auxiliary.compression` |
| Skills Hub | Пошук і відкриття навичок | `auxiliary.skills_hub` |
| MCP | Операції‑допоміжники MCP | `auxiliary.mcp` |
| Approval | Класифікація схвалення команд | `auxiliary.approval` |
| Title Generation | Підсумок назви сесії | `auxiliary.title_generation` |
| Triage Specifier | `hermes kanban specify` / кнопка dashboard ✨ — розгортає однорядкове завдання триажу у реальну специфікацію | `auxiliary.triage_specifier` |

### Ланцюжок автодетекції

Коли провайдер завдання встановлений у `"auto"` (за замовчуванням), Hermes пробує провайдери у порядку, доки один не спрацює:

**Для текстових завдань (compression, web extract тощо):**

```text
OpenRouter → Nous Portal → Custom endpoint → Codex OAuth →
API-key providers (z.ai, Kimi, MiniMax, Xiaomi MiMo, Hugging Face, Anthropic) → give up
```

**Для завдань зору:**

```text
Main provider (if vision-capable) → OpenRouter → Nous Portal →
Codex OAuth → Anthropic → Custom endpoint → give up
```

Якщо визначений провайдер не вдається під час виклику, Hermes також має внутрішню повторну спробу: якщо провайдер не є OpenRouter і не вказано явний `base_url`, він спробує OpenRouter як останній запасний (варіант).

### Налаштування допоміжних провайдерів

Кожне завдання можна налаштувати окремо у `config.yaml`:

```yaml
auxiliary:
  vision:
    provider: "auto"              # auto | openrouter | nous | codex | main | anthropic
    model: ""                     # e.g. "openai/gpt-4o"
    base_url: ""                  # direct endpoint (takes precedence over provider)
    api_key: ""                   # API key for base_url

  web_extract:
    provider: "auto"
    model: ""

  compression:
    provider: "auto"
    model: ""

  skills_hub:
    provider: "auto"
    model: ""

  mcp:
    provider: "auto"
    model: ""
```

Усі завдання вище слідують одному шаблону **provider / model / base_url**. Стискання контексту налаштовується під `auxiliary.compression`:

```yaml
auxiliary:
  compression:
    provider: main                                    # Same provider options as other auxiliary tasks
    model: google/gemini-3-flash-preview
    base_url: null                                    # Custom OpenAI-compatible endpoint
```

І модель запасного (варіанту) використовується:

```yaml
fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
  # base_url: http://localhost:8000/v1               # Optional custom endpoint
```

Усі три — auxiliary, compression, fallback — працюють однаково: встанови `provider`, щоб вибрати, хто обробляє запит, `model` — яку модель, і `base_url` — власну кінцеву точку (перезаписує провайдера).

### Параметри провайдера для допоміжних завдань

Ці параметри застосовуються лише до конфігурацій `auxiliary:`, `compression:` та `fallback_model:` — `"main"` **не** є допустимим значенням для вашого провайдера `model.provider` верхнього рівня. Для власних кінцевих точок використовуйте `provider: custom` у розділі `model:` (див. [AI Providers](/integrations/providers)).

| Провайдер | Опис | Вимоги |
|----------|------|--------|
| `"auto"` | Спробувати провайдери у порядку, доки один не спрацює (за замовчуванням) | Принаймні один налаштований провайдер |
| `"openrouter"` | Примусово OpenRouter | `OPENROUTER_API_KEY` |
| `"nous"` | Примусово Nous Portal | `hermes auth` |
| `"codex"` | Примусово Codex OAuth | `hermes model` → Codex |
| `"main"` | Використовувати провайдера, який застосовує головний агент (лише допоміжні завдання) | Налаштований активний головний провайдер |
| `"anthropic"` | Примусово Anthropic native | `ANTHROPIC_API_KEY` або облікові дані Claude Code |

### Пряме перевизначення кінцевої точки

Для будь‑якого допоміжного завдання встановлення `base_url` обходить розв’язання провайдера повністю і надсилає запити безпосередньо до цієї кінцевої точки:

```yaml
auxiliary:
  vision:
    base_url: "http://localhost:1234/v1"
    api_key: "local-key"
    model: "qwen2.5-vl"
```

`base_url` має пріоритет над `provider`. Hermes використовує налаштований `api_key` для автентифікації, переходячи до `OPENAI_API_KEY`, якщо він не встановлений. Він **не** повторно використовує `OPENROUTER_API_KEY` для власних кінцевих точок.
## Auxiliary Capacity-Error Fallback

Коли ти встановлюєш явний додатковий провайдер (наприклад `auxiliary.vision.provider: glm`), Hermes розглядає його як свій переважний вибір — але якщо провайдер буквально не може обробити запит через **capacity error** (HTTP 402 payment required, HTTP 429 daily‑quota exhaustion, збій з’єднання), Hermes переходить до ланцюжка запасних варіантів замість того, щоб мовчки провалитися:

1. **Primary aux provider** — той, який ти налаштував (перевіряється першим, завжди)
2. **`auxiliary.<task>.fallback_chain`** — твій список перевизначень для конкретного завдання, якщо ти його створив
3. **Main agent provider + model** — остання безпека (перевіряється завжди, навіть якщо ти не писав ланцюжок)
4. **Warn + re‑raise** — якщо всі шари зазнають невдачі, Hermes записує `Auxiliary <task>: ... all fallbacks exhausted` на рівні **WARNING** і повторно піднімає початкову помилку

Тимчасові обмеження HTTP 429 (`Retry-After: …`) розглядаються як обмеження запиту, а не як проблеми capacity — вони поважають твій явний вибір провайдера і **не** запускають ланцюжок запасних варіантів. Лише вичерпання щоденної/місячної квоти, помилки оплати та збої з’єднання обходять gate явного провайдера.

Для користувачів з `provider: auto` (без явного додаткового провайдера) існуючий ланцюжок авто‑детекції працює замість кроків 2‑3. Його перший крок вже є головною моделлю агента, тому користувачі `auto` отримують той самий результат без жодної конфігурації.

### Optional: per‑task fallback chain

Якщо ти хочеш інший порядок запасних варіантів, ніж «головна модель агента першою», явно налаштуй `fallback_chain`. Кожен запис потребує принаймні `provider`; `model`, `base_url` та `api_key` є необов’язковими.

```yaml
auxiliary:
  vision:
    provider: glm
    model: glm-4v-flash
    fallback_chain:
      - provider: openrouter
        model: google/gemini-3-flash-preview
      - provider: nous
        model: anthropic/claude-sonnet-4

  compression:
    provider: openrouter
    fallback_chain:
      - provider: openai
        model: gpt-4o-mini
```

Ти **не** зобов’язаний налаштовувати `fallback_chain`, щоб отримати запасний варіант — безпека головного агента працює завжди. Використовуй його лише тоді, коли дійсно потрібен інший порядок, ніж за замовчуванням.

### Provider quota errors that trigger fallback

Hermes розпізнає їх як еквівалент capacity‑error до 402 credit exhaustion (не тимчасові обмеження швидкості):

- Bedrock / LiteLLM: `Too many tokens per day`, `daily limit`, `tokens per day`
- Vertex AI / GCP: `quota exceeded`, `resource exhausted`, `RESOURCE_EXHAUSTED`
- Generic: `daily quota`, `quota_exceeded`

Якщо твій провайдер повертає іншу фразу для вичерпання щоденної квоти, і Hermes не запускає запасний варіант, це баг — відкрий issue з точним рядком помилки.
## Context Compression Fallback

Контекстне стиснення використовує блок конфігурації `auxiliary.compression` для керування тим, яка модель і провайдер виконують резюмування:

```yaml
auxiliary:
  compression:
    provider: "auto"                              # auto | openrouter | nous | main
    model: "google/gemini-3-flash-preview"
```

:::info Legacy migration
Старі конфігурації з `compression.summary_model` / `compression.summary_provider` / `compression.summary_base_url` автоматично мігруються до `auxiliary.compression.*` під час першого завантаження (версія конфігурації 17).
:::

Якщо немає доступного провайдера для стиснення, Hermes пропускає проміжні ходи діалогу без генерації підсумку, замість того щоб завершити сесію з помилкою.

---
## Перевизначення провайдера делегування

Підагенти, створені за допомогою `delegate_task`, **не** використовують основну запасну модель. Однак їх можна перенаправити до іншої пари provider:model для оптимізації витрат:

```yaml
delegation:
  provider: "openrouter"                      # override provider for all subagents
  model: "google/gemini-3-flash-preview"      # override model
  # base_url: "http://localhost:1234/v1"      # or use a direct endpoint
  # api_key: "local-key"
```

Дивись [Делегування підагентів](/user-guide/features/delegation) для повних деталей налаштувань.

---
## Постачальники Cron‑завдань

Cron‑завдання виконуються з використанням того provider, який налаштовано на момент виконання. Вони не підтримують запасний (fallback) варіант. Щоб використати інший provider для cron‑завдань, налаштуй перевизначення `provider` і `model` безпосередньо в самому cron‑завданні:

```python
cronjob(
    action="create",
    schedule="every 2h",
    prompt="Check server status",
    provider="openrouter",
    model="google/gemini-3-flash-preview"
)
```

Дивись [Заплановані завдання (Cron)](/user-guide/features/cron) для повних деталей конфігурації.

---
## Огляд

| Функція | Механізм запасний (варіант) | Розташування конфігурації |
|---------|----------------------------|---------------------------|
| Main agent model | `fallback_model` у config.yaml — переключення на запасний варіант кожен хід при помилках (основний відновлюється кожен хід) | `fallback_model:` (верхній рівень) |
| Auxiliary tasks (any) — auto users | Повний ланцюжок автоматичного визначення (спочатку основна модель агента, потім ланцюжок провайдерів) при помилках ємності | `auxiliary.<task>.provider: auto` |
| Auxiliary tasks (any) — explicit provider | `fallback_chain` (за наявності) → основна модель агента → попередження + підвищення, лише при помилках ємності | `auxiliary.<task>.fallback_chain` |
| Vision | Багаторівневий (див. вище) + внутрішня повторна спроба OpenRouter | `auxiliary.vision` |
| Web extraction | Багаторівневий (див. вище) + внутрішня повторна спроба OpenRouter | `auxiliary.web_extract` |
| Context compression | Багаторівневий (див. вище); переходить у режим без підсумку, якщо всі рівні недоступні | `auxiliary.compression` |
| Skills hub | Багаторівневий (див. вище) | `auxiliary.skills_hub` |
| MCP helpers | Багаторівневий (див. вище) | `auxiliary.mcp` |
| Approval classification | Багаторівневий (див. вище) | `auxiliary.approval` |
| Title generation | Багаторівневий (див. вище) | `auxiliary.title_generation` |
| Triage specifier | Багаторівневий (див. вище) | `auxiliary.triage_specifier` |
| Delegation | Перевизначення провайдера лише (без автоматичного запасного варіанту) | `delegation.provider` / `delegation.model` |
| Cron jobs | Перевизначення провайдера для кожного завдання лише (без автоматичного запасного варіанту) | Перезапис `provider` / `model` для кожного завдання |