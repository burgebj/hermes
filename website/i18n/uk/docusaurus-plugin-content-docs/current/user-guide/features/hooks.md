---
sidebar_position: 6
title: "Гачки подій"
description: "Запускай кастомний код у ключових точках життєвого циклу — записуй активність, надсилай сповіщення, публікуй у webhooks"
---

# Події (Event Hooks)

Hermes має три системи хуків, які виконують користувацький код у ключових точках життєвого циклу:

| Система | Реєструється через | Працює в | Випадок використання |
|--------|--------------------|----------|----------------------|
| **[Gateway hooks](#gateway-event-hooks)** | `HOOK.yaml` + `handler.py` у `~/.hermes/hooks/` | лише Gateway | Логування, сповіщення, вебхуки |
| **[Plugin hooks](#plugin-hooks)** | `ctx.register_hook()` у [plugin](/user-guide/features/plugins) | CLI + Gateway | Перехоплення інструментів, метрики, захисні механізми |
| **[Shell hooks](#shell-hooks)** | блок `hooks:` у `~/.hermes/config.yaml`, що вказує на shell‑скрипти | CLI + Gateway | Додаткові скрипти для блокування, автоформатування, інжекції контексту |

Усі три системи працюють у неблокуючому режимі — помилки в будь‑якому хуці перехоплюються та записуються в журнал, не призводячи до падіння агента.
## Gateway Event Hooks

Gateway hooks fire automatically during gateway operation (Telegram, Discord, Slack, WhatsApp, Teams) without blocking the main agent pipeline.

### Creating a Hook

Each hook is a directory under `~/.hermes/hooks/` containing two files:

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

The `events` list determines which events trigger your handler. You can subscribe to any combination of events, including wildcards like `command:*`.

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

**Handler rules:**
- Must be named `handle`
- Receives `event_type` (string) and `context` (dict)
- Can be `async def` or regular `def` — both work
- Errors are caught and logged, never crashing the agent

### Available Events

| Event | When it fires | Context keys |
|-------|---------------|--------------|
| `gateway:startup` | Gateway process starts | `platforms` (list of active platform names) |
| `session:start` | New messaging session created | `platform`, `user_id`, `session_id`, `session_key` |
| `session:end` | Session ended (before reset) | `platform`, `user_id`, `session_key` |
| `session:reset` | User ran `/new` or `/reset` | `platform`, `user_id`, `session_key` |
| `agent:start` | Agent begins processing a message | `platform`, `user_id`, `session_id`, `message` |
| `agent:step` | Each iteration of the tool‑calling loop | `platform`, `user_id`, `session_id`, `iteration`, `tool_names` |
| `agent:end` | Agent finishes processing | `platform`, `user_id`, `session_id`, `message`, `response` |
| `command:*` | Any slash command executed | `platform`, `user_id`, `command`, `args` |

#### Wildcard Matching

Handlers registered for `command:*` fire for any `command:` event (`command:model`, `command:reset`, etc.). Monitor all slash commands with a single subscription.

### Examples

#### Telegram Alert on Long Tasks

Send yourself a message when the agent takes more than 10 steps:

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

#### Command Usage Logger

Track which slash commands are used:

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

#### Session Start Webhook

POST to an external service on new sessions:

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

### Tutorial: BOOT.md — Run a Startup Checklist on Every Gateway Boot

A popular pattern from the community: drop a Markdown checklist at `~/.hermes/BOOT.md`, and have the agent run it once every time the gateway starts. Useful for “on every boot, check overnight cron failures and ping me on Discord if anything failed,” or “summarize the last 24 h of deploy.log and post it to Slack #ops.”

This tutorial shows how to build it yourself as a user‑defined hook. Hermes does not ship a built‑in BOOT.md hook — you wire up exactly the behavior you want.

#### What we're building

1. A file at `~/.hermes/BOOT.md` with natural‑language startup instructions.
2. A gateway hook that fires on `gateway:startup`, spawns a one‑shot agent with your gateway’s resolved model/credentials, and runs the BOOT.md instructions.
3. A `[SILENT]` convention so the agent can opt out of sending a message when there’s nothing to report.

#### Step 1: Write your checklist

Create `~/.hermes/BOOT.md`. Write it as if you were giving instructions to a human assistant:

```markdown
# Startup Checklist

1. Run `hermes cron list` and check if any scheduled jobs failed overnight.
2. If any failed, send a summary to Discord #ops using the `send_message` tool.
3. Check if `/opt/app/deploy.log` has any ERROR lines from the last 24 hours. If yes, summarize them and include in the same Discord message.
4. If nothing went wrong, reply with only `[SILENT]` so no message is sent.
```

The agent sees this as part of its prompt, so anything you can describe in plain language works — tool calls, shell commands, sending messages, summarizing files.

#### Step 2: Create the hook

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

The two key lines:

- `_resolve_gateway_model()` reads the gateway’s currently‑configured model.
- `_resolve_runtime_agent_kwargs()` resolves provider credentials the same way a normal gateway turn does — including API keys, base URLs, OAuth tokens, and credential pools.

Without these, a bare `AIAgent()` falls back to built‑in defaults and will return 401 against any non‑default endpoint.

#### Step 3: Test it

Restart the gateway:

```bash
hermes gateway restart
```

Watch the logs:

```bash
hermes logs --follow --level INFO | grep boot-md
```

You should see `Running BOOT.md (N chars)` followed by either `boot‑md completed: …` (summary of what the agent did) or `boot‑md completed (nothing to report)` when the agent replied `[SILENT]`.

Delete `~/.hermes/BOOT.md` to disable the checklist — the hook stays loaded but silently skips when the file isn’t there.

#### Extending the pattern

- **Schedule‑aware checklists:** key off `datetime.now().weekday()` inside BOOT.md’s instructions (“if it’s Monday, also check the weekly deploy log”). The instructions are free‑form text, so anything the agent can reason about is fair game.
- **Multiple checklists:** point the hook at a different file (`STARTUP.md`, `MORNING.md`, etc.) and register separate hook directories for each.
- **Non‑agent variant:** if you don’t need a full agent loop, skip `AIAgent` entirely and have the handler post a fixed notification directly via `httpx`. Cheaper, faster, and has no provider dependency.

#### Why this isn’t a built‑in

An earlier version of Hermes shipped this as a built‑in hook and silently spawned an agent with bare defaults on every gateway boot. That surprised users with custom endpoints and made the feature invisible to users who didn’t know it was running. Keeping it as a documented pattern — built by you, in your hooks directory — means you see exactly what it does and opt‑in by writing the files.

### How It Works

1. On gateway startup, `HookRegistry.discover_and_load()` scans `~/.hermes/hooks/`
2. Each subdirectory with `HOOK.yaml` + `handler.py` is loaded dynamically
3. Handlers are registered for their declared events
4. At each lifecycle point, `hooks.emit()` fires all matching handlers
5. Errors in any handler are caught and logged — a broken hook never crashes the agent

:::info
Gateway hooks only fire in the **gateway** (Telegram, Discord, Slack, WhatsApp, Teams). The CLI does not load gateway hooks. For hooks that work everywhere, use [plugin hooks](#plugin-hooks).
:::
## Plugin Hooks

[Plugins](/user-guide/features/plugins) можуть реєструвати хуки, які спрацьовують у **обох CLI і gateway** сесіях. Вони реєструються програмно через `ctx.register_hook()` у функції `register()` вашого плагіна.

```python
def register(ctx):
    ctx.register_hook("pre_tool_call", my_tool_observer)
    ctx.register_hook("post_tool_call", my_tool_logger)
    ctx.register_hook("pre_llm_call", my_memory_callback)
    ctx.register_hook("post_llm_call", my_sync_callback)
    ctx.register_hook("on_session_start", my_init_callback)
    ctx.register_hook("on_session_end", my_cleanup_callback)
```

**Загальні правила для всіх хуків:**

- Колбеки отримують **іменовані аргументи**. Завжди приймай `**kwargs` для сумісності вперед — нові параметри можуть бути додані в майбутніх версіях без порушення роботи вашого плагіна.
- Якщо колбек **викличе виключення**, це буде записано в журнал і пропущено. Інші хуки та агент продовжують працювати нормально. Плагін, що поводиться некоректно, ніколи не зможе зламати агент.
- Повернені значення двох хуків впливають на поведінку: [`pre_tool_call`](#pre_tool_call) може **заблокувати** інструмент, а [`pre_llm_call`](#pre_llm_call) може **вставити контекст** у виклик LLM. Всі інші хуки — це спостерігачі типу fire-and-forget.
### Коротке посилання

| Hook | Виконується коли | Повертає |
|------|-------------------|----------|
| [`pre_tool_call`](#pre_tool_call) | Перед будь‑яким виконанням інструменту | `{"action": "block", "message": str}` щоб відхилити виклик |
| [`post_tool_call`](#post_tool_call) | Після повернення будь‑якого інструменту | ігнорується |
| [`pre_llm_call`](#pre_llm_call) | Один раз за хід, перед циклом виклику інструментів | `{"context": str}` щоб додати контекст до повідомлення користувача |
| [`post_llm_call`](#post_llm_call) | Один раз за хід, після циклу виклику інструментів | ігнорується |
| [`on_session_start`](#on_session_start) | Створено нову сесію (лише перший хід) | ігнорується |
| [`on_session_end`](#on_session_end) | Сесія завершується | ігнорується |
| [`on_session_finalize`](#on_session_finalize) | CLI/шлюз завершує активну сесію (очищення, збереження, статистика) | ігнорується |
| [`on_session_reset`](#on_session_reset) | Шлюз замінює ключ сесії на новий (наприклад, `/new`, `/reset`) | ігнорується |
| [`subagent_stop`](#subagent_stop) | Дочірній процес `delegate_task` завершився | ігнорується |
| [`pre_gateway_dispatch`](#pre_gateway_dispatch) | Шлюз отримав повідомлення користувача, перед автентифікацією та розподілом | `{"action": "skip" \| "rewrite" \| "allow", ...}` щоб вплинути на потік |
| [`pre_approval_request`](#pre_approval_request) | Небезпечна команда потребує схвалення користувача, перед відправкою запиту/повідомлення | ігнорується |
| [`post_approval_response`](#post_approval_response) | Користувач відповів на запит схвалення (або час вичерпано) | ігнорується |
| [`transform_tool_result`](#transform_tool_result) | Після повернення будь‑якого інструменту, перед передачею результату моделі | `str` щоб замінити результат, `None` щоб залишити без змін |
| [`transform_terminal_output`](#transform_terminal_output) | В інструменті `terminal`, перед обрізанням/видаленням ANSI/редагуванням | `str` щоб замінити сирий вивід, `None` щоб залишити без змін |
| [`transform_llm_output`](#transform_llm_output) | Після завершення циклу виклику інструментів, перед доставкою остаточної відповіді | `str` щоб замінити текст відповіді, `None`/empty щоб залишити без змін |
### `pre_tool_call`

Виконується **негайно перед** кожним викликом інструмента — як вбудованих, так і інструментів‑плагінів.

**Сигнатура колбеку:**

```python
def my_callback(tool_name: str, args: dict, task_id: str, **kwargs):
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `tool_name` | `str` | Назва інструмента, який збираються виконати (наприклад, `"terminal"`, `"web_search"`, `"read_file"`) |
| `args` | `dict` | Аргументи, які модель передала інструменту |
| `task_id` | `str` | Ідентифікатор сесії/завдання. Порожній рядок, якщо не встановлено. |

**Викликається:** У `model_tools.py`, всередині `handle_function_call()`, перед запуском обробника інструмента. Викликається один раз для кожного виклику інструмента — якщо модель викликає 3 інструменти паралельно, це відбудеться 3 рази.

**Повертає значення — вето виклику:**

```python
return {"action": "block", "message": "Reason the tool call was blocked"}
```

Агент перериває виконання інструмента, повертаючи `message` як помилку, яку отримує модель. Перший підходящий блок‑директива виграє (спочатку зареєстровані Python‑плагіни, потім shell‑hooks). Будь‑яке інше повернуте значення ігнорується, тому існуючі колбеки лише‑для‑спостерігачів продовжують працювати без змін.

**Випадки використання:** Логування, аудит, підрахунок викликів інструментів, блокування небезпечних операцій, обмеження швидкості, застосування політик per‑user.

**Приклад — журнал аудиту викликів інструментів:**

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

**Приклад — попередження про небезпечні інструменти:**

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

Виконується **негайно після** повернення результату кожного виконання інструменту.

**Підпис зворотного виклику:**

```python
def my_callback(tool_name: str, args: dict, result: str, task_id: str,
                duration_ms: int, **kwargs):
```

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `tool_name` | `str` | Назва інструменту, який щойно виконався |
| `args` | `dict` | Аргументи, які модель передала інструменту |
| `result` | `str` | Повернене значення інструменту (завжди рядок JSON) |
| `task_id` | `str` | Ідентифікатор сесії/завдання. Порожній рядок, якщо не встановлено. |
| `duration_ms` | `int` | Час, який зайняло виконання інструменту, у мілісекундах (вимірюється за допомогою `time.monotonic()` навколо `registry.dispatch()`). |

**Викликається:** У `model_tools.py`, всередині `handle_function_call()`, після повернення результату обробника інструменту. Викликається один раз для кожного виклику інструменту. **Не викликається**, якщо інструмент підняв необроблене виключення (помилка перехоплюється і повертається як рядок JSON‑помилки, і `post_tool_call` викликається з цим рядком помилки як `result`).

**Повернене значення:** Ігнорується.

**Випадки використання:** Логування результатів інструментів, збір метрик, відстеження успішності/невдач інструментів, панелі затримок, сповіщення про перевищення бюджету на окремі інструменти, надсилання повідомлень, коли завершуються конкретні інструменти.

**Приклад — відстеження метрик використання інструменту:**

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

Виконується **один раз за хід**, перед тим, як розпочнеться цикл виклику інструментів. Це **єдиний хук, значення якого використовується** — він може вставляти контекст у повідомлення користувача поточного ходу.

**Підпис колбеку:**

```python
def my_callback(session_id: str, user_message: str, conversation_history: list,
                is_first_turn: bool, model: str, platform: str, **kwargs):
```

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `session_id` | `str` | Унікальний ідентифікатор поточної сесії |
| `user_message` | `str` | Початкове повідомлення користувача для цього ходу (до будь‑якої інжекції інструменту) |
| `conversation_history` | `list` | Копія повного списку повідомлень (формат OpenAI: `[{"role": "user", "content": "..."}]`) |
| `is_first_turn` | `bool` | `True`, якщо це перший хід нової сесії, `False` — у наступних ходах |
| `model` | `str` | Ідентифікатор моделі (наприклад, `"anthropic/claude-sonnet-4.6"`) |
| `platform` | `str` | Де запущена сесія: `"cli"`, `"telegram"`, `"discord"` тощо. |

**Виконується:** У `run_agent.py`, всередині `run_conversation()`, після стиснення контексту, але перед основним циклом `while`. Виконується один раз за виклик `run_conversation()` (тобто один раз за хід користувача), а не один раз за API‑виклик у циклі інструменту.

**Повернене значення:** Якщо колбек повертає словник з ключем `"context"` або простий непорожній рядок, текст додається до повідомлення користувача поточного ходу. Поверни `None`, якщо інжекція не потрібна.

```python
# Inject context
return {"context": "Recalled memories:\n- User likes Python\n- Working on hermes-agent"}

# Plain string (equivalent)
return "Recalled memories:\n- User likes Python"

# No injection
return None
```

**Куди інжектується контекст:** Завжди у **повідомлення користувача**, ніколи у системний промпт. Це зберігає кеш промпту — системний промпт залишається ідентичним у всіх ходах, тому кешовані токени повторно використовуються. Системний промпт — територія Hermes (настанови моделі, примус інструментів, особистість, навички). Плагіни додають контекст разом із вхідними даними користувача.

Весь інжектований контекст **тимчасовий** — додається лише під час виклику API. Початкове повідомлення користувача в історії розмови ніколи не змінюється, і нічого не зберігається у базі даних сесії.

Коли **кілька плагінів** повертають контекст, їхні результати об’єднуються подвоєними переносами рядка у порядку виявлення плагінів (алфавітно за назвою каталогу).

**Випадки використання:** Пам'ять, інжекція контексту RAG, запасний (варіант) / фолбек, аналітика за ходом.

**Приклад — відновлення пам'яті:**

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

**Приклад — запасний (варіант) / фолбек:**

```python
POLICY = "Never execute commands that delete files without explicit user confirmation."

def guardrails(**kwargs):
    return {"context": POLICY}

def register(ctx):
    ctx.register_hook("pre_llm_call", guardrails)
```

---
### `post_llm_call`

Виконується **один раз за хід**, після завершення циклу виклику інструментів, коли агент сформував остаточну відповідь. Спрацьовує лише на **успішних** ходах — не виконується, якщо хід був перерваний.

**Сигнатура зворотного виклику:**

```python
def my_callback(session_id: str, user_message: str, assistant_response: str,
                conversation_history: list, model: str, platform: str, **kwargs):
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | `str` | Унікальний ідентифікатор поточної сесії |
| `user_message` | `str` | Початкове повідомлення користувача для цього ходу |
| `assistant_response` | `str` | Остаточна текстова відповідь агента для цього ходу |
| `conversation_history` | `list` | Копія повного списку повідомлень після завершення ходу |
| `model` | `str` | Ідентифікатор моделі |
| `platform` | `str` | Платформа, на якій запущена сесія |

**Коли спрацьовує:** У `run_agent.py`, всередині `run_conversation()`, після того, як цикл інструментів завершується остаточною відповіддю. Захищено умовою `if final_response and not interrupted` — тому **не** виконується, коли користувач перериває хід посередині або агент досягає ліміту ітерацій без відповіді.

**Повернене значення:** ігнорується.

**Випадки використання:** Синхронізація даних розмови з зовнішньою системою пам’яті, обчислення метрик якості відповіді, журналювання підсумків ходів, ініціювання подальших дій.

**Приклад — синхронізація з зовнішньою пам’яттю:**

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

**Приклад — відстеження довжини відповідей:**

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

Виконується **один раз**, коли створюється абсолютно нова сесія. **Не** виконується при продовженні сесії (коли користувач надсилає друге повідомлення в існуючій сесії).

**Підпис зворотного виклику:**

```python
def my_callback(session_id: str, model: str, platform: str, **kwargs):
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | `str` | Унікальний ідентифікатор нової сесії |
| `model` | `str` | Ідентифікатор моделі |
| `platform` | `str` | Де виконується сесія |

**Виконується:** У `run_agent.py`, всередині `run_conversation()`, під час першого кроку нової сесії — саме після формування системної підказки, але перед запуском циклу інструментів. Перевірка виглядає так: `if not conversation_history` (немає попередніх повідомлень = нова сесія).

**Повернене значення:** Ігнорується.

**Випадки використання:** Ініціалізація стану, прив’язаного до сесії, прогрівання кешів, реєстрація сесії в зовнішньому сервісі, журналювання запуску сесій.

**Приклад — ініціалізація кешу сесії:**

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

Викликається **саме в кінці** кожного виклику `run_conversation()`, незалежно від результату. Також викликається з обробника виходу CLI, якщо агент був у середині ходу, коли користувач вийшов.

**Підпис зворотного виклику:**

```python
def my_callback(session_id: str, completed: bool, interrupted: bool,
                model: str, platform: str, **kwargs):
```

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `session_id` | `str` | Унікальний ідентифікатор сесії |
| `completed` | `bool` | `True`, якщо агент створив остаточну відповідь, `False` — інакше |
| `interrupted` | `bool` | `True`, якщо хід був перерваний (користувач надіслав нове повідомлення, `/stop` або вийшов) |
| `model` | `str` | Ідентифікатор моделі |
| `platform` | `str` | Де виконується сесія |

**Викликається:** У двох місцях:
1. **`run_agent.py`** — у кінці кожного виклику `run_conversation()`, після усієї очистки. Завжди викликається, навіть якщо під час ходу сталася помилка.
2. **`cli.py`** — у обробнику `atexit` CLI, але **лише**, якщо агент був у середині ходу (`_agent_running=True`) під час виходу. Це ловить `Ctrl+C` та `/exit` під час обробки. У цьому випадку `completed=False` і `interrupted=True`.

**Повернене значення:** Ігнорується.

**Випадки використання:** Скидання буферів, закриття з’єднань, збереження стану сесії, журналювання тривалості сесії, очистка ресурсів, ініційованих у `on_session_start`.

**Приклад — скидання та очистка:**

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

**Приклад — відстеження тривалості сесії:**

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
### `on_session_finalize`

Викликається, коли CLI або шлюз **завершує** активну сесію — наприклад, коли користувач виконує `/new`, шлюз виконує збір сміття (GC) неактивної сесії або CLI завершується з активним агентом. Це остання можливість записати стан, пов’язаний із вихідною сесією, перед тим як її ідентифікатор зникне.

**Підпис колбеку:**

```python
def my_callback(session_id: str | None, platform: str, **kwargs):
```

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `session_id` | `str` або `None` | Ідентифікатор вихідної сесії. Може бути `None`, якщо активної сесії не існувало. |
| `platform` | `str` | `"cli"` або назва платформи обміну повідомленнями (`"telegram"`, `"discord"` тощо). |

**Викликається:** у `cli.py` (при `/new` / виході CLI) та `gateway/run.py` (коли сесія скидається або збирається сміттям). Завжди супроводжується `on_session_reset` на стороні шлюзу.

**Повернене значення:** ігнорується.

**Випадки використання:** зберегти фінальні метрики сесії перед тим, як ідентифікатор сесії буде відкинуто, закрити ресурси, прив’язані до сесії, випустити фінальну телеметричну подію, спустошити чергу записів.
### `on_session_reset`

Викликається, коли шлюз **замінює новий ключ сесії** для активного чату — користувач викликав `/new`, `/reset`, `/clear` або адаптер вибрав нову сесію після періоду бездіяльності. Це дозволяє плагінам реагувати на те, що стан розмови був стертий, не чекаючи наступного `on_session_start`.

**Підпис зворотного виклику:**

```python
def my_callback(session_id: str, platform: str, **kwargs):
```

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `session_id` | `str` | Ідентифікатор нової сесії (вже оновлений до нового значення). |
| `platform` | `str` | Назва платформи обміну повідомленнями. |

**Викликається:** У `gateway/run.py` одразу після виділення нового ключа сесії, але до обробки наступного вхідного повідомлення. На шлюзі порядок такий: `on_session_finalize(old_id)` → swap → `on_session_reset(new_id)` → `on_session_start(new_id)` на першому вхідному ході.

**Повернене значення:** Ігнорується.

**Випадки використання:** Скидання кешів, прив’язаних до `session_id`, надсилання аналітики про оновлення сесії, підготовка нового сховища стану.

---

Дивись **[Build a Plugin guide](/guides/build-a-hermes-plugin)** для повного покрокового опису, включаючи схеми інструментів, обробники та розширені шаблони хуків.
### `subagent_stop`

Викликається **один раз для кожного дочірнього агента** після завершення `delegate_task`. Незалежно від того, чи делегував ти одну задачу, чи пакет з трьох, цей хук спрацьовує один раз для кожного дочірнього агента, послідовно у потоці батька.

**Підпис зворотного виклику:**

```python
def my_callback(parent_session_id: str, child_role: str | None,
                child_summary: str | None, child_status: str,
                duration_ms: int, **kwargs):
```

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `parent_session_id` | `str` | Ідентифікатор сесії делегуючого батьківського агента |
| `child_role` | `str \| None` | Тег ролі оркестратора, встановлений у дочірньому агенті (`None`, якщо функція не ввімкнена) |
| `child_summary` | `str \| None` | Остаточна відповідь, яку дочірній агент повернув батькові |
| `child_status` | `str` | `"completed"`, `"failed"`, `"interrupted"` або `"error"` |
| `duration_ms` | `int` | Реальний час у мілісекундах, витрачений на виконання дочірнього агента |

**Викликається:** У `tools/delegate_tool.py` після того, як `ThreadPoolExecutor.as_completed()` виснажує всі дочірні future. Виклик передається у потік батька, щоб авторам хуків не доводилося розбиратися з одночасним виконанням зворотних викликів.

**Повернене значення:** Ігнорується.

**Випадки використання:** Логування активності оркестрації, накопичення тривалості дочірніх процесів для білінгу, запис аудиту після делегування.

**Приклад — логування активності оркестратора:**

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
При інтенсивному делегуванні (наприклад, ролі оркестратора × 5 листків × вкладена глибина) `subagent_stop` спрацьовує багато разів за один хід. Тримай свій зворотний виклик швидким; важкі операції перенось у фонову чергу.
:::
### `pre_gateway_dispatch`

Виконується **один раз для кожного вхідного `MessageEvent`** у шлюзі, після внутрішньої перевірки, але **до** автентифікації/парування та диспетчеризації агенту. Це точка перехоплення для політик потоків повідомлень на рівні шлюзу (вікна лише‑прослуховування, передача людям, маршрутизація за чатами тощо), які не вписуються у жоден окремий адаптер платформи.

**Підпис колбеку:**

```python
def my_callback(event, gateway, session_store, **kwargs):
```

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `event` | `MessageEvent` | Нормалізоване вхідне повідомлення (містить `.text`, `.source`, `.message_id`, `.internal` тощо). |
| `gateway` | `GatewayRunner` | Активний runner шлюзу, щоб плагіни могли викликати `gateway.adapters[platform].send(...)` для відповідей у боковому каналі (повідомлення власнику тощо). |
| `session_store` | `SessionStore` | Для тихого додавання до транскрипту через `session_store.append_to_transcript(...)`. |

**Виконується:** У `gateway/run.py`, всередині `GatewayRunner._handle_message()`, одразу після обчислення `is_internal`. **Внутрішні події повністю пропускаються** (вони генеруються системою — завершення фонового процесу тощо — і не повинні підлягати політиці шлюзу).

**Повертає:** `None` або словник. Перший розпізнаний словник дії виграє; решта результатів плагінів ігнорується. Виключення в колбеках плагінів ловляться та логуються; у випадку помилки шлюз завжди продовжує звичайну диспетчеризацію.

| Повернення | Ефект |
|--------|--------|
| `{"action": "skip", "reason": "..."}` | Відкинути повідомлення — без відповіді агента, без процесу парування, без автентифікації. Припускається, що плагін уже обробив його (наприклад, тихо додав у транскрипт). |
| `{"action": "rewrite", "text": "new text"}` | Замінити `event.text`, потім продовжити звичайну диспетчеризацію з модифікованим подією. Корисно для об’єднання буферизованих навколишніх повідомлень в один запит. |
| `{"action": "allow"}` / `None` | Звичайна диспетчеризація — запускає повний ланцюжок автентифікації / парування / цикл агента. |

**Випадки використання:** Чати лише для прослуховування (відповідати лише при згадці; буферизувати навколишні повідомлення в контекст); передача людям (тихо додавати повідомлення клієнта, поки власник обробляє чат вручну); обмеження швидкості за профілем; маршрутизація за політикою.

**Приклад — тихо відкинути неавторизовані прямі повідомлення без запуску коду парування:**

```python
def deny_unauthorized_dms(event, **kwargs):
    src = event.source
    if src.chat_type == "dm" and not _is_approved_user(src.user_id):
        return {"action": "skip", "reason": "unauthorized-dm"}
    return None

def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", deny_unauthorized_dms)
```

**Приклад — перезаписати буфер навколишніх повідомлень в один запит при згадці:**

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

Виконується **одразу перед** тим, як запит на схвалення показується користувачеві — охоплює всі поверхні: інтерактивний CLI, Ink TUI, gateway‑платформи (Telegram, Discord, Slack, WhatsApp, Matrix тощо) та клієнти ACP (VS Code, Zed, JetBrains).

Саме тут можна підключити власний нотіфікатор — наприклад, macOS‑додаток у рядку меню, який виводить сповіщення «дозволити/відхилити», або журнал аудиту, що записує кожен запит на схвалення разом із контекстом.

**Підписка колбеку:**

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

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | `str` | Shell‑команда, що очікує схвалення |
| `description` | `str` | Людсько‑читабельна причина(и), чому команда позначена (об’єднуються, коли збігаються кілька шаблонів) |
| `pattern_key` | `str` | Основний ключ шаблону, який спрацював (наприклад, `"rm_rf"`, `"sudo"`) |
| `pattern_keys` | `list[str]` | Всі ключі шаблонів, які збіглися |
| `session_key` | `str` | Ідентифікатор сесії, корисний для розмежування сповіщень за чатами |
| `surface` | `str` | `"cli"` для інтерактивних підказок CLI/TUI, `"gateway"` для асинхронних схвалень на платформах |

**Повернене значення:** ігнорується. Хуки тут лише спостерігачі; вони не можуть відхилити чи заздалегідь відповісти на схвалення. Щоб заблокувати інструмент до того, як він потрапить у систему схвалення, використай [`pre_tool_call`](#pre_tool_call).

**Випадки використання:** сповіщення на робочому столі, push‑повідомлення, журнал аудиту, Slack‑вебхуки, маршрутизація ескалації, метрики.

**Приклад — сповіщення на робочому столі в macOS:**

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

Викликається **після** того, як користувач відповідає на запит підтвердження (або запит завершується через тайм‑аут).

**Підпис функції зворотного виклику:**

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

Ті ж kwargs, що й у `pre_approval_request`, плюс:

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `choice` | `str` | Одне зі значень `"once"`, `"session"`, `"always"`, `"deny"` або `"timeout"` |

**Повернене значення:** ігнорується.

**Випадки використання:** Закрити відповідне сповіщення на робочому столі, записати остаточне рішення в журнал аудиту, оновити метрики, продовжити дію лімітора швидкості.

```python
def log_decision(command, choice, session_key, **kwargs):
    logger.info("approval %s: %s for session %s", choice, command[:60], session_key)

def register(ctx):
    ctx.register_hook("post_approval_response", log_decision)
```

---
### `transform_tool_result`

Виконується **після** того, як інструмент повернув результат і **перед** тим, як результат буде додано до розмови. Дозволяє плагіну переписати будь‑який рядок результату інструмента — не лише вивід терміналу — перед тим, як модель його побачить.

**Підпис колбеку:**

```python
def my_callback(
    tool_name: str,
    arguments: dict,
    result: str,
    task_id: str | None,
    **kwargs,
) -> str | None:
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `tool_name` | `str` | Інструмент, який створив результат (`read_file`, `web_extract`, `delegate_task`, …). |
| `arguments` | `dict` | Аргументи, якими модель викликала інструмент. |
| `result` | `str` | Необроблений рядок результату інструмента, після обрізки та видалення ANSI‑послідовностей. |
| `task_id` | `str \| None` | Ідентифікатор завдання/сесії під час роботи в середовищах RL/benchmark. |

**Повернене значення:** `str` — рядок, яким замінюється результат (повернений рядок бачить модель), `None` — залишити без змін.

**Випадки застосування:** Видалення специфічних для організації PII з виводу `web_extract`, обгортання довгих JSON‑відповідей інструмента у заголовок‑резюме, вставка підказок з веб‑пошуку у результати `read_file`, переписування звітів підагента `delegate_task` у схему, специфічну для проєкту.

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

Застосовується до всіх інструментів. Для переписування лише виводу терміналу дивіться `transform_terminal_output` нижче — він вузькоспеціалізований і виконується раніше в конвеєрі (до обрізки, до редагування).

---
### `transform_terminal_output`

Виконується всередині конвеєра `terminal` інструмента — у передньому плані, **до** стандартного обрізання 50 KB, видалення ANSI‑послідовностей та редагування секретних даних. Дозволяє плагінам переписати необроблений `stdout`/`stderr` командного шелу до того, як будь‑яка подальша обробка втрутиться.

**Підпис зворотного виклику:**

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

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | `str` | Команда шелу, яка створила вивід. |
| `output` | `str` | Необроблений комбінований `stdout`/`stderr` (може бути дуже великим — обрізання відбувається після хука). |
| `exit_code` | `int` | Код завершення процесу. |
| `cwd` | `str` | Робочий каталог, у якому виконувалась команда. |

**Повернене значення:** `str` — для заміни виводу, `None` — щоб залишити його без змін.

**Випадки використання:** Вставляти підсумки для команд, що генерують масивний вивід (`du -ah`, `find`, `tree`), позначати вивід проєктно‑специфічним маркером, щоб подальші хуки знали, як його обробляти, видаляти шум вимірювань, який змінюється між запусками і порушує кешування підказок.

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

Добре поєднується з `transform_tool_result` (який охоплює всі інші інструменти).
### `transform_llm_output`

Виконується **один раз за хід** після завершення циклу виклику інструментів і коли модель сформувала остаточну відповідь, **перед** тим, як ця відповідь буде доставлена користувачеві (CLI, gateway або програмному виклику). Дозволяє плагіну переписати фінальний текст асистента за допомогою класичних методів програмування — без зайвих токенів інференції на SOUL‑текст чи трансформацію, керовану навичками.

**Підпис зворотного виклику:**

```python
def my_callback(
    response_text: str,
    session_id: str,
    model: str,
    platform: str,
    **kwargs,
) -> str | None:
```

| Параметр | Тип | Опис |
|-----------|------|-------------|
| `response_text` | `str` | Остаточний текст відповіді асистента для цього ходу. |
| `session_id` | `str` | Ідентифікатор сесії для цієї розмови (може бути порожнім для одноразових запусків). |
| `model` | `str` | Назва моделі, яка згенерувала відповідь (наприклад, `anthropic/claude-sonnet-4.6`). |
| `platform` | `str` | Платформа доставки (`cli`, `telegram`, `discord`, …; порожньо, коли не встановлено). |

**Повертає:** непорожній `str`, яким замінюється текст відповіді, `None` або порожній рядок — залишити без змін. **Перший непорожній рядок виграє**, коли зареєстровано кілька плагінів — аналогічно `transform_tool_result`.

**Випадки використання:** застосувати трансформацію особистості/словникового запасу (наприклад, «піратська мова», «Губка Боб»), видалити ідентифікатори користувача з фінального тексту, додати підпис‑футер, специфічний для проєкту, забезпечити дотримання корпоративного стилю без витрати токенів на інструкції SOUL.

```python
import os, re

def spongebob(response_text, **kwargs):
    if os.environ.get("SPONGEBOB_MODE") != "on":
        return None  # pass through unchanged
    return re.sub(r"!", "!! Tartar sauce!", response_text)

def register(ctx):
    ctx.register_hook("transform_llm_output", spongebob)
```

Хук спрацьовує лише при непорожній, не перерваній відповіді — він не активується під час переривань кнопкою зупинки або порожніх ходів. Виключення реєструються як попередження і не переривають виконання агента.
## Shell Hooks

Оголошуй shell‑script hooks у своєму `cli-config.yaml`, і Hermes запускатиме їх як підпроцеси щоразу, коли спрацює відповідна подія plugin‑hook — і в CLI, і в gateway‑сесіях. Писати Python‑плагіни не потрібно.

Використовуй shell hooks, коли потрібен простий, однофайловий скрипт (Bash, Python, будь‑який з shebang), щоб:

- **Заблокувати виклик інструменту** — відхилити небезпечні команди `terminal`, застосувати політики per‑directory, вимагати підтвердження для руйнівних операцій `write_file` / `patch`.
- **Виконати після виклику інструменту** — автоматично форматувати Python або TypeScript файли, які агент щойно записав, логувати API‑виклики, запускати CI‑workflow.
- **Вставити контекст у наступний оберт LLM** — додати вивід `git status`, поточний день тижня або отримані документи до повідомлення користувача (див. [`pre_llm_call`](#pre_llm_call)).
- **Спостерігати за подіями життєвого циклу** — записати рядок у лог, коли завершується підагент (`subagent_stop`) або стартує сесія (`on_session_start`).

Shell hooks реєструються викликом `agent.shell_hooks.register_from_config(cfg)` під час запуску CLI (`hermes_cli/main.py`) і під час запуску gateway (`gateway/run.py`). Вони природно поєднуються з Python‑plugin hooks — обидва проходять через один і той же диспетчер.

### Порівняння в один погляд

| Dimension | Shell hooks | [Plugin hooks](#plugin-hooks) | [Gateway hooks](#gateway-event-hooks) |
|-----------|-------------|-------------------------------|---------------------------------------|
| Declared in | `hooks:` block in `~/.hermes/config.yaml` | `register()` in a `plugin.yaml` plugin | `HOOK.yaml` + `handler.py` directory |
| Lives under | `~/.hermes/agent-hooks/` (by convention) | `~/.hermes/plugins/<name>/` | `~/.hermes/hooks/<name>/` |
| Language | Any (Bash, Python, Go binary, …) | Python only | Python only |
| Runs in | CLI + Gateway | CLI + Gateway | Gateway only |
| Events | `VALID_HOOKS` (incl. `subagent_stop`) | `VALID_HOOKS` | Gateway lifecycle (`gateway:startup`, `agent:*`, `command:*`) |
| Can block a tool call | Yes (`pre_tool_call`) | Yes (`pre_tool_call`) | No |
| Can inject LLM context | Yes (`pre_llm_call`) | Yes (`pre_llm_call`) | No |
| Consent | First‑use prompt per `(event, command)` pair | Implicit (Python plugin trust) | Implicit (dir trust) |
| Inter‑process isolation | Yes (subprocess) | No (in‑process) | No (in‑process) |

### Configuration schema

```yaml
hooks:
  <event_name>:                  # Must be in VALID_HOOKS
    - matcher: "<regex>"         # Optional; used for pre/post_tool_call only
      command: "<shell command>" # Required; runs via shlex.split, shell=False
      timeout: <seconds>         # Optional; default 60, capped at 300

hooks_auto_accept: false         # See "Consent model" below
```

Назви подій мають відповідати одному з [plugin hook events](#plugin-hooks); помилки у назвах викликають попередження «Did you mean X?», і такі записи пропускаються. Невідомі ключі в окремому записі ігноруються; відсутність `command` — це пропуск з попередженням. `timeout > 300` обрізається з попередженням.

### JSON wire protocol

Кожного разу, коли подія спрацьовує, Hermes створює підпроцес для кожного підходящого hook (за умови збігу matcher), передає JSON‑payload у **stdin** і читає **stdout** як JSON.

**stdin — payload, який отримує скрипт:**

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

`tool_name` та `tool_input` дорівнюють `null` для подій, не пов’язаних з інструментом (`pre_llm_call`, `subagent_stop`, lifecycle сесії). Словник `extra` містить усі kwargs, специфічні для події (`user_message`, `conversation_history`, `child_role`, `duration_ms`, …). Непідтримувані типи перетворюються у рядок, а не відкидаються.

**stdout — необов’язкова відповідь:**

```jsonc
// Block a pre_tool_call (both shapes accepted; normalised internally):
{"decision": "block", "reason":  "Forbidden: rm -rf"}   // Claude-Code style
{"action":   "block", "message": "Forbidden: rm -rf"}   // Hermes-canonical

// Inject context for pre_llm_call:
{"context": "Today is Friday, 2026-04-17"}

// Silent no-op — any empty / non-matching output is fine:
```

Помилковий JSON, ненульові коди виходу та тайм‑аути записуються у попередження, але не переривають цикл агента.

### Worked examples

#### 1. Авто‑форматування Python‑файлів після кожного запису

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

Вид у контексті агента **не** перечитується автоматично — реформатування впливає лише на файл на диску. Подальші виклики `read_file` отримають вже відформатовану версію.

#### 2. Блокування руйнівних `terminal` команд

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

#### 3. Вставка `git status` у кожен оберт (еквівалент Claude‑Code `UserPromptSubmit`)

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

Подія Claude Code `UserPromptSubmit` навмисно не є окремою подією Hermes — `pre_llm_call` спрацьовує в тому ж місці і вже підтримує вставку контексту. Використай її тут.

#### 4. Логування завершення кожного підагента

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

### Consent model

Кожна унікальна пара `(event, command)` запитує підтвердження у користувача під час першого використання, після чого рішення зберігається у `~/.hermes/shell-hooks-allowlist.json`. Подальші запуски (CLI або gateway) пропускають запит.

Три способи обійти інтерактивний запит — достатньо будь‑якого одного:

1. Прапорець `--accept-hooks` у CLI (наприклад `hermes --accept-hooks chat`)
2. Змінна середовища `HERMES_ACCEPT_HOOKS=1`
3. `hooks_auto_accept: true` у `cli-config.yaml`

У не‑TTY середовищах (gateway, cron, CI) потрібен один із цих трьох параметрів — інакше нові hook‑и залишаться незареєстрованими і буде записано попередження.

**Редагування скриптів довіряється безпечно.** Ключі allowlist прив’язані до точного рядка команди, а не до хешу скрипту, тому зміна скрипту на диску не анулює згоду. `hermes hooks doctor` повідомляє про зсув mtime, щоб ти міг помітити зміни і вирішити, чи потрібно повторно схвалювати.

### The `hermes hooks` CLI

| Command | What it does |
|---------|--------------|
| `hermes hooks list` | Dump configured hooks with matcher, timeout, and consent status |
| `hermes hooks test <event> [--for-tool X] [--payload-file F]` | Fire every matching hook against a synthetic payload and print the parsed response |
| `hermes hooks revoke <command>` | Remove every allowlist entry matching `<command>` (takes effect on next restart) |
| `hermes hooks doctor` | For every configured hook: check exec bit, allowlist status, mtime drift, JSON output validity, and rough execution time |

### Security

Shell hooks працюють з **твоїми повними користувацькими обліковими даними** — та ж межа довіри, що і у cron‑запису або shell‑alias. Став `hooks:` блок у `config.yaml` як привілейовану конфігурацію:

- Посилайся лише на скрипти, які ти написав або повністю перевірив.
- Тримай скрипти в `~/.hermes/agent-hooks/`, щоб шлях був простим для аудиту.
- Після отримання спільної конфігурації запускай `hermes hooks doctor`, щоб виявити нові hook‑и перед їх реєстрацією.
- Якщо `config.yaml` контролюється версіями в команді, переглядай PR‑и, що змінюють розділ `hooks:`, так само, як ти переглядаєш CI‑конфіг.

### Ordering and precedence

Python‑plugin hooks і shell hooks проходять через один диспетчер `invoke_hook()`. Плагіни Python реєструються першими (`discover_and_load()`), shell hooks — другими (`register_from_config()`), тому рішення Python `pre_tool_call` блокування мають пріоритет у випадку конфлікту. Перший дійсний блок перемагає — агрегатор повертає одразу, коли будь‑який колбек повертає `{"action": "block", "message": str}` з непорожнім повідомленням.