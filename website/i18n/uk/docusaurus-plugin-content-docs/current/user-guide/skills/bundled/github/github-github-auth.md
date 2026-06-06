---
title: "Налаштування аутентифікації Github — GitHub auth: HTTPS‑токени, SSH‑ключі, вхід через gh CLI"
sidebar_label: "Github Auth"
description: "Налаштування автентифікації GitHub: HTTPS‑токени, SSH‑ключі, вхід gh CLI"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Github Auth

GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Налаштування автентифікації GitHub

Ця навичка налаштовує автентифікацію, щоб агент міг працювати з репозиторіями GitHub, PR, issue та CI. Вона охоплює два шляхи:

- **`git` (завжди доступний)** — використовує HTTPS personal access tokens або SSH‑ключі
- **`gh` CLI (якщо встановлено)** — розширений доступ до GitHub API зі спрощеним процесом автентифікації

## Потік виявлення

Коли користувач просить тебе працювати з GitHub, спочатку виконай цю перевірку:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Дерево рішень:**
1. Якщо `gh auth status` показує, що автентифіковано → все гаразд, використовуй `gh` для всього
2. Якщо `gh` встановлено, але не автентифіковано → використай метод «gh auth», описаний нижче
3. Якщо `gh` не встановлено → використай метод «git‑only», описаний нижче (без sudo)

---

## Метод 1: Автентифікація лише через Git (без gh, без sudo)

Працює на будь‑якій машині з встановленим `git`. Не потрібен доступ root.

### Варіант A: HTTPS з Personal Access Token (рекомендовано)

Найпортативніший метод — працює скрізь, без налаштувань SSH.

**Крок 1: Створи personal access token**

Попроси користувача перейти за посиланням: **https://github.com/settings/tokens**

- Натисни «Generate new token (classic)»
- Дай йому назву, наприклад «hermes-agent»
- Вибери scopes:
  - `repo` (повний доступ до репозиторію — читання, запис, push, PR)
  - `workflow` (тригер та керування GitHub Actions)
  - `read:org` (якщо працюєш з репозиторіями організацій)
- Встанови термін дії (90 днів — хороший варіант)
- Скопіюй токен — його більше не буде показано

**Крок 2: Налаштуй git для збереження токену**

```bash
# Set up the credential helper to cache credentials
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

Після одноразового введення облікових даних вони зберігаються і повторно використовуються для всіх майбутніх операцій.

**Альтернатива: helper кешу (облікові дані зникають з пам’яті)**

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

**Альтернатива: задати токен безпосередньо в URL віддаленого репозиторію (для окремого репо)**

```bash
# Embed token in the remote URL (avoids credential prompts entirely)
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

**Крок 3: Налаштуй ідентифікацію git**

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

**Крок 4: Перевірка**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

### Варіант B: Автентифікація SSH‑ключем

Підходить користувачам, які віддають перевагу SSH або вже мають налаштовані ключі.

**Крок 1: Перевір наявність існуючих SSH‑ключів**

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

**Крок 2: Згенеруй ключ, якщо потрібно**

```bash
# Generate an ed25519 key (modern, secure, fast)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# Display the public key for them to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

Попроси користувача додати публічний ключ за адресою: **https://github.com/settings/keys**
- Натисни «New SSH key»
- Встав вміст публічного ключа
- Дай йому назву, наприклад «hermes-agent‑<machine-name>»

**Крок 3: Перевір з’єднання**

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Крок 4: Налаштуй git для використання SSH з GitHub**

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

**Крок 5: Налаштуй ідентифікацію git**

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

---

## Метод 2: Автентифікація через gh CLI

Якщо `gh` встановлено, він обробляє і доступ до API, і git‑облікові дані в одному кроці.

### Інтерактивний вхід у браузері (Desktop)

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

### Вхід за токеном (Headless / SSH‑сервери)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

### Перевірка

```bash
gh auth status
```

---

## Використання GitHub API без gh

Коли `gh` недоступний, можна все ж отримати доступ до повного GitHub API за допомогою `curl` і personal access token. Так саме інші навички GitHub реалізують свої запасні варіанти.

### Встановлення токену для API‑запитів

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

### Витяг токену з git‑облікових даних

Якщо git‑облікові дані вже налаштовано (через `credential.helper store`), токен можна витягти:

```bash
# Read from git credential store
grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
```

### Допоміжний інструмент: визначення методу автентифікації

Використовуй цей шаблон на початку будь‑якого GitHub‑workflow:

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

## Устранення проблем

| Проблема | Рішення |
|---------|----------|
| `git push` запитує пароль | GitHub вимкнув автентифікацію паролем. Використай personal access token як пароль або перейди на SSH |
| `remote: Permission to X denied` | Токен може не мати scope `repo` — згенеруй новий з правильними правами |
| `fatal: Authentication failed` | Кешовані облікові дані можуть бути застарілими — виконай `git credential reject`, потім повторно автентифікуйся |
| `ssh: connect to host github.com port 22: Connection refused` | Спробуй SSH через HTTPS‑порт: додай у `~/.ssh/config` `Host github.com` з `Port 443` та `Hostname ssh.github.com` |
| Облікові дані не зберігаються | Перевір `git config --global credential.helper` — має бути `store` або `cache` |
| Кілька облікових записів GitHub | Використай SSH з різними ключами per‑host alias у `~/.ssh/config`, або URL‑з‑токеном per‑repo |
| `gh: command not found` + без sudo | Використай метод 1 (git‑only) — встановлення не потрібне |