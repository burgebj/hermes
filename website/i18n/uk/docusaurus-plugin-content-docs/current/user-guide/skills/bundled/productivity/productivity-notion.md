---
title: "Notion — Notion API + ntn CLI: сторінки, бази даних, markdown, Workers"
sidebar_label: "Notion"
description: "Notion API + ntn CLI: сторінки, бази даних, markdown, Workers"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Notion

Notion API + ntn CLI: сторінки, бази даних, markdown, Workers.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/productivity/notion` |
| Версія | `2.0.0` |
| Автор | community |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `Notion`, `Productivity`, `Notes`, `Database`, `API`, `CLI`, `Workers` |
:::info
Наступне — повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# Notion

Спілкуйся з Notion двома способами. Той самий токен інтеграції працює для обох — вибирай, що доступно.

◆ **`ntn` CLI** — офіційний CLI Notion. Коротший синтаксис, одно‑рядкові завантаження файлів, потрібен для Workers. лише macOS + Linux станом на травень 2026 (підтримка Windows «незабаром»). **За замовчуванням, якщо встановлено.**
◆ **HTTP + curl** — працює скрізь, включаючи Windows. **Запасний (варіант) за замовчуванням**, коли `ntn` не встановлено.
## Налаштування

### 1. Отримай токен інтеграції (обов’язково для обох шляхів)

1. Створи інтеграцію за адресою https://notion.so/my-integrations
2. Скопіюй API‑ключ (починається з `ntn_` або `secret_`)
3. Збережи у `~/.hermes/.env`:
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```
4. **Поділи цільові сторінки/бази даних з інтеграцією** у Notion: меню сторінки `...` → `Connect to` → назва твоєї інтеграції. Без цього API поверне 404 для цієї сторінки, навіть якщо вона існує.

### 2. Встанови `ntn` (рекомендований шлях на macOS / Linux)

```bash
# Recommended
curl -fsSL https://ntn.dev | bash

# Or via npm (needs Node 22+, npm 10+)
npm install --global ntn

ntn --version    # verify
```

**Пропусти `ntn login` — використай токен інтеграції замість нього.** Це працює без графічного інтерфейсу, браузер не потрібен:
```bash
export NOTION_API_TOKEN=$NOTION_API_KEY      # ntn reads NOTION_API_TOKEN
export NOTION_KEYRING=0                       # don't try to use the OS keychain
```

Додай ці експорти до профілю оболонки (або до `~/.hermes/.env`), щоб кожна сесія їх успадковувала.

### 3. Вибери шлях під час виконання

```bash
if command -v ntn >/dev/null 2>&1; then
  # use ntn
else
  # fall back to curl
fi
```

Користувачі Windows: пропусти крок 2 повністю, доки не з’явиться нативний `ntn` — шлях B працює без проблем. Якщо хочеш зручність CLI вже зараз, встанови `ntn` всередині WSL2.
## Основи API

`Notion-Version: 2025-09-03` є обов’язковим у всіх HTTP‑запитах. `ntn` робить це за тебе. У цій версії те, що користувачі називають «databases», у API називаються **data sources**.
## Path A — `ntn` CLI (preferred, macOS / Linux)

### Raw API calls (shorthand for curl)
```bash
ntn api v1/users                                  # GET
ntn api v1/pages parent[page_id]=abc123 \         # POST with inline body
  properties[title][0][text][content]="Notes"
ntn api v1/pages/abc123 -X PATCH archived:=true   # PATCH; := is non-string (bool/num/null)
```

Нотатки щодо синтаксису:
- `key=value` — рядкові поля
- `key[nested]=value` — поля вкладеного об’єкта
- `key:=value` — типізоване присвоєння (булеві, числа, null, масиви)

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

Для складних запитів із `sorts`, кількома умовами фільтрації або складною логікою передай JSON через конвеєр:
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

Порівняй з 3‑кроковим HTTP‑потоком (створити завантаження → PUT байти → посилання).

### Useful env vars
| Var | Effect |
|---|---|
| `NOTION_API_TOKEN` | Токен автентифікації (перезаписує keychain) — встанови його як токен інтеграції |
| `NOTION_KEYRING=0` | Файлові облікові дані у `~/.config/notion/auth.json` замість OS keychain |
| `NOTION_WORKSPACE_ID` | Пропусти запит вибору робочого простору |
## Path B — HTTP + curl (cross‑platform, default on Windows)

All requests share this pattern:

```bash
curl -s -X GET "https://api.notion.com/v1/..." \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json"
```

On Windows the `curl` shipped with Windows 10+ works **as‑is**. PowerShell users can also use `Invoke‑RestMethod`.

### Пошук
```bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"query": "page title"}'
```

### Читання метаданих сторінки
```bash
curl -s "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Читання сторінки у форматі Markdown (дружньо до агента)

Легше передати моделі, ніж блок JSON.

```bash
curl -s "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Читання вмісту сторінки як блоків (коли потрібна структура)
```bash
curl -s "https://api.notion.com/v1/blocks/{page_id}/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03"
```

### Створення сторінки з Markdown

`POST /v1/pages` accepts a `markdown` body param.

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

### Патч сторінки за допомогою Markdown
```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}/markdown" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"markdown": "## Update\n\nShipped the prototype."}'
```

### Створення сторінки в базі даних (властивості типу)
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

### Запит до бази даних (джерело даних)
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

### Створення бази даних
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

### Оновлення властивостей сторінки
```bash
curl -s -X PATCH "https://api.notion.com/v1/pages/{page_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"Status": {"select": {"name": "Done"}}}}'
```

### Додавання блоків до сторінки
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

### Завантаження файлів (трьохкроковий процес)
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
## Типи властивостей

Загальні формати властивостей для елементів бази даних:

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
## API Version 2025-09-03 — Databases vs Data Sources

- **Бази даних стали data sources.** Використовуй кінцеві точки `/data_sources/` для запитів та отримання даних.
- **Два ID для кожної бази даних:** `database_id` і `data_source_id`.
  - `database_id` при створенні сторінок: `parent: {"database_id": "..."}`
  - `data_source_id` при запиті: `POST /v1/data_sources/{id}/query`
- Пошук повертає бази даних як `"object": "data_source"` з полем `data_source_id`.
## Notion Workers (advanced, requires `ntn`)

Workers — це програми TypeScript, які Notion хостить для тебе. Один worker може надавати будь‑яку комбінацію:
- **Syncs** — отримувати дані з зовнішніх API у базу даних Notion за розкладом (за замовчуванням 30 хв).
- **Tools** — з’являються як викликаємі інструменти всередині Custom Agents у Notion.
- **Webhooks** — отримувати HTTP‑події від зовнішніх сервісів (GitHub, Stripe тощо) та виконувати дії в Notion.

**Plan / platform gating:**
- CLI працює на всіх планах. **Розгортання Workers вимагає Business або Enterprise.**
- `ntn` доступний лише на macOS/Linux станом на травень 2026. Користувачі Windows потребують WSL2 або повинні чекати нативної підтримки.
- Безкоштовно до 11 серпня 2026; після цього використання обліковується у Notion credits.

### Minimal Worker

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

### Webhook capability

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

Після розгортання: `ntn workers webhooks list` показує URL, який генерує Notion. Считай цей URL секретом — будь‑хто, хто його має, може надсилати POST‑події, якщо ти не додасте перевірку підпису.

### Worker lifecycle commands

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

Коли потрібно створити Worker, ініціалізуй його за допомогою `ntn workers new`, напиши код у `src/index.ts`, встанови будь‑які секрети командою `ntn workers env set` і розгорни. Документація Notion за адресою https://developers.notion.com/workers охоплює весь API.
## Notion‑Flavored Markdown (використовується в `/markdown` endpoint'ах)

Стандартний CommonMark плюс XML‑подібні теги для блоків, специфічних для Notion. Використовуй **табуляції** для відступів.

**Блоки, що виходять за межі CommonMark:**
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
- Згадки: `<mention-user url="..."/>`, `<mention-page url="...">Title</mention-page>`, `<mention-date start="2026-05-15"/>`
- Підкреслення: `<span underline="true">text</span>`
- Колір: `<span color="blue">text</span>` або на рівні блоку `{color="blue"}` у першому рядку
- Математика: inline `$x^2$`, block `$$ ... $$`
- Цитати: `[^https://example.com]`

**Кольори:** `gray brown orange yellow green blue purple pink red`, плюс варіанти `*_bg` для фонів.

Заголовки 5/6 згортаються до H4. Кілька рядків, що починаються з `>`, відображаються як окремі блоки цитат — використай `<br>` всередині одного `>` для багаторядкових цитат.
## Вибір правильного шляху

| Завдання | mac / Linux | Windows |
|---|---|---|
| Читати/записувати сторінки, шукати, запитувати бази даних | `ntn api ...` | curl |
| Прочитати сторінку, щоб агент підсумував | `ntn api v1/pages/{id}/markdown` | curl `/markdown` endpoint |
| Завантажити файл | `ntn files create < file` | 3‑step HTTP flow |
| Одноразове дослідження API | `ntn api ...` | curl |
| Створити інструмент синхронізації / webhook / агент, розміщений у Notion | `ntn workers ...` | WSL2 + `ntn workers ...` |
## Примітки

- Ідентифікатори сторінок/баз даних — це UUID (з дефісами або без — обидва варіанти приймаються).
- Обмеження швидкості: ~3 запити/секунду в середньому. CLI не обходить це.
- API не може встановлювати фільтри **view** бази даних — це лише у UI.
- Використовуй `"is_inline": true`, коли створюєш джерела даних, щоб вбудувати їх у сторінку.
- Завжди передавай `-s` до `curl`, щоб придушити індикатори прогресу (чистіший вивід агента).
- Пропускай JSON через `jq` під час читання: `... | jq '.results[0].properties'`.
- Notion також постачається з сервером MCP (`Notion MCP`, ~91 % більш ефективним у використанні токенів для операцій з БД, ніж попередня версія) — підключи його через підтримку MCP Hermes, якщо потрібен стрімінговий доступ до Notion зсередини сесії, проте наведені вище шляхи достатні для більшості одноразових завдань.