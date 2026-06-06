---
title: "Findmy — Отслеживай устройства Apple/AirTags через FindMy"
sidebar_label: "Findmy"
description: "Отслеживай устройства Apple/AirTags через FindMy"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Findmy

Отслеживание устройств Apple / AirTag через Find My.app в macOS.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/apple/findmy` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | macos |
| Tags | `FindMy`, `AirTag`, `location`, `tracking`, `macOS`, `Apple` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда навык активирован. Это то, что агент видит как инструкции при работе навыка.
:::

# Find My (Apple)

Отслеживание устройств Apple и AirTag через Find My.app в macOS. Поскольку Apple не предоставляет CLI для Find My, этот навык использует AppleScript для открытия приложения и захват экрана для чтения местоположения устройств.

## Требования

- **macOS** с установленным приложением Find My и входом в iCloud
- Устройства / AirTag уже зарегистрированы в Find My
- Разрешение на запись экрана для терминала (System Settings → Privacy → Screen Recording)
- **Опционально, но рекомендуется**: установить `peekaboo` для более надёжной UI‑автоматизации:
  `brew install steipete/tap/peekaboo`

## Когда использовать

- Пользователь спрашивает «где мой [устройство/кот/ключи/сумка]?»
- Отслеживание местоположения AirTag
- Проверка местоположения устройств (iPhone, iPad, Mac, AirPods)
- Мониторинг перемещения питомца или предмета во времени (маршруты патруля AirTag)

## Метод 1: AppleScript + Скриншот (Базовый)

### Открыть Find My и перейти к нужному разделу

```bash
# Open Find My app
osascript -e 'tell application "FindMy" to activate'

# Wait for it to load
sleep 3

# Take a screenshot of the Find My window
screencapture -w -o /tmp/findmy.png
```

Затем использовать `vision_analyze` для чтения скриншота:
```
vision_analyze(image_url="/tmp/findmy.png", question="What devices/items are shown and what are their locations?")
```

### Переключение между вкладками

```bash
# Switch to Devices tab
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Devices" of toolbar 1 of window 1
    end tell
end tell'

# Switch to Items tab (AirTags)
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
```

## Метод 2: UI‑автоматизация Peekaboo (Рекомендуемый)

Если установлен `peekaboo`, использовать его для более надёжного взаимодействия с UI:

```bash
# Open Find My
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Capture and annotate the UI
peekaboo see --app "FindMy" --annotate --path /tmp/findmy-ui.png

# Click on a specific device/item by element ID
peekaboo click --on B3 --app "FindMy"

# Capture the detail view
peekaboo image --app "FindMy" --path /tmp/findmy-detail.png
```

Затем проанализировать скриншот с помощью vision:
```
vision_analyze(image_url="/tmp/findmy-detail.png", question="What is the location shown for this device/item? Include address and coordinates if visible.")
```

## Рабочий процесс: отслеживание местоположения AirTag во времени

Для мониторинга AirTag (например, отслеживание маршрута патруля кота):

```bash
# 1. Open FindMy to Items tab
osascript -e 'tell application "FindMy" to activate'
sleep 3

# 2. Click on the AirTag item (stay on page — AirTag only updates when page is open)

# 3. Periodically capture location
while true; do
    screencapture -w -o /tmp/findmy-$(date +%H%M%S).png
    sleep 300  # Every 5 minutes
done
```

Анализировать каждый скриншот с помощью vision, извлекать координаты и собирать маршрут.

## Ограничения

- Find My **не имеет CLI или API** — необходимо использовать UI‑автоматизацию
- AirTag обновляют местоположение только пока страница Find My активно отображается
- Точность зависит от близлежащих устройств Apple в сети Find My
- Требуется разрешение на запись экрана для скриншотов
- UI‑автоматизация AppleScript может ломаться при обновлениях macOS

## Правила

1. Держи приложение Find My в переднем плане при отслеживании AirTag (обновления прекращаются при сворачивании)
2. Используй `vision_analyze` для чтения содержимого скриншота — не пытайся парсить отдельные пиксели
3. Для постоянного отслеживания используй `cronjob`, чтобы периодически захватывать и сохранять местоположения
4. Соблюдай конфиденциальность — отслеживай только те устройства/предметы, которые принадлежат пользователю