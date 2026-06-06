---
title: "Blogwatcher — Мониторинг блогов и RSS/Atom лент через инструмент blogwatcher-cli"
sidebar_label: "Blogwatcher"
description: "Отслеживай блоги и RSS/Atom‑ленты с помощью инструмента blogwatcher-cli"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Blogwatcher

Отслеживание блогов и RSS/Atom‑лент с помощью инструмента `blogwatcher-cli`.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/blogwatcher` |
| Version | `2.0.0` |
| Author | JulienTant (fork of Hyaxia/blogwatcher) |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `RSS`, `Blogs`, `Feed-Reader`, `Monitoring` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Blogwatcher

Отслеживание обновлений блога и RSS/Atom‑ленты с помощью инструмента `blogwatcher-cli`. Поддерживает автоматическое обнаружение лент, запасной вариант — скрейпинг HTML, импорт OPML и управление прочитанными/непрочитанными статьями.

## Installation

Выбери один из методов:

- **Go:** `go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest`
- **Docker:** `docker run --rm -v blogwatcher-cli:/data ghcr.io/julientant/blogwatcher-cli`
- **Binary (Linux amd64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (Linux arm64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (macOS Apple Silicon):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (macOS Intel):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`

All releases: https://github.com/JulienTant/blogwatcher-cli/releases

### Docker with persistent storage

По умолчанию база данных находится в `~/.blogwatcher-cli/blogwatcher-cli.db`. В Docker она теряется при перезапуске контейнера. Используй `BLOGWATCHER_DB` или монтирование тома, чтобы сохранить её:

```bash
# Named volume (simplest)
docker run --rm -v blogwatcher-cli:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan

# Host bind mount
docker run --rm -v /path/on/host:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan
```

### Migrating from the original blogwatcher

Если переходишь с `Hyaxia/blogwatcher`, перемести свою базу данных:

```bash
mv ~/.blogwatcher/blogwatcher.db ~/.blogwatcher-cli/blogwatcher-cli.db
```

Имя бинарного файла изменилось с `blogwatcher` на `blogwatcher-cli`.

## Common Commands

### Managing blogs

- Добавить блог: `blogwatcher-cli add "My Blog" https://example.com`
- Добавить с указанием ленты: `blogwatcher-cli add "My Blog" https://example.com --feed-url https://example.com/feed.xml`
- Добавить с HTML‑скрейпингом: `blogwatcher-cli add "My Blog" https://example.com --scrape-selector "article h2 a"`
- Показать отслеживаемые блоги: `blogwatcher-cli blogs`
- Удалить блог: `blogwatcher-cli remove "My Blog" --yes`
- Импортировать из OPML: `blogwatcher-cli import subscriptions.opml`

### Scanning and reading

- Сканировать все блоги: `blogwatcher-cli scan`
- Сканировать один блог: `blogwatcher-cli scan "My Blog"`
- Показать непрочитанные статьи: `blogwatcher-cli articles`
- Показать все статьи: `blogwatcher-cli articles --all`
- Фильтр по блогу: `blogwatcher-cli articles --blog "My Blog"`
- Фильтр по категории: `blogwatcher-cli articles --category "Engineering"`
- Отметить статью как прочитанную: `blogwatcher-cli read 1`
- Отметить статью как непрочитанную: `blogwatcher-cli unread 1`
- Отметить все как прочитанные: `blogwatcher-cli read-all`
- Отметить все статьи блога как прочитанные: `blogwatcher-cli read-all --blog "My Blog" --yes`

## Environment Variables

Все флаги можно задать через переменные окружения с префиксом `BLOGWATCHER_`:

| Variable | Description |
|---|---|
| `BLOGWATCHER_DB` | Путь к файлу базы SQLite |
| `BLOGWATCHER_WORKERS` | Количество одновременно работающих сканеров (по умолчанию: 8) |
| `BLOGWATCHER_SILENT` | Выводить только сообщение «scan done» при сканировании |
| `BLOGWATCHER_YES` | Пропускать запросы подтверждения |
| `BLOGWATCHER_CATEGORY` | Фильтр по умолчанию для статей по категории |

## Example Output

```
$ blogwatcher-cli blogs
Tracked blogs (1):

  xkcd
    URL: https://xkcd.com
    Feed: https://xkcd.com/atom.xml
    Last scanned: 2026-04-03 10:30
```

```
$ blogwatcher-cli scan
Scanning 1 blog(s)...

  xkcd
    Source: RSS | Found: 4 | New: 4

Found 4 new article(s) total!
```

```
$ blogwatcher-cli articles
Unread articles (2):

  [1] [new] Barrel - Part 13
       Blog: xkcd
       URL: https://xkcd.com/3095/
       Published: 2026-04-02
       Categories: Comics, Science

  [2] [new] Volcano Fact
       Blog: xkcd
       URL: https://xkcd.com/3094/
       Published: 2026-04-01
       Categories: Comics
```

## Notes

- Автоматически обнаруживает RSS/Atom‑ленты на главных страницах блогов, если не указан `--feed-url`.
- Переходит к HTML‑скрейпингу, если RSS не удалось получить и настроен `--scrape-selector`.
- Категории из RSS/Atom‑лент сохраняются и могут использоваться для фильтрации статей.
- Массовый импорт блогов из OPML‑файлов, экспортированных из Feedly, Inoreader, NewsBlur и др.
- База данных хранится в `~/.blogwatcher-cli/blogwatcher-cli.db` по умолчанию (можно переопределить с помощью `--db` или `BLOGWATCHER_DB`).
- Используй `blogwatcher-cli <command> --help`, чтобы увидеть все флаги и опции.