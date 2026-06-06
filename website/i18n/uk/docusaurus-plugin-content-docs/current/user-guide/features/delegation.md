---
sidebar_position: 7
title: "Делегування субагента"
description: "Створити ізольовані дочірні агенти для паралельних робочих потоків з delegate_task"
---

# Делегування підагентів

Інструмент `delegate_task` створює дочірні екземпляри AIAgent з ізольованим контекстом, обмеженими наборами інструментів та власними термінальними сесіями. Кожен дочірній агент отримує нову розмову і працює самостійно — лише його підсумковий звіт потрапляє в контекст батьківського агента.
## Одне завдання

```python
delegate_task(
    goal="Debug why tests fail",
    context="Error: assertion in test_foo.py line 42",
    toolsets=["terminal", "file"]
)
```
## Паралельна пакетна обробка

До 3 одночасних підагентів за замовчуванням (можна налаштувати, без жорсткого ліміту):

```python
delegate_task(tasks=[
    {"goal": "Research topic A", "toolsets": ["web"]},
    {"goal": "Research topic B", "toolsets": ["web"]},
    {"goal": "Fix the build", "toolsets": ["terminal", "file"]}
])
```
## Як працює контекст субагента

:::warning Critical: Subagents Know Nothing
Субагенти починаються з **повністю нової розмови**. Вони не мають жодних знань про історію розмови батька, попередні виклики інструментів або будь‑що, обговорене до делегування. Єдиний контекст субагента походить із полів `goal` і `context`, які батьківський агент заповнює під час виклику `delegate_task`.
:::

Це означає, що батьківський агент повинен передати **все**, що потрібно субагенту, у виклику:

```python
# BAD - subagent has no idea what "the error" is
delegate_task(goal="Fix the error")

# GOOD - subagent has all context it needs
delegate_task(
    goal="Fix the TypeError in api/handlers.py",
    context="""The file api/handlers.py has a TypeError on line 47:
    'NoneType' object has no attribute 'get'.
    The function process_request() receives a dict from parse_body(),
    but parse_body() returns None when Content-Type is missing.
    The project is at /home/user/myproject and uses Python 3.11."""
)
```

Субагент отримує сфокусовану системну підказку, сформовану з вашої мети та контексту, яка інструктує його завершити завдання та надати структуроване резюме того, що він зробив, що знайшов, які файли були змінені та які проблеми виникли.
## Практичні приклади

### Паралельне дослідження

Досліджуй кілька тем одночасно та збирай резюме:

```python
delegate_task(tasks=[
    {
        "goal": "Research the current state of WebAssembly in 2025",
        "context": "Focus on: browser support, non-browser runtimes, language support",
        "toolsets": ["web"]
    },
    {
        "goal": "Research the current state of RISC-V adoption in 2025",
        "context": "Focus on: server chips, embedded systems, software ecosystem",
        "toolsets": ["web"]
    },
    {
        "goal": "Research quantum computing progress in 2025",
        "context": "Focus on: error correction breakthroughs, practical applications, key players",
        "toolsets": ["web"]
    }
])
```

### Огляд коду + виправлення

Делегуй процес огляду та виправлення коду новому контексту:

```python
delegate_task(
    goal="Review the authentication module for security issues and fix any found",
    context="""Project at /home/user/webapp.
    Auth module files: src/auth/login.py, src/auth/jwt.py, src/auth/middleware.py.
    The project uses Flask, PyJWT, and bcrypt.
    Focus on: SQL injection, JWT validation, password handling, session management.
    Fix any issues found and run the test suite (pytest tests/auth/).""",
    toolsets=["terminal", "file"]
)
```

### Рефакторинг кількох файлів

Делегуй велике завдання рефакторингу, яке переповнило б контекст батьківської сесії:

```python
delegate_task(
    goal="Refactor all Python files in src/ to replace print() with proper logging",
    context="""Project at /home/user/myproject.
    Use the 'logging' module with logger = logging.getLogger(__name__).
    Replace print() calls with appropriate log levels:
    - print(f"Error: ...") -> logger.error(...)
    - print(f"Warning: ...") -> logger.warning(...)
    - print(f"Debug: ...") -> logger.debug(...)
    - Other prints -> logger.info(...)
    Don't change print() in test files or CLI output.
    Run pytest after to verify nothing broke.""",
    toolsets=["terminal", "file"]
)
```
## Деталі режиму пакетної обробки

Коли ти передаєш масив `tasks`, підагенти виконуються **паралельно** за допомогою пулу потоків:

- **Максимальна паралельність:** 3 завдання за замовчуванням (можна налаштувати через `delegation.max_concurrent_children` або змінну середовища `DELEGATION_MAX_CONCURRENT_CHILDREN`; мінімум 1, без жорсткого верхнього обмеження). Пакети, що перевищують ліміт, повертають помилку інструмента, а не тихо обрізаються.
- **Пул потоків:** Використовує `ThreadPoolExecutor` з налаштованим лімітом паралельності як максимальну кількість робітників.
- **Відображення прогресу:** У режимі CLI дерево‑перегляд показує виклики інструментів кожного підагента в реальному часі з рядками завершення для кожного завдання. У режимі шлюзу прогрес пакетний і передається у зворотний виклик прогресу батька.
- **Порядок результатів:** Результати сортуються за індексом завдання, щоб відповідати порядку вводу, незалежно від порядку завершення.
- **Поширення переривання:** Переривання батька (наприклад, надсилання нового повідомлення) перериває всі активні дочірні процеси.

Делегування одного завдання виконується без накладних витрат пулу потоків.
## Перевизначення моделі

Ти можеш налаштувати іншу модель для підагентів через `config.yaml` — це корисно для делегування простих завдань дешевшим/швидшим моделям:

```yaml
# In ~/.hermes/config.yaml
delegation:
  model: "google/gemini-flash-2.0"    # Cheaper model for subagents
  provider: "openrouter"              # Optional: route subagents to a different provider
```

Якщо не вказано, підагенти використовують ту ж модель, що й батьківський агент.
## Поради щодо вибору набору інструментів

Параметр `toolsets` керує тим, до яких інструментів має доступ підагент. Обирай його відповідно до завдання:

| Шаблон набору інструментів | Випадок використання |
|---------------------------|----------------------|
| `["terminal", "file"]` | Робота з кодом, налагодження, редагування файлів, збірки |
| `["web"]` | Дослідження, перевірка фактів, пошук у документації |
| `["terminal", "file", "web"]` | Завдання повного стеку (за замовчуванням) |
| `["file"]` | Аналіз лише для читання, перегляд коду без виконання |
| `["terminal"]` | Системне адміністрування, управління процесами |

Деякі набори інструментів блокуються для підагентів незалежно від того, що вказано:
- `delegation` — блоковано для листових підагентів (за замовчуванням). Залишається для дітей `role="orchestrator"`, обмежено `max_spawn_depth` — дивись [Depth Limit and Nested Orchestration](#depth-limit-and-nested-orchestration) нижче.
- `clarify` — підагенти не можуть взаємодіяти з користувачем
- `memory` — заборонено запис у спільну постійну пам'ять
- `code_execution` — діти мають розмірковувати крок за кроком
- `send_message` — заборонені крос‑платформенні побічні ефекти (наприклад, надсилання повідомлень у Telegram)
## Максимальна кількість ітерацій

Кожен підагент має ліміт ітерацій (за замовчуванням: 50), який контролює, скільки ходів виклику інструменту він може здійснити:

```python
delegate_task(
    goal="Quick file check",
    context="Check if /etc/nginx/nginx.conf exists and print its first 10 lines",
    max_iterations=10  # Simple task, don't need many turns
)
```
## Тайм‑аут дочірнього процесу

Субагенти вважаються «завислими» і завершуються, якщо вони мовчать більше `delegation.child_timeout_seconds` секунд реального часу. За замовчуванням **600** (10 хвилин) — збільшено з 300 с у попередніх випусках, бо моделі з високим рівнем міркувань у нетривіальних дослідницьких завданнях вбивалися посеред роздумів. Налаштуй це для кожної інсталяції:

```yaml
delegation:
  child_timeout_seconds: 600   # default
```

Знизь значення для швидких локальних моделей; підвищуй для повільних моделей міркувань у складних задачах. Таймер скидається щоразу, коли дочірній процес робить API‑виклик або виклик інструмента — лише дійсно неактивні працівники викликають завершення.

:::tip Діагностичний дамп при тайм‑ауті без викликів
Якщо субагент завершує роботу через тайм‑аут, не зробивши **жодного** API‑виклику (зазвичай: недоступний провайдер, помилка автентифікації або відхилення схеми інструмента), `delegate_task` записує структурований діагностичний файл у `~/.hermes/logs/subagent-timeout-<session>-<timestamp>.log`, що містить знімок конфігурації субагента, трасування розв’язання облікових даних та будь‑які ранні повідомлення про помилки. Значно простіше визначити причину, ніж при попередній поведінці без повідомлень про тайм‑аут.
:::
## Моніторинг запущених підагентів (`/agents`)

TUI постачається з оверлеєм `/agents` (аліас `/tasks`), який перетворює рекурсивний `delegate_task` fan‑out у першокласну поверхню аудиту:

- Живий деревовидний перегляд запущених і нещодавно завершених підагентів, згрупованих за батьком
- Зведені дані по гілці: вартість, токени та кількість змінених файлів
- Керування завершенням та паузою — скасувати конкретний підагент у процесі без переривання його «братів»
- Пост‑хок аналіз: крок за кроком перегляд історії кожного підагента навіть після того, як він повернувся до батька

Класичний CLI просто виводить `/agents` у вигляді текстового підсумку; саме в TUI оверлей розквітає. Дивись [TUI — Slash commands](/user-guide/tui#slash-commands).
## Обмеження глибини та вкладена оркестрація

За замовчуванням делегування **плоске**: батько (depth 0) створює дочірні процеси (depth 1), і ці діти не можуть делегувати далі. Це запобігає неконтрольованому рекурсивному делегуванню.

Для багатоступеневих робочих процесів (research → synthesis або паралельна оркестрація над підзадачами) батько може створювати дочірні процеси‑**оркестратори**, які *можуть* делегувати своїм власним працівникам:

```python
delegate_task(
    goal="Survey three code review approaches and recommend one",
    role="orchestrator",  # Allows this child to spawn its own workers
    context="...",
)
```

- `role="leaf"` (за замовчуванням): дитина не може делегувати далі — ідентично поведінці плоского делегування.
- `role="orchestrator"`: дитина зберігає набір інструментів `delegation`. Керується параметром `delegation.max_spawn_depth` (за замовчуванням **1** = плоске, тому `role="orchestrator"` не діє). Підвищте `max_spawn_depth` до 2, щоб дозволити оркестратору створювати листових онуків; до 3 — для трьох рівнів (максимум).
- `delegation.orchestrator_enabled: false`: глобальний вимикач, який змушує кожну дитину бути `leaf` незалежно від параметра `role`.

**Попередження про витрати:** При `max_spawn_depth: 3` і `max_concurrent_children: 3` дерево може досягти 3×3×3 = 27 одночасних листових агентів. Кожен додатковий рівень множить витрати — підвищуйте `max_spawn_depth` навмисно.
## Тривалість та надійність

:::warning delegate_task is synchronous — not durable
`delegate_task` виконується **всередині поточного ходу батька**. Він блокує батька, доки всі діти не завершаться (або не будуть скасовані). Це **не** черга фонових завдань:

- Якщо батько переривається (користувач надсилає нове повідомлення, `/stop`, `/new`), усі активні діти скасовуються і повертають `status="interrupted"`. Їхня робота в процесі виконується скидається.
- Діти **не** продовжують виконання після завершення ходу батька.
- Скасовані діти повертають структурований результат (`status="interrupted"`, `exit_reason="interrupted"`), але оскільки батько також був перерваний, цей результат часто ніколи не потрапляє у відповідь, видиму користувачеві.

Для **надійної довготривалої роботи**, яка повинна пережити переривання або існувати довше поточного ходу, використай:

- `cronjob` (action=`create`) — планує окремий запуск агента; імунний до переривань ходу батька.
- `terminal(background=True, notify_on_complete=True)` — довготривалі shell‑команди, які продовжують працювати, поки агент займається іншим.
:::
## Ключові властивості

- Кожен підагент отримує **власну термінальну сесію** (окрему від батьківської)
- **Вкладене делегування за вибором** — лише підагенти з `role="orchestrator"` можуть делегувати далі, і лише коли `max_spawn_depth` підвищено від стандартного значення 1 (плоске). Вимкнути глобально можна за допомогою `orchestrator_enabled: false`.
- Листові підагенти **не можуть** викликати: `delegate_task`, `clarify`, `memory`, `send_message`, `execute_code`. Оркеструючі підагенти зберігають `delegate_task`, але все одно не можуть використовувати інші чотири.
- **Пропагування переривань** — переривання батьківського процесу перериває всі активні дочірні (включно з онуками під оркестратором)
- Тільки підсумковий звіт потрапляє у контекст батька, що забезпечує ефективне використання токенів
- Підагенти успадковують **API‑ключ, конфігурацію провайдера та пул облікових даних** батька (дозволяє ротацію ключа при обмеженнях швидкості)
## Делегування vs execute_code

| Фактор | delegate_task | execute_code |
|--------|--------------|-------------|
| **Reasoning** | Повний цикл розумової діяльності LLM | Просто виконання Python‑коду |
| **Context** | Свіжа ізольована розмова | Без розмови, лише скрипт |
| **Tool access** | Усі незаблоковані інструменти з розумовим циклом | 7 інструментів через RPC, без розумової діяльності |
| **Parallelism** | 3 одночасних підагенти за замовчуванням (можна налаштувати) | Один скрипт |
| **Best for** | Складні завдання, що потребують судження | Механічні багатокрокові конвеєри |
| **Token cost** | Вище (повний цикл LLM) | Нижче (повертається лише stdout) |
| **User interaction** | Відсутня (підагенти не можуть уточнювати) | Відсутня |

**Rule of thumb:** Використовуй `delegate_task`, коли підзавдання вимагає розумової діяльності, судження або багатокрокового розв’язання проблем. Використовуй `execute_code`, коли потрібна механічна обробка даних або скриптові робочі процеси.
## Конфігурація

```yaml
# In ~/.hermes/config.yaml
delegation:
  max_iterations: 50                        # Max turns per child (default: 50)
  # max_concurrent_children: 3              # Parallel children per batch (default: 3)
  # max_spawn_depth: 1                      # Tree depth (1-3, default 1 = flat). Raise to 2 to allow orchestrator children to spawn leaves; 3 for three levels.
  # orchestrator_enabled: true              # Disable to force all children to leaf role.
  model: "google/gemini-3-flash-preview"             # Optional provider/model override
  provider: "openrouter"                             # Optional built-in provider
  api_mode: anthropic_messages                       # optional; auto-detected from base_url for anthropic_messages endpoints

# Or use a direct custom endpoint instead of provider:
delegation:
  model: "qwen2.5-coder"
  base_url: "http://localhost:1234/v1"
  api_key: "local-key"
  # api_mode: "anthropic_messages"  # Optional. Wire protocol override for base_url ("chat_completions", "codex_responses", or "anthropic_messages"). Empty = auto-detect from URL (e.g. /anthropic suffix). Set explicitly for endpoints the heuristic can't classify (Azure AI Foundry, MiniMax, Zhipu GLM, LiteLLM proxies, …).
```

Коли `base_url` вказує на сумісну з Anthropic кінцеву точку — наприклад шлях, що закінчується на `/anthropic`, маршрут Azure Foundry Claude або проксі MiniMax `/anthropic` — `api_mode` автоматично визначається як `anthropic_messages`, тож підагент використовує правильний формат передачі даних без необхідності налаштовувати щось. Встанови `api_mode` явно, якщо автоматичне визначення помилкове (рідко).

:::tip
Агент автоматично обробляє делегування залежно від складності завдання. Тобі не потрібно явно просити його делегувати — він зробить це, коли це має сенс.
:::