---
title: "Baoyu Article Illustrator — Ілюстрації статей: тип × стиль × узгодженість палітри"
sidebar_label: "Baoyu Article Illustrator"
description: "Ілюстрації статті: тип × стиль × узгодженість палітри"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Ілюстратор статей Baoyu

Ілюстрації до статей: тип × стиль × узгодженість кольорової палітри.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/creative/baoyu-article-illustrator` |
| Версія | `1.57.0` |
| Автор | 宝玉 (JimLiu) |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `article-illustration`, `creative`, `image-generation` |
:::info
Наступне — повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# Ілюстратор статей

Адаптовано з [baoyu-article-illustrator](https://github.com/JimLiu/baoyu-skills) для екосистеми інструментів Hermes Agent.

Аналізуй статті, визначай позиції для ілюстрацій, генеруй зображення з дотриманням узгодженості **Тип × Стиль × Палітра**.
## Коли використовувати

Запусти цей **skill**, коли користувач просить проілюструвати статтю, додати зображення до статті, згенерувати ілюстрації для контенту або використовує фрази типу «为文章配图», «illustrate article» чи «add images». Користувач надає статтю (шлях до файлу або вставлений вміст) і, за бажанням, вказує тип, стиль, палітру або щільність.
## Три виміри

| Вимір | Контроль | Приклади |
|-----------|----------|----------|
| **Тип** | Структура інформації | infographic, scene, flowchart, comparison, framework, timeline |
| **Стиль** | Підхід до візуалізації | notion, warm, minimal, blueprint, watercolor, elegant |
| **Палітра** | Кольорова схема (необов’язково) | macaron, warm, neon — переважає стандартні кольори стилю |

Комбінуйте довільно: `type=infographic, style=vector-illustration, palette=macaron`.

Або використовуйте пресети: `edu-visual` → type + style + palette in one shot. Дивись [style-presets.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/style-presets.md).
## Типи

| Тип | Найкраще для |
|------|----------|
| `infographic` | дані, метрики, технічні |
| `scene` | наративи, емоційні |
| `flowchart` | процеси, робочі потоки |
| `comparison` | поруч, варіанти |
| `framework` | моделі, архітектура |
| `timeline` | історія, еволюція |
## Стилі

Дивись [references/styles.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/styles.md) для основних стилів, повної галереї та сумісності Type × Style.
## Структура виводу

<!-- ascii-guard-ignore -->
```
{output-dir}/
├── source-{slug}.{ext}    # Only for pasted content
├── outline.md
├── prompts/
│   └── NN-{type}-{slug}.md
└── NN-{type}-{slug}.png
```
<!-- ascii-guard-ignore-end -->

**Типова директорія виводу**:

| Вхід | Директорія виводу | Шлях вставки Markdown |
|------|-------------------|-----------------------|
| Шлях до файлу статті | `{article-dir}/imgs/` | `imgs/NN-{type}-{slug}.png` |
| Вставлений контент | `illustrations/{topic-slug}/` (cwd) | `illustrations/{topic-slug}/NN-{type}-{slug}.png` |

Якщо користувач запитує інший макет (наприклад, зображення поруч зі статтею або піддиректорію `illustrations/`), виконуй його вимоги.

**Slug**: 2‑4 слова, kebab‑case. **Конфлікт**: додавай `-YYYYMMDD-HHMMSS`.
## Основні принципи

- **Візуалізуй концепції, а не метафори** — якщо стаття використовує метафору (наприклад, «电锯切西瓜»), ілюструй підґрунтову концепцію, а не буквальне зображення.
- **Мітки використовуй дані статті** — реальні числа, терміни та цитати зі статті, а не загальні заповнювачі.
- **Файли підказок — це записи відтворюваності** — кожна ілюстрація повинна мати збережений файл підказки у `prompts/` перед тим, як генерувати будь‑яке зображення.
- **Видаляй секрети** — скануй вихідний контент на предмет API‑ключів, токенів або облікових даних перед записом будь‑якої інформації на диск.
## Робочий процес

```
- [ ] Step 1: Detect reference images (if provided)
- [ ] Step 2: Analyze content
- [ ] Step 3: Confirm settings (clarify tool, one question at a time)
- [ ] Step 4: Generate outline
- [ ] Step 5: Generate prompts
- [ ] Step 6: Generate images (image_generate)
- [ ] Step 7: Finalize
```

### Крок 1: Виявлення референсних зображень

Якщо користувач надає референсні зображення (шляхи, вставлені inline, вкладення або URL):

1. Для кожного референсу виклич `vision_analyze` з шляхом/URL та питанням про стиль, палітру, композицію та тему. Запиши отриманий опис у `{output-dir}/references/NN-ref-{slug}.md` за допомогою `write_file`.
2. **Не** намагайся копіювати бінарник через `write_file` / `read_file` — вони працюють лише з текстом. Якщо потрібна локальна копія для запису, використай `terminal` (`cp "$src" "{output-dir}/references/NN-ref-{slug}.{ext}"`). Сам інструмент ніколи не потребує читати бінарник; він працює з описом, отриманим від vision.
3. Оскільки `image_generate` не приймає вхідні зображення, опис vision вбудовується в підказки під час Кроку 5.

Повні процедури: [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md#step-1-detect-reference-images).

### Крок 2: Аналіз

| Аналіз | Вихід |
|----------|--------|
| Тип контенту | Technical / Tutorial / Methodology / Narrative |
| Мета | information / visualization / imagination |
| Основні аргументи | 2‑5 головних пунктів |
| Позиції | Де ілюстрації додають цінність |

Прочитай джерело (шлях до файлу → `read_file` або вставлений текст) і запиши аналіз у `{output-dir}/analysis.md` за допомогою `write_file`.

Повні процедури: [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md#step-2-analyze).

### Крок 3: Підтвердження налаштувань

Використай інструмент `clarify`. Оскільки `clarify` обробляє одне питання за раз, спочатку задавай найважливіше питання. Пропусти будь‑яке питання, відповідь на яке вже є у запиті користувача.

| Порядок | Питання | Варіанти |
|-------|----------|---------|
| Q1 | **Preset або тип** | [Recommended preset], [alt preset] або вручну: infographic, scene, flowchart, comparison, framework, timeline, mixed |
| Q2 | **Щільність** | minimal (1‑2), balanced (3‑5), per-section (Recommended), rich (6+) |
| Q3 | **Стиль** *(пропусти, якщо обрано preset у Q1)* | [Recommended], minimal-flat, sci‑fi, hand‑drawn, editorial, scene, poster |
| Q4 | **Палітра** *(необов’язково)* | Default (кольори стилю), macaron, warm, neon |
| Q5 | **Мова** *(лише якщо мова статті неоднозначна)* | мова статті / мова користувача |

Не задавай більше 2‑3 питань `clarify` підряд. Якщо користувач вже вказав ці параметри у своєму запиті, пропусти їх повністю.

Повні процедури: [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md#step-3-confirm-settings).

### Крок 4: Генерація плану → `outline.md`

Збережи `{output-dir}/outline.md` за допомогою `write_file` з frontmatter (type, density, style, palette, image_count) та одним записом для кожної ілюстрації:

```yaml
## Illustration 1
**Position**: [section/paragraph]
**Purpose**: [why]
**Visual Content**: [what to show]
**Filename**: 01-infographic-concept-name.png
```

Повний шаблон: [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md#step-4-generate-outline).

### Крок 5: Генерація підказок

**BLOCKING**: Кожна ілюстрація повинна мати збережений файл підказки перед тим, як генеруватиметься будь‑яке зображення — файл підказки є записом відтворюваності.

Для кожної ілюстрації:

1. Створи файл підказки згідно [references/prompt-construction.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/prompt-construction.md).
2. Збережи його у `{output-dir}/prompts/NN-{type}-{slug}.md` за допомогою `write_file` з YAML frontmatter.
3. Підказки ПОВИННІ використовувати шаблони, специфічні для типу, з структурованими секціями (ZONES / LABELS / COLORS / STYLE / ASPECT).
4. LABELS ПОВИННІ включати дані, специфічні для статті: фактичні числа, терміни, метрики, цитати.
5. Обробляй референси (`direct`/`style`/`palette`) згідно frontmatter підказки — для використання `direct` вбудовуй текстовий опис референсу у підказку (оскільки `image_generate` не приймає вхідні зображення).

### Крок 6: Генерація зображень

Для кожного файлу підказки:

1. Виклич `image_generate(prompt=..., aspect_ratio=...)`. `image_generate` повертає JSON‑результат з URL зображення; він НЕ записує файл на диск і НЕ приймає шлях виводу.
2. Перетвори `ASPECT` підказки у enum `image_generate`: `16:9` → `landscape`, `9:16` → `portrait`, `1:1` → `square`. Кастомні співвідношення → найближчий іменований аспект.
3. Завантаж URL за допомогою `terminal` (наприклад `curl -sSL -o "{output-dir}/NN-{type}-{slug}.png" "{url}"`).
4. При невдачі генерації автоматично повтори спробу один раз.

Примітка: бекенд генерації зображень налаштовується користувачем (за замовчуванням: FAL FLUX 2 Klein 9B) і НЕ може бути вибраний агентом через `image_generate`. Не записуй назви моделей у підказки в очікуванні їх маршрутизації.

### Крок 7: Завершення

Встав `![description](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/{relative-path}/NN-{type}-{slug}.png)` після відповідного абзацу. Alt‑текст: короткий опис мовою статті.

Звіт:

```
Article Illustration Complete!
Article: [path] | Type: [type] | Density: [level] | Style: [style] | Palette: [palette or default]
Images: X/N generated
```
## Модифікація

| Дія   | Кроки |
|-------|-------|
| Редагувати | Оновити підказку → Перегенерувати → Оновити посилання |
| Додати | Розташування → Підказка → Згенерувати → Оновити структуру → Вставити |
| Видалити | Видалити файли → Видалити посилання → Оновити структуру |
## Посилання

| Файл | Вміст |
|------|---------|
| [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/workflow.md) | Детальні процедури |
| [references/usage.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/usage.md) | Приклади використання |
| [references/styles.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/styles.md) | Галерея стилів + галерея палітр |
| [references/style-presets.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/style-presets.md) | Швидкі пресети (type + style + palette) |
| [references/prompt-construction.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-article-illustrator/references/prompt-construction.md) | Шаблони запитів |
## Підводні камені

1. **Цілісність даних має першорядне значення** — ніколи не підсумовуй, не перефразовуй і не змінюй вихідну статистику. «73% increase» залишається «73% increase».
2. **Видаляй секрети** — скануй вихідний вміст на предмет API‑ключів, токенів або облікових даних перед включенням у будь‑який output‑файл.
3. **Не ілюструй метафори буквально** — візуалізуй підлягаючу концепцію.
4. **Prompt‑файли є обов’язковими** — без збереженого prompt‑файлу не можна генерувати зображення. Файл дозволяє відтворити або переключити бекенди пізніше.
5. **`image_generate` – співвідношення сторін** — інструмент підтримує `landscape`, `portrait` та `square`. Користувацькі співвідношення прив’язуються до найближчого варіанту.
6. **`image_generate` повертає URL, а не локальний файл** — завжди завантажуй його через `terminal` (`curl`) перед вставкою локальних шляхів до зображень у статтю.
7. **Вибір бекенду не здійснюється агентом** — `image_generate` використовує ту модель, яку налаштував користувач (за замовчуванням: FAL FLUX 2 Klein 9B). Не пиши `"use <model> to generate this"` у підказках, очікуючи, що це буде маршрутизовано.