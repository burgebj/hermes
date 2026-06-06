---
title: "Duckduckgo Search — Бесплатный веб‑поиск через DuckDuckGo — текст, новости, изображения, видео"
sidebar_label: "Duckduckgo Search"
description: "Бесплатный веб‑поиск через DuckDuckGo — текст, новости, изображения, видео"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Поиск DuckDuckGo

Бесплатный веб‑поиск через DuckDuckGo — текст, новости, изображения, видео. API‑ключ не требуется. Предпочитай CLI `ddgs`, если он установлен; используй Python‑библиотеку DDGS только после проверки, что `ddgs` доступен в текущем окружении выполнения.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/research/duckduckgo-search` |
| Path | `optional-skills/research/duckduckgo-search` |
| Version | `1.3.0` |
| Author | gamedevCloudy |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `search`, `duckduckgo`, `web-search`, `free`, `fallback` |
| Related skills | [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда навык вызывается. Это то, что агент видит как инструкции, когда навык активен.
:::

# Поиск DuckDuckGo

Бесплатный веб‑поиск с использованием DuckDuckGo. **API‑ключ не требуется.**

Предпочтительно, когда `web_search` недоступен или непригоден (например, когда `FIRECRAWL_API_KEY` не установлен). Также может использоваться как отдельный путь поиска, когда явно нужны результаты DuckDuckGo.

## Поток обнаружения

Проверь, что действительно доступно, прежде чем выбирать подход:

```bash
# Check CLI availability
command -v ddgs >/dev/null && echo "DDGS_CLI=installed" || echo "DDGS_CLI=missing"
```

Дерево решений:
1. Если установлен CLI `ddgs`, предпочесть `terminal` + `ddgs`
2. Если CLI `ddgs` отсутствует, не предполагать, что `execute_code` может импортировать `ddgs`
3. Если пользователь явно хочет DuckDuckGo, сначала установить `ddgs` в соответствующей среде
4. Иначе перейти к встроенным веб/браузерным инструментам

Важное замечание о среде выполнения:
- `terminal` и `execute_code` — отдельные среды выполнения
- Успешная установка в оболочке не гарантирует, что `execute_code` сможет импортировать `ddgs`
- Никогда не предполагай, что сторонние Python‑пакеты предустановлены внутри `execute_code`

## Установка

Устанавливай `ddgs` только тогда, когда поиск DuckDuckGo действительно нужен и среда выполнения его ещё не предоставляет.

```bash
# Python package + CLI entrypoint
pip install ddgs

# Verify CLI
ddgs --help
```

Если рабочий процесс зависит от импортов Python, убедись, что та же среда может импортировать `ddgs`, прежде чем использовать `from ddgs import DDGS`.

## Метод 1: Поиск через CLI (предпочтительно)

Используй команду `ddgs` через `terminal`, если она существует. Это предпочтительный путь, потому что он не полагается на наличие пакета `ddgs` в песочнице `execute_code`.

```bash
# Text search
ddgs text -q "python async programming" -m 5

# News search
ddgs news -q "artificial intelligence" -m 5

# Image search
ddgs images -q "landscape photography" -m 10

# Video search
ddgs videos -q "python tutorial" -m 5

# With region filter
ddgs text -q "best restaurants" -m 5 -r us-en

# Recent results only (d=day, w=week, m=month, y=year)
ddgs text -q "latest AI news" -m 5 -t w

# JSON output for parsing
ddgs text -q "fastapi tutorial" -m 5 -o json
```

### Флаги CLI

| Флаг | Описание | Пример |
|------|----------|--------|
| `-q` | Запрос — **обязательно** | `-q "search terms"` |
| `-m` | Максимальное количество результатов | `-m 5` |
| `-r` | Регион | `-r us-en` |
| `-t` | Ограничение по времени | `-t w` (неделя) |
| `-s` | Безопасный поиск | `-s off` |
| `-o` | Формат вывода | `-o json` |

## Метод 2: Python API (только после проверки)

Используй класс `DDGS` в `execute_code` или другой среде Python только после подтверждения, что `ddgs` установлен там. Не предполагай, что `execute_code` по умолчанию содержит сторонние пакеты.

Безопасная формулировка:
- «Используй `execute_code` с `ddgs` после установки или проверки пакета, если это необходимо»

Избегай формулировок:
- «`execute_code` включает `ddgs`»
- «Поиск DuckDuckGo работает по умолчанию в `execute_code`»

**Важно:** `max_results` всегда должен передаваться как **именованный аргумент** — позиционное использование вызывает ошибку во всех методах.

### Текстовый поиск

Лучше всего для: общего исследования, компаний, документации.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.text("python async programming", max_results=5):
        print(r["title"])
        print(r["href"])
        print(r.get("body", "")[:200])
        print()
```

Возвращает: `title`, `href`, `body`

### Поиск новостей

Лучше всего для: текущих событий, срочных новостей, последних обновлений.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.news("AI regulation 2026", max_results=5):
        print(r["date"], "-", r["title"])
        print(r.get("source", ""), "|", r["url"])
        print(r.get("body", "")[:200])
        print()
```

Возвращает: `date`, `title`, `body`, `url`, `image`, `source`

### Поиск изображений

Лучше всего для: визуальных справок, изображений продуктов, схем.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.images("semiconductor chip", max_results=5):
        print(r["title"])
        print(r["image"])
        print(r.get("thumbnail", ""))
        print(r.get("source", ""))
        print()
```

Возвращает: `title`, `image`, `thumbnail`, `url`, `height`, `width`, `source`

### Поиск видео

Лучше всего для: учебных материалов, демонстраций, объяснений.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.videos("FastAPI tutorial", max_results=5):
        print(r["title"])
        print(r.get("content", ""))
        print(r.get("duration", ""))
        print(r.get("provider", ""))
        print(r.get("published", ""))
        print()
```

Возвращает: `title`, `content`, `description`, `duration`, `provider`, `published`, `statistics`, `uploader`

### Быстрая справка

| Метод | Когда использовать | Ключевые поля |
|--------|---------------------|----------------|
| `text()` | Общее исследование, компании | title, href, body |
| `news()` | Текущие события, обновления | date, title, source, body, url |
| `images()` | Визуалы, схемы | title, image, thumbnail, url |
| `videos()` | Учебные материалы, демонстрации | title, content, duration, provider |

## Рабочий процесс: поиск → извлечение

DuckDuckGo возвращает заголовки, URL и фрагменты — не полный контент страниц. Чтобы получить полное содержание, сначала выполните поиск, а затем извлеките наиболее релевантный URL с помощью `web_extract`, браузерных инструментов или `curl`.

Пример CLI:

```bash
ddgs text -q "fastapi deployment guide" -m 3 -o json
```

Пример Python, только после подтверждения, что `ddgs` установлен в этой среде:

```python
from ddgs import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text("fastapi deployment guide", max_results=3))
    for r in results:
        print(r["title"], "->", r["href"])
```

Затем извлеки лучший URL с помощью `web_extract` или другого инструмента получения контента.

## Ограничения

- **Ограничение частоты запросов**: DuckDuckGo может замедлять ответы после большого количества быстрых запросов. При необходимости добавляй небольшую задержку между поисками.
- **Отсутствие извлечения контента**: `ddgs` возвращает только фрагменты, а не полный текст страниц. Используй `web_extract`, браузерные инструменты или `curl` для получения полной статьи/страницы.
- **Качество результатов**: В целом хорошее, но менее настраиваемое, чем поиск Firecrawl.
- **Доступность**: DuckDuckGo может блокировать запросы с некоторых облачных IP. Если поиск возвращает пустой результат, попробуй другие ключевые слова или подожди несколько секунд.
- **Вариативность полей**: Возвращаемые поля могут различаться между результатами или версиями `ddgs`. Используй `.get()` для опциональных полей, чтобы избежать `KeyError`.
- **Разные среды выполнения**: Успешная установка `ddgs` в терминале не автоматически означает, что `execute_code` сможет его импортировать.

## Устранение неполадок

| Проблема | Возможная причина | Что делать |
|----------|-------------------|------------|
| `ddgs: command not found` | CLI не установлен в среде оболочки | Установи `ddgs` или используй встроенные веб/браузерные инструменты |
| `ModuleNotFoundError: No module named 'ddgs'` | В Python‑среде пакет не установлен | Не используй Python‑DDGS, пока эта среда не будет подготовлена |
| Поиск ничего не возвращает | Временное ограничение частоты запросов или плохой запрос | Подожди несколько секунд, повтори запрос или уточни запрос |
| CLI работает, а импорт в `execute_code` падает | Терминал и `execute_code` — разные среды | Продолжай использовать CLI или отдельно подготовь Python‑среду |

## Подводные камни

- **`max_results` только как именованный аргумент**: `ddgs.text("query", 5)` вызывает ошибку. Используй `ddgs.text("query", max_results=5)`.
- **Не предполагай наличие CLI**: Проверь `command -v ddgs` перед использованием.
- **Не предполагай, что `execute_code` может импортировать `ddgs`**: `from ddgs import DDGS` может завершиться `ModuleNotFoundError`, если эта среда не подготовлена отдельно.
- **Имя пакета**: Пакет называется `ddgs` (ранее `duckduckgo-search`). Устанавливай через `pip install ddgs`.
- **Не путай `-q` и `-m`** (CLI): `-q` — запрос, `-m` — количество максимальных результатов.
- **Пустые результаты**: Если `ddgs` ничего не возвращает, вероятно, достигнут лимит запросов. Подожди несколько секунд и повтори.

## Проверено на

Проверенные примеры соответствуют семантике `ddgs==9.11.2`. Руководство навыка теперь рассматривает доступность CLI и возможность импорта Python‑пакета как отдельные вопросы, чтобы задокументированный рабочий процесс соответствовал реальному поведению среды выполнения.