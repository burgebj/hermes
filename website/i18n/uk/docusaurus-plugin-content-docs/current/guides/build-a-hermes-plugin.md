---
sidebar_position: 9
sidebar_label: "Build a Plugin"
title: "Створити плагін Hermes"
description: "Покроковий посібник зі створення повного плагіна Hermes з інструментами, хуками, файлами даних та навичками"
---

# Створити плагін Hermes

Цей посібник крок за кроком показує, як створити повний плагін Hermes з нуля. Після завершення у тебе буде працюючий плагін з кількома інструментами, хуками життєвого циклу, доставленими файлами даних та упакованим skill — усе, що підтримує система плагінів.

:::info Не впевнений, який посібник тобі потрібен?
Hermes має кілька різних підключуваних інтерфейсів — деякі використовують Python `register_*` API, інші керуються конфігурацією або просто підключаються як каталоги. Спочатку скористайся цією картою:

| Якщо ти хочеш додати… | Читати |
|---|---|
| Власні інструменти, хуки, slash‑команди, skills або підкоманди CLI | **Цей посібник** (загальна поверхня плагіна) |
| **LLM / inference backend** (новий provider) | [Model Provider Plugins](/developer-guide/model-provider-plugin) |
| **gateway channel** (Discord/Telegram/IRC/Teams/тощо) | [Adding Platform Adapters](/developer-guide/adding-platform-adapters) |
| **memory backend** (Honcho/Mem0/Supermemory/тощо) | [Memory Provider Plugins](/developer-guide/memory-provider-plugin) |
| **context‑compression engine** | [Context Engine Plugins](/developer-guide/context-engine-plugin) |
| **image‑generation backend** | [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin) |
| **video‑generation backend** | [Video Generation Provider Plugins](/developer-guide/video-gen-provider-plugin) |
| **TTS backend** (будь‑яка CLI — Piper, VoxCPM, Kokoro, voice cloning, …) | [TTS custom command providers](/user-guide/features/tts#custom-command-providers) — керується конфігурацією, Python не потрібен |
| **STT backend** (власний whisper / ASR CLI) | [Voice Message Transcription](/user-guide/features/tts#voice-message-transcription-stt) — встанови `HERMES_LOCAL_STT_COMMAND` у шаблон shell |
| **External tools via MCP** (filesystem, GitHub, Linear, будь‑який MCP‑сервер) | [MCP](/user-guide/features/mcp) — оголоси `mcp_servers.<name>` у `config.yaml` |
| **Gateway event hooks** (виконуються під час запуску, подій сесії, команд) | [Event Hooks](/user-guide/features/hooks#gateway-event-hooks) — поклади `HOOK.yaml` + `handler.py` у `~/.hermes/hooks/<name>/` |
| **Shell hooks** (виконати shell‑команду під час подій) | [Shell Hooks](/user-guide/features/hooks#shell-hooks) — оголоси під `hooks:` у `config.yaml` |
| **Additional skill sources** (власні репозиторії GitHub, приватні індекси skill) | [Skills](/user-guide/features/skills) — `hermes skills tap add <repo>` · [Publishing a tap](/user-guide/features/skills#publishing-a-custom-skill-tap) |
| Першокласний **core** inference provider (не плагін) | [Adding Providers](/developer-guide/adding-providers) |

Переглянь повну [Pluggable interfaces table](/user-guide/features/plugins#pluggable-interfaces--where-to-go-for-each) для консолідованого огляду всіх точок розширення, включаючи конфігураційно‑керовані (TTS, STT, MCP, shell hooks) та каталоги‑підключення (gateway hooks).:::
## Що ти створюєш

Плагін **calculator** з двома інструментами:
- `calculate` — обчислює математичні вирази (`2**16`, `sqrt(144)`, `pi * 5**2`)
- `unit_convert` — конвертує між одиницями вимірювання (`100 F → 37.78 C`, `5 km → 3.11 mi`)

Плюс хук, який логує кожен виклик інструменту, і вбудований файл **skill**.
## Крок 1: Створити каталог плагіну

```bash
mkdir -p ~/.hermes/plugins/calculator
cd ~/.hermes/plugins/calculator
```
## Крок 2: Напиши маніфест

Створи `plugin.yaml`:

```yaml
name: calculator
version: 1.0.0
description: Math calculator — evaluate expressions and convert units
provides_tools:
  - calculate
  - unit_convert
provides_hooks:
  - post_tool_call
```

Це повідомляє Hermes: «Я плагін під назвою calculator, я надаю інструменти та хуки». Поля `provides_tools` і `provides_hooks` — це списки того, що реєструє плагін.

Необов’язкові поля, які можна додати:
```yaml
author: Your Name
requires_env:          # gate loading on env vars; prompted during install
  - SOME_API_KEY       # simple format — plugin disabled if missing
  - name: OTHER_KEY    # rich format — shows description/url during install
    description: "Key for the Other service"
    url: "https://other.com/keys"
    secret: true
```
## Крок 3: Створи схеми інструментів

Створи `schemas.py` — це те, що LLM читає, щоб вирішити, коли викликати твої інструменти:

```python
"""Tool schemas — what the LLM sees."""

CALCULATE = {
    "name": "calculate",
    "description": (
        "Evaluate a mathematical expression and return the result. "
        "Supports arithmetic (+, -, *, /, **), functions (sqrt, sin, cos, "
        "log, abs, round, floor, ceil), and constants (pi, e). "
        "Use this for any math the user asks about."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate (e.g., '2**10', 'sqrt(144)')",
            },
        },
        "required": ["expression"],
    },
}

UNIT_CONVERT = {
    "name": "unit_convert",
    "description": (
        "Convert a value between units. Supports length (m, km, mi, ft, in), "
        "weight (kg, lb, oz, g), temperature (C, F, K), data (B, KB, MB, GB, TB), "
        "and time (s, min, hr, day)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "value": {
                "type": "number",
                "description": "The numeric value to convert",
            },
            "from_unit": {
                "type": "string",
                "description": "Source unit (e.g., 'km', 'lb', 'F', 'GB')",
            },
            "to_unit": {
                "type": "string",
                "description": "Target unit (e.g., 'mi', 'kg', 'C', 'MB')",
            },
        },
        "required": ["value", "from_unit", "to_unit"],
    },
}
```

**Чому схеми важливі:** Поле `description` — це те, за чим LLM вирішує, коли використовувати твій інструмент. Будь конкретним щодо того, що він робить і коли його слід застосовувати. `parameters` визначають, які аргументи передає LLM.
## Крок 4: Створи обробники інструментів

Створи `tools.py` — це код, який фактично виконується, коли LLM викликає твої інструменти:

```python
"""Tool handlers — the code that runs when the LLM calls each tool."""

import json
import math

# Safe globals for expression evaluation — no file/network access
_SAFE_MATH = {
    "abs": abs, "round": round, "min": min, "max": max,
    "pow": pow, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
    "tan": math.tan, "log": math.log, "log2": math.log2, "log10": math.log10,
    "floor": math.floor, "ceil": math.ceil,
    "pi": math.pi, "e": math.e,
    "factorial": math.factorial,
}


def calculate(args: dict, **kwargs) -> str:
    """Evaluate a math expression safely.

    Rules for handlers:
    1. Receive args (dict) — the parameters the LLM passed
    2. Do the work
    3. Return a JSON string — ALWAYS, even on error
    4. Accept **kwargs for forward compatibility
    """
    expression = args.get("expression", "").strip()
    if not expression:
        return json.dumps({"error": "No expression provided"})

    try:
        result = eval(expression, {"__builtins__": {}}, _SAFE_MATH)
        return json.dumps({"expression": expression, "result": result})
    except ZeroDivisionError:
        return json.dumps({"expression": expression, "error": "Division by zero"})
    except Exception as e:
        return json.dumps({"expression": expression, "error": f"Invalid: {e}"})


# Conversion tables — values are in base units
_LENGTH = {"m": 1, "km": 1000, "mi": 1609.34, "ft": 0.3048, "in": 0.0254, "cm": 0.01}
_WEIGHT = {"kg": 1, "g": 0.001, "lb": 0.453592, "oz": 0.0283495}
_DATA = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
_TIME = {"s": 1, "ms": 0.001, "min": 60, "hr": 3600, "day": 86400}


def _convert_temp(value, from_u, to_u):
    # Normalize to Celsius
    c = {"F": (value - 32) * 5/9, "K": value - 273.15}.get(from_u, value)
    # Convert to target
    return {"F": c * 9/5 + 32, "K": c + 273.15}.get(to_u, c)


def unit_convert(args: dict, **kwargs) -> str:
    """Convert between units."""
    value = args.get("value")
    from_unit = args.get("from_unit", "").strip()
    to_unit = args.get("to_unit", "").strip()

    if value is None or not from_unit or not to_unit:
        return json.dumps({"error": "Need value, from_unit, and to_unit"})

    try:
        # Temperature
        if from_unit.upper() in {"C","F","K"} and to_unit.upper() in {"C","F","K"}:
            result = _convert_temp(float(value), from_unit.upper(), to_unit.upper())
            return json.dumps({"input": f"{value} {from_unit}", "result": round(result, 4),
                             "output": f"{round(result, 4)} {to_unit}"})

        # Ratio-based conversions
        for table in (_LENGTH, _WEIGHT, _DATA, _TIME):
            lc = {k.lower(): v for k, v in table.items()}
            if from_unit.lower() in lc and to_unit.lower() in lc:
                result = float(value) * lc[from_unit.lower()] / lc[to_unit.lower()]
                return json.dumps({"input": f"{value} {from_unit}",
                                 "result": round(result, 6),
                                 "output": f"{round(result, 6)} {to_unit}"})

        return json.dumps({"error": f"Cannot convert {from_unit} → {to_unit}"})
    except Exception as e:
        return json.dumps({"error": f"Conversion failed: {e}"})
```

**Ключові правила для обробників:**
1. **Сигнатура:** `def my_handler(args: dict, **kwargs) -> str`
2. **Повернення:** Завжди рядок JSON. І успіхи, і помилки.
3. **Ніколи не піднімати виключення:** Перехоплюй усі виключення, повертаючи JSON‑помилку.
4. **Приймати `**kwargs`:** Hermes може передавати додатковий контекст у майбутньому.
## Крок 5: Напиши реєстрацію

Створи `__init__.py` — це підключає схеми до обробників:

```python
"""Calculator plugin — registration."""

import logging

from . import schemas, tools

logger = logging.getLogger(__name__)

# Track tool usage via hooks
_call_log = []

def _on_post_tool_call(tool_name, args, result, task_id, **kwargs):
    """Hook: runs after every tool call (not just ours)."""
    _call_log.append({"tool": tool_name, "session": task_id})
    if len(_call_log) > 100:
        _call_log.pop(0)
    logger.debug("Tool called: %s (session %s)", tool_name, task_id)


def register(ctx):
    """Wire schemas to handlers and register hooks."""
    ctx.register_tool(name="calculate",    toolset="calculator",
                      schema=schemas.CALCULATE,    handler=tools.calculate)
    ctx.register_tool(name="unit_convert", toolset="calculator",
                      schema=schemas.UNIT_CONVERT, handler=tools.unit_convert)

    # This hook fires for ALL tool calls, not just ours
    ctx.register_hook("post_tool_call", _on_post_tool_call)
```

**Що робить `register()`:**
- Викликається точно один раз під час запуску
- `ctx.register_tool()` розміщує твій інструмент у реєстрі — модель бачить його одразу
- `ctx.register_hook()` підписується на події життєвого циклу
- `ctx.register_cli_command()` реєструє підкоманду CLI (наприклад `hermes my-plugin <subcommand>`)
- `ctx.register_command()` реєструє slash‑команду у сесії (наприклад `/myplugin <args>` у чаті CLI / gateway) — дивись розділ [Register slash commands](#register-slash-commands) нижче
- `ctx.dispatch_tool(name, arguments)` — викликає будь‑який інший інструмент (вбудований або з іншого плагіна) з контекстом батьківського агента (згоди, пул облікових даних, task_id), підключеним автоматично. Корисно в обробниках slash‑команд, які потребують виклику `terminal`, `read_file` або будь‑якого іншого інструмента, ніби модель викликала його безпосередньо.
- Якщо ця функція викликає помилку, плагін вимикається, але Hermes продовжує працювати нормально

**Приклад `dispatch_tool` — slash‑команда, що запускає інструмент:**

```python
def handle_scan(ctx, argstr):
    """Implement /scan by invoking the terminal tool through the registry."""
    result = ctx.dispatch_tool("terminal", {"command": f"find . -name '{argstr}'"})
    return result  # returned to the caller's chat UI

def register(ctx):
    ctx.register_command("scan", handle_scan, help="Find files matching a glob")
```

Відправлений інструмент проходить через звичайні процеси затвердження, редагування та бюджету — це реальний виклик інструмента, а не обхід цих процесів.
## Крок 6: Перевір це

Запусти Hermes:

```bash
hermes
```

Ти маєш побачити `calculator: calculate, unit_convert` у списку інструментів банера.

Спробуй ці підказки:
```
What's 2 to the power of 16?
Convert 100 fahrenheit to celsius
What's the square root of 2 times pi?
How many gigabytes is 1.5 terabytes?
```

Перевір статус плагіна:
```
/plugins
```

Вивід:
```
Plugins (1):
  ✓ calculator v1.0.0 (2 tools, 1 hooks)
```

### Налагодження виявлення плагінів

Якщо твій плагін не з’являється — або з’являється, але не завантажується — встанови `HERMES_PLUGINS_DEBUG=1`, щоб отримати докладні логи виявлення у stderr:

```bash
HERMES_PLUGINS_DEBUG=1 hermes plugins list
```

Ти побачиш, для кожного джерела плагіна (bundled, user, project, entry‑points):

- які каталоги сканувалися і скільки маніфестів кожен з них повернув
- для кожного маніфесту: розв’язаний ключ, назва, тип, джерело, шлях на диску
- причини пропуску: `disabled via config`, `not enabled in config`, `exclusive plugin`, `no plugin.yaml, depth cap reached`
- при завантаженні: імпортований плагін, плюс однорядковий підсумок того, що `register(ctx)` зареєстрував (інструменти, хуки, slash‑команди, CLI‑команди)
- при помилці парсингу: повний traceback виключення (помилки сканера YAML тощо)
- при помилці `register()`: повний traceback, що вказує на рядок у твоєму `__init__.py`, який викликав помилку

Ті ж логи завжди записуються у `~/.hermes/logs/agent.log` на рівні **WARNING** (лише помилки) та **DEBUG** (усе), коли встановлена змінна оточення. Тож якщо ти не можеш запустити з цією змінною (наприклад, всередині шлюзу), переглянь файл логу:

```bash
hermes logs --level WARNING | grep -i plugin
```

Типові причини, чому плагін не з’являється:

- **Not enabled in config** — плагіни підключаються за бажанням. Виконай `hermes plugins enable <name>` (назва береться з виводу `plugins list`, який може мати вигляд `<category>/<plugin>` для вкладених структур).
- **Wrong directory layout** — має бути `~/.hermes/plugins/<plugin-name>/plugin.yaml` (плоска) або `~/.hermes/plugins/<category>/<plugin-name>/plugin.yaml` (один рівень вкладеності категорії, максимум). Все, що глибше, ігнорується.
- **Missing __init__.py** — у каталозі плагіна мають бути і `plugin.yaml`, і `__init__.py` з функцією `register(ctx)`.
- **Wrong kind** — адаптери шлюзу потребують `kind: platform` у їхньому маніфесті. Провайдери пам’яті автоматично визначаються як `kind: exclusive` і маршрутизуються через конфіг `memory.provider`, а не `plugins.enabled`.
## Остаточна структура вашого плагіна

```
~/.hermes/plugins/calculator/
├── plugin.yaml      # "I'm calculator, I provide tools and hooks"
├── __init__.py      # Wiring: schemas → handlers, register hooks
├── schemas.py       # What the LLM reads (descriptions + parameter specs)
└── tools.py         # What runs (calculate, unit_convert functions)
```

Four files, clear separation:
- **Manifest** оголошує, що це за плагін
- **Schemas** описують інструменти для LLM
- **Handlers** реалізують фактичну логіку
- **Registration** з’єднує все
## Що ще вміють робити плагіни?
### Файли даних корабля

Помісти будь‑які файли у каталог плагіна та читай їх під час імпорту:

```python
# In tools.py or __init__.py
from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_DATA_FILE = _PLUGIN_DIR / "data" / "languages.yaml"

with open(_DATA_FILE) as f:
    _DATA = yaml.safe_load(f)
```
### Пакет навичок

Плагіни можуть постачати файли навичок, які агент завантажує через `skill_view("plugin:skill")`. Зареєструй їх у своєму `__init__.py`:

```
~/.hermes/plugins/my-plugin/
├── __init__.py
├── plugin.yaml
└── skills/
    ├── my-workflow/
    │   └── SKILL.md
    └── my-checklist/
        └── SKILL.md
```

```python
from pathlib import Path

def register(ctx):
    skills_dir = Path(__file__).parent / "skills"
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            ctx.register_skill(child.name, skill_md)
```

Тепер агент може завантажити твої навички за їх іменем у просторі імен:

```python
skill_view("my-plugin:my-workflow")   # → plugin's version
skill_view("my-workflow")              # → built-in version (unchanged)
```

**Ключові властивості:**
- Навички плагінів є **тільки для читання** — вони не потрапляють у `~/.hermes/skills/` і їх не можна редагувати через `skill_manage`.
- Навички плагінів **не** включені до індексу `<available_skills>` у системному підказці — їх потрібно явно завантажити.
- Одиночні назви навичок залишаються без змін — простір імен запобігає конфліктам із вбудованими навичками.
- Коли агент завантажує навичку плагіна, перед нею додається банер контексту пакету, що перераховує суміжні навички того ж плагіна.

:::tip Legacy pattern
Старий шаблон `shutil.copy2` (копіювання навички у `~/.hermes/skills/`) все ще працює, але створює ризик конфлікту імен з вбудованими навичками. Для нових плагінів віддавай перевагу `ctx.register_skill()`.
:::
### Шлюз на змінних середовища

Якщо твоєму плагіну потрібен API‑ключ:

```yaml
# plugin.yaml — simple format (backwards-compatible)
requires_env:
  - WEATHER_API_KEY
```

Якщо `WEATHER_API_KEY` не встановлено, плагін вимикається з чітким повідомленням. Ніяких збоїв, жодних помилок у агенті — лише «Plugin weather disabled (missing: WEATHER_API_KEY)».

Коли користувачі виконують `hermes plugins install`, їх **запитують інтерактивно** про будь‑які відсутні змінні `requires_env`. Значення зберігаються у файл `.env` автоматично.

Для кращого досвіду встановлення використай розширений формат із описами та URL‑адресами реєстрації:

```yaml
# plugin.yaml — rich format
requires_env:
  - name: WEATHER_API_KEY
    description: "API key for OpenWeather"
    url: "https://openweathermap.org/api"
    secret: true
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Назва змінної середовища |
| `description` | No | Показується користувачеві під час запиту встановлення |
| `url` | No | Де отримати облікові дані |
| `secret` | No | Якщо `true`, ввід приховується (як поле пароля) |

Обидва формати можна змішувати в одному списку. Вже встановлені змінні пропускаються без повідомлень.
### Ліниве встановлення необов’язкових Python‑залежностей

Якщо твій плагін обгортає SDK, який не кожен користувач має встановленим (vendor SDK, важка ML‑бібліотека, пакет, специфічний для платформи), не `import` його у верхній частині модуля. Використай допоміжну функцію `tools.lazy_deps.ensure(...)` всередині обробника інструмента — Hermes встановить пакет при першому використанні, згідно з конфігурацією користувача `security.allow_lazy_installs`.

```python
# tools.py
from tools.lazy_deps import ensure, FeatureUnavailable

def my_tool_handler(args, **kwargs):
    try:
        ensure("my-plugin.my-backend")   # key must be in LAZY_DEPS
    except FeatureUnavailable as exc:
        return {"error": str(exc)}

    import my_backend_sdk   # safe now
    ...
```

Два правила моделі безпеки у `tools/lazy_deps.py`:

| Rule | Why |
|---|---|
| Your feature key must appear in the in-tree `LAZY_DEPS` allowlist | Запобігає тому, щоб зловмисна конфігурація змусила Hermes встановити довільні пакети — лише специфікації, які постачається сам Hermes, можуть бути встановлені |
| Specs are PyPI-by-name only | Не допускаються `--index-url`, `git+https://` чи шляхи `file:`. Фіксуй версії за допомогою PEP 440 (`"my-sdk>=1.2,<2"`) у записі allowlist |

Для сторонніх плагінів, розповсюджуваних через pip, оголоси необов’язкові залежності як extras `[project.optional-dependencies]` у власному `pyproject.toml` і попроси користувачів виконати `pip install your-plugin[backend]` — цей шлях не проходить через `lazy_deps`. Ліниве встановлення найкорисніше для **bundled** плагінів, коли жорстка залежність у кожному встановленні збільшувала б базовий розмір Hermes.

Коли `security.allow_lazy_installs: false` встановлено глобально, `ensure()` одразу піднімає `FeatureUnavailable` з підказкою щодо виправлення — твій плагін має перехопити це і деградувати плавно (повернути результат помилки, а не падати у циклі інструмента).
### Умовна доступність інструментів

Для інструментів, які залежать від необов’язкових бібліотек:

```python
ctx.register_tool(
    name="my_tool",
    schema={...},
    handler=my_handler,
    check_fn=lambda: _has_optional_lib(),  # False = tool hidden from model
)
```
### Перевизначення вбудованого інструменту

Щоб замінити вбудований інструмент власною реалізацією (наприклад, замінити інструмент браузера за замовчуванням на бекенд headed‑Chrome CDP або замінити `web_search` на власний корпоративний індекс), передай `override=True`:

```python
def register(ctx):
    ctx.register_tool(
        name="browser_navigate",             # same name as the built-in
        toolset="plugin_my_browser",         # your own toolset namespace
        schema={...},
        handler=my_custom_navigate,
        override=True,                       # explicit opt-in
    )
```

Без `override=True` реєстр відхиляє будь‑яку реєстрацію, яка могла б перекрити існуючий інструмент з іншого набору інструментів — це запобігає випадковим перезаписам. Перевизначення записується на рівні INFO, тому його можна відстежити у `~/.hermes/logs/agent.log`. Плагіни завантажуються після вбудованих інструментів, тож порядок реєстрації правильний: твій обробник замінює вбудований.
### Реєстрація кількох хуків

⟦HOLD_23⟆
### Довідка щодо хуків

Кожен хук докладно задокументований у **[довідці з Event Hooks](/user-guide/features/hooks#plugin-hooks)** — сигнатури зворотних викликів, таблиці параметрів, точний момент спрацьовування та приклади. Ось короткий огляд:

| Хук | Спрацьовує коли | Сигнатура зворотного виклику | Повертає |
|------|----------------|-----------------------------|----------|
| [`pre_tool_call`](/user-guide/features/hooks#pre_tool_call) | Перед виконанням будь‑якого інструменту | `tool_name: str, args: dict, task_id: str` | ігнорується |
| [`post_tool_call`](/user-guide/features/hooks#post_tool_call) | Після повернення результату будь‑якого інструменту | `tool_name: str, args: dict, result: str, task_id: str, duration_ms: int` | ігнорується |
| [`pre_llm_call`](/user-guide/features/hooks#pre_llm_call) | Один раз за хід, перед циклом виклику інструментів | `session_id: str, user_message: str, conversation_history: list, is_first_turn: bool, model: str, platform: str` | [введення контексту](#pre_llm_call-context-injection) |
| [`post_llm_call`](/user-guide/features/hooks#post_llm_call) | Один раз за хід, після циклу виклику інструментів (лише успішні ходи) | `session_id: str, user_message: str, assistant_response: str, conversation_history: list, model: str, platform: str` | ігнорується |
| [`on_session_start`](/user-guide/features/hooks#on_session_start) | Створено нову сесію (лише перший хід) | `session_id: str, model: str, platform: str` | ігнорується |
| [`on_session_end`](/user-guide/features/hooks#on_session_end) | Кінець кожного виклику `run_conversation` + вихід CLI | `session_id: str, completed: bool, interrupted: bool, model: str, platform: str` | ігнорується |
| [`on_session_finalize`](/user-guide/features/hooks#on_session_finalize) | CLI/шлюз завершує активну сесію | `session_id: str \| None, platform: str` | ігнорується |
| [`on_session_reset`](/user-guide/features/hooks#on_session_reset) | Шлюз підмінює ключ сесії (`/new`, `/reset`) | `session_id: str, platform: str` | ігнорується |

Більшість хуків — це спостерігачі типу fire-and-forget: їхні значення повернення ігноруються. Виняток становить `pre_llm_call`, який може вводити контекст у розмову.

Усі зворотні виклики мають приймати `**kwargs` для забезпечення сумісності у майбутньому. Якщо колбек хука викликає помилку, вона **логуються і пропускаються**. Інші хуки та агент продовжують роботу у звичайному режимі.
### `pre_llm_call` context injection

Це єдиний хук, значення повернення якого має значення. Коли колбек `pre_llm_call` повертає словник з ключем `"context"` (або простий рядок), Hermes вставляє цей текст у **користувацьке повідомлення поточного туру**. Це механізм для плагінів пам’яті, інтеграцій RAG, захисних бар’єрів та будь‑якого плагіна, який потребує надати моделі додатковий контекст.

#### Формат повернення

```python
# Dict with context key
return {"context": "Recalled memories:\n- User prefers dark mode\n- Last project: hermes-agent"}

# Plain string (equivalent to the dict form above)
return "Recalled memories:\n- User prefers dark mode"

# Return None or don't return → no injection (observer-only)
return None
```

Будь‑яке не‑None, не‑порожнє повернення з ключем `"context"` (або простим непорожнім рядком) збирається і додається до користувацького повідомлення поточного туру.

#### Як працює ін’єкція

Вставлений контекст додається до **користувацького повідомлення**, а не до системного підказника. Це навмисний дизайн‑вибір:

- **Збереження кешу підказника** — системний підказник залишається ідентичним у всіх турах. Anthropic та OpenRouter кешують префікс системного підказника, тому його стабільність економить понад 75 % токенів вводу у багатотурових розмовах. Якщо б плагіни змінювали системний підказник, кожен тур був би промахом кешу.
- **Ефемерність** — ін’єкція відбувається лише під час виклику API. Оригінальне користувацьке повідомлення в історії розмови ніколи не змінюється, і нічого не зберігається в базі даних сесії.
- **Системний підказник — це територія Hermes** — він містить модель‑специфічні рекомендації, правила застосування інструментів, інструкції щодо особистості та кешований вміст навичок. Плагіни додають контекст поряд із вводом користувача, а не змінюючи основні інструкції агента.

#### Приклад: Плагін відновлення пам’яті

```python
"""Memory plugin — recalls relevant context from a vector store."""

import httpx

MEMORY_API = "https://your-memory-api.example.com"

def recall_context(session_id, user_message, is_first_turn, **kwargs):
    """Called before each LLM turn. Returns recalled memories."""
    try:
        resp = httpx.post(f"{MEMORY_API}/recall", json={
            "session_id": session_id,
            "query": user_message,
        }, timeout=3)
        memories = resp.json().get("results", [])
        if not memories:
            return None  # nothing to inject

        text = "Recalled context from previous sessions:\n"
        text += "\n".join(f"- {m['text']}" for m in memories)
        return {"context": text}
    except Exception:
        return None  # fail silently, don't break the agent

def register(ctx):
    ctx.register_hook("pre_llm_call", recall_context)
```

#### Приклад: Плагін захисних бар’єрів

```python
"""Guardrails plugin — enforces content policies."""

POLICY = """You MUST follow these content policies for this session:
- Never generate code that accesses the filesystem outside the working directory
- Always warn before executing destructive operations
- Refuse requests involving personal data extraction"""

def inject_guardrails(**kwargs):
    """Injects policy text into every turn."""
    return {"context": POLICY}

def register(ctx):
    ctx.register_hook("pre_llm_call", inject_guardrails)
```

#### Приклад: Хук лише для спостерігання (без ін’єкції)

```python
"""Analytics plugin — tracks turn metadata without injecting context."""

import logging
logger = logging.getLogger(__name__)

def log_turn(session_id, user_message, model, is_first_turn, **kwargs):
    """Fires before each LLM call. Returns None — no context injected."""
    logger.info("Turn: session=%s model=%s first=%s msg_len=%d",
                session_id, model, is_first_turn, len(user_message or ""))
    # No return → no injection

def register(ctx):
    ctx.register_hook("pre_llm_call", log_turn)
```

#### Кілька плагінів, що повертають контекст

Коли кілька плагінів повертають контекст з `pre_llm_call`, їхні виходи об’єднуються подвоєними переносами рядка і додаються разом до користувацького повідомлення. Порядок відповідає порядку виявлення плагінів (алфавітному за назвою каталогу плагіна).
### Реєстрація CLI‑команд

Плагіни можуть додавати власне дерево підкоманд `hermes <plugin>`:

```python
def _my_command(args):
    """Handler for hermes my-plugin <subcommand>."""
    sub = getattr(args, "my_command", None)
    if sub == "status":
        print("All good!")
    elif sub == "config":
        print("Current config: ...")
    else:
        print("Usage: hermes my-plugin <status|config>")

def _setup_argparse(subparser):
    """Build the argparse tree for hermes my-plugin."""
    subs = subparser.add_subparsers(dest="my_command")
    subs.add_parser("status", help="Show plugin status")
    subs.add_parser("config", help="Show plugin config")
    subparser.set_defaults(func=_my_command)

def register(ctx):
    ctx.register_tool(...)
    ctx.register_cli_command(
        name="my-plugin",
        help="Manage my plugin",
        setup_fn=_setup_argparse,
        handler_fn=_my_command,
    )
```

Після реєстрації користувачі можуть запускати `hermes my-plugin status`, `hermes my-plugin config` тощо.

**Плагіни провайдерів пам’яті** використовують підхід, заснований на конвенції: додайте функцію `register_cli(subparser)` у файл `cli.py` вашого плагіна. Система виявлення плагінів пам’яті знаходить її автоматично — виклик `ctx.register_cli_command()` не потрібен. Дивіться [Memory Provider Plugin guide](/developer-guide/memory-provider-plugin#adding-cli-commands) для деталей.

**Гейтинг активного провайдера:** CLI‑команди плагіна пам’яті з’являються лише тоді, коли їх провайдер є активним `memory.provider` у конфігурації. Якщо користувач ще не налаштував ваш провайдер, ваші CLI‑команди не будуть заповнювати вивід довідки.
### Реєстрація slash‑команд

Плагіни можуть реєструвати slash‑команди під час сесії — команди, які користувачі вводять під час розмови (наприклад `/lcm status` або `/ping`). Вони працюють і в CLI, і в gateway (Telegram, Discord тощо).

```python
def _handle_status(raw_args: str) -> str:
    """Handler for /mystatus — called with everything after the command name."""
    if raw_args.strip() == "help":
        return "Usage: /mystatus [help|check]"
    return "Plugin status: all systems nominal"

def register(ctx):
    ctx.register_command(
        "mystatus",
        handler=_handle_status,
        description="Show plugin status",
    )
```

Після реєстрації користувачі можуть вводити `/mystatus` у будь‑якій сесії. Команда з’являється в автодоповненні, у виводі `/help` та у меню бота Telegram.

**Сигнатура:** `ctx.register_command(name: str, handler: Callable, description: str = "")`

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `name` | `str` | Назва команди без початкового слешу (наприклад `"lcm"`, `"mystatus"`) |
| `handler` | `Callable[[str], str \| None]` | Викликається з рядком необроблених аргументів. Може бути також `async`. |
| `description` | `str` | Показується в `/help`, автодоповненні та у меню бота Telegram |

**Ключові відмінності від `register_cli_command()`:**

| | `register_command()` | `register_cli_command()` |
|---|---|---|
| Викликається як | `/name` у сесії | `hermes name` у терміналі |
| Де працює | CLI‑сесії, Telegram, Discord тощо | Тільки в терміналі |
| Обробник отримує | Рядок необроблених аргументів | `argparse.Namespace` |
| Випадки використання | Діагностика, статус, швидкі дії | Складні дерева підкоманд, майстри налаштування |

**Захист від конфліктів:** Якщо плагін намагається зареєструвати назву, що конфліктує зі вбудованою командою (`help`, `model`, `new` тощо), реєстрація безшумно відхиляється з попередженням у журналі. Вбудовані команди завжди мають пріоритет.

**Асинхронні обробники:** gateway автоматично виявляє та чекає асинхронних обробників, тому можна використовувати як синхронні, так і асинхронні функції:

```python
async def _handle_check(raw_args: str) -> str:
    result = await some_async_operation()
    return f"Check result: {result}"

def register(ctx):
    ctx.register_command("check", handler=_handle_check, description="Run async check")
```
### Dispatch tools from slash commands

Обробники slash‑команд, які мають оркеструвати інструменти (запускати підагента через `delegate_task`, викликати `file_edit` тощо), повинні користуватися `ctx.dispatch_tool()` замість прямого доступу до внутрішніх компонентів фреймворку. Контекст батьківського агента (підказки робочого простору, спінер, успадкування моделі) підключається автоматично.

```python
def register(ctx):
    def _handle_deliver(raw_args: str):
        result = ctx.dispatch_tool(
            "delegate_task",
            {
                "goal": raw_args,
                "toolsets": ["terminal", "file", "web"],
            },
        )
        return result

    ctx.register_command(
        "deliver",
        handler=_handle_deliver,
        description="Delegate a goal to a subagent",
    )
```

**Signature:** `ctx.dispatch_tool(name: str, args: dict, *, parent_agent=None) -> str`

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Назва інструменту, зареєстрована в реєстрі інструментів (наприклад, `"delegate_task"`, `"file_edit"`) |
| `args` | `dict` | Аргументи інструменту, у тій самій формі, яку надсилатиме модель |
| `parent_agent` | `Agent \| None` | Необов’язкове перевизначення. Якщо не вказано, береться з поточного CLI‑агента (або плавно деградує в режимі шлюзу) |

**Runtime behavior:**

- **CLI mode:** `parent_agent` визначається з активного CLI‑агента, тому підказки робочого простору, спінер і успадкування моделі працюють, як очікується.
- **Gateway mode:** CLI‑агент відсутній, тому інструменти плавно деградують — робочий простір читається з `TERMINAL_CWD`, і спінер не відображається.
- **Explicit override:** Якщо викликальник явно передає `parent_agent=`, це значення використовується і не перезаписується.

Це публічний, стабільний інтерфейс для диспетчеризації інструментів з команд плагінів. Плагіни не повинні звертатися до `ctx._cli_ref.agent` або подібного приватного стану.

:::tip
У цьому посібнику розглядаються **загальні плагіни** (інструменти, хуки, slash‑команди, CLI‑команди). Нижче наведено шаблони створення для кожного спеціалізованого типу плагінів; кожен розділ посилається на повний посібник з описом полів та прикладами.
:::
## Спеціалізовані типи плагінів

Hermes має п’ять спеціалізованих типів плагінів, окрім загальної поверхні. Кожен розташовується у каталозі `plugins/<category>/<name>/` (вбудовані) або `~/.hermes/plugins/<category>/<name>/` (користувацькі). Контракт відрізняється залежно від категорії — обери потрібний, а потім ознайомся з його повним посібником.

### Плагіни провайдерів моделей — додати бекенд LLM

Помісти профіль у `plugins/model-providers/<name>/`:

```python
# plugins/model-providers/acme/__init__.py
from providers import register_provider
from providers.base import ProviderProfile

register_provider(ProviderProfile(
    name="acme",
    aliases=("acme-inference",),
    display_name="Acme Inference",
    env_vars=("ACME_API_KEY", "ACME_BASE_URL"),
    base_url="https://api.acme.example.com/v1",
    auth_type="api_key",
    default_aux_model="acme-small-fast",
    fallback_models=("acme-large-v3", "acme-medium-v3"),
))
```

```yaml
# plugins/model-providers/acme/plugin.yaml
name: acme-provider
kind: model-provider
version: 1.0.0
description: Acme Inference — OpenAI-compatible direct API
```

Виявляються при першому виклику `get_provider_profile()` або `list_providers()` — `auth.py`, `config.py`, `doctor.py`, `models.py`, `runtime_provider.py` та транспорт `chat_completions` автоматично підключають їх. Користувацькі плагіни переважають вбудовані за назвою.

**Повний посібник:** [Model Provider Plugins](/developer-guide/model-provider-plugin) — довідка по полям, перевизначувані хуки (`prepare_messages`, `build_extra_body`, `build_api_kwargs_extras`, `fetch_models`), вибір `api_mode`, типи автентифікації, тестування.

### Плагіни платформ — додати канал шлюзу

Помісти адаптер у `plugins/platforms/<name>/`:

```python
# plugins/platforms/myplatform/adapter.py
from gateway.platforms.base import BasePlatformAdapter

class MyPlatformAdapter(BasePlatformAdapter):
    async def connect(self): ...
    async def send(self, chat_id, text): ...
    async def disconnect(self): ...

def check_requirements():
    import os
    return bool(os.environ.get("MYPLATFORM_TOKEN"))

def _env_enablement():
    import os
    tok = os.getenv("MYPLATFORM_TOKEN", "").strip()
    if not tok:
        return None
    return {"token": tok}

def register(ctx):
    ctx.register_platform(
        name="myplatform",
        label="MyPlatform",
        adapter_factory=lambda cfg: MyPlatformAdapter(cfg),
        check_fn=check_requirements,
        required_env=["MYPLATFORM_TOKEN"],
        # Auto-populate PlatformConfig.extra from env so env-only setups
        # show up in `hermes gateway status` without SDK instantiation.
        env_enablement_fn=_env_enablement,
        # Opt in to cron delivery: `deliver=myplatform` routes to this var.
        cron_deliver_env_var="MYPLATFORM_HOME_CHANNEL",
        emoji="💬",
        platform_hint="You are chatting via MyPlatform. Keep responses concise.",
    )
```

```yaml
# plugins/platforms/myplatform/plugin.yaml
name: myplatform-platform
label: MyPlatform
kind: platform
version: 1.0.0
description: MyPlatform gateway adapter
requires_env:
  - name: MYPLATFORM_TOKEN
    description: "Bot token from the MyPlatform console"
    password: true
optional_env:
  - name: MYPLATFORM_HOME_CHANNEL
    description: "Default channel for cron delivery"
    password: false
```

**Повний посібник:** [Adding Platform Adapters](/developer-guide/adding-platform-adapters) — повний контракт `BasePlatformAdapter`, маршрутизація повідомлень, контроль автентифікації, інтеграція майстра налаштувань. Дивись `plugins/platforms/irc/` для прикладу, що працює лише зі стандартною бібліотекою.

### Плагіни провайдерів пам’яті — додати бекенд знань між сесіями

Помісти реалізацію `MemoryProvider` у `plugins/memory/<name>/`:

```python
# plugins/memory/my-memory/__init__.py
from agent.memory_provider import MemoryProvider

class MyMemoryProvider(MemoryProvider):
    @property
    def name(self) -> str:
        return "my-memory"

    def is_available(self) -> bool:
        import os
        return bool(os.environ.get("MY_MEMORY_API_KEY"))

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id

    def sync_turn(self, user_message, assistant_response, **kwargs) -> None:
        ...

    def prefetch(self, query: str, **kwargs) -> str | None:
        ...

def register(ctx):
    ctx.register_memory_provider(MyMemoryProvider())
```

Провайдери пам’яті — одиничний вибір: активний лише один, який задається через `memory.provider` у `config.yaml`.

**Повний посібник:** [Memory Provider Plugins](/developer-guide/memory-provider-plugin) — повний ABC `MemoryProvider`, контракт потоків, ізоляція профілів, реєстрація команд CLI через `cli.py`.

### Плагіни контекстних двигунів — замінити компресор контексту

```python
# plugins/context_engine/my-engine/__init__.py
from agent.context_engine import ContextEngine

class MyContextEngine(ContextEngine):
    @property
    def name(self) -> str:
        return "my-engine"

    def should_compress(self, messages, model) -> bool: ...
    def compress(self, messages, model) -> list[dict]: ...

def register(ctx):
    ctx.register_context_engine(MyContextEngine())
```

Контекстні двигуни — одиничний вибір: задаються через `context.engine` у `config.yaml`.

**Повний посібник:** [Context Engine Plugins](/developer-guide/context-engine-plugin).

### Бекенди генерації зображень

Помісти провайдера у `plugins/image_gen/<name>/`:

```python
# plugins/image_gen/my-imggen/__init__.py
from agent.image_gen_provider import ImageGenProvider

class MyImageGenProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "my-imggen"

    def is_available(self) -> bool: ...
    def generate(self, prompt: str, **kwargs) -> str: ...   # returns image path

def register(ctx):
    ctx.register_image_gen_provider(MyImageGenProvider())
```

```yaml
# plugins/image_gen/my-imggen/plugin.yaml
name: my-imggen
kind: backend
version: 1.0.0
description: Custom image generation backend
```

**Повний посібник:** [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin) — повний ABC `ImageGenProvider`, метадані `list_models()` / `get_setup_schema()`, допоміжні функції `success_response()`/`error_response()`, вивід у base64 чи URL, перевизначення користувачем, розповсюдження через pip.

**Приклади:** `plugins/image_gen/openai/` (DALL‑E / GPT‑Image через OpenAI SDK), `plugins/image_gen/openai-codex/`, `plugins/image_gen/xai/` (Grok image gen).
## Не‑Python розширення

Hermes також приймає розширення, які зовсім не є Python‑плагінами. Вони показані в [таблиці підключуваних інтерфейсів](/user-guide/features/plugins#pluggable-interfaces--where-to-go-for-each); нижче коротко описані різні стилі авторства.

### MCP‑сервери — реєстрація зовнішніх інструментів

Model Context Protocol (MCP) сервери реєструють свої інструменти в Hermes без жодного Python‑плагіна. Оголоси їх у `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
    timeout: 120

  linear:
    url: "https://mcp.linear.app/sse"
    auth:
      type: "oauth"
```

Hermes підключається до кожного сервера під час запуску, отримує список його інструментів і реєструє їх поряд із вбудованими. LLM бачить їх точно так само, як будь‑який інший інструмент. **Повний посібник:** [MCP](/user-guide/features/mcp).

### Хуки подій шлюзу — спрацьовують під час життєвих подій

Додай маніфест + обробник у `~/.hermes/hooks/<name>/`:

```yaml
# ~/.hermes/hooks/long-task-alert/HOOK.yaml
name: long-task-alert
description: Send a push notification when a long task finishes
events:
  - agent:end
```

```python
# ~/.hermes/hooks/long-task-alert/handler.py
async def handle(event_type: str, context: dict) -> None:
    if context.get("duration_seconds", 0) > 120:
        # send notification …
        pass
```

Події включають `gateway:startup`, `session:start`, `session:end`, `session:reset`, `agent:start`, `agent:step`, `agent:end` та шаблон `command:*`. Помилки в хуках ловляться та записуються в журнал — вони ніколи не блокують основний конвеєр.

**Повний посібник:** [Gateway Event Hooks](/user-guide/features/hooks#gateway-event-hooks).

### Shell‑хуки — виконання shell‑команди під час виклику інструменту

Якщо потрібно просто запустити скрипт, коли інструмент спрацьовує (повідомлення, аудити, сповіщення, авто‑форматери), використай shell‑хуки в `config.yaml` — Python не потрібен:

```yaml
hooks:
  - event: post_tool_call
    command: "notify-send 'Tool ran: {tool_name}'"
    when:
      tools: [terminal, patch, write_file]
```

Підтримуються ті ж події, що й у Python‑плагінів (`pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, `on_session_start`, `on_session_end`, `pre_gateway_dispatch`), плюс структурований JSON‑вивід для блокуючих рішень `pre_tool_call`.

**Повний посібник:** [Shell Hooks](/user-guide/features/hooks#shell-hooks).

### Джерела навичок — додати власний реєстр навичок

Якщо ти підтримуєш репозиторій GitHub з навичками (або хочеш підключити індекс спільноти, що виходить за межі вбудованих джерел), додай його як **tap**:

```bash
hermes skills tap add myorg/skills-repo
hermes skills search my-workflow --source myorg/skills-repo
hermes skills install myorg/skills-repo/my-workflow
```

Публікація власного tap — це просто репозиторій GitHub з каталогами `skills/<skill-name>/SKILL.md` — сервер або реєстрація не потрібні.

**Повні посібники:** [Skills Hub](/user-guide/features/skills#skills-hub) · [Публікація власного tap](/user-guide/features/skills#publishing-a-custom-skill-tap) (структура репо, мінімальний приклад, нестандартні шляхи, рівні довіри).

### TTS / STT через шаблони команд

Будь‑який CLI, який читає/записує аудіо або текст, можна підключити через `config.yaml` — Python код не потрібен:

```yaml
tts:
  provider: voxcpm
  providers:
    voxcpm:
      type: command
      command: "voxcpm --ref ~/voice.wav --text-file {input_path} --out {output_path}"
      output_format: mp3
      voice_compatible: true
```

Для STT вкажи `HERMES_LOCAL_STT_COMMAND` у вигляді шаблону shell. Підтримувані плейсхолдери: `{input_path}`, `{output_path}`, `{format}`, `{voice}`, `{model}`, `{speed}` (TTS); `{input_path}`, `{output_dir}`, `{language}`, `{model}` (STT). Будь‑який CLI, що працює з шляхами, автоматично стає плагіном.

**Повні посібники:** [TTS custom command providers](/user-guide/features/tts#custom-command-providers) · [STT](/user-guide/features/tts#voice-message-transcription-stt).
## Розповсюдження через pip

Для публічного поширення плагінів додай точку входу у свій Python‑пакет:

```toml
# pyproject.toml
[project.entry-points."hermes_agent.plugins"]
my-plugin = "my_plugin_package"
```

```bash
pip install hermes-plugin-calculator
# Plugin auto-discovered on next hermes startup
```
## Розповсюдження для NixOS

Користувачі NixOS можуть встановлювати ваш плагін декларативно, якщо ви надаєте `pyproject.toml` з точками входу:

**Плагіни‑точки входу** (рекомендовано для розповсюдження):
```nix
# User's configuration.nix
services.hermes-agent.extraPythonPackages = [
  (pkgs.python312Packages.buildPythonPackage {
    pname = "my-plugin";
    version = "1.0.0";
    src = pkgs.fetchFromGitHub {
      owner = "you";
      repo = "hermes-my-plugin";
      rev = "v1.0.0";
      hash = "sha256-...";  # nix-prefetch-url --unpack
    };
    format = "pyproject";
    build-system = [ pkgs.python312Packages.setuptools ];
  })
];
```

**Плагіни‑каталоги** (не потрібен `pyproject.toml`):
```nix
services.hermes-agent.extraPlugins = [
  (pkgs.fetchFromGitHub {
    owner = "you";
    repo = "hermes-my-plugin";
    rev = "v1.0.0";
    hash = "sha256-...";
  })
];
```

Дивіться [Посібник з налаштування Nix](/getting-started/nix-setup#plugins) для повної документації, включаючи використання overlay та перевірку колізій.
## Поширені помилки

**Обробник не повертає рядок JSON:**
```python
# Wrong — returns a dict
def handler(args, **kwargs):
    return {"result": 42}

# Right — returns a JSON string
def handler(args, **kwargs):
    return json.dumps({"result": 42})
```

**У сигнатурі обробника відсутній `**kwargs`:**
```python
# Wrong — will break if Hermes passes extra context
def handler(args):
    ...

# Right
def handler(args, **kwargs):
    ...
```

**Обробник піднімає виключення:**
```python
# Wrong — exception propagates, tool call fails
def handler(args, **kwargs):
    result = 1 / int(args["value"])  # ZeroDivisionError!
    return json.dumps({"result": result})

# Right — catch and return error JSON
def handler(args, **kwargs):
    try:
        result = 1 / int(args.get("value", 0))
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

**Опис схеми надто розпливчастий:**
```python
# Bad — model doesn't know when to use it
"description": "Does stuff"

# Good — model knows exactly when and how
"description": "Evaluate a mathematical expression. Use for arithmetic, trig, logarithms. Supports: +, -, *, /, **, sqrt, sin, cos, log, pi, e."
```