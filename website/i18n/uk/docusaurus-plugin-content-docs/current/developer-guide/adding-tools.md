---
sidebar_position: 2
title: "Додавання інструментів"
description: "Як додати новий інструмент до Hermes Agent — схеми, обробники, реєстрація та набори інструментів"
---

# Додавання інструментів

Перш ніж писати інструмент, запитай себе: **чи це не має бути [skill](creating-skills.md) замість?**

:::warning Built-in Core Tools Only
Ця сторінка призначена для додавання **вбудованого Hermes інструменту** до самого репозиторію.
Якщо тобі потрібен особистий, локальний для проєкту або інший кастомний інструмент без зміни ядра Hermes, використай шлях плагінів:

- [Plugins](/user-guide/features/plugins)
- [Build a Hermes Plugin](/guides/build-a-hermes-plugin)

За замовчуванням використовуйте плагіни для більшості створення кастомних інструментів. Дотримуйтесь цієї сторінки лише коли ти явно хочеш доставити новий вбудований інструмент у `tools/` та `toolsets.py`.
:::

Зроби це **Skill**, коли можливість можна виразити інструкціями + shell‑командами + існуючими інструментами (пошук в arXiv, git‑workflow, управління Docker, обробка PDF).

Зроби це **Tool**, коли потрібна повна інтеграція з API‑ключами, кастомна логіка обробки, робота з бінарними даними або стрімінгом (автоматизація браузера, TTS, аналіз зображень).

## Огляд

Додавання інструменту зачіпає **2 файли**:

1. **`tools/your_tool.py`** — обробник, схема, функція перевірки, виклик `registry.register()`
2. **`toolsets.py`** — додати назву інструменту до `_HERMES_CORE_TOOLS` (або конкретного набору)

Будь‑який файл `tools/*.py` з викликом `registry.register()` на верхньому рівні автоматично виявляється під час запуску — список імпортів вручну не потрібен.

## Крок 1: Створити файл вбудованого інструменту

Кожен файл інструменту має одну й ту ж структуру:

```python
# tools/weather_tool.py
"""Weather Tool -- look up current weather for a location."""

import json
import os
import logging

logger = logging.getLogger(__name__)


# --- Availability check ---

def check_weather_requirements() -> bool:
    """Return True if the tool's dependencies are available."""
    return bool(os.getenv("WEATHER_API_KEY"))


# --- Handler ---

def weather_tool(location: str, units: str = "metric") -> str:
    """Fetch weather for a location. Returns JSON string."""
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return json.dumps({"error": "WEATHER_API_KEY not configured"})
    try:
        # ... call weather API ...
        return json.dumps({"location": location, "temp": 22, "units": units})
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- Schema ---

WEATHER_SCHEMA = {
    "name": "weather",
    "description": "Get current weather for a location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name or coordinates (e.g. 'London' or '51.5,-0.1')"
            },
            "units": {
                "type": "string",
                "enum": ["metric", "imperial"],
                "description": "Temperature units (default: metric)",
                "default": "metric"
            }
        },
        "required": ["location"]
    }
}


# --- Registration ---

from tools.registry import registry

registry.register(
    name="weather",
    toolset="weather",
    schema=WEATHER_SCHEMA,
    handler=lambda args, **kw: weather_tool(
        location=args.get("location", ""),
        units=args.get("units", "metric")),
    check_fn=check_weather_requirements,
    requires_env=["WEATHER_API_KEY"],
)
```

### Ключові правила

:::danger Important
- Обробники **МУСЯТЬ** повертати JSON‑рядок (через `json.dumps()`), ніколи не сирі `dict`‑и
- Помилки **МУСЯТЬ** повертатися у вигляді `{"error": "message"}`, ніколи не підніматися як виключення
- `check_fn` викликається під час побудови визначень інструменту — якщо вона повертає `False`, інструмент тихо виключається
- `handler` отримує `(args: dict, **kwargs)`, де `args` — це аргументи виклику інструменту LLM
:::

## Крок 2: Додати вбудований інструмент до набору інструментів

У `toolsets.py` додай назву інструменту:

```python
# If it should be available on all platforms (CLI + messaging):
_HERMES_CORE_TOOLS = [
    ...
    "weather",  # <-- add here
]

# Or create a new standalone toolset:
"weather": {
    "description": "Weather lookup tools",
    "tools": ["weather"],
    "includes": []
},
```

## ~~Крок 3: Додати імпорт для виявлення~~ (Більше не потрібно)

Модулі інструментів з викликом `registry.register()` на верхньому рівні автоматично виявляються функцією `discover_builtin_tools()` у `tools/registry.py`. Список імпортів вручну підтримувати не треба — просто створи файл у `tools/`, і він буде підхвачений під час запуску.

## Асинхронні обробники

Якщо твоєму обробнику потрібен асинхронний код, познач його `is_async=True`:

```python
async def weather_tool_async(location: str) -> str:
    async with aiohttp.ClientSession() as session:
        ...
    return json.dumps(result)

registry.register(
    name="weather",
    toolset="weather",
    schema=WEATHER_SCHEMA,
    handler=lambda args, **kw: weather_tool_async(args.get("location", "")),
    check_fn=check_weather_requirements,
    is_async=True,  # registry calls _run_async() automatically
)
```

Реєстр обробляє асинхронний міст прозоро — тобі ніколи не доведеться викликати `asyncio.run()` самостійно.

## Обробники, яким потрібен `task_id`

Інструменти, що керують станом у межах сесії, отримують `task_id` через `**kwargs`:

```python
def _handle_weather(args, **kw):
    task_id = kw.get("task_id")
    return weather_tool(args.get("location", ""), task_id=task_id)

registry.register(
    name="weather",
    ...
    handler=_handle_weather,
)
```

## Інструменти, перехоплені циклом агента

Деякі інструменти (`todo`, `memory`, `session_search`, `delegate_task`) потребують доступу до стану агента у межах сесії. Вони перехоплюються `run_agent.py` до того, як потраплять у реєстр. Реєстр все ще містить їх схеми, але `dispatch()` повертає запасний (fallback) варіант помилки, якщо перехоплення обійдено.

## Необов’язково: інтеграція майстра налаштувань

Якщо твоєму інструменту потрібен API‑ключ, додай його у `hermes_cli/config.py`:

```python
OPTIONAL_ENV_VARS = {
    ...
    "WEATHER_API_KEY": {
        "description": "Weather API key for weather lookup",
        "prompt": "Weather API key",
        "url": "https://weatherapi.com/",
        "tools": ["weather"],
        "password": True,
    },
}
```

## Чек‑лист

- [ ] Файл інструменту створений з обробником, схемою, функцією перевірки та реєстрацією
- [ ] Додано до відповідного набору інструментів у `toolsets.py`
- [ ] Підтверджено, що це дійсно має бути вбудованим/ядровим інструментом, а не плагіном
- [ ] Обробник повертає JSON‑рядки, помилки повертаються як `{"error": "…"}`
- [ ] Необов’язково: API‑ключ додано до `OPTIONAL_ENV_VARS` у `hermes_cli/config.py`
- [ ] Необов’язково: Додано до `toolset_distributions.py` для пакетної обробки
- [ ] Протестовано за допомогою `hermes chat -q "Use the weather tool for London"`