---
title: "Google Workspace — Gmail, Calendar, Drive, Docs, Sheets через gws CLI або Python"
sidebar_label: "Google Workspace"
description: "Gmail, Calendar, Drive, Docs, Sheets через gws CLI або Python"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Google Workspace

Gmail, Calendar, Drive, Docs, Sheets за допомогою `gws` CLI або `Python`.
## Метадані навички

| | |
|---|---|
| Source | Вбудований (встановлений за замовчуванням) |
| Path | `skills/productivity/google-workspace` |
| Version | `1.1.0` |
| Author | Nous Research |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Google`, `Gmail`, `Calendar`, `Drive`, `Sheets`, `Docs`, `Contacts`, `Email`, `OAuth` |
| Related skills | [`himalaya`](/docs/user-guide/skills/bundled/email/email-himalaya) |
:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це інструкції, які бачить агент під час роботи навички.
:::

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets і Docs — через керований Hermes OAuth та тонкий обгортковий CLI. Коли встановлено `gws`, навичка використовує його як бекенд виконання для ширшого охоплення Google Workspace; інакше вона переходить до вбудованої реалізації клієнта на Python.
## Посилання

- `references/gmail-search-syntax.md` — Оператори пошуку Gmail (is:unread, from:, newer_than:, тощо)
## Scripts

- `scripts/setup.py` — налаштування OAuth2 (виконується один раз для авторизації)
- `scripts/google_api.py` — обгортка CLI сумісності. Вона надає перевагу `gws` для операцій, коли він доступний, зберігаючи існуючий контракт виводу JSON Hermes.
## Налаштування в перший раз

Налаштування повністю не‑інтерактивне — ти керуєш ним крок за кроком, щоб воно працювало в CLI, Telegram, Discord або будь‑якій іншій платформі.

Визнач спочатку скорочення:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### Крок 0: Перевірити, чи вже налаштовано

```bash
$GSETUP --check
```

Якщо виводиться `AUTHENTICATED`, переходь до **Використання** — налаштування вже виконано.

### Крок 1: Тріаж — запитай у користувача, що йому потрібно

Перед початком налаштування OAuth запитай у користувача **два** питання:

**Питання 1: «Які сервіси Google тобі потрібні? Тільки електронну пошту чи ще Calendar/Drive/Sheets/Docs?»**

- **Тільки Email** → Цей навик їм не потрібен. Використай навик `himalaya` замість — він працює з паролем додатку Gmail (Settings → Security → App Passwords) і налаштування займає 2 хвилини. Проєкт у Google Cloud не потрібен. Завантаж навик `himalaya` і слідуй його інструкціям.
- **Email + Calendar** → Продовжуй з цим навиком, але під час автентифікації використай `--services email,calendar`, щоб екран згоди запитував лише потрібні області.
- **Тільки Calendar/Drive/Sheets/Docs** → Продовжуй з цим навиком і використай більш вузький набір `--services`, наприклад `calendar,drive,sheets,docs`.
- **Повний доступ до Workspace** → Продовжуй з цим навиком і використай стандартний набір сервісів `all`.

**Питання 2: «Чи використовує твій обліковий запис Google Advanced Protection (апаратні ключі безпеки, необхідні для входу)? Якщо ти не впевнений, швидше за все ні — це те, в чому ти мав би явно зареєструватись».**

- **Ні / Не впевнений** → Звичайне налаштування. Продовжуй далі.
- **Так** → Адміністратор Workspace має додати OAuth‑client ID до списку дозволених додатків організації, перш ніж Крок 4 працюватиме. Повідом його заздалегідь.

### Крок 2: Створити OAuth‑облікові дані (одноразово, ~5 хв)

Скажи користувачу:

> Тобі потрібен Google Cloud OAuth‑клієнт. Це одноразове налаштування:
>
> 1. Створи або вибери проєкт:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Увімкни необхідні API у бібліотеці API:
>    https://console.cloud.google.com/apis/library
>    Увімкни: Gmail API, Google Calendar API, Google Drive API, Google Sheets API, Google Docs API, People API
> 3. Створи OAuth‑клієнт тут:
>    https://console.cloud.google.com/apis/credentials
>    Credentials → Create Credentials → OAuth 2.0 Client ID
> 4. Тип застосунку: «Desktop app» → Create
> 5. Якщо застосунок ще в режимі **Testing**, додай обліковий запис Google користувача як тестового користувача тут:
>    https://console.cloud.google.com/auth/audience
>    Audience → Test users → Add users
> 6. Завантаж JSON‑файл і повідом мені шлях до нього
>
> **Важлива нотатка Hermes CLI**: якщо шлях починається з `/`, НЕ надсилай його окремим повідомленням у CLI, бо його можуть сприйняти як slash‑команду. Надішли його в реченні, наприклад:
> ``The JSON file path is: /home/user/Downloads/client_secret_....json``

Після того, як користувач надасть шлях:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

Якщо вони вставлять сирі значення client ID / client secret замість шляху до файлу, створи для них дійсний Desktop OAuth JSON‑файл, збережи його явно (наприклад `~/Downloads/hermes-google-client-secret.json`), а потім запусти `--client-secret` з цим файлом.

### Крок 3: Отримати URL авторизації

Використай набір сервісів, обраний у Кроці 1. Приклади:

```bash
$GSETUP --auth-url --services email,calendar --format json
$GSETUP --auth-url --services calendar,drive,sheets,docs --format json
$GSETUP --auth-url --services all --format json
```

Це поверне JSON з полем `auth_url` і також збереже точний URL у `~/.hermes/google_oauth_last_url.txt`.

**Правила агента для цього кроку**
- Витягни поле `auth_url` і надішли цей точний URL користувачу в одному рядку.
- Скажи, що браузер, ймовірно, завершиться помилкою на `http://localhost:1` після схвалення, і це очікувано.
- Попроси скопіювати **повний** перенаправлений URL з адресного рядка браузера.
- Якщо користувач отримує `Error 403: access_denied`, направ його безпосередньо до `https://console.cloud.google.com/auth/audience`, щоб додати себе як тестового користувача.

### Крок 4: Обміняти код

Користувач вставить назад або URL типу `http://localhost:1/?code=4/0A...&scope=...`, або лише рядок коду. Обидва варіанти працюють. Крок `--auth-url` зберігає тимчасову очікуючу OAuth‑сесію локально, щоб `--auth-code` міг завершити PKCE‑обмін пізніше, навіть на безголових системах:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED" --format json
```

Якщо `--auth-code` не вдається через прострочений код, вже використаний код або код із старої вкладки браузера, він тепер повертає новий `fresh_auth_url`. У цьому випадку негайно надішли новий URL користувачу і попроси його повторити процедуру з новим перенаправленням браузера.

### Крок 5: Перевірка

```bash
$GSETUP --check
```

Повинно вивести `AUTHENTICATED`. Налаштування завершено — токен оновлюватиметься автоматично відтепер.

### Примітки

- Токен зберігається у `~/.hermes/google_token.json` і автоматично оновлюється.
- Стан/верифікатор очікуючої OAuth‑сесії тимчасово зберігаються у `~/.hermes/google_oauth_pending.json` до завершення обміну.
- Якщо встановлено `gws`, `google_api.py` вказує його на той самий файл `~/.hermes/google_token.json`. Користувачам не потрібно запускати окремий `gws auth login` процес.
- Для відкликання: `$GSETUP --revoke`
## Використання

Усі команди проходять через скрипт API. Встанови `GAPI` як скорочення:

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
## Формат виводу

Усі команди повертають JSON. Розбирай його за допомогою `jq` або читай безпосередньо. Ключові поля:

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

1. **Ніколи не надсилай електронну пошту, не створюй/видаляй події в календарі, не видаляй файли Drive, не ділись файлами та не змінюй Docs/Sheets без підтвердження користувача.** Показуй, що саме буде зроблено (одержувачі, ідентифікатори файлів, вміст, роль доступу) і запитуй схвалення. Для `drive delete` надавай перевагу стандартному переміщенню у кошик (можна відновити), а не `--permanent`.
2. **Перевір автентифікацію перед першим використанням** — запусти `setup.py --check`. Якщо вона не проходить, проведи користувача через процес налаштування.
3. **Використовуй довідник синтаксису пошуку Gmail** для складних запитів — завантаж його за допомогою `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
4. **Час у календарі має включати часовий пояс** — завжди використовуйте ISO 8601 з офсетом (наприклад, `2026-03-01T10:00:00-06:00`) або UTC (`Z`).
5. **Дотримуйся обмежень швидкості** — уникай швидких послідовних викликів API. За можливості групуй запити.
## Усунення проблем

| Проблема | Виправлення |
|---------|------------|
| `NOT_AUTHENTICATED` | Запусти кроки налаштування 2‑5 вище |
| `REFRESH_FAILED` | Токен відкликано або він прострочений — повтори кроки 3‑5 |
| `HttpError 403: Insufficient Permission` | Відсутня область API — `$GSETUP --revoke`, потім повтори кроки 3‑5 |
| `AUTHENTICATED (partial)` або "Token missing scopes" | Нові можливості запису (Drive write/delete, Docs create/edit) потребують повторної авторизації. `$GSETUP --revoke`, потім повтори кроки 3‑5, щоб надати оновлені області. |
| `HttpError 403: Access Not Configured` | API не ввімкнено — користувачеві потрібно активувати його в Google Cloud Console |
| `ModuleNotFoundError` | Запусти `$GSETUP --install-deps` |
| Advanced Protection blocks auth | Адміністратор Workspace має додати OAuth‑клієнт ID у білий список |
## Відкликання доступу

```bash
$GSETUP --revoke
```