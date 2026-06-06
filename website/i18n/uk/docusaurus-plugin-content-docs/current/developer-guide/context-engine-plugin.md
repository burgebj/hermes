---
sidebar_position: 9
title: "Плагіни контекстного двигуна"
description: "Як створити плагін движка контексту, який замінює вбудований ContextCompressor"
---

# Створення плагіна Context Engine

Плагіни **context engine** замінюють вбудований `ContextCompressor` альтернативною стратегією управління контекстом розмови. Наприклад, движок Lossless Context Management (LCM), який будує knowledge DAG замість втратного підсумовування.

## Як це працює

Управління контекстом агента побудовано на ABC `ContextEngine` (`agent/context_engine.py`). Вбудований `ContextCompressor` є реалізацією за замовчуванням. Плагін‑движки повинні реалізувати той самий інтерфейс.

Одночасно може бути активним **лише один** context engine. Вибір керується конфігурацією:

```yaml
# config.yaml
context:
  engine: "compressor"    # default built-in
  engine: "lcm"           # activates a plugin engine named "lcm"
```

Плагін‑движки **ніколи не активуються автоматично** — користувач повинен явно встановити `context.engine` на назву плагіна.

## Структура каталогів

Кожен context engine розташовується в `plugins/context_engine/<name>/`:

```
plugins/context_engine/lcm/
├── __init__.py      # exports the ContextEngine subclass
├── plugin.yaml      # metadata (name, description, version)
└── ...              # any other modules your engine needs
```

## ABC `ContextEngine`

Ваш движок повинен реалізувати ці **обов’язкові** методи:

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

### Атрибути класу, які ваш движок має підтримувати

Агент читає їх безпосередньо для відображення та логування:

```python
last_prompt_tokens: int = 0
last_completion_tokens: int = 0
last_total_tokens: int = 0
threshold_tokens: int = 0        # when compression triggers
context_length: int = 0          # model's full context window
compression_count: int = 0       # how many times compress() has run
```

### Додаткові методи

Вони мають розумні значення за замовчуванням в ABC. Перевизначайте за потреби:

| Метод | За замовчуванням | Коли перевизначати |
|--------|------------------|--------------------|
| `on_session_start(session_id, **kwargs)` | No‑op | Потрібно завантажити збережений стан (DAG, DB) |
| `on_session_end(session_id, messages)` | No‑op | Потрібно записати стан, закрити з’єднання |
| `on_session_reset()` | Скидає лічильники токенів | Є стан, що зберігається в межах сесії, який треба очистити |
| `update_model(model, context_length, ...)` | Оновлює `context_length` + поріг | Потрібно переобчислити бюджети при зміні моделі |
| `get_tool_schemas()` | Повертає `[]` | Ваш движок надає інструменти, викликані агентом (наприклад, `lcm_grep`) |
| `handle_tool_call(name, args, **kwargs)` | Повертає JSON‑помилку | Ви реалізуєте обробники інструментів |
| `should_compress_preflight(messages)` | Повертає `False` | Ви можете виконати дешеву оцінку перед викликом API |
| `get_status()` | Стандартний словник токен/поріг | У вас є власні метрики для експорту |

## Інструменти движка

Context engines можуть відкривати інструменти, які агент викликає безпосередньо. Повертайте схеми з `get_tool_schemas()` і обробляйте виклики в `handle_tool_call()`:

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

Інструменти движка ін’єкціються у список інструментів агента під час запуску та автоматично диспетчеризуються — реєстрація в реєстрі не потрібна.

## Реєстрація

### Через каталог (рекомендовано)

Помістіть ваш движок у `plugins/context_engine/<name>/`. Файл `__init__.py` має експортувати підклас `ContextEngine`. Система виявлення знаходить і створює його автоматично.

### Через загальну систему плагінів

Загальний плагін також може зареєструвати context engine:

```python
def register(ctx):
    engine = LCMEngine(context_length=200000)
    ctx.register_context_engine(engine)
```

Може бути зареєстрований лише один движок. Другий плагін, який спробує зареєструватися, буде відхилений з попередженням.

## Життєвий цикл

```
1. Engine instantiated (plugin load or directory discovery)
2. on_session_start() — conversation begins
3. update_from_response() — after each API call
4. should_compress() — checked each turn
5. compress() — called when should_compress() returns True
6. on_session_end() — session boundary (CLI exit, /reset, gateway expiry)
```

`on_session_reset()` викликається на `/new` або `/reset` для очищення стану сесії без повного вимкнення.

## Конфігурація

Користувачі вибирають ваш движок через `hermes plugins` → Provider Plugins → Context Engine, або редагуючи `config.yaml`:

```yaml
context:
  engine: "lcm"   # must match your engine's name property
```

Блок конфігурації `compression` (`compression.threshold`, `compression.protect_last_n` тощо) специфічний для вбудованого `ContextCompressor`. Ваш движок має визначити власний формат конфігурації за потреби, читаючи його з `config.yaml` під час ініціалізації.

## Тестування

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

Дивіться `tests/agent/test_context_engine.py` для повного набору тестів контракту ABC.

## Дивись також

- [Context Compression and Caching](/developer-guide/context-compression-and-caching) — як працює вбудований компресор
- [Memory Provider Plugins](/developer-guide/memory-provider-plugin) — аналогічна система одно‑обрання плагінів для пам’яті
- [Plugins](/user-guide/features/plugins) — огляд загальної системи плагінів