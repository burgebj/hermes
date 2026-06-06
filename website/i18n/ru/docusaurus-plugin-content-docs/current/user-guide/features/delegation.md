---
sidebar_position: 7
title: "Делегирование субагента"
description: "Создай изолированных дочерних агентов для параллельных рабочих потоков с delegate_task"
---

# Делегирование субагентов

Инструмент `delegate_task` создаёт дочерние экземпляры AIAgent с изолированным контекстом, ограниченными наборами инструментов и собственными терминальными сессиями. Каждый дочерний агент получает новый разговор и работает независимо — только его итоговое резюме попадает в контекст родителя.
## Одинарная задача

```python
delegate_task(
    goal="Debug why tests fail",
    context="Error: assertion in test_foo.py line 42",
    toolsets=["terminal", "file"]
)
```
## Параллельный пакет

До 3 одновременно работающих субагентов по умолчанию (настраиваемо, без жёсткого ограничения):

```python
delegate_task(tasks=[
    {"goal": "Research topic A", "toolsets": ["web"]},
    {"goal": "Research topic B", "toolsets": ["web"]},
    {"goal": "Fix the build", "toolsets": ["terminal", "file"]}
])
```
## Как работает контекст субагента

:::warning Critical: Subagents Know Nothing
Субагенты начинают с **совершенно новой беседы**. У них нет никакой информации о истории разговора родителя, предыдущих вызовах инструментов или о том, что обсуждалось до делегирования. Единственный контекст субагента поступает из полей `goal` и `context`, которые родительский агент заполняет при вызове `delegate_task`.
:::

Это означает, что родительский агент должен передать **всё**, что необходимо субагенту, в вызове:

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

Субагент получает целевой системный запрос, построенный из вашей цели и контекста, с инструкцией выполнить задачу и предоставить структурированное резюме того, что он сделал, что нашёл, какие файлы изменил и какие проблемы возникли.
## Практические примеры

### Параллельные исследования

Исследуй несколько тем одновременно и собирай резюме:

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

### Обзор кода + исправление

Передай процесс обзора и исправления новому контексту:

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

### Рефакторинг нескольких файлов

Передай большую задачу рефакторинга, которая могла бы переполнить контекст родителя:

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
## Подробности пакетного режима

Когда ты передаёшь массив `tasks`, субагенты работают **параллельно** с использованием пула потоков:

- **Максимальная параллельность:** 3 задачи по умолчанию (настраивается через `delegation.max_concurrent_children` или переменную окружения `DELEGATION_MAX_CONCURRENT_CHILDREN`; минимум — 1, без жёсткого верхнего предела). Пакеты, превышающие лимит, возвращают ошибку инструмента вместо тихого усечения.
- **Пул потоков:** Использует `ThreadPoolExecutor` с настроенным лимитом параллельности в качестве максимального количества рабочих.
- **Отображение прогресса:** В режиме CLI дерево‑вид показывает вызовы инструментов каждого субагента в реальном времени со строками завершения для каждой задачи. В режиме шлюза прогресс агрегируется и передаётся в callback прогресса родителя.
- **Порядок результатов:** Результаты сортируются по индексу задачи, чтобы соответствовать порядку ввода независимо от порядка завершения.
- **Распространение прерываний:** Прерывание родителя (например, отправка нового сообщения) прерывает все активные дочерние задачи.

Делегирование одной задачи выполняется напрямую без накладных расходов пула потоков.
## Переопределение модели

Ты можешь настроить другую модель для субагентов через `config.yaml` — это удобно для делегирования простых задач более дешёвым и быстрым моделям:

```yaml
# In ~/.hermes/config.yaml
delegation:
  model: "google/gemini-flash-2.0"    # Cheaper model for subagents
  provider: "openrouter"              # Optional: route subagents to a different provider
```

Если не указано, субагенты используют ту же модель, что и у родителя.
## Toolset Selection Tips

Параметр `toolsets` управляет тем, к каким инструментам имеет доступ субагент. Выбирай в зависимости от задачи:

| Шаблон набора инструментов | Сценарий использования |
|----------------------------|------------------------|
| `["terminal", "file"]` | Работа с кодом, отладка, редактирование файлов, сборки |
| `["web"]` | Исследования, проверка фактов, поиск в документации |
| `["terminal", "file", "web"]` | Полно‑стековые задачи (по умолчанию) |
| `["file"]` | Анализ только для чтения, ревью кода без выполнения |
| `["terminal"]` | Системное администрирование, управление процессами |

Некоторые наборы инструментов блокируются для субагентов независимо от указанных значений:
- `delegation` — блокируется для листовых субагентов (по умолчанию). Остаётся доступным для дочерних элементов с `role="orchestrator"`, ограниченных `max_spawn_depth` — см. [Depth Limit and Nested Orchestration](#depth-limit-and-nested-orchestration) ниже.
- `clarify` — субагенты не могут взаимодействовать с пользователем.
- `memory` — запись в общую постоянную память запрещена.
- `code_execution` — дочерние элементы должны рассуждать пошагово.
- `send_message` — отсутствие побочных эффектов между платформами (например, отправка сообщений в Telegram).
## Максимальное количество итераций

У каждого субагента есть лимит итераций (по умолчанию — 50), который определяет, сколько ходов вызова инструментов он может выполнить:

```python
delegate_task(
    goal="Quick file check",
    context="Check if /etc/nginx/nginx.conf exists and print its first 10 lines",
    max_iterations=10  # Simple task, don't need many turns
)
```
## Тайм‑аут дочернего процесса

Субагенты убиваются как зависшие, если они молчат более `delegation.child_timeout_seconds` секунд реального времени. По умолчанию **600** (10 минут) — повышено с 300 с в ранних версиях, потому что модели с высоким уровнем рассуждения при нетривиальных исследовательских задачах убивались посреди размышлений. Настраивай значение под каждую установку:

```yaml
delegation:
  child_timeout_seconds: 600   # default
```

Уменьши его для быстрых локальных моделей; увеличь для медленно рассуждающих моделей на сложных задачах. Таймер сбрасывается каждый раз, когда дочерний процесс делает вызов API или инструмента — только действительно бездействующие воркеры вызывают завершение.

:::tip Диагностический дамп при тайм‑ауте без вызовов
Если субагент истекает по тайм‑ауту, сделав **ноль** вызовов API (обычно: недоступный провайдер, ошибка аутентификации или отклонение схемы инструмента), `delegate_task` записывает структурированный диагностический файл в `~/.hermes/logs/subagent-timeout-<session>-<timestamp>.log`, содержащий снимок конфигурации субагента, трассировку разрешения учётных данных и любые ранние сообщения об ошибках. Это гораздо проще для поиска причины, чем прежнее поведение молчаливого тайм‑аута.
:::
## Мониторинг запущенных субагентов (`/agents`)

TUI поставляется с надстройкой `/agents` (alias `/tasks`), которая превращает рекурсивный `delegate_task` fan‑out в полноценный интерфейс аудита:

- Живой древовидный просмотр запущенных и недавно завершившихся субагентов, сгруппированных по родителю
- Сводка затрат, токенов и затронутых файлов для каждой ветки
- Управление завершением и паузой — отменить конкретный субагент в процессе без прерывания его соседей
- Последующий обзор: пошагово просмотреть историю каждого субагента ход за ходом даже после того, как он вернулся к родителю

Классический CLI просто выводит `/agents` в виде текстового резюме; именно в TUI эта надстройка раскрывается полностью. См. [TUI — Slash commands](/user-guide/tui#slash-commands).
## Ограничение глубины и вложенная оркестрация

По умолчанию делегирование **плоское**: родитель (глубина 0) порождает дочерние элементы (глубина 1), и эти дочерние элементы не могут делегировать дальше. Это предотвращает бесконтрольное рекурсивное делегирование.

Для многоэтапных рабочих процессов (исследование → синтез или параллельная оркестрация над подзадачами) родитель может порождать дочерние элементы‑**оркестраторы**, которые *могут* делегировать своим собственным работникам:

```python
delegate_task(
    goal="Survey three code review approaches and recommend one",
    role="orchestrator",  # Allows this child to spawn its own workers
    context="...",
)
```

- `role="leaf"` (по умолчанию): дочерний элемент не может делегировать дальше — то же, что и при плоском делегировании.
- `role="orchestrator"`: дочерний элемент сохраняет набор инструментов `delegation`. Ограничивается параметром `delegation.max_spawn_depth` (по умолчанию **1** = плоское, поэтому `role="orchestrator"` ничего не делает). Увеличьте `max_spawn_depth` до 2, чтобы оркестраторы могли порождать листовые внуки; до 3 — для трёх уровней (верхний предел).
- `delegation.orchestrator_enabled: false`: глобальный переключатель, заставляющий каждый дочерний элемент быть `leaf` независимо от параметра `role`.

**Предупреждение о стоимости:** При `max_spawn_depth: 3` и `max_concurrent_children: 3` дерево может достигать 3 × 3 × 3 = 27 одновременно работающих листовых агентов. Каждый дополнительный уровень умножает расходы — повышайте `max_spawn_depth` осознанно.
## Время жизни и надёжность

:::warning delegate_task is synchronous — not durable
`delegate_task` выполняется **внутри текущего хода родителя**. Он блокирует родителя, пока каждый дочерний процесс не завершится (или не будет отменён). Это **не** очередь фоновых задач:

- Если родитель прерывается (пользователь отправляет новое сообщение, `/stop`, `/new`), все активные дочерние процессы отменяются и возвращают `status="interrupted"`. Их работа в процессе выполнения отбрасывается.
- Дочерние процессы **не** продолжают работу после завершения хода родителя.
- Отменённые дочерние процессы возвращают структурированный результат (`status="interrupted"`, `exit_reason="interrupted"`), но поскольку родитель также был прерван, этот результат часто никогда не попадает в ответ, видимый пользователю.

Для **надёжной длительной работы**, которая должна пережить прерывания или выйти за пределы текущего хода, используй:

- `cronjob` (action=`create`) — планирует отдельный запуск агента; не подвержен прерываниям хода родителя.
- `terminal(background=True, notify_on_complete=True)` — длительные команды оболочки, которые продолжают работать, пока агент занимается другими задачами.
:::
## Ключевые свойства

- Каждый субагент получает **свою собственную терминальную сессию** (отдельную от родительской)
- **Вложенная делегация включается вручную** — только дочерние элементы с `role="orchestrator"` могут делегировать дальше, и только когда `max_spawn_depth` повышен от значения по умолчанию 1 (плоская структура). Отключить глобально можно с помощью `orchestrator_enabled: false`.
- Листовые субагенты **не могут** вызывать: `delegate_task`, `clarify`, `memory`, `send_message`, `execute_code`. Субагенты‑оркестраторы сохраняют возможность `delegate_task`, но всё равно не могут использовать остальные четыре.
- **Распространение прерываний** — прерывание родителя прерывает всех активных дочерних (включая внуков под оркестраторами)
- Только окончательное резюме попадает в контекст родителя, что делает использование токенов эффективным
- Субагенты наследуют у родителя **API‑ключ, конфигурацию провайдера и пул учётных данных** (что позволяет вращать ключи при ограничениях по частоте)
## Делегирование vs execute_code

| Фактор | delegate_task | execute_code |
|--------|--------------|-------------|
| **Reasoning** | Полный цикл рассуждений LLM | Просто выполнение Python‑кода |
| **Context** | Свежий изолированный диалог | Нет диалога, только скрипт |
| **Tool access** | Все незаблокированные инструменты с рассуждениями | 7 инструментов через RPC, без рассуждений |
| **Parallelism** | По умолчанию 3 параллельных субагента (настраиваемо) | Один скрипт |
| **Best for** | Сложные задачи, требующие суждения | Механические многошаговые конвейеры |
| **Token cost** | Выше (полный цикл LLM) | Ниже (возвращается только stdout) |
| **User interaction** | Нет (субагенты не могут уточнять) | Нет |

**Rule of thumb:** Используй `delegate_task`, когда подзадача требует рассуждений, суждения или многошагового решения проблемы. Используй `execute_code`, когда нужна механическая обработка данных или скриптовый рабочий процесс.
## Конфигурация

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

Когда `base_url` указывает на совместимый с Anthropic endpoint — например, путь, заканчивающийся на `/anthropic`, маршрут Azure Foundry Claude или прокси MiniMax `/anthropic` — `api_mode` автоматически определяется как `anthropic_messages`, так что субагент использует правильный формат передачи без необходимости чего‑то настраивать. Установи `api_mode` явно, если автоматическое определение ошибочно (это бывает редко).

:::tip
Агент автоматически обрабатывает делегирование в зависимости от сложности задачи. Тебе не нужно явно просить его делегировать — он сделает это, когда это будет целесообразно.
:::