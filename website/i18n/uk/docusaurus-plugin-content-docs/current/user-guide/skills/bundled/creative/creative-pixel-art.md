---
title: "Pixel Art — Pixel art з палітрами епох (NES, Game Boy, PICO-8)"
sidebar_label: "Pixel Art"
description: "Піксельне мистецтво з палітрами епох (NES, Game Boy, PICO-8)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Pixel Art

Pixel art w/ era palettes (NES, Game Boy, PICO-8).

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/pixel-art` |
| Version | `2.0.0` |
| Author | dodo-reach |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `creative`, `pixel-art`, `arcade`, `snes`, `nes`, `gameboy`, `retro`, `image`, `video` |

## Довідка: повний SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Pixel Art

Перетвори будь‑яке зображення у ретро‑піксельне мистецтво, а потім за бажанням анімуй його у короткий MP4 або GIF з ефектами, характерними для епохи (дощ, світлячки, сніг, вуглинки).

Два скрипти постачаються з цією навичкою:

- `scripts/pixel_art.py` — фото → pixel‑art PNG (дискретизація Флойда‑Штайнберга)
- `scripts/pixel_art_video.py` — pixel‑art PNG → анімований MP4 (+ optional GIF)

Кожен можна імпортувати або запускати безпосередньо. Пресети підбираються під апаратні палітри,
коли потрібні точні кольори епохи (NES, Game Boy, PICO‑8 тощо), або використовують
адаптивну N‑кольорову квантизацію для вигляду в стилі аркад/SNES.

## Коли використовувати

- Користувач хоче ретро‑піксельне мистецтво з вихідного зображення
- Користувач просить стиль NES / Game Boy / PICO‑8 / C64 / аркада / SNES
- Користувач хоче коротку зациклену анімацію (дощ, нічне небо, сніг тощо)
- Плакати, обкладинки альбомів, соціальні пости, спрайти, персонажі, аватари

## Робочий процес

Перед генерацією підтверджуй стиль з користувачем. Різні пресети дають
значно різні результати, а повторна генерація дороговартісна.

### Крок 1 — Запропонувати стиль

Виклич `clarify` з 4‑ма представницькими пресетами. Вибери набір на основі того,
що попросив користувач — не виводь усі 14.

Типове меню, коли намір користувача неясний:

```python
clarify(
    question="Which pixel-art style do you want?",
    choices=[
        "arcade — bold, chunky 80s cabinet feel (16 colors, 8px)",
        "nes — Nintendo 8-bit hardware palette (54 colors, 8px)",
        "gameboy — 4-shade green Game Boy DMG",
        "snes — cleaner 16-bit look (32 colors, 4px)",
    ],
)
```

Якщо користувач вже назвав епоху (наприклад, «80‑х аркада», «Gameboy»), пропусти
`clarify` і використай відповідний пресет безпосередньо.

### Крок 2 — Запропонувати анімацію (опціонально)

Якщо користувач попросив відео/GIF, або результат може виграти від руху,
запитай, яку сцену:

```python
clarify(
    question="Want to animate it? Pick a scene or skip.",
    choices=[
        "night — stars + fireflies + leaves",
        "urban — rain + neon pulse",
        "snow — falling snowflakes",
        "skip — just the image",
    ],
)
```

Не викликай `clarify` більше двох разів підряд. Один раз для стилю, один раз для сцени, якщо анімація на розгляді. Якщо користувач явно вказав конкретний стиль і сцену у своєму повідомленні, пропусти `clarify` зовсім.

### Крок 3 — Генерувати

Спочатку запусти `pixel_art()`. Якщо запитана анімація, підключи
`pixel_art_video()` до отриманого результату.

## Каталог пресетів

| Preset | Era | Palette | Block | Best for |
|--------|-----|---------|-------|----------|
| `arcade` | 80s arcade | adaptive 16 | 8px | Bold posters, hero art |
| `snes` | 16-bit | adaptive 32 | 4px | Characters, detailed scenes |
| `nes` | 8-bit | NES (54) | 8px | True NES look |
| `gameboy` | DMG handheld | 4 green shades | 8px | Monochrome Game Boy |
| `gameboy_pocket` | Pocket handheld | 4 grey shades | 8px | Mono GB Pocket |
| `pico8` | PICO-8 | 16 fixed | 6px | Fantasy-console look |
| `c64` | Commodore 64 | 16 fixed | 8px | 8-bit home computer |
| `apple2` | Apple II hi-res | 6 fixed | 10px | Extreme retro, 6 colors |
| `teletext` | BBC Teletext | 8 pure | 10px | Chunky primary colors |
| `mspaint` | Windows MS Paint | 24 fixed | 8px | Nostalgic desktop |
| `mono_green` | CRT phosphor | 2 green | 6px | Terminal/CRT aesthetic |
| `mono_amber` | CRT amber | 2 amber | 6px | Amber monitor look |
| `neon` | Cyberpunk | 10 neons | 6px | Vaporwave/cyber |
| `pastel` | Soft pastel | 10 pastels | 6px | Kawaii / gentle |

Названі палітри знаходяться у `scripts/palettes.py` (дивись `references/palettes.md` для
повного списку — 28 названих палітр). Будь‑який пресет можна перевизначити:

```python
pixel_art("in.png", "out.png", preset="snes", palette="PICO_8", block=6)
```

## Каталог сцен (для відео)

| Scene | Effects |
|-------|---------|
| `night` | Twinkling stars + fireflies + drifting leaves |
| `dusk` | Fireflies + sparkles |
| `tavern` | Dust motes + warm sparkles |
| `indoor` | Dust motes |
| `urban` | Rain + neon pulse |
| `nature` | Leaves + fireflies |
| `magic` | Sparkles + fireflies |
| `storm` | Rain + lightning |
| `underwater` | Bubbles + light sparkles |
| `fire` | Embers + sparkles |
| `snow` | Snowflakes + sparkles |
| `desert` | Heat shimmer + dust |

## Шаблони виклику

### Python (import)

```python
import sys
sys.path.insert(0, "/home/teknium/.hermes/skills/creative/pixel-art/scripts")
from pixel_art import pixel_art
from pixel_art_video import pixel_art_video

# 1. Convert to pixel art
pixel_art("/path/to/photo.jpg", "/tmp/pixel.png", preset="nes")

# 2. Animate (optional)
pixel_art_video(
    "/tmp/pixel.png",
    "/tmp/pixel.mp4",
    scene="night",
    duration=6,
    fps=15,
    seed=42,
    export_gif=True,
)
```

### CLI

```bash
cd /home/teknium/.hermes/skills/creative/pixel-art/scripts

python pixel_art.py in.jpg out.png --preset gameboy
python pixel_art.py in.jpg out.png --preset snes --palette PICO_8 --block 6

python pixel_art_video.py out.png out.mp4 --scene night --duration 6 --gif
```

## Обґрунтування конвеєра

**Перетворення пікселів:**
1. Підвищення контрасту, кольору, різкості (сильніше для менших палітр)
2. Постеризація для спрощення тональних ділянок перед квантизацією
3. Зменшення розміру за допомогою `block` з `Image.NEAREST` (жорсткі пікселі, без інтерполяції)
4. Квантизація з дискретизацією Флойда‑Штайнберга — проти адаптивної
   N‑кольорової палітри АБО названої апаратної палітри
5. Підвищення розміру назад за допомогою `Image.NEAREST`

Квантизація ПІСЛЯ зменшення розміру зберігає дискретизацію, вирівняну з фінальною сіткою пікселів.
Квантизація ДО зменшення марнує розсіювання помилки на деталях, які зникають.

**Накладення відео:**
- Копіює базовий кадр кожен тик (статичний фон)
- Накладає без стану по‑кадрові частинки (одна функція на ефект)
- Кодує через ffmpeg `libx264 -pix_fmt yuv420p -crf 18`
- Опціональний GIF через `palettegen` + `paletteuse`

## Залежності

- Python 3.9+
- Pillow (`pip install Pillow`)
- ffmpeg у PATH (потрібен лише для відео — Hermes встановлює пакет)

## Підводні камені

- Ключі палітри чутливі до регістру (`"NES"`, `"PICO_8"`, `"GAMEBOY_ORIGINAL"`).
- Дуже маленькі джерела (<100px шириною) руйнуються під 8‑10px блоками. Спочатку збільшіть
  джерело, якщо воно крихітне.
- Дробові `block` або `palette` зламають квантизацію — залишайте їх позитивними цілими числами.
- Кількість частинок анімації налаштована для канвасів ~640x480. На дуже великих
  зображеннях можливо знадобиться другий прохід з іншим seed для густини.
- `mono_green` / `mono_amber` примушують `color=0.0` (десатурація). Якщо перевизначаєте
  і залишаєте хрома, 2‑кольорова палітра може створювати смуги на плавних ділянках.
- Цикл `clarify`: викликайте його не більше двох разів за хід (стиль, потім сцена). Не засипайте користувача зайвими виборами.

## Перевірка

- PNG створено за вказаним шляхом
- Видимі квадратні піксельні блоки відповідного розміру пресету
- Кількість кольорів відповідає пресету (перевірте зображення або запустіть `Image.open(p).getcolors()`)
- Відео — дійсний MP4 (`ffprobe` може його відкрити) з ненульовим розміром

## Атрибуція

Названі апаратні палітри та процедурні анімаційні цикли в `pixel_art_video.py`
портовані з [pixel-art-studio](https://github.com/Synero/pixel-art-studio)
(MIT). Дивіться `ATTRIBUTION.md` у цьому каталозі навички для деталей.