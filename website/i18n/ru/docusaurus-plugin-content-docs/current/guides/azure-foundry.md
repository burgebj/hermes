---
sidebar_position: 15
title: "Microsoft Foundry"
description: "Используй Hermes Agent с Microsoft Foundry — конечные точки в стиле OpenAI и Anthropic, автоопределение транспорта и развернутых моделей"
---

# Microsoft Foundry

Провайдер `azure-foundry` Hermes Agent поддерживает Microsoft Foundry (ранее Azure AI Foundry) и Azure OpenAI. Один ресурс Foundry может размещать модели с двумя разными форматами передачи:

- **OpenAI‑style** — `POST /v1/chat/completions` на эндпоинтах вида `https://<resource>.openai.azure.com/openai/v1`. Используется для GPT‑4.x, GPT‑5.x, Llama, Mistral и большинства моделей с открытыми весами.
- **Anthropic‑style** — `POST /v1/messages` на эндпоинтах вида `https://<resource>.services.ai.azure.com/anthropic`. Применяется, когда Microsoft Foundry обслуживает модели Claude через формат API сообщений Anthropic.

Мастер настройки проверяет ваш эндпоинт и автоматически определяет, какой транспорт используется, какие развертывания доступны и длину контекста каждой модели.
## Предварительные требования

- Ресурс Microsoft Foundry или Azure OpenAI с как минимум одним развертыванием
- URL‑конечная точка развертывания
- **Либо** API‑ключ (в Azure Portal в разделе «Keys and Endpoint»), **либо** роль **Azure AI User** RBAC на ресурсе Foundry, если планируешь использовать Microsoft Entra ID (рекомендованный Microsoft путь без ключа). В некоторых тенантах роль может отображаться как **Foundry User** в рамках переименования Microsoft.
## Быстрый старт

```bash
hermes model
# → Select "Azure Foundry"
# → Enter your endpoint URL
# → Choose Authentication:
#     1. API key
#     2. Microsoft Entra ID  (managed identity / workload identity / az login)
# → (Entra) Hermes probes DefaultAzureCredential; on success it never asks for a key
# → (API key) Enter your API key
# Hermes probes the endpoint and auto-detects transport + models
# → Pick a model from the list (or type a deployment name manually)
```

Мастер выполнит:

1. **Sniff the URL path** — URL, заканчивающиеся на `/anthropic`, распознаются как маршруты Microsoft Foundry Claude.
2. **Probe `GET <base>/models`** — если конечная точка возвращает список моделей в формате OpenAI, Hermes переключается на `chat_completions` и предварительно заполняет выборщик возвращёнными идентификаторами развертываний.
3. **Probe Anthropic Messages shape** — запасной (вариант) для конечных точек, которые не раскрывают `/models`, но принимают формат Anthropic Messages.
4. **Fall back to manual entry** — приватные/ограниченные конечные точки, отвергающие каждую проверку, всё равно работают; ты выбираешь режим API и вводишь имя развертывания вручную.

Длина контекста для выбранной модели определяется через стандартную цепочку метаданных Hermes (`models.dev`, метаданные провайдера и жёстко заданные запасные варианты семейств) и сохраняется в `config.yaml`, чтобы модель могла корректно определить размер собственного окна контекста.
## Microsoft Entra ID (keyless, RBAC) — recommended

Microsoft recommends [keyless authentication with Microsoft Entra ID](https://learn.microsoft.com/azure/ai-foundry/foundry-models/how-to/configure-entra-id) for production Foundry workloads. Hermes supports Entra ID for **both** API surfaces:

- **OpenAI-style** (`api_mode: chat_completions` / `codex_responses`) — GPT‑4/5, Llama, Mistral, DeepSeek, etc.
- **Anthropic-style** (`api_mode: anthropic_messages`) — Claude models on Microsoft Foundry.

Foundry's RBAC is per‑resource (`Azure AI User` grants both surfaces; some tenants may display `Foundry User`) and Microsoft documents the same inference scope (`https://ai.azure.com/.default`) for both. Under the hood:

- OpenAI‑style uses the OpenAI Python SDK's native callable `api_key=` contract — the SDK mints a fresh JWT per request automatically.
- Anthropic‑style uses an `httpx.Client` with a request event hook installed by `agent.azure_identity_adapter.build_bearer_http_client`, because the Anthropic SDK does not accept callable `auth_token` natively. The hook rewrites `Authorization: Bearer <fresh-jwt>` per outbound request. Same Microsoft RBAC, same Foundry scope — the SDK contract is the only difference.

### Почему использовать Entra ID?

- Нет долговременных API‑ключей, которые нужно вращать или отзывать.
- Доступ управляется RBAC — предоставляй или отзывай `Azure AI User` на ресурсе Foundry, без необходимости менять конфигурацию.
- Журналы доступа и аудита сегментируются по получателю, а не объединяются в один статический ключ.
- Одна точка аутентификации для Azure VM, AKS pod‑ов, App Service, Functions, Container Apps и Foundry Agent Service через **управляемую идентичность**.
- Потоки *workload identity* и *service principal* для CI/CD‑конвейеров.

### Одноразовая настройка (сторона Azure)

1. В Azure Portal открой свой ресурс Foundry → **Access control (IAM)** → **Add → Add role assignment**.
2. Выбери роль **Azure AI User** (или **Foundry User**, если в твоём тенанте роль переименована).
3. Назначь её:
   - **Твоей учётной записи** для локальной разработки с `az login`.
   - **Управляемой идентичности или workload identity** для вычислений в Azure (рекомендовано для продакшна).
   - **Идентичности агента Hosted Agent** сервиса Foundry Agent Service, когда Hermes работает внутри hosted‑агента.
   - **Сервис‑принципалу** для CI/CD‑конвейеров, если workload identity недоступна.
4. Подожди ~5 минут, пока роль распространится.

Эквивалент в Azure CLI:

```bash
az role assignment create \
  --assignee <principal-or-agent-identity-client-id> \
  --role "Azure AI User" \
  --scope <foundry-resource-id>
```

### Одноразовая настройка (сторона Hermes)

```bash
hermes model
# → Select "Azure Foundry"
# → Enter your endpoint URL
# → Authentication: 2 (Microsoft Entra ID)
# → (optional) user-assigned managed identity client ID
# → (optional) Azure tenant ID
# → Hermes probes DefaultAzureCredential() and reports which inner
#    credential succeeded (e.g. AzureCliCredential, ManagedIdentityCredential)
```

Мастер запускает ограниченный preflight‑пробный запрос (таймаут 10 s). При ошибке он предлагает «save anyway, validate later» — удобно, когда конфигурируешь машину, у которой ещё нет учётных данных, но они появятся во время выполнения (например, готовишь конфиг для развертывания с managed‑identity).

`azure-identity` устанавливается автоматически при первом использовании через lazy‑install путь Hermes. Чтобы предустановить:

```bash
pip install azure-identity
```

### Конфигурация записывается в `config.yaml`

```yaml
model:
  provider: azure-foundry
  base_url: https://my-resource.openai.azure.com/openai/v1
  api_mode: chat_completions
  auth_mode: entra_id
  default: gpt-4o
  context_length: 128000
  entra:
    scope: https://ai.azure.com/.default        # only when overriding the default
```

Hermes управляет лишь одной Entra‑специфичной настройкой в `config.yaml`:

- **`scope`** — OAuth‑ресурсный scope. По умолчанию используется документированный Microsoft inference scope (`https://ai.azure.com/.default`). Переопределяй только если твой ресурс был provisioned против нестандартного audience.

Всё остальное (tenant, secret сервис‑принципала, файл федеративного токена, authority суверенного облака, предпочтения брокера) читается `azure-identity` напрямую из стандартных переменных окружения `AZURE_*` — см. [credential resolution order](#credential-resolution-order) ниже. Задай их в `~/.hermes/.env` или в окружении развертывания точно так же, как описано в справке SDK Microsoft.

Никакие секреты не попадают в `~/.hermes/.env` в режиме Entra — `azure-identity` кэширует токены в процессе (и, где доступно, в системном keychain / `~/.IdentityService`).

### Порядок разрешения учётных данных

`azure-identity`'s `DefaultAzureCredential` проходит эту цепочку при каждом запросе токена, останавливаясь на первом креденшале, который вернёт токен:

1. **Environment credential** — `AZURE_TENANT_ID` + `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` (или `AZURE_CLIENT_CERTIFICATE_PATH` / `AZURE_FEDERATED_TOKEN_FILE`).
2. **Workload Identity** — `AZURE_FEDERATED_TOKEN_FILE` (AKS federated tokens / OIDC).
3. **Managed Identity** — IMDS endpoint (`169.254.169.254`) для виртуальных машин; `IDENTITY_ENDPOINT` для App Service / Functions / Container Apps. Hosted‑agents Foundry Agent Service используют идентичность самого агента.
4. **Visual Studio Code** — Azure account extension.
5. **Azure CLI** — сессия `az login`.
6. **Azure Developer CLI** — `azd auth login`.
7. **Azure PowerShell** — `Connect-AzAccount`.
8. **Broker** (Windows / WSL only) — Web Account Manager.

Interactive browser credential исключён по умолчанию для безнадзорных запусков Hermes; используй Azure CLI, Azure Developer CLI, управляемую идентичность, workload identity или сервис‑принципал.

### Паттерны развертывания

**Локальная разработка:**
```bash
az login
hermes model   # pick Azure Foundry → Entra ID
hermes         # uses your az login token
```

**Azure VM / Functions / App Service / Container Apps (system‑assigned managed identity):**
1. Включи system‑assigned identity на вычислительном ресурсе.
2. Предоставь этой идентичности `Azure AI User` (или `Foundry User`) на ресурсе Foundry.
3. Установи `model.auth_mode: entra_id` в `config.yaml` — переменные окружения не нужны.

**Azure VM / Functions / App Service / Container Apps (user‑assigned managed identity):**
- Задай `AZURE_CLIENT_ID` равным client ID пользовательской управляемой идентичности, чтобы `DefaultAzureCredential` выбрал её.

**Foundry Agent Service hosted agent:**
- Создай hosted‑agent и предоставь его идентичности `Azure AI User` (или `Foundry User`) на ресурсе Foundry. Hermes использует `ManagedIdentityCredential` изнутри hosted‑агента; назначение роли относится к идентичности агента, а не к проекту или пользователю.

**AKS Workload Identity (заменяет AAD Pod Identity):**
- Аннотируй сервис‑аккаунт pod‑а client ID workload identity.
- Файл федеративного токена pod‑а автоматически обнаруживается через `AZURE_FEDERATED_TOKEN_FILE`.
- `model.auth_mode: entra_id` работает без дополнительных изменений конфигурации.

**Сервис‑принципал в CI:**
- Задай `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` в окружении runner‑а.

#### Суверенные облака (Government, China)

Экспортируй `AZURE_AUTHORITY_HOST` (например `https://login.microsoftonline.us` для Azure Government, `https://login.partner.microsoftonline.cn` для Azure China). `azure-identity` читает его напрямую.

### Проверки работоспособности

`hermes doctor` запускает 10 s пробу против `DefaultAzureCredential`, когда `model.auth_mode: entra_id`, и сообщает, какой внутренний креденшал сработал (переменные окружения присутствуют, endpoint управляемой идентичности доступен и т.д.).

`hermes auth` выводит структурированный блок статуса:

```
azure-foundry (Microsoft Entra ID):
  Endpoint: https://my-resource.openai.azure.com/openai/v1
  Scope: https://ai.azure.com/.default
  Status: configured; live token probe is skipped here
```

### Ограничения

- **Anthropic‑style эндпоинты используют httpx event hook.** Anthropic Python SDK не принимает callable `auth_token` нативно (≤ 0.86.0). Hermes устанавливает request event hook на кастомный `httpx.Client`, который генерирует свежий JWT для каждого исходящего запроса и переписывает `Authorization: Bearer <jwt>`. Это функционально эквивалентно native `Callable[[], str]` контракту OpenAI SDK, но добавляет один уровень индирекции. Если Anthropic SDK добавит поддержку callable‑auth в будущих версиях, Hermes переключится на неё автоматически.
- **Batch‑задачи и `multiprocessing.Pool`.** Провайдер токенов Entra — замыкание, которое нельзя сериализовать (pickle) между процессами. `batch_runner.py` автоматически убирает callable из конфигурации воркера и позволяет каждому процессу построить свой провайдер из `config.yaml` — пользователь ничего не делает, но каждый воркер платит один проход цепочки при старте.
- **Отсутствие сохранения bearer JWT в `auth.json`.** Hermes не дублирует внутренний кэш токенов `azure-identity`; при холодном старте цепочка креденшалов проходит заново при первой инференции.
## Конфигурация (записывается в `config.yaml`)

После запуска мастера ты увидишь что‑то вроде этого:

```yaml
model:
  provider: azure-foundry
  base_url: https://my-resource.openai.azure.com/openai/v1
  api_mode: chat_completions         # or "anthropic_messages"
  default: gpt-5.4-mini              # your deployment / model name
  context_length: 400000             # auto-detected
```

А в `~/.hermes/.env`:

```
AZURE_FOUNDRY_API_KEY=<your-azure-key>
```
## OpenAI‑style endpoints (GPT, Llama и др.)

GA‑endpoint Azure OpenAI версии v1 принимает стандартный клиент Python `openai` с минимальными изменениями:

```yaml
model:
  provider: azure-foundry
  base_url: https://my-resource.openai.azure.com/openai/v1
  api_mode: chat_completions
  default: gpt-5.4
```

Важное поведение:

- **GPT‑5.x, codex и модели серии o автоматически маршрутизируются в Responses API.** Microsoft Foundry развёртывает модели GPT‑5 / codex / o1 / o3 / o4 только как Responses API — вызов `/chat/completions` к ним возвращает `400 "The requested operation is unsupported."`. Hermes определяет эти семейства моделей по имени и прозрачно повышает `api_mode` до `codex_responses`, даже если в `config.yaml по‑прежнему указано `api_mode: chat_completions`. GPT‑4, GPT‑4o, Llama, Mistral и другие развертывания остаются на `/chat/completions`.
- **`max_completion_tokens` используется автоматически.** Azure OpenAI (как и прямой OpenAI) требует `max_completion_tokens` для моделей gpt-4o, серии o и gpt-5.x. Hermes отправляет правильный параметр в зависимости от endpoint.
- **Эндпоинты до версии v1, требующие `api-version`.** Если у тебя есть устаревший базовый URL вида `https://<resource>.openai.azure.com/openai?api-version=2025-04-01-preview`, Hermes извлекает строку запроса и передаёт её через `default_query` в каждом запросе (иначе SDK OpenAI отбрасывает её при объединении путей).
## Конечные точки в стиле Anthropic (Claude через Microsoft Foundry)

Для развертываний Claude используй маршрут в стиле Anthropic:

```yaml
model:
  provider: azure-foundry
  base_url: https://my-resource.services.ai.azure.com/anthropic
  api_mode: anthropic_messages
  default: claude-sonnet-4-6
```

Важное поведение:

- **`/v1` удаляется из базового URL.** SDK Anthropic добавляет `/v1/messages` к каждому запросу — Hermes удаляет любой завершающий `/v1` перед передачей URL в SDK, чтобы избежать двойных путей `/v1`.
- **`api-version` передаётся через `default_query`, а не добавляется к URL.** Azure Anthropic требует параметр строки запроса `api-version`. Встраивание его в базовый URL приводит к некорректным путям вроде `/anthropic?api-version=.../v1/messages` и возвращает 404. Hermes передаёт `api-version=2025-04-15` через `default_query` SDK Anthropic.
- **Для аутентификации используется Bearer вместо `x-api-key`.** Маршрут, совместимый с Anthropic в Azure, требует заголовок `Authorization: Bearer <key>`, а не нативный заголовок Anthropic `x-api-key`. Hermes обнаруживает `azure.com` в базовом URL и направляет ключ API через поле `auth_token` SDK, чтобы правильный заголовок попал к upstream.
- **Бета‑заголовок контекстного окна 1 M сохраняется.** Azure всё ещё ограничивает контекст Claude в 1 M токенов (Opus 4.6/4.7, Sonnet 4.6) заголовком `anthropic-beta: context-1m-2025-08-07`. Hermes оставляет этот бета‑заголовок на путях Azure (он удаляется из нативных запросов OAuth Anthropic, потому что некоторые подписки отклоняют его, но Azure требует).
- **Обновление OAuth‑токена отключено.** Развертывания в Azure используют статические ключи API. Цикл обновления OAuth‑токена `~/.claude/.credentials.json`, применяемый к консоли Anthropic, явно пропускается для конечных точек Azure, чтобы токен OAuth Claude не перезаписал твой ключ Azure в середине сессии.
## Альтернатива: `provider: anthropic` + Azure base URL

Если у тебя уже настроен `provider: anthropic` и ты просто хочешь направить его на Microsoft Foundry для Claude, можешь полностью отказаться от использования провайдера `azure-foundry`:

```yaml
model:
  provider: anthropic
  base_url: https://my-resource.services.ai.azure.com/anthropic
  key_env: AZURE_ANTHROPIC_KEY
  default: claude-sonnet-4-6
```

При установленном `AZURE_ANTHROPIC_KEY` в `~/.hermes/.env`. Hermes обнаруживает `azure.com` в базовом URL и обходит цепочку OAuth‑токенов Claude Code, поэтому ключ Azure используется напрямую через аутентификацию `x-api-key`.

`key_env` — каноничное поле в snake_case; `api_key_env` (а также camelCase `keyEnv` / `apiKeyEnv`) принимаются как алиасы. Если заданы одновременно `key_env` и `AZURE_ANTHROPIC_KEY`/`ANTHROPIC_API_KEY`, приоритет имеет переменная окружения с именем `key_env`.
## Обнаружение моделей

Azure **не** предоставляет endpoint, работающий только по API‑ключу, для получения списка ваших *развернутых* моделей. Перечисление развертываний требует аутентификации Azure Resource Manager (`az cognitiveservices account deployment list`) с Azure AD‑принципалом, а не ключа API вывода.

Что может Hermes:

- Azure OpenAI v1 endpoints (`<resource>.openai.azure.com/openai/v1`) предоставляют `GET /models` с каталогом **доступных** моделей ресурса. Hermes использует этот список для предварительного заполнения выбора модели.
- Маршруты Microsoft Foundry `/anthropic`: обнаруживаются по пути URL, название модели вводится вручную.
- Приватные / защищённые firewall‑ом endpoints: вводятся вручную с дружелюбным сообщением «не удалось выполнить проверку».

Ты всегда можешь ввести имя развертывания напрямую — Hermes не проверяет его наличие в полученном списке.
## Переменные окружения

| Переменная | Назначение |
|----------|---------|
| `AZURE_FOUNDRY_API_KEY` | Основной API‑ключ для Microsoft Foundry / Azure OpenAI (режим `api_key`) |
| `AZURE_FOUNDRY_BASE_URL` | URL конечной точки (устанавливается через `hermes model`; переменная окружения используется как запасной (вариант)) |
| `AZURE_ANTHROPIC_KEY` | Используется `provider: anthropic` + базовый URL Azure (альтернатива `ANTHROPIC_API_KEY`) |
| `AZURE_TENANT_ID` | Тенант Entra ID для потоков service‑principal |
| `AZURE_CLIENT_ID` | Entra ID client ID (service principal, workload identity или user‑assigned managed identity) |
| `AZURE_CLIENT_SECRET` | Секрет service principal |
| `AZURE_CLIENT_CERTIFICATE_PATH` | Сертификат service principal (альтернатива секрету) |
| `AZURE_FEDERATED_TOKEN_FILE` | Путь к федеративному токену workload identity (AKS) |
| `AZURE_AUTHORITY_HOST` | Переопределение хоста authority для суверенных облаков |
| `IDENTITY_ENDPOINT` / `MSI_ENDPOINT` | Конечная точка Managed Identity для App Service, Functions и Container Apps; обычно VMs используют IMDS |

Azure SDK читает переменные `AZURE_*` напрямую. Hermes не проверяет их, кроме как для вывода в `hermes doctor`, где указываются присутствующие источники.
## Устранение неполадок

**401 Unauthorized при развертывании gpt‑5.x.**
Azure обслуживает gpt‑5.x по адресу `/chat/completions`, а не `/responses`. Hermes обрабатывает это автоматически, когда URL содержит `openai.azure.com`, но если ты видишь 401 с телом `Invalid API key`, проверь, что `api_mode` в твоём `config.yaml` установлен в `chat_completions`.

**404 на `/v1/messages?api-version=.../v1/messages`.**
Это ошибка некорректного URL из старых настроек Azure Anthropic. Обнови Hermes — параметр `api-version` теперь передаётся через `default_query`, а не вшит в базовый URL, поэтому SDK больше не может испортить его при объединении URL.

**Wizard сообщает «Auto‑detection incomplete».**
Конечная точка отклонила как проверку `/models`, так и проверку Anthropic Messages. Это нормально для частных конечных точек за файрволом или с белым списком IP‑адресов. Переключись на ручной выбор режима API и введи имя развертывания — всё будет работать, Hermes просто не может предварительно заполнить список.

**Выбран неверный транспорт.**
Запусти `hermes model` ещё раз, и мастер повторно выполнит проверку. Если проверка всё равно выбирает неправильный режим, можешь отредактировать `config.yaml` напрямую:

```yaml
model:
  provider: azure-foundry
  api_mode: anthropic_messages   # or chat_completions
```

**Entra ID: «credential chain exhausted» или 401 Unauthorized после переключения на `auth_mode: entra_id`.**
- Выполни `az login`, чтобы обновить свою сессию разработчика (кешированный токен мог истечь).
- Убедись, что назначение роли `Azure AI User` (или `Foundry User`) вступило в силу: `az role assignment list --assignee <user-or-identity-id>` должно отобразить её в твоём ресурсе Foundry. Распространение роли может занять до 5 минут.
- Для управляемых идентичностей, назначенных пользователем, проверь, что `AZURE_CLIENT_ID` соответствует идентичности, привязанной к вычислительному ресурсу.
- Запусти `hermes doctor` — проверка Azure Entra покажет, удалось ли получить токен, и выдаст подсказку по исправлению.

**Entra ID: мастер зависает на предзапуске или истекает тайм‑аут.**
10‑секундный предзапуск — это мягкая проверка. Выбери «Save anyway and validate later» и запусти `hermes doctor` после развертывания в целевую среду. Частые причины — недоступный сервис токенов или устаревшее локальное состояние входа; предпочтительно использовать workload identity в CI, задать `AZURE_TENANT_ID`+`AZURE_CLIENT_ID`+`AZURE_CLIENT_SECRET` при работе с сервисным принципалом, либо выполнить `az login` для локальной разработки.

**401 на Anthropic‑подобном эндпоинте с Entra ID.**
Убедись, что та же роль `Azure AI User` (или `Foundry User`) назначена на ресурсе Foundry (она покрывает пути `/openai/v1` и `/anthropic`). Если проверка в стиле OpenAI проходит в мастере, а запросы `claude‑*` падают во время выполнения, наиболее частой причиной является устаревший `model.entra.scope`, оставшийся от предыдущего запуска мастера — удали строку `entra.scope` из `config.yaml`, чтобы во время выполнения использовался диапазон по умолчанию `https://ai.azure.com/.default`.
## Связанные

- [Переменные окружения](/reference/environment-variables)
- [Конфигурация](/user-guide/configuration)
- [AWS Bedrock](/guides/aws-bedrock) — другая крупная интеграция облачного провайдера
- [Microsoft: Настройка Entra ID для Foundry](https://learn.microsoft.com/azure/ai-foundry/foundry-models/how-to/configure-entra-id) — документация upstream для безключевого пути