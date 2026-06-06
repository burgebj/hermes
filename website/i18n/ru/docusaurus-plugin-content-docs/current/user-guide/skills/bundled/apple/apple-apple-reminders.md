---
title: "Apple Reminders — Apple Reminders через remindctl: add, list, complete"
sidebar_label: "Apple Reminders"
description: "Apple Reminders через remindctl: add, list, complete"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Apple Reminders

Apple Reminders через remindctl: добавить, вывести список, завершить.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/apple/apple-reminders` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | macos |
| Tags | `Reminders`, `tasks`, `todo`, `macOS`, `Apple` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Apple Reminders

Используй `remindctl` для управления Apple Reminders напрямую из терминала. Задачи синхронизируются между всеми устройствами Apple через iCloud.

## Предварительные требования

- **macOS** с приложением Reminders.app
- Установить: `brew install steipete/tap/remindctl`
- Предоставь приложению Reminders разрешение, когда будет запрошено
- Проверить: `remindctl status` / Запросить: `remindctl authorize`

## Когда использовать

- Пользователь упоминает «reminder» или «Reminders app»
- Создание личных задач с датами выполнения, которые синхронизируются с iOS
- Управление списками Apple Reminders
- Пользователь хочет, чтобы задачи отображались на его iPhone/iPad

## Когда НЕ использовать

- Планирование оповещений агента → используй инструмент cronjob вместо этого
- События календаря → используй Apple Calendar или Google Calendar
- Управление проектными задачами → используй GitHub Issues, Notion и т.п.
- Если пользователь говорит «remind me», но имеет в виду оповещение агента → сначала уточни

## Быстрая справка

### Просмотр напоминаний

```bash
remindctl                    # Today's reminders
remindctl today              # Today
remindctl tomorrow           # Tomorrow
remindctl week               # This week
remindctl overdue            # Past due
remindctl all                # Everything
remindctl 2026-01-04         # Specific date
```

### Управление списками

```bash
remindctl list               # List all lists
remindctl list Work          # Show specific list
remindctl list Projects --create    # Create list
remindctl list Work --delete        # Delete list
```

### Создание напоминаний

```bash
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting prep" --due "2026-02-15 09:00"
```

### Дата выполнения vs Сигнал/Раннее напоминание

`--due` и `--alarm` — разные поля:

- `--due` задаёт дату/время выполнения напоминания.
- `--alarm` задаёт триггер сигнала/уведомления EventKit. При тайм‑заданном выполнении по умолчанию может быть установлен сигнал в момент выполнения, но передай `--alarm` явно, когда пользователь просит более раннее напоминание.

Для напоминания, выполненного в 14:00 с уведомлением за 30 минут до этого:

```bash
remindctl add --title "Hairdresser" --due "2026-05-15 14:00" --alarm "2026-05-15 13:30"
```

Чтобы отредактировать существующее напоминание:

```bash
remindctl edit 87354 --due "2026-05-15 14:00" --alarm "2026-05-15 13:30"
```

Интерфейс Reminders может показывать или группировать элемент по времени сигнала, потому что именно тогда срабатывает уведомление. Проверь с помощью JSON, а не полагайся, что время выполнения изменилось:

```bash
remindctl today --json
```

Ожидаемая структура:

- `dueDate`: фактическое время выполнения
- `alarmDate`: время сигнала / раннего напоминания

Публичные документы Apple `EKReminder` перечисляют только свойства, специфичные для напоминаний. Поддержка сигнала приходит из наследованного поведения `EKCalendarItem`, которое expose‑ится флагом `--alarm` в remindctl.

### Завершить / Удалить

```bash
remindctl complete 1 2 3          # Complete by ID
remindctl delete 4A83 --force     # Delete by ID
```

### Форматы вывода

```bash
remindctl today --json       # JSON for scripting
remindctl today --plain      # TSV format
remindctl today --quiet      # Counts only
```

## Форматы дат

Поддерживаются `--due` и фильтрами дат:
- `today`, `tomorrow`, `yesterday`
- `YYYY-MM-DD`
- `YYYY-MM-DD HH:mm`
- ISO 8601 (`2026-01-04T12:34:56Z`)

## Правила

1. Когда пользователь говорит «remind me», уточни: Apple Reminders (синхронизируется с телефоном) vs оповещение агента cronjob
2. Всегда подтверждай содержание напоминания и дату выполнения перед созданием
3. Используй `--json` для программного парсинга