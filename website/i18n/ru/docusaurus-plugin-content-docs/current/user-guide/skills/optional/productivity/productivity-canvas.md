---
title: "Canvas — интеграция Canvas LMS — получение записанных курсов и заданий с использованием аутентификации по токену API"
sidebar_label: "Canvas"
description: "Интеграция Canvas LMS — получение записанных курсов и заданий с использованием аутентификации по токену API"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Canvas

Интеграция с Canvas LMS — получение зачисленных курсов и заданий с помощью аутентификации токеном API.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/productivity/canvas` |
| Path | `optional-skills/productivity/canvas` |
| Version | `1.0.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Canvas`, `LMS`, `Education`, `Courses`, `Assignments` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык включён.
:::

# Canvas LMS — доступ к курсам и заданиям

Доступ только для чтения к Canvas LMS для получения списка курсов и заданий.

## Скрипты

- `scripts/canvas_api.py` — Python CLI для вызовов Canvas API

## Настройка

1. Войдите в свой экземпляр Canvas в браузере
2. Перейдите в **Account → Settings** (нажмите значок профиля, затем Settings)
3. Прокрутите до **Approved Integrations** и нажмите **+ New Access Token**
4. Дайте токену имя (например, "Hermes Agent"), при желании укажите срок действия и нажмите **Generate Token**
5. Скопируйте токен и добавьте его в `~/.hermes/.env`:

```
CANVAS_API_TOKEN=your_token_here
CANVAS_BASE_URL=https://yourschool.instructure.com
```

Базовый URL — это то, что отображается в браузере, когда вы вошли в Canvas (без завершающего слеша).

## Использование

```bash
CANVAS="python $HERMES_HOME/skills/productivity/canvas/scripts/canvas_api.py"

# List all active courses
$CANVAS list_courses --enrollment-state active

# List all courses (any state)
$CANVAS list_courses

# List assignments for a specific course
$CANVAS list_assignments 12345

# List assignments ordered by due date
$CANVAS list_assignments 12345 --order-by due_at
```

## Формат вывода

**list_courses** возвращает:
```json
[{"id": 12345, "name": "Intro to CS", "course_code": "CS101", "workflow_state": "available", "start_at": "...", "end_at": "..."}]
```

**list_assignments** возвращает:
```json
[{"id": 67890, "name": "Homework 1", "due_at": "2025-02-15T23:59:00Z", "points_possible": 100, "submission_types": ["online_upload"], "html_url": "...", "description": "...", "course_id": 12345}]
```

Примечание: описания заданий обрезаются до 500 символов. Поле `html_url` содержит ссылку на полную страницу задания в Canvas.

## Справочник API (curl)

```bash
# List courses
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "$CANVAS_BASE_URL/api/v1/courses?enrollment_state=active&per_page=10"

# List assignments for a course
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "$CANVAS_BASE_URL/api/v1/courses/COURSE_ID/assignments?per_page=10&order_by=due_at"
```

Canvas использует заголовки `Link` для постраничной навигации. Python‑скрипт обрабатывает пагинацию автоматически.

## Правила

- Этот навык **только для чтения** — он лишь получает данные и никогда не изменяет курсы или задания
- При первом использовании проверьте аутентификацию, выполнив `$CANVAS list_courses` — если получен ответ 401, проведите пользователя через процесс настройки
- Canvas ограничивает количество запросов примерно до 700 запросов за 10 минут; проверяйте заголовок `X-Rate-Limit-Remaining`, если достигаете лимита

## Устранение неполадок

| Проблема | Решение |
|---------|-----|
| 401 Unauthorized | Токен недействителен или истёк — сгенерируйте новый в настройках Canvas |
| 403 Forbidden | Токен не имеет прав доступа к этому курсу |
| Empty course list | Попробуйте `--enrollment-state active` или уберите флаг, чтобы увидеть все состояния |
| Wrong institution | Убедитесь, что `CANVAS_BASE_URL` совпадает с URL в вашем браузере |
| Timeout errors | Проверьте сетевое соединение с вашим экземпляром Canvas |