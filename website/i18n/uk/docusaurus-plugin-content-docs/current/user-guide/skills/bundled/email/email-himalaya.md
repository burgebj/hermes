---
title: "Himalaya — Himalaya CLI: електронна пошта IMAP/SMTP з терміналу"
sidebar_label: "Himalaya"
description: "Himalaya CLI: електронна пошта IMAP/SMTP з терміналу"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Himalaya

Himalaya CLI: IMAP/SMTP email from terminal.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/email/himalaya` |
| Version | `1.1.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Email`, `IMAP`, `SMTP`, `CLI`, `Communication` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Himalaya Email CLI

Himalaya — це CLI‑клієнт електронної пошти, який дозволяє керувати листами з терміналу за допомогою бекендів IMAP, SMTP, Notmuch або Sendmail.

## Довідкові матеріали

- `references/configuration.md` (налаштування файлу конфігурації + автентифікація IMAP/SMTP)
- `references/message-composition.md` (синтаксис MML для створення листів)

## Передумови

1. Himalaya CLI встановлений (`himalaya --version` для перевірки)
2. Файл конфігурації за адресою `~/.config/himalaya/config.toml`
3. Налаштовані облікові дані IMAP/SMTP (пароль зберігається безпечно)

### Встановлення

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Налаштування конфігурації

Запусти інтерактивний майстер для створення облікового запису:

```bash
himalaya account configure
```

Або створіть `~/.config/himalaya/config.toml` вручну:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **Зверни увагу на синтаксис псевдонімів.** У документації до версії < v1.2.0 > використовувався підрозділ `[accounts.NAME.folder.alias]` (однина `alias`). У версії v1.2.0 ця форма тихо ігнорується — TOML парситься, але резолвер псевдонімів її не читає, тому кожен запит переходить до канонічного імені. У Gmail це означає, що збереження у «Sent» не вдається *після* успішної доставки SMTP, і `himalaya message send` завершується з кодом помилки. Будь‑який виклик (агент, скрипт, користувач), який повторює спробу за цим кодом, повторно виконає всю відправку — включно з SMTP — що призведе до дублювання листів одержувачам. Завжди використовуйте `folder.aliases.X` (множина, крапкові ключі, безпосередньо під `[accounts.NAME]`).

## Примітки щодо інтеграції з Hermes

- **Читання, перелік, пошук, переміщення, видалення** працюють безпосередньо через інструмент у терміналі
- **Створення/відповідь/пересилання** — рекомендується передавати вхідні дані через конвеєр (`cat << EOF | himalaya template send`) для надійності. Інтерактивний режим `$EDITOR` працює з `pty=true` + фон + інструмент процесу, але вимагає знання редактора та його команд
- Використовуйте `--output json` для структурованого виводу, який легше парсити програмно
- Майстер `himalaya account configure` вимагає інтерактивного вводу — використовуйте PTY‑режим: `terminal(command="himalaya account configure", pty=true)`

## Типові операції

### Перелік папок

```bash
himalaya folder list
```

### Перелік листів

Перелік листів у **INBOX** (за замовчуванням):

```bash
himalaya envelope list
```

Перелік листів у конкретній папці:

```bash
himalaya envelope list --folder "Sent"
```

Перелік з пагінацією:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Пошук листів

```bash
himalaya envelope list from john@example.com subject meeting
```

### Читання листа

Читання листа за ID (показує простий текст):

```bash
himalaya message read 42
```

Експорт сирого MIME:

```bash
himalaya message export 42 --full
```

### Відповідь на лист

Щоб відповісти неінтерактивно з Hermes, прочитай оригінальне повідомлення, сформуй відповідь і передай її через конвеєр:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Або сформуй відповідь вручну:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Відповідь всім (інтерактивно — потрібен `$EDITOR`, використай підхід з шаблоном вище замість цього):

```bash
himalaya message reply 42 --all
```

### Пересилання листа

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Написання нового листа

**Неінтерактивно (використовуй це з Hermes)** — передай повідомлення через stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Або з прапорцем заголовків:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Примітка: `himalaya message write` без переданих даних відкриває `$EDITOR`. Це працює з `pty=true` + фоновим режимом, але передача через конвеєр простіша та надійніша.

### Переміщення/копіювання листів

Перемістити у папку:

```bash
himalaya message move 42 "Archive"
```

Скопіювати у папку:

```bash
himalaya message copy 42 "Important"
```

### Видалення листа

```bash
himalaya message delete 42
```

### Керування прапорцями

Додати прапорець:

```bash
himalaya flag add 42 --flag seen
```

Видалити прапорець:

```bash
himalaya flag remove 42 --flag seen
```

## Кілька облікових записів

Перелік облікових записів:

```bash
himalaya account list
```

Використати конкретний обліковий запис:

```bash
himalaya --account work envelope list
```

## Вкладення

Зберегти вкладення з повідомлення:

```bash
himalaya attachment download 42
```

Зберегти у конкретну директорію:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Формати виводу

Більшість команд підтримують `--output` для структурованого виводу:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Налагодження

Увімкнути журналювання налагодження:

```bash
RUST_LOG=debug himalaya envelope list
```

Повне трасування з backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Поради

- Використовуйте `himalaya --help` або `himalaya <command> --help` для детального опису.
- Ідентифікатори листів відносні до поточної папки; після зміни папки перечитуйте список.
- Для створення багатих листів з вкладеннями використовуйте синтаксис MML (див. `references/message-composition.md`).
- Зберігайте паролі безпечно за допомогою `pass`, системного сховища ключів або команди, що виводить пароль.