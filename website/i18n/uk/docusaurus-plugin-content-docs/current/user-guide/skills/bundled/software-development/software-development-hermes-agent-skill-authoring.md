---
title: "Hermes Agent Skill Authoring — Автор у‑репозиторії SKILL"
sidebar_label: "Hermes Agent Skill Authoring"
description: "Автор у репозиторії SKILL"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Авторинг навичок Hermes Agent

Автор у‑репозиторії SKILL.md: frontmatter, validator, structure.

## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/software-development/hermes-agent-skill-authoring` |
| Версія | `1.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `skills`, `authoring`, `hermes-agent`, `conventions`, `skill-md` |
| Пов’язані навички | [`writing-plans`](/docs/user-guide/skills/bundled/software-development/software-development-writing-plans), [`requesting-code-review`](/docs/user-guide/skills/bundled/software-development/software-development-requesting-code-review) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Авторинг навичок Hermes-Agent (у‑репозиторії)

## Огляд

Існує два місця, де може знаходитися SKILL.md:

1. **Локальна користувача:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — особиста, не спільна. Створюється через `skill_manage(action='create')`.
2. **У‑репозиторії (цей випадок):** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — закомічена, постачається разом з пакетом. Використовуй `write_file` + `git add`. `skill_manage(action='create')` НЕ цілиться в це дерево.

## Коли використовувати

- Користувач просить додати навичку «у цьому гілці / репо / коміті».
- Ти комітиш багаторазовий workflow, який має постачатися разом з hermes-agent.
- Ти редагуєш існуючу навичку у `/home/bb/hermes-agent/skills/` (використовуй `patch` для невеликих правок, `write_file` для перепису; `skill_manage` все ще працює для патчів у‑репозиторійних навичок, але не для `create`).

## Обов’язковий Frontmatter

Джерело правди: `tools/skill_manager_tool.py::_validate_frontmatter`. Жорсткі вимоги:

- Починається з `---` як перші байти (без попереднього порожнього рядка).
- Закривається `\n---\n` перед тілом.
- Парситься як YAML‑меппінг.
- Поле `name` присутнє.
- Поле `description` присутнє, ≤ **1024 символи** (`MAX_DESCRIPTION_LENGTH`).
- Непорожнє тіло після закриваючого `---`.

Форма, що використовується кожною навичкою у `skills/software-development/`:

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

`version` / `author` / `license` / `metadata` НЕ перевіряються валідатором, але у всіх peers вони є — пропусти їх, і твоя навичка виглядатиме чужою.

## Обмеження розмірів

- Опис: ≤ 1024 символи (перевіряється).
- Повний SKILL.md: ≤ 100 000 символів (перевіряється як `MAX_SKILL_CONTENT_CHARS`, ~36k токенів).
- Навички‑peers у `software-development/` мають **8‑14k символів**. Орієнтуйся на цей діапазон. Якщо перевищуєш 20k, розбий на `references/*.md` і посилайся на них з SKILL.md.

## Структура, що відповідає peer‑моделі

Кожна навичка у‑репозиторії приблизно слідує:

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

Не кожен розділ обов’язковий, але `Overview` + `When to Use` + практичне тіло + підказки — мінімум, щоб навичка виглядала як peer.

## Розміщення у директорії

```
skills/<category>/<skill-name>/SKILL.md
```

Поточні категорії в репозиторії (перевір за допомогою `ls skills/`): `autonomous-ai-agents`, `creative`, `data‑science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `leisure`, `mcp`, `media`, `mlops/*`, `note‑taking`, `productivity`, `red‑teaming`, `research`, `smart‑home`, `social‑media`, `software-development`.

Обери найблизьку існуючу категорію. Не вигадуй нові верхньорівневі категорії без потреби.

## Робочий процес

1. **Ознайомся з peers** у цільовій категорії:
   ```
   ls skills/<category>/
   ```
   Прочитай 2‑3 SKILL.md peers, щоб збігтися у тоні та структурі.
2. **Перевір обмеження валідатора** у `tools/skill_manager_tool.py`, якщо сумніваєшся.
3. **Чернетка** за допомогою `write_file` у `skills/<category>/<name>/SKILL.md`.
4. **Локальна валідація**:
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
5. **Git add + commit** у активній гілці.
6. **Примітка:** завантажувач навичок у поточній сесії кешується — `skill_view` / `skills_list` не побачать нову навичку, доки не запустиш нову сесію. Це очікувано, а не баг.

## Перехресні посилання на інші навички

`metadata.hermes.related_skills` об’єднує обидва дерева (`skills/` у‑репозиторії та `~/.hermes/skills/`) під час завантаження. ТИ МОЖЕШ посилатися на локальну користувача навичку з у‑репозиторійної, але вона не буде резольвитися у інших користувачів, які клонують репо. Віддавай перевагу посиланням лише на у‑репозиторійні навички. Якщо часто використовувана навичка живе лише в `~/.hermes/skills/`, розглянь можливість перенести її в репо.

## Редагування існуючих у‑репозиторійних навичок

- **Невелика правка (опечатка, додана підказка, уточнений тригер):** `skill_manage(action='patch', name=..., old_string=..., new_string=...)` працює з у‑репозиторійними навичками.
- **Грубе переписування:** `write_file` весь SKILL.md. `skill_manage(action='edit')` теж працює, але потребує повного нового вмісту.
- **Додавання допоміжних файлів:** `write_file` у `skills/<category>/<name>/references/<file>.md`, `templates/<file>`, або `scripts/<file>`. `skill_manage(action='write_file')` також працює і примушує дотримуватись allowlist‑у піддиректорій `references/templates/scripts/assets`.
- **Завжди коміти** правку — у‑репозиторійні навички є джерелом, а не станом виконання.

## Поширені підводні камені

1. **Використання `skill_manage(action='create')` для у‑репозиторійної навички.** Воно пише у `~/.hermes/skills/`, а не в дерево репо. Для створення у‑репо використай `write_file`.

2. **Пробіли перед `---`.** Валідатор перевіряє `content.startswith("---")`; будь‑який порожній рядок або BOM призведе до помилки.

3. **Занадто загальний опис.** Опис peers починається з «Use when …» і описує *клас тригера*, а не конкретне завдання. «Use when debugging X» → «Debug X».

4. **Забуті блоки author/license/metadata.** Не перевіряються валідатором, але у всіх peers вони є; їх відсутність робить навичку виглядати незавершеною.

5. **Створення навички, що дублює peer.** Перед створенням переглянь `ls skills/<category>/` і відкрий 2‑3 peers. Краще розширити існуючу навичку, ніж створювати вузького брата.

6. **Очікування, що поточна сесія побачить нову навичку.** Не побачить. Завантажувач навичок ініціалізується під час старту сесії. Перевір у новій сесії або через `skill_view` з точним шляхом.

7. **Посилання на навички, яких немає у‑репо.** `related_skills: [some-user-local-skill]` працює для тебе, але ламає інші клонування. Віддавай перевагу лише у‑репо посиланням.

## Чек‑лист перевірки

- [ ] Файл розташований за `skills/<category>/<name>/SKILL.md` (не в `~/.hermes/skills/`)
- [ ] Frontmatter починається з байту 0 з `---`, закінчується `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` присутні
- [ ] Назва ≤ 64 символи, лише нижній регістр і дефіси
- [ ] Опис ≤ 1024 символи і починається з «Use when …»
- [ ] Загальний розмір файлу ≤ 100 000 символів (ціль — 8‑15k)
- [ ] Структура: `# Title` → `## Overview` → `## When to Use` → тіло → `## Common Pitfalls` → `## Verification Checklist`
- [ ] `related_skills` посилання резольвються у‑репо (або явно зазначені як user‑local)
- [ ] `git add skills/<category>/<name>/ && git commit` виконано у потрібній гілці