---
title: "Скраплінг"
sidebar_label: "Scrapling"
description: "Веб-скрейпінг за допомогою Scrapling — HTTP‑запити, автоматизація stealth‑браузера, обходження Cloudflare та сканування павуків через CLI і Python"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Scrapling

Web scraping with Scrapling — HTTP‑запити, stealth‑автоматизація браузера, обходи Cloudflare та сканування пауками через CLI і Python.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/research/scrapling` |
| Path | `optional-skills/research/scrapling` |
| Version | `1.0.0` |
| Author | FEUAZUR |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Web Scraping`, `Browser`, `Cloudflare`, `Stealth`, `Crawling`, `Spider` |
| Related skills | [`duckduckgo-search`](/docs/user-guide/skills/optional/research/research-duckduckgo-search), [`domain-intel`](/docs/user-guide/skills/optional/research/research-domain-intel) |

## Довідка: повний SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Scrapling

[Scrapling](https://github.com/D4Vinci/Scrapling) — це фреймворк для веб‑скрапінгу з обходом анти‑ботів, stealth‑автоматизацією браузера та підтримкою пауків. Він пропонує три стратегії отримання даних (HTTP, динамічний JS, stealth/Cloudflare) і повний CLI.

**Ця навичка призначена лише для освітніх та дослідницьких цілей.** Користувачі повинні дотримуватись місцевих та міжнародних законів про скрапінг даних і поважати умови використання сайтів.

## Коли використовувати

- Скрепінг статичних HTML‑сторінок (швидше, ніж інструменти браузера)
- Скрепінг сторінок, що рендеряться JavaScript‑ом і потребують реального браузера
- Обхід Cloudflare Turnstile або інших систем виявлення ботів
- Сканування кількох сторінок за допомогою паука
- Коли вбудований інструмент `web_extract` не повертає потрібних даних

## Встановлення

```bash
pip install "scrapling[all]"
scrapling install
```

Мінімальна установка (лише HTTP, без браузера):
```bash
pip install scrapling
```

Тільки автоматизація браузера:
```bash
pip install "scrapling[fetchers]"
scrapling install
```

## Швидка довідка

| Підхід | Клас | Коли застосовувати |
|----------|-------|-------------------|
| HTTP | `Fetcher` / `FetcherSession` | Статичні сторінки, API, швидкі масові запити |
| Dynamic | `DynamicFetcher` / `DynamicSession` | Контент, що рендериться JS, SPA |
| Stealth | `StealthyFetcher` / `StealthySession` | Cloudflare, сайти з захистом від ботів |
| Spider | `Spider` | Сканування багатьох сторінок з переходом за посиланнями |

## Використання CLI

### Витяг статичної сторінки

```bash
scrapling extract get 'https://example.com' output.md
```

З CSS‑селектором та імітацією браузера:

```bash
scrapling extract get 'https://example.com' output.md \
  --css-selector '.content' \
  --impersonate 'chrome'
```

### Витяг JS‑рендерованої сторінки

```bash
scrapling extract fetch 'https://example.com' output.md \
  --css-selector '.dynamic-content' \
  --disable-resources \
  --network-idle
```

### Витяг сторінки, захищеної Cloudflare

```bash
scrapling extract stealthy-fetch 'https://protected-site.com' output.html \
  --solve-cloudflare \
  --block-webrtc \
  --hide-canvas
```

### POST‑запит

```bash
scrapling extract post 'https://example.com/api' output.json \
  --json '{"query": "search term"}'
```

### Формати виводу

Формат виводу визначається розширенням файлу:
- `.html` — сирий HTML
- `.md` — конвертовано в Markdown
- `.txt` — простий текст
- `.json` / `.jsonl` — JSON

## Python: HTTP‑скрапінг

### Одиночний запит

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text').getall()
for q in quotes:
    print(q)
```

### Сесія (постійні куки)

```python
from scrapling.fetchers import FetcherSession

with FetcherSession(impersonate='chrome') as session:
    page = session.get('https://example.com/', stealthy_headers=True)
    links = page.css('a::attr(href)').getall()
    for link in links[:5]:
        sub = session.get(link)
        print(sub.css('h1::text').get())
```

### POST / PUT / DELETE

```python
page = Fetcher.post('https://api.example.com/data', json={"key": "value"})
page = Fetcher.put('https://api.example.com/item/1', data={"name": "updated"})
page = Fetcher.delete('https://api.example.com/item/1')
```

### З проксі

```python
page = Fetcher.get('https://example.com', proxy='http://user:pass@proxy:8080')
```

## Python: Динамічні сторінки (JS‑рендеринг)

Для сторінок, які потребують виконання JavaScript (SPA, lazy‑loaded контент):

```python
from scrapling.fetchers import DynamicFetcher

page = DynamicFetcher.fetch('https://example.com', headless=True)
data = page.css('.js-loaded-content::text').getall()
```

### Очікування конкретного елементу

```python
page = DynamicFetcher.fetch(
    'https://example.com',
    wait_selector=('.results', 'visible'),
    network_idle=True,
)
```

### Вимкнення ресурсів для підвищення швидкості

Блокує шрифти, зображення, медіа, таблиці стилів (~25 % швидше):

```python
from scrapling.fetchers import DynamicSession

with DynamicSession(headless=True, disable_resources=True, network_idle=True) as session:
    page = session.fetch('https://example.com')
    items = page.css('.item::text').getall()
```

### Кастомна автоматизація сторінки

```python
from playwright.sync_api import Page
from scrapling.fetchers import DynamicFetcher

def scroll_and_click(page: Page):
    page.mouse.wheel(0, 3000)
    page.wait_for_timeout(1000)
    page.click('button.load-more')
    page.wait_for_selector('.extra-results')

page = DynamicFetcher.fetch('https://example.com', page_action=scroll_and_click)
results = page.css('.extra-results .item::text').getall()
```

## Python: Режим Stealth (обхід анти‑ботів)

Для сайтів, захищених Cloudflare або сильно ідентифікованих:

```python
from scrapling.fetchers import StealthyFetcher

page = StealthyFetcher.fetch(
    'https://protected-site.com',
    headless=True,
    solve_cloudflare=True,
    block_webrtc=True,
    hide_canvas=True,
)
content = page.css('.protected-content::text').getall()
```

### Stealth‑сесія

```python
from scrapling.fetchers import StealthySession

with StealthySession(headless=True, solve_cloudflare=True) as session:
    page1 = session.fetch('https://protected-site.com/page1')
    page2 = session.fetch('https://protected-site.com/page2')
```

## Вибір елементів

Усі fetcher‑и повертають об’єкт `Selector` з такими методами:

### CSS‑селектори

```python
page.css('h1::text').get()              # First h1 text
page.css('a::attr(href)').getall()      # All link hrefs
page.css('.quote .text::text').getall() # Nested selection
```

### XPath

```python
page.xpath('//div[@class="content"]/text()').getall()
page.xpath('//a/@href').getall()
```

### Методи пошуку

```python
page.find_all('div', class_='quote')       # By tag + attribute
page.find_by_text('Read more', tag='a')    # By text content
page.find_by_regex(r'\$\d+\.\d{2}')       # By regex pattern
```

### Подібні елементи

Пошук елементів зі схожою структурою (корисно для списків товарів тощо):

```python
first_product = page.css('.product')[0]
all_similar = first_product.find_similar()
```

### Навігація

```python
el = page.css('.target')[0]
el.parent                # Parent element
el.children              # Child elements
el.next_sibling          # Next sibling
el.prev_sibling          # Previous sibling
```

## Python: Spider‑фреймворк

Для багатосторінкового сканування з переходом за посиланнями:

```python
from scrapling.spiders import Spider, Request, Response

class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 10
    download_delay = 1

    async def parse(self, response: Response):
        for quote in response.css('.quote'):
            yield {
                "text": quote.css('.text::text').get(),
                "author": quote.css('.author::text').get(),
                "tags": quote.css('.tag::text').getall(),
            }

        next_page = response.css('.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page)

result = QuotesSpider().start()
print(f"Scraped {len(result.items)} quotes")
result.items.to_json("quotes.json")
```

### Spider з кількома сесіями

Маршрутизація запитів до різних типів fetcher‑ів:

```python
from scrapling.fetchers import FetcherSession, AsyncStealthySession

class SmartSpider(Spider):
    name = "smart"
    start_urls = ["https://example.com/"]

    def configure_sessions(self, manager):
        manager.add("fast", FetcherSession(impersonate="chrome"))
        manager.add("stealth", AsyncStealthySession(headless=True), lazy=True)

    async def parse(self, response: Response):
        for link in response.css('a::attr(href)').getall():
            if "protected" in link:
                yield Request(link, sid="stealth")
            else:
                yield Request(link, sid="fast", callback=self.parse)
```

### Пауза/відновлення сканування

```python
spider = QuotesSpider(crawldir="./crawl_checkpoint")
spider.start()  # Ctrl+C to pause, re-run to resume from checkpoint
```

## Підводні камені

- **Потрібна установка браузера**: після `pip install` запусти `scrapling install` — без цього `DynamicFetcher` і `StealthyFetcher` не працюватимуть.
- **Тайм‑ауты**: у `DynamicFetcher`/`StealthyFetcher` тайм‑аут вимірюється в **мілісекундах** (за замовчуванням 30000), у `Fetcher` — в **секундах**.
- **Обхід Cloudflare**: `solve_cloudflare=True` додає 5‑15 секунд до часу запиту — вмикай лише за потреби.
- **Використання ресурсів**: `StealthyFetcher` запускає реальний браузер — обмежуй кількість одночасних запитів.
- **Юридичний аспект**: завжди перевіряй `robots.txt` та умови використання сайту перед скрапінгом. Ця бібліотека призначена лише для освітніх та дослідницьких цілей.
- **Версія Python**: потрібна Python 3.10+.