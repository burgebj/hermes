---
title: "Notion — Notion API + ntn CLI: страницы, базы данных, markdown, Workers"
sidebar_label: "Notion"
description: "Notion API + ntn CLI: страницы, базы данных, markdown, Workers"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Notion

Notion API + ntn CLI: страницы, базы данных, markdown, Workers.
## Метаданные навыка

| | |
|---|---|
| Source | Встроенный (устанавливается по умолчанию) |
| Path | `skills/productivity/notion` |
| Version | `2.0.0` |
| Author | сообщество |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Notion`, `Productivity`, `Notes`, `Database`, `API`, `CLI`, `Workers` |
:::info
Следующее — полное определение **skill**, которое Hermes загружает при срабатывании этого **skill**. Это то, что агент видит как инструкции, когда **skill** активен.
:::

# Notion

Общайся с Notion двумя способами. Один и тот же токен интеграции работает для обоих — выбирай, что доступно.

◆ **`ntn` CLI** — официальное CLI Notion. Краткий синтаксис, загрузка файлов в одну строку, требуется для Workers. Только macOS + Linux (по состоянию на май 2026); поддержка Windows «скоро». **По умолчанию, если установлен.**
◆ **HTTP + curl** — работает везде, включая Windows. **Запасной вариант по умолчанию**, когда `ntn` не установлен.
## Настройка

### 1. Получить токен интеграции (обязательно для обоих путей)

1. Создай интеграцию на https://notion.so/my-integrations
2. Скопируй API‑ключ (начинается с `ntn_` или `secret_`)
3. Сохрани в `~/.hermes/.env`:
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```
4. **Поделись целевыми страницами/базами данных с интеграцией** в Notion: меню страницы `...` → `Connect to` → имя твоей интеграции. Без этого API вернёт 404 для этой страницы, даже если она существует.

### 2. Установить `ntn` (рекомендованный путь для macOS / Linux)

```bash
# Recommended
curl -fsSL https://ntn.dev | bash

# Or via npm (needs Node 22+, npm 10+)
npm install --global ntn

ntn --version    # verify
```

**Пропусти `ntn login` — используй токен интеграции вместо него.** Это работает в безголовом режиме, браузер не нужен:
```bash
export NOTION_API_TOKEN=$NOTION_API_KEY      # ntn reads NOTION_API_TOKEN
export NOTION_KEYRING=0                       # don't try to use the OS keychain
```

Добавь эти экспорты в профиль оболочки (или в `~/.hermes/.env`), чтобы каждая сессия их наследовала.

### 3. Выбери путь во время выполнения

```bash
if command -v ntn >/dev/null 2>&1; then
  # use ntn
else
  # fall back to curl
fi
```

Пользователи Windows: полностью пропусти шаг 2, пока не появится нативный `ntn` — путь B работает без проблем. Если сейчас нужен удобный CLI, установи `ntn` внутри WSL2.
## Основы API

`Notion-Version: 2025-09-03` обязательно указывается во всех HTTP‑запросах. `ntn` делает это за тебя. В этой версии то, что пользователи называют «базы данных», в API называется **источниками данных**.
## Path A — `ntn` CLI (preferred, macOS / Linux)

### Raw API calls (shorthand for curl)
```bash
ntn api v1/users                                  # GET
ntn api v1/pages parent[page_id]=abc123 \         # POST with inline body
  properties[title][0][text][content]="Notes"
ntn api v1/pages/abc123 -X PATCH archived:=true   # PATCH; := is non-string (bool/num/null)
```

Примечания к синтаксису:
- `key=value` — строковые поля
- `key[nested]=value` — поля вложенного объекта
- `key:=value` — типизированное присваивание (булевы, числа, null, массивы)

### Search
```bash
ntn api v1/search query="page title"
```

### Read page metadata
```bash
ntn api v1/pages/{page_id}
```

### Read page as Markdown (agent-friendly)
```bash
ntn api v1/pages/{page_id}/markdown
```

### Read page content as blocks
```bash
ntn api v1/blocks/{page_id}/children
```

### Create page from Markdown
```bash
ntn api v1/pages \
  parent[page_id]=xxx \
  properties[title][0][text][content]="Notes from meeting" \
  markdown="# Agenda

- Q3 roadmap
- Hiring"
```

### Patch a page with Markdown
```bash
ntn api v1/pages/{page_id}/markdown -X PATCH \
  markdown="## Update

Shipped the prototype."
```

### Query a database (data source)
```bash
ntn api v1/data_sources/{data_source_id}/query -X POST \
  filter[property]=Status filter[select][equals]=Active
```

Для сложных запросов с `sorts`, несколькими условиями фильтрации или составной логикой передавай JSON через конвейер:
```bash
echo '{"filter": {"property": "Status", "select": {"equals": "Active"}}, "sorts": [{"property": "Date", "direction": "descending"}]}' | \
  ntn api v1/data_sources/{data_source_id}/query -X POST --json -
```

### File uploads (one-liner — biggest CLI win)
```bash
ntn files create < photo.png
ntn files create --external-url https://example.com/photo.png
ntn files list
```

Сравни с 3‑шаговым HTTP‑потоком (create upload → PUT bytes → reference).

### Useful env vars
| Var | Effect |
|---|---|
| `NOTION_API_TOKEN` | Токен аутентификации (перезаписывает keychain) — укажи токен своей интеграции |
| `NOTION_KEYRING=0` | Учётные данные в файле `~/.config/notion/auth.json` вместо системного keychain |
| `NOTION_WORKSPACE_ID` | Пропустить запрос выбора рабочего пространства |
## Path B — HTTP + curl (кроссплатформенный, по умолчанию в Windows)

Все запросы следуют этой схеме:

```bash
curl -s -X GET "https://api.notion.com/v1/..." \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json"
```

В Windows `curl`, поставляемый с Windows 10+, работает как есть. Пользователи PowerShell также могут использовать `Invoke-RestMethod`.

### Поиск
```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"query": "page title"}'
```

### Чтение метаданных страницы
```bash
curl -s "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Чтение страницы в формате Markdown (удобно для агента)

Проще передать модели, чем JSON‑блок.

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Чтение содержимого страницы в виде блоков (когда нужна структура)
```bash
curl -s "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Создание страницы из Markdown

`POST /v1/pages` принимает параметр тела `markdown`.

```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "properties": {"title": [{"text": {"content": "Notes from meeting"}}]},
    "markdown": "# Agenda\n\n- Q3 roadmap\n- Hiring\n\n## Decisions\n- Ship MVP Friday"
  }'
```

### Обновление страницы с помощью Markdown
```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"markdown": "## Update\n\nShipped the prototype."}'
```

### Создание страницы в базе данных (типизированные свойства)
```bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "xxx"},
    "properties": {
      "Name": {"title": [{"text": {"content": "New Item"}}]},
      "Status": {"select": {"name": "Todo"}}
    }
  }'
```

### Запрос к базе данных (источник данных)
```bash
curl -s -X POST "https://api.notion.com/v1/data_sources/{data_source_id}/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {"property": "Status", "select": {"equals": "Active"}},
    "sorts": [{"property": "Date", "direction": "descending"}]
  }'
```

### Создание базы данных
```bash
curl -s -X POST "https://api.notion.com/v1/data_sources" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"page_id": "xxx"},
    "title": [{"text": {"content": "My Database"}}],
    "properties": {
      "Name": {"title": {}},
      "Status": {"select": {"options": [{"name": "Todo"}, {"name": "Done"}]}},
      "Date": {"date": {}}
    }
  }'
```

### Обновление свойств страницы
```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"Status": {"select": {"name": "Done"}}}}'
```

### Добавление блоков к странице
```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{
    "children": [
      {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Hello from Hermes!"}}]}}
    ]
  }'
```

### Загрузка файлов (трёхшаговый процесс)
```bash
# 1. Create upload
curl -s -X POST "https://api.notion.com/v1/file_uploads" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"filename": "photo.png", "content_type": "image/png"}'

# 2. PUT bytes to the upload_url returned above
curl -s -X PUT "{upload_url}" --data-binary @photo.png

# 3. Reference {file_upload_id} in a page/block payload
```
## Типы свойств

Общие форматы свойств элементов базы данных:

- **Title:** `{"title": [{"text": {"content": "..."}}]}`
- **Rich text:** `{"rich_text": [{"text": {"content": "..."}}]}`
- **Select:** `{"select": {"name": "Option"}}`
- **Multi-select:** `{"multi_select": [{"name": "A"}, {"name": "B"}]}`
- **Date:** `{"date": {"start": "2026-01-15", "end": "2026-01-16"}}`
- **Checkbox:** `{"checkbox": true}`
- **Number:** `{"number": 42}`
- **URL:** `{"url": "https://..."}`
- **Email:** `{"email": "user@example.com"}`
- **Relation:** `{"relation": [{"id": "page_id"}]}`
## Версия API 2025‑09‑03 — Базы данных vs Источники данных

- **Базы данных стали источниками данных.** Используй эндпоинты `/data_sources/` для запросов и получения данных.
- **Два идентификатора для каждой базы данных:** `database_id` и `data_source_id`.
  - `database_id` — при создании страниц: `parent: {"database_id": "..."}`
  - `data_source_id` — при выполнении запросов: `POST /v1/data_sources/{id}/query`
- Поиск возвращает базы данных как `"object": "data_source"` с полем `data_source_id`.
## Workers Notion (advanced, requires `ntn`)

Workers — это программы на TypeScript, которые Notion размещает для тебя. Один Worker может предоставлять любую комбинацию:
- **Syncs** — вытягивание данных из внешних API в базу данных Notion по расписанию (по умолчанию каждые 30 минут).
- **Tools** — появляются как вызываемые инструменты внутри Custom Agents Notion.
- **Webhooks** — получают HTTP‑события от внешних сервисов (GitHub, Stripe и др.) и действуют в Notion.

**Ограничения по плану / платформе:**
- CLI работает на всех планах. **Развёртывание Workers требует Business или Enterprise.**
- `ntn` доступен только на macOS/Linux по состоянию на май 2026. Пользователям Windows нужен WSL2 или им придётся ждать нативной поддержки.
- Бесплатно до 11 августа 2026; далее — по кредитам Notion.

### Минимальный Worker

```bash
ntn workers new my-worker      # scaffold
cd my-worker
# Edit src/index.ts
ntn workers deploy --name my-worker
```

`src/index.ts`:
```typescript
import { Worker } from "@notionhq/workers";

const worker = new Worker();
export default worker;

worker.tool("greet", {
  title: "Greet a User",
  description: "Returns a friendly greeting",
  inputSchema: { type: "object", properties: { name: { type: "string" } }, required: ["name"] },
  execute: async ({ name }) => `Hello, ${name}!`,
});
```

### Возможности Webhook

```typescript
worker.webhook("onGithubPush", {
  title: "GitHub Push Handler",
  execute: async (events, { notion }) => {
    for (const event of events) {
      // event.body, event.rawBody (for signature verification), event.headers
      console.log("got delivery", event.deliveryId);
    }
  },
});
```

После развёртывания: `ntn workers webhooks list` показывает URL, который генерирует Notion. Относись к этому URL как к секрету — любой, у кого он есть, может отправлять POST‑запросы, если ты не добавишь проверку подписи.

### Команды жизненного цикла Worker

```bash
ntn workers deploy
ntn workers list
ntn workers exec <capability-key> -d '{"name": "world"}'
ntn workers sync trigger <key>            # run a sync now
ntn workers sync pause <key>
ntn workers env set GITHUB_WEBHOOK_SECRET=...
ntn workers runs list                     # recent invocations
ntn workers runs logs <run-id>
ntn workers webhooks list
```

Когда нужно собрать Worker, создай шаблон с помощью `ntn workers new`, напиши код в `src/index.ts`, установи любые секреты через `ntn workers env set` и разверни его. Документация Notion доступна по адресу https://developers.notion.com/workers и охватывает весь набор API.
## Notion‑Flavored Markdown (используется в эндпоинтах `/markdown`)

Стандартный CommonMark плюс XML‑подобные теги для блоков, специфичных для Notion. Для отступов используй **табуляцию**.

**Блоки, выходящие за пределы CommonMark:**
```
<callout icon="🎯" color="blue_bg">
	Ship the MVP by **Friday**.
</callout>

<details color="gray">
<summary>Toggle title</summary>
	Children indented one tab
</details>

<columns>
	<column>Left side</column>
	<column>Right side</column>
</columns>

<table_of_contents color="gray"/>
```

**Inline:**
- Упоминания: `<mention-user url="..."/>`, `<mention-page url="...">Title</mention-page>`, `<mention-date start="2026-05-15"/>`
- Подчёркивание: `<span underline="true">text</span>`
- Цвет: `<span color="blue">text</span>` или на уровне блока `{color="blue"}` в первой строке
- Математика: inline `$x^2$`, block `$$ ... $$`
- Цитирования: `[^https://example.com]`

**Цвета:** `gray brown orange yellow green blue purple pink red`, плюс варианты `*_bg` для фона.

Заголовки уровней 5/6 сворачиваются в H4. Несколько строк, начинающихся с `>`, отображаются как отдельные блоки цитат — для многострочных цитат используй `<br>` внутри одного `>`.
## Выбор правильного пути

| Задача | mac / Linux | Windows |
|---|---|---|
| Чтение/запись страниц, поиск, запросы к базам данных | `ntn api ...` | curl |
| Прочитать страницу, чтобы агент её суммировал | `ntn api v1/pages/{id}/markdown` | curl `/markdown` endpoint |
| Загрузить файл | `ntn files create < file` | 3‑шаговый HTTP‑поток |
| Разовый запрос к API | `ntn api ...` | curl |
| Создать синхронизацию / webhook / инструмент агента, размещённый в Notion | `ntn workers ...` | WSL2 + `ntn workers ...` |
## Примечания

- Идентификаторы страниц/баз данных — это UUID (с дефисами или без — оба варианта принимаются).
- Ограничение скорости: ~3 запроса/секунду в среднем. CLI не обходят это ограничение.
- API не может задавать фильтры **view** (представления) базы данных — это только в UI.
- Используй `"is_inline": true` при создании источников данных, чтобы встроить их в страницу.
- Всегда передавай `-s` в `curl`, чтобы подавлять индикаторы прогресса (чистый вывод агента).
- Пропускай JSON через `jq` при чтении: `... | jq '.results[0].properties'`.
- Notion теперь поставляется с сервером MCP (`Notion MCP`, ~91 % более эффективным по токенам при операциях с БД, чем предыдущая версия) — подключи его через поддержку MCP Hermes, если нужен потоковый доступ к Notion изнутри сессии, но указанных выше путей достаточно для большинства одноразовых задач.