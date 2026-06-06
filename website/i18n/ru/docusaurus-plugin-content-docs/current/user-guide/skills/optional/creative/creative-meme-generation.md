---
title: "Генерация мемов — Создавай реальные изображения мемов, выбирая шаблон и накладывая текст с помощью Pillow"
sidebar_label: "Meme Generation"
description: "Создавай реальные мем‑изображения, выбирая шаблон и накладывая текст с помощью Pillow"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Генерация мемов

Создавай реальные изображения мемов, выбирая шаблон и накладывая текст с помощью Pillow. Получаются настоящие файлы .png мемов.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/creative/meme-generation` |
| Path | `optional-skills/creative/meme-generation` |
| Version | `2.0.0` |
| Author | adanaleycio |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `creative`, `memes`, `humor`, `images` |
| Related skills | [`ascii-art`](/docs/user-guide/skills/bundled/creative/creative-ascii-art), `generative-widgets` |

## Справочник: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Генерация мемов

Создавай реальные изображения мемов по теме. Выбирает шаблон, пишет подписи и рендерит настоящий файл .png с наложенным текстом.

## Когда использовать

- Пользователь просит тебя сделать или сгенерировать мем
- Пользователь хочет мем о конкретной теме, ситуации или фрустрации
- Пользователь говорит «meme this» или что‑то в этом роде

## Доступные шаблоны

Скрипт поддерживает **любой из ~100 популярных шаблонов imgflip** по имени или ID, плюс 10 отобранных шаблонов с ручной настройкой позиционирования текста.

### Отобранные шаблоны (кастомное размещение текста)

| ID | Name | Fields | Best for |
|----|------|--------|----------|
| `this-is-fine` | This is Fine | top, bottom | chaos, denial |
| `drake` | Drake Hotline Bling | reject, approve | rejecting/preferring |
| `distracted-boyfriend` | Distracted Boyfriend | distraction, current, person | temptation, shifting priorities |
| `two-buttons` | Two Buttons | left, right, person | impossible choice |
| `expanding-brain` | Expanding Brain | 4 levels | escalating irony |
| `change-my-mind` | Change My Mind | statement | hot takes |
| `woman-yelling-at-cat` | Woman Yelling at Cat | woman, cat | arguments |
| `one-does-not-simply` | One Does Not Simply | top, bottom | deceptively hard things |
| `grus-plan` | Gru's Plan | step1-3, realization | plans that backfire |
| `batman-slapping-robin` | Batman Slapping Robin | robin, batman | shutting down bad ideas |

### Динамические шаблоны (через API imgflip)

Любой шаблон, не входящий в отобранный список, можно использовать по имени или ID imgflip. Для них применяется умное позиционирование текста по умолчанию (top/bottom для 2‑полей, равномерно распределённое для 3+). Поиск осуществляется с помощью:
```bash
python "$SKILL_DIR/scripts/generate_meme.py" --search "disaster"
```

## Процедура

### Режим 1: Классический шаблон (по умолчанию)

1. Прочитай тему пользователя и определи основной динамический элемент (хаос, дилемма, предпочтение, ирония и т.д.).
2. Выбери шаблон, который лучше всего подходит. Используй колонку «Best for» или поиск с `--search`.
3. Напиши короткие подписи для каждого поля (не более 8‑12 слов на поле, короче — лучше).
4. Найди каталог скрипта навыка:
   ```
   SKILL_DIR=$(dirname "$(find ~/.hermes/skills -path '*/meme-generation/SKILL.md' 2>/dev/null | head -1)")
   ```
5. Запусти генератор:
   ```bash
   python "$SKILL_DIR/scripts/generate_meme.py" <template_id> /tmp/meme.png "caption 1" "caption 2" ...
   ```
6. Верни изображение с `MEDIA:/tmp/meme.png`

### Режим 2: Пользовательское AI‑изображение (если доступен image_generate)

Используй этот режим, когда ни один классический шаблон не подходит или пользователь хочет что‑то оригинальное.

1. Сначала напиши подписи.
2. Используй `image_generate` для создания сцены, соответствующей концепции мема. **Не включай текст в запрос к изображению** — текст будет добавлен скриптом. Описывай только визуальную сцену.
3. Найди путь к сгенерированному изображению из URL результата `image_generate`. При необходимости скачай его локально.
4. Запусти скрипт с `--image` для наложения текста, выбрав режим:
   - **Overlay** (текст непосредственно на изображении, белый с чёрным контуром):
     ```bash
     python "$SKILL_DIR/scripts/generate_meme.py" --image /path/to/scene.png /tmp/meme.png "top text" "bottom text"
     ```
   - **Bars** (чёрные полосы сверху/снизу с белым текстом — чище, всегда читаемо):
     ```bash
     python "$SKILL_DIR/scripts/generate_meme.py" --image /path/to/scene.png --bars /tmp/meme.png "top text" "bottom text"
     ```
   Используй `--bars`, когда изображение перегружено деталями и текст будет трудно читать поверх него.
5. **Проверь с помощью vision** (если доступен `vision_analyze`): убедись, что результат выглядит хорошо:
   ```
   vision_analyze(image_url="/tmp/meme.png", question="Is the text legible and well-positioned? Does the meme work visually?")
   ```
   Если модель vision отмечает проблемы (трудно читаемый текст, плохое размещение и т.д.), попробуй другой режим (переключись между overlay и bars) или сгенерируй сцену заново.
6. Верни изображение с `MEDIA:/tmp/meme.png`

## Примеры

**«отладка продакшна в 2 утра»:**
```bash
python generate_meme.py this-is-fine /tmp/meme.png "SERVERS ARE ON FIRE" "This is fine"
```

**«выбор между сном и ещё одним эпизодом»:**
```bash
python generate_meme.py drake /tmp/meme.png "Getting 8 hours of sleep" "One more episode at 3 AM"
```

**«этапы понедельника утром»:**
```bash
python generate_meme.py expanding-brain /tmp/meme.png "Setting an alarm" "Setting 5 alarms" "Sleeping through all alarms" "Working from bed"
```

## Список шаблонов

Чтобы увидеть все доступные шаблоны:
```bash
python generate_meme.py --list
```

## Подводные камни

- Делай подписи КОРОТКИМИ. Мемы с длинным текстом выглядят ужасно.
- Соответствуй количество текстовых аргументов количеству полей шаблона.
- Выбирай шаблон, который подходит к структуре шутки, а не только к теме.
- Не генерируй оскорбительный, ненавистный или персонально направленный контент.
- Скрипт кэширует изображения шаблонов в `scripts/.cache/` после первой загрузки.

## Проверка

Вывод считается корректным, если:
- На пути вывода создан файл .png
- Текст читаем (белый с чёрным контуром) на шаблоне
- Шутка «заходит» — подпись соответствует предполагаемой структуре шаблона
- Файл можно доставить через путь `MEDIA:`