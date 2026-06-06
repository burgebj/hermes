---
title: "Скраплинг"
sidebar_label: "Scrapling"
description: "Веб‑скрейпинг с Scrapling — HTTP‑запросы, скрытая автоматизация браузера, обход Cloudflare и паукообразный обход через CLI и Python"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Scrapling

Web scraping with Scrapling — HTTP‑запросы, скрытая автоматизация браузера, обход Cloudflare и обход паука через CLI и Python.

## Метаданные навыка

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

## Справочник: полный SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Scrapling

[Scrapling](https://github.com/D4Vinci/Scrapling) — это фреймворк для веб‑скрапинга с обходом анти‑ботов, скрытой автоматизацией браузера и пауком. Он предоставляет три стратегии получения (HTTP, динамический JS, скрытый/Cloudflare) и полноценный CLI.

**Этот навык предназначен только для образовательных и исследовательских целей.** Пользователи обязаны соблюдать местные/международные законы о скрапинге данных и уважать условия обслуживания сайтов.

## Когда использовать

- Скрапинг статических HTML‑страниц (быстрее, чем инструменты браузера)
- Скрапинг страниц, рендерящихся JS и требующих реального браузера
- Обход Cloudflare Turnstile или детекции ботов
- Обход нескольких страниц с помощью паука
- Когда встроенный инструмент `web_extract` не возвращает нужные данные

## Установка

```bash
pip install "scrapling[all]"
scrapling install
```

Минимальная установка (только HTTP, без браузера):
```bash
pip install scrapling
```

Только автоматизация браузера:
```bash
pip install "scrapling[fetchers]"
scrapling install
```

## Быстрый справочник

| Approach | Class | Use When |
|----------|-------|----------|
| HTTP | `Fetcher` / `FetcherSession` | Статические страницы, API, быстрые массовые запросы |
| Dynamic | `DynamicFetcher` / `DynamicSession` | Контент, рендерящийся JS, SPA |
| Stealth | `StealthyFetcher` / `StealthySession` | Cloudflare, сайты с защитой от ботов |
| Spider | `Spider` | Обход нескольких страниц с переходом по ссылкам |

## Использование CLI

### Извлечение статической страницы

```bash
scrapling extract get 'https://example.com' output.md
```

С CSS‑селектором и имитацией браузера:

```bash
scrapling extract get 'https://example.com' output.md \
  --css-selector '.content' \
  --impersonate 'chrome'
```

### Извлечение страницы, рендерящейся JS

```bash
scrapling extract fetch 'https://example.com' output.md \
  --css-selector '.dynamic-content' \
  --disable-resources \
  --network-idle
```

### Извлечение страницы, защищённой Cloudflare

```bash
scrapling extract stealthy-fetch 'https://protected-site.com' output.html \
  --solve-cloudflare \
  --block-webrtc \
  --hide-canvas
```

### POST‑запрос

```bash
scrapling extract post 'https://example.com/api' output.json \
  --json '{"query": "search term"}'
```

### Форматы вывода

Формат вывода определяется расширением файла:
- `.html` — сырой HTML
- `.md` — конвертировано в Markdown
- `.txt` — обычный текст
- `.json` / `.jsonl` — JSON

## Python: HTTP‑скрапинг

### Один запрос

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text').getall()
for q in quotes:
    print(q)
```

### Сессия (постоянные куки)

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

### С прокси

```python
page = Fetcher.get('https://example.com', proxy='http://user:pass@proxy:8080')
```

## Python: Динамические страницы (JS‑рендеринг)

Для страниц, требующих выполнения JavaScript (SPA, лениво загружаемый контент):

```python
from scrapling.fetchers import DynamicFetcher

page = DynamicFetcher.fetch('https://example.com', headless=True)
data = page.css('.js-loaded-content::text').getall()
```

### Ожидание конкретного элемента

```python
page = DynamicFetcher.fetch(
    'https://example.com',
    wait_selector=('.results', 'visible'),
    network_idle=True,
)
```

### Отключение ресурсов для ускорения

Блокирует шрифты, изображения, медиа, стили (~25 % быстрее):

```python
from scrapling.fetchers import DynamicSession

with DynamicSession(headless=True, disable_resources=True, network_idle=True) as session:
    page = session.fetch('https://example.com')
    items = page.css('.item::text').getall()
```

### Пользовательская автоматизация страницы

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

## Python: Скрытый режим (обход анти‑ботов)

Для сайтов, защищённых Cloudflare или сильно отпечатанных:

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

### Скрытая сессия

```python
from scrapling.fetchers import StealthySession

with StealthySession(headless=True, solve_cloudflare=True) as session:
    page1 = session.fetch('https://protected-site.com/page1')
    page2 = session.fetch('https://protected-site.com/page2')
```

## Выбор элементов

Все fetcher‑ы возвращают объект `Selector` со следующими методами:

### CSS‑селекторы

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

### Методы поиска

```python
page.find_all('div', class_='quote')       # By tag + attribute
page.find_by_text('Read more', tag='a')    # By text content
page.find_by_regex(r'\$\d+\.\d{2}')       # By regex pattern
```

### Похожие элементы

Поиск элементов со схожей структурой (полезно для списков товаров и т.п.):

```python
first_product = page.css('.product')[0]
all_similar = first_product.find_similar()
```

### Навигация

```python
el = page.css('.target')[0]
el.parent                # Parent element
el.children              # Child elements
el.next_sibling          # Next sibling
el.prev_sibling          # Previous sibling
```

## Python: Фреймворк паука

Для обхода нескольких страниц с переходом по ссылкам:

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

### Мульти‑сессия паука

Маршрутизация запросов к разным типам fetcher‑ов:

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

### Пауза/возобновление обхода

```python
spider = QuotesSpider(crawldir="./crawl_checkpoint")
spider.start()  # Ctrl+C to pause, re-run to resume from checkpoint
```

## Подводные камни

- **Требуется установка браузера**: выполните `scrapling install` после установки pip — без этого `DynamicFetcher` и `StealthyFetcher` не будут работать
- **Таймауты**: таймаут у `DynamicFetcher`/`StealthyFetcher` задаётся в **миллисекундах** (по умолчанию 30000), у `Fetcher` — в **секундах**
- **Обход Cloudflare**: `solve_cloudflare=True` добавляет 5–15 секунд к времени получения — включайте только при необходимости
- **Использование ресурсов**: `StealthyFetcher` запускает реальный браузер — ограничьте одновременное использование
- **Юридические вопросы**: всегда проверяй `robots.txt` и условия обслуживания сайта перед скрапингом. Эта библиотека предназначена для образовательных и исследовательских целей
- **Версия Python**: требуется Python 3.10+