---
title: "Arxiv — Поиск статей arXiv по ключевому слову, автору, категории или ID"
sidebar_label: "Arxiv"
description: "Поиск статей arXiv по ключевому слову, автору, категории или ID"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Arxiv

Поиск статей arXiv по ключевому слову, автору, категории или ID.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/arxiv` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Research`, `Arxiv`, `Papers`, `Academic`, `Science`, `API` |
| Related skills | [`ocr-and-documents`](/docs/user-guide/skills/bundled/productivity/productivity-ocr-and-documents) |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# arXiv Research

Поиск и получение академических статей из arXiv через их бесплатный REST API. Без API‑ключа, без зависимостей — только curl.

## Быстрая справка

| Действие | Команда |
|--------|---------|
| Поиск статей | `curl "https://export.arxiv.org/api/query?search_query=all:QUERY&max_results=5"` |
| Получить конкретную статью | `curl "https://export.arxiv.org/api/query?id_list=2402.03300"` |
| Читать аннотацию (веб) | `web_extract(urls=["https://arxiv.org/abs/2402.03300"])` |
| Читать полную статью (PDF) | `web_extract(urls=["https://arxiv.org/pdf/2402.03300"])` |

## Поиск статей

API возвращает Atom XML. Разбирай с помощью `grep`/`sed` или передавай в `python3` для чистого вывода.

### Базовый поиск

```bash
curl -s "https://export.arxiv.org/api/query?search_query=all:GRPO+reinforcement+learning&max_results=5"
```

### Чистый вывод (парсинг XML в читаемый формат)

```bash
curl -s "https://export.arxiv.org/api/query?search_query=all:GRPO+reinforcement+learning&max_results=5&sortBy=submittedDate&sortOrder=descending" | python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom'}
root = ET.parse(sys.stdin).getroot()
for i, entry in enumerate(root.findall('a:entry', ns)):
    title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
    arxiv_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
    published = entry.find('a:published', ns).text[:10]
    authors = ', '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns))
    summary = entry.find('a:summary', ns).text.strip()[:200]
    cats = ', '.join(c.get('term') for c in entry.findall('a:category', ns))
    print(f'{i+1}. [{arxiv_id}] {title}')
    print(f'   Authors: {authors}')
    print(f'   Published: {published} | Categories: {cats}')
    print(f'   Abstract: {summary}...')
    print(f'   PDF: https://arxiv.org/pdf/{arxiv_id}')
    print()
"
```

## Синтаксис поискового запроса

| Префикс | Что ищет | Пример |
|--------|----------|---------|
| `all:` | Все поля | `all:transformer+attention` |
| `ti:` | Заголовок | `ti:large+language+models` |
| `au:` | Автор | `au:vaswani` |
| `abs:` | Аннотация | `abs:reinforcement+learning` |
| `cat:` | Категория | `cat:cs.AI` |
| `co:` | Комментарий | `co:accepted+NeurIPS` |

### Логические операторы

```
# AND (default when using +)
search_query=all:transformer+attention

# OR
search_query=all:GPT+OR+all:BERT

# AND NOT
search_query=all:language+model+ANDNOT+all:vision

# Exact phrase
search_query=ti:"chain+of+thought"

# Combined
search_query=au:hinton+AND+cat:cs.LG
```

## Сортировка и пагинация

| Параметр | Опции |
|-----------|---------|
| `sortBy` | `relevance`, `lastUpdatedDate`, `submittedDate` |
| `sortOrder` | `ascending`, `descending` |
| `start` | Смещение результата (нумерация с 0) |
| `max_results` | Количество результатов (по умолчанию 10, максимум 30000) |

```bash
# Latest 10 papers in cs.AI
curl -s "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10"
```

## Получение конкретных статей

```bash
# By arXiv ID
curl -s "https://export.arxiv.org/api/query?id_list=2402.03300"

# Multiple papers
curl -s "https://export.arxiv.org/api/query?id_list=2402.03300,2401.12345,2403.00001"
```

## Генерация BibTeX

После получения метаданных статьи сгенерировать запись BibTeX:

&#123;% raw %&#125;
```bash
curl -s "https://export.arxiv.org/api/query?id_list=1706.03762" | python3 -c "
import sys, xml.etree.ElementTree as ET
ns = {'a': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
root = ET.parse(sys.stdin).getroot()
entry = root.find('a:entry', ns)
if entry is None: sys.exit('Paper not found')
title = entry.find('a:title', ns).text.strip().replace('\n', ' ')
authors = ' and '.join(a.find('a:name', ns).text for a in entry.findall('a:author', ns))
year = entry.find('a:published', ns).text[:4]
raw_id = entry.find('a:id', ns).text.strip().split('/abs/')[-1]
cat = entry.find('arxiv:primary_category', ns)
primary = cat.get('term') if cat is not None else 'cs.LG'
last_name = entry.find('a:author', ns).find('a:name', ns).text.split()[-1]
print(f'@article{{{last_name}{year}_{raw_id.replace(\".\", \"\")},')
print(f'  title     = {{{title}}},')
print(f'  author    = {{{authors}}},')
print(f'  year      = {{{year}}},')
print(f'  eprint    = {{{raw_id}}},')
print(f'  archivePrefix = {{arXiv}},')
print(f'  primaryClass  = {{{primary}}},')
print(f'  url       = {{https://arxiv.org/abs/{raw_id}}}')
print('}')
"
```
&#123;% endraw %&#125;

## Чтение содержимого статьи

После нахождения статьи прочитай её:

```
# Abstract page (fast, metadata + abstract)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper (PDF → markdown via Firecrawl)
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
```

Для локальной обработки PDF смотри навык `ocr-and-documents`.

## Часто используемые категории

| Категория | Область |
|----------|-------|
| `cs.AI` | Artificial Intelligence |
| `cs.CL` | Computation and Language (NLP) |
| `cs.CV` | Computer Vision |
| `cs.LG` | Machine Learning |
| `cs.CR` | Cryptography and Security |
| `stat.ML` | Machine Learning (Statistics) |
| `math.OC` | Optimization and Control |
| `physics.comp-ph` | Computational Physics |

Полный список: https://arxiv.org/category_taxonomy

## Вспомогательный скрипт

Скрипт `scripts/search_arxiv.py` обрабатывает XML и предоставляет чистый вывод:

```bash
python scripts/search_arxiv.py "GRPO reinforcement learning"
python scripts/search_arxiv.py "transformer attention" --max 10 --sort date
python scripts/search_arxiv.py --author "Yann LeCun" --max 5
python scripts/search_arxiv.py --category cs.AI --sort date
python scripts/search_arxiv.py --id 2402.03300
python scripts/search_arxiv.py --id 2402.03300,2401.12345
```

Без зависимостей — использует только стандартную библиотеку Python.

---

## Semantic Scholar (цитаты, связанные статьи, профили авторов)

arXiv не предоставляет данные о цитатах или рекомендациях. Для этого используй **Semantic Scholar API** — бесплатно, без ключа для базового использования (1 запрос/сек), возвращает JSON.

### Получить детали статьи + цитаты

```bash
# By arXiv ID
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300?fields=title,authors,citationCount,referenceCount,influentialCitationCount,year,abstract" | python3 -m json.tool

# By Semantic Scholar paper ID or DOI
curl -s "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1234/example?fields=title,citationCount"
```

### Получить цитаты ДЛЯ статьи (кто её цитировал)

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300/citations?fields=title,authors,year,citationCount&limit=10" | python3 -m json.tool
```

### Получить ссылки ИЗ статьи (что она цитирует)

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300/references?fields=title,authors,year,citationCount&limit=10" | python3 -m json.tool
```

### Поиск статей (альтернатива поиску arXiv, возвращает JSON)

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=GRPO+reinforcement+learning&limit=5&fields=title,authors,year,citationCount,externalIds" | python3 -m json.tool
```

### Получить рекомендации статей

```bash
curl -s -X POST "https://api.semanticscholar.org/recommendations/v1/papers/" \
  -H "Content-Type: application/json" \
  -d '{"positivePaperIds": ["arXiv:2402.03300"], "negativePaperIds": []}' | python3 -m json.tool
```

### Профиль автора

```bash
curl -s "https://api.semanticscholar.org/graph/v1/author/search?query=Yann+LeCun&fields=name,hIndex,citationCount,paperCount" | python3 -m json.tool
```

### Полезные поля Semantic Scholar

`title`, `authors`, `year`, `abstract`, `citationCount`, `referenceCount`, `influentialCitationCount`, `isOpenAccess`, `openAccessPdf`, `fieldsOfStudy`, `publicationVenue`, `externalIds` (содержит arXiv ID, DOI и т.д.)

---

## Полный исследовательский workflow

1. **Discover**: `python scripts/search_arxiv.py "your topic" --sort date --max 10`
2. **Assess impact**: `curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:ID?fields=citationCount,influentialCitationCount"`
3. **Read abstract**: `web_extract(urls=["https://arxiv.org/abs/ID"])`
4. **Read full paper**: `web_extract(urls=["https://arxiv.org/pdf/ID"])`
5. **Find related work**: `curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:ID/references?fields=title,citationCount&limit=20"`
6. **Get recommendations**: POST к endpoint рекомендаций Semantic Scholar
7. **Track authors**: `curl -s "https://api.semanticscholar.org/graph/v1/author/search?query=NAME"`

## Ограничения по частоте запросов

| API | Ограничение | Авторизация |
|-----|------------|-------------|
| arXiv | ~1 запрос / 3 секунды | Не требуется |
| Semantic Scholar | 1 запрос / секунду | Не требуется (100 запросов/сек при наличии API‑ключа) |

## Примечания

- arXiv возвращает Atom XML — используй вспомогательный скрипт или фрагмент парсинга для чистого вывода
- Semantic Scholar возвращает JSON — передавай через `python3 -m json.tool` для читаемости
- ID arXiv: старый формат (`hep-th/0601001`) vs новый (`2402.03300`)
- PDF: `https://arxiv.org/pdf/{id}` — аннотация: `https://arxiv.org/abs/{id}`
- HTML (если доступно): `https://arxiv.org/html/{id}`
- Для локальной обработки PDF смотри навык `ocr-and-documents`

## Версионирование ID

- `arxiv.org/abs/1706.03762` всегда указывает на **последнюю** версию
- `arxiv.org/abs/1706.03762v1` указывает на **конкретную** неизменяемую версию
- При генерации цитат сохраняй суффикс версии, которую действительно читал, чтобы избежать дрейфа цитат (поздняя версия может существенно менять содержание)
- Поле API `<id>` возвращает URL с версией (например, `http://arxiv.org/abs/1706.03762v7`)

## Отозванные статьи

Статьи могут быть отозваны после публикации. В этом случае:
- Поле `<summary>` содержит уведомление об отзыве (ищи «withdrawn» или «retracted»)
- Метаданные могут быть неполными
- Всегда проверяй `<summary>` перед тем, как считать результат действительной статьей