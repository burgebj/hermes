---
title: "Гиперкадры"
sidebar_label: "Hyperframes"
description: "Создай видеокомпозиции на основе HTML, анимированные титульные карточки, социальные оверлеи, видео с говорящей головой и субтитрами, аудио‑реактивные визуалы и шейдерные переходы."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# HyperFrames

Создавай видеокомпозиции на основе HTML, анимированные титульные карточки, социальные оверлеи, видео с говорящей головой и субтитрами, визуалы, реагирующие на звук, и переходы‑шейдеры с помощью HyperFrames. HTML — источник правды для видео. Используй, когда пользователь хочет получить отрендеренный MP4/WebM из HTML‑композиции, анимировать текст/логотипы/диаграммы поверх медиа, синхронизировать субтитры с аудио, добавить озвучивание TTS или преобразовать веб‑сайт в видео.
## Метаданные навыка

| | |
|---|---|
| Источник | Опционально — установить с помощью `hermes skills install official/creative/hyperframes` |
| Путь | `optional-skills/creative/hyperframes` |
| Версия | `1.0.0` |
| Автор | heygen-com |
| Лицензия | Apache-2.0 |
| Платформы | linux, macos, windows |
| Теги | `creative`, `video`, `animation`, `html`, `gsap`, `motion-graphics` |
| Связанные навыки | [`manim-video`](/docs/user-guide/skills/bundled/creative/creative-manim-video), [`meme-generation`](/docs/user-guide/skills/optional/creative/creative-meme-generation) |
:::info
Следующее — полное определение скилла, которое Hermes загружает, когда этот скилл вызывается. Это то, что агент видит как инструкции, когда скилл активен.
:::

# HyperFrames

HTML — источник правды для видео. Композиция — это HTML‑файл с атрибутами `data-*` для тайминга, тайм‑линией GSAP для анимации и CSS для оформления. Движок HyperFrames захватывает страницу кадр за кадром и кодирует её в MP4/WebM с помощью FFmpeg.

**Дополнение к `manim-video`:** Используй `manim-video` для математических/геометрических объяснений (уравнения, в стиле 3B1B). Используй `hyperframes` для моушн‑графики, говорящей головы с субтитрами, презентаций продуктов, социальных наложений, переходов шейдеров и всего, что основано на реальном видеоматериале/аудио.
## Когда использовать

- Пользователь запрашивает отрендеренное видео из текста, сценария или веб‑страницы
- Анимированные титульные карточки, нижние титры или типографические интро
- Видео с озвучкой и субтитрами (TTS + субтитры, синхронные с формой волны)
- Визуализации, реагирующие на звук (синхронизация с битом, спектральные полосы, пульсирующее свечение)
- Переходы «сцена‑к‑сцене» (кроссфейд, вытирание, искажение шейдером, вспышка‑через‑белый)
- Социальные оверлеи (в стиле Instagram/TikTok/YouTube)
- Конвейер «веб‑страница‑в‑видео» (захват URL, создание промо‑ролика)
- Любая анимация HTML/CSS/JS, которую необходимо детерминированно отрендерить в видеофайл

Не используй этот **skill** для:
- Чистой математической/уравнительной анимации (→ `manim-video`)
- Генерации изображений или мемов (→ `meme-generation`, image models)
- Живой видеоконференции или трансляций
## Быстрая справка

```bash
npx hyperframes init my-video               # scaffold a project
cd my-video
npx hyperframes lint                        # validate before preview/render
npx hyperframes preview                     # live-reload browser preview (port 3002)
npx hyperframes render --output final.mp4   # render to MP4
npx hyperframes doctor                      # diagnose environment issues
```

Флаги рендеринга: `--quality draft|standard|high` · `--fps 24|30|60` · `--format mp4|webm` · `--docker` (воспроизводимый) · `--strict`.

Полная справка по CLI: [references/cli.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/cli.md).
## Установка (однократно)

```bash
bash "$(dirname "$(find ~/.hermes/skills -path '*/hyperframes/SKILL.md' 2>/dev/null | head -1)")/scripts/setup.sh"
```

Скрипт:
1. Проверяет, что установлен Node.js ≥ 22 и FFmpeg (выводит инструкции по исправлению, если нет).
2. Устанавливает `hyperframes` CLI глобально (`npm install -g hyperframes@>=0.4.2`).
3. Предварительно кэширует `chrome-headless-shell` через Puppeteer — **обязательно** для получения наилучшего качества рендеринга через путь захвата `HeadlessExperimental.beginFrame` в Chrome.
4. Запускает `npx hyperframes doctor` и сообщает результат.

См. [references/troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/troubleshooting.md), если настройка не удалась.
## Procedure

### 1. Планируй перед написанием HTML

Прежде чем трогать код, сформулируй на высоком уровне:
- **Что** — сюжетная арка, ключевые моменты, эмоциональные удары
- **Структура** — композиции, дорожки (видео/аудио/оверлеи), длительности
- **Визуальная идентичность** — цвета, шрифты, характер анимации (взрывная / кинематографичная / плавная / техническая)
- **Геройский кадр** — для каждой сцены момент, когда большинство элементов видны одновременно. Это статический макет, который ты построишь первым.

**Визуальная идентичность (HARD‑GATE).** Перед написанием ЛЮБОЙ HTML‑композиции должна быть определена визуальная идентичность. Не используй композиции с дефолтными или общими цветами (`#333`, `#3b82f6`, `Roboto` — признаки пропуска этого шага). Проверяй в порядке:

1. **`DESIGN.md` в корне проекта?** → используй его точные цвета, шрифты, правила анимации и ограничения «Что НЕ делать».
2. **Пользователь назвал стиль** (например, «Swiss Pulse», «dark and techy», «luxury brand»)? → сгенерируй минимальный `DESIGN.md` с разделами `## Style Prompt`, `## Colors` (3‑5 hex‑значений с ролями), `## Typography` (1‑2 семейства), `## What NOT to Do` (3‑5 анти‑паттернов).
3. **Ни то, ни другое?** → задай 3 вопроса перед написанием любого HTML:
   - Настроение? (взрывное / кинематографичное / плавное / техническое / хаотичное / тёплое)
   - Светлое или тёмное полотно?
   - Есть ли фирменные цвета, шрифты или визуальные референсы?

   Затем создай `DESIGN.md` на основе ответов. Каждая композиция должна отсылать свою палитру и типографику к `DESIGN.md` или явному указанию пользователя.

### 2. Каркас

```bash
npx hyperframes init my-video --non-interactive
```

Шаблоны: `blank`, `warm-grain`, `play-mode`, `swiss-grid`, `vignelli`, `decision-tree`, `kinetic-type`, `product-promo`, `nyt-graph`. Выбери один через `--example <name>`, добавь медиа через `--video clip.mp4` или `--audio track.mp3`.

### 3. Разметка перед анимацией

Сначала напиши статический `HTML+CSS` для **геройского кадра** — без GSAP. Контейнер `.scene-content` должен заполнять сцену (`width:100%; height:100%; padding:Npx`) и иметь `display:flex` + `gap`. Используй отступы, чтобы «втянуть» контент внутрь — никогда не ставь `position:absolute; top:Npx` на контейнер контента (контент будет вылезать, если он выше оставшегося пространства).

Только после того, как геройский кадр выглядит правильно, добавляй входные анимации `gsap.from()` (анимировать **к** CSS‑позиции) и выходные `gsap.to()` (анимировать **из** неё).

См. [references/composition.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/composition.md) для полной схемы `data‑attribute` и правил композиции.

### 4. Анимация с GSAP

Каждая композиция должна:
- Зарегистрировать свою тайм‑линию: `window.__timelines["<composition-id>"] = tl`
- Запускать её в паузе: `gsap.timeline({ paused: true })` — управление воспроизведением находится у плеера
- Использовать конечные значения `repeat` (без `repeat: -1` — ломает движок захвата). Вычисляй: `repeat: Math.ceil(duration / cycleDuration) - 1`.
- Быть детерминированной — без `Math.random()`, `Date.now()` и любой логики, зависящей от реального времени. При необходимости псевдослучайности используй сидированный PRNG.
- Строить синхронно — без `async/await`, `setTimeout` и `Promise` вокруг построения тайм‑линии.

См. [references/gsap.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/gsap.md) для базового API GSAP (tweens, eases, stagger, timelines).

### 5. Переходы между сценами

Для многосценных композиций требуются переходы. Правила:
1. **Всегда используй переход между сценами** — без резких скачков.
2. **Всегда используй входные анимации** для каждого элемента сцены (`gsap.from(...)`).
3. **Никогда не используй выходные анимации**, кроме финальной сцены — переход сам является выходом.
4. Финальная сцена может затухать.

Установи шейдерные переходы через `npx hyperframes add <transition-name>` (`flash-through-white`, `liquid-wipe` и т.п.). Полный список: `npx hyperframes add --list`.

### 6. Аудио, субтитры, TTS, аудио‑реактивность, выделение

- **Аудио:** всегда отдельный элемент `<audio>` (видео — `muted playsinline`).
- **TTS:** `npx hyperframes tts "Script text" --voice af_nova --output narration.wav`. Список голосов — `--list`. Первая буква ID голоса кодирует язык (`a`/`b` = English, `e` = Spanish, `f` = French, `j` = Japanese, `z` = Mandarin и т.д.) — CLI автоматически определяет локаль фонемизатора; `--lang` указывай только для переопределения. Для неанглийской фонемизации требуется системный `espeak-ng`.
- **Субтитры:** `npx hyperframes transcribe narration.wav` → транскрипция по словам. Выбирай стиль из тона транскрипции (hype / corporate / tutorial / storytelling / social — см. таблицу в `references/features.md`). **Языковое правило:** никогда не используй модели `.en` Whisper, если аудио не подтверждено как английское — `.en` переводит, а не транскрибирует. Каждая группа субтитров ДОЛЖНА иметь жёсткий `tl.set(el, { opacity: 0, visibility: "hidden" }, group.end)` для удаления после выхода — иначе группы «протекают» в последующие.
- **Аудио‑реактивные визуалы:** предварительно извлеки аудио‑полосы (bass / mid / treble) и берись за образцы по кадру внутри тайм‑линии через `for`‑цикл `tl.call(draw, [], f / fps)` — один длинный твин не реагирует на аудио. Отображай bass → `scale` (пульс), treble → `textShadow`/`boxShadow` (сияние), общую амплитуду → `opacity`/`y`/`backgroundColor`. Избегай клише «полос эквалайзера» — визуал должен подстраиваться под контент, аудио лишь управляет поведением.
- **Выделение в стиле маркера:** highlight, circle, burst, scribble, sketchout‑эффекты для акцента текста — детерминированный CSS + GSAP, см. `references/features.md#marker-highlighting`. Полностью перемотаемый, без анимированных SVG‑фильтров.
- **Переходы сцен:** каждая многосценная композиция ДОЛЖНА использовать переходы (без резких скачков). Выбирай из CSS‑примитивов (push slide, blur crossfade, zoom through, staggered blocks) или шейдерных переходов (`flash-through-white`, `liquid-wipe`, `cross-warp-morph`, `chromatic-split` и т.п.) через `npx hyperframes add`. Таблицы настроения и энергии находятся в `references/features.md#transitions`. Не смешивай CSS‑ и шейдерные переходы в одной композиции.

### 7. Линт, валидация, инспекция, предпросмотр, рендер

```bash
npx hyperframes lint              # catches missing data-composition-id, overlapping tracks, unregistered timelines
npx hyperframes validate          # WCAG contrast audit at 5 timestamps
npx hyperframes inspect           # visual layout audit — overflow, off-frame elements, occluded text
npx hyperframes preview           # live browser preview
npx hyperframes render --quality draft --output draft.mp4    # fast iteration
npx hyperframes render --quality high --output final.mp4     # final delivery
```

`hyperframes validate` проверяет фоновые пиксели позади каждого текстового элемента и предупреждает о контрасте ниже 4.5:1 (или 3:1 для крупного текста). `hyperframes inspect` — вспомогательный инструмент для проверки разметки: запускает страницу в разные моменты времени и отмечает проблемы, которые не видит статический линт (субтитр, выходящий за безопасную зону только на 4.5 s, карточка, переполняющаяся при самом длинном заголовке, элемент, оказавшийся позади шейдерного перехода). Запускай `inspect`, особенно для композиций с речевыми пузырями, карточками, субтитрами или плотной типографикой.

### 8. Сайт‑в‑видео (если пользователь дал URL)

Используй 7‑шаговый workflow захвата‑в‑видео из [references/website-to-video.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/website-to-video.md): capture → DESIGN.md → SCRIPT.md → storyboard → composition → render → deliver.
## Подводные камни

- **`HeadlessExperimental.beginFrame` wasn't found** — в Chromium 147+ этот протокол удалён. Убедись, что используешь `hyperframes@>=0.4.2` (автоматически определяет и переходит в режим скриншота). Обходной вариант: `export PRODUCER_FORCE_SCREENSHOT=true`. См. [hyperframes#294](https://github.com/heygen-com/hyperframes/issues/294) и [references/troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/troubleshooting.md).
- **System Chrome (не `chrome-headless-shell`)** — рендеринг «виснет» 120 сек, затем происходит тайм‑аут. Запусти `npx puppeteer browsers install chrome-headless-shell` (setup.sh делает это). `hyperframes doctor` покажет, какой бинарный файл будет использован.
- **`repeat: -1` где‑либо** — ломает движок захвата. Всегда вычисляй конечное количество повторов.
- **`gsap.set()` на клип‑элементах, которые появляются позже** — элемент ещё не существует при загрузке страницы. Используй `tl.set(selector, vars, timePosition)` внутри таймлайна, в момент или после `data-start` клипа.
- **`<br>` внутри текста контента** — принудительные разрывы не учитывают ширину шрифта, поэтому естественный перенос + `<br>` приводит к двойному разрыву. Используй `max-width`, чтобы текст переносился автоматически. Исключение: короткие заголовки отображения, где каждое слово намеренно размещено на отдельной строке.
- **Анимация `visibility` или `display`** — GSAP не умеет анимировать эти свойства. Используй `autoAlpha` (обрабатывает и видимость, и непрозрачность).
- **Вызов `video.play()` или `audio.play()`** — воспроизведение контролируется фреймворком. Никогда не вызывай их самостоятельно.
- **Построение таймлайнов асинхронно** — движок захвата читает `window.__timelines` синхронно после загрузки страницы. Никогда не оборачивай построение таймлайна в `async`, `setTimeout` или Promise.
- **Отдельный `index.html`, обёрнутый в `<template>`** — скрывает всё содержимое от браузера. Только **подкомпозиции**, загружаемые через `data-composition-src`, используют `<template>`.
- **Использование видео для аудио** — всегда используй `<video>` с отключённым звуком + отдельный `<audio>`.
## Проверка

До и после рендеринга:

1. **Lint + validate + inspect проходят:** `npx hyperframes lint --strict && npx hyperframes validate && npx hyperframes inspect` (lint ловит структурные проблемы, validate — контраст, inspect — визуальное расположение / переполнение — см. troubleshooting.md, если появляются предупреждения).
2. **Хореография анимации** — для новых композиций или значительных изменений анимации запусти карту анимаций. `npx hyperframes init` копирует скрипты skill в проект, поэтому путь локален для проекта:
      ```bash
   node skills/hyperframes/scripts/animation-map.mjs <composition-dir> \
     --out <composition-dir>/.hyperframes/anim-map
   ```
   Выводит один файл `animation-map.json` с сводками по каждому твину, ASCII‑диаграммой Ганта, обнаружением стэггеров, «мёртвыми зонами» (> 1 с без анимации), жизненными циклами элементов и флагами (`offscreen`, `collision`, `invisible`, `paced-fast` <0.2s, `paced-slow` >2s). Просмотри сводки и флаги — исправь или обоснуй каждый. Пропускай при небольших правках.
3. **Файл существует + не пустой:** `ls -lh final.mp4`.
4. **Продолжительность совпадает с `data-duration`:** `ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 final.mp4`.
5. **Визуальная проверка:** извлеки кадр из середины композиции: `ffmpeg -i final.mp4 -ss 00:00:05 -vframes 1 preview.png`.
6. **Аудио присутствует, если ожидается:** `ffprobe -v error -show_streams -select_streams a -of default=nw=1:nk=1 final.mp4 | head -1`.

Если `hyperframes render` не удаётся, запусти `npx hyperframes doctor` и приложи его вывод при сообщении об ошибке.
## Ссылки

- [composition.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/composition.md) — атрибуты данных, контракт таймлайна, неотъемлемые правила, правила типографии/ресурсов
- [cli.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/cli.md) — все команды CLI (`init`, `capture`, `lint`, `validate`, `inspect`, `preview`, `render`, `transcribe`, `tts`, `doctor`, `browser`, `info`, `upgrade`, `benchmark`)
- [gsap.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/gsap.md) — ядро API GSAP для HyperFrames (`tweens`, `eases`, `stagger`, `timelines`, `matchMedia`)
- [features.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/features.md) — субтитры, TTS, аудиореактивный, выделение маркеров, переходы (загрузка по запросу)
- [website-to-video.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/website-to-video.md) — семишаговый рабочий процесс захвата‑в‑видео
- [troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/troubleshooting.md) — исправление OpenClaw, переменные окружения, распространённые ошибки рендеринга