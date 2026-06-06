---
title: "Subagent Driven Development — Виконуй плани через delegate_task субагенти (2‑етапний перегляд)"
sidebar_label: "Subagent Driven Development"
description: "Виконуй плани через підагенти delegate_task (2‑етапний перегляд)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Subagent‑Driven Development

Виконуй плани за допомогою підагентів `delegate_task` (двохетапний перегляд).

## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/software-development/subagent-driven-development` |
| Версія | `1.1.0` |
| Автор | Hermes Agent (adapted from obra/superpowers) |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `delegation`, `subagent`, `implementation`, `workflow`, `parallel` |
| Пов’язані навички | [`writing-plans`](/docs/user-guide/skills/bundled/software-development/software-development-writing-plans), [`requesting-code-review`](/docs/user-guide/skills/bundled/software-development/software-development-requesting-code-review), [`test-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-test-driven-development) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повний опис навички, який Hermes завантажує під час її активації. Це інструкції, які бачить агент, коли навичка активна.
:::

# Subagent‑Driven Development

## Огляд

Виконуй плани реалізації, створюючи нові підагенти для кожного завдання та застосовуючи систематичний двохетапний перегляд.

**Основний принцип:** новий підагент на завдання + двохетапний перегляд (специфікація → якість) = висока якість, швидка ітерація.

## Коли використовувати

Використовуй цю навичку, коли:
- Є план реалізації (з навички `writing-plans` або вимоги користувача)
- Завдання переважно незалежні
- Важливі якість та відповідність специфікації
- Потрібен автоматизований перегляд між завданнями

**На відміну від ручного виконання:**
- Свіжий контекст для кожного завдання (не плутаються накопичені стани)
- Автоматичний процес перегляду виявляє проблеми рано
- Узгоджені перевірки якості для всіх завдань
- Підагенти можуть ставити питання перед початком роботи

## Процес

### 1. Читання та парсинг плану

Прочитай файл плану. Витягни **всі** завдання разом із їхнім повним текстом і контекстом одразу. Створи список «to‑do»:

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

**Ключ:** Читай план **один раз**. Витягни все. Не змушуй підагенти читати файл плану — надай повний текст завдання безпосередньо в контексті.

### 2. Робочий процес для кожного завдання

Для **кожного** завдання в плані:

#### Крок 1: Запуск підагента‑реалізатора

Використай `delegate_task` з повним контекстом:

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

#### Крок 2: Запуск переглядача відповідності специфікації

Після завершення реалізатора перевір відповідність оригінальній специфікації:

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

**Якщо виявлено проблеми зі специфікацією:** виправ прогалини, потім повтори перегляд специфікації. Продовжуй лише після досягнення відповідності.

#### Крок 3: Запуск переглядача якості коду

Після успішної перевірки специфікації:

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

**Якщо виявлено проблеми з якістю:** виправ їх, повтори перегляд. Продовжуй лише після схвалення.

#### Крок 4: Позначити завершеним

```python
todo([{"id": "task-1", "content": "Create User model with email field", "status": "completed"}], merge=True)
```

### 3. Фінальний перегляд

Після **всіх** завдань запусти підагента‑інтеграційного переглядача:

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

### 4. Перевірка та коміт

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit if needed
git add -A && git commit -m "feat: complete [feature name] implementation"
```

## Гранулярність завдань

**Кожне завдання = 2‑5 хвилин цілеспрямованої роботи.**

**Занадто велике:**
- «Реалізувати систему автентифікації користувачів»

**Оптимальний розмір:**
- «Створити модель User з полями email та password»
- «Додати функцію хешування пароля»
- «Створити endpoint входу»
- «Додати генерацію JWT‑токену»
- «Створити endpoint реєстрації»

## Червоні прапорці — Ніколи не роби

- Починати реалізацію без плану
- Пропускати перегляди (відповідність специфікації **або** якість коду)
- Продовжувати роботу з незакритими критичними/важливими проблемами
- Запускати кілька підагентів‑реалізаторів для завдань, що змінюють одні й ті ж файли
- Давати підагенту читати файл плану (надай повний текст у контексті)
- Пропускати контекст, що встановлює сцену (підагенту треба розуміти, куди вписується завдання)
- Ігнорувати питання підагента (відповідай перед тим, як дозволити продовжити)
- Прихилятись до «досить близько» щодо відповідності специфікації
- Пропускати цикли перегляду (рецензент знайшов проблеми → реалізатор виправляє → повторний перегляд)
- Дозволяти самоперегляд реалізатора замість справжнього перегляду (обидва потрібні)
- **Починати перегляд якості коду до того, як специфікація пройде** (неправильний порядок)
- Переходити до наступного завдання, доки якийсь перегляд має відкриті питання

## Робота з проблемами

### Якщо підагент ставить питання

- Відповідай чітко та повністю
- За потреби надай додатковий контекст
- Не квапити підагента до реалізації

### Якщо рецензент виявив проблеми

- Підагент‑реалізатор (або новий підагент) виправляє їх
- Рецензент переглядає знову
- Повторюй, доки не отримаєш схвалення
- Не пропускай повторний перегляд

### Якщо підагент не справився із завданням

- Запусти новий підагент‑виправлення з конкретними інструкціями щодо помилки
- Не намагайся виправляти вручну у сесії контролера (забруднення контексту)

## Примітки щодо ефективності

**Навіщо новий підагент на завдання:**
- Запобігає забрудненню контексту накопиченим станом
- Кожен підагент отримує чистий, сфокусований контекст
- Не виникає плутанини через код або міркування попередніх завдань

**Навіщо двохетапний перегляд:**
- Перегляд специфікації виявляє недобудову/перебудову на ранньому етапі
- Перегляд якості гарантує, що реалізація добре побудована
- Виявляє проблеми до їх накопичення між завданнями

**Вартісний компроміс:**
- Більше викликів підагентів (реалізатор + 2 переглядачі на завдання)
- Але проблеми виявляються рано (дешевше, ніж виправляти складні баги пізніше)

## Інтеграція з іншими навичками

### З `writing-plans`

Ця навичка **виконує** плани, створені `writing-plans`:
1. Вимоги користувача → `writing-plans` → план реалізації
2. План реалізації → `subagent-driven-development` → робочий код

### З `test-driven-development`

Підагенти‑реалізатори мають дотримуватись TDD:
1. Спочатку написати тест, що провалюється
2. Реалізувати мінімальний код
3. Перевірити, що тест проходить
4. Закомітити

Включай інструкції TDD у контекст кожного підагента‑реалізатора.

### З `requesting-code-review`

Двохетапний процес — це саме код‑рев’ю. Для фінального інтеграційного перегляду використай виміри рев’ю з навички `requesting-code-review`.

### З `systematic-debugging`

Якщо підагент натрапляє на баги під час реалізації:
1. Дотримуйся процесу `systematic-debugging`
2. Знайди корінь проблеми перед виправленням
3. Напиши регресійний тест
4. Продовжуй реалізацію

## Приклад робочого процесу

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

## Пам’ятай

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
```

**Якість — не випадковість. Це результат систематичного процесу.**

## Додаткова література (завантажуй за потреби)

Коли оркестрація потребує значного використання контексту, довгих циклів перегляду або складних контрольних точок, завантажуй ці довідники для конкретної дисципліни:

- **`references/context-budget-discipline.md`** — модель деградації контексту в чотири рівні (PEAK / GOOD / DEGRADING / POOR), правила глибини читання, що масштабуються з розміром вікна контексту, та ранні сигнали тихої деградації. Завантажуй, коли запуск явно споживатиме великий обсяг контексту (багатофазові плани, багато підагентів, великі артефакти).
- **`references/gates-taxonomy.md`** — чотири канонічні типи воріт (Pre‑flight, Revision, Escalation, Abort) з їхньою поведінкою, відновленням та прикладами. Завантажуй, коли проектуєш або переглядаєш будь‑який робочий процес із контрольними точками — використовуй термінологію явно, щоб кожне ворота мали визначений вхід, поведінку при невдачі та правила відновлення.

Обидва довідники адаптовані з `gsd-build/get-shit-done` (MIT © 2025 Lex Christopherson).