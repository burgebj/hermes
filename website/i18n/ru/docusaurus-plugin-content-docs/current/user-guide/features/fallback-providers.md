---
title: Запасные провайдеры
description: Настрой автоматический откат на резервных провайдеров LLM, когда твоя основная модель недоступна.
sidebar_label: Fallback Providers
sidebar_position: 8
---

# Запасные варианты провайдеров

Hermes Agent имеет три уровня устойчивости, которые поддерживают работу твоих сессий, когда у провайдеров возникают проблемы:

1. **[Пулы учётных данных](./credential-pools.md)** — ротация между несколькими API‑ключами одного и того же провайдера (используется первой)
2. **Запасной вариант основной модели** — автоматически переключается на *другого* провайдера : модель, когда основная модель выходит из строя
3. **Запасной вариант вспомогательной задачи** — независимое разрешение провайдера для побочных задач, таких как зрение, сжатие и веб‑извлечение

Пулы учётных данных обеспечивают ротацию внутри одного провайдера (например, несколько ключей OpenRouter). Эта страница описывает кросс‑провайдерный запасной вариант. Оба механизма являются опциональными и работают независимо.
## Запасной вариант основной модели

Когда основной провайдер LLM сталкивается с ошибками — ограничениями скорости, перегрузкой сервера, сбоями аутентификации, разрывами соединения — Hermes может автоматически переключиться на резервный набор **провайдер:модель** в середине сессии, не теряя диалог.

### Конфигурация

Самый простой путь — интерактивный менеджер:

```bash
hermes fallback
```

`hermes fallback` переиспользует выбор провайдера из `hermes model` — тот же список провайдеров, те же запросы учётных данных, та же валидация. Используй подкоманды `add`, `list` (alias `ls`), `remove` (alias `rm`) и `clear` для управления цепочкой. Изменения сохраняются в списке верхнего уровня `fallback_providers:` в `config.yaml`.

Если предпочитаешь редактировать YAML напрямую, добавь секцию `fallback_model` в `~/.hermes/config.yaml`:

```yaml
fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
```

Оба поля `provider` и `model` **обязательны**. Если какое‑то из них отсутствует, запасной вариант отключается.

:::note `fallback_model` vs `fallback_providers`
`fallback_model` (единственное число) — устаревший ключ единственного запасного варианта; Hermes всё ещё учитывает его для обратной совместимости. `fallback_providers` (множественное число, список) поддерживает несколько запасных вариантов, проверяемых по порядку; `hermes fallback` записывает в этот ключ. Когда оба заданы, Hermes объединяет их, при этом приоритет имеет `fallback_providers`.
:::

### Поддерживаемые провайдеры

| Провайдер | Значение | Требования |
|----------|----------|------------|
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` |
| Nous Portal | `nous` | `hermes setup --portal` (fresh) или `hermes auth add nous` (OAuth) |
| OpenAI Codex | `openai-codex` | `hermes model` (ChatGPT OAuth) |
| GitHub Copilot | `copilot` | `COPILOT_GITHUB_TOKEN`, `GH_TOKEN` или `GITHUB_TOKEN` |
| GitHub Copilot ACP | `copilot-acp` | внешний процесс (интеграция в редактор) |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` или учётные данные Claude Code |
| z.ai / GLM | `zai` | `GLM_API_KEY` |
| Kimi / Moonshot | `kimi-coding` | `KIMI_API_KEY` |
| MiniMax | `minimax` | `MINIMAX_API_KEY` |
| MiniMax (Китай) | `minimax-cn` | `MINIMAX_CN_API_KEY` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` |
| NVIDIA NIM | `nvidia` | `NVIDIA_API_KEY` (опционально: `NVIDIA_BASE_URL`) |
| GMI Cloud | `gmi` | `GMI_API_KEY` (опционально: `GMI_BASE_URL`) |
| StepFun | `stepfun` | `STEPFUN_API_KEY` (опционально: `STEPFUN_BASE_URL`) |
| Ollama Cloud | `ollama-cloud` | `OLLAMA_API_KEY` |
| Google Gemini (OAuth) | `google-gemini-cli` | `hermes model` (Google OAuth; опционально: `HERMES_GEMINI_PROJECT_ID`) |
| Google AI Studio | `gemini` | `GOOGLE_API_KEY` (alias: `GEMINI_API_KEY`) |
| xAI (Grok) | `xai` (alias `grok`) | `XAI_API_KEY` (опционально: `XAI_BASE_URL`) |
| xAI Grok OAuth (SuperGrok) | `xai-oauth` (alias `grok-oauth`) | `hermes model` → xAI Grok OAuth (вход в браузере; подписка SuperGrok) |
| AWS Bedrock | `bedrock` | стандартная аутентификация boto3 (`AWS_REGION` + `AWS_PROFILE` или `AWS_ACCESS_KEY_ID`) |
| Qwen Portal (OAuth) | `qwen-oauth` | `hermes model` (Qwen Portal OAuth; опционально: `HERMES_QWEN_BASE_URL`) |
| MiniMax (OAuth) | `minimax-oauth` | `hermes model` (MiniMax portal OAuth) |
| OpenCode Zen | `opencode-zen` | `OPENCODE_ZEN_API_KEY` |
| OpenCode Go | `opencode-go` | `OPENCODE_GO_API_KEY` |
| Kilo Code | `kilocode` | `KILOCODE_API_KEY` |
| Xiaomi MiMo | `xiaomi` | `XIAOMI_API_KEY` |
| Arcee AI | `arcee` | `ARCEEAI_API_KEY` |
| Alibaba / DashScope | `alibaba` | `DASHSCOPE_API_KEY` |
| Alibaba Coding Plan | `alibaba-coding-plan` | `ALIBABA_CODING_PLAN_API_KEY` (переходит к `DASHSCOPE_API_KEY`) |
| Kimi / Moonshot (Китай) | `kimi-coding-cn` | `KIMI_CN_API_KEY` |
| Tencent TokenHub | `tencent-tokenhub` | `TOKENHUB_API_KEY` |
| Microsoft Foundry | `azure-foundry` | `AZURE_FOUNDRY_API_KEY` + `AZURE_FOUNDRY_BASE_URL` |
| LM Studio (локально) | `lmstudio` | `LM_API_KEY` (или без него для локального) + `LM_BASE_URL` |
| Hugging Face | `huggingface` | `HF_TOKEN` |
| Пользовательский эндпоинт | `custom` | `base_url` + `key_env` (см. ниже) |

### Пользовательский эндпоинт для запасного варианта

Для пользовательского совместимого с OpenAI эндпоинта добавь `base_url` и, при необходимости, `key_env`:

```yaml
fallback_model:
  provider: custom
  model: my-local-model
  base_url: http://localhost:8000/v1
  key_env: MY_LOCAL_KEY              # env var name containing the API key
```

### Когда срабатывает запасной вариант

Запасной вариант активируется автоматически, когда основная модель терпит неудачу по следующим причинам:

- **Ограничения скорости** (HTTP 429) — после исчерпания попыток повторов
- **Ошибки сервера** (HTTP 500, 502, 503) — после исчерпания попыток повторов
- **Сбои аутентификации** (HTTP 401, 403) — сразу (нет смысла повторять)
- **Не найдено** (HTTP 404) — сразу
- **Недопустимые ответы** — когда API возвращает некорректные или пустые ответы многократно

При срабатывании Hermes:

1. Получает учётные данные для запасного провайдера;
2. Создаёт новый API‑клиент;
3. Меняет модель, провайдера и клиент «на месте»;
4. Сбрасывает счётчик повторов и продолжает диалог.

Переключение происходит без видимых прерываний — история диалога, вызовы инструментов и контекст сохраняются. Агент продолжает работу точно с того места, где остановился, лишь используя другую модель.

:::info По‑ходу‑хода, а не по‑сессии
Запасной вариант **привязан к отдельному ходу**: каждое новое сообщение пользователя начинается с восстановленной основной модели. Если основная модель падает в середине хода, запасной вариант активируется только для этого хода. При следующем сообщении Hermes снова пытается использовать основную модель. В рамках одного хода запасной вариант может сработать максимум один раз — если он тоже падает, применяется обычная обработка ошибок (повторы, затем сообщение об ошибке). Это предотвращает каскадные циклы переключения внутри хода, одновременно давая основной модели шанс каждый новый ход.
:::

### Примеры

**OpenRouter как запасной вариант для Anthropic native:**
```yaml
model:
  provider: anthropic
  default: claude-sonnet-4-6

fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
```

**Nous Portal как запасной вариант для OpenRouter:**
```yaml
model:
  provider: openrouter
  default: anthropic/claude-opus-4

fallback_model:
  provider: nous
  model: nous-hermes-3
```

**Локальная модель как запасной вариант для облачной:**
```yaml
fallback_model:
  provider: custom
  model: llama-3.1-70b
  base_url: http://localhost:8000/v1
  key_env: LOCAL_API_KEY
```

**Codex OAuth как запасной вариант:**
```yaml
fallback_model:
  provider: openai-codex
  model: gpt-5.3-codex
```

### Где работает запасной вариант

| Контекст | Поддержка запасного варианта |
|----------|-----------------------------|
| CLI‑сессии | ✔ |
| Шлюз обмена сообщениями (Telegram, Discord и др.) | ✔ |
| Делегирование субагенту | ✘ (субагенты не наследуют конфигурацию запасного варианта) |
| Cron‑задачи | ✘ (запускаются с фиксированным провайдером) |
| Вспомогательные задачи (vision, compression) | ✘ (используют собственную цепочку провайдеров — см. ниже) |

:::tip
Для `fallback_model` нет переменных окружения — он настраивается исключительно через `config.yaml`. Это сделано намеренно: конфигурация запасного варианта должна быть осознанным выбором, а не переопределяться устаревшими экспортами из оболочки.
:::

---
## Запасной (вариант) вспомогательной задачи

Hermes использует отдельные лёгкие модели для побочных задач. Каждая задача имеет собственную цепочку разрешения провайдера, которая выступает в качестве встроенной системы запасного (фоллбэк) варианта.

### Задачи с независимым разрешением провайдера

| Задача | Что делает | Ключ конфигурации |
|--------|------------|-------------------|
| Vision | Анализ изображений, скриншоты браузера | `auxiliary.vision` |
| Web Extract | Сводка веб‑страницы | `auxiliary.web_extract` |
| Compression | Сводки сжатия контекста | `auxiliary.compression` |
| Skills Hub | Поиск и открытие навыков | `auxiliary.skills_hub` |
| MCP | Операции‑помощники MCP | `auxiliary.mcp` |
| Approval | Классификация одобрения умных команд | `auxiliary.approval` |
| Title Generation | Сводки заголовков сессии | `auxiliary.title_generation` |
| Triage Specifier | `hermes kanban specify` / кнопка dashboard ✨ — превращает однострочную задачу триажа в реальную спецификацию | `auxiliary.triage_specifier` |

### Цепочка автоопределения

Когда провайдер задачи установлен в `"auto"` (значение по умолчанию), Hermes пробует провайдеры по порядку, пока один не сработает:

**Для текстовых задач (compression, web extract и др.):**

```text
OpenRouter → Nous Portal → Custom endpoint → Codex OAuth →
API-key providers (z.ai, Kimi, MiniMax, Xiaomi MiMo, Hugging Face, Anthropic) → give up
```

**Для задач зрения:**

```text
Main provider (if vision-capable) → OpenRouter → Nous Portal →
Codex OAuth → Anthropic → Custom endpoint → give up
```

Если выбранный провайдер не удаётся вызвать, у Hermes также есть внутренний повтор: если провайдер не OpenRouter и явно не указан `base_url`, в качестве последнего запаса используется OpenRouter.

### Настройка вспомогательных провайдеров

Каждую задачу можно настраивать независимо в `config.yaml`:

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

Все задачи выше следуют одной и той же схеме **provider / model / base_url**. Сжатие контекста настраивается под `auxiliary.compression`:

```yaml
auxiliary:
  compression:
    provider: main                                    # Same provider options as other auxiliary tasks
    model: google/gemini-3-flash-preview
    base_url: null                                    # Custom OpenAI-compatible endpoint
```

А модель‑запас используется:

```yaml
fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4
  # base_url: http://localhost:8000/v1               # Optional custom endpoint
```

Все три — auxiliary, compression, fallback — работают одинаково: задаёшь `provider`, чтобы выбрать, кто обрабатывает запрос, `model` — какую модель использовать, и `base_url` — куда направить запрос (переопределяет провайдера).

### Параметры провайдера для вспомогательных задач

Эти параметры применимы только к конфигурациям `auxiliary:`, `compression:` и `fallback_model:` — `"main"` **не является** допустимым значением для вашего верхнеуровневого `model.provider`. Для пользовательских конечных точек используй `provider: custom` в секции `model:` (см. [AI Providers](/integrations/providers)).

| Провайдер | Описание | Требования |
|----------|----------|------------|
| `"auto"` | Пробовать провайдеры по порядку, пока один не сработает (по умолчанию) | Должен быть настроен хотя бы один провайдер |
| `"openrouter"` | Принудительно использовать OpenRouter | `OPENROUTER_API_KEY` |
| `"nous"` | Принудительно использовать Nous Portal | `hermes auth` |
| `"codex"` | Принудительно использовать Codex OAuth | `hermes model` → Codex |
| `"main"` | Использовать тот же провайдер, что и основной агент (только для вспомогательных задач) | Настроен активный основной провайдер |
| `"anthropic"` | Принудительно использовать нативный Anthropic | `ANTHROPIC_API_KEY` или учётные данные Claude Code |

### Прямое переопределение конечной точки

Для любой вспомогательной задачи указание `base_url` полностью обходит разрешение провайдера и отправляет запросы напрямую к этой конечной точке:

```yaml
auxiliary:
  vision:
    base_url: "http://localhost:1234/v1"
    api_key: "local-key"
    model: "qwen2.5-vl"
```

`base_url` имеет приоритет над `provider`. Hermes использует настроенный `api_key` для аутентификации, при отсутствии — переходит к `OPENAI_API_KEY`. Он **не** переиспользует `OPENROUTER_API_KEY` для пользовательских конечных точек.
## Auxiliary Capacity-Error Fallback

Когда ты задаёшь явный вспомогательный провайдер (например, `auxiliary.vision.provider: glm`), Hermes рассматривает его как предпочтительный выбор — но если провайдер буквально не может выполнить запрос из‑за **capacity error** (HTTP 402 payment required, HTTP 429 exhaustion daily‑quota, сбой соединения), Hermes переходит к цепочке запасных (вариантов) вместо тихого отказа:

1. **Primary aux provider** — тот, который ты настроил (первый, всегда)
2. **`auxiliary.<task>.fallback_chain`** — твой список переопределений для задачи, если ты его создал
3. **Main agent provider + model** — последняя страховка (всегда пробуется, даже если ты не задавал цепочку)
4. **Warn + re-raise** — если каждый уровень не удался, Hermes записывает `Auxiliary <task>: ... all fallbacks exhausted` на уровне **WARNING** и повторно выбрасывает исходную ошибку

Временные ограничения HTTP 429 (`Retry-After: …`) рассматриваются как ограничения запроса, а не как проблемы ёмкости — они уважают твой явный выбор провайдера и **не** активируют лестницу запасных (вариантов). Только исчерпание дневного/месячного лимита, ошибки оплаты и сбои соединения обходят шлюз явного провайдера.

Для пользователей с `provider: auto` (без явного вспомогательного провайдера) существующая цепочка автоопределения работает вместо шагов 2‑3. Её первый шаг уже является основной моделью агента, поэтому пользователи `auto` получают тот же результат без какой‑либо конфигурации.

### Optional: per-task fallback chain

Если тебе нужен порядок запасных (вариантов), отличный от «сначала основная модель агента», явно задай `fallback_chain`. Каждый элемент должен содержать минимум `provider`; `model`, `base_url` и `api_key` являются опциональными.

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

Тебе **не нужно** настраивать `fallback_chain`, чтобы получить запасной (вариант) — страховка основного агента работает независимо от этого. Используй её только когда действительно нужен иной порядок, чем по умолчанию.

### Provider quota errors that trigger fallback

Hermes распознаёт их как эквивалент capacity‑error к 402 credit exhaustion (не временные ограничения скорости):

- Bedrock / LiteLLM: `Too many tokens per day`, `daily limit`, `tokens per day`
- Vertex AI / GCP: `quota exceeded`, `resource exhausted`, `RESOURCE_EXHAUSTED`
- Generic: `daily quota`, `quota_exceeded`

Если твой провайдер возвращает другую фразу при исчерпании дневного лимита и Hermes не активирует запасной (вариант), это баг — открой issue с точной строкой ошибки.
## Запасной вариант сжатия контекста

Сжатие контекста использует блок конфигурации `auxiliary.compression` для управления тем, какая модель и провайдер выполняют суммирование:

```yaml
auxiliary:
  compression:
    provider: "auto"                              # auto | openrouter | nous | main
    model: "google/gemini-3-flash-preview"
```

:::info Legacy migration
Старые конфигурации с `compression.summary_model` / `compression.summary_provider` / `compression.summary_base_url` автоматически мигрируют в `auxiliary.compression.*` при первой загрузке (версия конфигурации 17).
:::

Если для сжатия нет доступного провайдера, Hermes отбрасывает промежуточные реплики диалога без генерации резюме, вместо того чтобы прервать сессию.

---
## Переопределение провайдера делегирования

Субагенты, создаваемые `delegate_task`, **не** используют основную запасную модель. Однако их можно перенаправить к другой паре provider:model для оптимизации затрат:

```yaml
delegation:
  provider: "openrouter"                      # override provider for all subagents
  model: "google/gemini-3-flash-preview"      # override model
  # base_url: "http://localhost:1234/v1"      # or use a direct endpoint
  # api_key: "local-key"
```

См. [Делегирование субагентов](/user-guide/features/delegation) для полных деталей конфигурации.

---
## Провайдеры Cron‑задач

Cron‑задачи выполняются с тем провайдером, который указан в момент их запуска. Они не поддерживают модель запасного (fallback) варианта. Чтобы использовать другой провайдер для cron‑задач, укажи переопределения `provider` и `model` непосредственно в самой cron‑задаче:

```python
cronjob(
    action="create",
    schedule="every 2h",
    prompt="Check server status",
    provider="openrouter",
    model="google/gemini-3-flash-preview"
)
```

См. [Запланированные задачи (Cron)](/user-guide/features/cron) для получения полной информации о конфигурации.

---
## Краткое содержание

| Функция | Механизм запасного (варианта) | Расположение конфигурации |
|---------|------------------------------|----------------------------|
| Основная модель агента | `fallback_model` в `config.yaml` — переключение при ошибках на каждый ход (основная модель восстанавливается каждый ход) | `fallback_model:` (верхний уровень) |
| Вспомогательные задачи (любые) — автоопределение | Полная цепочка автоопределения (сначала основная модель агента, затем цепочка провайдеров) при ошибках ограничения ресурсов | `auxiliary.<task>.provider: auto` |
| Вспомогательные задачи (любые) — явный провайдер | `fallback_chain` (если задан) → основная модель агента → предупреждение + исключение, только при ошибках ограничения ресурсов | `auxiliary.<task>.fallback_chain` |
| Зрение | Многоуровневый (см. выше) + внутренний повтор OpenRouter | `auxiliary.vision` |
| Веб‑извлечение | Многоуровневый (см. выше) + внутренний повтор OpenRouter | `auxiliary.web_extract` |
| Сжатие контекста | Многоуровневый (см. выше); переходит к отсутствию резюме, если все уровни недоступны | `auxiliary.compression` |
| Центр навыков | Многоуровневый (см. выше) | `auxiliary.skills_hub` |
| MCP‑помощники | Многоуровневый (см. выше) | `auxiliary.mcp` |
| Классификация одобрения | Многоуровневый (см. выше) | `auxiliary.approval` |
| Генерация заголовка | Многоуровневый (см. выше) | `auxiliary.title_generation` |
| Триаж‑указатель | Многоуровневый (см. выше) | `auxiliary.triage_specifier` |
| Делегирование | Только переопределение провайдера (автоматический запасной вариант отсутствует) | `delegation.provider` / `delegation.model` |
| Cron‑задачи | Только переопределение провайдера для каждой задачи (автоматический запасной вариант отсутствует) | Per-job `provider` / `model` |