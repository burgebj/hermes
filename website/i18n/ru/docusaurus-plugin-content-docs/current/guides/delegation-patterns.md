---
sidebar_position: 13
title: "Делегирование & Параллельная работа"
description: "Когда и как использовать делегирование субагентов — шаблоны для параллельных исследований, ревью кода и работы с несколькими файлами"
---

# Делегирование и параллельная работа

Hermes может создавать изолированных дочерних агентов для выполнения задач параллельно. Каждый субагент получает собственный разговор, терминальную сессию и набор инструментов. Возвращается только итоговое резюме — промежуточные вызовы инструментов никогда не попадают в окно контекста.

Для полного справочника по функции см. [Subagent Delegation](/user-guide/features/delegation).

---

## Когда делегировать

**Хорошие кандидаты для делегирования:**
- Подзадачи, требующие интенсивных рассуждений (отладка, ревью кода, синтез исследований)
- Задачи, которые заполнят ваш контекст промежуточными данными
- Параллельные независимые потоки работы (исследования A и B одновременно)
- Задачи с «чистым» контекстом, когда нужен подход без предвзятости

**Используй что‑то другое:**
- Один вызов инструмента → просто используй инструмент напрямую
- Механическая многошаговая работа с логикой между шагами → `execute_code`
- Задачи, требующие взаимодействия с пользователем → субагенты не могут использовать `clarify`
- Быстрые правки файлов → делай их напрямую
- Долговременная работа, которая должна пережить текущий ход → `cronjob` или `terminal(background=True, notify_on_complete=True)`. `delegate_task` **синхронный**: если родительский ход прерывается, активные дочерние агенты отменяются, а их работа отбрасывается.

---

## Шаблон: Параллельные исследования

Исследуй три темы одновременно и получи структурированные резюме:

```
Research these three topics in parallel:
1. Current state of WebAssembly outside the browser
2. RISC-V server chip adoption in 2025
3. Practical quantum computing applications

Focus on recent developments and key players.
```

За кулисами Hermes использует:

```python
delegate_task(tasks=[
    {
        "goal": "Research WebAssembly outside the browser in 2025",
        "context": "Focus on: runtimes (Wasmtime, Wasmer), cloud/edge use cases, WASI progress",
        "toolsets": ["web"]
    },
    {
        "goal": "Research RISC-V server chip adoption",
        "context": "Focus on: server chips shipping, cloud providers adopting, software ecosystem",
        "toolsets": ["web"]
    },
    {
        "goal": "Research practical quantum computing applications",
        "context": "Focus on: error correction breakthroughs, real-world use cases, key companies",
        "toolsets": ["web"]
    }
])
```

Все три запускаются одновременно. Каждый субагент независимо ищет в вебе и возвращает резюме. Затем родительский агент синтезирует их в единый брифинг.

---

## Шаблон: Ревью кода

Делегируй проверку безопасности свежему субагенту, который будет рассматривать код без предвзятости:

```
Review the authentication module at src/auth/ for security issues.
Check for SQL injection, JWT validation problems, password handling,
and session management. Fix anything you find and run the tests.
```

Ключевое — поле `context` — в нём должно быть всё, что требуется субагенту:

```python
delegate_task(
    goal="Review src/auth/ for security issues and fix any found",
    context="""Project at /home/user/webapp. Python 3.11, Flask, PyJWT, bcrypt.
    Auth files: src/auth/login.py, src/auth/jwt.py, src/auth/middleware.py
    Test command: pytest tests/auth/ -v
    Focus on: SQL injection, JWT validation, password hashing, session management.
    Fix issues found and verify tests pass.""",
    toolsets=["terminal", "file"]
)
```

:::warning Проблема контекста
Субагенты **ничего не знают** о вашем разговоре. Они начинают полностью с нуля. Если делегировать «исправить баг, о котором мы говорили», субагент не поймёт, о каком баге идёт речь. Всегда явно передавай пути к файлам, сообщения об ошибках, структуру проекта и ограничения.
:::

---

## Шаблон: Сравнение альтернатив

Оцени несколько подходов к одной и той же проблеме параллельно, затем выбери лучший:

```
I need to add full-text search to our Django app. Evaluate three approaches
in parallel:
1. PostgreSQL tsvector (built-in)
2. Elasticsearch via django-elasticsearch-dsl
3. Meilisearch via meilisearch-python

For each: setup complexity, query capabilities, resource requirements,
and maintenance overhead. Compare them and recommend one.
```

Каждый субагент независимо исследует один вариант. Поскольку они изолированы, нет «перекрёстного загрязнения» — каждая оценка основывается только на своих данных. Родительский агент получает все три резюме и делает сравнение.

---

## Шаблон: Рефакторинг нескольких файлов

Раздели большую задачу рефакторинга между параллельными субагентами, каждый из которых работает с отдельной частью кодовой базы:

```python
delegate_task(tasks=[
    {
        "goal": "Refactor all API endpoint handlers to use the new response format",
        "context": """Project at /home/user/api-server.
        Files: src/handlers/users.py, src/handlers/auth.py, src/handlers/billing.py
        Old format: return {"data": result, "status": "ok"}
        New format: return APIResponse(data=result, status=200).to_dict()
        Import: from src.responses import APIResponse
        Run tests after: pytest tests/handlers/ -v""",
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "Update all client SDK methods to handle the new response format",
        "context": """Project at /home/user/api-server.
        Files: sdk/python/client.py, sdk/python/models.py
        Old parsing: result = response.json()["data"]
        New parsing: result = response.json()["data"] (same key, but add status code checking)
        Also update sdk/python/tests/test_client.py""",
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "Update API documentation to reflect the new response format",
        "context": """Project at /home/user/api-server.
        Docs at: docs/api/. Format: Markdown with code examples.
        Update all response examples from old format to new format.
        Add a 'Response Format' section to docs/api/overview.md explaining the schema.""",
        "toolsets": ["terminal", "file"]
    }
])
```

:::tip
Каждый субагент получает собственную терминальную сессию. Они могут работать в одном каталоге проекта, не мешая друг другу, — при условии, что редактируют разные файлы. Если два субагента могут изменить один и тот же файл, обработай его самостоятельно после завершения параллельной работы.
:::

---

## Шаблон: Сбор данных, затем анализ

Используй `execute_code` для механического сбора данных, а затем делегируй тяжёлый аналитический этап:

```python
# Step 1: Mechanical gathering (execute_code is better here — no reasoning needed)
execute_code("""
from hermes_tools import web_search, web_extract

results = []
for query in ["AI funding Q1 2026", "AI startup acquisitions 2026", "AI IPOs 2026"]:
    r = web_search(query, limit=5)
    for item in r["data"]["web"]:
        results.append({"title": item["title"], "url": item["url"], "desc": item["description"]})

# Extract full content from top 5 most relevant
urls = [r["url"] for r in results[:5]]
content = web_extract(urls)

# Save for the analysis step
import json
with open("/tmp/ai-funding-data.json", "w") as f:
    json.dump({"search_results": results, "extracted": content["results"]}, f)
print(f"Collected {len(results)} results, extracted {len(content['results'])} pages")
""")

# Step 2: Reasoning-heavy analysis (delegation is better here)
delegate_task(
    goal="Analyze AI funding data and write a market report",
    context="""Raw data at /tmp/ai-funding-data.json contains search results and
    extracted web pages about AI funding, acquisitions, and IPOs in Q1 2026.
    Write a structured market report: key deals, trends, notable players,
    and outlook. Focus on deals over $100M.""",
    toolsets=["terminal", "file"]
)
```

Это часто самый эффективный шаблон: `execute_code` дешево обрабатывает 10+ последовательных вызовов инструментов, а субагент выполняет единственную дорогую задачу рассуждения с чистым контекстом.

---

## Выбор набора инструментов

Выбирай наборы инструментов в зависимости от потребностей субагента:

| Тип задачи | Наборы инструментов | Почему |
|-----------|----------------------|--------|
| Веб‑исследование | `["web"]` | только `web_search` + `web_extract` |
| Работа с кодом | `["terminal", "file"]` | доступ к оболочке + операции с файлами |
| Полный стек | `["terminal", "file", "web"]` | всё, кроме обмена сообщениями |
| Анализ только для чтения | `["file"]` | только чтение файлов, без оболочки |

Ограничение наборов инструментов помогает сосредоточить субагента и избежать случайных побочных эффектов (например, запуск команд оболочки субагентом‑исследователем).

---

## Ограничения

- **По умолчанию 3 параллельные задачи**: пакеты по умолчанию содержат 3 одновременно работающих субагента (настраивается через `delegation.max_concurrent_children` в `config.yaml`, без жёсткого потолка, только минимум = 1)
- **Вложенное делегирование только по запросу**: листовые субагенты (по умолчанию) не могут вызывать `delegate_task`, `clarify`, `memory`, `send_message` или `execute_code`. Оркестровочные субагенты (`role="orchestrator"`) сохраняют `delegate_task` для дальнейшего делегирования, но только когда `delegation.max_spawn_depth` поднят выше значения по умолчанию = 1 (поддерживается 1‑3 уровня); остальные четыре остаются заблокированными. Отключить глобально можно через `delegation.orchestrator_enabled: false`.

### Настройка параллелизма и глубины

| Параметр | По умолчанию | Диапазон | Эффект |
|----------|--------------|----------|--------|
| `max_concurrent_children` | 3 | ≥ 1 | Размер параллельной партии на один вызов `delegate_task` |
| `max_spawn_depth` | 1 | 1‑3 | Сколько уровней делегирования могут порождать новых субагентов |

Пример: запуск 30 параллельных воркеров с вложенными субагентами:

```yaml
delegation:
  max_concurrent_children: 30
  max_spawn_depth: 2
```

- **Отдельные терминалы** — каждый субагент получает собственную терминальную сессию с отдельным рабочим каталогом и состоянием
- **Без истории разговора** — субагенты видят только `goal` и `context`, переданные родительским агентом при вызове `delegate_task`
- **По умолчанию 50 итераций** — для простых задач уменьшай `max_iterations`, чтобы сэкономить ресурсы
- **Не долговременно** — `delegate_task` синхронный и работает внутри родительского хода. Если родитель прерывается (новое сообщение пользователя, `/stop`, `/new`), все активные дочерние агенты отменяются (`status="interrupted"`) и их работа отбрасывается. Для задач, которые должны пережить текущий ход, используй `cronjob` или `terminal(background=True, notify_on_complete=True)`.

---

## Советы

**Формулируй цели конкретно.** «Исправить баг» слишком расплывчато. «Исправить `TypeError` в `api/handlers.py` на строке 47, где `process_request()` получает `None` от `parse_body()`» даёт субагенту достаточно информации для работы.

**Указывай пути к файлам.** Субагенты не знают структуру вашего проекта. Всегда включай абсолютные пути к нужным файлам, корню проекта и команду тестирования.

**Используй делегирование для изоляции контекста.** Иногда нужен свежий взгляд. Делегирование заставляет чётко сформулировать проблему, а субагент подходит к ней без накопленных в разговоре предположений.

**Проверяй результаты.** Резюме субагентов — это лишь резюме. Если субагент сообщает «баг исправлен и тесты проходят», проверь это, запустив тесты самостоятельно или просмотрев дифф.

---

*Для полного справочника по делегированию — все параметры, интеграция ACP и расширенная конфигурация — см. [Subagent Delegation](/user-guide/features/delegation).*