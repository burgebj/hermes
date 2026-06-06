---
title: "Гіперрамки"
sidebar_label: "Hyperframes"
description: "Створюй HTML‑базовані відео‑композиції, анімовані титульні картки, соціальні накладки, відео‑розмови з субтитрами, аудіореактивні візуали та шейдерні переходи."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Hyperframes

Створюй відео‑композиції на основі HTML, анімовані титульні картки, соціальні накладки, відео‑розмови з субтитрами, аудіореактивну візуалізацію та шейдерні переходи за допомогою HyperFrames. HTML — це джерело правди для відео. Використовуй, коли користувач хоче отримати готовий MP4/WebM з HTML‑композиції, анімувати текст/логотипи/діаграми на медіа, синхронізувати субтитри з аудіо, додати TTS‑нарацію або перетворити веб‑сайт у відео.
## Метадані навички

| | |
|---|---|
| Джерело | Необов’язково — встановити за допомогою `hermes skills install official/creative/hyperframes` |
| Шлях | `optional-skills/creative/hyperframes` |
| Версія | `1.0.0` |
| Автор | heygen-com |
| Ліцензія | Apache-2.0 |
| Платформи | linux, macos, windows |
| Теги | `creative`, `video`, `animation`, `html`, `gsap`, `motion-graphics` |
| Пов’язані навички | [`manim-video`](/docs/user-guide/skills/bundled/creative/creative-manim-video), [`meme-generation`](/docs/user-guide/skills/optional/creative/creative-meme-generation) |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# HyperFrames

HTML — це джерело правди для відео. Композиція — це HTML‑файл з атрибутами `data-*` для таймінгу, таймлайном GSAP для анімації та CSS для зовнішнього вигляду. Двигун HyperFrames захоплює сторінку кадр за кадром і кодує її в MP4/WebM за допомогою FFmpeg.

**Complement to `manim-video`:** Use `manim-video` for mathematical/geometric explainers (equations, 3B1B-style). Use `hyperframes` for motion-graphics, talking-head with captions, product tours, social overlays, shader transitions, and anything driven by real video/audio media.
## Коли використовувати

- Користувач запитує готове відео з тексту, сценарію або веб‑сайту
- Анімовані титульні картки, нижні треті або типографічні інтро
- Відео з озвученням та субтитрами (TTS + субтитри, синхронізовані з формою хвилі)
- Візуалізації, що реагують на аудіо (синхронізація з бітом, смуги спектру, пульсуюче світіння)
- Переходи між сценами (crossfade, wipe, shader warp, flash‑through‑white)
- Соціальні оверлеї (стиль Instagram/TikTok/YouTube)
- Конвеєр «веб‑сайт → відео» (захоплення URL, створення промо‑відео)
- Будь‑яка анімація HTML/CSS/JS, яку потрібно детерміновано відтворити у відеофайл

Не використовуйте цей **skill** для:

- Чистих математичних анімацій або анімацій рівнянь (→ `manim-video`)
- Генерації зображень або мемів (→ `meme-generation`, image models)
- Живих відео‑конференцій або трансляцій
## Коротка довідка

```bash
npx hyperframes init my-video               # scaffold a project
cd my-video
npx hyperframes lint                        # validate before preview/render
npx hyperframes preview                     # live-reload browser preview (port 3002)
npx hyperframes render --output final.mp4   # render to MP4
npx hyperframes doctor                      # diagnose environment issues
```

Параметри рендерингу: `--quality draft|standard|high` · `--fps 24|30|60` · `--format mp4|webm` · `--docker` (reproducible) · `--strict`.

Повна довідка CLI: [references/cli.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/cli.md).
## Налаштування (одноразове)

```bash
bash "$(dirname "$(find ~/.hermes/skills -path '*/hyperframes/SKILL.md' 2>/dev/null | head -1)")/scripts/setup.sh"
```

Скрипт:
1. Перевіряє, чи встановлені Node.js >= 22 та FFmpeg (виводить інструкції з виправлення, якщо ні).
2. Встановлює CLI `hyperframes` глобально (`npm install -g hyperframes@>=0.4.2`).
3. Попередньо кешує `chrome-headless-shell` за допомогою Puppeteer — **обов’язково** для найякіснішого рендерингу через шлях захоплення Chrome `HeadlessExperimental.beginFrame`.
4. Запускає `npx hyperframes doctor` і виводить результат.

Дивись [references/troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/troubleshooting.md), якщо налаштування не вдається.
## Процедура

### 1. Плануй перед написанням HTML

Перш ніж торкатися коду, сформулюй на високому рівні:
- **What** — сюжетна арка, ключові моменти, емоційні удари
- **Structure** — композиції, треки (відео/аудіо/оверлеї), тривалість
- **Visual identity** — кольори, шрифти, характер руху (вибуховий / кінематичний / плавний / технічний)
- **Hero frame** — для кожної сцени момент, коли найбільше елементів одночасно видно. Це статичний макет, який ти спочатку створиш.

**Visual Identity Gate (HARD‑GATE).** Перед написанням будь‑якої композиції HTML має бути визначена візуальна ідентичність. Не пиши композиції з типово‑заданими або загальними кольорами (`#333`, `#3b82f6`, `Roboto` — це ознаки пропуску кроку). Перевір у такому порядку:

1. **`DESIGN.md` у корені проєкту?** → Використай його точні кольори, шрифти, правила руху та обмеження «What NOT to Do».
2. **Користувач назвав стиль** (наприклад, «Swiss Pulse», «dark and techy», «luxury brand»)? → Згенеруй мінімальний `DESIGN.md` з `## Style Prompt`, `## Colors` (3‑5 hex‑кольорів з ролями), `## Typography` (1‑2 сімейства), `## What NOT to Do` (3‑5 анти‑патернів).
3. **Ні одного з вищезазначеного?** → Задай 3 питання перед написанням будь‑якого HTML:
   - Настрій? (вибуховий / кінематичний / плавний / технічний / хаотичний / теплий)
   - Світла чи темна канва?
   - Які‑небудь бренд‑кольори, шрифти або візуальні референси?

   Потім згенеруй `DESIGN.md` на основі відповідей. Кожна композиція має відслідковувати свою палітру та типографіку до `DESIGN.md` або явного вказання користувача.

### 2. Scaffold

```bash
npx hyperframes init my-video --non-interactive
```

Шаблони: `blank`, `warm-grain`, `play-mode`, `swiss-grid`, `vignelli`, `decision-tree`, `kinetic-type`, `product-promo`, `nyt-graph`. Передай `--example <name>` для вибору, `--video clip.mp4` або `--audio track.mp3` для старту з медіа.

### 3. Layout before animation

Спочатку напиши статичний HTML+CSS для **hero frame** — без GSAP. Контейнер `.scene-content` має заповнювати сцену (`width:100%; height:100%; padding:Npx`) з `display:flex` + `gap`. Використовуй padding, щоб відштовхнути контент всередину — ніколи `position:absolute; top:Npx` на контейнері контенту (контент виходить за межі, коли він вищий за залишковий простір).

Лише після того, як hero frame виглядає правильно, додавай входи `gsap.from()` (анімуй **до** CSS‑позиції) та виходи `gsap.to()` (анімуй **з** неї).

Дивись [references/composition.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/composition.md) для повної схеми атрибутів `data‑attribute` та правил композиції.

### 4. Animate with GSAP

Кожна композиція повинна:
- Зареєструвати свою таймлайн: `window.__timelines["<composition-id>"] = tl`
- Запускатися у паузі: `gsap.timeline({ paused: true })` — плеєр керує відтворенням
- Використовувати кінцеві значення `repeat` (без `repeat: -1` — руйнує движок захоплення). Обчислюй: `repeat: Math.ceil(duration / cycleDuration) - 1`.
- Бути детермінованою — без `Math.random()`, `Date.now()` або логіки реального часу. Якщо потрібна псевдо‑випадковість, використай PRNG з фіксованим зерном.
- Будувати синхронно — без `async`/`await`, `setTimeout` чи Promise навколо створення таймлайну.

Дивись [references/gsap.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/gsap.md) для основного API GSAP (tweens, eases, stagger, timelines).

### 5. Transitions between scenes

Багатосценічні композиції потребують переходів. Правила:
1. **Always use a transition between scenes** — no jump cuts.
2. **Always use entrance animations** on every scene element (`gsap.from(...)`).
3. **Never use exit animations** except on the final scene — the transition IS the exit.
4. The final scene may fade out.

Встановлюй шейдер‑переходи через `npx hyperframes add <transition-name>` (`flash-through-white`, `liquid-wipe` тощо). Повний список: `npx hyperframes add --list`.

### 6. Audio, captions, TTS, audio‑reactive, highlighting

- **Audio:** завжди окремий `<audio>`‑елемент (відео — `muted playsinline`).
- **TTS:** `npx hyperframes tts "Script text" --voice af_nova --output narration.wav`. Перелік голосів — `--list`. Перша літера ID голосу кодує мову (`a`/`b`=English, `e`=Spanish, `f`=French, `j`=Japanese, `z`=Mandarin тощо) — CLI автоматично визначає локаль фонемізатора; `--lang` передавай лише для перевизначення. Для не‑англійської фонемізації потрібен системний `espeak-ng`.
- **Captions:** `npx hyperframes transcribe narration.wav` → транскрипція на рівні слів. Обирай стиль згідно тону транскрипції (hype / corporate / tutorial / storytelling / social — дивись таблицю у `references/features.md`). **Language rule:** ніколи не використовуйте `.en` whisper‑моделі, якщо аудіо не підтверджено англійським — `.en` перекладає не‑англійське аудіо замість транскрибування. Кожна група субтитрів ПОВИННА мати жорстке `tl.set(el, { opacity: 0, visibility: "hidden" }, group.end)` завершення після вихідного твіну — інакше групи залишаються видимими в наступних.
- **Audio‑reactive visuals:** попередньо екстрагуй аудіо‑діапазони (bass / mid / treble) і підбирай кадр у таймлайні через `for`‑цикл `tl.call(draw, [], f / fps)` — один довгий твін не реагує на аудіо. Відображай bass → `scale` (пульс), treble → `textShadow`/`boxShadow` (світіння), загальна амплітуда → `opacity`/`y`/`backgroundColor`. Уникай кліше еквалайзер‑барів — нехай контент визначає візуал, аудіо керує поведінкою.
- **Marker‑style highlighting:** підсвічування, коло, вибух, скретч, скетч‑ефекти для акценту тексту — детерміновані CSS+GSAP — дивись `references/features.md#marker-highlighting`. Повністю перемотуються, без анімованих SVG‑фільтрів.
- **Scene transitions:** кожна багатосценічна композиція ПОВИННА використовувати переходи (без різких стрибків). Обирай між CSS‑примітивами (push slide, blur crossfade, zoom through, staggered blocks) або шейдер‑переходами (`flash-through-white`, `liquid-wipe`, `cross-warp-morph`, `chromatic‑split` тощо) через `npx hyperframes add`. Таблиці настрою та енергії — у `references/features.md#transitions`. Не змішуй CSS‑ та шейдер‑переходи в одній композиції.

### 7. Lint, validate, inspect, preview, render

```bash
npx hyperframes lint              # catches missing data-composition-id, overlapping tracks, unregistered timelines
npx hyperframes validate          # WCAG contrast audit at 5 timestamps
npx hyperframes inspect           # visual layout audit — overflow, off-frame elements, occluded text
npx hyperframes preview           # live browser preview
npx hyperframes render --quality draft --output draft.mp4    # fast iteration
npx hyperframes render --quality high --output final.mp4     # final delivery
```

`hyperframes validate` зразкові пікселі позаду кожного текстового елементу і попереджає про контраст нижче 4.5:1 (або 3:1 для великого тексту). `hyperframes inspect` — це допоміжний інструмент для макету: запускає сторінку у різних тайм‑стемпах і виявляє проблеми, які не бачить статичний лінт (субтитр, що виходить за безпечну зону лише на 4.5 s, картка, що переповнюється, коли її заголовок найдовший, елемент, що потрапляє за шейдер‑переход). Запускай `inspect` особливо для композицій із бульбашками діалогів, картками, субтитрами або щільною типографікою.

### 8. Website‑to‑video (якщо користувач надає URL)

Використай 7‑кроковий workflow захоплення‑у‑відео з [references/website-to-video.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/website-to-video.md): capture → DESIGN.md → SCRIPT.md → storyboard → composition → render → deliver.
## Pitfalls

- **`HeadlessExperimental.beginFrame' wasn't found`** — у Chromium 147+ цей протокол видалено. Переконайся, що використовуєш `hyperframes@>=0.4.2` (автоматично визначає та переходить у режим скріншоту). Аварійний варіант: `export PRODUCER_FORCE_SCREENSHOT=true`. Дивись [hyperframes#294](https://github.com/heygen-com/hyperframes/issues/294) та [references/troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/troubleshooting.md).
- **System Chrome (не `chrome-headless-shell`)** — рендеринг зависає на 120 сек, після чого виникає тайм‑аут. Запусти `npx puppeteer browsers install chrome-headless-shell` (setup.sh робить це). `hyperframes doctor` покаже, який бінарник буде використано.
- **`repeat: -1` будь‑де** — руйнує механізм захоплення. Завжди обчислюй скінченну кількість повторень.
- **`gsap.set()` на елементи кліпу, які з’являються пізніше** — елемент ще не існує під час завантаження сторінки. Використовуй `tl.set(selector, vars, timePosition)` всередині таймлайну, у момент або після `data-start` кліпу.
- **`<br>` у тексті контенту** — примусові переноси не враховують ширину відрендереного шрифту, тому природний перенос + `<br>` створює подвійну розривку. Використовуй `max-width`, щоб дозволити тексту переноситися. Виняток: короткі заголовки, де кожне слово навмисно розташоване на окремому рядку.
- **Анімація `visibility` або `display`** — GSAP не може tween‑ити ці властивості. Використовуй `autoAlpha` (обробляє і видимість, і прозорість).
- **Виклик `video.play()` або `audio.play()`** — відтворення контролює фреймворк. Не викликай їх сам.
- **Побудова таймлайнів асинхронно** — механізм захоплення читає `window.__timelines` синхронно після завантаження сторінки. Не обгортай конструювання таймлайну в `async`, `setTimeout` чи Promise.
- **Окремий `index.html`, обгорнутий у `<template>`** — приховує весь контент від браузера. Тільки **sub‑compositions**, завантажені через `data-composition-src`, використовують `<template>`.
- **Використання відео замість аудіо** — завжди використовуйте вимкнений звук у `<video>` + окремий `<audio>`.
## Перевірка

Перед і після рендерингу:

1. **Lint + validate + inspect pass:** `npx hyperframes lint --strict && npx hyperframes validate && npx hyperframes inspect` (lint виявляє структурні проблеми, validate — контраст, inspect — візуальне розташування/переповнення — дивись `troubleshooting.md`, якщо з’являються попередження).
2. **Анімаційна хореографія** — для нових композицій або суттєвих змін анімації запусти карту анімації. `npx hyperframes init` копіює скрипти `skill` у проєкт, тому шлях є локальним для проєкту:
   ```bash
   node skills/hyperframes/scripts/animation-map.mjs <composition-dir> \
     --out <composition-dir>/.hyperframes/anim-map
   ```
   Виводить один `animation-map.json` з підсумками по кожному твіну, ASCII‑діаграмою Ганта, виявленням затримок, «мертвих зон» (>1 с без анімації), життєвими циклами елементів та прапорцями (`offscreen`, `collision`, `invisible`, `paced-fast` &lt;0.2s, `paced-slow` >2s). Переглянь підсумки та прапорці — виправ або обґрунтуй кожен. Пропусти на невеликих правках.
3. **Файл існує + не нульовий:** `ls -lh final.mp4`.
4. **Тривалість відповідає `data-duration`:** `ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 final.mp4`.
5. **Візуальна перевірка:** витягни кадр середньої композиції: `ffmpeg -i final.mp4 -ss 00:00:05 -vframes 1 preview.png`.
6. **Аудіо присутнє, якщо очікується:** `ffprobe -v error -show_streams -select_streams a -of default=nw=1:nk=1 final.mp4 | head -1`.

Якщо `hyperframes render` не вдається, запусти `npx hyperframes doctor` і додай його вивід до звіту.
## Посилання

- [composition.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/composition.md) — атрибути даних, контракт таймлайну, непереговорні правила, правила типографіки/активів
- [cli.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/cli.md) — усі команди CLI (init, capture, lint, validate, inspect, preview, render, transcribe, tts, doctor, browser, info, upgrade, benchmark)
- [gsap.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/gsap.md) — ядровий API GSAP для HyperFrames (tweens, eases, stagger, timelines, matchMedia)
- [features.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/features.md) — підписи, TTS, аудіо‑реактивність, підсвічування маркерів, переходи (завантаження за запитом)
- [website-to-video.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/website-to-video.md) — 7‑кроковий процес захоплення‑у‑відео
- [troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/hyperframes/references/troubleshooting.md) — виправлення OpenClaw, змінні середовища, типові помилки рендерингу