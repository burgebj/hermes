---
sidebar_position: 2
sidebar_label: "Google Workspace"
title: "Google Workspace — Gmail, Calendar, Drive, Sheets та Docs"
description: "Надсилай електронну пошту, керуй подіями календаря, шукай у Drive, читай/пиши Sheets і отримуй доступ до Docs — все через OAuth2‑автентифіковані Google API"
---

# Навичка Google Workspace

Інтеграція Gmail, Calendar, Drive, Contacts, Sheets та Docs для Hermes. Використовує OAuth2 з автоматичним оновленням токену. За можливості надає перевагу [Google Workspace CLI (`gws`)](https://github.com/nicholasgasior/gws) для ширшого охоплення, а в іншому випадку переходить до бібліотек Python від Google.

**Шлях навички:** `skills/productivity/google-workspace/`

## Налаштування

Налаштування повністю керується агентом — попроси Hermes налаштувати Google Workspace, і він проведе тебе через кожен крок. Послідовність:

1. **Створи проект Google Cloud** і ввімкни необхідні API (Gmail, Calendar, Drive, Sheets, Docs, People)
2. **Створи облікові дані OAuth 2.0** (тип Desktop app) і завантаж JSON‑файл секрету клієнта
3. **Авторизуйся** — Hermes генерує URL для авторизації, ти підтверджуєш у браузері, вставляєш назад URL перенаправлення
4. **Готово** — токен автоматично оновлюється далі

:::tip Користувачі лише електронної пошти
Якщо потрібна лише пошта (без Calendar/Drive/Sheets), використай навичку **himalaya** — вона працює з паролем додатку Gmail і займає 2 хвилини. Проект Google Cloud не потрібен.
:::

## Gmail

### Пошук

```bash
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"
```

Повертає JSON з `id`, `from`, `subject`, `date`, `snippet` та `labels` для кожного повідомлення.

### Читання

```bash
$GAPI gmail get MESSAGE_ID
```

Повертає повний вміст повідомлення у вигляді тексту (віддає перевагу plain text, у випадку — HTML).

### Надсилання

```bash
# Basic send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"

# HTML email
$GAPI gmail send --to user@example.com --subject "Report" \
  --body "<h1>Q4 Results</h1><p>Details here</p>" --html

# Custom From header (display name + email)
$GAPI gmail send --to user@example.com --subject "Hello" \
  --from '"Research Agent" <user@example.com>' --body "Message text"

# With CC
$GAPI gmail send --to user@example.com --cc "team@example.com" \
  --subject "Update" --body "FYI"
```

### Користувацький заголовок From

Прапорець `--from` дозволяє налаштувати відображуване ім’я відправника у вихідних листах. Це корисно, коли кілька агентів користуються одним обліковим записом Gmail, а ти хочеш, щоб отримувачі бачили різні імена:

```bash
# Agent 1
$GAPI gmail send --to client@co.com --subject "Research Summary" \
  --from '"Research Agent" <shared@company.com>' --body "..."

# Agent 2  
$GAPI gmail send --to client@co.com --subject "Code Review" \
  --from '"Code Assistant" <shared@company.com>' --body "..."
```

**Як це працює:** Значення `--from` встановлюється як заголовок RFC 5322 `From` у MIME‑повідомленні. Gmail дозволяє змінювати відображуване ім’я для вашої власної автентифікованої електронної адреси без додаткових налаштувань. Отримувачі бачать кастомне ім’я (наприклад, «Research Agent»), а адреса залишається тією ж.

**Важливо:** Якщо ти використовуєш *іншу електронну адресу* у `--from` (не ту, що автентифікована), Gmail вимагає, щоб ця адреса була налаштована як [Send As alias](https://support.google.com/mail/answer/22370) у Gmail Settings → Accounts → Send mail as.

Прапорець `--from` працює як для `send`, так і для `reply`:

```bash
$GAPI gmail reply MESSAGE_ID \
  --from '"Support Bot" <shared@company.com>' --body "We're on it"
```

### Відповіді

```bash
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
```

Автоматично формує ланцюжок відповіді (встановлює заголовки `In-Reply-To` та `References`) і використовує ідентифікатор потоку оригінального повідомлення.

### Мітки

```bash
# List all labels
$GAPI gmail labels

# Add/remove labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

## Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (timezone required)
$GAPI calendar create --summary "Team Standup" \
  --start 2026-03-01T10:00:00-07:00 --end 2026-03-01T10:30:00-07:00

# With location and attendees
$GAPI calendar create --summary "Lunch" \
  --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z \
  --location "Cafe" --attendees "alice@co.com,bob@co.com"

# Delete event
$GAPI calendar delete EVENT_ID
```

:::warning
Час у Calendar **повинен** містити зсув часового поясу (наприклад, `-07:00`) або використовувати UTC (`Z`). Самостійні datetime, як `2026-03-01T10:00:00`, неоднозначні і будуть розглядатися як UTC.
:::

## Drive

```bash
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5
```

## Sheets

```bash
# Read a range
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write to a range
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

## Docs

```bash
$GAPI docs get DOC_ID
```

Повертає назву документа та повний текстовий вміст.

## Contacts

```bash
$GAPI contacts list --max 20
```

## Формат виводу

Усі команди повертають JSON. Ключові поля для кожного сервісу:

| Command | Fields |
|---------|--------|
| `gmail search` | `id`, `threadId`, `from`, `to`, `subject`, `date`, `snippet`, `labels` |
| `gmail get` | `id`, `threadId`, `from`, `to`, `subject`, `date`, `labels`, `body` |
| `gmail send/reply` | `status`, `id`, `threadId` |
| `calendar list` | `id`, `summary`, `start`, `end`, `location`, `description`, `htmlLink` |
| `calendar create` | `status`, `id`, `summary`, `htmlLink` |
| `drive search` | `id`, `name`, `mimeType`, `modifiedTime`, `webViewLink` |
| `contacts list` | `name`, `emails`, `phones` |
| `sheets get` | 2D array of cell values |

## Устранення проблем

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Запусти налаштування (попроси Hermes налаштувати Google Workspace) |
| `REFRESH_FAILED` | Токен відкликано — повторно пройди кроки авторизації |
| `HttpError 403: Insufficient Permission` | Не вистачає прав — відколи та повторно авторизуйся з потрібними сервісами |
| `HttpError 403: Access Not Configured` | API не ввімкнено в Google Cloud Console |
| `ModuleNotFoundError` | Запусти скрипт налаштування з `--install-deps` |