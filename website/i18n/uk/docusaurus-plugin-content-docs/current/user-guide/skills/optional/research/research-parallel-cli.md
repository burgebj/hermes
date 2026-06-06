---
title: "паралельний Cli"
sidebar_label: "Parallel Cli"
description: "Опціональний vendor skill для Parallel CLI — agent-native веб‑пошук, екстракція, глибоке дослідження, збагачення, FindAll та моніторинг"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Parallel Cli

Опціональний вендорський скіл для Parallel CLI — агентно‑нативний веб‑пошук, екстракція, глибоке дослідження, збагачення, FindAll та моніторинг. Віддавай перевагу JSON‑виводу та неінтерактивним потокам.
## Метадані навички

| | |
|---|---|
| Джерело | Опційно — встановити за допомогою `hermes skills install official/research/parallel-cli` |
| Шлях | `optional-skills/research/parallel-cli` |
| Версія | `1.1.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `Research`, `Web`, `Search`, `Deep-Research`, `Enrichment`, `CLI` |
| Пов’язані навички | [`duckduckgo-search`](/docs/user-guide/skills/optional/research/research-duckduckgo-search), [`mcporter`](/docs/user-guide/skills/optional/mcp/mcp-mcporter) |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Parallel CLI

Використовуй `parallel-cli`, коли користувач явно хоче Parallel, або коли термінальний‑нативний робочий процес виграє від vendor‑specific стеку Parallel для веб‑пошуку, екстракції, глибоких досліджень, збагачення, виявлення сутностей або моніторингу.

Це необов’язковий сторонній робочий процес, а не базова можливість Hermes.

## Important expectations
- Parallel — це платний сервіс з безкоштовним рівнем, а не повністю безкоштовний локальний інструмент.
- Він перекривається з вбудованим у Hermes `web_search` / `web_extract`, тому не слід надавати йому перевагу за замовчуванням для звичайних запитів.
- Обирай цей skill, коли користувач згадує Parallel конкретно або потребує можливостей, таких як збагачення Parallel, FindAll або моніторинг робочих процесів.

`parallel-cli` розроблений для агентів:
- JSON‑вивід через `--json`
- Неінтерактивне виконання команд
- Асинхронні довготривалі завдання з `--no-wait`, `status` та `poll`
- Ланцюжок контексту за допомогою `--previous-interaction-id`
- Пошук, екстракція, дослідження, збагачення, виявлення сутностей та моніторинг в одному CLI
## Коли це використовувати

Віддавай перевагу цьому **skill**, коли:
- Користувач явно згадує Parallel або `parallel-cli`
- Завдання потребує більш складних робочих процесів, ніж простий одноразовий пошук/витяг
- Тобі потрібні асинхронні глибокі дослідницькі завдання, які можна запустити та опитувати пізніше
- Потрібне структуроване збагачення, виявлення сутностей **FindAll** або моніторинг

Віддавай перевагу нативному Hermes `web_search` / `web_extract` для швидких одноразових запитів, коли Parallel не запитано спеціально.
## Встановлення

Спробуй мінімально інвазивний шлях інсталяції, який підходить для даного середовища.

### Homebrew

```bash
brew install parallel-web/tap/parallel-cli
```

### npm

```bash
npm install -g parallel-web-cli
```

### Python package

```bash
pip install "parallel-web-tools[cli]"
```

### Standalone installer

```bash
curl -fsSL https://parallel.ai/install.sh | bash
```

Якщо ти хочеш ізольовану інсталяцію Python, `pipx` також може працювати:

```bash
pipx install "parallel-web-tools[cli]"
pipx ensurepath
```
## Аутентифікація

Інтерактивний вхід:

```bash
parallel-cli login
```

Безголовий / SSH / CI:

```bash
parallel-cli login --device
```

Змінна середовища API‑ключа:

```bash
export PARALLEL_API_KEY="***"
```

Перевір статус поточної аутентифікації:

```bash
parallel-cli auth
```

Якщо аутентифікація вимагає взаємодії з браузером, запусти з `pty=true`.
## Основний набір правил

1. Завжди надавай перевагу `--json`, коли потрібен машинозчитуваний вивід.
2. Використовуй явні аргументи та не‑інтерактивні процеси.
3. Для довготривалих завдань застосовуй `--no-wait`, а потім `status` / `poll`.
4. Цитуй лише URL‑и, які повертає вивід CLI.
5. Зберігай великі JSON‑виводи у тимчасовий файл, коли очікуються подальші питання.
6. Використовуй фонові процеси лише для справді довготривалих робочих процесів; інакше працюй у передньому плані.
7. Надавай перевагу інструментам Hermes, якщо користувач не вимагає спеціально Parallel або не потребує лише робочих процесів Parallel.
## Швидка довідка

<!-- ascii-guard-ignore -->
```text
parallel-cli
├── auth
├── login
├── logout
├── search
├── extract / fetch
├── research run|status|poll|processors
├── enrich run|status|poll|plan|suggest|deploy
├── findall run|ingest|status|poll|result|enrich|extend|schema|cancel
└── monitor create|list|get|update|delete|events|event-group|simulate
```
<!-- ascii-guard-ignore-end -->
## Загальні прапорці та шаблони

Корисні прапорці:
- `--json` — для структурованого виводу
- `--no-wait` — для асинхронних операцій
- `--previous-interaction-id <id>` — для наступних завдань, які повторно використовують попередній контекст
- `--max-results <n>` — для вказання кількості результатів пошуку
- `--mode one-shot|agentic` — для визначення поведінки пошуку
- `--include-domains domain1.com,domain2.com`
- `--exclude-domains domain1.com,domain2.com`
- `--after-date YYYY-MM-DD`

Read from stdin when convenient:

```bash
echo "What is the latest funding for Anthropic?" | parallel-cli search - --json
echo "Research question" | parallel-cli research run - --json
```
## Пошук

Використовуй для поточних веб‑запитів зі структурованими результатами.

```bash
parallel-cli search "What is Anthropic's latest AI model?" --json
parallel-cli search "SEC filings for Apple" --include-domains sec.gov --json
parallel-cli search "bitcoin price" --after-date 2026-01-01 --max-results 10 --json
parallel-cli search "latest browser benchmarks" --mode one-shot --json
parallel-cli search "AI coding agent enterprise reviews" --mode agentic --json
```

Корисні обмеження:
- `--include-domains` — щоб звузити довірені джерела
- `--exclude-domains` — щоб прибрати шумні домени
- `--after-date` — для фільтрації за актуальністю
- `--max-results` — коли потрібне ширше охоплення

Якщо очікуєш подальші питання, збережи вивід:

```bash
parallel-cli search "latest React 19 changes" --json -o /tmp/react-19-search.json
```

При підсумовуванні результатів:
- починай з відповіді
- включай дати, імена та конкретні факти
- цитуй лише повернені джерела
- уникай вигадування URL‑адрес або назв джерел
## Витяг

Використовуй, щоб отримати чистий вміст або markdown за URL.

```bash
parallel-cli extract https://example.com --json
parallel-cli extract https://company.com --objective "Find pricing info" --json
parallel-cli extract https://example.com --full-content --json
parallel-cli fetch https://example.com --json
```

Використовуй `--objective`, коли сторінка охоплює багато тем і потрібен лише один фрагмент інформації.
## Глибоке дослідження

Використовуй для більш складних багатокрокових дослідницьких завдань, які можуть займати час.

Загальні рівні процесора:
- `lite` / `base` для швидших, дешевших проходів
- `core` / `pro` для більш ретельного синтезу
- `ultra` для найважчих дослідницьких завдань

### Синхронний

```bash
parallel-cli research run \
  "Compare the leading AI coding agents by pricing, model support, and enterprise controls" \
  --processor core \
  --json
```

### Асинхронний запуск + опитування

```bash
parallel-cli research run \
  "Compare the leading AI coding agents by pricing, model support, and enterprise controls" \
  --processor ultra \
  --no-wait \
  --json

parallel-cli research status trun_xxx --json
parallel-cli research poll trun_xxx --json
parallel-cli research processors --json
```

### Ланцюжок контексту / продовження

```bash
parallel-cli research run "What are the top AI coding agents?" --json
parallel-cli research run \
  "What enterprise controls does the top-ranked one offer?" \
  --previous-interaction-id trun_xxx \
  --json
```

Рекомендований робочий процес Hermes:
1. запусти з `--no-wait --json`
2. отримай повернений run/task ID
3. якщо користувач хоче продовжити іншу роботу, рухайся далі
4. пізніше виклич `status` або `poll`
5. підсумуй фінальний звіт з посиланнями на повернені джерела
## Збагачення

Використовуй, коли користувач має CSV/JSON/табличні вхідні дані і потрібні додаткові стовпці, отримані шляхом веб‑дослідження.

### Пропоновані стовпці

```bash
parallel-cli enrich suggest "Find the CEO and annual revenue" --json
```

### План конфігурації

```bash
parallel-cli enrich plan -o config.yaml
```

### Вбудовані дані

```bash
parallel-cli enrich run \
  --data '[{"company": "Anthropic"}, {"company": "Mistral"}]' \
  --intent "Find headquarters and employee count" \
  --json
```

### Не‑інтерактивний запуск файлу

```bash
parallel-cli enrich run \
  --source-type csv \
  --source companies.csv \
  --target enriched.csv \
  --source-columns '[{"name": "company", "description": "Company name"}]' \
  --intent "Find the CEO and annual revenue"
```

### Запуск з YAML‑конфігом

```bash
parallel-cli enrich run config.yaml
```

### Статус / опитування

```bash
parallel-cli enrich status <task_group_id> --json
parallel-cli enrich poll <task_group_id> --json
```

Використовуй явні JSON‑масиви для визначення стовпців під час не‑інтерактивної роботи.
Перевіряй вихідний файл перед повідомленням про успіх.
## FindAll

Використовуй для веб‑масштабного виявлення сутностей, коли користувач хоче отримати набір виявлених сутностей, а не коротку відповідь.

```bash
parallel-cli findall run "Find AI coding agent startups with enterprise offerings" --json
parallel-cli findall run "AI startups in healthcare" -n 25 --json
parallel-cli findall status <run_id> --json
parallel-cli findall poll <run_id> --json
parallel-cli findall result <run_id> --json
parallel-cli findall schema <run_id> --json
```

Це краще підходить, ніж звичайний пошук, коли користувач хоче отримати виявлений набір сутностей, який можна переглянути, відфільтрувати або пізніше збагачувати.
## Монітор

Використовуй для безперервного виявлення змін у часі.

```bash
parallel-cli monitor list --json
parallel-cli monitor get <monitor_id> --json
parallel-cli monitor events <monitor_id> --json
parallel-cli monitor delete <monitor_id> --json
```

Створення зазвичай є чутливою частиною, оскільки важливі ритм і доставка:

```bash
parallel-cli monitor create --help
```

Використовуй це, коли користувач хоче повторюване відстеження сторінки чи джерела, а не одноразове отримання.
## Рекомендовані шаблони використання Hermes

### Швидка відповідь з посиланнями
1. Запусти `parallel-cli search ... --json`
2. Проаналізуй заголовки, URL‑адреси, дати, уривки
3. Підведи підсумок з вбудованими посиланнями лише на повернені URL‑адреси

### Дослідження URL
1. Запусти `parallel-cli extract URL --json`
2. За потреби повтори з `--objective` або `--full-content`
3. Цитуй або підведи підсумок витягнутого markdown

### Довготривалий дослідницький процес
1. Запусти `parallel-cli research run ... --no-wait --json`
2. Збережи отриманий ID
3. Продовжуй інші завдання або періодично опитуй статус
4. Підведи підсумок остаточного звіту з посиланнями

### Структурований процес збагачення
1. Переглянь вхідний файл і стовпці
2. Використай `enrich suggest` або вкажи явні збагачені стовпці
3. Запусти `enrich run`
4. За потреби опитуй завершення
5. Перевір вихідний файл перед повідомленням про успіх
## Обробка помилок та коди виходу

CLI документує такі коди виходу:
- `0` успіх
- `2` невірне введення
- `3` помилка автентифікації
- `4` помилка API
- `5` тайм‑аут

Якщо ти стикаєшся з помилками автентифікації:
1. перевір `parallel-cli auth`
2. переконайся, що `PARALLEL_API_KEY` встановлений, або запусти `parallel-cli login` / `parallel-cli login --device`
3. переконайся, що `parallel-cli` є в `PATH`
## Обслуговування

Перевір поточний стан автентифікації / встановлення:

```bash
parallel-cli auth
parallel-cli --help
```

Команди оновлення:

```bash
parallel-cli update
pip install --upgrade parallel-web-tools
parallel-cli config auto-update-check off
```
## Підводні камені

- Не опускай `--json`, якщо користувач явно не хоче вивід у людському форматі.
- Не цитуй джерела, яких немає у виводі CLI.
- `login` може вимагати взаємодію PTY/браузера.
- Віддавай перевагу виконанню у передньому плані для коротких завдань; не зловживай фоновими процесами.
- Для великих наборів результатів зберігай JSON у `/tmp/*.json` замість того, щоб заповнювати весь контекст.
- Не вибирай тихо режим **Parallel**, коли вбудованих інструментів Hermes достатньо.
- Пам’ятай, що це робочий процес постачальника, який зазвичай потребує автентифікації облікового запису та платного використання поза безкоштовним рівнем.