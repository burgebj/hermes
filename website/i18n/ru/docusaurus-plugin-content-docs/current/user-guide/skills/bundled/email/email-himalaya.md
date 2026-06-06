---
title: "Himalaya — Himalaya CLI: IMAP/SMTP email из терминала"
sidebar_label: "Himalaya"
description: "Himalaya CLI: электронная почта IMAP/SMTP из терминала"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Himalaya

Himalaya CLI: IMAP/SMTP email from terminal.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/email/himalaya` |
| Version | `1.1.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Email`, `IMAP`, `SMTP`, `CLI`, `Communication` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# Himalaya Email CLI

Himalaya — это CLI‑клиент электронной почты, позволяющий управлять письмами из терминала с помощью бекендов IMAP, SMTP, Notmuch или Sendmail.

## Ссылки

- `references/configuration.md` (настройка конфигурационного файла + аутентификация IMAP/SMTP)
- `references/message-composition.md` (синтаксис MML для составления писем)

## Предварительные требования

1. Установлен Himalaya CLI (`himalaya --version` для проверки)
2. Файл конфигурации в `~/.config/himalaya/config.toml`
3. Настроены учётные данные IMAP/SMTP (пароль хранится безопасно)

### Установка

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Настройка конфигурации

Запусти интерактивный мастер для настройки учётной записи:

```bash
himalaya account configure
```

Или создай `~/.config/himalaya/config.toml` вручную:

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

> **Внимание к синтаксису alias.** В документации до версии 1.2.0 использовался подраздел `[accounts.NAME.folder.alias]` (единственное `alias`). Начиная с v1.2.0 эта форма игнорируется — TOML парсится корректно, но разрешатель alias её не читает, поэтому каждый поиск переходит к каноничному имени. В Gmail это приводит к тому, что сохранение в Sent не происходит *после* успешной доставки по SMTP, и `himalaya message send` завершается с ненулевым кодом. Любой вызывающий (агент, скрипт, пользователь), который повторно пытается при этом коде выхода, повторно выполнит всю отправку — включая SMTP — что создаст дублирующие письма получателям. Всегда используй `folder.aliases.X` (множественное, через точку, непосредственно под `[accounts.NAME]`).

## Примечания по интеграции с Hermes

- **Чтение, перечисление, поиск, перемещение, удаление** работают напрямую через терминальный инструмент
- **Создание/ответ/пересылка** — рекомендуется использовать ввод через конвейер (`cat << EOF | himalaya template send`) для надёжности. Интерактивный режим `$EDITOR` работает с `pty=true` + background + process tool, но требует знать редактор и его команды
- Используй `--output json` для структурированного вывода, удобного для программного парсинга
- Мастер `himalaya account configure` требует интерактивного ввода — используй PTY‑режим: `terminal(command="himalaya account configure", pty=true)`

## Часто используемые операции

### Список папок

```bash
himalaya folder list
```

### Список писем

Список писем в INBOX (по умолчанию):

```bash
himalaya envelope list
```

Список писем в конкретной папке:

```bash
himalaya envelope list --folder "Sent"
```

Список с постраничным выводом:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Поиск писем

```bash
himalaya envelope list from john@example.com subject meeting
```

### Чтение письма

Чтение письма по ID (отображает обычный текст):

```bash
himalaya message read 42
```

Экспортировать сырой MIME:

```bash
himalaya message export 42 --full
```

### Ответ на письмо

Для неинтерактивного ответа из Hermes прочитай оригинальное сообщение, составь ответ и передай его через конвейер:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Или собери ответ вручную:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Ответ всем (интерактивный — нужен $EDITOR, вместо этого используй подход с шаблоном выше):

```bash
himalaya message reply 42 --all
```

### Переслать письмо

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Написать новое письмо

**Неинтерактивное (используй из Hermes)** — передай сообщение через stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Или с флагом заголовков:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Примечание: `himalaya message write` без ввода через конвейер открывает `$EDITOR`. Это работает с `pty=true` + background mode, но передача через конвейер проще и надёжнее.

### Переместить/Скопировать письма

Переместить в папку:

```bash
himalaya message move 42 "Archive"
```

Скопировать в папку:

```bash
himalaya message copy 42 "Important"
```

### Удалить письмо

```bash
himalaya message delete 42
```

### Управление флагами

Добавить флаг:

```bash
himalaya flag add 42 --flag seen
```

Удалить флаг:

```bash
himalaya flag remove 42 --flag seen
```

## Несколько учётных записей

Список учётных записей:

```bash
himalaya account list
```

Использовать конкретную учётную запись:

```bash
himalaya --account work envelope list
```

## Вложения

Сохранить вложения из сообщения:

```bash
himalaya attachment download 42
```

Сохранить в конкретный каталог:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Форматы вывода

Большинство команд поддерживают `--output` для структурированного вывода:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Отладка

Включить журнал отладки:

```bash
RUST_LOG=debug himalaya envelope list
```

Полный трасс с backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Советы

- Используй `himalaya --help` или `himalaya <command> --help` для подробного справочника.
- Идентификаторы сообщений относительны текущей папки; после смены папки перечитай список.
- Для создания богатых писем с вложениями используй синтаксис MML (см. `references/message-composition.md`).
- Храни пароли безопасно, используя `pass`, системный keyring или команду, выводящую пароль.