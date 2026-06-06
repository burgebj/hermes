---
sidebar_position: 9
title: "Плагины контекстного движка"
description: "Как собрать плагин контекстного движка, заменяющий встроенный ContextCompressor"
---

# Создание плагина Context Engine

Плагины контекстного движка заменяют встроенный `ContextCompressor` альтернативной стратегией управления контекстом разговора. Например, движок Lossless Context Management (LCM), который строит DAG знаний вместо потерь при суммировании.

## Как это работает

Управление контекстом агента построено на абстрактном классе `ContextEngine` (`agent/context_engine.py`). Встроенный `ContextCompressor` является реализацией по умолчанию. Плагин‑движки должны реализовать тот же интерфейс.

Одновременно может быть активен **только один** контекстный движок. Выбор управляется конфигурацией:

```yaml
# config.yaml
context:
  engine: "compressor"    # default built-in
  engine: "lcm"           # activates a plugin engine named "lcm"
```

Плагин‑движки **никогда не активируются автоматически** — пользователь должен явно установить `context.engine` в имя плагина.

## Структура каталогов

Каждый контекстный движок находится в `plugins/context_engine/<name>/`:

```
plugins/context_engine/lcm/
├── __init__.py      # exports the ContextEngine subclass
├── plugin.yaml      # metadata (name, description, version)
└── ...              # any other modules your engine needs
```

## Абстрактный класс ContextEngine

Ваш движок должен реализовать следующие **обязательные** методы:

```python
from agent.context_engine import ContextEngine

class LCMEngine(ContextEngine):

    @property
    def name(self) -> str:
        """Short identifier, e.g. 'lcm'. Must match config.yaml value."""
        return "lcm"

    def update_from_response(self, usage: dict) -> None:
        """Called after every LLM call with the usage dict.

        Update self.last_prompt_tokens, self.last_completion_tokens,
        self.last_total_tokens from the response.
        """

    def should_compress(self, prompt_tokens: int = None) -> bool:
        """Return True if compaction should fire this turn."""

    def compress(self, messages: list, current_tokens: int = None,
                 focus_topic: str = None) -> list:
        """Compact the message list and return a new (possibly shorter) list.

        The returned list must be a valid OpenAI-format message sequence.

        ``focus_topic`` is an optional topic string from manual
        ``/compress <focus>``; engines that support guided compression should
        prioritise preserving information related to it, others may ignore it.
        """
```

### Атрибуты класса, которые ваш движок должен поддерживать

Агент читает их напрямую для отображения и логирования:

```python
last_prompt_tokens: int = 0
last_completion_tokens: int = 0
last_total_tokens: int = 0
threshold_tokens: int = 0        # when compression triggers
context_length: int = 0          # model's full context window
compression_count: int = 0       # how many times compress() has run
```

### Необязательные методы

У них есть разумные значения по умолчанию в абстрактном классе. Переопределяйте при необходимости:

| Метод | Значение по умолчанию | Переопределять, когда |
|--------|----------------------|----------------------|
| `on_session_start(session_id, **kwargs)` | No‑op | Нужно загрузить сохранённое состояние (DAG, DB) |
| `on_session_end(session_id, messages)` | No‑op | Нужно сбросить состояние, закрыть соединения |
| `on_session_reset()` | Сбрасывает счётчики токенов | Есть состояние, зависящее от сессии, которое нужно очистить |
| `update_model(model, context_length, ...)` | Обновляет `context_length` + порог | Нужно пересчитать бюджеты при переключении модели |
| `get_tool_schemas()` | Возвращает `[]` | Ваш движок предоставляет вызываемые агентом инструменты (например, `lcm_grep`) |
| `handle_tool_call(name, args, **kwargs)` | Возвращает JSON ошибки | Вы реализуете обработчики инструментов |
| `should_compress_preflight(messages)` | Возвращает `False` | Можно выполнить дешёвую оценку до вызова API |
| `get_status()` | Стандартный словарь токенов/порога | Есть пользовательские метрики для экспорта |

## Инструменты движка

Контекстные движки могут предоставлять инструменты, которые агент вызывает напрямую. Возвращайте схемы из `get_tool_schemas()` и обрабатывайте вызовы в `handle_tool_call()`:

```python
def get_tool_schemas(self):
    return [{
        "name": "lcm_grep",
        "description": "Search the context knowledge graph",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    }]

def handle_tool_call(self, name, args, **kwargs):
    if name == "lcm_grep":
        results = self._search_dag(args["query"])
        return json.dumps({"results": results})
    return json.dumps({"error": f"Unknown tool: {name}"})
```

Инструменты движка внедряются в список инструментов агента при запуске и автоматически диспетчеризуются — регистрация в реестре не требуется.

## Регистрация

### Через каталог (рекомендовано)

Поместите ваш движок в `plugins/context_engine/<name>/`. Файл `__init__.py` должен экспортировать подкласс `ContextEngine`. Система обнаружения найдёт и автоматически создаст его экземпляр.

### Через общую систему плагинов

Общий плагин также может зарегистрировать контекстный движок:

```python
def register(ctx):
    engine = LCMEngine(context_length=200000)
    ctx.register_context_engine(engine)
```

Можно зарегистрировать только один движок. Попытка второго плагина зарегистрировать движок будет отклонена с предупреждением.

## Жизненный цикл

```
1. Engine instantiated (plugin load or directory discovery)
2. on_session_start() — conversation begins
3. update_from_response() — after each API call
4. should_compress() — checked each turn
5. compress() — called when should_compress() returns True
6. on_session_end() — session boundary (CLI exit, /reset, gateway expiry)
```

`on_session_reset()` вызывается при `/new` или `/reset` для очистки состояния, зависящего от сессии, без полной остановки.

## Конфигурация

Пользователи выбирают ваш движок через `hermes plugins` → Provider Plugins → Context Engine, либо редактируя `config.yaml`:

```yaml
context:
  engine: "lcm"   # must match your engine's name property
```

Блок конфигурации `compression` (`compression.threshold`, `compression.protect_last_n` и т.д.) относится к встроенному `ContextCompressor`. При необходимости ваш движок должен определить собственный формат конфигурации, читая его из `config.yaml` во время инициализации.

## Тестирование

```python
from agent.context_engine import ContextEngine

def test_engine_satisfies_abc():
    engine = YourEngine(context_length=200000)
    assert isinstance(engine, ContextEngine)
    assert engine.name == "your-name"

def test_compress_returns_valid_messages():
    engine = YourEngine(context_length=200000)
    msgs = [{"role": "user", "content": "hello"}]
    result = engine.compress(msgs)
    assert isinstance(result, list)
    assert all("role" in m for m in result)
```

См. `tests/agent/test_context_engine.py` для полного набора тестов контракта ABC.

## Смотрите также

- [Context Compression and Caching](/developer-guide/context-compression-and-caching) — как работает встроенный компрессор
- [Memory Provider Plugins](/developer-guide/memory-provider-plugin) — аналогичная система плагинов с единственным выбором для памяти
- [Plugins](/user-guide/features/plugins) — обзор общей системы плагинов