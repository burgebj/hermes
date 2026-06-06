---
title: "Pixel Art — Пиксельный арт с палитрами эпох (NES, Game Boy, PICO-8)"
sidebar_label: "Pixel Art"
description: "Пиксель-арт с палитрами эпох (NES, Game Boy, PICO-8)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Пиксельный арт

Пиксельный арт с палитрами эпох (NES, Game Boy, PICO‑8).

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/pixel-art` |
| Version | `2.0.0` |
| Author | dodo-reach |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `creative`, `pixel-art`, `arcade`, `snes`, `nes`, `gameboy`, `retro`, `image`, `video` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# Пиксельный арт

Преобразуй любое изображение в ретро‑пиксельный арт, а затем, при желании, анимируй его в короткий MP4 или GIF с эффектами, характерными для эпохи (дождь, светлячки, снег, искры).

С этим навыком поставляются два скрипта:

- `scripts/pixel_art.py` — фото → пиксельный PNG (дизеринг Флойда‑Штайнберга)
- `scripts/pixel_art_video.py` — пиксельный PNG → анимированный MP4 (+ опциональный GIF)

Каждый из них можно импортировать или запускать напрямую. Пресеты привязываются к аппаратным палитрам, когда нужны точные цвета эпохи (NES, Game Boy, PICO‑8 и т.д.), либо используют адаптивную N‑цветную квантизацию для вида аркад/SNES.

## Когда использовать

- Пользователь хочет ретро‑пиксельный арт из исходного изображения
- Пользователь просит стилизацию под NES / Game Boy / PICO‑8 / C64 / аркаду / SNES
- Пользователь хочет короткую зацикленную анимацию (дождь, ночное небо, снег и пр.)
- Плакаты, обложки альбомов, посты в соцсетях, спрайты, персонажи, аватары

## Рабочий процесс

Перед генерацией уточни стиль у пользователя. Разные пресеты дают совершенно разные результаты, а повторная генерация дорогая.

### Шаг 1 — Предложить стиль

Вызови `clarify` с 4‑мя репрезентативными пресетами. Выбери набор исходя из того, что запросил пользователь — не показывай сразу все 14.

Меню по умолчанию, когда намерение пользователя неясно:

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

Если пользователь уже назвал эпоху (например, «80‑х аркада», «Gameboy»), пропусти `clarify` и сразу используй соответствующий пресет.

### Шаг 2 — Предложить анимацию (по желанию)

Если пользователь попросил видео/GIF, или результат может выиграть от движения, спроси, какая сцена нужна:

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

Не вызывай `clarify` более двух раз подряд: один раз — для стиля, один раз — для сцены, если анимация рассматривается. Если пользователь явно указал конкретный стиль и сцену в своём сообщении, полностью пропусти `clarify`.

### Шаг 3 — Генерация

Сначала запусти `pixel_art()`. Если запрошена анимация, передай результат в `pixel_art_video()`.

## Каталог пресетов

| Preset | Era | Palette | Block | Best for |
|--------|-----|---------|-------|----------|
| `arcade` | 80s arcade | adaptive 16 | 8px | Bold posters, hero art |
| `snes` | 16‑bit | adaptive 32 | 4px | Characters, detailed scenes |
| `nes` | 8‑bit | NES (54) | 8px | True NES look |
| `gameboy` | DMG handheld | 4 green shades | 8px | Monochrome Game Boy |
| `gameboy_pocket` | Pocket handheld | 4 grey shades | 8px | Mono GB Pocket |
| `pico8` | PICO‑8 | 16 fixed | 6px | Fantasy‑console look |
| `c64` | Commodore 64 | 16 fixed | 8px | 8‑bit home computer |
| `apple2` | Apple II hi‑res | 6 fixed | 10px | Extreme retro, 6 colors |
| `teletext` | BBC Teletext | 8 pure | 10px | Chunky primary colors |
| `mspaint` | Windows MS Paint | 24 fixed | 8px | Nostalgic desktop |
| `mono_green` | CRT phosphor | 2 green | 6px | Terminal/CRT aesthetic |
| `mono_amber` | CRT amber | 2 amber | 6px | Amber monitor look |
| `neon` | Cyberpunk | 10 neons | 6px | Vaporwave/cyber |
| `pastel` | Soft pastel | 10 pastels | 6px | Kawaii / gentle |

Именованные палитры находятся в `scripts/palettes.py` (см. `references/palettes.md` для полного списка — всего 28 именованных палитр). Любой пресет можно переопределить:

```python
pixel_art("in.png", "out.png", preset="snes", palette="PICO_8", block=6)
```

## Каталог сцен (для видео)

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

## Шаблоны вызова

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

## Обоснование конвейера

**Пиксельное преобразование:**
1. Усилить контраст/цвет/резкость (чем сильнее — для меньших палитр)
2. Постеризовать для упрощения тональных областей перед квантизацией
3. Понизить разрешение с помощью `block` и `Image.NEAREST` (жёсткие пиксели, без интерполяции)
4. Квантизировать с дизерингом Флойда‑Штайнберга — либо к адаптивной N‑цветной палитре, либо к именованной аппаратной палитре
5. Масштабировать обратно с `Image.NEAREST`

Квантизация **после** понижения сохраняет выравнивание дизеринга с конечной пиксельной сеткой. Квантизация **до** понижения тратит диффузию ошибки на детали, которые исчезнут.

**Наложение видео:**
- Копирует базовый кадр каждый тик (статический фон)
- Накладывает безсостояния‑по‑кадру частицы (по одной функции на эффект)
- Кодирует через ffmpeg `libx264 -pix_fmt yuv420p -crf 18`
- Опциональный GIF через `palettegen` + `paletteuse`

## Зависимости

- Python 3.9+
- Pillow (`pip install Pillow`)
- ffmpeg в `PATH` (нужен только для видео — Hermes устанавливает пакет)

## Подводные камни

- Ключи палитр чувствительны к регистру (`"NES"`, `"PICO_8"`, `"GAMEBOY_ORIGINAL"`).
- Очень маленькие источники (< 100 px шириной) ломаются при блоках 8‑10 px. Увеличь исходник, если он крошечный.
- Дробные значения `block` или `palette` ломают квантизацию — оставляй их положительными целыми.
- Количества частиц в анимации настроены для канвы ≈ 640×480. На очень больших изображениях может потребоваться второй проход с другим `seed` для плотности.
- `mono_green` / `mono_amber` принудительно задают `color=0.0` (обесцвечивание). Если переопределяешь и сохраняешь хрома, 2‑цветная палитра может давать полосы на плавных областях.
- Цикл `clarify`: вызывай не более двух раз за ход (стиль, затем сцена). Не забрасывай пользователя множеством вариантов.

## Проверка

- PNG создаётся по указанному пути
- Видны чёткие квадратные пиксельные блоки соответствующего размера пресета
- Количество цветов соответствует пресету (проверь визуально или выполните `Image.open(p).getcolors()`)
- Видео — корректный MP4 (`ffprobe` открывает его) ненулевого размера

## Атрибуция

Именованные аппаратные палитры и процедурные анимационные циклы в `pixel_art_video.py` портированы из [pixel-art-studio](https://github.com/Synero/pixel-art-studio) (MIT). См. `ATTRIBUTION.md` в каталоге этого навыка для деталей.