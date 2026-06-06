---
title: "Linear — Linear: керуй задачами, проектами, командами через GraphQL + curl"
sidebar_label: "Linear"
description: "Linear: керуй задачами, проєктами, командами через GraphQL + curl"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Linear

Linear: manage issues, projects, teams via GraphQL + curl.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/linear` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Linear`, `Project Management`, `Issues`, `GraphQL`, `API`, `Productivity` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Linear — Управління задачами та проєктами

Керуйте задачами, проєктами та командами Linear безпосередньо через GraphQL API за допомогою `curl`. Без сервера MCP, без OAuth‑потоку, без додаткових залежностей.

## Налаштування

1. Отримай особистий API‑ключ у **Linear Settings > Account > Security & access > Personal API keys** (URL: https://linear.app/settings/account/security). Примітка: сторінка org‑level *Settings > API* показує лише OAuth‑додатки та ключі учасників робочого простору, а не особисті ключі.
2. Встанови `LINEAR_API_KEY` у своєму середовищі (через `hermes setup` або конфігурацію env)

## Основи API

- **Endpoint:** `https://api.linear.app/graphql` (POST)
- **Auth header:** `Authorization: $LINEAR_API_KEY` (без префікса "Bearer" для API‑ключів)
- **Усі запити – POST** з `Content-Type: application/json`
- **Як UUID, так і короткі ідентифікатори** (наприклад, `ENG-123`) працюють для `issue(id:)`

Базовий шаблон curl:
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name } }"}' | python3 -m json.tool
```

## Python‑скрипт‑помічник (зручна альтернатива)

Для швидких однорядкових запитів, які не потребують написання GraphQL вручну, ця навичка постачається зі скриптом Python у `scripts/linear_api.py`. Нульові залежності. Та сама автентифікація (читає `LINEAR_API_KEY`).

```bash
SCRIPT=$(dirname "$(find ~/.hermes -path '*skills/productivity/linear/scripts/linear_api.py' 2>/dev/null | head -1)")/linear_api.py

python3 "$SCRIPT" whoami
python3 "$SCRIPT" list-teams
python3 "$SCRIPT" get-issue ENG-42
python3 "$SCRIPT" get-document 38359beef67c      # fetch a doc by slugId from the URL
python3 "$SCRIPT" raw 'query { viewer { name } }'
```

Усі підкоманди: `whoami`, `list-teams`, `list-projects`, `list-states`, `list-issues`, `get-issue`, `search-issues`, `create-issue`, `update-issue`, `update-status`, `add-comment`, `list-documents`, `get-document`, `search-documents`, `raw`. Запусти з `--help` для перегляду прапорців.

Використовуй скрипт, коли потрібна швидка відповідь без написання GraphQL. Використовуй curl, коли потрібен запит, який скрипт не охоплює, або коли треба скласти фільтри inline.

## Стан робочого процесу

Linear використовує об’єкти `WorkflowState` з полем `type`. **6 типів станів:**

| Type | Description |
|------|-------------|
| `triage` | Вхідні задачі, що потребують перегляду |
| `backlog` | Визнані, але ще не заплановані |
| `unstarted` | Заплановані/готові, але не розпочаті |
| `started` | Активно в роботі |
| `completed` | Завершені |
| `canceled` | Не будуть виконані |

Кожна команда має власні назви станів (наприклад, "In Progress" має тип `started`). Щоб змінити статус задачі, потрібен `stateId` (UUID) цільового стану — спочатку запитай стани робочого процесу.

**Значення пріоритету:** 0 = None, 1 = Urgent, 2 = High, 3 = Medium, 4 = Low

## Типові запити

### Отримати поточного користувача
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name email } }"}' | python3 -m json.tool
```

### Список команд
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ teams { nodes { id name key } } }"}' | python3 -m json.tool
```

### Список станів робочого процесу для команди
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ workflowStates(filter: { team: { key: { eq: \"ENG\" } } }) { nodes { id name type } } }"}' | python3 -m json.tool
```

### Список задач (перші 20)
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(first: 20) { nodes { identifier title priority state { name type } assignee { name } team { key } url } pageInfo { hasNextPage endCursor } } }"}' | python3 -m json.tool
```

### Список моїх призначених задач
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { assignedIssues(first: 25) { nodes { identifier title state { name type } priority url } } } }"}' | python3 -m json.tool
```

### Отримати одну задачу (за ідентифікатором типу ENG-123)
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issue(id: \"ENG-123\") { id identifier title description priority state { id name type } assignee { id name } team { key } project { name } labels { nodes { name } } comments { nodes { body user { name } createdAt } } url } }"}' | python3 -m json.tool
```

### Пошук задач за текстом
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issueSearch(query: \"bug login\", first: 10) { nodes { identifier title state { name } assignee { name } url } } }"}' | python3 -m json.tool
```

### Фільтрація задач за типом стану
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(filter: { state: { type: { in: [\"started\"] } } }, first: 20) { nodes { identifier title state { name } assignee { name } } } }"}' | python3 -m json.tool
```

### Фільтрація за командою та виконавцем
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(filter: { team: { key: { eq: \"ENG\" } }, assignee: { email: { eq: \"user@example.com\" } } }, first: 20) { nodes { identifier title state { name } priority } } }"}' | python3 -m json.tool
```

### Список проєктів
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ projects(first: 20) { nodes { id name description progress lead { name } teams { nodes { key } } url } } }"}' | python3 -m json.tool
```

### Список учасників команди
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users { nodes { id name email active } } }"}' | python3 -m json.tool
```

### Список міток
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issueLabels { nodes { id name color } } }"}' | python3 -m json.tool
```

## Типові мутації

### Створити задачу
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation($input: IssueCreateInput!) { issueCreate(input: $input) { success issue { id identifier title url } } }",
    "variables": {
      "input": {
        "teamId": "TEAM_UUID",
        "title": "Fix login bug",
        "description": "Users cannot login with SSO",
        "priority": 2
      }
    }
  }' | python3 -m json.tool
```

### Оновити статус задачі
Спочатку отримай UUID цільового стану з запиту станів робочого процесу вище, потім:
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { stateId: \"STATE_UUID\" }) { success issue { identifier state { name type } } } }"}' | python3 -m json.tool
```

### Призначити задачу
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { assigneeId: \"USER_UUID\" }) { success issue { identifier assignee { name } } } }"}' | python3 -m json.tool
```

### Встановити пріоритет
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { priority: 1 }) { success issue { identifier priority } } }"}' | python3 -m json.tool
```

### Додати коментар
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { commentCreate(input: { issueId: \"ISSUE_UUID\", body: \"Investigated. Root cause is X.\" }) { success comment { id body } } }"}' | python3 -m json.tool
```

### Встановити дату завершення
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { dueDate: \"2026-04-01\" }) { success issue { identifier dueDate } } }"}' | python3 -m json.tool
```

### Додати мітки до задачі
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { labelIds: [\"LABEL_UUID_1\", \"LABEL_UUID_2\"] }) { success issue { identifier labels { nodes { name } } } } }"}' | python3 -m json.tool
```

### Додати задачу до проєкту
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { projectId: \"PROJECT_UUID\" }) { success issue { identifier project { name } } } }"}' | python3 -m json.tool
```

### Створити проєкт
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation($input: ProjectCreateInput!) { projectCreate(input: $input) { success project { id name url } } }",
    "variables": {
      "input": {
        "name": "Q2 Auth Overhaul",
        "description": "Replace legacy auth with OAuth2 and PKCE",
        "teamIds": ["TEAM_UUID"]
      }
    }
  }' | python3 -m json.tool
```

## Документи

Linear **Documents** – це текстові документи (RFC, специфікації, нотатки), що зберігаються разом із задачами. Вони мають власний кореневий запит `documents` та одиничний запит `document(id:)`.

### URL‑и документів та `slugId`

URL‑и документів виглядають так:
```
https://linear.app/<workspace>/document/<slug>-<hexSlugId>
```

Останній шістнадцятковий сегмент – це `slugId`. Приклад: `https://linear.app/nousresearch/document/rfc-hermes-permission-gateway-discord-38359beef67c` → `slugId` дорівнює `38359beef67c`.

**Важлива деталь схеми:** тіло Markdown знаходиться у полі `content`. ProseMirror JSON – у `contentState` (не `contentData` — це поле не існує, API повертає 400).

### Отримати документ за `slugId`

`document(id:)` приймає лише UUID. Щоб отримати за hex‑slugом URL, відфільтруй колекцію:

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "query($s: String!) { documents(filter: { slugId: { eq: $s } }, first: 1) { nodes { id title content contentState slugId url creator { name } project { name } updatedAt } } }", "variables": {"s": "38359beef67c"}}' \
  | python3 -m json.tool
```

Або через Python‑помічник:
```bash
python3 scripts/linear_api.py get-document 38359beef67c
```

### Отримати документ за UUID

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ document(id: \"11700cff-b514-4db3-afcc-3ed1afacba1c\") { title content url } }"}' \
  | python3 -m json.tool
```

### Список останніх документів

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ documents(first: 25, orderBy: updatedAt) { nodes { id title slugId url updatedAt project { name } } } }"}' \
  | python3 -m json.tool
```

### Пошук документів за назвою

У схемі Linear немає кореневого `searchDocuments`. Використовуй фільтр підрядка назви:

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ documents(filter: { title: { containsIgnoreCase: \"RFC\" } }, first: 25) { nodes { title slugId url } } }"}' \
  | python3 -m json.tool
```

## Пагінація

Linear використовує пагінацію типу Relay (cursor):

```bash
# First page
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(first: 20) { nodes { identifier title } pageInfo { hasNextPage endCursor } } }"}' | python3 -m json.tool

# Next page — use endCursor from previous response
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(first: 20, after: \"CURSOR_FROM_PREVIOUS\") { nodes { identifier title } pageInfo { hasNextPage endCursor } } }"}' | python3 -m json.tool
```

Розмір сторінки за замовчуванням: 50. Максимум: 250. Завжди використовуйте `first: N` для обмеження результатів.

## Довідник фільтрації

Оператори: `eq`, `neq`, `in`, `nin`, `lt`, `lte`, `gt`, `gte`, `contains`, `startsWith`, `containsIgnoreCase`

Комбінуйте фільтри за допомогою `or: [...]` для логіки OR (за замовчуванням AND всередині об’єкта фільтра).

## Типовий робочий процес

1. **Запитати команди**, щоб отримати їх ID та ключі
2. **Запитати стани робочого процесу** для цільової команди, щоб отримати UUID станів
3. **Список або пошук задач**, щоб знайти те, що потрібно виконати
4. **Створити задачі** з ID команди, назвою, описом, пріоритетом
5. **Оновити статус**, встановивши `stateId` у цільовий стан робочого процесу
6. **Додати коментарі** для відстеження прогресу
7. **Позначити завершеним**, встановивши `stateId` у стан типу "completed" команди

## Обмеження швидкості

- 5 000 запитів за годину на API‑ключ
- 3 000 000 балів складності за годину
- Використовуйте `first: N` для обмеження результатів і зниження вартості складності
- Слідкуйте за заголовком відповіді `X-RateLimit-Requests-Remaining`

## Важливі нотатки

- Завжди використовуйте інструмент `terminal` з `curl` для API‑викликів — НЕ використовуйте `web_extract` або `browser`
- Завжди перевіряйте масив `errors` у відповідях GraphQL — HTTP 200 може містити помилки
- Якщо `stateId` не вказано під час створення задач, Linear за замовчуванням ставить перший стан backlog
- Поле `description` підтримує Markdown
- Використовуйте `python3 -m json.tool` або `jq` для форматування JSON‑відповідей для зручного читання