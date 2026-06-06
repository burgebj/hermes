---
sidebar_position: 2
title: "Внутрішнє ACP"
description: "Як працює адаптер ACP: життєвий цикл, сесії, міст подій, схвалення та відображення інструментів"
---

# ACP Internals

Адаптер ACP обгортає синхронний `AIAgent` Hermes у асинхронний JSON‑RPC stdio‑сервер.

Ключові файли реалізації:

- `acp_adapter/entry.py`
- `acp_adapter/server.py`
- `acp_adapter/session.py`
- `acp_adapter/events.py`
- `acp_adapter/permissions.py`
- `acp_adapter/tools.py`
- `acp_adapter/auth.py`
- `acp_registry/agent.json`

## Boot flow

```text
hermes acp / hermes-acp / python -m acp_adapter
  -> acp_adapter.entry.main()
  -> parse --version / --check / --setup before server startup
  -> load ~/.hermes/.env
  -> configure stderr logging
  -> construct HermesACPAgent
  -> acp.run_agent(agent, use_unstable_protocol=True)
```

Шлях Zed ACP Registry запускає той самий адаптер через `uvx --from 'hermes-agent[acp]==<version>' hermes-acp`, вказуючи на випуск `hermes-agent` у PyPI.

`stdout` зарезервовано для транспорту ACP JSON‑RPC. Людсько‑читабельні логи надходять у `stderr`.

## Major components

### `HermesACPAgent`

`acp_adapter/server.py` реалізує протокол ACP‑агента.

Обов’язки:

- ініціалізація / автентифікація
- нові/завантаження/відновлення/форк/перелік/скасування методи сесії
- виконання підказки
- перемикання моделі сесії
- підключення синхронних колбеків AIAgent до асинхронних сповіщень ACP

### `SessionManager`

`acp_adapter/session.py` відстежує живі ACP‑сесії.

Кожна сесія зберігає:

- `session_id`
- `agent`
- `cwd`
- `model`
- `history`
- `cancel_event`

Менеджер є потокобезпечним і підтримує:

- створення
- отримання
- видалення
- форк
- перелік
- очищення
- оновлення `cwd`

### Event bridge

`acp_adapter/events.py` перетворює колбеки AIAgent у ACP‑події `session_update`.

З’єднані колбеки:

- `tool_progress_callback`
- `thinking_callback` (наразі встановлений у `None` в ACP‑мості — міркування передається через `step_callback`)
- `step_callback`

Оскільки `AIAgent` працює у робочому потоці, а ACP‑ввід/вивід живе в головному циклі подій, місток використовує:

```python
asyncio.run_coroutine_threadsafe(...)
```

### Permission bridge

`acp_adapter/permissions.py` адаптує небезпечні запити схвалення терміналу у запити дозволу ACP.

Відображення:

- `allow_once` → Hermes `once`
- `allow_always` → Hermes `always`
- опції відхилення → Hermes `deny`

Тайм‑аути та збої мосту відхиляються за замовчуванням.

### Tool rendering helpers

`acp_adapter/tools.py` відображає інструменти Hermes у типи інструментів ACP і формує вміст для редактора.

Приклади:

- `patch` / `write_file` → diff‑файлів
- `terminal` → текст команди оболонки
- `read_file` / `search_files` → попередній перегляд тексту
- великі результати → скорочені текстові блоки для безпеки UI

## Session lifecycle

```text
new_session(cwd)
  -> create SessionState
  -> create AIAgent(platform="acp", enabled_toolsets=["hermes-acp"])
  -> bind task_id/session_id to cwd override

prompt(..., session_id)
  -> extract text from ACP content blocks
  -> reset cancel event
  -> install callbacks + approval bridge
  -> run AIAgent in ThreadPoolExecutor
  -> update session history
  -> emit final agent message chunk
```

### Скасування

`cancel(session_id)`:

- встановлює подію скасування сесії
- викликає `agent.interrupt()`, якщо доступно
- змушує відповідь підказки повернути `stop_reason="cancelled"`

### Forking

`fork_session()` глибоко копіює історію повідомлень у нову живу сесію, зберігаючи стан розмови та надаючи форку власний `session_id` і `cwd`.

## Provider/auth behavior

ACP не реалізує власне сховище автентифікації.

Замість цього він повторно використовує резолвер середовища Hermes:

- `acp_adapter/auth.py`
- `hermes_cli/runtime_provider.py`

Тому ACP рекламує і використовує поточний налаштований провайдер/облікові дані Hermes. Він також завжди рекламує метод автентифікації налаштування терміналу (`hermes-setup`, args `--setup`), щоб клієнти реєстру першого запуску могли відкрити інтерактивну конфігурацію моделі/провайдера Hermes перед запуском звичайної ACP‑сесії.

## Working directory binding

ACP‑сесії несуть `cwd` редактора.

Менеджер сесій прив’язує цей `cwd` до ідентифікатора ACP‑сесії через переопреділення терміналу/файлів у межах завдання, тому інструменти файлів і терміналу працюють відносно робочого простору редактора.

## Duplicate same-name tool calls

Місток подій відстежує ідентифікатори інструментів FIFO за назвою інструмента, а не лише один ID на назву. Це важливо для:

- паралельних викликів з однаковою назвою
- повторних викликів з однаковою назвою в одному кроці

Без черг FIFO події завершення прикріплювалися б до неправильного виклику інструмента.

## Approval callback restoration

ACP тимчасово встановлює колбек схвалення на інструмент терміналу під час виконання підказки, а потім відновлює попередній колбек. Це запобігає залишенню специфічних для сесії ACP обробників схвалення, встановлених глобально назавжди.

## Current limitations

- ACP‑сесії зберігаються у спільному `~/.hermes/state.db` (SessionDB) і прозоро відновлюються після перезапуску процесу; вони з’являються у `session_search`
- блоки підказок, що не є текстовими, наразі ігноруються при вилученні тексту запиту
- UX, специфічний для редактора, варіюється залежно від реалізації клієнта ACP

## Related files

- `tests/acp/` — тестовий набір ACP
- `toolsets.py` — визначення набору інструментів `hermes-acp`
- `hermes_cli/main.py` — підкоманда CLI `hermes acp`
- `pyproject.toml` — необов’язкова залежність `[acp]` + скрипт `hermes-acp`