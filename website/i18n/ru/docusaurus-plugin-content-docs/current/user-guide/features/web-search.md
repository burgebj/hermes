---
title: веб-поиск & извлечение
description: Выполняй веб‑поиск и извлекай содержимое страниц с несколькими backend‑провайдерами — включая бесплатный self-hosted SearXNG.
sidebar_label: Web Search
sidebar_position: 6
---

# Веб‑поиск и извлечение

Hermes Agent включает два веб‑инструмента, вызываемых моделью и поддерживаемых несколькими провайдерами:

- **`web_search`** — поиск в интернете и возврат ранжированных результатов
- **`web_extract`** — получение и извлечение читаемого контента из одного или нескольких URL

Оба инструмента настраиваются через единый выбор бэкенда. Провайдеры выбираются с помощью `hermes tools` или задаются напрямую в `config.yaml`.
## Бэкенды

| Провайдер | Env Var | Поиск | Извлечение | Бесплатный тариф |
|----------|---------|--------|------------|-----------------|
| **Firecrawl** (default) | `FIRECRAWL_API_KEY` | ✔ | ✔ | 500 credits/mo |
| **SearXNG** | `SEARXNG_URL` | ✔ | — | ✔ Free (self-hosted) |
| **Brave Search (free tier)** | `BRAVE_SEARCH_API_KEY` | ✔ | — | 2 000 queries/mo |
| **DDGS (DuckDuckGo)** | — (no key) | ✔ | — | ✔ Free |
| **Tavily** | `TAVILY_API_KEY` | ✔ | ✔ | 1 000 searches/mo |
| **Exa** | `EXA_API_KEY` | ✔ | ✔ | 1 000 searches/mo |
| **Parallel** | `PARALLEL_API_KEY` | ✔ | ✔ | Paid |
| **xAI (Grok)** | `XAI_API_KEY` or `hermes auth login xai-oauth` | ✔ | — | Paid (SuperGrok or per-token) |

Brave Search, DDGS и xAI — **только поиск**: сочетай любой из них с Firecrawl/Tavily/Exa/Parallel, когда также нужен `web_extract`. DDGS использует Python‑пакет [`ddgs`](https://pypi.org/project/ddgs/) под капотом; если он ещё не установлен, выполни `pip install ddgs` (или позволь Hermes установить его при первом использовании). xAI запускает серверный инструмент `web_search` Grok на Responses API — результаты генерируются LLM, а не берутся из индекса, поэтому заголовки, описания и выбор URL полностью зависят от модели (см. [предупреждение о модели доверия](#xai-grok) ниже).

**Разделение по возможностям:** можно использовать разных провайдеров для поиска и извлечения независимо — например, бесплатный SearXNG для поиска и Firecrawl для извлечения. См. [Per-capability configuration](#per-capability-configuration) ниже.

:::tip Nous Subscribers
Если у тебя есть платная подписка на [Nous Portal](https://portal.nousresearch.com), веб‑поиск и извлечение доступны через **[Tool Gateway](tool-gateway.md)** с управляемым Firecrawl — API‑ключ не нужен. Новые установки могут выполнить `hermes setup --portal`, чтобы войти и включить все инструменты шлюза сразу; существующие установки могут включить только веб‑поиск командой `hermes tools`.
:::
## Как `web_extract` обрабатывает длинные страницы

Бэкенды возвращают необработанный markdown страницы, который может быть огромным (тематические форумы, сайты документации, новостные статьи с встроенными комментариями). Чтобы окно контекста оставалось пригодным и расходы были минимальными, `web_extract` пропускает полученный контент через **вспомогательную модель `web_extract`** перед передачей агенту. Поведение полностью зависит от размера:

| Размер страницы (символов) | Что происходит |
|----------------------------|----------------|
| Менее 5 000 | Возвращается как есть — без вызова LLM, полный markdown попадает к агенту |
| 5 000 – 500 000 | Однопроходное резюмирование вспомогательной моделью `web_extract`, ограничено примерно 5 000 символов вывода |
| 500 000 – 2 000 000 | Делится на части по 100 k‑символов, каждая резюмируется параллельно, затем синтезируется итоговое резюме (~5 000 символов) |
| Более 2 000 000 | Отказ с подсказкой использовать более целевой URL‑источник |

Резюме сохраняет цитаты, блоки кода и ключевые факты в их оригинальном формате — это компрессор контента, а не перефразировщик. Если резюмирование не удалось или истекло время, Hermes переходит к первым ~5 000 символам необработанного контента вместо бесполезной ошибки.

### Какая модель выполняет резюмирование?

Вспомогательная задача `web_extract`. По умолчанию (`auxiliary.web_extract.provider: "auto"`), это твоя **основная чат‑модель** — тот же провайдер и модель, что и `hermes model`. Это подходит для большинства конфигураций, но на дорогих моделях рассуждения (Opus, MiniMax M2.7 и др.) каждый извлечённый длинный документ добавляет значительные расходы.

Чтобы направлять резюме извлечений к дешевой, быстрой модели независимо от основной:

```yaml
# ~/.hermes/config.yaml
auxiliary:
  web_extract:
    provider: openrouter
    model: google/gemini-3-flash-preview
    timeout: 360       # seconds; raise if you hit summarization timeouts
```

Или выбрать интерактивно: `hermes model` → **Configure auxiliary models** → `web_extract`.

См. [Auxiliary Models](/user-guide/configuration#auxiliary-models) для полного справочника и шаблонов переопределения задач.

### Когда резюмирование мешает

Если тебе нужен именно необработанный контент страницы — например, ты собираешь структурированную страницу, где резюме LLM может удалить важные поля — используй `browser_navigate` + `browser_snapshot` вместо этого. Инструмент браузера возвращает живое дерево доступности без переписывания вспомогательной моделью (при этом имеет собственный лимит снимка в 8 000 символов для огромных страниц).
## Настройка

### Быстрая настройка через `hermes tools`

Запусти `hermes tools`, перейди в **Web Search & Extract** и выбери провайдер. Мастер запросит требуемый URL или API‑ключ и запишет их в твой конфиг.

```bash
hermes tools
```

---

### Firecrawl (по умолчанию)

Полнофункциональный поиск и извлечение. Рекомендуется для большинства пользователей.

```bash
# ~/.hermes/.env
FIRECRAWL_API_KEY=fc-your-key-here
```

Получить ключ можно на [firecrawl.dev](https://firecrawl.dev). Бесплатный тариф включает 500 кредитов в месяц.

**Самостоятельный запуск Firecrawl:** Укажи свой собственный экземпляр вместо облачного API:

```bash
# ~/.hermes/.env
FIRECRAWL_API_URL=http://localhost:3002
```

Когда установлен `FIRECRAWL_API_URL`, API‑ключ становится необязательным (отключи серверную аутентификацию с помощью `USE_DB_AUTHENTICATION=false`).

---

### SearXNG (бесплатно, самостоятельный хостинг)

SearXNG — это уважающий конфиденциальность, открытый метапоисковый движок, который агрегирует результаты более чем 70 поисковыми системами. **API‑ключ не требуется** — просто укажи Hermes на работающий экземпляр SearXNG.

SearXNG предназначен **только для поиска** — `web_extract` требует отдельного провайдера извлечения.

#### Вариант A — Самостоятельный запуск с Docker (рекомендовано)

Это даст тебе приватный экземпляр без ограничений по частоте запросов.

**1. Создай рабочий каталог:**

```bash
mkdir -p ~/searxng/searxng
cd ~/searxng
```

**2. Напиши `docker-compose.yml`:**

```yaml
# ~/searxng/docker-compose.yml
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8888:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8888/
    restart: unless-stopped
```

**3. Запусти контейнер:**

```bash
docker compose up -d
```

**4. Включи формат JSON API:**

По умолчанию SearXNG поставляется с отключённым выводом JSON. Скопируй сгенерированный конфиг и включи его:

```bash
# Copy the auto-generated config out of the container
docker cp searxng:/etc/searxng/settings.yml ~/searxng/searxng/settings.yml
```

Открой `~/searxng/searxng/settings.yml` и найди блок `formats` (примерно на строке 84):

```yaml
# Before (default — JSON disabled):
formats:
  - html

# After (enable JSON for Hermes):
formats:
  - html
  - json
```

**5. Перезапусти для применения:**

```bash
docker cp ~/searxng/searxng/settings.yml searxng:/etc/searxng/settings.yml
docker restart searxng
```

**6. Проверь, что всё работает:**

```bash
curl -s "http://localhost:8888/search?q=test&format=json" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"results\"])} results')"
```

Ты должен увидеть что‑то вроде `10 results`. Если получаешь `403 Forbidden`, значит формат JSON всё ещё отключён — проверь шаг 4 ещё раз.

**7. Настрой Hermes:**

```bash
# ~/.hermes/.env
SEARXNG_URL=http://localhost:8888
```

Затем выбери SearXNG в качестве поискового бэкенда в `~/.hermes/config.yaml`:

```yaml
web:
  search_backend: "searxng"
```

Или задай через `hermes tools` → Web Search & Extract → SearXNG.

---

#### Вариант B — Использовать публичный экземпляр

Публичные экземпляры SearXNG перечислены на [searx.space](https://searx.space/). Фильтруй по экземплярам, у которых **включён формат JSON** (отображается в таблице).

```bash
# ~/.hermes/.env
SEARXNG_URL=https://searx.example.com
```

:::caution Public instances
Публичные экземпляры имеют ограничения по частоте запросов, переменную доступность и могут в любой момент отключить формат JSON. Для продакшн‑использования настоятельно рекомендуется самостоятельный хостинг.
:::

---

#### Сочетание SearXNG с провайдером извлечения

SearXNG отвечает за поиск; тебе нужен отдельный провайдер для `web_extract`. Используй ключи по отдельным возможностям:

```yaml
# ~/.hermes/config.yaml
web:
  search_backend: "searxng"
  extract_backend: "firecrawl"   # or tavily, exa, parallel
```

С такой конфигурацией Hermes использует SearXNG для всех поисковых запросов и Firecrawl для извлечения URL — сочетая бесплатный поиск с качественным извлечением.

---

### Tavily

AI‑оптимизированный поиск и извлечение с щедрым бесплатным тарифом.

```bash
# ~/.hermes/.env
TAVILY_API_KEY=tvly-your-key-here
```

Получить ключ можно на [app.tavily.com](https://app.tavily.com/home). Бесплатный тариф включает 1 000 поисков в месяц.

---

### Exa

Нейронный поиск с семантическим пониманием. Хорош для исследований и поиска концептуально связанных материалов.

```bash
# ~/.hermes/.env
EXA_API_KEY=your-exa-key-here
```

Получить ключ можно на [exa.ai](https://exa.ai). Бесплатный тариф включает 1 000 поисков в месяц.

---

### Parallel

AI‑нативный поиск и извлечение с глубокими исследовательскими возможностями.

```bash
# ~/.hermes/.env
PARALLEL_API_KEY=your-parallel-key-here
```

Доступ получаешь на [parallel.ai](https://parallel.ai).

---

### xAI (Grok) {#xai-grok}

Маршрутизирует `web_search` через серверный [web_search tool](https://docs.x.ai/developers/tools/web-search) Grok в Responses API. Grok выполняет реальный поиск и возвращает топ‑результаты в виде структурированного JSON.

Работает с любым путём учётных данных — никаких новых переменных окружения, никаких новых мастеров настройки:

```bash
# ~/.hermes/.env (env-var path)
XAI_API_KEY=sk-xai-your-key-here
```

или для подписчиков SuperGrok:

```bash
hermes auth login xai-oauth
```

Затем выбери xAI в качестве поискового бэкенда:

```yaml
# ~/.hermes/config.yaml
web:
  backend: "xai"
```

**Дополнительные настройки:**

```yaml
web:
  backend: "xai"
  xai:
    model: grok-4.3              # reasoning model required by web_search (default)
    allowed_domains:             # optional, max 5 — mutex with excluded_domains
      - arxiv.org
    excluded_domains:            # optional, max 5
      - example-spam.com
    timeout: 90                  # seconds (default)
```

**Только поиск** — сочетай с Firecrawl / Tavily / Exa / Parallel, если также нужен `web_extract`. При 401 провайдер выполнит единственное принудительное обновление OAuth‑токена и повторит запрос (это покрывает отзыв токена в середине окна и непрозрачные токены, которые проактивная проверка истечения не может декодировать); учётные данные из переменных окружения пропускают повтор.

:::caution Trust model
В отличие от провайдеров, основанных на индексе (Brave, Tavily, Exa), которые возвращают дословные результаты поисковых систем, xAI — это LLM, выбирающий, какие URL показать, и самостоятельно формирующий заголовки и описания. *Содержание* запроса влияет на вывод, поэтому специально сформулированный вредоносный запрос (например, внедрённый через ненадёжный входной поток, который агент получил) может в принципе заставить Grok выдавать выбранные атакующим URL. Обрабатывай возвращённые URL так же, как любые ссылки, сгенерированные моделью — проверяй их перед загрузкой, особенно если запрос пришёл из ненадёжного источника.
:::

---
## Конфигурация

### Один бэкенд

Установи один провайдер для всех веб‑возможностей:

```yaml
# ~/.hermes/config.yaml
web:
  backend: "searxng"   # firecrawl | searxng | brave-free | ddgs | tavily | exa | parallel | xai
```

### Конфигурация по возможностям

Используй разные провайдеры для поиска и извлечения. Это позволяет комбинировать бесплатный поиск (SearXNG) с платным провайдером извлечения, или наоборот:

```yaml
# ~/.hermes/config.yaml
web:
  search_backend: "searxng"     # used by web_search
  extract_backend: "firecrawl"  # used by web_extract
```

Когда ключи по возможностям пусты, оба переходят к `web.backend`. Когда `web.backend` также пуст, бэкенд определяется автоматически на основе того, какой API‑ключ/URL присутствует.

**Порядок приоритета (по возможности):**
1. `web.search_backend` / `web.extract_backend` (явно указанные по возможности)
2. `web.backend` (общий запасной вариант)
3. Автоопределение из переменных окружения

### Автоопределение

Если бэкенд не настроен явно, Hermes выбирает первый доступный на основе установленных учётных данных:

| Наличие учётных данных | Автоматически выбранный бэкенд |
|------------------------|---------------------------------|
| `FIRECRAWL_API_KEY` или `FIRECRAWL_API_URL` | firecrawl |
| `PARALLEL_API_KEY` | parallel |
| `TAVILY_API_KEY` | tavily |
| `EXA_API_KEY` | exa |
| `SEARXNG_URL` | searxng |

xAI Web Search **не** включён в цепочку автоопределения — наличие `XAI_API_KEY` (или вход через xAI Grok OAuth) не перенаправляет веб‑трафик автоматически через xAI, так как эти учётные данные также используются для инференса / TTS / генерации изображений, и пользователь может захотеть другой бэкенд для веба. Включи его явно с помощью `web.backend: "xai"`.

---
## Проверь свою настройку

Запусти `hermes setup`, чтобы увидеть, какой веб‑бэкенд обнаружен:

```
✅ Web Search & Extract (searxng)
```

Или проверь через CLI:

```bash
# Activate the venv and run the web tools module directly
source ~/.hermes/hermes-agent/.venv/bin/activate
python -m tools.web_tools
```

Эта команда выводит активный бэкенд и его статус:

```
✅ Web backend: searxng
   Using SearXNG (search only): http://localhost:8888
```

---
## Устранение неполадок

### `web_search` возвращает `{"success": false}`

- Проверь, что `SEARXNG_URL` доступен: `curl -s "http://localhost:8888/search?q=test&format=json"`
- Если получаешь HTTP 403, формат JSON отключён — добавь `json` в список `formats` в `settings.yml` и перезапусти
- Если возникает ошибка соединения, контейнер может не работать: `docker ps | grep searxng`

### `web_extract` сообщает «search-only backend»

SearXNG не может извлекать содержимое URL. Установи `web.extract_backend` на провайдера, поддерживающего извлечение:

```yaml
web:
  search_backend: "searxng"
  extract_backend: "firecrawl"  # or tavily / exa / parallel
```

### SearXNG возвращает 0 результатов

Некоторые публичные инстансы отключают определённые поисковые движки или категории. Попробуй:
- Другой запрос
- Другой публичный инстанс с сайта [searx.space](https://searx.space/)
- Самохостинг собственного инстанса для надёжных результатов

### Ограничение скорости на публичном инстансе

Перейди на самохостинг (см. [Option A](#option-a--self-host-with-docker-recommended) выше). При использовании Docker твой собственный инстанс не имеет ограничений скорости.

### `web_extract` возвращает усечённое содержимое с пометкой «summarization timed out»

Вспомогательная модель не успела завершить суммирование в установленный тайм‑аут. Можно:

- Увеличить `auxiliary.web_extract.timeout` в `config.yaml` (по умолчанию 360 с на новых установках, 30 с, если ключ отсутствует)
- Переключить вспомогательную задачу `web_extract` на более быструю модель (например, `google/gemini-3-flash-preview`) — см. [How `web_extract` handles long pages](#how-web_extract-handles-long-pages)
- Для страниц, где суммирование не подходит, использовать `browser_navigate` вместо этого

---
## Optional skill: `searxng-search`

Для агентов, которым необходимо использовать SearXNG через `curl` напрямую (например, как запасной вариант, когда набор веб‑инструментов недоступен), установи необязательный навык `searxng-search`:

```bash
hermes skills install official/research/searxng-search
```

Это добавит навык, который обучает агента:
- Вызывать JSON‑API SearXNG через `curl` или Python
- Фильтровать по категории (`general`, `news`, `science` и т.д.)
- Обрабатывать пагинацию и случаи ошибок
- Корректно переходить к запасному варианту, когда SearXNG недоступен