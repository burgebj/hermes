---
title: "Sherlock — OSINT пошук імен користувачів у понад 400 соціальних мережах"
sidebar_label: "Sherlock"
description: "OSINT пошук імен користувачів у понад 400 соціальних мережах"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Sherlock

OSINT username search across 400+ social networks. Hunt down social media accounts by username.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/security/sherlock` |
| Path | `optional-skills/security/sherlock` |
| Version | `1.0.0` |
| Author | unmodeled-tyler |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `osint`, `security`, `username`, `social-media`, `reconnaissance` |

## Довідка: повний SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Sherlock OSINT Username Search

Hunt down social media accounts by username across 400+ social networks using the [Sherlock Project](https://github.com/sherlock-project/sherlock).

## Коли використовувати

- Користувач просить знайти акаунти, пов’язані з ім’ям користувача
- Користувач хоче перевірити доступність імені користувача на різних платформах
- Користувач проводить OSINT або розвідувальні дослідження
- Користувач запитує «де зареєстровано це ім’я користувача?» або подібне

## Вимоги

- Sherlock CLI встановлений: `pipx install sherlock-project` або `pip install sherlock-project`
- Або: Docker доступний (`docker run -it --rm sherlock/sherlock`)
- Мережевий доступ для запитів до соціальних платформ

## Процедура

### 1. Перевірка, чи встановлений Sherlock

**Перед будь‑якими діями** перевір, чи доступний sherlock:

```bash
sherlock --version
```

Якщо команда не спрацює:
- Запропонуй встановити: `pipx install sherlock-project` (рекомендовано) або `pip install sherlock-project`
- **Не** використовуйте кілька методів встановлення — обери один і продовжуй
- Якщо встановлення не вдається, повідом користувача і зупинись

### 2. Витягнути ім'я користувача

**Витягни ім'я користувача безпосередньо з повідомлення користувача, якщо воно явно зазначене.**

Приклади, коли **не** слід уточнювати:
- “Find accounts for nasa” → ім'я користувача `nasa`
- “Search for johndoe123” → ім'я користувача `johndoe123`
- “Check if alice exists on social media” → ім'я користувача `alice`
- “Look up user bob on social networks” → ім'я користувача `bob`

**Уточнюй лише якщо:**
- Згадано кілька можливих імен користувачів (“search for alice or bob”)
- Формулювання неоднозначне (“search for my username” без уточнення)
- Ім'я користувача взагалі не вказано (“do an OSINT search”)

При витягуванні бережи **точне** ім'я, включаючи регістр, цифри, підкреслення тощо.

### 3. Побудувати команду

**Команда за замовчуванням** (використовуй її, якщо користувач не попросив іншого):
```bash
sherlock --print-found --no-color "<username>" --timeout 90
```

**Опціональні прапорці** (додавай лише за явним запитом користувача):
- `--nsfw` — включити NSFW‑сайти (тільки якщо користувач попросив)
- `--tor` — маршрутизувати через Tor (тільки якщо користувач попросив анонімність)

**Не став питання про параметри через clarify** — просто виконуй пошук за замовчуванням. Користувач може запросити додаткові опції за потреби.

### 4. Виконати пошук

Запусти через інструмент `terminal`. Команда зазвичай займає 30‑120 секунд залежно від мережі та кількості сайтів.

**Приклад виклику в терміналі:**
```json
{
  "command": "sherlock --print-found --no-color \"target_username\"",
  "timeout": 180
}
```

### 5. Розпарсити та представити результати

Sherlock виводить знайдені акаунти у простому форматі. Розпарси вивід і представ результати:

1. **Рядок‑резюме:** “Found X accounts for username 'Y'”
2. **Категоризовані посилання:** групуй за типом платформи, якщо це корисно (соціальні, професійні, форуми тощо)
3. **Розташування файлу результатів:** за замовчуванням Sherlock зберігає їх у `<username>.txt`

**Приклад розбору виводу:**
```
[+] Instagram: https://instagram.com/username
[+] Twitter: https://twitter.com/username
[+] GitHub: https://github.com/username
```

Представ результати як клікабельні посилання, коли це можливо.

## Підводні камені

### No Results Found
Якщо Sherlock не знайшов жодного акаунту, це часто правильно — ім'я може бути не зареєстроване на перевірених платформах. Запропонуй:
- Перевірити правопис/варіації
- Спробувати схожі імена з шаблоном `?`: `sherlock "user?name"`
- Можливі налаштування приватності або видалені акаунти

### Timeout Issues
Деякі сайти повільні або блокують автоматичні запити. Використай `--timeout 120` для збільшення часу очікування або `--site` для обмеження області пошуку.

### Tor Configuration
`--tor` потребує запущеного демона Tor. Якщо користувач хоче анонімність, а Tor недоступний, запропонуй:
- Встановити сервіс Tor
- Використати `--proxy` з іншим проксі

### False Positives
Деякі сайти завжди повертають “found” через структуру відповіді. Перевір підозрілі результати вручну.

### Rate Limiting
Агресивні пошуки можуть викликати обмеження швидкості. Для масових пошуків додавай затримки між запитами або використай `--local` з кешованими даними.

## Встановлення

### pipx (рекомендовано)
```bash
pipx install sherlock-project
```

### pip
```bash
pip install sherlock-project
```

### Docker
```bash
docker pull sherlock/sherlock
docker run -it --rm sherlock/sherlock <username>
```

### Пакети Linux
Доступно для Debian 13+, Ubuntu 22.10+, Homebrew, Kali, BlackArch.

## Етичне використання

Цей інструмент призначений лише для легітимних OSINT‑досліджень та наукових цілей. Нагадай користувачам:
- Шукати лише ті імена користувачів, які вони власні або мають дозвіл досліджувати
- Дотримуватись умов використання платформ
- Не використовувати для переслідування, домагань чи незаконних дій
- Розглядати питання конфіденційності перед поширенням результатів

## Верифікація

Після запуску sherlock перевір:
1. Вивід містить список знайдених сайтів з URL‑адресами
2. Створено файл `<username>.txt` (за замовчуванням) при використанні файлового виводу
3. Якщо використано `--print-found`, вивід має містити лише рядки `[+]` з результатами

## Приклад взаємодії

**User:** “Can you check if the username 'johndoe123' exists on social media?”

**Agent procedure:**
1. Перевір `sherlock --version` (переконайся, що встановлено)
2. Ім'я користувача задано — переходь далі
3. Запусти: `sherlock --print-found --no-color "johndoe123" --timeout 90`
4. Розпарси вивід і представ посилання

**Response format:**
> Found 12 accounts for username 'johndoe123':
>
> • https://twitter.com/johndoe123
> • https://github.com/johndoe123
> • https://instagram.com/johndoe123
> • [... additional links]
>
> Results saved to: johndoe123.txt

---

**User:** “Search for username 'alice' including NSFW sites”

**Agent procedure:**
1. Перевір, чи встановлений sherlock
2. Ім'я користувача та прапорець NSFW вказані
3. Запусти: `sherlock --print-found --no-color --nsfw "alice" --timeout 90`
4. Представ результати