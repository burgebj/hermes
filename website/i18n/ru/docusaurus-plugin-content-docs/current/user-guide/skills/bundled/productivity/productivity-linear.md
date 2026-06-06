---
title: "Linear — Linear: управляй задачами, проектами, командами через GraphQL + curl"
sidebar_label: "Linear"
description: "Linear: управлять задачами, проектами, командами через GraphQL + curl"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Linear

Linear: управлять задачами, проектами, командами через GraphQL + curl.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/linear` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Linear`, `Project Management`, `Issues`, `GraphQL`, `API`, `Productivity` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Linear — Управление задачами и проектами

Управляй задачами, проектами и командами Linear напрямую через GraphQL API с помощью `curl`. Без сервера MCP, без OAuth‑потока, без дополнительных зависимостей.

## Настройка

1. Получи персональный API‑ключ в **Linear Settings > Account > Security & access > Personal API keys** (URL: https://linear.app/settings/account/security). Примечание: страница уровня организации *Settings > API* показывает только OAuth‑приложения и ключи участников рабочего пространства, а не персональные ключи.
2. Установи `LINEAR_API_KEY` в своей среде (через `hermes setup` или конфигурацию окружения).

## Основы API

- **Endpoint:** `https://api.linear.app/graphql` (POST)
- **Заголовок авторизации:** `Authorization: $LINEAR_API_KEY` (без префикса «Bearer» для API‑ключей)
- **Все запросы – POST** с `Content-Type: application/json`
- **Как UUID, так и короткие идентификаторы** (например, `ENG-123`) работают для `issue(id:)`

Базовый шаблон curl:
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { id name } }"}' | python3 -m json.tool
```

## Скрипт‑помощник на Python (удобная альтернатива)

Для быстрых однострочников, не требующих ручного написания GraphQL, навык поставляется со стандартным CLI на Python в `scripts/linear_api.py`. Никаких зависимостей. Тот же механизм авторизации (чтение `LINEAR_API_KEY`).

```bash
SCRIPT=$(dirname "$(find ~/.hermes -path '*skills/productivity/linear/scripts/linear_api.py' 2>/dev/null | head -1)")/linear_api.py

python3 "$SCRIPT" whoami
python3 "$SCRIPT" list-teams
python3 "$SCRIPT" get-issue ENG-42
python3 "$SCRIPT" get-document 38359beef67c      # fetch a doc by slugId from the URL
python3 "$SCRIPT" raw 'query { viewer { name } }'
```

Все подкоманды: `whoami`, `list-teams`, `list-projects`, `list-states`, `list-issues`, `get-issue`, `search-issues`, `create-issue`, `update-issue`, `update-status`, `add-comment`, `list-documents`, `get-document`, `search-documents`, `raw`. Запусти с `--help` для списка флагов.

Используй скрипт, когда нужен быстрый ответ без составления GraphQL. Используй curl, когда нужен запрос, который скрипт не покрывает, или когда хочется собрать фильтры inline.

## Состояния рабочего процесса

Linear использует объекты `WorkflowState` с полем `type`. **6 типов состояний:**

| Type | Description |
|------|-------------|
| `triage` | Входящие задачи, требующие обзора |
| `backlog` | Принятые, но ещё не запланированные |
| `unstarted` | Запланированы/готовы, но не начаты |
| `started` | Активно в работе |
| `completed` | Завершено |
| `canceled` | Не будет выполнено |

У каждой команды свои именованные состояния (например, «In Progress» имеет тип `started`). Чтобы изменить статус задачи, нужен `stateId` (UUID) целевого состояния — сначала запроси состояния рабочего процесса.

**Значения приоритета:** 0 = Нет, 1 = Срочно, 2 = Высокий, 3 = Средний, 4 = Низкий

## Часто используемые запросы

### Получить текущего пользователя
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

### Список состояний рабочего процесса для команды
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ workflowStates(filter: { team: { key: { eq: \"ENG\" } } }) { nodes { id name type } } }"}' | python3 -m json.tool
```

### Список задач (первые 20)
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(first: 20) { nodes { identifier title priority state { name type } assignee { name } team { key } url } pageInfo { hasNextPage endCursor } } }"}' | python3 -m json.tool
```

### Список моих назначенных задач
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ viewer { assignedIssues(first: 25) { nodes { identifier title state { name type } priority url } } } }"}' | python3 -m json.tool
```

### Получить одну задачу (по идентификатору, например ENG-123)
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issue(id: \"ENG-123\") { id identifier title description priority state { id name type } assignee { id name } team { key } project { name } labels { nodes { name } } comments { nodes { body user { name } createdAt } } url } }"}' | python3 -m json.tool
```

### Поиск задач по тексту
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issueSearch(query: \"bug login\", first: 10) { nodes { identifier title state { name } assignee { name } url } } }"}' | python3 -m json.tool
```

### Фильтрация задач по типу состояния
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(filter: { state: { type: { in: [\"started\"] } } }, first: 20) { nodes { identifier title state { name } assignee { name } } } }"}' | python3 -m json.tool
```

### Фильтрация по команде и исполнителю
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issues(filter: { team: { key: { eq: \"ENG\" } }, assignee: { email: { eq: \"user@example.com\" } } }, first: 20) { nodes { identifier title state { name } priority } } }"}' | python3 -m json.tool
```

### Список проектов
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ projects(first: 20) { nodes { id name description progress lead { name } teams { nodes { key } } url } } }"}' | python3 -m json.tool
```

### Список участников команды
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users { nodes { id name email active } } }"}' | python3 -m json.tool
```

### Список меток
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ issueLabels { nodes { id name color } } }"}' | python3 -m json.tool
```

## Часто используемые мутации

### Создать задачу
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

### Обновить статус задачи
Сначала получи UUID целевого состояния из запроса состояний рабочего процесса выше, затем:
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { stateId: \"STATE_UUID\" }) { success issue { identifier state { name type } } } }"}' | python3 -m json.tool
```

### Назначить задачу
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { assigneeId: \"USER_UUID\" }) { success issue { identifier assignee { name } } } }"}' | python3 -m json.tool
```

### Установить приоритет
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { priority: 1 }) { success issue { identifier priority } } }"}' | python3 -m json.tool
```

### Добавить комментарий
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { commentCreate(input: { issueId: \"ISSUE_UUID\", body: \"Investigated. Root cause is X.\" }) { success comment { id body } } }"}' | python3 -m json.tool
```

### Установить дату завершения
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { dueDate: \"2026-04-01\" }) { success issue { identifier dueDate } } }"}' | python3 -m json.tool
```

### Добавить метки к задаче
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { labelIds: [\"LABEL_UUID_1\", \"LABEL_UUID_2\"] }) { success issue { identifier labels { nodes { name } } } } }"}' | python3 -m json.tool
```

### Добавить задачу в проект
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { issueUpdate(id: \"ENG-123\", input: { projectId: \"PROJECT_UUID\" }) { success issue { identifier project { name } } } }"}' | python3 -m json.tool
```

### Создать проект
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

## Документы

Linear **Documents** — это текстовые документы (RFC, спецификации, заметки), хранящиеся рядом с задачами. У них есть собственный корневой запрос `documents` и одиночный запрос `document(id:)`.

### URL‑адреса документов и `slugId`

URL‑адреса документов выглядят так:
```
https://linear.app/<workspace>/document/<slug>-<hexSlugId>
```

Последний шестнадцатеричный сегмент — это `slugId`. Пример: `https://linear.app/nousresearch/document/rfc-hermes-permission-gateway-discord-38359beef67c` → `slugId` — `38359beef67c`.

**Важная деталь схемы:** тело Markdown находится в поле `content`. JSON ProseMirror находится в `contentState` (не в `contentData` — это поле не существует, API вернёт 400).

### Получить документ по `slugId`

`document(id:)` принимает только UUID. Чтобы получить по hex‑slugу URL, отфильтруй коллекцию:

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "query($s: String!) { documents(filter: { slugId: { eq: $s } }, first: 1) { nodes { id title content contentState slugId url creator { name } project { name } updatedAt } } }", "variables": {"s": "38359beef67c"}}' \
  | python3 -m json.tool
```

Или через Python‑помощник:
```bash
python3 scripts/linear_api.py get-document 38359beef67c
```

### Получить документ по UUID
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ document(id: \"11700cff-b514-4db3-afcc-3ed1afacba1c\") { title content url } }"}' \
  | python3 -m json.tool
```

### Список последних документов
```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ documents(first: 25, orderBy: updatedAt) { nodes { id title slugId url updatedAt project { name } } } }"}' \
  | python3 -m json.tool
```

### Поиск документов по названию

В схеме Linear нет корневого `searchDocuments`. Используй фильтр подстроки названия:

```bash
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ documents(filter: { title: { containsIgnoreCase: \"RFC\" } }, first: 25) { nodes { title slugId url } } }"}' \
  | python3 -m json.tool
```

## Пагинация

Linear использует пагинацию в стиле Relay‑cursor:

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

Размер страницы по умолчанию: 50. Максимум: 250. Всегда используй `first: N`, чтобы ограничить количество результатов.

## Справочник фильтров

Операторы сравнения: `eq`, `neq`, `in`, `nin`, `lt`, `lte`, `gt`, `gte`, `contains`, `startsWith`, `containsIgnoreCase`

Объединяй фильтры с помощью `or: [...]` для логики ИЛИ (по умолчанию внутри объекта фильтра используется И).

## Типичный рабочий процесс

1. **Запросить команды** — получить ID и ключи команд
2. **Запросить состояния рабочего процесса** для целевой команды — получить UUID состояний
3. **Список или поиск задач** — найти, что требуется выполнить
4. **Создать задачи** с указанием ID команды, заголовка, описания, приоритета
5. **Обновить статус** — установить `stateId` в целевое состояние рабочего процесса
6. **Добавить комментарии** — отслеживать прогресс
7. **Отметить как завершённое** — установить `stateId` в состояние типа `completed` команды

## Ограничения по частоте запросов

- 5 000 запросов/час на API‑ключ
- 3 000 000 баллов сложности/час
- Используй `first: N`, чтобы ограничить результаты и снизить стоимость сложности
- Отслеживай заголовок ответа `X-RateLimit-Requests-Remaining`

## Важные замечания

- Всегда используй инструмент `terminal` с `curl` для вызовов API — не используй `web_extract` или `browser`
- Всегда проверяй массив `errors` в ответах GraphQL — HTTP 200 может всё равно содержать ошибки
- Если при создании задачи опустить `stateId`, Linear по умолчанию ставит первое состояние backlog
- Поле `description` поддерживает Markdown
- Используй `python3 -m json.tool` или `jq` для форматирования JSON‑ответов для лучшей читаемости