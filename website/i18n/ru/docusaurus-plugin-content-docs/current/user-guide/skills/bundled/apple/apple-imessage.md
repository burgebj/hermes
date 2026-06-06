---
title: "Imessage — Отправляй и получай iMessages/SMS через CLI imsg в macOS"
sidebar_label: "Imessage"
description: "Отправляй и получай iMessages/SMS через imsg CLI на macOS"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# iMessage

Отправляй и получай iMessage/SMS через CLI `imsg` на macOS.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/apple/imessage` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | macos |
| Tags | `iMessage`, `SMS`, `messaging`, `macOS`, `Apple` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# iMessage

Используй `imsg` для чтения и отправки iMessage/SMS через приложение Messages.app в macOS.

## Предварительные требования

- **macOS** с вошедшим в систему приложением Messages.app
- Установи: `brew install steipete/tap/imsg`
- Предоставь полный доступ к диску для терминала (System Settings → Privacy → Full Disk Access)
- Предоставь разрешение на автоматизацию для Messages.app, когда будет запрошено

## Когда использовать

- Пользователь просит отправить iMessage или SMS
- Чтение истории разговоров iMessage
- Просмотр последних чатов в Messages.app
- Отправка на номера телефонов или Apple ID

## Когда НЕ использовать

- Сообщения Telegram/Discord/Slack/WhatsApp → используй соответствующий шлюз‑канал
- Управление групповыми чатами (добавление/удаление участников) → не поддерживается
- Массовая рассылка → всегда сначала подтверждай с пользователем

## Быстрая справка

### Список чатов

```bash
imsg chats --limit 10 --json
```

### Просмотр истории

```bash
# By chat ID
imsg history --chat-id 1 --limit 20 --json

# With attachments info
imsg history --chat-id 1 --limit 20 --attachments --json
```

### Отправка сообщений

```bash
# Text only
imsg send --to "+14155551212" --text "Hello!"

# With attachment
imsg send --to "+14155551212" --text "Check this out" --file /path/to/image.jpg

# Force iMessage or SMS
imsg send --to "+14155551212" --text "Hi" --service imessage
imsg send --to "+14155551212" --text "Hi" --service sms
```

### Отслеживание новых сообщений

```bash
imsg watch --chat-id 1 --attachments
```

## Параметры сервиса

- `--service imessage` — принудительно использовать iMessage (требуется, чтобы получатель имел iMessage)
- `--service sms` — принудительно использовать SMS (зелёный пузырёк)
- `--service auto` — позволить Messages.app решить автоматически (по умолчанию)

## Правила

1. **Всегда подтверждай получателя и содержание сообщения** перед отправкой
2. **Никогда не отправляй на неизвестные номера** без явного одобрения пользователя
3. **Проверь существование путей к файлам** перед их вложением
4. **Не спамь** — ограничивай частоту отправки

## Пример рабочего процесса

User: "Text mom that I'll be late"

```bash
# 1. Find mom's chat
imsg chats --limit 20 --json | jq '.[] | select(.displayName | contains("Mom"))'

# 2. Confirm with user: "Found Mom at +1555123456. Send 'I'll be late' via iMessage?"

# 3. Send after confirmation
imsg send --to "+1555123456" --text "I'll be late"
```