---
title: "Python Debugpy — налагодження Python: pdb REPL + debugpy remote (DAP)"
sidebar_label: "Python Debugpy"
description: "Налагодження Python: pdb REPL + debugpy remote (DAP)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Python Debugpy

Налагодження Python: pdb REPL + віддалений debugpy (DAP).
## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/software-development/python-debugpy` |
| Версія | `1.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos |
| Теги | `debugging`, `python`, `pdb`, `debugpy`, `breakpoints`, `dap`, `post-mortem` |
| Пов’язані навички | [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging), [`node-inspect-debugger`](/docs/user-guide/skills/bundled/software-development/software-development-node-inspect-debugger), [`debugging-hermes-tui-commands`](/docs/user-guide/skills/bundled/software-development/software-development-debugging-hermes-tui-commands) |
:::info
Нижче наведено повне визначення skill, яке Hermes завантажує, коли цей skill активується. Це те, що агент бачить як інструкції, коли skill активний.
:::

# Python Debugger (pdb + debugpy)
## Огляд

Три інструменти, вибрані за ситуацією:

| Інструмент | Коли |
|---|---|
| **`breakpoint()` + pdb** | Локально, інтерактивно, найпростіше. Додай `breakpoint()` у код, запусти звичайно, отримай REPL у цьому рядку. |
| **`python -m pdb`** | Запусти існуючий скрипт під pdb без змін у коді. Корисно для швидкого дослідження. |
| **`debugpy`** | Віддалено / безголово / «підключитися до вже запущеного процесу». Працює за протоколом DAP, скриптується з терміналу, підходить для довгоживучих процесів (gateway, daemon, PTY‑діти). |

**Починай з `breakpoint()`.** Це найдешевший спосіб, який працює.
## Коли використовувати

- Тест провалюється, і traceback не розкриває, чому значення неправильне
- Потрібно крок за кроком пройти функцію і спостерігати, як змінюється колекція
- Довготривалий процес (hermes gateway, tui_gateway) поводиться неправильно, і його не вдається перезапустити
- Постмортем: виключення виникло в прод‑подібному коді, і ти хочеш дослідити локальні змінні у місці збою
- Підпроцес / дочірній процес (Python `_SlashWorker`, PTY bridge worker) є справжнім місцем помилки

**Не використовуйте для:** речей, які `print()` / `logging.debug` вирішують за хвилину, або речей, які вже розкриває `pytest -vv --tb=long --showlocals`.
## pdb Швидке посилання

В будь‑якому pdb‑prompt (`(Pdb)`):

| Command | Action |
|---|---|
| `h` / `h cmd` | допомога |
| `n` | наступний рядок (step over) |
| `s` | step into |
| `r` | повернутись з поточної функції |
| `c` | продовжити |
| `unt N` | продовжити до рядка N |
| `j N` | перейти до рядка N (лише в межах тієї ж функції) |
| `l` / `ll` | переглянути код навколо поточного рядка / повна функція |
| `w` | where (стек‑трасування) |
| `u` / `d` | переміститися вгору / вниз у стеку |
| `a` | вивести аргументи поточної функції |
| `p expr` / `pp expr` | print / pretty‑print вираз |
| `display expr` | автоматично виводити вираз при кожній зупинці |
| `b file:line` | встановити точку зупину |
| `b func` | зупинитися на вході у функцію |
| `b file:line, cond` | умовна точка зупину |
| `cl N` | видалити точку зупину N |
| `tbreak file:line` | одноразова точка зупину |
| `!stmt` | виконати довільний код Python (включаючи присвоєння) |
| `interact` | запустити повний REPL Python у поточній області (Ctrl+D — вихід) |
| `q` | вийти |

Команда `interact` — найпотужніша: можна імпортувати будь‑що, досліджувати складні об’єкти, навіть викликати методи, які змінюють стан. Локальні змінні за замовчуванням лише для читання; використай `!x = 42` у prompt `(Pdb)`, щоб змінити їх.
## Рецепт 1: Локальна точка зупинки

Найпростіше. Відредагуй файл:

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # <-- drops into pdb here
    return result + y
```

Запусти код звичайним способом. Ти опинишся на рядку `breakpoint()` з повним доступом до локальних змінних.

**Не забудь видалити `breakpoint()` перед комітом.** Скористайся `git diff` або grep у pre‑commit:
```bash
rg -n 'breakpoint\(\)' --type py
```
## Рецепт 2: Запуск скрипту під pdb (без правок у коді)

```bash
python -m pdb path/to/script.py arg1 arg2
# Lands at first line of script
(Pdb) b path/to/script.py:42
(Pdb) c
```
## Рецепт 3: Налагодження тесту pytest

Тест‑раннер **hermes** та **pytest** підтримують це:

```bash
# Drop to pdb on failure (or on any raised exception):
scripts/run_tests.sh tests/path/to/test_file.py::test_name --pdb

# Drop to pdb at the START of the test:
scripts/run_tests.sh tests/path/to/test_file.py::test_name --trace

# Show locals in tracebacks without pdb:
scripts/run_tests.sh tests/path/to/test_file.py --showlocals --tb=long
```

Примітка: `scripts/run_tests.sh` за замовчуванням використовує xdist (`-n 4`), а pdb НЕ працює у xdist. Додай `-p no:xdist` або запусти окремий тест з `-n 0`:

```bash
scripts/run_tests.sh tests/foo_test.py::test_bar --pdb -p no:xdist
# or
source .venv/bin/activate
python -m pytest tests/foo_test.py::test_bar --pdb
```

Це обходить гарантії **hermetic‑env** — підходить для налагодження, але перед відправкою запусти знову під обгорткою, щоб підтвердити.
## Рецепт 4: Постмортем будь‑якого виключення

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

Або обгорнути весь скрипт:

```bash
python -m pdb -c continue script.py
# When it crashes, pdb catches it and you're in the frame of the exception
```

Або встановити глобальний хук у REPL/Jupyter:

```python
import sys
def excepthook(etype, value, tb):
    import pdb; pdb.post_mortem(tb)
sys.excepthook = excepthook
```
## Рецепт 5: Віддалене налагодження за допомогою debugpy (приєднання до запущеного процесу)

Для довготривалих процесів: Hermes gateway, tui_gateway, демон, процес, який вже поводиться неправильно і його не можна чисто перезапустити.

### Налаштування

```bash
source /home/bb/hermes-agent/.venv/bin/activate
pip install debugpy
```

### Шаблон A: Редагування коду — процес чекає на налагоджувач під час запуску

Додай біля початку точки входу (або всередині функції, яку потрібно налагоджувати):

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
print("debugpy listening on 5678, waiting for client...", flush=True)
debugpy.wait_for_client()
debugpy.breakpoint()       # optional: pause immediately once attached
```

Запусти процес; він блокується на `wait_for_client()`.

### Шаблон B: Без редагування коду — запуск з `-m debugpy`

```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py arg1
```

Еквівалент для модуля‑входу:

```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client -m your.module
```

### Шаблон C: Приєднання до вже запущеного процесу

Потрібні PID і попередньо встановлений debugpy у середовищі цілі:

```bash
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
# debugpy injects itself into the process. Then attach a client as below.
```

Деякі ядра/конфігурації безпеки блокують ін’єкцію на основі ptrace (`/proc/sys/kernel/yama/ptrace_scope`). Виправити можна так:
```bash
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```

### Підключення клієнта з терміналу

Найпростіший DAP‑клієнт у терміналі — VS Code CLI або невеликий скрипт. Усередині Hermes у тебе є два практичних варіанти:

**Варіант 1: власний REPL CLI debugpy** — не офіційна функція, але маленький скрипт DAP‑клієнта:

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

Це підходить для одноразової автоматизації, але незручно як інтерактивний UX.

**Варіант 2: Приєднання з VS Code / Cursor / Zed** — якщо користувач має відкритий один із них, він може додати `launch.json`:

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

**Варіант 3: Відмовитися від DAP, використати `remote-pdb`** — зазвичай саме те, що потрібно термінальному агенту:

```bash
pip install remote-pdb
```

У твоєму коді:
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # blocks until connection
```

Потім у терміналі:
```bash
nc 127.0.0.1 4444
# You get a (Pdb) prompt exactly as if debugging locally.
```

`remote-pdb` — найчистіший вибір, дружній до агента, коли протокол DAP debugpy надмірний. Використовуй `debugpy` лише тоді, коли дійсно потрібна інтеграція з IDE.
## Налагодження процесів, специфічних для Hermes

### Тести
Дивись Recipe 3. Завжди додавай `-p no:xdist` або запускай окремі тести без xdist.

### `run_agent.py` / CLI — одноразовий запуск
Найпростіше: додай `breakpoint()` біля підозрілої лінії, потім запусти `hermes` звичайним способом. Управління повернеться у твій термінал у точці паузи.

### Підпроцес `tui_gateway` (створюється командою `hermes --tui`)
gateway працює як дочірній процес Node TUI. Варіанти:

**A. Відредагувати код gateway:**
```python
# tui_gateway/server.py near the top of serve()
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
```
Запусти `hermes --tui`. TUI з’явиться «замороженим» (його бекенд чекає). Підключи клієнт; виконання продовжиться, коли ти виконаєш `continue`.

**B. Використати `remote-pdb` у конкретному обробнику:**
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)   # in the RPC handler you want to trap
```
Запусти відповідну slash‑command з TUI, потім у іншому терміналі виконай `nc 127.0.0.1 4444`.

### Підпроцес `_SlashWorker`
Той самий підхід — `remote-pdb` з `set_trace()` всередині шляху `exec` робітника. Робітник зберігається між slash‑командами, тому перший запуск блокується, доки ти не під’єднаєшся; подальші slash‑команди проходять нормально, якщо ти не активуєш його знову.

### Gateway (`gateway/run.py`)
Тривалий процес. Використовуй `remote-pdb` у обробнику або `debugpy` з `--wait-for-client`, якщо все одно перезапускаєш gateway.
## Common Pitfalls

1. **pdb under pytest-xdist silently does nothing.** Ти не побачиш підказку, тест просто зависне. Завжди використовуй `-p no:xdist` або `-n 0`.

2. **`breakpoint()` in CI / non‑TTY contexts hangs the process.** Безпечно локально; ніколи не комітти його. Додай grep у `pre‑commit` як захисну мережу.

3. **`PYTHONBREAKPOINT=0`** вимикає всі виклики `breakpoint()`. Перевіряй змінну середовища, якщо твоя точка зупину не спрацьовує:
   ```bash
   echo $PYTHONBREAKPOINT
   ```

4. **`debugpy.listen` blocks only if you also call `wait_for_client()`.** Без цього виконання продовжується, і твоя перша точка зупину може спрацювати до підключення клієнта.

5. **Attach to PID fails on hardened kernels.** `ptrace_scope=1` (типове для Ubuntu) дозволяє лише ptrace процесів того ж користувача. Обхід: `echo 0 > /proc/sys/kernel/yama/ptrace_scope` (потрібен root) або запускати під `debugpy` від самого початку.

6. **Threads.** `pdb` дебажить лише поточний потік. Для багатопотокового коду використай `debugpy` (DAP, що розуміє потоки) або встанови `threading.settrace()` для кожного потоку.

7. **asyncio.** `pdb` працює в корутинах, але `await` всередині pdb потребує Python 3.13+ або `await` у режимі `interact` на старіших версіях. Для 3.11/3.12 використай трюки з `asyncio.run_coroutine_threadsafe` або `!stmt`‑await через `asyncio.ensure_future`.

8. **`scripts/run_tests.sh` strips credentials and sets `HOME=<tmpdir>`.** Якщо твоя помилка залежить від користувацької конфігурації або реальних API‑ключів, вона не відтвориться під обгорткою. Спочатку відтворюй проблему за допомогою чистого `pytest`, потім перевіряй під обгорткою.

9. **Forking / multiprocessing.** `pdb` не слідує за форками. Кожен дочірній процес потребує власного `breakpoint()` або `set_trace()`. Для підагентів Hermes дебаж один процес за раз.
## Перелік перевірок

- [ ] Після `pip install debugpy` підтвердьте: `python -c "import debugpy; print(debugpy.__version__)"`
- [ ] Для віддаленого налагодження підтвердьте, що порт дійсно прослуховується: `ss -tlnp | grep 5678`
- [ ] Перший breakpoint дійсно спрацьовує (якщо ні, ймовірно, у вас `PYTHONBREAKPOINT=0`, ви під xdist, або виконання завершилось до підключення)
- [ ] `where` / `w` показує очікуваний стек викликів
- [ ] Після налагодження очисти код: не залишайте зайвих `breakpoint()` / `set_trace()` у закоміченому коді
  ```bash
  rg -n 'breakpoint\(\)|set_trace\(|debugpy\.listen' --type py
  ```
## One-Shot Recipes

**«Чому в цьому словнику відсутній ключ?»**
```python
# add above the KeyError site
breakpoint()
# then in pdb:
(Pdb) pp d
(Pdb) pp list(d.keys())
(Pdb) w                # how did we get here
```

**«Цей тест проходить окремо, але падає в сукупності.»**
```bash
scripts/run_tests.sh tests/the_test.py --pdb -p no:xdist
# But if it only fails WITH other tests:
source .venv/bin/activate
python -m pytest tests/ -x --pdb -p no:xdist
# Now it pdb-traps at the exact failing test after state accumulated.
```

**«Мій асинхронний обробник блокує потік.»**
```python
# Add at handler entry
import remote_pdb; remote_pdb.set_trace(host="127.0.0.1", port=4444)
```
Запусти обробник: `nc 127.0.0.1 4444`, потім `w`, щоб побачити призупинену рамку, `!import asyncio; asyncio.all_tasks()` — щоб дізнатися, які ще завдання очікують.

**«Post-mortem після аварії в дочірньому процесі Ink / subprocess.»**
```bash
PYTHONFAULTHANDLER=1 python -m pdb -c continue path/to/entrypoint.py
# On crash, pdb lands at the frame of the exception with full locals
```