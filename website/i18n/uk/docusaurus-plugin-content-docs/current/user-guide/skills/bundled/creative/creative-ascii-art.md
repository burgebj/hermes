---
title: "Ascii Art — ASCII art: pyfiglet, cowsay, коробки, image-to-ascii"
sidebar_label: "Ascii Art"
description: "ASCII‑арт: pyfiglet, cowsay, boxes, image-to-ascii"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# ASCII Art

ASCII art: pyfiglet, cowsay, boxes, image-to-ascii.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Навичка ASCII Art

Кілька інструментів для різних потреб ASCII‑арт. Усі інструменти — локальні CLI‑програми або безкоштовні REST‑API — без потреби в API‑ключах.

## Інструмент 1: Текстові банери (pyfiglet — локально)

Рендерить текст у вигляді великих ASCII‑арт банерів. 571 вбудований шрифт.

### Налаштування

```bash
pip install pyfiglet --break-system-packages -q
```

### Використання

```bash
python3 -m pyfiglet "YOUR TEXT" -f slant
python3 -m pyfiglet "TEXT" -f doom -w 80    # Set width
python3 -m pyfiglet --list_fonts             # List all 571 fonts
```

### Рекомендовані шрифти

| Стиль | Шрифт | Найкраще для |
|-------|------|--------------|
| Чистий і сучасний | `slant` | Назви проєктів, заголовки |
| Жирний і блоковий | `doom` | Заголовки, логотипи |
| Великий і читабельний | `big` | Банери |
| Класичний банер | `banner3` | Широкі дисплеї |
| Компактний | `small` | Підзаголовки |
| Кіберпанк | `cyberlarge` | Технічні теми |
| 3D‑ефект | `3-d` | Сплеш‑скрін |
| Готичний | `gothic` | Драматичний текст |

### Поради

- Попередньо переглянь 2‑3 шрифти і дай користувачеві вибрати улюблений
- Короткий текст (1‑8 символів) найкраще виглядає в деталізованих шрифтах типу `doom` або `block`
- Довгий текст краще з компактними шрифтами типу `small` або `mini`

## Інструмент 2: Текстові банери (asciified API — віддалено, без встановлення)

Безкоштовний REST‑API, що перетворює текст у ASCII‑арт. 250+ шрифтів FIGlet. Повертає простий текст без потреби в парсингу. Використовуй, коли pyfiglet не встановлений або як швидку альтернативу.

### Використання (через curl у терміналі)

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

### Поради

- URL‑кодуй пробіли як `+` у параметрі `text`
- Відповідь — простий текст ASCII‑арт — без обгортки JSON, готовий до виводу
- Імена шрифтів чутливі до регістру; використай endpoint шрифтів, щоб отримати точні назви
- Працює в будь‑якому терміналі з curl — без Python чи pip

## Інструмент 3: Cowsay (Меседж‑арт)

Класичний інструмент, що обгортає текст у бульбашку діалогу з ASCII‑персонажем.

### Налаштування

```bash
sudo apt install cowsay -y    # Debian/Ubuntu
# brew install cowsay         # macOS
```

### Використання

```bash
cowsay "Hello World"
cowsay -f tux "Linux rules"       # Tux the penguin
cowsay -f dragon "Rawr!"          # Dragon
cowsay -f stegosaurus "Roar!"     # Stegosaurus
cowthink "Hmm..."                  # Thought bubble
cowsay -l                          # List all characters
```

### Доступні персонажі (50+)

`beavis.zen`, `bong`, `bunny`, `cheese`, `daemon`, `default`, `dragon`,
`dragon-and-cow`, `elephant`, `eyes`, `flaming-skull`, `ghostbusters`,
`hellokitty`, `kiss`, `kitty`, `koala`, `luke-koala`, `mech-and-cow`,
`meow`, `moofasa`, `moose`, `ren`, `sheep`, `skeleton`, `small`,
`stegosaurus`, `stimpy`, `supermilker`, `surgery`, `three-eyes`,
`turkey`, `turtle`, `tux`, `udder`, `vader`, `vader-koala`, `www`

### Модифікатори очей/язика

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

## Інструмент 4: Boxes (Декоративні рамки)

Малює декоративні ASCII‑рамки/фрейми навколо будь‑якого тексту. 70+ вбудованих дизайнів.

### Налаштування

```bash
sudo apt install boxes -y    # Debian/Ubuntu
# brew install boxes         # macOS
```

### Використання

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

### Комбінація з pyfiglet або asciified

```bash
python3 -m pyfiglet "HERMES" -f slant | boxes -d stone
# Or without pyfiglet installed:
curl -s "https://asciified.thelicato.io/api/v2/ascii?text=HERMES&font=Slant" | boxes -d stone
```

## Інструмент 5: TOIlet (Кольоровий текстовий арт)

Як pyfiglet, але з ANSI‑кольоровими ефектами та візуальними фільтрами. Чудово підходить для «цукерок» у терміналі.

### Налаштування

```bash
sudo apt install toilet toilet-fonts -y    # Debian/Ubuntu
# brew install toilet                      # macOS
```

### Використання

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

### Фільтри

`crop`, `gay` (rainbow), `metal`, `flip`, `flop`, `180`, `left`, `right`, `border`

**Note**: toilet outputs ANSI escape codes for colors — works in terminals but may not render in all contexts (e.g., plain text files, some chat platforms).

## Інструмент 6: Image to ASCII Art

Перетворює зображення (PNG, JPEG, GIF, WEBP) у ASCII‑арт.

### Варіант A: ascii-image-converter (рекомендовано, сучасний)

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

### Варіант B: jp2a (легковаговий, лише JPEG)

```bash
sudo apt install jp2a -y
jp2a --width=80 image.jpg
jp2a --colors image.jpg              # Colorized
```

## Інструмент 7: Пошук готових ASCII‑артів

Шукає підготовлені ASCII‑арти в інтернеті. Використовуй `terminal` з `curl`.

### Джерело A: ascii.co.uk (рекомендовано для готових артов)

Велика колекція класичних ASCII‑артів, організованих за темами. Арти знаходяться всередині HTML‑тегів `<pre>`. Отримай сторінку за допомогою curl, потім витягни арт маленьким Python‑скриптом.

**URL‑шаблон:** `https://ascii.co.uk/art/{subject}`

**Крок 1 — Отримати сторінку:**

```bash
curl -s 'https://ascii.co.uk/art/cat' -o /tmp/ascii_art.html
```

**Крок 2 — Витягнути арт з тегів pre:**

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

**Доступні теми** (використовуй у шляху URL):
- Тварини: `cat`, `dog`, `horse`, `bird`, `fish`, `dragon`, `snake`, `rabbit`, `elephant`, `dolphin`, `butterfly`, `owl`, `wolf`, `bear`, `penguin`, `turtle`
- Предмети: `car`, `ship`, `airplane`, `rocket`, `guitar`, `computer`, `coffee`, `beer`, `cake`, `house`, `castle`, `sword`, `crown`, `key`
- Природа: `tree`, `flower`, `sun`, `moon`, `star`, `mountain`, `ocean`, `rainbow`
- Персонажі: `skull`, `robot`, `angel`, `wizard`, `pirate`, `ninja`, `alien`
- Свята: `christmas`, `halloween`, `valentine`

**Поради:**
- Зберігай підписи/ініціали авторів — важливий етикет
- На одній сторінці може бути кілька артов — вибери найкращий для користувача
- Працює стабільно через curl, без JavaScript

### Джерело B: GitHub Octocat API (весела пасхалька)

Повертає випадковий GitHub Octocat з мудрим цитатою. Авторизація не потрібна.

```bash
curl -s https://api.github.com/octocat
```

## Інструмент 8: Веселі ASCII‑утиліти (через curl)

Ці безкоштовні сервіси повертають ASCII‑арт одразу — чудово для розваг.

### QR‑коди у вигляді ASCII‑арт

```bash
curl -s "qrenco.de/Hello+World"
curl -s "qrenco.de/https://example.com"
```

### Погода у вигляді ASCII‑арт

```bash
curl -s "wttr.in/London"          # Full weather report with ASCII graphics
curl -s "wttr.in/Moon"            # Moon phase in ASCII art
curl -s "v2.wttr.in/London"       # Detailed version
```

## Інструмент 9: LLM‑генерований кастомний арт (запасний варіант)

Коли інші інструменти не мають потрібного, згенеруй ASCII‑арт безпосередньо, використовуючи ці Unicode‑символи:

### Палітра символів

**Box Drawing:** `╔ ╗ ╚ ╝ ║ ═ ╠ ╣ ╦ ╩ ╬ ┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼ ╭ ╮ ╰ ╯`

**Block Elements:** `░ ▒ ▓ █ ▄ ▀ ▌ ▐ ▖ ▗ ▘ ▝ ▚ ▞`

**Geometric & Symbols:** `◆ ◇ ◈ ● ○ ◉ ■ □ ▲ △ ▼ ▽ ★ ☆ ✦ ✧ ◀ ▶ ◁ ▷ ⬡ ⬢ ⌂`

### Правила

- Максимальна ширина: 60 символів у рядку (термінал‑безпечно)
- Максимальна висота: 15 рядків для банерів, 25 — для сцен
- Тільки моноширинний шрифт: вивід має коректно відображатися у фіксованих шрифтах

## Потік рішень

1. **Текст у вигляді банеру** → pyfiglet, якщо встановлено, інакше asciified API через curl
2. **Обгорнути повідомлення у кумедний персонаж** → cowsay
3. **Додати декоративну рамку/фрейм** → boxes (можна комбінувати з pyfiglet/asciified)
4. **Арт конкретного об’єкта** (cat, rocket, dragon) → ascii.co.uk через curl + парсинг
5. **Конвертувати зображення у ASCII** → ascii-image-converter або jp2a
6. **QR‑код** → qrenco.de через curl
7. **Погода/місячний арт** → wttr.in через curl
8. **Щось кастомне/креативне** → LLM‑генерація з Unicode‑палетрою
9. **Будь‑який інструмент не встановлений** → встановити його або перейти до наступного варіанту