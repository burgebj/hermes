---
title: "провайдеры ИИ"
sidebar_label: "AI Providers"
sidebar_position: 1
---

# Провайдеры ИИ

Эта страница описывает настройку провайдеров инференса для Hermes Agent — от облачных API, таких как OpenRouter и Anthropic, до саморазмещённых конечных точек, таких как Ollama и vLLM, а также продвинутых конфигураций маршрутизации и запасных (fallback) вариантов. Для использования Hermes необходимо настроить как минимум один провайдер.
## Провайдеры инференса

Тебе нужен хотя бы один способ подключиться к LLM. Используй `hermes model` для переключения провайдеров и моделей интерактивно, либо настрой напрямую:

| Провайдер | Настройка |
|----------|-----------|
| **Nous Portal** | `hermes model` (OAuth, подписка) |
| **OpenAI Codex** | `hermes model` (OAuth ChatGPT, использует модели Codex) |
| **GitHub Copilot** | `hermes model` (OAuth device code flow, `COPILOT_GITHUB_TOKEN`, `GH_TOKEN` или `gh auth token`) |
| **GitHub Copilot ACP** | `hermes model` (запускает локальный `copilot --acp --stdio`) |
| **Anthropic** | `hermes model` (Claude Max + дополнительные кредиты через OAuth; также поддерживает API‑ключ Anthropic или токен‑настройку — см. примечание ниже) |
| **OpenRouter** | `OPENROUTER_API_KEY` в `~/.hermes/.env` |
| **NovitaAI** | `NOVITA_API_KEY` в `~/.hermes/.env` (provider: `novita`, 200+ моделей, Model API, Agent Sandbox, GPU Cloud) |
| **z.ai / GLM** | `GLM_API_KEY` в `~/.hermes/.env` (provider: `zai`) |
| **Kimi / Moonshot** | `KIMI_API_KEY` в `~/.hermes/.env` (provider: `kimi-coding`) |
| **Kimi / Moonshot (China)** | `KIMI_CN_API_KEY` в `~/.hermes/.env` (provider: `kimi-coding-cn`; aliases: `kimi-cn`, `moonshot-cn`) |
| **Arcee AI** | `ARCEEAI_API_KEY` в `~/.hermes/.env` (provider: `arcee`; aliases: `arcee-ai`, `arceeai`) |
| **GMI Cloud** | `GMI_API_KEY` в `~/.hermes/.env` (provider: `gmi`; aliases: `gmi-cloud`, `gmicloud`) |
| **MiniMax** | `MINIMAX_API_KEY` в `~/.hermes/.env` (provider: `minimax`) |
| **MiniMax China** | `MINIMAX_CN_API_KEY` в `~/.hermes/.env` (provider: `minimax-cn`) |
| **xAI (Grok) — Responses API** | `XAI_API_KEY` в `~/.hermes/.env` (provider: `xai`) |
| **xAI Grok OAuth (SuperGrok)** | `hermes model` → "xAI Grok OAuth (SuperGrok / Premium+)" — вход через браузер, без API‑ключа. См. [руководство](../guides/xai-grok-oauth.md) |
| **Qwen Cloud (Alibaba DashScope)** | `DASHSCOPE_API_KEY` в `~/.hermes/.env` (provider: `alibaba`) |
| **Alibaba Cloud (Coding Plan)** | `DASHSCOPE_API_KEY` (provider: `alibaba-coding-plan`, alias: `alibaba_coding`) — отдельный SKU биллинга, иной endpoint |
| **Kilo Code** | `KILOCODE_API_KEY` в `~/.hermes/.env` (provider: `kilocode`) |
| **Xiaomi MiMo** | `XIAOMI_API_KEY` в `~/.hermes/.env` (provider: `xiaomi`, aliases: `mimo`, `xiaomi-mimo`) |
| **Tencent TokenHub** | `TOKENHUB_API_KEY` в `~/.hermes/.env` (provider: `tencent-tokenhub`, aliases: `tencent`, `tokenhub`, `tencentmaas`) |
| **OpenCode Zen** | `OPENCODE_ZEN_API_KEY` в `~/.hermes/.env` (provider: `opencode-zen`) |
| **OpenCode Go** | `OPENCODE_GO_API_KEY` в `~/.hermes/.env` (provider: `opencode-go`) |
| **DeepSeek** | `DEEPSEEK_API_KEY` в `~/.hermes/.env` (provider: `deepseek`) |
| **Hugging Face** | `HF_TOKEN` в `~/.hermes/.env` (provider: `huggingface`, aliases: `hf`) |
| **Google / Gemini** | `GOOGLE_API_KEY` (или `GEMINI_API_KEY`) в `~/.hermes/.env` (provider: `gemini`) |
| **Google Gemini (OAuth)** | `hermes model` → "Google Gemini (OAuth)" (provider: `google-gemini-cli`, поддерживается бесплатный тариф, вход через браузер PKCE) |
| **OpenAI API (direct)** | `OPENAI_API_KEY` в `~/.hermes/.env` (provider: `openai-api`, опционально `OPENAI_BASE_URL`) |
| **Azure AI Foundry** | `hermes model` → "Azure AI Foundry" (provider: `azure-foundry`; использует endpoint и ключ Azure OpenAI / Foundry) |
| **AWS Bedrock** | `hermes model` → "AWS Bedrock" (provider: `bedrock`; стандартная цепочка AWS‑учётных данных через boto3) |
| **NVIDIA Build** | `NVIDIA_API_KEY` в `~/.hermes/.env` (provider: `nvidia`; модели, размещённые на build.nvidia.com) |
| **Ollama Cloud** | `hermes model` → "Ollama Cloud" (provider: `ollama-cloud`; облачный Ollama API) |
| **Qwen OAuth** | `hermes model` → "Qwen OAuth" (provider: `qwen-oauth`; вход через браузер PKCE) |
| **MiniMax OAuth** | `hermes model` → "MiniMax (OAuth)" (provider: `minimax-oauth`; вход через браузер PKCE) |
| **StepFun** | `STEPFUN_API_KEY` в `~/.hermes/.env` (provider: `stepfun`) |
| **LM Studio** | `hermes model` → "LM Studio" (provider: `lmstudio`, опционально `LM_API_KEY`) |
| **Custom Endpoint** | `hermes model` → выбрать "Custom endpoint" (сохраняется в `config.yaml`) |

Для официального пути с API‑ключом смотри отдельный [Google Gemini guide](/guides/google-gemini).

:::tip Псевдоним ключа модели
В секции конфигурации `model:` можно использовать либо `default:`, либо `model:` в качестве имени ключа для идентификатора модели. Оба варианта `model: { default: my-model }` и `model: { model: my-model }` работают одинаково.
:::
### Nous Portal

[Nous Portal](https://portal.nousresearch.com) — единый **gateway** подписки Nous Research и **рекомендованный способ запуска Hermes Agent**. Один вход через OAuth покрывает более 300 передовых агентных моделей (Claude, GPT, Gemini, DeepSeek, Qwen, Kimi, GLM, MiniMax, Grok, …) плюс [Tool Gateway](/user-guide/features/tool-gateway) (веб‑поиск, генерация изображений, TTS, автоматизация браузера) плюс [Nous Chat](https://chat.nousresearch.com) — списывается с твоей подписки Nous, а не с отдельных аккаунтов провайдеров.

```bash
hermes setup --portal     # fresh install — OAuth + provider + gateway in one command
hermes model              # existing install — pick "Nous Portal" from the list
hermes portal status      # inspect login + routing at any time
```

Ещё нет подписки? Оформи её на [portal.nousresearch.com/manage-subscription](https://portal.nousresearch.com/manage-subscription).

**Для полной информации:** смотри отдельную [страницу интеграции Nous Portal](/integrations/nous-portal) (что входит в подписку, каталог моделей, устранение неполадок) и пошаговое руководство [Запуск Hermes Agent через Nous Portal](/guides/run-hermes-with-nous-portal).

**Идентификация клиента.** Каждый запрос к Portal от Hermes Agent содержит тег `client=hermes-client-v<version>` (например `client=hermes-client-v0.13.0`), автоматически согласованный с установленной у тебя версией. Тег отправляется по всем путям Portal — основной цикл чата, вспомогательные вызовы, компресс‑суммаризатор, веб‑извлечение — и позволяет телеметрии на стороне Portal различать трафик Hermes от других клиентов. Настройка не требуется; тег обновляется автоматически при выполнении `hermes update`.

**JWT‑аутентификация (автоматически).** Hermes предпочитает scoped `inference:invoke` JWT для запросов к Portal, используя устаревший путь opaque session‑key как запасный вариант. Конфигурация не нужна — учётные данные управляются OAuth‑процессом и вращаются прозрачно. Отозванные токены обновления помещаются в карантин, чтобы избежать повторных запросов.

:::info Codex Note
Провайдер OpenAI Codex аутентифицируется через код устройства (открыть URL, ввести код). Hermes сохраняет полученные учётные данные в собственном хранилище auth под `~/.hermes/auth.json` и может импортировать существующие учётные данные Codex CLI из `~/.codex/auth.json`, если они есть. Установка Codex CLI не требуется.

Если обновление токена завершается ошибкой терминала (HTTP 4xx, `invalid_grant`, отозванный грант и т.п.), Hermes помечает токен обновления как недействительный и прекращает его повторное использование, чтобы ты не видел поток одинаковых ошибок аутентификации. При следующем запросе будет выведено типизированное сообщение о повторной аутентификации. Выполни `hermes auth add codex-oauth` (или `hermes model` → OpenAI Codex), чтобы начать новый вход по коду устройства; карантин будет снят после следующего успешного обмена.
:::

:::warning
Даже при использовании Nous Portal, Codex или собственного эндпоинта, некоторые инструменты (vision, web summarization, MoA) используют отдельную «вспомогательную» модель. По умолчанию (`auxiliary.*.provider: "auto"`), Hermes направляет эти задачи к твоей **основной модели чата** — той же модели, которую ты выбрал в `hermes model`. Ты можешь переопределить каждую задачу отдельно, направив её к более дешёвой/быстрой модели (например Gemini Flash на OpenRouter) — смотри [Auxiliary Models](/user-guide/configuration#auxiliary-models).
:::

:::tip Nous Tool Gateway
Платные подписчики Nous Portal также получают доступ к **[Tool Gateway](/user-guide/features/tool-gateway)** — веб‑поиск, генерация изображений, TTS и автоматизация браузера через твою подписку. Дополнительные API‑ключи не нужны. При свежей установке `hermes setup --portal` выполнит вход, установит Nous в качестве провайдера и включит gateway одной командой. Существующие пользователи могут включить его через `hermes model` или по отдельному инструменту через `hermes tools`. Проверить маршрутизацию в любой момент можно с помощью `hermes portal status`.
:::
### Две команды для управления моделями

Hermes имеет **две** команды моделей, которые служат разным целям:

| Command | Where to run | What it does |
|---------|-------------|--------------|
| **`hermes model`** | Your terminal (outside any session) | Full setup wizard — add providers, run OAuth, enter API keys, configure endpoints |
| **`/model`** | Inside a Hermes chat session | Quick switch between **already-configured** providers and models |

Если ты пытаешься переключиться на провайдера, который ещё не настроен (например, у тебя настроен только OpenRouter, а ты хочешь использовать Anthropic), тебе нужна команда `hermes model`, а не `/model`. Сначала выйди из сессии (`Ctrl+C` или `/quit`), запусти `hermes model`, завершите настройку провайдера, затем начни новую сессию.
### Anthropic (Native)

Используй модели Claude напрямую через API Anthropic — без прокси OpenRouter. Поддерживает три метода аутентификации:

:::caution Требуются кредиты «extra usage» Claude Max
Когда ты аутентифицируешься через `hermes model` → Anthropic OAuth (или через `hermes auth add anthropic --type oauth`), Hermes работает как Claude Code от имени твоего аккаунта Anthropic. **Это работает только если у тебя план Claude Max и ты приобрёл кредиты «extra usage».** Базовое ограничение плана Max (использование, включённое в Claude Code по умолчанию) не расходуется Hermes — расходуются только добавленные тобой дополнительные/переполнительные кредиты. Подписчики Claude Pro не могут использовать этот путь.

Если у тебя нет Max + дополнительных кредитов, используй `ANTHROPIC_API_KEY` — запросы оплачиваются по модели «pay‑per‑token» в организации, к которой привязан ключ (стандартные цены API, независимо от подписки Claude).
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

Когда ты выбираешь Anthropic OAuth через `hermes model`, Hermes отдаёт предпочтение собственному хранилищу учётных данных Claude Code вместо копирования токена в `~/.hermes/.env`. Это сохраняет возможность обновления учётных данных Claude.

Или установи навсегда:
```yaml
model:
  provider: "anthropic"
  default: "claude-sonnet-4-6"
```

:::tip Aliases
`--provider claude` и `--provider claude-code` также работают как сокращения для `--provider anthropic`.
:::
### GitHub Copilot

Hermes поддерживает GitHub Copilot как провайдера первого уровня с двумя режимами:

**`copilot` — Direct Copilot API** (рекомендовано). Использует твою подписку GitHub Copilot для доступа к GPT‑5.x, Claude, Gemini и другим моделям через Copilot API.

```bash
hermes chat --provider copilot --model gpt-5.4
```

**Варианты аутентификации** (проверяются в указанном порядке):

1. переменная окружения `COPILOT_GITHUB_TOKEN`
2. переменная окружения `GH_TOKEN`
3. переменная окружения `GITHUB_TOKEN`
4. резервный вариант CLI `gh auth token`

Если токен не найден, `hermes model` предлагает **вход по коду устройства OAuth** — тот же поток, что используется CLI Copilot и opencode.

:::warning Token types
Copilot API **не** поддерживает классические Personal Access Tokens (`ghp_*`). Поддерживаемые типы токенов:

| Тип | Префикс | Как получить |
|------|--------|------------|
| OAuth‑токен | `gho_` | `hermes model` → GitHub Copilot → Login with GitHub |
| Тонко‑гранулированный PAT | `github_pat_` | GitHub Settings → Developer settings → Fine-grained tokens (нужен доступ **Copilot Requests**) |
| Токен GitHub App | `ghu_` | Через установку GitHub App |
:::

:::info Copilot auth behavior in Hermes
Hermes отправляет поддерживаемый токен GitHub (`gho_*`, `github_pat_*` или `ghu_*`) напрямую на `api.githubcopilot.com` и добавляет заголовки, специфичные для Copilot (`Editor-Version`, `Copilot-Integration-Id`, `Openai-Intent`, `x-initiator`).

При HTTP 401 Hermes теперь выполняет одноразовое восстановление учётных данных перед резервным вариантом:

1. Повторно разрешает токен по обычной цепочке приоритетов (`COPILOT_GITHUB_TOKEN` → `GH_TOKEN` → `GITHUB_TOKEN` → `gh auth token`)
2. Пересобирает общий клиент OpenAI с обновлёнными заголовками
3. Один раз повторяет запрос

Некоторые старые прокси‑сообщества используют поток обмена `api.github.com/copilot_internal/v2/token`. Этот эндпоинт может быть недоступен для некоторых типов аккаунтов (возвращает 404). Поэтому Hermes оставляет прямую аутентификацию токеном в качестве основного пути и полагается на обновление учётных данных в runtime + повторный запрос для надёжности.
:::

**Маршрутизация API**: модели GPT‑5+ (кроме `gpt-5-mini`) автоматически используют Responses API. Все остальные модели (GPT‑4o, Claude, Gemini и т.д.) используют Chat Completions. Модели автоматически определяются из живого каталога Copilot.

**`copilot-acp` — Copilot ACP agent backend**. Запускает локальный Copilot CLI как подпроцесс:

```bash
hermes chat --provider copilot-acp --model copilot-acp
# Requires the GitHub Copilot CLI in PATH and an existing `copilot login` session
```

**Постоянные настройки:**
```yaml
model:
  provider: "copilot"
  default: "gpt-5.4"
```

| Переменная окружения | Описание |
|---------------------|----------|
| `COPILOT_GITHUB_TOKEN` | Токен GitHub для Copilot API (первый приоритет) |
| `HERMES_COPILOT_ACP_COMMAND` | Переопределить путь к бинарнику Copilot CLI (по умолчанию: `copilot`) |
| `HERMES_COPILOT_ACP_ARGS` | Переопределить аргументы ACP (по умолчанию: `--acp --stdio`) |
### Провайдеры API‑ключей первого класса

Эти провайдеры имеют встроенную поддержку с выделенными идентификаторами провайдера. Установи API‑ключ и используй `--provider` для выбора:

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

Или задай провайдера постоянно в `config.yaml`:
```yaml
model:
  provider: "gmi"
  default: "zai-org/GLM-5.1-FP8"
```

Базовые URL можно переопределить с помощью переменных окружения `NOVITA_BASE_URL`, `GLM_BASE_URL`, `KIMI_BASE_URL`, `MINIMAX_BASE_URL`, `MINIMAX_CN_BASE_URL`, `DASHSCOPE_BASE_URL`, `XIAOMI_BASE_URL`, `GMI_BASE_URL` или `TOKENHUB_BASE_URL`.

:::note Z.AI Endpoint Auto-Detection
При использовании провайдера Z.AI / GLM Hermes автоматически проверяет несколько конечных точек (глобальную, китайскую, варианты для программирования), чтобы найти ту, которая принимает твой API‑ключ. Тебе не нужно вручную задавать `GLM_BASE_URL` — рабочая конечная точка определяется и кэшируется автоматически.
:::
### xAI (Grok) — Responses API + кэширование подсказок

xAI подключён через Responses API (`codex_responses` transport) для автоматической поддержки рассуждений в моделях Grok 4 — параметр `reasoning_effort` не требуется, сервер рассуждает по умолчанию. Установи `XAI_API_KEY` в `~/.hermes/.env` и выбери xAI в `hermes model`, либо добавь `grok` как ярлык в `/model grok-4-fast-reasoning`.

Подписчики SuperGrok и X Premium+ могут входить через браузерный OAuth вместо API‑ключа — выбери **xAI Grok OAuth (SuperGrok / Premium+)** в `hermes model` или выполни `hermes auth add xai-oauth`. Тот же OAuth‑токен автоматически переиспользуется прямыми инструментами xAI (TTS, генерация изображений, генерация видео, транскрипция). Смотри [руководство по xAI Grok OAuth](../guides/xai-grok-oauth.md) для полного процесса — а если Hermes работает на удалённом хосте, также смотри [OAuth через SSH / Remote Hosts](../guides/oauth-over-ssh.md) для требуемого туннеля `ssh -L`.

При использовании xAI в качестве провайдера (любой базовый URL, содержащий `x.ai`) Hermes автоматически включает кэширование подсказок, отправляя заголовок `x-grok-conv-id` с каждым запросом API. Это направляет запросы к тому же серверу в рамках одной сессии разговора, позволяя инфраструктуре xAI переиспользовать кэшированные системные подсказки и историю диалога.

Никакой дополнительной настройки не требуется — кэширование активируется автоматически, когда обнаружен endpoint xAI и доступен идентификатор сессии. Это снижает задержку и стоимость многократных диалогов.

xAI также предоставляет отдельный endpoint TTS (`/v1/tts`). Выбери **xAI TTS** в `hermes tools` → Voice & TTS, или смотри страницу [Voice & TTS](../user-guide/features/tts.md#text-to-speech) для настройки.

**Миграция устаревшей модели xAI (15 мая 2026).** xAI выводит из эксплуатации `grok-4*`, `grok-3`, `grok-code-fast-1` и `grok-imagine-image-pro` — 2026‑05‑15. При запуске `hermes doctor` и `hermes chat` обнаруживается любая конфигурация, всё ещё указывающая на устаревший реф, и выводится рекомендация замены. Выполни `hermes migrate xai` для одноразовой переписи конфигурации — по умолчанию dry‑run, добавь `--apply`, чтобы записать изменения (автоматически создаётся резервная копия с тайм‑стампом `config.yaml.bak-pre-migrate-xai-*`).

```bash
hermes migrate xai          # preview replacements
hermes migrate xai --apply  # rewrite ~/.hermes/config.yaml in place
```

**Бэкенд веб‑поиска xAI.** Когда включён набор инструментов [Web Search](../user-guide/features/web-search.md), `web.backend: xai` направляет поиск через хост‑endpoint поиска xAI, используя те же учётные данные `XAI_API_KEY` / OAuth. Дополнительная настройка не требуется, если xAI уже сконфигурирован как провайдер.
### NovitaAI

NovitaAI — это облачная платформа, изначально созданная для ИИ, предназначенная разработчикам и агентам. Её три продуктовые линии: Model API с более чем 200 моделями, Agent Sandbox для создания и запуска ИИ‑агентов и GPU Cloud для масштабируемых вычислений, всё доступно из единой платформы.

```bash
# Use any available model
hermes chat --provider novita --model moonshotai/kimi-k2.5
# Requires: NOVITA_API_KEY in ~/.hermes/.env

# Short alias
hermes chat --provider novita-ai --model deepseek/deepseek-v3-0324
```

Или установить постоянно в `config.yaml`:
```yaml
model:
  provider: "novita"
  default: "moonshotai/kimi-k2.5"
  base_url: "https://api.novita.ai/openai/v1"
```

Получите свой API‑ключ на [novita.ai/settings/key-management](https://novita.ai/settings/key-management). Базовый URL можно переопределить с помощью `NOVITA_BASE_URL`.
### Ollama Cloud — Управляемые модели Ollama, OAuth + API‑ключ

[Ollama Cloud](https://ollama.com/cloud) размещает тот же каталог открытых моделей, что и локальный Ollama, но без требования GPU. Выбери её в `hermes model` как **Ollama Cloud**, вставь свой API‑ключ из [ollama.com/settings/keys](https://ollama.com/settings/keys), и Hermes автоматически обнаружит доступные модели.

```bash
hermes model
# → pick "Ollama Cloud"
# → paste your OLLAMA_API_KEY
# → select from discovered models (gpt-oss:120b, glm-4.6:cloud, qwen3-coder:480b-cloud, etc.)
```

Или напрямую в `config.yaml`:
```yaml
model:
  provider: "ollama-cloud"
  default: "gpt-oss:120b"
```

Каталог моделей загружается динамически из `ollama.com/v1/models` и кэшируется в течение одного часа. Нотация `model:tag` (например `qwen3-coder:480b-cloud`) сохраняется при нормализации — не используй тире.

:::tip Ollama Cloud vs local Ollama
Оба используют один и тот же совместимый с OpenAI API. Cloud — провайдер первого класса (`--provider ollama-cloud`, `OLLAMA_API_KEY`); локальный Ollama доступен через поток Custom Endpoint (базовый URL `http://localhost:11434/v1`, без ключа). Используй Ollama Cloud для больших моделей, которые нельзя запустить локально; используй локальный Ollama для приватности или офлайн‑работы.
:::
### AWS Bedrock

Anthropic Claude, Amazon Nova, DeepSeek v3.2, Meta Llama 4 и другие модели через AWS Bedrock. Использует цепочку учётных данных AWS SDK (`boto3`) — без API‑ключа, только стандартную аутентификацию AWS.

```bash
# Simplest — named profile in ~/.aws/credentials
hermes chat --provider bedrock --model us.anthropic.claude-sonnet-4-6

# Or with explicit env vars
AWS_PROFILE=myprofile AWS_REGION=us-east-1 hermes chat --provider bedrock --model us.anthropic.claude-sonnet-4-6
```

Или навсегда в `config.yaml`:
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

Аутентификация использует стандартную цепочку boto3: явные `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`, `AWS_PROFILE` из `~/.aws/credentials`, роль IAM на EC2/ECS/Lambda, IMDS или SSO. Переменная окружения не требуется, если ты уже аутентифицирован через AWS CLI.

Bedrock использует **Converse API** под капотом — запросы преобразуются в модель‑независимую форму Bedrock, поэтому одна и та же конфигурация работает для Claude, Nova, DeepSeek и Llama. Устанавливай `BEDROCK_BASE_URL` только если вызываешь региональный эндпоинт, отличный от значения по умолчанию.

См. [AWS Bedrock guide](/guides/aws-bedrock) для пошагового руководства по настройке IAM, выбору региона и кросс‑региональному выводу.
### Qwen Portal (OAuth)

Alibaba Qwen Portal с OAuth‑входом через браузер. Выбери **Qwen OAuth (Portal)** в `hermes model`, войди через браузер, и Hermes сохранит токен обновления.

```bash
hermes model
# → pick "Qwen OAuth (Portal)"
# → browser opens; sign in with your Alibaba account
# → confirm — credentials are saved to ~/.hermes/auth.json

hermes chat   # uses portal.qwen.ai/v1 endpoint
```

Или настрой `config.yaml`:
```yaml
model:
  provider: "qwen-oauth"
  default: "qwen3-coder-plus"
```

Установи `HERMES_QWEN_BASE_URL` только если конечная точка портала переносится (по умолчанию: `https://portal.qwen.ai/v1`).

:::tip Qwen OAuth vs Qwen Cloud (Alibaba DashScope)
`qwen-oauth` использует ориентированный на потребителя Qwen Portal с OAuth‑входом — идеален для отдельных пользователей. Провайдер `alibaba` использует Qwen Cloud (Alibaba DashScope) с `DASHSCOPE_API_KEY` — идеален для программных / производственных нагрузок. Оба маршрутизируют к моделям семейства Qwen, но находятся на разных конечных точках.
:::
### Alibaba Cloud (План кодинга)

Если у тебя оформлена подписка на **Coding Plan** от Alibaba (отдельный тарифный SKU от стандартного доступа к DashScope API), Hermes представляет её как собственного провайдера первого уровня: `alibaba-coding-plan`. Конечная точка: `https://coding-intl.dashscope.aliyuncs.com/v1`. Он совместим с OpenAI так же, как обычный провайдер `alibaba`, но использует другой базовый URL и биллинг.

```yaml
model:
  provider: alibaba_coding     # alias for alibaba-coding-plan
  model: qwen3-coder-plus
```

Или из CLI:

```bash
hermes chat --provider alibaba_coding --model qwen3-coder-plus
```

`alibaba_coding` использует тот же `DASHSCOPE_API_KEY`, который уже используется в записи `alibaba` — отдельный ключ не нужен, только другая цель маршрутизации. До регистрации этого провайдера пользователи, указывавшие `provider: alibaba_coding` в `config.yaml`, тихо переходили к маршрутизации через OpenRouter.
### MiniMax (OAuth)

MiniMax-M2.7 через браузерный вход OAuth — ключ API не требуется. Выбери **MiniMax (OAuth)** в `hermes model`, войди через браузер, и Hermes сохранит токены доступа и обновления. Под капотом используется совместимый с Anthropic Messages endpoint (`/anthropic`).

```bash
hermes model
# → pick "MiniMax (OAuth)"
# → browser opens; sign in with your MiniMax account (global or CN region)
# → confirm — credentials are saved to ~/.hermes/auth.json

hermes chat   # uses api.minimax.io/anthropic endpoint
```

Или настрой `config.yaml`:
```yaml
model:
  provider: "minimax-oauth"
  default: "MiniMax-M2.7"
```

Поддерживаемые модели: `MiniMax-M2.7` (основная) и `MiniMax-M2.7-highspeed` (подключена как вспомогательная модель по умолчанию). Путь OAuth игнорирует `MINIMAX_API_KEY` / `MINIMAX_BASE_URL`.

:::tip MiniMax OAuth vs API key
`minimax-oauth` использует портал MiniMax для потребителей с входом OAuth — не требуется настройка биллинга. Провайдеры `minimax` и `minimax-cn` используют `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` — для программного доступа. Смотри [MiniMax OAuth guide](/guides/minimax-oauth) для полного руководства.
:::
### NVIDIA NIM

Nemotron и другие модели с открытым исходным кодом через [build.nvidia.com](https://build.nvidia.com) (бесплатный API‑ключ) или локальную точку доступа NIM.

```bash
# Cloud (build.nvidia.com)
hermes chat --provider nvidia --model nvidia/nemotron-3-super-120b-a12b
# Requires: NVIDIA_API_KEY in ~/.hermes/.env

# Local NIM endpoint — override base URL
NVIDIA_BASE_URL=http://localhost:8000/v1 hermes chat --provider nvidia --model nvidia/nemotron-3-super-120b-a12b
```

Или установить постоянно в `config.yaml`:
```yaml
model:
  provider: "nvidia"
  default: "nvidia/nemotron-3-super-120b-a12b"
```

:::tip Local NIM
Для развертываний on‑prem (DGX Spark, локальный GPU) установи `NVIDIA_BASE_URL=http://localhost:8000/v1`. NIM предоставляет тот же совместимый с OpenAI API для чат‑запросов, что и build.nvidia.com, поэтому переключение между облаком и локальным окружением происходит изменением одной переменной окружения.
:::

Hermes автоматически добавляет заголовок `NIM billing-origin` к каждому запросу к `build.nvidia.com` — дополнительная настройка не требуется. Это направляет потребление к правильному источнику в панели биллинга NVIDIA.
### GMI Cloud

Открытые модели и модели рассуждения через [GMI Cloud](https://www.gmicloud.ai/) — совместимый с API OpenAI, аутентификация с помощью API‑ключа.

```bash
# GMI Cloud
hermes chat --provider gmi --model deepseek-ai/DeepSeek-V3.2
# Requires: GMI_API_KEY in ~/.hermes/.env
```

Или задать его постоянно в `config.yaml`:
```yaml
model:
  provider: "gmi"
  default: "deepseek-ai/DeepSeek-V3.2"
```

Базовый URL можно переопределить с помощью `GMI_BASE_URL` (по умолчанию: `https://api.gmi-serving.com/v1`).
### StepFun

Модели серии Step через [StepFun](https://platform.stepfun.com) — API, совместимое с OpenAI, аутентификация по API‑ключу.

```bash
# StepFun
hermes chat --provider stepfun --model step-3-mini
# Requires: STEPFUN_API_KEY in ~/.hermes/.env
```

Или задать его постоянно в `config.yaml`:
```yaml
model:
  provider: "stepfun"
  default: "step-3-mini"
```

Базовый URL можно переопределить с помощью `STEPFUN_BASE_URL` (по умолчанию: `https://api.stepfun.com/v1`).
### Провайдеры инференса Hugging Face

[Hugging Face Inference Providers](https://huggingface.co/docs/inference-providers) маршрутизирует более 20 открытых моделей через единый совместимый с OpenAI endpoint (`router.huggingface.co/v1`). Запросы автоматически направляются к самому быстрому доступному бэкенду (Groq, Together, SambaNova и др.) с автоматическим переключением при сбое.

```bash
# Use any available model
hermes chat --provider huggingface --model Qwen/Qwen3.5-397B-A17B
# Requires: HF_TOKEN in ~/.hermes/.env

# Short alias
hermes chat --provider hf --model deepseek-ai/DeepSeek-V3.2
```

Или установить постоянно в `config.yaml`:
```yaml
model:
  provider: "huggingface"
  default: "Qwen/Qwen3.5-397B-A17B"
```

Получите токен на [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) — убедитесь, что включено разрешение «Make calls to Inference Providers». Бесплатный тариф включает кредит $0.10 / мес, без надбавки к ставкам провайдеров.

Вы можете добавлять суффиксы маршрутизации к именам моделей: `:fastest` (по умолчанию), `:cheapest` или `:provider_name`, чтобы принудительно использовать конкретный бэкенд.

Базовый URL можно переопределить с помощью `HF_BASE_URL`.
### Google Gemini через OAuth (`google-gemini-cli`)

Провайдер `google-gemini-cli` использует бэкенд Google Cloud Code Assist — тот же API, что и у собственного инструмента Google `gemini-cli`. Он поддерживает как **бесплатный уровень** (щедрая суточная квота для личных аккаунтов), так и **платные уровни** (Standard/Enterprise через проект GCP).

**Быстрый старт:**

```bash
hermes model
# → pick "Google Gemini (OAuth)"
# → see policy warning, confirm
# → browser opens to accounts.google.com, sign in
# → done — Hermes auto-provisions your free tier on first request
```

Hermes поставляется с **публичным** OAuth‑клиентом `gemini-cli` от Google по умолчанию — те же учётные данные, что Google включает в свой открытый `gemini-cli`. Десктоп‑клиенты OAuth не являются конфиденциальными (безопасность обеспечивает PKCE). Устанавливать `gemini-cli` или регистрировать собственный OAuth‑клиент GCP не требуется.

**Как работает аутентификация:**
- PKCE Authorization Code flow против `accounts.google.com`
- Обратный вызов в браузере по `http://127.0.0.1:8085/oauth2callback` (с резервным портом, если основной занят)
- Токены сохраняются в `~/.hermes/auth/google_oauth.json` (chmod 0600, атомарная запись, межпроцессная блокировка `fcntl`)
- Автоматическое обновление за 60 с до истечения срока
- Безголовые окружения (SSH, `HERMES_HEADLESS=1`) → резервный режим paste‑mode
- Дедупликация обновлений в полёте — два одновременных запроса не приведут к двойному обновлению
- `invalid_grant` (отозванный refresh‑токен) → файл учётных данных удаляется, пользователь получает запрос на повторный вход

**Как работает вывод:**
- Трафик направляется к `https://cloudcode-pa.googleapis.com/v1internal:generateContent` (или `:streamGenerateContent?alt=sse` для потоковой передачи), **не** к платному эндпоинту `v1beta/openai`
- Тело запроса оборачивается в `{project, model, user_prompt_id, request}`
- Поля OpenAI‑формата `messages[]`, `tools[]`, `tool_choice` переводятся в нативный формат Gemini `contents[]`, `tools[].functionDeclarations`, `toolConfig`
- Ответы переводятся обратно в форму OpenAI, чтобы остальная часть Hermes работала без изменений

**Уровни и идентификаторы проектов:**

| Ваша ситуация | Что делать |
|---|---|
| Личный аккаунт Google, нужен бесплатный уровень | Ничего — войди, начни чат |
| Аккаунт Workspace / Standard / Enterprise | Установи `HERMES_GEMINI_PROJECT_ID` или `GOOGLE_CLOUD_PROJECT` в идентификатор твоего проекта GCP |
| Организация, защищённая VPC‑SC | Hermes обнаруживает `SECURITY_POLICY_VIOLATED` и автоматически переключает на `standard-tier` |

Бесплатный уровень автоматически создаёт управляемый Google проект при первом использовании. Настройка GCP не требуется.

**Мониторинг квоты:**

```
/gquota
```

Показывает оставшуюся квоту Code Assist по модели с индикаторами прогресса:

```
Gemini Code Assist quota  (project: 123-abc)

  gemini-2.5-pro                      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░   85%
  gemini-2.5-flash [input]            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░   92%
```

:::warning Policy risk
Google считает использование OAuth‑клиента Gemini CLI в стороннем программном обеспечении нарушением политики. Некоторые пользователи сталкивались с ограничениями аккаунтов. Для минимального риска используй собственный API‑ключ через провайдер `gemini`. Hermes выводит предварительное предупреждение и требует явного подтверждения перед началом OAuth.
:::

**Собственный OAuth‑клиент (по желанию):**

Если ты предпочитаешь зарегистрировать собственный OAuth‑клиент Google — например, чтобы квота и согласия были привязаны к твоему проекту GCP — установи:

```bash
HERMES_GEMINI_CLIENT_ID=your-client.apps.googleusercontent.com
HERMES_GEMINI_CLIENT_SECRET=...   # optional for Desktop clients
```

Зарегистрируй OAuth‑клиент **Desktop app** на
[console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
с включённым Generative Language API.
## Пользовательские и самостоятельные провайдеры LLM

Hermes Agent работает с **любым API‑endpoint, совместимым с OpenAI**. Если сервер реализует `/v1/chat/completions`, ты можешь указать Hermes использовать его. Это означает, что можно применять локальные модели, серверы инференса на GPU, маршрутизаторы с несколькими провайдерами или любой сторонний API.
### Общая настройка

Три способа настроить пользовательскую конечную точку:

**Интерактивная настройка (рекомендовано):**
```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter: API base URL, API key, Model name
```

**Ручная конфигурация (`config.yaml`):**
```yaml
# In ~/.hermes/config.yaml
model:
  default: your-model-name
  provider: custom
  base_url: http://localhost:8000/v1
  api_key: your-key-or-leave-empty-for-local
```

:::warning Legacy env vars
`LLM_MODEL` в `.env` **удалена** — `config.yaml` является единственным источником правды для настройки модели и конечной точки. `OPENAI_BASE_URL` всё ещё учитывается, но **только** для провайдера `openai-api` (он переопределяет конечную точку OpenAI при прямом доступе по API‑ключу). Для остальных провайдеров и пользовательских конечных точек используй `hermes model` или укажи `model.base_url` непосредственно в `config.yaml`. Если в твоём `.env` остались устаревшие записи, они будут автоматически удалены при следующем запуске `hermes setup` или миграции конфигурации.
:::

Оба подхода сохраняют данные в `config.yaml`, который является единственным источником правды для модели, провайдера и базового URL.
### Переключение моделей с помощью `/model`

:::warning hermes model vs /model
**`hermes model`** (запускается из терминала, вне любой сессии чата) — это **полный мастер настройки провайдера**. Используй его для добавления новых провайдеров, выполнения OAuth‑потоков, ввода API‑ключей и настройки пользовательских конечных точек.

**`/model`** (вводится внутри активной сессии Hermes) может только **переключать между провайдерами и моделями, которые уже настроены**. Он не может добавить новые провайдеры, выполнить OAuth или запросить API‑ключи. Если у тебя настроен только один провайдер (например, OpenRouter), `/model` покажет только модели этого провайдера.

**Чтобы добавить новый провайдер:** выйди из сессии (`Ctrl+C` или `/quit`), запусти `hermes model`, настрой новый провайдер, затем начни новую сессию.
:::

Как только у тебя будет настроена хотя бы одна пользовательская конечная точка, ты можешь переключать модели в ходе сессии:

```
/model custom:qwen-2.5          # Switch to a model on your custom endpoint
/model custom                    # Auto-detect the model from the endpoint
/model openrouter:claude-sonnet-4 # Switch back to a cloud provider
```

Если у тебя **настроены именованные пользовательские провайдеры** (см. ниже), используй тройной синтаксис:

```
/model custom:local:qwen-2.5    # Use the "local" custom provider with model qwen-2.5
/model custom:work:llama3       # Use the "work" custom provider with llama3
```

При переключении провайдеров Hermes сохраняет базовый URL и провайдера в конфигурацию, чтобы изменение сохранялось после перезапуска. При переключении от пользовательской конечной точки к встроенному провайдеру устаревший базовый URL автоматически очищается.

:::tip
`/model custom` (без указания имени модели) запрашивает API `/models` твоей конечной точки и автоматически выбирает модель, если загружена ровно одна. Удобно для локальных серверов, работающих с единственной моделью.
:::

Всё ниже следует той же схеме — просто меняй URL, ключ и имя модели.
### Ollama — локальные модели, без конфигурации

[Ollama](https://ollama.com/) запускает модели с открытыми весами локально одной командой. Лучшее решение для: быстрого локального экспериментирования, работы с конфиденциальными данными, использования в офлайн‑режиме. Поддерживает вызов инструментов через совместимый с OpenAI API.

```bash
# Install and run a model
ollama pull qwen2.5-coder:32b
ollama serve   # Starts on port 11434
```

Затем настройте Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:11434/v1
# Skip API key (Ollama doesn't need one)
# Enter model name (e.g. qwen2.5-coder:32b)
```

Или настройте `config.yaml` напрямую:

```yaml
model:
  default: qwen2.5-coder:32b
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 64000   # See warning below
```

:::caution Ollama по умолчанию использует очень небольшые длины контекста
Ollama **не** использует полное окно контекста вашей модели по умолчанию. В зависимости от объёма VRAM, значение по умолчанию:

| Доступный VRAM | Длина контекста по умолчанию |
|----------------|------------------------------|
| Менее 24 ГБ   | **4 096 токенов**            |
| 24–48 ГБ      | 32 768 токенов               |
| 48+ ГБ        | 256 000 токенов              |

Hermes Agent требует минимум **64 000 токенов** окна контекста для использования агента с инструментами. Более короткие окна отклоняются при запуске, потому что системный запрос, схемы инструментов и состояние текущего диалога нуждаются в достаточном месте для надёжных многошаговых рабочих процессов.

**Как увеличить** (выбери один вариант):

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

**Нельзя задать длину контекста через совместимый с OpenAI API** (`/v1/chat/completions`). Её нужно настраивать на стороне сервера или через Modelfile. Это главный источник путаницы при интеграции Ollama с инструментами, такими как Hermes.
:::

**Проверь, что контекст установлен правильно:**

```bash
ollama ps
# Look at the CONTEXT column — it should show your configured value
```

:::tip
Получить список доступных моделей можно командой `ollama list`. Скачать любую модель из [библиотеки Ollama](https://ollama.com/library) можно командой `ollama pull <model>`. Ollama автоматически управляет выгрузкой на GPU — для большинства конфигураций дополнительная настройка не требуется.
:::

---
### vLLM — Высокопроизводительный инференс на GPU

[vLLM](https://docs.vllm.ai/) — стандарт для продакшн‑развёртывания LLM. Лучшее решение для: максимальной пропускной способности на GPU‑аппаратуре, обслуживания больших моделей, непрерывного батчинга.

```bash
pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --port 8000 \
  --max-model-len 65536 \
  --tensor-parallel-size 2 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

Затем настройте Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:8000/v1
# Skip API key (or enter one if you configured vLLM with --api-key)
# Enter model name: meta-llama/Llama-3.1-70B-Instruct
```

**Длина контекста:** vLLM по умолчанию читает `max_position_embeddings` модели. Если она превышает объём памяти твоего GPU, будет ошибка с предложением установить `--max-model-len` меньше. Ты также можешь использовать `--max-model-len auto`, чтобы автоматически подобрать максимальное значение, которое помещается. Установи `--gpu-memory-utilization 0.95` (по умолчанию 0.9), чтобы уместить больше контекста в VRAM.

**Вызов инструмента требует явных флагов:**

| Флаг | Назначение |
|------|------------|
| `--enable-auto-tool-choice` | Требуется для `tool_choice: "auto"` (значение по умолчанию в Hermes) |
| `--tool-call-parser <name>` | Парсер формата вызова инструмента моделью |

Поддерживаемые парсеры: `hermes` (Qwen 2.5, Hermes 2/3), `llama3_json` (Llama 3.x), `mistral`, `deepseek_v3`, `deepseek_v31`, `xlam`, `pythonic`. Без этих флагов вызовы инструмента не будут работать — модель будет выводить их как обычный текст.

:::tip
vLLM поддерживает читаемые человеком размеры: `--max-model-len 64k` (строчная k = 1000, заглавная K = 1024).
:::

---
### SGLang — Быстрое обслуживание с RadixAttention

[SGLang](https://github.com/sgl-project/sglang) — альтернатива vLLM с RadixAttention для повторного использования KV‑кэша. Лучшее применение: многошаговые диалоги (кеширование префикса), ограниченное декодирование, структурированный вывод.

```bash
pip install "sglang[all]"
python -m sglang.launch_server \
  --model meta-llama/Llama-3.1-70B-Instruct \
  --port 30000 \
  --context-length 65536 \
  --tp 2 \
  --tool-call-parser qwen
```

Затем настройте Hermes:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:30000/v1
# Enter model name: meta-llama/Llama-3.1-70B-Instruct
```

**Длина контекста:** По умолчанию SGLang читает её из конфигурации модели. Используйте `--context-length`, чтобы переопределить. Если необходимо превысить объявленный максимум модели, установите `SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1`.

**Вызов инструментов:** Используйте `--tool-call-parser` с соответствующим парсером для семейства вашей модели: `qwen` (Qwen 2.5), `llama3`, `llama4`, `deepseekv3`, `mistral`, `glm`. Без этого флага вызовы инструментов возвращаются как обычный текст.

:::caution SGLang по умолчанию ограничивает вывод 128 токенами
Если ответы выглядят усечёнными, добавьте `max_tokens` к вашим запросам или установите `--default-max-tokens` на сервере. По умолчанию SGLang выдаёт только 128 токенов на ответ, если это не указано в запросе.
:::

---
### llama.cpp / llama-server — Инференс на CPU и Metal

[llama.cpp](https://github.com/ggml-org/llama.cpp) запускает квантизированные модели на CPU, Apple Silicon (Metal) и потребительских GPU. Лучшее решение для: запуска моделей без GPU в дата‑центре, пользователей Mac, развертывания на краю.

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

**Длина контекста (`-c`):** В последних сборках по умолчанию `0`, что считывает контекст обучения модели из метаданных GGUF. Для моделей с контекстом обучения ≥ 128 k это может привести к OOM при попытке выделить весь KV‑кеш. Установи `-c` явно как минимум 64 000 токенов для Hermes. Если используешь параллельные слоты (`-np`), общий контекст делится между слотами — с `-c 64000 -np 4` каждый слот получает только 16 k, что ниже минимального значения Hermes для активной сессии.

Затем настрой Hermes, чтобы он указывал на неё:

```bash
hermes model
# Select "Custom endpoint (self-hosted / VLLM / etc.)"
# Enter URL: http://localhost:8080/v1
# Skip API key (local servers don't need one)
# Enter model name — or leave blank to auto-detect if only one model is loaded
```

Это сохраняет конечную точку в `config.yaml`, чтобы она сохранялась между сессиями.

:::caution `--jinja` обязателен для вызова инструментов
Без `--jinja` llama‑server полностью игнорирует параметр `tools`. Модель будет пытаться вызывать инструменты, записывая JSON в текст своего ответа, но Hermes не распознает это как вызов инструмента — ты увидишь сырой JSON вроде `{"name": "web_search", ...}` напечатанный как сообщение вместо реального поиска.
:::

:::tip
Скачай GGUF‑модели с [Hugging Face](https://huggingface.co/models?library=gguf). Квантование Q4_K_M обеспечивает лучший баланс качества и использования памяти.
:::
### LM Studio — десктопное приложение с локальными моделями

[LM Studio](https://lmstudio.ai/) — десктопное приложение для запуска локальных моделей с графическим интерфейсом. Лучшее решение для: пользователей, которым удобнее визуальный интерфейс, быстрой проверки моделей, разработчиков на macOS/Windows/Linux.

Запусти сервер из приложения LM Studio (вкладка **Developer** → **Start Server**), либо используй CLI:

```bash
lms server start                        # Starts on port 1234
lms load qwen2.5-coder --context-length 64000
```

Затем настрой Hermes:

```bash
hermes model
# Select "LM Studio"
# Press Enter to use http://localhost:1234/v1
# Pick one of the discovered models
# If LM Studio server auth is enabled, enter LM_API_KEY when prompted
```

Hermes автоматически загрузит модель LM Studio с длиной контекста 64 K.

Чтобы изменить длину контекста в LM Studio:

1. Нажми на значок шестерёнки рядом с выбором модели.
2. Установи **Context Length** минимум 64000 для плавной работы.
3. Перезагрузи модель, чтобы изменение вступило в силу.
4. Если твой компьютер не справляется с 64000, рассмотрите использование более лёгкой модели с большей длиной контекста.

Можно также воспользоваться CLI: `lms load model-name --context-length 64000`

Для оценки, поместится ли модель, используй: `lms load model-name --context-length 64000 --estimate-only`

Чтобы задать постоянные значения по умолчанию для каждой модели: вкладка **My Models** → значок шестерёнки у модели → установить размер контекста.
:::

**Вызов инструментов:** Поддерживается, начиная с LM Studio 0.3.6. Модели с нативным обучением вызова инструментов (Qwen 2.5, Llama 3.x, Mistral, Hermes) автоматически обнаруживаются и помечаются значком инструмента. Другие модели используют общий запасной вариант, который может быть менее надёжным.

---
### Сетевое взаимодействие WSL2 (пользователи Windows)

Поскольку Hermes Agent требует Unix‑окружения, пользователи Windows запускают его внутри WSL2. Если ваш сервер моделей (Ollama, LM Studio и т.д.) работает на **Windows‑хосте**, необходимо «мостить» сетевой разрыв — WSL2 использует виртуальный сетевой адаптер со своей подсетью, поэтому `localhost` внутри WSL2 указывает на Linux‑VM, **а не** на Windows‑хост.

:::tip Оба процесса в WSL2? Нет проблем.
Если ваш сервер моделей также работает внутри WSL2 (что обычно для vLLM, SGLang и llama-server), `localhost` работает как ожидается — они используют одно и то же сетевое пространство имён. Пропусти этот раздел.
:::

#### Вариант 1: Режим зеркального сетевого взаимодействия (рекомендовано)

Доступно в **Windows 11 22H2+**, режим зеркалирования делает `localhost` двунаправленным между Windows и WSL2 — самое простое решение.

1. Создай или отредактируй `%USERPROFILE%\.wslconfig` (например, `C:\Users\YourName\.wslconfig`):
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

2. Перезапусти WSL из PowerShell:
   ```powershell
   wsl --shutdown
   ```

3. Открой терминал WSL2 заново. `localhost` теперь достигает сервисов Windows:
   ```bash
   curl http://localhost:11434/v1/models   # Ollama on Windows — works
   ```

:::note Hyper‑V Firewall
В некоторых сборках Windows 11 брандмауэр Hyper‑V по умолчанию блокирует зеркальные соединения. Если `localhost` всё ещё не работает после включения зеркального режима, выполни это в **PowerShell от администратора**:
```powershell
Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow
```
:::

#### Вариант 2: Использовать IP‑адрес Windows‑хоста (Windows 10 / более старые сборки)

Если зеркальный режим недоступен, найди IP‑адрес Windows‑хоста изнутри WSL2 и используй его вместо `localhost`:

```bash
# Get the Windows host IP (the default gateway of WSL2's virtual network)
ip route show | grep -i default | awk '{ print $3 }'
# Example output: 172.29.192.1
```

Подставь этот IP в конфигурацию Hermes:

```yaml
model:
  default: qwen2.5-coder:32b
  provider: custom
  base_url: http://172.29.192.1:11434/v1   # Windows host IP, not localhost
```

:::tip Динамический помощник
IP‑адрес хоста может измениться после перезапуска WSL2. Ты можешь получать его динамически в оболочке:
```bash
export WSL_HOST=$(ip route show | grep -i default | awk '{ print $3 }')
echo "Windows host at: $WSL_HOST"
curl http://$WSL_HOST:11434/v1/models   # Test Ollama
```

Или использовать mDNS‑имя твоего компьютера (требуется `libnss-mdns` в WSL2):
```bash
sudo apt install libnss-mdns
curl http://$(hostname).local:11434/v1/models
```
:::

#### Адрес привязки сервера (требуется для NAT‑режима)

Если ты используешь **Вариант 2** (режим NAT с IP‑адресом хоста), сервер моделей в Windows должен принимать соединения не только от `127.0.0.1`. По умолчанию большинство серверов слушают только localhost — соединения из WSL2 в режиме NAT приходят из другой виртуальной подсети и будут отклонены. В режиме зеркалирования `localhost` напрямую отображается, поэтому привязка к `127.0.0.1` работает без проблем.

| Сервер | Привязка по умолчанию | Как исправить |
|--------|----------------------|---------------|
| **Ollama** | `127.0.0.1` | Установи переменную окружения `OLLAMA_HOST=0.0.0.0` перед запуском Ollama (System Settings → Environment Variables в Windows или отредактируй сервис Ollama) |
| **LM Studio** | `127.0.0.1` | Включи **«Serve on Network»** на вкладке Developer → Server settings |
| **llama-server** | `127.0.0.1` | Добавь `--host 0.0.0.0` к команде запуска |
| **vLLM** | `0.0.0.0` | Уже привязывается ко всем интерфейсам по умолчанию |
| **SGLang** | `127.0.0.1` | Добавь `--host 0.0.0.0` к команде запуска |

**Ollama на Windows (подробно):** Ollama работает как сервис Windows. Чтобы задать `OLLAMA_HOST`:
1. Открой **System Properties** → **Environment Variables**
2. Добавь новую **System variable**: `OLLAMA_HOST` = `0.0.0.0`
3. Перезапусти сервис Ollama (или перезагрузи систему)

#### Брандмауэр Windows

Брандмауэр Windows рассматривает WSL2 как отдельную сеть (как в режиме NAT, так и в зеркальном). Если после выполненных шагов соединения всё ещё не проходят, добавь правило брандмауэра для порта твоего сервера моделей:

```powershell
# Run in Admin PowerShell — replace PORT with your server's port
New-NetFirewallRule -DisplayName "Allow WSL2 to Model Server" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434
```

Распространённые порты: Ollama `11434`, vLLM `8000`, SGLang `30000`, llama-server `8080`, LM Studio `1234`.

#### Быстрая проверка

Изнутри WSL2 проверь, что ты можешь достучаться до сервера моделей:

```bash
# Replace URL with your server's address and port
curl http://localhost:11434/v1/models          # Mirrored mode
curl http://172.29.192.1:11434/v1/models       # NAT mode (use your actual host IP)
```

Если получаешь JSON‑ответ со списком моделей, всё в порядке. Используй тот же URL в качестве `base_url` в конфигурации Hermes.
### Устранение неполадок локальных моделей

Эти проблемы затрагивают **все** локальные серверы вывода при работе с Hermes.

#### «Connection refused» из WSL2 к серверу модели, запущенному в Windows

Если ты запускаешь Hermes внутри WSL2, а сервер модели — на хосте Windows, `http://localhost:<port>` не будет работать в режиме NAT‑сетевого подключения WSL2 по умолчанию. Смотри раздел [WSL2 Networking](#wsl2-networking-windows-users) выше — там указано, как исправить.

#### Вызовы инструментов отображаются как текст вместо выполнения

Модель выводит что‑то вроде `{"name": "web_search", "arguments": {...}}` в виде сообщения, а не действительно вызывает инструмент.

**Причина:** На твоём сервере отключён вызов инструментов, либо модель не поддерживает его через реализацию вызова инструментов сервера.

| Server | Fix |
|--------|-----|
| **llama.cpp** | Добавь `--jinja` к команде запуска |
| **vLLM** | Добавь `--enable-auto-tool-choice --tool-call-parser hermes` |
| **SGLang** | Добавь `--tool-call-parser qwen` (или соответствующий парсер) |
| **Ollama** | Вызов инструментов включён по умолчанию — убедись, что твоя модель поддерживает его (проверь с помощью `ollama show model-name`) |
| **LM Studio** | Обнови до версии 0.3.6+ и используй модель с нативной поддержкой инструментов |

#### Модель, кажется, забывает контекст или даёт несвязные ответы

**Причина:** Окно контекста слишком мало. Когда диалог превышает лимит контекста, большинство серверов молча отбрасывают старые сообщения. Системный промпт Hermes + схемы инструментов уже могут занимать 4 k–8 k токенов.

**Диагностика:**

```bash
# Check what Hermes thinks the context is
# Look at startup line: "Context limit: X tokens"

# Check your server's actual context
# Ollama: ollama ps (CONTEXT column)
# llama.cpp: curl http://localhost:8080/props | jq '.default_generation_settings.n_ctx'
# vLLM: check --max-model-len in startup args
```

**Исправление:** Установи контекст минимум в **64 000 токенов** для использования агентом. Смотри разделы каждого сервера выше для конкретного флага.

#### «Context limit: 2048 tokens» при запуске

Hermes автоматически определяет длину контекста из эндпоинта `/v1/models` твоего сервера. Если сервер сообщает низкое значение (или не сообщает его вовсе), Hermes использует объявленный лимит модели, который может быть неверным.

**Исправление:** Укажи его явно в `config.yaml`:

```yaml
model:
  default: your-model
  provider: custom
  base_url: http://localhost:11434/v1
  context_length: 64000
```

#### Ответы обрезаются посередине предложения

**Возможные причины:**
1. **Низкий лимит вывода (`max_tokens`) на сервере** — по умолчанию SGLang выдаёт 128 токенов за ответ. Установи `--default-max-tokens` на сервере или настрой Hermes через `model.max_tokens` в `config.yaml`. Заметь: `max_tokens` контролирует только длину ответа — он не связан с тем, насколько длинной может быть история диалога (это `context_length`).
2. **Исчерпание контекста** — модель заполнила своё окно контекста. Увеличь `model.context_length` или включи [context compression](/user-guide/configuration#context-compression) в Hermes.
### LiteLLM Proxy — Шлюз мультипровайдеров

[LiteLLM](https://docs.litellm.ai/) — это прокси, совместимый с OpenAI, который объединяет более 100 провайдеров LLM за единым API. Оптимально для: переключения между провайдерами без изменения конфигурации, балансировки нагрузки, цепочек запасных вариантов, контроля бюджета.

```bash
# Install and start
pip install "litellm[proxy]"
litellm --model anthropic/claude-sonnet-4 --port 4000

# Or with a config file for multiple models:
litellm --config litellm_config.yaml --port 4000
```

Затем настрой Hermes с помощью `hermes model` → Пользовательская конечная точка → `http://localhost:4000/v1`.

Пример `litellm_config.yaml` с запасным вариантом:
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
### ClawRouter — Оптимизированный по стоимости роутинг

[ClawRouter](https://github.com/BlockRunAI/ClawRouter) от BlockRunAI — это локальный прокси‑маршрутизатор, который автоматически выбирает модели в зависимости от сложности запроса. Он классифицирует запросы по 14 измерениям и направляет их к самой дешёвой модели, способной выполнить задачу. Оплата производится криптовалютой USDC (без API‑ключей).

```bash
# Install and start
npx @blockrun/clawrouter    # Starts on port 8402
```

Затем настрой Hermes с помощью `hermes model` → Custom endpoint → `http://localhost:8402/v1` → имя модели `blockrun/auto`.

Профили роутинга:
| Профиль | Стратегия | Экономия |
|---------|----------|----------|
| `blockrun/auto` | Сбалансированное качество/стоимость | 74‑100% |
| `blockrun/eco` | Наиболее дешёвая возможная | 95‑100% |
| `blockrun/premium` | Лучшие модели по качеству | 0% |
| `blockrun/free` | Только бесплатные модели | 100% |
| `blockrun/agentic` | Оптимизировано для использования инструментов | различается |

:::note
ClawRouter требует кошелёк, пополненный USDC, в сети Base или Solana для оплаты. Все запросы проходят через backend‑API BlockRun. Запусти `npx @blockrun/clawrouter doctor`, чтобы проверить статус кошелька.
:::
### Другие совместимые провайдеры

Любой сервис с API, совместимым с OpenAI, работает. Некоторые популярные варианты:

| Провайдер | Базовый URL | Примечания |
|----------|-------------|------------|
| [Together AI](https://together.ai) | `https://api.together.xyz/v1` | Облачный хостинг открытых моделей |
| [Groq](https://groq.com) | `https://api.groq.com/openai/v1` | Ультрабыстрый вывод |
| [DeepSeek](https://deepseek.com) | `https://api.deepseek.com/v1` | Модели DeepSeek |
| [Fireworks AI](https://fireworks.ai) | `https://api.fireworks.ai/inference/v1` | Быстрый хостинг открытых моделей |
| [GMI Cloud](https://www.gmicloud.ai/) | `https://api.gmi-serving.com/v1` | Управляемый вывод, совместимый с OpenAI |
| [Cerebras](https://cerebras.ai) | `https://api.cerebras.ai/v1` | Вывод на чипе ваферного масштаба |
| [Mistral AI](https://mistral.ai) | `https://api.mistral.ai/v1` | Модели Mistral |
| [OpenAI](https://openai.com) | `https://api.openai.com/v1` | Прямой доступ к OpenAI |
| [Azure OpenAI](https://azure.microsoft.com) | `https://YOUR.openai.azure.com/` | Корпоративный OpenAI |
| [LocalAI](https://localai.io) | `http://localhost:8080/v1` | Самостоятельный хостинг, мульти‑модель |
| [Jan](https://jan.ai) | `http://localhost:1337/v1` | Десктоп‑приложение с локальными моделями |

Настрой любой из них с помощью `hermes model` → Пользовательский эндпоинт, или в `config.yaml`:

```yaml
model:
  default: meta-llama/Llama-3.1-70B-Instruct-Turbo
  provider: custom
  base_url: https://api.together.xyz/v1
  api_key: your-together-key
```

---
### Обнаружение длины контекста

:::note Два параметра, легко перепутать
**`context_length`** — это **общий размер окна контекста** — совокупный бюджет токенов ввода *и* вывода (например, 200 000 для Claude Opus 4.6). Hermes использует его, чтобы решить, когда сжимать историю, и для проверки запросов к API.

**`model.max_tokens`** — это **ограничение вывода** — максимальное количество токенов, которое модель может сгенерировать в *одном ответе*. Он не имеет отношения к тому, насколько длинной может быть история разговора. Стандартное название `max_tokens` часто вызывает путаницу; в нативном API Anthropic его переименовали в `max_output_tokens` для ясности.

Устанавливай `context_length`, если автоопределение неверно определило размер окна.
Устанавливай `model.max_tokens` только тогда, когда нужно ограничить длину отдельных ответов.
:::

Hermes использует цепочку разрешения из нескольких источников, чтобы определить правильное окно контекста для твоей модели и провайдера:

1. **Переопределение в конфиге** — `model.context_length` в `config.yaml` (наивысший приоритет)
2. **Пользовательский провайдер per‑model** — `custom_providers[].models.<id>.context_length`
3. **Постоянный кэш** — ранее обнаруженные значения (сохраняются между перезапусками)
4. **Эндпоинт `/models`** — запрос к API твоего сервера (локальные/пользовательские эндпоинты)
5. **Anthropic `/v1/models`** — запрос к API Anthropic за `max_input_tokens` (только для пользователей с API‑ключом)
6. **OpenRouter API** — живые метаданные модели из OpenRouter
7. **Nous Portal** — сопоставление суффиксов ID моделей Nous с метаданными OpenRouter
8. **[models.dev](https://models.dev)** — поддерживаемый сообществом реестр с контекстными длинами, специфичными для провайдеров, для более чем 3800 моделей от 100+ провайдеров
9. **Запасные значения по умолчанию** — общие шаблоны семейства моделей (по умолчанию 128K)

Для большинства конфигураций это работает «из коробки». Система учитывает провайдера — одна и та же модель может иметь разные ограничения контекста в зависимости от того, кто её обслуживает (например, `claude-opus-4.6` имеет 1 M в прямом API Anthropic, но 128K в GitHub Copilot).

Чтобы явно задать длину контекста, добавь `context_length` в конфигурацию модели:

```yaml
model:
  default: "qwen3.5:9b"
  base_url: "http://localhost:8080/v1"
  context_length: 131072  # tokens
```

Для пользовательских эндпоинтов также можно задать длину контекста per‑model:

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

`hermes model` запросит длину контекста при настройке пользовательского эндпоинта. Оставь поле пустым для автоопределения.

:::tip Когда задавать вручную
- Ты используешь Ollama с пользовательским `num_ctx`, который ниже максимального для модели
- Хочешь ограничить контекст ниже максимального (например, 8k на модели с 128k, чтобы сэкономить VRAM)
- Ты работаешь через прокси, который не раскрывает `/v1/models`
:::
### Именованные пользовательские провайдеры

Если ты работаешь с несколькими пользовательскими конечными точками (например, локальным сервером разработки и удалённым GPU‑сервером), их можно определить как именованные пользовательские провайдеры в `config.yaml`:

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

Некоторые совместимые с OpenAI конечные точки требуют специфичных для провайдера полей тела запроса. Добавь карту `extra_body` к соответствующему пользовательскому провайдеру, и Hermes объединит её с каждым запросом `chat‑completions` для этой конечной точки:

```yaml
custom_providers:
  - name: gemma-local
    base_url: http://localhost:8080/v1
    model: google/gemma-4-31b-it
    extra_body:
      enable_thinking: true
      reasoning_effort: high
```

Используй структуру, описанную твоим сервером. Например, развертывания vLLM Gemma и некоторые конечные точки NVIDIA NIM ожидают `enable_thinking` внутри `chat_template_kwargs`, а не как поле верхнего уровня `extra_body`:

```yaml
extra_body:
  chat_template_kwargs:
    enable_thinking: true
```

Мастер `hermes model` → Custom Endpoint теперь явно запрашивает `api_mode` и сохраняет твой ответ в `config.yaml`. Автоматическое определение по URL (например, пути `/anthropic` → `anthropic_messages`) всё ещё происходит как запасной вариант, когда поле оставлено пустым.

**Нативная поддержка зрения для моделей пользовательских провайдеров.** Если твоя пользовательская конечная точка обслуживает модель с возможностью зрения, которой нет в `models.dev`, установи `model.supports_vision: true`, чтобы Hermes маршрутизировал прикреплённые изображения нативно (как части `image_url`), а не предварительно обрабатывал их через `vision_analyze`. Один переключатель — не нужно также задавать `agent.image_input_mode: native`.

```yaml
model:
  provider: custom
  base_url: http://localhost:8080/v1
  default: qwen3.6-35b-a3b
  supports_vision: true   # send images natively; otherwise vision_analyze pre-describes them
```

Тот же ключ учитывается для моделей отдельных именованных провайдеров (`custom_providers[*].models[*].supports_vision`) и принимает стандартные булевы значения YAML (`true/false/yes/no/on/off/1/0`).

Переключайся между ними в середине сессии с помощью тройного синтаксиса:

```
/model custom:local:qwen-2.5       # Use the "local" endpoint with qwen-2.5
/model custom:work:llama3-70b      # Use the "work" endpoint with llama3-70b
/model custom:anthropic-proxy:claude-sonnet-4  # Use the proxy
```

Ты также можешь выбрать именованные пользовательские провайдеры из интерактивного меню `hermes model`.
### Cookbook: Together AI, Groq, Perplexity

Поставщики облачных сервисов, перечисленные в [Other Compatible Providers](#other-compatible-providers), используют REST‑диалект OpenAI, поэтому их можно подключать одинаково через `custom_providers:`. Ниже три готовых рецепта. Каждый вставляется в `~/.hermes/config.yaml`, а соответствующий API‑ключ помещается в `~/.hermes/.env`.

#### Together AI

Размещает модели с открытым весом (Llama, MiniMax, Gemma, DeepSeek, Qwen) по ценам значительно ниже, чем у официальных API. Хороший вариант по умолчанию для флота из нескольких моделей.

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

Смена модели в середине сессии:

```
/model custom:together:meta-llama/Llama-3.3-70B-Instruct-Turbo
/model custom:together:google/gemma-4-31b-it
/model custom:together:deepseek-ai/DeepSeek-V3
```

Эндпоинт Together `/v1/models` работает, поэтому `hermes model` может автоматически обнаруживать доступные модели.

#### Groq

Ультрабыстрая инференция (~500 ток/с на Llama‑3.3‑70B). Небольшой каталог, но отличен для интерактивного использования с чувствительностью к задержкам.

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

Полезен, когда нужна модель, автоматически выполняющая веб‑поиск и цитирование. Доступные модели строго ограничены — проверяй текущий список в [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api).

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

#### Несколько провайдеров в одной конфигурации

Три рецепта можно комбинировать — использовать их все одновременно и переключаться по ходу работы с помощью `/model custom:<name>:<model>`:

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
- `hermes doctor` должен вывести отсутствие предупреждений `Unknown provider` для всех этих имён после исправлений валидатора CLI в #15083.
- Если эндпоинт `/v1/models` провайдера недоступен (чаще всего это Perplexity), `hermes model` сохранит модель с предупреждением, а не отвергнет её полностью — см. #15136.
- Чтобы полностью избавиться от `custom_providers:` и использовать простое `provider: custom` с переменной окружения `CUSTOM_BASE_URL`, см. #15103.
:::
### Выбор правильной конфигурации

| Сценарий использования | Рекомендация |
|----------|-------------|
| **Просто хочется, чтобы всё работало** | OpenRouter (по умолчанию) или Nous Portal |
| **Локальные модели, простая настройка** | Ollama |
| **Production GPU serving** | vLLM или SGLang |
| **Mac / без GPU** | Ollama или llama.cpp |
| **Маршрутизация между несколькими провайдерами** | LiteLLM Proxy или OpenRouter |
| **Оптимизация затрат** | ClawRouter или OpenRouter с `sort: "price"` |
| **Максимальная конфиденциальность** | Ollama, vLLM или llama.cpp (полностью локально) |
| **Enterprise / Azure** | Azure OpenAI с пользовательским endpoint |
| **Китайские AI‑модели** | z.ai (GLM), Kimi/Moonshot (`kimi-coding` или `kimi-coding-cn`), MiniMax, Xiaomi MiMo или Tencent TokenHub (провайдеры первого уровня) |

:::tip
Ты можешь переключаться между провайдерами в любой момент с помощью `hermes model` — перезапуск не требуется. История твоих разговоров, память и навыки сохраняются независимо от выбранного провайдера.
:::
## Необязательные API‑ключи

| Функция | Провайдер | Переменная окружения |
|---------|-----------|-----------------------|
| Веб‑скрейпинг | [Firecrawl](https://firecrawl.dev/) | `FIRECRAWL_API_KEY`, `FIRECRAWL_API_URL` |
| Автоматизация браузера | [Browserbase](https://browserbase.com/) | `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` |
| Генерация изображений | [FAL](https://fal.ai/) | `FAL_KEY` |
| Премиум‑голоса TTS | [ElevenLabs](https://elevenlabs.io/) | `ELEVENLABS_API_KEY` |
| OpenAI TTS + транскрипция голоса | [OpenAI](https://platform.openai.com/api-keys) | `VOICE_TOOLS_OPENAI_KEY` |
| Mistral TTS + транскрипция голоса | [Mistral](https://console.mistral.ai/) | `MISTRAL_API_KEY` |
| Кросс‑сессионное моделирование пользователя | [Honcho](https://honcho.dev/) | `HONCHO_API_KEY` |
| Семантическая долгосрочная память | [Supermemory](https://supermemory.ai) | `SUPERMEMORY_API_KEY` |

### Самохостинг Firecrawl

По умолчанию Hermes использует [облачный API Firecrawl](https://firecrawl.dev/) для веб‑поиска и скрейпинга. Если ты предпочитаешь запускать Firecrawl локально, можешь направить Hermes на собственный экземпляр. Смотри файл Firecrawl — [SELF_HOST.md](https://github.com/firecrawl/firecrawl/blob/main/SELF_HOST.md) — полные инструкции по настройке.

**Что ты получаешь:** API‑ключ не нужен, нет ограничений по скорости, нет расходов за страницу, полная суверенность над данными.

**Что ты теряешь:** Облачная версия использует фирменный «Fire‑engine» Firecrawl для продвинутого обхода анти‑ботов (Cloudflare, CAPTCHA, ротация IP). Самохостинг использует базовый `fetch` + Playwright, поэтому некоторые защищённые сайты могут не работать. Поиск осуществляется через DuckDuckGo вместо Google.

**Настройка:**

1. Клонируй и запусти стек Docker Firecrawl (5 контейнеров: API, Playwright, Redis, RabbitMQ, PostgreSQL — требуется ~4‑8 ГБ ОЗУ):
   ```bash
   git clone https://github.com/firecrawl/firecrawl
   cd firecrawl
   # In .env, set: USE_DB_AUTHENTICATION=false, HOST=0.0.0.0, PORT=3002
   docker compose up -d
   ```

2. Укажи Hermes свой экземпляр (API‑ключ не нужен):
   ```bash
   hermes config set FIRECRAWL_API_URL http://localhost:3002
   ```

Ты также можешь задать одновременно `FIRECRAWL_API_KEY` и `FIRECRAWL_API_URL`, если в твоём саморазвёрнутом экземпляре включена аутентификация.
## Маршрутизация провайдера OpenRouter

При использовании OpenRouter ты можешь управлять тем, как запросы распределяются между провайдерами. Добавь секцию `provider_routing` в `~/.hermes/config.yaml`:

```yaml
provider_routing:
  sort: "throughput"          # "price" (default), "throughput", or "latency"
  # only: ["anthropic"]      # Only use these providers
  # ignore: ["deepinfra"]    # Skip these providers
  # order: ["anthropic", "google"]  # Try providers in this order
  # require_parameters: true  # Only use providers that support all request params
  # data_collection: "deny"   # Exclude providers that may store/train on data
```

**Сокращения:** Добавляй `:nitro` к любому названию модели для сортировки по пропускной способности (например, `anthropic/claude-sonnet-4:nitro`), или `:floor` — для сортировки по цене.
## OpenRouter Pareto Code Router

OpenRouter предоставляет экспериментальный роутер моделей кодинга `openrouter/pareto-code`, который автоматически направляет запросы к самой дешёвой модели, удовлетворяющей порогу качества кода (оценённому по [Artificial Analysis](https://artificialanalysis.ai/)). Выбери эту модель и отрегулируй параметр `min_coding_score` в `~/.hermes/config.yaml`:

```yaml
model:
  provider: openrouter
  model: openrouter/pareto-code

openrouter:
  min_coding_score: 0.65   # 0.0–1.0; higher = stronger (more expensive) coders. Default 0.65.
```

Примечания:

- `min_coding_score` **отправляется** только когда `model.model` равно `openrouter/pareto-code`. Для любой другой модели значение игнорируется.
- Установи пустую строку (или удали строку), чтобы OpenRouter выбрал самого сильного доступного кодера — это задокументированное поведение при отсутствии блока `plugins`.
- Выбор детерминирован по оценке в конкретный день, но фактическая модель может измениться по мере смещения границы Парето (появление новых моделей, обновления бенчмарков).
- См. полную документацию роутера в OpenRouter — [Pareto Router docs](https://openrouter.ai/docs/guides/routing/routers/pareto-router).
- Чтобы использовать роутер Pareto Code для конкретной **вспомогательной задачи** (сжатие, компьютерное зрение и т.п.) вместо основного агента, задай `extra_body.plugins` в настройках этой задачи — см. [Auxiliary Models → OpenRouter routing & Pareto Code for auxiliary tasks](/user-guide/configuration#openrouter-routing--pareto-code-for-auxiliary-tasks).
## Fallback Providers

Настраивай цепочку резервных провайдеров, которые Hermes будет пробовать по порядку, когда основная модель не справляется (ограничения по частоте запросов, ошибки сервера, сбои аутентификации). Канонический формат — верхнеуровневый список `fallback_providers:`:

```yaml
fallback_providers:
  - provider: openrouter
    model: anthropic/claude-sonnet-4
  - provider: anthropic
    model: claude-sonnet-4
    # base_url: http://localhost:8000/v1    # optional, for custom endpoints
    # api_mode: chat_completions           # optional override
```

Устаревший однопарный словарь `fallback_model:` всё ещё поддерживается для обратной совместимости:

```yaml
fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
```

При активации запасной вариант заменяет модель и провайдера в середине сессии без потери разговора. Цепочка проверяется поэлементно; активация происходит однократно за сессию.

Поддерживаемые провайдеры: `openrouter`, `nous`, `novita`, `openai-codex`, `copilot`, `copilot-acp`, `anthropic`, `gemini`, `google-gemini-cli`, `qwen-oauth`, `huggingface`, `zai`, `kimi-coding`, `kimi-coding-cn`, `minimax`, `minimax-cn`, `minimax-oauth`, `deepseek`, `nvidia`, `xai`, `xai-oauth`, `ollama-cloud`, `bedrock`, `azure-foundry`, `opencode-zen`, `opencode-go`, `kilocode`, `xiaomi`, `arcee`, `gmi`, `stepfun`, `lmstudio`, `alibaba`, `alibaba-coding-plan`, `tencent-tokenhub`, `custom`.

:::tip
Запасные провайдеры настраиваются исключительно через `config.yaml` — или интерактивно с помощью `hermes fallback`. Подробности о том, когда происходит срабатывание, как продвигается цепочка и как это взаимодействует с вспомогательными задачами и делегированием, смотри [Fallback Providers](/user-guide/features/fallback-providers).
:::
## См. также

- [Конфигурация](/user-guide/configuration) — Общая конфигурация (структура каталогов, приоритет конфигураций, терминальные бэкенды, память, сжатие и др.)
- [Переменные окружения](/reference/environment-variables) — Полный справочник всех переменных окружения