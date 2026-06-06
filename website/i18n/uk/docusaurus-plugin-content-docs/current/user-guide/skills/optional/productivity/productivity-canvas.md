---
title: "Canvas — інтеграція Canvas LMS — отримати зараховані курси та завдання, використовуючи автентифікацію токеном API"
sidebar_label: "Canvas"
description: "Інтеграція Canvas LMS — отримання записаних курсів та завдань за допомогою автентифікації токеном API"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Canvas

Інтеграція Canvas LMS — отримання курсів та завдань за допомогою автентифікації токеном API.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/productivity/canvas` |
| Path | `optional-skills/productivity/canvas` |
| Version | `1.0.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Canvas`, `LMS`, `Education`, `Courses`, `Assignments` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Canvas LMS — доступ до курсів та завдань

Доступ лише для читання до Canvas LMS для отримання списку курсів та завдань.

## Скрипти

- `scripts/canvas_api.py` — Python CLI для викликів Canvas API

## Налаштування

1. Увійди у свою інстанцію Canvas у браузері.
2. Перейди до **Account → Settings** (клацни іконку профілю, потім **Settings**).
3. Прокрути до **Approved Integrations** і натисни **+ New Access Token**.
4. Дай назву токену (наприклад, “Hermes Agent”), за потреби вкажи термін дії та натисни **Generate Token**.
5. Скопіюй токен і додай його у `~/.hermes/.env`:

```
CANVAS_API_TOKEN=your_token_here
CANVAS_BASE_URL=https://yourschool.instructure.com
```

Базовий URL — це те, що видно у браузері, коли ти ввійшов у Canvas (без кінцевого слешу).

## Використання

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

## Формат виводу

**list_courses** повертає:
```json
[{"id": 12345, "name": "Intro to CS", "course_code": "CS101", "workflow_state": "available", "start_at": "...", "end_at": "..."}]
```

**list_assignments** повертає:
```json
[{"id": 67890, "name": "Homework 1", "due_at": "2025-02-15T23:59:00Z", "points_possible": 100, "submission_types": ["online_upload"], "html_url": "...", "description": "...", "course_id": 12345}]
```

Примітка: опис завдань обрізано до 500 символів. Поле `html_url` містить посилання на повну сторінку завдання в Canvas.

## Довідка API (curl)

```bash
# List courses
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "$CANVAS_BASE_URL/api/v1/courses?enrollment_state=active&per_page=10"

# List assignments for a course
curl -s -H "Authorization: Bearer $CANVAS_API_TOKEN" \
  "$CANVAS_BASE_URL/api/v1/courses/COURSE_ID/assignments?per_page=10&order_by=due_at"
```

Canvas використовує заголовки `Link` для пагінації. Python‑скрипт обробляє пагінацію автоматично.

## Правила

- Ця навичка **тільки для читання** — вона лише отримує дані, ніколи не змінює курси чи завдання.
- При першому використанні перевір автентифікацію, запустивши `$CANVAS list_courses` — якщо отримаєш 401, проведи користувача через процес налаштування.
- Canvas обмежує швидкість до ~700 запитів за 10 хвилин; перевір заголовок `X-Rate-Limit-Remaining`, якщо наближаєшся до ліміту.

## Усунення проблем

| Проблема | Вирішення |
|----------|-----------|
| 401 Unauthorized | Токен недійсний або прострочений — згенеруй новий у налаштуваннях Canvas. |
| 403 Forbidden | Токен не має прав доступу до цього курсу. |
| Empty course list | Спробуй `--enrollment-state active` або прибери прапорець, щоб побачити всі стани. |
| Wrong institution | Перевір, чи `CANVAS_BASE_URL` відповідає URL у твоєму браузері. |
| Timeout errors | Перевір мережеве з’єднання з твоєю інстанцією Canvas. |