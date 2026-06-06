---
title: "Идеация — генерировать идеи проектов через креативные ограничения"
sidebar_label: "Ideation"
description: "Генерируй идеи проектов с помощью креативных ограничений"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Идеация

Генерация идей проектов через творческие ограничения.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/creative-ideation` |
| Version | `1.0.0` |
| Author | SHL0MS |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Creative`, `Ideation`, `Projects`, `Brainstorming`, `Inspiration` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Creative Ideation

## Когда использовать

Используй, когда пользователь говорит «I want to build something», «give me a project idea», «I'm bored», «what should I make», «inspire me» или любую вариацию «I have tools but no direction». Работает для кода, искусства, аппаратного обеспечения, написания, инструментов и всего, что можно создать.

Генерируй идеи проектов через творческие ограничения. Ограничение + направление = креативность.

## Как это работает

1. **Pick a constraint** from the library below — random, or matched to the user's domain/mood
2. **Interpret it broadly** — a coding prompt can become a hardware project, an art prompt can become a CLI tool
3. **Generate 3 concrete project ideas** that satisfy the constraint
4. **If they pick one, build it** — create the project, write the code, ship it

## Правило

Каждый запрос интерпретируется как можно шире. «Включает ли это X?» → Да. Запросы дают направление и лёгкое ограничение. Без того и другого креативности нет.

## Библиотека ограничений

### Для разработчиков

**Solve your own itch:**
Создай инструмент, которого тебе не хватало на этой неделе. Менее 50 строк. Выпусти его сегодня.

**Automate the annoying thing:**
Что в твоём рабочем процессе отнимает больше всего времени? Автоматизируй это. Две часы работы над проблемой, которая стоит тебе пять минут в день.

**The CLI tool that should exist:**
Подумай о команде, которую ты хотел бы вводить. `git undo-that-thing-i-just-did`. `docker why-is-this-broken`. `npm explain-yourself`. Теперь реализуй её.

**Nothing new except glue:**
Создай что‑то полностью из существующих API, библиотек и наборов данных. Единственный оригинальный вклад — то, как ты их соединяешь.

**Frankenstein week:**
Возьми что‑то, что делает X, и заставь делать Y. Репозиторий git, который играет музыку. Dockerfile, генерирующий стихи. Cron‑задачу, отправляющую комплименты.

**Subtract:**
Сколько можно удалить из кодовой базы, прежде чем она сломается? Сократи инструмент до минимально жизнеспособной функции. Удаляй, пока не останется лишь сущность.

**High concept, low effort:**
Глубокая идея, реализованная лениво. Концепт должен быть блестящим, реализация — один вечер. Если занимает дольше, ты переусердствовал.

### Для мастеров и художников

**Blatantly copy something:**
Выбери то, что восхищает тебя — инструмент, произведение искусства, интерфейс. Воссоздай это с нуля. Обучение происходит в разнице между твоей версией и оригиналом.

**One million of something:**
Один миллион — и много, и немного. Миллион пикселей — это 1 МБ фото. Миллион запросов к API — это обычный вторник. Миллион чего‑угодно становится интересным в масштабе.

**Make something that dies:**
Веб‑сайт, который теряет функцию каждый день. Чат‑бот, который забывает. Обратный отсчёт к ничему. Эксперимент с гниением, уничтожением или отпусканием.

**Do a lot of math:**
Генеративная геометрия, shader‑golf, математическое искусство, вычислительное оригами. Время вспомнить, что такое arcsin.

### Для всех

**Text is the universal interface:**
Создай приложение, где текст — единственный интерфейс. Никаких кнопок, никаких графических элементов, только ввод и вывод слов. Текст может входить и выходить почти из любого места.

**Start at the punchline:**
Придумай смешную фразу. Затем работай в обратном порядке, чтобы воплотить её в жизнь. «Я научил термостат газлайтить меня» → теперь реализуй это.

**Hostile UI:**
Создай намеренно болезненный в использовании интерфейс. Поле пароля, требующее 47 условий. Форму, где каждый ярлык лжёт. CLI, который судит твои команды.

**Take two:**
Вспомни старый проект. Сделай его заново с нуля, не глядя на оригинал. Посмотри, как изменилось твоё мышление.

См. `references/full-prompt-library.md` для более чем 30 дополнительных ограничений в областях коммуникации, масштаба, философии, трансформации и др.

## Сопоставление ограничений пользователям

| User says | Pick from |
|-----------|-----------|
| "I want to build something" (no direction) | Random — any constraint |
| "I'm learning [language]" | Blatantly copy something, Automate the annoying thing |
| "I want something weird" | Hostile UI, Frankenstein week, Start at the punchline |
| "I want something useful" | Solve your own itch, The CLI tool that should exist, Automate the annoying thing |
| "I want something beautiful" | Do a lot of math, One million of something |
| "I'm burned out" | High concept, low effort, Make something that dies |
| "Weekend project" | Nothing new except glue, Start at the punchline |
| "I want a challenge" | One million of something, Subtract, Take two |

## Формат вывода

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

## Пример

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

After the user picks one, start building — create the project, write the code, iterate.

## Атрибуция

Constraint approach inspired by [wttdotm.com/prompts.html](https://wttdotm.com/prompts.html). Adapted and expanded for software development and general-purpose ideation.