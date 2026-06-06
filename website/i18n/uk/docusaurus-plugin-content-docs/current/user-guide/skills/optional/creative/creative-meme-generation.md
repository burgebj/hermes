---
title: "Генерація мемів — Створюй реальні зображення мемів, вибираючи шаблон і накладаючи текст за допомогою Pillow"
sidebar_label: "Meme Generation"
description: "Створюй реальні мем‑зображення, вибираючи шаблон і накладаючи текст за допомогою Pillow"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Генерація мемів

Генеруй реальні зображення мемів, вибираючи шаблон і накладаючи текст за допомогою Pillow. Створює справжні файли .png мемів.

## Метадані навички

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

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Генерація мемів

Генеруй реальні зображення мемів за темою. Вибирає шаблон, пише підписи та рендерить справжній файл .png з накладеним текстом.

## Коли використовувати

- Користувач просить тебе створити або згенерувати мем
- Користувач хоче мем про конкретну тему, ситуацію або розчарування
- Користувач каже «meme this» або подібне

## Доступні шаблони

Скрипт підтримує **будь‑який з ~100 популярних шаблонів imgflip** за назвою або ID, плюс 10 відібраних шаблонів з ручним розташуванням тексту.

### Відібрані шаблони (кастомне розташування тексту)

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

### Динамічні шаблони (з API imgflip)

Будь‑який шаблон, якого немає у відібраному списку, можна використати за назвою або ID imgflip. Для них застосовується розумне розташування тексту за замовчуванням (top/bottom для 2‑полів, рівномірно розподілене для 3+). Пошук за:
```bash
python "$SKILL_DIR/scripts/generate_meme.py" --search "disaster"
```

## Процедура

### Режим 1: Класичний шаблон (за замовчуванням)

1. Прочитай тему користувача та визнач основну динаміку (хаос, дилема, перевага, іронія тощо).
2. Вибери шаблон, який найкраще підходить. Використай колонку «Best for» або пошук з `--search`.
3. Напиши короткі підписи для кожного поля (8‑12 слів максимум у полі, коротше — краще).
4. Знайди каталог скрипту навички:
   ```
   SKILL_DIR=$(dirname "$(find ~/.hermes/skills -path '*/meme-generation/SKILL.md' 2>/dev/null | head -1)")
   ```
5. Запусти генератор:
   ```bash
   python "$SKILL_DIR/scripts/generate_meme.py" <template_id> /tmp/meme.png "caption 1" "caption 2" ...
   ```
6. Поверни зображення за `MEDIA:/tmp/meme.png`.

### Режим 2: Кастомне AI‑зображення (коли доступний `image_generate`)

Використовуй цей режим, коли жоден класичний шаблон не підходить або коли користувач хоче щось оригінальне.

1. Спочатку напиши підписи.
2. Використай `image_generate` для створення сцени, що відповідає концепції мему. **Не включай жодного тексту** у підказку до зображення — текст буде додано скриптом. Описуй лише візуальну сцену.
3. Знайди шлях до згенерованого зображення у URL результату `image_generate`. За потреби завантаж його локально.
4. Запусти скрипт з `--image` для накладання тексту, вибираючи режим:
   - **Overlay** (текст безпосередньо на зображенні, білий з чорним контуром):
     ```bash
     python "$SKILL_DIR/scripts/generate_meme.py" --image /path/to/scene.png /tmp/meme.png "top text" "bottom text"
     ```
   - **Bars** (чорні смуги зверху/знизу з білим текстом — чистіше, завжди читається):
     ```bash
     python "$SKILL_DIR/scripts/generate_meme.py" --image /path/to/scene.png --bars /tmp/meme.png "top text" "bottom text"
     ```
   Використовуй `--bars`, коли зображення зайняте/детальне і текст важко читати поверх нього.
5. **Перевірка за допомогою vision** (якщо доступний `vision_analyze`): переконайся, що результат виглядає добре:
   ```
   vision_analyze(image_url="/tmp/meme.png", question="Is the text legible and well-positioned? Does the meme work visually?")
   ```
   Якщо модель vision виявляє проблеми (текст важко читати, погане розташування тощо), спробуй інший режим (перемикай між overlay і bars) або згенеруй сцену заново.
6. Поверни зображення за `MEDIA:/tmp/meme.png`.

## Приклади

**«debugging production at 2 AM»:**
```bash
python generate_meme.py this-is-fine /tmp/meme.png "SERVERS ARE ON FIRE" "This is fine"
```

**«choosing between sleep and one more episode»:**
```bash
python generate_meme.py drake /tmp/meme.png "Getting 8 hours of sleep" "One more episode at 3 AM"
```

**«the stages of a Monday morning»:**
```bash
python generate_meme.py expanding-brain /tmp/meme.png "Setting an alarm" "Setting 5 alarms" "Sleeping through all alarms" "Working from bed"
```

## Перелік шаблонів

Щоб переглянути всі доступні шаблони:
```bash
python generate_meme.py --list
```

## Підводні камені

- Тримай підписи **КОРОТКИМИ**. Меми з довгим текстом виглядають жахливо.
- Відповідність кількості текстових аргументів кількості полів шаблону.
- Вибирай шаблон, який підходить до структури жарту, а не лише до теми.
- Не генеруй ненависницький, образливий або персонально спрямований контент.
- Скрипт кешує зображення шаблонів у `scripts/.cache/` після першого завантаження.

## Перевірка

Вихід вважається правильним, якщо:

- Створено файл .png за вказаним шляхом виводу;
- Текст читабельний (білий з чорним контуром) на шаблоні;
- Жарт «влучає» — підпис відповідає передбаченій структурі шаблону;
- Файл можна доставити через шлях `MEDIA:`.