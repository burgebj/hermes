---
title: "Gif Search — Пошук/завантаження GIF‑файлів з Tenor за допомогою curl + jq"
sidebar_label: "Gif Search"
description: "Пошук/завантаження GIF‑файлів з Tenor за допомогою curl + jq"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Пошук GIF

Пошук/завантаження GIF‑ів з Tenor за допомогою `curl` + `jq`.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/gif-search` |
| Version | `1.1.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `GIF`, `Media`, `Search`, `Tenor`, `API` |

## Посилання: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# GIF Search (Tenor API)

Пошук і завантаження GIF‑ів безпосередньо через Tenor API за допомогою `curl`. Додаткові інструменти не потрібні.

## Коли використовувати

Корисно для пошуку реакційних GIF‑ів, створення візуального контенту та надсилання GIF‑ів у чаті.

## Налаштування

Встанови свій ключ API Tenor у середовище (додай у `~/.hermes/.env`):

```bash
TENOR_API_KEY=your_key_here
```

Отримай безкоштовний ключ API за адресою https://developers.google.com/tenor/guides/quickstart — ключ API Tenor у Google Cloud Console безкоштовний і має щедрі ліміти запитів.

## Передумови

- `curl` і `jq` (обидва стандартні в macOS/Linux)
- змінна середовища `TENOR_API_KEY`

## Пошук GIF‑ів

```bash
# Search and get GIF URLs
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.gif.url'

# Get smaller/preview versions
curl -s "https://tenor.googleapis.com/v2/search?q=nice+work&limit=3&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.tinygif.url'
```

## Завантаження GIF‑а

```bash
# Search and download the top result
URL=$(curl -s "https://tenor.googleapis.com/v2/search?q=celebration&limit=1&key=${TENOR_API_KEY}" | jq -r '.results[0].media_formats.gif.url')
curl -sL "$URL" -o celebration.gif
```

## Отримання повних метаданих

```bash
curl -s "https://tenor.googleapis.com/v2/search?q=cat&limit=3&key=${TENOR_API_KEY}" | jq '.results[] | {title: .title, url: .media_formats.gif.url, preview: .media_formats.tinygif.url, dimensions: .media_formats.gif.dims}'
```

## Параметри API

| Parameter | Description |
|-----------|-------------|
| `q` | Запит пошуку (URL‑кодуй пробіли як `+`) |
| `limit` | Максимальна кількість результатів (1‑50, за замовчуванням 20) |
| `key` | Ключ API (з змінної `$TENOR_API_KEY`) |
| `media_filter` | Фільтр форматів: `gif`, `tinygif`, `mp4`, `tinymp4`, `webm` |
| `contentfilter` | Безпека: `off`, `low`, `medium`, `high` |
| `locale` | Мова: `en_US`, `es`, `fr` тощо |

## Доступні формати медіа

Кожен результат має кілька форматів у `.media_formats`:

| Format | Use case |
|--------|----------|
| `gif` | GIF повної якості |
| `tinygif` | Маленьке прев’ю GIF |
| `mp4` | Відео‑версія (менший розмір файлу) |
| `tinymp4` | Маленьке прев’ю відео |
| `webm` | WebM‑відео |
| `nanogif` | Дрібна мініатюра |

## Примітки

- URL‑кодуй запит: пробіли як `+`, спеціальні символи як `%XX`
- Для надсилання в чаті URL‑и `tinygif` легші
- URL‑и GIF можна використовувати безпосередньно в markdown: `![alt](https://github.com/NousResearch/hermes-agent/blob/main/skills/media/gif-search/url)`