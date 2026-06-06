---
title: "Apple Reminders — Apple Reminders через remindctl: add, list, complete"
sidebar_label: "Apple Reminders"
description: "Apple Reminders через remindctl: додати, переглянути, завершити"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Apple Reminders

Apple Reminders via remindctl: add, list, complete.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/apple/apple-reminders` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | macos |
| Tags | `Reminders`, `tasks`, `todo`, `macOS`, `Apple` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# Apple Reminders

Використовуй `remindctl` для керування Apple Reminders безпосередньо з терміналу. Завдання синхронізуються між усіма пристроями Apple через iCloud.

## Передумови

- **macOS** з Reminders.app
- Встановити: `brew install steipete/tap/remindctl`
- Надати Reminders дозвіл, коли буде запитано
- Перевірити: `remindctl status` / Запит: `remindctl authorize`

## Коли використовувати

- Користувач згадує «reminder» або «Reminders app»
- Створення особистих справ з датами завершення, які синхронізуються з iOS
- Керування списками Apple Reminders
- Користувач хоче, щоб завдання відображалися на його iPhone/iPad

## Коли НЕ використовувати

- Планування сповіщень агента → використай інструмент cronjob
- Події календаря → використай Apple Calendar або Google Calendar
- Управління завданнями проєкту → використай GitHub Issues, Notion тощо
- Якщо користувач каже «remind me», маючи на увазі сповіщення агента → спочатку уточни

## Швидка довідка

### Перегляд нагадувань

```bash
remindctl                    # Today's reminders
remindctl today              # Today
remindctl tomorrow           # Tomorrow
remindctl week               # This week
remindctl overdue            # Past due
remindctl all                # Everything
remindctl 2026-01-04         # Specific date
```

### Керування списками

```bash
remindctl list               # List all lists
remindctl list Work          # Show specific list
remindctl list Projects --create    # Create list
remindctl list Work --delete        # Delete list
```

### Створення нагадувань

```bash
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting prep" --due "2026-02-15 09:00"
```

### Час завершення vs Сповіщення / Раннє нагадування

`--due` і `--alarm` — це різні поля:

- `--due` встановлює дату/час завершення нагадування.
- `--alarm` встановлює тригер сповіщення EventKit. Таймовані нагадування можуть за замовчуванням мати сповіщення в момент завершення, але передавай `--alarm` явно, коли користувач просить нагадати раніше.

Для нагадування, запланованого на 14:00 з повідомленням за 30 хвилин до цього:

```bash
remindctl add --title "Hairdresser" --due "2026-05-15 14:00" --alarm "2026-05-15 13:30"
```

Щоб відредагувати існуюче нагадування:

```bash
remindctl edit 87354 --due "2026-05-15 14:00" --alarm "2026-05-15 13:30"
```

Інтерфейс Reminders може показувати або групувати елемент за часом сповіщення, оскільки саме тоді спрацьовує повідомлення. Перевіряй за допомогою JSON, а не припускай, що час завершення змінився:

```bash
remindctl today --json
```

Очікувана структура:

- `dueDate`: фактичний час завершення
- `alarmDate`: час сповіщення / раннього нагадування

Публічні документи Apple `EKReminder` перераховують лише властивості, специфічні для нагадувань. Підтримка сповіщень походить від успадкованої поведінки `EKCalendarItem`, яку expose‑є прапорець `--alarm` у remindctl.

### Завершити / Видалити

```bash
remindctl complete 1 2 3          # Complete by ID
remindctl delete 4A83 --force     # Delete by ID
```

### Формати виводу

```bash
remindctl today --json       # JSON for scripting
remindctl today --plain      # TSV format
remindctl today --quiet      # Counts only
```

## Формати дат

Приймаються `--due` та фільтрами дат:
- `today`, `tomorrow`, `yesterday`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH:mm`
- ISO 8601 (`2026-01-04T12:34:56Z`)

## Правила

1. Коли користувач каже «remind me», уточнюй: Apple Reminders (синхронізується з телефоном) чи сповіщення агента cronjob
2. Завжди підтверджуй вміст нагадування та дату завершення перед створенням
3. Використовуй `--json` для програмного парсингу