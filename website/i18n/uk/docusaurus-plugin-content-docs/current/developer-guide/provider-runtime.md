---
sidebar_position: 4
title: "Provider Runtime вирішення"
description: "Як Hermes вирішує провайдери, облікові дані, режими API та допоміжні моделі під час виконання."
---

# Runtime розв’язання провайдера

Hermes має спільний runtime‑розв’язувач провайдера, який використовується в:

- CLI
- gateway
- cron‑завданнях
- ACP
- допоміжних викликах моделей

Основна реалізація:

- `hermes_cli/runtime_provider.py` — розв’язання облікових даних, `_resolve_custom_runtime()`
- `hermes_cli/auth.py` — реєстр провайдерів, `resolve_provider()`
- `hermes_cli/model_switch.py` — спільний конвеєр перемикача `/model` (CLI + gateway)
- `agent/auxiliary_client.py` — маршрутизація допоміжних моделей
- `providers/` — ABC + точки входу реєстру (`ProviderProfile`, `register_provider`, `get_provider_profile`, `list_providers`)
- `plugins/model-providers/<name>/` — плагіни для окремих провайдерів (вбудовані), які оголошують `api_mode`, `base_url`, `env_vars`, `fallback_models` і реєструються в реєстрі при першому доступі. Користувацькі плагіни у `$HERMES_HOME/plugins/model-providers/<name>/` перевизначають вбудовані з тим же ім’ям.

`get_provider_profile()` у `providers/` повертає `ProviderProfile` для заданого ідентифікатора провайдера. `runtime_provider.py` викликає його під час розв’язання, щоб отримати канонічний `base_url`, пріоритетний список `env_vars`, `api_mode` та `fallback_models` без необхідності дублювати ці дані в кількох файлах. Додавання нового плагіна у `plugins/model-providers/<your-provider>/` (або `$HERMES_HOME/plugins/model-providers/<your-provider>/`), який викликає `register_provider()`, достатньо, щоб `runtime_provider.py` його підхопив — жодної гілки в самому розв’язувачі не потрібно.

Якщо ти намагаєшся додати новий провайдер інференсу першого класу, ознайомся з [Adding Providers](./adding-providers.md) та [Model Provider Plugin guide](./model-provider-plugin.md) разом з цією сторінкою.
## Пріоритет розв’язання

На високому рівні розв’язання провайдера використовує:

1. явний запит CLI/runtime
2. `config.yaml` — конфігурація моделі/провайдера
3. змінні середовища
4. специфічні для провайдера значення за замовчуванням або автоматичне визначення

Таке упорядкування має значення, оскільки Hermes розглядає збережений вибір моделі/провайдера як джерело істини для звичайних запусків. Це запобігає тому, що застарілий експорт змінної оболонки безшумно переоприділяє кінцеву точку, яку користувач останнім часом вибрав у `hermes model`.
## Провайдери

Поточні сімейства провайдерів включають (дивись `plugins/model-providers/` для повного набору, що постачається в комплекті):

- OpenRouter
- Nous Portal
- OpenAI Codex
- Copilot / Copilot ACP
- Anthropic (native)
- Google / Gemini (`gemini`, `google-gemini-cli`)
- Alibaba / DashScope (`alibaba`, `alibaba-coding-plan`)
- DeepSeek
- Z.AI
- Kimi / Moonshot (`kimi-coding`, `kimi-coding-cn`)
- MiniMax (`minimax`, `minimax-cn`, `minimax-oauth`)
- Kilo Code
- Hugging Face
- OpenCode Zen / OpenCode Go
- AWS Bedrock
- Azure Foundry
- NVIDIA NIM
- xAI (Grok)
- Arcee
- GMI Cloud
- StepFun
- Qwen OAuth
- Xiaomi
- Ollama Cloud
- LM Studio
- Tencent TokenHub
- Custom (`provider: custom`) — провайдер першого класу для будь‑якої сумісної з OpenAI кінцевої точки
- Named custom providers (`custom_providers` list in config.yaml)
## Вивід під час виконання розв’язання

Runtime resolver повертає дані, зокрема:

- `provider`
- `api_mode`
- `base_url`
- `api_key`
- `source`
- метадані, специфічні для провайдера, такі як інформація про термін дії/оновлення
## Чому це важливо

Цей **резолвер** — головна причина, чому Hermes може ділитися логікою автентифікації/виконання між:

- `hermes chat`
- обробкою повідомлень шлюзу
- завданнями cron, що запускаються у нових сесіях
- сесіями редактора ACP
- допоміжними завданнями моделі
## OpenRouter і власні базові URL‑и, сумісні з OpenAI

Hermes містить логіку, яка запобігає витоку неправильного API‑ключа до власного endpoint, коли існує кілька ключів провайдерів (наприклад, `OPENROUTER_API_KEY` і `OPENAI_API_KEY`).

Кожен API‑ключ провайдера прив’язаний до свого базового URL:

- `OPENROUTER_API_KEY` надсилається лише до endpoint‑ів `openrouter.ai`
- `OPENAI_API_KEY` використовується для власних endpoint‑ів і як запасний (варіант)

Hermes також розрізняє:

- реальний власний endpoint, обраний користувачем
- шлях запасного OpenRouter, який використовується, коли власний endpoint не налаштовано

Це розрізнення особливо важливе для:

- локальних серверів моделей
- несумісних з OpenRouter API, сумісних з OpenAI
- перемикання провайдерів без повторного запуску налаштувань
- збережених у конфігурації власних endpoint‑ів, які мають продовжувати працювати, навіть якщо `OPENAI_BASE_URL` не експортовано в поточному шеллі
## Native Anthropic path

Anthropic більше не лише «через OpenRouter».

Коли розв’язання провайдера вибирає `anthropic`, Hermes використовує:

- `api_mode = anthropic_messages`
- нативний Anthropic Messages API
- `agent/anthropic_adapter.py` для перекладу

Розв’язання облікових даних для нативного Anthropic тепер надає перевагу оновлюваним обліковим даним Claude Code над скопійованими токенами середовища, якщо обидва присутні. На практиці це означає:

- файли облікових даних Claude Code розглядаються як пріоритетне джерело, коли вони містять оновлювану автентифікацію
- ручні значення `ANTHROPIC_TOKEN` / `CLAUDE_CODE_OAUTH_TOKEN` все ще працюють як явні перевизначення
- Hermes попередньо перевіряє оновлення облікових даних Anthropic перед викликами нативного Messages API
- Hermes все ще повторює спробу один раз при 401 після перебудови клієнта Anthropic, як запасний (варіант) шлях
## OpenAI Codex шлях

Codex використовує окремий шлях Responses API:

- `api_mode = codex_responses`
- підтримка спеціалізованого розв’язання облікових даних та сховища автентифікації
## Додаткова маршрутизація моделей

Додаткові завдання, такі як:

- vision
- web extraction summarization
- context compression summaries
- skills hub operations
- MCP helper operations
- memory flushes

можуть використовувати власну маршрутизацію провайдера/моделі замість основної розмовної моделі.

Коли додаткове завдання налаштовано з провайдером `main`, Hermes вирішує це через той самий спільний шлях виконання, що й звичайний чат. На практиці це означає:

- env‑driven custom endpoints все ще працюють
- custom endpoints, збережені через `hermes model` / `config.yaml`, також працюють
- auxiliary routing може розрізняти реальний збережений custom endpoint і запасний (варіант) OpenRouter
## Запасні (варіант) моделі

Hermes підтримує налаштований ланцюжок запасних (варіант) провайдерів — список записів `(provider, model)`, які перебираються послідовно, коли основна модель стикається з помилками. Спадковий одноелементний словник `fallback_model` все ще приймається для зворотної сумісності (і мігрується при першому записі).

### Як це працює всередині

1. **Зберігання**: `AIAgent.__init__` зберігає словник `fallback_model` і встановлює `_fallback_activated = False`.

2. **Точки спрацювання**: `_try_activate_fallback()` викликається з трьох місць у головному циклі повторних спроб у `run_agent.py`:
   - Після досягнення максимальної кількості повторів при недійсних відповідях API (None choices, missing content)
   - При помилках клієнта, які не підлягають повтору (HTTP 401, 403, 404)
   - Після максимальної кількості повторів при транзиторних помилках (HTTP 429, 500, 502, 503)

3. **Потік активації** (`_try_activate_fallback`):
   - Одразу повертає `False`, якщо вже активовано або не налаштовано
   - Викликає `resolve_provider_client()` з `auxiliary_client.py` для створення нового клієнта з правильною автентифікацією
   - Визначає `api_mode`: `codex_responses` для openai‑codex, `anthropic_messages` для anthropic, `chat_completions` для всіх інших
   - Замінює «на місці»: `self.model`, `self.provider`, `self.base_url`, `self.api_mode`, `self.client`, `self._client_kwargs`
   - Для запасного Anthropic: створює нативний клієнт Anthropic замість сумісного з OpenAI
   - Перевіряє кешування підказок (увімкнено для моделей Claude на OpenRouter)
   - Встановлює `_fallback_activated = True` — запобігає повторному спрацюванню
   - Скидає лічильник повторів до 0 і продовжує цикл

4. **Потік конфігурації**:
   - CLI: `cli.py` читає `CLI_CONFIG["fallback_model"]` → передає в `AIAgent(fallback_model=…)`
   - Шлюз: `gateway/run.py._load_fallback_model()` читає `config.yaml` → передає в `AIAgent`
   - Валідація: обидва ключі `provider` і `model` мають бути непорожніми, інакше запасний (варіант) режим вимикається

### Що НЕ підтримує запасний (варіант) режим

- **Делегування підагентів** (`tools/delegate_tool.py`): підагенти успадковують провайдера батька, але не конфігурацію запасного (варіант) провайдера
- **Допоміжні завдання**: використовують власний незалежний ланцюжок автоматичного визначення провайдера (див. розділ «Auxiliary model routing» вище)

Cron‑завдання **підтримують** запасний (варіант) режим: `run_job()` читає `fallback_providers` (або спадковий `fallback_model`) з `config.yaml` і передає його в `AIAgent(fallback_model=…)`, відповідаючи шаблону `_load_fallback_model()` у шлюзі. Дивись [Cron Internals](./cron-internals.md).

### Покриття тестами

Поведінка запасного (варіант) режиму протестована у кількох наборах:

- `tests/run_agent/test_fallback_credential_isolation.py` — ізоляція облікових даних між основною та запасною моделями
- `tests/hermes_cli/test_fallback_cmd.py` — команда CLI `/fallback`
- `tests/gateway/test_fallback_eviction.py` — видалення провайдерів, які зазнали збою, у шлюзі
## Пов’язані документи

- [Agent Loop Internals](./agent-loop.md)
- [ACP Internals](./acp-internals.md)
- [Context Compression & Prompt Caching](./context-compression-and-caching.md)