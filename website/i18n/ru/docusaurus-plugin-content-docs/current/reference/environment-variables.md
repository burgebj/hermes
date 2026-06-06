---
sidebar_position: 2
title: "Переменные окружения"
description: "Полный справочник всех переменных окружения, используемых Hermes Agent"
---

# Справочник переменных окружения

Все переменные находятся в файле `~/.hermes/.env`. Их также можно задать с помощью команды `hermes config set VAR value`.
## Поставщики LLM

| Переменная | Описание |
|----------|-------------|
| `OPENROUTER_API_KEY` | Ключ API OpenRouter (рекомендовано для гибкости) |
| `OPENROUTER_BASE_URL` | Переопределить совместимый с OpenRouter базовый URL |
| `HERMES_OPENROUTER_CACHE` | Включить кэширование ответов OpenRouter (`1`/`true`/`yes`/`on`). Переопределяет `openrouter.response_cache` в `config.yaml`. См. [Response Caching](https://openrouter.ai/docs/guides/features/response-caching). |
| `HERMES_OPENROUTER_CACHE_TTL` | TTL кэша в секундах (1‑86400). Переопределяет `openrouter.response_cache_ttl` в `config.yaml`. |
| `NOUS_BASE_URL` | Переопределить базовый URL Nous Portal (редко требуется; только для разработки/тестирования) |
| `NOUS_INFERENCE_BASE_URL` | Переопределить конечную точку инференса Nous напрямую |
| `OPENAI_API_KEY` | Ключ API для пользовательских совместимых с OpenAI конечных точек (используется с `OPENAI_BASE_URL`) |
| `OPENAI_BASE_URL` | Базовый URL для пользовательской конечной точки (VLLM, SGLang и др.) |
| `COPILOT_GITHUB_TOKEN` | Токен GitHub для API Copilot — приоритет первый (OAuth `gho_*` или гранулированный PAT `github_pat_*`; классические PAT `ghp_*` **не поддерживаются**) |
| `GH_TOKEN` | Токен GitHub — приоритет второй для Copilot (также используется CLI `gh`) |
| `GITHUB_TOKEN` | Токен GitHub — приоритет третий для Copilot |
| `HERMES_COPILOT_ACP_COMMAND` | Переопределить путь к бинарнику Copilot ACP CLI (по умолчанию: `copilot`) |
| `COPILOT_CLI_PATH` | Псевдоним для `HERMES_COPILOT_ACP_COMMAND` |
| `HERMES_COPILOT_ACP_ARGS` | Переопределить аргументы Copilot ACP (по умолчанию: `--acp --stdio`) |
| `COPILOT_ACP_BASE_URL` | Переопределить базовый URL Copilot ACP |
| `GLM_API_KEY` | Ключ API z.ai / ZhipuAI GLM ([z.ai](https://z.ai)) |
| `ZAI_API_KEY` | Псевдоним для `GLM_API_KEY` |
| `Z_AI_API_KEY` | Псевдоним для `GLM_API_KEY` |
| `GLM_BASE_URL` | Переопределить базовый URL z.ai (по умолчанию: `https://api.z.ai/api/paas/v4`) |
| `KIMI_API_KEY` | Ключ API Kimi / Moonshot AI ([moonshot.ai](https://platform.moonshot.ai)) |
| `KIMI_BASE_URL` | Переопределить базовый URL Kimi (по умолчанию: `https://api.moonshot.ai/v1`) |
| `KIMI_CN_API_KEY` | Ключ API Kimi / Moonshot China ([moonshot.cn](https://platform.moonshot.cn)) |
| `ARCEEAI_API_KEY` | Ключ API Arcee AI ([chat.arcee.ai](https://chat.arcee.ai/)) |
| `ARCEE_BASE_URL` | Переопределить базовый URL Arcee (по умолчанию: `https://api.arcee.ai/api/v1`) |
| `GMI_API_KEY` | Ключ API GMI Cloud ([gmicloud.ai](https://www.gmicloud.ai/)) |
| `GMI_BASE_URL` | Переопределить базовый URL GMI Cloud (по умолчанию: `https://api.gmi-serving.com/v1`) |
| `MINIMAX_API_KEY` | Ключ API MiniMax — глобальная конечная точка ([minimax.io](https://www.minimax.io)). **Не используется `minimax-oauth`** (OAuth‑путь использует вход через браузер). |
| `MINIMAX_BASE_URL` | Переопределить базовый URL MiniMax (по умолчанию: `https://api.minimax.io/anthropic` — Hermes использует совместимую с Anthropic Messages конечную точку MiniMax). **Не используется `minimax-oauth`**. |
| `MINIMAX_CN_API_KEY` | Ключ API MiniMax — китайская конечная точка ([minimaxi.com](https://www.minimaxi.com)). **Не используется `minimax-oauth`** (OAuth‑путь использует вход через браузер). |
| `MINIMAX_CN_BASE_URL` | Переопределить базовый URL MiniMax China (по умолчанию: `https://api.minimaxi.com/anthropic`). **Не используется `minimax-oauth`**. |
| `KILOCODE_API_KEY` | Ключ API Kilo Code ([kilo.ai](https://kilo.ai)) |
| `KILOCODE_BASE_URL` | Переопределить базовый URL Kilo Code (по умолчанию: `https://api.kilo.ai/api/gateway`) |
| `XIAOMI_API_KEY` | Ключ API Xiaomi MiMo ([platform.xiaomimimo.com](https://platform.xiaomimimo.com)) |
| `XIAOMI_BASE_URL` | Переопределить базовый URL Xiaomi MiMo (по умолчанию: `https://api.xiaomimimo.com/v1`) |
| `TOKENHUB_API_KEY` | Ключ API Tencent TokenHub ([tokenhub.tencentmaas.com](https://tokenhub.tencentmaas.com)) |
| `TOKENHUB_BASE_URL` | Переопределить базовый URL Tencent TokenHub (по умолчанию: `https://tokenhub.tencentmaas.com/v1`) |
| `AZURE_FOUNDRY_API_KEY` | Ключ API Microsoft Foundry / Azure OpenAI ([ai.azure.com](https://ai.azure.com/)). Не нужен, если `model.auth_mode: entra_id` |
| `AZURE_FOUNDRY_BASE_URL` | URL конечной точки Microsoft Foundry (например, `https://<resource>.openai.azure.com/openai/v1` для стиля OpenAI или `https://<resource>.services.ai.azure.com/anthropic` для стиля Anthropic) |
| `AZURE_ANTHROPIC_KEY` | Ключ API Azure Anthropic для `provider: anthropic` + `base_url`, указывающего на развертывание Claude в Microsoft Foundry (альтернатива `ANTHROPIC_API_KEY`, когда настроены и Anthropic, и Azure Anthropic) |
| `AZURE_TENANT_ID` | Идентификатор арендатора Entra ID (потоки service‑principal; учитывается `azure-identity`, когда `model.auth_mode: entra_id`) |
| `AZURE_CLIENT_ID` | Идентификатор клиента Entra ID (service principal, workload identity или user‑assigned managed identity) |
| `AZURE_CLIENT_SECRET` | Секрет service principal, используемый `EnvironmentCredential` |
| `AZURE_CLIENT_CERTIFICATE_PATH` | Сертификат service principal (альтернатива `AZURE_CLIENT_SECRET`) |
| `AZURE_FEDERATED_TOKEN_FILE` | Путь к файлу федеративного токена для AKS Workload Identity / OIDC потоков |
| `AZURE_AUTHORITY_HOST` | Переопределение authority для суверенных облаков (например, `https://login.microsoftonline.us` для Azure Government). См. [Azure Foundry guide](/guides/azure-foundry#sovereign-clouds-government-china) |
| `IDENTITY_ENDPOINT` / `MSI_ENDPOINT` | Конечная точка Managed Identity для App Service, Functions и Container Apps; обычно VMs используют IMDS и не задают эти переменные |
| `HF_TOKEN` | Токен Hugging Face для провайдеров инференса ([huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)) |
| `HF_BASE_URL` | Переопределить базовый URL Hugging Face (по умолчанию: `https://router.huggingface.co/v1`) |
| `GOOGLE_API_KEY` | Ключ API Google AI Studio ([aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)) |
| `GEMINI_API_KEY` | Псевдоним для `GOOGLE_API_KEY` |
| `GEMINI_BASE_URL` | Переопределить базовый URL Google AI Studio |
| `HERMES_GEMINI_CLIENT_ID` | OAuth‑клиент ID для PKCE‑входа `google-gemini-cli` (необязательно; по умолчанию используется публичный клиент gemini‑cli от Google) |
| `HERMES_GEMINI_CLIENT_SECRET` | OAuth‑секрет клиента для `google-gemini-cli` (необязательно) |
| `HERMES_GEMINI_PROJECT_ID` | Идентификатор проекта GCP для платных уровней Gemini (бесплатный уровень автоматически provisioned) |
| `ANTHROPIC_API_KEY` | Ключ API Anthropic Console ([console.anthropic.com](https://console.anthropic.com/)) |
| `ANTHROPIC_TOKEN` | Ручной или устаревший токен/override OAuth Anthropic |
| `DASHSCOPE_API_KEY` | Ключ API Qwen Cloud (Alibaba DashScope) для моделей Qwen ([modelstudio.console.alibabacloud.com](https://modelstudio.console.alibabacloud.com/)) |
| `DASHSCOPE_BASE_URL` | Пользовательский базовый URL DashScope (по умолчанию: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`; используйте `https://dashscope.aliyuncs.com/compatible-mode/v1` для региона mainland‑China) |
| `DEEPSEEK_API_KEY` | Ключ API DeepSeek для прямого доступа ([platform.deepseek.com](https://platform.deepseek.com/api_keys)) |
| `DEEPSEEK_BASE_URL` | Пользовательский базовый URL DeepSeek API |
| `NOVITA_API_KEY` | Ключ API NovitaAI — AI‑нативное облако для Model API, Agent Sandbox и GPU Cloud ([novita.ai/settings/key-management](https://novita.ai/settings/key-management)) |
| `NOVITA_BASE_URL` | Переопределить базовый URL NovitaAI (по умолчанию: `https://api.novita.ai/openai/v1`) |
| `NVIDIA_API_KEY` | Ключ API NVIDIA NIM — Nemotron и открытые модели ([build.nvidia.com](https://build.nvidia.com)) |
| `NVIDIA_BASE_URL` | Переопределить базовый URL NVIDIA (по умолчанию: `https://integrate.api.nvidia.com/v1`; установить `http://localhost:8000/v1` для локальной NIM‑конечной точки) |
| `STEPFUN_API_KEY` | Ключ API StepFun — модели серии Step ([platform.stepfun.com](https://platform.stepfun.com)) |
| `STEPFUN_BASE_URL` | Переопределить базовый URL StepFun (по умолчанию: `https://api.stepfun.com/v1`) |
| `OLLAMA_API_KEY` | Ключ API Ollama Cloud — управляемый каталог Ollama без локального GPU ([ollama.com/settings/keys](https://ollama.com/settings/keys)) |
| `OLLAMA_BASE_URL` | Переопределить базовый URL Ollama Cloud (по умолчанию: `https://ollama.com/v1`) |
| `XAI_API_KEY` | Ключ API xAI (Grok) для чата + TTS + веб‑поиска ([console.x.ai](https://console.x.ai/)) |
| `XAI_BASE_URL` | Переопределить базовый URL xAI (по умолчанию: `https://api.x.ai/v1`) |
| `MISTRAL_API_KEY` | Ключ API Mistral для Voxtral TTS и Voxtral STT ([console.mistral.ai](https://console.mistral.ai)) |
| `AWS_REGION` | Регион AWS для инференса Bedrock (например, `us-east-1`, `eu-central-1`). Читается boto3. |
| `AWS_PROFILE` | Именованный профиль AWS для аутентификации Bedrock (чтение `~/.aws/credentials`). Оставь пустым, чтобы использовать цепочку учётных данных boto3 по умолчанию. |
| `BEDROCK_BASE_URL` | Переопределить базовый URL runtime Bedrock (по умолчанию: `https://bedrock-runtime.us-east-1.amazonaws.com`; обычно оставляют пустым и используют `AWS_REGION`) |
| `HERMES_QWEN_BASE_URL` | Переопределить базовый URL Qwen Portal (по умолчанию: `https://portal.qwen.ai/v1`) |
| `OPENCODE_ZEN_API_KEY` | Ключ API OpenCode Zen — pay‑as‑you‑go доступ к курируемым моделям ([opencode.ai](https://opencode.ai/auth)) |
| `OPENCODE_ZEN_BASE_URL` | Переопределить базовый URL OpenCode Zen |
| `OPENCODE_GO_API_KEY` | Ключ API OpenCode Go — подписка $10/мес для открытых моделей ([opencode.ai](https://opencode.ai/auth)) |
| `OPENCODE_GO_BASE_URL` | Переопределить базовый URL OpenCode Go |
| `CLAUDE_CODE_OAUTH_TOKEN` | Явный переопределяющий токен Claude Code, если экспортировать вручную |
| `HERMES_MODEL` | Переопределить имя модели на уровне процесса (используется планировщиком cron; для обычного использования предпочтительнее `config.yaml`) |
| `VOICE_TOOLS_OPENAI_KEY` | Предпочтительный ключ OpenAI для провайдеров speech‑to‑text и text‑to‑speech |
| `HERMES_LOCAL_STT_COMMAND` | Необязательный шаблон локальной команды speech‑to‑text. Поддерживает плейсхолдеры `{input_path}`, `{output_dir}`, `{language}` и `{model}` |
| `HERMES_LOCAL_STT_LANGUAGE` | Язык по умолчанию, передаваемый в `HERMES_LOCAL_STT_COMMAND` или автоматически определяемый локальным fallback `whisper` CLI (по умолчанию: `en`) |
| `HERMES_HOME` | Переопределить каталог конфигурации Hermes (по умолчанию: `~/.hermes`). Также задаёт PID‑файл шлюза и имя systemd‑службы, позволяя нескольким установкам работать одновременно |
| `HERMES_GIT_BASH_PATH` | **Только Windows.** Переопределить поиск `bash.exe` для инструмента терминала. Может указывать на любой bash — полную установку Git‑for‑Windows, WSL bash через symlink, MSYS2, Cygwin. Инсталлятор автоматически задаёт путь к PortableGit. См. [Windows (Native) Guide](../user-guide/windows-native.md#how-hermes-runs-shell-commands-on-windows) |
| `HERMES_DISABLE_WINDOWS_UTF8` | **Только Windows.** Установить `1`, чтобы отключить shim UTF‑8 stdio (`configure_windows_stdio()`) и вернуться к кодовой странице консоли. Полезно для отладки проблем кодировки; редко требуется в обычной работе |
| `HERMES_KANBAN_HOME` | Переопределить общий корень Hermes, привязывающий доску Kanban (БД + рабочие пространства + логи воркеров). При отсутствии — `get_default_hermes_root()` (родитель любого активного профиля). Полезно для тестов и необычных развертываний |
| `HERMES_KANBAN_BOARD` | Закрепить активную доску Kanban для данного процесса. Имеет приоритет над `~/.hermes/kanban/current`; диспетчер передаёт её в окружение подпроцессов воркеров, чтобы они физически не видели задачи на других досках. По умолчанию `default`. Валидация слага: строчные буквы, цифры, дефисы и подчёркивания, 1‑64 символа |
| `HERMES_KANBAN_DB` | Закрепить путь к файлу базы данных Kanban напрямую (самый высокий приоритет; переопределяет `HERMES_KANBAN_BOARD` и `HERMES_KANBAN_HOME`). Диспетчер передаёт её в окружение воркеров, чтобы они использовали одну и ту же доску |
| `HERMES_KANBAN_WORKSPACES_ROOT` | Закрепить корень рабочих пространств Kanban напрямую (самый высокий приоритет для рабочих пространств; переопределяет `HERMES_KANBAN_HOME`). Диспетчер передаёт её в окружение воркеров |
| `HERMES_KANBAN_DISPATCH_IN_GATEWAY` | Переопределение выполнения `kanban.dispatch_in_gateway` во время работы. Установи `0`, `false`, `no` или `off`, чтобы шлюз не запускал встроенный диспетчер Kanban; любое другое непустое значение включает его. Полезно, когда отдельный процесс‑диспетчер владеет доской. |
## Авторизация провайдера (OAuth)

Для нативной аутентификации Anthropic Hermes предпочитает использовать собственные файлы учётных данных Claude Code, если они существуют, поскольку такие учётные данные могут автоматически обновляться. **OAuth для Anthropic требует плана Claude Max с приобретёнными дополнительными кредитами использования** — Hermes работает от имени Claude Code, который использует только дополнительные кредиты плана Max, а не базовое выделение Max, и не работает с Claude Pro. Если у тебя нет Max + дополнительных кредитов, используй API‑ключ. Переменные окружения, такие как `ANTHROPIC_TOKEN`, остаются полезными как ручные переопределения, но они больше не являются предпочтительным способом входа в Claude Max.

| Variable | Description |
|----------|-------------|
| `HERMES_PORTAL_BASE_URL` | Переопределить URL Nous Portal (для разработки/тестирования) |
| `NOUS_INFERENCE_BASE_URL` | Переопределить URL API инференса Nous |
| `HERMES_NOUS_MIN_KEY_TTL_SECONDS` | Минимальное время жизни ключа агента перед пере‑созданием (по умолчанию: 1800 = 30 мин) |
| `HERMES_NOUS_TIMEOUT_SECONDS` | Таймаут HTTP для потоков учётных данных / токенов Nous |
| `HERMES_DUMP_REQUESTS` | Сохранять полезные нагрузки запросов API в файлы журналов (`true`/`false`) |
| `HERMES_PREFILL_MESSAGES_FILE` | Путь к JSON‑файлу с временными предварительными сообщениями, внедряемыми во время вызова API |
| `HERMES_TIMEZONE` | Переопределение часового пояса IANA (например `America/New_York`) |
## API инструментов

| Variable | Description |
|----------|-------------|
| `PARALLEL_API_KEY` | AI‑нативный веб‑поиск ([parallel.ai](https://parallel.ai/)) |
| `FIRECRAWL_API_KEY` | Веб‑скрейпинг и облачный браузер ([firecrawl.dev](https://firecrawl.dev/)) |
| `FIRECRAWL_API_URL` | Пользовательский endpoint Firecrawl API для самохостинг‑экземпляров (необязательно) |
| `TAVILY_API_KEY` | Ключ API Tavily для AI‑нативного веб‑поиска, извлечения и обхода ([app.tavily.com](https://app.tavily.com/home)) |
| `SEARXNG_URL` | URL экземпляра SearXNG для бесплатного самохостинг‑веб‑поиска — ключ API не требуется ([searxng.github.io](https://searxng.github.io/searxng/)) |
| `TAVILY_BASE_URL` | Переопределяет endpoint API Tavily. Полезно для корпоративных прокси и самохостинг‑совместимых с Tavily поисковых бекендов. Та же схема, что и у `GROQ_BASE_URL`. |
| `EXA_API_KEY` | Ключ API Exa для AI‑нативного веб‑поиска и контента ([exa.ai](https://exa.ai/)) |
| `BROWSERBASE_API_KEY` | Автоматизация браузера ([browserbase.com](https://browserbase.com/)) |
| `BROWSERBASE_PROJECT_ID` | ID проекта Browserbase |
| `BROWSER_USE_API_KEY` | Ключ API облачного браузера Browser Use ([browser-use.com](https://browser-use.com/)) |
| `FIRECRAWL_BROWSER_TTL` | TTL сессии браузера Firecrawl в секундах (по умолчанию: 300) |
| `BROWSER_CDP_URL` | URL Chrome DevTools Protocol для локального браузера (устанавливается через `/browser connect`, например `ws://localhost:9222`) |
| `CAMOFOX_URL` | Локальный URL анти‑детекционного браузера Camofox (по умолчанию: `http://localhost:9377`) |
| `CAMOFOX_USER_ID` | Необязательный внешний ID пользователя Camofox для общих видимых сессий |
| `CAMOFOX_SESSION_KEY` | Необязательный ключ сессии Camofox, используемый при создании вкладок для `CAMOFOX_USER_ID` |
| `CAMOFOX_ADOPT_EXISTING_TAB` | Установи `true`, чтобы переиспользовать существующую вкладку Camofox перед созданием новой |
| `BROWSER_INACTIVITY_TIMEOUT` | Тайм‑аут бездействия сессии браузера в секундах |
| `AGENT_BROWSER_ARGS` | Дополнительные флаги запуска Chromium (разделённые запятыми или переводом строки). Hermes автоматически добавляет `--no-sandbox,--disable-dev-shm-usage`, когда работает от root или в ограниченных пользовательских неймспейсах AppArmor (Ubuntu 23.10+, DGX Spark, многие контейнерные образы); задавай вручную только для переопределения или добавления других флагов. |
| `FAL_KEY` | Генерация изображений ([fal.ai](https://fal.ai/)) |
| `GROQ_API_KEY` | Ключ API Groq Whisper STT ([groq.com](https://groq.com/)) |
| `ELEVENLABS_API_KEY` | Премиум‑голоса TTS ElevenLabs ([elevenlabs.io](https://elevenlabs.io/)) |
| `STT_GROQ_MODEL` | Переопределить модель STT Groq (по умолчанию: `whisper-large-v3-turbo`) |
| `GROQ_BASE_URL` | Переопределить совместимый с OpenAI endpoint STT Groq |
| `STT_OPENAI_MODEL` | Переопределить модель STT OpenAI (по умолчанию: `whisper-1`) |
| `STT_OPENAI_BASE_URL` | Переопределить совместимый с OpenAI endpoint STT |
| `GITHUB_TOKEN` | Токен GitHub для Skills Hub (более высокие лимиты API, публикация навыков) |
| `HONCHO_API_KEY` | Кросс‑сессионное моделирование пользователя ([honcho.dev](https://honcho.dev/)) |
| `HONCHO_BASE_URL` | Базовый URL для самохостинг‑экземпляров Honcho (по умолчанию: облако Honcho). Ключ API не требуется для локальных экземпляров |
| `HINDSIGHT_TIMEOUT` | Тайм‑аут в секундах для вызовов API провайдера памяти Hindsight (по умолчанию: `60`). Увеличь, если твой экземпляр Hindsight медленно отвечает во время `/sync` или `on_session_switch` и ты видишь тайм‑ауты в `errors.log`. |
| `SUPERMEMORY_API_KEY` | Семантическая долговременная память с восстановлением профиля и ingest‑ом сессий ([supermemory.ai](https://supermemory.ai)) |
| `DAYTONA_API_KEY` | Облачные песочницы Daytona ([daytona.io](https://daytona.io/)) |

### Наблюдаемость Langfuse

Переменные окружения для встроенного плагина [`observability/langfuse`](/user-guide/features/built-in-plugins#observabilitylangfuse). Установи их в `~/.hermes/.env`. Плагин также должен быть включён (`hermes plugins enable observability/langfuse` или отметкой в `hermes plugins`), иначе переменные не подействуют.

| Variable | Description |
|----------|-------------|
| `HERMES_LANGFUSE_PUBLIC_KEY` | Публичный ключ проекта Langfuse (`pk-lf-...`). Обязательно. |
| `HERMES_LANGFUSE_SECRET_KEY` | Секретный ключ проекта Langfuse (`sk-lf-...`). Обязательно. |
| `HERMES_LANGFUSE_BASE_URL` | URL сервера Langfuse (по умолчанию: `https://cloud.langfuse.com`). Устанавливается для самохостинга. |
| `HERMES_LANGFUSE_ENV` | Тег окружения в трассах (`production`, `staging`, …) |
| `HERMES_LANGFUSE_RELEASE` | Тег релиза/версии в трассах |
| `HERMES_LANGFUSE_SAMPLE_RATE` | Скорость сэмплинга SDK 0.0–1.0 (по умолчанию: `1.0`) |
| `HERMES_LANGFUSE_MAX_CHARS` | Обрезка поля для сериализованных полезных нагрузок (по умолчанию: `12000`) |
| `HERMES_LANGFUSE_DEBUG` | `true` включает подробный лог плагина в `agent.log` |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL` | Стандартные имена SDK Langfuse. Принимаются как резервные, если эквиваленты `HERMES_LANGFUSE_*` не заданы. |

### Шлюз инструментов Nous

Эти переменные настраивают [шлюз инструментов](/user-guide/features/tool-gateway) для платных подписчиков Nous или самохостинг‑развёртываний шлюза. Большинству пользователей их не требуется задавать — шлюз конфигурируется автоматически через `hermes model` или `hermes tools`.

| Variable | Description |
|----------|-------------|
| `TOOL_GATEWAY_DOMAIN` | Базовый домен для маршрутизации шлюза инструментов (по умолчанию: `nousresearch.com`) |
| `TOOL_GATEWAY_SCHEME` | Схема HTTP или HTTPS для URL шлюза (по умолчанию: `https`) |
| `TOOL_GATEWAY_USER_TOKEN` | Токен аутентификации для шлюза инструментов (обычно заполняется автоматически из аутентификации Nous) |
| `FIRECRAWL_GATEWAY_URL` | Переопределить URL endpoint шлюза Firecrawl специально |
## Терминальный бэкенд

| Variable | Description |
|----------|-------------|
| `TERMINAL_ENV` | Бэкенд: `local`, `docker`, `ssh`, `singularity`, `modal`, `daytona` |
| `HERMES_DOCKER_BINARY` | Переопределяет бинарник контейнера, к которому Hermes обращается (например, `podman`, `/usr/local/bin/docker`). Если не задан, Hermes автоматически ищет `docker` или `podman` в `PATH`. Нужно, когда установлены оба и требуется использовать не тот, который выбран по умолчанию, или когда бинарник находится вне `PATH`. |
| `TERMINAL_DOCKER_IMAGE` | Docker‑образ (по умолчанию: `nikolaik/python-nodejs:python3.11-nodejs20`) |
| `TERMINAL_DOCKER_FORWARD_ENV` | JSON‑массив имён переменных окружения, которые следует явно передавать в терминальные сессии Docker. Примечание: `required_environment_variables`, объявленные skill, передаются автоматически — этот параметр нужен только для переменных, не объявленных ни одним skill. |
| `TERMINAL_DOCKER_VOLUMES` | Дополнительные монтирования Docker‑томов (через запятую `host:container`) |
| `TERMINAL_DOCKER_MOUNT_CWD_TO_WORKSPACE` | Расширенный параметр: монтировать текущий рабочий каталог запуска в Docker `/workspace` (`true`/`false`, по умолчанию: `false`) |
| `TERMINAL_SINGULARITY_IMAGE` | Образ Singularity или путь к файлу `.sif` |
| `TERMINAL_MODAL_IMAGE` | Образ контейнера Modal |
| `TERMINAL_DAYTONA_IMAGE` | Образ песочницы Daytona |
| `TERMINAL_TIMEOUT` | Тайм‑аут команды в секундах |
| `TERMINAL_LIFETIME_SECONDS` | Максимальное время жизни терминальных сессий в секундах |
| `TERMINAL_CWD` | Рабочий каталог для терминальных сессий (только gateway/cron; CLI использует каталог запуска) |
| `SUDO_PASSWORD` | Разрешить sudo без интерактивного запроса |

Для облачных бэкендов песочницы постоянство ориентировано на файловую систему. `TERMINAL_LIFETIME_SECONDS` управляет тем, когда Hermes очищает неактивную терминальную сессию, а последующие возобновления могут воссоздать песочницу вместо сохранения живых процессов.
## SSH‑бэкенд

| Variable | Description |
|----------|-------------|
| `TERMINAL_SSH_HOST` | Имя хоста удалённого сервера |
| `TERMINAL_SSH_USER` | Имя пользователя SSH |
| `TERMINAL_SSH_PORT` | SSH‑порт (по умолчанию: 22) |
| `TERMINAL_SSH_KEY` | Путь к закрытому ключу |
| `TERMINAL_SSH_PERSISTENT` | Переопределить постоянную оболочку для SSH (по умолчанию: берётся значение `TERMINAL_PERSISTENT_SHELL`) |
## Ресурсы контейнера (Docker, Singularity, Modal, Daytona)

| Переменная | Описание |
|------------|----------|
| `TERMINAL_CONTAINER_CPU` | ядра CPU (по умолчанию: 1) |
| `TERMINAL_CONTAINER_MEMORY` | память в МБ (по умолчанию: 5120) |
| `TERMINAL_CONTAINER_DISK` | диск в МБ (по умолчанию: 51200) |
| `TERMINAL_CONTAINER_PERSISTENT` | сохранять файловую систему контейнера между сессиями (по умолчанию: `true`) |
| `TERMINAL_SANDBOX_DIR` | каталог хоста для рабочих пространств и наложений (по умолчанию: `~/.hermes/sandboxes/`) |
## Постоянный shell

| Variable | Description |
|----------|-------------|
| `TERMINAL_PERSISTENT_SHELL` | Включает постоянный shell для нелокальных бэкендов (по умолчанию: `true`). Также можно задать через `terminal.persistent_shell` в `config.yaml`. |
| `TERMINAL_LOCAL_PERSISTENT` | Включает постоянный shell для локального бэкенда (по умолчанию: `false`). |
| `TERMINAL_SSH_PERSISTENT` | Переопределяет настройку постоянного shell для SSH‑бэкенда (по умолчанию: берётся значение `TERMINAL_PERSISTENT_SHELL`). |
## Messaging

| Переменная | Описание |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram‑бота (от @BotFather) |
| `TELEGRAM_ALLOWED_USERS` | Список ID пользователей через запятую, которым разрешено использовать бота (применяется к личным сообщениям, группам и форумам) |
| `TELEGRAM_GROUP_ALLOWED_USERS` | Список ID отправителей через запятую, авторизованных только в группах/форумах (НЕ даёт доступа к личным сообщениям). Значения в виде Chat‑ID (начинающиеся с `-`) всё ещё учитываются как chat‑ID для обратной совместимости с конфигурациями до #17686, с предупреждением об устаревании. |
| `TELEGRAM_GROUP_ALLOWED_CHATS` | Список ID групп/форумов через запятую; любой участник считается авторизованным |
| `TELEGRAM_HOME_CHANNEL` | Канал/чат Telegram по умолчанию для доставки cron‑сообщений |
| `TELEGRAM_HOME_CHANNEL_NAME` | Отображаемое имя домашнего канала Telegram |
| `TELEGRAM_CRON_THREAD_ID` | ID темы форума для получения cron‑сообщений; переопределяет `TELEGRAM_HOME_CHANNEL_THREAD_ID` только для cron. Используй в режиме тем, чтобы ответы на cron‑сообщения открывали новую сессию, а не попадали в системный лобби (#24409). |
| `TELEGRAM_WEBHOOK_URL` | Публичный HTTPS‑URL для режима webhook (включает webhook вместо polling) |
| `TELEGRAM_WEBHOOK_PORT` | Локальный порт прослушивания для сервера webhook (по умолчанию: `8443`) |
| `TELEGRAM_WEBHOOK_SECRET` | Секретный токен, который Telegram отсылает в каждом обновлении для проверки. **Обязательно, если установлен `TELEGRAM_WEBHOOK_URL`** — шлюз откажется запускаться без него (GHSA-3vpc-7q5r-276h). Генерировать с помощью `openssl rand -hex 32`. |
| `TELEGRAM_REACTIONS` | Включить реакцию эмодзи на сообщения во время обработки (по умолчанию: `false`) |
| `TELEGRAM_REQUIRE_MENTION` | Требовать явного упоминания перед ответом в группах Telegram. Эквивалент `telegram.require_mention` в `config.yaml`. |
| `TELEGRAM_MENTION_PATTERNS` | JSON‑массив, список через перевод строки или через запятую с регулярными выражениями‑пробуждающими словами, принимаемыми при включённом ограничении упоминаний в группах Telegram. Эквивалент `telegram.mention_patterns`. |
| `TELEGRAM_EXCLUSIVE_BOT_MENTIONS` | При включении явные упоминания `@...bot` в группах Telegram направляются только к упомянутым бот‑именам до выполнения ответов или пробуждающих слов. По умолчанию: `true`. Эквивалент `telegram.exclusive_bot_mentions`. |
| `TELEGRAM_REPLY_TO_MODE` | Поведение ссылки‑ответа: `off`, `first` (по умолчанию) или `all`. Соответствует шаблону Discord. |
| `TELEGRAM_IGNORED_THREADS` | Список ID тем/тредов форума Telegram через запятую, где бот никогда не отвечает |
| `TELEGRAM_PROXY` | URL прокси для соединений Telegram — переопределяет `HTTPS_PROXY`. Поддерживает `http://`, `https://`, `socks5://` |
| `DISCORD_BOT_TOKEN` | Токен Discord‑бота |
| `DISCORD_ALLOWED_USERS` | Список ID пользователей Discord через запятую, которым разрешено использовать бота |
| `DISCORD_ALLOWED_ROLES` | Список ID ролей Discord через запятую, которым разрешено использовать бота (ИЛИ с `DISCORD_ALLOWED_USERS`). Автоматически включает intent Members. Полезно, когда команды модерации меняются — права ролей распространяются автоматически. |
| `DISCORD_ALLOWED_CHANNELS` | Список ID каналов Discord через запятую. При задании бот отвечает только в этих каналах (плюс личные сообщения, если разрешено). Переопределяет `config.yaml` `discord.allowed_channels`. |
| `DISCORD_PROXY` | URL прокси для соединений Discord — переопределяет `HTTPS_PROXY`. Поддерживает `http://`, `https://`, `socks5://` |
| `DISCORD_HOME_CHANNEL` | Канал Discord по умолчанию для доставки cron‑сообщений |
| `DISCORD_HOME_CHANNEL_NAME` | Отображаемое имя домашнего канала Discord |
| `DISCORD_COMMAND_SYNC_POLICY` | Политика синхронизации slash‑команд Discord при старте: `safe` (diff и reconcile), `bulk` (унаследованный `tree.sync()`), или `off` |
| `DISCORD_REQUIRE_MENTION` | Требовать @упоминание перед ответом в каналах сервера |
| `DISCORD_FREE_RESPONSE_CHANNELS` | Список ID каналов через запятую, где упоминание не требуется |
| `DISCORD_AUTO_THREAD` | Автоматически создавать ветки для длинных ответов, если поддерживается |
| `DISCORD_ALLOW_ANY_ATTACHMENT` | При `true` принимать вложения любого типа (не только из встроенного списка PDF/text/zip/office). Неизвестные типы кэшируются и передаются агенту как локальный путь, чтобы он мог их просмотреть через `terminal` / `read_file` / `ffprobe`. По умолчанию `false`. |
| `DISCORD_MAX_ATTACHMENT_BYTES` | Максимальный размер вложения в байтах, который шлюз будет кэшировать. По умолчанию `33554432` (32 MiB). Установи `0` для снятия ограничения (вложения держатся в памяти пока записываются). |
| `DISCORD_REACTIONS` | Включить реакцию эмодзи на сообщения во время обработки (по умолчанию: `true`) |
| `DISCORD_IGNORED_CHANNELS` | Список ID каналов через запятую, где бот никогда не отвечает |
| `DISCORD_NO_THREAD_CHANNELS` | Список ID каналов через запятую, где бот отвечает без автоматического создания веток |
| `DISCORD_REPLY_TO_MODE` | Поведение ссылки‑ответа: `off`, `first` (по умолчанию) или `all` |
| `DISCORD_ALLOW_MENTION_EVERYONE` | Разрешить боту упоминать `@everyone`/`@here` (по умолчанию: `false`). См. [Контроль упоминаний](../user-guide/messaging/discord.md#mention-control). |
| `DISCORD_ALLOW_MENTION_ROLES` | Разрешить боту упоминать роли `@role` (по умолчанию: `false`). |
| `DISCORD_ALLOW_MENTION_USERS` | Разрешить боту упоминать отдельных `@user` (по умолчанию: `true`). |
| `DISCORD_ALLOW_MENTION_REPLIED_USER` | Упоминать автора при ответе на его сообщение (по умолчанию: `true`). |
| `SLACK_BOT_TOKEN` | Токен Slack‑бота (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Токен уровня приложения Slack (`xapp-...`, требуется для Socket Mode) |
| `SLACK_ALLOWED_USERS` | Список ID пользователей Slack через запятую |
| `SLACK_HOME_CHANNEL` | Канал Slack по умолчанию для доставки cron‑сообщений |
| `SLACK_HOME_CHANNEL_NAME` | Отображаемое имя домашнего канала Slack |
| `GOOGLE_CHAT_PROJECT_ID` | ID проекта GCP, где размещён Pub/Sub‑топик (по умолчанию берётся `GOOGLE_CLOUD_PROJECT`) |
| `GOOGLE_CHAT_SUBSCRIPTION_NAME` | Полный путь подписки Pub/Sub, `projects/{proj}/subscriptions/{sub}` (устаревший алиас: `GOOGLE_CHAT_SUBSCRIPTION`) |
| `GOOGLE_CHAT_SERVICE_ACCOUNT_JSON` | Путь к JSON‑файлу сервисного аккаунта или сам JSON inline (по умолчанию берётся `GOOGLE_APPLICATION_CREDENTIALS`) |
| `GOOGLE_CHAT_ALLOWED_USERS` | Список email‑ов пользователей через запятую, которым разрешено общаться с ботом |
| `GOOGLE_CHAT_ALLOW_ALL_USERS` | Разрешить любому пользователю Google Chat вызывать бота (только для разработки) |
| `GOOGLE_CHAT_HOME_CHANNEL` | Пространство (например `spaces/AAAA...`) по умолчанию для доставки cron‑сообщений |
| `GOOGLE_CHAT_HOME_CHANNEL_NAME` | Отображаемое имя домашнего пространства Google Chat |
| `GOOGLE_CHAT_MAX_MESSAGES` | Максимальное количество сообщений в полёте для FlowControl Pub/Sub (по умолчанию: `1`) |
| `GOOGLE_CHAT_MAX_BYTES` | Максимальное количество байтов в полёте для FlowControl Pub/Sub (по умолчанию: `16777216`, 16 MiB) |
| `GOOGLE_CHAT_BOOTSTRAP_SPACES` | Список дополнительных ID пространств через запятую, которые проверяются при старте при разрешении собственного `users/{id}` |
| `GOOGLE_CHAT_DEBUG_RAW` | Установи любое значение, чтобы логировать отредактированные конверты Pub/Sub на уровне DEBUG (только для отладки) |
| `WHATSAPP_ENABLED` | Включить мост WhatsApp (`true`/`false`) |
| `WHATSAPP_MODE` | `bot` (отдельный номер) или `self-chat` (сообщать себе) |
| `WHATSAPP_ALLOWED_USERS` | Список телефонных номеров через запятую (с кодом страны, без `+`), или `*` для разрешения всех отправителей |
| `WHATSAPP_ALLOW_ALL_USERS` | Разрешить всем отправителям WhatsApp без списка разрешённых (`true`/`false`) |
| `WHATSAPP_DEBUG` | Логировать сырые события сообщений в мосту для отладки (`true`/`false`) |
| `SIGNAL_HTTP_URL` | HTTP‑endpoint демона signal‑cli (например `http://127.0.0.1:8080`) |
| `SIGNAL_ACCOUNT` | Номер телефона бота в формате E.164 |
| `SIGNAL_ALLOWED_USERS` | Список номеров E.164 или UUID через запятую |
| `SIGNAL_GROUP_ALLOWED_USERS` | Список ID групп через запятую, или `*` для всех групп |
| `SIGNAL_HOME_CHANNEL_NAME` | Отображаемое имя домашнего канала Signal |
| `SIGNAL_IGNORE_STORIES` | Игнорировать истории/статусы Signal |
| `SIGNAL_ALLOW_ALL_USERS` | Разрешить всем пользователям Signal без списка разрешённых |
| `TWILIO_ACCOUNT_SID` | SID аккаунта Twilio (используется в навыке телефонии) |
| `TWILIO_AUTH_TOKEN` | Токен аутентификации Twilio (используется в навыке телефонии; также для проверки подписи webhook) |
| `TWILIO_PHONE_NUMBER` | Номер телефона Twilio в формате E.164 (используется в навыке телефонии) |
| `SMS_WEBHOOK_URL` | Публичный URL для проверки подписи Twilio — должен совпадать с URL webhook в консоли Twilio (обязательно) |
| `SMS_WEBHOOK_PORT` | Порт прослушивания webhook для входящих SMS (по умолчанию: `8080`) |
| `SMS_WEBHOOK_HOST` | Адрес привязки webhook (по умолчанию: `0.0.0.0`) |
| `SMS_INSECURE_NO_SIGNATURE` | Установи `true`, чтобы отключить проверку подписи Twilio (только локальная разработка — не для продакшна) |
| `SMS_ALLOWED_USERS` | Список номеров E.164 через запятую, которым разрешено общаться |
| `SMS_ALLOW_ALL_USERS` | Разрешить всем отправителям SMS без списка разрешённых |
| `SMS_HOME_CHANNEL` | Номер телефона для доставки cron‑задач / уведомлений |
| `SMS_HOME_CHANNEL_NAME` | Отображаемое имя домашнего канала SMS |
| `EMAIL_ADDRESS` | Адрес электронной почты для адаптера шлюза Email |
| `EMAIL_PASSWORD` | Пароль или app‑пароль для учётной записи email |
| `EMAIL_IMAP_HOST` | Хост IMAP для адаптера email |
| `EMAIL_IMAP_PORT` | Порт IMAP |
| `EMAIL_SMTP_HOST` | Хост SMTP для адаптера email |
| `EMAIL_SMTP_PORT` | Порт SMTP |
| `EMAIL_ALLOWED_USERS` | Список email‑ов через запятую, которым разрешено писать боту |
| `EMAIL_HOME_ADDRESS` | Получатель по умолчанию для проактивных email‑сообщений |
| `EMAIL_HOME_ADDRESS_NAME` | Отображаемое имя целевого получателя email |
| `EMAIL_POLL_INTERVAL` | Интервал опроса email в секундах |
| `EMAIL_ALLOW_ALL_USERS` | Разрешить всем входящим email‑отправителям |
| `DINGTALK_CLIENT_ID` | AppKey бота DingTalk из портала разработчиков ([open.dingtalk.com](https://open.dingtalk.com)) |
| `DINGTALK_CLIENT_SECRET` | AppSecret бота DingTalk из портала разработчиков |
| `DINGTALK_ALLOWED_USERS` | Список ID пользователей DingTalk через запятую, которым разрешено писать боту |
| `FEISHU_APP_ID` | App ID бота Feishu/Lark из [open.feishu.cn](https://open.feishu.cn/) |
| `FEISHU_APP_SECRET` | App Secret бота Feishu/Lark |
| `FEISHU_DOMAIN` | `feishu` (Китай) или `lark` (международный). По умолчанию: `feishu` |
| `FEISHU_CONNECTION_MODE` | `websocket` (рекомендовано) или `webhook`. По умолчанию: `websocket` |
| `FEISHU_ENCRYPT_KEY` | Необязательный ключ шифрования для режима webhook |
| `FEISHU_VERIFICATION_TOKEN` | Необязательный токен проверки для режима webhook |
| `FEISHU_ALLOWED_USERS` | Список ID пользователей Feishu через запятую, которым разрешено писать боту |
| `FEISHU_ALLOW_BOTS` | `none` (по умолчанию) / `mentions` / `all` — принимать входящие сообщения от других ботов. См. [сообщения bot‑to‑bot](../user-guide/messaging/feishu.md#bot-to-bot-messaging) |
| `FEISHU_REQUIRE_MENTION` | `true` (по умолчанию) / `false` — обязаны ли групповые сообщения @упоминать бота. Переопределяется per‑chat через `group_rules.<chat_id>.require_mention`. |
| `FEISHU_HOME_CHANNEL` | ID чата Feishu для доставки cron‑сообщений и уведомлений |
| `WECOM_BOT_ID` | ID AI‑бота WeCom из админ‑консоли |
| `WECOM_SECRET` | Секрет AI‑бота WeCom |
| `WECOM_WEBSOCKET_URL` | Пользовательский URL WebSocket (по умолчанию: `wss://openws.work.weixin.qq.com`) |
| `WECOM_ALLOWED_USERS` | Список ID пользователей WeCom через запятую, которым разрешено писать боту |
| `WECOM_HOME_CHANNEL` | ID чата WeCom для доставки cron‑сообщений и уведомлений |
| `WECOM_CALLBACK_CORP_ID` | Corp ID предприятия WeCom для собственного callback‑приложения |
| `WECOM_CALLBACK_CORP_SECRET` | Corp‑секрет для собственного callback‑приложения |
| `WECOM_CALLBACK_AGENT_ID` | ID агента собственного callback‑приложения |
| `WECOM_CALLBACK_TOKEN` | Токен проверки callback |
| `WECOM_CALLBACK_ENCODING_AES_KEY` | AES‑ключ для шифрования callback |
| `WECOM_CALLBACK_HOST` | Адрес привязки сервера callback (по умолчанию: `0.0.0.0`) |
| `WECOM_CALLBACK_PORT` | Порт сервера callback (по умолчанию: `8645`) |
| `WECOM_CALLBACK_ALLOWED_USERS` | Список ID пользователей через запятую для белого списка |
| `WECOM_CALLBACK_ALLOW_ALL_USERS` | Установи `true`, чтобы разрешить всем пользователям без белого списка |
| `WEIXIN_ACCOUNT_ID` | ID аккаунта Weixin, полученный через QR‑логин через iLink Bot API |
| `WEIXIN_TOKEN` | Токен аутентификации Weixin, полученный через QR‑логин через iLink Bot API |
| `WEIXIN_BASE_URL` | Переопределить базовый URL iLink Bot API Weixin (по умолчанию: `https://ilinkai.weixin.qq.com`) |
| `WEIXIN_CDN_BASE_URL` | Переопределить базовый URL CDN Weixin для медиа (по умолчанию: `https://novac2c.cdn.weixin.qq.com/c2c`) |
| `WEIXIN_DM_POLICY` | Политика прямых сообщений: `open`, `allowlist`, `pairing`, `disabled` (по умолчанию: `open`) |
| `WEIXIN_GROUP_POLICY` | Политика групповых сообщений: `open`, `allowlist`, `disabled` (по умолчанию: `disabled`) |
| `WEIXIN_ALLOWED_USERS` | Список ID пользователей Weixin через запятую, которым разрешено писать боту в личных сообщениях |
| `WEIXIN_GROUP_ALLOWED_USERS` | Список ID групповых чатов Weixin через запятую (не ID участников). Имя переменной устарело — ожидает ID групп. Действует только когда iLink действительно доставляет групповые события; идентификаторы iLink‑ботов (`...@im.bot`) обычно не получают обычные групповые сообщения WeChat. |
| `WEIXIN_HOME_CHANNEL` | ID чата Weixin для доставки cron‑сообщений и уведомлений |
| `WEIXIN_HOME_CHANNEL_NAME` | Отображаемое имя домашнего канала Weixin |
| `WEIXIN_ALLOW_ALL_USERS` | Разрешить всем пользователям Weixin без белого списка (`true`/`false`) |
| `BLUEBUBBLES_SERVER_URL` | URL сервера BlueBubbles (например `http://192.168.1.10:1234`) |
| `BLUEBUBBLES_PASSWORD` | Пароль сервера BlueBubbles |
| `BLUEBUBBLES_WEBHOOK_HOST` | Адрес привязки webhook‑слушателя (по умолчанию: `127.0.0.1`) |
| `BLUEBUBBLES_WEBHOOK_PORT` | Порт webhook‑слушателя (по умолчанию: `8645`) |
| `BLUEBUBBLES_HOME_CHANNEL` | Телефон/email для доставки cron/уведомлений |
| `BLUEBUBBLES_ALLOWED_USERS` | Список авторизованных пользователей через запятую |
| `BLUEBUBBLES_ALLOW_ALL_USERS` | Разрешить всем пользователям (`true`/`false`) |
| `QQ_APP_ID` | App ID QQ‑бота из [q.qq.com](https://q.qq.com) |
| `QQ_CLIENT_SECRET` | App Secret QQ‑бота из [q.qq.com](https://q.qq.com) |
| `QQ_STT_API_KEY` | API‑ключ внешнего STT‑провайдера (опционально, используется, когда встроенный ASR QQ не возвращает текст) |
| `QQ_STT_BASE_URL` | Базовый URL внешнего STT‑провайдера (опционально) |
| `QQ_STT_MODEL` | Название модели внешнего STT‑провайдера (опционально) |
| `QQ_ALLOWED_USERS` | Список открытых ID пользователей QQ через запятую, которым разрешено писать боту |
| `QQ_GROUP_ALLOWED_USERS` | Список ID групп QQ через запятую для доступа к @‑сообщениям в группах |
| `QQ_ALLOW_ALL_USERS` | Разрешить всем пользователям (`true`/`false`, переопределяет `QQ_ALLOWED_USERS`) |
| `QQBOT_HOME_CHANNEL` | Открытый ID пользователя/группы QQ для доставки cron‑сообщений и уведомлений |
| `QQBOT_HOME_CHANNEL_NAME` | Отображаемое имя домашнего канала QQ |
| `QQ_PORTAL_HOST` | Переопределить хост портала QQ (установи `sandbox.q.qq.com` для маршрутизации через песочницу; по умолчанию: `q.qq.com`). |
| `MATTERMOST_URL` | URL сервера Mattermost (например `https://mm.example.com`) |
| `MATTERMOST_TOKEN` | Токен бота или персональный токен доступа для Mattermost |
| `MATTERMOST_ALLOWED_USERS` | Список ID пользователей Mattermost через запятую, которым разрешено писать боту |
| `MATTERMOST_HOME_CHANNEL` | ID канала для проактивной доставки сообщений (cron, уведомления) |
| `MATTERMOST_REQUIRE_MENTION` | Требовать `@упоминание` в каналах (по умолчанию: `true`). Установи `false`, чтобы отвечать на все сообщения. |
| `MATTERMOST_FREE_RESPONSE_CHANNELS` | Список ID каналов через запятую, где бот отвечает без `@упоминания` |
| `MATTERMOST_REPLY_MODE` | Стиль ответа: `thread` (ответы в ветках) или `off` (плоские сообщения, по умолчанию) |
| `MATRIX_HOMESERVER` | URL homeserver Matrix (например `https://matrix.org`) |
| `MATRIX_ACCESS_TOKEN` | Токен доступа Matrix для аутентификации бота |
| `MATRIX_USER_ID` | ID пользователя Matrix (например `@hermes:matrix.org`) — требуется для входа по паролю, опционально при наличии токена доступа |
| `MATRIX_PASSWORD` | Пароль Matrix (альтернатива токену доступа) |
| `MATRIX_ALLOWED_USERS` | Список ID пользователей Matrix через запятую, которым разрешено писать боту (например `@alice:matrix.org`) |
| `MATRIX_HOME_ROOM` | ID комнаты для проактивной доставки сообщений (например `!abc123:matrix.org`) |
| `MATRIX_ENCRYPTION` | Включить сквозное шифрование (`true`/`false`, по умолчанию: `false`) |
| `MATRIX_DEVICE_ID` | Постоянный ID устройства Matrix для сохранения E2EE между перезапусками (например `HERMES_BOT`). Без него ключи E2EE вращаются каждый запуск, и расшифровка исторических комнат ломается. |
| `MATRIX_REACTIONS` | Включить эмодзи‑реакции в жизненном цикле обработки входящих сообщений (по умолчанию: `true`). Установи `false`, чтобы отключить. |
| `MATRIX_REQUIRE_MENTION` | Требовать `@упоминание` в комнатах (по умолчанию: `true`). Установи `false`, чтобы отвечать на все сообщения. |
| `MATRIX_FREE_RESPONSE_ROOMS` | Список ID комнат через запятую, где бот отвечает без `@упоминания` |
| `MATRIX_AUTO_THREAD` | Автоматически создавать ветки для сообщений в комнате (по умолчанию: `true`) |
| `MATRIX_DM_MENTION_THREADS` | Создавать ветку, когда бот @упомянут в личном сообщении (по умолчанию: `false`) |
| `MATRIX_RECOVERY_KEY` | Ключ восстановления для проверки кросс‑подписей после ротации ключей устройства. Рекомендуется для E2EE‑настроек с включённым кросс‑подписыванием. |
| `HASS_TOKEN` | Долгоживущий токен доступа Home Assistant (включает платформу HA + инструменты) |
| `HASS_URL` | URL Home Assistant (по умолчанию: `http://homeassistant.local:8123`) |
| `WEBHOOK_ENABLED` | Включить адаптер платформы webhook (`true`/`false`) |
| `WEBHOOK_PORT` | Порт HTTP‑сервера для приёма webhook‑ов (по умолчанию: `8644`) |
| `WEBHOOK_SECRET` | Глобальный HMAC‑секрет для проверки подписи webhook (используется как запасной, если маршруты не задают свой) |
| `API_SERVER_ENABLED` | Включить совместимый с OpenAI API‑сервер (`true`/`false`). Работает параллельно с другими платформами. |
| `API_SERVER_KEY` | Токен Bearer для аутентификации API‑сервера. Обязательно, когда сервер включён. |
| `API_SERVER_CORS_ORIGINS` | Список источников браузеров через запятую, которым разрешён прямой вызов API‑сервера (например `http://localhost:3000,http://127.0.0.1:3000`). По умолчанию: отключено. |
| `API_SERVER_PORT` | Порт API‑сервера (по умолчанию: `8642`) |
| `API_SERVER_HOST` | Адрес/хост привязки API‑сервера (по умолчанию: `127.0.0.1`). `API_SERVER_KEY` всё равно требуется на loopback; используй узкий список `API_SERVER_CORS_ORIGINS` для доступа из браузера. |
| `API_SERVER_MODEL_NAME` | Имя модели, объявляемое на `/v1/models`. По умолчанию берётся имя профиля (или `hermes-agent` для профиля по умолчанию). Полезно в многопользовательских настройках, где фронтендам вроде Open WebUI нужны разные имена моделей. |
| `GATEWAY_PROXY_URL` | URL удалённого Hermes API‑сервера для пересылки сообщений ([режим proxy](/user-guide/messaging/matrix#proxy-mode-e2ee-on-macos)). При задании шлюз обрабатывает только ввод‑вывод платформ — вся работа агента делегируется удалённому серверу. Также задаётся через `gateway.proxy_url` в `config.yaml`. |
| `GATEWAY_PROXY_KEY` | Токен Bearer для аутентификации с удалённым API‑сервером в режиме proxy. Должен совпадать с `API_SERVER_KEY` на удалённом хосте. |
| `MESSAGING_CWD` | Рабочий каталог для терминальных команд в режиме обмена сообщениями (по умолчанию: `~`) |
| `GATEWAY_ALLOWED_USERS` | Список ID пользователей через запятую, разрешённых на всех платформах |
| `GATEWAY_ALLOW_ALL_USERS` | Разрешить всем пользователям без белых списков (`true`/`false`, по умолчанию: `false`) |

### Microsoft Graph (Teams Meetings)

Учётные данные только для приложения (app‑only) клиента Microsoft Graph REST, используемого в предстоящем конвейере сводки встреч Teams. См. [Регистрация приложения Microsoft Graph](/guides/microsoft-graph-app-registration) для пошагового руководства в Azure Portal и точного списка требуемых разрешений API.

| Переменная | Описание |
|----------|-------------|
| `MSGRAPH_TENANT_ID` | ID арендатора Azure AD (GUID каталога) для регистрации приложения Graph. |
| `MSGRAPH_CLIENT_ID` | ID приложения (client) в регистрации Azure. |
| `MSGRAPH_CLIENT_SECRET` | Значение client‑secret для регистрации приложения. Храни в `~/.hermes/.env` с правами `chmod 600`; периодически ротируй через Azure Portal. |
| `MSGRAPH_SCOPE` | OAuth2‑scope для запроса токена client‑credentials (по умолчанию: `https://graph.microsoft.com/.default`). |
| `MSGRAPH_AUTHORITY_URL` | URL authority Microsoft identity platform (по умолчанию: `https://login.microsoftonline.com`). Переопределяй только для национальных/суверенных облаков (например `https://login.microsoftonline.us` для GCC High). |

### Microsoft Graph Webhook Listener

Слушатель входящих уведомлений‑изменений для событий Graph (встречи Teams, календарь, чат и т.д.). См. [Microsoft Graph Webhook Listener](/user-guide/messaging/msgraph-webhook) для настройки и усиления безопасности.

| Переменная | Описание |
|----------|-------------|
| `MSGRAPH_WEBHOOK_ENABLED` | Включить платформу шлюза `msgraph_webhook` (`true`/`1`/`yes`). |
| `MSGRAPH_WEBHOOK_PORT` | Порт, к которому привязывается слушатель (по умолчанию: `8646`). |
| `MSGRAPH_WEBHOOK_CLIENT_STATE` | Общий секрет, который Graph отсылает в каждом уведомлении; сравнивается через `hmac.compare_digest`. Генерировать с помощью `openssl rand -hex 32`. |
| `MSGRAPH_WEBHOOK_ACCEPTED_RESOURCES` | Список разрешённых путей/шаблонов ресурсов Graph через запятую (например `communications/onlineMeetings,chats/*/messages`). `*` в конце — префикс‑соответствие. Пусто = принимать всё. |
| `MSGRAPH_WEBHOOK_ALLOWED_SOURCE_CIDRS` | Список CIDR‑диапазонов через запятую, которым разрешено POST‑запросы к слушателю (например `52.96.0.0/14,52.104.0.0/14`). Пусто = разрешить всем (по умолчанию). В продакшне ограничь диапазонами egress Microsoft Graph. |

### Доставка сводки встреч Teams

Используется только когда включён плагин [`teams_pipeline`](/user-guide/messaging/msgraph-webhook). Настройки также можно задать в `platforms.teams.extra` в `config.yaml` — переменные окружения имеют приоритет, если обе заданы. См. [Microsoft Teams → Доставка сводки встреч](/user-guide/messaging/teams#meeting-summary-delivery-teams-meeting-pipeline).

| Переменная | Описание |
|----------|-------------|
| `TEAMS_DELIVERY_MODE` | `graph` или `incoming_webhook`. |
| `TEAMS_INCOMING_WEBHOOK_URL` | URL webhook, сгенерированный в Teams; обязателен, если `TEAMS_DELIVERY_MODE=incoming_webhook`. |
| `TEAMS_GRAPH_ACCESS_TOKEN` | Предварительно полученный делегированный токен доступа для доставки через Graph. Обычно не нужен — запись падает обратно к учётным данным `MSGRAPH_*`, если не задан. |
| `TEAMS_TEAM_ID` | ID целевой команды для доставки в канал (`graph`‑режим). |
| `TEAMS_CHANNEL_ID` | ID целевого канала (в паре с `TEAMS_TEAM_ID`). |
| `TEAMS_CHAT_ID` | ID целевого 1:1 или группового чата (альтернатива команде+каналу для `graph`‑режима). |

### LINE Messaging API

Используется встроенным плагином платформы LINE (`plugins/platforms/line/`). См. [Messaging Gateway → LINE](/user-guide/messaging/line) для полной настройки.

| Переменная | Описание |
|----------|-------------|
| `LINE_CHANNEL_ACCESS_TOKEN` | Долгоживущий токен доступа канала из консоли LINE Developers (вкладка Messaging API). Обязательно. |
| `LINE_CHANNEL_SECRET` | Секрет канала (вкладка Basic settings); используется для проверки подписи webhook HMAC‑SHA256. Обязательно. |
| `LINE_HOST` | Хост привязки webhook (по умолчанию: `0.0.0.0`). |
| `LINE_PORT` | Порт привязки webhook (по умолчанию: `8646`). |
| `LINE_PUBLIC_URL` | Публичный HTTPS‑базовый URL (например `https://my-tunnel.example.com`). Требуется для отправки изображений/аудио/видео — LINE принимает только HTTPS‑доступные URL. |
| `LINE_ALLOWED_USERS` | Список ID пользователей через запятую, которым разрешено писать боту (префикс `U`). |
| `LINE_ALLOWED_GROUPS` | Список ID групп через запятую, в которых бот будет отвечать (префикс `C`). |
| `LINE_ALLOWED_ROOMS` | Список ID комнат через запятую, в которых бот будет отвечать (префикс `R`). |
| `LINE_ALLOW_ALL_USERS` | Хак для разработки — принимает любой источник. По умолчанию: `false`. |
| `LINE_HOME_CHANNEL` | Целевой канал доставки по умолчанию для cron‑задач с `deliver: line`. |
| `LINE_SLOW_RESPONSE_THRESHOLD` | Секунды до срабатывания кнопки постбэка медленного LLM‑шаблона (по умолчанию: `45`). Установи `0`, чтобы отключить и всегда использовать Push‑fallback. |
| `LINE_PENDING_TEXT` | Текст‑пузырёк, отображаемый рядом с кнопкой постбэка. |
| `LINE_BUTTON_LABEL` | Надпись на кнопке постбэка (по умолчанию: `Get answer`). |
| `LINE_DELIVERED_TEXT` | Ответ, когда уже доставленный постбэк нажимают повторно (по умолчанию: `Already replied ✅`). |
| `LINE_INTERRUPTED_TEXT` | Ответ, когда нажимают кнопку постбэка, оставленную после `/stop` (по умолчанию: `Run was interrupted before completion.`). |

### ntfy (push‑уведомления)

[ntfy](https://ntfy.sh/) — лёгкий HTTP‑сервис push‑уведомлений. Подпишись на топик через [мобильное приложение ntfy](https://ntfy.sh/docs/subscribe/phone/), публикуй в этот топик, чтобы общаться с агентом.

| Переменная | Описание |
|----------|-------------|
| `NTFY_TOPIC` | Топик для подписки (входящие сообщения). Обязательно. |
| `NTFY_SERVER_URL` | URL сервера (по умолчанию: `https://ntfy.sh`). Укажи собственный ntfy‑сервер для приватности. |
| `NTFY_TOKEN` | Необязательный токен аутентификации. Bearer‑токен (например `tk_xyz`) или `user:pass` для Basic auth. |
| `NTFY_PUBLISH_TOPIC` | Топик для исходящих ответов (по умолчанию тот же, что `NTFY_TOPIC`). |
| `NTFY_MARKDOWN` | Установи `true`, чтобы отправлять ответы с заголовком `X-Markdown: true`. По умолчанию: `false`. |
| `NTFY_ALLOWED_USERS` | Белый список (рассматривается как ID пользователей; в ntfy это имена топиков). Обычно ставится то же значение, что и `NTFY_TOPIC`. |
| `NTFY_ALLOW_ALL_USERS` | Хак для разработки — безопасен только на контролируемых приватных топиках. По умолчанию: `false`. |
| `NTFY_HOME_CHANNEL` | Целевой канал доставки по умолчанию для cron‑задач с `deliver: ntfy`. |
| `NTFY_HOME_CHANNEL_NAME` | Человекочитаемая метка домашнего канала (по умолчанию — имя топика). |

См. [руководство по ntfy](/user-guide/messaging/ntfy) — особенно раздел **модель идентификации** — перед развертыванием с недоверенными топиками.

### Расширенная настройка обмена сообщениями

Продвинутые параметры для каждой платформы, регулирующие throttling пакетного отправителя сообщений. Большинству пользователей их менять не требуется; значения по умолчанию учитывают лимиты платформ без ощущения задержки.

| Переменная | Описание |
|----------|-------------|
| `HERMES_TELEGRAM_TEXT_BATCH_DELAY_SECONDS` | Окно ожидания перед сбросом очередного текстового куска Telegram (по умолчанию: `0.6`). |
| `HERMES_TELEGRAM_TEXT_BATCH_SPLIT_DELAY_SECONDS` | Задержка между частями, когда одно сообщение Telegram превышает лимит длины (по умолчанию: `2.0`). |
| `HERMES_TELEGRAM_MEDIA_BATCH_DELAY_SECONDS` | Окно ожидания перед сбросом очередных медиа‑сообщений Telegram (по умолчанию: `0.6`). |
| `HERMES_TELEGRAM_FOLLOWUP_GRACE_SECONDS` | Задержка перед отправкой follow‑up после завершения агента, чтобы избежать гонки с последним куском потока. |
| `HERMES_TELEGRAM_HTTP_CONNECT_TIMEOUT` / `_READ_TIMEOUT` / `_WRITE_TIMEOUT` / `_POOL_TIMEOUT` | Переопределить базовые HTTP‑таймауты `python-telegram-bot` (секунды). |
| `HERMES_TELEGRAM_HTTP_POOL_SIZE` | Максимальное количество одновременных HTTP‑соединений к API Telegram. |
| `HERMES_TELEGRAM_DISABLE_FALLBACK_IPS` | Отключить жёстко закодированные fallback‑IP Cloudflare, используемые при сбое DNS (`true`/`false`). |
| `HERMES_DISCORD_TEXT_BATCH_DELAY_SECONDS` | Окно ожидания перед сбросом очередного текстового куска Discord (по умолчанию: `0.6`). |
| `HERMES_DISCORD_TEXT_BATCH_SPLIT_DELAY_SECONDS` | Задержка между частями, когда сообщение Discord превышает лимит длины (по умолчанию: `2.0`). |
| `HERMES_MATRIX_TEXT_BATCH_DELAY_SECONDS` / `_SPLIT_DELAY_SECONDS` | Аналоги Telegram‑параметров для Matrix. |
| `HERMES_FEISHU_TEXT_BATCH_DELAY_SECONDS` / `_SPLIT_DELAY_SECONDS` / `_MAX_CHARS` / `_MAX_MESSAGES` | Тюнинг batch‑ера Feishu — задержка, задержка разделения, макс. символов в сообщении, макс. сообщений в пакете. |
| `HERMES_FEISHU_MEDIA_BATCH_DELAY_SECONDS` | Задержка сброса медиа‑сообщений Feishu. |
| `HERMES_FEISHU_DEDUP_CACHE_SIZE` | Размер кэша дедупликации webhook‑ов Feishu (по умолчанию: `1024`). |
| `HERMES_WECOM_TEXT_BATCH_DELAY_SECONDS` / `_SPLIT_DELAY_SECONDS` | Тюнинг batch‑ера WeCom. |
| `HERMES_VISION_DOWNLOAD_TIMEOUT` | Таймаут в секундах для загрузки изображения перед передачей в модель зрения (по умолчанию: `30`). |
| `HERMES_RESTART_DRAIN_TIMEOUT` | Шлюз: секунды ожидания завершения активных запусков при `/restart` перед принудительным перезапуском (по умолчанию: `900`). |
| `HERMES_GATEWAY_PLATFORM_CONNECT_TIMEOUT` | Таймаут соединения для каждой платформы при старте шлюза (секунды). |
| `HERMES_GATEWAY_BUSY_INPUT_MODE` | Поведение шлюза при занятости ввода: `queue`, `steer` или `interrupt`. Может быть переопределено в чате через `/busy`. |
| `HERMES_GATEWAY_BUSY_ACK_ENABLED` | Отправлять ли шлюзом сообщение‑подтверждение (⚡/⏳/⏩) когда пользователь вводит данные, пока агент занят (по умолчанию: `true`). Установи `false`, чтобы полностью подавлять такие сообщения — ввод всё равно будет поставлен в очередь/перенаправлен/прерван, только ответ в чате будет скрыт. Наследуется из `display.busy_ack_enabled` в `config.yaml`. |
| `HERMES_GATEWAY_NO_SUPERVISE` | В Docker‑образе s6‑overlay отключить авто‑надзор при запуске `hermes gateway run` и использовать семантику foreground (без авто‑перезапуска, шлюз — основной процесс контейнера). Истинные значения: `1`, `true`, `yes`. Эквивалент флага CLI `--no-supervise`. Вне s6‑образа — без эффекта. |
| `HERMES_FILE_MUTATION_VERIFIER` | Включить проверку изменений файлов за каждый ход (по умолчанию: `true`). При включении Hermes добавляет советующий список вызовов `write_file`/`patch`, которые не удались и не были заменены успешным записыванием. Установи `0`, `false`, `no` или `off`, чтобы подавить. Отражает `display.file_mutation_verifier` в `config.yaml`; переменная окружения имеет приоритет. |
| `HERMES_CRON_TIMEOUT` | Таймаут бездействия для запусков cron‑задач в секундах (по умолчанию: `600`). Агент может работать бесконечно, пока активно вызывает инструменты или получает токены потока — таймаут срабатывает только в простое. Установи `0` для снятия ограничения. |
| `HERMES_CRON_SCRIPT_TIMEOUT` | Таймаут скриптов предзапуска, привязанных к cron‑задачам, в секундах (по умолчанию: `120`). Переопредели для скриптов, требующих более длительного выполнения (например, случайные задержки для обхода анти‑ботов). Также задаётся через `cron.script_timeout_seconds` в `config.yaml`. |
| `HERMES_CRON_MAX_PARALLEL` | Максимальное количество одновременно работающих cron‑задач за тик (по умолчанию: `4`). |
## Поведение агента

| Переменная | Описание |
|------------|----------|
| `HERMES_MAX_ITERATIONS` | Максимальное количество итераций вызова инструментов за разговор (по умолчанию: 90) |
| `HERMES_INFERENCE_MODEL` | Переопределяет название модели на уровне процесса (имеет приоритет над `config.yaml` для сессии). Также задаётся флагом `-m`/`--model`. |
| `HERMES_YOLO_MODE` | Установить `1` для обхода запросов подтверждения опасных команд. Эквивалентно `--yolo`. |
| `HERMES_ACCEPT_HOOKS` | Автоматически одобрять любые неизвестные shell‑hook‑и, объявленные в `config.yaml`, без запроса в TTY. Эквивалентно `--accept-hooks` или `hooks_auto_accept: true`. |
| `HERMES_IGNORE_USER_CONFIG` | Пропускать `~/.hermes/config.yaml` и использовать встроенные значения по умолчанию (учётные данные в `.env` всё равно загружаются). Эквивалентно `--ignore-user-config`. |
| `HERMES_IGNORE_RULES` | Пропускать авто‑внедрение `AGENTS.md`, `SOUL.md`, `.cursorrules`, памяти и предзагруженных навыков. Эквивалентно `--ignore-rules`. |
| `HERMES_MD_NAMES` | Список имён файлов правил через запятую для авто‑внедрения (по умолчанию: `AGENTS.md,CLAUDE.md,.cursorrules,SOUL.md`). |
| `HERMES_TOOL_PROGRESS` | Устаревшая переменная совместимости для отображения прогресса инструмента. Предпочтительно использовать `display.tool_progress` в `config.yaml`. |
| `HERMES_TOOL_PROGRESS_MODE` | Устаревшая переменная совместимости для режима прогресса инструмента. Предпочтительно использовать `display.tool_progress` в `config.yaml`. |
| `HERMES_HUMAN_DELAY_MODE` | Регулировка темпа ответов: `off`/`natural`/`custom` |
| `HERMES_HUMAN_DELAY_MIN_MS` | Минимальное значение пользовательской задержки (мс) |
| `HERMES_HUMAN_DELAY_MAX_MS` | Максимальное значение пользовательской задержки (мс) |
| `HERMES_QUIET` | Подавление несущественного вывода (`true`/`false`) |
| `CODEX_HOME` | Когда включён [runtime сервера приложений Codex](../user-guide/features/codex-app-server-runtime), переопределяет каталог, из которого CLI Codex читает конфиг и аутентификацию (по умолчанию: `~/.codex`). Миграция Hermes записывает управляемый блок в `<CODEX_HOME>/config.toml`. |
| `HERMES_KANBAN_TASK` | Устанавливается диспетчером kanban при создании воркера (UUID задачи). Воркеры и подпроцесс `hermes-tools` MCP наследуют её, чтобы инструменты kanban корректно проверяли доступ. Не задавать вручную. |
| `HERMES_API_TIMEOUT` | Таймаут вызова LLM API в секундах (по умолчанию: `1800`) |
| `HERMES_API_CALL_STALE_TIMEOUT` | Таймаут «застоявшегося» вызова без потоковой передачи в секундах (по умолчанию: `300`). Автоматически отключается для локальных провайдеров, если не задан. Также настраивается через `providers.<id>.stale_timeout_seconds` или `providers.<id>.models.<model>.stale_timeout_seconds` в `config.yaml`. |
| `HERMES_STREAM_READ_TIMEOUT` | Таймаут чтения из потокового сокета в секундах (по умолчанию: `120`). Автоматически увеличивается до `HERMES_API_TIMEOUT` для локальных провайдеров. Увеличьте, если локальные LLM‑ы завершаются по таймауту при длительной генерации кода. |
| `HERMES_STREAM_STALE_TIMEOUT` | Таймаут обнаружения «застоявшегося» потока в секундах (по умолчанию: `180`). Автоматически отключается для локальных провайдеров. Прерывает соединение, если за этот промежуток не поступает ни одного чанка. |
| `HERMES_STREAM_RETRIES` | Количество попыток повторного подключения в середине потока при временных сетевых ошибках (по умолчанию: `3`). |
| `HERMES_AGENT_TIMEOUT` | Таймаут бездействия шлюза для запущенного агента в секундах (по умолчанию: `900`). Сбрасывается после каждого вызова инструмента и каждого полученного токена. Установить `0` для отключения. |
| `HERMES_AGENT_TIMEOUT_WARNING` | Шлюз: отправлять предупреждающее сообщение после указанного количества секунд бездействия (по умолчанию: 75 % от `HERMES_AGENT_TIMEOUT`). |
| `HERMES_AGENT_NOTIFY_INTERVAL` | Шлюз: интервал в секундах между уведомлениями о прогрессе при длительных ходах агента. |
| `HERMES_CHECKPOINT_TIMEOUT` | Таймаут создания контрольной точки в файловой системе в секундах (по умолчанию: `30`). |
| `HERMES_EXEC_ASK` | Включить запросы подтверждения выполнения в режиме шлюза (`true`/`false`) |
| `HERMES_ENABLE_PROJECT_PLUGINS` | Включить авто‑обнаружение локальных плагинов репозитория из `./.hermes/plugins/` как для загрузчика агента, так и для веб‑сервера дашборда. Принимает стандартный набор истинных значений: `1` / `true` / `yes` / `on` (без учёта регистра). Всё остальное — включая `0`, `false`, `no`, `off` и пустую строку — считается **отключённым** (по умолчанию). Примечание: начиная с GHSA‑5qr3‑c538‑wm9j (#29156) веб‑сервер дашборда отказывается автоматически импортировать файл Python `api` плагина проекта, даже если переменная включена — плагины проекта могут расширять UI через статический JS/CSS, но их бек‑энд‑маршруты загружаются только после перемещения в `~/.hermes/plugins/`. |
| `HERMES_PLUGINS_DEBUG` | `1`/`true` — выводить подробные логи обнаружения плагинов в stderr: просканированные каталоги, разобранные манифесты, причины пропуска и полные трассировки при ошибках парсинга или `register()`. Предназначено авторам плагинов. |
| `HERMES_BACKGROUND_NOTIFICATIONS` | Режим фоновых уведомлений процесса в шлюзе: `all` (по умолчанию), `result`, `error`, `off` |
| `HERMES_EPHEMERAL_SYSTEM_PROMPT` | Временный системный запрос, внедряемый во время вызова API (никогда не сохраняется в сессиях) |
| `HERMES_PREFILL_MESSAGES_FILE` | Путь к JSON‑файлу с временными предварительными сообщениями, внедряемыми во время вызова API. |
| `HERMES_ALLOW_PRIVATE_URLS` | `true`/`false` — разрешать инструментам доступ к URL‑адресам localhost/внутренних сетей. По умолчанию отключено в режиме шлюза. |
| `HERMES_REDACT_SECRETS` | `true`/`false` — управлять редактированием (маскировкой) секретов в выводе инструментов, логах и ответах чата (по умолчанию: `true`). |
| `HERMES_WRITE_SAFE_ROOT` | Необязательный префикс каталога, ограничивающий записи `write_file`/`patch`; пути за его пределами требуют подтверждения. |
| `HERMES_DISABLE_FILE_STATE_GUARD` | Установить `1` для отключения защиты «файл изменён после чтения» при `patch`/`write_file`. |
| `HERMES_CORE_TOOLS` | Список основных инструментов через запятую для переопределения (продвинутое; редко требуется). |
| `HERMES_BUNDLED_SKILLS` | Список встроенных навыков через запятую для переопределения при запуске. |
| `HERMES_OPTIONAL_SKILLS` | Список названий необязательных навыков для авто‑установки при первом запуске. |
| `HERMES_DEBUG_INTERRUPT` | Установить `1` для записи подробных трассировок прерываний/отмен в `agent.log`. |
| `HERMES_DUMP_REQUESTS` | Сохранять полезные нагрузки запросов API в файлы логов (`true`/`false`) |
| `HERMES_DUMP_REQUEST_STDOUT` | Сохранять полезные нагрузки запросов API в stdout вместо файлов логов. |
| `HERMES_OAUTH_TRACE` | Установить `1` для записи обмена OAuth‑токенами и попыток обновления. Включает замаскированную информацию о времени. |
| `HERMES_OAUTH_FILE` | Переопределить путь к файлу хранения учётных данных OAuth (по умолчанию: `~/.hermes/auth.json`). |
| `HERMES_AGENT_HELP_GUIDANCE` | Добавлять дополнительный текст рекомендаций к системному запросу для пользовательских развертываний. |
| `HERMES_AGENT_LOGO` | Переопределить ASCII‑баннер логотипа при запуске CLI. |
| `DELEGATION_MAX_CONCURRENT_CHILDREN` | Максимальное количество параллельных под‑агентов на один пакет `delegate_task` (по умолчанию: `3`, минимум 1, без верхнего ограничения). Также настраивается через `delegation.max_concurrent_children` в `config.yaml` — значение в конфиге имеет приоритет. |
## Интерфейс

| Переменная | Описание |
|------------|----------|
| `HERMES_TUI` | Запускает [TUI](../user-guide/tui.md) вместо классического CLI, если переменная установлена в `1`. Эквивалентно передаче `--tui`. |
| `HERMES_TUI_DIR` | Путь к предварительно собранному каталогу `ui-tui/` (должен содержать `dist/entry.js` и заполненный `node_modules`). Используется дистрибутивами и Nix, чтобы пропустить установку `npm install` при первом запуске. |
| `HERMES_TUI_RESUME` | Возобновляет конкретную TUI‑сессию по ID при запуске. Если переменная задана, `hermes --tui` не создаёт новую сессию, а подключается к указанной — удобно для повторного подключения после разрыва или сбоя терминала. |
| `HERMES_TUI_THEME` | Принудительно задаёт цветовую тему TUI: `light`, `dark` или сырые 6‑символьные hex‑коды фона (например, `ffffff` или `1a1a2e`). Если переменная не задана, Hermes автоматически определяет тему, используя `COLORFGBG` и запросы к фону терминала; эта переменная переопределяет определение на терминалах (Ghostty, Warp, iTerm2 и др.), которые не задают `COLORFGBG`. |
| `HERMES_INFERENCE_MODEL` | Принудительно задаёт модель для `hermes -z` / `hermes chat` без изменения `config.yaml`. Работает совместно с флагом `--provider`. Полезно для скриптов‑вызывателей (sweeper, CI, пакетные запускатели), которым нужно переопределять модель по умолчанию для каждого запуска. |
## Настройки сессии

| Variable | Description |
|----------|-------------|
| `SESSION_IDLE_MINUTES` | Сбрасывать сессии после N минут бездействия (по умолчанию: 1440) |
| `SESSION_RESET_HOUR` | Час ежедневного сброса в 24‑часовом формате (по умолчанию: 4 = 4 утра) |
| `HERMES_SESSION_ID` | **Экспортируется автоматически в каждый подпроцесс инструмента**, который запускает Hermes (`terminal`, `execute_code`, постоянный shell, бэкенды Docker/Singularity, делегированные запуски субагентов). Устанавливается агентом в текущий идентификатор сессии; скрипты пользователя, вызываемые из инструментов, могут читать его, чтобы сопоставлять вывод, телеметрию или побочные эффекты с исходной сессией Hermes. **Не следует задавать его вручную** — переопределение из родительского shell работает только вне запуска агента и перезаписывается в момент, когда агент начинает сессию. |
## Сжатие контекста (только `config.yaml`)

Сжатие контекста настраивается исключительно через `config.yaml` — переменных окружения для него нет. Настройки порога находятся в блоке `compression:`, а модель/провайдер суммирования — в `auxiliary.compression:`.

```yaml
compression:
  enabled: true
  threshold: 0.50
  target_ratio: 0.20         # fraction of threshold to preserve as recent tail
  protect_last_n: 20         # minimum recent messages to keep uncompressed
```

:::info Legacy migration
Старые конфигурации с `compression.summary_model`, `compression.summary_provider` и `compression.summary_base_url` автоматически мигрируют в `auxiliary.compression.*` при первой загрузке.
:::
## Переопределения вспомогательных задач

| Variable | Description |
|----------|-------------|
| `AUXILIARY_VISION_PROVIDER` | Переопределить провайдера для задач компьютерного зрения |
| `AUXILIARY_VISION_MODEL` | Переопределить модель для задач компьютерного зрения |
| `AUXILIARY_VISION_BASE_URL` | Прямая совместимая с OpenAI конечная точка для задач компьютерного зрения |
| `AUXILIARY_VISION_API_KEY` | API‑ключ, связанный с `AUXILIARY_VISION_BASE_URL` |
| `AUXILIARY_WEB_EXTRACT_PROVIDER` | Переопределить провайдера для извлечения/резюмирования веб‑контента |
| `AUXILIARY_WEB_EXTRACT_MODEL` | Переопределить модель для извлечения/резюмирования веб‑контента |
| `AUXILIARY_WEB_EXTRACT_BASE_URL` | Прямая совместимая с OpenAI конечная точка для извлечения/резюмирования веб‑контента |
| `AUXILIARY_WEB_EXTRACT_API_KEY` | API‑ключ, связанный с `AUXILIARY_WEB_EXTRACT_BASE_URL` |

Для задач с прямыми конечными точками Hermes использует API‑ключ, настроенный для задачи, или `OPENAI_API_KEY`. Он не переиспользует `OPENROUTER_API_KEY` для этих пользовательских конечных точек.
## Поставщики запасных вариантов (только config.yaml)

Основная цепочка запасных моделей настраивается исключительно через `config.yaml` — переменных окружения для этого нет. Добавь список верхнего уровня `fallback_providers` с ключами `provider` и `model`, чтобы включить автоматическое переключение при ошибках основной модели.

```yaml
fallback_providers:
  - provider: openrouter
    model: anthropic/claude-sonnet-4
```

Старый вариант верхнего уровня `fallback_model` с единственным поставщиком всё ещё читается для обратной совместимости, но новая конфигурация должна использовать `fallback_providers`.

См. [Fallback Providers](/user‑guide/features/fallback-providers) для полного описания.
## Маршрутизация провайдеров (только config.yaml)

Эти параметры размещаются в `~/.hermes/config.yaml` в разделе `provider_routing`:

| Ключ | Описание |
|-----|----------|
| `sort` | Сортировать провайдеров: `"price"` (по умолчанию), `"throughput"` или `"latency"` |
| `only` | Список slug‑ов провайдеров, которые разрешены (например, `["anthropic", "google"]`) |
| `ignore` | Список slug‑ов провайдеров, которые следует пропустить |
| `order` | Список slug‑ов провайдеров, которые будут пробоваться в указанном порядке |
| `require_parameters` | Использовать только провайдеров, поддерживающих все параметры запроса (`true`/`false`) |
| `data_collection` | `"allow"` (по умолчанию) или `"deny"` для исключения провайдеров, сохраняющих данные |

:::tip
Используй `hermes config set` для установки переменных окружения — это автоматически сохраняет их в нужный файл (`.env` для секретов, `config.yaml` для всего остального).
:::