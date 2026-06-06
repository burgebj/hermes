---
sidebar_position: 10
title: "Посібник: GitHub PR Review агент"
description: "Створи автоматизованого AI рев'юера коду, який стежить за твоїми репозиторіями, переглядає pull request'и та надає зворотний зв'язок — без участі"
---

# Посібник: Створення агента огляду PR на GitHub

**Проблема:** Ваша команда відкриває PR швидше, ніж ви встигаєте їх переглядати. PR залишаються відкритими кілька днів у очікуванні перегляду. Молодші розробники зливають баги, бо ніхто не має часу їх перевірити. Ви проводите ранок, розбираючись у diff‑ах, замість того, щоб будувати нові функції.

**Рішення:** AI‑агент, який цілодобово стежить за вашими репозиторіями, оглядає кожен новий PR на наявність багів, проблем безпеки та якості коду, і надсилає вам підсумок — так ви витрачаєте час лише на ті PR, які дійсно потребують людського рішення.

**Що ти створиш:**

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

У цьому посібнику використовується **cron jobs** для періодичного опитування PR за розкладом — без сервера чи публічної кінцевої точки. Працює за NAT та між брандмауерами.

:::tip Хочеш огляди в режимі реального часу?
Якщо у тебе є публічна кінцева точка, ознайомся з [Automated GitHub PR Comments with Webhooks](./webhook-github-pr-review.md) — GitHub миттєво надсилає події до Hermes, коли PR відкривають або оновлюють.
:::

---

## Передумови

- **Hermes Agent встановлений** — дивись [Installation guide](/getting-started/installation)
- **Gateway запущений** для cron jobs:
  ```bash
  hermes gateway install   # Install as a service
  # or
  hermes gateway           # Run in foreground
  ```
- **GitHub CLI (`gh`) встановлений та автентифікований**:
  ```bash
  # Install
  brew install gh        # macOS
  sudo apt install gh    # Ubuntu/Debian

  # Authenticate
  gh auth login
  ```
- **Налаштований обмін повідомленнями** (необов’язково) — [Telegram](/user-guide/messaging/telegram) або [Discord](/user-guide/messaging/discord)

:::tip Немає обміну повідомленнями? Не проблема
Використай `deliver: "local"` щоб зберігати огляди у `~/.hermes/cron/output/`. Чудово для тестування перед підключенням сповіщень.
:::

---

## Крок 1: Перевірка налаштувань

Переконайся, що Hermes має доступ до GitHub. Запусти чат:

```bash
hermes
```

Протести простою командою:

```
Run: gh pr list --repo NousResearch/hermes-agent --state open --limit 3
```

Ти маєш побачити список відкритих PR. Якщо це працює — ти готовий.

---

## Крок 2: Спробуй ручний огляд

У тому ж чаті попроси Hermes оглянути реальний PR:

```
Review this pull request. Read the diff, check for bugs, security issues,
and code quality. Be specific about line numbers and quote problematic code.

Run: gh pr diff 3888 --repo NousResearch/hermes-agent
```

Hermes:
1. Виконає `gh pr diff`, щоб отримати зміни коду
2. Прочитає весь diff
3. Створить структурований огляд із конкретними знахідками

Якщо якість задовольняє, час автоматизувати процес.

---

## Крок 3: Створи навичку огляду

Навичка (skill) дає Hermes послідовні правила огляду, які зберігаються між сесіями та запуском cron. Без неї якість оглядів коливається.

```bash
mkdir -p ~/.hermes/skills/code-review
```

Створи `~/.hermes/skills/code-review/SKILL.md`:

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

Перевір, що вона завантажилась — запусти `hermes` і ти повинен побачити `code-review` у списку навичок під час старту.

---

## Крок 4: Навчи його своїм конвенціям

Саме це робить оглядач дійсно корисним. Запусти сесію і навчись Hermes стандартам твоєї команди:

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

Ці пам’яті зберігаються назавжди — оглядач буде дотримуватись твоїх конвенцій без повторного вказування.

---

## Крок 5: Створи автоматичний cron‑запуск

Тепер з’єднай усе разом. Створи cron‑завдання, що виконується кожні 2 години:

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

Перевір, що воно заплановано:

```bash
hermes cron list
```

### Інші корисні розклади

| Розклад | Коли |
|----------|------|
| `0 */2 * * *` | Кожні 2 години |
| `0 9,13,17 * * 1-5` | Тричі на день, лише будні |
| `0 9 * * 1` | Щотижневий понеділковий ранок |
| `30m` | Кожні 30 хвилин (репозиторії з великим трафіком) |

---

## Крок 6: Запусти за запитом

Не хочеш чекати розклад? Запусти вручну:

```bash
hermes cron run pr-review
```

Або зсередини чат‑сесії:

```
/cron run pr-review
```

---

## Додаткові можливості

### Публікувати огляди безпосередньо у GitHub

Замість доставки у Telegram, дай агенту залишати коментарі у самому PR:

Додай це до свого cron‑prompt:

```
After reviewing, post your review:
- For issues: gh pr review NUMBER --repo REPO --comment --body "YOUR_REVIEW"
- For critical issues: gh pr review NUMBER --repo REPO --request-changes --body "YOUR_REVIEW"
- For clean PRs: gh pr review NUMBER --repo REPO --approve --body "Looks good"
```

:::caution
Переконайся, що `gh` має токен з правами `repo`. Огляди публікуються від імені користувача, під яким автентифіковано `gh`.
:::

### Щотижневий дашборд PR

Створи огляд всіх репозиторіїв у понеділковий ранок:

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

### Моніторинг кількох репозиторіїв

Масштабуй, додаючи більше репозиторіїв у prompt. Агент обробляє їх послідовно — без додаткових налаштувань.

---

## Устранення проблем

### "gh: command not found"
Gateway працює у мінімальному середовищі. Переконайся, що `gh` є в `PATH` системи, і перезапусти gateway.

### Огляди надто загальні
1. Додай навичку `code-review` (Крок 3)
2. Навчи Hermes свої конвенції через пам’ять (Крок 4)
3. Чим більше контексту про ваш стек, тим кращі огляди

### Cron‑завдання не запускається
```bash
hermes gateway status    # Is the gateway running?
hermes cron list         # Is the job enabled?
```

### Обмеження швидкості
GitHub дозволяє 5 000 API‑запитів/годину для автентифікованих користувачів. Кожен огляд PR використовує ~3‑5 запитів (список + diff + опціональні коментарі). Навіть 100 PR/день залишаються в межах ліміту.

---

## Що далі?

- **[Webhook-Based PR Reviews](./webhook-github-pr-review.md)** — отримуй миттєві огляди, коли PR відкривають (потрібна публічна кінцева точка)
- **[Daily Briefing Bot](/guides/daily-briefing-bot)** — поєднай огляди PR з ранковим дайджестом новин
- **[Build a Plugin](/guides/build-a-hermes-plugin)** — упакуй логіку огляду у поширюваний плагін
- **[Profiles](/user-guide/profiles)** — запусти окремий профіль оглядача зі своєю пам’яттю та конфігурацією
- **[Fallback Providers](/user-guide/features/fallback-providers)** — забезпеч огляди навіть коли один провайдер недоступний