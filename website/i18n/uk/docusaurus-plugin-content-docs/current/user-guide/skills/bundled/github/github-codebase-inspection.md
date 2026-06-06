---
title: "Перевірка кодової бази — Перевіряй кодові бази за допомогою pygount: LOC, мови, співвідношення"
sidebar_label: "Codebase Inspection"
description: "Перевіряй кодові бази за допомогою pygount: LOC, мови, співвідношення"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Перевірка кодової бази

Перевіряй кодові бази за допомогою **pygount**: LOC, мови, співвідношення.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/github/codebase-inspection` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `LOC`, `Code Analysis`, `pygount`, `Codebase`, `Metrics`, `Repository` |
| Related skills | [`github-repo-management`](/docs/user-guide/skills/bundled/github/github-github-repo-management) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активована. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Перевірка кодової бази за допомогою pygount

Аналізуй репозиторії за кількістю рядків коду, розподілом мов, кількістю файлів та співвідношенням коду до коментарів за допомогою `pygount`.

## Коли використовувати

- Користувач просить підрахувати LOC (рядки коду)
- Користувач хоче розподіл мов у репозиторії
- Користувач запитує про розмір або склад кодової бази
- Користувач хоче співвідношення коду до коментарів
- Загальні питання типу «наскільки великий цей репо»

## Передумови

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

## 1. Основний підсумок (найпоширеніший)

Отримай повний розподіл мов з кількістю файлів, рядків коду та рядків коментарів:

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**ВАЖЛИВО:** Завжди використовуйте `--folders-to-skip`, щоб виключити каталоги залежностей/збірки, інакше `pygount` буде сканувати їх і працюватиме дуже довго або зависне.

## 2. Типові виключення папок

Налаштуй залежно від типу проєкту:

```bash
# Python projects
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript projects
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# General catch-all
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

## 3. Фільтрація за конкретною мовою

```bash
# Only count Python files
pygount --suffix=py --format=summary .

# Only count Python and YAML
pygount --suffix=py,yaml,yml --format=summary .
```

## 4. Детальний вивід файл за файлом

```bash
# Default format shows per-file breakdown
pygount --folders-to-skip=".git,node_modules,venv" .

# Sort by code lines (pipe through sort)
pygount --folders-to-skip=".git,node_modules,venv" . | sort -t$'\t' -k1 -nr | head -20
```

## 5. Формати виводу

```bash
# Summary table (default recommendation)
pygount --format=summary .

# JSON output for programmatic use
pygount --format=json .

# Pipe-friendly: Language, file count, code, docs, empty, string
pygount --format=summary . 2>/dev/null
```

## 6. Інтерпретація результатів

Колонки таблиці підсумку:
- **Language** — виявлена мова програмування
- **Files** — кількість файлів цієї мови
- **Code** — рядки фактичного коду (виконуваного/дефінітивного)
- **Comment** — рядки, що є коментарями або документацією
- **%** — відсоток від загальної кількості

Спеціальні псевдо‑мови:
- `__empty__` — порожні файли
- `__binary__` — бінарні файли (зображення, скомпільовані тощо)
- `__generated__` — автогенеровані файли (виявлені евристично)
- `__duplicate__` — файли з ідентичним вмістом
- `__unknown__` — нерозпізнані типи файлів

## Підводні камені

1. **Always exclude .git, node_modules, venv** — без `--folders-to-skip` `pygount` сканує все і може працювати хвилинами або зависнути на великих деревах залежностей.
2. **Markdown shows 0 code lines** — `pygount` класифікує весь вміст Markdown як коментарі, а не код. Це очікувана поведінка.
3. **JSON files show low code counts** — `pygount` може консервативно рахувати рядки JSON. Для точного підрахунку рядків у JSON використай `wc -l` безпосередньо.
4. **Large monorepos** — для дуже великих репозиторіїв розглянь можливість використання `--suffix` для цільового сканування окремих мов замість повного аналізу.