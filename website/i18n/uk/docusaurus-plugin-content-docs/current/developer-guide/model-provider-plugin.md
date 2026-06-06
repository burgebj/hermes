---
sidebar_position: 10
title: "Плагіни Model Provider"
description: "Як створити плагін провайдера моделі (бекенд інференсу) для Hermes Agent"
---

# Створення плагіна **model provider**

Плагіни **model provider** оголошують бекенд інференсу — сумісну з OpenAI кінцеву точку, сервер Anthropic Messages, API відповідей у стилі Codex або нативну поверхню Bedrock — через який Hermes може маршрутизувати виклики `AIAgent`. Кожен вбудований провайдер (OpenRouter, Anthropic, GMI, DeepSeek, Nvidia, …) постачається у вигляді одного з цих плагінів. Треті сторони можуть додати свої, просто створивши каталог у `$HERMES_HOME/plugins/model-providers/` без жодних змін у репозиторії.

:::tip
Плагіни **model provider** — це третій тип **provider plugin**. Інші — це [Memory Provider Plugins](/developer-guide/memory-provider-plugin) (знання між сесіями) та [Context Engine Plugins](/developer-guide/context-engine-plugin) (стратегії стиснення контексту). Усі три слідують одному шаблону: «додати каталог, оголосити профіль, без правок репозиторію».
:::
## Як працює виявлення

`providers/__init__.py._discover_providers()` виконується ліниво під час першого виклику `get_provider_profile()` або `list_providers()`. Порядок виявлення:

1. **Вбудовані плагіни** — `<repo>/plugins/model-providers/<name>/` — постачаються з Hermes
2. **Користувацькі плагіни** — `$HERMES_HOME/plugins/model-providers/<name>/` — просто додай будь‑яку теку; перезапуск не потрібен для наступних сесій
3. **Застарілий однофайловий** — `<repo>/providers/<name>.py` — сумісність зі встановленнями поза деревом

**Користувацькі плагіни перекривають вбудовані плагіни з тією ж назвою**, оскільки `register_provider()` працює за принципом «останній запис перемагає». Додай теку `$HERMES_HOME/plugins/model-providers/gmi/`, щоб замінити вбудований профіль GMI, не змінюючи репозиторій.
## Структура директорії

```
plugins/model-providers/my-provider/
├── __init__.py       # Calls register_provider(profile) at module-level
├── plugin.yaml       # kind: model-provider + metadata (optional but recommended)
└── README.md         # Setup instructions (optional)
```

Єдиний необхідний файл – `__init__.py`. `plugin.yaml` використовується `hermes plugins` для інспекції та загальним PluginManager для маршрутизації плагіна до потрібного завантажувача; без нього загальний завантажувач переходить до евристики на основі вихідного тексту.
## Minimal example — простий провайдер API‑ключа

```python
# plugins/model-providers/acme-inference/__init__.py
from providers import register_provider
from providers.base import ProviderProfile

acme = ProviderProfile(
    name="acme-inference",
    aliases=("acme",),
    display_name="Acme Inference",
    description="Acme — OpenAI-compatible direct API",
    signup_url="https://acme.example.com/keys",
    env_vars=("ACME_API_KEY", "ACME_BASE_URL"),
    base_url="https://api.acme.example.com/v1",
    auth_type="api_key",
    default_aux_model="acme-small-fast",
    fallback_models=(
        "acme-large-v3",
        "acme-medium-v3",
        "acme-small-fast",
    ),
)

register_provider(acme)
```

```yaml
# plugins/model-providers/acme-inference/plugin.yaml
name: acme-inference
kind: model-provider
version: 1.0.0
description: Acme Inference — OpenAI-compatible direct API
author: Your Name
```

Ось і все. Після розміщення цих двох файлів наступне **auto‑wire** без жодних інших змін:

| Інтеграція | Де | Що отримує |
|---|---|---|
| Розв’язання облікових даних | `hermes_cli/auth.py` | `PROVIDER_REGISTRY["acme-inference"]` заповнюється з профілю |
| CLI‑прапорець `--provider` | `hermes_cli/main.py` | Приймає `acme-inference` |
| Вибір `hermes model` | `hermes_cli/models.py` | Показується в `CANONICAL_PROVIDERS`, список моделей отримується з `{base_url}/models` |
| `hermes doctor` | `hermes_cli/doctor.py` | Перевірка стану для `ACME_API_KEY` + проба `{base_url}/models` |
| `hermes setup` | `hermes_cli/config.py` | `ACME_API_KEY` з’являється в `OPTIONAL_ENV_VARS` та майстрі налаштувань |
| Зворотне зіставлення URL | `agent/model_metadata.py` | Ім’я хосту → назва провайдера для авто‑виявлення |
| Додаткова модель | `agent/auxiliary_client.py` | Використовує `default_aux_model` для стиснення / підсумовування |
| Розв’язання під час виконання | `hermes_cli/runtime_provider.py` | Повертає правильні `base_url`, `api_key`, `api_mode` |
| Транспорт | `agent/transports/chat_completions.py` | Шлях профілю генерує kwargs через `prepare_messages` / `build_extra_body` / `build_api_kwargs_extras` |
## Поля ProviderProfile

Повне визначення у `providers/base.py`. Найкорисніші:

| Поле | Тип | Призначення |
|---|---|---|
| `name` | str | Канонічний ідентифікатор — відповідає `model.provider` у `config.yaml` та прапору `--provider` |
| `aliases` | `tuple[str, ...]` | Альтернативні назви, які розв’язує `get_provider_profile()` (наприклад, `grok` → `xai`) |
| `api_mode` | str | `chat_completions` \| `codex_responses` \| `anthropic_messages` \| `bedrock_converse` |
| `display_name` | str | Людська назва, що показується у вибірці `hermes model` |
| `description` | str | Підзаголовок у вибірці |
| `signup_url` | str | Показується під час першого запуску («отримати API‑ключ тут») |
| `env_vars` | `tuple[str, ...]` | Змінні середовища з API‑ключами у пріоритетному порядку; останній запис `*_BASE_URL` використовується як перевизначення базового URL користувача |
| `base_url` | str | Типова кінцева точка інференції |
| `models_url` | str | Явний URL каталогу (за замовчуванням `{base_url}/models`) |
| `auth_type` | str | `api_key` \| `oauth_device_code` \| `oauth_external` \| `copilot` \| `aws_sdk` \| `external_process` |
| `fallback_models` | `tuple[str, ...]` | Підготовлений список, який показується, коли не вдається отримати живий каталог |
| `default_headers` | `dict[str, str]` | Надсилаються з кожним запитом (наприклад, `Editor-Version` у Copilot) |
| `fixed_temperature` | Any | `None` = використати значення виклику; маркер `OMIT_TEMPERATURE` = не надсилати температуру взагалі (Kimi) |
| `default_max_tokens` | `int \| None` | Обмеження `max_tokens` на рівні провайдера (Nvidia: 16384) |
| `default_aux_model` | str | Дешева модель для допоміжних завдань (стиснення, комп’ютерний зір, резюмування) |
## Перевизначувані хуки

Успадкуй `ProviderProfile` для нетривіальних особливостей:

```python
from typing import Any
from providers.base import ProviderProfile

class AcmeProfile(ProviderProfile):
    def prepare_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Provider-specific message preprocessing. Runs after codex
        sanitization, before developer-role swap. Default: pass-through."""
        # Example: Qwen normalizes plain-text content to a list-of-parts
        # array and injects cache_control; Kimi rewrites tool-call JSON
        return messages

    def build_extra_body(self, *, session_id=None, **context) -> dict:
        """Provider-specific extra_body fields merged into the API call.
        Context includes: session_id, provider_preferences, model, base_url,
        reasoning_config. Default: empty dict."""
        # Example: OpenRouter's provider-preferences block,
        # Gemini's thinking_config translation.
        return {}

    def build_api_kwargs_extras(self, *, reasoning_config=None, **context):
        """Returns (extra_body_additions, top_level_kwargs). Needed when some
        fields go top-level (Kimi's reasoning_effort) and some go in extra_body
        (OpenRouter's reasoning dict). Default: ({}, {})."""
        return {}, {}

    def fetch_models(self, *, api_key=None, timeout=8.0) -> list[str] | None:
        """Live catalog fetch. Default hits {models_url or base_url}/models with
        Bearer auth. Override for: custom auth (Anthropic), no REST endpoint
        (Bedrock → None), or public/unauthenticated catalogs (OpenRouter)."""
        return super().fetch_models(api_key=api_key, timeout=timeout)
```
## Приклади посилань на хуки

Ознайомся з цими вбудованими плагінами‑ідіомами:

| Плагін | Навіщо дивитися |
|---|---|
| `plugins/model-providers/openrouter/` | Агрегатор з налаштуваннями провайдера, публічний каталог моделей |
| `plugins/model-providers/gemini/` | `thinking_config` переклад (рідний + сумісний з OpenAI вкладений формат) |
| `plugins/model-providers/kimi-coding/` | `OMIT_TEMPERATURE`, `extra_body.thinking`, верхньорівневий `reasoning_effort` |
| `plugins/model-providers/qwen-oauth/` | Нормалізація повідомлень, ін’єкція `cache_control`, VL high‑res |
| `plugins/model-providers/nous/` | Теги атрибуції, «пропускати міркування, коли вимкнено» |
| `plugins/model-providers/custom/` | Ollama `num_ctx` + особливості `think: false` |
| `plugins/model-providers/bedrock/` | `api_mode="bedrock_converse"`, `fetch_models` повертає None (відсутня REST‑точка) |
## Перевизначення користувачем — заміна вбудованого без редагування репозиторію

Скажімо, ти хочеш направити `gmi` на свій приватний staging‑endpoint для тестування. Створи `~/.hermes/plugins/model-providers/gmi/__init__.py`:

```python
from providers import register_provider
from providers.base import ProviderProfile

register_provider(ProviderProfile(
    name="gmi",
    aliases=("gmi-cloud", "gmicloud"),
    env_vars=("GMI_API_KEY",),
    base_url="https://gmi-staging.internal.example.com/v1",
    auth_type="api_key",
    default_aux_model="google/gemini-3.1-flash-lite-preview",
))
```

У наступній сесії `get_provider_profile("gmi").base_url` поверне URL staging‑endpoint. Без патчу репозиторію, без повторної збірки. Оскільки плагіни користувача виявляються після вбудованих, виклик користувача `register_provider()` має перевагу.
## вибір api_mode

Розпізнаються чотири значення. Hermes вибирає одне на основі:

1. Явного перевизначення користувачем (`config.yaml` `model.api_mode`, якщо встановлено)
2. Диспетчеризації per-model від OpenCode (`opencode_model_api_mode` для Zen і Go)
3. Автоматичне визначення URL — суфікс `/anthropic` → `anthropic_messages`, `api.openai.com` → `codex_responses`, `api.x.ai` → `codex_responses`, `/coding` на доменах Kimi → `chat_completions`
4. **Profile `api_mode`** як запасний (варіант), коли автодетекція URL нічого не знайшла
5. За замовчуванням `chat_completions`

Встанови `profile.api_mode` відповідно до типового режиму, який надає твій провайдер — це слугує підказкою. Явні перевизначення URL користувачем все одно мають пріоритет.
## Типи автентифікації

| `auth_type` | Значення | Хто використовує |
|---|---|---|
| `api_key` | Одна змінна середовища містить статичний API‑ключ | Більшість провайдерів |
| `oauth_device_code` | Потік OAuth за допомогою коду пристрою | — |
| `oauth_external` | Користувач входить в інше місце, токени зберігаються у `auth.json` | Anthropic OAuth, MiniMax OAuth, Gemini Cloud Code, Qwen Portal, Nous Portal |
| `copilot` | Цикл оновлення токену GitHub Copilot | лише плагін `copilot` |
| `aws_sdk` | Ланцюжок облікових даних AWS SDK (роль IAM, профіль, змінна середовища) | лише плагін `bedrock` |
| `external_process` | Автентифікація обробляється підпроцесом, який запускає агент | лише плагін `copilot‑acp` |

`auth_type` визначає, які гілки коду розглядають твого провайдера як «простий провайдер api‑key» — якщо це не `api_key`, PluginManager все одно записує маніфест, але автоматизація на рівні CLI Hermes (перевірки **doctor**, прапорець `--provider`, делегування майстру налаштувань) може його пропустити.
## Час виявлення

Виявлення провайдера є **lazy** — ініціюється під час першого виклику `get_provider_profile()` або `list_providers()` у процесі. На практиці це відбувається одразу під час запуску (завантаження модуля `auth.py` розширює `PROVIDER_REGISTRY` одразу). Якщо потрібно перевірити, чи ваш плагін завантажився, виконай:

```bash
hermes doctor
```

— успішний профіль `auth_type="api_key"` з’явиться у розділі **Provider Connectivity** з пробою `/models`.

Для програмної інспекції:

```python
from providers import list_providers
for p in list_providers():
    print(p.name, p.base_url, p.api_mode)
```
## Тестування вашого плагіна

Вкажи `HERMES_HOME` на тимчасову директорію, щоб не забруднювати реальну конфігурацію:

```bash
export HERMES_HOME=/tmp/hermes-plugin-test
mkdir -p $HERMES_HOME/plugins/model-providers/my-provider
cat > $HERMES_HOME/plugins/model-providers/my-provider/__init__.py <<'EOF'
from providers import register_provider
from providers.base import ProviderProfile
register_provider(ProviderProfile(
    name="my-provider",
    env_vars=("MY_API_KEY",),
    base_url="https://api.my-provider.example.com/v1",
    auth_type="api_key",
))
EOF

export MY_API_KEY=your-test-key
hermes -z "hello" --provider my-provider -m some-model
```
## Загальна інтеграція PluginManager

Загальний `PluginManager` (об’єкт, на якому працює `hermes plugins`) **бачить** плагіни‑постачальники моделей, але не імпортує їх — їх життєвий цикл керує `providers/__init__.py`. Менеджер записує маніфест для інспекції та категоризує їх за `kind: model-provider`. Коли ти кладеш непідписаний користувацький плагін у `$HERMES_HOME/plugins/`, який викликає `register_provider` з `ProviderProfile`, менеджер автоматично примушує його до типу `kind: model-provider` за допомогою евристики на основі вихідного тексту — тому плагін все одно правильно маршрутується, навіть без `plugin.yaml`.
## Розповсюдження через pip

Як і будь‑який плагін Hermes, провайдери моделей можуть постачатися у вигляді пакету pip. Додай entry point у свій `pyproject.toml`:

```toml
[project.entry-points."hermes.plugins"]
acme-inference = "acme_hermes_plugin:register"
```

…де `acme_hermes_plugin:register` — це функція, яка викликає `register_provider(profile)`. Загальний `PluginManager` підбирає плагіни‑точки входу під час `discover_and_load()`. Для pip‑плагінів `kind: model-provider` тобі все одно потрібно оголосити тип у маніфесті (або покластися на евристику source‑text).

Дивись [Building a Hermes Plugin](/guides/build-a-hermes-plugin#distribute-via-pip) для повного налаштування точок входу.
## Пов’язані сторінки

- [Provider Runtime](/developer-guide/provider-runtime) — пріоритет розв’язання + де кожен шар читає профіль
- [Adding Providers](/developer-guide/adding-providers) — чек‑лист від початку до кінця для нових бекендів інференсу (охоплює як швидкий шлях плагіна, так і повну інтеграцію CLI/автентифікації)
- [Memory Provider Plugins](/developer-guide/memory-provider-plugin) — Плагіни провайдера пам’яті
- [Context Engine Plugins](/developer-guide/context-engine-plugin) — Плагіни контекстного движка
- [Building a Hermes Plugin](/guides/build-a-hermes-plugin) — загальні рекомендації зі створення плагіна Hermes