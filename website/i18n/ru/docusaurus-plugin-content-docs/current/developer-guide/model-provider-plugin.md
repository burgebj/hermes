---
sidebar_position: 10
title: "Плагины поставщика модели"
description: "Как создать плагин провайдера модели (backend вывода) для Hermes Agent"
---

# Создание плагина провайдера модели

Плагины провайдера модели объявляют бэкенд инференса — совместимую с OpenAI конечную точку, сервер Anthropic Messages, API ответов в стиле Codex или нативный интерфейс Bedrock, через который Hermes может маршрутизировать вызовы `AIAgent`. Каждый встроенный провайдер (OpenRouter, Anthropic, GMI, DeepSeek, Nvidia, …) поставляется в виде одного из этих плагинов. Сторонние разработчики могут добавить свои, разместив каталог в `$HERMES_HOME/plugins/model-providers/` без каких‑либо изменений в репозитории.

:::tip
Плагины провайдера модели — это третий тип **плагина провайдера**. Другие типы — [Плагины провайдера памяти](/developer-guide/memory-provider-plugin) (знания между сессиями) и [Плагины контекстного движка](/developer-guide/context-engine-plugin) (стратегии сжатия контекста). Все три следуют одному и тому же шаблону: «размести каталог, объяви профиль, без правок репозитория».
:::
## Как работает обнаружение

`providers/__init__.py._discover_providers()` выполняется лениво при первом вызове `get_provider_profile()` или `list_providers()`. Порядок обнаружения:

1. **Встроенные плагины** — `<repo>/plugins/model-providers/<name>/` — поставляются с Hermes
2. **Пользовательские плагины** — `$HERMES_HOME/plugins/model-providers/<name>/` — можно разместить в любом каталоге; перезапуск не требуется для последующих сессий
3. **Устаревший однофайловый провайдер** — `<repo>/providers/<name>.py` — совместимость с установками вне дерева исходников

**Пользовательские плагины переопределяют встроенные плагины с тем же именем**, потому что `register_provider()` работает по принципу «последний записал — победил». Размести каталог `$HERMES_HOME/plugins/model-providers/gmi/`, чтобы заменить встроенный профиль GMI, не меняя репозиторий.
## Структура каталогов

```
plugins/model-providers/my-provider/
├── __init__.py       # Calls register_provider(profile) at module-level
├── plugin.yaml       # kind: model-provider + metadata (optional but recommended)
└── README.md         # Setup instructions (optional)
```

Единственный обязательный файл — `__init__.py`. `plugin.yaml` используется `hermes plugins` для интроспекции и общим PluginManager — для маршрутизации плагина к нужному загрузчику; без него общий загрузчик переходит к эвристике исходного текста.
## Минимальный пример — простой провайдер API‑ключа

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

Вот и всё. После размещения этих двух файлов происходит **автоподключение** без каких‑либо дополнительных правок:

| Интеграция | Где | Что получает |
|---|---|---|
| Разрешение учётных данных | `hermes_cli/auth.py` | `PROVIDER_REGISTRY["acme-inference"]` заполняется из профиля |
| Флаг CLI `--provider` | `hermes_cli/main.py` | Принимает `acme-inference` |
| Выбор модели `hermes model` | `hermes_cli/models.py` | Появляется в `CANONICAL_PROVIDERS`, список моделей получаемый из `{base_url}/models` |
| `hermes doctor` | `hermes_cli/doctor.py` | Проверка состояния для `ACME_API_KEY` + проверка `{base_url}/models` |
| `hermes setup` | `hermes_cli/config.py` | `ACME_API_KEY` появляется в `OPTIONAL_ENV_VARS` и в мастере настройки |
| Обратное сопоставление URL | `agent/model_metadata.py` | Имя хоста → имя провайдера для автоматического определения |
| Вспомогательная модель | `agent/auxiliary_client.py` | Использует `default_aux_model` для сжатия/суммирования |
| Разрешение во время выполнения | `hermes_cli/runtime_provider.py` | Возвращает корректные `base_url`, `api_key`, `api_mode` |
| Транспорт | `agent/transports/chat_completions.py` | Путь профиля генерирует kwargs через `prepare_messages` / `build_extra_body` / `build_api_kwargs_extras` |
## Поля ProviderProfile

Полное определение в `providers/base.py`. Самые полезные:

| Поле | Тип | Назначение |
|---|---|---|
| `name` | str | Канонический идентификатор — соответствует `model.provider` в `config.yaml` и флагу `--provider` |
| `aliases` | `tuple[str, ...]` | Альтернативные имена, разрешаемые `get_provider_profile()` (например, `grok` → `xai`) |
| `api_mode` | str | `chat_completions` \| `codex_responses` \| `anthropic_messages` \| `bedrock_converse` |
| `display_name` | str | Человекочитаемая метка, отображаемая в выборе `hermes model` |
| `description` | str | Подзаголовок в выборе |
| `signup_url` | str | Показывается при первой настройке («получить API‑ключ здесь») |
| `env_vars` | `tuple[str, ...]` | Переменные окружения с API‑ключом в порядке приоритета; окончательная запись `*_BASE_URL` используется как переопределение базового URL пользователя |
| `base_url` | str | URL конечной точки по умолчанию |
| `models_url` | str | Явный URL каталога (по умолчанию `{base_url}/models`) |
| `auth_type` | str | `api_key` \| `oauth_device_code` \| `oauth_external` \| `copilot` \| `aws_sdk` \| `external_process` |
| `fallback_models` | `tuple[str, ...]` | Курируемый список, показываемый при ошибке получения живого каталога |
| `default_headers` | `dict[str, str]` | Отправляются в каждом запросе (например, `Editor-Version` у Copilot) |
| `fixed_temperature` | Any | `None` = использовать значение вызывающего; `OMIT_TEMPERATURE` — специальный маркер, не отправлять температуру вовсе (Kimi) |
| `default_max_tokens` | `int \| None` | Ограничение `max_tokens` на уровне провайдера (Nvidia: 16384) |
| `default_aux_model` | str | Дешёвая модель для вспомогательных задач (сжатие, зрение, суммирование) |
## Переопределяемые хуки

Создай подкласс `ProviderProfile` для нетривиальных особенностей:

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
## Примеры справки по хукам

Обрати внимание на эти встроенные плагины‑идиомы:

| Плагин | Для чего |
|---|---|
| `plugins/model-providers/openrouter/` | Агрегатор с предпочтениями провайдера, публичный каталог моделей |
| `plugins/model-providers/gemini/` | Перевод `thinking_config` (родные + вложенные формы, совместимые с OpenAI) |
| `plugins/model-providers/kimi-coding/` | `OMIT_TEMPERATURE`, `extra_body.thinking`, `reasoning_effort` верхнего уровня |
| `plugins/model-providers/qwen-oauth/` | Нормализация сообщений, внедрение `cache_control`, VL‑high‑res |
| `plugins/model-providers/nous/` | Теги атрибуции, «не выполнять рассуждение, если отключено» |
| `plugins/model-providers/custom/` | Особенности Ollama: `num_ctx` + `think: false` |
| `plugins/model-providers/bedrock/` | `api_mode="bedrock_converse"`, `fetch_models` возвращает `None` (нет REST‑конечного пункта) |
## Переопределения пользователем — заменяем встроенный элемент без изменения репозитория

Скажем, ты хочешь направить `gmi` на свой приватный staging‑endpoint для тестирования. Создай файл `~/.hermes/plugins/model-providers/gmi/__init__.py`:

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

В следующей сессии `get_provider_profile("gmi").base_url` вернёт URL staging‑окружения. Без патча репозитория, без пересборки. Поскольку пользовательские плагины обнаруживаются после встроенных, вызов `register_provider()` от пользователя имеет приоритет.
## Выбор api_mode

Распознаются четыре значения. Hermes выбирает одно на основе:

1. Явного переопределения пользователем (`config.yaml` `model.api_mode`, если задано)
2. Диспетчеризации OpenCode для каждой модели (`opencode_model_api_mode` для Zen и Go)
3. Автоматического определения URL — суффикс `/anthropic` → `anthropic_messages`, `api.openai.com` → `codex_responses`, `api.x.ai` → `codex_responses`, `/coding` на доменах Kimi → `chat_completions`
4. **Profile `api_mode`** как запасной вариант, когда определение URL ничего не нашло
5. Значение по умолчанию `chat_completions`

Установи `profile.api_mode`, чтобы он соответствовал значению по умолчанию, которое предоставляет твой провайдер — это служит подсказкой. Переопределения URL от пользователя по‑прежнему имеют приоритет.
## Типы аутентификации

| `auth_type` | Значение | Кто использует |
|---|---|---|
| `api_key` | Одна переменная окружения содержит статический API‑ключ | Большинство провайдеров |
| `oauth_device_code` | OAuth‑поток с кодом устройства | — |
| `oauth_external` | Пользователь аутентифицируется в другом месте, токены попадают в `auth.json` | Anthropic OAuth, MiniMax OAuth, Gemini Cloud Code, Qwen Portal, Nous Portal |
| `copilot` | Цикл обновления токена GitHub Copilot | только плагин `copilot` |
| `aws_sdk` | Цепочка учётных данных AWS SDK (IAM‑роль, профиль, переменные окружения) | только плагин `bedrock` |
| `external_process` | Аутентификация обрабатывается подпроцессом, который запускает агент | только плагин `copilot-acp` |

`auth_type` определяет, какие ветки кода рассматривают твой провайдер как «простой провайдер с API‑ключом» — если значение не `api_key`, PluginManager всё равно сохраняет манифест, но автоматизация уровня CLI Hermes (проверки doctor, флаг `--provider`, делегирование мастером настройки) может его пропустить.
## Время обнаружения

Обнаружение провайдера **ленивое** — оно запускается при первом вызове `get_provider_profile()` или `list_providers()` в ходе выполнения. На практике это происходит сразу при старте (загрузка модуля `auth.py` сразу заполняет `PROVIDER_REGISTRY`). Если нужно убедиться, что плагин загрузился, выполни:

```bash
hermes doctor
```

— в разделе **Provider Connectivity** появится успешный профиль `auth_type="api_key"` с проверкой `/models`.

Для программного осмотра:

```python
from providers import list_providers
for p in list_providers():
    print(p.name, p.base_url, p.api_mode)
```
## Тестирование твоего плагина

Укажи `HERMES_HOME` на временный каталог, чтобы не загрязнять реальную конфигурацию:

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
## Общая интеграция PluginManager

Общий `PluginManager` (объект, с которым работает `hermes plugins`) **обнаруживает** плагины‑поставщики моделей, но не импортирует их — за их жизненный цикл отвечает `providers/__init__.py`. Менеджер сохраняет манифест для интроспекции и классифицирует их по `kind: model-provider`. Когда ты помещаешь непомеченный пользовательский плагин в `$HERMES_HOME/plugins/`, который вызывает `register_provider` с `ProviderProfile`, менеджер автоматически приводит его к `kind: model-provider` с помощью эвристики исходного текста — так плагин всё равно будет правильно маршрутизирован даже без `plugin.yaml`.
## Распространение через pip

Как и любой плагин Hermes, поставщики моделей могут поставляться в виде пакета pip. Добавь точку входа в свой `pyproject.toml`:

```toml
[project.entry-points."hermes.plugins"]
acme-inference = "acme_hermes_plugin:register"
```

…где `acme_hermes_plugin:register` — это функция, вызывающая `register_provider(profile)`. Общий PluginManager обнаруживает плагины‑точки входа во время `discover_and_load()`. Для pip‑плагинов `kind: model-provider` всё равно необходимо объявить `kind` в манифесте (или полагаться на эвристику исходного текста).

См. [Building a Hermes Plugin](/guides/build-a-hermes-plugin#distribute-via-pip) для полной настройки точек входа.
## Связанные страницы

- [Provider Runtime](/developer-guide/provider-runtime) — приоритет разрешения + где каждый слой читает профиль
- [Adding Providers](/developer-guide/adding-providers) — чек‑лист от начала до конца для новых бекендов инференса (охватывает как быстрый путь плагина, так и полную интеграцию CLI/аутентификации)
- [Memory Provider Plugins](/developer-guide/memory-provider-plugin)
- [Context Engine Plugins](/developer-guide/context-engine-plugin)
- [Building a Hermes Plugin](/guides/build-a-hermes-plugin) — общее руководство по созданию плагинов