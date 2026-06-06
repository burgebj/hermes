---
title: "Hermes Agent Skill Authoring — Автор в‑репозитории SKILL"
sidebar_label: "Hermes Agent Skill Authoring"
description: "Автор в‑repo SKILL"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Авторинг навыков Hermes Agent

Автор в репозитории SKILL.md: frontmatter, validator, structure.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/software-development/hermes-agent-skill-authoring` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `skills`, `authoring`, `hermes-agent`, `conventions`, `skill-md` |
| Related skills | [`writing-plans`](/docs/user-guide/skills/bundled/software-development/software-development-writing-plans), [`requesting-code-review`](/docs/user-guide/skills/bundled/software-development/software-development-requesting-code-review) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при работе навыка.
:::

# Авторинг навыков Hermes-Agent (в репозитории)

## Обзор

SKILL.md может находиться в двух местах:

1. **Локально у пользователя:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — личный, не общий. Создаётся через `skill_manage(action='create')`.
2. **В репозитории (этот случай):** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — закоммиченный, поставляется вместе с пакетом. Используй `write_file` + `git add`. `skill_manage(action='create')` НЕ нацеливается на это дерево.

## Когда использовать

- Пользователь просит добавить навык «в этой ветке / репозитории / коммите».
- Ты коммитишь переиспользуемый workflow, который должен поставляться с Hermes Agent.
- Ты редактируешь существующий навык в `/home/bb/hermes-agent/skills/` (используй `patch` для небольших правок, `write_file` для переписей; `skill_manage` всё ещё работает для `patch` над навыками в репозитории, но не для `create`).

## Обязательный frontmatter

Источник правды: `tools/skill_manager_tool.py::_validate_frontmatter`. Жёсткие требования:

- Начинается с `---` в первых байтах (без ведущей пустой строки).
- Закрывается `\n---\n` перед телом.
- Парсится как YAML‑mapping.
- Поле `name` присутствует.
- Поле `description` присутствует, ≤ **1024 символов** (`MAX_DESCRIPTION_LENGTH`).
- После закрывающего `---` тело не пустое.

Форма, соответствующая всем навыкам в `skills/software-development/`:

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

`version` / `author` / `license` / `metadata` НЕ проверяются валидатором, но у всех пир‑навыков они есть — если их опустить, навык будет выглядеть чужеродным.

## Ограничения по размеру

- Описание: ≤ 1024 символов (проверяется).
- Полный SKILL.md: ≤ 100 000 символов (проверяется как `MAX_SKILL_CONTENT_CHARS`, ~36 k токенов).
- Навыки‑пиры в `software-development/` обычно **8‑14 k символов**. Стремись к этому диапазону. Если превышаешь 20 k, разбей на `references/*.md` и ссылайся из SKILL.md.

## Структура, соответствующая пирам

Каждый навык в репозитории примерно следует:

```
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers
- "Don't use for:" counter-triggers

## <Topic sections specific to the skill>
- Quick-reference tables are common
- Code blocks with exact commands
- Hermes-specific recipes (tests via scripts/run_tests.sh, ui-tui paths, etc.)

## Common Pitfalls
Numbered list of mistakes and their fixes.

## Verification Checklist
- [ ] Checkbox list of post-action verifications

## One-Shot Recipes (optional)
Named scenarios → concrete command sequences.
```

Не каждый раздел обязателен, но `Overview` + `When to Use` + практическое тело + подводные камни — это минимум, чтобы навык выглядел как пир.

## Размещение в директории

```
skills/<category>/<skill-name>/SKILL.md
```

Текущие категории в репозитории (проверь `ls skills/`): `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `leisure`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Выбирай ближайшую существующую категорию. Не придумывай новые верхнеуровневые категории без необходимости.

## Рабочий процесс

1. **Ознакомься с пирами** в целевой категории:
      ```
   ls skills/<category>/
   ```
   Прочитай 2‑3 SKILL.md‑файла, чтобы подобрать тон и структуру.
2. **Проверь ограничения валидатора** в `tools/skill_manager_tool.py`, если не уверен.
3. **Черновик** с помощью `write_file` в `skills/<category>/<name>/SKILL.md`.
4. **Локальная валидация**:
      ```python
   import yaml, re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = yaml.safe_load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 1024
   assert len(content) <= 100_000
   ```
5. **Git add + commit** в активной ветке.
6. **Замечание:** загрузчик навыков текущей сессии кэшируется — `skill_view` / `skills_list` не увидят новый навык до новой сессии. Это ожидаемо, а не баг.

## Перекрёстные ссылки на другие навыки

`metadata.hermes.related_skills` объединяет оба дерева (`skills/` в‑репозитории и `~/.hermes/skills/`) при загрузке. Ты МОЖЕШЬ ссылаться на локальный пользовательский навык из репозитория, но он не будет разрешён у других пользователей, клонировавших репозиторий. Предпочитай ссылки только на in‑repo навыки из in‑repo навыков. Если часто используемый навык живёт лишь в `~/.hermes/skills/`, рассмотрите его перенос в репозиторий.

## Редактирование существующих in‑repo навыков

- **Небольшая правка (опечатка, добавление подводного камня, уточнение триггера):** `skill_manage(action='patch', name=..., old_string=..., new_string=...)` работает с in‑repo навыками.
- **Крупная переписка:** `write_file` весь SKILL.md. `skill_manage(action='edit')` тоже работает, но требует полного нового содержимого.
- **Добавление вспомогательных файлов:** `write_file` в `skills/<category>/<name>/references/<file>.md`, `templates/<file>` или `scripts/<file>`. `skill_manage(action='write_file')` тоже работает и проверяет allowlist поддиректорий `references/templates/scripts/assets`.
- **Всегда коммить** правку — in‑repo навыки являются исходным кодом, а не состоянием выполнения.

## Распространённые подводные камни

1. **Использование `skill_manage(action='create')` для in‑repo навыка.** Он пишет в `~/.hermes/skills/`, а не в дерево репозитория. Для создания в‑репозитории используй `write_file`.
2. **Пробелы перед `---`.** Валидатор проверяет `content.startswith("---")`; любой ведущий пустой ряд или BOM приводит к ошибке.
3. **Слишком общее описание.** Описания пиров начинаются с «Use when …» и описывают *класс триггера*, а не одну задачу. «Use when debugging X» → «Debug X».
4. **Забыли блок author/license/metadata.** Не проверяется валидатором, но у всех пиров он есть; отсутствие делает навык выглядеть незавершённым.
5. **Создание навыка, дублирующего существующий.** Перед созданием выполните `ls skills/<category>/` и откройте 2‑3 пира. Лучше расширить существующий навык, чем создавать узконаправленный дубликат.
6. **Ожидание, что текущая сессия увидит новый навык.** Не увидит. Загрузчик навыков инициализируется при старте сессии. Проверь в новой сессии или через `skill_view`, указав точный путь.
7. **Ссылка на навыки, которых нет в‑репозитории.** `related_skills: [some-user-local-skill]` работает для тебя, но ломает другие клоны. Предпочитай только in‑repo ссылки.

## Чек‑лист проверки

- [ ] Файл находится в `skills/<category>/<name>/SKILL.md` (не в `~/.hermes/skills/`)
- [ ] Frontmatter начинается с байта 0 `---`, закрывается `\n---\n`
- [ ] Присутствуют `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}`
- [ ] Имя ≤ 64 символов, только строчные буквы и дефисы
- [ ] Описание ≤ 1024 символов и начинается с «Use when …»
- [ ] Общий размер файла ≤ 100 000 символов (стремись к 8‑15 k)
- [ ] Структура: `# Title` → `## Overview` → `## When to Use` → тело → `## Common Pitfalls` → `## Verification Checklist`
- [ ] Ссылки в `related_skills` разрешаются в‑repo (или явно помечены как пользовательские)
- [ ] Выполнено `git add skills/<category>/<name>/ && git commit` в нужной ветке