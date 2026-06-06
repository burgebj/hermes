---
sidebar_position: 8
title: "Плагіни provider пам'яті"
description: "Як створити плагін провайдера пам'яті для Hermes Agent"
---

# Побудова плагіна провайдера пам’яті

Плагіни провайдерів пам’яті надають Hermes Agent постійні знання між сесіями, що виходять за межі вбудованих MEMORY.md та USER.md. У цьому посібнику розглядається, як створити такий плагін.

:::tip
Провайдери пам’яті — один із двох типів **плагінів провайдерів**. Інший — [плагіни контекстного двигуна](/developer-guide/context-engine-plugin), які замінюють вбудований компресор контексту. Обидва слідують одному шаблону: одиничний вибір, конфігурація через налаштування, керування за допомогою `hermes plugins`.
:::

## Структура директорії

Кожен провайдер пам’яті розташовується у `plugins/memory/<name>/`:

```
plugins/memory/my-provider/
├── __init__.py      # MemoryProvider implementation + register() entry point
├── plugin.yaml      # Metadata (name, description, hooks)
└── README.md        # Setup instructions, config reference, tools
```

## Абстрактний базовий клас MemoryProvider

Ваш плагін реалізує абстрактний базовий клас `MemoryProvider` з `agent/memory_provider.py`:

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

## Обов’язкові методи

### Основний життєвий цикл

| Метод | Коли викликається | Потрібно реалізовувати? |
|--------|-------------------|--------------------------|
| `name` (property) | Завжди | **Так** |
| `is_available()` | Ініціалізація агента, перед активацією | **Так** — без мережевих викликів |
| `initialize(session_id, **kwargs)` | Запуск агента | **Так** |
| `get_tool_schemas()` | Після ініціалізації, для інжекції інструментів | **Так** |
| `handle_tool_call(tool_name, args, **kwargs)` | Коли агент використовує ваші інструменти | **Так** (якщо у вас є інструменти) |

### Конфігурація

| Метод | Призначення | Потрібно реалізовувати? |
|--------|-------------|--------------------------|
| `get_config_schema()` | Оголошення полів конфігурації для `hermes memory setup` | **Так** |
| `save_config(values, hermes_home)` | Запис конфігурації, що не є секретною, у нативне розташування | **Так** (крім випадків лише змінних середовища) |

### Додаткові гачки

| Метод | Коли викликається | Випадок використання |
|--------|-------------------|-----------------------|
| `system_prompt_block()` | Формування системного підказки | Статична інформація провайдера |
| `prefetch(query, *, session_id="")` | Перед кожним API‑викликом | Повернення відновленого контексту |
| `queue_prefetch(query)` | Після кожного ходу | Попереднє прогрівання для наступного ходу |
| `sync_turn(user, assistant, *, session_id="")` | Після завершеного ходу | Збереження розмови |
| `on_session_end(messages)` | Кінець розмови | Останнє вилучення/очищення |
| `on_pre_compress(messages)` | Перед компресією контексту | Збереження інсайтів перед відкиданням |
| `on_memory_write(action, target, content)` | Вбудовані записи пам’яті | Дублювання у ваш бекенд |
| `shutdown()` | Вихід процесу | Прибирання з’єднань |

## Схема конфігурації

`get_config_schema()` повертає список дескрипторів полів, які використовуються у `hermes memory setup`:

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

Поля з `secret: True` та `env_var` записуються у `.env`. Поля без секретності передаються у `save_config()`.

:::tip Minimal vs Full Schema
Кожне поле у `get_config_schema()` пропонується під час `hermes memory setup`. Провайдери з великою кількістю опцій мають тримати схему мінімальною — включати лише ті поля, які користувач **повинен** налаштувати (API‑ключ, обов’язкові облікові дані). Додаткові налаштування документуйте у файлі конфігурації (наприклад, `$HERMES_HOME/myprovider.json`), а не запитуйте їх під час майстра налаштувань. Це робить майстер швидшим, залишаючи можливість розширеної конфігурації. Приклад — провайдер Supermemory, який запитує лише API‑ключ; інші параметри зберігаються у `supermemory.json`.
:::

## Збереження конфігурації

```python
def save_config(self, values: dict, hermes_home: str) -> None:
    """Write non-secret config to your native location."""
    import json
    from pathlib import Path
    config_path = Path(hermes_home) / "my-provider.json"
    config_path.write_text(json.dumps(values, indent=2))
```

Для провайдерів, які працюють лише з змінними середовища, залиште стандартну пусту реалізацію.

## Точка входу плагіна

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

## Договір про багатопоточність

**`sync_turn()` ПОВИНЕН бути неблокуючим.** Якщо ваш бекенд має затримки (API‑виклики, обробка LLM), виконуйте роботу у демон‑потоку:

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

`messages` — це необов’язковий контекст розмови у стилі OpenAI, що передається після завершеного ходу. Якщо присутній, він містить повідомлення користувача/асистента, виклики інструментів та результати інструментів. Провайдери, яким не потрібен сирий контекст ходу, можуть пропустити параметр `messages`; Hermes продовжуватиме викликати їх за старою сигнатурою.

Хмарні провайдери мають документувати, які частини `messages` надсилаються поза пристроєм. Виклики інструментів та їх результати можуть містити шляхи до файлів, вивід команд або інші дані робочого простору.

## Ізоляція профілю

Усі шляхи зберігання **повинні** використовувати аргумент `hermes_home`, переданий у `initialize()`, а не жорстко закодований `~/.hermes`:

```python
# CORRECT — profile-scoped
from hermes_constants import get_hermes_home
data_dir = get_hermes_home() / "my-provider"

# WRONG — shared across all profiles
data_dir = Path("~/.hermes/my-provider").expanduser()
```

## Тестування

Дивіться `tests/agent/test_memory_provider.py` та суміжні тести пам’яті (`tests/agent/test_memory_session_switch.py`, `tests/agent/test_memory_user_id.py`, `tests/run_agent/test_memory_provider_init.py`) для прикладів end‑to‑end.

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

## Додавання CLI‑команд

Плагіни провайдерів пам’яті можуть реєструвати власне дерево підкоманд CLI (наприклад, `hermes my-provider status`, `hermes my-provider config`). Це працює за принципом виявлення за конвенцією — без змін у ядрових файлах.

### Як це працює

1. Додайте файл `cli.py` у директорію вашого плагіна
2. Визначте функцію `register_cli(subparser)`, яка будує дерево argparse
3. Система плагінів пам’яті виявляє її під час запуску через `discover_plugin_cli_commands()`
4. Ваші команди з’являються під `hermes <provider-name> <subcommand>`

**Фільтрація за активним провайдером:** Ваші CLI‑команди відображаються лише тоді, коли ваш провайдер встановлений як активний `memory.provider` у конфігурації. Якщо користувач ще не налаштував ваш провайдер, команди не будуть показані у `hermes --help`.

### Приклад

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

### Реалізація‑зразок

Дивіться `plugins/memory/honcho/cli.py` для повного прикладу з 13 підкомандами, управлінням між профілями (`--target-profile`) та читанням/записом конфігурації.

### Структура директорії з CLI

```
plugins/memory/my-provider/
├── __init__.py      # MemoryProvider implementation + register()
├── plugin.yaml      # Metadata
├── cli.py           # register_cli(subparser) — CLI commands
└── README.md        # Setup instructions
```

## Правило одного провайдера

Може бути активним лише **один** зовнішній провайдер пам’яті одночасно. Якщо користувач спробує зареєструвати другий, MemoryManager відхилить його з попередженням. Це запобігає надмірному збільшенню схеми інструментів та конфліктам бекендів.