---
title: "Openhue — Керування світильниками, сценами, кімнатами Philips Hue через OpenHue CLI"
sidebar_label: "Openhue"
description: "Керуй Philips Hue лампами, сценами, кімнатами через OpenHue CLI"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Openhue

Керування лампами Philips Hue, сценами, кімнатами через OpenHue CLI.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/smart-home/openhue` |
| Version | `1.0.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Smart-Home`, `Hue`, `Lights`, `IoT`, `Automation` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# OpenHue CLI

Керування лампами Philips Hue та сценами через Hue Bridge з терміналу.

## Попередні вимоги

```bash
# Linux (pre-built binary)
curl -sL https://github.com/openhue/openhue-cli/releases/latest/download/openhue-linux-amd64 -o ~/.local/bin/openhue && chmod +x ~/.local/bin/openhue

# macOS
brew install openhue/cli/openhue-cli
```

Перший запуск вимагає натискання кнопки на вашому Hue Bridge для парування. Bridge має бути в тій самій локальній мережі, що й комп’ютер, на якому запущений Hermes.

## Коли використовувати

- «Увімкнути/вимкнути лампи»
- «Затемнити лампи у вітальні»
- «Встановити сцену» або «режим кіно»
- Керування конкретними кімнатами, зонами або окремими лампочками Hue
- Регулювання яскравості, кольору або колірної температури

## Поширені команди

### Список ресурсів

```bash
openhue get light       # List all lights
openhue get room        # List all rooms
openhue get scene       # List all scenes
```

### Керування лампами

```bash
# Turn on/off
openhue set light "Bedroom Lamp" --on
openhue set light "Bedroom Lamp" --off

# Brightness (0-100)
openhue set light "Bedroom Lamp" --on --brightness 50

# Color temperature (warm to cool: 153-500 mirek)
openhue set light "Bedroom Lamp" --on --temperature 300

# Color (by name or hex)
openhue set light "Bedroom Lamp" --on --color red
openhue set light "Bedroom Lamp" --on --rgb "#FF5500"
```

### Керування кімнатами

```bash
# Turn off entire room
openhue set room "Bedroom" --off

# Set room brightness
openhue set room "Bedroom" --on --brightness 30
```

### Сцени

```bash
openhue set scene "Relax" --room "Bedroom"
openhue set scene "Concentrate" --room "Office"
```

## Швидкі пресети

```bash
# Bedtime (dim warm)
openhue set room "Bedroom" --on --brightness 20 --temperature 450

# Work mode (bright cool)
openhue set room "Office" --on --brightness 100 --temperature 250

# Movie mode (dim)
openhue set room "Living Room" --on --brightness 10

# Everything off
openhue set room "Bedroom" --off
openhue set room "Office" --off
openhue set room "Living Room" --off
```

## Примітки

- Bridge має бути в тій самій локальній мережі, що й комп’ютер, на якому запущений Hermes
- Перший запуск вимагає фізичного натискання кнопки на Hue Bridge для авторизації
- Кольори працюють лише з лампочками, що підтримують колір (не лише білими моделями)
- Імена ламп і кімнат чутливі до регістру — використовуйте `openhue get light`, щоб перевірити точні назви
- Чудово підходить для cron‑завдань для планового освітлення (наприклад, затемнити перед сном, яскраво ввімкнути під час пробудження)