---
title: "Ascii Art — ASCII art: pyfiglet, cowsay, boxes, image-to-ascii"
sidebar_label: "Ascii Art"
description: "ASCII‑арт: pyfiglet, cowsay, boxes, image-to-ascii"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# ASCII Art

ASCII art: pyfiglet, cowsay, boxes, image-to-ascii.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/ascii-art` |
| Version | `4.0.0` |
| Author | 0xbyt4, Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `ASCII`, `Art`, `Banners`, `Creative`, `Unicode`, `Text-Art`, `pyfiglet`, `figlet`, `cowsay`, `boxes` |
| Related skills | [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# Навык ASCII Art

Несколько инструментов для разных задач ASCII‑искусства. Все инструменты — локальные CLI‑программы или бесплатные REST API — без необходимости в API‑ключах.

## Инструмент 1: Текстовые баннеры (pyfiglet — локально)

Отображает текст в виде больших ASCII‑баннеров. 571 встроенный шрифт.

### Установка

```bash
pip install pyfiglet --break-system-packages -q
```

### Использование

```bash
python3 -m pyfiglet "YOUR TEXT" -f slant
python3 -m pyfiglet "TEXT" -f doom -w 80    # Set width
python3 -m pyfiglet --list_fonts             # List all 571 fonts
```

### Рекомендуемые шрифты

| Стиль | Шрифт | Лучшее применение |
|-------|------|-------------------|
| Чистый и современный | `slant` | Имена проектов, заголовки |
| Жирный и блоковый | `doom` | Заголовки, логотипы |
| Большой и читаемый | `big` | Баннеры |
| Классический баннер | `banner3` | Широкие дисплеи |
| Компактный | `small` | Субтитры |
| Киберпанк | `cyberlarge` | Техно‑темы |
| 3D‑эффект | `3-d` | Сплеш‑экраны |
| Готический | `gothic` | Драматический текст |

### Советы

- Предпросмотр 2‑3 шрифтов и дай пользователю выбрать любимый.
- Краткий текст (1‑8 символов) лучше всего выглядит в детализированных шрифтах, таких как `doom` или `block`.
- Длинный текст лучше отображать компактными шрифтами, например `small` или `mini`.

## Инструмент 2: Текстовые баннеры (asciified API — удалённо, без установки)

Бесплатный REST API, преобразующий текст в ASCII‑арт. Более 250 шрифтов FIGlet. Возвращает обычный текст напрямую — без необходимости парсинга. Используй, когда pyfiglet не установлен или нужен быстрый вариант.

### Использование (через `curl` в терминале)

```bash
# Basic text banner (default font)
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello+World"

# With a specific font
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Slant"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Doom"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Star+Wars"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=3-D"
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=Hello&font=Banner3"

# List all available fonts (returns JSON array)
curl -s "https://asciified.thelicato.io/api/v2/fonts"
```

### Советы

- URL‑кодируй пробелы как `+` в параметре `text`.
- Ответ — обычный текст ASCII‑арт — без JSON‑обёртки, готов к выводу.
- Имена шрифтов чувствительны к регистру; используй endpoint шрифтов, чтобы получить точные имена.
- Работает в любом терминале с `curl` — без Python и `pip`.

## Инструмент 3: Cowsay (искусство сообщений)

Классический инструмент, оборачивающий текст в «облачко» речи с ASCII‑персонажем.

### Установка

```bash
sudo apt install cowsay -y    # Debian/Ubuntu
# brew install cowsay         # macOS
```

### Использование

```bash
cowsay "Hello World"
cowsay -f tux "Linux rules"       # Tux the penguin
cowsay -f dragon "Rawr!"          # Dragon
cowsay -f stegosaurus "Roar!"     # Stegosaurus
cowthink "Hmm..."                  # Thought bubble
cowsay -l                          # List all characters
```

### Доступные персонажи (50+)

`beavis.zen`, `bong`, `bunny`, `cheese`, `daemon`, `default`, `dragon`,
`dragon-and-cow`, `elephant`, `eyes`, `flaming-skull`, `ghostbusters`,
`hellokitty`, `kiss`, `kitty`, `koala`, `luke-koala`, `mech-and-cow`,
`meow`, `moofasa`, `moose`, `ren`, `sheep`, `skeleton`, `small`,
`stegosaurus`, `stimpy`, `supermilker`, `surgery`, `three-eyes`,
`turkey`, `turtle`, `tux`, `udder`, `vader`, `vader-koala`, `www`

### Модификаторы глаз/языка

```bash
cowsay -b "Borg"       # =_= eyes
cowsay -d "Dead"       # x_x eyes
cowsay -g "Greedy"     # $_$ eyes
cowsay -p "Paranoid"   # @_@ eyes
cowsay -s "Stoned"     # *_* eyes
cowsay -w "Wired"      # O_O eyes
cowsay -e "OO" "Msg"   # Custom eyes
cowsay -T "U " "Msg"   # Custom tongue
```

## Инструмент 4: Boxes (декоративные рамки)

Рисует декоративные ASCII‑рамки/кадры вокруг любого текста. Более 70 встроенных дизайнов.

### Установка

```bash
sudo apt install boxes -y    # Debian/Ubuntu
# brew install boxes         # macOS
```

### Использование

```bash
echo "Hello World" | boxes                    # Default box
echo "Hello World" | boxes -d stone           # Stone border
echo "Hello World" | boxes -d parchment       # Parchment scroll
echo "Hello World" | boxes -d cat             # Cat border
echo "Hello World" | boxes -d dog             # Dog border
echo "Hello World" | boxes -d unicornsay      # Unicorn
echo "Hello World" | boxes -d diamonds        # Diamond pattern
echo "Hello World" | boxes -d c-cmt           # C-style comment
echo "Hello World" | boxes -d html-cmt        # HTML comment
echo "Hello World" | boxes -a c               # Center text
boxes -l                                       # List all 70+ designs
```

### Комбинация с pyfiglet или asciified

```bash
python3 -m pyfiglet "HERMES" -f slant | boxes -d stone
# Or without pyfiglet installed:
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=HERMES&font=Slant" | boxes -d stone
```

## Инструмент 5: TOIlet (цветной текстовый арт)

Как pyfiglet, но с ANSI‑цветовыми эффектами и визуальными фильтрами. Отлично подходит для «сладостей» в терминале.

### Установка

```bash
sudo apt install toilet toilet-fonts -y    # Debian/Ubuntu
# brew install toilet                      # macOS
```

### Использование

```bash
toilet "Hello World"                    # Basic text art
toilet -f bigmono12 "Hello"            # Specific font
toilet --gay "Rainbow!"                 # Rainbow coloring
toilet --metal "Metal!"                 # Metallic effect
toilet -F border "Bordered"             # Add border
toilet -F border --gay "Fancy!"         # Combined effects
toilet -f pagga "Block"                 # Block-style font (unique to toilet)
toilet -F list                          # List available filters
```

### Фильтры

`crop`, `gay` (rainbow), `metal`, `flip`, `flop`, `180`, `left`, `right`, `border`

**Примечание**: `toilet` выводит ANSI‑коды для цветов — работает в терминалах, но может не отобразиться во всех контекстах (например, в обычных текстовых файлах или некоторых чат‑платформах).

## Инструмент 6: Изображение в ASCII‑арт

Преобразует изображения (PNG, JPEG, GIF, WEBP) в ASCII‑арт.

### Вариант A: ascii-image-converter (рекомендовано, современно)

```bash
# Install
sudo snap install ascii-image-converter
# OR: go install github.com/TheZoraiz/ascii-image-converter@latest
```

```bash
ascii-image-converter image.png                  # Basic
ascii-image-converter image.png -C               # Color output
ascii-image-converter image.png -d 60,30         # Set dimensions
ascii-image-converter image.png -b               # Braille characters
ascii-image-converter image.png -n               # Negative/inverted
ascii-image-converter https://url/image.jpg      # Direct URL
ascii-image-converter image.png --save-txt out   # Save as text
```

### Вариант B: jp2a (легковесный, только JPEG)

```bash
sudo apt install jp2a -y
jp2a --width=80 image.jpg
jp2a --colors image.jpg              # Colorized
```

## Инструмент 7: Поиск готового ASCII‑арта

Ищет отобранный ASCII‑арт в интернете. Используй `terminal` с `curl`.

### Источник A: ascii.co.uk (рекомендовано для готового арта)

Большая коллекция классического ASCII‑арта, упорядоченного по темам. Арт находится внутри HTML‑тегов `<pre>`. Скачай страницу через `curl`, затем извлеки арт небольшим фрагментом Python.

**Шаблон URL:** `https://ascii.co.uk/art/{subject}`

**Шаг 1 — Получить страницу:**

```bash
curl -s 'https://ascii.co.uk/art/cat' -o /tmp/ascii_art.html
```

**Шаг 2 — Извлечь арт из тегов `<pre>`:**

```python
import re, html
with open('/tmp/ascii_art.html') as f:
    text = f.read()
arts = re.findall(r'<pre[^>]*>(.*?)</pre>', text, re.DOTALL)
for art in arts:
    clean = re.sub(r'<[^>]+>', '', art)
    clean = html.unescape(clean).strip()
    if len(clean) > 30:
        print(clean)
        print('\n---\n')
```

**Доступные темы** (используй как часть пути URL):

- Животные: `cat`, `dog`, `horse`, `bird`, `fish`, `dragon`, `snake`, `rabbit`, `elephant`, `dolphin`, `butterfly`, `owl`, `wolf`, `bear`, `penguin`, `turtle`
- Предметы: `car`, `ship`, `airplane`, `rocket`, `guitar`, `computer`, `coffee`, `beer`, `cake`, `house`, `castle`, `sword`, `crown`, `key`
- Природа: `tree`, `flower`, `sun`, `moon`, `star`, `mountain`, `ocean`, `rainbow`
- Персонажи: `skull`, `robot`, `angel`, `wizard`, `pirate`, `ninja`, `alien`
- Праздники: `christmas`, `halloween`, `valentine`

**Советы:**

- Сохраняй подписи/инициалы художника — важный этикет.
- На странице может быть несколько артов — выбери лучший для пользователя.
- Работает надёжно через `curl`, без JavaScript.

### Источник B: GitHub Octocat API (весёлое пасхальное яйцо)

Возвращает случайного Octocat с мудрой цитатой. Авторизация не требуется.

```bash
curl -s https://api.github.com/octocat
```

## Инструмент 8: Весёлые ASCII‑утилиты (через `curl`)

Эти бесплатные сервисы сразу возвращают ASCII‑арт — отлично для развлечений.

### QR‑коды в виде ASCII‑арта

```bash
curl -s "qrenco.de/Hello+World"
curl -s "qrenco.de/https://example.com"
```

### Погода в виде ASCII‑арта

```bash
curl -s "wttr.in/London"          # Full weather report with ASCII graphics
curl -s "wttr.in/Moon"            # Moon phase in ASCII art
curl -s "v2.wttr.in/London"       # Detailed version
```

## Инструмент 9: Пользовательский ASCII‑арт, сгенерированный LLM (запасной вариант)

Когда вышеуказанные инструменты не дают нужного, генерируй ASCII‑арт напрямую, используя эти Unicode‑символы:

### Палитра символов

**Box Drawing:** `╔ ╗ ╚ ╝ ║ ═ ╠ ╣ ╦ ╩ ╬ ┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼ ╭ ╮ ╰ ╯`

**Block Elements:** `░ ▒ ▓ █ ▄ ▀ ▌ ▐ ▖ ▗ ▘ ▝ ▚ ▞`

**Geometric & Symbols:** `◆ ◇ ◈ ● ○ ◉ ■ □ ▲ △ ▼ ▽ ★ ☆ ✦ ✧ ◀ ▶ ◁ ▷ ⬡ ⬢ ⌂`

### Правила

- Максимальная ширина: 60 символов в строке (безопасно для терминала).
- Максимальная высота: 15 строк для баннеров, 25 строк — для сцен.
- Только моноширинный шрифт: вывод должен корректно отображаться в фикс‑ширинных шрифтах.

## Дерево решений

1. **Текст как баннер** → pyfiglet, если установлен, иначе asciified API через `curl`.
2. **Обёрнуть сообщение в забавный персонаж** → cowsay.
3. **Добавить декоративную рамку/кадр** → boxes (можно комбинировать с pyfiglet/asciified).
4. **Артефакт конкретной вещи** (кот, ракета, дракон) → ascii.co.uk через `curl` + парсинг.
5. **Преобразовать изображение в ASCII** → ascii-image-converter или jp2a.
6. **QR‑код** → qrenco.de через `curl`.
7. **Погода/луна в виде арта** → wttr.in через `curl`.
8. **Что‑то кастомное/креативное** → генерация LLM с Unicode‑палитрой.
9. **Любой инструмент не установлен** → установить его или перейти к следующему варианту.