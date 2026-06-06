---
title: "Разработка, управляемая подагентами — Выполняй планы через подагенты delegate_task (двухэтапный обзор)"
sidebar_label: "Subagent Driven Development"
description: "Выполняй планы через субагентов delegate_task (двухэтапный обзор)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Разработка с помощью субагентов

Выполняй планы через субагенты `delegate_task` (двухэтапный обзор).

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/software-development/subagent-driven-development` |
| Version | `1.1.0` |
| Author | Hermes Agent (adapted from obra/superpowers) |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `delegation`, `subagent`, `implementation`, `workflow`, `parallel` |
| Related skills | [`writing-plans`](/docs/user-guide/skills/bundled/software-development/software-development-writing-plans), [`requesting-code-review`](/docs/user-guide/skills/bundled/software-development/software-development-requesting-code-review), [`test-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-test-driven-development) |

## Ссылка: полный SKILL.md

:::info
Ниже полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Subagent-Driven Development

## Обзор

Выполняй планы реализации, отправляя новые субагенты для каждой задачи с систематическим двухэтапным обзором.

**Основной принцип:** Новый субагент для каждой задачи + двухэтапный обзор (спецификация → качество) = высокое качество, быстрая итерация.

## Когда использовать

Используй этот навык, когда:
- У тебя есть план реализации (из навыка writing-plans или требования пользователя)
- Задачи в основном независимы
- Важны качество и соответствие спецификации
- Ты хочешь автоматический обзор между задачами

**по сравнению с ручным выполнением:**
- Новый контекст для каждой задачи (нет путаницы от накопленного состояния)
- Автоматический процесс обзора ловит проблемы рано
- Последовательные проверки качества для всех задач
- Субагенты могут задавать вопросы перед началом работы

## Процесс

### 1. Чтение и разбор плана

Прочитай файл плана. Извлеки ВСЕ задачи с их полным текстом и контекстом сразу. Создай список дел:

```python
# Read the plan
read_file("docs/plans/feature-plan.md")

# Create todo list with all tasks
todo([
    {"id": "task-1", "content": "Create User model with email field", "status": "pending"},
    {"id": "task-2", "content": "Add password hashing utility", "status": "pending"},
    {"id": "task-3", "content": "Create login endpoint", "status": "pending"},
])
```

**Ключ:** Читать план ОДИН раз. Извлечь всё. Не заставляй субагентов читать файл плана — передай полный текст задачи напрямую в контекст.

### 2. Рабочий процесс для каждой задачи

Для КАЖДОЙ задачи в плане:

#### Шаг 1: Запуск субагента‑implementer

Используй `delegate_task` с полным контекстом:

```python
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model with password hashing"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

#### Шаг 2: Запуск проверяющего соответствия спецификации

После завершения implementer‑subagent проверь соответствие оригинальной спецификации:

```python
delegate_task(
    goal="Review if implementation matches the spec from the plan",
    context="""
    ORIGINAL TASK SPEC:
    - Create src/models/user.py with User class
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    CHECK:
    - [ ] All requirements from spec implemented?
    - [ ] File paths match spec?
    - [ ] Function signatures match spec?
    - [ ] Behavior matches expected?
    - [ ] Nothing extra added (no scope creep)?

    OUTPUT: PASS or list of specific spec gaps to fix.
    """,
    toolsets=['file']
)
```

**Если найдены проблемы со спецификацией:** Исправь пробелы, затем повторно запусти проверку спецификации. Продолжай только после соответствия спецификации.

#### Шаг 3: Запуск проверяющего качества кода

После того как проверка спецификации прошла:

```python
delegate_task(
    goal="Review code quality for Task 1 implementation",
    context="""
    FILES TO REVIEW:
    - src/models/user.py
    - tests/models/test_user.py

    CHECK:
    - [ ] Follows project conventions and style?
    - [ ] Proper error handling?
    - [ ] Clear variable/function names?
    - [ ] Adequate test coverage?
    - [ ] No obvious bugs or missed edge cases?
    - [ ] No security issues?

    OUTPUT FORMAT:
    - Critical Issues: [must fix before proceeding]
    - Important Issues: [should fix]
    - Minor Issues: [optional]
    - Verdict: APPROVED or REQUEST_CHANGES
    """,
    toolsets=['file']
)
```

**Если найдены проблемы с качеством:** Исправь их, проведи повторный обзор. Продолжай только после одобрения.

#### Шаг 4: Пометить как завершённую

```python
todo([{"id": "task-1", "content": "Create User model with email field", "status": "completed"}], merge=True)
```

### 3. Финальный обзор

После завершения ВСЕХ задач запусти финального интеграционного проверяющего:

```python
delegate_task(
    goal="Review the entire implementation for consistency and integration issues",
    context="""
    All tasks from the plan are complete. Review the full implementation:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for merge?
    """,
    toolsets=['terminal', 'file']
)
```

### 4. Проверка и коммит

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit if needed
git add -A && git commit -m "feat: complete [feature name] implementation"
```

## Гранулярность задач

**Каждая задача = 2–5 минут сосредоточенной работы.**

**Слишком крупно:**
- «Реализовать систему аутентификации пользователей»

**Подходящий размер:**
- «Создать модель User с полями email и password»
- «Добавить функцию хеширования пароля»
- «Создать endpoint входа»
- «Добавить генерацию JWT‑токена»
- «Создать endpoint регистрации»

## Красные флаги — чего никогда не делай

- Начинать реализацию без плана
- Пропускать обзоры (соответствие спецификации ИЛИ качество кода)
- Продолжать с нерешёнными критическими/важными проблемами
- Запускать несколько субагентов‑implementer для задач, затрагивающих одни и те же файлы
- Заставлять субагент читать файл плана (предоставляй полный текст в контексте)
- Пропускать контекст, задающий сцену (субагенту нужно понять, где задача вписывается)
- Игнорировать вопросы субагента (ответь, прежде чем позволить продолжить)
- Принимать «достаточно близко» для соответствия спецификации
- Пропускать циклы обзора (обзорщик нашёл проблемы → исполнитель исправляет → повторный обзор)
- Позволять исполнителю самопроверяться вместо реального обзора (нужны оба)
- **Начинать обзор качества кода до того, как проверка спецификации ПРойдёт** (неправильный порядок)
- Переходить к следующей задаче, пока любой из обзоров имеет открытые проблемы

## Обработка проблем

### Если субагент задаёт вопросы

- Отвечай ясно и полностью
- При необходимости предоставляй дополнительный контекст
- Не торопи его к реализации

### Если проверяющий находит проблемы

- Subagent‑implementer (или новый) исправляет их
- Проверяющий проводит повторный обзор
- Повторяй, пока не будет одобрено
- Не пропускай повторный обзор

### Если субагент не справляется с задачей

- Запусти нового subagent‑fix с конкретными инструкциями о том, что пошло не так
- Не пытайся исправлять вручную в сессии контроллера (загрязнение контекста)

## Замечания по эффективности

**Почему новый субагент для каждой задачи:**
- Предотвращает загрязнение контекста накопленным состоянием
- Каждый субагент получает чистый, сфокусированный контекст
- Нет путаницы от кода или рассуждений предыдущих задач

**Почему двухэтапный обзор:**
- Обзор спецификации ловит недостроенные/перестроенные части рано
- Обзор качества гарантирует, что реализация построена хорошо
- Ловит проблемы до того, как они накапливаются через задачи

**Компромисс по стоимости:**
- Больше вызовов субагентов (implementer + 2 обзора на задачу)
- Но проблемы ловятся рано (дешевле, чем отладка накопленных проблем позже)

## Интеграция с другими навыками

### С writing-plans

Этот навык ИСПОЛЬЗУЕТ планы, созданные навыком writing-plans:
1. Требования пользователя → writing-plans → план реализации
2. План реализации → subagent-driven-development → рабочий код

### С test-driven-development

Subagent‑implementer должны следовать TDD:
1. Сначала написать падающий тест
2. Реализовать минимальный код
3. Проверить, что тест проходит
4. Закоммитить

Включай инструкции TDD в каждый контекст исполнителя.

### С requesting-code-review

Двухэтапный процесс обзора ЯВЛЯЕТСЯ код‑ревью. Для финального интеграционного обзора используй измерения обзора из навыка requesting-code-review.

### С systematic-debugging

Если субагент сталкивается с багами во время реализации:
1. Следуй процессу systematic-debugging
2. Найди коренную причину перед исправлением
3. Напиши регрессионный тест
4. Возобнови реализацию

## Пример рабочего процесса

```
[Read plan: docs/plans/auth-feature.md]
[Create todo list with 5 tasks]

--- Task 1: Create User model ---
[Dispatch implementer subagent]
  Implementer: "Should email be unique?"
  You: "Yes, email must be unique"
  Implementer: Implemented, 3/3 tests passing, committed.

[Dispatch spec reviewer]
  Spec reviewer: ✅ PASS — all requirements met

[Dispatch quality reviewer]
  Quality reviewer: ✅ APPROVED — clean code, good tests

[Mark Task 1 complete]

--- Task 2: Password hashing ---
[Dispatch implementer subagent]
  Implementer: No questions, implemented, 5/5 tests passing.

[Dispatch spec reviewer]
  Spec reviewer: ❌ Missing: password strength validation (spec says "min 8 chars")

[Implementer fixes]
  Implementer: Added validation, 7/7 tests passing.

[Dispatch spec reviewer again]
  Spec reviewer: ✅ PASS

[Dispatch quality reviewer]
  Quality reviewer: Important: Magic number 8, extract to constant
  Implementer: Extracted MIN_PASSWORD_LENGTH constant
  Quality reviewer: ✅ APPROVED

[Mark Task 2 complete]

... (continue for all tasks)

[After all tasks: dispatch final integration reviewer]
[Run full test suite: all passing]
[Done!]
```

## Помни

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
```

**Качество — не случайность. Это результат систематического процесса.**

## Дополнительные материалы (загружаются по необходимости)

Когда оркестрация требует значительного использования контекста, длинных циклов обзора или сложных проверочных контрольных точек, загрузи эти ссылки для конкретной дисциплины:

- **`references/context-budget-discipline.md`** — Модель деградации контекста в четыре уровня (PEAK / GOOD / DEGRADING / POOR), правила глубины чтения, масштабируемые с размером окна контекста, и ранние признаки тихой деградации. Загрузи, когда запуск явно потребует значительный контекст (многофазные планы, множество субагентов, большие артефакты).
- **`references/gates-taxonomy.md`** — Четыре канонических типа ворот (Pre-flight, Revision, Escalation, Abort) с поведением, восстановлением и примерами. Загрузи, когда проектируешь или проверяешь любой рабочий процесс с проверочными контрольными точками — используй терминологию явно, чтобы у каждой вороты были определённые вход, поведение при сбое и правила возобновления.

Обе ссылки адаптированы из gsd-build/get-shit-done (MIT © 2025 Lex Christopherson).