---
title: "Github Auth — настройка аутентификации GitHub: HTTPS‑токены, SSH‑ключи, вход через gh CLI"
sidebar_label: "Github Auth"
description: "Настройка аутентификации GitHub: HTTPS‑токены, SSH‑ключи, вход через gh CLI"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Github Auth

Настройка аутентификации GitHub: HTTPS‑токены, SSH‑ключи, вход через `gh` CLI.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/github/github-auth` |
| Version | `1.1.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `GitHub`, `Authentication`, `Git`, `gh-cli`, `SSH`, `Setup` |
| Related skills | [`github-pr-workflow`](/docs/user-guide/skills/bundled/github/github-github-pr-workflow), [`github-code-review`](/docs/user-guide/skills/bundled/github/github-github-code-review), [`github-issues`](/docs/user-guide/skills/bundled/github/github-github-issues), [`github-repo-management`](/docs/user-guide/skills/bundled/github/github-github-repo-management) |

## Reference: full SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык включён.
:::

# GitHub Authentication Setup

Этот навык настраивает аутентификацию, чтобы агент мог работать с репозиториями GitHub, pull‑request’ами, задачами и CI. Рассматриваются два пути:

- **`git` (всегда доступен)** — использует HTTPS‑токены доступа или SSH‑ключи
- **`gh` CLI (если установлен)** — более богатый доступ к API GitHub с упрощённым процессом аутентификации

## Detection Flow

Когда пользователь просит тебя работать с GitHub, сначала выполни эту проверку:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Дерево решений:**
1. Если `gh auth status` показывает, что пользователь аутентифицирован → всё готово, используй `gh` для всего
2. Если `gh` установлен, но не аутентифицирован → используй метод «gh auth», описанный ниже
3. Если `gh` не установлен → используй метод «только git» (без `sudo`)

---

## Method 1: Git-Only Authentication (No gh, No sudo)

Работает на любой машине с установленным `git`. Не требуется доступ root.

### Option A: HTTPS with Personal Access Token (Recommended)

Самый переносимый способ — работает везде, без необходимости настраивать SSH.

**Шаг 1: Создай персональный токен доступа**

Попроси пользователя перейти по ссылке: **https://github.com/settings/tokens**

- Нажать «Generate new token (classic)»
- Дать токену имя, например `hermes-agent`
- Выбрать области доступа:
  - `repo` (полный доступ к репозиториям — чтение, запись, push, PR)
  - `workflow` (запуск и управление GitHub Actions)
  - `read:org` (если работают с репозиториями организаций)
- Установить срок действия (по умолчанию 90 дней)
- Скопировать токен — он больше не будет отображён

**Шаг 2: Настрой `git` для сохранения токена**

```bash
# Set up the credential helper to cache credentials
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

После однократного ввода учётных данных они сохраняются и будут использоваться при всех последующих операциях.

**Альтернатива: помощник‑кеш (учётные данные хранятся в памяти)**

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

**Альтернатива: задать токен непосредственно в URL удалённого репозитория (для отдельного репозитория)**

```bash
# Embed token in the remote URL (avoids credential prompts entirely)
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

**Шаг 3: Настрой идентификацию `git`**

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

**Шаг 4: Проверка**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

### Option B: SSH Key Authentication

Подходит пользователям, предпочитающим SSH или уже имеющим ключи.

**Шаг 1: Проверь наличие существующих SSH‑ключей**

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

**Шаг 2: Сгенерируй ключ, если он отсутствует**

```bash
# Generate an ed25519 key (modern, secure, fast)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# Display the public key for them to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

Попроси пользователя добавить публичный ключ по адресу: **https://github.com/settings/keys**
- Нажать «New SSH key»
- Вставить содержимое публичного ключа
- Дать ему название, например `hermes-agent‑<machine-name>`

**Шаг 3: Проверь соединение**

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Шаг 4: Настрой `git` использовать SSH для GitHub**

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

**Шаг 5: Настрой идентификацию `git`**

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

---

## Method 2: gh CLI Authentication

Если установлен `gh`, он управляет как доступом к API, так и учётными данными `git` в одном шаге.

### Interactive Browser Login (Desktop)

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

### Token-Based Login (Headless / SSH Servers)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

### Verify

```bash
gh auth status
```

---

## Using the GitHub API Without gh

Когда `gh` недоступен, всё равно можно обращаться к полному API GitHub через `curl`, используя персональный токен доступа. Именно так реализованы резервные варианты в остальных навыках GitHub.

### Setting the Token for API Calls

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

### Extracting the Token from Git Credentials

Если учётные данные `git` уже настроены (через `credential.helper store`), токен можно извлечь:

```bash
# Read from git credential store
grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
```

### Helper: Detect Auth Method

Используй этот шаблон в начале любого рабочего процесса с GitHub:

```bash
# Try gh first, fall back to git + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=curl"
elif [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
  echo "AUTH_METHOD=curl"
elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  export GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
  echo "AUTH_METHOD=curl"
else
  echo "AUTH_METHOD=none"
  echo "Need to set up authentication first"
fi
```

---

## Troubleshooting

| Проблема | Решение |
|---------|----------|
| `git push` запрашивает пароль | GitHub отключил аутентификацию паролем. Используй персональный токен доступа в качестве пароля или переключись на SSH |
| `remote: Permission to X denied` | Токен может не иметь области `repo` — сгенерируй новый с нужными правами |
| `fatal: Authentication failed` | Сохранённые учётные данные могут быть устаревшими — выполни `git credential reject` и аутентифицируйся заново |
| `ssh: connect to host github.com port 22: Connection refused` | Попробуй SSH через HTTPS‑порт: добавь в `~/.ssh/config` блок `Host github.com` с `Port 443` и `Hostname ssh.github.com` |
| Учётные данные не сохраняются | Проверь `git config --global credential.helper` — должно быть `store` или `cache` |
| Несколько аккаунтов GitHub | Используй SSH с разными ключами и алиасами хостов в `~/.ssh/config`, либо задавай URL с токеном для каждого репозитория |
| `gh: command not found` + нет `sudo` | Используй метод 1 «только git» — установка не требуется |