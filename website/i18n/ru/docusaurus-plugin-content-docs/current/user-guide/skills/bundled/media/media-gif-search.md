---
title: "Gif Search — Поиск/скачивание GIF‑файлов с Tenor через curl + jq"
sidebar_label: "Gif Search"
description: "Искать/скачивать GIF‑файлы с Tenor с помощью curl + jq"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Поиск GIF

Поиск/загрузка GIF‑файлов из Tenor с помощью curl + jq.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/gif-search` |
| Version | `1.1.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `GIF`, `Media`, `Search`, `Tenor`, `API` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при активном навыке.
:::

# GIF Search (Tenor API)

Поиск и загрузка GIF‑файлов напрямую через Tenor API с помощью curl. Дополнительные инструменты не требуются.

## Когда использовать

Полезно для поиска реакционных GIF, создания визуального контента и отправки GIF в чат.

## Настройка

Установи свой Tenor API‑ключ в переменной окружения (добавь в `~/.hermes/.env`):

```bash
TENOR_API_KEY=your_key_here
```

Получить бесплатный API‑ключ можно на https://developers.google.com/tenor/guides/quickstart — ключ Tenor API в Google Cloud Console бесплатный и имеет щедрые ограничения по частоте запросов.

## Требования

- `curl` и `jq` (оба стандартны в macOS/Linux)
- переменная окружения `TENOR_API_KEY`

## Поиск GIF

```bash
# Search and get GIF URLs
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.gif.url'

# Get smaller/preview versions
curl -s "https://tenor.googleapis.com/v2/search?q=nice+work&limit=3&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.tinygif.url'
```

## Загрузка GIF

```bash
# Search and download the top result
URL=$(curl -s "https://tenor.googleapis.com/v2/search?q=celebration&limit=1&key=${TENOR_API_KEY}" | jq -r '.results[0].media_formats.gif.url')
curl -sL "$URL" -o celebration.gif
```

## Получение полной метаданных

```bash
curl -s "https://tenor.googleapis.com/v2/search?q=cat&limit=3&key=${TENOR_API_KEY}" | jq '.results[] | {title: .title, url: .media_formats.gif.url, preview: .media_formats.tinygif.url, dimensions: .media_formats.gif.dims}'
```

## Параметры API

| Parameter | Description |
|-----------|-------------|
| `q` | Поисковый запрос (пробелы кодировать как `+`) |
| `limit` | Максимальное количество результатов (1‑50, по умолчанию 20) |
| `key` | API‑ключ (из переменной окружения `$TENOR_API_KEY`) |
| `media_filter` | Форматы фильтра: `gif`, `tinygif`, `mp4`, `tinymp4`, `webm` |
| `contentfilter` | Безопасность: `off`, `low`, `medium`, `high` |
| `locale` | Язык: `en_US`, `es`, `fr` и т.д. |

## Доступные форматы медиа

Каждый результат имеет несколько форматов в `.media_formats`:

| Format | Use case |
|--------|----------|
| `gif` | GIF полного качества |
| `tinygif` | Маленькое превью‑GIF |
| `mp4` | Видео‑версия (меньший размер файла) |
| `tinymp4` | Маленькое превью‑видео |
| `webm` | WebM‑видео |
| `nanogif` | Крошечный миниатюрный GIF |

## Примечания

- Кодируй запрос в URL: пробелы как `+`, специальные символы как `%XX`.
- Для отправки в чат URL `tinygif` легче по весу.
- URL GIF можно использовать напрямую в markdown: `![alt](https://github.com/NousResearch/hermes-agent/blob/main/skills/media/gif-search/url)`