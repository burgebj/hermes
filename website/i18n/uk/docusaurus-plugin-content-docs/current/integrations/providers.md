---
title: "постачальники ШІ"
sidebar_label: "AI Providers"
sidebar_position: 1
---

# Провайдери ШІ

Ця сторінка охоплює налаштування провайдерів інференції для Hermes Agent — від хмарних API, таких як OpenRouter і Anthropic, до самохостинг‑ендпоінтів, як Ollama і vLLM, до розширених налаштувань маршрутизації та запасного (фолбек) варіанту конфігурацій. Тобі потрібен принаймні один налаштований провайдер, щоб використовувати Hermes.
## Inference Providers

Тобі потрібен принаймні один спосіб підключення до LLM. Використовуй `hermes model` для інтерактивного перемикання постачальників і моделей або налаштуй їх безпосередньо:

| Provider | Налаштування |
|----------|--------------|
| **Nous Portal** | `hermes model` (OAuth, підписка) |
| **OpenAI Codex** | `hermes model` (ChatGPT OAuth, використовує моделі Codex) |
| **GitHub Copilot** | `hermes model` (OAuth device code flow, `COPILOT_GITHUB_TOKEN`, `GH_TOKEN` або `gh auth token`) |
| **GitHub Copilot ACP** | `hermes model` (запускає локальний `copilot --acp --stdio`) |
| **Anthropic** | `hermes model` (Claude Max + додаткові кредити через OAuth; також підтримує Anthropic API key або ручний setup‑token — дивись примітку нижче) |
| **OpenRouter** | `OPENROUTER_API_KEY` у `~/.hermes/.env` |
| **NovitaAI** | `NOVITA_API_KEY` у `~/.hermes/.env` (provider: `novita`, 200+ моделей, Model API, Agent Sandbox, GPU Cloud) |
| **z.ai / GLM** | `GLM_API_KEY` у `~/.hermes/.env` (provider: `zai`) |
| **Kimi / Moonshot** | `KIMI_API_KEY` у `~/.hermes/.env` (provider: `kimi-coding`) |
| **Kimi / Moonshot (China)** | `KIMI_CN_API_KEY` у `~/.hermes/.env` (provider: `kimi-coding-cn`; aliases: `kimi-cn`, `moonshot-cn`) |
| **Arcee AI** | `ARCEEAI_API_KEY` у `~/.hermes/.env` (provider: `arcee`; aliases: `arcee-ai`, `arceeai`) |
| **GMI Cloud** | `GMI_API_KEY` у `~/.hermes/.env` (provider: `gmi`; aliases: `gmi-cloud`, `gmicloud`) |
| **MiniMax** | `MINIMAX_API_KEY` у `~/.hermes/.env` (provider: `minimax`) |
| **MiniMax China** | `MINIMAX_CN_API_KEY` у `~/.hermes/.env` (provider: `minimax-cn`) |
| **xAI (Grok) — Responses API** | `XAI_API_KEY` у `~/.hermes/.env` (provider: `xai`) |
| **xAI Grok OAuth (SuperGrok)** | `hermes model` → “xAI Grok OAuth (SuperGrok / Premium+)” — вхід у браузері, без API‑key. Дивись [guide](../guides/xai-grok-oauth.md) |
| **Qwen Cloud (Alibaba DashScope)** | `DASHSCOPE_API_KEY` у `~/.hermes/.env` (provider: `alibaba`) |
| **Alibaba Cloud (Coding Plan)** | `DASHSCOPE_API_KEY` (provider: `alibaba-coding-plan`, alias: `alibaba_coding`) — окремий SKU білінгу, інший endpoint |
| **Kilo Code** | `KILOCODE_API_KEY` у `~/.hermes/.env` (provider: `kilocode`) |
| **Xiaomi MiMo** | `XIAOMI_API_KEY` у `~/.hermes/.env` (provider: `xiaomi`, aliases: `mimo`, `xiaomi-mimo`) |
| **Tencent TokenHub** | `TOKENHUB_API_KEY` у `~/.hermes/.env` (provider: `tencent-tokenhub`, aliases: `tencent`, `tokenhub`, `tencentmaas`) |
| **OpenCode Zen** | `OPENCODE_ZEN_API_KEY` у `~/.hermes/.env` (provider: `opencode-zen`) |
| **OpenCode Go** | `OPENCODE_GO_API_KEY` у `~/.hermes/.env` (provider: `opencode-go`) |
| **DeepSeek** | `DEEPSEEK_API_KEY` у `~/.hermes/.env` (provider: `deepseek`) |
| **Hugging Face** | `HF_TOKEN` у `~/.hermes/.env` (provider: `huggingface`, aliases: `hf`) |
| **Google / Gemini** | `GOOGLE_API_KEY` (або `GEMINI_API_KEY`) у `~/.hermes/.env` (provider: `gemini`) |
| **Google Gemini (OAuth)** | `hermes model` → “Google Gemini (OAuth)” (provider: `google-gemini-cli`, безкоштовний тариф, вхід у браузері PKCE) |
| **OpenAI API (direct)** | `OPENAI_API_KEY` у `~/.hermes/.env` (provider: `openai-api`, optional `OPENAI_BASE_URL`) |
| **Azure AI Foundry** | `hermes model` → “Azure AI Foundry” (provider: `azure-foundry`; використовує Azure OpenAI / Foundry endpoint і key) |
| **AWS Bedrock** | `hermes model` → “AWS Bedrock” (provider: `bedrock`; стандартний ланцюжок AWS credentials через boto3) |
| **NVIDIA Build** | `NVIDIA_API_KEY` у `~/.hermes/.env` (provider: `nvidia`; NIM‑хостовані моделі на build.nvidia.com) |
| **Ollama Cloud** | `hermes model` → “Ollama Cloud” (provider: `ollama-cloud`; хмарний Ollama API) |
| **Qwen OAuth** | `hermes model` → “Qwen OAuth” (provider: `qwen-oauth`; вхід у браузері PKCE) |
| **MiniMax OAuth** | `hermes model` → “MiniMax (OAuth)” (provider: `minimax-oauth`; вхід у браузері PKCE) |
| **StepFun** | `STEPFUN_API_KEY` у `~/.hermes/.env` (provider: `stepfun`) |
| **LM Studio** | `hermes model` → “LM Studio” (provider: `lmstudio`, optional `LM_API_KEY`) |
| **Custom Endpoint** | `hermes model` → вибери “Custom endpoint” (збережено у `config.yaml`) |

Для офіційного шляху з API‑key дивись спеціальний [Google Gemini guide](/guides/google-gemini).

:::tip Псевдонім ключа моделі
У секції конфігурації `model:` можна використовувати як `default:`, так і `model:` як назву ключа для ідентифікатора моделі. Обидва варіанти `model: { default: my-model }` і `model: { model: my-model }` працюють однаково.
:::
### Nous Portal

[Nous Portal](https://portal.nousresearch.com) — це уніфікований **gateway** підписки Nous Research і **рекомендований спосіб запуску Hermes Agent**. Один OAuth‑логін охоплює 300+ передових агентних моделей (Claude, GPT, Gemini, DeepSeek, Qwen, Kimi, GLM, MiniMax, Grok, …) плюс [Tool Gateway](/user-guide/features/tool-gateway) (веб‑пошук, генерація зображень, TTS, автоматизація браузера) плюс [Nous Chat](https://chat.nousresearch.com) — оплата здійснюється за твою підписку Nous, а не окремими обліковими записами постачальників.

```bash
hermes setup --portal     # fresh install — OAuth + provider + gateway in one command
hermes model              # existing install — pick "Nous Portal" from the list
hermes portal status      # inspect login + routing at any time
```

Ще немає підписки? Оформи її за адресою [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription).

**Для повних деталей:** дивись спеціальну [сторінку інтеграції Nous Portal](/integrations/nous-portal) (що входить у підписку, каталог моделей, усунення проблем) та покроковий посібник [Запуск Hermes Agent з Nous Portal](/guides/run-hermes-with-nous-portal).

**Ідентифікація клієнта.** Кожен запит до Portal від Hermes Agent містить тег `client=hermes-client-v<version>` (наприклад, `client=hermes-client-v0.13.0`), який автоматично синхронізується з твоїм встановленим релізом. Цей тег надсилається на всі шляхи Portal — основний цикл чату, допоміжні виклики, компресійний підсумовувач, веб‑видобуток — і дозволяє телеметрії на боці Portal розрізняти трафік Hermes від інших клієнтів. Ніяких налаштувань не потрібно; тег оновлюється автоматично, коли ти виконуєш `hermes update`.

**JWT‑автентифікація (автоматично).** Hermes надає перевагу scoped `inference:invoke` JWT для запитів до Portal, використовуючи шлях legacy opaque session‑key як запасний варіант. Ніяких конфігурацій не потрібно — облікові дані керуються OAuth‑потоком і оновлюються прозоро. Відкликані refresh‑токени ізолюються, щоб уникнути повторних атак.

:::info Codex Note
Постачальник OpenAI Codex автентифікується за допомогою коду пристрою (відкрий URL, введи код). Hermes зберігає отримані облікові дані у власному сховищі автентифікації під `~/.hermes/auth.json` і може імпортувати існуючі облікові дані Codex CLI з `~/.codex/auth.json`, якщо вони присутні. Інсталяція Codex CLI не потрібна.

Якщо оновлення токена завершується помилкою терміналу (HTTP 4xx, `invalid_grant`, відкликаний грант тощо), Hermes позначає refresh‑токен як недійсний і припиняє його повторне використання, щоб ти не бачив потік однакових помилок автентифікації. Наступний запит поверне повідомлення про повторну автентифікацію. Запусти `hermes auth add codex-oauth` (або `hermes model` → OpenAI Codex), щоб розпочати новий вхід за кодом пристрою; ізоляція зникає після успішного обміну.
:::

:::warning
Навіть при використанні Nous Portal, Codex або кастомного кінцевого пункту, деякі інструменти (vision, web summarization, MoA) використовують окрему «допоміжну» модель. За замовчуванням (`auxiliary.*.provider: "auto"`), Hermes направляє ці завдання до твоєї **головної чат‑моделі** — тієї ж моделі, яку ти вибрав у `hermes model`. Ти можеш перевизначити кожне завдання окремо, щоб направити його до дешевшої/швидшої моделі (наприклад, Gemini Flash на OpenRouter) — дивись [Auxiliary Models](/user-guide/configuration#auxiliary-models).
:::

:::tip Nous Tool Gateway
Платні підписники Nous Portal також отримують доступ до **[Tool Gateway](/user-guide/features/tool-gateway)** — веб‑пошук, генерація зображень, TTS та автоматизація браузера, що працюють через твою підписку. Додаткові API‑ключі не потрібні. При новій інсталяції `hermes setup --portal` виконує вхід, встановлює Nous як твого провайдера і вмикає шлюз в одній команді. Існуючі користувачі можуть увімкнути його через `hermes model` або per‑tool через `hermes tools`. Перевірити маршрутизацію у будь‑який момент можна за допомогою `hermes portal status`.
:::
### Дві команди для керування моделями

Hermes має **дві** команди для роботи з моделями, які служать різним цілям:

| Команда | Де запускати | Що робить |
|---------|---------------|-----------|
| **`hermes model`** | Твій термінал (поза будь‑якою сесією) | Повний майстер налаштування — додати провайдери, виконати OAuth, ввести API‑ключі, налаштувати кінцеві точки |
| **`/model`** | Усередині чат‑сесії Hermes | Швидке перемикання між **вже‑налаштованими** провайдерами та моделями |

Якщо ти намагаєшся переключитися на провайдера, який ще не налаштовано (наприклад, у тебе налаштовано лише OpenRouter, а ти хочеш використати Anthropic), потрібно використовувати `hermes model`, а не `/model`. Спершу вийди з сесії (`Ctrl+C` або `/quit`), запусти `hermes model`, завершити налаштування провайдера, а потім розпочни нову сесію.
### Anthropic (Native)

Використовуй моделі Claude безпосередньо через Anthropic API — без необхідності проксі OpenRouter. Підтримує три методи автентифікації:

:::caution Потрібні кредити «extra usage» Claude Max
Коли ти автентифікуєшся через `hermes model` → Anthropic OAuth (або через `hermes auth add anthropic --type oauth`), Hermes працює як Claude Code у твоєму обліковому записі Anthropic. **Це працює лише якщо ти маєш план Claude Max і придбав додаткові кредити «extra usage».** Базовий ліміт плану Max (використання, включене у Claude Code за замовчуванням) не споживається Hermes — споживаються лише додаткові/надлишкові кредити, які ти додав. Абоненти Claude Pro не можуть використовувати цей шлях.

Якщо у тебе немає Max + додаткових кредитів, використай `ANTHROPIC_API_KEY` — запити будуть оплачуватись за токеном відповідно до організації, що володіє цим ключем (стандартне ціноутворення API, незалежно від підписки Claude).
:::

```bash
# With an API key (pay-per-token)
export ANTHROPIC_API_KEY=***
hermes chat --provider anthropic --model claude-sonnet-4-6

# Preferred: authenticate through `hermes model`
# Hermes will use Claude Code's credential store directly when available
hermes model

# Manual override with a setup-token (fallback / legacy)
export ANTHROPIC_TOKEN=***  # setup-token or manual OAuth token
hermes chat --provider anthropic

# Auto-detect Claude Code credentials (if you already use Claude Code)
hermes chat --provider anthropic  # reads Claude Code credential files automatically
```

Коли ти обираєш Anthropic OAuth через `hermes model`, Hermes надає перевагу власному сховищу облікових даних Claude Code замість копіювання токену у `~/.hermes/.env`. Це дозволяє оновлюваним обліковим даним Claude залишатися оновлюваними.

Або встанови це назавжди:
```yaml
model:
  provider: "anthropic"
  default: "claude-sonnet-4-6"
```

:::tip Псевдоніми
`--provider claude` і `--provider claude-code` також працюють як скорочення для `--provider anthropic`.
:::
### GitHub Copilot

Hermes підтримує GitHub Copilot як провайдера першого класу з двома режимами:

**`copilot` — Direct Copilot API** (рекомендовано). Використовує твою підписку GitHub Copilot для доступу до GPT‑5.x, Claude, Gemini та інших моделей через Copilot API.

⟦HOLD_3⟩

**Варіанти автентифікації** (перевіряються у цьому порядку):

1. `COPILOT_GITHUB_TOKEN` — змінна середовища
2. `GH_TOKEN` — змінна середовища
3. `GITHUB_TOKEN` — змінна середовища
4. `gh auth token` — CLI‑запасний (фолбек) варіант

Якщо токен не знайдено, `hermes model` пропонує **OAuth device code login** — той самий процес, що використовується CLI Copilot та opencode.

:::warning Token types
Copilot API **не** підтримує класичні Personal Access Tokens (`ghp_*`). Підтримувані типи токенів:

| Тип | Префікс | Як отримати |
|------|--------|------------|
| OAuth token | `gho_` | `hermes model` → GitHub Copilot → Login with GitHub |
| Fine‑grained PAT | `github_pat_` | GitHub Settings → Developer settings → Fine‑grained tokens (потрібен дозвіл **Copilot Requests**) |
| GitHub App token | `ghu_` | Через встановлення GitHub App |
:::

:::info Copilot auth behavior in Hermes
Hermes надсилає підтримуваний токен GitHub (`gho_*`, `github_pat_*` або `ghu_*`) безпосередньо до `api.githubcopilot.com` і додає заголовки, специфічні для Copilot (`Editor-Version`, `Copilot-Integration-Id`, `Openai-Intent`, `x-initiator`).

При HTTP 401 Hermes тепер виконує одноразове відновлення облікових даних перед запасним (фолбек) варіантом:

1. Повторно отримати токен за звичайним ланцюжком пріоритету (`COPILOT_GITHUB_TOKEN` → `GH_TOKEN` → `GITHUB_TOKEN` → `gh auth token`)
2. Перебудувати спільний OpenAI‑клієнт з оновленими заголовками
3. Повторити запит один раз

Деякі старі проксі‑спільноти використовують потоки обміну `api.github.com/copilot_internal/v2/token`. Цей кінцевий пункт може бути недоступний для певних типів акаунтів (повертає 404). Тому Hermes залишає пряму автентифікацію токеном як основний шлях і покладається на оновлення облікових даних у runtime + повторний запит для надійності.
:::

**Маршрутизація API**: моделі GPT‑5+ (крім `gpt-5-mini`) автоматично використовують Responses API. Всі інші моделі (GPT‑4o, Claude, Gemini тощо) використовують Chat Completions. Моделі визначаються автоматично з живого каталогу Copilot.

**`copilot-acp` — Copilot ACP agent backend**. Запускає локальний Copilot CLI як підпроцес:

⟦HOLD_4⟩

**Постійна конфігурація:**
⟦HOLD_5⟩

| Змінна середовища | Опис |
|-------------------|------|
| `COPILOT_GITHUB_TOKEN` | Токен GitHub для Copilot API (перший пріоритет) |
| `HERMES_COPILOT_ACP_COMMAND` | Перевизначити шлях до бінарника Copilot CLI (за замовчуванням: `copilot`) |
| `HERMES_COPILOT_ACP_ARGS` | Перевизначити аргументи ACP (за замовчуванням: `--acp --stdio`) |
### First-Class API-Key Providers

Ці провайдери мають вбудовану підтримку з виділеними ідентифікаторами провайдерів. Встанови API‑ключ і використай `--provider` для вибору:

```bash
# NovitaAI Model API
hermes chat --provider novita --model moonshotai/kimi-k2.5
# Requires: NOVITA_API_KEY in ~/.hermes/.env

# z.ai / ZhipuAI GLM
hermes chat --provider zai --model glm-5
# Requires: GLM_API_KEY in ~/.hermes/.env

# Kimi / Moonshot AI (international: api.moonshot.ai)
hermes chat --provider kimi-coding --model kimi-for-coding
# Requires: KIMI_API_KEY in ~/.hermes/.env

# Kimi / Moonshot AI (China: api.moonshot.cn)
hermes chat --provider kimi-coding-cn --model kimi-k2.5
# Requires: KIMI_CN_API_KEY in ~/.hermes/.env

# MiniMax (global endpoint)
hermes chat --provider minimax --model MiniMax-M2.7
# Requires: MINIMAX_API_KEY in ~/.hermes/.env

# MiniMax (China endpoint)
hermes chat --provider minimax-cn --model MiniMax-M2.7
# Requires: MINIMAX_CN_API_KEY in ~/.hermes/.env

# Qwen Cloud / DashScope (Qwen models)
hermes chat --provider alibaba --model qwen3.5-plus
# Requires: DASHSCOPE_API_KEY in ~/.hermes/.env

# Xiaomi MiMo
hermes chat --provider xiaomi --model mimo-v2-pro
# Requires: XIAOMI_API_KEY in ~/.hermes/.env

# Tencent TokenHub (Hy3 Preview)
hermes chat --provider tencent-tokenhub --model hy3-preview
# Requires: TOKENHUB_API_KEY in ~/.hermes/.env

# Arcee AI (Trinity models)
hermes chat --provider arcee --model trinity-large-thinking
# Requires: ARCEEAI_API_KEY in ~/.hermes/.env

# GMI Cloud
# Use the exact model ID returned by GMI's /v1/models endpoint.
hermes chat --provider gmi --model zai-org/GLM-5.1-FP8
# Requires: GMI_API_KEY in ~/.hermes/.env
```

Або встанови провайдера назавжди у `config.yaml`:
```yaml
model:
  provider: "gmi"
  default: "zai-org/GLM-5.1-FP8"
```

Базові URL‑и можна перевизначити за допомогою змінних середовища `NOVITA_BASE_URL`, `GLM_BASE_URL`, `KIMI_BASE_URL`, `MINIMAX_BASE_URL`, `MINIMAX_CN_BASE_URL`, `DASHSCOPE_BASE_URL`, `XIAOMI_BASE_URL`, `GMI_BASE_URL` або `TOKENHUB_BASE_URL`.

:::note Z.AI Endpoint Auto-Detection
При використанні провайдера Z.AI / GLM Hermes автоматично опитує кілька кінцевих точок (глобальні, Китай, варіанти для кодування), щоб знайти ту, яка приймає твій API‑ключ. Не потрібно вручну встановлювати `GLM_BASE_URL` — робоча кінцева точка визначається та кешується автоматично.
:::
### xAI (Grok) — Responses API + Prompt Caching

xAI підключається через Responses API (`codex_responses` transport) для автоматичної підтримки розумових процесів у моделях Grok 4 — параметр `reasoning_effort` не потрібен, сервер розмірковує за замовчуванням. Встанови `XAI_API_KEY` у `~/.hermes/.env` і обери xAI у `hermes model`, або використай `grok` як скорочення в `/model grok-4-fast-reasoning`.

Користувачі SuperGrok та X Premium+ можуть увійти через браузерний OAuth замість використання API‑ключа — обери **xAI Grok OAuth (SuperGrok / Premium+)** у `hermes model`, або запусти `hermes auth add xai-oauth`. Той самий OAuth‑токен автоматично використовується інструментами прямого доступу до xAI (TTS, генерація зображень, генерація відео, транскрипція). Дивись [xAI Grok OAuth guide](../guides/xai-grok-oauth.md) для повного процесу — і якщо Hermes працює на віддаленому хості, також переглянь [OAuth over SSH / Remote Hosts](../guides/oauth-over-ssh.md) щодо необхідного тунелю `ssh -L`.

При використанні xAI як провайдера (будь‑яка базова URL, що містить `x.ai`), Hermes автоматично вмикає кешування підказок, додаючи заголовок `x-grok-conv-id` до кожного API‑запиту. Це маршрутизує запити до того самого сервера в межах однієї сесії розмови, дозволяючи інфраструктурі xAI повторно використовувати кешовані системні підказки та історію розмов.

Ніякої конфігурації не потрібно — кешування активується автоматично, коли виявлено endpoint xAI і доступний ідентифікатор сесії. Це зменшує затримку та вартість багатокрокових розмов.

xAI також надає спеціальний TTS endpoint (`/v1/tts`). Обери **xAI TTS** у `hermes tools` → Voice & TTS, або переглянь сторінку [Voice & TTS](../user-guide/features/tts.md#text-to-speech) для налаштувань.

**Відсторонення моделі xAI (15 травня 2026):** xAI припиняє підтримку `grok-4*`, `grok-3`, `grok-code-fast-1` та `grok-imagine-image-pro` 15 травня 2026 р. `hermes doctor` і `hermes chat` під час запуску виявляють будь‑яку конфігурацію, що ще вказує на відсторонену модель, і виводять рекомендовану заміну. Використай `hermes migrate xai` для одноразової перепису конфігурації — за замовчуванням виконується dry‑run, додай `--apply`, щоб записати зміни (автоматично створюється резервна копія `config.yaml.bak-pre-migrate-xai-*` з міткою часу).

```bash
hermes migrate xai          # preview replacements
hermes migrate xai --apply  # rewrite ~/.hermes/config.yaml in place
```

**Бекенд веб‑пошуку xAI.** Коли набір інструментів [Web Search](../user-guide/features/web-search.md) увімкнено, `web.backend: xai` маршрутизує пошук через хостований endpoint пошуку xAI, використовуючи той самий `XAI_API_KEY` / OAuth‑облікові дані. Додаткове налаштування не потрібне, якщо xAI вже сконфігуровано як провайдер.
### NovitaAI

[NovitaAI](https://novita.ai) — це AI‑нативна хмара для будівників і агентів. Її три продуктові лінії: Model API для понад 200 моделей, Agent Sandbox для створення та запуску AI‑агентів і GPU Cloud для масштабованих обчислень, всі доступні з однієї платформи.

```bash
# Use any available model
hermes chat --provider novita --model moonshotai/kimi-k2.5
# Requires: NOVITA_API_KEY in ~/.hermes/.env

# Short alias
hermes chat --provider novita-ai --model deepseek/deepseek-v3-0324
```

Або встановити це назавжди в `config.yaml`:
```yaml
model:
  provider: "novita"
  default: "moonshotai/kimi-k2.5"
  base_url: "https://api.novita.ai/openai/v1"
```

Отримай свій API‑ключ за адресою [novita.ai/settings/key-management](https://novita.ai/settings/key-management). Базовий URL можна перевизначити за допомогою `NOVITA_BASE_URL`.
### Ollama Cloud — Керовані моделі Ollama, OAuth + API‑ключ

[Ollama Cloud](https://ollama.com/cloud) розміщує той самий каталог відкритих моделей, що й локальна Ollama, але без вимоги GPU. Вибери її в `hermes model` як **Ollama Cloud**, встав свій API‑ключ з [ollama.com/settings/keys](https://ollama.com/settings/keys), і Hermes автоматично виявить доступні моделі.

```bash
hermes model
# → pick "Ollama Cloud"
# → paste your OLLAMA_API_KEY
# → select from discovered models (gpt-oss:120b, glm-4.6:cloud, qwen3-coder:480b-cloud, etc.)
```

Або `config.yaml` безпосередньо:
```yaml
model:
  provider: "ollama-cloud"
  default: "gpt-oss:120b"
```

Каталог моделей отримується динамічно з `ollama.com/v1/models` і кешується на одну годину. Нотація `model:tag` (наприклад `qwen3-coder:480b-cloud`) зберігається під час нормалізації — не використовуйте дефіси.

:::tip Ollama Cloud vs local Ollama
Обидва працюють за однаковим сумісним з OpenAI API. Cloud — це провайдер першого класу (`--provider ollama-cloud`, `OLLAMA_API_KEY`); локальна Ollama доступна через потік Custom Endpoint (базовий URL `http://localhost:11434/v1`, без ключа). Використовуй Ollama Cloud для великих моделей, які не вдається запустити локально; використовуйте локальну Ollama для приватності або офлайн‑роботи.
:::
### AWS Bedrock

Anthropic Claude, Amazon Nova, DeepSeek v3.2, Meta Llama 4 та інші моделі через AWS Bedrock. Використовує ланцюжок облікових даних AWS SDK (`boto3`) — без API‑ключа, лише стандартна автентифікація AWS.

```bash
# Simplest — named profile in ~/.aws/credentials
hermes chat --provider bedrock --model us.anthropic.claude-sonnet-4-6

# Or with explicit env vars
AWS_PROFILE=myprofile AWS_REGION=us-east-1 hermes chat --provider bedrock --model us.anthropic.claude-sonnet-4-6
```

Або назавжди у `config.yaml`:
```yaml
model:
  provider: "bedrock"
  default: "us.anthropic.claude-sonnet-4-6"
bedrock:
  region: "us-east-1"          # or set AWS_REGION
  # profile: "myprofile"       # or set AWS_PROFILE
  # discovery: true            # auto-discover region from IAM
  # guardrail:                 # optional Bedrock Guardrails
  #   guardrail_identifier: "your-guardrail-id"
  #   guardrail_version: "DRAFT"
```

Автентифікація використовує стандартний ланцюжок boto3: явні `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`, `AWS_PROFILE` з `~/.aws/credentials`, IAM‑роль на EC2/ECS/Lambda, IMDS або SSO. Змінна середовища не потрібна, якщо ти вже автентифікований за допомогою AWS CLI.

Bedrock використовує **Converse API** під капотом — запити перетворюються у модель‑агностичну форму Bedrock, тому одна і та ж конфігурація працює для моделей Claude, Nova, DeepSeek та Llama. Встанови `BEDROCK_BASE_URL` лише якщо викликаєш нестандартну регіональну кінцеву точку.

Дивись [AWS Bedrock guide](/guides/aws-bedrock) для покрокового налаштування IAM, вибору регіону та крос‑регіонального інференсу.
### Qwen Portal (OAuth)

Alibaba's Qwen Portal з браузерним входом OAuth. Вибери **Qwen OAuth (Portal)** у `hermes model`, увійди через браузер, і Hermes збереже токен оновлення.

```bash
hermes model
# → pick "Qwen OAuth (Portal)"
# → browser opens; sign in with your Alibaba account
# → confirm — credentials are saved to ~/.hermes/auth.json

hermes chat   # uses portal.qwen.ai/v1 endpoint
```

Або налаштуй `config.yaml`:
```yaml
model:
  provider: "qwen-oauth"
  default: "qwen3-coder-plus"
```

Встанови `HERMES_QWEN_BASE_URL` лише якщо кінцева точка порталу переміщується (за замовчуванням: `https://portal.qwen.ai/v1`).

:::tip Qwen OAuth vs Qwen Cloud (Alibaba DashScope)
`qwen-oauth` використовує орієнтований на споживача Qwen Portal з входом OAuth — ідеально для окремих користувачів. Провайдер `alibaba` використовує Qwen Cloud (Alibaba DashScope) з `DASHSCOPE_API_KEY` — ідеально для програмних/виробничих навантажень. Обидва маршрутизуються до моделей сімейства Qwen, але розташовані на різних кінцевих точках.
:::
### Alibaba Cloud (Coding Plan)

Якщо ти підписаний на **Coding Plan** від Alibaba (окремий тарифний SKU, відмінний від стандартного доступу до DashScope API), Hermes надає його як власного провайдера першого класу: `alibaba-coding-plan`. Кінцева точка: `https://coding-intl.dashscope.aliyuncs.com/v1`. Він сумісний з OpenAI, як і звичайний провайдер `alibaba`, але має інший базовий URL та інший механізм білінгу.

```yaml
model:
  provider: alibaba_coding     # alias for alibaba-coding-plan
  model: qwen3-coder-plus
```

Або з CLI:

```bash
hermes chat --provider alibaba_coding --model qwen3-coder-plus
```

`alibaba_coding` використовує той самий `DASHSCOPE_API_KEY`, який вже використовується у записі `alibaba` — окремий ключ не потрібен, лише інша ціль маршрутизації. Перш ніж цей провайдер був зареєстрований, користувачі, які вказували `provider: alibaba_coding` у `config.yaml`, тихо переходили до маршрутизації OpenRouter.
### MiniMax (OAuth)

MiniMax-M2.7 через браузерний OAuth‑вхід — ключ API не потрібен. Обери **MiniMax (OAuth)** у `hermes model`, увійди через браузер, і Hermes збереже access‑ та refresh‑токени. Під капотом використовується сумісна з Anthropic Messages кінцева точка (`/anthropic`).

```bash
hermes model
# → pick "MiniMax (OAuth)"
# → browser opens; sign in with your MiniMax account (global or CN region)
# → confirm — credentials are saved to ~/.hermes/auth.json

hermes chat   # uses api.minimax.io/anthropic endpoint
```

Або налаштуй `config.yaml`:
```yaml
model:
  provider: "minimax-oauth"
  default: "MiniMax-M2.7"
```

Підтримувані моделі: `MiniMax-M2.7` (основна) та `MiniMax-M2.7-highspeed` (встановлена як типова допоміжна модель). Шлях OAuth ігнорує `MINIMAX_API_KEY` / `MINIMAX_BASE_URL`.

:::tip MiniMax OAuth vs API key
`minimax-oauth` використовує споживчий портал MiniMax з OAuth‑входом — налаштування білінгу не потрібне. Провайдери `minimax` і `minimax-cn` використовують `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` — для програмного доступу. Дивись [MiniMax OAuth guide](/guides/minimax-oauth) для повного покрокового опису.
:::
### NVIDIA NIM

Nemotron та інші open‑source моделі через [build.nvidia.com](https://build.nvidia.com) (безкоштовний API‑ключ) або локальну кінцеву точку NIM.

```bash
# Cloud (build.nvidia.com)
hermes chat --provider nvidia --model nvidia/nemotron-3-super-120b-a12b
# Requires: NVIDIA_API_KEY in ~/.hermes/.env

# Local NIM endpoint — override base URL
NVIDIA_BASE_URL=http://localhost:8000/v1 hermes chat --provider nvidia --model nvidia/nemotron-3-super-120b-a12b
```

Або встанови це назавжди у `config.yaml`:
```yaml
model:
  provider: "nvidia"
  default: "nvidia/nemotron-3-super-120b-a12b"
```

:::tip Local NIM
Для розгортань on‑prem (DGX Spark, локальний GPU) встанови `NVIDIA_BASE_URL=http://localhost:8000/v1`. NIM надає той самий сумісний з OpenAI API чат‑комплішнс, що й build.nvidia.com, тому перехід між хмарою та локальним — це зміна однієї змінної середовища.
:::

Hermes автоматично додає заголовок NIM billing‑origin до кожного запиту до `build.nvidia.com` — налаштування не потрібні. Це маршрутизує споживання до правильного джерела у панелі білінгу NVIDIA.
### GMI Cloud

Відкриті та reasoning‑моделі через [GMI Cloud](https://www.gmicloud.ai/) — API, сумісний з OpenAI, автентифікація за API‑ключем.

```bash
# GMI Cloud
hermes chat --provider gmi --model deepseek-ai/DeepSeek-V3.2
# Requires: GMI_API_KEY in ~/.hermes/.env
```

Або встанови його назавжди у `config.yaml`:
```yaml
model:
  provider: "gmi"
  default: "deepseek-ai/DeepSeek-V3.2"
```

Базовий URL можна перевизначити за допомогою `GMI_BASE_URL` (за замовчуванням: `https://api.gmi-serving.com/v1`).
### StepFun

Моделі серії Step через [StepFun](https://platform.stepfun.com) — сумісний з API OpenAI, автентифікація за API‑ключем.

```bash
# StepFun
hermes chat --provider stepfun --model step-3-mini
# Requires: STEPFUN_API_KEY in ~/.hermes/.env
```

Або встанови його назавжди у `config.yaml`:
```yaml
model:
  provider: "stepfun"
  default: "step-3-mini"
```

Базовий URL можна перевизначити за допомогою `STEPFUN_BASE_URL` (за замовчуванням: `https://api.stepfun.com/v1`).
### Провайдери Inference від Hugging Face

[Провайдери Inference від Hugging Face](https://huggingface.co/docs/inference-providers) маршрутує до 20+ відкритих моделей через уніфіковану сумісну з OpenAI кінцеву точку (`router.huggingface.co/v1`). Запити автоматично перенаправляються до найшвидшого доступного бекенду (Groq, Together, SambaNova тощо) з автоматичним відкотом у разі збою.

```bash
# Use any available model
hermes chat --provider huggingface --model Qwen/Qwen3.5-397B-A17B
# Requires: HF_TOKEN in ~/.hermes/.env

# Short alias
hermes chat --provider hf --model deepseek-ai/DeepSeek-V3.2
```

Або встанови це назавжди у `config.yaml`:
```yaml
model:
  provider: "huggingface"
  default: "Qwen/Qwen3.5-397B-A17B"
```

Отримай свій токен на [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) — переконайся, що увімкнено дозвіл «Make calls to Inference Providers». Безкоштовний тариф включає ($0.10/місяць кредиту, без націнки на ставки провайдерів).

Ти можеш додавати суфікси маршрутизації до назв моделей: `:fastest` (за замовчуванням), `:cheapest` або `:provider_name`, щоб примусово використовувати конкретний бекенд.

Базову URL можна перевизначити за допомогою `HF_BASE_URL`.
### Google Gemini via OAuth (`google-gemini-cli`)

Провайдер `google-gemini-cli` використовує бекенд Google Cloud Code Assist — той самий API, який використовує власний інструмент Google `gemini-cli`. Це підтримує як **безкоштовний рівень** (щедра добова квота для особистих акаунтів), так і **платні рівні** (Standard/Enterprise через проєкт GCP).

**Швидкий старт:**

```bash
hermes model
# → pick "Google Gemini (OAuth)"
# → see policy warning, confirm
# → browser opens to accounts.google.com, sign in
# → done — Hermes auto-provisions your free tier on first request
```

Hermes постачається з **публічним** десктоп‑клієнтом OAuth `gemini-cli` від Google за замовчуванням — ті ж облікові дані, які Google включає у свій open‑source `gemini-cli`. Десктоп‑клієнти OAuth не є конфіденційними (PKCE забезпечує безпеку). Тобі не потрібно встановлювати `gemini-cli` або реєструвати власний OAuth‑клієнт GCP.

**Як працює автентифікація:**
- PKCE Authorization Code flow проти `accounts.google.com`
- Колбек браузера за `http://127.0.0.1:8085/oauth2callback` (з резервним портом, якщо зайнято)
- Токени зберігаються у `~/.hermes/auth/google_oauth.json` (chmod 0600, атомарний запис, міжпроцесний `fcntl`‑блок)
- Автоматичне оновлення за 60 с до закінчення терміну дії
- Безголові середовища (SSH, `HERMES_HEADLESS=1`) → резервний режим paste‑mode
- Дедуплікація оновлення в польоті — два одночасних запити не подвоюють оновлення
- `invalid_grant` (відкликаний refresh) → файл облікових даних стирається, користувач запитується повторно ввійти

**Як працює інференція:**
- Трафік надходить до `https://cloudcode-pa.googleapis.com/v1internal:generateContent` (або `:streamGenerateContent?alt=sse` для стрімінгу), НЕ до платного endpoint `v1beta/openai`
- Тіло запиту обгорнуте `{project, model, user_prompt_id, request}`
- OpenAI‑подібні `messages[]`, `tools[]`, `tool_choice` перетворюються у нативний формат Gemini `contents[]`, `tools[].functionDeclarations`, `toolConfig`
- Відповіді переводяться назад у форму OpenAI, тож решта Hermes працює без змін

**Рівні та ідентифікатори проєктів:**

| Твоя ситуація | Що робити |
|---|---|
| Особистий акаунт Google, потрібен безкоштовний рівень | Нічого — увійди, починай чат |
| Робочий простір / Standard / Enterprise акаунт | Встанови `HERMES_GEMINI_PROJECT_ID` або `GOOGLE_CLOUD_PROJECT` у ідентифікатор твого проєкту GCP |
| Організація, захищена VPC‑SC | Hermes виявляє `SECURITY_POLICY_VIOLATED` і автоматично примушує `standard-tier` |

Безкоштовний рівень автоматично створює проєкт, керований Google, при першому використанні. Налаштування GCP не потрібне.

**Моніторинг квоти:**

```
/gquota
```

Показує залишкову квоту Code Assist на модель у вигляді індикаторів прогресу:

```
Gemini Code Assist quota  (project: 123-abc)

  gemini-2.5-pro                      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░   85%
  gemini-2.5-flash [input]            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░   92%
```

:::warning Policy risk
Google вважає використання клієнта Gemini CLI OAuth у сторонньому програмному забезпеченні політичною порушенням. Деякі користувачі повідомляли про обмеження акаунтів. Для мінімального ризику рекомендовано використовувати власний API‑ключ через провайдер `gemini`. Hermes показує застереження заздалегідь і вимагає явного підтвердження перед початком OAuth.
:::

**Власний OAuth‑клієнт (необов’язково):**

Якщо ти хочеш зареєструвати свій власний Google OAuth‑клієнт — напр., щоб квота і згода були прив’язані до твого проєкту GCP — встанови:

```bash
HERMES_GEMINI_CLIENT_ID=your-client.apps.googleusercontent.com
HERMES_GEMINI_CLIENT_SECRET=...   # optional for Desktop clients
```

Зареєструй **Desktop app** OAuth‑клієнт у [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials) з увімкненою Generative Language API.
## Користувацькі та самостійно розгорнуті LLM‑провайдери

Hermes Agent працює з **будь‑яким API‑endpoint, сумісним з OpenAI**. Якщо сервер реалізує `/v1/chat/completions`, ти можеш вказати Hermes на нього. Це означає, що можна використовувати локальні моделі, сервери інференсу на GPU, маршрутизатори з кількома провайдерами або будь‑який сторонній API.
### General Setup

Три способи налаштувати власну кінцеву точку:

**Interactive setup (recommended):**
```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter: API base URL, API key, Model name
```

**Manual config (`config.yaml`):**
```yaml
# In ~/.hermes/config.yaml
model:
  default: your-model-name
  provider: custom
  base_url: http://localhost:8000/v1
  api_key: your-key-or-leave-empty-for-local
```

:::warning Legacy env vars
`LLM_MODEL` у `.env` **видалено** — `config.yaml` є єдиним джерелом правди для налаштувань моделі та кінцевої точки. `OPENAI_BASE_URL` все ще враховується, але **лише** для провайдера `openai-api` (він перевизначає кінцеву точку OpenAI для прямого доступу за API‑ключем). Для інших провайдерів і власних кінцевих точок використай `hermes model` або встанови `model.base_url` безпосередньо в `config.yaml`. Якщо у твоєму `.env` залишилися застарілі записи, вони автоматично очищуються під час наступного `hermes setup` або міграції конфігурації.
:::

Обидва підходи зберігаються в `config.yaml`, який є єдиним джерелом правди для моделі, провайдера та базового URL.
### Перемикання моделей за допомогою `/model`

:::warning hermes model vs /model
**`hermes model`** (запускається у твоєму терміналі, поза будь‑якою сесією чату) — це **повний майстер налаштування провайдера**. Використовуй його, щоб додати нових провайдерів, запустити OAuth‑потоки, ввести API‑ключі та налаштувати власні кінцеві точки.

**`/model`** (вводиться всередині активної сесії Hermes) може лише **перемикати між провайдерами та моделями, які вже налаштовані**. Він не може додавати нових провайдерів, запускати OAuth чи запитувати API‑ключі. Якщо ти налаштував лише одного провайдера (наприклад OpenRouter), `/model` покаже лише моделі цього провайдера.

**Щоб додати нового провайдера:** Вийди з сесії (`Ctrl+C` або `/quit`), запусти `hermes model`, налаштуй нового провайдера, а потім запусти нову сесію.
:::

Після того як у тебе буде налаштована хоча б одна власна кінцева точка, ти можеш перемикати моделі під час сесії:

```
/model custom:qwen-2.5          # Switch to a model on your custom endpoint
/model custom                    # Auto-detect the model from the endpoint
/model openrouter:claude-sonnet-4 # Switch back to a cloud provider
```

Якщо у тебе налаштовані **іменовані власні провайдери** (дивись нижче), використай трикратний синтаксис:

```
/model custom:local:qwen-2.5    # Use the "local" custom provider with model qwen-2.5
/model custom:work:llama3       # Use the "work" custom provider with llama3
```

При перемиканні провайдерів Hermes зберігає базовий URL та провайдера у конфігурації, тому зміна зберігається після перезапуску. При переході від власної кінцевої точки до вбудованого провайдера застарілий базовий URL автоматично очищується.

:::tip
`/model custom` (без назви моделі) запитує API `/models` твоєї кінцевої точки і автоматично обирає модель, якщо завантажена лише одна. Корисно для локальних серверів, що працюють з однією моделлю.
:::

Все нижче слідує цьому ж шаблону — просто заміни URL, ключ і назву моделі.

---
### Ollama — Локальні моделі, Zero Config

[Ollama](https://ollama.com/) запускає моделі з відкритими вагами локально за одну команду. Найкраще підходить для: швидких локальних експериментів, роботи з чутливими даними, офлайн‑використання. Підтримує виклик інструментів через сумісний з OpenAI API.

```bash
# Install and run a model
ollama pull qwen2.5-coder:32b
ollama serve   # Starts on port 11434
```

Потім налаштуй Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:11434/v1
# Skip API key (Ollama doesn't need one)
# Enter model name (e.g. qwen2.5-coder:32b)
```

Або налаштуй `config.yaml` безпосередньо:

```yaml
model:
  default: qwen2.5-coder:32b
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 64000   # See warning below
```

:::caution Ollama за замовчуванням має дуже низькі довжини контексту
Ollama **не** використовує повне контекстне вікно твоєї моделі за замовчуванням. Залежно від об’єму VRAM, типове значення таке:

| Доступна VRAM | Типовий контекст |
|----------------|------------------|
| Менше 24 ГБ | **4 096 токенів** |
| 24–48 ГБ | 32 768 токенів |
| 48+ ГБ | 256 000 токенів |

Hermes Agent потребує щонайменше **64 000 токенів** контексту для використання агентом з інструментами. Менші вікна відхиляються під час запуску, бо системний підказник, схеми інструментів і стан розмови потребують достатньо місця для надійних багатокрокових робочих процесів.

**Як збільшити його** (вибери один варіант):

```bash
# Option 1: Set server-wide via environment variable (recommended)
OLLAMA_CONTEXT_LENGTH=64000 ollama serve

# Option 2: For systemd-managed Ollama
sudo systemctl edit ollama.service
# Add: Environment="OLLAMA_CONTEXT_LENGTH=64000"
# Then: sudo systemctl daemon-reload && sudo systemctl restart ollama

# Option 3: Bake it into a custom model (persistent per-model)
echo -e "FROM qwen2.5-coder:32b\nPARAMETER num_ctx 64000" > Modelfile
ollama create qwen2.5-coder-64k -f Modelfile
```

**Не можна встановити довжину контексту через сумісний з OpenAI API** (`/v1/chat/completions`). Це треба налаштувати на боці сервера або через Modelfile. Це #1 причина плутанини під час інтеграції Ollama з інструментами, такими як Hermes.
:::

**Перевір, що контекст встановлено правильно:**

```bash
ollama ps
# Look at the CONTEXT column — it should show your configured value
```

:::tip
Список доступних моделей можна отримати командою `ollama list`. Завантаж будь‑яку модель з [бібліотеки Ollama](https://ollama.com/library) за допомогою `ollama pull <model>`. Ollama автоматично виконує перенесення на GPU — налаштування не потрібні для більшості конфігурацій.
:::

---
### vLLM — Високопродуктивний GPU Inference

[vLLM](https://docs.vllm.ai/) — це стандарт для продакшн‑сервісу LLM. Найкраще підходить для: максимальної пропускної здатності на GPU‑апаратурі, обслуговування великих моделей, безперервного батчінгу.

```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --max-model-len 65536 \
  --tensor-parallel-size 2 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

Потім налаштуй Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:8000/v1
# Skip API key (or enter one if you configured vLLM with --api-key)
# Enter model name: meta-llama/Llama-3.1-70B-Instruct
```

**Довжина контексту:** vLLM читає `max_position_embeddings` моделі за замовчуванням. Якщо це перевищує пам’ять GPU, виникає помилка і пропонує встановити `--max-model-len` нижче. Також можна використати `--max-model-len auto`, щоб автоматично знайти максимальну довжину, що вміщується. Встанови `--gpu-memory-utilization 0.95` (за замовчуванням 0.9), щоб втиснути більше контексту у VRAM.

**Виклик інструментів вимагає явних прапорців:**

| Прапорець | Призначення |
|-----------|-------------|
| `--enable-auto-tool-choice` | Потрібний для `tool_choice: "auto"` (за замовчуванням у Hermes) |
| `--tool-call-parser <name>` | Парсер формату виклику інструменту моделі |

Підтримувані парсери: `hermes` (Qwen 2.5, Hermes 2/3), `llama3_json` (Llama 3.x), `mistral`, `deepseek_v3`, `deepseek_v31`, `xlam`, `pythonic`. Без цих прапорців виклики інструментів не працюватимуть — модель виводитиме їх як текст.

:::tip
vLLM підтримує людсько‑читабельні розміри: `--max-model-len 64k` (нижня k = 1000, верхня K = 1024).
:::

---
### SGLang — Швидке обслуговування з RadixAttention

[SGLang](https://github.com/sgl-project/sglang) — альтернатива vLLM з RadixAttention для повторного використання KV‑кешу. Найкраще підходить для: багатократних діалогів (кешування префіксів), обмеженого декодування, структурованого виводу.

```bash
pip install "sglang[all]"
python -m sglang.launch_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --port 30000 \
  --context-length 65536 \
  --tp 2 \
  --tool-call-parser qwen
```

Потім налаштуй Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:30000/v1
# Enter model name: meta-llama/Llama-3.1-70B-Instruct
```

**Довжина контексту:** SGLang читає її з конфігурації моделі за замовчуванням. Використай `--context-length`, щоб перевизначити. Якщо потрібно перевищити оголошене максимальне значення моделі, встанови `SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1`.

**Виклик інструментів:** Використай `--tool-call-parser` з відповідним парсером для сімейства твоєї моделі: `qwen` (Qwen 2.5), `llama3`, `llama4`, `deepseekv3`, `mistral`, `glm`. Без цього прапорця виклики інструментів повертаються як простий текст.

:::caution SGLang за замовчуванням має максимум 128 токенів у виводі
Якщо відповіді здаються обрізаними, додай `max_tokens` до своїх запитів або встанови `--default-max-tokens` на сервері. За замовчуванням SGLang повертає лише 128 токенів у відповіді, якщо це не вказано в запиті.
:::

---
### llama.cpp / llama-server — CPU & Metal Inference

[llama.cpp](https://github.com/ggml-org/llama.cpp) запускає квантизовані моделі на CPU, Apple Silicon (Metal) та споживчих GPU. Найкраще підходить: запуск моделей без GPU у дата‑центрі, користувачі Mac, розгортання на краю.

```bash
# Build and start llama-server
cmake -B build && cmake --build build --config Release
./build/bin/llama-server \
  --jinja -fa \
  -c 64000 \
  -ngl 99 \
  -m models/qwen2.5-coder-32b-instruct-Q4_K_M.gguf \
  --port 8080 --host 0.0.0.0
```

**Довжина контексту (`-c`):** Останні збірки за замовчуванням мають `0`, що читає контекст навчання моделі з метаданих GGUF. Для моделей з контекстом навчання ≥ 128 k це може викликати OOM при спробі виділити весь KV‑кеш. Встанови `-c` явно принаймні 64 000 токенів для Hermes. Якщо використовуєш паралельні слоти (`-np`), загальний контекст ділиться між слотами — з `-c 64000 -np 4` кожен слот отримує лише 16 k, що нижче мінімуму Hermes на активну сесію.

Потім налаштуй Hermes, щоб вказати на нього:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:8080/v1
# Skip API key (local servers don't need one)
# Enter model name — or leave blank to auto-detect if only one model is loaded
```

Це зберігає кінцеву точку у `config.yaml`, тож вона зберігається між сесіями.

:::caution `--jinja` is required for tool calling
Без `--jinja` llama‑server ігнорує параметр `tools` повністю. Модель спробує викликати інструменти, записуючи JSON у текст відповіді, але Hermes не розпізнає це як виклик інструмента — ти побачиш сирий JSON типу `{"name": "web_search", ...}` у вигляді повідомлення замість реального пошуку.
:::

:::tip
Завантажуй GGUF‑моделі з [Hugging Face](https://huggingface.co/models?library=gguf). Квантизація Q4_K_M забезпечує найкращий баланс якості та використання пам’яті.
:::

---
### LM Studio — Desktop App with Local Models

[LM Studio](https://lmstudio.ai/) — це десктопний застосунок для запуску локальних моделей з графічним інтерфейсом. Найкраще підходить: користувачам, які віддають перевагу візуальному інтерфейсу, швидкому тестуванню моделей, розробникам на macOS/Windows/Linux.

Запусти сервер із застосунку LM Studio (вкладка **Developer** → **Start Server**), або використай CLI:

```bash
lms server start                        # Starts on port 1234
lms load qwen2.5-coder --context-length 64000
```

Потім налаштуй Hermes:

```bash
hermes model
# Select "LM Studio"
# Press Enter to use http://localhost:1234/v1
# Pick one of the discovered models
# If LM Studio server auth is enabled, enter LM_API_KEY when prompted
```

Hermes автоматично завантажить модель LM Studio з довжиною контексту 64 K.

Щоб змінити довжину контексту в LM Studio:

1. Натисни на іконку шестерні поруч із вибором моделі.
2. Встанови **“Context Length”** щонайменше 64000 для плавної роботи.
3. Перезавантаж модель, щоб зміна набрала сили.
4. Якщо твій комп’ютер не вміщає 64000, розглянь використання меншої моделі з більшою довжиною контексту.

Альтернативно, використай CLI: `lms load model-name --context-length 64000`

Можеш скористатися CLI, щоб оцінити, чи модель вміститься: `lms load model-name --context-length 64000 --estimate-only`

Щоб встановити постійні значення за замовчуванням для кожної моделі: вкладка **My Models** → іконка шестерні на моделі → встановити розмір контексту.
:::

**Tool calling:** Підтримується, починаючи з LM Studio 0.3.6. Моделі з вбудованим навчанням виклику інструментів (Qwen 2.5, Llama 3.x, Mistral, Hermes) автоматично розпізнаються і позначаються значком інструменту. Інші моделі використовують загальний запасний варіант, який може бути менш надійним.

---
### WSL2 Networking (Windows Users)

Оскільки Hermes Agent потребує Unix‑середовища, користувачі Windows запускають його всередині WSL2. Якщо твій сервер моделей (Ollama, LM Studio тощо) працює на **Windows‑хості**, потрібно подолати мережевий розрив — WSL2 використовує віртуальний мережевий адаптер зі своєю підмережею, тому `localhost` всередині WSL2 посилається на Linux‑VM, **не** на Windows‑хост.

:::tip Both in WSL2? No problem.
Якщо твій сервер моделей також працює всередині WSL2 (поширено для vLLM, SGLang та llama‑server), `localhost` працює, як очікувалося — вони ділять один мережевий простір. Пропусти цей розділ.
:::

#### Option 1: Mirrored Networking Mode (Recommended)

Доступно на **Windows 11 22H2+**, режим дзеркалювання робить `localhost` двосторонньо працездатним між Windows і WSL2 — найпростіше рішення.

1. Створи або відредагуй `%USERPROFILE%\.wslconfig` (наприклад, `C:\Users\YourName\.wslconfig`):
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

2. Перезапусти WSL з PowerShell:
   ```powershell
   wsl --shutdown
   ```

3. Відкрий знову термінал WSL2. `localhost` тепер досягає Windows‑служб:
   ```bash
   curl http://localhost:11434/v1/models   # Ollama on Windows — works
   ```

:::note Hyper‑V Firewall
На деяких збірках Windows 11 брандмауер Hyper‑V за замовчуванням блокує дзеркальні з’єднання. Якщо `localhost` все ще не працює після ввімкнення режиму дзеркалювання, виконай це в **Admin PowerShell**:
```powershell
Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow
```
:::

#### Option 2: Use the Windows Host IP (Windows 10 / older builds)

Якщо не можеш використовувати режим дзеркалювання, знайди IP‑адресу Windows‑хоста всередині WSL2 і використай її замість `localhost`:

```bash
# Get the Windows host IP (the default gateway of WSL2's virtual network)
ip route show | grep -i default | awk '{ print $3 }'
# Example output: 172.29.192.1
```

Використай цю IP‑адресу у конфігурації Hermes:

```yaml
model:
  default: qwen2.5-coder:32b
  provider: custom
  base_url: http://172.29.192.1:11434/v1   # Windows host IP, not localhost
```

:::tip Dynamic helper
IP‑адреса хоста може змінюватися після перезапуску WSL2. Ти можеш отримати її динамічно у своєму шеллі:
```bash
export WSL_HOST=$(ip route show | grep -i default | awk '{ print $3 }')
echo "Windows host at: $WSL_HOST"
curl http://$WSL_HOST:11434/v1/models   # Test Ollama
```

Або використай mDNS‑назву твоєї машини (вимагає `libnss‑mdns` у WSL2):
```bash
sudo apt install libnss-mdns
curl http://$(hostname).local:11434/v1/models
```
:::

#### Server Bind Address (Required for NAT Mode)

Якщо ти використовуєш **Option 2** (режим NAT з IP‑адресою хоста), сервер моделей у Windows має приймати з’єднання ззовні `127.0.0.1`. За замовчуванням більшість серверів слухають лише `localhost` — з’єднання WSL2 у режимі NAT надходять з іншої віртуальної підмережі і будуть відхилені. У режимі дзеркалювання `localhost` мапиться безпосередньо, тому прив’язка за замовчуванням `127.0.0.1` працює нормально.

| Server | Default bind | How to fix |
|--------|-------------|------------|
| **Ollama** | `127.0.0.1` | Встанови змінну середовища `OLLAMA_HOST=0.0.0.0` перед запуском Ollama (System Settings → Environment Variables у Windows або відредагуй службу Ollama) |
| **LM Studio** | `127.0.0.1` | Увімкни **"Serve on Network"** у вкладці Developer → Server settings |
| **llama‑server** | `127.0.0.1` | Додай `--host 0.0.0.0` до команди запуску |
| **vLLM** | `0.0.0.0` | Уже прив’язується до всіх інтерфейсів за замовчуванням |
| **SGLang** | `127.0.0.1` | Додай `--host 0.0.0.0` до команди запуску |

**Ollama on Windows (detailed):** Ollama працює як Windows‑служба. Щоб встановити `OLLAMA_HOST`:
1. Відкрий **System Properties** → **Environment Variables**
2. Додай нову **System variable**: `OLLAMA_HOST` = `0.0.0.0`
3. Перезапусти службу Ollama (або перезавантаж комп’ютер)

#### Windows Firewall

Windows Firewall розглядає WSL2 як окрему мережу (як у режимі NAT, так і в режимі дзеркалювання). Якщо з’єднання все ще не працюють після виконання вищезазначених кроків, додай правило брандмауера для порту твого серверу моделей:

```powershell
# Run in Admin PowerShell — replace PORT with your server's port
New-NetFirewallRule -DisplayName "Allow WSL2 to Model Server" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434
```

Типові порти: Ollama `11434`, vLLM `8000`, SGLang `30000`, llama‑server `8080`, LM Studio `1234`.

#### Quick Verification

Зсередини WSL2 перевір, чи можеш досягти свій сервер моделей:

```bash
# Replace URL with your server's address and port
curl http://localhost:11434/v1/models          # Mirrored mode
curl http://172.29.192.1:11434/v1/models       # NAT mode (use your actual host IP)
```

Якщо ти отримав JSON‑відповідь зі списком моделей, все готово. Використай той самий URL як `base_url` у конфігурації Hermes.
### Устранення проблем з локальними моделями

Ці проблеми впливають **на всі** локальні сервери інференсу при використанні Hermes.

#### «Connection refused» від WSL2 до сервера моделі, розгорнутого у Windows

Якщо ти запускаєш Hermes всередині WSL2, а сервер моделі працює на хості Windows, `http://localhost:<port>` не працюватиме у режимі NAT‑мережі WSL2 за замовчуванням. Дивись розділ [WSL2 Networking](#wsl2-networking-windows-users) вище для виправлення.

#### Виклики інструментів відображаються як текст замість виконання

Модель повертає щось на кшталт `{"name": "web_search", "arguments": {...}}` у вигляді повідомлення замість фактичного виклику інструменту.

**Причина:** Твій сервер не має ввімкненого виклику інструментів, або модель не підтримує це через реалізацію виклику інструментів у сервері.

| Server | Fix |
|--------|-----|
| **llama.cpp** | Додай `--jinja` до команди запуску |
| **vLLM** | Додай `--enable-auto-tool-choice --tool-call-parser hermes` |
| **SGLang** | Додай `--tool-call-parser qwen` (або відповідний парсер) |
| **Ollama** | Виклик інструментів ввімкнено за замовчуванням — переконайся, що твоя модель його підтримує (перевір за допомогою `ollama show model-name`) |
| **LM Studio** | Онови до 0.3.6+ і використай модель з вбудованою підтримкою інструментів |

#### Модель здається забуває контекст або дає несумісні відповіді

**Причина:** Вікно контексту занадто маленьке. Коли розмова перевищує ліміт контексту, більшість серверів тихо відкидає старі повідомлення. Системний промпт Hermes + схеми інструментів вже можуть займати 4k–8k токенів.

**Діагностика:**

```bash
# Check what Hermes thinks the context is
# Look at startup line: "Context limit: X tokens"

# Check your server's actual context
# Ollama: ollama ps (CONTEXT column)
# llama.cpp: curl http://localhost:8080/props | jq '.default_generation_settings.n_ctx'
# vLLM: check --max-model-len in startup args
```

**Виправлення:** Встанови контекст щонайменше **64 000 токенів** для використання агентом. Дивись розділ кожного сервера вище для конкретного прапорця.

#### «Context limit: 2048 tokens» під час запуску

Hermes автоматично визначає довжину контексту з ендпоінту `/v1/models` твого сервера. Якщо сервер повідомляє низьке значення (або не повідомляє його взагалі), Hermes використовує заявлений ліміт моделі, який може бути неправильним.

**Виправлення:** Вкажи його явно у `config.yaml`:

```yaml
model:
  default: your-model
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 64000
```

#### Відповіді обрізаються посеред речення

**Можливі причини:**
1. **Низький ліміт виводу (`max_tokens`) на сервері** — у SGLang за замовчуванням 128 токенів на відповідь. Встанови `--default-max-tokens` на сервері або налаштуй Hermes через `model.max_tokens` у `config.yaml`. Зауваж: `max_tokens` контролює лише довжину відповіді — це не те саме, що довжина історії розмови (це `context_length`).
2. **Вичерпання контексту** — модель заповнила своє вікно контексту. Збільш `model.context_length` або ввімкни [context compression](/user-guide/configuration#context-compression) у Hermes.
### LiteLLM Proxy — Multi-Provider Gateway

[LiteLLM](https://docs.litellm.ai/) — це проксі, сумісний з OpenAI, який об’єднує понад 100 провайдерів LLM за єдиним API. Найкраще підходить для: перемикання між провайдерами без зміни конфігурації, балансування навантаження, ланцюжків запасних (фолбек) варіантів, контролю бюджету.

```bash
# Install and start
pip install "litellm[proxy]"
litellm --model anthropic/claude-sonnet-4 --port 4000

# Or with a config file for multiple models:
litellm --config litellm_config.yaml --port 4000
```

Потім налаштуй Hermes за допомогою `hermes model` → Custom endpoint → `http://localhost:4000/v1`.

Приклад `litellm_config.yaml` із запасним (фолбек) варіантом:
```yaml
model_list:
  - model_name: "best"
    litellm_params:
      model: anthropic/claude-sonnet-4
      api_key: sk-ant-...
  - model_name: "best"
    litellm_params:
      model: openai/gpt-4o
      api_key: sk-...
router_settings:
  routing_strategy: "latency-based-routing"
```

---
### ClawRouter — Оптимізований за вартістю маршрутизація

[ClawRouter](https://github.com/BlockRunAI/ClawRouter) від BlockRunAI — це локальний проксі‑маршрутизатор, який автоматично обирає моделі залежно від складності запиту. Він класифікує запити за 14 вимірами та направляє їх до найдешевшої моделі, що може виконати завдання. Оплата здійснюється криптовалютою USDC (без API‑ключів).

```bash
# Install and start
npx @blockrun/clawrouter    # Starts on port 8402
```

Потім налаштуй Hermes за допомогою `hermes model` → Custom endpoint → `http://localhost:8402/v1` → ім'я моделі `blockrun/auto`.

Профілі маршрутизації:
| Профіль | Стратегія | Заощадження |
|---------|-----------|-------------|
| `blockrun/auto` | Збалансована якість/вартість | 74‑100% |
| `blockrun/eco` | Найдешевша можлива | 95‑100% |
| `blockrun/premium` | Найкращі моделі за якістю | 0% |
| `blockrun/free` | Тільки безкоштовні моделі | 100% |
| `blockrun/agentic` | Оптимізовано для використання інструментів | змінюється |

:::note
ClawRouter вимагає гаманця, фінансованого USDC, у мережі Base або Solana для оплати. Усі запити проходять через бекенд‑API BlockRun. Запусти `npx @blockrun/clawrouter doctor`, щоб перевірити статус гаманця.
:::
### Інші сумісні провайдери

Будь‑яка служба з API, сумісним з OpenAI, працює. Ось кілька популярних варіантів:

| Провайдер | Базовий URL | Примітки |
|----------|-------------|----------|
| [Together AI](https://together.ai) | `https://api.together.xyz/v1` | Cloud-hosted open models |
| [Groq](https://groq.com) | `https://api.groq.com/openai/v1` | Ultra-fast inference |
| [DeepSeek](https://deepseek.com) | `https://api.deepseek.com/v1` | DeepSeek models |
| [Fireworks AI](https://fireworks.ai) | `https://api.fireworks.ai/inference/v1` | Fast open model hosting |
| [GMI Cloud](https://www.gmicloud.ai/) | `https://api.gmi-serving.com/v1` | Managed OpenAI-compatible inference |
| [Cerebras](https://cerebras.ai) | `https://api.cerebras.ai/v1` | Wafer-scale chip inference |
| [Mistral AI](https://mistral.ai) | `https://api.mistral.ai/v1` | Mistral models |
| [OpenAI](https://openai.com) | `https://api.openai.com/v1` | Direct OpenAI access |
| [Azure OpenAI](https://azure.microsoft.com) | `https://YOUR.openai.azure.com/` | Enterprise OpenAI |
| [LocalAI](https://localai.io) | `http://localhost:8080/v1` | Self-hosted, multi-model |
| [Jan](https://jan.ai) | `http://localhost:1337/v1` | Desktop app with local models |

Налаштуй будь‑який з них за допомогою `hermes model` → **Custom endpoint**, або в `config.yaml`:

```yaml
model:
  default: meta-llama/Llama-3.1-70B-Instruct-Turbo
  provider: custom
  base_url: https://api.together.xyz/v1
  api_key: your-together-key
```

---
### Визначення довжини контексту

:::note Два налаштування, легко сплутати
**`context_length`** — це **загальне вікно контексту** — сумарний бюджет для вхідних *і* вихідних токенів (наприклад, 200 000 для Claude Opus 4.6). Hermes використовує його, щоб вирішити, коли стискати історію, і для валідації запитів API.

**`model.max_tokens`** — це **обмеження виводу** — максимальна кількість токенів, яку модель може згенерувати в *одній відповіді*. Це не має нічого спільного з тим, наскільки довгою може бути історія розмови. Стандартна назва `max_tokens` часто вводить в оману; у рідному API Anthropic її згодом перейменували на `max_output_tokens` для ясності.

Встанови `context_length`, коли авто‑виявлення помилково визначає розмір вікна.
Встанови `model.max_tokens` лише коли потрібно обмежити довжину окремих відповідей.
:::

Hermes використовує багатоджерельний ланцюжок розв’язання для визначення правильного вікна контексту вашої моделі та провайдера:

1. **Перевизначення конфігурації** — `model.context_length` у `config.yaml` (найвищий пріоритет)
2. **Custom provider per‑model** — `custom_providers[].models.<id>.context_length`
3. **Персистентний кеш** — раніше виявлені значення (зберігаються між перезапусками)
4. **Endpoint `/models`** — запит до API вашого сервера (локальні/кастомні endpoint’и)
5. **Anthropic `/v1/models`** — запит до API Anthropic за `max_input_tokens` (лише для користувачів з API‑ключем)
6. **OpenRouter API** — живі метадані моделі від OpenRouter
7. **Nous Portal** — суфікс‑збіги ID моделей Nous з метаданими OpenRouter
8. **[models.dev](https://models.dev)** — спільно підтримуваний реєстр з провайдер‑специфічними довжинами контексту для 3800+ моделей від 100+ провайдерів
9. **Запасні значення за замовчуванням** — широкі шаблони сімей моделей (128 K за замовчуванням)

Для більшості налаштувань це працює «з коробки». Система орієнтована на провайдера — одна і та сама модель може мати різні обмеження контексту залежно від того, хто її обслуговує (наприклад, `claude-opus-4.6` має 1 M на прямому Anthropic, але 128 K у GitHub Copilot).

Щоб явно задати довжину контексту, додай `context_length` у конфігурацію моделі:

```yaml
model:
  default: "qwen3.5:9b"
  base_url: "http://localhost:8080/v1"
  context_length: 131072  # tokens
```

Для кастомних endpoint’ів можна також встановити довжину контексту per‑model:

```yaml
custom_providers:
  - name: "My Local LLM"
    base_url: "http://localhost:11434/v1"
    models:
      qwen3.5:27b:
        context_length: 64000
      deepseek-r1:70b:
        context_length: 65536
```

`hermes model` запитає про довжину контексту під час налаштування кастомного endpoint’а. Залиш її порожньою для авто‑виявлення.

:::tip Коли встановлювати вручну
- Ти використовуєш Ollama з кастомним `num_ctx`, який нижчий за максимум моделі
- Хочеш обмежити контекст нижче максимуму моделі (наприклад, 8 k на 128 k моделі, щоб заощадити VRAM)
- Працюєш за проксі, який не розкриває `/v1/models`
:::

---
### Іменовані кастомні провайдери

Якщо ти працюєш з кількома кастомними endpoint'ами (наприклад, локальним dev‑сервером і віддаленим GPU‑сервером), їх можна визначити як іменовані кастомні провайдери у `config.yaml`:

```yaml
custom_providers:
  - name: local
    base_url: http://localhost:8080/v1
    # api_key omitted — Hermes uses "no-key-required" for keyless local servers
  - name: work
    base_url: https://gpu-server.internal.corp/v1
    key_env: CORP_API_KEY
    api_mode: chat_completions   # set explicitly by `hermes model` → Custom Endpoint wizard; auto-detection still happens as a fallback
  - name: anthropic-proxy
    base_url: https://proxy.example.com/anthropic
    key_env: ANTHROPIC_PROXY_KEY
    api_mode: anthropic_messages  # for Anthropic-compatible proxies
```

Деякі сумісні з OpenAI endpoint'и потребують специфічних для провайдера полів у тілі запиту. Додай мапу `extra_body` до відповідного кастомного провайдера, і Hermes об’єднає її з кожним запитом `chat‑completions` для цього endpoint'а:

```yaml
custom_providers:
  - name: gemma-local
    base_url: http://localhost:8080/v1
    model: google/gemma-4-31b-it
    extra_body:
      enable_thinking: true
      reasoning_effort: high
```

Використовуй структуру, яку документує твій сервер. Наприклад, розгортання vLLM Gemma та деякі endpoint'и NVIDIA NIM очікують `enable_thinking` у `chat_template_kwargs` замість верхнього рівня `extra_body`:

```yaml
extra_body:
  chat_template_kwargs:
    enable_thinking: true
```

Майстер `hermes model` → Custom Endpoint тепер явно запитує `api_mode` і зберігає твою відповідь у `config.yaml`. Автоматичне визначення за URL (наприклад, шляхи `/anthropic` → `anthropic_messages`) все ще працює як запасний (варіант), коли поле залишено порожнім.

**Нативна підтримка зору для моделей кастомних провайдерів.** Якщо твій кастомний endpoint надає модель з можливістю зору, яка не входить до `models.dev`, встанови `model.supports_vision: true`, щоб Hermes маршрутизував прикріплені зображення нативно (як частини `image_url`), а не через попередню обробку `vision_analyze`. Один перемикач — не потрібно також встановлювати `agent.image_input_mode: native`.

```yaml
model:
  provider: custom
  base_url: http://localhost:8080/v1
  default: qwen3.6-35b-a3b
  supports_vision: true   # send images natively; otherwise vision_analyze pre-describes them
```

Той самий ключ працює для моделей у кожному іменованому провайдері (`custom_providers[*].models[*].supports_vision`) і приймає стандартні булеві значення YAML (`true/false/yes/no/on/off/1/0`).

Перемикай їх під час сесії за допомогою трійного синтаксису:

```
/model custom:local:qwen-2.5       # Use the "local" endpoint with qwen-2.5
/model custom:work:llama3-70b      # Use the "work" endpoint with llama3-70b
/model custom:anthropic-proxy:claude-sonnet-4  # Use the proxy
```

Ти також можеш вибирати іменовані кастомні провайдери у інтерактивному меню `hermes model`.

---
### Cookbook: Together AI, Groq, Perplexity

Хмарні провайдери, зазначені в [Other Compatible Providers](#other-compatible-providers), всі підтримують діалект REST OpenAI, тому їх налаштовують однаково у розділі `custom_providers:`. Нижче наведено три готові рецепти. Кожен з них додається у `~/.hermes/config.yaml`, а відповідний API‑ключ розміщується у `~/.hermes/.env`.

#### Together AI

Хостить моделі з відкритою вагою (Llama, MiniMax, Gemma, DeepSeek, Qwen) за цінами, значно нижчими за офіційні API. Хороший варіант за замовчуванням для флоту з кількома моделями.

```yaml
# ~/.hermes/config.yaml
custom_providers:
  - name: together
    base_url: https://api.together.xyz/v1
    key_env: TOGETHER_API_KEY
    # api_mode: chat_completions  # default — no need to set

model:
  default: MiniMaxAI/MiniMax-M2.7   # or any model from together.ai/models
  provider: custom:together
```

```bash
# ~/.hermes/.env
TOGETHER_API_KEY=your-together-key
```

Перемикання моделей під час сесії:

```
/model custom:together:meta-llama/Llama-3.3-70B-Instruct-Turbo
/model custom:together:google/gemma-4-31b-it
/model custom:together:deepseek-ai/DeepSeek-V3
```

Endpoint `/v1/models` від Together працює, тому `hermes model` може автоматично виявляти доступні моделі.

#### Groq

Ультрашвидка інференція (~500 ток/с на Llama-3.3-70B). Малий каталог, але потужний для інтерактивного використання з чутливістю до затримки.

```yaml
# ~/.hermes/config.yaml
custom_providers:
  - name: groq
    base_url: https://api.groq.com/openai/v1
    key_env: GROQ_API_KEY

model:
  default: llama-3.3-70b-versatile
  provider: custom:groq
```

```bash
# ~/.hermes/.env
GROQ_API_KEY=your-groq-key
```

#### Perplexity

Корисний, коли потрібна модель, що виконує живий веб‑пошук і автоматично додає цитати. Жорстко обмежений у доступних моделях — перевір [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) для актуального списку.

```yaml
# ~/.hermes/config.yaml
custom_providers:
  - name: perplexity
    base_url: https://api.perplexity.ai
    key_env: PERPLEXITY_API_KEY

model:
  default: sonar
  provider: custom:perplexity
```

```bash
# ~/.hermes/.env
PERPLEXITY_API_KEY=your-perplexity-key
```

#### Кілька провайдерів в одному конфігу

Три рецепти можна комбінувати — використовуй їх усі разом і перемикайся між ними за допомогою `/model custom:<name>:<model>`:

```yaml
custom_providers:
  - name: together
    base_url: https://api.together.xyz/v1
    key_env: TOGETHER_API_KEY
  - name: groq
    base_url: https://api.groq.com/openai/v1
    key_env: GROQ_API_KEY
  - name: perplexity
    base_url: https://api.perplexity.ai
    key_env: PERPLEXITY_API_KEY

model:
  default: MiniMaxAI/MiniMax-M2.7
  provider: custom:together      # boot to Together; switch freely after
```

:::tip Troubleshooting
- `hermes doctor` не має виводити попереджень `Unknown provider` для будь‑яких з цих імен після виправлень валідатора CLI у #15083.
- Якщо endpoint `/v1/models` провайдера недоступний (найчастіше це Perplexity), `hermes model` збереже модель з попередженням замість жорсткого відхилення — див. #15136.
- Щоб повністю пропустити `custom_providers:` і використовувати простий `provider: custom` з змінною середовища `CUSTOM_BASE_URL`, див. #15103.
:::

---
### Вибір правильного налаштування

| Випадок використання | Рекомендовано |
|----------------------|---------------|
| **Просто хочеш, щоб працювало** | OpenRouter (за замовчуванням) або Nous Portal |
| **Локальні моделі, просте налаштування** | Ollama |
| **Production GPU serving** | vLLM або SGLang |
| **Mac / без GPU** | Ollama або llama.cpp |
| **Multi-provider routing** | LiteLLM Proxy або OpenRouter |
| **Cost optimization** | ClawRouter або OpenRouter з `sort: "price"` |
| **Maximum privacy** | Ollama, vLLM або llama.cpp (повністю локально) |
| **Enterprise / Azure** | Azure OpenAI з кастомним endpoint |
| **Chinese AI models** | z.ai (GLM), Kimi/Moonshot (`kimi-coding` або `kimi-coding-cn`), MiniMax, Xiaomi MiMo або Tencent TokenHub (провайдери першого класу) |

:::tip
Ти можеш переключатися між провайдерами в будь-який момент за допомогою `hermes model` — перезапуск не потрібен. Історія розмов, пам'ять і навички залишаються незалежно від того, який провайдер використовується.
:::
## Додаткові API‑ключі

| Функція | Провайдер | Змінна середовища |
|---------|----------|-------------------|
| Веб‑скрейпінг | [Firecrawl](https://firecrawl.dev/) | `FIRECRAWL_API_KEY`, `FIRECRAWL_API_URL` |
| Автоматизація браузера | [Browserbase](https://browserbase.com/) | `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` |
| Генерація зображень | [FAL](https://fal.ai/) | `FAL_KEY` |
| Преміум‑голоси TTS | [ElevenLabs](https://elevenlabs.io/) | `ELEVENLABS_API_KEY` |
| OpenAI TTS + транскрипція голосу | [OpenAI](https://platform.openai.com/api-keys) | `VOICE_TOOLS_OPENAI_KEY` |
| Mistral TTS + транскрипція голосу | [Mistral](https://console.mistral.ai/) | `MISTRAL_API_KEY` |
| Крос‑сесійне моделювання користувачів | [Honcho](https://honcho.dev/) | `HONCHO_API_KEY` |
| Семантична довготривала пам’ять | [Supermemory](https://supermemory.ai) | `SUPERMEMORY_API_KEY` |

### Самостійний хостинг Firecrawl

За замовчуванням Hermes використовує [хмарний API Firecrawl](https://firecrawl.dev/) для веб‑пошуку та скрейпінгу. Якщо ти хочеш запускати Firecrawl локально, можеш вказати Hermes на самостійно розгорнутий інстанс. Дивись файл [SELF_HOST.md](https://github.com/firecrawl/firecrawl/blob/main/SELF_HOST.md) у репозиторії Firecrawl для повних інструкцій з налаштування.

**Що ти отримуєш:** не потрібен API‑ключ, немає обмежень швидкості, немає вартості за сторінку, повна суверенність даних.

**Що втрачаєш:** хмарна версія використовує власний «Fire‑engine» Firecrawl для просунутого обходу анти‑бот захисту (Cloudflare, CAPTCHA, ротація IP). Самостійно розгорнута версія працює на базовому `fetch` + Playwright, тому деякі захищені сайти можуть не працювати. Пошук здійснюється через DuckDuckGo замість Google.

**Налаштування:**

1. Клонуй і запусти Docker‑стек Firecrawl (5 контейнерів: API, Playwright, Redis, RabbitMQ, PostgreSQL — потрібно ~4‑8 ГБ RAM):
   ```bash
   git clone https://github.com/firecrawl/firecrawl
   cd firecrawl
   # In .env, set: USE_DB_AUTHENTICATION=false, HOST=0.0.0.0, PORT=3002
   docker compose up -d
   ```

2. Вкажи Hermes на свій інстанс (API‑ключ не потрібен):
   ```bash
   hermes config set FIRECRAWL_API_URL http://localhost:3002
   ```

Ти також можеш задати і `FIRECRAWL_API_KEY`, і `FIRECRAWL_API_URL`, якщо твій самостійно розгорнутий інстанс має ввімкнену автентифікацію.
## OpenRouter Provider Routing

При використанні OpenRouter ти можеш керувати тим, як запити маршрутизуються між провайдерами. Додай розділ `provider_routing` у `~/.hermes/config.yaml`:

```yaml
provider_routing:
  sort: "throughput"          # "price" (default), "throughput", or "latency"
  # only: ["anthropic"]      # Only use these providers
  # ignore: ["deepinfra"]    # Skip these providers
  # order: ["anthropic", "google"]  # Try providers in this order
  # require_parameters: true  # Only use providers that support all request params
  # data_collection: "deny"   # Exclude providers that may store/train on data
```

**Швидкі клавіші:** Додай `:nitro` до будь‑якої назви моделі для сортування за пропускною здатністю (наприклад, `anthropic/claude-sonnet-4:nitro`), або `:floor` для сортування за ціною.
## OpenRouter Pareto Code Router

OpenRouter постачається з експериментальним роутером моделей кодування `openrouter/pareto-code`, який автоматично направляє запити до найдешевшої моделі, що відповідає бар’єру якості кодування (оцінюється за допомогою [Artificial Analysis](https://artificialanalysis.ai/)). Обери цю модель і налаштуй параметр `min_coding_score` у `~/.hermes/config.yaml`:

```yaml
model:
  provider: openrouter
  model: openrouter/pareto-code

openrouter:
  min_coding_score: 0.65   # 0.0–1.0; higher = stronger (more expensive) coders. Default 0.65.
```

Нотатки:

- `min_coding_score` **надсилається** лише коли `model.model` дорівнює `openrouter/pareto-code`. Для будь‑якої іншої моделі це значення не має ефекту.
- Встанови порожній рядок (або видали рядок), щоб дозволити OpenRouter вибрати найсильнішого доступного кодувальника — це задокументована поведінка, коли блок плагінів пропущено.
- Вибір детермінований за оцінкою на даний день, проте фактична модель може змінитися, коли фронт Парето зсувається (нові моделі, оновлення бенчмарків).
- Дивись повну документацію роутера OpenRouter у [Pareto Router docs](https://openrouter.ai/docs/guides/routing/routers/pareto-router).
- Щоб використати роутер Pareto Code для конкретного **додаткового завдання** (компресія, візія тощо) замість основного агента, встанови `extra_body.plugins` у цьому завданні — дивись [Auxiliary Models → OpenRouter routing & Pareto Code for auxiliary tasks](/user-guide/configuration#openrouter-routing--pareto-code-for-auxiliary-tasks).
## Запасний (варіант) провайдери

Налаштуй ланцюжок резервних провайдерів, які Hermes пробує у порядку, коли основна модель не працює (обмеження швидкості, помилки сервера, помилки автентифікації). Канонічний формат — це список верхнього рівня `fallback_providers:`:

```yaml
fallback_providers:
  - provider: openrouter
    model: anthropic/claude-sonnet-4
  - provider: anthropic
    model: claude-sonnet-4
    # base_url: http://localhost:8000/v1    # optional, for custom endpoints
    # api_mode: chat_completions           # optional override
```

Застарілий словник `fallback_model:` з однією парою все ще приймається для зворотної сумісності:

```yaml
fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
```

Після активації запасний (варіант) провайдер змінює модель і провайдера під час сесії без втрати розмови. Ланцюжок перебирається елемент за елементом; активація відбувається один раз за сесію.

Підтримувані провайдери: `openrouter`, `nous`, `novita`, `openai-codex`, `copilot`, `copilot-acp`, `anthropic`, `gemini`, `google-gemini-cli`, `qwen-oauth`, `huggingface`, `zai`, `kimi-coding`, `kimi-coding-cn`, `minimax`, `minimax-cn`, `minimax-oauth`, `deepseek`, `nvidia`, `xai`, `xai-oauth`, `ollama-cloud`, `bedrock`, `azure-foundry`, `opencode-zen`, `opencode-go`, `kilocode`, `xiaomi`, `arcee`, `gmi`, `stepfun`, `lmstudio`, `alibaba`, `alibaba-coding-plan`, `tencent-tokenhub`, `custom`.

:::tip
Запасний (варіант) провайдер налаштовується виключно через `config.yaml` — або інтерактивно за допомогою `hermes fallback`. Для повних деталей про те, коли він спрацьовує, як просувається ланцюжок і як взаємодіє з допоміжними завданнями та делегуванням, дивись [Fallback Providers](/user-guide/features/fallback-providers).
:::
## Дивись також

- [Configuration](/user-guide/configuration) — Загальна конфігурація (структура каталогів, пріоритетність конфігурації, бекенди терміналу, пам'ять, стискання та інше)
- [Environment Variables](/reference/environment-variables) — Повний довідник усіх змінних середовища