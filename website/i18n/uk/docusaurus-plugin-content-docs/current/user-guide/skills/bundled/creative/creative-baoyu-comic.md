---
title: "Baoyu Comic — Knowledge comics (知识漫画): освітні, біографічні, навчальні"
sidebar_label: "Baoyu Comic"
description: "Knowledge comics (知识漫画): освітні, біографічні, навчальні"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Baoyu Comic

Комікси знань (知识漫画): освітні, біографічні, навчальні.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлюється за замовчуванням) |
| Шлях | `skills/creative/baoyu-comic` |
| Версія | `1.56.1` |
| Автор | 宝玉 (JimLiu) |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `comic`, `knowledge-comic`, `creative`, `image-generation` |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Створювач коміксів‑знань

Адаптовано з [baoyu-comic](https://github.com/JimLiu/baoyu-skills) для екосистеми інструментів Hermes Agent.

Створюй оригінальні комікси‑знання з гнучкими поєднаннями стилю мистецтва та тону.
## Коли використовувати

Запусти цю навичку, коли користувач просить створити знань‑/освітній комікс, біографічний комікс, навчальний комікс або вживає терміни типу «知识漫画», «教育漫画» чи «Logicomix‑style». Користувач надає вміст (текст, шлях до файлу, URL або тему) і за потреби вказує стиль мистецтва, тон, макет, співвідношення сторін або мову.
## Референтні зображення

Інструмент Hermes `image_generate` працює **лише з підказкою** — він приймає текстову підказку та співвідношення сторін, а повертає URL зображення. Він **НЕ** приймає референтні зображення. Коли користувач надає референтне зображення, використай його для **видобутку ознак у тексті**, які вбудовуються в підказку кожної сторінки:

**Прийом**: Приймай шляхи до файлів, коли їх надає користувач (або коли зображення вставлені в розмову).
- Шлях(и) до файлу → копіюй у `refs/NN-ref-{slug}.{ext}` поряд із виводом комікса для підтвердження походження
- Вставлене зображення без шляху → запитай у користувача шлях за допомогою `clarify` або вербально видобути стилістичні ознаки як текстовий запасний варіант
- Відсутність референсу → пропусти цей розділ

**Режими використання** (на один референт):

| Використання | Ефект |
|--------------|-------|
| `style` | Видобути стилістичні ознаки (обробка ліній, текстура, настрій) і додати їх до тіла підказки кожної сторінки |
| `palette` | Видобути HEX‑кольори і додати їх до тіла підказки кожної сторінки |
| `scene` | Видобути композицію сцени або нотатки про предмет і додати їх до відповідних сторінок |

**Записуй у frontmatter підказки кожної сторінки**, коли є референси:

```yaml
references:
  - ref_id: 01
    filename: 01-ref-scene.png
    usage: style
    traits: "muted earth tones, soft-edged ink wash, low-contrast backgrounds"
```

Послідовність персонажів забезпечується **текстовими описами** у `characters/characters.md` (написаними на кроці 3), які вбудовуються безпосередньо у підказку кожної сторінки (крок 5). Додатковий PNG‑лист персонажів, згенерований на кроці 7.1, слугує лише як артефакт для перегляду людьми і не використовується як вхід для `image_generate`.
## Options

### Visual Dimensions

| Option | Values | Description |
|--------|--------|-------------|
| Art | ligne-claire (default), manga, realistic, ink-brush, chalk, minimalist | Стиль мистецтва / техніка рендерингу |
| Tone | neutral (default), warm, dramatic, romantic, energetic, vintage, action | Настрій / атмосфера |
| Layout | standard (default), cinematic, dense, splash, mixed, webtoon, four-panel | Розташування панелей |
| Aspect | 3:4 (default, portrait), 4:3 (landscape), 16:9 (widescreen) | Співвідношення сторін сторінки |
| Language | auto (default), zh, en, ja, etc. | Мова виведення |
| Refs | File paths | Референтні зображення, що використовуються для вилучення стилю / палітри (не передаються до моделі зображень). Дивись [Reference Images](#reference-images) вище. |

### Partial Workflow Options

| Option | Description |
|--------|-------------|
| Storyboard only | Генерувати лише сторіборд, пропустити підказки та зображення |
| Prompts only | Генерувати сторіборд + підказки, пропустити зображення |
| Images only | Генерувати зображення з існуючого каталогу підказок |
| Regenerate N | Перегенерувати лише конкретні сторінки (наприклад, `3` або `2,5,8`) |

Details: [references/partial-workflows.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/partial-workflows.md)

### Art, Tone & Preset Catalogue

- **Art styles** (6): `ligne-claire`, `manga`, `realistic`, `ink-brush`, `chalk`, `minimalist`. Повні визначення у `references/art-styles/<style>.md`.
- **Tones** (7): `neutral`, `warm`, `dramatic`, `romantic`, `energetic`, `vintage`, `action`. Повні визначення у `references/tones/<tone>.md`.
- **Presets** (5) зі спеціальними правилами, що виходять за межі простого art + tone:

  | Preset | Equivalent | Hook |
  |--------|-----------|------|
  | `ohmsha` | manga + neutral | Візуальні метафори, без говорячих голів, розкриття гаджетів |
  | `wuxia` | ink-brush + action | Ефекти Ці, бойові візуали, атмосферність |
  | `shoujo` | manga + romantic | Декоративні елементи, деталі очей, романтичні моменти |
  | `concept-story` | manga + warm | Візуальна система символів, арка зростання, баланс діалогу та дії |
  | `four-panel` | minimalist + neutral + four-panel layout | Структура 起承转合, ЧБ + акцентний колір, персонажі‑палички |

  Повні правила у `references/presets/<preset>.md` — завантажуй файл, коли обираєш пресет.

- **Compatibility matrix** та таблиця **content‑signal → preset** розташовані у [references/auto-selection.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/auto-selection.md). Прочитай їх перед рекомендацією комбінацій у кроці 2.
## Структура файлів

Вихідний каталог: `comic/{topic-slug}/`
- Slug: 2‑4 слова у kebab‑case з теми (наприклад, `alan-turing-bio`)
- У випадку конфлікту – додаємо мітку часу (наприклад, `turing-story-20260118-143052`)

**Вміст**:
| Файл | Опис |
|------|------|
| `source-{slug}.md` | Збережений вихідний контент (kebab‑case slug відповідає вихідному каталогу) |
| `analysis.md` | Аналіз вмісту |
| `storyboard.md` | Сторіборд з розбиттям на панелі |
| `characters/characters.md` | Визначення персонажів |
| `characters/characters.png` | Референсний лист персонажів (завантажений з `image_generate`) |
| `prompts/NN-{cover\|page}-[slug].md` | Промпти для генерації |
| `NN-{cover\|page}-[slug].png` | Згенеровані зображення (завантажені з `image_generate`) |
| `refs/NN-ref-{slug}.{ext}` | Користувацькі референс‑зображення (необов’язково, для підтвердження походження) |
## Обробка мови

**Пріоритет визначення**:
1. Мова, вказана користувачем (явна опція)
2. Мова розмови користувача
3. Мова вихідного вмісту

**Правило**: Використовувати мову введення користувача для ВСІХ взаємодій:
- Опис сценаріїв та конспектів сцен
- Підказки для генерації зображень
- Варіанти вибору користувача та підтвердження
- Оновлення прогресу, питання, помилки, підсумки

Технічні терміни залишаються англійською.
## Workflow

### Контрольний список прогресу

```
Comic Progress:
- [ ] Step 1: Setup & Analyze
  - [ ] 1.1 Analyze content
  - [ ] 1.2 Check existing directory
- [ ] Step 2: Confirmation - Style & options ⚠️ REQUIRED
- [ ] Step 3: Generate storyboard + characters
- [ ] Step 4: Review outline (conditional)
- [ ] Step 5: Generate prompts
- [ ] Step 6: Review prompts (conditional)
- [ ] Step 7: Generate images
  - [ ] 7.1 Generate character sheet (if needed) → characters/characters.png
  - [ ] 7.2 Generate pages (with character descriptions embedded in prompt)
- [ ] Step 8: Completion report
```

### Послідовність

```
Input → Analyze → [Check Existing?] → [Confirm: Style + Reviews] → Storyboard → [Review?] → Prompts → [Review?] → Images → Complete
```

### Підсумок кроків

| Крок | Дія | Ключовий результат |
|------|-----|----------------------|
| 1.1 | Аналіз вмісту | `analysis.md`, `source-{slug}.md` |
| 1.2 | Перевірка існуючого каталогу | Обробка конфліктів |
| 2 | Підтвердження стилю, фокусу, аудиторії, оглядів | Переваги користувача |
| 3 | Генерація сторіборду + персонажів | `storyboard.md`, `characters/` |
| 4 | Перегляд структури (за запитом) | Затвердження користувачем |
| 5 | Генерація підказок | `prompts/*.md` |
| 6 | Перегляд підказок (за запитом) | Затвердження користувачем |
| 7.1 | Генерація аркуша персонажа (за потреби) | `characters/characters.png` |
| 7.2 | Генерація сторінок | `*.png` файли |
| 8 | Звіт про завершення | Підсумок |

### Питання користувача

Використовуй інструмент `clarify` для підтвердження опцій. Оскільки `clarify` обробляє одне питання за раз, спочатку задавай найважливіше питання та рухайся послідовно. Повний набір питань кроку 2 дивись у [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/workflow.md).

**Обробка тайм‑ауту (КРИТИЧНО)**: `clarify` може повернути
`"The user did not provide a response within the time limit. Use your best judgement to make the choice and proceed."` — це НЕ згода користувача на використання значень за замовчуванням.

- Сприймай це як значення **лише для цього одного питання**. Продовжуй задавати інші питання кроку 2 послідовно; кожне питання — окрема точка згоди.
- **Відобрази вибране за замовчуванням у наступному повідомленні**, щоб користувач міг його виправити, напр.:
  `"Style: defaulted to ohmsha preset (clarify timed out). Say the word to switch."` — невідображене значення не відрізнити від того, що питання не задавали.
- Не зводь крок 2 до одного проходу «використати всі значення за замовчуванням» після одного тайм‑ауту. Якщо користувач відсутній, він буде відсутній для всіх п’яти питань, але зможе виправити видимі значення, коли повернеться, а невидимі виправити не зможе.

### Крок 7: Генерація зображень

Використовуй вбудований інструмент Hermes `image_generate` для всіх рендерів зображень. Його схема приймає лише `prompt` і `aspect_ratio` (`landscape` | `portrait` | `square`); інструмент **повертає URL**, а не локальний файл. Тому кожну згенеровану сторінку або аркуш персонажа треба завантажити у вихідний каталог.

**Вимога щодо файлу підказки (жорстко)**: запиши повний фінальний підказок кожного зображення у окремий файл у `prompts/` (назва: `NN-{type}-[slug].md`) **до** виклику `image_generate`. Файл підказки слугує записом для відтворюваності.

**Відповідність співвідношень сторін** — поле `aspect_ratio` у сторіборді перетворюється у формат `image_generate` так:

| Співвідношення у сторіборді | Формат `image_generate` |
|-----------------------------|--------------------------|
| `3:4`, `9:16`, `2:3`        | `portrait` |
| `4:3`, `16:9`, `3:2`        | `landscape` |
| `1:1`                      | `square` |

**Крок завантаження** — після кожного виклику `image_generate`:
1. Прочитай URL із результату інструмента
2. Завантаж байти зображення, вказавши **абсолютний** шлях виводу, напр.:
   `curl -fsSL "<url>" -o /abs/path/to/comic/<slug>/NN-page-<slug>.png`
3. Перевір, що файл існує і не порожній за точно вказаним шляхом, перш ніж переходити до наступної сторінки

**Ніколи не покладайся на збереження поточної директорії (CWD) у shell**. CWD інструмента терміналу може змінитися між пакетами (закінчення сесії, `TERMINAL_LIFETIME_SECONDS`, невдалий `cd`, що залишив у неправильній теці). `curl -o relative/path.png` — це «тихий» підступ: якщо CWD змістився, файл опиниться в іншому місці без помилки. **Завжди передавай повністю кваліфікований абсолютний шлях до `-o`**, або вказуй `workdir=<abs path>` у інструменті терміналу. Інцидент квітень 2026: сторінки 06‑09 10‑сторінкового коміксу опинилися у корені репозиторію замість `comic/<slug>/` через успадкування застарілого CWD у пакеті 3 і `curl -o 06-page-skills.png`, що записало файл у неправильну теку. Агент потім кілька ходів стверджував, що файли існують, хоча їх не було.

**7.1 Аркуш персонажа** — генеруй його (у `characters/characters.png`, співвідношення `landscape`) коли комікс багатосторінковий з повторюваними персонажами. Пропусти для простих пресетів (наприклад, чотирипанельний мінімалізм) або односторінкових коміксів. Файл підказки `characters/characters.md` має існувати до виклику `image_generate`. Згенерований PNG — це **артефакт для перегляду людиною** (щоб користувач міг візуально перевірити дизайн персонажа) і довідка для подальших регенерацій або ручних правок підказок — він **не** керує кроком 7.2. Підказки сторінок вже записані у кроці 5 на основі **текстових описів** у `characters/characters.md`; `image_generate` не приймає зображення як візуальний вхід.

**7.2 Сторінки** — підказка кожної сторінки **повинна вже бути** у `prompts/NN-{cover|page}-[slug].md` перед викликом `image_generate`. Оскільки `image_generate` працює лише з підказками, узгодженість персонажів забезпечується **вбудовуванням описів персонажів (з `characters/characters.md`) безпосередньо у кожну підказку сторінки під час кроку 5**. Це вбудовування виконується однаково, незалежно від того, чи створено PNG‑аркуш у 7.1; PNG слугує лише допоміжним засобом для перегляду/регенерації.

**Правило резервного копіювання**: існуючі файли `prompts/…md` і `…png` → перейменовуй, додаючи суфікс `-backup-YYYYMMDD-HHMMSS` перед регенерацією.

Повний покроковий робочий процес (аналіз, сторіборд, контрольні перегляди, варіанти регенерації): [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/workflow.md).
## Посилання

**Core Templates**:
- [analysis-framework.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/analysis-framework.md) – глибокий аналіз контенту
- [character-template.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/character-template.md) – формат визначення персонажа
- [storyboard-template.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/storyboard-template.md) – структура сторіборда
- [ohmsha-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/ohmsha-guide.md) – особливості манги Ohmsha

**Style Definitions**:
- `references/art-styles/` – стилі мистецтва (ligne-claire, manga, realistic, ink-brush, chalk, minimalist)
- `references/tones/` – тони (neutral, warm, dramatic, romantic, energetic, vintage, action)
- `references/presets/` – пресети зі спеціальними правилами (ohmsha, wuxia, shoujo, concept-story, four-panel)
- `references/layouts/` – макети (standard, cinematic, dense, splash, mixed, webtoon, four-panel)

**Workflow**:
- [workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/workflow.md) – деталі повного робочого процесу
- [auto-selection.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/auto-selection.md) – аналіз сигналів контенту
- [partial-workflows.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/partial-workflows.md) – опції часткових робочих процесів
## Модифікація сторінки

| Дія | Кроки |
|--------|-------|
| **Редагувати** | **Оновити файл підказки СПЕРШ** → регенерувати зображення → завантажити новий PNG |
| **Додати** | Створити підказку у вказаній позиції → згенерувати з вбудованими описами персонажів → перенумерувати наступні → оновити сторіборд |
| **Видалити** | Видалити файли → перенумерувати наступні → оновити сторіборд |

**ВАЖЛИВО**: При оновленні сторінок ЗАВЖДИ спочатку оновлюй файл підказки (`prompts/NN-{cover|page}-[slug].md`) перед регенерацією. Це забезпечує документування змін та їх відтворюваність.
## Підводні камені

- Генерація зображень: 10‑30 секунд на сторінку; автоматичне повторення один раз у разі помилки
- **Завжди завантажуй** URL, який повертає `image_generate`, у локальний PNG — downstream‑інструменти (і огляд користувачем) очікують файли в каталозі виводу, а не епемерні URL
- **Використовуй абсолютні шляхи для `curl -o`** — ніколи не покладайся на поточний робочий каталог persistent‑shell між пакетами. Тихий підступ: файли потрапляють у неправильний каталог, і наступний `ls` за потрібним шляхом нічого не показує. Дивись крок 7 «Download step».
- Використовуй стилізовані альтернативи для чутливих публічних осіб
- **Підтвердження кроку 2 обов’язкове** — не пропускай
- **Кроки 4/6 умовні** — лише якщо користувач запросив у кроці 2
- **Крок 7.1 лист персонажів** — рекомендовано для багатосторінкових коміксів, опціонально для простих пресетів. PNG слугує допоміжним засобом для огляду/перегенерації; підказки до сторінок (написані в кроці 5) використовують текстові описи у `characters/characters.md`, а не PNG. `image_generate` не приймає зображення як візуальний вхід
- **Видаляй секрети** — скануй вихідний контент на API‑ключі, токени або облікові дані перед записом будь‑якого вихідного файлу