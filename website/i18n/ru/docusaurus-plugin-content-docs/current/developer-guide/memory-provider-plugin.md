---
sidebar_position: 8
title: "Плагины провайдера памяти"
description: "Как создать плагин провайдера памяти для Hermes Agent"
---

# Создание плагина провайдера памяти

Плагины провайдеров памяти дают Hermes Agent постоянные знания между сессиями, выходящие за пределы встроенных MEMORY.md и USER.md. В этом руководстве рассматривается, как создать такой плагин.

:::tip
Провайдеры памяти — один из двух типов **provider plugin**. Другой тип — [Context Engine Plugins](/developer-guide/context-engine-plugin), которые заменяют встроенный компрессор контекста. Оба следуют одной схеме: одиночный выбор, конфигурация через параметры, управление через `hermes plugins`.
:::

## Структура каталогов

Каждый провайдер памяти находится в `plugins/memory/<name>/`:

```
plugins/memory/my-provider/
├── __init__.py      # MemoryProvider implementation + register() entry point
├── plugin.yaml      # Metadata (name, description, hooks)
└── README.md        # Setup instructions, config reference, tools
```

## Абстрактный базовый класс MemoryProvider

Ваш плагин реализует абстрактный базовый класс `MemoryProvider` из `agent/memory_provider.py`:

```python
from agent.memory_provider import MemoryProvider

class MyMemoryProvider(MemoryProvider):
    @property
    def name(self) -> str:
        return "my-provider"

    def is_available(self) -> bool:
        """Check if this provider can activate. NO network calls."""
        return bool(os.environ.get("MY_API_KEY"))

    def initialize(self, session_id: str, **kwargs) -> None:
        """Called once at agent startup.

        kwargs always includes:
          hermes_home (str): Active HERMES_HOME path. Use for storage.
        """
        self._api_key = os.environ.get("MY_API_KEY", "")
        self._session_id = session_id

    # ... implement remaining methods
```

## Обязательные методы

### Основной жизненный цикл

| Метод | Когда вызывается | Требуется реализовать? |
|--------|-------------------|------------------------|
| `name` (property) | Всегда | **Да** |
| `is_available()` | Инициализация агента, до активации | **Да** — без сетевых запросов |
| `initialize(session_id, **kwargs)` | Запуск агента | **Да** |
| `get_tool_schemas()` | После инициализации, для внедрения инструментов | **Да** |
| `handle_tool_call(tool_name, args, **kwargs)` | Когда агент использует ваши инструменты | **Да** (если у вас есть инструменты) |

### Конфигурация

| Метод | Назначение | Требуется реализовать? |
|--------|------------|------------------------|
| `get_config_schema()` | Объявить поля конфигурации для `hermes memory setup` | **Да** |
| `save_config(values, hermes_home)` | Записать неконфиденциальные настройки в нативное место | **Да** (если не только переменные окружения) |

### Необязательные хуки

| Метод | Когда вызывается | Сценарий использования |
|--------|-------------------|------------------------|
| `system_prompt_block()` | Сборка системного промпта | Статическая информация провайдера |
| `prefetch(query, *, session_id="")` | Перед каждым API‑вызовом | Возврат восстановленного контекста |
| `queue_prefetch(query)` | После каждого хода | Предзагрузка для следующего хода |
| `sync_turn(user, assistant, *, session_id="")` | После завершения хода | Сохранение разговора |
| `on_session_end(messages)` | Завершение беседы | Финальная обработка/сброс |
| `on_pre_compress(messages)` | Перед компрессией контекста | Сохранение инсайтов перед удалением |
| `on_memory_write(action, target, content)` | Встроенные записи памяти | Дублирование в ваш бекенд |
| `shutdown()` | Выход процесса | Очистка соединений |

## Схема конфигурации

`get_config_schema()` возвращает список дескрипторов полей, используемых `hermes memory setup`:

```python
def get_config_schema(self):
    return [
        {
            "key": "api_key",
            "description": "My Provider API key",
            "secret": True,           # → written to .env
            "required": True,
            "env_var": "MY_API_KEY",   # explicit env var name
            "url": "https://my-provider.com/keys",  # where to get it
        },
        {
            "key": "region",
            "description": "Server region",
            "default": "us-east",
            "choices": ["us-east", "eu-west", "ap-south"],
        },
        {
            "key": "project",
            "description": "Project identifier",
            "default": "hermes",
        },
    ]
```

Поля с `secret: True` и `env_var` попадают в `.env`. Поля без секрета передаются в `save_config()`.

:::tip Минимальная vs Полная схема
Каждое поле в `get_config_schema()` запрашивается во время `hermes memory setup`. Провайдерам с множеством опций следует держать схему минимальной — включать только те поля, которые пользователь **обязан** настроить (API‑ключ, обязательные учётные данные). Опциональные настройки документируйте в справочнике конфигурационного файла (например, `$HERMES_HOME/myprovider.json`), а не запрашивайте их все во время установки. Это ускоряет мастер настройки, но сохраняет возможность продвинутой конфигурации. См. пример провайдера Supermemory — он запрашивает только API‑ключ; все остальные параметры находятся в `supermemory.json`.
:::

## Сохранение конфигурации

```python
def save_config(self, values: dict, hermes_home: str) -> None:
    """Write non-secret config to your native location."""
    import json
    from pathlib import Path
    config_path = Path(hermes_home) / "my-provider.json"
    config_path.write_text(json.dumps(values, indent=2))
```

Для провайдеров, использующих только переменные окружения, оставьте стандартную пустую реализацию.

## Точка входа плагина

```python
def register(ctx) -> None:
    """Called by the memory plugin discovery system."""
    ctx.register_memory_provider(MyMemoryProvider())
```

## plugin.yaml

```yaml
name: my-provider
version: 1.0.0
description: "Short description of what this provider does."
hooks:
  - on_session_end    # list hooks you implement
```

## Договорённость по потокам

**`sync_turn()` ДОЛЖЕН быть неблокирующим.** Если ваш бекенд имеет задержки (API‑вызовы, обработка LLM), выполняйте работу в демон‑потоке:

```python
def sync_turn(self, user_content, assistant_content, *, session_id="", messages=None):
    def _sync():
        try:
            self._api.ingest(user_content, assistant_content, session_id=session_id, messages=messages)
        except Exception as e:
            logger.warning("Sync failed: %s", e)

    if self._sync_thread and self._sync_thread.is_alive():
        self._sync_thread.join(timeout=5.0)
    self._sync_thread = threading.Thread(target=_sync, daemon=True)
    self._sync_thread.start()
```

`messages` — необязательный контекст разговора в стиле OpenAI, доступный после завершённого хода. Когда он присутствует, включает сообщения пользователя/ассистента, вызовы инструментов ассистента и сообщения‑результаты инструментов. Провайдеры, которым не нужен сырой контекст хода, могут опустить параметр `messages`; Hermes будет продолжать вызывать их со старой сигнатурой.

Облачные провайдеры должны документировать, какие части `messages` отправляются за пределы устройства. Вызовы инструментов и их результаты могут содержать пути к файлам, вывод команд или другие данные рабочего пространства.

## Изоляция профилей

Все пути хранения **должны** использовать аргумент `hermes_home`, получаемый в `initialize()`, а не жёстко прописанный `~/.hermes`:

```python
# CORRECT — profile-scoped
from hermes_constants import get_hermes_home
data_dir = get_hermes_home() / "my-provider"

# WRONG — shared across all profiles
data_dir = Path("~/.hermes/my-provider").expanduser()
```

## Тестирование

Смотрите `tests/agent/test_memory_provider.py` и сопутствующие тесты памяти (`tests/agent/test_memory_session_switch.py`, `tests/agent/test_memory_user_id.py`, `tests/run_agent/test_memory_provider_init.py`) для примеров сквозных сценариев.

```python
from agent.memory_manager import MemoryManager

mgr = MemoryManager()
mgr.add_provider(my_provider)
mgr.initialize_all(session_id="test-1", platform="cli")

# Test tool routing
result = mgr.handle_tool_call("my_tool", {"action": "add", "content": "test"})

# Test lifecycle
mgr.sync_all("user msg", "assistant msg")
mgr.on_session_end([])
mgr.shutdown_all()
```

## Добавление CLI‑команд

Плагины провайдеров памяти могут регистрировать собственное дерево подкоманд CLI (например, `hermes my-provider status`, `hermes my-provider config`). Это реализовано через систему обнаружения по конвенции — изменения в ядре не требуются.

### Как это работает

1. Добавьте файл `cli.py` в каталог вашего плагина
2. Определите функцию `register_cli(subparser)`, которая строит дерево argparse
3. Система плагинов памяти обнаруживает её при старте через `discover_plugin_cli_commands()`
4. Ваши команды появятся под `hermes <provider-name> <subcommand>`

**Фильтрация по активному провайдеру:** Ваши CLI‑команды отображаются только тогда, когда ваш провайдер указан как активный `memory.provider` в конфигурации. Если пользователь не настроил ваш провайдер, команды не появятся в `hermes --help`.

### Пример

```python
# plugins/memory/my-provider/cli.py

def my_command(args):
    """Handler dispatched by argparse."""
    sub = getattr(args, "my_command", None)
    if sub == "status":
        print("Provider is active and connected.")
    elif sub == "config":
        print("Showing config...")
    else:
        print("Usage: hermes my-provider <status|config>")

def register_cli(subparser) -> None:
    """Build the hermes my-provider argparse tree.

    Called by discover_plugin_cli_commands() at argparse setup time.
    """
    subs = subparser.add_subparsers(dest="my_command")
    subs.add_parser("status", help="Show provider status")
    subs.add_parser("config", help="Show provider config")
    subparser.set_defaults(func=my_command)
```

### Реализация‑пример

Смотрите `plugins/memory/honcho/cli.py` для полного примера с 13 подкомандами, управлением кросс‑профилями (`--target-profile`) и чтением/записью конфигурации.

### Структура каталогов с CLI

```
plugins/memory/my-provider/
├── __init__.py      # MemoryProvider implementation + register()
├── plugin.yaml      # Metadata
├── cli.py           # register_cli(subparser) — CLI commands
└── README.md        # Setup instructions
```

## Правило единственного провайдера

Только **один** внешний провайдер памяти может быть активен одновременно. Если пользователь пытается зарегистрировать второй, MemoryManager отклонит его с предупреждением. Это предотвращает рост количества схем инструментов и конфликты бекендов.