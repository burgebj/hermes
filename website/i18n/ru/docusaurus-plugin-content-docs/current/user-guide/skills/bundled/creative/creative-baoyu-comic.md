---
title: "Baoyu Comic — Knowledge comics (知识漫画): образовательные, биографические, учебные"
sidebar_label: "Baoyu Comic"
description: "Knowledge comics (知识漫画): образовательные, биографические, учебные"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Baoyu Comic

Комиксы‑знания (知识漫画): образовательные, биографические, учебные.
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/creative/baoyu-comic` |
| Версия | `1.56.1` |
| Автор | 宝玉 (JimLiu) |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `comic`, `knowledge-comic`, `creative`, `image-generation` |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Создатель познавательных комиксов

Адаптировано из [baoyu-comic](https://github.com/JimLiu/baoyu-skills) для инструментальной экосистемы Hermes Agent.

Создавай оригинальные познавательные комиксы с гибкими комбинациями художественного стиля × тона.
## Когда использовать

Активируй этот навык, когда пользователь просит создать познавательный/образовательный комикс, биографический комикс, учебный комикс или использует такие термины, как «知识漫画», «教育漫画» или «Logicomix-style». Пользователь предоставляет контент (текст, путь к файлу, URL или тему) и при желании указывает художественный стиль, тон, макет, соотношение сторон или язык.
## Справочные изображения

Инструмент Hermes `image_generate` работает **только с подсказкой** — принимает текстовую подсказку и соотношение сторон, возвращает URL изображения. Он **НЕ** принимает справочные изображения. Когда пользователь предоставляет справочное изображение, используй его для **извлечения черт в виде текста**, которые встраиваются в каждую подсказку страницы:

**Ввод**: Принимай пути к файлам, когда пользователь их предоставляет (или вставляет изображения в разговоре).
- Путь(и) к файлу → копировать в `refs/NN-ref-{slug}.{ext}` рядом с выводом комикса для указания источника
- Вставленное изображение без пути → запроси у пользователя путь через `clarify` или извлеки стилистические черты устно как текстовый запасной вариант
- Нет справочного изображения → пропустить этот раздел

**Режимы использования** (для каждого справочного изображения):

| Usage | Effect |
|-------|--------|
| `style` | Извлечь черты стиля (обработка линий, текстура, настроение) и добавить к телу подсказки каждой страницы |
| `palette` | Извлечь HEX‑цвета и добавить к телу подсказки каждой страницы |
| `scene` | Извлечь композицию сцены или заметки о предмете и добавить к соответствующей странице(ам) |

**Записывай в frontmatter подсказки каждой страницы**, когда есть справочные изображения:

```yaml
references:
  - ref_id: 01
    filename: 01-ref-scene.png
    usage: style
    traits: "muted earth tones, soft-edged ink wash, low-contrast backgrounds"
```

Последовательность персонажей обеспечивается **текстовыми описаниями** в `characters/characters.md` (написанными в Шаге 3), которые встраиваются непосредственно в каждую подсказку страницы (Шаг 5). Необязательный PNG‑лист персонажей, генерируемый в Шаге 7.1, служит для человеческого обзора и не является входными данными для `image_generate`.
## Параметры

### Визуальные размеры

| Параметр | Значения | Описание |
|----------|----------|----------|
| Art | ligne-claire (по умолчанию), manga, realistic, ink-brush, chalk, minimalist | Стиль искусства / техника рендеринга |
| Tone | neutral (по умолчанию), warm, dramatic, romantic, energetic, vintage, action | Настроение / атмосфера |
| Layout | standard (по умолчанию), cinematic, dense, splash, mixed, webtoon, four-panel | Расположение панелей |
| Aspect | 3:4 (по умолчанию, портрет), 4:3 (ландшафт), 16:9 (широкоформат) | Соотношение сторон страницы |
| Language | auto (по умолчанию), zh, en, ja, и др. | Язык вывода |
| Refs | Путь к файлам | Справочные изображения, используемые для извлечения стиля / палитры (не передаются модели изображения). См. [Reference Images](#reference-images) выше. |

### Параметры частичного рабочего процесса

| Параметр | Описание |
|----------|----------|
| Storyboard only | Сгенерировать только раскадровку, пропустить подсказки и изображения |
| Prompts only | Сгенерировать раскадровку + подсказки, пропустить изображения |
| Images only | Сгенерировать изображения из существующего каталога подсказок |
| Regenerate N | Перегенерировать только указанные страницы (например, `3` или `2,5,8`) |

Подробности: [references/partial-workflows.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/partial-workflows.md)

### Каталог стилей, тонов и пресетов

- **Стили искусства** (6): `ligne-claire`, `manga`, `realistic`, `ink-brush`, `chalk`, `minimalist`. Полные определения в `references/art-styles/<style>.md`.
- **Тоны** (7): `neutral`, `warm`, `dramatic`, `romantic`, `energetic`, `vintage`, `action`. Полные определения в `references/tones/<tone>.md`.
- **Пресеты** (5) со специальными правилами, выходящими за рамки простого сочетания стиль + тон:

  | Пресет | Эквивалент | Хук |
  |--------|------------|-----|
  | `ohmsha` | manga + neutral | Визуальные метафоры, без говорящих голов, раскрытие гаджетов |
  | `wuxia` | ink-brush + action | Эффекты Ци, боевые визуалы, атмосферность |
  | `shoujo` | manga + romantic | Декоративные элементы, детали глаз, романтические моменты |
  | `concept-story` | manga + warm | Система визуальных символов, арка роста, баланс диалога и действия |
  | `four-panel` | minimalist + neutral + four-panel layout | Структура 起承转合, чёрно‑белое + акцентный цвет, персонажи‑палочки |

  Полные правила в `references/presets/<preset>.md` — загружай файл при выборе пресета.

- **Матрица совместимости** и таблица **content‑signal → preset** находятся в [references/auto-selection.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/auto-selection.md). Ознакомься с ними перед рекомендацией комбинаций на Шаге 2.
## Структура файлов

Выходной каталог: `comic/{topic-slug}/`
- **Slug**: 2‑4 слова в kebab‑case из названия темы (например, `alan-turing-bio`)
- **Конфликт**: добавить метку времени (например, `turing-story-20260118-143052`)

**Содержимое**:
| Файл | Описание |
|------|----------|
| `source-{slug}.md` | Сохранённое исходное содержимое (slug в kebab‑case совпадает с именем каталога) |
| `analysis.md` | Анализ содержимого |
| `storyboard.md` | Сториборд с разбивкой на панели |
| `characters/characters.md` | Определения персонажей |
| `characters/characters.png` | Референс‑лист персонажей (скачивается из `image_generate`) |
| `prompts/NN-{cover\|page}-[slug].md` | Промпты генерации |
| `NN-{cover\|page}-[slug].png` | Сгенерированные изображения (скачиваются из `image_generate`) |
| `refs/NN-ref-{slug}.{ext}` | Пользовательские референс‑изображения (необязательно, для указания источника) |
## Обработка языка

**Приоритет определения**:
1. Язык, указанный пользователем (явный параметр)
2. Язык общения пользователя
3. Язык исходного контента

**Правило**: использовать язык, выбранный пользователем, для ВСЕХ взаимодействий:
- наброски раскадровки и описания сцен
- подсказки для генерации изображений
- варианты выбора и подтверждения пользователя
- обновления прогресса, вопросы, ошибки, резюме

Технические термины остаются на английском.
## Workflow

### Progress Checklist

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

### Flow

```
Input → Analyze → [Check Existing?] → [Confirm: Style + Reviews] → Storyboard → [Review?] → Prompts → [Review?] → Images → Complete
```

### Step Summary

| Step | Action | Key Output |
|------|--------|------------|
| 1.1 | Analyze content | `analysis.md`, `source-{slug}.md` |
| 1.2 | Check existing directory | Handle conflicts |
| 2 | Confirm style, focus, audience, reviews | User preferences |
| 3 | Generate storyboard + characters | `storyboard.md`, `characters/` |
| 4 | Review outline (if requested) | User approval |
| 5 | Generate prompts | `prompts/*.md` |
| 6 | Review prompts (if requested) | User approval |
| 7.1 | Generate character sheet (if needed) | `characters/characters.png` |
| 7.2 | Generate pages | `*.png` files |
| 8 | Completion report | Summary |

### User Questions

Use the `clarify` tool to confirm options. Since `clarify` handles one question at a time, ask the most important question first and proceed sequentially. See [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/workflow.md) for the full Step 2 question set.

**Timeout handling (CRITICAL)**: `clarify` can return `"The user did not provide a response within the time limit. Use your best judgement to make the choice and proceed."` — this is **NOT** user consent to default everything.

- Treat it as a default **for that one question only**. Continue asking the remaining Step 2 questions in sequence; each question is an independent consent point.
- **Отобрази выбранный по умолчанию вариант явно** в следующем сообщении, чтобы пользователь мог его исправить, например: `"Style: defaulted to ohmsha preset (clarify timed out). Say the word to switch."` — незарегистрированный дефолт неотличим от того, что вопрос не задавался.
- Не сворачивай Step 2 в один проход «использовать все значения по умолчанию» после одного таймаута. Если пользователь действительно отсутствует, он будет отсутствовать для всех пяти вопросов — но сможет исправить видимые дефолты, вернувшись, а невидимые исправить уже нельзя.

### Step 7: Image Generation

Use Hermes' built-in `image_generate` tool for all image rendering. Its schema accepts only `prompt` and `aspect_ratio` (`landscape` | `portrait` | `square`); it **returns a URL**, not a local file. Поэтому каждый сгенерированный лист или страница должны быть скачаны в каталог вывода.

**Требование к файлу подсказки (жёстко)**: запиши полный финальный prompt каждого изображения в отдельный файл в `prompts/` (имя: `NN-{type}-[slug].md`) **ПРЕЖДЕ** вызова `image_generate`. Файл подсказки служит записью воспроизводимости.

**Сопоставление соотношений сторон** — поле `aspect_ratio` в storyboard сопоставляется с форматом `image_generate` так:

| Соотношение storyboard | Формат `image_generate` |
|------------------------|------------------------|
| `3:4`, `9:16`, `2:3`   | `portrait` |
| `4:3`, `16:9`, `3:2`   | `landscape` |
| `1:1`                  | `square` |

**Шаг загрузки** — после каждого вызова `image_generate`:
1. Считай URL из результата инструмента.
2. Скачай байты изображения, указав **абсолютный** путь вывода, например
   ```bash
   curl -fsSL "<url>" -o /abs/path/to/comic/<slug>/NN-page-<slug>.png
   ```
3. Убедись, что файл существует и не пустой по этому точному пути, прежде чем переходить к следующей странице.

**Никогда не полагайся на текущий каталог CWD для путей `-o`.** CWD в постоянном терминальном сеансе может измениться между пакетами (истечение `TERMINAL_LIFETIME_SECONDS`, неудачный `cd` и т.п.). `curl -o relative/path.png` — скрытая ловушка: если CWD сдвинулся, файл окажется в другом месте без ошибки. **Всегда передавай полностью квалифицированный абсолютный путь к `-o`**, либо указывай `workdir=<abs path>` в терминальном инструменте. Инцидент апрель 2026: страницы 06‑09 десятстраничного комикса оказались в корне репозитория вместо `comic/<slug>/` из‑за того, что пакет 3 унаследовал устаревший CWD от пакета 2, и `curl -o 06-page-skills.png` записал файл в неверный каталог. Агент затем несколько ходов утверждал, что файлы существуют, хотя их там не было.

**7.1 Character sheet** — генерируй её (в `characters/characters.png`, соотношение `landscape`), когда комикс многостраничный с повторяющимися персонажами. Пропускай для простых пресетов (например, четырёхпанельный минимализм) или одностраничных комиксов. Файл подсказки `characters/characters.md` должен существовать до вызова `image_generate`. Сгенерированный PNG — **артефакт для проверки человеком** (чтобы пользователь мог визуально оценить дизайн персонажей) и справочный материал для последующей регенерации или ручного редактирования подсказок — он **не управляет** Step 7.2. Подсказки страниц уже записаны в Step 5 из **текстовых описаний** в `characters/characters.md`; `image_generate` не принимает изображения как визуальный ввод.

**7.2 Pages** — подсказка каждой страницы ДОЛЖНА уже находиться в `prompts/NN-{cover|page}-[slug].md` до вызова `image_generate`. Поскольку `image_generate` работает только с подсказками, согласованность персонажей обеспечивается **встраиванием описаний персонажей (из `characters/characters.md`) непосредственно в каждую подсказку страницы на этапе Step 5**. Встраивание происходит одинаково, независимо от того, был ли создан PNG лист в 7.1; PNG служит лишь вспомогательным материалом для проверки/регенерации.

**Правило резервного копирования**: существующие файлы `prompts/…md` и `…png` переименовывай, добавляя суффикс `-backup-YYYYMMDD-HHMMSS` перед регенерацией.

Полный пошаговый workflow (анализ, storyboard, контрольные точки, варианты регенерации): [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/workflow.md).
## Ссылки

**Базовые шаблоны**:
- [analysis-framework.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/analysis-framework.md) – глубокий анализ контента
- [character-template.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/character-template.md) – формат описания персонажа
- [storyboard-template.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/storyboard-template.md) – структура раскадровки
- [ohmsha-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/ohmsha-guide.md) – особенности манги Ohmsha

**Определения стилей**:
- `references/art-styles/` – стили искусства (ligne-claire, manga, realistic, ink-brush, chalk, minimalist)
- `references/tones/` – тона (neutral, warm, dramatic, romantic, energetic, vintage, action)
- `references/presets/` – пресеты со специальными правилами (ohmsha, wuxia, shoujo, concept-story, four-panel)
- `references/layouts/` – макеты (standard, cinematic, dense, splash, mixed, webtoon, four-panel)

**Рабочий процесс**:
- [workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/workflow.md) – подробное описание полного рабочего процесса
- [auto-selection.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/auto-selection.md) – анализ сигналов контента
- [partial-workflows.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/creative/baoyu-comic/references/partial-workflows.md) – варианты частичных рабочих процессов
## Модификация страницы

| Действие | Шаги |
|----------|------|
| **Edit** | **Сначала обнови prompt‑файл** → перегенерируй изображение → скачай новый PNG |
| **Add** | Создай prompt в нужной позиции → сгенерируй с встроенными описаниями персонажей → перенумеруй последующие → обнови storyboard |
| **Delete** | Удали файлы → перенумеруй последующие → обнови storyboard |

**IMPORTANT**: При обновлении страниц **ВСЕГДА** сначала обновляй prompt‑файл (`prompts/NN-{cover|page}-[slug].md`), а затем перегенерируй. Это гарантирует, что изменения задокументированы и воспроизводимы.
## Подводные камни

- Генерация изображений: 10–30 секунд на страницу; автоматический повтор один раз при ошибке
- **Всегда скачивай** URL, возвращённый `image_generate`, в локальный PNG — последующие инструменты (и проверка пользователем) ожидают файлы в каталоге вывода, а не временные URL
- **Используй абсолютные пути для `curl -o`** — никогда не полагайся на текущий рабочий каталог `persistent-shell` между пакетами. Скрытая ловушка: файлы оказываются в неправильном каталоге, и последующий `ls` по ожидаемому пути ничего не показывает. См. Шаг 7 «Download step».
- Используй стилизованные альтернативы для чувствительных публичных фигур
- **Требуется подтверждение Шага 2** — не пропускай
- **Шаги 4/6 условные** — только если пользователь запросил их в Шаге 2
- **Шаг 7.1 лист персонажа** — рекомендуется для многостраничных комиксов, необязательно для простых пресетов. PNG служит вспомогательным материалом для проверки/перегенерации; подсказки страниц (написанные в Шаге 5) используют текстовые описания из `characters/characters.md`, а не PNG. `image_generate` не принимает изображения как визуальный ввод
- **Удаляй секреты** — сканируй исходный контент на наличие API‑ключей, токенов или учётных данных перед записью любого выходного файла