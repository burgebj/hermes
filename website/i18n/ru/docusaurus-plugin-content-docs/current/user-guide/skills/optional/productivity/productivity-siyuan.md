---
title: "Siyuan"
sidebar_label: "Siyuan"
description: "SiYuan Note API для поиска, чтения, создания и управления блоками и документами в самохостовой базе знаний через curl"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Siyuan

SiYuan Note API для поиска, чтения, создания и управления блоками и документами в самохостовой базе знаний через `curl`.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/productivity/siyuan` |
| Path | `optional-skills/productivity/siyuan` |
| Version | `1.0.0` |
| Author | FEUAZUR |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `SiYuan`, `Notes`, `Knowledge Base`, `PKM`, `API` |
| Related skills | [`obsidian`](/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian), [`notion`](/docs/user-guide/skills/bundled/productivity/productivity-notion) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при работе навыка.
:::

# SiYuan Note API

Используй API ядра [SiYuan](https://github.com/siyuan-note/siyuan) через `curl` для поиска, чтения, создания, обновления и удаления блоков и документов в самохостовой базе знаний. Никаких дополнительных инструментов не требуется — только `curl` и токен API.

## Предварительные требования

1. Установи и запусти SiYuan (десктоп или Docker)
2. Получи токен API: **Settings > About > API token**
3. Сохрани его в `~/.hermes/.env`:
   ```
   SIYUAN_TOKEN=your_token_here
   SIYUAN_URL=http://127.0.0.1:6806
   ```
   `SIYUAN_URL` по умолчанию `http://127.0.0.1:6806`, если не задан.

## Основы API

Все вызовы SiYuan API — **POST с JSON‑тело**. Каждый запрос следует этому шаблону:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/..." \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
```

Ответы — JSON со следующей структурой:

```json
{"code": 0, "msg": "", "data": { ... }}
```

`code: 0` означает успех. Любое другое значение — ошибка, смотри `msg` для деталей.

**Формат ID:** SiYuan ID выглядят как `20210808180117-6v0mkxr` (14‑значная метка времени + 7 буквенно‑цифровых символов).

## Быстрая справка

| Операция | Endpoint |
|-----------|----------|
| Полнотекстовый поиск | `/api/search/fullTextSearchBlock` |
| SQL‑запрос | `/api/query/sql` |
| Чтение блока | `/api/block/getBlockKramdown` |
| Чтение дочерних блоков | `/api/block/getChildBlocks` |
| Получить путь | `/api/filetree/getHPathByID` |
| Получить атрибуты | `/api/attr/getBlockAttrs` |
| Список ноутбуков | `/api/notebook/lsNotebooks` |
| Список документов | `/api/filetree/listDocsByPath` |
| Создать ноутбук | `/api/notebook/createNotebook` |
| Создать документ | `/api/filetree/createDocWithMd` |
| Добавить блок | `/api/block/appendBlock` |
| Обновить блок | `/api/block/updateBlock` |
| Переименовать документ | `/api/filetree/renameDocByID` |
| Установить атрибуты | `/api/attr/setBlockAttrs` |
| Удалить блок | `/api/block/deleteBlock` |
| Удалить документ | `/api/filetree/removeDocByID` |
| Экспортировать как Markdown | `/api/export/exportMdContent` |

## Часто используемые операции

### Поиск (полнотекстовый)

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/search/fullTextSearchBlock" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "meeting notes", "page": 0}' | jq '.data.blocks[:5]'
```

### Поиск (SQL)

Запроси базу блоков напрямую. Безопасны только `SELECT`‑запросы.

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/query/sql" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"stmt": "SELECT id, content, type, box FROM blocks WHERE content LIKE '\''%keyword%'\'' AND type='\''p'\'' LIMIT 20"}' | jq '.data'
```

Полезные столбцы: `id`, `parent_id`, `root_id`, `box` (ID ноутбука), `path`, `content`, `type`, `subtype`, `created`, `updated`.

### Чтение содержимого блока

Возвращает содержимое блока в формате Kramdown (похожем на Markdown).

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/getBlockKramdown" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data.kramdown'
```

### Чтение дочерних блоков

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/getChildBlocks" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data'
```

### Получить человекочитаемый путь

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/getHPathByID" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data'
```

### Получить атрибуты блока

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/attr/getBlockAttrs" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data'
```

### Список ноутбуков

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/notebook/lsNotebooks" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.data.notebooks[] | {id, name, closed}'
```

### Список документов в ноутбуке

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/listDocsByPath" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notebook": "NOTEBOOK_ID", "path": "/"}' | jq '.data.files[] | {id, name}'
```

### Создать документ

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/createDocWithMd" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notebook": "NOTEBOOK_ID",
    "path": "/Meeting Notes/2026-03-22",
    "markdown": "# Meeting Notes\n\n- Discussed project timeline\n- Assigned tasks"
  }' | jq '.data'
```

### Создать ноутбук

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/notebook/createNotebook" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My New Notebook"}' | jq '.data.notebook.id'
```

### Добавить блок в документ

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/appendBlock" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "parentID": "DOCUMENT_OR_BLOCK_ID",
    "data": "New paragraph added at the end.",
    "dataType": "markdown"
  }' | jq '.data'
```

Также доступны: `/api/block/prependBlock` (те же параметры, вставка в начало) и `/api/block/insertBlock` (использует `previousID` вместо `parentID` для вставки после конкретного блока).

### Обновить содержимое блока

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/updateBlock" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "BLOCK_ID",
    "data": "Updated content here.",
    "dataType": "markdown"
  }' | jq '.data'
```

### Переименовать документ

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/renameDocByID" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "DOCUMENT_ID", "title": "New Title"}'
```

### Установить атрибуты блока

Пользовательские атрибуты должны начинаться с `custom-`:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/attr/setBlockAttrs" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "BLOCK_ID",
    "attrs": {
      "custom-status": "reviewed",
      "custom-priority": "high"
    }
  }'
```

### Удалить блок

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/deleteBlock" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "BLOCK_ID"}'
```

Чтобы удалить весь документ, используй `/api/filetree/removeDocByID` с `{"id": "DOC_ID"}`.
Чтобы удалить ноутбук, используй `/api/notebook/removeNotebook` с `{"notebook": "NOTEBOOK_ID"}`.

### Экспортировать документ как Markdown

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/export/exportMdContent" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "DOCUMENT_ID"}' | jq -r '.data.content'
```

## Типы блоков

Распространённые значения `type` в SQL‑запросах:

| Тип | Описание |
|------|----------|
| `d` | Документ (корневой блок) |
| `p` | Параграф |
| `h` | Заголовок |
| `l` | Список |
| `i` | Элемент списка |
| `c` | Блок кода |
| `m` | Математический блок |
| `t` | Таблица |
| `b` | Цитата |
| `s` | Суперблок |
| `html` | HTML‑блок |

## Подводные камни

- **Все endpoint — POST** — даже операции только для чтения. Не используй GET.
- **Безопасность SQL**: используй только SELECT‑запросы. INSERT/UPDATE/DELETE/DROP опасны и никогда не должны отправляться.
- **Валидация ID**: ID должны соответствовать шаблону `YYYYMMDDHHmmss-xxxxxxx`. Отклоняй всё остальное.
- **Ответы с ошибками**: всегда проверяй `code != 0` в ответах перед обработкой `data`.
- **Большие документы**: содержимое блоков и результаты экспорта могут быть очень большими. Используй `LIMIT` в SQL и передавай через `jq`, чтобы извлечь только нужное.
- **ID ноутбуков**: при работе с конкретным ноутбуком сначала получи его ID через `lsNotebooks`.

## Альтернатива: MCP‑сервер

Если предпочитаешь нативную интеграцию вместо `curl`, установи SiYuan MCP‑сервер:

```yaml
# In ~/.hermes/config.yaml under mcp_servers:
mcp_servers:
  siyuan:
    command: npx
    args: ["-y", "@porkll/siyuan-mcp"]
    env:
      SIYUAN_TOKEN: "your_token"
      SIYUAN_URL: "http://127.0.0.1:6806"
```