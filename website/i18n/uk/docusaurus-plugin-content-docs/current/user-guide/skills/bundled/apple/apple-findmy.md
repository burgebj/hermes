---
title: "Findmy — Відстежуй пристрої Apple/AirTags через FindMy"
sidebar_label: "Findmy"
description: "Відстежуй пристрої Apple/AirTags через FindMy"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Findmy

Відстежуй пристрої Apple/AirTags через FindMy.app у macOS.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/apple/findmy` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | macos |
| Tags | `FindMy`, `AirTag`, `location`, `tracking`, `macOS`, `Apple` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Find My (Apple)

Відстежуй пристрої Apple та AirTags через FindMy.app у macOS. Оскільки Apple не надає CLI для FindMy, ця навичка використовує AppleScript для відкриття програми та захоплення екрану для зчитування розташувань пристроїв.

## Передумови

- **macOS** з встановленим додатком Find My та підключеним iCloud
- Пристрої/AirTags вже зареєстровані у Find My
- Дозвіл на запис екрану для терміналу (System Settings → Privacy → Screen Recording)
- **Опційно, але рекомендовано**: встановити `peekaboo` для кращої автоматизації UI:
  `brew install steipete/tap/peekaboo`

## Коли використовувати

- Користувач запитує «де мій [пристрій/кіт/ключі/сумка]?»
- Відстеження розташувань AirTag
- Перевірка розташувань пристроїв (iPhone, iPad, Mac, AirPods)
- Моніторинг переміщення домашніх тварин або предметів протягом часу (маршрути патрулювання AirTag)

## Метод 1: AppleScript + Screenshot (Базовий)

### Відкрити FindMy та перейти до потрібного розділу

```bash
# Open Find My app
osascript -e 'tell application "FindMy" to activate'

# Wait for it to load
sleep 3

# Take a screenshot of the Find My window
screencapture -w -o /tmp/findmy.png
```

Потім використати `vision_analyze` для зчитування скріншоту:
```
vision_analyze(image_url="/tmp/findmy.png", question="What devices/items are shown and what are their locations?")
```

### Перемикання між вкладками

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

## Метод 2: Peekaboo UI Automation (Рекомендовано)

Якщо встановлено `peekaboo`, використай його для більш надійної взаємодії з UI:
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

Потім проаналізуй за допомогою `vision_analyze`:
```
vision_analyze(image_url="/tmp/findmy-detail.png", question="What is the location shown for this device/item? Include address and coordinates if visible.")
```

## Робочий процес: Відстеження розташування AirTag протягом часу

Для моніторингу AirTag (наприклад, відстеження маршруту патрулювання кота):
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

Аналізуй кожен скріншот за допомогою `vision_analyze`, щоб отримати координати, і складай маршрут.

## Обмеження

- FindMy не має **CLI або API** — потрібно використовувати автоматизацію UI
- AirTags оновлюють розташування лише тоді, коли сторінка FindMy активно відображається
- Точність розташування залежить від близьких пристроїв Apple у мережі FindMy
- Потрібен дозвіл на запис екрану для скріншотів
- Автоматизація UI через AppleScript може перестати працювати в різних версіях macOS

## Правила

1. Тримай додаток FindMy у передньому плані під час відстеження AirTags (оновлення зупиняються при мінімізації)
2. Використовуй `vision_analyze` для зчитування вмісту скріншоту — не намагайся аналізувати пікселі вручну
3. Для безперервного відстеження використай `cronjob`, щоб періодично захоплювати та записувати розташування
4. Дотримуйся конфіденційності — відстежуй лише пристрої/предмети, що належать користувачу