---
sidebar_position: 2
title: "Добавление инструментов"
description: "Как добавить новый инструмент в Hermes Agent — схемы, обработчики, регистрация и наборы инструментов"
---

# Добавление инструментов

Прежде чем писать инструмент, спроси себя: **не следует ли это оформить как [skill](creating-skills.md) вместо этого?**

:::warning Только встроенные основные инструменты
Эта страница предназначена для добавления **встроенного инструмента Hermes** в сам репозиторий.
Если нужен персональный, локальный для проекта или иной кастомный инструмент без изменения ядра Hermes, используй путь плагина:

- [Plugins](/user-guide/features/plugins)
- [Build a Hermes Plugin](/guides/build-a-hermes-plugin)

По умолчанию используй плагины для большинства кастомных инструментов. Следуй этой странице только тогда, когда явно хочешь добавить новый встроенный инструмент в `tools/` и `toolsets.py`.
:::

Сделай **Skill**, если возможность может быть выражена инструкциями + командами оболочки + существующими инструментами (поиск в arXiv, git‑workflow, управление Docker, обработка PDF).

Сделай **Tool**, если требуется сквозная интеграция с API‑ключами, пользовательской логикой обработки, бинарными данными или потоковой передачей (автоматизация браузера, TTS, анализ изображений).

## Обзор

Добавление инструмента затрагивает **2 файла**:

1. **`tools/your_tool.py`** — обработчик, схема, функция проверки, вызов `registry.register()`
2. **`toolsets.py`** — добавление имени инструмента в `_HERMES_CORE_TOOLS` (или в конкретный набор)

Любой файл `tools/*.py` с вызовом `registry.register()` на верхнем уровне автоматически обнаруживается при запуске — список импортов вручную не нужен.

## Шаг 1: Создать файл встроенного инструмента

Каждый файл инструмента имеет одинаковую структуру:

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

### Ключевые правила

:::danger Важно
- Обработчики **ДОЛЖНЫ** возвращать строку JSON (через `json.dumps()`), а не сырые словари
- Ошибки **ДОЛЖНЫ** возвращаться как `{"error": "message"}`, а не выбрасываться как исключения
- `check_fn` вызывается при построении определений инструмента — если она возвращает `False`, инструмент тихо исключается
- `handler` получает `(args: dict, **kwargs)`, где `args` — аргументы вызова инструмента от LLM
:::

## Шаг 2: Добавить встроенный инструмент в набор инструментов

В `toolsets.py` добавь имя инструмента:

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

## ~~Шаг 3: Добавить импорт для обнаружения~~ (Больше не требуется)

Модули инструментов с вызовом `registry.register()` на верхнем уровне автоматически обнаруживаются функцией `discover_builtin_tools()` в `tools/registry.py`. Список импортов вручную поддерживать не нужно — просто создай файл в `tools/`, и он будет подхвачен при запуске.

## Асинхронные обработчики

Если твоему обработчику нужен асинхронный код, пометь его `is_async=True`:

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

Реестр прозрачно обрабатывает асинхронный мост — тебе никогда не придётся вызывать `asyncio.run()` самостоятельно.

## Обработчики, которым нужен `task_id`

Инструменты, управляющие состоянием в рамках сессии, получают `task_id` через `**kwargs`:

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

## Инструменты, перехваченные в цикле агента

Некоторые инструменты (`todo`, `memory`, `session_search`, `delegate_task`) нуждаются в доступе к состоянию агента в рамках сессии. Они перехватываются `run_agent.py` до попадания в реестр. Реестр всё равно хранит их схемы, но `dispatch()` возвращает ошибку‑запасной вариант, если перехват был обойден.

## Необязательно: интеграция с мастером настройки

Если твоему инструменту нужен API‑ключ, добавь его в `hermes_cli/config.py`:

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

- [ ] Файл инструмента создан с обработчиком, схемой, функцией проверки и регистрацией
- [ ] Добавлен в соответствующий набор инструментов в `toolsets.py`
- [ ] Подтверждено, что это действительно должен быть встроенный/ядровой инструмент, а не плагин
- [ ] Обработчик возвращает строки JSON, ошибки возвращаются как `{"error": "..."}`
- [ ] Необязательно: API‑ключ добавлен в `OPTIONAL_ENV_VARS` в `hermes_cli/config.py`
- [ ] Необязательно: Добавлен в `toolset_distributions.py` для пакетной обработки
- [ ] Протестировано с `hermes chat -q "Use the weather tool for London"`