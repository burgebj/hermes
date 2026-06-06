---
title: "Searxng Search — бесплатный метапоиск через SearXNG — агрегирует результаты более чем 70 поисковыми системами"
sidebar_label: "Searxng Search"
description: "Бесплатный метапоиск через SearXNG — агрегирует результаты более чем 70 поисковых систем"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Поиск SearXNG

Бесплатный метапоиск через SearXNG — агрегирует результаты более чем 70 поисковыми системами. Саморазмещаемый или используемый публичный экземпляр. API‑ключ не требуется. Автоматически переходит в запасной (fallback) режим, когда набор инструментов веб‑поиска недоступен.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/research/searxng-search` |
| Path | `optional-skills/research/searxng-search` |
| Version | `1.0.0` |
| Author | hermes-agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `search`, `searxng`, `meta-search`, `self-hosted`, `free`, `fallback` |
| Related skills | [`duckduckgo-search`](/docs/user-guide/skills/optional/research/research-duckduckgo-search), [`domain-intel`](/docs/user-guide/skills/optional/research/research-domain-intel) |

## Ссылка: полный SKILL.md

:::info
Ниже полное определение навыка, которое Hermes загружает, когда этот навык вызывается. Это то, что агент видит как инструкции, когда навык активен.
:::

# SearXNG Search

Free meta-search using [SearXNG](https://searxng.org/) — a privacy-respecting, self-hosted search aggregator that queries 70+ search engines simultaneously.

**No API key required** when using a public instance. Can also be self-hosted for full control. Automatically appears as a fallback when the main web search toolset (`FIRECRAWL_API_KEY`) is not configured.

## Конфигурация

SearXNG требует переменную окружения `SEARXNG_URL`, указывающую на ваш экземпляр SearXNG:

```bash
# Public instances (no setup required)
SEARXNG_URL=https://searxng.example.com

# Self-hosted SearXNG
SEARXNG_URL=http://localhost:8888
```

Если экземпляр не настроен, навык недоступен, и агент переходит к другим вариантам поиска.

## Поток обнаружения

Проверь, что действительно доступно, прежде чем выбирать подход:

```bash
# Check if SEARXNG_URL is set and the instance is reachable
curl -s --max-time 5 "${SEARXNG_URL}/search?q=test&format=json" | head -c 200
```

Дерево решений:
1. Если `SEARXNG_URL` установлен и экземпляр отвечает, использовать SearXNG.
2. Если `SEARXNG_URL` не установлен или недоступен, перейти к другим доступным инструментам поиска.
3. Если пользователь явно хочет SearXNG, помочь ему настроить экземпляр или найти публичный.

## Метод 1: CLI через curl (рекомендовано)

Вызови `curl` через `terminal`, чтобы обратиться к JSON‑API SearXNG. Это избавляет от предположения, что установлен какой‑то конкретный Python‑пакет.

```bash
# Text search (JSON output)
curl -s --max-time 10 \
  "${SEARXNG_URL}/search?q=python+async+programming&format=json&engines=google,bing&limit=10"

# With Safesearch off
curl -s --max-time 10 \
  "${SEARXNG_URL}/search?q=example&format=json&safesearch=0"

# Specific categories (general, news, science, etc.)
curl -s --max-time 10 \
  "${SEARXNG_URL}/search?q=AI+news&format=json&categories=news"
```

### Распространённые флаги CLI

| Флаг | Описание | Пример |
|------|----------|--------|
| `q` | Строка запроса (URL‑закодирована) | `q=python+async` |
| `format` | Формат вывода: `json`, `csv`, `rss` | `format=json` |
| `engines` | Имена движков через запятую | `engines=google,bing,ddg` |
| `limit` | Максимум результатов на движок (по умолчанию 10) | `limit=5` |
| `categories` | Фильтр по категории | `categories=news,science` |
| `safesearch` | 0=отключён, 1=умеренный, 2=строгий | `safesearch=0` |
| `time_range` | Фильтр по времени: `day`, `week`, `month`, `year` | `time_range=week` |

### Разбор JSON‑результатов

```bash
# Extract titles and URLs from JSON
curl -s --max-time 10 "${SEARXNG_URL}/search?q=fastapi&format=json&limit=5" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(r.get('title',''))
    print(r.get('url',''))
    print(r.get('content','')[:200])
    print()
"
```

Возвращаемые поля для каждого результата: `title`, `url`, `content` (snippet), `engine`, `parsed_url`, `img_src`, `thumbnail`, `author`, `published_date`.

## Метод 2: Python API через `requests`

Обращайся к REST‑API SearXNG напрямую из Python с помощью библиотеки `requests`:

```python
import os, requests, urllib.parse

base_url = os.environ.get("SEARXNG_URL", "")
if not base_url:
    raise RuntimeError("SEARXNG_URL is not set")

query = "fastapi deployment guide"
params = {
    "q": query,
    "format": "json",
    "limit": 5,
    "engines": "google,bing",
}

resp = requests.get(f"{base_url}/search", params=params, timeout=10)
resp.raise_for_status()
data = resp.json()

for r in data.get("results", []):
    print(r["title"])
    print(r["url"])
    print(r.get("content", "")[:200])
    print()
```

## Метод 3: Python‑пакет `searxng-data`

Для более структурированного доступа установи пакет `searxng-data`:

```bash
pip install searxng-data
```

```python
from searxng_data import engines

# List available engines
print(engines.list_engines())
```

> Примечание: пакет предоставляет только метаданные движков, а не сам поисковый API.

## Саморазмещение SearXNG

Чтобы запустить собственный экземпляр SearXNG:

```bash
# Using Docker
docker run -d -p 8888:8080 \
  -v $(pwd)/searxng:/etc/searxng \
  searxng/searxng:latest

# Then set
SEARXNG_URL=http://localhost:8888
```

Или установить через pip:

```bash
pip install searxng
# Edit /etc/searxng/settings.yml
searxng-run
```

Публичные экземпляры SearXNG доступны по адресу:
- `https://searxng.example.com` (замени на любой публичный экземпляр)

## Рабочий процесс: поиск, затем извлечение

SearXNG возвращает только заголовки, URL и сниппеты — не полный контент страниц. Чтобы получить полное содержимое, сначала выполните поиск, а затем извлеките наиболее релевантный URL с помощью `web_extract`, браузерных инструментов или `curl`.

```bash
# Search for relevant pages
curl -s "${SEARXNG_URL}/search?q=fastapi+deployment&format=json&limit=3"
# Output: list of results with titles and URLs

# Then extract the best URL with web_extract
```

## Ограничения

- **Доступность экземпляра**: если экземпляр SearXNG недоступен, поиск не выполнится. Всегда проверяй, что `SEARXNG_URL` установлен и экземпляр доступен.
- **Отсутствие извлечения контента**: SearXNG возвращает лишь сниппеты. Для полного текста используй `web_extract`, браузерные инструменты или `curl`.
- **Ограничения по частоте запросов**: некоторые публичные экземпляры лимитируют запросы. Саморазмещение избавляет от этого.
- **Набор движков**: доступные движки зависят от конфигурации конкретного экземпляра; некоторые могут быть отключены.
- **Актуальность результатов**: метапоиск агрегирует внешние движки, поэтому свежесть результатов определяется этими движками.

## Устранение неполадок

| Проблема | Возможная причина | Что делать |
|----------|-------------------|------------|
| `SEARXNG_URL` не установлен | Нет настроенного экземпляра | Использовать публичный экземпляр SearXNG или развернуть свой |
| Connection refused | Экземпляр не запущен или указан неверный URL | Проверить правильность URL и запущен ли экземпляр |
| Empty results | Экземпляр блокирует запрос | Попробовать другой публичный экземпляр или развернуть свой |
| Slow responses | Публичный экземпляр перегружен | Саморазместить или выбрать менее загруженный публичный экземпляр |
| `json` format not supported | Старая версия SearXNG | Попробовать `format=rss` или обновить SearXNG |

## Подводные камни

- **Всегда задавай `SEARXNG_URL`**: без него навык не будет работать.
- **URL‑кодируй запросы**: пробелы и специальные символы должны быть закодированы в curl, либо используй `urllib.parse.quote()` в Python.
- **Запрашивай `format=json`**: формат по умолчанию может быть не машинно‑читаемым. Явно указывай JSON.
- **Устанавливай таймаут**: используй `--max-time` или параметр `timeout=`, чтобы избежать зависаний при недоступных экземплярах.
- **Саморазмещение — лучший вариант**: публичные экземпляры могут падать, лимитировать запросы или блокировать их. Саморазмещённый экземпляр надёжен.

## Поиск экземпляров

Если `SEARXNG_URL` не задан и пользователь интересуется SearXNG, помоги ему:
1. Найти публичный экземпляр SearXNG (поиск по запросу «public searxng instance»).
2. Настроить собственный с помощью Docker или pip.

Публичные экземпляры перечислены здесь: https://searxng.org/