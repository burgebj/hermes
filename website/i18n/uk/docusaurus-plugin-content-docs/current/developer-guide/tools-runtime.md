---
sidebar_position: 9
title: "Runtime інструментів"
description: "Поведінка реєстру інструментів, наборів інструментів, диспетчеризації та термінальних середовищ"
---

# Runtime інструментів

Інструменти Hermes – це само‑реєструючі функції, згруповані в набори інструментів та виконувані через центральну систему реєстру/диспетчеризації.

Основні файли:

- `tools/registry.py`
- `model_tools.py`
- `toolsets.py`
- `tools/terminal_tool.py`
- `tools/environments/*`

## Модель реєстрації інструментів

Кожен модуль інструменту викликає `registry.register(...)` під час імпорту.

`model_tools.py` відповідає за імпорт/виявлення модулів інструментів та формування списку схем, який використовується моделлю.

### Як працює `registry.register()`

Кожен файл інструменту в `tools/` викликає `registry.register()` на рівні модуля, оголошуючи себе. Підпис функції:

```python
registry.register(
    name="terminal",               # Unique tool name (used in API schemas)
    toolset="terminal",            # Toolset this tool belongs to
    schema={...},                  # OpenAI function-calling schema (description, parameters)
    handler=handle_terminal,       # The function that executes when the tool is called
    check_fn=check_terminal,       # Optional: returns True/False for availability
    requires_env=["SOME_VAR"],     # Optional: env vars needed (for UI display)
    is_async=False,                # Whether the handler is an async coroutine
    description="Run commands",    # Human-readable description
    emoji="💻",                    # Emoji for spinner/progress display
)
```

Кожен виклик створює `ToolEntry`, що зберігається у словнику‑одиночці `ToolRegistry._tools`, індексованому за назвою інструменту. Якщо в різних наборах інструментів виникає колізія імен, виводиться попередження, і переважає пізніша реєстрація.

### Виявлення: `discover_builtin_tools()`

Коли імпортується `model_tools.py`, він викликає `discover_builtin_tools()` з `tools/registry.py`. Ця функція сканує кожен файл `tools/*.py`, використовуючи парсинг AST, щоб знайти модулі, які містять виклики `registry.register()` на верхньому рівні, а потім імпортує їх:

```python
# tools/registry.py (simplified)
def discover_builtin_tools(tools_dir=None):
    tools_path = Path(tools_dir) if tools_dir else Path(__file__).parent
    for path in sorted(tools_path.glob("*.py")):
        if path.name in {"__init__.py", "registry.py", "mcp_tool.py"}:
            continue
        if _module_registers_tools(path):  # AST check for top-level registry.register()
            importlib.import_module(f"tools.{path.stem}")
```

Таке автовиявлення означає, що нові файли інструментів підхоплюються автоматично — немає необхідності підтримувати ручний список. Перевірка AST збігається лише з викликами `registry.register()` на верхньому рівні (не всередині функцій), тому допоміжні модулі в `tools/` не імпортуються.

Кожен імпорт ініціює виклики `registry.register()` модуля. Помилки в необов’язкових інструментах (наприклад, відсутність `fal_client` для генерації зображень) ловляться та логуються — вони не заважають завантаженню інших інструментів.

Після виявлення базових інструментів також виявляються інструменти MCP та плагін‑інструменти:

1. **Інструменти MCP** — `tools.mcp_tool.discover_mcp_tools()` читає конфігурацію сервера MCP і реєструє інструменти з зовнішніх серверів.
2. **Плагін‑інструменти** — `hermes_cli.plugins.discover_plugins()` завантажує плагіни користувача/проекту/pip, які можуть зареєструвати додаткові інструменти.

## Перевірка доступності інструменту (`check_fn`)

Кожен інструмент може опціонально надати `check_fn` — викликаємий, який повертає `True`, коли інструмент доступний, і `False` в іншому випадку. Типові перевірки включають:

- **Наявність API‑ключа** — напр., `lambda: bool(os.environ.get("SERP_API_KEY"))` для веб‑пошуку
- **Запущений сервіс** — напр., перевірка, чи налаштовано сервер Honcho
- **Встановлений бінарник** — напр., перевірка доступності `playwright` для інструментів браузера

Коли `registry.get_definitions()` формує список схем для моделі, він виконує `check_fn()` кожного інструменту:

```python
# Simplified from registry.py
if entry.check_fn:
    try:
        available = bool(entry.check_fn())
    except Exception:
        available = False   # Exceptions = unavailable
    if not available:
        continue            # Skip this tool entirely
```

Ключові поведінки:
- Результати перевірки **кешуються протягом одного виклику** — якщо кілька інструментів ділять один `check_fn`, він виконується лише один раз.
- Виключення в `check_fn()` трактуються як «недоступний» (fail‑safe).
- Метод `is_toolset_available()` перевіряє, чи проходить `check_fn` набору інструментів, і використовується для відображення в UI та розв’язання набору інструментів.

## Розв’язання набору інструментів

Набори інструментів — це іменовані групи інструментів. Hermes розв’язує їх через:

- явні списки увімкнених/вимкнених наборів
- пресети платформи (`hermes-cli`, `hermes-telegram` тощо)
- динамічні набори MCP
- спеціально підготовлені набори, такі як `hermes-acp`

### Як `get_tool_definitions()` фільтрує інструменти

Головна точка входу — `model_tools.get_tool_definitions(enabled_toolsets, disabled_toolsets, quiet_mode)`:

1. **Якщо вказані `enabled_toolsets`** — включаються лише інструменти з цих наборів. Кожна назва набору розв’язується через `resolve_toolset()`, який розгортає складні набори в окремі назви інструментів.

2. **Якщо вказані `disabled_toolsets`** — стартуємо з УСІХ наборів, а потім віднімаємо вимкнені.

3. **Якщо нічого не вказано** — включаються всі відомі набори.

4. **Фільтрація реєстру** — отриманий набір імен передається в `registry.get_definitions()`, який застосовує фільтрацію `check_fn` і повертає схеми у форматі OpenAI.

5. **Динамічне патчування схем** — після фільтрації схеми `execute_code` та `browser_navigate` динамічно коригуються, щоб посилатися лише на інструменти, які пройшли фільтрацію (запобігає галюцинаціям моделі щодо недоступних інструментів).

### Застарілі назви наборів

Старі назви наборів з суфіксом `_tools` (наприклад, `web_tools`, `terminal_tools`) мапуються на їхні сучасні назви через `_LEGACY_TOOLSET_MAP` задля зворотної сумісності.

## Диспетчеризація

Під час виконання інструменти диспетчеризуються через центральний реєстр, з виключеннями в циклі агента для деяких інструментів рівня агента, таких як обробка пам’яті/todo/сесії.

### Потік диспетчеризації: виклик інструменту моделі → виконання обробника

Коли модель повертає `tool_call`, потік виглядає так:

```
Model response with tool_call
    ↓
run_agent.py agent loop
    ↓
model_tools.handle_function_call(name, args, task_id, user_task)
    ↓
[Agent-loop tools?] → handled directly by agent loop (todo, memory, session_search, delegate_task)
    ↓
[Plugin pre-hook] → invoke_hook("pre_tool_call", ...)
    ↓
registry.dispatch(name, args, **kwargs)
    ↓
Look up ToolEntry by name
    ↓
[Async handler?] → bridge via _run_async()
[Sync handler?]  → call directly
    ↓
Return result string (or JSON error)
    ↓
[Plugin post-hook] → invoke_hook("post_tool_call", ...)
```

### Обгортка помилок

Весь виконуваний код інструменту обгорнуто у два рівні обробки помилок:

1. **`registry.dispatch()`** — ловить будь‑яке виключення з обробника і повертає `{"error": "Tool execution failed: ExceptionType: message"}` у вигляді JSON.

2. **`handle_function_call()`** — обгортає весь диспетчер у другий `try/except`, який повертає `{"error": "Error executing tool_name: message"}`.

Таким чином модель завжди отримує коректний JSON‑рядок, а не необроблене виключення.

### Інструменти циклу агента

Чотири інструменти перехоплюються до диспетчеризації реєстру, бо потребують стану агента (TodoStore, MemoryStore тощо):

- `todo` — планування/відстеження задач
- `memory` — запис у постійну пам’ять
- `session_search` — пошук по всіх сесіях
- `delegate_task` — створення під‑агентних сесій

Їх схеми все ще зареєстровані в реєстрі (для `get_tool_definitions`), проте їх обробники повертають заглушкову помилку, якщо диспетчер все ж спробує їх викликати напряму.

### Асинхронний міст

Коли обробник інструменту асинхронний, `_run_async()` мостить його до синхронного шляху диспетчеризації:

- **CLI‑шлях (без запущеного циклу)** — використовує постійний event loop, щоб зберігати кешовані асинхронні клієнти живими.
- **Gateway‑шлях (з запущеним циклом)** — створює одноразовий потік з `asyncio.run()`.
- **Робочі потоки (паралельні інструменти)** — використовує постійні цикли, збережені у thread‑local storage.

## Потік схвалення DANGEROUS_PATTERNS

Термінальний інструмент інтегрує систему схвалення небезпечних команд, визначену в `tools/approval.py`:

1. **Виявлення патернів** — `DANGEROUS_PATTERNS` — список кортежів `(regex, description)`, що охоплює руйнівні дії:
   - рекурсивне видалення (`rm -rf`)
   - форматування файлових систем (`mkfs`, `dd`)
   - руйнівні SQL‑операції (`DROP TABLE`, `DELETE FROM` без `WHERE`)
   - перезапис системних конфігурацій (`> /etc/`)
   - маніпуляції сервісами (`systemctl stop`)
   - віддалене виконання коду (`curl | sh`)
   - fork‑бомби, вбивання процесів тощо.

2. **Виявлення** — перед виконанням будь‑якої термінальної команди `detect_dangerous_command(command)` перевіряє її проти всіх патернів.

3. **Запит схвалення** — якщо знайдено збіг:
   - **CLI‑режим** — інтерактивний запит пропонує користувачу схвалити, відхилити або дозволити назавжди.
   - **Gateway‑режим** — асинхронний колбек схвалення надсилає запит у платформу обміну повідомленнями.
   - **Розумне схвалення** — опціонально, допоміжний LLM може автоматично схвалити низько‑ризикові команди, які збігаються з патернами (наприклад, `rm -rf node_modules/` безпечна, хоча підпадає під «рекурсивне видалення»).

4. **Стан сесії** — схвалення відстежуються per‑session. Після схвалення «рекурсивного видалення» для даної сесії подальші `rm -rf` не запитують підтвердження.

5. **Постійний allowlist** — опція «дозволити назавжди» записує патерн у `config.yaml` у розділ `command_allowlist`, зберігаючи його між сесіями.

## Термінальні/Runtime середовища

Термінальна система підтримує кілька бекендів:

- local
- docker
- ssh
- singularity
- modal
- daytona

Вона також підтримує:

- перевизначення cwd per‑task
- управління фоновими процесами
- PTY‑режим
- колбеки схвалення для небезпечних команд

## Конкурентність

Виклики інструментів можуть виконуватись послідовно або паралельно, залежно від набору інструментів та вимог взаємодії.

## Пов’язані документи

- [Посилання на набори інструментів](../reference/toolsets-reference.md)
- [Посилання на вбудовані інструменти](../reference/tools-reference.md)
- [Внутрішня логіка циклу агента](./agent-loop.md)
- [Внутрішня логіка ACP](./acp-internals.md)