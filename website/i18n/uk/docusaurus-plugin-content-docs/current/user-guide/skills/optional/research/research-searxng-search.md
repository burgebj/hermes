---
title: "Searxng Search — Безкоштовний метапошук через SearXNG — агрегує результати з більш ніж 70 пошукових систем"
sidebar_label: "Searxng Search"
description: "Безкоштовний метапошук через SearXNG — агрегує результати з більш ніж 70 пошукових систем"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Пошук SearXNG

Безкоштовний метапошук через SearXNG — агрегує результати з 70+ пошукових систем. Самостійно розгорнутий або використай публічний інстанс. Ключ API не потрібен. Автоматично переходить у **запасний (варіант)**, коли інструмент веб‑пошуку недоступний.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# SearXNG Search

Безкоштовний метапошук за допомогою [SearXNG](https://searxng.org/) — агрегатора пошуку, що поважає приватність, самостійно розгорнутого і одночасно запитує 70+ пошукових систем.

**Ключ API не потрібен** при використанні публічного інстансу. Можна також розгорнути самостійно для повного контролю. Автоматично з’являється як **запасний (варіант)**, коли основний інструмент веб‑пошуку (`FIRECRAWL_API_KEY`) не налаштований.

## Конфігурація

SearXNG потребує змінної середовища `SEARXNG_URL`, що вказує на ваш інстанс SearXNG:

```bash
# Public instances (no setup required)
SEARXNG_URL=https://searxng.example.com

# Self-hosted SearXNG
SEARXNG_URL=http://localhost:8888
```

Якщо інстанс не налаштований, ця навичка недоступна і агент переходить до інших варіантів пошуку.

## Потік виявлення

Перевірте, що саме доступно, перед вибором підходу:

```bash
# Check if SEARXNG_URL is set and the instance is reachable
curl -s --max-time 5 "${SEARXNG_URL}/search?q=test&format=json" | head -c 200
```

Дерево рішень:
1. Якщо `SEARXNG_URL` встановлено і інстанс відповідає, використовуй SearXNG.
2. Якщо `SEARXNG_URL` не встановлено або недоступний, переходь до інших доступних інструментів пошуку.
3. Якщо користувач явно хоче SearXNG, допоможи налаштувати інстанс або знайти публічний.

## Метод 1: CLI через curl (рекомендовано)

Використовуй `curl` у `terminal` для виклику JSON API SearXNG. Це дозволяє уникнути залежності від конкретного Python‑пакету.

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

### Поширені прапорці CLI

| Flag | Description | Example |
|------|-------------|---------|
| `q` | Рядок запиту (URL‑закодований) | `q=python+async` |
| `format` | Формат виводу: `json`, `csv`, `rss` | `format=json` |
| `engines` | Імена двигунів, розділені комами | `engines=google,bing,ddg` |
| `limit` | Максимальна кількість результатів на двигун (за замовчуванням 10) | `limit=5` |
| `categories` | Фільтр за категорією | `categories=news,science` |
| `safesearch` | 0=none, 1=moderate, 2=strict | `safesearch=0` |
| `time_range` | Фільтр: `day`, `week`, `month`, `year` | `time_range=week` |

### Парсинг JSON‑результатів

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

Повертає для кожного результату: `title`, `url`, `content` (snippet), `engine`, `parsed_url`, `img_src`, `thumbnail`, `author`, `published_date`.

## Метод 2: Python API через `requests`

Використовуй REST API SearXNG безпосередньо з Python за допомогою бібліотеки `requests`:

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

Для більш структурованого доступу встанови пакет `searxng-data`:

```bash
pip install searxng-data
```

```python
from searxng_data import engines

# List available engines
print(engines.list_engines())
```

Примітка: цей пакет надає лише метадані про двигуни, а не сам API пошуку.

## Самостійне розгортання SearXNG

Щоб запустити власний інстанс SearXNG:

```bash
# Using Docker
docker run -d -p 8888:8080 \
  -v $(pwd)/searxng:/etc/searxng \
  searxng/searxng:latest

# Then set
SEARXNG_URL=http://localhost:8888
```

Або встановити через pip:

```bash
pip install searxng
# Edit /etc/searxng/settings.yml
searxng-run
```

Публічні інстанси SearXNG доступні за:
- `https://searxng.example.com` (заміни на будь‑який публічний інстанс)

## Робочий процес: пошук → екстракція

SearXNG повертає назви, URL‑и та снипети — не повний вміст сторінок. Щоб отримати повний вміст, спочатку шукай, а потім витягни найбільш релевантний URL за допомогою `web_extract`, інструментів браузера або `curl`.

```bash
# Search for relevant pages
curl -s "${SEARXNG_URL}/search?q=fastapi+deployment&format=json&limit=3"
# Output: list of results with titles and URLs

# Then extract the best URL with web_extract
```

## Обмеження

- **Доступність інстансу**: Якщо інстанс SearXNG недоступний, пошук не вдається. Завжди перевіряй, що `SEARXNG_URL` встановлено і інстанс досяжний.
- **Відсутність екстракції вмісту**: SearXNG повертає лише снипети, а не повний вміст сторінки. Використовуй `web_extract`, інструменти браузера або `curl` для повних статей.
- **Обмеження швидкості**: Деякі публічні інстанси обмежують кількість запитів. Самостійне розгортання усуває це.
- **Покриття двигунів**: Доступні двигуни залежать від конфігурації вашого інстансу SearXNG. Деякі можуть бути вимкнені.
- **Свіжість результатів**: Метапошук агрегує зовнішні двигуни — свіжість результатів залежить від цих двигунів.

## Устранення проблем

| Problem | Likely Cause | What To Do |
|---------|--------------|------------|
| `SEARXNG_URL` not set | No instance configured | Use a public SearXNG instance or set up your own |
| Connection refused | Instance not running or wrong URL | Check the URL is correct and the instance is running |
| Empty results | Instance blocks the query | Try a different instance or self-host |
| Slow responses | Public instance under load | Self-host or use a less‑loaded public instance |
| `json` format not supported | Old SearXNG version | Try `format=rss` or upgrade SearXNG |

## Підводні камені

- **Завжди встановлюй `SEARXNG_URL`**: без цього навичка не працюватиме.
- **URL‑кодуй запити**: пробіли та спеціальні символи мають бути URL‑закодовані у `curl`, або використай `urllib.parse.quote()` у Python.
- **Використовуй `format=json`**: формат за замовчуванням може бути не машинозчитуваним. Завжди явно запитуй JSON.
- **Встанови тайм‑аут**: використовуйте `--max-time` або `timeout=` — щоб уникнути зависання при недоступних інстансах.
- **Самостійне розгортання — найкраще**: публічні інстанси можуть падати, обмежувати швидкість або блокувати запити. Самостійний інстанс надійний.

## Виявлення інстансів

Якщо `SEARXNG_URL` не встановлено і користувач запитує про SearXNG, допоможи йому:
1. Знайти публічний інстанс SearXNG (пошукай “public searxng instance”).
2. Налаштувати власний за допомогою Docker або pip.

Публічні інстанси перелічені за: https://searxng.org/