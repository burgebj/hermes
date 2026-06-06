---
title: "Baoyu Infographic — Інфографіка: 21 шаблон × 21 стиль (信息图, 可视化)"
sidebar_label: "Baoyu Infographic"
description: "Інфографіка: 21 макетів x 21 стиль (信息图, 可视化)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Baoyu Infographic

Інфографіка: 21 шаблон × 21 стиль (信息图, 可视化).
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлюється за замовчуванням) |
| Шлях | `skills/creative/baoyu-infographic` |
| Версія | `1.56.1` |
| Автор | 宝玉 (JimLiu) |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `infographic`, `visual-summary`, `creative`, `image-generation` |
:::info
Нижче наведено повне визначення **skill**, яке Hermes завантажує, коли цей **skill** активовано. Це інструкції, які бачить агент під час роботи **skill**.
:::

# Генератор інфографіки

Адаптовано з [baoyu-infographic](https://github.com/JimLiu/baoyu-skills) для екосистеми інструментів Hermes Agent.

Два виміри: **layout** (структура інформації) × **style** (візуальна естетика). Вільно комбінуй будь‑який layout з будь‑яким style.
## Коли використовувати

Запусти цей **skill**, коли користувач просить створити інфографіку, візуальне резюме, інформаційну графіку або вживає такі терміни, як «信息图», «可视化» чи «高密度信息大图». Користувач надає вміст (текст, шлях до файлу, URL або тему) і, за потреби, вказує макет, стиль, співвідношення сторін або мову.
## Параметри

| Параметр | Значення |
|----------|----------|
| Layout | 21 варіант (див. Layout Gallery), за замовчуванням: bento-grid |
| Style | 21 варіант (див. Style Gallery), за замовчуванням: craft-handmade |
| Aspect | Іменовані: landscape (16:9), portrait (9:16), square (1:1). Користувацькі: будь‑яке співвідношення W:H (наприклад, 3:4, 4:3, 2.35:1) |
| Language | en, zh, ja, тощо |
## Галерея макетів

| Макет | Найкраще підходить для |
|--------|------------------------|
| `linear-progression` | Хронології, процеси, підручники |
| `binary-comparison` | A проти B, до‑після, плюси‑мінуси |
| `comparison-matrix` | Порівняння за кількома факторами |
| `hierarchical-layers` | Піраміди, рівні пріоритету |
| `tree-branching` | Категорії, таксономії |
| `hub-spoke` | Центральна концепція з пов’язаними елементами |
| `structural-breakdown` | Вибухові вигляди, перерізи |
| `bento-grid` | Кілька тем, огляд (за замовчуванням) |
| `iceberg` | Видимі та приховані аспекти |
| `bridge` | Проблема‑рішення |
| `funnel` | Конверсія, фільтрація |
| `isometric-map` | Просторові взаємозв’язки |
| `dashboard` | Метрики, KPI |
| `periodic-table` | Категоризовані колекції |
| `comic-strip` | Наративи, послідовності |
| `story-mountain` | Структура сюжету, арки напруги |
| `jigsaw` | Взаємопов’язані частини |
| `venn-diagram` | Перекриваючі концепції |
| `winding-roadmap` | Подорож, віхи |
| `circular-flow` | Цикли, повторювані процеси |
| `dense-modules` | Високощільні модулі, насичені даними посібники |

Повні визначення: `references/layouts/<layout>.md`
## Галерея стилів

| Style | Опис |
|-------|------|
| `craft-handmade` | Ручна робота, паперове ремесло (за замовчуванням) |
| `claymation` | 3D глиняні фігурки, стоп‑моушн |
| `kawaii` | Японський cute‑стиль, пастельні тони |
| `storybook-watercolor` | М’яка живописна, казкова |
| `chalkboard` | Крейда на чорній дошці |
| `cyberpunk-neon` | Неонове сяйво, футуристичний |
| `bold-graphic` | Коміксний стиль, півтони |
| `aged-academia` | Вінтажна наука, сепія |
| `corporate-memphis` | Плоский вектор, яскравий |
| `technical-schematic` | Чертеж, інженерний |
| `origami` | Складений папір, геометричний |
| `pixel-art` | Ретро 8‑біт |
| `ui-wireframe` | Чорно‑білий мокап інтерфейсу |
| `subway-map` | Діаграма транспорту |
| `ikea-manual` | Мінімалістичне лінійне мистецтво |
| `knolling` | Організований flat‑lay |
| `lego-brick` | Конструкція з іграшкових цеглин |
| `pop-laboratory` | Сітка чертежу, координатні маркери, лабораторна точність |
| `morandi-journal` | Ручний дудл, теплі тони Моренді |
| `retro-pop-grid` | 1970‑х ретро поп‑арт, швейцарська сітка, товсті контури |
| `hand-drawn-edu` | Макаронні пастелі, ручна хиткість, stick‑фігурки |

Full definitions: `references/styles/<style>.md`
## Рекомендовані комбінації

| Тип контенту | Макет + Стиль |
|--------------|----------------|
| Timeline/History | `linear-progression` + `craft-handmade` |
| Step-by-step | `linear-progression` + `ikea-manual` |
| A vs B | `binary-comparison` + `corporate-memphis` |
| Hierarchy | `hierarchical-layers` + `craft-handmade` |
| Overlap | `venn-diagram` + `craft-handmade` |
| Conversion | `funnel` + `corporate-memphis` |
| Cycles | `circular-flow` + `craft-handmade` |
| Technical | `structural-breakdown` + `technical-schematic` |
| Metrics | `dashboard` + `corporate-memphis` |
| Educational | `bento-grid` + `chalkboard` |
| Journey | `winding-roadmap` + `storybook-watercolor` |
| Categories | `periodic-table` + `bold-graphic` |
| Product Guide | `dense-modules` + `morandi-journal` |
| Technical Guide | `dense-modules` + `pop-laboratory` |
| Trendy Guide | `dense-modules` + `retro-pop-grid` |
| Educational Diagram | `hub-spoke` + `hand-drawn-edu` |
| Process Tutorial | `linear-progression` + `hand-drawn-edu` |

Default: `bento-grid` + `craft-handmade`
## Клавіші‑скорочення за ключовими словами

Коли ввід користувача містить ці ключові слова, **автоматично обирай** відповідний макет і пропонуй пов’язані стилі як головні рекомендації у кроці 3. Пропусти виведення макету на основі вмісту для збігів за ключовими словами.

Якщо у скорочення є **Prompt Notes**, додавай їх до згенерованого запиту (крок 5) як додаткові інструкції щодо стилю.

| Ключове слово користувача | Макет | Рекомендовані стилі | Типовий аспект | Примітки до запиту |
|---------------------------|-------|----------------------|----------------|--------------------|
| 高密度信息大图 / high-density-info | `dense-modules` | `morandi-journal`, `pop-laboratory`, `retro-pop-grid` | portrait | — |
| 信息图 / infographic | `bento-grid` | `craft-handmade` | landscape | Minimalist: clean canvas, ample whitespace, no complex background textures. Simple cartoon elements and icons only. |
## Output Structure

<!-- ascii-guard-ignore -->
```
infographic/{topic-slug}/
├── source-{slug}.{ext}
├── analysis.md
├── structured-content.md
├── prompts/infographic.md
└── infographic.png
```
<!-- ascii-guard-ignore-end -->

Slug: 2‑4 слова у kebab‑case з теми. У випадку конфлікту додай ``-YYYYMMDD-HHMMSS``.
## Основні принципи

- Зберігати вихідні дані без змін — без підсумовування чи перефразування (але **видаляти будь‑які облікові дані, API‑ключі, токени або секрети** перед включенням у результати)
- Визначати навчальні цілі перед структуризацією контенту
- Структурувати для візуальної комунікації (заголовки, мітки, візуальні елементи)
## Робочий процес

### Крок 1: Аналіз вмісту

**Load references**: Прочитай `references/analysis-framework.md` з цього навику.

1. Збережи вихідний вміст (шлях до файлу або вставка → `source.md` за допомогою `write_file`)
   - **Правило резервного копіювання**: Якщо `source.md` існує, перейменуй його в `source-backup-YYYYMMDD-HHMMSS.md`
2. Проаналізуй: тема, тип даних, складність, тон, аудиторія
3. Визнач мову джерела та мову користувача
4. Витягни інструкції дизайну з вводу користувача
5. Збережи аналіз у `analysis.md`
   - **Правило резервного копіювання**: Якщо `analysis.md` існує, перейменуй його в `analysis-backup-YYYYMMDD-HHMMSS.md`

Дивись `references/analysis-framework.md` для детального формату.

### Крок 2: Створити структурований вміст → `structured-content.md`

Перетвори вміст у структуру інфографіки:
1. Заголовок і навчальні цілі
2. Розділи з: ключовою концепцією, вмістом (дослівно), візуальним елементом, текстовими підписами
3. Дані (всі статистики/цитати копіюються точно)
4. Інструкції дизайну від користувача

**Правила**: Тільки Markdown. Ніякої нової інформації. Зберігати дані достовірно. Видалити будь‑які облікові дані або секрети з виходу.

Дивись `references/structured-content-template.md` для детального формату.

### Крок 3: Рекомендації комбінацій

**3.1 Спочатку перевірити скорочення ключових слів**: Якщо ввід користувача відповідає ключовому слову з таблиці **Keyword Shortcuts**, автоматично обери пов’язаний layout і пріоритетно підкажи пов’язані style як головні рекомендації. Пропусти визначення layout на основі вмісту.

**3.2 Інакше** порекомендуй 3‑5 комбінацій «layout×style» на основі:
- Структура даних → відповідний layout
- Тон вмісту → відповідний style
- Очікування аудиторії
- Інструкції користувача щодо дизайну

### Крок 4: Підтвердження варіантів

Використай інструмент `clarify` для підтвердження варіантів з користувачем. Оскільки `clarify` обробляє одне питання за раз, спочатку запитай найважливіше:

**Q1 — Комбінація**: Представ 3+ комбінації layout×style з обґрунтуванням. Попроси користувача обрати одну.

**Q2 — Аспект**: Запитай про перевагу співвідношення сторін (landscape/portrait/square або власне W:H).

**Q3 — Мова** (тільки якщо мова джерела ≠ мова користувача): Запитай, якою мовою має бути текстовий вміст.

### Крок 5: Створити підказку → `prompts/infographic.md`

**Правило резервного копіювання**: Якщо `prompts/infographic.md` існує, перейменуй його в `prompts/infographic-backup-YYYYMMDD-HHMMSS.md`

**Load references**: Прочитай обраний layout з `references/layouts/<layout>.md` та style з `references/styles/<style>.md`.

Об’єднай:
1. Визначення layout з `references/layouts/<layout>.md`
2. Визначення style з `references/styles/<style>.md`
3. Базовий шаблон з `references/base-prompt.md`
4. Структурований вміст з Кроку 2
5. Увесь текст у підтвердженій мові

**Розв’язання співвідношення сторін** для `{{ASPECT_RATIO}}`:
- Іменовані пресети → рядок співвідношення: `landscape` → `16:9`, `portrait` → `9:16`, `square` → `1:1`
- Власні W:H співвідношення → використати як є (наприклад, `3:4`, `4:3`, `2.35:1`)

Збережи зібрану підказку у `prompts/infographic.md` за допомогою `write_file`.

### Крок 6: Генерація зображення

Використай інструмент `image_generate` з підготовленою підказкою з Кроку 5.

- Перетвори співвідношення сторін у формат `image_generate`: `16:9` → `landscape`, `9:16` → `portrait`, `1:1` → `square`
- Для власних співвідношень вибери найближче іменоване співвідношення
- При помилці автоматично повторити один раз
- Збережи отриманий URL/шлях до зображення в вихідному каталозі

### Крок 7: Підсумковий звіт

Повідом: тема, layout, style, співвідношення, мова, шлях до виходу, створені файли.
## Посилання

- `references/analysis-framework.md` — методологія аналізу
- `references/structured-content-template.md` — формат контенту
- `references/base-prompt.md` — шаблон підказки
- `references/layouts/<layout>.md` — 21 визначення макету
- `references/styles/<style>.md` — 21 визначення стилю
## Підводні камені

1. **Цілісність даних має першорядне значення** — ніколи не підсумовуй, не перефразовуй і не змінюй вихідну статистику. «73% increase» має залишатися «73% increase», а не «значне збільшення».
2. **Видаляй секрети** — завжди скануй вихідний вміст на наявність API‑ключів, токенів або облікових даних перед включенням у будь‑який вихідний файл.
3. **Одне повідомлення на розділ** — кожен розділ інфографіки має передавати одну чітку ідею. Перевантаження розділів знижує читабельність.
4. **Послідовність стилю** — визначення стилю з файлу‑посилання має застосовуватись послідовно по всій інфографіці. Не змішуй стилі.
5. **Співвідношення сторін image_generate** — інструмент підтримує лише `landscape`, `portrait` та `square`. Користувацькі співвідношення, такі як `3:4`, мають відповідати найближчому варіанту (у цьому випадку `portrait`).