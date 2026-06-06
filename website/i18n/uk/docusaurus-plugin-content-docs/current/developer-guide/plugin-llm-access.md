---
sidebar_position: 11
title: "Плагін LLM доступ"
description: "Запусти будь‑який виклик LLM всередині плагіна через ctx.llm — чат або структурований, синхронний або асинхронний. Автентифікація, що належить хосту, fail‑closed trust gate, необов’язкова валідація JSON Schema."
---

# Плагін LLM Access

`ctx.llm` — це підтримуваний спосіб для плагіна здійснити виклик LLM.
Chat completion, structured extraction, sync, async, з зображеннями чи без — один інтерфейс, один trust gate, одна хост‑власна облікова дані.

Плагіни звертаються до цього, коли потрібно виконати щось, що стосується моделі, але не є частиною розмови агента. Хук, який переписує помилку інструменту у зрозумілий для нетехнічного користувача вигляд. Адаптер шлюзу, що перекладає вхідне повідомлення перед його постановкою в чергу. Сlash‑команда, що підсумовує довге вставлення. Запланована задача, що оцінює вчорашню активність і записує один рядок у статус‑дошку. Пре‑фільтр, що вирішує, чи варто взагалі будити агента повідомленням.

Це завдання, у яких агент не повинен бути в циклі. Потрібен лише один виклик LLM, типізована відповідь і завершення роботи.
## Найменший можливий виклик

```python
result = ctx.llm.complete(messages=[{"role": "user", "content": "ping"}])
return result.text
```

Ось весь API в один рядок. Без ключів, без конфігурації провайдера, без ініціалізації SDK. Плагін працює з будь‑яким провайдером і моделлю, які користувач зараз використовує — коли він змінює провайдера, плагін автоматично слідує за ним.
## Більш повний приклад чату

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

`purpose` — це довільний рядок аудиту, який відображається у `agent.log` і в `result.audit`, щоб оператори могли бачити, який плагін виконав який виклик. Необов’язковий, але рекомендований для всіх, що часто спрацьовують.
## Структурований вивід

Коли плагіну потрібна типізована відповідь, перемикайся на структурний режим:

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

Хост запитує JSON‑вивід у провайдера, розбирає його локально
як запасний (варіант), перевіряє за твоєю схемою, якщо `jsonschema` встановлено, і повертає Python‑об’єкт у `result.parsed`. Якщо модель не змогла створити дійсний JSON, `result.parsed` дорівнює `None`, а `result.text` містить необроблену відповідь.
## Що дає цей lane

* **Один виклик, чотири форми.** `complete()` для чату,
  `complete_structured()` для типізованого JSON, `acomplete()` і
  `acomplete_structured()` для asyncio. Ті ж аргументи, ті ж об’єкти результату.
* **Облікові дані, якими керує хост.** OAuth‑токени, потоки оновлення, пул облікових даних, перезапису aux для кожного завдання — усі концепції облікових даних, які вже має Hermes, застосовуються. Плагін ніколи не бачить токен; хост атрибутує виклик назад через `result.audit`.
* **Обмежений.** Одиночний синхронний або асинхронний виклик. Без потокової передачі, без циклів інструментів, без стану розмови, який треба керувати. Вкажи вхідні дані, отримай результат, поверни його.
* **Довіра у режимі fail‑closed.** Плагін, який ти ніколи не налаштовував, не може вибрати власного провайдера, модель, агент або збережений обліковий запис. Типова поведінка — «використовуй те, що використовує користувач». Оператори можуть увімкнути конкретні перевизначення для кожного плагіна у `config.yaml`.
## Швидкий старт

Два повних плагіни нижче — один для чату, інший для структурованого. Обидва
поставляються всередині єдиної функції `register(ctx)` і не потребують
зовнішньої конфігурації, щоб працювати з будь‑якою моделлю, яку користувач
має активною.

### Чат‑комплішн — `/tldr`

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

`result.text` — це відповідь моделі; `result.usage` містить кількість токенів; `result.provider` і `result.model` містять атрибуцію.

### Структуроване вилучення — `/paste-to-tasks`

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

Третій робочий приклад, цього разу з вхідним зображенням, розташований у
репозиторії [`hermes-example-plugins`](https://github.com/NousResearch/hermes-example-plugins/tree/main/plugin-llm-example)
(додатковий репозиторій для прикладів плагінів — не входить до складу
hermes-agent). Для асинхронного інтерфейсу (`acomplete()` /
`acomplete_structured()` з `asyncio.gather()`), дивіться
[`plugin-llm-async-example`](https://github.com/NousResearch/hermes-example-plugins/tree/main/plugin-llm-async-example)
у тому ж репозиторії.
## Коли використовувати який

| Ти хочеш… | Використовуй |
|---|---|
| Відповідь у вільному тексті (переклад, резюме, переписування, генерація) | `complete()` |
| Запит з кількома ходами (system + few‑shot приклади + користувач) | `complete()` |
| Типізований `dict` у відповіді, перевірений за схемою | `complete_structured()` |
| Вхід зображення або тексту з типізованим `dict` у відповіді | `complete_structured()` |
| Той самий виклик з асинхронного коду (gateway adapters, async hooks) | `acomplete()` / `acomplete_structured()` |

Все інше — вибір провайдера, визначення моделі, автентифікація, запасний (варіант), тайм‑аут, маршрутизація візуального вводу — однакове для всіх чотирьох.
## API surface

`ctx.llm` — це екземпляр `agent.plugin_llm.PluginLlm`.

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

Просте завершення чату. `messages` має стандартну форму OpenAI — список словників `{"role": "...", "content": "..."}`. Багатокрокові підказки (system + кілька пар користувач/асистент + фінальний користувач) працюють точно так само, як у SDK OpenAI.

`provider=` і `model=` є незалежними і мають ту ж форму, що й головна конфігурація хоста (`model.provider` + `model.model`). Вкажи лише `model=` — щоб використати активного провайдера користувача з іншим моделем. Вкажи обидва, щоб повністю переключити провайдерів. Будь‑який аргумент без явного підтвердження оператором викликає `PluginLlmTrustError`.

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

Вхідними даними можуть бути текстові або зображувальні блоки (сирі байти автоматично кодуються у base64 як URL `data:`). Коли вказано `json_schema` або `json_mode=True`, хост запитує JSON‑вихід через `response_format`, локально парсить його як запасний варіант і перевіряє відповідність вашій схемі, якщо встановлено `jsonschema`.

* `result.content_type == "json"` — `result.parsed` — об’єкт Python, який відповідає вашій схемі.
* `result.content_type == "text"` — парсинг або валідація не вдалася; перегляньте `result.text` для отримання сирої відповіді моделі.

### Async

```python
result = await ctx.llm.acomplete(messages=...)
result = await ctx.llm.acomplete_structured(instructions=..., input=...)
```

Ті ж аргументи та типи результатів, що й у синхронних аналогів. Використовуй їх у шлюзових адаптерах, асинхронних хуках або будь‑якому коді плагіна, який вже працює в циклі `asyncio`.

### Result attributes

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

`usage` містить `input_tokens`, `output_tokens`, `total_tokens`, `cache_read_tokens`, `cache_write_tokens` та `cost_usd`, коли провайдер повертає ці поля.
## Ворота довіри

Типова поведінка — fail-closed. Якщо у конфігураційному блоці немає `plugins.entries`, плагін може:

* виконувати будь‑який з чотирьох методів проти активного провайдера та моделі користувача,
* задавати аргументи формування запиту (`temperature`, `max_tokens`, `timeout`, `system_prompt`, `purpose`, `messages`, `instructions`, `input`, `json_schema`),

…і це все. Аргументи `provider=`, `model=`, `agent_id=` та `profile=` викликають `PluginLlmTrustError`, доки оператор не ввімкне їх.

**Більшість плагінів цю секцію не потребують.** Плагін, який просто викликає `ctx.llm.complete(messages=…)` без перевизначень, працює проти того, що користувач має активним, і працює без налаштувань. Блок нижче має сенс лише тоді, коли плагін спеціально хоче прив’язатися до іншої моделі або провайдера, ніж у користувача.

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

Ідентифікатор плагіна — це поле `name:` у маніфесті для плоских плагінів, або ключ, отриманий з шляху, для вкладених плагінів (`image_gen/openai`, `memory/honcho` тощо).

### Що забезпечують ворота

| Перевизначення | За замовчуванням | Ключ конфігурації                |
| -------------- | ---------------- | -------------------------------- |
| `provider=`    | заборонено       | `allow_provider_override: true` |
| ↳ allowlist   | —                | `allowed_providers: [...]`       |
| `model=`       | заборонено       | `allow_model_override: true`    |
| ↳ allowlist   | —                | `allowed_models: [...]`         |
| `agent_id=`   | заборонено       | `allow_agent_id_override: true` |
| `profile=`    | заборонено       | `allow_profile_override: true`   |

Кожне перевизначення контролюється окремо. Надання `allow_model_override` **не** надає автоматично `allow_provider_override` — плагін, якому довіряють вибирати модель, все одно прив’язаний до активного провайдера користувача, якщо не отримав і доступ до воріт провайдера.

### Чого ворота НЕ повинні забезпечувати

* Аргументи формування запиту — `temperature`, `max_tokens`, `timeout`, `system_prompt`, `purpose`, `messages`, `instructions`, `input`, `json_schema`, `schema_name`, `json_mode` — завжди дозволені; вони не вибирають облікові дані чи маршрути.
* Типова політика «заперечити» означає, що непідготовлений плагін все ще може виконувати корисну роботу — він просто працює проти активного провайдера і моделі. Операторам потрібно лише думати про `plugins.entries` для плагінів, які потребують більш тонкого маршрутування.
## Що належить хосту

Повний список того, що `ctx.llm` виконує за плагін, щоб тобі не доводилося:

* **Вирішення провайдера.** Читає `model.provider` + `model.model` з конфігурації користувача (або явних перевизначень, коли довірено).
* **Авторизація.** Отримує API‑ключі, OAuth‑токени або токени оновлення з `~/.hermes/auth.json` / змінних середовища, включаючи пул облікових даних, коли він налаштований. Плагін ніколи їх не бачить.
* **Маршрутизація Vision.** Коли подається зображення і активна текстова модель користувача підтримує лише текст, хост автоматично переходить до налаштованої моделі Vision.
* **Ланцюжок запасного (варіанту).** Якщо основний провайдер користувача повертає 5xx або 429, запит проходить через звичний для Hermes агрегатор‑свідомий запасний (варіант) перед тим, як повернути помилку плагіну.
* **Тайм‑аут.** Дотримується твого аргументу `timeout=` і, за потреби, переходить до конфігурації `auxiliary.<task>.timeout` або глобального значення за замовчуванням.
* **Формування JSON.** Надсилає `response_format` провайдеру, коли ти запитуєш JSON, а потім локально повторно парсить відповідь у код‑блоці, якщо провайдер її повернув.
* **Валідація схеми.** Перевіряє відповідність `json_schema`, коли встановлено `jsonschema`; інакше записує рядок налагодження та пропускає сувору валідацію.
* **Журнал аудиту.** Кожний виклик записує один рядок INFO у `agent.log` з ідентифікатором плагіну, провайдером/моделлю, призначенням та загальною кількістю токенів.
## Що належить плагіну

* **Форма запиту.** `messages` для чату, `instructions` + `input` для структурованих запитів. Плагін формує підказку; хост її виконує.
* **Схема.** Будь‑яка форма, яку ти хочеш отримати назад. Хост не виводить її за тебе.
* **Обробка помилок.** `complete_structured()` піднімає `ValueError` при порожніх вхідних даних і при невдачі валідації схеми. `PluginLlmTrustError` спрацьовує, коли шлюз довіри відхиляє перевизначення. Будь‑що інше (провайдер 5xx, відсутні налаштовані облікові дані, тайм‑аут) піднімає те, що піднімає `auxiliary_client.call_llm()`.
* **Вартість.** Кожен виклик виконується на платному провайдері користувача. Не виконуй цикл `complete()` для кожного повідомлення шлюзу, не розмірковуючи про витрати токенів.
## Де це вписується в інтерфейс плагіна

Існуючі методи `ctx.*` розширюють підсистему Hermes:

| `ctx.register_tool` | додає інструмент, який агент може викликати |
| `ctx.register_platform` | підключає новий адаптер шлюзу |
| `ctx.register_image_gen_provider` | замінює бекенд генерації зображень |
| `ctx.register_memory_provider` | замінює бекенд пам'яті |
| `ctx.register_context_engine` | замінює компресор контексту |
| `ctx.register_hook` | спостерігає за подією життєвого циклу |

`ctx.llm` — це перший інтерфейс, який дозволяє плагіну запускати ту саму модель, з якою спілкується користувач, *поза межами* (out of band), без жодного з наведених вище. Це його єдина задача. Якщо твоєму плагіну потрібно зареєструвати інструмент, який викликає агент, використай `register_tool`. Якщо потрібно реагувати на подію життєвого циклу, використай `register_hook`. Якщо потрібно здійснити власний виклик моделі — з будь‑якої причини, структурованої чи ні — використай `ctx.lll`.
## Довідка

* Реалізація: [`agent/plugin_llm.py`](https://github.com/NousResearch/hermes-agent/blob/main/agent/plugin_llm.py)
* Тести: [`tests/agent/test_plugin_llm.py`](https://github.com/NousResearch/hermes-agent/blob/main/tests/agent/test_plugin_llm.py)
* Плагіни‑приклади (додатковий репозиторій):
  * [`plugin-llm-example`](https://github.com/NousResearch/hermes-example-plugins/tree/main/plugin-llm-example) — синхронне структуроване вилучення з вхідним зображенням
  * [`plugin-llm-async-example`](https://github.com/NousResearch/hermes-example-plugins/tree/main/plugin-llm-async-example) — асинхронно за допомогою `asyncio.gather()`
* Допоміжний клієнт (двигун під капотом): дивись
  [Runtime провайдера](/developer-guide/provider-runtime).