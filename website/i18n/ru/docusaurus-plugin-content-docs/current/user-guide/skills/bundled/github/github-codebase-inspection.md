---
title: "Осмотр кодовой базы — анализируй кодовые базы с помощью pygount: LOC, языки, соотношения"
sidebar_label: "Codebase Inspection"
description: "Проверь кодовые базы с помощью pygount: LOC, языки, соотношения"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Инспекция кодовой базы

Инспектируй кодовые базы с помощью pygount: LOC, языки, соотношения.

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при активном навыке.
:::

# Инспекция кодовой базы с pygount

Анализируй репозитории на предмет количества строк кода, распределения по языкам, количества файлов и соотношения кода к комментариям с помощью `pygount`.

## Когда использовать

- Пользователь запрашивает количество LOC (строк кода)
- Пользователь хочет разбивку репозитория по языкам
- Пользователь интересуется размером или составом кодовой базы
- Пользователь хочет соотношение кода к комментариям
- Общие вопросы типа «насколько большой этот репозиторий»

## Предварительные требования

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

## 1. Базовое резюме (Самое распространённое)

Получить полную разбивку по языкам с подсчётом файлов, строк кода и строк комментариев:

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**ВАЖНО:** Всегда используй `--folders-to-skip`, чтобы исключать каталоги зависимостей/сборки, иначе pygount будет их обходить и займёт очень много времени или зависнет.

## 2. Общие исключения папок

Настраивай в зависимости от типа проекта:

```bash
# Python projects
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript projects
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# General catch-all
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

## 3. Фильтрация по конкретному языку

```bash
# Only count Python files
pygount --suffix=py --format=summary .

# Only count Python and YAML
pygount --suffix=py,yaml,yml --format=summary .
```

## 4. Подробный вывод файл за файлом

```bash
# Default format shows per-file breakdown
pygount --folders-to-skip=".git,node_modules,venv" .

# Sort by code lines (pipe through sort)
pygount --folders-to-skip=".git,node_modules,venv" . | sort -t$'\t' -k1 -nr | head -20
```

## 5. Форматы вывода

```bash
# Summary table (default recommendation)
pygount --format=summary .

# JSON output for programmatic use
pygount --format=json .

# Pipe-friendly: Language, file count, code, docs, empty, string
pygount --format=summary . 2>/dev/null
```

## 6. Интерпретация результатов

Колонки таблицы резюме:
- **Language** — обнаруженный язык программирования
- **Files** — количество файлов данного языка
- **Code** — строки реального кода (исполняемого/декларативного)
- **Comment** — строки, являющиеся комментариями или документацией
- **%** — процент от общего количества

Особые псевдо‑языки:
- `__empty__` — пустые файлы
- `__binary__` — бинарные файлы (изображения, скомпилированные и т.п.)
- `__generated__` — автоматически сгенерированные файлы (обнаруженные эвристически)
- `__duplicate__` — файлы с идентичным содержимым
- `__unknown__` — нераспознанные типы файлов

## Подводные камни

1. **Всегда исключай .git, node_modules, venv** — без `--folders-to-skip` pygount будет обходить всё и может занять минуты или зависнуть на больших деревьях зависимостей.
2. **Markdown показывает 0 строк кода** — pygount классифицирует весь контент Markdown как комментарии, а не как код. Это ожидаемое поведение.
3. **JSON‑файлы показывают низкое количество кода** — pygount может консервативно подсчитывать строки JSON. Для точного подсчёта строк JSON используй `wc -l` напрямую.
4. **Большие монорепозитории** — для очень больших репозиториев рассматривай возможность использования `--suffix` для таргетинга конкретных языков вместо сканирования всего.