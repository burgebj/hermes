---
title: "Airtable — Airtable REST API через curl"
sidebar_label: "Airtable"
description: "Airtable REST API через curl"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Airtable

REST API Airtable через `curl`. Операции CRUD над записями, фильтры, upsert‑ы.
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/productivity/airtable` |
| Версия | `1.1.0` |
| Автор | сообщество |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `Airtable`, `Productivity`, `Database`, `API` |
:::info
Следующее — полное определение **skill**, которое Hermes загружает при срабатывании этого **skill**. Это то, что агент видит как инструкции, когда **skill** активен.
:::

# Airtable — базы, таблицы и записи

Работай с REST API Airtable напрямую через `curl`, используя инструмент `terminal`. Без сервера MCP, без OAuth‑потока, без Python SDK — только `curl` и персональный токен доступа.
## Предварительные требования

1. Создай **Personal Access Token (PAT)** на https://airtable.com/create/tokens (токены начинаются с `pat...`).
2. Предоставь эти области доступа (минимум):
   - `data.records:read` — чтение строк
   - `data.records:write` — создание / обновление / удаление строк
   - `schema.bases:read` — просмотр баз и таблиц
3. **Важно:** в том же интерфейсе токена добавь каждую базу, к которой хочешь получить доступ, в список **Access** токена. PAT привязываются к базе — валидный токен для неправильной базы возвращает `403`.
4. Сохрани токен в `~/.hermes/.env` (или через `hermes setup`):
   ```
   AIRTABLE_API_KEY=pat_your_token_here
   ```

> Примечание: устаревшие API‑ключи `key...` были отменены в феврале 2024 года. Сейчас работают только PAT и токены OAuth.
## Основы API

- **Endpoint:** `https://api.airtable.com/v0`
- **Auth header:** `Authorization: Bearer $AIRTABLE_API_KEY`
- **All requests** используют JSON (`Content-Type: application/json` для любого тела POST/PATCH/PUT).
- **Object IDs:** базы `app…`, таблицы `tbl…`, записи `rec…`, поля `fld…`. Идентификаторы никогда не меняются; имена могут. Предпочитай использовать идентификаторы в автоматизациях.
- **Rate limit:** 5 запросов/сек/база. `429` → делай back‑off. Всплеск запросов к одной базе будет ограничен.

Базовый шаблон curl:
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=5" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

`-s` подавляет индикатор прогресса curl — оставляй его включённым для каждого вызова, чтобы вывод инструмента оставался чистым для Hermes. Передавай через `python3 -m json.tool` (всегда доступно) или `jq` (если установлен) для читаемого JSON.
## Типы полей (формы тела запроса)

| Тип поля | Форма записи |
|---|---|
| Текст в одну строку | `"Name": "hello"` |
| Длинный текст | `"Notes": "multi\nline"` |
| Число | `"Score": 42` |
| Флажок | `"Done": true` |
| Один вариант | `"Status": "Todo"` (имя должно уже существовать, если только не `typecast: true`) |
| Несколько вариантов | `"Tags": ["urgent", "bug"]` |
| Дата | `"Due": "2026-04-01"` |
| Дата и время (UTC) | `"At": "2026-04-01T14:30:00.000Z"` |
| URL / Email / Phone | `"Link": "https://…"` |
| Вложение | `"Files": [{"url": "https://…"}]` (Airtable получает и переразмещает) |
| Связанная запись | `"Owner": ["recXXXXXXXXXXXXXX"]` (массив ID записей) |
| Пользователь | `"AssignedTo": {"id": "usrXXXXXXXXXXXXXX"}` |

Передай `"typecast": true` в верхнем уровне тела create/update, чтобы Airtable автоматически привёл значения к нужному типу (например, создать новый вариант выбора «на лету», преобразовать `"42"` → `42`).
## Общие запросы

### Список баз, которые видит токен
```bash
curl -s "https://api.airtable.com/v0/meta/bases" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Список таблиц и схемы базы
```bash
curl -s "https://api.airtable.com/v0/meta/bases/$BASE_ID/tables" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
Используй это ПЕРЕД изменением данных — подтверждает точные имена полей и их ID, выводит `options.choices` для полей‑выборов и показывает имена основных полей.

### Список записей (первые 10)
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=10" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Получить одну запись
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Фильтрация записей (filterByFormula)
Формулы Airtable должны быть URL‑закодированы. Позволь стандартной библиотеке Python выполнить это — никогда не кодируй вручную:
```bash
FORMULA="{Status}='Todo'"
ENC=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$FORMULA")
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?filterByFormula=$ENC&maxRecords=20" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

Полезные шаблоны формул:
- Точное совпадение: `{Email}='user@example.com'`
- Содержит: `FIND('bug', LOWER({Title}))`
- Несколько условий: `AND({Status}='Todo', {Priority}='High')`
- Или: `OR({Owner}='alice', {Owner}='bob')`
- Не пусто: `NOT({Assignee}='')`
- Сравнение дат: `IS_AFTER({Due}, TODAY())`

### Сортировка и выбор конкретных полей
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?sort%5B0%5D%5Bfield%5D=Priority&sort%5B0%5D%5Bdirection%5D=asc&fields%5B%5D=Name&fields%5B%5D=Status" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
Квадратные скобки в параметрах запроса ДОЛЖНЫ быть URL‑закодированы (`%5B` / `%5D`).

### Использовать именованный вид
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?view=Grid%20view&maxRecords=50" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
Виды применяют свои сохранённые фильтры и сортировку на стороне сервера.
## Общие мутации

### Создать запись
```bash
curl -s -X POST "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Name":"New task","Status":"Todo","Priority":"High"}}' | python3 -m json.tool
```

### Создать до 10 записей за один вызов
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
Конечные точки пакетных запросов ограничены **10 записями за запрос**. Для больших вставок выполняй цикл пакетами по 10 с короткой паузой, чтобы соблюдать ограничение 5 запросов в секунду на базу.

### Обновить запись (PATCH — объединяет, сохраняет неизменные поля)
```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Status":"Done"}}' | python3 -m json.tool
```

### Upsert по полю слияния (ID не требуется)
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
`performUpsert` создаёт записи, у которых значения поля слияния новые, и патчит записи, у которых значения поля слияния уже существуют. Отлично подходит для идемпотентных синхронизаций.

### Удалить запись
```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Удалить до 10 записей за один вызов
```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE?records%5B%5D=rec1&records%5B%5D=rec2" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
## Пагинация

Эндпоинты, возвращающие списки, возвращают не более **100 записей на страницу**. Если в ответе присутствует `"offset": "..."`, передай его в следующем вызове. Повторяй запрос, пока поле присутствует:

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
## Типичный рабочий процесс Hermes

1. **Подтверди аутентификацию.** `curl -s -o /dev/null -w "%{http_code}\n" https://api.airtable.com/v0/meta/bases -H "Authorization: Bearer $AIRTABLE_API_KEY"` — ожидай `200`.
2. **Найди базу.** Выведи список баз (шаг выше) ИЛИ запроси у пользователя ID `app...` напрямую, если токен не имеет `schema.bases:read`.
3. **Исследуй схему.** `GET /v0/meta/bases/$BASE_ID/tables` — кешируй точные имена полей и имя первичного поля локально в сессии перед любыми изменениями.
4. **Читай, прежде чем писать.** Для «update X where Y» сначала используй `filterByFormula`, чтобы определить ID `rec...`, затем `PATCH /v0/$BASE_ID/$TABLE/$RECORD_ID`. Никогда не угадывай ID записей.
5. **Пакетные записи.** Объединяй связанные создания в один POST из 10 записей, чтобы оставаться в пределах бюджета 5 запросов/сек.
6. **Разрушительные операции.** Удаления нельзя отменить через API. Если пользователь говорит «delete all Xs», отобрази фильтр + количество записей и запроси подтверждение перед выполнением.
## Подводные камни

- **`filterByFormula` ДОЛЖЕН быть URL‑закодирован**. Имена полей с пробелами или не‑ASCII‑символами также требуют кодирования (`{My Field}` → `%7BMy%20Field%7D`). Используй стандартную библиотеку Python (шаблон выше) — никогда не кодируй вручную.
- **Пустые поля опускаются в ответах**. Отсутствие ключа `"Assignee"` не означает, что поле не существует — это значит, что значение записи пустое. Проверь схему (шаг 3), прежде чем делать вывод, что поле отсутствует.
- **PATCH vs PUT**. `PATCH` объединяет переданные поля с записью. `PUT` полностью заменяет запись и очищает любые поля, которые не были включены. По умолчанию используй `PATCH`.
- **Варианты одиночного выбора должны существовать**. Запись `"Status": "Shipping"` при отсутствии `Shipping` в списке вариантов поля приводит к ошибке `INVALID_MULTIPLE_CHOICE_OPTIONS`, если не передать `"typecast": true` (который автоматически создаёт вариант).
- **Токен привязан к базе**. Ошибка `403` в одной базе при работе в другой означает, что список доступа токена не включает эту базу — это не проблема области действия или аутентификации. Перенаправь пользователя на https://airtable.com/create/tokens, чтобы предоставить доступ.
- **Ограничения по частоте запросов привязаны к базе, а не к токену**. 5 запросов/сек на `baseA` и 5 запросов/сек на `baseB` допустимы; 6 запросов/сек только на `baseA` вызовут ограничение. Следи за заголовком `Retry-After` в ответе `429`.
## Важные замечания для Hermes

- **Всегда используй инструмент `terminal` с `curl`.** НЕ используй `web_extract` (он не может отправлять заголовки авторизации) или `browser_navigate` (требует UI‑авторизацию и медленный).
- **`AIRTABLE_API_KEY` автоматически попадает из `~/.hermes/.env` в подпроцесс** при загрузке этого навыка — нет необходимости переэкспортировать её перед каждым вызовом `curl`.
- **Осторожно экранируй фигурные скобки в формулах.** В теле heredoc `{Status}` воспринимается как литерал. В аргументе оболочки `{Status}` безопасен вне контекста расширения скобок `{...}` — но перед вставкой динамических строк в URL пропускай их через `python3 urllib.parse.quote`.
- **Для красивого вывода используй `python3 -m json.tool`** (всегда доступен) вместо `jq` (опционально). Обращайся к `jq` только когда нужен фильтр/проекция.
- **Пагинация происходит постранично, а не глобально.** Ограничение Airtable в 100 записей — жёсткое; увеличить его нельзя. Делай цикл с `offset`, пока поле отсутствует.
- **Читай массив `errors`** в ответах с кодом, не являющимся 2xx — Airtable возвращает структурированные коды ошибок, такие как `AUTHENTICATION_REQUIRED`, `INVALID_PERMISSIONS`, `MODEL_ID_NOT_FOUND`, `INVALID_MULTIPLE_CHOICE_OPTIONS`, которые точно указывают, в чём проблема.