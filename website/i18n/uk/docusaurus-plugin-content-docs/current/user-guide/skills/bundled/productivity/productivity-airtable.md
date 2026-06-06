---
title: "Airtable — Airtable REST API через curl"
sidebar_label: "Airtable"
description: "Airtable REST API через curl"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Airtable

Airtable REST API за допомогою `curl`. Операції CRUD над записами, фільтри, upserts.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/productivity/airtable` |
| Версія | `1.1.0` |
| Автор | community |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `Airtable`, `Productivity`, `Database`, `API` |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Airtable — Bases, Tables & Records

Працюй з REST API Airtable безпосередньо за допомогою `curl` через інструмент `terminal`. Без сервера MCP, без OAuth‑потоку, без Python SDK — лише `curl` і персональний токен доступу.
## Передумови

1. Створи **Personal Access Token (PAT)** за адресою https://airtable.com/create/tokens (токени починаються з `pat...`).
2. Надай ці області доступу (мінімум):
   - `data.records:read` — читання рядків
   - `data.records:write` — створення / оновлення / видалення рядків
   - `schema.bases:read` — перегляд баз і таблиць
3. **Важливо:** у тому ж інтерфейсі токену додай кожну базу, до якої потрібен доступ, у список **Access** токену. PAT‑и мають область доступу per‑base — дійсний токен для неправильної бази поверне `403`.
4. Збережи токен у `~/.hermes/.env` (або через `hermes setup`):
   ```
   AIRTABLE_API_KEY=pat_your_token_here
   ```

> Note: legacy `key...` API keys were deprecated Feb 2024. Only PATs and OAuth tokens work now.
## Основи API

- **Endpoint:** `https://api.airtable.com/v0`
- **Auth header:** `Authorization: Bearer $AIRTABLE_API_KEY`
- **Усі запити** використовують JSON (`Content-Type: application/json` для будь‑якого тіла POST/PATCH/PUT).
- **Ідентифікатори об’єктів:** bases `app...`, tables `tbl...`, records `rec...`, fields `fld...`. Ідентифікатори не змінюються; назви можуть. У автоматизаціях надавай перевагу ідентифікаторам.
- **Ліміт швидкості:** 5 запитів/сек/база. `429` → зменшити навантаження. Сплеск запитів до однієї бази буде обмежений.

Base curl pattern:
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=5" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

`-s` вимикає індикатор прогресу curl — залиш його у кожному виклику, щоб вивід інструмента залишався чистим для Hermes. Пропусти результат через `python3 -m json.tool` (завжди доступний) або `jq` (за наявності) для читабельного JSON.
## Типи полів (форми тіла запиту)

| Тип поля | Форма запису |
|---|---|
| Текст в один рядок | `"Name": "hello"` |
| Довгий текст | `"Notes": "multi\nline"` |
| Число | `"Score": 42` |
| Прапорець | `"Done": true` |
| Один варіант вибору | `"Status": "Todo"` (назва має вже існувати, якщо не `typecast: true`) |
| Кілька варіантів вибору | `"Tags": ["urgent", "bug"]` |
| Дата | `"Due": "2026-04-01"` |
| Дата і час (UTC) | `"At": "2026-04-01T14:30:00.000Z"` |
| URL / Email / Телефон | `"Link": "https://…"` |
| Вкладення | `"Files": [{"url": "https://…"}]` (Airtable завантажує та повторно розміщує) |
| Пов’язаний запис | `"Owner": ["recXXXXXXXXXXXXXX"]` (масив ідентифікаторів запису) |
| Користувач | `"AssignedTo": {"id": "usrXXXXXXXXXXXXXX"}` |

Передай `"typecast": true` на верхньому рівні тіла create/update, щоб Airtable автоматично приводив значення (наприклад, створював нову опцію вибору «на льоту», конвертував `"42"` → `42`).
## Common Queries

### List bases the token can see
```bash
curl -s "https://api.airtable.com/v0/meta/bases" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### List tables + schema for a base
```bash
curl -s "https://api.airtable.com/v0/meta/bases/$BASE_ID/tables" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
Використовуй це ПЕРЕД внесенням змін — підтверджує точні назви полів і ID, показує `options.choices` для полів‑вибору та відображає назви первинних полів.

### List records (first 10)
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=10" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Get a single record
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Filter records (filterByFormula)
Формули Airtable мають бути URL‑закодовані. Нехай це робить стандартна бібліотека Python — ніколи не кодуй вручну:
```bash
FORMULA="{Status}='Todo'"
ENC=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$FORMULA")
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?filterByFormula=$ENC&maxRecords=20" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

Корисні шаблони формул:
- Точний збіг: `{Email}='user@example.com'`
- Містить: `FIND('bug', LOWER({Title}))`
- Кілька умов: `AND({Status}='Todo', {Priority}='High')`
- Або: `OR({Owner}='alice', {Owner}='bob')`
- Не порожнє: `NOT({Assignee}='')`
- Порівняння дат: `IS_AFTER({Due}, TODAY())`

### Sort + select specific fields
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?sort%5B0%5D%5Bfield%5D=Priority&sort%5B0%5D%5Bdirection%5D=asc&fields%5B%5D=Name&fields%5B%5D=Status" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
Квадратні дужки в параметрах запиту ПОВИННІ бути URL‑закодовані (`%5B` / `%5D`).

### Use a named view
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?view=Grid%20view&maxRecords=50" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
Перегляди застосовують їх збережений фільтр і сортування на боці сервера.
## Common Mutations

### Створити запис
```bash
curl -s -X POST "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Name":"New task","Status":"Todo","Priority":"High"}}' | python3 -m json.tool
```

### Створити до 10 записів в одному виклику
```bash
curl -s -X POST "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "typecast": true,
    "records": [
      {"fields": {"Name": "Task A", "Status": "Todo"}},
      {"fields": {"Name": "Task B", "Status": "In progress"}}
    ]
  }' | python3 -m json.tool
```
Batch‑endpoints обмежені **10 записами за запит**. Для більших вставок виконуй цикл пакетами по 10 записів із короткою паузою, щоб не перевищити 5 запитів/сек/базу.

### Оновити запис (PATCH — об’єднує, зберігає незмінені поля)
```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Status":"Done"}}' | python3 -m json.tool
```

### Upsert за полем злиття (ID не потрібен)
```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "performUpsert": {"fieldsToMergeOn": ["Email"]},
    "records": [
      {"fields": {"Email": "user@example.com", "Status": "Active"}}
    ]
  }' | python3 -m json.tool
```
`performUpsert` створює записи, чиї значення merge‑field нові, та патчить записи, чиї значення merge‑field вже існують. Чудово підходить для ідемпотентних синхронізацій.

### Видалити запис
```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Видалити до 10 записів в одному виклику
```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE?records%5B%5D=rec1&records%5B%5D=rec2" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
## Пагінація

List‑endpoints повертають не більше **100 записів на сторінку**. Якщо у відповіді є `"offset": "..."`, передай його у наступному запиті. Повторюй цикл, доки поле відсутнє:

```bash
OFFSET=""
while :; do
  URL="https://api.airtable.com/v0/$BASE_ID/$TABLE?pageSize=100"
  [ -n "$OFFSET" ] && URL="$URL&offset=$OFFSET"
  RESP=$(curl -s "$URL" -H "Authorization: Bearer $AIRTABLE_API_KEY")
  echo "$RESP" | python3 -c 'import json,sys; d=json.load(sys.stdin); [print(r["id"], r["fields"].get("Name","")) for r in d["records"]]'
  OFFSET=$(echo "$RESP" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("offset",""))')
  [ -z "$OFFSET" ] && break
done
```
## Типовий робочий процес Hermes

1. **Підтвердити автентифікацію.** `curl -s -o /dev/null -w "%{http_code}\n" https://api.airtable.com/v0/meta/bases -H "Authorization: Bearer $AIRTABLE_API_KEY"` — очікуй `200`.
2. **Знайти базу.** Переглянь бази (крок вище) АБО запитай у користувача `app...` ID безпосередньо, якщо токен не має `schema.bases:read`.
3. **Перевірити схему.** `GET /v0/meta/bases/$BASE_ID/tables` — кешуй точні назви полів і назву первинного поля локально в сесії перед будь‑якими змінами.
4. **Читай, перш ніж писати.** Для «update X where Y» спочатку використай `filterByFormula`, щоб отримати `rec...` ID, потім `PATCH /v0/$BASE_ID/$TABLE/$RECORD_ID`. Ніколи не вгадуй ID запису.
5. **Пакетні записи.** Об’єднуй пов’язані створення в один POST на 10 записів, щоб залишатися в межах бюджету 5 запитів/сек.
6. **Деструктивні операції.** Видалення не можна скасувати через API. Якщо користувач каже «delete all Xs», відобрази фільтр + кількість записів і підтверди перед виконанням.
## Підводні камені

- **`filterByFormula` ПОВИНЕН бути URL‑закодований.** Імена полів з пробілами або не‑ASCII також потребують кодування (`{My Field}` → `%7BMy%20Field%7D`). Використовуй стандартну бібліотеку Python (шаблон вище) — ніколи не кодуй вручну.
- **Порожні поля опускаються у відповідях.** Відсутність ключа `"Assignee"` не означає, що поле не існує — це означає, що значення цього запису порожнє. Перевір схему (крок 3), перш ніж робити висновок, що поле відсутнє.
- **PATCH vs PUT.** `PATCH` об’єднує передані поля з записом. `PUT` замінює запис повністю і стирає будь‑яке поле, яке не було включено. За замовчуванням використай `PATCH`.
- **Опції single‑select мають існувати.** Запис `"Status": "Shipping"` коли `Shipping` відсутній у списку опцій поля, викликає помилку `INVALID_MULTIPLE_CHOICE_OPTIONS`, якщо не передати `"typecast": true` (яке автоматично створює опцію).
- **Обмеження токену за базою.** `403` у одній базі, а інша працює, означає, що список доступу токену не включає цю базу — це не проблема області чи автентифікації. Перенаправ користувача на https://airtable.com/create/tokens, щоб надати доступ.
- **Ліміти швидкості застосовуються до бази, а не до токену.** 5 запитів/сек на `baseA` і 5 запитів/сек на `baseB` — це нормально; 6 запитів/сек лише на `baseA` призведе до обмеження. Слідкуй за заголовком `Retry-After` у відповіді `429`.
## Важливі нотатки для Hermes

- **Завжди використовуйте інструмент `terminal` разом із `curl`.** Не використовуйте `web_extract` (він не може надсилати заголовки автентифікації) або `browser_navigate` (потрібна UI‑автентифікація і це повільно).
- **`AIRTABLE_API_KEY` переходить з `~/.hermes/.env` у підпроцес автоматично** коли цей skill завантажується — не потрібно повторно експортувати його перед кожним викликом `curl`.
- **Обов’язково екрануйте фігурні дужки у формулах.** У тілі heredoc `{Status}` сприймається буквально. У аргументі оболонки `{Status}` безпечно поза контекстом розширення `{...}` — але перед вставкою динамічних рядків у URL пропустіть їх через `python3 urllib.parse.quote`.
- **Форматуйте вивід за допомогою `python3 -m json.tool`** (завжди доступний) замість `jq` (необов’язковий). Використовуйте `jq` лише коли потрібне фільтрування/проекція.
- **Пагінація здійснюється посторінково, а не глобально.** Обмеження Airtable у 100 записів є жорстким; збільшити його неможливо. Виконуйте цикл з `offset`, доки поле відсутнє.
- **Читайте масив `errors`** у відповідях, що не є 2xx — Airtable повертає структуровані коди помилок, такі як `AUTHENTICATION_REQUIRED`, `INVALID_PERMISSIONS`, `MODEL_ID_NOT_FOUND`, `INVALID_MULTIPLE_CHOICE_OPTIONS`, які точно вказують, у чому проблема.