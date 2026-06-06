---
sidebar_position: 9
sidebar_label: "Build a Plugin"
title: "Создай плагин Hermes"
description: "Пошаговое руководство по созданию полного плагина Hermes с инструментами, хуками, файлами данных и навыками"
---

# Создание плагина Hermes

Это руководство пошагово показывает, как создать полноценный плагин Hermes с нуля. К концу ты получишь работающий плагин с несколькими инструментами, хуками жизненного цикла, включёнными файловыми данными и упакованным skill — всем, что поддерживает система плагинов.

:::info Не уверен, какое руководство тебе нужно?
Hermes имеет несколько различных расширяемых интерфейсов — одни используют Python‑API `register_*`, другие управляются конфигурацией или работают как «drop‑in» каталоги. Сначала посмотри эту карту:

| Если ты хочешь добавить… | Читай |
|---|---|
| Пользовательские инструменты, хуки, слеш‑команды, skills или подкоманды CLI | **Это руководство** (общий интерфейс плагина) |
| **LLM / inference‑бэкенд** (новый провайдер) | [Model Provider Plugins](/developer-guide/model-provider-plugin) |
| **gateway‑шлюз** (Discord/Telegram/IRC/Teams/и т.д.) | [Adding Platform Adapters](/developer-guide/adding-platform-adapters) |
| **бэкенд памяти** (Honcho/Mem0/Supermemory/и т.д.) | [Memory Provider Plugins](/developer-guide/memory-provider-plugin) |
| **движок сжатия контекста** | [Context Engine Plugins](/developer-guide/context-engine-plugin) |
| **бэкенд генерации изображений** | [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin) |
| **бэкенд генерации видео** | [Video Generation Provider Plugins](/developer-guide/video-gen-provider-plugin) |
| **TTS‑бэкенд** (любой CLI — Piper, VoxCPM, Kokoro, клонирование голоса, …) | [TTS custom command providers](/user-guide/features/tts#custom-command-providers) — управляется конфигурацией, Python не требуется |
| **STT‑бэкенд** (кастомный whisper / ASR CLI) | [Voice Message Transcription](/user-guide/features/tts#voice-message-transcription-stt) — задай `HERMES_LOCAL_STT_COMMAND` как шаблон оболочки |
| **внешние инструменты через MCP** (файловая система, GitHub, Linear, любой сервер MCP) | [MCP](/user-guide/features/mcp) — объяви `mcp_servers.<name>` в `config.yaml` |
| **хуки событий gateway** (выполняются при запуске, события сессии, команды) | [Event Hooks](/user-guide/features/hooks#gateway-event-hooks) — положи `HOOK.yaml` + `handler.py` в `~/.hermes/hooks/<name>/` |
| **Shell‑хуки** (запуск shell‑команды при событиях) | [Shell Hooks](/user-guide/features/hooks#shell-hooks) — объяви в разделе `hooks:` в `config.yaml` |
| **дополнительные источники skills** (кастомные репозитории GitHub, приватные индексы skills) | [Skills](/user-guide/features/skills) — `hermes skills tap add <repo>` · [Publishing a tap](/user-guide/features/skills#publishing-a-custom-skill-tap) |
| Первоклассный **core‑инференс‑провайдер** (не плагин) | [Adding Providers](/developer-guide/adding-providers) |

Смотри полную [таблицу расширяемых интерфейсов](/user-guide/features/plugins#pluggable-interfaces--where-to-go-for-each) для консолидированного обзора всех точек расширения, включая конфигурационные (TTS, STT, MCP, Shell‑hooks) и «drop‑in» каталоги (gateway‑hooks).:::
## Что ты создаёшь

Плагин **calculator** с двумя инструментами:
- `calculate` — вычисляет математические выражения (`2**16`, `sqrt(144)`, `pi * 5**2`)
- `unit_convert` — преобразует единицы измерения (`100 F → 37.78 C`, `5 km → 3.11 mi`)

Плюс хук, который записывает каждый вызов инструмента, и встроенный файл навыка.
## Шаг 1: Создай каталог плагина

```bash
mkdir -p ~/.hermes/plugins/calculator
cd ~/.hermes/plugins/calculator
```
## Шаг 2: Создай манифест

Создай `plugin.yaml`:

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

Это сообщает Hermes: «Я плагин под названием calculator, я предоставляю инструменты и хуки». Поля `provides_tools` и `provides_hooks` — это списки того, что регистрирует плагин.

Опциональные поля, которые можно добавить:
```yaml
author: Your Name
requires_env:          # gate loading on env vars; prompted during install
  - SOME_API_KEY       # simple format — plugin disabled if missing
  - name: OTHER_KEY    # rich format — shows description/url during install
    description: "Key for the Other service"
    url: "https://other.com/keys"
    secret: true
```
## Шаг 3: Создай схемы инструментов

Создай `schemas.py` — это то, что LLM читает, чтобы решить, когда вызывать твои инструменты:

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

**Почему схемы важны:** Поле `description` показывает, как LLM определяет, когда следует использовать твой инструмент. Будь конкретен в описании того, что он делает и когда его следует применять. Поле `parameters` задаёт, какие аргументы передаёт LLM.
## Шаг 4: Напиши обработчики инструментов

Создай `tools.py` — это код, который действительно исполняется, когда LLM вызывает твои инструменты:

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

**Ключевые правила для обработчиков:**
1. **Сигнатура:** `def my_handler(args: dict, **kwargs) -> str`
2. **Возврат:** Всегда строка в формате JSON. Как в случае успеха, так и в случае ошибки.
3. **Никогда не генерируй исключения:** Перехватывай все исключения и возвращай JSON‑ошибку.
4. **Принимай `**kwargs`:** Hermes может передать дополнительный контекст в будущем.
## Шаг 5: Регистрация

Создай `__init__.py` — это связывает схемы с обработчиками:

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

**Что делает `register()`:**
- Вызывается ровно один раз при запуске
- `ctx.register_tool()` помещает твой инструмент в реестр — модель видит его сразу
- `ctx.register_hook()` подписывается на события жизненного цикла
- `ctx.register_cli_command()` регистрирует подкоманду CLI (например, `hermes my-plugin <subcommand>`)
- `ctx.register_command()` регистрирует слеш‑команду в сессии (например, `/myplugin <args>` внутри чата CLI / gateway) — см. [Register slash commands](#register-slash-commands) ниже
- `ctx.dispatch_tool(name, arguments)` — вызывает любой другой инструмент (встроенный или из другого плагина) с контекстом родительского агента (одобрения, учётные данные, `task_id`), автоматически подключённым. Полезно в обработчиках слеш‑команд, которым нужно вызвать `terminal`, `read_file` или любой другой инструмент, как будто модель вызвала его напрямую.
- Если эта функция падает, плагин отключается, но Hermes продолжает работать нормально

**Пример `dispatch_tool` — слеш‑команда, запускающая инструмент:**

```python
def handle_scan(ctx, argstr):
    """Implement /scan by invoking the terminal tool through the registry."""
    result = ctx.dispatch_tool("terminal", {"command": f"find . -name '{argstr}'"})
    return result  # returned to the caller's chat UI

def register(ctx):
    ctx.register_command("scan", handle_scan, help="Find files matching a glob")
```

Вызванный инструмент проходит обычные конвейеры одобрения, редактирования и бюджета — это реальный вызов инструмента, а не обход этих механизмов.
## Шаг 6: Тестирование

Запусти Hermes:

```bash
hermes
```

В баннере в списке инструментов ты должен увидеть `calculator: calculate, unit_convert`.

Попробуй эти подсказки:
```
What's 2 to the power of 16?
Convert 100 fahrenheit to celsius
What's the square root of 2 times pi?
How many gigabytes is 1.5 terabytes?
```

Проверь статус плагина:
```
/plugins
```

Вывод:
```
Plugins (1):
  ✓ calculator v1.0.0 (2 tools, 1 hooks)
```

### Отладка обнаружения плагинов

Если плагин не появляется — или появляется, но не загружается — включи `HERMES_PLUGINS_DEBUG=1`, чтобы получить подробные логи обнаружения в `stderr`:

```bash
HERMES_PLUGINS_DEBUG=1 hermes plugins list
```

Ты увидишь для каждого источника плагина (bundled, user, project, entry‑points):

- какие каталоги сканировались и сколько манифестов каждый из них выдал
- по каждому манифесту: разрешённый ключ, имя, тип, источник, путь на диске
- причины пропуска: `disabled via config`, `not enabled in config`, `exclusive plugin`, `no plugin.yaml, depth cap reached`
- при загрузке: импортируемый плагин, плюс однострочное резюме того, что зарегистрировал `register(ctx)` (инструменты, хуки, slash‑команды, команды CLI)
- при ошибке парсинга: полный traceback исключения (ошибки сканера YAML и т.д.)
- при ошибке `register()`: полный traceback, указывающий строку в твоём `__init__.py`, где произошёл вызов

Те же логи всегда записываются в `~/.hermes/logs/agent.log` с уровнем WARNING (только сбои) и DEBUG (всё) при установленной переменной окружения. Поэтому, если ты не можешь запустить с переменной (например, изнутри шлюза), смотри файл журнала:

```bash
hermes logs --level WARNING | grep -i plugin
```

Распространённые причины, по которым плагин не появляется:

- **Не включён в конфигурации** — плагины подключаются по желанию. Выполни `hermes plugins enable <name>` (имя берётся из вывода `plugins list`, может выглядеть как `<category>/<plugin>` для вложенных структур).
- **Неправильная структура каталогов** — должна быть `~/.hermes/plugins/<plugin-name>/plugin.yaml` (плоская) или `~/.hermes/plugins/<category>/<plugin-name>/plugin.yaml` (один уровень вложенности категории, максимум). Всё, что глубже, игнорируется.
- **Отсутствует `__init__.py`** — в каталоге плагина должны присутствовать и `plugin.yaml`, и `__init__.py` с функцией `register(ctx)`.
- **Неправильный `kind`** — адаптерам шлюза нужен `kind: platform` в манифесте. Провайдеры памяти автоматически определяются как `kind: exclusive` и маршрутизируются через конфигурацию `memory.provider`, а не `plugins.enabled`.
## Финальная структура твоего плагина

```
~/.hermes/plugins/calculator/
├── plugin.yaml      # "I'm calculator, I provide tools and hooks"
├── __init__.py      # Wiring: schemas → handlers, register hooks
├── schemas.py       # What the LLM reads (descriptions + parameter specs)
└── tools.py         # What runs (calculate, unit_convert functions)
```

Four files, clear separation:
- **Manifest** объявляет, что представляет собой плагин
- **Schemas** описывают инструменты для LLM
- **Handlers** реализуют фактическую логику
- **Registration** соединяет всё
## Что ещё могут делать плагины?

### Поставлять файлы данных

Помести любые файлы в каталог плагина и читай их во время импорта:

```python
# In tools.py or __init__.py
from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent
_DATA_FILE = _PLUGIN_DIR / "data" / "languages.yaml"

with open(_DATA_FILE) as f:
    _DATA = yaml.safe_load(f)
```

### Пакетировать навыки

Плагины могут поставлять файлы навыков, которые агент загружает через `skill_view("plugin:skill")`. Зарегистрируй их в своём `__init__.py`:

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

Теперь агент может загружать твои навыки по их пространству имён:

```python
skill_view("my-plugin:my-workflow")   # → plugin's version
skill_view("my-workflow")              # → built-in version (unchanged)
```

**Ключевые свойства:**
- Навыки плагина **только для чтения** — они не попадают в `~/.hermes/skills/` и не могут быть отредактированы через `skill_manage`.
- Навыки плагина **не** перечисляются в индексе `<available_skills>` системной подсказки — они загружаются явно по запросу.
- Обычные имена навыков остаются без изменений — пространство имён предотвращает конфликты со встроенными навыками.
- Когда агент загружает навык плагина, в начало контекста пакета добавляется баннер со списком соседних навыков из того же плагина.

:::tip Legacy pattern
Старый шаблон `shutil.copy2` (копирование навыка в `~/.hermes/skills/`) всё ещё работает, но создаёт риск конфликтов имён со встроенными навыками. Для новых плагинов предпочтительно использовать `ctx.register_skill()`.
:::

### Управление через переменные окружения

Если плагину нужен API‑ключ:

```yaml
# plugin.yaml — simple format (backwards-compatible)
requires_env:
  - WEATHER_API_KEY
```

Если `WEATHER_API_KEY` не задан, плагин отключается с чётким сообщением. Нет краша, нет ошибки в агенте — просто «Plugin weather disabled (missing: WEATHER_API_KEY)».

При выполнении `hermes plugins install` пользователю **интерактивно предлагается** ввести любые недостающие переменные `requires_env`. Значения сохраняются в `.env` автоматически.

Для более удобной установки используй формат rich с описаниями и URL‑ами регистрации:

```yaml
# plugin.yaml — rich format
requires_env:
  - name: WEATHER_API_KEY
    description: "API key for OpenWeather"
    url: "https://openweathermap.org/api"
    secret: true
```

| Поле | Обязательно | Описание |
|------|--------------|----------|
| `name` | Да | Имя переменной окружения |
| `description` | Нет | Показано пользователю во время запроса установки |
| `url` | Нет | Где получить учётные данные |
| `secret` | Нет | Если `true`, ввод скрывается (как поле пароля) |

Оба формата можно смешивать в одном списке. Уже заданные переменные пропускаются без вывода.

### Лениво‑устанавливать необязательные зависимости Python

Если твой плагин оборачивает SDK, который не каждый пользователь будет иметь (вендорный SDK, тяжёлая ML‑библиотека, пакет, специфичный для платформы), не `import` его в начале модуля. Используй вспомогательную функцию `tools.lazy_deps.ensure(...)` внутри обработчика инструмента — Hermes установит пакет при первом использовании, при условии, что в конфигурации пользователя включён `security.allow_lazy_installs`.

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

Два правила из модели безопасности в `tools/lazy_deps.py`:

| Правило | Почему |
|--------|--------|
| Твой ключ функции должен присутствовать во встроенном списке `LAZY_DEPS` | Предотвращает злонамерённую конфигурацию, заставляющую Hermes установить произвольные пакеты — допускаются только спецификации, которые поставляются самим Hermes |
| Спецификации только по имени из PyPI | Никаких `--index-url`, `git+https://` или `file:` путей. Зафиксируй версии с помощью PEP 440 (`"my-sdk>=1.2,<2"`) в записи списка разрешённых |

Для сторонних плагинов, распространяемых через pip, объяви необязательные зависимости как extras `[project.optional-dependencies]` в своём `pyproject.toml` и предложи пользователям выполнить `pip install your-plugin[backend]` — этот путь не проходит через `lazy_deps`. Ленивый установочный механизм наиболее полезен для **упакованных** плагинов, где включение жёсткой зависимости в каждый установочный пакет увеличило бы базовый размер Hermes.

Когда глобально установлен `security.allow_lazy_installs: false`, `ensure()` сразу бросает `FeatureUnavailable` с подсказкой по исправлению — твой плагин должен перехватить её и деградировать корректно (вернуть ошибочный результат, а не падать).

### Условная доступность инструмента

Для инструментов, зависящих от необязательных библиотек:

```python
ctx.register_tool(
    name="my_tool",
    schema={...},
    handler=my_handler,
    check_fn=lambda: _has_optional_lib(),  # False = tool hidden from model
)
```

### Переопределение встроенного инструмента

Чтобы заменить встроенный инструмент своей реализацией (например, заменить стандартный браузер‑инструмент на backend Chrome CDP с UI, или заменить `web_search` на корпоративный индекс), передай `override=True`:

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

Без `override=True` реестр отклонит любую регистрацию, которая затмевала бы существующий инструмент из другого набора инструментов — это предотвращает случайные перезаписи. Переопределение логируется на уровне INFO, так что его можно отследить в `~/.hermes/logs/agent.log`. Плагины загружаются после встроенных инструментов, поэтому порядок регистрации корректен: твой обработчик заменяет встроенный.

### Регистрация нескольких хуков

```python
def register(ctx):
    ctx.register_hook("pre_tool_call", before_any_tool)
    ctx.register_hook("post_tool_call", after_any_tool)
    ctx.register_hook("pre_llm_call", inject_memory)
    ctx.register_hook("on_session_start", on_new_session)
    ctx.register_hook("on_session_end", on_session_end)
```

### Справочник по хукам

Каждый хук полностью задокументирован в **[справочнике событийных хуков](/user-guide/features/hooks#plugin-hooks)** — сигнатуры обратных вызовов, таблицы параметров, точные моменты срабатывания и примеры. Ниже — сводка:

| Хук | Срабатывает когда | Сигнатура обратного вызова | Возврат |
|------|-------------------|----------------------------|---------|
| [`pre_tool_call`](/user-guide/features/hooks#pre_tool_call) | Перед выполнением любого инструмента | `tool_name: str, args: dict, task_id: str` | игнорируется |
| [`post_tool_call`](/user-guide/features/hooks#post_tool_call) | После возврата любого инструмента | `tool_name: str, args: dict, result: str, task_id: str, duration_ms: int` | игнорируется |
| [`pre_llm_call`](/user-guide/features/hooks#pre_llm_call) | Один раз за ход, перед циклом вызова инструментов | `session_id: str, user_message: str, conversation_history: list, is_first_turn: bool, model: str, platform: str` | [внедрение контекста](#pre_llm_call-context-injection) |
| [`post_llm_call`](/user-guide/features/hooks#post_llm_call) | Один раз за ход, после цикла вызова инструментов (только успешные ходы) | `session_id: str, user_message: str, assistant_response: str, conversation_history: list, model: str, platform: str` | игнорируется |
| [`on_session_start`](/user-guide/features/hooks#on_session_start) | Создана новая сессия (только первый ход) | `session_id: str, model: str, platform: str` | игнорируется |
| [`on_session_end`](/user-guide/features/hooks#on_session_end) | Завершение каждого вызова `run_conversation` + выход из CLI | `session_id: str, completed: bool, interrupted: bool, model: str, platform: str` | игнорируется |
| [`on_session_finalize`](/user-guide/features/hooks#on_session_finalize) | CLI/шлюз завершает активную сессию | `session_id: str \| None, platform: str` | игнорируется |
| [`on_session_reset`](/user-guide/features/hooks#on_session_reset) | Шлюз меняет ключ сессии (`/new`, `/reset`) | `session_id: str, platform: str` | игнорируется |

Большинство хуков — наблюдатели fire‑and‑forget, их возвращаемые значения игнорируются. Исключение — `pre_llm_call`, который может внедрять контекст в разговор.

Все обратные вызовы должны принимать `**kwargs` для будущей совместимости. Если обработчик хука падает, ошибка логируется и пропускается. Остальные хуки и агент продолжают работу как обычно.

### Внедрение контекста в `pre_llm_call`

Это единственный хук, значение возвращаемого результата которого имеет смысл. Когда обратный вызов `pre_llm_call` возвращает словарь с ключом `"context"` (или простую строку), Hermes вставляет этот текст в **сообщение пользователя текущего хода**. Это механизм для плагинов памяти, интеграций RAG, ограничений и любого плагина, который должен предоставить модели дополнительный контекст.

#### Формат возврата

```python
# Dict with context key
return {"context": "Recalled memories:\n- User prefers dark mode\n- Last project: hermes-agent"}

# Plain string (equivalent to the dict form above)
return "Recalled memories:\n- User prefers dark mode"

# Return None or don't return → no injection (observer-only)
return None
```

Любой ненулевой, непустой возврат с ключом `"context"` (или непустой строкой) собирается и добавляется к сообщению пользователя текущего хода.

#### Как работает внедрение

Внедрённый контекст добавляется к **сообщению пользователя**, а не к системной подсказке. Это осознанный дизайн‑выбор:

- **Сохранение кэша подсказки** — системная подсказка остаётся одинаковой между ходами. Anthropic и OpenRouter кэшируют префикс системной подсказки, поэтому её стабильность экономит более 75 % токенов ввода в многократных диалогах. Если бы плагины изменяли системную подсказку, каждый ход приводил бы к промаху кэша.
- **Эфемерность** — внедрение происходит только во время вызова API. Исходное сообщение пользователя в истории разговора никогда не меняется, и ничего не сохраняется в базе данных сессии.
- **Системная подсказка — территория Hermes** — в ней находятся инструкции, специфичные для модели, правила применения инструментов, личностные указания и кэшированный контент навыков. Плагины добавляют контекст рядом с вводом пользователя, а не меняют базовые инструкции агента.

#### Пример: плагин воспоминаний

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

#### Пример: плагин ограничений

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

#### Пример: хук только для наблюдения (без внедрения)

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

#### Несколько плагинов, возвращающих контекст

Когда несколько плагинов возвращают контекст из `pre_llm_call`, их выводы объединяются двойными переводами строки и добавляются к сообщению пользователя совместно. Порядок соответствует порядку обнаружения плагинов (алфавитный порядок названий каталогов плагинов).

### Регистрация команд CLI

Плагины могут добавить свои подкоманды `hermes <plugin>`:

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

После регистрации пользователи могут выполнять `hermes my-plugin status`, `hermes my-plugin config` и т.д.

**Плагины‑поставщики памяти** используют иной подход: добавь функцию `register_cli(subparser)` в файл `cli.py` плагина. Система обнаружения плагинов памяти найдёт её автоматически — вызов `ctx.register_cli_command()` не требуется. См. руководство **[Memory Provider Plugin](/developer-guide/memory-provider-plugin#adding-cli-commands)** для деталей.

**Гейтинг активного провайдера:** Команды CLI плагина памяти появляются только тогда, когда их провайдер установлен как активный `memory.provider` в конфигурации. Если пользователь ещё не настроил твой провайдер, команды CLI не будут загромождать вывод справки.

### Регистрация слеш‑команд

Плагины могут регистрировать команды, вводимые в ходе сессии — команды, которые пользователь набирает во время разговора (например, `/lcm status` или `/ping`). Они работают как в CLI, так и в шлюзах (Telegram, Discord и др.).

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

После регистрации пользователь может в любой сессии ввести `/mystatus`. Команда появляется в автодополнении, выводе `/help` и меню бота Telegram.

**Сигнатура:** `ctx.register_command(name: str, handler: Callable, description: str = "")`

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | `str` | Имя команды без начального слеша (например, `"lcm"`, `"mystatus"`) |
| `handler` | `Callable[[str], str \| None]` | Вызывается с необработанной строкой аргументов. Может быть `async`. |
| `description` | `str` | Показано в `/help`, автодополнении и меню бота Telegram |

**Ключевые отличия от `register_cli_command()`:**

| | `register_command()` | `register_cli_command()` |
|---|---|---|
| Вызывается как | `/name` в сессии | `hermes name` в терминале |
| Где работает | CLI‑сессии, Telegram, Discord и др. | Только терминал |
| Обработчик получает | Необработанную строку аргументов | `argparse.Namespace` |
| Сценарий использования | Диагностика, статус, быстрые действия | Сложные деревья подкоманд, мастера настройки |

**Защита от конфликтов:** Если плагин пытается зарегистрировать имя, конфликтующее со встроенной командой (`help`, `model`, `new` и т.п.), регистрация тихо отклоняется с предупреждением в логе. Встроенные команды всегда имеют приоритет.

**Асинхронные обработчики:** Шлюз автоматически определяет и ожидает async‑обработчики, так что можно использовать как синхронные, так и асинхронные функции:

```python
async def _handle_check(raw_args: str) -> str:
    result = await some_async_operation()
    return f"Check result: {result}"

def register(ctx):
    ctx.register_command("check", handler=_handle_check, description="Run async check")
```

### Диспатчинг инструментов из слеш‑команд

Обработчики слеш‑команд, которым нужно оркестрировать инструменты (запустить суб‑агента через `delegate_task`, вызвать `file_edit` и т.п.), должны использовать `ctx.dispatch_tool()` вместо обращения к внутренностям фреймворка. Контекст родительского агента (подсказки рабочего пространства, спиннер, наследование модели) подключается автоматически.

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

**Сигнатура:** `ctx.dispatch_tool(name: str, args: dict, *, parent_agent=None) -> str`

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | `str` | Имя инструмента, зарегистрированного в реестре (например, `"delegate_task"`, `"file_edit"`) |
| `args` | `dict` | Аргументы инструмента, в том же виде, в каком их отправляет модель |
| `parent_agent` | `Agent \| None` | Необязательное переопределение. Если не указано, берётся текущий CLI‑агент (или деградирует корректно в режиме шлюза) |

**Поведение во время выполнения:**
- **CLI‑режим:** `parent_agent` берётся из активного CLI‑агента, поэтому подсказки рабочего пространства, спиннер и выбор модели наследуются как ожидается.
- **Шлюз‑режим:** CLI‑агента нет, поэтому инструменты работают в упрощённом режиме — рабочее пространство берётся из `TERMINAL_CWD`, спиннер не показывается.
- **Явное переопределение:** Если вызывающий передаёт `parent_agent=` явно, оно используется и не переопределяется.

Это публичный, стабильный интерфейс для диспатчинга инструментов из команд плагина. Плагины не должны обращаться к `ctx._cli_ref.agent` или другим приватным полям.

:::tip
Это руководство охватывает **общие плагины** (инструменты, хуки, слеш‑команды, команды CLI). Ниже представлены шаблоны авторства для каждого специализированного типа плагина; каждый из них ссылается на полное руководство с полями и примерами.
:::
## Специализированные типы плагинов

Hermes имеет пять специализированных типов плагинов помимо общей поверхности. Каждый из них поставляется в виде каталога `plugins/<category>/<name>/` (bundled) или `~/.hermes/plugins/<category>/<name>/` (user). Контракт отличается в зависимости от категории — выбери нужный и прочитай его полное руководство.

### Плагины провайдеров моделей — добавить LLM‑backend

Помести профиль в `plugins/model-providers/<name>/`:

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

Ленивая загрузка происходит при первом вызове `get_provider_profile()` или `list_providers()` — `auth.py`, `config.py`, `doctor.py`, `models.py`, `runtime_provider.py` и транспорт `chat_completions` автоматически подключаются к нему. Пользовательские плагины переопределяют встроенные по имени.

**Полное руководство:** [Model Provider Plugins](/developer-guide/model-provider-plugin) — справочник полей, переопределяемые хуки (`prepare_messages`, `build_extra_body`, `build_api_kwargs_extras`, `fetch_models`), выбор `api_mode`, типы аутентификации, тестирование.

### Плагины платформ — добавить канал шлюза

Помести адаптер в `plugins/platforms/<name>/`:

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

**Полное руководство:** [Adding Platform Adapters](/developer-guide/adding-platform-adapters) — полный контракт `BasePlatformAdapter`, маршрутизация сообщений, контроль доступа, интеграция мастера настройки. Смотри `plugins/platforms/irc/` для работающего примера только со стандартной библиотекой.

### Плагины провайдеров памяти — добавить кросс‑сессионный backend знаний

Помести реализацию `MemoryProvider` в `plugins/memory/<name>/`:

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

Провайдеры памяти выбираются единственным образом — активен только один одновременно, задаётся через `memory.provider` в `config.yaml`.

**Полное руководство:** [Memory Provider Plugins](/developer-guide/memory-provider-plugin) — полный ABC `MemoryProvider`, контракт многопоточности, изоляция профилей, регистрация команд CLI через `cli.py`.

### Плагины движков контекста — заменить компрессор контекста

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

Движки контекста выбираются единственным образом — задаются через `context.engine` в `config.yaml`.

**Полное руководство:** [Context Engine Plugins](/developer-guide/context-engine-plugin).

### Бэкенды генерации изображений

Помести провайдера в `plugins/image_gen/<name>/`:

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

**Полное руководство:** [Image Generation Provider Plugins](/developer-guide/image-gen-provider-plugin) — полный ABC `ImageGenProvider`, метаданные `list_models()` / `get_setup_schema()`, вспомогательные функции `success_response()` / `error_response()`, вывод в base64 vs URL, переопределения пользователем, дистрибутив pip.

**Примеры:** `plugins/image_gen/openai/` (DALL‑E / GPT‑Image через SDK OpenAI), `plugins/image_gen/openai-codex/`, `plugins/image_gen/xai/` (Grok image gen).
## Поверхности расширений, не являющихся Python‑плагинами

Hermes также принимает расширения, которые вовсе не являются Python‑плагинами. Они перечислены в [таблице подключаемых интерфейсов](/user-guide/features/plugins#pluggable-interfaces--where-to-go-for-each); ниже кратко описан каждый стиль авторинга.

### MCP‑серверы — регистрация внешних инструментов

Серверы Model Context Protocol (MCP) регистрируют свои инструменты в Hermes без какого‑либо Python‑плагина. Объяви их в `~/.hermes/config.yaml`:

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

Hermes подключается к каждому серверу при запуске, получает список его инструментов и регистрирует их рядом со встроенными. LLM видит их точно так же, как любой другой инструмент. **Полное руководство:** [MCP](/user-guide/features/mcp).

### Хуки событий шлюза — срабатывание при событиях жизненного цикла

Помести манифест + обработчик в `~/.hermes/hooks/<name>/`:

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

События включают `gateway:startup`, `session:start`, `session:end`, `session:reset`, `agent:start`, `agent:step`, `agent:end` и шаблон `command:*`. Ошибки в хуках перехватываются и логируются — они никогда не блокируют основной конвейер.

**Полное руководство:** [Gateway Event Hooks](/user-guide/features/hooks#gateway-event-hooks).

### Shell‑хуки — запуск shell‑команды при вызове инструмента

Если нужно просто выполнить скрипт, когда срабатывает инструмент (уведомления, аудиторские логи, настольные оповещения, автоформаттеры), используй shell‑хуки в `config.yaml` — Python не требуется:

```yaml
hooks:
  - event: post_tool_call
    command: "notify-send 'Tool ran: {tool_name}'"
    when:
      tools: [terminal, patch, write_file]
```

Поддерживаются все те же события, что и у хуков Python‑плагинов (`pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, `on_session_start`, `on_session_end`, `pre_gateway_dispatch`), плюс структурированный JSON‑вывод для блокирующих решений `pre_tool_call`.

**Полное руководство:** [Shell Hooks](/user-guide/features/hooks#shell-hooks).

### Источники навыков — добавление собственного реестра навыков

Если ты поддерживаешь репозиторий GitHub с навыками (или хочешь подключить индекс сообщества помимо встроенных источников), добавь его как **tap**:

```bash
hermes skills tap add myorg/skills-repo
hermes skills search my-workflow --source myorg/skills-repo
hermes skills install myorg/skills-repo/my-workflow
```

Публикация собственного tap — это просто репозиторий GitHub с каталогами `skills/<skill-name>/SKILL.md` — сервер или регистрация не требуются.

**Полные руководства:** [Skills Hub](/user-guide/features/skills#skills-hub) · [Публикация собственного tap](/user-guide/features/skills#publishing-a-custom-skill-tap) (структура репозитория, минимальный пример, пути, отличные от стандартных, уровни доверия).

### TTS / STT через шаблоны команд

Любой CLI, который читает/записывает аудио или текст, можно подключить через `config.yaml` — Python‑код не нужен:

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

Для STT укажи `HERMES_LOCAL_STT_COMMAND` на шаблон shell. Поддерживаемые плейсхолдеры: `{input_path}`, `{output_path}`, `{format}`, `{voice}`, `{model}`, `{speed}` (TTS); `{input_path}`, `{output_dir}`, `{language}`, `{model}` (STT). Любой CLI, работающий с путями, автоматически становится плагином.

**Полные руководства:** [TTS custom command providers](/user-guide/features/tts#custom-command-providers) · [STT](/user-guide/features/tts#voice-message-transcription-stt).
## Распространение через pip

Для публичного распространения плагинов добавь точку входа в свой пакет Python:

```toml
# pyproject.toml
[project.entry-points."hermes_agent.plugins"]
my-plugin = "my_plugin_package"
```

```bash
pip install hermes-plugin-calculator
# Plugin auto-discovered on next hermes startup
```
## Распространение для NixOS

Пользователи NixOS могут устанавливать твой плагин декларативно, если ты предоставляешь `pyproject.toml` с точками входа:

**Плагины‑точки входа** (рекомендовано для распространения):
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

**Плагины‑каталоги** (не требуется `pyproject.toml`):
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

См. [руководство по настройке Nix](/getting-started/nix-setup#plugins) для полной документации, включая использование overlay и проверку конфликтов.
## Распространённые ошибки

**Обработчик не возвращает строку JSON:**
```python
# Wrong — returns a dict
def handler(args, **kwargs):
    return {"result": 42}

# Right — returns a JSON string
def handler(args, **kwargs):
    return json.dumps({"result": 42})
```

**Отсутствует `**kwargs` в сигнатуре обработчика:**
```python
# Wrong — will break if Hermes passes extra context
def handler(args):
    ...

# Right
def handler(args, **kwargs):
    ...
```

**Обработчик генерирует исключения:**
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

**Описание схемы слишком расплывчато:**
```python
# Bad — model doesn't know when to use it
"description": "Does stuff"

# Good — model knows exactly when and how
"description": "Evaluate a mathematical expression. Use for arithmetic, trig, logarithms. Supports: +, -, *, /, **, sqrt, sin, cos, log, pi, e."
```