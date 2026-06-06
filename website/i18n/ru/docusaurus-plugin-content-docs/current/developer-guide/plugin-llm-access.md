---
sidebar_position: 11
title: "Плагин LLM доступ"
description: "Запусти любой вызов LLM изнутри плагина через `ctx.llm` — чат или структурированный, синхронный или асинхронный. Аутентификация, принадлежащая хосту, закрытый по умолчанию доверительный шлюз, опциональная проверка JSON Schema."
---

# Plugin LLM Access

`ctx.llm` — поддерживаемый способ для плагина выполнить вызов LLM.
Chat‑completion, структурированное извлечение, синхронный и асинхронный режим, с изображениями или без — одинаковый интерфейс, одинаковый шлюз доверия, одинаковые принадлежащие хосту учётные данные.

Плагины используют это, когда им нужно выполнить что‑то, связанное с моделью, но не являющееся частью разговора агента. Хук, который преобразует ошибку инструмента в понятный не‑инженеру текст. Адаптер шлюза инструментов, переводящий входящее сообщение перед постановкой в очередь. Слеш‑команда, подводящая итог длинному вставленному фрагменту. Запланированная задача, оценивающая вчерашнюю активность и записывающая одну строку в доску статуса. Предфильтр, решающий, стоит ли вообще будить агента ради сообщения.

Это задачи, в которых агент не должен участвовать. Требуется один вызов LLM, типизированный ответ — и всё.
## Наименьший возможный вызов

```python
result = ctx.llm.complete(messages=[{"role": "user", "content": "ping"}])
return result.text
```

Это весь API в одной строке. Без ключей, без конфигурации провайдера, без инициализации SDK. Плагин работает с тем провайдером и моделью, которые пользователь использует в данный момент — при переключении провайдера плагин автоматически следует за ним.
## Более полный пример чата

```python
result = ctx.llm.complete(
    messages=[
        {"role": "system", "content": "Rewrite errors as one short sentence a non-engineer can act on."},
        {"role": "user",   "content": traceback_text},
    ],
    max_tokens=64,
    purpose="hooks.error-rewrite",
)
return result.text
```

`purpose` — это строка произвольного формата аудита; она отображается в `agent.log` и в `result.audit`, чтобы операторы могли видеть, какой плагин выполнил какой вызов. Необязательно, но рекомендуется для всех часто вызываемых плагинов.
## Структурированный вывод

Когда плагину нужен типизированный ответ, переключайся на структурированный режим:

```python
result = ctx.llm.complete_structured(
    instructions="Score this support reply for urgency (0–1) and pick a category.",
    input=[{"type": "text", "text": message_body}],
    json_schema=TRIAGE_SCHEMA,
    purpose="support.triage",
    temperature=0.0,
    max_tokens=128,
)

if result.parsed["urgency"] > 0.8:
    await dispatch_to_oncall(result.parsed["category"], message_body)
```

Хост запрашивает у провайдера вывод в формате JSON, парсит его локально
как запасной вариант, проверяет по твоей схеме, если установлен `jsonschema`,
и возвращает объект Python в `result.parsed`. Если модель не смогла
сгенерировать корректный JSON, `result.parsed` будет `None`, а
`result.text` будет содержать необработанный ответ.
## Что даёт этот lane

* **Один вызов, четыре варианта.** `complete()` — для чата, `complete_structured()` — для типизированного JSON, `acomplete()` и `acomplete_structured()` — для asyncio. Те же аргументы, те же объекты‑результаты.
* **Учётные данные, принадлежащие хосту.** OAuth‑токены, потоки обновления, пул учётных данных, переопределения aux per‑task — каждая концепция учётных данных, уже присутствующая в Hermes, применяется. Плагин никогда не видит токен; хост атрибутирует вызов обратно через `result.audit`.
* **Ограниченный.** Один синхронный или асинхронный вызов. Нет потоковой передачи, нет циклов инструментов, нет состояния диалога для управления. Указываешь ввод, получаешь результат, возвращаешь.
* **Fail‑closed доверие.** Плагин, который ты никогда не настраивал, не может выбрать собственного provider, модель, агент или сохранённые учётные данные. По умолчанию используется то, что использует пользователь. Операторы могут включать конкретные переопределения для каждого плагина в `config.yaml`.
## Быстрый старт

Два готовых плагина ниже — один для чата, один для структурированного извлечения. Оба находятся внутри единственной функции `register(ctx)` и не требуют внешней конфигурации, работают с любой активной у пользователя моделью.

### Chat completion — `/tldr`

```python
def register(ctx):
    ctx.register_command(
        name="tldr",
        handler=lambda raw: _tldr(ctx, raw),
        description="Summarise the supplied text in one paragraph.",
        args_hint="<text>",
    )


def _tldr(ctx, raw_args: str) -> str:
    text = raw_args.strip()
    if not text:
        return "Usage: /tldr <text to summarise>"
    result = ctx.llm.complete(
        messages=[
            {"role": "system",
             "content": "Summarise the user's text in one tight paragraph. No preamble."},
            {"role": "user", "content": text},
        ],
        max_tokens=256,
        temperature=0.3,
        purpose="tldr",
    )
    return result.text
```

`result.text` — ответ модели; `result.usage` — количество токенов; `result.provider` и `result.model` — атрибуция.

### Structured extraction — `/paste-to-tasks`

```python
def register(ctx):
    ctx.register_command(
        name="paste-to-tasks",
        handler=lambda raw: _paste_to_tasks(ctx, raw),
        description="Turn freeform meeting notes into structured tasks.",
        args_hint="<text>",
    )


_TASKS_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "owner":  {"type": "string"},
                    "action": {"type": "string"},
                    "due":    {"type": "string", "description": "ISO date or empty"},
                },
                "required": ["action"],
            },
        },
    },
    "required": ["tasks"],
}


def _paste_to_tasks(ctx, raw_args: str) -> str:
    if not raw_args.strip():
        return "Usage: /paste-to-tasks <meeting notes>"
    result = ctx.llm.complete_structured(
        instructions=(
            "Extract concrete action items from these meeting notes. "
            "One task per actionable line. If no owner is named, leave 'owner' blank."
        ),
        input=[{"type": "text", "text": raw_args}],
        json_schema=_TASKS_SCHEMA,
        schema_name="meeting.tasks",
        purpose="paste-to-tasks",
        temperature=0.0,
        max_tokens=512,
    )
    if result.parsed is None:
        return f"Couldn't parse a response. Raw output:\n{result.text}"
    lines = [f"- [{t.get('owner') or '?'}] {t['action']}" for t in result.parsed["tasks"]]
    return "\n".join(lines) or "(no tasks found)"
```

Третий рабочий пример, на этот раз с вводом изображения, находится в репозитории
[`hermes-example-plugins`](https://github.com/NousResearch/hermes-example-plugins/tree/main/plugin-llm-example)
(дополнительный репозиторий для справочных плагинов — не включён в сам hermes-agent). Для асинхронного интерфейса (`acomplete()` / `acomplete_structured()` с `asyncio.gather()`), см. [`plugin-llm-async-example`](https://github.com/NousResearch/hermes-example-plugins/tree/main/plugin-llm-async-example) в том же репозитории.
## Когда использовать что

| Тебе нужно… | Выбирай |
|---|---|
| Свободный текстовый ответ (перевод, резюме, переписывание, генерация) | `complete()` |
| Многошаговый запрос (system + few‑shot‑примеры + user) | `complete()` |
| Словарь‑тип, проверенный по схеме | `complete_structured()` |
| Ввод изображение‑или‑текст с ответом‑словарём‑типа | `complete_structured()` |
| Тот же вызов из асинхронного кода (gateway adapters, async hooks) | `acomplete()` / `acomplete_structured()` |

Всё остальное — выбор провайдера, разрешение модели, аутентификация, запасной (вариант), тайм‑аут, маршрутизация vision — одинаково для всех четырёх.
## API‑поверхность

`ctx.llm` — это экземпляр `agent.plugin_llm.PluginLlm`.

### `complete()`

```python
result = ctx.llm.complete(
    messages=[{"role": "user", "content": "Hi"}],
    provider=None,         # optional, gated — Hermes provider id (e.g. "openrouter")
    model=None,            # optional, gated — whatever string that provider expects
    temperature=None,
    max_tokens=None,
    timeout=None,          # seconds
    agent_id=None,         # optional, gated
    profile=None,          # optional, gated — explicit auth-profile name
    purpose="optional-audit-string",
)
# → PluginLlmCompleteResult(text, provider, model, agent_id, usage, audit)
```

Простая генерация ответа в чате. `messages` имеет стандартный формат OpenAI — список словарей `{"role": "...", "content": "..."}`. Многошаговые подсказки (system + несколько пар пользователь/ассистент + финальный пользователь) работают точно так же, как в SDK OpenAI.

`provider=` и `model=` независимы и следуют той же схеме, что и основная конфигурация хоста (`model.provider` + `model.model`). Укажи только `model=` — чтобы использовать активный у пользователя провайдер с другой моделью. Укажи оба параметра — чтобы полностью переключить провайдеры. Любой из аргументов без согласия оператора вызывает `PluginLlmTrustError`.

### `complete_structured()`

```python
result = ctx.llm.complete_structured(
    instructions="What you want extracted.",
    input=[
        {"type": "text",  "text": "..."},
        {"type": "image", "data": b"...", "mime_type": "image/png"},
        {"type": "image", "url":  "https://..."},
    ],
    json_schema={...},     # optional — triggers parsed result + validation
    json_mode=False,       # set True without a schema to ask for JSON anyway
    schema_name=None,      # optional human-readable schema name
    system_prompt=None,
    provider=None,         # optional, gated
    model=None,            # optional, gated
    temperature=None,
    max_tokens=None,
    timeout=None,
    agent_id=None,
    profile=None,
    purpose=None,
)
# → PluginLlmStructuredResult(text, provider, model, agent_id,
#                             usage, parsed, content_type, audit)
```

Входные данные могут быть текстовыми или блоками изображений (сырые байты автоматически кодируются в base64 как URL `data:`). Когда передаётся `json_schema` или `json_mode=True`, хост запрашивает JSON‑вывод через `response_format`, парсит его локально как запасной (вариант) и проверяет по твоей схеме, если установлен `jsonschema`.

* `result.content_type == "json"` — `result.parsed` это объект Python, соответствующий твоей схеме.
* `result.content_type == "text"` — парсинг или проверка не удалась; смотри `result.text` для получения сырого ответа модели.

### Async

```python
result = await ctx.llm.acomplete(messages=...)
result = await ctx.llm.acomplete_structured(instructions=..., input=...)
```

Те же аргументы и типы результатов, что и у синхронных методов. Используй их в адаптерах шлюза, асинхронных хуках или любом плагин‑кода, уже работающем в цикле `asyncio`.

### Атрибуты результата

```python
@dataclass
class PluginLlmCompleteResult:
    text: str                    # the assistant's response
    provider: str                # e.g. "openrouter", "anthropic"
    model: str                   # whatever the provider returned for this call
    agent_id: str                # whose model/auth was used
    usage: PluginLlmUsage        # tokens + cache + cost estimate
    audit: Dict[str, Any]        # plugin_id, purpose, profile

@dataclass
class PluginLlmStructuredResult(PluginLlmCompleteResult):
    parsed: Optional[Any]        # JSON object when content_type == "json"
    content_type: str            # "json" or "text"
    # audit also carries schema_name when supplied
```

`usage` содержит `input_tokens`, `output_tokens`, `total_tokens`, `cache_read_tokens`, `cache_write_tokens` и `cost_usd`, если провайдер возвращает эти поля.
## Ворота доверия

Поведение по умолчанию — fail‑closed. При отсутствии блока конфигурации `plugins.entries` плагин может:

* вызывать любой из четырёх методов против активного у пользователя провайдера и модели,
* задавать аргументы формирования запроса (`temperature`, `max_tokens`, `timeout`, `system_prompt`, `purpose`, `messages`, `instructions`, `input`, `json_schema`),

…и всё. Аргументы `provider=`, `model=`, `agent_id=` и `profile=` вызывают `PluginLlmTrustError`, пока оператор явно не разрешит их.

**Большинству плагинов этот раздел не нужен.** Плагин, который просто вызывает `ctx.llm.complete(messages=…)` без переопределений, работает с тем, что у пользователя активировано, и не требует настройки. Блок ниже имеет смысл только тогда, когда плагин специально хочет привязаться к другой модели или провайдеру, отличному от пользовательского.

```yaml
plugins:
  entries:
    my-plugin:
      llm:
        # Allow this plugin to choose a different Hermes provider
        # (must be one Hermes already knows about — same names as
        # `hermes model` and config.yaml model.provider).
        allow_provider_override: true

        # Optionally restrict which providers. Use ["*"] for any.
        allowed_providers:
          - openrouter
          - anthropic

        # Allow this plugin to ask for a specific model.
        allow_model_override: true

        # Optionally restrict which models. Use ["*"] for any.
        # Models are matched literally against whatever string the
        # plugin sends — Hermes does not look anything up.
        allowed_models:
          - openai/gpt-4o-mini
          - anthropic/claude-3-5-haiku

        # Allow cross-agent calls (rare).
        allow_agent_id_override: false

        # Allow the plugin to request a specific stored auth profile
        # (e.g. a different OAuth account on the same provider).
        allow_profile_override: false
```

Идентификатор плагина — это поле манифеста `name:` для плоских плагинов или ключ, полученный из пути, для вложенных плагинов (`image_gen/openai`, `memory/honcho` и т.д.).

### Что контролируют ворота

| Переопределение | По умолчанию | Ключ конфигурации                |
| ---------------- | ------------ | -------------------------------- |
| `provider=`      | отказано     | `allow_provider_override: true`  |
| ↳ allowlist      | —            | `allowed_providers: [...]`       |
| `model=`         | отказано     | `allow_model_override: true`     |
| ↳ allowlist      | —            | `allowed_models: [...]`          |
| `agent_id=`      | отказано     | `allow_agent_id_override: true`  |
| `profile=`       | отказано     | `allow_profile_override: true`   |

Каждое переопределение контролируется независимо. Предоставление `allow_model_override` **не** подразумевает также `allow_provider_override` — плагин, которому доверяют выбирать модель, всё равно привязан к активному у пользователя провайдеру, если только не получит доступ к воротам провайдера.

### Что ворота НЕ обязаны контролировать

* Аргументы формирования запроса — `temperature`, `max_tokens`, `timeout`, `system_prompt`, `purpose`, `messages`, `instructions`, `input`, `json_schema`, `schema_name`, `json_mode` — всегда разрешены; они не выбирают учётные данные и маршруты.
* Политика отказа по умолчанию означает, что неконфигурированный плагин всё равно может выполнять полезную работу — он просто работает с активным провайдером и моделью. Операторам нужно задумываться о `plugins.entries` только для плагинов, которым требуется более тонкая маршрутизация.
## Что делает хост

Полный список того, что `ctx.llm` делает за плагин, чтобы тебе не пришлось:

* **Разрешение провайдера.** Читает `model.provider` + `model.model` из конфигурации пользователя (или из явных переопределений, когда доверено).
* **Auth.** Получает API‑ключи, OAuth‑токены или токены обновления из `~/.hermes/auth.json` / переменных окружения, включая пул учётных данных, если он сконфигурирован. Плагин их никогда не видит.
* **Vision routing.** Когда передаётся изображение, а активная текстовая модель пользователя поддерживает только текст, хост автоматически переключается на сконфигурированную модель Vision.
* **Fallback chain.** Если основной провайдер пользователя отвечает ошибкой 5xx или 429, запрос проходит через обычный агрегатор‑aware fallback Hermes перед тем, как вернуть ошибку плагину.
* **Timeout.** Учитывает твой аргумент `timeout=` и, при необходимости, переходит к конфигурации `auxiliary.<task>.timeout` или к глобальному значению aux по умолчанию.
* **JSON shaping.** Отправляет `response_format` провайдеру, когда ты запрашиваешь JSON, затем повторно разбирает локально ответ в кодовом блоке, если провайдер его вернул.
* **Schema validation.** Выполняет валидацию по твоему `json_schema`, если установлен `jsonschema`; иначе записывает строку отладки и пропускает строгую проверку.
* **Audit log.** Каждый вызов записывает одну строку INFO в `agent.log` с идентификатором плагина, провайдером/моделью, назначением и общим числом токенов.
## Что принадлежит плагину

* **Форма запроса.** `messages` для чата, `instructions` + `input` для структурированных запросов. Плагин формирует подсказку; хост её исполняет.
* **Схема.** Любая форма, которую ты хочешь получить обратно. Хост не выводит её за тебя.
* **Обработка ошибок.** `complete_structured()` генерирует `ValueError` при пустых входных данных и при ошибке проверки схемы. `PluginLlmTrustError` срабатывает, когда шлюз доверия отклоняет переопределение. В остальных случаях (ошибки провайдера 5xx, отсутствие настроенных учётных данных, тайм‑аут) генерируется то же исключение, что и `auxiliary_client.call_llm()`.
* **Стоимость.** Каждый вызов выполняется через платного провайдера пользователя. Не вызывай `complete()` в цикле для каждого сообщения шлюза, не учитывая расход токенов.
## Где это вписывается в поверхность плагина

Существующие методы `ctx.*` расширяют подсистему Hermes:

| `ctx.register_tool` | добавляет инструмент, который может вызвать агент |
| `ctx.register_platform` | подключает новый адаптер шлюза |
| `ctx.register_image_gen_provider` | заменяет бекенд генерации изображений |
| `ctx.register_memory_provider` | заменяет бекенд памяти |
| `ctx.register_context_engine` | заменяет компрессор контекста |
| `ctx.register_hook` | наблюдает за событием жизненного цикла |

`ctx.llm` — первая поверхность, позволяющая плагину запускать ту же модель, с которой разговаривает пользователь, *вне канала*, без каких‑либо из перечисленных выше. Это её единственная задача. Если твоему плагину нужно зарегистрировать инструмент, вызываемый агентом, используй `register_tool`. Если нужно отреагировать на событие жизненного цикла, используй `register_hook`. Если требуется выполнить собственный вызов модели — по любой причине, структурированный или нет — используй `ctx.llm`.
## Справка

* Реализация: [`agent/plugin_llm.py`](https://github.com/NousResearch/hermes-agent/blob/main/agent/plugin_llm.py)
* Тесты: [`tests/agent/test_plugin_llm.py`](https://github.com/NousResearch/hermes-agent/blob/main/tests/agent/test_plugin_llm.py)
* Справочные плагины (репозиторий‑компаньон):
  * [`plugin-llm-example`](https://github.com/NousResearch/hermes-example-plugins/tree/main/plugin-llm-example) — синхронное структурированное извлечение с вводом изображения
  * [`plugin-llm-async-example`](https://github.com/NousResearch/hermes-example-plugins/tree/main/plugin-llm-async-example) — асинхронный пример с `asyncio.gather()`
* Вспомогательный клиент (движок под капотом): см. [Provider Runtime](/developer-guide/provider-runtime).