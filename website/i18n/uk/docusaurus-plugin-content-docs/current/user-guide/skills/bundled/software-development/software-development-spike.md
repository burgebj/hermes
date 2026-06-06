---
title: "Spike — одноразові експерименти для перевірки ідеї перед розробкою"
sidebar_label: "Spike"
description: "Одноразові експерименти для перевірки ідеї перед створенням"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Спайк

Тимчасові експерименти для перевірки ідеї перед її реалізацією.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудована (встановлена за замовчуванням) |
| Шлях | `skills/software-development/spike` |
| Версія | `1.0.0` |
| Автор | Hermes Agent (адаптовано з gsd-build/get-shit-done) |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `spike`, `prototype`, `experiment`, `feasibility`, `throwaway`, `exploration`, `research`, `planning`, `mvp`, `proof-of-concept` |
| Пов’язані навички | [`sketch`](/docs/user-guide/skills/bundled/creative/creative-sketch), [`writing-plans`](/docs/user-guide/skills/bundled/software-development/software-development-writing-plans), [`subagent-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-subagent-driven-development), [`plan`](/docs/user-guide/skills/bundled/software-development/software-development-plan) |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Спайк

Використовуй цей навик, коли користувач хоче **перевірити ідею** перед тим, як переходити до реальної розробки — підтвердити здійсненність, порівняти підходи або виявити невідомі аспекти, які не розвʼяже жодне дослідження. Спайки створені як одноразові; викидай їх, коли вони виконали свою задачу.

Завантажуй цей навик, коли користувач каже щось типу «let me try this», «I want to see if X works», «spike this out», «before I commit to Y», «quick prototype of Z», «is this even possible?», або «compare A vs B».
## Коли НЕ слід використовувати це

- Відповідь можна знайти в документації або прочитавши код — просто досліджуй, не створюй
- Робота є частиною продакшн‑шляху — використовуй `writing-plans` / `plan` замість цього
- Ідея вже підтверджена — переходь одразу до реалізації
## Якщо у користувача встановлена повна система GSD

Якщо `gsd-spike` з’являється як sibling‑skill (встановлений через `npx get-shit-done-cc --hermes`), віддавай перевагу **`gsd-spike`**, коли користувач хоче повний GSD‑workflow: постійний стан у `.planning/spikes/`, відстеження MANIFEST між сесіями, формат вердикту Given/When/Then та шаблони комітів, що інтегруються з рештою GSD. Цей skill — легка автономна версія для користувачів, які не мають (або не хочуть) повної системи.
## Core method

Незалежно від масштабу, кожен спайк слідує цьому циклу:

```
decompose  →  research  →  build  →  verdict
   ↑__________________________________________↓
                  iterate on findings
```

### 1. Decompose

Розбий ідею користувача на **2‑5 незалежних питань щодо здійсненності**. Кожне питання — окремий спайк. Представ їх у вигляді таблиці з формулюванням Given/When/Then:

| # | Spike | Validates (Given/When/Then) | Risk |
|---|-------|----------------------------|------|
| 001 | websocket-streaming | Given a WS connection, when LLM streams tokens, then client receives chunks &lt; 100ms | High |
| 002a | pdf-parse-pdfjs | Given a multi-page PDF, when parsed with pdfjs, then structured text is extractable | Medium |
| 002b | pdf-parse-camelot | Given a multi-page PDF, when parsed with camelot, then structured text is extractable | Medium |

**Типи спайків:**
- **standard** — один підхід, що відповідає на одне питання
- **comparison** — те саме питання, різні підходи (спільний номер, суфікс літери `a`/`b`/`c`)

**Хороші питання спайків:** конкретна здійсненність з вимірюваним результатом.
**Погані питання спайків:** надто широкі, без вимірюваного результату або просто «прочитай документацію про X».

**Сортуй за ризиком.** Спайк, який найімовірніше знищить ідею, виконується першим. Немає сенсу прототипувати легкі частини, якщо важка частина не працює.

**Пропусти розбиття** лише якщо користувач вже точно знає, що саме хоче спайкнути, і повідомив про це. Тоді сприймай його ідею як один спайк.

### 2. Align (для ідей з кількома спайками)

Представ таблицю спайків. Запитай: «Будувати все в цьому порядку, чи коригувати?» Дай користувачеві можливість видалити, змінити порядок або переформулювати перед тим, як ти писатимеш код.

### 3. Research (для кожного спайка, перед будуванням)

Спайки не є бездослідними — ти досліджуєш достатньо, щоб обрати правильний підхід, а потім будуєш. Для кожного спайка:

1. **Коротко опиши.** 2‑3 речення: що це за спайк, чому він важливий, головний ризик.
2. **Висвітли конкуренти**, якщо є реальний вибір:

   | Approach | Tool/Library | Pros | Cons | Status |
   |----------|-------------|------|------|--------|
   | ... | ... | ... | ... | maintained / abandoned / beta |

3. **Обери один.** Поясни, чому. Якщо 2+ підходи життєздатні, створи швидкі варіанти в межах спайка.
4. **Пропусти дослідження** для чистої логіки без зовнішніх залежностей.

Використовуй інструменти Hermes для кроку дослідження:

- `web_search("python websocket streaming libraries 2025")` — знайди кандидати
- `web_extract(urls=["https://websockets.readthedocs.io/..."])` — прочитай реальну документацію (повертає markdown)
- `terminal("pip show websockets | grep Version")` — перевір, що встановлено у venv проєкту

Для бібліотек без сторінок документації клонуй і читай їх `README.md` / `examples/` через `read_file`. Context7 MCP (якщо користувач його налаштував) також є хорошим джерелом — `mcp_*_resolve-library-id` потім `mcp_*_query-docs`.

### 4. Build

Один каталог на спайк. Тримай його автономним.

<!-- ascii-guard-ignore -->
```
spikes/
├── 001-websocket-streaming/
│   ├── README.md
│   └── main.py
├── 002a-pdf-parse-pdfjs/
│   ├── README.md
│   └── parse.js
└── 002b-pdf-parse-camelot/
    ├── README.md
    └── parse.py
```
<!-- ascii-guard-ignore-end -->

**Схильність до того, що користувач може взаємодіяти.** Спайки провалюються, коли єдиний результат — це рядок логу «it works». Користувач хоче *відчути* роботу спайка. Типові варіанти за пріоритетом:

1. Запусковий CLI, який приймає вхід і виводить вимірюваний результат
2. Мінімальна HTML‑сторінка, що демонструє поведінку
3. Малий веб‑сервер з одним endpoint
4. Юніт‑тест, що перевіряє питання з розпізнаваними асерціями

**Глибина понад швидкість.** Ніколи не оголошуй «it works» після одного успішного запуску. Тестуй граничні випадки. Слідкуй за несподіваними результатами. Висновок достовірний лише при чесному розслідуванні.

**Уникай**, якщо спайк не вимагає: складного управління пакетами, інструментів збірки/бандлерів, Docker, файлів `.env`, систем конфігурації. Хардкодь усе — це спайк.

**Будування одного спайка** — типова послідовність інструментів:

```
terminal("mkdir -p spikes/001-websocket-streaming")
write_file("spikes/001-websocket-streaming/README.md", "# 001: websocket-streaming\n\n...")
write_file("spikes/001-websocket-streaming/main.py", "...")
terminal("cd spikes/001-websocket-streaming && python3 main.py")
# Observe output, iterate.
```

**Паралельні порівняльні спайки (002a / 002b) — делегуй.** Коли два підходи можна виконувати паралельно і обидва потребують реальної інженерії (не 10‑рядкових прототипів), розподіли їх за допомогою `delegate_task`:

```
delegate_task(tasks=[
    {"goal": "Build 002a-pdf-parse-pdfjs: ...", "toolsets": ["terminal", "file", "web"]},
    {"goal": "Build 002b-pdf-parse-camelot: ...", "toolsets": ["terminal", "file", "web"]},
])
```

Кожен підагент повертає свій висновок; ти пишеш підсумкове порівняння.

### 5. Verdict

Кожен `README.md` спайка завершується:

```markdown
## Verdict: VALIDATED | PARTIAL | INVALIDATED

### What worked
- ...

### What didn't
- ...

### Surprises
- ...

### Recommendation for the real build
- ...
```

**VALIDATED** = основне питання отримало позитивну відповідь, з доказами.
**PARTIAL** = працює за умов X, Y, Z — їх задокументовано.
**INVALIDATED** = не працює, з причиною. Це успішний спайк.
## Порівняння спайків

Коли два підходи відповідають на одне й те саме питання (002a / 002b), збудуй їх **один за іншим**, а потім проведи пряме порівняння в кінці:

```markdown
## Head-to-head: pdfjs vs camelot

| Dimension | pdfjs (002a) | camelot (002b) |
|-----------|--------------|----------------|
| Extraction quality | 9/10 structured | 7/10 table-only |
| Setup complexity | npm install, 1 line | pip + ghostscript |
| Perf on 100-page PDF | 3s | 18s |
| Handles rotated text | no | yes |

**Winner:** pdfjs for our use case. Camelot if we need table-first extraction later.
```
## Frontier mode (вибір, що спайкнути далі)

Якщо спайки вже існують і користувач запитує «what should I spike next?», пройди існуючі каталоги та шукай:

- **Integration risks** — два підтверджені спайки, які торкаються одного ресурсу, але тестувалися незалежно
- **Data handoffs** — вихідні дані спайка A вважалися сумісними з вхідними даними спайка B; це ніколи не було доведено
- **Gaps in the vision** — передбачені, але непідтверджені можливості
- **Alternative approaches** — різні підходи для PARTIAL або INVALIDATED спайків

Запропонуй 2‑4 кандидати у форматі Given/When/Then. Дай користувачеві вибрати.
- Створи `spikes/` (або `.planning/spikes/`, якщо користувач дотримується конвенцій GSD) у корені репозиторію
- По одному каталогу на спайк: `NNN-descriptive-name/`
- `README.md` для кожного спайка фіксує питання, підхід, результати, висновок
- Тримай код як одноразовий — спайк, який займає 2 дні на «очищення для продакшн», був поганим спайком
## Атрибуція

Адаптовано з робочого процесу `/gsd-spike` проєкту GSD (Get Shit Done) — MIT © 2025 Lex Christopherson ([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). Повна система GSD пропонує постійний стан спайку, відстеження MANIFEST та інтеграцію з ширшим конвеєром, орієнтованим на специфікації; встановити за допомогою `npx get-shit-done-cc --hermes --global`.