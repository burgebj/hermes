---
title: "Python Debugpy — отладка Python: pdb REPL + удалённый debugpy (DAP)"
sidebar_label: "Python Debugpy"
description: "Отладка Python: pdb REPL + debugpy remote (DAP)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Python Debugpy

Отладка Python: REPL `pdb` + удалённый `debugpy` (DAP).
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/software-development/python-debugpy` |
| Версия | `1.0.0` |
| Автор | Hermes Agent |
| Лицензия | MIT |
| Платформы | linux, macos |
| Теги | `debugging`, `python`, `pdb`, `debugpy`, `breakpoints`, `dap`, `post-mortem` |
| Связанные навыки | [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging), [`node-inspect-debugger`](/docs/user-guide/skills/bundled/software-development/software-development-node-inspect-debugger), [`debugging-hermes-tui-commands`](/docs/user-guide/skills/bundled/software-development/software-development-debugging-hermes-tui-commands) |
:::info
Ниже представлено полное определение **skill**, которое Hermes загружает при срабатывании этого **skill**. Это то, что агент видит в виде инструкций, когда **skill** активен.
:::

# Отладчик Python (pdb + debugpy)
## Обзор

Три инструмента, выбранные в зависимости от ситуации:

| Инструмент | Когда |
|---|---|
| **`breakpoint()` + pdb** | Локально, интерактивно, самый простой. Добавь `breakpoint()` в код, запусти как обычно, получишь REPL на этой строке. |
| **`python -m pdb`** | Запусти существующий скрипт под pdb без изменения исходного кода. Удобно для быстрого исследования. |
| **`debugpy`** | Удалённо / без UI / «подключиться к уже запущенному процессу». Работает по DAP, управляется из терминала, подходит для длительно работающих процессов (gateway, daemon, PTY‑дочерних). |

**Начинай с `breakpoint()`.** Это самый простой способ, который работает.
## Когда использовать

- Тест падает, и traceback не показывает, почему значение неверно
- Нужно пошагово пройтись по функции и наблюдать, как меняется коллекция
- Длительно работающий процесс (hermes gateway, tui_gateway) ведёт себя некорректно, и его нельзя перезапустить
- Постмортем: исключение возникло в прод‑похожем коде, и требуется исследовать локальные переменные в месте сбоя
- Подпроцесс / дочерний процесс (Python `_SlashWorker`, PTY bridge worker) является реальным местом ошибки

**Не использовать для:** задач, которые решаются `print()` / `logging.debug` за минуту, или тех, которые уже раскрывает `pytest -vv --tb=long --showlocals`.
## Быстрый справочник pdb

Внутри любого приглашения pdb (`(Pdb)`):

| Команда | Действие |
|---|---|
| `h` / `h cmd` | справка |
| `n` | следующая строка (step over) |
| `s` | шаг в функцию (step into) |
| `r` | возврат из текущей функции |
| `c` | продолжить |
| `unt N` | продолжать до строки N |
| `j N` | перейти к строке N (только в той же функции) |
| `l` / `ll` | вывести исходный код вокруг текущей строки / всю функцию |
| `w` | где (stack trace) |
| `u` / `d` | переместиться вверх / вниз в стеке |
| `a` | вывести аргументы текущей функции |
| `p expr` / `pp expr` | вывести / красиво вывести выражение |
| `display expr` | автоматически выводить `expr` при каждой остановке |
| `b file:line` | установить точку останова |
| `b func` | остановка при входе в функцию |
| `b file:line, cond` | условная точка останова |
| `cl N` | снять точку останова N |
| `tbreak file:line` | одноразовая точка останова |
| `!stmt` | выполнить произвольный код Python (включая присваивания) |
| `interact` | перейти в полноценный REPL Python в текущей области (Ctrl+D — выйти) |
| `q` | выйти |

Команда `interact` — самая мощная: можно импортировать любые модули, исследовать сложные объекты, даже вызывать методы, изменяющие состояние. Локальные переменные по умолчанию только для чтения; используй `!x = 42` в приглашении `(Pdb)`, чтобы изменить их.
## Рецепт 1: Локальная контрольная точка

Самый простой способ. Отредактируй файл:

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # <-- drops into pdb here
    return result + y
```

Запусти код обычным образом. Ты окажешься на строке `breakpoint()` с полным доступом к локальным переменным.

**Не забудь удалить `breakpoint()` перед коммитом.** Используй `git diff` или `grep` в pre‑commit:
```bash
rg -n 'breakpoint\(\)' --type py
```
## Рецепт 2: Запуск скрипта в pdb (без изменения исходного кода)

```bash
python -m pdb path/to/script.py arg1 arg2
# Lands at first line of script
(Pdb) b path/to/script.py:42
(Pdb) c
```
## Рецепт 3: Отладка теста pytest

Тест‑раннер hermes и pytest оба поддерживают это:

```bash
# Drop to pdb on failure (or on any raised exception):
scripts/run_tests.sh tests/path/to/test_file.py::test_name --pdb

# Drop to pdb at the START of the test:
scripts/run_tests.sh tests/path/to/test_file.py::test_name --trace

# Show locals in tracebacks without pdb:
scripts/run_tests.sh tests/path/to/test_file.py --showlocals --tb=long
```

Примечание: `scripts/run_tests.sh` использует xdist (`-n 4`) по умолчанию, а pdb НЕ работает под xdist. Добавь `-p no:xdist` или запусти один тест с `-n 0`:

```bash
scripts/run_tests.sh tests/foo_test.py::test_bar --pdb -p no:xdist
# or
source .venv/bin/activate
python -m pytest tests/foo_test.py::test_bar --pdb
```

Это обходи гарантии hermetic‑env — подходит для отладки, но перед отправкой запусти снова под обёрткой, чтобы убедиться.
## Рецепт 4: Post-mortem при любой ошибке

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

Или обернуть весь скрипт:

```bash
python -m pdb -c continue script.py
# When it crashes, pdb catches it and you're in the frame of the exception
```

Или установить глобальный хук в repl/jupyter:

```python
import sys
def excepthook(etype, value, tb):
    import pdb; pdb.post_mortem(tb)
sys.excepthook = excepthook
```
## Рецепт 5: Удалённая отладка с debugpy (подключение к запущенному процессу)

Для длительно работающих процессов: Hermes gateway, tui_gateway, демон, процесс, который уже ведёт себя некорректно и его нельзя перезапустить чисто.

### Настройка

```bash
source /home/bb/hermes-agent/.venv/bin/activate
pip install debugpy
```

### Шаблон A: Правка исходного кода — процесс ждёт отладчика при запуске

Добавь в начале точки входа (или внутри функции, которую нужно отладить):

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
print("debugpy listening on 5678, waiting for client...", flush=True)
debugpy.wait_for_client()
debugpy.breakpoint()       # optional: pause immediately once attached
```

Запусти процесс; он блокируется на `wait_for_client()`.

### Шаблон B: Без правки исходного кода — запуск с `-m debugpy`

```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py arg1
```

Эквивалент для модуля‑входа:

```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client -m your.module
```

### Шаблон C: Подключение к уже запущенному процессу

Требуются PID и предустановленный debugpy в окружении цели:

```bash
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
# debugpy injects itself into the process. Then attach a client as below.
```

Некоторые ядра/конфигурации безопасности блокируют внедрение на основе ptrace (`/proc/sys/kernel/yama/ptrace_scope`). Исправить можно так:
```bash
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

### Подключение клиента из терминала

Самый простой DAP‑клиент в терминале — VS Code CLI или небольшой скрипт. Изнутри Hermes у тебя есть два практичных варианта:

**Вариант 1: собственный REPL CLI `debugpy`** — не официальная функция, но крошечный скрипт DAP‑клиента:

```python
# /tmp/dap_client.py
import socket, json, itertools, time, sys

HOST, PORT = "127.0.0.1", 5678
s = socket.create_connection((HOST, PORT))
seq = itertools.count(1)

def send(msg):
    msg["seq"] = next(seq)
    body = json.dumps(msg).encode()
    s.sendall(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)

def recv():
    header = b""
    while b"\r\n\r\n" not in header:
        header += s.recv(1)
    length = int(header.decode().split("Content-Length:")[1].split("\r\n")[0].strip())
    body = b""
    while len(body) < length:
        body += s.recv(length - len(body))
    return json.loads(body)

send({"type": "request", "command": "initialize", "arguments": {"adapterID": "python"}})
print(recv())
send({"type": "request", "command": "attach", "arguments": {}})
print(recv())
send({"type": "request", "command": "setBreakpoints",
      "arguments": {"source": {"path": sys.argv[1]},
                    "breakpoints": [{"line": int(sys.argv[2])}]}})
print(recv())
send({"type": "request", "command": "configurationDone"})
# ... loop reading events and sending continue/stepIn/etc.
```

Это удобно для одноразовой автоматизации, но неудобно как интерактивный UX.

**Вариант 2: подключение из VS Code / Cursor / Zed** — если у пользователя открыт один из этих редакторов, он может добавить `launch.json`:

```json
{
  "name": "Attach to Hermes",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "127.0.0.1", "port": 5678 },
  "justMyCode": false,
  "pathMappings": [
    { "localRoot": "${workspaceFolder}", "remoteRoot": "/home/bb/hermes-agent" }
  ]
}
```

**Вариант 3: отказаться от DAP, использовать `remote-pdb`** — обычно именно то, что нужно терминальному агенту:

```bash
pip install remote-pdb
```

В твоём коде:
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # blocks until connection
```

Затем из терминала:
```bash
nc 127.0.0.1 4444
# You get a (Pdb) prompt exactly as if debugging locally.
```

`remote-pdb` — самый чистый выбор, дружелюбный к агенту, когда протокол DAP debugpy избыточен. Используй `debugpy` только тогда, когда действительно нужна интеграция с IDE.
## Отладка процессов, специфичных для Hermes

### Тесты
См. рецепт 3. Всегда добавляй `-p no:xdist` или запускай отдельные тесты без xdist.

### `run_agent.py` / CLI — однократный запуск
Проще всего: добавь `breakpoint()` рядом с подозрительной строкой, затем запусти `hermes` обычным образом. Управление вернётся в твой терминал в точке паузы.

### Подпроцесс `tui_gateway` (создаётся командой `hermes --tui`)
gateway запускается как дочерний процесс Node TUI. Варианты:

**A. Редактировать исходный код gateway:**
```python
# tui_gateway/server.py near the top of serve()
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
```
Запусти `hermes --tui`. TUI замёрзнет (его бекенд ждёт). Подключи клиент — выполнение продолжится, когда ты введёшь `continue`.

**B. Использовать `remote-pdb` в конкретном обработчике:**
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # in the RPC handler you want to trap
```
Вызови соответствующую slash‑команду из TUI, затем в другом терминале выполни `nc 127.0.0.1 4444`.

### Подпроцесс `_SlashWorker`
Тот же шаблон — `remote-pdb` с `set_trace()` внутри пути `exec` рабочего процесса. Worker сохраняется между slash‑командами, поэтому первое срабатывание блокируется до подключения; последующие slash‑команды проходят нормально, если не переактивировать отладчик.

### gateway (`gateway/run.py`)
Длительно живущий процесс. Используй `remote-pdb` в обработчике или `debugpy` с `--wait-for-client`, если всё равно перезапускаешь gateway.
## Общие подводные камни

1. **pdb под pytest‑xdist молча ничего не делает.** Ты не увидишь подсказку, тест просто зависает. Всегда используй `-p no:xdist` или `-n 0`.

2. **`breakpoint()` в CI / контекстах без TTY зависает процесс.** Безопасно локально; никогда не коммить его. Добавь grep‑проверку в `pre‑commit` как страховку.

3. **`PYTHONBREAKPOINT=0`** отключает все вызовы `breakpoint()`. Проверь переменные окружения, если твоя точка останова не срабатывает:
   ```bash
   echo $PYTHONBREAKPOINT
   ```

4. **`debugpy.listen` блокирует только если ты также вызываешь `wait_for_client()`.** Без этого выполнение продолжается, и первая точка останова может сработать до подключения клиента.

5. **Подключение к PID не работает на «жёстко настроенных» ядрах.** `ptrace_scope=1` (значение по умолчанию в Ubuntu) позволяет `ptrace` только процессам того же пользователя. Обход: `echo 0 > /proc/sys/kernel/yama/ptrace_scope` (требует root) или запускать сразу под `debugpy`.

6. **Потоки.** `pdb` отлаживает только текущий поток. Для многопоточного кода используй `debugpy` (DAP, учитывающий потоки) или вызывай `threading.settrace()` в каждом потоке.

7. **asyncio.** `pdb` работает в корутинах, но `await` внутри pdb требует Python 3.13+ или `await` из режима `interact` в более старых версиях. Для 3.11/3.12 используй трюки с `asyncio.run_coroutine_threadsafe` или `await`‑выражения через `!stmt` и `asyncio.ensure_future`.

8. **`scripts/run_tests.sh` удаляет учётные данные и задаёт `HOME=<tmpdir>`.** Если твой баг зависит от пользовательской конфигурации или реальных API‑ключей, он не воспроизводится под обёрткой. Сначала отладь чистым `pytest`, затем проверь снова под обёрткой.

9. **Fork / multiprocessing.** `pdb` не следует за форками. Каждый дочерний процесс нуждается в своей `breakpoint()` или `set_trace()`. Для подагентов Hermes отлаживай один процесс за раз.
## Список проверок

- [ ] После `pip install debugpy` убедись: `python -c "import debugpy; print(debugpy.__version__)"`
- [ ] Для удалённой отладки проверь, что порт действительно прослушивается: `ss -tlnp | grep 5678`
- [ ] Первый брейкпоинт действительно срабатывает (если нет, вероятно, установлен `PYTHONBREAKPOINT=0`, ты работаешь под xdist или выполнение завершилось до подключения)
- [ ] `where` / `w` показывает ожидаемый стек вызовов
- [ ] Очистка после отладки: в закоммиченном коде нет оставшихся `breakpoint()` / `set_trace()`
  ```bash
  rg -n 'breakpoint\(\)|set_trace\(|debugpy\.listen' --type py
  ```
## Одноразовые рецепты

**"Why is this dict missing a key?"**
```python
# add above the KeyError site
breakpoint()
# then in pdb:
(Pdb) pp d
(Pdb) pp list(d.keys())
(Pdb) w                # how did we get here
```

**"This test passes in isolation but fails in the suite."**
```bash
scripts/run_tests.sh tests/the_test.py --pdb -p no:xdist
# But if it only fails WITH other tests:
source .venv/bin/activate
python -m pytest tests/ -x --pdb -p no:xdist
# Now it pdb-traps at the exact failing test after state accumulated.
```

**"My async handler deadlocks."**
```python
# Add at handler entry
import remote_pdb; remote_pdb.set_trace(host="127.0.0.1", port=4444)
```
Запусти обработчик: `nc 127.0.0.1 4444`, затем `w`, чтобы увидеть приостановленный кадр, `!import asyncio; asyncio.all_tasks()` — чтобы увидеть, что ещё ожидает выполнения.

**"Post-mortem on a crash in an Ink child process / subprocess."**
```bash
PYTHONFAULTHANDLER=1 python -m pdb -c continue path/to/entrypoint.py
# On crash, pdb lands at the frame of the exception with full locals
```