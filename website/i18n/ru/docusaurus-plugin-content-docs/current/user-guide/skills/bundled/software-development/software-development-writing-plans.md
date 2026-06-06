---
title: "Планирование — Создавай планы реализации: небольшие задачи, пути, код"
sidebar_label: "Writing Plans"
description: "Напиши планы реализации: небольшие задачи, пути, код"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Планы написания

Пиши планы реализации: задачи небольшими порциями, пути, код.

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Написание планов реализации

## Обзор

Пиши всесторонние планы реализации, предполагая, что у исполнителя нулевой контекст о кодовой базе и сомнительный вкус. Документируй всё, что ему нужно: какие файлы менять, полный код, команды тестирования, документацию для проверки, как верифицировать. Делай задачи небольшими порциями. DRY. YAGNI. TDD. Частые коммиты.

Предполагаем, что исполнитель — квалифицированный разработчик, но почти ничего не знает о наборе инструментов или предметной области. Предполагаем, что он не очень хорошо разбирается в проектировании тестов.

**Основной принцип:** Хороший план делает реализацию очевидной. Если кто‑то вынужден угадывать, план неполный.

## Когда использовать

**Всегда используйте перед:**
- Реализацией многошаговых функций
- Разбиением сложных требований
- Делегированием субагентам через `subagent-driven-development`

**Не пропускайте, когда:**
- Функция кажется простой (предположения могут привести к багам)
- Вы планируете реализовать её сами (будущий ты нуждается в руководстве)
- Работаете в одиночку (документация важна)

## Гранулярность задач небольших порций

**Каждая задача = 2‑5 минут сосредоточенной работы.**

Каждый шаг — отдельное действие:
- «Write the failing test» — шаг
- «Run it to make sure it fails» — шаг
- «Implement the minimal code to make the test pass» — шаг
- «Run the tests and make sure they pass» — шаг
- «Commit» — шаг

**Слишком крупно:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Правильный размер:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Структура документа плана

### Заголовок (обязательно)

Каждый план ДОЛЖЕН начинаться с:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Структура задачи

Каждая задача следует этому формату:

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

## Процесс написания

### Шаг 1: Понимание требований

Прочитай и пойми:
- Требования к функции
- Проектные документы или описание пользователя
- Критерии приёмки
- Ограничения

### Шаг 2: Исследование кодовой базы

Используй инструменты Hermes для понимания проекта:

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

### Шаг 3: Проектирование подхода

Определи:
- Паттерн архитектуры
- Организацию файлов
- Необходимые зависимости
- Стратегию тестирования

### Шаг 4: Формирование задач

Создай задачи в порядке:
1. Настройка/инфраструктура
2. Основная функциональность (TDD для каждой)
3. Пограничные случаи
4. Интеграция
5. Очистка/документация

### Шаг 5: Добавление полных деталей

Для каждой задачи включи:
- **Точные пути к файлам** (не «конфиг‑файл», а `src/config/settings.py`)
- **Полные примеры кода** (не «добавить валидацию», а сам код)
- **Точные команды** с ожидаемым выводом
- **Шаги верификации**, подтверждающие, что задача работает

### Шаг 6: Проверка плана

Проверь:
- [ ] Задачи последовательны и логичны
- [ ] Каждая задача небольшая (2‑5 мин)
- [ ] Пути к файлам точны
- [ ] Примеры кода полные (можно скопировать и вставить)
- [ ] Команды точны с ожидаемым выводом
- [ ] Нет недостающего контекста
- [ ] Принципы DRY, YAGNI, TDD применены

### Шаг 7: Сохранить план

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Принципы

### DRY (Don’t Repeat Yourself)

**Плохо:** Копировать‑вставлять валидацию в 3 местах
**Хорошо:** Выделить функцию валидации и использовать её везде

### YAGNI (You Aren’t Gonna Need It)

**Плохо:** Добавлять «гибкость» для будущих требований
**Хорошо:** Реализовать только то, что нужно сейчас

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

Каждая задача, порождающая код, должна включать полный цикл TDD:
1. Написать падающий тест
2. Запустить, убедиться в падении
3. Написать минимальный код
4. Запустить, убедиться в прохождении

Смотри навык `test-driven-development` для деталей.

### Частые коммиты

Коммит после каждой задачи:
```bash
git add [files]
git commit -m "type: description"
```

## Частые ошибки

### Неясные задачи

**Плохо:** «Добавить аутентификацию»
**Хорошо:** «Создать модель `User` с полями `email` и `password_hash`»

### Неполный код

**Плохо:** «Шаг 1: Добавить функцию валидации»
**Хорошо:** «Шаг 1: Добавить функцию валидации», после чего следует полный код функции

### Отсутствие верификации

**Плохо:** «Шаг 3: Проверить, что работает»
**Хорошо:** «Шаг 3: Запустить `pytest tests/test_auth.py -v`, ожидаемый результат: 3 passed»

### Отсутствие путей к файлам

**Плохо:** «Создать файл модели»
**Хорошо:** «Создать: `src/models/user.py`»

## Передача исполнения

После сохранения плана предложи подход к исполнению:

**«Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two‑stage review (spec compliance then code quality). Shall I proceed?»**

При исполнении используй навык `subagent-driven-development`:
- Новый `delegate_task` для каждой задачи с полным контекстом
- Проверка соответствия спецификации после каждой задачи
- Проверка качества кода после прохождения спецификации
- Продолжать только когда обе проверки одобрены

## Помни

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**Хороший план делает реализацию очевидной.**