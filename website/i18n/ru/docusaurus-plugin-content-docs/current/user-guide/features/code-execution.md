---
sidebar_position: 8
title: "Выполнение кода"
description: "Программное выполнение Python с доступом к RPC‑инструменту — свести многошаговые рабочие процессы в один ход"
---

# Выполнение кода (Программный вызов инструментов)

Инструмент `execute_code` позволяет агенту писать Python‑скрипты, которые вызывают инструменты Hermes программно, сворачивая многошаговые рабочие процессы в один ход LLM. Скрипт запускается в дочернем процессе на хосте агента, общаясь с Hermes через RPC‑сокет Unix‑домена.

## Как это работает

1. Агент пишет Python‑скрипт, используя `from hermes_tools import ...`
2. Hermes генерирует заглушку модуля `hermes_tools.py` с RPC‑функциями
3. Hermes открывает Unix‑доменный сокет и запускает поток‑слушатель RPC
4. Скрипт выполняется в дочернем процессе — вызовы инструментов передаются через сокет обратно в Hermes
5. В LLM возвращается только вывод `print()` скрипта; промежуточные результаты инструментов никогда не попадают в окно контекста

```python
# The agent can write scripts like:
from hermes_tools import web_search, web_extract

results = web_search("Python 3.13 features", limit=5)
for r in results["data"]["web"]:
    content = web_extract([r["url"]])
    # ... filter and process ...
print(summary)
```

**Доступные инструменты внутри скриптов:** `web_search`, `web_extract`, `read_file`, `write_file`, `search_files`, `patch`, `terminal` (только в foreground).

## Когда агент использует это

Агент использует `execute_code`, когда есть:

- **3 + вызова инструментов** с логикой обработки между ними
- Массовая фильтрация данных или условные ветвления
- Циклы над результатами

Ключевое преимущество: промежуточные результаты инструментов не попадают в окно контекста — возвращается только финальный вывод `print()`, что значительно снижает расход токенов.

## Практические примеры

### Конвейер обработки данных

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

### Многошаговое веб‑исследование

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

### Массовый рефакторинг файлов

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

### Конвейер сборки и тестов

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

## Режим выполнения

`execute_code` имеет два режима выполнения, управляемых параметром `code_execution.mode` в `~/.hermes/config.yaml`:

| Режим | Рабочий каталог | Интерпретатор Python |
|------|-------------------|--------------------|
| **`project`** (по умолчанию) | Рабочий каталог сессии (тот же, что у `terminal()`) | Активный `VIRTUAL_ENV` / `CONDA_PREFIX` python, с откатом к собственному python Hermes |
| `strict` | Временный изолированный каталог, отделённый от проекта пользователя | `sys.executable` (собственный python Hermes) |

**Когда оставлять `project`:** если нужны `import pandas`, `from my_project import foo` или относительные пути вроде `open(".env")` — они будут работать так же, как в `terminal()`. Это почти всегда желаемое поведение.

**Когда переключать на `strict`:** если требуется максимальная воспроизводимость — одинаковый интерпретатор в каждой сессии независимо от активированного пользователем venv, и скрипты должны быть изолированы от дерева проекта (нет риска случайного чтения файлов проекта по относительному пути).

```yaml
# ~/.hermes/config.yaml
code_execution:
  mode: project   # or "strict"
```

Поведение запасного варианта в режиме `project`: если `VIRTUAL_ENV` / `CONDA_PREFIX` не установлен, повреждён или указывает на Python старше 3.8, разрешатель чисто откатывается к `sys.executable` — агент никогда не остаётся без работающего интерпретатора.

Критически важные инварианты безопасности одинаковы в обоих режимах:

- очистка окружения (удаляются API‑ключи, токены, учётные данные)
- белый список инструментов (скрипты не могут рекурсивно вызывать `execute_code`, `delegate_task` или инструменты MCP)
- ограничения ресурсов (таймаут, лимит stdout, лимит вызовов инструментов)

Переключение режима меняет только место и интерпретатор выполнения скриптов, а не то, какие учётные данные они видят и какие инструменты могут вызывать.

## Ограничения ресурсов

| Ресурс | Лимит | Примечания |
|----------|-------|-------|
| **Таймаут** | 5 минут (300 s) | Скрипт завершается `SIGTERM`, затем через 5 s — `SIGKILL` |
| **Stdout** | 50 KB | Вывод обрезается с уведомлением `[output truncated at 50KB]` |
| **Stderr** | 10 KB | Включается в вывод при ненулевом коде завершения для отладки |
| **Вызовы инструментов** | 50 за исполнение | При достижении лимита возвращается ошибка |

Все лимиты настраиваются через `config.yaml`:

```yaml
# In ~/.hermes/config.yaml
code_execution:
  mode: project      # project (default) | strict
  timeout: 300       # Max seconds per script (default: 300)
  max_tool_calls: 50 # Max tool calls per execution (default: 50)
```

## Как работают вызовы инструментов внутри скриптов

Когда ваш скрипт вызывает функцию вроде `web_search("query")`:

1. Вызов сериализуется в JSON и отправляется через Unix‑доменный сокет в родительский процесс
2. Родитель передаёт его стандартному обработчику `handle_function_call`
3. Результат отправляется обратно через сокет
4. Функция возвращает разобранный результат

Это значит, что вызовы инструментов внутри скриптов работают так же, как обычные вызовы — одинаковые ограничения скорости, обработка ошибок и возможности. Единственное ограничение: `terminal()` доступен только в foreground (без параметров `background` или `pty`).

## Обработка ошибок

Когда скрипт падает, агент получает структурированную информацию об ошибке:

- **Ненулевой код выхода**: `stderr` включён в вывод, агент видит полный traceback
- **Таймаут**: скрипт завершается, агент получает сообщение `"Script timed out after 300s and was killed."`
- **Прерывание**: если пользователь отправил новое сообщение во время выполнения, скрипт прекращается и агент видит `[execution interrupted — user sent a new message]`
- **Лимит вызовов инструментов**: при достижении лимита 50 последующие вызовы возвращают сообщение об ошибке

Ответ всегда содержит `status` (success/error/timeout/interrupted), `output`, `tool_calls_made` и `duration_seconds`.

## Безопасность

:::danger Модель безопасности
Дочерний процесс запускается в **минимальном окружении**. API‑ключи, токены и учётные данные по умолчанию удаляются. Скрипт получает доступ к инструментам только через RPC‑канал — он не может читать секреты из переменных окружения, если это явно не разрешено.
:::

Переменные окружения, содержащие в имени `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL`, `PASSWD` или `AUTH`, исключаются. Проходят только безопасные системные переменные (`PATH`, `HOME`, `LANG`, `SHELL`, `PYTHONPATH`, `VIRTUAL_ENV` и т.д.).

### Пропуск переменных окружения навыка

Когда навык объявляет `required_environment_variables` в своём frontmatter, эти переменные **автоматически передаются** в дочерние процессы `execute_code` и `terminal` после загрузки навыка. Это позволяет навыкам использовать свои объявленные API‑ключи без ослабления общей модели безопасности.

Для случаев, не связанных с навыками, переменные можно явно добавить в whitelist в `config.yaml`:

```yaml
terminal:
  env_passthrough:
    - MY_CUSTOM_KEY
    - ANOTHER_TOKEN
```

См. [Руководство по безопасности](/user-guide/security#environment-variable-passthrough) для полного описания.

Hermes всегда записывает скрипт и автоматически сгенерированную RPC‑заглушку `hermes_tools.py` во временный staging‑каталог, который удаляется после выполнения. В режиме `strict` скрипт также **выполняется** там; в режиме `project` он запускается в рабочем каталоге сессии (staging‑каталог остаётся в `PYTHONPATH`, поэтому импорты работают). Дочерний процесс находится в своей группе процессов, что позволяет чисто завершать его при таймауте или прерывании.

## `execute_code` vs `terminal`

| Сценарий | `execute_code` | `terminal` |
|----------|----------------|------------|
| Многошаговые рабочие процессы с вызовами инструментов между ними | ✅ | ❌ |
| Простая командная оболочка | ❌ | ✅ |
| Фильтрация/обработка больших выводов инструментов | ✅ | ❌ |
| Запуск сборки или тестового набора | ❌ | ✅ |
| Циклическая обработка результатов поиска | ✅ | ❌ |
| Интерактивные/фоновые процессы | ❌ | ✅ |
| Необходимы API‑ключи в окружении | ⚠️ Только через [passthrough](/user-guide/security#environment-variable-passthrough) | ✅ (большинство проходит) |

**Практический совет:** используй `execute_code`, когда нужно программно вызывать инструменты Hermes с логикой между вызовами. Для выполнения команд оболочки, сборок и процессов используй `terminal`.

## Поддерживаемые платформы

Выполнение кода требует Unix‑доменных сокетов и доступно только на **Linux и macOS**. На Windows оно автоматически отключается — агент переходит к обычным последовательным вызовам инструментов.