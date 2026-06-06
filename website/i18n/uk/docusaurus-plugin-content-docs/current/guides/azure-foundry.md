---
sidebar_position: 15
title: "Microsoft Foundry"
description: "Використовуй Hermes Agent з Microsoft Foundry — кінцеві точки у стилі OpenAI та Anthropic, автоматичне визначення транспорту та розгорнутих моделей"
---

# Microsoft Foundry

Провайдер `azure-foundry` Hermes Agent підтримує Microsoft Foundry (раніше Azure AI Foundry) та Azure OpenAI. Один ресурс Foundry може розміщувати моделі з двома різними форматами передачі даних:

- **OpenAI‑style** — `POST /v1/chat/completions` на кінцевих точках типу `https://<resource>.openai.azure.com/openai/v1`. Використовується для GPT‑4.x, GPT‑5.x, Llama, Mistral та більшості моделей з відкритими вагами.
- **Anthropic‑style** — `POST /v1/messages` на кінцевих точках типу `https://<resource>.services.ai.azure.com/anthropic`. Використовується, коли Microsoft Foundry надає моделі Claude у форматі Anthropic Messages API.

Майстер налаштування сканує твою кінцеву точку та автоматично визначає, який транспорт використовується, які розгортання доступні та довжину контексту кожної моделі.
## Передумови

- Microsoft Foundry або ресурс Azure OpenAI з принаймні одним розгортанням
- URL‑адреса кінцевої точки розгортання
- **Або** API‑ключ (у Azure Portal у розділі “Keys and Endpoint”) **або** роль **Azure AI User** RBAC на ресурсі Foundry, якщо плануєш використовувати Microsoft Entra ID (безключовий шлях, який рекомендує Microsoft). У деяких орендарів роль може відображатися як **Foundry User** під час оновлення назви Microsoft.
## Швидкий старт

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

Майстер виконає:

1. **Sniff the URL path** — URL‑адреси, що закінчуються на `/anthropic`, розпізнаються як маршрути Microsoft Foundry Claude.
2. **Probe `GET <base>/models`** — якщо кінцева точка повертає список моделей у форматі OpenAI, Hermes переключається на `chat_completions` і попередньо заповнює вибірник повернутими ідентифікаторами розгортання.
3. **Probe Anthropic Messages shape** — запасний (варіант) для кінцевих точок, які не розкривають `/models`, але приймають формат Anthropic Messages.
4. **Fall back to manual entry** — приватні/закриті кінцеві точки, які відхиляють кожен запит, все ще працюють; ти обираєш режим API і вводиш назву розгортання вручну.

Довжина контексту для обраної моделі визначається через стандартний ланцюжок метаданих Hermes (`models.dev`, метадані провайдера та жорстко закодовані запасні (варіант) сімейства) і зберігається у `config.yaml`, щоб модель могла правильно розрахувати власне вікно контексту.
## Microsoft Entra ID (keyless, RBAC) — recommended

Microsoft recommends [keyless authentication with Microsoft Entra ID](https://learn.microsoft.com/azure/ai-foundry/foundry-models/how-to/configure-entra-id) for production Foundry workloads. Hermes supports Entra ID for **both** API surfaces:

- **OpenAI-style** (`api_mode: chat_completions` / `codex_responses`) — GPT‑4/5, Llama, Mistral, DeepSeek тощо.
- **Anthropic-style** (`api_mode: anthropic_messages`) — Claude‑моделі в Microsoft Foundry.

RBAC у Foundry прив’язаний до ресурсу (`Azure AI User` надає доступ до обох поверхонь; у деяких тенантах може відображатися `Foundry User`) і Microsoft документує один і той самий inference‑scope (`https://ai.azure.com/.default`) для обох. Під капотом:

- OpenAI‑style використовує нативний callable‑контракт `api_key=` у OpenAI Python SDK — SDK автоматично генерує свіжий JWT для кожного запиту.
- Anthropic‑style працює через `httpx.Client` з встановленим request‑event hook, який додає `agent.azure_identity_adapter.build_bearer_http_client`. Це необхідно, бо Anthropic SDK не приймає callable `auth_token` нативно. Hook переписує заголовок `Authorization: Bearer <fresh-jwt>` для кожного вихідного запиту. RBAC та scope однакові — різниця лише в контракті SDK.

### Чому використовувати Entra ID?

- Немає довгоживучих API‑ключів, які треба обертати або відкликати.
- Доступ, керований RBAC — додаєш або видаляєш `Azure AI User` на ресурсі Foundry, без зміни конфігурації.
- Журнали доступу та аудиту сегментуються за виконавцем, а не всі виклики ділять один статичний ключ.
- Єдина поверхня автентифікації для Azure VM, AKS pod‑ів, App Service, Functions, Container Apps та Foundry Agent Service через керовану ідентичність.
- Потоки ідентичності робочих навантажень та сервіс‑принципалів для CI/CD‑конвеєрів.

### Одноразове налаштування (сторона Azure)

1. У Azure Portal відкрий ресурс Foundry → **Access control (IAM)** → **Add → Add role assignment**.
2. Вибери роль **Azure AI User** (або **Foundry User**, якщо у твоєму тенанті роль перейменовано).
3. Признач її:
   - **Твоєму користувацькому обліковому запису** для локальної розробки за допомогою `az login`.
   - **Керованій ідентичності або ідентичності робочого навантаження** для Azure‑хостованих обчислень (рекомендовано для продакшну).
   - **Ідентичності агента Hosted Agent сервісу Foundry**, коли Hermes працює всередині хостованого агента.
   - **Сервіс‑принципалу** для CI/CD‑конвеєрів, коли ідентичність робочого навантаження недоступна.
4. Зачекай ~5 хв, доки роль розповсюдиться.

Azure CLI equivalent:

```bash
az role assignment create \
  --assignee <principal-or-agent-identity-client-id> \
  --role "Azure AI User" \
  --scope <foundry-resource-id>
```

### Одноразове налаштування (сторона Hermes)

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

Майстер запускає обмежену preflight‑пробу (тайм‑аут 10 s). При помилці пропонує «save anyway, validate later» — корисно, коли налаштовуєш машину, яка ще не має облікових даних, але вони будуть доступні під час виконання (наприклад, підготовка конфігурації для розгортання з керованою ідентичністю).

`azure-identity` встановлюється автоматично при першому використанні через lazy‑install Hermes. Щоб попередньо встановити:

```bash
pip install azure-identity
```

### Конфігурація, записана у `config.yaml`

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

Hermes керує лише однією Entra‑специфічною опцією у `config.yaml`:

- **`scope`** — OAuth‑ресурсний скоп. За замовчуванням використовується задокументований Microsoft скоп інференсу (`https://ai.azure.com/.default`). Перевизначай лише, якщо твій ресурс був створений з нестандартною аудиторією.

Все інше (тенант, секрет сервіс‑принципалу, файл федеративного токену, суверенна хмара, налаштування брокера) читається `azure-identity` безпосередньо зі стандартних змінних середовища `AZURE_*` — дивись [credential resolution order](#credential-resolution-order) нижче. Встанови їх у `~/.hermes/.env` або у середовищі розгортання саме так, як описано в довідці Microsoft SDK.

Ніякі секрети не потрапляють у `~/.hermes/.env` у режимі Entra — `azure-identity` кешує токени в процесі (і, якщо доступно, у сховищі ОС / `~/.IdentityService`).

### Порядок розв’язання облікових даних

`azure-identity`'s `DefaultAzureCredential` проходить цей ланцюжок при кожному запиті токену, зупиняючись на першій обліковці, що повернула токен:

1. **Environment credential** — `AZURE_TENANT_ID` + `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` (або `AZURE_CLIENT_CERTIFICATE_PATH` / `AZURE_FEDERATED_TOKEN_FILE`).
2. **Workload Identity** — `AZURE_FEDERATED_TOKEN_FILE` (AKS federated tokens / OIDC).
3. **Managed Identity** — IMDS endpoint (`169.254.169.254`) для віртуальних машин; `IDENTITY_ENDPOINT` для App Service / Functions / Container Apps. Hosted‑agent агенти Foundry Agent Service використовують ідентичність самого агента.
4. **Visual Studio Code** — Azure account extension.
5. **Azure CLI** — `az login` сесія.
6. **Azure Developer CLI** — `azd auth login`.
7. **Azure PowerShell** — `Connect-AzAccount`.
8. **Broker** (Windows / WSL only) — Web Account Manager.

Інтерактивна браузерна обліковка виключена за замовчуванням для безконтактних запусків Hermes; використовуйте Azure CLI, Azure Developer CLI, керовану ідентичність, workload identity або облікові дані сервіс‑принципалу.

### Шаблони розгортання

**Локальна розробка:**
```bash
az login
hermes model   # pick Azure Foundry → Entra ID
hermes         # uses your az login token
```

**Azure VM / Functions / App Service / Container Apps (system‑assigned managed identity):**
1. Увімкни system‑assigned ідентичність на ресурсі обчислень.
2. Надій роль `Azure AI User` (або `Foundry User`) на ресурсі Foundry.
3. Встанови `model.auth_mode: entra_id` у `config.yaml` — змінні середовища не потрібні.

**Azure VM / Functions / App Service / Container Apps (user‑assigned managed identity):**
- Встанови `AZURE_CLIENT_ID` у client ID user‑assigned ідентичності, щоб `DefaultAzureCredential` обрав правильну.

**Foundry Agent Service hosted agent:**
- Створи hosted‑agent і надай його ідентичності роль `Azure AI User` (або `Foundry User`) на ресурсі Foundry. Hermes використовує `ManagedIdentityCredential` всередині hosted‑agent; призначення ролі має бути на ідентичності агента, а не лише на проєкті чи користувачі.

**AKS Workload Identity (замінює AAD Pod Identity):**
- Додай анотацію до service account pod‑а з client ID workload identity.
- Файл федеративного токену pod‑а автоматично виявляється через `AZURE_FEDERATED_TOKEN_FILE`.
- `model.auth_mode: entra_id` працює без додаткових змін конфігурації.

**Сервіс‑принципал у CI:**
- Встанови `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` у середовищі runner‑а.

#### Суверенні хмари (Government, China)

Експортуй `AZURE_AUTHORITY_HOST` (наприклад `https://login.microsoftonline.us` для Azure Government, `https://login.partner.microsoftonline.cn` для Azure China). `azure-identity` читає його безпосередньо.

### Перевірки працездатності

`hermes doctor` запускає 10 s пробу проти `DefaultAzureCredential`, коли `model.auth_mode: entra_id`, і повідомляє, яка внутрішня обліковка перемогла (наявність змінних, доступність endpoint тощо).

`hermes auth` показує структурований блок статусу:

```
azure-foundry (Microsoft Entra ID):
  Endpoint: https://my-resource.openai.azure.com/openai/v1
  Scope: https://ai.azure.com/.default
  Status: configured; live token probe is skipped here
```

### Обмеження

- **Anthropic‑style endpoints використовують httpx event hook.** Anthropic Python SDK не приймає callable `auth_token` нативно (≤ 0.86.0). Hermes встановлює request event hook на кастомному `httpx.Client`, який створює свіжий JWT для кожного вихідного запиту і переписує `Authorization: Bearer <jwt>`. Це функціонально еквівалентно native `Callable[[], str]` контракту OpenAI SDK, лише додає один рівень індирекції. Якщо Anthropic SDK додасть підтримку callable‑auth у майбутньому, Hermes перейде на нього прозоро.
- **Batch‑jobs та `multiprocessing.Pool`.** Провайдер токену Entra — це closure, який не можна pickle‑нути між процесами. `batch_runner.py` автоматично видаляє callable з конфігурації воркера і дозволяє кожному процесу відновити власний провайдер з `config.yaml` — користувачеві нічого не потрібно робити, проте кожен воркер сплачує один проход ланцюжка при старті.
- **Відсутність збереження bearer JWT у `auth.json`.** Hermes не дублює внутрішній кеш токенів `azure-identity`; холодний старт проходить ланцюжок обліковок при першій інференції.
## Конфігурація (записується у `config.yaml`)

Після запуску майстра ти побачиш щось подібне:

```yaml
model:
  provider: azure-foundry
  base_url: https://my-resource.openai.azure.com/openai/v1
  api_mode: chat_completions         # or "anthropic_messages"
  default: gpt-5.4-mini              # your deployment / model name
  context_length: 400000             # auto-detected
```

А у `~/.hermes/.env`:

```
AZURE_FOUNDRY_API_KEY=<your-azure-key>
```
## OpenAI‑style endpoints (GPT, Llama, тощо)

Azure OpenAI v1 GA endpoint приймає стандартний клієнт Python `openai` з мінімальними змінами:

```yaml
model:
  provider: azure-foundry
  base_url: https://my-resource.openai.azure.com/openai/v1
  api_mode: chat_completions
  default: gpt-5.4
```

Важлива поведінка:

- **GPT‑5.x, codex та o‑series автоматично перенаправляються до Responses API.** Microsoft Foundry розгортає моделі GPT‑5 / codex / o1 / o3 / o4 лише як Responses‑API — виклик `/chat/completions` для них повертає `400 "The requested operation is unsupported."`. Hermes визначає ці сімейства моделей за назвою та прозоро оновлює `api_mode` до `codex_responses`, навіть якщо у `config.yaml` все ще вказано `api_mode: chat_completions`. GPT‑4, GPT‑4o, Llama, Mistral та інші розгортання залишаються на `/chat/completions`.
- **`max_completion_tokens` використовується автоматично.** Azure OpenAI (як і прямий OpenAI) вимагає `max_completion_tokens` для моделей gpt‑4o, o‑series та gpt‑5.x. Hermes надсилає правильний параметр залежно від endpoint.
- **Pre‑v1 endpoint‑и, які потребують `api-version`.** Якщо у тебе є застаріла базова URL‑адреса типу `https://<resource>.openai.azure.com/openai?api-version=2025-04-01-preview`, Hermes витягує рядок запиту та передає його через `default_query` у кожному запиті (SDK OpenAI інакше відкидає його під час об’єднання шляхів).
## Точки доступу у стилі Anthropic (Claude через Microsoft Foundry)

Для розгортань Claude використай маршрут у стилі Anthropic:

```yaml
model:
  provider: azure-foundry
  base_url: https://my-resource.services.ai.azure.com/anthropic
  api_mode: anthropic_messages
  default: claude-sonnet-4-6
```

Важлива поведінка:

- **`/v1` видаляється з базового URL.** SDK Anthropic додає `/v1/messages` до кожного запиту — Hermes видаляє будь‑який кінцевий `/v1` перед передачею URL до SDK, щоб уникнути подвоєння шляху `/v1`.
- **`api-version` передається через `default_query`, а не додається до URL.** Azure Anthropic вимагає параметр запиту `api-version`. Вбудовування його в базовий URL створює некоректні шляхи типу `/anthropic?api-version=.../v1/messages` і повертає 404. Hermes передає `api-version=2025-04-15` через `default_query` SDK Anthropic.
- **Використовується автентифікація Bearer замість `x-api-key`.** Маршрут, сумісний з Anthropic у Azure, вимагає заголовок `Authorization: Bearer <key>` замість рідного заголовка Anthropic `x-api-key`. Hermes виявляє `azure.com` у базовому URL і передає ключ API через поле `auth_token` SDK, щоб правильний заголовок потрапив до upstream.
- **Залишається бета‑заголовок 1 M контекстного вікна.** Azure все ще обмежує контекст Claude у 1 млн токенів (Opus 4.6/4.7, Sonnet 4.6) заголовком `anthropic-beta: context-1m-2025-08-07`. Hermes залишає цей бета‑заголовок у шляхах Azure (він видаляється з нативних запитів OAuth Anthropic, бо деякі підписки його відхиляють, але Azure його потребує).
- **Оновлення OAuth‑токену вимкнено.** У розгортаннях Azure використовуються статичні ключі API. Цикл оновлення OAuth‑токену `~/.claude/.credentials.json`, який застосовується до Anthropic Console, явно пропускається для кінцевих точок Azure, щоб токен OAuth Claude Code не перезаписував ваш Azure‑ключ під час сесії.
## Альтернатива: `provider: anthropic` + Azure base URL

Якщо ти вже налаштував `provider: anthropic` і просто хочеш спрямувати його на Microsoft Foundry для Claude, можеш повністю пропустити провайдера `azure-foundry`:

```yaml
model:
  provider: anthropic
  base_url: https://my-resource.services.ai.azure.com/anthropic
  key_env: AZURE_ANTHROPIC_KEY
  default: claude-sonnet-4-6
```

З встановленою змінною `AZURE_ANTHROPIC_KEY` у `~/.hermes/.env`. Hermes виявляє `azure.com` у базовому URL і обходить ланцюжок OAuth‑токену Claude Code, тому Azure‑ключ використовується безпосередньо з автентифікацією `x-api-key`.

`key_env` — це канонічна назва поля у snake_case; `api_key_env` (а також camelCase `keyEnv` / `apiKeyEnv`) приймаються як альтернативи. Якщо встановлені і `key_env`, і `AZURE_ANTHROPIC_KEY`/`ANTHROPIC_API_KEY`, пріоритет має змінна середовища з назвою `key_env`.
## Виявлення моделей

Azure **не** надає чистого endpoint, що працює лише за API‑ключем, для отримання списку ваших *розгорнутих* розгортань моделей. Перерахування розгортань вимагає автентифікації Azure Resource Manager (`az cognitiveservices account deployment list`) за допомогою Azure AD‑принципала, а не ключа inference API.

Що може Hermes:

- Azure OpenAI v1 endpoints (`<resource>.openai.azure.com/openai/v1`) надають `GET /models` з **доступним** каталогом моделей ресурсу. Hermes використовує цей список для попереднього заповнення вибору моделі.
- Microsoft Foundry `/anthropic` маршрути: виявляються за шляхом URL, назву моделі вводять вручну.
- Приватні / захищені endpoint'и: ручне введення з дружнім повідомленням «не вдалося виконати запит».

Ти завжди можеш ввести назву розгортання безпосередньо — Hermes не перевіряє її проти повернутого списку.
## Змінні середовища

| Змінна | Призначення |
|----------|-------------|
| `AZURE_FOUNDRY_API_KEY` | Основний API‑ключ для Microsoft Foundry / Azure OpenAI (режим `api_key`) |
| `AZURE_FOUNDRY_BASE_URL` | URL кінцевої точки (встановлюється через `hermes model`; змінна середовища використовується як запасний (варіант)) |
| `AZURE_ANTHROPIC_KEY` | Використовується `provider: anthropic` + базовим URL Azure (альтернатива `ANTHROPIC_API_KEY`) |
| `AZURE_TENANT_ID` | Тенант Entra ID для потоків service‑principal |
| `AZURE_CLIENT_ID` | ID клієнта Entra ID (service principal, workload identity або user‑assigned managed identity) |
| `AZURE_CLIENT_SECRET` | Секрет service principal |
| `AZURE_CLIENT_CERTIFICATE_PATH` | Сертифікат service principal (альтернатива секрету) |
| `AZURE_FEDERATED_TOKEN_FILE` | Шлях до федеративного токену Workload Identity (AKS) |
| `AZURE_AUTHORITY_HOST` | Перевизначення хоста влади суверенної хмари |
| `IDENTITY_ENDPOINT` / `MSI_ENDPOINT` | Кінцева точка Managed Identity для App Service, Functions та Container Apps; віртуальні машини зазвичай використовують IMDS |

Azure SDK читає змінні середовища `AZURE_*` безпосередньо. Hermes їх не інспектує, окрім повідомлення про те, які джерела присутні у виводі `hermes doctor`.
## Troubleshooting

**401 Unauthorized на розгортаннях gpt-5.x.**
Azure надає gpt-5.x за адресою `/chat/completions`, а не `/responses`. Hermes обробляє це автоматично, коли URL містить `openai.azure.com`, але якщо ти бачиш 401 з тілом `Invalid API key`, перевір, чи `api_mode` у твоєму `config.yaml` встановлено в `chat_completions`.

**404 на `/v1/messages?api-version=.../v1/messages`.**
Це помилка некоректного URL у старих налаштуваннях Azure Anthropic. Онови Hermes — параметр `api-version` тепер передається через `default_query`, а не вбудовується у базовий URL, тому SDK більше не спотворює його під час з’єднання шляхів.

**Wizard повідомляє “Auto-detection incomplete.”**
Кінцева точка відхилила як пробу `/models`, так і пробу Anthropic Messages. Це нормально для приватних кінцевих точок за фаєрволом або з білим списком IP‑адрес. Перейдіть до ручного вибору режиму API і введи назву розгортання — все працюватиме, просто Hermes не зможе автоматично заповнити список.

**Вибрано неправильний транспорт.**
Запусти `hermes model` ще раз, і майстер повторно проведе пробу. Якщо проба все ще вибирає неправильний режим, можеш відредагувати `config.yaml` вручну:

```yaml
model:
  provider: azure-foundry
  api_mode: anthropic_messages   # or chat_completions
```

**Entra ID: “credential chain exhausted” або 401 Unauthorized після переходу на `auth_mode: entra_id`.**
- Запусти `az login`, щоб оновити свою розробницьку сесію (кешований токен міг прострочитися).
- Перевір, чи застосовано роль `Azure AI User` (або `Foundry User`): `az role assignment list --assignee <user-or-identity-id>` має показати її у твоєму ресурсі Foundry. Розповсюдження ролі може зайняти до 5 хвилин.
- Для керованих ідентичностей, призначених користувачем, переконайся, що `AZURE_CLIENT_ID` відповідає ідентичності, прикріпленій до обчислювального ресурсу.
- Запусти `hermes doctor` — Azure Entra probe повідомить, чи успішно отримано токен, і надасть підказку щодо виправлення.

**Entra ID: майстер зависає або час очікування закінчується під час попередньої перевірки.**
10‑секундна попередня перевірка — це м’яка перевірка. Обери “Save anyway and validate later” і запусти `hermes doctor` після розгортання в цільове середовище. Типові причини — недоступний сервіс токенів або застарілий локальний стан входу; у CI краще використовувати workload identity, задати `AZURE_TENANT_ID` + `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` при використанні сервісного принципалу, або запустити `az login` для локальної розробки.

**401 на Anthropic‑подібній кінцевій точці з Entra ID.**
Переконайся, що та сама роль `Azure AI User` (або `Foundry User`) призначена на ресурсі Foundry (вона охоплює шляхи `/openai/v1` і `/anthropic`). Якщо проба у стилі OpenAI працює під час майстра, а запити `claude-*` падають під час виконання, найчастіша причина — залишився застарілий параметр `model.entra.scope` від попереднього запуску майстра. Видали рядок `entra.scope` у `config.yaml`, щоб під час виконання використався типовий scope `https://ai.azure.com/.default`.
## Related

- [Environment variables](/reference/environment-variables)
- [Configuration](/user-guide/configuration)
- [AWS Bedrock](/guides/aws-bedrock) — інша інтеграція великого хмарного провайдера
- [Microsoft: Configure Entra ID for Foundry](https://learn.microsoft.com/azure/ai-foundry/foundry-models/how-to/configure-entra-id) — вихідна документація для безключового шляху