---
title: "Google Workspace — Gmail, Calendar, Drive, Docs, Sheets через gws CLI или Python"
sidebar_label: "Google Workspace"
description: "Gmail, Calendar, Drive, Docs, Sheets через gws CLI или Python"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Google Workspace

Gmail, Calendar, Drive, Docs, Sheets с помощью gws CLI или Python.
## Метаданные навыка

| | |
|---|---|
| Source | Встроенный (устанавливается по умолчанию) |
| Path | `skills/productivity/google-workspace` |
| Version | `1.1.0` |
| Author | Nous Research |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Google`, `Gmail`, `Calendar`, `Drive`, `Sheets`, `Docs`, `Contacts`, `Email`, `OAuth` |
| Related skills | [`himalaya`](/docs/user-guide/skills/bundled/email/email-himalaya) |
:::info
Следующий текст — полное определение **skill**, которое Hermes загружает при срабатывании этого **skill**. Это то, что агент видит как инструкции, когда **skill** активен.
:::

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets и Docs — через управляемый Hermes OAuth и тонкую обёртку CLI. Когда установлен `gws`, **skill** использует его в качестве backend‑исполнителя для более широкого охвата Google Workspace; в противном случае он переходит к встроенной реализации клиента на Python.
## Ссылки

- `references/gmail-search-syntax.md` — Операторы поиска Gmail (is:unread, from:, newer_than:, и т.д.)
## Скрипты

- `scripts/setup.py` — настройка OAuth2 (выполняется один раз для авторизации)
- `scripts/google_api.py` — совместимая обёртка‑CLI. Предпочитает `gws` для операций, когда он доступен, при этом сохраняет существующий контракт JSON‑вывода Hermes.
## Первичная настройка

Настройка полностью неинтерактивна — ты управляешь ею шаг за шагом, чтобы она работала в CLI, Telegram, Discord или любой другой платформе.

Сначала определи сокращение:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### Шаг 0: Проверить, настроено ли уже

```bash
$GSETUP --check
```

Если выводится `AUTHENTICATED`, переходи к использованию — настройка уже выполнена.

### Шаг 1: Триаж — спроси пользователя, что ему нужно

Перед началом настройки OAuth задай пользователю ДВА вопроса:

**Вопрос 1: «Какие сервисы Google вам нужны? Только электронную почту или также Calendar/Drive/Sheets/Docs?»**

- **Только email** → Этот навык им вовсе не нужен. Используй навык `himalaya` вместо него — он работает с паролем приложения Gmail (Settings → Security → App Passwords) и настраивается за 2 минуты. Проект в Google Cloud не требуется. Загрузите навык `himalaya` и следуйте его инструкциям по настройке.
- **Email + Calendar** → Продолжай с этим навыком, но при аутентификации укажи `--services email,calendar`, чтобы экран согласия запрашивал только те области, которые действительно нужны.
- **Только Calendar/Drive/Sheets/Docs** → Продолжай с этим навыком и укажи более узкий набор `--services`, например `calendar,drive,sheets,docs`.
- **Полный доступ к Workspace** → Продолжай с этим навыком и используй набор сервисов по умолчанию `all`.

**Вопрос 2: «Использует ли ваш аккаунт Google Advanced Protection (требуются аппаратные ключи безопасности для входа)? Если ты не уверен, скорее всего — нет, это то, в чём ты явно регистрировался бы заранее.»**

- **Нет / Не уверен** → Обычная настройка. Продолжай ниже.
- **Да** → Администратор Workspace должен добавить ID OAuth‑клиента в список разрешённых приложений организации до того, как Шаг 4 начнёт работать. Сообщи об этом заранее.

### Шаг 2: Создать OAuth‑учётные данные (один раз, ~5 минут)

Сообщи пользователю:

> Тебе нужен OAuth‑клиент Google Cloud. Это одноразовая настройка:
>
> 1. Создай или выбери проект:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Включи необходимые API в библиотеке API:
>    https://console.cloud.google.com/apis/library
>    Включи: Gmail API, Google Calendar API, Google Drive API, Google Sheets API, Google Docs API, People API
> 3. Создай OAuth‑клиент здесь:
>    https://console.cloud.google.com/apis/credentials
>    Credentials → Create Credentials → OAuth 2.0 Client ID
> 4. Тип приложения: «Desktop app» → Create
> 5. Если приложение всё ещё в режиме Testing, добавь аккаунт пользователя как тестового здесь:
>    https://console.cloud.google.com/auth/audience
>    Audience → Test users → Add users
> 6. Скачай JSON‑файл и сообщи мне путь к файлу
>
> Важное примечание к Hermes CLI: если путь к файлу начинается с `/`, НЕ отправляй его как отдельное сообщение в CLI, потому что его могут принять за слеш‑команду. Вставь его в предложение, например:
> `The JSON file path is: /home/user/Downloads/client_secret_....json`

После того как он предоставит путь:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

Если он вставит сырые значения client ID / client secret вместо пути к файлу, создай для него корректный Desktop OAuth JSON‑файл, сохрани его явно (например `~/Downloads/hermes-google-client-secret.json`), а затем запусти `--client-secret` с этим файлом.

### Шаг 3: Получить URL авторизации

Используй набор сервисов, выбранный в Шаге 1. Примеры:

```bash
$GSETUP --auth-url --services email,calendar --format json
$GSETUP --auth-url --services calendar,drive,sheets,docs --format json
$GSETUP --auth-url --services all --format json
```

Команда возвращает JSON с полем `auth_url` и также сохраняет точный URL в `~/.hermes/google_oauth_last_url.txt`.

Правила агента для этого шага:
- Извлеки поле `auth_url` и отправь пользователю именно этот URL в одной строке.
- Скажи пользователю, что после одобрения браузер, скорее всего, завершится ошибкой на `http://localhost:1`, и это ожидаемо.
- Попроси его скопировать ПОЛНЫЙ перенаправленный URL из адресной строки браузера.
- Если пользователь получит `Error 403: access_denied`, сразу направь его на `https://console.cloud.google.com/auth/audience`, чтобы добавить себя как тестового пользователя.

### Шаг 4: Обменять код

Пользователь вставит либо URL вида `http://localhost:1/?code=4/0A...&scope=...`, либо просто строку кода. Оба варианта работают. Шаг `--auth-url` сохраняет временную неполную OAuth‑сессию локально, чтобы `--auth-code` мог завершить PKCE‑обмен позже, даже на безголовых системах:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED" --format json
```

Если `--auth-code` не удаётся из‑за истечения срока действия кода, его повторного использования или получения из более старой вкладки браузера, он теперь возвращает свежий `fresh_auth_url`. В этом случае сразу отправь новый URL пользователю и попроси его повторить попытку, используя только последний перенаправленный URL.

### Шаг 5: Проверка

```bash
$GSETUP --check
```

Должно вывести `AUTHENTICATED`. Настройка завершена — токен будет автоматически обновляться отныне.

### Примечания

- Токен хранится в `~/.hermes/google_token.json` и автоматически обновляется.
- Состояние/верификатор незавершённой OAuth‑сессии временно сохраняются в `~/.hermes/google_oauth_pending.json` до завершения обмена.
- Если установлен `gws`, `google_api.py` указывает его на тот же файл учётных данных `~/.hermes/google_token.json`. Пользователям не требуется запускать отдельный поток `gws auth login`.
- Чтобы отозвать доступ: `$GSETUP --revoke`
## Использование

Все команды проходят через скрипт API. Установи `GAPI` как короткое имя:

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '"Research Agent" <user@example.com>' --body "Message text"

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '"Support Bot" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
# Search existing files
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5

# Get metadata for a single file
$GAPI drive get FILE_ID

# Upload a local file (auto-detects MIME type)
$GAPI drive upload /path/to/report.pdf
$GAPI drive upload /path/to/image.png --name "Logo.png" --parent FOLDER_ID

# Download (binary files download as-is; Google-native files export to a
# sensible default — Docs→pdf, Sheets→csv, Slides→pdf, Drawings→png)
$GAPI drive download FILE_ID
$GAPI drive download DOC_ID --output ~/doc.pdf
$GAPI drive download DOC_ID --export-mime text/plain --output ~/doc.txt

# Create a folder
$GAPI drive create-folder "Reports"
$GAPI drive create-folder "Q4" --parent FOLDER_ID

# Share
$GAPI drive share FILE_ID --email alice@example.com --role reader
$GAPI drive share FILE_ID --email alice@example.com --role writer --notify
$GAPI drive share FILE_ID --type anyone --role reader        # anyone with link
$GAPI drive share FILE_ID --type domain --domain example.com --role reader

# Delete — defaults to trash (reversible). Use --permanent to skip the trash.
$GAPI drive delete FILE_ID
$GAPI drive delete FILE_ID --permanent
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Create a new spreadsheet
$GAPI sheets create --title "Q4 Budget"
$GAPI sheets create --title "Inventory" --sheet-name "Stock"

# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### Docs

```bash
# Read
$GAPI docs get DOC_ID

# Create a new Doc (optionally seeded with body text)
$GAPI docs create --title "Meeting Notes"
$GAPI docs create --title "Draft" --body "First paragraph..."

# Append text to the end of an existing Doc
$GAPI docs append DOC_ID --text "Additional content to append"
```
## Формат вывода

Все команды возвращают JSON. Разбирай их с помощью `jq` или читай напрямую. Ключевые поля:

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Drive get**: `{id, name, mimeType, modifiedTime, size, webViewLink, parents, owners}`
- **Drive upload**: `{status: "uploaded", id, name, mimeType, webViewLink}`
- **Drive download**: `{status: "downloaded", id, name, path, mimeType}`
- **Drive create-folder**: `{status: "created", id, name, webViewLink}`
- **Drive share**: `{status: "shared", permissionId, fileId, role, type}`
- **Drive delete**: `{status: "trashed" | "deleted", fileId, permanent}`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`
- **Sheets create**: `{status: "created", spreadsheetId, title, spreadsheetUrl}`
- **Docs create**: `{status: "created", documentId, title, url}`
- **Docs append**: `{status: "appended", documentId, inserted_at, characters}`
## Правила

1. **Никогда не отправляй email, не создавай/удаляй события календаря, не удаляй файлы Drive, не делись файлами и не изменяй Docs/Sheets без предварительного подтверждения пользователя.** Показывай, что будет сделано (получатели, ID файлов, содержимое, роль доступа) и запрашивай одобрение. Для `drive delete` предпочитай перемещение в корзину (обратимое) вместо `--permanent`.
2. **Проверь авторизацию перед первым использованием** — запусти `setup.py --check`. Если проверка не прошла, проведи пользователя через процесс настройки.
3. **Используй справочник синтаксиса поиска Gmail** для сложных запросов — загрузить его можно с помощью `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
4. **Время в календаре должно включать часовой пояс** — всегда используй ISO 8601 с смещением (например, `2026-03-01T10:00:00-06:00`) или UTC (`Z`).
5. **Соблюдай ограничения по частоте запросов** — избегай быстрых последовательных вызовов API. По возможности объединяй чтения в пакеты.
## Устранение неполадок

| Проблема | Решение |
|----------|---------|
| `NOT_AUTHENTICATED` | Выполни шаги 2‑5 из раздела **Setup** |
| `REFRESH_FAILED` | Токен отозван или истёк — повторно выполни шаги 3‑5 |
| `HttpError 403: Insufficient Permission` | Отсутствует необходимый API‑scope — `$GSETUP --revoke`, затем повторно выполни шаги 3‑5 |
| `AUTHENTICATED (partial)` или `Token missing scopes` | Для новых возможностей записи (запись/удаление в Drive, создание/редактирование Docs) требуется повторная авторизация. `$GSETUP --revoke`, затем повторно выполни шаги 3‑5, чтобы предоставить расширенные scopes |
| `HttpError 403: Access Not Configured` | API не включён — пользователю нужно включить его в Google Cloud Console |
| `ModuleNotFoundError` | Выполни `$GSETUP --install-deps` |
| Advanced Protection blocks auth | Администратор Workspace должен добавить OAuth‑client‑ID в список разрешённых |
## Отзыв доступа

```bash
$GSETUP --revoke
```