---
title: "1Password — Налаштуй та використай 1Password CLI (op)"
sidebar_label: "1Password"
description: "Налаштуй і використай 1Password CLI (op)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# 1Password

Налаштуй та використай 1Password CLI (`op`). Використовуй під час встановлення CLI, увімкнення інтеграції з десктоп‑додатком, входу в обліковий запис та читання/вставки секретів для команд.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/security/1password` |
| Path | `optional-skills/security/1password` |
| Version | `1.0.0` |
| Author | arceus77-7, enhanced by Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `security`, `secrets`, `1password`, `op`, `cli` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# 1Password CLI

Використовуй цю навичку, коли користувач хоче керувати секретами через 1Password замість відкритих змінних середовища або файлів.

## Вимоги

- Обліковий запис 1Password
- 1Password CLI (`op`) встановлений
- Один з: інтеграція з десктоп‑додатком, токен сервісного облікового запису (`OP_SERVICE_ACCOUNT_TOKEN`) або Connect‑сервер
- `tmux` доступний для стабільних автентифікованих сесій під час викликів Hermes у терміналі (лише потік десктоп‑додатку)

## Коли використовувати

- Встановити або налаштувати 1Password CLI
- Увійти за допомогою `op signin`
- Читати посилання на секрети, наприклад `op://Vault/Item/field`
- Вставляти секрети у конфігурації/шаблони за допомогою `op inject`
- Запускати команди з секретними змінними середовища через `op run`

## Методи автентифікації

### Сервісний обліковий запис (рекомендовано для Hermes)

Встанови `OP_SERVICE_ACCOUNT_TOKEN` у `~/.hermes/.env` (навичка запросить його під час першого завантаження).
Не потрібен десктоп‑додаток. Підтримуються `op read`, `op inject`, `op run`.

```bash
export OP_SERVICE_ACCOUNT_TOKEN="your-token-here"
op whoami  # verify — should show Type: SERVICE_ACCOUNT
```

### Інтеграція з десктоп‑додатком (інтерактивно)

1. Увімкни в десктоп‑додатку 1Password: Settings → Developer → Integrate with 1Password CLI
2. Переконайся, що додаток розблоковано
3. Запусти `op signin` і підтверди біометричний запит

### Connect‑сервер (самостійний хостинг)

```bash
export OP_CONNECT_HOST="http://localhost:8080"
export OP_CONNECT_TOKEN="your-connect-token"
```

## Налаштування

1. Встанови CLI:

```bash
# macOS
brew install 1password-cli

# Linux (official package/install docs)
# See references/get-started.md for distro-specific links.

# Windows (winget)
winget install AgileBits.1Password.CLI
```

2. Перевір:

```bash
op --version
```

3. Обери один із методів автентифікації вище та налаштуй його.

## Шаблон виконання Hermes (потік десктоп‑додатку)

Команди терміналу Hermes за замовчуванням не‑інтерактивні і можуть втрачати контекст автентифікації між викликами.
Для надійного використання `op` з інтеграцією десктоп‑додатку запускай вхід та операції з секретами всередині окремої сесії `tmux`.

Примітка: це НЕ потрібно, коли використовується `OP_SERVICE_ACCOUNT_TOKEN` — токен зберігається між викликами терміналу автоматично.

```bash
SOCKET_DIR="${TMPDIR:-/tmp}/hermes-tmux-sockets"
mkdir -p "$SOCKET_DIR"
SOCKET="$SOCKET_DIR/hermes-op.sock"
SESSION="op-auth-$(date +%Y%m%d-%H%M%S)"

tmux -S "$SOCKET" new -d -s "$SESSION" -n shell

# Sign in (approve in desktop app when prompted)
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- "eval \"\$(op signin --account my.1password.com)\"" Enter

# Verify auth
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- "op whoami" Enter

# Example read
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- "op read 'op://Private/Npmjs/one-time password?attribute=otp'" Enter

# Capture output when needed
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -200

# Cleanup
tmux -S "$SOCKET" kill-session -t "$SESSION"
```

## Типові операції

### Читання секрету

```bash
op read "op://app-prod/db/password"
```

### Отримання OTP

```bash
op read "op://app-prod/npm/one-time password?attribute=otp"
```

### Вставка у шаблон

```bash
echo "db_password: {{ op://app-prod/db/password }}" | op inject
```

### Запуск команди з секретною змінною середовища

```bash
export DB_PASSWORD="op://app-prod/db/password"
op run -- sh -c '[ -n "$DB_PASSWORD" ] && echo "DB_PASSWORD is set" || echo "DB_PASSWORD missing"'
```

## Обмеження

- Ніколи не виводь необроблені секрети користувачеві, якщо він явно не запросив значення.
- Віддавай перевагу `op run` / `op inject` замість запису секретів у файли.
- Якщо команда повертає помилку «account is not signed in», запусти `op signin` знову в тій самій сесії `tmux`.
- Якщо інтеграція з десктоп‑додатком недоступна (headless/CI), використай потік токену сервісного облікового запису.

## Примітка щодо CI / безголового режиму

Для не‑інтерактивного використання автентифікуйся за допомогою `OP_SERVICE_ACCOUNT_TOKEN` і уникай інтерактивного `op signin`.
Сервісні облікові записи вимагають CLI v2.18.0+.

## Посилання

- `references/get-started.md`
- `references/cli-examples.md`
- https://developer.1password.com/docs/cli/
- https://developer.1password.com/docs/service-accounts/