---
title: "Apple Notes — Управляй Apple Notes через memo CLI: создавай, ищи, редактируй"
sidebar_label: "Apple Notes"
description: "Управляй Apple Notes через memo CLI: создавай, ищи, редактируй"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Apple Notes

Управляй Apple Notes через CLI `memo`: создавай, ищи, редактируй.

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Apple Notes

Используй `memo` для управления Apple Notes напрямую из терминала. Заметки синхронизируются между всеми устройствами Apple через iCloud.

## Предварительные требования

- **macOS** с приложением Notes.app
- Установить: `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Предоставь доступ автоматизации приложению Notes.app, когда будет запрошено (System Settings → Privacy → Automation)

## Когда использовать

- Пользователь просит создать, просмотреть или найти заметку в Apple Notes
- Сохранение информации в Notes.app для доступа с разных устройств
- Организация заметок по папкам
- Экспорт заметок в Markdown/HTML

## Когда НЕ использовать

- Управление хранилищем Obsidian → используй навык `obsidian`
- Bear Notes → отдельное приложение (не поддерживается)
- Быстрые заметки только для агента → используй `memory` tool

## Быстрая справка

### Просмотр заметок

```bash
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)
```

### Создание заметок

```bash
memo notes -a                     # Interactive editor
memo notes -a "Note Title"        # Quick add with title
```

### Редактирование заметок

```bash
memo notes -e                     # Interactive selection to edit
```

### Удаление заметок

```bash
memo notes -d                     # Interactive selection to delete
```

### Перемещение заметок

```bash
memo notes -m                     # Move note to folder (interactive)
```

### Экспорт заметок

```bash
memo notes -ex                    # Export to HTML/Markdown
```

## Ограничения

- Невозможно редактировать заметки, содержащие изображения или вложения
- Интерактивные подсказки требуют доступа к терминалу (при необходимости используйте `pty=true`)
- Только macOS — требуется приложение Notes.app

## Правила

1. Предпочитай Apple Notes, когда пользователь хочет синхронизацию между устройствами (iPhone/iPad/Mac).
2. Используй `memory` tool для внутренних заметок агента, которым не нужна синхронизация.
3. Используй навык `obsidian` для управления знаниями в формате Markdown.