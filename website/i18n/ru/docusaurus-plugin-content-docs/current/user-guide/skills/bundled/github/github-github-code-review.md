---
title: "Github Code Review — Обзор PR: диффы, встроенные комментарии через gh или REST"
sidebar_label: "Github Code Review"
description: "Ревью PR: диффы, встроенные комментарии через gh или REST"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Обзор кода в GitHub

Обзор PR: диффы, встроенные комментарии через gh или REST.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/github/github-code-review` |
| Version | `1.1.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `GitHub`, `Code-Review`, `Pull-Requests`, `Git`, `Quality` |
| Related skills | [`github-auth`](/docs/user-guide/skills/bundled/github/github-github-auth), [`github-pr-workflow`](/docs/user-guide/skills/bundled/github/github-github-pr-workflow) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# Обзор кода в GitHub

Выполняй обзоры кода на локальных изменениях перед пушем или проверяй открытые PR на GitHub. Большая часть этого навыка использует обычный `git` — разделение `gh`/`curl` имеет значение только для взаимодействий уровня PR.

## Предварительные требования

- Авторизован в GitHub (см. навык `github-auth`)
- Находится внутри репозитория `git`

### Настройка (для взаимодействий с PR)

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. Обзор локальных изменений (до пуша)

Это чистый `git` — работает везде, API не требуется.

### Получить дифф

```bash
# Staged changes (what would be committed)
git diff --staged

# All changes vs main (what a PR would contain)
git diff main...HEAD

# File names only
git diff main...HEAD --name-only

# Stat summary (insertions/deletions per file)
git diff main...HEAD --stat
```

### Стратегия обзора

1. **Сначала получи общую картину:**

   ```bash
git diff main...HEAD --stat
git log main..HEAD --oneline
```

2. **Обзор файл за файлом** — используй `read_file` для изменённых файлов, чтобы получить полный контекст, и дифф, чтобы увидеть, что изменилось:

   ```bash
git diff main...HEAD -- src/auth/login.py
```

3. **Проверь типичные проблемы:**

   ```bash
# Debug statements, TODOs, console.logs left behind
git diff main...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|HACK\|XXX\|debugger"

# Large files accidentally staged
git diff main...HEAD --stat | sort -t'|' -k2 -rn | head -10

# Secrets or credential patterns
git diff main...HEAD | grep -in "password\|secret\|api_key\|token.*=\|private_key"

# Merge conflict markers
git diff main...HEAD | grep -n "<<<<<<\|>>>>>>\|======="
```

4. **Представь структурированную обратную связь** пользователю.

### Формат вывода обзора

При обзоре локальных изменений представляй результаты в следующей структуре:

```
## Code Review Summary

### Critical
- **src/auth.py:45** — SQL injection: user input passed directly to query.
  Suggestion: Use parameterized queries.

### Warnings
- **src/models/user.py:23** — Password stored in plaintext. Use bcrypt or argon2.
- **src/api/routes.py:112** — No rate limiting on login endpoint.

### Suggestions
- **src/utils/helpers.py:8** — Duplicates logic in `src/core/utils.py:34`. Consolidate.
- **tests/test_auth.py** — Missing edge case: expired token test.

### Looks Good
- Clean separation of concerns in the middleware layer
- Good test coverage for the happy path
```

---

## 2. Обзор Pull Request на GitHub

### Просмотр деталей PR

**С помощью gh:**

```bash
gh pr view 123
gh pr diff 123
gh pr diff 123 --name-only
```

**С помощью git + curl:**

```bash
PR_NUMBER=123

# Get PR details
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "
import sys, json
pr = json.load(sys.stdin)
print(f\"Title: {pr['title']}\")
print(f\"Author: {pr['user']['login']}\")
print(f\"Branch: {pr['head']['ref']} -> {pr['base']['ref']}\")
print(f\"State: {pr['state']}\")
print(f\"Body:\n{pr['body']}\")"

# List changed files
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/files \
  | python3 -c "
import sys, json
for f in json.load(sys.stdin):
    print(f\"{f['status']:10} +{f['additions']:-4} -{f['deletions']:-4}  {f['filename']}\")"
```

### Выгрузка PR локально для полного обзора

Это работает обычным `git` — `gh` не нужен:

```bash
# Fetch the PR branch and check it out
git fetch origin pull/123/head:pr-123
git checkout pr-123

# Now you can use read_file, search_files, run tests, etc.

# View diff against the base branch
git diff main...pr-123
```

**С gh (быстрый способ):**

```bash
gh pr checkout 123
```

### Оставить комментарии к PR

**Общий комментарий к PR — с gh:**

```bash
gh pr comment 123 --body "Overall looks good, a few suggestions below."
```

**Общий комментарий к PR — с curl:**

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/issues/$PR_NUMBER/comments \
  -d '{"body": "Overall looks good, a few suggestions below."}'
```

### Оставить встроенные (inline) комментарии

**Один встроенный комментарий — с gh (через API):**

```bash
HEAD_SHA=$(gh pr view 123 --json headRefOid --jq '.headRefOid')

gh api repos/$OWNER/$REPO/pulls/123/comments \
  --method POST \
  -f body="This could be simplified with a list comprehension." \
  -f path="src/auth/login.py" \
  -f commit_id="$HEAD_SHA" \
  -f line=45 \
  -f side="RIGHT"
```

**Один встроенный комментарий — с curl:**

```bash
# Get the head commit SHA
HEAD_SHA=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments \
  -d "{
    \"body\": \"This could be simplified with a list comprehension.\",
    \"path\": \"src/auth/login.py\",
    \"commit_id\": \"$HEAD_SHA\",
    \"line\": 45,
    \"side\": \"RIGHT\"
  }"
```

### Отправить формальный обзор (Approve / Request Changes)

**С gh:**

```bash
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments."
gh pr review 123 --comment --body "Some suggestions, nothing blocking."
```

**С curl — многокомментарный обзор отправляется атомарно:**

```bash
HEAD_SHA=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews \
  -d "{
    \"commit_id\": \"$HEAD_SHA\",
    \"event\": \"COMMENT\",
    \"body\": \"Code review from Hermes Agent\",
    \"comments\": [
      {\"path\": \"src/auth.py\", \"line\": 45, \"body\": \"Use parameterized queries to prevent SQL injection.\"},
      {\"path\": \"src/models/user.py\", \"line\": 23, \"body\": \"Hash passwords with bcrypt before storing.\"},
      {\"path\": \"tests/test_auth.py\", \"line\": 1, \"body\": \"Add test for expired token edge case.\"}
    ]
  }"
```

Значения события: `"APPROVE"`, `"REQUEST_CHANGES"`, `"COMMENT"`

Поле `line` относится к номеру строки в *новой* версии файла. Для удалённых строк используй `"side": "LEFT"`.

---

## 3. Чеклист обзора

При выполнении обзора кода (локального или PR) систематически проверяй:

### Корректность
- Делает ли код то, что заявлено?
- Обработаны ли граничные случаи (пустые входы, `null`, большие данные, конкурентный доступ)?
- Обрабатываются ли ошибки корректно?

### Безопасность
- Нет жёстко закодированных секретов, учётных данных или API‑ключей
- Валидация входных данных от пользователей
- Нет SQL‑инъекций, XSS или обхода путей
- Проверки аутентификации/авторизации там, где необходимо

### Качество кода
- Ясные имена (переменных, функций, классов)
- Нет излишней сложности или преждевременной абстракции
- DRY — нет дублированной логики, которую следует вынести
- Функции сфокусированы (единственная ответственность)

### Тестирование
- Протестированы новые пути кода?
- Покрыты ли счастливый путь и случаи ошибок?
- Тесты читаемы и поддерживаемы?

### Производительность
- Нет запросов N+1 или лишних циклов
- При необходимости используется кэширование
- Нет блокирующих операций в асинхронных путях

### Документация
- Публичные API задокументированы
- Неочевидная логика имеет комментарии, объясняющие «почему»
- `README` обновлён, если поведение изменилось

---

## 4. Рабочий процесс пред‑пуш обзора

Когда пользователь просит тебя «проверить код» или «проверить перед пушем»:

1. `git diff main...HEAD --stat` — увидеть объём изменений
2. `git diff main...HEAD` — прочитать полный дифф
3. Для каждого изменённого файла используй `read_file`, если нужен более широкий контекст
4. Применяй чеклист выше
5. Представь результаты в структурированном формате (Critical / Warnings / Suggestions / Looks Good)
6. Если найдены критические проблемы, предложи исправить их до пуша пользователя

---

## 5. Рабочий процесс обзора PR (сквозной)

Когда пользователь просит тебя «обзор PR #N», «посмотри этот PR» или даёт URL PR, следуй этому рецепту:

### Шаг 1: Настроить окружение

```bash
source "${HERMES_HOME:-$HOME/.hermes}/skills/github/github-auth/scripts/gh-env.sh"
# Or run the inline setup block from the top of this skill
```

### Шаг 2: Собрать контекст PR

Получить метаданные PR, описание и список изменённых файлов, чтобы понять объём перед погружением в код.

**С gh:**
```bash
gh pr view 123
gh pr diff 123 --name-only
gh pr checks 123
```

**С curl:**
```bash
PR_NUMBER=123

# PR details (title, author, description, branch)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER

# Changed files with line counts
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER/files
```

### Шаг 3: Выгрузить PR локально

Это даёт полный доступ к `read_file`, `search_files` и возможность запускать тесты.

```bash
git fetch origin pull/$PR_NUMBER/head:pr-$PR_NUMBER
git checkout pr-$PR_NUMBER
```

### Шаг 4: Прочитать дифф и понять изменения

```bash
# Full diff against the base branch
git diff main...HEAD

# Or file-by-file for large PRs
git diff main...HEAD --name-only
# Then for each file:
git diff main...HEAD -- path/to/file.py
```

Для каждого изменённого файла используй `read_file`, чтобы увидеть полный контекст вокруг изменений — диффы могут упустить проблемы, видимые только в окружении кода.

### Шаг 5: Запустить автоматические проверки локально (если применимо)

```bash
# Run tests if there's a test suite
python -m pytest 2>&1 | tail -20
# or: npm test, cargo test, go test ./..., etc.

# Run linter if configured
ruff check . 2>&1 | head -30
# or: eslint, clippy, etc.
```

### Шаг 6: Применить чеклист обзора (раздел 3)

Пройди каждую категорию: Корректность, Безопасность, Качество кода, Тестирование, Производительность, Документация.

### Шаг 7: Опубликовать обзор в GitHub

Собери вывод и отправь его как формальный обзор с встроенными комментариями.

**С gh:**
```bash
# If no issues — approve
gh pr review $PR_NUMBER --approve --body "Reviewed by Hermes Agent. Code looks clean — good test coverage, no security concerns."

# If issues found — request changes with inline comments
gh pr review $PR_NUMBER --request-changes --body "Found a few issues — see inline comments."
```

**С curl — атомарный обзор с несколькими встроенными комментариями:**
```bash
HEAD_SHA=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['sha'])")

# Build the review JSON — event is APPROVE, REQUEST_CHANGES, or COMMENT
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$GH_OWNER/$GH_REPO/pulls/$PR_NUMBER/reviews \
  -d "{
    \"commit_id\": \"$HEAD_SHA\",
    \"event\": \"REQUEST_CHANGES\",
    \"body\": \"## Hermes Agent Review\n\nFound 2 issues, 1 suggestion. See inline comments.\",
    \"comments\": [
      {\"path\": \"src/auth.py\", \"line\": 45, \"body\": \"🔴 **Critical:** User input passed directly to SQL query — use parameterized queries.\"},
      {\"path\": \"src/models.py\", \"line\": 23, \"body\": \"⚠️ **Warning:** Password stored without hashing.\"},
      {\"path\": \"src/utils.py\", \"line\": 8, \"body\": \"💡 **Suggestion:** This duplicates logic in core/utils.py:34.\"}
    ]
  }"
```

### Шаг 8: Также оставить сводный комментарий

Помимо встроенных комментариев, оставь общий комментарий‑резюме, чтобы автор PR получил полную картину сразу. Используй шаблон формата вывода обзора из `references/review-output-template.md`.

**С gh:**
```bash
gh pr comment $PR_NUMBER --body "$(cat <<'EOF'
## Code Review Summary

**Verdict: Changes Requested** (2 issues, 1 suggestion)

### 🔴 Critical
- **src/auth.py:45** — SQL injection vulnerability

### ⚠️ Warnings
- **src/models.py:23** — Plaintext password storage

### 💡 Suggestions
- **src/utils.py:8** — Duplicated logic, consider consolidating

### ✅ Looks Good
- Clean API design
- Good error handling in the middleware layer

---
*Reviewed by Hermes Agent*
EOF
)"
```

### Шаг 9: Очистить окружение

```bash
git checkout main
git branch -D pr-$PR_NUMBER
```

### Решение: Approve vs Request Changes vs Comment

- **Approve** — нет критических или предупреждающих проблем, только мелкие предложения или всё в порядке
- **Request Changes** — есть критическая или предупреждающая проблема, которую следует исправить перед слиянием
- **Comment** — наблюдения и предложения, но ничего блокирующего (используй, когда не уверен или PR в статусе draft)