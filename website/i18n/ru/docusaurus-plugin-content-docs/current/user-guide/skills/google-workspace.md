---
sidebar_position: 2
sidebar_label: "Google Workspace"
title: "Google Workspace — Gmail, Calendar, Drive, Sheets & Docs"
description: "Отправляй email, управляй событиями календаря, ищи в Drive, читай/пиши Sheets и получай доступ к Docs — всё через OAuth2‑аутентифицированные Google APIs"
---

# Навык Google Workspace

Интеграция Gmail, Calendar, Drive, Contacts, Sheets и Docs для Hermes. Использует OAuth2 с автоматическим обновлением токена. Предпочитает [Google Workspace CLI (`gws`)](https://github.com/nicholasgasior/gws), когда он доступен, для более широкого охвата, и в противном случае переходит к клиентским библиотекам Python от Google.

**Путь к навыку:** `skills/productivity/google-workspace/`

## Настройка

Настройка полностью управляется агентом — попроси Hermes настроить Google Workspace, и он проведёт тебя через каждый шаг. Последовательность:

1. **Создай проект Google Cloud** и включи необходимые API (Gmail, Calendar, Drive, Sheets, Docs, People)
2. **Создай учётные данные OAuth 2.0** (тип Desktop app) и скачай JSON‑файл client secret
3. **Авторизуйся** — Hermes генерирует URL для авторизации, ты подтверждаешь в браузере, затем вставляешь обратно URL перенаправления
4. **Готово** — токен будет автоматически обновляться с этого момента

:::tip Пользователи только электронной почты
Если нужен только email (без Calendar/Drive/Sheets), используй навык **himalaya** — он работает с паролем приложения Gmail и занимает 2 минуты. Проект Google Cloud не требуется.
:::

## Gmail

### Поиск

```bash
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"
```

Возвращает JSON с `id`, `from`, `subject`, `date`, `snippet` и `labels` для каждого сообщения.

### Чтение

```bash
$GAPI gmail get MESSAGE_ID
```

Возвращает полное тело сообщения в виде текста (предпочитает plain text, переходит к HTML).

### Отправка

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

### Пользовательский заголовок From

Флаг `--from` позволяет задать отображаемое имя отправителя в исходящих письмах. Это полезно, когда несколько агентов используют одну учётную запись Gmail, но ты хочешь, чтобы получатели видели разные имена:

```bash
# Agent 1
$GAPI gmail send --to client@co.com --subject "Research Summary" \
  --from '"Research Agent" <shared@company.com>' --body "..."

# Agent 2  
$GAPI gmail send --to client@co.com --subject "Code Review" \
  --from '"Code Assistant" <shared@company.com>' --body "..."
```

**Как это работает:** Значение `--from` устанавливается как заголовок RFC 5322 `From` в MIME‑сообщении. Gmail позволяет менять отображаемое имя для твоего аутентифицированного адреса без дополнительной конфигурации. Получатели видят пользовательское имя (например, «Research Agent»), а адрес электронной почты остаётся тем же.

**Важно:** Если ты указываешь *другой адрес электронной почты* в `--from` (не аутентифицированный аккаунт), Gmail требует, чтобы этот адрес был настроен как [псевдоним Send As](https://support.google.com/mail/answer/22370) в Настройки Gmail → Accounts → Send mail as.

Флаг `--from` работает как с `send`, так и с `reply`:

```bash
$GAPI gmail reply MESSAGE_ID \
  --from '"Support Bot" <shared@company.com>' --body "We're on it"
```

### Ответ

```bash
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
```

Автоматически формирует цепочку ответа (устанавливает заголовки `In-Reply-To` и `References`) и использует `threadId` оригинального сообщения.

### Метки

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
Время в Calendar **должно** включать смещение часового пояса (например, `-07:00`) или использовать UTC (`Z`). Даты без указания зоны, такие как `2026-03-01T10:00:00`, неоднозначны и будут интерпретированы как UTC.
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

Возвращает заголовок документа и его полный текстовый контент.

## Contacts

```bash
$GAPI contacts list --max 20
```

## Формат вывода

Все команды возвращают JSON. Ключевые поля для каждого сервиса:

| Команда | Поля |
|---------|------|
| `gmail search` | `id`, `threadId`, `from`, `to`, `subject`, `date`, `snippet`, `labels` |
| `gmail get` | `id`, `threadId`, `from`, `to`, `subject`, `date`, `labels`, `body` |
| `gmail send/reply` | `status`, `id`, `threadId` |
| `calendar list` | `id`, `summary`, `start`, `end`, `location`, `description`, `htmlLink` |
| `calendar create` | `status`, `id`, `summary`, `htmlLink` |
| `drive search` | `id`, `name`, `mimeType`, `modifiedTime`, `webViewLink` |
| `contacts list` | `name`, `emails`, `phones` |
| `sheets get` | 2‑мерный массив значений ячеек |

## Устранение неполадок

| Проблема | Решение |
|----------|---------|
| `NOT_AUTHENTICATED` | Запусти настройку (попроси Hermes настроить Google Workspace) |
| `REFRESH_FAILED` | Токен отозван — повтори шаги авторизации |
| `HttpError 403: Insufficient Permission` | Не хватает прав — отмени авторизацию и повторно предоставь нужные сервисы |
| `HttpError 403: Access Not Configured` | API не включён в консоли Google Cloud |
| `ModuleNotFoundError` | Запусти скрипт настройки с `--install-deps` |