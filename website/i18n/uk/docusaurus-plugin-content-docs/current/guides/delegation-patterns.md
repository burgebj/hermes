---
sidebar_position: 13
title: "Делегування та паралельна робота"
description: "Коли і як використовувати делегування субагентів — шаблони для паралельних досліджень, рев’ю коду та роботи з багатьма файлами"
---

# Делегування та паралельна робота

Hermes може створювати ізольовані дочірні агенти для виконання завдань паралельно. Кожен підагент отримує свою розмову, термінальну сесію та набір інструментів. Повертається лише підсумковий звіт — проміжні виклики інструментів ніколи не потрапляють у твоє вікно контексту.

Для повного опису функції дивись [Subagent Delegation](/user-guide/features/delegation).

---

## Коли делегувати

**Хороші кандидати для делегування:**
- Підзадачі, що вимагають інтенсивного мислення (налагодження, рев’ю коду, синтез досліджень)
- Завдання, які заповнювали б твій контекст проміжними даними
- Паралельні незалежні потоки роботи (дослідження A і B одночасно)
- Завдання зі свіжим контекстом, коли потрібен підхід без упереджень

**Використовуй інше:**
- Одиночний виклик інструменту → просто використай інструмент безпосередньо
- Механічна багатокрокова робота з логікою між кроками → `execute_code`
- Завдання, що потребують взаємодії з користувачем → підагенти не можуть використовувати `clarify`
- Швидкі правки файлів → роби їх безпосередньо
- Тривала робота, що має пережити поточний хід → `cronjob` або `terminal(background=True, notify_on_complete=True)`. `delegate_task` є **синхронним**: якщо батьківський хід переривається, активні діти скасовуються, а їхня робота втрачається.

---

## Шаблон: Паралельне дослідження

Досліджуй три теми одночасно і отримай структуровані підсумки:

```
Research these three topics in parallel:
1. Current state of WebAssembly outside the browser
2. RISC-V server chip adoption in 2025
3. Practical quantum computing applications

Focus on recent developments and key players.
```

За лаштунками Hermes використовує:

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

Усі три працюють одночасно. Кожен підагент самостійно шукає в інтернеті та повертає підсумок. Батьківський агент потім синтезує їх у зв’язний брифінг.

---

## Шаблон: Рев’ю коду

Делегуй перевірку безпеки свіжому підагенту, який підходить до коду без упереджень:

```
Review the authentication module at src/auth/ for security issues.
Check for SQL injection, JWT validation problems, password handling,
and session management. Fix anything you find and run the tests.
```

Ключове — поле `context`: воно має містити все, що потрібне підагенту:

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

:::warning Context Problem
Підагенти **абсолютно нічого** не знають про твою розмову. Вони стартують повністю свіжо. Якщо делегувати «виправити баг, про який ми говорили», підагент не має уявлення, про який баг йдеться. Завжди передавай шляхи до файлів, повідомлення про помилки, структуру проєкту та обмеження явно.
:::

---

## Шаблон: Порівняння альтернатив

Оціни кілька підходів до однієї проблеми паралельно, а потім обери найкращий:

```
I need to add full-text search to our Django app. Evaluate three approaches
in parallel:
1. PostgreSQL tsvector (built-in)
2. Elasticsearch via django-elasticsearch-dsl
3. Meilisearch via meilisearch-python

For each: setup complexity, query capabilities, resource requirements,
and maintenance overhead. Compare them and recommend one.
```

Кожен підагент досліджує один варіант самостійно. Оскільки вони ізольовані, немає перехресного забруднення — кожна оцінка стоїть на власних перевагах. Батьківський агент отримує всі три підсумки і робить порівняння.

---

## Шаблон: Рефакторинг кількох файлів

Розподіли велику задачу рефакторингу між паралельними підагентами, кожен з яких обробляє свою частину кодової бази:

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
Кожен підагент отримує свою термінальну сесію. Вони можуть працювати в одному каталозі проєкту, не заважаючи один одному — доки редагують різні файли. Якщо два підагенти можуть торкнутися одного й того ж файлу, оброби цей файл сам після завершення паралельної роботи.
:::

---

## Шаблон: Збір даних, а потім аналіз

Використай `execute_code` для механічного збору даних, а потім делегуй важке мислення:

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

Це часто найефективніший шаблон: `execute_code` дешево виконує 10+ послідовних викликів інструментів, а підагент виконує одну дороговартісну задачу мислення зі свіжим контекстом.

---

## Вибір набору інструментів

Обирай набори інструментів згідно потреб підагента:

| Тип завдання | Набори інструментів | Чому |
|--------------|---------------------|------|
| Веб‑дослідження | `["web"]` | лише web_search + web_extract |
| Робота з кодом | `["terminal", "file"]` | доступ до оболонки + операції з файлами |
| Full‑stack | `["terminal", "file", "web"]` | усе, крім обміну повідомленнями |
| Аналіз лише для читання | `["file"]` | лише читання файлів, без оболонки |

Обмеження набору інструментів тримає підагента сфокусованим і запобігає випадковим побічним ефектам (наприклад, підагент дослідження, що запускає команди оболонки).

---

## Обмеження

- **За замовчуванням 3 паралельні завдання**: пакети за замовчуванням містять 3 одночасних підагенти (можна змінити через `delegation.max_concurrent_children` у `config.yaml`, жорсткого верхнього ліміту немає, лише мінімум 1)
- **Вкладене делегування за вимогою**: листові підагенти (за замовчуванням) не можуть викликати `delegate_task`, `clarify`, `memory`, `send_message` або `execute_code`. Оркеструючі підагенти (`role="orchestrator"`) зберігають `delegate_task` для подальшого делегування, але лише коли `delegation.max_spawn_depth` піднято вище 1 (підтримується 1‑3); інші чотири залишаються заблокованими. Вимкнути глобально можна через `delegation.orchestrator_enabled: false`.

### Налаштування паралелізму та глибини

| Конфігурація | За замовчуванням | Діапазон | Ефект |
|--------------|------------------|----------|------|
| `max_concurrent_children` | 3 | ≥1 | Розмір паралельної партії на один виклик `delegate_task` |
| `max_spawn_depth` | 1 | 1‑3 | Скільки рівнів делегування можуть створювати нових підагентів |

Приклад: запуск 30 паралельних воркерів із вкладеними підагентами:

```yaml
delegation:
  max_concurrent_children: 30
  max_spawn_depth: 2
```

- **Окремі термінали** — кожен підагент отримує свою термінальну сесію з окремим робочим каталогом і станом
- **Без історії розмови** — підагенти бачать лише `goal` і `context`, які батьківський агент передає при виклику `delegate_task`
- **За замовчуванням 50 ітерацій** — встанови `max_iterations` нижче для простих завдань, щоб заощадити кошти
- **Не довговічні** — `delegate_task` синхронний і виконується в межах батьківського ходу. Якщо батьківський хід переривається (нове повідомлення користувача, `/stop`, `/new`), всі активні діти скасовуються (`status="interrupted"`) і їхня робота втрачається. Для роботи, що має пережити поточний хід, використай `cronjob` або `terminal(background=True, notify_on_complete=True)`.

---

## Поради

**Будь конкретним у цілях.** «Виправити баг» занадто розпливчасто. «Виправити TypeError у файлі `api/handlers.py` рядок 47, де функція `process_request()` отримує `None` від `parse_body()`» дає підагенту достатньо інформації для роботи.

**Включай шляхи до файлів.** Підагенти не знають структуру твого проєкту. Завжди додавай абсолютні шляхи до релевантних файлів, кореневий каталог проєкту та команду тестування.

**Використовуй делегування для ізоляції контексту.** Іноді потрібен свіжий погляд. Делегування змушує чітко сформулювати проблему, а підагент підходить до неї без накопичених у розмові упереджень.

**Перевіряй результати.** Підсумки підагентів — це лише підсумки. Якщо підагент каже «виправив баг і тести проходять», перевір це, запустивши тести самостійно або переглянувши diff.

---

*Для повного довідника з делегуванням — усі параметри, інтеграція ACP та розширені налаштування — дивись [Subagent Delegation](/user-guide/features/delegation).*