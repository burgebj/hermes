---
title: "Writing Plans — Напиши плани впровадження: маленькі завдання, шляхи, код"
sidebar_label: "Writing Plans"
description: "Напиши плани реалізації: дрібні завдання, шляхи, код"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Писання планів

Write implementation plans: bite-sized tasks, paths, code.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/software-development/writing-plans` |
| Version | `1.1.0` |
| Author | Hermes Agent (adapted from obra/superpowers) |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `planning`, `design`, `implementation`, `workflow`, `documentation` |
| Related skills | [`subagent-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-subagent-driven-development), [`test-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-test-driven-development), [`requesting-code-review`](/docs/user-guide/skills/bundled/software-development/software-development-requesting-code-review) |

## Довідка: повний SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Писання планів реалізації

## Огляд

Створюй докладні плани реалізації, виходячи з того, що виконавець не має жодного контексту щодо кодової бази і, можливо, має сумнівний смак. Документуй усе, що потрібно: які файли змінювати, повний код, команди тестування, документацію для перевірки, способи верифікації. Діли роботу на bite‑sized завдання. Дотримуйся принципів DRY, YAGNI, TDD. Часті коміти.

Припускай, що виконавець — досвідчений розробник, але майже нічого не знає про інструментарій чи предметну область. Припускай, що він не дуже добре розбирається у проєктуванні тестів.

**Основний принцип:** Хороший план робить реалізацію очевидною. Якщо доводиться щось вгадувати, план неповний.

## Коли використовувати

**Завжди використовуйте перед:**
- Реалізацією багатокрокових функціональностей
- Розбиттям складних вимог
- Делегуванням підагентам через `subagent-driven-development`

**Не пропускайте, коли:**
- Функція здається простішою (припущення часто призводять до багів)
- Плануєш реалізувати сам (майбутньому «ти» потрібен гайд)
- Працюєш наодинці (документація важлива)

## Гранулярність завдань «на укус»

**Кожне завдання = 2‑5 хвилин цілеспрямованої роботи.**

Кожен крок — окрема дія:
- «Write the failing test» — крок
- «Run it to make sure it fails» — крок
- «Implement the minimal code to make the test pass» — крок
- «Run the tests and make sure they pass» — крок
- «Commit» — крок

**Занадто велике:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Правильний розмір:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Структура документа плану

### Header (Required)

Кожен план ПОВИНЕН починатися з:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Структура завдання

Кожне завдання оформлюється за наступним шаблоном:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Процес написання

### Крок 1: Розуміння вимог

Прочитай і зрозумій:
- Вимоги до функціональності
- Дизайн‑документи або опис користувача
- Критерії приймання
- Обмеження

### Крок 2: Дослідження кодової бази

Використай інструменти Hermes для ознайомлення з проєктом:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Крок 3: Проектування підходу

Визнач:
- Архітектурний патерн
- Організацію файлів
- Необхідні залежності
- Стратегію тестування

### Крок 4: Формування завдань

Створи завдання у такій послідовності:
1. Налаштування/інфраструктура
2. Основна функціональність (TDD для кожного)
3. Граничні випадки
4. Інтеграція
5. Прибирання/документація

### Крок 5: Додати повні деталі

Для кожного завдання вкажи:
- **Точні шляхи до файлів** (не «конфіг‑файл», а `src/config/settings.py`)
- **Повні приклади коду** (не «додати валідацію», а сам код)
- **Точні команди** з очікуваним виводом
- **Кроки верифікації**, що доводять успішність завдання

### Крок 6: Перегляд плану

Перевір:
- [ ] Завдання послідовні та логічні
- [ ] Кожне завдання bite‑sized (2‑5 хв)
- [ ] Шляхи до файлів точні
- [ ] Приклади коду повні (можна скопіювати‑вставити)
- [ ] Команди точні з очікуваним виводом
- [ ] Немає пропущеного контексту
- [ ] Дотримано принципів DRY, YAGNI, TDD

### Крок 7: Збереження плану

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Принципи

### DRY (Don’t Repeat Yourself)

**Погано:** копіювати‑вставляти валідацію в 3 місцях
**Добре:** винести валідацію в окрему функцію й використовувати її скрізь

### YAGNI (You Aren’t Gonna Need It)

**Погано:** додавати «гнучкість» для майбутніх вимог
**Добре:** реалізувати лише те, що потрібно зараз

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test‑Driven Development)

Кожне завдання, що генерує код, має включати повний цикл TDD:
1. Написати тест, який провалюється
2. Запустити його, переконатися у провалі
3. Написати мінімальний код
4. Запустити тест, переконатися у проходженні

Деталі — у навичці `test-driven-development`.

### Часті коміти

Коміт після кожного завдання:
```bash
git add [files]
git commit -m "type: description"
```

## Поширені помилки

### Нечіткі завдання

**Погано:** «Add authentication»
**Добре:** «Create User model with `email` and `password_hash` fields»

### Неповний код

**Погано:** «Step 1: Add validation function»
**Добре:** «Step 1: Add validation function» і далі повний код функції

### Відсутня верифікація

**Погано:** «Step 3: Test it works»
**Добре:** «Step 3: Run `pytest tests/test_auth.py -v`, expected output: 3 passed»

### Відсутні шляхи до файлів

**Погано:** «Create the model file»
**Добре:** «Create: `src/models/user.py`»

## Передача виконання

Після збереження плану запропонуй підхід до виконання:

**«Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two‑stage review (spec compliance then code quality). Shall I proceed?»**

Для виконання використай навичку `subagent-driven-development`:
- новий `delegate_task` для кожного завдання з повним контекстом
- рев’ю відповідності специфікації після кожного завдання
- рев’ю якості коду після успішного проходження специфікації
- продовжуй лише після схвалення обох рев’ю

## Пам’ятай

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**Хороший план робить реалізацію очевидною.**