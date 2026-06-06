---
sidebar_position: 8
title: "Виконання коду"
description: "Програмний виконання Python з доступом до інструменту RPC — звести багатокрокові робочі процеси в один крок"
---

# Виконання коду (Programmatic Tool Calling)

Інструмент `execute_code` дозволяє агенту писати Python‑скрипти, які програмно викликають інструменти Hermes, об’єднуючи багатокрокові робочі процеси в один хід LLM. Скрипт запускається у дочірньому процесі на хості агента, спілкуючись з Hermes через RPC‑з’єднання Unix‑доменної сокети.

## Як це працює

1. Агент пише Python‑скрипт, використовуючи `from hermes_tools import ...`
2. Hermes генерує заглушковий модуль `hermes_tools.py` з RPC‑функціями
3. Hermes відкриває Unix‑доменної сокети і запускає потік‑слухач RPC
4. Скрипт виконується у дочірньому процесі — виклики інструментів передаються через сокет назад до Hermes
5. Повертається лише вивід `print()` скрипту; проміжні результати інструментів ніколи не потрапляють у вікно контексту

```python
# The agent can write scripts like:
from hermes_tools import web_search, web_extract

results = web_search("Python 3.13 features", limit=5)
for r in results["data"]["web"]:
    content = web_extract([r["url"]])
    # ... filter and process ...
print(summary)
```

**Доступні інструменти всередині скриптів:** `web_search`, `web_extract`, `read_file`, `write_file`, `search_files`, `patch`, `terminal` (лише у передньому плані).

## Коли агент використовує це

Агент застосовує `execute_code`, коли є:

- **3+ виклики інструментів** з логікою обробки між ними
- Фільтрація великих обсягів даних або умовне розгалуження
- Цикли над результатами

Ключова перевага: проміжні результати інструментів не потрапляють у вікно контексту — повертається лише фінальний вивід `print()`, що значно зменшує використання токенів.

## Практичні приклади

### Конвеєр обробки даних

```python
from hermes_tools import search_files, read_file
import json

# Find all config files and extract database settings
matches = search_files("database", path=".", file_glob="*.yaml", limit=20)
configs = []
for match in matches.get("matches", []):
    content = read_file(match["path"])
    configs.append({"file": match["path"], "preview": content["content"][:200]})

print(json.dumps(configs, indent=2))
```

### Багатокрокове веб‑дослідження

```python
from hermes_tools import web_search, web_extract
import json

# Search, extract, and summarize in one turn
results = web_search("Rust async runtime comparison 2025", limit=5)
summaries = []
for r in results["data"]["web"]:
    page = web_extract([r["url"]])
    for p in page.get("results", []):
        if p.get("content"):
            summaries.append({
                "title": r["title"],
                "url": r["url"],
                "excerpt": p["content"][:500]
            })

print(json.dumps(summaries, indent=2))
```

### Масове рефакторинг файлів

```python
from hermes_tools import search_files, read_file, patch

# Find all Python files using deprecated API and fix them
matches = search_files("old_api_call", path="src/", file_glob="*.py")
fixed = 0
for match in matches.get("matches", []):
    result = patch(
        path=match["path"],
        old_string="old_api_call(",
        new_string="new_api_call(",
        replace_all=True
    )
    if "error" not in str(result):
        fixed += 1

print(f"Fixed {fixed} files out of {len(matches.get('matches', []))} matches")
```

### Конвеєр збірки та тестування

```python
from hermes_tools import terminal, read_file
import json

# Run tests, parse results, and report
result = terminal("cd /project && python -m pytest --tb=short -q 2>&1", timeout=120)
output = result.get("output", "")

# Parse test output
passed = output.count(" passed")
failed = output.count(" failed")
errors = output.count(" error")

report = {
    "passed": passed,
    "failed": failed,
    "errors": errors,
    "exit_code": result.get("exit_code", -1),
    "summary": output[-500:] if len(output) > 500 else output
}

print(json.dumps(report, indent=2))
```

## Режим виконання

`execute_code` має два режими виконання, які керуються параметром `code_execution.mode` у `~/.hermes/config.yaml`:

| Режим | Робоча директорія | Python‑інтерпретатор |
|------|-------------------|----------------------|
| **`project`** (за замовчуванням) | Робоча директорія сесії (те саме, що у `terminal()`) | Активний `VIRTUAL_ENV` / `CONDA_PREFIX` python, або, за потреби, python Hermes |
| `strict` | Тимчасова ізольована директорія, відокремлена від проєкту користувача | `sys.executable` (власний python Hermes) |

**Коли залишати `project`:** потрібні `import pandas`, `from my_project import foo` або відносні шляхи типу `open(".env")`, які працюють так само, як у `terminal()`. Це майже завжди те, що треба.

**Коли перемикатися на `strict`:** потрібна максимальна відтворюваність — один і той самий інтерпретатор у кожній сесії, незалежно від того, яке віртуальне середовище активував користувач, і скрипти мають бути ізольовані від дерева проєкту (без ризику випадкового читання файлів проєкту за допомогою відносного шляху).

```yaml
# ~/.hermes/config.yaml
code_execution:
  mode: project   # or "strict"
```

Поведінка запасного варіанту в режимі `project`: якщо `VIRTUAL_ENV` / `CONDA_PREFIX` не встановлені, пошкоджені або вказують на Python старіший за 3.8, резолвер чисто переходить до `sys.executable` — агент ніколи не залишиться без робочого інтерпретатора.

Безпекові інваріанти однакові в обох режимах:

- очищення середовища (ключі API, токени, облікові дані видаляються)
- білий список інструментів (скрипти не можуть рекурсивно викликати `execute_code`, `delegate_task` або інструменти MCP)
- обмеження ресурсів (тайм‑аут, обмеження stdout, ліміт викликів інструментів)

Перемикання режиму змінює лише місце та інтерпретатор виконання скриптів, а не те, які облікові дані вони бачать чи які інструменти можуть викликати.

## Обмеження ресурсів

| Ресурс | Ліміт | Примітки |
|----------|-------|----------|
| **Тайм‑аут** | 5 хвилин (300 s) | Скрипт завершується сигналом SIGTERM, потім SIGKILL через 5 s грації |
| **Stdout** | 50 KB | Вивід обрізається з повідомленням `[output truncated at 50KB]` |
| **Stderr** | 10 KB | Додається до виводу при ненульовому коді завершення для налагодження |
| **Виклики інструментів** | 50 за виконання | Повертається помилка, коли досягнуто ліміту |

Усі ліміти налаштовуються у `config.yaml`:

```yaml
# In ~/.hermes/config.yaml
code_execution:
  mode: project      # project (default) | strict
  timeout: 300       # Max seconds per script (default: 300)
  max_tool_calls: 50 # Max tool calls per execution (default: 50)
```

## Як працюють виклики інструментів у скриптах

Коли ваш скрипт викликає функцію типу `web_search("query")`:

1. Виклик серіалізується у JSON і надсилається через Unix‑доменної сокети до батьківського процесу
2. Батько передає його стандартному обробнику `handle_function_call`
3. Результат надсилається назад через сокет
4. Функція повертає розпарсений результат

Тобто виклики інструментів у скриптах поводяться так само, як звичайні виклики — ті ж обмеження швидкості, та ж обробка помилок, ті ж можливості. Єдине обмеження — `terminal()` доступний лише у передньому плані (без параметрів `background` чи `pty`).

## Обробка помилок

Коли скрипт падає, агент отримує структуровану інформацію про помилку:

- **Ненульовий код завершення**: `stderr` включено у вивід, тому агент бачить повний traceback
- **Тайм‑аут**: Скрипт завершується, і агент бачить `"Script timed out after 300s and was killed."`
- **Переривання**: Якщо користувач надсилає нове повідомлення під час виконання, скрипт завершується і агент бачить `[execution interrupted — user sent a new message]`
- **Ліміт викликів інструментів**: При досягненні 50‑викликового ліміту подальші виклики повертають повідомлення про помилку

Відповідь завжди містить `status` (success/error/timeout/interrupted), `output`, `tool_calls_made` та `duration_seconds`.

## Безпека

:::danger Security Model
Дочірній процес працює в **мінімальному середовищі**. Ключі API, токени та облікові дані за замовчуванням видаляються. Скрипт отримує доступ до інструментів лише через RPC‑канал — він не може читати секрети з змінних середовища, якщо це явно не дозволено.
:::

Змінні середовища, що містять `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL`, `PASSWD` або `AUTH` у назві, виключаються. Через це проходять лише безпечні системні змінні (`PATH`, `HOME`, `LANG`, `SHELL`, `PYTHONPATH`, `VIRTUAL_ENV` тощо).

### Передача змінних середовища у скілі

Коли скіл оголошує `required_environment_variables` у frontmatter, ці змінні **автоматично передаються** до процесів `execute_code` і `terminal` після завантаження скіла. Це дозволяє скілам використовувати їхні API‑ключі без ослаблення безпеки довільного коду.

Для випадків, коли скрипт не є частиною скіла, можна явно дозволити змінні у `config.yaml`:

```yaml
terminal:
  env_passthrough:
    - MY_CUSTOM_KEY
    - ANOTHER_TOKEN
```

Дивіться [Посібник з безпеки](/user-guide/security#environment-variable-passthrough) для повних деталей.

Hermes завжди записує скрипт і автогенерований RPC‑заглушковий файл `hermes_tools.py` у тимчасову staging‑директорію, яка очищується після виконання. У режимі `strict` скрипт також **виконується** там; у режимі `project` він виконується у робочій директорії сесії (staging‑директорія залишається у `PYTHONPATH`, тому імпорти працюють). Дочірній процес працює у власній групі процесів, що дозволяє чисто його завершити при тайм‑ауті або перериванні.

## `execute_code` vs `terminal`

| Випадок використання | `execute_code` | `terminal` |
|----------------------|----------------|-----------|
| Багатокрокові робочі процеси з викликами інструментів між ними | ✅ | ❌ |
| Простий shell‑команда | ❌ | ✅ |
| Фільтрація/обробка великих виходів інструментів | ✅ | ❌ |
| Запуск збірки або тестового набору | ❌ | ✅ |
| Циклічне перебираання результатів пошуку | ✅ | ❌ |
| Інтерактивні/фонові процеси | ❌ | ✅ |
| Потрібні API‑ключі у середовищі | ⚠️ Тільки через [passthrough](/user-guide/security#environment-variable-passthrough) | ✅ (більшість передається) |

**Загальне правило:** Використовуй `execute_code`, коли треба програмно викликати інструменти Hermes з логікою між викликами. Використовуй `terminal` для запуску shell‑команд, збірок та процесів.

## Підтримка платформ

Виконання коду потребує Unix‑доменної сокети і доступне лише на **Linux та macOS**. На Windows воно автоматично вимикається — агент переходить до звичайних послідовних викликів інструментів.