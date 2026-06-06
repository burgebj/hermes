---
title: "Siyuan"
sidebar_label: "Siyuan"
description: "API SiYuan Note для пошуку, читання, створення та керування блоками й документами в самостійно розгорнутій базі знань за допомогою curl"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# SiYuan

SiYuan Note API для пошуку, читання, створення та керування блоками і документами в самохостованій базі знань за допомогою curl.

## Метадані навички

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

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# SiYuan Note API

Використовуй [SiYuan](https://github.com/siyuan-note/siyuan) kernel API через curl для пошуку, читання, створення, оновлення та видалення блоків і документів у самохостованій базі знань. Додаткові інструменти не потрібні — лише curl і токен API.

## Передумови

1. Встанови та запусти SiYuan (десктоп або Docker)
2. Отримай свій токен API: **Settings > About > API token**
3. Збережи його у `~/.hermes/.env`:
   ```
   SIYUAN_TOKEN=your_token_here
   SIYUAN_URL=http://127.0.0.1:6806
   ```
   `SIYUAN_URL` за замовчуванням `http://127.0.0.1:6806`, якщо не вказано.

## Основи API

Усі виклики SiYuan API — **POST з JSON‑тілом**. Кожен запит слідує цьому шаблону:

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/..." \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
```

Відповіді — JSON зі структурою:

```json
{"code": 0, "msg": "", "data": { ... }}
```
`code: 0` означає успіх. Будь‑яке інше значення — помилка, дивись `msg` для деталей.

**Формат ID:** SiYuan ID виглядає як `20210808180117-6v0mkxr` (14‑цифровий timestamp + 7 алфавітно‑цифрових символів).

## Швидка довідка

| Операція | Endpoint |
|-----------|----------|
| Повнотекстовий пошук | `/api/search/fullTextSearchBlock` |
| SQL‑запит | `/api/query/sql` |
| Читання блоку | `/api/block/getBlockKramdown` |
| Читання дочірніх блоків | `/api/block/getChildBlocks` |
| Отримати шлях | `/api/filetree/getHPathByID` |
| Отримати атрибути | `/api/attr/getBlockAttrs` |
| Список ноутбуків | `/api/notebook/lsNotebooks` |
| Список документів | `/api/filetree/listDocsByPath` |
| Створити ноутбук | `/api/notebook/createNotebook` |
| Створити документ | `/api/filetree/createDocWithMd` |
| Додати блок | `/api/block/appendBlock` |
| Оновити блок | `/api/block/updateBlock` |
| Перейменувати документ | `/api/filetree/renameDocByID` |
| Встановити атрибути | `/api/attr/setBlockAttrs` |
| Видалити блок | `/api/block/deleteBlock` |
| Видалити документ | `/api/filetree/removeDocByID` |
| Експортувати як Markdown | `/api/export/exportMdContent` |

## Типові операції

### Пошук (повнотекстовий)

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/search/fullTextSearchBlock" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "meeting notes", "page": 0}' | jq '.data.blocks[:5]'
```

### Пошук (SQL)

Запитуй базу блоків безпосередньо. Безпечно лише SELECT‑запити.

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/query/sql" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"stmt": "SELECT id, content, type, box FROM blocks WHERE content LIKE '\''%keyword%'\'' AND type='\''p'\'' LIMIT 20"}' | jq '.data'
```

Корисні колонки: `id`, `parent_id`, `root_id`, `box` (ID ноутбука), `path`, `content`, `type`, `subtype`, `created`, `updated`.

### Читання вмісту блоку

Повертає вміст блоку у форматі Kramdown (подібному до Markdown).

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/getBlockKramdown" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data.kramdown'
```

### Читання дочірніх блоків

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/getChildBlocks" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data'
```

### Отримання людськочитабельного шляху

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/getHPathByID" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data'
```

### Отримання атрибутів блоку

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/attr/getBlockAttrs" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "20210808180117-6v0mkxr"}' | jq '.data'
```

### Список ноутбуків

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/notebook/lsNotebooks" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.data.notebooks[] | {id, name, closed}'
```

### Список документів у ноутбуку

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/listDocsByPath" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notebook": "NOTEBOOK_ID", "path": "/"}' | jq '.data.files[] | {id, name}'
```

### Створення документа

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

### Створення ноутбука

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/notebook/createNotebook" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My New Notebook"}' | jq '.data.notebook.id'
```

### Додавання блоку до документа

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

Також доступно: `/api/block/prependBlock` (ті ж параметри, вставка на початок) та `/api/block/insertBlock` (використовує `previousID` замість `parentID` для вставки після конкретного блоку).

### Оновлення вмісту блоку

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

### Перейменування документа

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/filetree/renameDocByID" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "DOCUMENT_ID", "title": "New Title"}'
```

### Встановлення атрибутів блоку

Користувацькі атрибути мають мати префікс `custom-`:

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

### Видалення блоку

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/block/deleteBlock" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "BLOCK_ID"}'
```

Для видалення цілого документа: використай `/api/filetree/removeDocByID` з `{"id": "DOC_ID"}`.
Для видалення ноутбука: використай `/api/notebook/removeNotebook` з `{"notebook": "NOTEBOOK_ID"}`.

### Експорт документа як Markdown

```bash
curl -s -X POST "${SIYUAN_URL:-http://127.0.0.1:6806}/api/export/exportMdContent" \
  -H "Authorization: Token $SIYUAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "DOCUMENT_ID"}' | jq -r '.data.content'
```

## Типи блоків

Типові значення `type` у SQL‑запитах:

| Тип | Опис |
|------|-------------|
| `d` | Document (кореневий блок) |
| `p` | Paragraph |
| `h` | Heading |
| `l` | List |
| `i` | List item |
| `c` | Code block |
| `m` | Math block |
| `t` | Table |
| `b` | Blockquote |
| `s` | Super block |
| `html` | HTML block |

## Підводні камені

- **Усі endpoint'и POST** — навіть операції лише для читання. Не використовуйте GET.
- **SQL‑безпека**: використовуйте лише SELECT‑запити. INSERT/UPDATE/DELETE/DROP небезпечні і їх не слід надсилати.
- **Валідація ID**: ID мають відповідати шаблону `YYYYMMDDHHmmss-xxxxxxx`. Відхиляйте все інше.
- **Помилкові відповіді**: завжди перевіряйте `code != 0` у відповідях перед обробкою `data`.
- **Великі документи**: вміст блоків і результати експорту можуть бути дуже великими. Використовуйте `LIMIT` у SQL і передавайте через `jq`, щоб отримати лише потрібне.
- **ID ноутбуків**: коли працюєте з конкретним ноутбуком, спочатку отримайте його ID через `lsNotebooks`.

## Альтернатива: MCP Server

Якщо ти віддаєш перевагу нативній інтеграції замість curl, встанови SiYuan MCP server:

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