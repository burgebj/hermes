---
sidebar_position: 2
title: "Змінні середовища"
description: "Повний довідник усіх змінних середовища, що використовуються Hermes Agent"
---

# Довідник змінних середовища

Усі змінні зберігаються у `~/.hermes/.env`. Також їх можна встановити за допомогою `hermes config set VAR value`.
## LLM‑провайдери
| Variable | Опис |
|----------|------|
| `OPENROUTER_API_KEY` | OpenRouter API key (рекомендовано для гнучкості) |
| `OPENROUTER_BASE_URL` | Перевизначити сумісну з OpenRouter базову URL |
| `HERMES_OPENROUTER_CACHE` | Увімкнути кешування відповідей OpenRouter (`1`/`true`/`yes`/`on`). Перевизначає `openrouter.response_cache` у `config.yaml`. Див. [Response Caching](https://openrouter.ai/docs/guides/features/response-caching). |
| `HERMES_OPENROUTER_CACHE_TTL` | Час життя кешу в секундах (1‑86400). Перевизначає `openrouter.response_cache_ttl` у `config.yaml`. |
| `NOUS_BASE_URL` | Перевизначити базову URL Nous Portal (рідко потрібно; лише для розробки/тестування) |
| `NOUS_INFERENCE_BASE_URL` | Перевизначити кінцеву точку inference Nous безпосередньо |
| `OPENAI_API_KEY` | API‑ключ для кастомних сумісних з OpenAI кінцевих точок (використовується разом з `OPENAI_BASE_URL`) |
| `OPENAI_BASE_URL` | Базова URL для кастомної кінцевої точки (VLLM, SGLang тощо) |
| `COPILOT_GITHUB_TOKEN` | GitHub token для Copilot API — пріоритетний (OAuth `gho_*` або fine‑grained PAT `github_pat_*`; classic PAT `ghp_*` **не підтримуються**) |
| `GH_TOKEN` | GitHub token — другий пріоритет для Copilot (також використовується `gh` CLI) |
| `GITHUB_TOKEN` | GitHub token — третій пріоритет для Copilot |
| `HERMES_COPILOT_ACP_COMMAND` | Перевизначити шлях до бінарника Copilot ACP CLI (за замовчуванням: `copilot`) |
| `COPILOT_CLI_PATH` | Псевдонім для `HERMES_COPILOT_ACP_COMMAND` |
| `HERMES_COPILOT_ACP_ARGS` | Перевизначити аргументи Copilot ACP (за замовчуванням: `--acp --stdio`) |
| `COPILOT_ACP_BASE_URL` | Перевизначити базову URL Copilot ACP |
| `GLM_API_KEY` | z.ai / ZhipuAI GLM API key ([z.ai](https://z.ai)) |
| `ZAI_API_KEY` | Псевдонім для `GLM_API_KEY` |
| `Z_AI_API_KEY` | Псевдонім для `GLM_API_KEY` |
| `GLM_BASE_URL` | Перевизначити базову URL z.ai (за замовчуванням: `https://api.z.ai/api/paas/v4`) |
| `KIMI_API_KEY` | Kimi / Moonshot AI API key ([moonshot.ai](https://platform.moonshot.ai)) |
| `KIMI_BASE_URL` | Перевизначити базову URL Kimi (за замовчуванням: `https://api.moonshot.ai/v1`) |
| `KIMI_CN_API_KEY` | Kimi / Moonshot China API key ([moonshot.cn](https://platform.moonshot.cn)) |
| `ARCEEAI_API_KEY` | Arcee AI API key ([chat.arcee.ai](https://chat.arcee.ai/)) |
| `ARCEE_BASE_URL` | Перевизначити базову URL Arcee (за замовчуванням: `https://api.arcee.ai/api/v1`) |
| `GMI_API_KEY` | GMI Cloud API key ([gmicloud.ai](https://www.gmicloud.ai/)) |
| `GMI_BASE_URL` | Перевизначити базову URL GMI Cloud (за замовчуванням: `https://api.gmi-serving.com/v1`) |
| `MINIMAX_API_KEY` | MiniMax API key — глобальна кінцева точка ([minimax.io](https://www.minimax.io)). **Не використовується `minimax‑oauth`** (OAuth‑шлях використовує вхід у браузері). |
| `MINIMAX_BASE_URL` | Перевизначити базову URL MiniMax (за замовчуванням: `https://api.minimax.io/anthropic` — Hermes використовує сумісну з Anthropic Messages кінцеву точку MiniMax). **Не використовується `minimax‑oauth`**. |
| `MINIMAX_CN_API_KEY` | MiniMax API key — китайська кінцева точка ([minimaxi.com](https://www.minimaxi.com)). **Не використовується `minimax‑oauth`** (OAuth‑шлях використовує вхід у браузері). |
| `MINIMAX_CN_BASE_URL` | Перевизначити базову URL MiniMax China (за замовчуванням: `https://api.minimaxi.com/anthropic`). **Не використовується `minimax‑oauth`**. |
| `KILOCODE_API_KEY` | Kilo Code API key ([kilo.ai](https://kilo.ai)) |
| `KILOCODE_BASE_URL` | Перевизначити базову URL Kilo Code (за замовчуванням: `https://api.kilo.ai/api/gateway`) |
| `XIAOMI_API_KEY` | Xiaomi MiMo API key ([platform.xiaomimimo.com](https://platform.xiaomimimo.com)) |
| `XIAOMI_BASE_URL` | Перевизначити базову URL Xiaomi MiMo (за замовчуванням: `https://api.xiaomimimo.com/v1`) |
| `TOKENHUB_API_KEY` | Tencent TokenHub API key ([tokenhub.tencentmaas.com](https://tokenhub.tencentmaas.com)) |
| `TOKENHUB_BASE_URL` | Перевизначити базову URL Tencent TokenHub (за замовчуванням: `https://tokenhub.tencentmaas.com/v1`) |
| `AZURE_FOUNDRY_API_KEY` | Microsoft Foundry / Azure OpenAI API key ([ai.azure.com](https://ai.azure.com/)). Не потрібен, коли `model.auth_mode: entra_id` |
| `AZURE_FOUNDRY_BASE_URL` | URL кінцевої точки Microsoft Foundry (наприклад `https://<resource>.openai.azure.com/openai/v1` для стилю OpenAI або `https://<resource>.services.ai.azure.com/anthropic` для стилю Anthropic) |
| `AZURE_ANTHROPIC_KEY` | Azure Anthropic API key для `provider: anthropic` + `base_url`, що вказує на розгортання Microsoft Foundry Claude (альтернатива `ANTHROPIC_API_KEY`, коли налаштовано і Anthropic, і Azure Anthropic) |
| `AZURE_TENANT_ID` | Entra ID tenant ID (потоки service‑principal; використовується `azure-identity`, коли `model.auth_mode: entra_id`) |
| `AZURE_CLIENT_ID` | Entra ID client ID (service principal, workload identity або user‑assigned managed identity) |
| `AZURE_CLIENT_SECRET` | Секрет service principal, що використовується `EnvironmentCredential` |
| `AZURE_CLIENT_CERTIFICATE_PATH` | Сертифікат service principal (альтернатива `AZURE_CLIENT_SECRET`) |
| `AZURE_FEDERATED_TOKEN_FILE` | Шлях до файлу федеративного токену для AKS Workload Identity / OIDC потоків |
| `AZURE_AUTHORITY_HOST` | Перевизначення authority суверенної хмари (наприклад `https://login.microsoftonline.us` для Azure Government). |
| Дивись [Посібник Azure Foundry](/guides/azure-foundry#sovereign-clouds-government-china) |
| `IDENTITY_ENDPOINT` / `MSI_ENDPOINT` | Кінцева точка Managed Identity для App Service, Functions та Container Apps; віртуальні машини зазвичай використовують IMDS і не встановлюють ці змінні |
| `HF_TOKEN` | Токен Hugging Face для Inference Providers ([huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)) |
| `HF_BASE_URL` | Перевизначення базового URL Hugging Face (за замовчуванням: `https://router.huggingface.co/v1`) |
| `GOOGLE_API_KEY` | API‑ключ Google AI Studio ([aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)) |
| `GEMINI_API_KEY` | Псевдонім для `GOOGLE_API_KEY` |
| `GEMINI_BASE_URL` | Перевизначення базового URL Google AI Studio |
| `HERMES_GEMINI_CLIENT_ID` | OAuth‑client ID для `google-gemini-cli` PKCE‑login (необов’язково; за замовчуванням використовується публічний клієнт gemini‑cli від Google) |
| `HERMES_GEMINI_CLIENT_SECRET` | OAuth‑client secret для `google-gemini-cli` (необов’язково) |
| `HERMES_GEMINI_PROJECT_ID` | Ідентифікатор проєкту GCP для платних рівнів Gemini (безкоштовний рівень створюється автоматично) |
| `ANTHROPIC_API_KEY` | API‑ключ Anthropic Console ([console.anthropic.com](https://console.anthropic.com/)) |
| `ANTHROPIC_TOKEN` | Перевизначення ручного або застарілого Anthropic OAuth/setup‑token |
| `DASHSCOPE_API_KEY` | API‑ключ Qwen Cloud (Alibaba DashScope) для моделей Qwen ([modelstudio.console.alibabacloud.com](https://modelstudio.console.alibabacloud.com/)) |
| `DASHSCOPE_BASE_URL` | Кастомний базовий URL DashScope (за замовчуванням: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`; використовуйте `https://dashscope.aliyuncs.com/compatible-mode/v1` для регіону материкового Китаю) |
| `DEEPSEEK_API_KEY` | API‑ключ DeepSeek для прямого доступу до DeepSeek ([platform.deepseek.com](https://platform.deepseek.com/api_keys)) |
| `DEEPSEEK_BASE_URL` | Кастомний базовий URL DeepSeek API |
| `NOVITA_API_KEY` | API‑ключ NovitaAI — AI‑нативний хмарний сервіс для Model API, Agent Sandbox та GPU Cloud ([novita.ai/settings/key-management](https://novita.ai/settings/key-management)) |
| `NOVITA_BASE_URL` | Перевизначення базового URL NovitaAI (за замовчуванням: `https://api.novita.ai/openai/v1`) |
| `NVIDIA_API_KEY` | API‑ключ NVIDIA NIM — Nemotron та відкриті моделі ([build.nvidia.com](https://build.nvidia.com)) |
| `NVIDIA_BASE_URL` | Перевизначення базового URL NVIDIA (за замовчуванням: `https://integrate.api.nvidia.com/v1`; встановіть `http://localhost:8000/v1` для локальної точки NIM) |
| `STEPFUN_API_KEY` | API‑ключ StepFun — моделі серії Step ([platform.stepfun.com](https://platform.stepfun.com)) |
| `STEPFUN_BASE_URL` | Перевизначення базового URL StepFun (за замовчуванням: `https://api.stepfun.com/v1`) |
| `OLLAMA_API_KEY` | API‑ключ Ollama Cloud — керований каталог Ollama без локального GPU ([ollama.com/settings/keys](https://ollama.com/settings/keys)) |
| `OLLAMA_BASE_URL` | Перевизначення базового URL Ollama Cloud (за замовчуванням: `https://ollama.com/v1`) |
| `XAI_API_KEY` | API‑ключ xAI (Grok) для чату, TTS та веб‑пошуку ([console.x.ai](https://console.x.ai/)) |
| `XAI_BASE_URL` | Перевизначення базового URL xAI (за замовчуванням: `https://api.x.ai/v1`) |
| `MISTRAL_API_KEY` | API‑ключ Mistral для Voxtral TTS та Voxtral STT ([console.mistral.ai](https://console.mistral.ai)) |
| `AWS_REGION` | Регіон AWS для інференсу Bedrock (наприклад, `us-east-1`, `eu-central-1`). Читається бібліотекою boto3. |
| `AWS_PROFILE` | Іменований профіль AWS для автентифікації Bedrock (читає `~/.aws/credentials`). Якщо не вказано — використовується стандартний ланцюжок облікових даних boto3. |
| `BEDROCK_BASE_URL` | Перевизначення базового URL середовища виконання Bedrock (за замовчуванням: `https://bedrock-runtime.us-east-1.amazonaws.com`; зазвичай залишають порожнім і використовують `AWS_REGION`) |
| `HERMES_QWEN_BASE_URL` | Перевизначення базового URL Qwen Portal (за замовчуванням: `https://portal.qwen.ai/v1`) |
| `OPENCODE_ZEN_API_KEY` | API‑ключ OpenCode Zen — доступ «pay‑as‑you‑go» до підготовлених моделей ([opencode.ai](https://opencode.ai/auth)) |
| `OPENCODE_ZEN_BASE_URL` | Перевизначення базового URL OpenCode Zen |
| `OPENCODE_GO_API_KEY` | API‑ключ OpenCode Go — підписка $10/міс для відкритих моделей ([opencode.ai](https://opencode.ai/auth)) |
| `OPENCODE_GO_BASE_URL` | Перевизначення базового URL OpenCode Go |
| `CLAUDE_CODE_OAUTH_TOKEN` | Явне перевизначення токену Claude Code, якщо його експортуєш вручну |
| `HERMES_MODEL` | Перевизначення назви моделі на рівні процесу (використовується планувальником cron; для звичайного використання краще `config.yaml`) |
| `VOICE_TOOLS_OPENAI_KEY` | Бажаний ключ OpenAI для провайдерів розпізнавання мови та синтезу мови OpenAI |
| `HERMES_LOCAL_STT_COMMAND` | Необов’язковий шаблон локальної команди розпізнавання мови. Підтримує плейсхолдери `{input_path}`, `{output_dir}`, `{language}` та `{model}` |
| `HERMES_LOCAL_STT_LANGUAGE` | Мова за замовчуванням, що передається до `HERMES_LOCAL_STT_COMMAND` або автоматично визначена локальним fallback‑CLI `whisper` (за замовчуванням: `en`) |
| `HERMES_HOME` | Перевизначення каталогу конфігурації Hermes (за замовчуванням: `~/.hermes`). Також впливає на файл PID шлюзу та назву сервісу systemd, що дозволяє одночасно запускати кілька інсталяцій |
| `HERMES_GIT_BASH_PATH` | **Тільки Windows.** Перевизначення пошуку `bash.exe` для інструменту терміналу. Показує на будь‑який bash — повна інсталяція Git‑for‑Windows, bash у WSL через symlink, MSYS2, Cygwin. Інсталятор автоматично встановлює шлях до PortableGit, який він підготував. Дивись [Windows (Native) Guide](../user-guide/windows-native.md#how-hermes-runs-shell-commands-on-windows) |
| `HERMES_DISABLE_WINDOWS_UTF8` | **Тільки Windows.** Встанови `1`, щоб вимкнути shim UTF‑8 stdio (`configure_windows_stdio()`) і повернутись до кодової сторінки локалі консолі. Корисно для діагностики проблем кодування; рідко потрібне в звичайній роботі |
| `HERMES_KANBAN_HOME` | Перевизначення спільного кореня Hermes, що прив’язує kanban‑дошку (база даних + робочі простори + логи воркерів). Повертається до `get_default_hermes_root()` (батьківський каталог активного профілю). Корисно для тестів та незвичних розгортань |
| `HERMES_KANBAN_BOARD` | Фіксує активну kanban‑дошку для цього процесу. Має пріоритет над `~/.hermes/kanban/current`; диспетчер передає це у середовище підпроцесів воркерів, тому воркери фізично не бачать завдань на інших дошках. За замовчуванням `default`. Валідація slug: лише малі латинські літери, цифри, дефіси та підкреслення, 1‑64 символи |
| `HERMES_KANBAN_DB` | Фіксує шлях до файлу бази даних kanban безпосередньо (найвищий пріоритет; переважає `HERMES_KANBAN_BOARD` і `HERMES_KANBAN_HOME`). Диспетчер передає це у середовище підпроцесів воркерів, щоб вони працювали з однією дошкою |
| `HERMES_KANBAN_WORKSPACES_ROOT` | Фіксує кореневий каталог робочих просторів kanban безпосередньо (найвищий пріоритет для робочих просторів; переважає `HERMES_KANBAN_HOME`). Диспетчер передає це у середовище підпроцесів воркерів |
| `HERMES_KANBAN_DISPATCH_IN_GATEWAY` | Перевизначення під час виконання для `kanban.dispatch_in_gateway`. Встанови `0`, `false`, `no` або `off`, щоб запобігти запуску вбудованого диспетчера Kanban у шлюзі; будь‑яке інше непорожнє значення його вмикає. Корисно, коли окремий процес‑диспетчер володіє дошкою. |
## Авторизація провайдера (OAuth)

Для нативної авторизації Anthropic Hermes надає перевагу власним файлам облікових даних Claude Code, якщо вони існують, оскільки ці облікові дані можуть автоматично оновлюватися. **OAuth до Anthropic вимагає плану Claude Max з придбаними додатковими кредитами використання** — Hermes працює як Claude Code, який бере кредити лише з додаткових/перевищувальних кредитів плану Max, а не з базової квоти Max, і не працює на Claude Pro. Якщо немає Max + додаткових кредитів, використовуй API‑ключ. Змінні середовища, такі як `ANTHROPIC_TOKEN`, залишаються корисними як ручні перевизначення, проте вони не є більше рекомендованим шляхом для входу в Claude Max.

| Variable | Description |
|----------|-------------|
| `HERMES_PORTAL_BASE_URL` | Перевизначити URL Nous Portal (для розробки/тестування) |
| `NOUS_INFERENCE_BASE_URL` | Перевизначити URL API inference Nous |
| `HERMES_NOUS_MIN_KEY_TTL_SECONDS` | Мінімальний TTL ключа агента перед повторним створенням (за замовчуванням: 1800 = 30 хв) |
| `HERMES_NOUS_TIMEOUT_SECONDS` | Тайм‑аут HTTP для потоків облікових даних / токенів Nous |
| `HERMES_DUMP_REQUESTS` | Записувати навантаження API‑запитів у файли журналу (`true`/`false`) |
| `HERMES_PREFILL_MESSAGES_FILE` | Шлях до JSON‑файлу з тимчасовими попередньо заповненими повідомленнями, які вставляються під час виклику API |
| `HERMES_TIMEZONE` | Перевизначення часової зони IANA (наприклад `America/New_York`) |
## API інструментів

| Змінна | Опис |
|----------|-------------|
| `PARALLEL_API_KEY` | AI‑нативний веб‑пошук ([parallel.ai](https://parallel.ai/)) |
| `FIRECRAWL_API_KEY` | Веб‑скрейпінг і хмарний браузер ([firecrawl.dev](https://firecrawl.dev/)) |
| `FIRECRAWL_API_URL` | Кастомна кінцева точка Firecrawl API для самохостинг‑екземплярів (необов’язково) |
| `TAVILY_API_KEY` | Ключ Tavily API для AI‑нативного веб‑пошуку, екстракції та сканування ([app.tavily.com](https://app.tavily.com/home)) |
| `SEARXNG_URL` | URL інстансу SearXNG для безкоштовного самохостинг‑веб‑пошуку — без ключа API ([searxng.github.io](https://searxng.github.io/searxng/)) |
| `TAVILY_BASE_URL` | Перевизначає кінцеву точку Tavily API. Корисно для корпоративних проксі та самохостинг‑бекендів, сумісних з Tavily. Така ж схема, як у `GROQ_BASE_URL`. |
| `EXA_API_KEY` | Ключ Exa API для AI‑нативного веб‑пошуку та вмісту ([exa.ai](https://exa.ai/)) |
| `BROWSERBASE_API_KEY` | Автоматизація браузера ([browserbase.com](https://browserbase.com/)) |
| `BROWSERBASE_PROJECT_ID` | Ідентифікатор проєкту Browserbase |
| `BROWSER_USE_API_KEY` | Ключ Browser Use cloud browser API ([browser-use.com](https://browser-use.com/)) |
| `FIRECRAWL_BROWSER_TTL` | Термін життя сесії браузера Firecrawl у секундах (за замовчуванням: 300) |
| `BROWSER_CDP_URL` | URL Chrome DevTools Protocol для локального браузера (встановлюється через `/browser connect`, напр. `ws://localhost:9222`) |
| `CAMOFOX_URL` | Локальний URL анти‑детекційного браузера Camofox (за замовчуванням: `http://localhost:9377`) |
| `CAMOFOX_USER_ID` | Необов’язковий зовнішньо керований ідентифікатор користувача Camofox для спільних видимих сесій |
| `CAMOFOX_SESSION_KEY` | Необов’язковий ключ сесії Camofox, що використовується при створенні вкладок для `CAMOFOX_USER_ID` |
| `CAMOFOX_ADOPT_EXISTING_TAB` | Встанови `true`, щоб повторно використати існуючу вкладку Camofox перед створенням нової |
| `BROWSER_INACTIVITY_TIMEOUT` | Тайм‑аут неактивності сесії браузера у секундах |
| `AGENT_BROWSER_ARGS` | Додаткові прапорці запуску Chromium (через кому або новий рядок). Hermes автоматично ін’єкціює `--no-sandbox,--disable-dev-shm-usage`, коли працює під root або в просторах імен користувачів, обмежених AppArmor (Ubuntu 23.10+, DGX Spark, багато контейнерних образів); встановлюй вручну лише для перевизначення або додавання інших прапорців. |
| `FAL_KEY` | Генерація зображень ([fal.ai](https://fal.ai/)) |
| `GROQ_API_KEY` | Ключ Groq Whisper STT API ([groq.com](https://groq.com/)) |
| `ELEVENLABS_API_KEY` | Преміум‑голоси ElevenLabs TTS ([elevenlabs.io](https://elevenlabs.io/)) |
| `STT_GROQ_MODEL` | Перевизначає модель Groq STT (за замовчуванням: `whisper-large-v3-turbo`) |
| `GROQ_BASE_URL` | Перевизначає кінцеву точку Groq OpenAI‑сумісного STT |
| `STT_OPENAI_MODEL` | Перевизначає модель OpenAI STT (за замовчуванням: `whisper-1`) |
| `STT_OPENAI_BASE_URL` | Перевизначає OpenAI‑сумісну кінцеву точку STT |
| `GITHUB_TOKEN` | Токен GitHub для Skills Hub (вищі ліміти API, публікація skill) |
| `HONCHO_API_KEY` | Крос‑сесійне моделювання користувачів ([honcho.dev](https://honcho.dev/)) |
| `HONCHO_BASE_URL` | Базовий URL для самохостинг‑екземплярів Honcho (за замовчуванням: Honcho cloud). Для локальних інстансів ключ API не потрібен |
| `HINDSIGHT_TIMEOUT` | Тайм‑аут у секундах для викликів API провайдера пам’яті Hindsight (за замовчуванням: `60`). Збільш його, якщо твій інстанс Hindsight повільно відповідає під час `/sync` або `on_session_switch` і ти бачиш тайм‑аут у `errors.log`. |
| `SUPERMEMORY_API_KEY` | Семантична довготривала пам’ять з відновленням профілю та інжестом сесії ([supermemory.ai](https://supermemory.ai)) |
| `DAYTONA_API_KEY` | Хмарні пісочниці Daytona ([daytona.io](https://daytona.io/)) |

### Спостереження Langfuse

Змінні середовища для вбудованого плагіна [`observability/langfuse`](/user-guide/features/built-in-plugins#observabilitylangfuse). Додай їх у `~/.hermes/.env`. Плагін також треба ввімкнути (`hermes plugins enable observability/langfuse` або позначити галочкою в `hermes plugins`) перед тим, як вони набудуть сили.

| Змінна | Опис |
|----------|-------------|
| `HERMES_LANGFUSE_PUBLIC_KEY` | Публічний ключ проєкту Langfuse (`pk-lf-...`). Обов’язково. |
| `HERMES_LANGFUSE_SECRET_KEY` | Секретний ключ проєкту Langfuse (`sk-lf-...`). Обов’язково. |
| `HERMES_LANGFUSE_BASE_URL` | URL сервера Langfuse (за замовчуванням: `https://cloud.langfuse.com`). Для самохостингу. |
| `HERMES_LANGFUSE_ENV` | Тег середовища у трасах (`production`, `staging`, …) |
| `HERMES_LANGFUSE_RELEASE` | Тег релізу/версії у трасах |
| `HERMES_LANGFUSE_SAMPLE_RATE` | Швидкість вибірки SDK 0.0–1.0 (за замовчуванням: `1.0`) |
| `HERMES_LANGFUSE_MAX_CHARS` | Обрізка поля для серіалізованих навантажень (за замовчуванням: `12000`) |
| `HERMES_LANGFUSE_DEBUG` | `true` вмикає докладне логування плагіна у `agent.log` |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL` | Стандартні назви SDK Langfuse. Приймаються як резерви, коли еквіваленти `HERMES_LANGFUSE_*` не встановлені. |

### Шлюз інструментів (Tool Gateway)

Ці змінні налаштовують [Tool Gateway](/user-guide/features/tool-gateway) для платних підписників Nous або самохостинг‑розгортань шлюзу. Більшість користувачів їх не потребують — шлюз налаштовується автоматично через `hermes model` або `hermes tools`.

| Змінна | Опис |
|----------|-------------|
| `TOOL_GATEWAY_DOMAIN` | Базовий домен для маршрутизації шлюзу інструментів (за замовчуванням: `nousresearch.com`) |
| `TOOL_GATEWAY_SCHEME` | Схема HTTP або HTTPS для URL шлюзу (за замовчуванням: `https`) |
| `TOOL_GATEWAY_USER_TOKEN` | Токен автентифікації для шлюзу інструментів (зазвичай автозаповнюється з Nous auth) |
| `FIRECRAWL_GATEWAY_URL` | Перевизначає URL кінцевої точки шлюзу Firecrawl конкретно |
## Terminal Backend

| Variable | Description |
|----------|-------------|
| `TERMINAL_ENV` | Backend: `local`, `docker`, `ssh`, `singularity`, `modal`, `daytona` |
| `HERMES_DOCKER_BINARY` | Перевизначає бінарник контейнера, до якого Hermes звертається (наприклад, `podman`, `/usr/local/bin/docker`). Якщо не встановлено, Hermes автоматично шукає `docker` або `podman` у `PATH`. Потрібно, коли встановлені обидва і потрібен не за замовчуванням, або коли бінарник знаходиться поза `PATH`. |
| `TERMINAL_DOCKER_IMAGE` | Docker‑образ (за замовчуванням: `nikolaik/python-nodejs:python3.11-nodejs20`) |
| `TERMINAL_DOCKER_FORWARD_ENV` | JSON‑масив імен змінних середовища, які потрібно явно передати у Docker‑сесії терміналу. Примітка: `required_environment_variables`, оголошені skill‑ом, передаються автоматично — це потрібно лише для змінних, не оголошених жодним skill‑ом. |
| `TERMINAL_DOCKER_VOLUMES` | Додаткові монтування Docker‑томів (пари `host:container`, розділені комами) |
| `TERMINAL_DOCKER_MOUNT_CWD_TO_WORKSPACE` | Розширений варіант: монтувати поточний робочий каталог у Docker `/workspace` (`true`/`false`, за замовчуванням: `false`) |
| `TERMINAL_SINGULARITY_IMAGE` | Singularity‑образ або шлях до `.sif` |
| `TERMINAL_MODAL_IMAGE` | Образ контейнера Modal |
| `TERMINAL_DAYTONA_IMAGE` | Образ sandbox Daytona |
| `TERMINAL_TIMEOUT` | Тайм‑аут команди в секундах |
| `TERMINAL_LIFETIME_SECONDS` | Максимальний час життя сесій терміналу в секундах |
| `TERMINAL_CWD` | Робочий каталог для сесій терміналу (лише gateway/cron; CLI використовує каталог запуску) |
| `SUDO_PASSWORD` | Дозволити sudo без інтерактивного запиту |

Для бекендів хмарних sandbox‑ів зберігання орієнтоване на файлову систему. `TERMINAL_LIFETIME_SECONDS` керує тим, коли Hermes очищає бездіяльну сесію терміналу, а подальші відновлення можуть створити новий sandbox замість підтримки тих самих живих процесів.
## SSH бекенд

| Змінна | Опис |
|----------|-------------|
| `TERMINAL_SSH_HOST` | Ім'я хоста віддаленого сервера |
| `TERMINAL_SSH_USER` | SSH ім'я користувача |
| `TERMINAL_SSH_PORT` | SSH порт (за замовчуванням: 22) |
| `TERMINAL_SSH_KEY` | Шлях до приватного ключа |
| `TERMINAL_SSH_PERSISTENT` | Перевизначити постійний шел для SSH (за замовчуванням: слідує `TERMINAL_PERSISTENT_SHELL`) |
## Ресурси контейнера (Docker, Singularity, Modal, Daytona)

| Змінна | Опис |
|----------|-------------|
| `TERMINAL_CONTAINER_CPU` | CPU‑ядра (за замовчуванням: 1) |
| `TERMINAL_CONTAINER_MEMORY` | Пам'ять у МБ (за замовчуванням: 5120) |
| `TERMINAL_CONTAINER_DISK` | Диск у МБ (за замовчуванням: 51200) |
| `TERMINAL_CONTAINER_PERSISTENT` | Зберігати файлову систему контейнера між сесіями (за замовчуванням: `true`) |
| `TERMINAL_SANDBOX_DIR` | Каталог хоста для робочих просторів і накладок (за замовчуванням: `~/.hermes/sandboxes/`) |
## Постійна оболонка

| Змінна | Опис |
|----------|-------------|
| `TERMINAL_PERSISTENT_SHELL` | Увімкнути постійну оболонку для не‑локальних бекендів (за замовчуванням: `true`). Також можна встановити через `terminal.persistent_shell` у `config.yaml` |
| `TERMINAL_LOCAL_PERSISTENT` | Увімкнути постійну оболонку для локального бекенда (за замовчуванням: `false`) |
| `TERMINAL_SSH_PERSISTENT` | Перевизначити постійну оболонку для SSH‑бекенда (за замовчуванням: слідує `TERMINAL_PERSISTENT_SHELL`) |
## Обмін повідомленнями
| Variable | Опис |
|----------|------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram‑бота (від @BotFather) |
| `TELEGRAM_ALLOWED_USERS` | Список ID користувачів, розділених комами, яким дозволено користуватися ботом (застосовується до особистих повідомлень, груп і форумів) |
| `TELEGRAM_GROUP_ALLOWED_USERS` | Список ID користувачів‑відправників, розділених комами, які авторизовані лише в групах/форумах (НЕ надає доступу до особистих повідомлень). Значення у вигляді Chat‑ID (починаються з `-`) залишаються сумісними для старих конфігурацій до #17686, з попередженням про застарілість. |
| `TELEGRAM_GROUP_ALLOWED_CHATS` | Список ID чатів груп/форумів, розділених комами; будь‑хто з учасників має доступ |
| `TELEGRAM_HOME_CHANNEL` | Канал/чат Telegram за замовчуванням для доставки cron‑повідомлень |
| `TELEGRAM_HOME_CHANNEL_NAME` | Відображуване ім’я домашнього каналу Telegram |
| `TELEGRAM_CRON_THREAD_ID` | ID теми форуму для отримання cron‑повідомлень; переважає `TELEGRAM_HOME_CHANNEL_THREAD_ID` лише для cron. Використовуй у режимі тем, щоб відповіді на cron‑повідомлення відкривали нову **сесію**, а не потрапляли в системну лобі (#24409). |
| `TELEGRAM_WEBHOOK_URL` | Публічний HTTPS‑URL для режиму webhook (вмикає webhook замість polling) |
| `TELEGRAM_WEBHOOK_PORT` | Локальний порт для прослуховування webhook‑сервера (за замовчуванням: `8443`) |
| `TELEGRAM_WEBHOOK_SECRET` | Секретний токен, який Telegram повертає у кожному оновленні для перевірки. **Обов’язково, коли встановлено `TELEGRAM_WEBHOOK_URL`** — шлюз не запуститься без нього (GHSA-3vpc-7q5r-276h). Генерується командою `openssl rand -hex 32`. |
| `TELEGRAM_REACTIONS` | Увімкнути реакції‑емодзі на повідомленнях під час обробки (за замовчуванням: `false`) |
| `TELEGRAM_REQUIRE_MENTION` | Потрібне явне згадування перед відповіддю в групах Telegram. Еквівалент `telegram.require_mention` у `config.yaml`. |
| `TELEGRAM_MENTION_PATTERNS` | JSON‑масив, список, розділений новими рядками, або список, розділений комами, regex‑шаблонів‑виклику, які приймаються, коли ввімкнено фільтрацію згадувань у групах Telegram. Еквівалент `telegram.mention_patterns`. |
| `TELEGRAM_EXCLUSIVE_BOT_MENTIONS` | Якщо увімкнено, явні згадки `@...bot` у групах Telegram маршрутизуються лише до зазначених імен ботів перед запуском відповіді або запасних варіантів. За замовчуванням: `true`. Еквівалент `telegram.exclusive_bot_mentions`. |
| `TELEGRAM_REPLY_TO_MODE` | Поведінка посилань у відповідях: `off`, `first` (за замовчуванням) або `all`. Відповідає шаблону Discord. |
| `TELEGRAM_IGNORED_THREADS` | Список ID тем/тредів форуму Telegram, розділених комами, у яких бот ніколи не відповідає |
| `TELEGRAM_PROXY` | URL проксі для підключень Telegram — переважає `HTTPS_PROXY`. Підтримує `http://`, `https://`, `socks5://` |
| `DISCORD_BOT_TOKEN` | Токен Discord‑бота |
| `DISCORD_ALLOWED_USERS` | Список ID користувачів Discord, розділених комами, яким дозволено користуватися ботом |
| `DISCORD_ALLOWED_ROLES` | Список ID ролей Discord, розділених комами, яким дозволено користуватися ботом (OR з `DISCORD_ALLOWED_USERS`). Автоматично вмикає інтенти Members. Корисно, коли команди модерації змінюються — права ролі поширюються автоматично. |
| `DISCORD_ALLOWED_CHANNELS` | Список ID каналів Discord, розділених комами. Якщо встановлено, бот відповідає лише в цих каналах (плюс DMs, якщо дозволено). Переважає `config.yaml` `discord.allowed_channels`. |
| `DISCORD_PROXY` | URL проксі для підключень Discord — переважає `HTTPS_PROXY`. Підтримує `http://`, `https://`, `socks5://` |
| `DISCORD_HOME_CHANNEL` | Канал Discord за замовчуванням для доставки cron‑повідомлень |
| `DISCORD_HOME_CHANNEL_NAME` | Відображуване ім’я домашнього каналу Discord |
| `DISCORD_COMMAND_SYNC_POLICY` | Політика синхронізації slash‑команд Discord під час старту: `safe` (diff і reconcile), `bulk` (застарілий `tree.sync()`), або `off` |
| `DISCORD_REQUIRE_MENTION` | Потрібне згадування @ перед відповіддю в каналах сервера |
| `DISCORD_FREE_RESPONSE_CHANNELS` | Список ID каналів, у яких згадування не обов’язкове |
| `DISCORD_AUTO_THREAD` | Автоматично створювати треди для довгих відповідей, коли підтримується |
| `DISCORD_ALLOW_ANY_ATTACHMENT` | Якщо `true`, приймати вкладення будь‑якого типу файлу (не лише зі вбудованого білого списку PDF/text/zip/office). Невідомі типи кешуються та передаються агенту як локальний шлях, щоб його можна було проаналізувати через `terminal` / `read_file` / `ffprobe`. За замовчуванням `false`. |
| `DISCORD_MAX_ATTACHMENT_BYTES` | Максимальна кількість байт на одне вкладення, яке шлюз кешуватиме. За замовчуванням `33554432` (32 MiB). Встанови `0` для відсутності обмеження (вкладення тримаються в пам’яті під час запису). |
| `DISCORD_REACTIONS` | Увімкнути реакції‑емодзі на повідомленнях під час обробки (за замовчуванням: `true`) |
| `DISCORD_IGNORED_CHANNELS` | Список ID каналів, у яких бот ніколи не відповідає |
| `DISCORD_NO_THREAD_CHANNELS` | Список ID каналів, у яких бот відповідає без автоматичного створення треду |
| `DISCORD_REPLY_TO_MODE` | Поведінка посилань у відповідях: `off`, `first` (за замовчуванням) або `all` |
| `DISCORD_ALLOW_MENTION_EVERYONE` | Дозволити боту згадувати `@everyone`/`@here` (за замовчуванням: `false`). Див. [Контроль згадувань](../user-guide/messaging/discord.md#mention-control). |
| `DISCORD_ALLOW_MENTION_ROLES` | Дозволити боту згадувати ролі `@role` (за замовчуванням: `false`). |
| `DISCORD_ALLOW_MENTION_USERS` | Дозволити боту згадувати окремих користувачів `@user` (за замовчуванням: `true`). |
| `DISCORD_ALLOW_MENTION_REPLIED_USER` | Згадувати автора при відповіді на його повідомлення (за замовчуванням: `true`). |
| `SLACK_BOT_TOKEN` | Токен Slack‑бота (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Токен рівня додатку Slack (`xapp-...`, потрібен для Socket Mode) |
| `SLACK_ALLOWED_USERS` | Список ID користувачів Slack, розділених комами |
| `SLACK_HOME_CHANNEL` | Канал Slack за замовчуванням для доставки cron‑повідомлень |
| `SLACK_HOME_CHANNEL_NAME` | Відображуване ім’я домашнього каналу Slack |
| `GOOGLE_CHAT_PROJECT_ID` | Ідентифікатор GCP‑проєкту, що розміщує тему Pub/Sub (переважає `GOOGLE_CLOUD_PROJECT`) |
| `GOOGLE_CHAT_SUBSCRIPTION_NAME` | Повний шлях підписки Pub/Sub, `projects/{proj}/subscriptions/{sub}` (старий псевдонім: `GOOGLE_CHAT_SUBSCRIPTION`) |
| `GOOGLE_CHAT_SERVICE_ACCOUNT_JSON` | Шлях до JSON Service Account або вбудований JSON (переважає `GOOGLE_APPLICATION_CREDENTIALS`) |
| `GOOGLE_CHAT_ALLOWED_USERS` | Список електронних адрес користувачів, розділених комами, яким дозволено спілкуватися з ботом |
| `GOOGLE_CHAT_ALLOW_ALL_USERS` | Дозволити будь‑якому користувачу Google Chat ініціювати бота (лише для розробки) |
| `GOOGLE_CHAT_HOME_CHANNEL` | Простір за замовчуванням (наприклад) |
| `GOOGLE_CHAT_HOME_CHANNEL_NAME` | Відображуване ім’я простору домашнього каналу Google Chat |
| `GOOGLE_CHAT_MAX_MESSAGES` | Pub/Sub FlowControl max in‑flight messages (за замовчуванням: `1`) |
| `GOOGLE_CHAT_MAX_BYTES` | Pub/Sub FlowControl max in‑flight bytes (за замовчуванням: `16777216`, 16 MiB) |
| `GOOGLE_CHAT_BOOTSTRAP_SPACES` | Додаткові ідентифікатори просторів, розділені комами, які слід перевіряти під час запуску при розв’язанні власного `users/{id}` бота |
| `GOOGLE_CHAT_DEBUG_RAW` | Встанови будь‑яке значення, щоб записувати редаговані конверти Pub/Sub на рівні DEBUG (лише для налагодження) |
| `WHATSAPP_ENABLED` | Увімкнути міст (bridge) WhatsApp (`true`/`false`) |
| `WHATSAPP_MODE` | `bot` (окремий номер) або `self-chat` (повідомляти самому собі) |
| `WHATSAPP_ALLOWED_USERS` | Номери телефонів, розділені комами (з кодом країни, без `+`), або `*` — дозволити всіх відправників |
| `WHATSAPP_ALLOW_ALL_USERS` | Дозволити всім відправникам WhatsApp без білого списку (`true`/`false`) |
| `WHATSAPP_DEBUG` | Записувати необроблені події повідомлень у мосту для діагностики (`true`/`false`) |
| `SIGNAL_HTTP_URL` | HTTP‑endpoint демона signal‑cli (наприклад `http://127.0.0.1:8080`) |
| `SIGNAL_ACCOUNT` | Номер телефону бота у форматі E.164 |
| `SIGNAL_ALLOWED_USERS` | Номери телефонів у форматі E.164 або UUID, розділені комами |
| `SIGNAL_GROUP_ALLOWED_USERS` | Ідентифікатори груп, розділені комами, або `*` — усі групи |
| `SIGNAL_HOME_CHANNEL_NAME` | Відображуване ім’я домашнього каналу Signal |
| `SIGNAL_IGNORE_STORIES` | Ігнорувати історії/оновлення статусу Signal |
| `SIGNAL_ALLOW_ALL_USERS` | Дозволити всім користувачам Signal без білого списку |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID (спільний з навичкою telephony) |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token (спільний з навичкою telephony; також використовується для перевірки підпису вебхука) |
| `TWILIO_PHONE_NUMBER` | Номер телефону Twilio у форматі E.164 (спільний з навичкою telephony) |
| `SMS_WEBHOOK_URL` | Публічний URL для перевірки підпису Twilio — має збігатися з URL вебхука в консолі Twilio (обов’язково) |
| `SMS_WEBHOOK_PORT` | Порт прослуховування вебхука для вхідних SMS (за замовчуванням: `8080`) |
| `SMS_WEBHOOK_HOST` | Адреса прив’язки вебхука (за замовчуванням: `0.0.0.0`) |
| `SMS_INSECURE_NO_SIGNATURE` | Встанови `true`, щоб вимкнути перевірку підпису Twilio (лише локальна розробка — не для продакшн) |
| `SMS_ALLOWED_USERS` | Номери телефонів у форматі E.164, розділені комами, яким дозволено спілкуватися |
| `SMS_ALLOW_ALL_USERS` | Дозволити всім відправникам SMS без білого списку |
| `SMS_HOME_CHANNEL` | Номер телефону для доставки cron‑завдань/сповіщень |
| `SMS_HOME_CHANNEL_NAME` | Відображуване ім’я домашнього каналу SMS |
| `EMAIL_ADDRESS` | Email‑адреса для адаптера шлюзу Email |
| `EMAIL_PASSWORD` | Пароль або пароль додатку для облікового запису електронної пошти |
| `EMAIL_IMAP_HOST` | Хост IMAP для адаптера електронної пошти |
| `EMAIL_IMAP_PORT` | Порт IMAP |
| `EMAIL_SMTP_HOST` | Хост SMTP для адаптера електронної пошти |
| `EMAIL_SMTP_PORT` | Порт SMTP |
| `EMAIL_ALLOWED_USERS` | Email‑адреси, розділені комами, яким дозволено надсилати повідомлення боту |
| `EMAIL_HOME_ADDRESS` | Типовий отримувач для проактивної доставки електронної пошти |
| `EMAIL_HOME_ADDRESS_NAME` | Відображуване ім’я цільового отримувача електронної пошти |
| `EMAIL_POLL_INTERVAL` | Інтервал опитування електронної пошти в секундах |
| `EMAIL_ALLOW_ALL_USERS` | Дозволити всім вхідним відправникам електронної пошти |
| `DINGTALK_CLIENT_ID` | AppKey бота DingTalk з порталу розробника ([open.dingtalk.com](https://open.dingtalk.com)) |
| `DINGTALK_CLIENT_SECRET` | AppSecret бота DingTalk з порталу розробника |
| `DINGTALK_ALLOWED_USERS` | Ідентифікатори користувачів DingTalk, розділені комами, яким дозволено надсилати повідомлення боту |
| `FEISHU_APP_ID` | App ID бота Feishu/Lark з [open.feishu.cn](https://open.feishu.cn/) |
| `FEISHU_APP_SECRET` | App Secret бота Feishu/Lark |
| `FEISHU_DOMAIN` | `feishu` (Китай) або `lark` (міжнародний). За замовчуванням: `feishu` |
| `FEISHU_CONNECTION_MODE` | `websocket` (рекомендовано) або `webhook`. За замовчуванням: `websocket` |
| `FEISHU_ENCRYPT_KEY` | Додатковий ключ шифрування для режиму webhook |
| `FEISHU_VERIFICATION_TOKEN` | Додатковий токен верифікації для режиму webhook |
| `FEISHU_ALLOWED_USERS` | Ідентифікатори користувачів Feishu, розділені комами, яким дозволено надсилати повідомлення боту |
| `FEISHU_ALLOW_BOTS` | `none` (за замовчуванням) / `mentions` / `all` — приймати вхідні повідомлення від інших ботів. Див. [bot-to-bot messaging](../user-guide/messaging/feishu.md#bot-to-bot-messaging) |
| `FEISHU_REQUIRE_MENTION` | `true` (за замовчуванням) / `false` — чи повинні групові повідомлення містити згадку @бота. Перевизначається per‑chat через `group_rules.<chat_id>.require_mention`. |
| `FEISHU_HOME_CHANNEL` | ID чату Feishu для доставки cron‑завдань та сповіщень |
| `WECOM_BOT_ID` | ID AI‑бота WeCom з консолі адміністратора |
| `WECOM_SECRET` | Секрет AI‑бота WeCom |
| `WECOM_WEBSOCKET_URL` | Користувацький URL WebSocket (за замовчуванням: `wss://openws.work.weixin.qq.com`) |
| `WECOM_ALLOWED_USERS` | Ідентифікатори користувачів WeCom, розділені комами, яким дозволено надсилати повідомлення боту |
| `WECOM_HOME_CHANNEL` | ID чату WeCom для доставки cron‑завдань та сповіщень |
| `WECOM_CALLBACK_CORP_ID` | Corp ID підприємства WeCom для самостійно створеного додатку |
| `WECOM_CALLBACK_CORP_SECRET` | Corp secret для самостійно створеного додатку |
| `WECOM_CALLBACK_AGENT_ID` | Agent ID самостійно створеного додатку |
| `WECOM_CALLBACK_TOKEN` | Токен верифікації колбеку |
| `WECOM_CALLBACK_ENCODING_AES_KEY` | AES‑ключ для шифрування колбеку |
| `WECOM_CALLBACK_HOST` | Адреса прив’язки сервера колбеку (за замовчуванням: `0.0.0.0`) |
| `WECOM_CALLBACK_PORT` | Порт сервера колбеку (за замовчуванням: `8645`) |
| `WECOM_CALLBACK_ALLOWED_USERS` | Ідентифікатори користувачів, розділені комами, у білому списку |
| `WECOM_CALLBACK_ALLOW_ALL_USERS` | Встанови `true`, щоб дозволити всім користувачам без білого списку |
| `WEIXIN_ACCOUNT_ID` | Ідентифікатор облікового запису Weixin, отриманий через QR‑логін через iLink Bot API |
| `WEIXIN_TOKEN` | Токен автентифікації Weixin, отриманий через QR‑логін через iLink Bot API |
| `WEIXIN_BASE_URL` | Перевизначити базовий URL iLink Bot API Weixin (за замовчуванням: `https://ilinkai.weixin.qq.com`) |
| `WEIXIN_CDN_BASE_URL` | Перевизначити базовий CDN‑URL Weixin для медіа (за замовчуванням: `https://novac2c.cdn.weixin.qq.com/c2c`) |
| `WEIXIN_DM_POLICY` | Політика прямих повідомлень: `open`, `allowlist`, `pairing`, `disabled` (за замовчуванням: `open`) |
| `WEIXIN_GROUP_POLICY` | Політика групових повідомлень: `open`, `allowlist`, `disabled` (за замовчуванням: `disabled`) |
| `WEIXIN_ALLOWED_USERS` | Ідентифікатори користувачів Weixin, розділені комами, яким дозволено надсилати DM боту |
| `WEIXIN_GROUP_ALLOWED_USERS` | Ідентифікатори групових чатів Weixin, розділені комами (не ідентифікатори учасників). Назва змінної залишилася з минулого — очікує саме групові ID. Діє лише коли iLink фактично доставляє події груп; ідентифікатори iLink‑бота, що входять через QR‑логін (`...@im.bot`), зазвичай не отримують звичайні повідомлення груп WeChat. |
| `WEIXIN_HOME_CHANNEL` | ID чату Weixin для доставки cron‑завдань та сповіщень |
| `WEIXIN_HOME_CHANNEL_NAME` | Відображуване ім’я домашнього каналу Weixin |
| `WEIXIN_ALLOW_ALL_USERS` | Дозволити всім користувачам Weixin без білого списку (`true`/`false`) |
| `BLUEBUBBLES_SERVER_URL` | URL сервера BlueBubbles (наприклад) |
| `BLUEBUBBLES_PASSWORD` | Пароль сервера BlueBubbles |
| `BLUEBUBBLES_WEBHOOK_HOST` | Адреса прив’язки прослуховувача Webhook (за замовчуванням: `127.0.0.1`) |
| `BLUEBUBBLES_WEBHOOK_PORT` | Порт прослуховувача Webhook (за замовчуванням: `8645`) |
| `BLUEBUBBLES_HOME_CHANNEL` | Телефон/електронна пошта для доставки cron/повідомлень |
| `BLUEBUBBLES_ALLOWED_USERS` | Список дозволених користувачів, розділений комами |
| `BLUEBUBBLES_ALLOW_ALL_USERS` | Дозволити всіх користувачів (`true`/`false`) |
| `QQ_APP_ID` | QQ Bot App ID з [q.qq.com](https://q.qq.com) |
| `QQ_CLIENT_SECRET` | QQ Bot App Secret з [q.qq.com](https://q.qq.com) |
| `QQ_STT_API_KEY` | API‑ключ для зовнішнього постачальника STT‑запасний (варіант) (необов’язково, використовується, коли вбудований ASR QQ не повертає текст) |
| `QQ_STT_BASE_URL` | Базовий URL зовнішнього постачальника STT (необов’язково) |
| `QQ_STT_MODEL` | Назва моделі зовнішнього постачальника STT (необов’язково) |
| `QQ_ALLOWED_USERS` | Список відкритих ID користувачів QQ, розділений комами, яким дозволено надсилати повідомлення боту |
| `QQ_GROUP_ALLOWED_USERS` | Список ID груп QQ, розділений комами, для доступу до групових @‑повідомлень |
| `QQ_ALLOW_ALL_USERS` | Дозволити всіх користувачів (`true`/`false`, переважає `QQ_ALLOWED_USERS`) |
| `QQBOT_HOME_CHANNEL` | Відкритий ID користувача/групи QQ для доставки cron та сповіщень |
| `QQBOT_HOME_CHANNEL_NAME` | Відображувана назва домашнього каналу QQ |
| `QQ_PORTAL_HOST` | Перевизначити хост порталу QQ (встанови `sandbox.q.qq.com` для маршрутизації через шлюз пісочниці; за замовчуванням: `q.qq.com`). |
| `MATTERMOST_URL` | URL сервера Mattermost (наприклад `https://mm.example.com`) |
| `MATTERMOST_TOKEN` | Токен бота або персональний токен доступу для Mattermost |
| `MATTERMOST_ALLOWED_USERS` | Список ID користувачів Mattermost, розділений комами, яким дозволено надсилати повідомлення боту |
| `MATTERMOST_HOME_CHANNEL` | ID каналу для проактивної доставки повідомлень (cron, сповіщення) |
| `MATTERMOST_REQUIRE_MENTION` | Вимагати `@mention` у каналах (за замовчуванням: `true`). Встанови `false`, щоб відповідати на всі повідомлення. |
| `MATTERMOST_FREE_RESPONSE_CHANNELS` | Список ID каналів, розділений комами, у яких бот відповідає без `@mention` |
| `MATTERMOST_REPLY_MODE` | Стиль відповіді: `thread` (вкладені відповіді) або `off` (плоскі повідомлення, за замовчуванням) |
| `MATRIX_HOMESERVER` | URL домашнього сервера Matrix (наприклад `https://matrix.org`) |
| `MATRIX_ACCESS_TOKEN` | Токен доступу Matrix для автентифікації бота |
| `MATRIX_USER_ID` | ID користувача Matrix (наприклад `@hermes:matrix.org`) — потрібен для входу за паролем, необов’язковий при використанні токену доступу |
| `MATRIX_PASSWORD` | Пароль Matrix (альтернатива токену доступу) |
| `MATRIX_ALLOWED_USERS` | Список ID користувачів Matrix, розділений комами, яким дозволено надсилати повідомлення боту (наприклад `@alice:matrix.org`) |
| `MATRIX_HOME_ROOM` | ID кімнати для проактивної доставки повідомлень (наприклад `!abc123:matrix.org`) |
| `MATRIX_ENCRYPTION` | Увімкнути наскрізне шифрування (`true`/`false`, за замовчуванням: `false`) |
| `MATRIX_DEVICE_ID` | Стабільний ID пристрою Matrix для збереження E2EE між перезапусками (наприклад `HERMES_BOT`). Без цього ключі E2EE оновлюються при кожному старті, і розшифровка історичних кімнат перестає працювати. |
| `MATRIX_REACTIONS` | Увімкнути обробку реакцій‑емодзі у вхідних повідомленнях (за замовчуванням: `true`). Встанови `false`, щоб вимкнути. |
| `MATRIX_REQUIRE_MENTION` | Вимагати `@mention` у кімнатах (за замовчуванням: `true`). Встанови `false`, щоб відповідати на всі повідомлення. |
| `MATRIX_FREE_RESPONSE_ROOMS` | Список ID кімнат, розділений комами, у яких бот відповідає без `@mention` |
| `MATRIX_AUTO_THREAD` | Автоматично створювати теми для повідомлень у кімнатах (за замовчуванням: `true`) |
| `MATRIX_DM_MENTION_THREADS` | Створювати тему, коли бот `@mentioned` у приватному чаті (за замовчуванням: `false`) |
| `MATRIX_RECOVERY_KEY` | Ключ відновлення для крос‑підпису після ротації ключа пристрою. Рекомендовано для налаштувань E2EE з увімкненим крос‑підписом. |
| `HASS_TOKEN` | Тривалий токен доступу Home Assistant (вмикає платформу HA + інструменти) |
| `HASS_URL` | URL Home Assistant (за замовчуванням: `http://homeassistant.local:8123`) |
| `WEBHOOK_ENABLED` | Увімкнути адаптер платформи webhook (`true`/`false`) |
| `WEBHOOK_PORT` | Порт HTTP‑сервера для отримання webhook‑ів (за замовчуванням: `8644`) |
| `WEBHOOK_SECRET` | Глобальний HMAC‑секрет для валідації підпису webhook (використовується як запасний, коли маршрути не вказують власний) |
| `API_SERVER_ENABLED` | Увімкнути сервер API, сумісний з OpenAI (`true`/`false`). Працює разом з іншими платформами. |
| `API_SERVER_KEY` | Токен Bearer для автентифікації сервера API. Обов’язковий, коли сервер API увімкнено. |
| `API_SERVER_CORS_ORIGINS` | Список походжень браузерів, розділений комами, яким дозволено викликати сервер API безпосередньо (наприклад `http://localhost:3000,http://127.0.0.1:3000`). За замовчуванням: вимкнено. |
| `API_SERVER_PORT` | Порт сервера API (за замовчуванням: `8642`) |
| `API_SERVER_HOST` | Адреса/хост прив’язки сервера API (за замовчуванням: `127.0.0.1`). `API_SERVER_KEY` все ще потрібен на loopback; використай вузький allowlist `API_SERVER_CORS_ORIGINS` для доступу браузера. |
| `API_SERVER_MODEL_NAME` | Назва моделі, оголошена на `/v1/models`. За замовчуванням — назва профілю (або `hermes-agent` для профілю за замовчуванням). Корисно для багатокористувацьких налаштувань, коли фронтенди типу Open WebUI потребують різних назв моделей для кожного з’єднання. |
| `GATEWAY_PROXY_URL` | URL віддаленого сервера Hermes API для переспрямування повідомлень ([режим проксі](/user-guide/messaging/matrix#proxy-mode-e2ee-on-macos)). При встановленні шлюз обробляє лише I/O платформи — вся робота агента делегується віддаленому серверу. Також можна налаштувати через `gateway.proxy_url` у `config.yaml`. |
| `GATEWAY_PROXY_KEY` | Токен Bearer для автентифікації з віддаленим сервером API в режимі проксі. Має збігатися з `API_SERVER_KEY` на віддаленому хості. |
| `MESSAGING_CWD` | Робочий каталог для термінальних команд у режимі обміну повідомленнями (за замовчуванням: `~`) |
| `GATEWAY_ALLOWED_USERS` | Список ID користувачів, розділений комами, дозволений на всіх платформах |
| `GATEWAY_ALLOW_ALL_USERS` | Дозволити всіх користувачів без списків дозволених (`true`/`false`, за замовчуванням: `false`) |
### Microsoft Graph (Teams Meetings)

App‑only credentials for the Microsoft Graph REST client used by the upcoming Teams meeting summary pipeline. See [Register a Microsoft Graph application](/guides/microsoft-graph-app-registration) for the Azure portal walkthrough and the exact API permissions required.

| Variable | Description |
|----------|-------------|
| `MSGRAPH_TENANT_ID` | Azure AD tenant ID (directory GUID) for the Graph app registration. |
| `MSGRAPH_CLIENT_ID` | Application (client) ID of the Azure app registration. |
| `MSGRAPH_CLIENT_SECRET` | Client secret value for the app registration. Store in `~/.hermes/.env` with `chmod 600`; rotate periodically via the Azure portal. |
| `MSGRAPH_SCOPE` | OAuth2 scope for the client‑credentials token request (default: `https://graph.microsoft.com/.default`). |
| `MSGRAPH_AUTHORITY_URL` | Microsoft identity platform authority (default: `https://login.microsoftonline.com`). Override only for national/sovereign clouds (e.g. `https://login.microsoftonline.us` for GCC High). |
### Microsoft Graph Webhook Listener

Вхідний слухач сповіщень про зміни для подій Graph (зустрічі Teams, календар, чат тощо). Дивись [Microsoft Graph Webhook Listener](/user-guide/messaging/msgraph-webhook) для налаштування та підвищення безпеки.

| Variable | Description |
|----------|-------------|
| `MSGRAPH_WEBHOOK_ENABLED` | Увімкнути шлюз `msgraph_webhook` (`true`/`1`/`yes`). |
| `MSGRAPH_WEBHOOK_PORT` | Порт, до якого прив’язується слухач (за замовчуванням: `8646`). |
| `MSGRAPH_WEBHOOK_CLIENT_STATE` | Спільний секрет, який Graph включає у кожне сповіщення; порівнюється за допомогою `hmac.compare_digest`. Згенеруй за допомогою `openssl rand -hex 32`. |
| `MSGRAPH_WEBHOOK_ACCEPTED_RESOURCES` | Кома‑розділений білий список шляхів/шаблонів ресурсів Graph (наприклад `communications/onlineMeetings,chats/*/messages`). Закінчуючий `*` означає префіксне співпадіння. Порожнє = приймати всі. |
| `MSGRAPH_WEBHOOK_ALLOWED_SOURCE_CIDRS` | Кома‑розділений білий список CIDR‑діапазонів, яким дозволено надсилати POST‑запити до слухача (наприклад `52.96.0.0/14,52.104.0.0/14`). Порожнє = дозволити всі (за замовчуванням). У продакшн‑середовищі обмежуйся опублікованими діапазонами egress Microsoft Graph. |
### Доставка підсумків зустрічі Teams

Використовується лише коли ввімкнено плагін [`teams_pipeline` plugin](/user-guide/messaging/msgraph-webhook). Налаштування також можна задати в `platforms.teams.extra` у `config.yaml` — змінні оточення мають пріоритет, якщо встановлені одночасно. Дивись [Microsoft Teams → Delivery of Meeting Summary](/user-guide/messaging/teams#meeting-summary-delivery-teams-meeting-pipeline).

| Variable | Description |
|----------|-------------|
| `TEAMS_DELIVERY_MODE` | `graph` або `incoming_webhook`. |
| `TEAMS_INCOMING_WEBHOOK_URL` | URL вебхука, згенерований Teams; обов’язковий, коли `TEAMS_DELIVERY_MODE=incoming_webhook`. |
| `TEAMS_GRAPH_ACCESS_TOKEN` | Попередньо отриманий делегований токен доступу для доставки через Graph. Рідко потрібен — модуль переходить до облікових даних програми `MSGRAPH_*`, якщо не встановлено. |
| `TEAMS_TEAM_ID` | Ідентифікатор цільової команди для доставки в канал (`graph` режим). |
| `TEAMS_CHANNEL_ID` | Ідентифікатор цільового каналу (пов’язаний з `TEAMS_TEAM_ID`). |
| `TEAMS_CHAT_ID` | Ідентифікатор цільового 1:1 або групового чату (альтернатива команді + каналу для `graph` режиму). |
### LINE Messaging API

Використовується вбудованим плагіном платформи LINE (`plugins/platforms/line/`). Дивись [Messaging Gateway → LINE](/user-guide/messaging/line) для повної налаштування.

| Variable | Description |
|----------|-------------|
| `LINE_CHANNEL_ACCESS_TOKEN` | Токен довготривалого доступу каналу з консолі LINE Developers (вкладка Messaging API). Обов’язково. |
| `LINE_CHANNEL_SECRET` | Секрет каналу (вкладка Basic settings); використовується для перевірки підпису вебхука HMAC‑SHA256. Обов’язково. |
| `LINE_HOST` | Хост прив’язки вебхука (за замовчуванням: `0.0.0.0`). |
| `LINE_PORT` | Порт прив’язки вебхука (за замовчуванням: `8646`). |
| `LINE_PUBLIC_URL` | Публічний HTTPS‑базовий URL (наприклад `https://my-tunnel.example.com`). Потрібно для надсилання зображень/аудіо/відео — LINE приймає лише HTTPS‑доступні URL. |
| `LINE_ALLOWED_USERS` | Список ID користувачів, розділених комами, яким дозволено надсилати повідомлення боту (`U`‑префікс). |
| `LINE_ALLOWED_GROUPS` | Список ID груп, розділених комами, у яких бот відповідатиме (`C`‑префікс). |
| `LINE_ALLOWED_ROOMS` | Список ID кімнат, розділених комами, у яких бот відповідатиме (`R`‑префікс). |
| `LINE_ALLOW_ALL_USERS` | Тільки для розробки — запасний (варіант) шлях, який приймає будь‑яке джерело. За замовчуванням: `false`. |
| `LINE_HOME_CHANNEL` | Цільова точка доставки за замовчуванням для cron‑завдань з `deliver: line`. |
| `LINE_SLOW_RESPONSE_THRESHOLD` | Кількість секунд до спрацювання постбеку шаблонних кнопок повільного LLM (за замовчуванням: `45`). Встанови `0`, щоб вимкнути і завжди використовувати Push‑fallback. |
| `LINE_PENDING_TEXT` | Текст бульбашки, що показується поруч із кнопкою постбеку. |
| `LINE_BUTTON_LABEL` | Текст мітки кнопки постбеку (за замовчуванням: `Get answer`). |
| `LINE_DELIVERED_TEXT` | Відповідь, коли вже доставлений постбек натискається знову (за замовчуванням: `Already replied ✅`). |
| `LINE_INTERRUPTED_TEXT` | Відповідь, коли натискається кнопка постбеку, залишена після `/stop` (за замовчуванням: `Run was interrupted before completion.`). |
### ntfy (push‑повідомлення)

[ntfy](https://ntfy.sh/) — це легковаговий HTTP‑базований сервіс push‑повідомлень. Підпишись на тему за допомогою [мобільного додатку ntfy](https://ntfy.sh/docs/subscribe/phone/), публікуй у цю тему, щоб спілкуватися з агентом.

| Variable | Description |
|----------|-------------|
| `NTFY_TOPIC` | Тема для підписки (вхідні повідомлення). Обов’язково. |
| `NTFY_SERVER_URL` | URL сервера (за замовчуванням: `https://ntfy.sh`). Вкажи самостійно розгорнутий ntfy для підвищення конфіденційності. |
| `NTFY_TOKEN` | Необов’язковий токен автентифікації. Bearer‑токен (наприклад `tk_xyz`) або `user:pass` для Basic auth. |
| `NTFY_PUBLISH_TOPIC` | Тема для вихідних відповідей (за замовчуванням `NTFY_TOPIC`). |
| `NTFY_MARKDOWN` | Встанови `true`, щоб надсилати відповіді з заголовком `X-Markdown: true`. За замовчуванням: `false`. |
| `NTFY_ALLOWED_USERS` | Білий список (розглядається як ідентифікатори користувачів; у ntfy це назви тем). Зазвичай встановлюється в те саме значення, що й `NTFY_TOPIC`. |
| `NTFY_ALLOW_ALL_USERS` | Тільки для розробки — «escape hatch», безпечний лише для тем з контрольованим доступом. За замовчуванням: `false`. |
| `NTFY_HOME_CHANNEL` | Цільова точка доставки за замовчуванням для cron‑завдань з `deliver: ntfy`. |
| `NTFY_HOME_CHANNEL_NAME` | Людська назва домашнього каналу (за замовчуванням — назва теми). |

Дивись [посібник з обміну повідомленнями ntfy](/user-guide/messaging/ntfy) — особливо розділ **модель ідентифікації** — перед розгортанням з недовіреними темами.
### Advanced Messaging Tuning

Advanced per‑platform knobs for throttling the outbound message batcher. Most users never need to touch these; defaults are set to respect each platform's rate limits without feeling sluggish.

| Variable | Description |
|----------|-------------|
| `HERMES_TELEGRAM_TEXT_BATCH_DELAY_SECONDS` | Вікно‑запасу перед вивантаженням черги текстових фрагментів Telegram (за замовчуванням: `0.6`). |
| `HERMES_TELEGRAM_TEXT_BATCH_SPLIT_DELAY_SECONDS` | Затримка між розділеними фрагментами, коли одне повідомлення Telegram перевищує ліміт довжини (за замовчуванням: `2.0`). |
| `HERMES_TELEGRAM_MEDIA_BATCH_DELAY_SECONDS` | Вікно‑запасу перед вивантаженням черги медіа‑фрагментів Telegram (за замовчуванням: `0.6`). |
| `HERMES_TELEGRAM_FOLLOWUP_GRACE_SECONDS` | Затримка перед надсиланням додаткового повідомлення після завершення роботи агента, щоб уникнути гонки останнього фрагмента потоку. |
| `HERMES_TELEGRAM_HTTP_CONNECT_TIMEOUT` / `_READ_TIMEOUT` / `_WRITE_TIMEOUT` / `_POOL_TIMEOUT` | Перевизначення HTTP‑таймаутів `python‑telegram‑bot` (секунди). |
| `HERMES_TELEGRAM_HTTP_POOL_SIZE` | Максимальна кількість одночасних HTTP‑з’єднань до API Telegram. |
| `HERMES_TELEGRAM_DISABLE_FALLBACK_IPS` | Вимкнути жорстко закодовані запасні (варіант) IP‑адреси Cloudflare, які використовуються при збоях DNS (`true`/`false`). |
| `HERMES_DISCORD_TEXT_BATCH_DELAY_SECONDS` | Вікно‑запасу перед вивантаженням черги текстових фрагментів Discord (за замовчуванням: `0.6`). |
| `HERMES_DISCORD_TEXT_BATCH_SPLIT_DELAY_SECONDS` | Затримка між розділеними фрагментами, коли повідомлення Discord перевищує ліміт довжини (за замовчуванням: `2.0`). |
| `HERMES_MATRIX_TEXT_BATCH_DELAY_SECONDS` / `_SPLIT_DELAY_SECONDS` | Еквіваленти Telegram‑параметрів для Matrix. |
| `HERMES_FEISHU_TEXT_BATCH_DELAY_SECONDS` / `_SPLIT_DELAY_SECONDS` / `_MAX_CHARS` / `_MAX_MESSAGES` | Налаштування batch‑процесора Feishu — затримка, затримка розділення, макс. символів у повідомленні, макс. повідомлень у batch‑і. |
| `HERMES_FEISHU_MEDIA_BATCH_DELAY_SECONDS` | Затримка вивантаження медіа у Feishu. |
| `HERMES_FEISHU_DEDUP_CACHE_SIZE` | Розмір кешу дедуплікації веб‑хуків Feishu (за замовчуванням: `1024`). |
| `HERMES_WECOM_TEXT_BATCH_DELAY_SECONDS` / `_SPLIT_DELAY_SECONDS` | Налаштування batch‑процесора WeCom. |
| `HERMES_VISION_DOWNLOAD_TIMEOUT` | Таймаут (секунди) завантаження зображення перед передачею його моделям зору (за замовчуванням: `30`). |
| `HERMES_RESTART_DRAIN_TIMEOUT` | Gateway: кількість секунд очікування завершення активних запусків при `/restart` перед примусовим перезапуском (за замовчуванням: `900`). |
| `HERMES_GATEWAY_PLATFORM_CONNECT_TIMEOUT` | Таймаут підключення для кожної платформи під час старту шлюзу (секунди). |
| `HERMES_GATEWAY_BUSY_INPUT_MODE` | Типова поведінка шлюзу при зайнятості вводу: `queue`, `steer` або `interrupt`. Можна перевизначити в чаті за допомогою `/busy`. |
| `HERMES_GATEWAY_BUSY_ACK_ENABLED` | Чи надсилає шлюз повідомлення‑підтвердження (⚡/⏳/⏩), коли користувач надсилає ввід, поки агент зайнятий (за замовчуванням: `true`). Встанови `false`, щоб повністю придушити ці повідомлення — ввід все одно буде поставлений у чергу/перенаправлений/перервано, лише відповідь у чаті буде вимкнена. Наслідується від `display.busy_ack_enabled` у `config.yaml`. |
| `HERMES_GATEWAY_NO_SUPERVISE` | У Docker‑образі s6‑overlay — відмовитися від автосупервізії при запуску `hermes gateway run` і використовувати семантику переднього плану без s6 (без автоперезапуску, шлюз — головний процес контейнера). Правдиві значення: `1`, `true`, `yes`. Еквівалент прапорцю CLI `--no-supervise`. Не діє поза s6‑образом. |
| `HERMES_FILE_MUTATION_VERIFIER` | Увімкнути футер‑верифікатор зміни файлів за кожен хід (за замовчуванням: `true`). При увімкненні Hermes додає advisory‑список будь‑яких викликів `write_file` / `patch`, які не вдалися під час ходу і не були замінені успішним записом. Встанови `0`, `false`, `no` або `off`, щоб придушити. Відображає `display.file_mutation_verifier` у `config.yaml`; змінна середовища має пріоритет. |
| `HERMES_CRON_TIMEOUT` | Таймаут бездіяльності для запусків агента cron (секунди, за замовчуванням: `600`). Агент може працювати без обмежень, доки активно викликає інструменти або отримує токени потоку — це спрацьовує лише під час простою. Встанови `0` для безлімітного часу. |
| `HERMES_CRON_SCRIPT_TIMEOUT` | Таймаут для скриптів, що виконуються перед запуском cron‑завдань (секунди, за замовчуванням: `120`). Перевизначається для скриптів, яким потрібен довший час виконання (наприклад, випадкові затримки для протидії бот‑детекції). Також налаштовується через `cron.script_timeout_seconds` у `config.yaml`. |
| `HERMES_CRON_MAX_PARALLEL` | Максимальна кількість одночасних запусків cron‑завдань за один тик (за замовчуванням: `4`). |
## Поведінка агента

| Змінна | Опис |
|----------|-------------|
| `HERMES_MAX_ITERATIONS` | Максимальна кількість ітерацій виклику інструментів за розмову (за замовчуванням: 90) |
| `HERMES_INFERENCE_MODEL` | Перевизначає назву моделі на рівні процесу (має пріоритет над `config.yaml` для сесії). Також можна задати через прапорець `-m`/`--model`. |
| `HERMES_YOLO_MODE` | Встанови `1`, щоб обійти запити підтвердження небезпечних команд. Еквівалент `--yolo`. |
| `HERMES_ACCEPT_HOOKS` | Автоматично схвалює будь‑які невідомі shell‑хуки, оголошені в `config.yaml`, без запиту в TTY. Еквівалент `--accept-hooks` або `hooks_auto_accept: true`. |
| `HERMES_IGNORE_USER_CONFIG` | Пропускає `~/.hermes/config.yaml` і використовує вбудовані значення за замовчуванням (облікові дані в `.env` все ще завантажуються). Еквівалент `--ignore-user-config`. |
| `HERMES_IGNORE_RULES` | Пропускає автоматичне підключення `AGENTS.md`, `SOUL.md`, `.cursorrules`, пам'ять та попередньо завантажені інструменти. Еквівалент `--ignore-rules`. |
| `HERMES_MD_NAMES` | Список імен файлів правил, розділених комами, для автоматичного підключення (за замовчуванням: `AGENTS.md,CLAUDE.md,.cursorrules,SOUL.md`). |
| `HERMES_TOOL_PROGRESS` | Застаріла змінна сумісності для відображення прогресу інструменту. Використовуй `display.tool_progress` у `config.yaml`. |
| `HERMES_TOOL_PROGRESS_MODE` | Застаріла змінна сумісності для режиму прогресу інструменту. Використовуй `display.tool_progress` у `config.yaml`. |
| `HERMES_HUMAN_DELAY_MODE` | Регулювання темпу відповіді: `off`/`natural`/`custom` |
| `HERMES_HUMAN_DELAY_MIN_MS` | Мінімальне значення діапазону кастомної затримки (мс) |
| `HERMES_HUMAN_DELAY_MAX_MS` | Максимальне значення діапазону кастомної затримки (мс) |
| `HERMES_QUIET` | Приховує неважливий вивід (`true`/`false`) |
| `CODEX_HOME` | Коли увімкнено [runtime сервера Codex app‑server](../user-guide/features/codex-app-server-runtime), перевизначає каталог, з якого Codex CLI читає конфігурацію та автентифікацію (за замовчуванням: `~/.codex`). Міграція Hermes записує керований блок у `<CODEX_HOME>/config.toml`. |
| `HERMES_KANBAN_TASK` | Встановлюється диспетчером kanban під час створення воркера (UUID завдання). Воркери та підпроцес `hermes-tools` MCP успадковують його, щоб інструменти kanban правильно працювали. Не встановлюй вручну. |
| `HERMES_API_TIMEOUT` | Тайм‑аут виклику LLM API у секундах (за замовчуванням: `1800`) |
| `HERMES_API_CALL_STALE_TIMEOUT` | Тайм‑аут «застарілого» не‑стрімінгового виклику у секундах (за замовчуванням: `300`). Автоматично вимикається для локальних провайдерів, якщо не задано. Також налаштовується через `providers.<id>.stale_timeout_seconds` або `providers.<id>.models.<model>.stale_timeout_seconds` у `config.yaml`. |
| `HERMES_STREAM_READ_TIMEOUT` | Тайм‑аут читання сокету потоку у секундах (за замовчуванням: `120`). Автоматично збільшується до `HERMES_API_TIMEOUT` для локальних провайдерів. Збільшуй, якщо локальні LLM тайм‑аутяться під час довгого генерування коду. |
| `HERMES_STREAM_STALE_TIMEOUT` | Тайм‑аут виявлення «застарілого» потоку у секундах (за замовчуванням: `180`). Автоматично вимикається для локальних провайдерів. При відсутності чанків протягом цього інтервалу з’єднання розривається. |
| `HERMES_STREAM_RETRIES` | Кількість спроб повторного підключення під час потоку при транзиторних мережевих помилках (за замовчуванням: `3`). |
| `HERMES_AGENT_TIMEOUT` | Тайм‑аут неактивності шлюзу для запущеного агента у секундах (за замовчуванням: `900`). Скидається після кожного виклику інструменту та кожного отриманого токену. Встанови `0`, щоб вимкнути. |
| `HERMES_AGENT_TIMEOUT_WARNING` | Шлюз: надсилає попереджувальне повідомлення після вказаної кількості секунд неактивності (за замовчуванням: 75 % від `HERMES_AGENT_TIMEOUT`). |
| `HERMES_AGENT_NOTIFY_INTERVAL` | Шлюз: інтервал у секундах між повідомленнями про прогрес під час довгих ходів агента. |
| `HERMES_CHECKPOINT_TIMEOUT` | Тайм‑аут створення контрольної точки у файловій системі у секундах (за замовчуванням: `30`). |
| `HERMES_EXEC_ASK` | Увімкнути запити підтвердження виконання в режимі шлюзу (`true`/`false`) |
| `HERMES_ENABLE_PROJECT_PLUGINS` | Дозволяє автоматичне виявлення плагінів репозиторію у `./.hermes/plugins/` як для завантажувача агента, так і для веб‑серверу дашборду. Приймає стандартний набір truthy‑значень: `1` / `true` / `yes` / `on` (без урахування регістру). Усі інші, включаючи `0`, `false`, `no`, `off` та порожній рядок, трактуються як **вимкнено** (за замовчуванням). Примітка: починаючи з GHSA-5qr3-c538-wm9j (#29156) веб‑сервер дашборду відмовляється автоматично імпортувати Python‑файл `api` плагіна проєкту, навіть якщо ця змінна ввімкнена — плагіни проєкту можуть розширювати UI через статичний JS/CSS, проте їх бекенд‑маршрути завантажуються лише після переміщення під `~/.hermes/plugins/`. |
| `HERMES_PLUGINS_DEBUG` | `1`/`true` — виводити докладні логи виявлення плагінів у stderr: скановані каталоги, розпарсені маніфести, причини пропуску та повні трасування помилок при парсингу або `register()`. Призначено авторам плагінів. |
| `HERMES_BACKGROUND_NOTIFICATIONS` | Режим сповіщень фонового процесу в шлюзі: `all` (за замовчуванням), `result`, `error`, `off` |
| `HERMES_EPHEMERAL_SYSTEM_PROMPT` | Ефемерна системна підказка, що інжектується під час API‑виклику (ніколи не зберігається у сесіях) |
| `HERMES_PREFILL_MESSAGES_FILE` | Шлях до JSON‑файлу з ефемерними попередньо заповненими повідомленнями, інжектованими під час API‑виклику. |
| `HERMES_ALLOW_PRIVATE_URLS` | `true`/`false` — дозволити інструментам отримувати URL‑и localhost/приватних мереж. За замовчуванням вимкнено в режимі шлюзу. |
| `HERMES_REDACT_SECRETS` | `true`/`false` — керує редагуванням секретів у виводі інструментів, логах та відповідях чату (за замовчуванням: `true`). |
| `HERMES_WRITE_SAFE_ROOT` | Необов’язковий префікс каталогу, який обмежує записи `write_file`/`patch`; шляхи поза ним вимагають підтвердження. |
| `HERMES_DISABLE_FILE_STATE_GUARD` | Встанови `1`, щоб вимкнути захист «файл змінено після читання» для `patch`/`write_file`. |
| `HERMES_CORE_TOOLS` | Список інструментів ядра, розділений комами, для перевизначення (просунутий; рідко потрібен). |
| `HERMES_BUNDLED_SKILLS` | Список вбудованих навичок, розділений комами, що завантажуються під час старту. |
| `HERMES_OPTIONAL_SKILLS` | Список назв необов’язкових навичок, які автоматично встановлюються при першому запуску, розділений комами. |
| `HERMES_DEBUG_INTERRUPT` | Встанови `1`, щоб записувати докладне трасування переривань/скасувань у `agent.log`. |
| `HERMES_DUMP_REQUESTS` | Записувати корисне навантаження API‑запитів у файли логів (`true`/`false`) |
| `HERMES_DUMP_REQUEST_STDOUT` | Записувати корисне навантаження API‑запитів у stdout замість файлів логів. |
| `HERMES_OAUTH_TRACE` | Встанови `1`, щоб логувати обмін OAuth‑токенами та спроби їх оновлення. Включає редаговану інформацію про час. |
| `HERMES_OAUTH_FILE` | Перевизначає шлях, що використовується для зберігання облікових даних OAuth (за замовчуванням: `~/.hermes/auth.json`). |
| `HERMES_AGENT_HELP_GUIDANCE` | Додає додатковий текст рекомендацій до системної підказки для кастомних розгортань. |
| `HERMES_AGENT_LOGO` | Перевизначає ASCII‑банер логотипу під час запуску CLI. |
| `DELEGATION_MAX_CONCURRENT_CHILDREN` | Максимальна кількість паралельних підагентів на пакет `delegate_task` (за замовчуванням: `3`, мінімум 1, без верхньої межі). Також налаштовується через `delegation.max_concurrent_children` у `config.yaml` — значення в конфігурації має пріоритет. |
## Interface

| Variable | Description |
|----------|-------------|
| `HERMES_TUI` | Запускає [TUI](../user-guide/tui.md) замість класичного CLI, якщо встановлено `1`. Еквівалентно передачі `--tui`. |
| `HERMES_TUI_DIR` | Шлях до попередньо зібраного каталогу `ui-tui/` (повинен містити `dist/entry.js` та заповнені `node_modules`). Використовується дистрибутивами та Nix, щоб пропустити перший запуск `npm install`. |
| `HERMES_TUI_RESUME` | Відновлює певну TUI‑сесію за ID під час запуску. Якщо встановлено, `hermes --tui` пропускає створення нової сесії і підхоплює вказану — корисно для повторного підключення після розриву з’єднання або аварії терміналу. |
| `HERMES_TUI_THEME` | Встановлює кольорову тему TUI: `light`, `dark` або довільний шестизначний hex‑колір фону (наприклад `ffffff` або `1a1a2e`). Якщо не встановлено, Hermes автоматично визначає тему за допомогою `COLORFGBG` та запитів до фону терміналу; ця змінна перевизначає визначення у терміналах (Ghostty, Warp, iTerm2 тощо), які не встановлюють `COLORFGBG`. |
| `HERMES_INFERENCE_MODEL` | Встановлює модель для `hermes -z` / `hermes chat` без зміни `config.yaml`. Працює разом із прапорцем `--provider`. Корисно для скриптових викликів (sweeper, CI, batch runners), які потребують перевизначення моделі за замовчуванням під час запуску. |
## Налаштування сесії

| Змінна | Опис |
|----------|-------------|
| `SESSION_IDLE_MINUTES` | Скидає сесії після N хвилин бездіяльності (за замовчуванням: 1440) |
| `SESSION_RESET_HOUR` | Щоденна година скидання у 24‑годинному форматі (за замовчуванням: 4 = 4 am) |
| `HERMES_SESSION_ID` | **Експортується автоматично у кожен підпроцес інструмента**, який запускає Hermes (`terminal`, `execute_code`, постійна оболонка, бекенди Docker/Singularity, делеговані запуски підагентів). Встановлюється агентом у поточний ідентифікатор сесії; скрипти користувача, викликані з інструментів, можуть читати його, щоб корелювати їхній вивід, телеметрію або побічні ефекти з вихідною сесією Hermes. **Не слід встановлювати це вручну** — перевизначення з батьківської оболонки діє лише поза запуском агента і перезаписується в момент, коли агент починає сесію. |
## Стиснення контексту (лише `config.yaml`)

Стиснення контексту налаштовується виключно через `config.yaml` — для нього не передбачено змінних середовища. Налаштування порогу розташовані у блоці `compression:`, а модель/провайдер підсумовування — у `auxiliary.compression:`.

```yaml
compression:
  enabled: true
  threshold: 0.50
  target_ratio: 0.20         # fraction of threshold to preserve as recent tail
  protect_last_n: 20         # minimum recent messages to keep uncompressed
```

:::info Legacy migration
Старі конфігурації з `compression.summary_model`, `compression.summary_provider` та `compression.summary_base_url` автоматично мігруються до `auxiliary.compression.*` під час першого завантаження.
:::
## Перевизначення допоміжних завдань

| Змінна | Опис |
|----------|-------------|
| `AUXILIARY_VISION_PROVIDER` | Перевизначити провайдера для завдань комп’ютерного зору |
| `AUXILIARY_VISION_MODEL` | Перевизначити модель для завдань комп’ютерного зору |
| `AUXILIARY_VISION_BASE_URL` | Прямий кінцевий пункт, сумісний з OpenAI, для завдань комп’ютерного зору |
| `AUXILIARY_VISION_API_KEY` | API‑ключ, пов’язаний з `AUXILIARY_VISION_BASE_URL` |
| `AUXILIARY_WEB_EXTRACT_PROVIDER` | Перевизначити провайдера для веб‑видобутку/резюмування |
| `AUXILIARY_WEB_EXTRACT_MODEL` | Перевизначити модель для веб‑видобутку/резюмування |
| `AUXILIARY_WEB_EXTRACT_BASE_URL` | Прямий кінцевий пункт, сумісний з OpenAI, для веб‑видобутку/резюмування |
| `AUXILIARY_WEB_EXTRACT_API_KEY` | API‑ключ, пов’язаний з `AUXILIARY_WEB_EXTRACT_BASE_URL` |

Для завдань із прямими кінцевими точками Hermes використовує налаштований API‑ключ завдання або `OPENAI_API_KEY`. Він не повторно використовує `OPENROUTER_API_KEY` для цих кастомних кінцевих точок.
## Постачальники запасних (варіантів) (лише config.yaml)

Основний ланцюжок запасних (варіантів) моделей налаштовується виключно через `config.yaml` — для нього немає змінних середовища. Додай список верхнього рівня `fallback_providers` з ключами `provider` і `model`, щоб увімкнути автоматичний запасний (варіант), коли твоя основна модель стикається з помилками.

```yaml
fallback_providers:
  - provider: openrouter
    model: anthropic/claude-sonnet-4
```

Старіша форма верхнього рівня `fallback_model` з одним постачальником все ще читається для зворотної сумісності, але нову конфігурацію слід використовувати `fallback_providers`.

Дивись [Fallback Providers](/user‑guide/features/fallback-providers) для повних деталей.
## Маршрутизація провайдерів (лише config.yaml)

Ці параметри розміщуються у `~/.hermes/config.yaml` у розділі `provider_routing`:

| Ключ | Опис |
|-----|------|
| `sort` | Сортування провайдерів: `"price"` (за замовчуванням), `"throughput"` або `"latency"` |
| `only` | Список slug‑ів провайдерів, які дозволені (наприклад, `["anthropic", "google"]`) |
| `ignore` | Список slug‑ів провайдерів, які слід пропустити |
| `order` | Список slug‑ів провайдерів, які слід спробувати у вказаному порядку |
| `require_parameters` | Використовувати лише провайдери, що підтримують усі параметри запиту (`true`/`false`) |
| `data_collection` | `"allow"` (за замовчуванням) або `"deny"` — для виключення провайдерів, що зберігають дані |

:::tip
Використовуй `hermes config set` для встановлення змінних середовища — команда автоматично зберігає їх у потрібний файл (`.env` для секретів, `config.yaml` для всього іншого).
:::