---
sidebar_position: 10
title: "Учебник: GitHub PR Review Agent"
description: "Создай автоматизированный AI‑ревьюер кода, который отслеживает твои репозитории, проверяет pull‑requests и предоставляет обратную связь — без участия человека."
---

# Учебник: Создание агента обзора PR на GitHub

**Проблема:** Ваша команда открывает PR быстрее, чем вы успеваете их проверять. PR остаются открытыми днями в ожидании взгляда. Младшие разработчики сливают баги, потому что никто не нашёл время проверить. Вы тратите утренние часы на разбор диффов вместо разработки.

**Решение:** AI‑агент, который круглосуточно наблюдает за вашими репозиториями, проверяет каждый новый PR на баги, уязвимости и качество кода, а затем отправляет вам сводку — так вы тратите время только на те PR, которые действительно требуют человеческого решения.

**Что ты построишь:**

```
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│   Cron Timer  ──▶  Hermes Agent  ──▶  GitHub API  ──▶  Review     │
│   (every 2h)       + gh CLI           (PR diffs)       delivery   │
│                    + skill                             (Telegram, │
│                    + memory                            Discord,   │
│                                                        local)     │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

В этом руководстве используются **cron‑задачи** для опроса PR по расписанию — сервер или публичный эндпоинт не требуются. Работает за NAT и файрволами.

:::tip Хочешь обзоры в реальном времени?
Если у тебя есть публичный эндпоинт, посмотри [Automated GitHub PR Comments with Webhooks](./webhook-github-pr-review.md) — GitHub мгновенно отправляет события в Hermes, когда открываются или обновляются PR.
:::

---

## Предварительные требования

- **Hermes Agent установлен** — смотри [Руководство по установке](/getting-started/installation)
- **Gateway запущен** для cron‑задач:
  ```bash
  hermes gateway install   # Install as a service
  # or
  hermes gateway           # Run in foreground
  ```
- **GitHub CLI (`gh`) установлен и аутентифицирован**:
  ```bash
  # Install
  brew install gh        # macOS
  sudo apt install gh    # Ubuntu/Debian

  # Authenticate
  gh auth login
  ```
- **Настроенный обмен сообщениями** (необязательно) — [Telegram](/user-guide/messaging/telegram) или [Discord](/user-guide/messaging/discord)

:::tip Нет мессенджера? Не проблема
Используй `deliver: "local"` чтобы сохранять обзоры в `~/.hermes/cron/output/`. Отлично подходит для тестов перед подключением уведомлений.
:::

---

## Шаг 1: Проверка настройки

Убедись, что Hermes может обращаться к GitHub. Запусти чат:

```bash
hermes
```

Проверь простой командой:

```
Run: gh pr list --repo NousResearch/hermes-agent --state open --limit 3
```

Ты должен увидеть список открытых PR. Если всё работает, можно продолжать.

---

## Шаг 2: Попробуй ручной обзор

Оставаясь в чате, попроси Hermes проверить реальный PR:

```
Review this pull request. Read the diff, check for bugs, security issues,
and code quality. Be specific about line numbers and quote problematic code.

Run: gh pr diff 3888 --repo NousResearch/hermes-agent
```

Hermes выполнит:
1. `gh pr diff` для получения изменений кода
2. Прочитает весь дифф
3. Сформирует структурированный обзор с конкретными находками

Если тебя устраивает качество, пора автоматизировать процесс.

---

## Шаг 3: Создай навык обзора

Навык даёт Hermes постоянные правила обзора, которые сохраняются между сессиями и cron‑запусками. Без него качество обзора будет разниться.

```bash
mkdir -p ~/.hermes/skills/code-review
```

Создай файл `~/.hermes/skills/code-review/SKILL.md`:

```markdown
---
name: code-review
description: Review pull requests for bugs, security issues, and code quality
---

# Code Review Guidelines

When reviewing a pull request:

## What to Check
1. **Bugs** — Logic errors, off-by-one, null/undefined handling
2. **Security** — Injection, auth bypass, secrets in code, SSRF
3. **Performance** — N+1 queries, unbounded loops, memory leaks
4. **Style** — Naming conventions, dead code, missing error handling
5. **Tests** — Are changes tested? Do tests cover edge cases?

## Output Format
For each finding:
- **File:Line** — exact location
- **Severity** — Critical / Warning / Suggestion
- **What's wrong** — one sentence
- **Fix** — how to fix it

## Rules
- Be specific. Quote the problematic code.
- Don't flag style nitpicks unless they affect readability.
- If the PR looks good, say so. Don't invent problems.
- End with: APPROVE / REQUEST_CHANGES / COMMENT
```

Проверь, что он загружен — запусти `hermes`, и ты должен увидеть `code-review` в списке навыков при старте.

---

## Шаг 4: Обучи его своим конвенциям

Это делает обзор действительно полезным. Запусти сессию и расскажи Hermes стандарты своей команды:

```
Remember: In our backend repo, we use Python with FastAPI.
All endpoints must have type annotations and Pydantic models.
We don't allow raw SQL — only SQLAlchemy ORM.
Test files go in tests/ and must use pytest fixtures.
```

```
Remember: In our frontend repo, we use TypeScript with React.
No `any` types allowed. All components must have props interfaces.
We use React Query for data fetching, never useEffect for API calls.
```

Эти воспоминания сохраняются навсегда — обозреватель будет применять твои конвенции без необходимости повторного объяснения.

---

## Шаг 5: Создай автоматическую cron‑задачу

Теперь соединяем всё вместе. Создай cron‑задачу, которая будет запускаться каждые 2 часа:

```bash
hermes cron create "0 */2 * * *" \
  "Check for new open PRs and review them.

Repos to monitor:
- myorg/backend-api
- myorg/frontend-app

Steps:
1. Run: gh pr list --repo REPO --state open --limit 5 --json number,title,author,createdAt
2. For each PR created or updated in the last 4 hours:
   - Run: gh pr diff NUMBER --repo REPO
   - Review the diff using the code-review guidelines
3. Format output as:

## PR Reviews — today

### [repo] #[number]: [title]
**Author:** [name] | **Verdict:** APPROVE/REQUEST_CHANGES/COMMENT
[findings]

If no new PRs found, say: No new PRs to review." \
  --name "pr-review" \
  --deliver telegram \
  --skill code-review
```

Проверь, что она запланирована:

```bash
hermes cron list
```

### Другие полезные расписания

| Расписание | Когда |
|----------|------|
| `0 */2 * * *` | Каждые 2 часа |
| `0 9,13,17 * * 1-5` | Три раза в день, только будние |
| `0 9 * * 1` | Еженедельный обзор в понедельник утром |
| `30m` | Каждые 30 минут (для репозиториев с высоким трафиком) |

---

## Шаг 6: Запусти по требованию

Не хочешь ждать расписания? Запусти вручную:

```bash
hermes cron run pr-review
```

Или из текущей чат‑сессии:

```
/cron run pr-review
```

---

## Дальнейшее развитие

### Публикация обзоров напрямую в GitHub

Вместо доставки в Telegram, заставь агента комментировать сам PR:

Добавь это в свой `cron‑prompt`:

```
After reviewing, post your review:
- For issues: gh pr review NUMBER --repo REPO --comment --body "YOUR_REVIEW"
- For critical issues: gh pr review NUMBER --repo REPO --request-changes --body "YOUR_REVIEW"
- For clean PRs: gh pr review NUMBER --repo REPO --approve --body "Looks good"
```

:::caution
Убедись, что у `gh` есть токен с областью `repo`. Обзоры публикуются от имени того, кто аутентифицирован в `gh`.
:::

### Еженедельная панель PR

Создай обзор всех репозиториев на утро понедельника:

```bash
hermes cron create "0 9 * * 1" \
  "Generate a weekly PR dashboard:
- myorg/backend-api
- myorg/frontend-app
- myorg/infra

For each repo show:
1. Open PR count and oldest PR age
2. PRs merged this week
3. Stale PRs (older than 5 days)
4. PRs with no reviewer assigned

Format as a clean summary." \
  --name "weekly-dashboard" \
  --deliver telegram
```

### Мониторинг нескольких репозиториев

Масштабируй, добавляя больше репозиториев в prompt. Агент обрабатывает их последовательно — дополнительной настройки не требуется.

---

## Устранение неполадок

### «gh: command not found»
Gateway работает в минимальном окружении. Убедись, что `gh` находится в `PATH` системы, и перезапусти gateway.

### Обзоры слишком общие
1. Добавь навык `code-review` (Шаг 3)
2. Обучи Hermes свои конвенции через память (Шаг 4)
3. Чем больше контекста о вашем стеке, тем лучше обзоры

### Cron‑задача не запускается
```bash
hermes gateway status    # Is the gateway running?
hermes cron list         # Is the job enabled?
```

### Ограничения по запросам
GitHub позволяет 5 000 API‑запросов в час для аутентифицированных пользователей. Каждый обзор PR использует ~3‑5 запросов (список + дифф + опциональные комментарии). Даже при проверке 100 PR в день это остаётся в пределах лимита.

---

## Что дальше?

- **[Webhook-Based PR Reviews](./webhook-github-pr-review.md)** — мгновенные обзоры при открытии PR (требуется публичный эндпоинт)
- **[Daily Briefing Bot](/guides/daily-briefing-bot)** — объединить обзоры PR с утренним дайджестом новостей
- **[Build a Plugin](/guides/build-a-hermes-plugin)** — упаковать логику обзора в совместно используемый плагин
- **[Profiles](/user-guide/profiles)** — запустить отдельный профиль обозревателя со своей памятью и конфигурацией
- **[Fallback Providers](/user-guide/features/fallback-providers)** — обеспечить работу обзоров даже при недоступности одного провайдера