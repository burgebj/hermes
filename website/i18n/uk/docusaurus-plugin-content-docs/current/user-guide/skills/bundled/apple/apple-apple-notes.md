---
title: "Apple Notes — Керуй Apple Notes через memo CLI: створювати, шукати, редагувати"
sidebar_label: "Apple Notes"
description: "Керуй Apple Notes через memo CLI: створюй, шукай, редагуй"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Apple Notes

Керуй Apple Notes за допомогою `memo` CLI: створюй, шукай, редагуй.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/apple/apple-notes` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | macos |
| Tags | `Notes`, `Apple`, `macOS`, `note-taking` |
| Related skills | [`obsidian`](/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Apple Notes

Використовуй `memo` для керування Apple Notes безпосередньо з терміналу. Нотатки синхронізуються між усіма пристроями Apple через iCloud.

## Передумови

- **macOS** з Notes.app
- Встановити: `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Надати доступ Automation до Notes.app, коли буде запитано (System Settings → Privacy → Automation)

## Коли використовувати

- Користувач просить створити, переглянути або знайти Apple Notes
- Збереження інформації в Notes.app для доступу з різних пристроїв
- Організація нотаток у папки
- Експорт нотаток у Markdown/HTML

## Коли НЕ використовувати

- Керування сховищем Obsidian → використай навичку `obsidian`
- Bear Notes → окрема програма (не підтримується тут)
- Нотатки лише для агента → використай інструмент `memory`

## Швидка довідка

### Перегляд нотаток

```bash
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)
```

### Створення нотаток

```bash
memo notes -a                     # Interactive editor
memo notes -a "Note Title"        # Quick add with title
```

### Редагування нотаток

```bash
memo notes -e                     # Interactive selection to edit
```

### Видалення нотаток

```bash
memo notes -d                     # Interactive selection to delete
```

### Переміщення нотаток

```bash
memo notes -m                     # Move note to folder (interactive)
```

### Експорт нотаток

```bash
memo notes -ex                    # Export to HTML/Markdown
```

## Обмеження

- Неможливо редагувати нотатки, що містять зображення або вкладення
- Інтерактивні підказки вимагають доступу до терміналу (за потреби використай `pty=true`)
- Тільки macOS — потрібен Apple Notes.app

## Правила

1. Віддавай перевагу Apple Notes, коли користувач хоче синхронізацію між пристроями (iPhone/iPad/Mac)
2. Використовуй інструмент `memory` для внутрішніх нотаток агента, які не потребують синхронізації
3. Використовуй навичку `obsidian` для управління знаннями у форматі Markdown