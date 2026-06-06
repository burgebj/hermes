---
title: "1Password — настройка и использование 1Password CLI (op)"
sidebar_label: "1Password"
description: "Настрой и используй 1Password CLI (op)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# 1Password

Настрой и используй 1Password CLI (`op`). Применяй при установке CLI, включении интеграции с настольным приложением, входе в аккаунт и чтении/внедрении секретов для команд.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/security/1password` |
| Path | `optional-skills/security/1password` |
| Version | `1.0.0` |
| Author | arceus77-7, enhanced by Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `security`, `secrets`, `1password`, `op`, `cli` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# 1Password CLI

Используй этот навык, когда пользователь хочет управлять секретами через 1Password вместо открытых переменных окружения или файлов.

## Требования

- Аккаунт 1Password
- Установленный 1Password CLI (`op`)
- Один из вариантов: интеграция с настольным приложением, токен сервисного аккаунта (`OP_SERVICE_ACCOUNT_TOKEN`) или сервер Connect
- `tmux` доступен для стабильных аутентифицированных сессий во время вызовов терминала Hermes (только поток интеграции с настольным приложением)

## Когда использовать

- Установить или настроить 1Password CLI
- Войти с помощью `op signin`
- Читать ссылки на секреты, например `op://Vault/Item/field`
- Внедрять секреты в конфиги/шаблоны с помощью `op inject`
- Выполнять команды с секретными переменными окружения через `op run`

## Методы аутентификации

### Сервисный аккаунт (рекомендовано для Hermes)

Установи `OP_SERVICE_ACCOUNT_TOKEN` в `~/.hermes/.env` (навык запросит его при первой загрузке).
Не требуется настольное приложение. Поддерживает `op read`, `op inject`, `op run`.

```bash
export OP_SERVICE_ACCOUNT_TOKEN="your-token-here"
op whoami  # verify — should show Type: SERVICE_ACCOUNT
```

### Интеграция с настольным приложением (интерактивно)

1. Включи в настольном приложении 1Password: Settings → Developer → Integrate with 1Password CLI
2. Убедись, что приложение разблокировано
3. Выполни `op signin` и одобри биометрический запрос

### Сервер Connect (самостоятельный хостинг)

```bash
export OP_CONNECT_HOST="http://localhost:8080"
export OP_CONNECT_TOKEN="your-connect-token"
```

## Настройка

1. Установи CLI:

```bash
# macOS
brew install 1password-cli

# Linux (official package/install docs)
# See references/get-started.md for distro-specific links.

# Windows (winget)
winget install AgileBits.1Password.CLI
```

2. Проверь:

```bash
op --version
```

3. Выбери один из методов аутентификации выше и настрой его.

## Шаблон выполнения Hermes (поток настольного приложения)

Команды терминала Hermes по умолчанию неинтерактивны и могут терять контекст аутентификации между вызовами.
Для надёжного использования `op` с интеграцией настольного приложения запускай вход и операции с секретами внутри отдельной tmux‑сессии.

Примечание: Это НЕ требуется при использовании `OP_SERVICE_ACCOUNT_TOKEN` — токен сохраняется между вызовами терминала автоматически.

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

## Часто используемые операции

### Чтение секрета

```bash
op read "op://app-prod/db/password"
```

### Получение OTP

```bash
op read "op://app-prod/npm/one-time password?attribute=otp"
```

### Внедрение в шаблон

```bash
echo "db_password: {{ op://app-prod/db/password }}" | op inject
```

### Выполнение команды с секретной переменной окружения

```bash
export DB_PASSWORD="op://app-prod/db/password"
op run -- sh -c '[ -n "$DB_PASSWORD" ] && echo "DB_PASSWORD is set" || echo "DB_PASSWORD missing"'
```

## Ограничения

- Никогда не выводи сырые секреты пользователю, если он явно не запросил значение.
- Предпочитай `op run` / `op inject` вместо записи секретов в файлы.
- Если команда завершилась ошибкой «account is not signed in», снова выполни `op signin` в той же tmux‑сессии.
- Если интеграция с настольным приложением недоступна (headless/CI), используй поток токена сервисного аккаунта.

## Примечание для CI / безголового режима

Для неинтерактивного использования аутентифицируйся с помощью `OP_SERVICE_ACCOUNT_TOKEN` и избегай интерактивного `op signin`.
Сервисные аккаунты требуют CLI версии 2.18.0+.

## Ссылки

- `references/get-started.md`
- `references/cli-examples.md`
- https://developer.1password.com/docs/cli/
- https://developer.1password.com/docs/service-accounts/