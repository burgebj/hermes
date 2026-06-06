---
title: "Openhue — Управляй светильниками Philips Hue, сценами, комнатами через OpenHue CLI"
sidebar_label: "Openhue"
description: "Управляй светильниками Philips Hue, сценами, комнатами через OpenHue CLI"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Openhue

Управляй лампами Philips Hue, сценами и комнатами через OpenHue CLI.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/smart-home/openhue` |
| Version | `1.0.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Smart-Home`, `Hue`, `Lights`, `IoT`, `Automation` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# OpenHue CLI

Управляй лампами Philips Hue и сценами через Hue Bridge из терминала.

## Требования

```bash
# Linux (pre-built binary)
curl -sL https://github.com/openhue/openhue-cli/releases/latest/download/openhue-linux-amd64 -o ~/.local/bin/openhue && chmod +x ~/.local/bin/openhue

# macOS
brew install openhue/cli/openhue-cli
```

Первый запуск требует нажать кнопку на твоём Hue Bridge для сопряжения. Мост должен находиться в той же локальной сети.

## Когда использовать

- «Включить/выключить свет»
- «Понизить яркость света в гостиной»
- «Установить сцену» или «режим кино»
- Управление конкретными комнатами, зонами или отдельными лампочками Hue
- Регулировка яркости, цвета или цветовой температуры

## Часто используемые команды

### Список ресурсов

```bash
openhue get light       # List all lights
openhue get room        # List all rooms
openhue get scene       # List all scenes
```

### Управление светом

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

### Управление комнатами

```bash
# Turn off entire room
openhue set room "Bedroom" --off

# Set room brightness
openhue set room "Bedroom" --on --brightness 30
```

### Сцены

```bash
openhue set scene "Relax" --room "Bedroom"
openhue set scene "Concentrate" --room "Office"
```

## Быстрые пресеты

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

## Примечания

- Мост должен находиться в той же локальной сети, что и машина, на которой запущен Hermes
- Первый запуск требует физически нажать кнопку на Hue Bridge для авторизации
- Цвета работают только с лампочками, поддерживающими цвет (не только белыми моделями)
- Имена ламп и комнат чувствительны к регистру — используй `openhue get light`, чтобы проверить точные имена
- Отлично подходит для cron‑задач для планового освещения (например, приглушить свет перед сном, включить яркий утром)