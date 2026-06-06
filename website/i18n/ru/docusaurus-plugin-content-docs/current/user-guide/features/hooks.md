---
sidebar_position: 6
title: "Обработчики событий"
description: "Запускай пользовательский код в ключевых точках жизненного цикла — веди журнал активности, отправляй оповещения, публикуй в веб‑хуки"
---

# Хуки событий

Hermes имеет три системы хуков, которые запускают пользовательский код в ключевых точках жизненного цикла:

| Система | Регистрация через | Выполняется в | Сценарий использования |
|--------|-------------------|---------------|------------------------|
| **[Gateway hooks](#gateway-event-hooks)** | `HOOK.yaml` + `handler.py` в `~/.hermes/hooks/` | только gateway | Логирование, оповещения, вебхуки |
| **[Plugin hooks](#plugin-hooks)** | `ctx.register_hook()` в [плагине](/user-guide/features/plugins) | CLI + gateway | Перехват инструментов, метрики, ограничительные меры |
| **[Shell hooks](#shell-hooks)** | блок `hooks:` в `~/.hermes/config.yaml`, указывающий на скрипты оболочки | CLI + gateway | Скрипты‑подключения для блокировки, автоформатирования, внедрения контекста |

Все три системы работают без блокировки — ошибки в любом хуке перехватываются и логируются, агент не падает.
## Хуки событий шлюза

Хуки шлюза срабатывают автоматически во время работы шлюза (Telegram, Discord, Slack, WhatsApp, Teams), не блокируя основной конвейер агента.

### Создание хука

Каждый хук — это каталог в `~/.hermes/hooks/`, содержащий два файла:

```text
~/.hermes/hooks/
└── my-hook/
    ├── HOOK.yaml      # Declares which events to listen for
    └── handler.py     # Python handler function
```

#### HOOK.yaml

```yaml
name: my-hook
description: Log all agent activity to a file
events:
  - agent:start
  - agent:end
  - agent:step
```

Список `events` определяет, какие события вызывают ваш обработчик. Вы можете подписаться на любую комбинацию событий, включая подстановочные знаки, такие как `command:*`.

#### handler.py

```python
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".hermes" / "hooks" / "my-hook" / "activity.log"

async def handle(event_type: str, context: dict):
    """Called for each subscribed event. Must be named 'handle'."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        **context,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

**Правила обработчика:**
- Должен называться `handle`
- Принимает `event_type` (строка) и `context` (dict)
- Может быть `async def` или обычным `def` — оба варианта работают
- Ошибки перехватываются и логируются, агент никогда не падает

### Доступные события

| Событие | Когда срабатывает | Ключи контекста |
|-------|-------------------|-----------------|
| `gateway:startup` | Запуск процесса шлюза | `platforms` (список активных названий платформ) |
| `session:start` | Создана новая сессия обмена сообщениями | `platform`, `user_id`, `session_id`, `session_key` |
| `session:end` | Сессия завершена (до сброса) | `platform`, `user_id`, `session_key` |
| `session:reset` | Пользователь выполнил `/new` или `/reset` | `platform`, `user_id`, `session_key` |
| `agent:start` | Агент начинает обработку сообщения | `platform`, `user_id`, `session_id`, `message` |
| `agent:step` | Каждая итерация цикла вызова инструментов | `platform`, `user_id`, `session_id`, `iteration`, `tool_names` |
| `agent:end` | Агент завершил обработку | `platform`, `user_id`, `session_id`, `message`, `response` |
| `command:*` | Выполнена любая слеш‑команда | `platform`, `user_id`, `command`, `args` |

#### Подстановочное сопоставление

Обработчики, зарегистрированные для `command:*`, срабатывают для любого события `command:` (`command:model`, `command:reset` и т.д.). Отслеживайте все слеш‑команды одной подпиской.

### Примеры

#### Оповещение в Telegram о длительных задачах

Отправляй себе сообщение, когда агент делает более 10 шагов:

```yaml
# ~/.hermes/hooks/long-task-alert/HOOK.yaml
name: long-task-alert
description: Alert when agent is taking many steps
events:
  - agent:step
```

```python
# ~/.hermes/hooks/long-task-alert/handler.py
import os
import httpx

THRESHOLD = 10
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_HOME_CHANNEL")

async def handle(event_type: str, context: dict):
    iteration = context.get("iteration", 0)
    if iteration == THRESHOLD and BOT_TOKEN and CHAT_ID:
        tools = ", ".join(context.get("tool_names", []))
        text = f"⚠️ Agent has been running for {iteration} steps. Last tools: {tools}"
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": CHAT_ID, "text": text},
            )
```

#### Журнал использования команд

Отслеживай, какие слеш‑команды используются:

```yaml
# ~/.hermes/hooks/command-logger/HOOK.yaml
name: command-logger
description: Log slash command usage
events:
  - command:*
```

```python
# ~/.hermes/hooks/command-logger/handler.py
import json
from datetime import datetime
from pathlib import Path

LOG = Path.home() / ".hermes" / "logs" / "command_usage.jsonl"

def handle(event_type: str, context: dict):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now().isoformat(),
        "command": context.get("command"),
        "args": context.get("args"),
        "platform": context.get("platform"),
        "user": context.get("user_id"),
    }
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

#### Веб‑хук при начале сессии

POST во внешнюю службу при новых сессиях:

```yaml
# ~/.hermes/hooks/session-webhook/HOOK.yaml
name: session-webhook
description: Notify external service on new sessions
events:
  - session:start
  - session:reset
```

```python
# ~/.hermes/hooks/session-webhook/handler.py
import httpx

WEBHOOK_URL = "https://your-service.example.com/hermes-events"

async def handle(event_type: str, context: dict):
    async with httpx.AsyncClient() as client:
        await client.post(WEBHOOK_URL, json={
            "event": event_type,
            **context,
        }, timeout=5)
```

### Руководство: BOOT.md — Запуск чек‑листа при каждом старте шлюза

Популярный шаблон из сообщества: размести Markdown‑чек‑лист в `~/.hermes/BOOT.md`, и агент будет выполнять его каждый раз при старте шлюза. Полезно для «при каждом запуске проверять неудачные cron‑задачи за ночь и писать мне в Discord, если что‑то не удалось», или «суммировать последние 24 ч. `deploy.log` и отправлять в Slack #ops».

Это руководство показывает, как собрать такой пользовательский хук. Hermes не поставляет встроенный хук BOOT.md — ты сам настраиваешь нужное поведение.

#### Что мы будем создавать

1. Файл `~/.hermes/BOOT.md` с инструкциями на естественном языке.
2. Хук шлюза, который срабатывает на `gateway:startup`, запускает одноразового агента с моделью/учётными данными твоего шлюза и исполняет инструкции BOOT.md.
3. Конвенцию `[SILENT]`, позволяющую агенту не отправлять сообщение, если нечего сообщать.

#### Шаг 1: Напиши свой чек‑лист

Создай `~/.hermes/BOOT.md`. Пиши его так, как будто даёшь указания человеческому помощнику:

```markdown
# Startup Checklist

1. Run `hermes cron list` and check if any scheduled jobs failed overnight.
2. If any failed, send a summary to Discord #ops using the `send_message` tool.
3. Check if `/opt/app/deploy.log` has any ERROR lines from the last 24 hours. If yes, summarize them and include in the same Discord message.
4. If nothing went wrong, reply with only `[SILENT]` so no message is sent.
```

Агент воспринимает это как часть своего промпта, поэтому всё, что можно описать простым языком, работает — вызовы инструментов, команды оболочки, отправка сообщений, суммирование файлов.

#### Шаг 2: Создай хук

```text
~/.hermes/hooks/boot-md/
├── HOOK.yaml
└── handler.py
```

**`~/.hermes/hooks/boot-md/HOOK.yaml`**

```yaml
name: boot-md
description: Run ~/.hermes/BOOT.md on gateway startup
events:
  - gateway:startup
```

**`~/.hermes/hooks/boot-md/handler.py`**

```python
"""Run ~/.hermes/BOOT.md on every gateway startup."""

import logging
import threading
from pathlib import Path

logger = logging.getLogger("hooks.boot-md")

BOOT_FILE = Path.home() / ".hermes" / "BOOT.md"


def _build_prompt(content: str) -> str:
    return (
        "You are running a startup boot checklist. Follow the instructions "
        "below exactly.\n\n"
        "---\n"
        f"{content}\n"
        "---\n\n"
        "Execute each instruction. Use the send_message tool to deliver any "
        "messages to platforms like Discord or Slack.\n"
        "If nothing needs attention and there is nothing to report, reply "
        "with ONLY: [SILENT]"
    )


def _run_boot_agent(content: str) -> None:
    """Spawn a one-shot agent and execute the checklist.

    Uses the gateway's resolved model and runtime credentials so this works
    against custom endpoints, aggregators, and OAuth-based providers alike.
    """
    try:
        from gateway.run import _resolve_gateway_model, _resolve_runtime_agent_kwargs
        from run_agent import AIAgent

        agent = AIAgent(
            model=_resolve_gateway_model(),
            **_resolve_runtime_agent_kwargs(),
            platform="gateway",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            max_iterations=20,
        )
        result = agent.run_conversation(_build_prompt(content))
        response = result.get("final_response", "")
        if response and "[SILENT]" not in response:
            logger.info("boot-md completed: %s", response[:200])
        else:
            logger.info("boot-md completed (nothing to report)")
    except Exception as e:
        logger.error("boot-md agent failed: %s", e)


async def handle(event_type: str, context: dict) -> None:
    if not BOOT_FILE.exists():
        return
    content = BOOT_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return

    logger.info("Running BOOT.md (%d chars)", len(content))

    # Background thread so gateway startup isn't blocked on a full agent turn.
    thread = threading.Thread(
        target=_run_boot_agent,
        args=(content,),
        name="boot-md",
        daemon=True,
    )
    thread.start()
```

Две ключевые строки:

- `_resolve_gateway_model()` читает текущую модель, настроенную в шлюзе.
- `_resolve_runtime_agent_kwargs()` получает учётные данные провайдера так же, как обычный запрос шлюза — включая API‑ключи, базовые URL, токены OAuth и пул учётных данных.

Без этого простой `AIAgent()` будет использовать встроенные значения по умолчанию и получит 401 от любого нестандартного эндпоинта.

#### Шаг 3: Протестируй

Перезапусти шлюз:

```bash
hermes gateway restart
```

Посмотри логи:

```bash
hermes logs --follow --level INFO | grep boot-md
```

Ты должен увидеть `Running BOOT.md (N chars)`, а затем либо `boot-md completed: …` (резюме действий агента), либо `boot-md completed (nothing to report)`, когда агент ответил `[SILENT]`.

Удалив `~/.hermes/BOOT.md`, отключишь чек‑лист — хук останется загруженным, но будет тихо пропускать отсутствие файла.

#### Расширение шаблона

- **Чек‑листы, учитывающие расписание:** используйте `datetime.now().weekday()` внутри инструкций BOOT.md («если понедельник, также проверить недельный `deploy.log`»). Инструкции свободного формата, так что всё, что агент может осмыслить, допускается.
- **Несколько чек‑листов:** указывайте хук на другой файл (`STARTUP.md`, `MORNING.md` и т.д.) и регистрируйте отдельные каталоги хуков для каждого.
- **Вариант без агента:** если не нужен полноценный цикл агента, полностью уберите `AIAgent` и пусть обработчик отправит фиксированное уведомление через `httpx`. Дешевле, быстрее и без зависимости от провайдера.

#### Почему это не встроено

Ранние версии Hermes поставляли этот хук как встроенный и тихо запускали агента с базовыми настройками при каждом старте шлюза. Это удивляло пользователей с кастомными эндпоинтами и делало функцию незаметной для тех, кто не знал о её работе. Оставив её как документированный шаблон — созданный тобой в каталоге хуков — ты видишь точный код и включаешь его только при необходимости.

### Как это работает

1. При старте шлюза `HookRegistry.discover_and_load()` сканирует `~/.hermes/hooks/`.
2. Каждый подкаталог с `HOOK.yaml` + `handler.py` загружается динамически.
3. Обработчики регистрируются для объявленных событий.
4. На каждой точке жизненного цикла `hooks.emit()` вызывает все подходящие обработчики.
5. Ошибки в любом обработчике перехватываются и логируются — сломанный хук никогда не падает агенту.

:::info
Хуки шлюза срабатывают только в **шлюзе** (Telegram, Discord, Slack, WhatsApp, Teams). CLI не загружает хуки шлюза. Для хуков, работающих везде, используй [plugin hooks](#plugin-hooks).
:::
## Хуки плагинов

[Плагины](/user-guide/features/plugins) могут регистрировать хуки, которые срабатывают **в сеансах CLI и gateway**. Они регистрируются программно через `ctx.register_hook()` в функции `register()` вашего плагина.

```python
def register(ctx):
    ctx.register_hook("pre_tool_call", my_tool_observer)
    ctx.register_hook("post_tool_call", my_tool_logger)
    ctx.register_hook("pre_llm_call", my_memory_callback)
    ctx.register_hook("post_llm_call", my_sync_callback)
    ctx.register_hook("on_session_start", my_init_callback)
    ctx.register_hook("on_session_end", my_cleanup_callback)
```

**Общие правила для всех хуков:**

- Обратные вызовы получают **именованные аргументы**. Всегда принимайте `**kwargs` для совместимости — в будущих версиях могут появиться новые параметры без поломки вашего плагина.
- Если обратный вызов **падает**, он логируется и пропускается. Остальные хуки и агент продолжают работу как обычно. Плохой плагин никогда не может сломать агент.
- Возвратные значения двух хуков влияют на поведение: [`pre_tool_call`](#pre_tool_call) может **блокировать** инструмент, а [`pre_llm_call`](#pre_llm_call) может **вставлять контекст** в вызов LLM. Все остальные хуки — наблюдатели fire‑and‑forget.

### Быстрая справка

| Хук | Срабатывает когда | Возвращает |
|------|-------------------|------------|
| [`pre_tool_call`](#pre_tool_call) | Перед выполнением любого инструмента | `{"action": "block", "message": str}` для вето вызова |
| [`post_tool_call`](#post_tool_call) | После возврата любого инструмента | игнорируется |
| [`pre_llm_call`](#pre_llm_call) | Один раз за ход, перед циклом вызова инструментов | `{"context": str}` для добавления контекста к сообщению пользователя |
| [`post_llm_call`](#post_llm_call) | Один раз за ход, после цикла вызова инструментов | игнорируется |
| [`on_session_start`](#on_session_start) | Создан новый сеанс (только первый ход) | игнорируется |
| [`on_session_end`](#on_session_end) | Сеанс завершается | игнорируется |
| [`on_session_finalize`](#on_session_finalize) | CLI/gateway завершают активный сеанс (flush, save, stats) | игнорируется |
| [`on_session_reset`](#on_session_reset) | Gateway меняет ключ сеанса (например `/new`, `/reset`) | игнорируется |
| [`subagent_stop`](#subagent_stop) | Дочерний `delegate_task` завершился | игнорируется |
| [`pre_gateway_dispatch`](#pre_gateway_dispatch) | Gateway получил сообщение пользователя, до auth + dispatch | `{"action": "skip" \| "rewrite" \| "allow", ...}` для влияния на поток |
| [`pre_approval_request`](#pre_approval_request) | Опасная команда требует одобрения, до отправки подсказки/уведомления | игнорируется |
| [`post_approval_response`](#post_approval_response) | Пользователь ответил на запрос одобрения (или время истекло) | игнорируется |
| [`transform_tool_result`](#transform_tool_result) | После возврата любого инструмента, до передачи результата модели | `str` для замены результата, `None` — оставить без изменений |
| [`transform_terminal_output`](#transform_terminal_output) | Внутри инструмента `terminal`, до усечения/ANSI‑strip/редактирования | `str` для замены сырого вывода, `None` — оставить без изменений |
| [`transform_llm_output`](#transform_llm_output) | После завершения цикла вызова инструментов, до доставки финального ответа | `str` для замены текста ответа, `None`/пустая строка — оставить без изменений |

---

### `pre_tool_call`

Срабатывает **непосредственно перед** выполнением любого инструмента — встроенных и плагинных.

**Сигнатура обратного вызова:**

```python
def my_callback(tool_name: str, args: dict, task_id: str, **kwargs):
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `tool_name` | `str` | Имя инструмента, который собирается выполниться (например `"terminal"`, `"web_search"`, `"read_file"`) |
| `args` | `dict` | Аргументы, которые модель передала инструменту |
| `task_id` | `str` | Идентификатор сеанса/задачи. Пустая строка, если не установлен. |

**Срабатывает:** В `model_tools.py`, внутри `handle_function_call()`, перед запуском обработчика инструмента. Срабатывает один раз за каждый вызов инструмента — если модель вызывает 3 инструмента параллельно, хук сработает 3 раза.

**Возвратное значение — вето вызова:**

```python
return {"action": "block", "message": "Reason the tool call was blocked"}
```

Агент прерывает инструмент, возвращая `message` как ошибку модели. Первая подходящая директива блокировки выигрывает (сначала плагины Python, затем хуки оболочки). Любое другое значение игнорируется, поэтому существующие только‑наблюдательные обратные вызовы продолжают работать без изменений.

**Сценарии использования:** Логирование, аудит, подсчёт вызовов инструментов, блокировка опасных операций, ограничение скорости, применение политик per‑user.

**Пример — журнал аудита вызовов инструментов:**

```python
import json, logging
from datetime import datetime

logger = logging.getLogger(__name__)

def audit_tool_call(tool_name, args, task_id, **kwargs):
    logger.info("TOOL_CALL session=%s tool=%s args=%s",
                task_id, tool_name, json.dumps(args)[:200])

def register(ctx):
    ctx.register_hook("pre_tool_call", audit_tool_call)
```

**Пример — предупреждение при опасных инструментах:**

```python
DANGEROUS = {"terminal", "write_file", "patch"}

def warn_dangerous(tool_name, **kwargs):
    if tool_name in DANGEROUS:
        print(f"⚠ Executing potentially dangerous tool: {tool_name}")

def register(ctx):
    ctx.register_hook("pre_tool_call", warn_dangerous)
```

---

### `post_tool_call`

Срабатывает **непосредственно после** возврата любого инструмента.

**Сигнатура обратного вызова:**

```python
def my_callback(tool_name: str, args: dict, result: str, task_id: str,
                duration_ms: int, **kwargs):
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `tool_name` | `str` | Имя инструмента, который только что выполнился |
| `args` | `dict` | Аргументы, которые модель передала инструменту |
| `result` | `str` | Возвратное значение инструмента (всегда JSON‑строка) |
| `task_id` | `str` | Идентификатор сеанса/задачи. Пустая строка, если не установлен. |
| `duration_ms` | `int` | Время выполнения инструмента в миллисекундах (измеряется `time.monotonic()` вокруг `registry.dispatch()`). |

**Срабатывает:** В `model_tools.py`, внутри `handle_function_call()`, после возврата обработчика инструмента. Срабатывает один раз за каждый вызов. **Не** срабатывает, если инструмент выбросил необработанное исключение (ошибка перехватывается и возвращается как JSON‑строка ошибки, и `post_tool_call` получает эту строку как `result`).

**Возвратное значение:** Игнорируется.

**Сценарии использования:** Логирование результатов, сбор метрик, отслеживание успешных/неуспешных вызовов, дашборды задержек, оповещения о бюджете per‑tool, отправка уведомлений при завершении конкретных инструментов.

**Пример — отслеживание метрик использования инструментов:**

```python
from collections import Counter, defaultdict
import json

_tool_counts = Counter()
_error_counts = Counter()
_latency_ms = defaultdict(list)

def track_metrics(tool_name, result, duration_ms=0, **kwargs):
    _tool_counts[tool_name] += 1
    _latency_ms[tool_name].append(duration_ms)
    try:
        parsed = json.loads(result)
        if "error" in parsed:
            _error_counts[tool_name] += 1
    except (json.JSONDecodeError, TypeError):
        pass

def register(ctx):
    ctx.register_hook("post_tool_call", track_metrics)
```

---

### `pre_llm_call`

Срабатывает **один раз за ход**, перед началом цикла вызова инструментов. Это **единственный хук**, чьё возвращаемое значение используется — он может вставлять контекст в сообщение пользователя текущего хода.

**Сигнатура обратного вызова:**

```python
def my_callback(session_id: str, user_message: str, conversation_history: list,
                is_first_turn: bool, model: str, platform: str, **kwargs):
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `session_id` | `str` | Уникальный идентификатор текущего сеанса |
| `user_message` | `str` | Исходное сообщение пользователя для этого хода (до любой инъекции навыков) |
| `conversation_history` | `list` | Копия полного списка сообщений (формат OpenAI: `[{"role": "user", "content": "..."}]`) |
| `is_first_turn` | `bool` | `True`, если это первый ход нового сеанса, `False` в последующих |
| `model` | `str` | Идентификатор модели (например `"anthropic/claude-sonnet-4.6"`) |
| `platform` | `str` | Где запущен сеанс: `"cli"`, `"telegram"`, `"discord"` и т.д. |

**Срабатывает:** В `run_agent.py`, внутри `run_conversation()`, после сжатия контекста, но до основного `while`‑цикла. Срабатывает один раз за каждый вызов `run_conversation()` (т.е. один раз за пользовательский ход), а не за каждый API‑вызов внутри цикла инструментов.

**Возвратное значение:** Если обратный вызов возвращает dict с ключом `"context"` или простую непустую строку, текст добавляется к текущему сообщению пользователя. Возврат `None` — без вставки.

```python
# Inject context
return {"context": "Recalled memories:\n- User likes Python\n- Working on hermes-agent"}

# Plain string (equivalent)
return "Recalled memories:\n- User likes Python"

# No injection
return None
```

**Где вставляется контекст:** Всегда в **сообщение пользователя**, никогда в системный промпт. Это сохраняет кэш промпта — системный промпт остаётся одинаковым между ходами, поэтому токены кэша переиспользуются. Системный промпт — это территория Hermes (руководство модели, принудительные инструменты, личность, навыки). Плагины добавляют контекст рядом с вводом пользователя.

Весь вставленный контекст **временный** — добавляется только при вызове API. Оригинальное сообщение пользователя в истории беседы не меняется, и ничего не сохраняется в базе сеанса.

Когда **несколько плагинов** возвращают контекст, их выводы объединяются двойными переводами строки в порядке обнаружения плагинов (алфавитный порядок по имени директории).

**Сценарии использования:** Вспоминание памяти, RAG‑вставка контекста, ограждения, аналитика per‑turn.

**Пример — вспоминание памяти:**

```python
import httpx

MEMORY_API = "https://your-memory-api.example.com"

def recall(session_id, user_message, is_first_turn, **kwargs):
    try:
        resp = httpx.post(f"{MEMORY_API}/recall", json={
            "session_id": session_id,
            "query": user_message,
        }, timeout=3)
        memories = resp.json().get("results", [])
        if not memories:
            return None
        text = "Recalled context:\n" + "\n".join(f"- {m['text']}" for m in memories)
        return {"context": text}
    except Exception:
        return None

def register(ctx):
    ctx.register_hook("pre_llm_call", recall)
```

**Пример — ограждения:**

```python
POLICY = "Never execute commands that delete files without explicit user confirmation."

def guardrails(**kwargs):
    return {"context": POLICY}

def register(ctx):
    ctx.register_hook("pre_llm_call", guardrails)
```

---

### `post_llm_call`

Срабатывает **один раз за ход**, после завершения цикла вызова инструментов и формирования финального ответа агентом. Срабатывает только при **успешных** ходах — не вызывается, если ход был прерван.

**Сигнатура обратного вызова:**

```python
def my_callback(session_id: str, user_message: str, assistant_response: str,
                conversation_history: list, model: str, platform: str, **kwargs):
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `session_id` | `str` | Уникальный идентификатор текущего сеанса |
| `user_message` | `str` | Исходное сообщение пользователя для этого хода |
| `assistant_response` | `str` | Финальный текстовый ответ агента для этого хода |
| `conversation_history` | `list` | Копия полного списка сообщений после завершения хода |
| `model` | `str` | Идентификатор модели |
| `platform` | `str` | Где запущен сеанс |

**Срабатывает:** В `run_agent.py`, внутри `run_conversation()`, после выхода из цикла инструментов. Защищено условием `if final_response and not interrupted` — поэтому не вызывается, когда пользователь прерывает ход или агент достигает лимита итераций без ответа.

**Возвратное значение:** Игнорируется.

**Сценарии использования:** Синхронизация данных беседы с внешней системой памяти, вычисление метрик качества ответа, логирование резюме хода, запуск последующих действий.

**Пример — синхронизация с внешней памятью:**

```python
import httpx

MEMORY_API = "https://your-memory-api.example.com"

def sync_memory(session_id, user_message, assistant_response, **kwargs):
    try:
        httpx.post(f"{MEMORY_API}/store", json={
            "session_id": session_id,
            "user": user_message,
            "assistant": assistant_response,
        }, timeout=5)
    except Exception:
        pass  # best-effort

def register(ctx):
    ctx.register_hook("post_llm_call", sync_memory)
```

**Пример — отслеживание длины ответов:**

```python
import logging
logger = logging.getLogger(__name__)

def log_response_length(session_id, assistant_response, model, **kwargs):
    logger.info("RESPONSE session=%s model=%s chars=%d",
                session_id, model, len(assistant_response or ""))

def register(ctx):
    ctx.register_hook("post_llm_call", log_response_length)
```

---

### `on_session_start`

Срабатывает **один раз**, когда создаётся полностью новый сеанс. Не срабатывает при продолжении существующего сеанса (когда пользователь отправляет второе сообщение).

**Сигнатура обратного вызова:**

```python
def my_callback(session_id: str, model: str, platform: str, **kwargs):
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `session_id` | `str` | Уникальный идентификатор нового сеанса |
| `model` | `str` | Идентификатор модели |
| `platform` | `str` | Где запущен сеанс |

**Срабатывает:** В `run_agent.py`, внутри `run_conversation()`, во время первого хода нового сеанса — конкретно после построения системного промпта, но до начала цикла инструментов. Проверка `if not conversation_history` (отсутствие предыдущих сообщений = новый сеанс).

**Возвратное значение:** Игнорируется.

**Сценарии использования:** Инициализация состояния, привязка кэшей, регистрация сеанса во внешнем сервисе, логирование стартов сеансов.

**Пример — инициализация кэша сеанса:**

```python
_session_caches = {}

def init_session(session_id, model, platform, **kwargs):
    _session_caches[session_id] = {
        "model": model,
        "platform": platform,
        "tool_calls": 0,
        "started": __import__("datetime").datetime.now().isoformat(),
    }

def register(ctx):
    ctx.register_hook("on_session_start", init_session)
```

---

### `on_session_end`

Срабатывает **в самом конце** каждого вызова `run_conversation()`, независимо от результата. Также вызывается из обработчика выхода CLI, если агент был в середине хода при завершении.

**Сигнатура обратного вызова:**

```python
def my_callback(session_id: str, completed: bool, interrupted: bool,
                model: str, platform: str, **kwargs):
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `session_id` | `str` | Идентификатор сеанса |
| `completed` | `bool` | `True`, если агент выдал финальный ответ, `False` иначе |
| `interrupted` | `bool` | `True`, если ход был прерван (пользователь отправил новое сообщение, `/stop` или вышел) |
| `model` | `str` | Идентификатор модели |
| `platform` | `str` | Где запущен сеанс |

**Срабатывает:** В двух местах:
1. **`run_agent.py`** — в конце каждого `run_conversation()`, после всей очистки. Всегда вызывается, даже если ход завершился ошибкой.
2. **`cli.py`** — в обработчике `atexit`, но **только** если агент был в середине хода (`_agent_running=True`) при выходе. Это ловит `Ctrl+C` и `/exit` во время обработки. В этом случае `completed=False` и `interrupted=True`.

**Возвратное значение:** Игнорируется.

**Сценарии использования:** Сброс буферов, закрытие соединений, сохранение состояния сеанса, логирование длительности, очистка ресурсов, инициализированных в `on_session_start`.

**Пример — сброс и очистка:**

```python
_session_caches = {}

def cleanup_session(session_id, completed, interrupted, **kwargs):
    cache = _session_caches.pop(session_id, None)
    if cache:
        # Flush accumulated data to disk or external service
        status = "completed" if completed else ("interrupted" if interrupted else "failed")
        print(f"Session {session_id} ended: {status}, {cache['tool_calls']} tool calls")

def register(ctx):
    ctx.register_hook("on_session_end", cleanup_session)
```

**Пример — отслеживание длительности сеанса:**

```python
import time, logging
logger = logging.getLogger(__name__)

_start_times = {}

def on_start(session_id, **kwargs):
    _start_times[session_id] = time.time()

def on_end(session_id, completed, interrupted, **kwargs):
    start = _start_times.pop(session_id, None)
    if start:
        duration = time.time() - start
        logger.info("SESSION_DURATION session=%s seconds=%.1f completed=%s interrupted=%s",
                     session_id, duration, completed, interrupted)

def register(ctx):
    ctx.register_hook("on_session_start", on_start)
    ctx.register_hook("on_session_end", on_end)
```

---

### `on_session_finalize`

Срабатывает, когда CLI или gateway **завершают** активный сеанс — например, пользователь вводит `/new`, gateway удаляет бездействующий сеанс, или CLI выходит при активном агенте. Это последний шанс сбросить состояние, связанное с уходящим сеансом, до того как его идентификатор исчезнет.

**Сигнатура обратного вызова:**

```python
def my_callback(session_id: str | None, platform: str, **kwargs):
```

| Параметр | Тип | Описание |
|----------|-----|----------|
| `session_id` | `str` или `None` | Идентификатор уходящего сеанса. Может быть `None`, если активного сеанса не было. |
| `platform` | `str` | `"cli"` или название мессенджер‑платформы (`"telegram"`, `"discord"` и т.д.). |

**Срабатывает:** В `cli.py` (при `/new` / выходе CLI) и `gateway/run.py` (при сбросе или удалении сеанса). Всегда сопровождается `on_session_reset` на стороне gateway.

**Возвратное значение:** Игнорируется.

**Сценарии использования:** Сохранение финальных метрик сеанса перед удалением ID, закрытие ресурсов, отправка последнего телеметрического события, сброс очередей записей.

---

### `on_session_reset`

Срабатывает, когда gateway **заменяет** ключ сеанса для активного чата — пользователь вызвал `/new`, `/reset`, `/clear` или адаптер выбрал свежий сеанс после простоя. Позволяет плагинам отреагировать на очистку состояния разговора без ожидания `on_session_start`.

**Сигнатура обратного вызова:**

```python
def my_callback(session_id: str, platform: str, **kwargs):
```

| Параметр | тип | Описание |
|----------|-----|----------|
| `session_id` | `str` | ID нового сеанса (уже заменённый на свежий). |
| `platform` | `str` | Название мессенджер‑платформы. |

**Срабатывает:** В `gateway/run.py`, сразу после выделения нового ключа сеанса, но до обработки следующего входящего сообщения. На gateway порядок такой: `on_session_finalize(old_id)` → swap → `on_session_reset(new_id)` → `on_session_start(new_id)` при первом входящем сообщении.

**Возвратное значение:** Игнорируется.

**Сценарии использования:** Сброс кэшей, привязанных к `session_id`, отправка аналитики о ротации сеанса, подготовка чистого состояния.

---

Смотрите **[Руководство по созданию плагина](/guides/build-a-hermes-plugin)** для полного пошагового описания, включая схемы инструментов, обработчики и продвинутые паттерны хуков.

---

### `subagent_stop`

Срабатывает **один раз за каждый дочерний агент** после завершения `delegate_task`. Независимо от того, делегировал ли ты одну задачу или пакет из трёх, хук вызывается один раз для каждого дочернего процесса, последовательно в потоке родителя.

**Сигнатура обратного вызова:**

```python
def my_callback(parent_session_id: str, child_role: str | None,
                child_summary: str | None, child_status: str,
                duration_ms: int, **kwargs):
```

| Параметр | тип | Описание |
|----------|-----|----------|
| `parent_session_id` | `str` | ID сеанса родительского агента‑делегатора |
| `child_role` | `str \| None` | Тег роли оркестратора, установленный у дочернего (`None`, если функция не включена) |
| `child_summary` | `str \| None` | Финальный ответ, который дочерний агент вернул родителю |
| `child_status` | `str` | `"completed"`, `"failed"`, `"interrupted"` или `"error"` |
| `duration_ms` | `int` | Реальное время работы дочернего агента в миллисекундах |

**Срабатывает:** В `tools/delegate_tool.py`, после того как `ThreadPoolExecutor.as_completed()` обработал все дочерние futures. Вызов происходит в потоке родителя, чтобы авторам хуков не приходилось думать о конкурентных вызовах.

**Возвратное значение:** Игнорируется.

**Сценарии использования:** Логирование оркестрации, суммирование длительности дочерних задач для биллинга, запись аудита после делегирования.

**Пример — логирование активности оркестратора:**

```python
import logging
logger = logging.getLogger(__name__)

def log_subagent(parent_session_id, child_role, child_status, duration_ms, **kwargs):
    logger.info(
        "SUBAGENT parent=%s role=%s status=%s duration_ms=%d",
        parent_session_id, child_role, child_status, duration_ms,
    )

def register(ctx):
    ctx.register_hook("subagent_stop", log_subagent)
```

:::info
При интенсивном делегировании (например, 5 ролей‑оркестраторов × 5 листьев × вложенная глубина) `subagent_stop` вызывается много раз за ход. Делай обратный вызов быстрым; тяжёлую работу отправляй в фон.
:::

---

### `pre_gateway_dispatch`

Срабатывает **один раз за каждый входящий `MessageEvent`** в gateway, после внутренней проверки, но **до** auth/pairing и диспетчеризации агента. Это точка перехвата для политик потока сообщений уровня gateway (окна только‑прослушивания, передача человеку, роутинг per‑chat), которые не укладываются в отдельный адаптер платформы.

**Сигнатура обратного вызова:**

```python
def my_callback(event, gateway, session_store, **kwargs):
```

| Параметр | тип | Описание |
|----------|-----|----------|
| `event` | `MessageEvent` | Нормализованное входящее сообщение (имеет `.text`, `.source`, `.message_id`, `.internal` и т.д.). |
| `gateway` | `GatewayRunner` | Активный объект gateway, чтобы плагины могли вызывать `gateway.adapters[platform].send(...)` для ответов в сторонних каналах (уведомления владельца и пр.). |
| `session_store` | `SessionStore` | Для тихого добавления в транскрипт через `session_store.append_to_transcript(...)`. |

**Срабатывает:** В `gateway/run.py`, внутри `GatewayRunner._handle_message()`, сразу после вычисления `is_internal`. **Внутренние события полностью пропускают хук** (это системные сообщения — завершения фоновых процессов и т.п., которые не должны фильтроваться политиками пользователя).

**Возвратное значение:** `None` или dict. Первый распознанный dict‑action выигрывает; остальные результаты игнорируются. Исключения в обратных вызовах ловятся и логируются; gateway всё равно продолжает обычную диспетчеризацию при ошибке.

| Возврат | Эффект |
|--------|--------|
| `{"action": "skip", "reason": "..."}` | Отбросить сообщение — без ответа агента, без паринга, без auth. Плагин считается обработавшим его (например, тихо записал в транскрипт). |
| `{"action": "rewrite", "text": "new text"}` | Заменить `event.text`, затем продолжить обычный диспетч с изменённым событием. Полезно для объединения буферных сообщений в один запрос. |
| `{"action": "allow"}` / `None` | Обычная диспетчеризация — запускается полный цикл auth / pairing / agent‑loop. |

**Сценарии использования:** Чаты только‑прослушивания (отвечать только при упоминании; буферировать сообщения в контекст), передача человеку (тихо записывать сообщения клиента, пока владелец вручную обрабатывает чат), ограничение скорости per‑profile, роутинг по политике.

**Пример — тихое отбрасывание неавторизованных DM без запуска паринга:**

```python
def deny_unauthorized_dms(event, **kwargs):
    src = event.source
    if src.chat_type == "dm" and not _is_approved_user(src.user_id):
        return {"action": "skip", "reason": "unauthorized-dm"}
    return None

def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", deny_unauthorized_dms)
```

**Пример — перезапись буфера сообщений в один запрос при упоминании:**

```python
_buffers = {}

def buffer_or_rewrite(event, **kwargs):
    key = (event.source.platform, event.source.chat_id)
    buf = _buffers.setdefault(key, [])
    if _bot_mentioned(event.text):
        combined = "\n".join(buf + [event.text])
        buf.clear()
        return {"action": "rewrite", "text": combined}
    buf.append(event.text)
    return {"action": "skip", "reason": "ambient-buffered"}

def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", buffer_or_rewrite)
```

---

### `pre_approval_request`

Срабатывает **непосредственно перед** отображением запроса одобрения пользователю — это охватывает все поверхности: интерактивный CLI, Ink TUI, платформы gateway (Telegram, Discord, Slack, WhatsApp, Matrix и т.д.), а также ACP‑клиенты (VS Code, Zed, JetBrains).

Это место для подключения собственного уведомления — например, macOS‑приложения в строке меню, которое показывает диалог «разрешить/отклонить», или аудита, фиксирующего каждый запрос одобрения с контекстом.

**Сигнатура обратного вызова:**

```python
def my_callback(
    command: str,
    description: str,
    pattern_key: str,
    pattern_keys: list[str],
    session_key: str,
    surface: str,
    **kwargs,
):
```

| Параметр | тип | Описание |
|----------|-----|----------|
| `command` | `str` | Команда оболочки, ожидающая одобрения |
| `description` | `str` | Человекочитаемая причина (объединённая, если совпало несколько шаблонов) |
| `pattern_key` | `str` | Основной ключ шаблона, вызвавшего запрос (например `"rm_rf"`, `"sudo"`) |
| `pattern_keys` | `list[str]` | Все совпавшие ключи шаблонов |
| `session_key` | `str` | Идентификатор сеанса, полезен для ограничения уведомлений per‑chat |
| `surface` | `str` | `"cli"` для интерактивных CLI/TUI‑подсказок, `"gateway"` для асинхронных одобрений платформ |

**Возвратное значение:** игнорируется. Хуки здесь только‑наблюдатели; они не могут вето или предзаполнить ответ одобрения. Для блокировки инструмента до попадания в систему одобрения используйте [`pre_tool_call`](#pre_tool_call).

**Сценарии использования:** Уведомления на рабочем столе, push‑оповещения, аудит, веб‑хуки Slack, эскалация, метрики.

**Пример — уведомление на macOS:**

```python
import subprocess

def notify_approval(command, description, session_key, **kwargs):
    title = "Hermes needs approval"
    body = f"{description}: {command[:80]}"
    subprocess.Popen([
        "osascript", "-e",
        f'display notification "{body}" with title "{title}"',
    ])

def register(ctx):
    ctx.register_hook("pre_approval_request", notify_approval)
```

---

### `post_approval_response`

Срабатывает **после** того, как пользователь ответил на запрос одобрения (или запрос истёк).

**Сигнатура обратного вызова:**

```python
def my_callback(
    command: str,
    description: str,
    pattern_key: str,
    pattern_keys: list[str],
    session_key: str,
    surface: str,
    choice: str,
    **kwargs,
):
```

Такие же kwargs, как в `pre_approval_request`, плюс:

| Параметр | тип | Описание |
|----------|-----|----------|
| `choice` | `str` | Один из `"once"`, `"session"`, `"always"`, `"deny"` или `"timeout"` |

**Возвратное значение:** игнорируется.

**Сценарии использования:** Закрытие уведомления, запись окончательного решения в аудит, обновление метрик, продление лимитов скорости.

```python
def log_decision(command, choice, session_key, **kwargs):
    logger.info("approval %s: %s for session %s", choice, command[:60], session_key)

def register(ctx):
    ctx.register_hook("post_approval_response", log_decision)
```

---

### `transform_tool_result`

Срабатывает **после** возврата инструмента и **до** добавления результата в историю беседы. Позволяет плагину переписать любой результат инструмента — не только вывод терминала — прежде чем модель его увидит.

**Сигнатура обратного вызова:**

```python
def my_callback(
    tool_name: str,
    arguments: dict,
    result: str,
    task_id: str | None,
    **kwargs,
) -> str | None:
```

| Параметр | тип | Описание |
|----------|-----|----------|
| `tool_name` | `str` | Инструмент, который выдал результат (`read_file`, `web_extract`, `delegate_task` и т.д.). |
| `arguments` | `dict` | Аргументы, с которыми модель вызывала инструмент. |
| `result` | `str` | Сырой результат инструмента, после усечения и удаления ANSI‑кодов. |
| `task_id` | `str \| None` | ID задачи/сеанса при работе в RL/benchmark‑окружениях. |

**Возвратное значение:** `str` — заменить результат (то, что увидит модель), `None` — оставить без изменений.

**Сценарии использования:** Удаление PII из `web_extract`, обёртка длинных JSON‑ответов заголовком‑резюме, внедрение подсказок RAG в результаты `read_file`, переоформление отчётов `delegate_task` в схему проекта.

```python
import re
SECRET = re.compile(r"sk-[A-Za-z0-9]{32,}")

def redact_secrets(tool_name, result, **kwargs):
    if SECRET.search(result):
        return SECRET.sub("[REDACTED]", result)
    return None

def register(ctx):
    ctx.register_hook("transform_tool_result", redact_secrets)
```

Применяется ко всем инструментам. Для переписывания только вывода терминала см. `transform_terminal_output` ниже — это более узконаправленный хук, который запускается раньше в пайплайне (до усечения, до редактирования).

---

### `transform_terminal_output`

Срабатывает внутри пайплайна `terminal`‑инструмента, **до** стандартного усечения 50 KB, удаления ANSI‑кодов и редактирования секретов. Позволяет плагинам переписать сырые `stdout`/`stderr` команды до любой дальнейшей обработки.

**Сигнатура обратного вызова:**

```python
def my_callback(
    command: str,
    output: str,
    exit_code: int,
    cwd: str,
    task_id: str | None,
    **kwargs,
) -> str | None:
```

| Параметр | тип | Описание |
|----------|-----|----------|
| `command` | `str` | Команда оболочки, которая сгенерировала вывод. |
| `output` | `str` | Сырой объединённый `stdout`/`stderr` (может быть очень большим — усечение происходит после хука). |
| `exit_code` | `int` | Код завершения процесса. |
| `cwd` | `str` | Рабочий каталог, в котором выполнялась команда. |

**Возвратное значение:** `str` — заменить вывод, `None` — оставить без изменений.

**Сценарии использования:** Добавление резюме к командам с огромным выводом (`du -ah`, `find`, `tree`), маркировка вывода проектным тегом, удаление шумовых временных меток, которые меняются между запусками и ломают кэш промпта.

```python
def summarize_find(command, output, **kwargs):
    if command.startswith("find ") and len(output) > 50_000:
        lines = output.count("\n")
        head = "\n".join(output.splitlines()[:40])
        return f"{head}\n\n[summary: {lines} paths total, showing first 40]"
    return None

def register(ctx):
    ctx.register_hook("transform_terminal_output", summarize_find)
```

Хорошо сочетается с `transform_tool_result` (который покрывает все остальные инструменты).

---

### `transform_llm_output`

Срабатывает **один раз за ход** после завершения цикла вызова инструментов и получения финального ответа модели, **до** доставки этого ответа пользователю (CLI, gateway или программный вызов). Позволяет плагину переписать финальный текст ассистента классическими методами — без дополнительных токенов на SOUL‑инструкции или навыки.

**Сигнатура обратного вызова:**

```python
def my_callback(
    response_text: str,
    session_id: str,
    model: str,
    platform: str,
    **kwargs,
) -> str | None:
```

| Параметр | тип | Описание |
|----------|-----|----------|
| `response_text` | `str` | Финальный текст ответа ассистента за этот ход. |
| `session_id` | `str` | ID сеанса (может быть пустым для одноразовых запусков). |
| `model` | `str` | Название модели, сгенерировавшей ответ (например `anthropic/claude-sonnet-4.6`). |
| `platform` | `str` | Платформа доставки (`cli`, `telegram`, `discord` …; пусто, если не задано). |

**Возвратное значение:** Непустая `str` — заменить текст ответа, `None` или пустая строка — оставить без изменений. **Первый непустой строковый результат выигрывает**, когда зарегистрировано несколько плагинов — аналогично `transform_tool_result`.

**Сценарии использования:** Применение стилистической трансформации (пиратский говор, Спанч Боб), удаление пользовательских идентификаторов из финального текста, добавление подписи проекта, принудительное соблюдение фирменного стиля без траты токенов на SOUL‑инструкции.

```python
import os, re

def spongebob(response_text, **kwargs):
    if os.environ.get("SPONGEBOB_MODE") != "on":
        return None  # pass through unchanged
    return re.sub(r"!", "!! Tartar sauce!", response_text)

def register(ctx):
    ctx.register_hook("transform_llm_output", spongebob)
```

Хук вызывается только при наличии непустого, не прерванного ответа — не срабатывает при прерываниях кнопкой стоп или пустых ходах. Исключения логируются как предупреждения и не ломают выполнение агента.
## Shell Hooks

Объявляй хуки‑скрипты в своём `cli-config.yaml`, и Hermes будет запускать их как подпроцессы каждый раз, когда срабатывает соответствующее событие плагин‑хука — как в CLI, так и в сессиях шлюза. Писать Python‑плагины не требуется.

Используй shell‑хуки, когда нужен простой однофайловый скрипт (Bash, Python, любой с шебангом), который:

- **Блокирует вызов инструмента** — отклонять опасные команды `terminal`, применять политики на уровне каталога, требовать подтверждения для деструктивных операций `write_file` / `patch`.
- **Запускается после вызова инструмента** — автоматически форматировать только что записанные файлы Python или TypeScript, логировать вызовы API, запускать CI‑workflow.
- **Внедряет контекст в следующий ход LLM** — добавлять вывод `git status`, текущий день недели или полученные документы к сообщению пользователя (см. [`pre_llm_call`](#pre_llm_call)).
- **Отслеживает события жизненного цикла** — писать строку в лог, когда суб‑агент завершает работу (`subagent_stop`) или начинается сессия (`on_session_start`).

Shell‑хуки регистрируются вызовом `agent.shell_hooks.register_from_config(cfg)` как при старте CLI (`hermes_cli/main.py`), так и при старте шлюза (`gateway/run.py`). Они естественно сочетаются с хуками Python‑плагинов — оба проходят через один и тот же диспетчер.

### Сравнение в двух словах

| Dimension | Shell hooks | [Plugin hooks](#plugin-hooks) | [Gateway hooks](#gateway-event-hooks) |
|-----------|-------------|-------------------------------|---------------------------------------|
| Объявляются в | блок `hooks:` в `~/.hermes/config.yaml` | `register()` в плагине `plugin.yaml` | `HOOK.yaml` + каталог `handler.py` |
| Хранятся в | `~/.hermes/agent-hooks/` (по соглашению) | `~/.hermes/plugins/<name>/` | `~/.hermes/hooks/<name>/` |
| Язык | Любой (Bash, Python, Go‑бинарник, …) | Только Python | Только Python |
| Запускаются в | CLI + Gateway | CLI + Gateway | Только Gateway |
| События | `VALID_HOOKS` (включая `subagent_stop`) | `VALID_HOOKS` | Жизненный цикл шлюза (`gateway:startup`, `agent:*`, `command:*`) |
| Могут блокировать вызов инструмента | Да (`pre_tool_call`) | Да (`pre_tool_call`) | Нет |
| Могут внедрять контекст LLM | Да (`pre_llm_call`) | Да (`pre_llm_call`) | Нет |
| Согласие | Запрос при первом использовании для каждой пары `(event, command)` | Неявное (доверие к Python‑плагину) | Неявное (доверие к каталогу) |
| Изоляция процессов | Да (подпроцесс) | Нет (внутри процесса) | Нет (внутри процесса) |

### Схема конфигурации

```yaml
hooks:
  <event_name>:                  # Must be in VALID_HOOKS
    - matcher: "<regex>"         # Optional; used for pre/post_tool_call only
      command: "<shell command>" # Required; runs via shlex.split, shell=False
      timeout: <seconds>         # Optional; default 60, capped at 300

hooks_auto_accept: false         # See "Consent model" below
```

Имена событий должны соответствовать одному из [событий плагин‑хуков](#plugin-hooks); опечатки вызывают предупреждение «Did you mean X?», и такие записи пропускаются. Неизвестные ключи внутри отдельной записи игнорируются; отсутствие `command` приводит к пропуску с предупреждением. `timeout > 300` ограничивается с предупреждением.

### JSON‑протокол передачи

Каждый раз, когда событие срабатывает, Hermes порождает подпроцесс для каждого подходящего хука (при условии совпадения), передаёт JSON‑payload в **stdin** и читает **stdout** как JSON.

**stdin — payload, получаемый скриптом:**

```json
{
  "hook_event_name": "pre_tool_call",
  "tool_name":       "terminal",
  "tool_input":      {"command": "rm -rf /"},
  "session_id":      "sess_abc123",
  "cwd":             "/home/user/project",
  "extra":           {"task_id": "...", "tool_call_id": "..."}
}
```

`tool_name` и `tool_input` имеют значение `null` для неинструментальных событий (`pre_llm_call`, `subagent_stop`, жизненный цикл сессии). Словарь `extra` содержит все специфичные для события kwargs (`user_message`, `conversation_history`, `child_role`, `duration_ms`, …). Неподдерживаемые значения сериализуются в строку, а не отбрасываются.

**stdout — необязательный ответ:**

```jsonc
// Block a pre_tool_call (both shapes accepted; normalised internally):
{"decision": "block", "reason":  "Forbidden: rm -rf"}   // Claude-Code style
{"action":   "block", "message": "Forbidden: rm -rf"}   // Hermes-canonical

// Inject context for pre_llm_call:
{"context": "Today is Friday, 2026-04-17"}

// Silent no-op — any empty / non-matching output is fine:
```

Некорректный JSON, ненулевые коды возврата и тайм‑ауты записываются в лог как предупреждения, но не прерывают цикл агента.

### Примеры

#### 1. Автоформатирование Python‑файлов после каждой записи

```yaml
# ~/.hermes/config.yaml
hooks:
  post_tool_call:
    - matcher: "write_file|patch"
      command: "~/.hermes/agent-hooks/auto-format.sh"
```

```bash
#!/usr/bin/env bash
# ~/.hermes/agent-hooks/auto-format.sh
payload="$(cat -)"
path=$(echo "$payload" | jq -r '.tool_input.path // empty')
[[ "$path" == *.py ]] && command -v black >/dev/null && black "$path" 2>/dev/null
printf '{}\n'
```

Внутренний вид файла, который агент видит в контексте, **не** перечитывается автоматически — переоформление затрагивает только файл на диске. Последующие вызовы `read_file` получат уже отформатированную версию.

#### 2. Блокировка деструктивных команд `terminal`

```yaml
hooks:
  pre_tool_call:
    - matcher: "terminal"
      command: "~/.hermes/agent-hooks/block-rm-rf.sh"
      timeout: 5
```

```bash
#!/usr/bin/env bash
# ~/.hermes/agent-hooks/block-rm-rf.sh
payload="$(cat -)"
cmd=$(echo "$payload" | jq -r '.tool_input.command // empty')
if echo "$cmd" | grep -qE 'rm[[:space:]]+-rf?[[:space:]]+/'; then
  printf '{"decision": "block", "reason": "blocked: rm -rf / is not permitted"}\n'
else
  printf '{}\n'
fi
```

#### 3. Внедрение `git status` в каждый ход (аналог Claude‑Code `UserPromptSubmit`)

```yaml
hooks:
  pre_llm_call:
    - command: "~/.hermes/agent-hooks/inject-cwd-context.sh"
```

```bash
#!/usr/bin/env bash
# ~/.hermes/agent-hooks/inject-cwd-context.sh
cat - >/dev/null   # discard stdin payload
if status=$(git status --porcelain 2>/dev/null) && [[ -n "$status" ]]; then
  jq --null-input --arg s "$status" \
     '{context: ("Uncommitted changes in cwd:\n" + $s)}'
else
  printf '{}\n'
fi
```

Событие `UserPromptSubmit` в Claude Code намеренно не реализовано как отдельный Hermes‑хук — `pre_llm_call` срабатывает в том же месте и уже поддерживает внедрение контекста. Используй его здесь.

#### 4. Логирование завершения каждого суб‑агента

```yaml
hooks:
  subagent_stop:
    - command: "~/.hermes/agent-hooks/log-orchestration.sh"
```

```bash
#!/usr/bin/env bash
# ~/.hermes/agent-hooks/log-orchestration.sh
log=~/.hermes/logs/orchestration.log
jq -c '{ts: now, parent: .session_id, extra: .extra}' < /dev/stdin >> "$log"
printf '{}\n'
```

### Модель согласия

Каждая уникальная пара `(event, command)` вызывает запрос у пользователя при первом появлении, после чего решение сохраняется в `~/.hermes/shell-hooks-allowlist.json`. Последующие запуски (CLI или шлюз) пропускают запрос.

Три способа обойти интерактивный запрос — достаточно любого из них:

1. Флаг `--accept-hooks` в CLI (например, `hermes --accept-hooks chat`)
2. Переменная окружения `HERMES_ACCEPT_HOOKS=1`
3. `hooks_auto_accept: true` в `cli-config.yaml`

Для запусков без TTY (gateway, cron, CI) нужен один из этих вариантов — иначе новые хуки останутся незарегистрированными и будет выдано предупреждение.

**Изменения скриптов считаются доверенными.** В списке разрешений хранится точная строка команды, а не хеш скрипта, поэтому правка файла на диске не аннулирует согласие. `hermes hooks doctor` проверяет отклонения времени изменения (mtime), позволяя увидеть правки и решить, нужно ли переутвердить.

### CLI `hermes hooks`

| Command | Что делает |
|---------|------------|
| `hermes hooks list` | Выводит настроенные хуки с их матчером, тайм‑аутом и статусом согласия |
| `hermes hooks test <event> [--for-tool X] [--payload-file F]` | Запускает каждый подходящий хук на синтетическом payload и печатает разобранный ответ |
| `hermes hooks revoke <command>` | Удаляет все записи allowlist, соответствующие `<command>` (вступает в силу после перезапуска) |
| `hermes hooks doctor` | Для каждого настроенного хука проверяет бит исполнения, статус в allowlist, отклонение mtime, корректность JSON‑вывода и примерное время выполнения |

### Безопасность

Shell‑хуки работают с **полными пользовательскими учётными данными** — та же граница доверия, что и у записи cron или алиаса оболочки. Относись к блоку `hooks:` в `config.yaml` как к привилегированной конфигурации:

- Ссылайся только на скрипты, написанные тобой или полностью проверенные.
- Храни скрипты внутри `~/.hermes/agent-hooks/`, чтобы путь было легко аудировать.
- После получения общей конфигурации запускай `hermes hooks doctor`, чтобы увидеть новые хуки до их регистрации.
- Если `config.yaml` находится под версионным контролем в команде, проверяй PR‑ы, меняющие секцию `hooks:`, так же, как проверяешь конфиги CI.

### Порядок и приоритет

И Python‑плагин‑хуки, и shell‑хуки проходят через один диспетчер `invoke_hook()`. Сначала регистрируются Python‑плагины (`discover_and_load()`), затем shell‑хуки (`register_from_config()`), поэтому решения Python‑хуков `pre_tool_call` имеют приоритет в случае конфликта. Первый валидный блок выигрывает — агрегатор возвращает сразу, как только любой коллбэк выдаёт `{"action": "block", "message": str}` с непустым сообщением.