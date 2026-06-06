---
title: "Ідеація — Генеруй ідеї проєктів за допомогою креативних обмежень"
sidebar_label: "Ideation"
description: "Генеруй ідеї проєктів за допомогою креативних обмежень"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Ідеація

Генеруй ідеї проєктів за допомогою креативних обмежень.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/creative-ideation` |
| Version | `1.0.0` |
| Author | SHL0MS |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Creative`, `Ideation`, `Projects`, `Brainstorming`, `Inspiration` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Креативна ідеація

## Коли використовувати

Використовуй, коли користувач каже «Хочу щось створити», «Дай ідею проєкту», «Мені нудно», «Що мені зробити», «Натхни мене» або будь‑яку варіацію типу «У мене є інструменти, а напрямку немає». Працює для коду, мистецтва, апаратури, написання текстів, інструментів і будь‑чого, що можна створити.

Генеруй ідеї проєктів через креативні обмеження. Обмеження + напрямок = креативність.

## Як це працює

1. **Вибери обмеження** з бібліотеки нижче — випадкове або підбиране під домен/настрій користувача.
2. **Інтерпретуй його широко** — запит на код може стати апаратним проєктом, запит на мистецтво — інструментом CLI.
3. **Згенеруй 3 конкретні ідеї проєктів**, що задовольняють обмеження.
4. **Якщо користувач вибирає одну, реалізуй її** — створи проєкт, напиши код, випусти.

## Правило

Кожен запит інтерпретується якомога ширше. «Чи включає це X?» → Так. Запити дають напрямок і легке обмеження. Без одного з них креативності немає.

## Бібліотека обмежень

### Для розробників

**Solve your own itch:**
Створи інструмент, якого ти хотів би мати цього тижня. Менше 50 рядків. Випусти сьогодні.

**Automate the annoying thing:**
Що найнадокучливіше у твоєму робочому процесі? Автоматизуй це. Дві години на проблему, яка вартує п’ять хвилин щодня.

**The CLI tool that should exist:**
Подумай про команду, яку ти хотів би мати. `git undo-that-thing-i-just-did`. `docker why-is-this-broken`. `npm explain-yourself`. Тепер реалізуй її.

**Nothing new except glue:**
Створи щось лише з існуючих API, бібліотек та наборів даних. Єдиний оригінальний внесок — те, як ти їх поєднаєш.

**Frankenstein week:**
Візьми щось, що робить X, і змінити його на Y. Git‑репозиторій, що грає музику. Dockerfile, що генерує поезію. Cron‑завдання, що надсилає компліменти.

**Subtract:**
Скільки можна видалити з кодової бази, перш ніж вона зламається? Скороти інструмент до мінімальної життєздатної функції. Видаляй, доки не залишиться лише сутність.

**High concept, low effort:**
Глибока ідея, реалізована ліниво. Концепція має бути блискучою, реалізація — займати лише один день. Якщо потрібно більше часу, ти надмірно ускладнюєш задачу.

### Для майстрів та художників

**Blatantly copy something:**
Вибери те, що ти захоплюєшся — інструмент, твір мистецтва, інтерфейс. Відтворити його з нуля. Навчання полягає у розриві між твоєю версією та оригіналом.

**One million of something:**
Мільйон — це і багато, і не так вже й багато. Мільйон пікселів — це фото 1 МБ. Мільйон запитів до API — це вівторок. Будь‑яка кількість стає цікавою в масштабі мільйона.

**Make something that dies:**
Веб‑сайт, що втрачає функцію щодня. Чат‑бот, що забуває. Зворотний відлік до нічого. Вправа в розкладанні, знищенні чи відпусканні.

**Do a lot of math:**
Генеративна геометрія, shader‑golf, математичне мистецтво, обчислювальне оригамі. Час переосвоїти, що таке arcsin.

### Для будь‑кого

**Text is the universal interface:**
Створи щось, де текст — єдиний інтерфейс. Без кнопок, без графіки, лише слова на вході та виході. Текст може проходити через майже будь‑що.

**Start at the punchline:**
Придумай кумедне речення. Працюй у зворотному напрямку, щоб його втілити. «Я навчив термостат газлайтити мене» → тепер реалізуй.

**Hostile UI:**
Створи щось навмисно болісне у використанні. Поле пароля, що вимагає 47 умов. Форма, де кожна мітка бреше. CLI, що судить твої команди.

**Take two:**
Згадай старий проєкт. Зроби його заново з нуля. Не дивись на оригінал. Подивися, що змінилося у твоєму мисленні.

Дивись `references/full-prompt-library.md` для понад 30 додаткових обмежень у сферах комунікації, масштабу, філософії, трансформації тощо.

## Підбір обмежень під користувачів

| Користувач каже | Вибираємо з |
|------------------|-------------|
| «Хочу щось створити» (без напрямку) | Випадкове — будь‑яке обмеження |
| «Вивчаю [мова]» | Blatantly copy something, Automate the annoying thing |
| «Хочу щось дивне» | Hostile UI, Frankenstein week, Start at the punchline |
| «Хочу щось корисне» | Solve your own itch, The CLI tool that should exist, Automate the annoying thing |
| «Хочу щось красиве» | Do a lot of math, One million of something |
| «Я вигорів» | High concept, low effort, Make something that dies |
| «Проєкт на вихідні» | Nothing new except glue, Start at the punchline |
| «Хочу виклик» | One million of something, Subtract, Take two |

## Формат виводу

```
## Constraint: [Name]
> [The constraint, one sentence]

### Ideas

1. **[One-line pitch]**
   [2-3 sentences: what you'd build and why it's interesting]
   ⏱ [weekend / week / month] • 🔧 [stack]

2. **[One-line pitch]**
   [2-3 sentences]
   ⏱ ... • 🔧 ...

3. **[One-line pitch]**
   [2-3 sentences]
   ⏱ ... • 🔧 ...
```

## Приклад

```
## Constraint: The CLI tool that should exist
> Think of a command you've wished you could type. Now build it.

### Ideas

1. **`git whatsup` — show what happened while you were away**
   Compares your last active commit to HEAD and summarizes what changed,
   who committed, and what PRs merged. Like a morning standup from your repo.
   ⏱ weekend • 🔧 Python, GitPython, click

2. **`explain 503` — HTTP status codes for humans**
   Pipe any status code or error message and get a plain-English explanation
   with common causes and fixes. Pulls from a curated database, not an LLM.
   ⏱ weekend • 🔧 Rust or Go, static dataset

3. **`deps why <package>` — why is this in my dependency tree**
   Traces a transitive dependency back to the direct dependency that pulled
   it in. Answers "why do I have 47 copies of lodash" in one command.
   ⏱ weekend • 🔧 Node.js, npm/yarn lockfile parsing
```

Після того, як користувач обирає один варіант, починай реалізовувати — створи проєкт, напиши код, ітеративно вдосконалюй.

## Атрибуція

Підхід з обмеженнями натхнено [wttdotm.com/prompts.html](https://wttdotm.com/prompts.html). Адаптовано та розширено для розробки програмного забезпечення та загального ідеаційного процесу.