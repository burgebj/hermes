---
title: "Duckduckgo Search — Безкоштовний веб‑пошук через DuckDuckGo — текст, новини, зображення, відео"
sidebar_label: "Duckduckgo Search"
description: "Безкоштовний веб-пошук через DuckDuckGo — текст, новини, зображення, відео"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Duckduckgo Search

Безкоштовний веб‑пошук через DuckDuckGo — текст, новини, зображення, відео. Ключ API не потрібен. Якщо встановлений, надавай перевагу CLI `ddgs`; бібліотеку Python DDGS використовуйте лише після перевірки, що `ddgs` доступний у поточному середовищі виконання.

## Метадані навички

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

## Reference: full SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує під час її активації. Це інструкції, які бачить агент, коли навичка активна.
:::

# DuckDuckGo Search

Безкоштовний веб‑пошук за допомогою DuckDuckGo. **Ключ API не потрібен.**

Надається перевага, коли `web_search` недоступний або невідповідний (наприклад, коли не встановлено `FIRECRAWL_API_KEY`). Також може використовуватись як окремий шлях пошуку, коли потрібні саме результати DuckDuckGo.

## Detection Flow

Перевіряй, що саме доступно, перед вибором підходу:

```bash
# Check CLI availability
command -v ddgs >/dev/null && echo "DDGS_CLI=installed" || echo "DDGS_CLI=missing"
```

Дерево рішень:
1. Якщо встановлений CLI `ddgs`, надавай перевагу `terminal` + `ddgs`
2. Якщо CLI `ddgs` відсутній, не припускай, що `execute_code` може імпортувати `ddgs`
3. Якщо користувач явно хоче DuckDuckGo, спочатку встанови `ddgs` у відповідному середовищі
4. Інакше переходь до вбудованих інструментів веб/браузера

Важлива примітка про середовища виконання:
- `terminal` і `execute_code` – це різні середовища
- Успішна установка в оболонці не гарантує, що `execute_code` зможе імпортувати `ddgs`
- Ніколи не припускай, що сторонні Python‑пакети попередньо встановлені в `execute_code`

## Installation

Встановлюй `ddgs` лише тоді, коли пошук DuckDuckGo потрібен саме зараз і середовище його ще не має.

```bash
# Python package + CLI entrypoint
pip install ddgs

# Verify CLI
ddgs --help
```

Якщо робочий процес залежить від імпортів Python, переконайся, що саме це середовище може імпортувати `ddgs`, перш ніж використовувати `from ddgs import DDGS`.

## Method 1: CLI Search (Preferred)

Використовуй команду `ddgs` через `terminal`, якщо вона доступна. Це пріоритетний шлях, оскільки він не вимагає, щоб у пісочниці `execute_code` був встановлений пакет `ddgs`.

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

### CLI Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-q` | Запит — **обов’язковий** | `-q "search terms"` |
| `-m` | Максимальна кількість результатів | `-m 5` |
| `-r` | Регіон | `-r us-en` |
| `-t` | Обмеження за часом | `-t w` (тиждень) |
| `-s` | Безпечний пошук | `-s off` |
| `-o` | Формат виводу | `-o json` |

## Method 2: Python API (Only After Verification)

Використовуй клас `DDGS` у `execute_code` або іншому середовищі Python лише після підтвердження, що `ddgs` встановлений там. Не припускай, що `execute_code` містить сторонні пакети за замовчуванням.

Безпечна формулювання:
- “Використовуй `execute_code` з `ddgs` після встановлення або перевірки пакету, якщо це потрібно”

Уникай формулювань:
- “`execute_code` включає `ddgs`”
- “Пошук DuckDuckGo працює за замовчуванням у `execute_code`”

**Важливо:** `max_results` завжди передається як **іменований аргумент** — позиційне використання викликає помилку у всіх методах.

### Text Search

Найкраще для: загальних досліджень, компаній, документації.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.text("python async programming", max_results=5):
        print(r["title"])
        print(r["href"])
        print(r.get("body", "")[:200])
        print()
```

Повертає: `title`, `href`, `body`

### News Search

Найкраще для: поточних подій, новин, останніх оновлень.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.news("AI regulation 2026", max_results=5):
        print(r["date"], "-", r["title"])
        print(r.get("source", ""), "|", r["url"])
        print(r.get("body", "")[:200])
        print()
```

Повертає: `date`, `title`, `body`, `url`, `image`, `source`

### Image Search

Найкраще для: візуальних довідок, зображень продуктів, діаграм.

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

Повертає: `title`, `image`, `thumbnail`, `url`, `height`, `width`, `source`

### Video Search

Найкраще для: навчальних матеріалів, демонстрацій, пояснювальних відео.

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

Повертає: `title`, `content`, `description`, `duration`, `provider`, `published`, `statistics`, `uploader`

### Quick Reference

| Method | Use When | Key Fields |
|--------|----------|------------|
| `text()` | Загальні дослідження, компанії | title, href, body |
| `news()` | Поточні події, оновлення | date, title, source, body, url |
| `images()` | Візуальні матеріали, діаграми | title, image, thumbnail, url |
| `videos()` | Навчальні матеріали, демонстрації | title, content, duration, provider |

## Workflow: Search then Extract

DuckDuckGo повертає лише назви, URL та уривки — не повний вміст сторінки. Щоб отримати повний текст, спочатку шукай, а потім витягни найбільш релевантний URL за допомогою `web_extract`, інструментів браузера або `curl`.

CLI‑приклад:

```bash
ddgs text -q "fastapi deployment guide" -m 3 -o json
```

Python‑приклад, лише після підтвердження, що `ddgs` встановлений у цьому середовищі:

```python
from ddgs import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text("fastapi deployment guide", max_results=3))
    for r in results:
        print(r["title"], "->", r["href"])
```

Потім витягни найкращий URL за допомогою `web_extract` або іншого інструменту отримання вмісту.

## Limitations

- **Rate limiting**: DuckDuckGo може обмежувати швидкість після великої кількості швидких запитів. За потреби додавай коротку затримку між пошуками.
- **Відсутність витягнення вмісту**: `ddgs` повертає лише уривки, а не повний текст сторінки. Використовуй `web_extract`, інструменти браузера або `curl` для отримання повної статті/сторінки.
- **Якість результатів**: Зазвичай хороша, але менш налаштовувана, ніж пошук Firecrawl.
- **Доступність**: DuckDuckGo може блокувати запити з деяких хмарних IP. Якщо результати порожні, спробуй інші ключові слова або зачекай кілька секунд.
- **Змінність полів**: Повернуті поля можуть відрізнятись між результатами або версіями `ddgs`. Використовуй `.get()` для необов’язкових полів, щоб уникнути `KeyError`.
- **Окремі середовища**: Успішна установка `ddgs` у терміналі не означає, що `execute_code` зможе його імпортувати.

## Troubleshooting

| Problem | Likely Cause | What To Do |
|---------|--------------|------------|
| `ddgs: command not found` | CLI не встановлений у середовищі оболонки | Встанови `ddgs` або використай вбудовані інструменти веб/браузера |
| `ModuleNotFoundError: No module named 'ddgs'` | У Python‑середовищі пакет не встановлений | Не використовуйте Python‑DDGS, доки це середовище не підготовлено |
| Search returns nothing | Тимчасове обмеження швидкості або поганий запит | Зачекай кілька секунд, повтори спробу або скоригуй запит |
| CLI works but `execute_code` import fails | Терминал і `execute_code` – різні середовища | Продовжуй використовувати CLI або окремо підготуй Python‑середовище |

## Pitfalls

- **`max_results` лише іменований**: `ddgs.text("query", 5)` викликає помилку. Використовуй `ddgs.text("query", max_results=5)`.
- **Не припускай наявність CLI**: Перевіряй `command -v ddgs` перед використанням.
- **Не припускай, що `execute_code` може імпортувати `ddgs`**: `from ddgs import DDGS` може завершитись `ModuleNotFoundError`, якщо це середовище не підготовлене.
- **Назва пакету**: Пакет називається `ddgs` (раніше `duckduckgo-search`). Встановлюй через `pip install ddgs`.
- **Не плутай `-q` і `-m`** (CLI): `-q` — запит, `-m` — кількість результатів.
- **Порожні результати**: Якщо `ddgs` нічого не повертає, можливо, діє обмеження швидкості. Зачекай кілька секунд і спробуй знову.

## Validated With

Перевірено на прикладах з `ddgs==9.11.2`. Тепер рекомендації навички розрізняють доступність CLI та можливість імпорту Python‑пакету, тому задокументований робочий процес відповідає реальній поведінці середовищ.