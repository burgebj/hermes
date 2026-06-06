---
title: "Imessage — Надсилай та отримуй iMessages/SMS за допомогою CLI imsg у macOS"
sidebar_label: "Imessage"
description: "Надсилати та отримувати iMessages/SMS за допомогою imsg CLI на macOS"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# iMessage

Надсилай та отримуй iMessages/SMS за допомогою CLI `imsg` на macOS.

## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/apple/imessage` |
| Версія | `1.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Платформи | macos |
| Теги | `iMessage`, `SMS`, `messaging`, `macOS`, `Apple` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# iMessage

Використовуй `imsg` для читання та надсилання iMessage/SMS через macOS Messages.app.

## Передумови

- **macOS** з підключеним Messages.app
- Встановити: `brew install steipete/tap/imsg`
- Надати Full Disk Access для терміналу (System Settings → Privacy → Full Disk Access)
- Надати дозвіл Automation для Messages.app, коли буде запитано

## Коли використовувати

- Користувач просить надіслати iMessage або текстове повідомлення
- Читання історії розмов iMessage
- Перегляд останніх чатів у Messages.app
- Надсилання на телефонні номери або Apple ID

## Коли НЕ використовувати

- Повідомлення Telegram/Discord/Slack/WhatsApp → використай відповідний канал шлюзу
- Керування груповими чатами (додавання/видалення учасників) → не підтримується
- Масове надсилання повідомлень → спочатку завжди підтверджуй з користувачем

## Швидка довідка

### Список чатів

```bash
imsg chats --limit 10 --json
```

### Перегляд історії

```bash
# By chat ID
imsg history --chat-id 1 --limit 20 --json

# With attachments info
imsg history --chat-id 1 --limit 20 --attachments --json
```

### Надсилання повідомлень

```bash
# Text only
imsg send --to "+14155551212" --text "Hello!"

# With attachment
imsg send --to "+14155551212" --text "Check this out" --file /path/to/image.jpg

# Force iMessage or SMS
imsg send --to "+14155551212" --text "Hi" --service imessage
imsg send --to "+14155551212" --text "Hi" --service sms
```

### Спостереження за новими повідомленнями

```bash
imsg watch --chat-id 1 --attachments
```

## Параметри сервісу

- `--service imessage` — Примусово iMessage (вимагає, щоб одержувач мав iMessage)
- `--service sms` — Примусово SMS (зелений балон)
- `--service auto` — Дозволити Messages.app вирішити (за замовчуванням)

## Правила

1. **Завжди підтверджуй одержувача та вміст повідомлення** перед надсиланням
2. **Ніколи не надсилай на невідомі номери** без явного схвалення користувачем
3. **Перевіряй існування шляхів до файлів** перед прикріпленням
4. **Не спам** — обмежуй частоту надсилань

## Приклад робочого процесу

Користувач: "Напиши мамі, що я запізнюся"

```bash
# 1. Find mom's chat
imsg chats --limit 20 --json | jq '.[] | select(.displayName | contains("Mom"))'

# 2. Confirm with user: "Found Mom at +1555123456. Send 'I'll be late' via iMessage?"

# 3. Send after confirmation
imsg send --to "+1555123456" --text "I'll be late"
```