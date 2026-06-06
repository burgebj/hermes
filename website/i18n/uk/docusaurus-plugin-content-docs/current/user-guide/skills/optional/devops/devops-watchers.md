---
title: "Watchers — опитування RSS, JSON APIs та GitHub з видаленням дублювання за водяним знаком"
sidebar_label: "Watchers"
description: "Опитувати RSS, JSON API та GitHub з видаленням дублікатів за водяним знаком"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Watchers

Poll RSS, JSON APIs, and GitHub with watermark dedup.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/devops/watchers` |
| Path | `optional-skills/devops/watchers` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `cron`, `polling`, `rss`, `github`, `http`, `automation`, `monitoring` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Watchers

Poll external sources on an interval and react only to new items. Three ready-made scripts plus a shared watermark helper; wire them into a cron job (or run them ad‑hoc from the terminal).

## Коли використовувати

- Користувач хоче стежити за RSS/Atom‑стрічкою і отримувати сповіщення про нові записи
- Користувач хоче стежити за issue / pull / release / commit у репозиторії GitHub
- Користувач хоче опитувати довільний JSON‑endpoint і отримувати сповіщення про нові елементи
- Користувач просить «watcher for X» або «notify me when X changes»

## Ментальна модель

Watcher — це просто скрипт, який:

1. Отримує дані з зовнішнього джерела
2. Порівнює їх із файлом‑водяним знаком, що містить раніше побачені ID
3. Записує новий водяний знак назад
4. Виводить нові елементи у stdout (або нічого, якщо змін немає)

Скрипти нижче обробляють усі три випадки. Агент запускає їх через інструмент **terminal** — з cron‑завдання, вебхука або інтерактивного чату — і повідомляє, що нового.

## Готові скрипти

Усі три розташовані в `$HERMES_HOME/skills/devops/watchers/scripts/` після встановлення навички. Кожен читає `WATCHER_STATE_DIR` (за замовчуванням `$HERMES_HOME/watcher-state/`) для свого файлу стану, ключованого аргументом `--name`.

| Script | What it watches | Dedup key |
|---|---|---|
| `watch_rss.py` | RSS 2.0 або Atom feed URL | `<guid>` / `<id>` |
| `watch_http_json.py` | Будь‑який JSON endpoint, що повертає список об’єктів | Configurable id field |
| `watch_github.py` | GitHub issues / pulls / releases / commits для репозиторію | `id` / `sha` |

Усі три:

- Перший запуск записує базову лінію — ніколи не відтворює існуючі записи
- Водяний знак — це обмежений набір ID (max 500) для контролю пам’яті
- Формат виводу: `## <title>\n<url>\n\n<optional body>` для кожного елементу
- Порожній stdout при відсутності нових записів — викликальник трактує це як «тихий» режим
- Ненульовий код виходу при помилках отримання

## Використання

Запусти watcher безпосередньо через інструмент **terminal**:

```bash
python $HERMES_HOME/skills/devops/watchers/scripts/watch_rss.py \
  --name hn --url https://news.ycombinator.com/rss --max 5
```

Watch a GitHub repo (set `GITHUB_TOKEN` in `~/.hermes/.env` to avoid the 60 req/hr anonymous rate limit):

```bash
python $HERMES_HOME/skills/devops/watchers/scripts/watch_github.py \
  --name hermes-issues --repo NousResearch/hermes-agent --scope issues
```

Poll an arbitrary JSON API:

```bash
python $HERMES_HOME/skills/devops/watchers/scripts/watch_http_json.py \
  --name api --url https://api.example.com/events \
  --id-field event_id --items-path data.events
```

## Підключення до cron

Попроси агента запланувати cron‑завдання, використовуючи підказку типу:

> Every 15 minutes, run `watch_rss.py --name hn --url https://news.ycombinator.com/rss`. If it prints anything, summarize the headlines and deliver them. If it prints nothing, stay silent.

The agent invokes the script via the terminal tool inside the cron job's agent loop; no changes to cron's built-in `--script` flag are needed.

## Файли стану

Кожен watcher записує `$HERMES_HOME/watcher-state/<name>.json`. Переглянь:

```bash
cat $HERMES_HOME/watcher-state/hn.json
```

Force a replay (next run treated as first poll):

```bash
rm $HERMES_HOME/watcher-state/hn.json
```

## Написання власного

Усі три скрипти використовують один шаблон: завантажити водяний знак, отримати дані, порівняти, зберегти, вивести. `scripts/_watermark.py` — спільний помічник; імпортуй його, щоб отримати атомарні записи + обмежений набір ID + базову лінію без додаткових зусиль. Дивись будь‑який із трьох референтних скриптів, щоб зрозуміти, скільки коду потрібно.

## Поширені підводні камені

1. **Виведення заголовка «no new items» кожного разу.** Викликальники очікують порожній stdout = тихий режим. Якщо ти виводиш щось при порожньому дельті, ти спамиш канал. Шиплені скрипти це враховують; кастомні скрипти мають робити те ж саме.
2. **Очікування, що перший запуск виведе елементи.** Він не виведе — перший запуск лише записує базову лінію. Якщо потрібен початковий дайджест, видали файл стану після першого запуску або додай прапорець `--prime-with-latest N` у власний скрипт.
3. **Необмежене зростання водяного знака.** Спільний помічник обмежує його 500 ID. Підвищуй це значення для стрімких фідів; знижуй на обмежених файлових системах.
4. **Розміщення каталогу стану там, де пісочниця агента не може писати.** `$HERMES_HOME/watcher-state/` завжди доступний для запису. Docker/Modal бекенди можуть не бачити довільні шляхи хоста.