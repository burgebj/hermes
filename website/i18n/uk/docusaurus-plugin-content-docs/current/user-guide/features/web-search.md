---
title: Веб-пошук & Витяг
description: Шукай в інтернеті та витягай вміст сторінок з кількома бекенд‑провайдерами — включаючи безкоштовний самохостинг SearXNG.
sidebar_label: Web Search
sidebar_position: 6
---

# Веб‑пошук та екстракція

Hermes Agent включає два веб‑інструменти, які можна викликати з моделі та які підтримуються кількома провайдерами:

- **`web_search`** — пошук в інтернеті та повернення ранжованих результатів
- **`web_extract`** — отримання та екстракція читабельного вмісту з одного або кількох URL‑адрес

Обидва інструменти налаштовуються через єдине налаштування бекенду. Провайдери обираються за допомогою `hermes tools` або встановлюються безпосередньо в `config.yaml`.
## Backends

| Provider | Env Var | Search | Extract | Free tier |
|----------|---------|--------|---------|-----------|
| **Firecrawl** (default) | `FIRECRAWL_API_KEY` | ✔ | ✔ | 500 credits/mo |
| **SearXNG** | `SEARXNG_URL` | ✔ | — | ✔ Free (self-hosted) |
| **Brave Search (free tier)** | `BRAVE_SEARCH_API_KEY` | ✔ | — | 2 000 queries/mo |
| **DDGS (DuckDuckGo)** | — (no key) | ✔ | — | ✔ Free |
| **Tavily** | `TAVILY_API_KEY` | ✔ | ✔ | 1 000 searches/mo |
| **Exa** | `EXA_API_KEY` | ✔ | ✔ | 1 000 searches/mo |
| **Parallel** | `PARALLEL_API_KEY` | ✔ | ✔ | Paid |
| **xAI (Grok)** | `XAI_API_KEY` or `hermes auth login xai-oauth` | ✔ | — | Paid (SuperGrok or per-token) |

Brave Search, DDGS і xAI — це **лише пошук** — поєднуй будь‑який з них з Firecrawl/Tavily/Exa/Parallel, коли потрібен також `web_extract`. DDGS використовує пакет Python [`ddgs`](https://pypi.org/project/ddgs/) під капотом; якщо він ще не встановлений, запусти `pip install ddgs` (або дай Hermes встановити його автоматично під час першого використання). xAI запускає серверний інструмент `web_search` Grok на Responses API — результати генерує LLM, а не індекс, тому назви, описи та вибір URL‑ів — це вихід моделі (дивись застереження щодо [trust-model](#xai-grok) нижче).

**Розподіл за можливостями:** можна окремо використовувати різних провайдерів для пошуку та витягування — наприклад, SearXNG (free) для пошуку і Firecrawl для витягування. Дивись [Per-capability configuration](#per-capability-configuration) нижче.

:::tip Nous Subscribers
Якщо у тебе є платна підписка на [Nous Portal](https://portal.nousresearch.com), веб‑пошук і витягування доступні через **[Tool Gateway](tool-gateway.md)** з керованим Firecrawl — ключ API не потрібен. Нові інсталяції можуть виконати `hermes setup --portal`, щоб увійти та ввімкнути всі інструменти шлюзу одразу; існуючі інсталяції можуть увімкнути лише веб‑пошук за допомогою `hermes tools`.
:::
## Як `web_extract` обробляє довгі сторінки

Backends повертають сирий markdown сторінки, який може бути величезним (теми форумів, сайти документації, новинні статті з вбудованими коментарями). Щоб твоє контекстне вікно залишалося придатним і витрати були низькими, `web_extract` пропускає отриманий вміст через **auxiliary модель `web_extract`** перед передачею агенту. Поведінка керується лише розміром:

| Розмір сторінки (символів) | Що відбувається |
|----------------------------|------------------|
| Менше 5 000 | Повертається як є — без виклику LLM, повний markdown потрапляє до агента |
| 5 000 – 500 000 | Однопрохідне резюме за допомогою auxiliary моделі `web_extract`, обмежене приблизно 5 000 символами виходу |
| 500 000 – 2 000 000 | Розбито на частини: розбивається на фрагменти по 100 k символів, кожен резюмується паралельно, потім синтезується фінальне резюме (~5 000 символів) |
| Понад 2 000 000 | Відхилено з підказкою використати більш сфокусоване URL‑джерело |

Резюме зберігає цитати, блоки коду та ключові факти у їхньому оригінальному форматуванні — це компресор вмісту, а не перефразовувач. Якщо резюмування не вдається або час вичерпується, Hermes переходить до перших ~5 000 символів сирого вмісту замість безглуздої помилки.

### Яка модель виконує резюмування?

auxiliary задача `web_extract`. За замовчуванням (`auxiliary.web_extract.provider: "auto"`), це твоя **головна чат‑модель** — той самий провайдер, та сама модель, що й `hermes model`. Це підходить для більшості налаштувань, але на дорогих моделях розуміння (Opus, MiniMax M2.7 тощо) кожен витяг довгої сторінки додає суттєві витрати.

Щоб направляти резюме витягів до дешевої, швидкої моделі незалежно від твоєї головної:

```yaml
# ~/.hermes/config.yaml
auxiliary:
  web_extract:
    provider: openrouter
    model: google/gemini-3-flash-preview
    timeout: 360       # seconds; raise if you hit summarization timeouts
```

Або вибрати інтерактивно: `hermes model` → **Configure auxiliary models** → `web_extract`.

Дивись [Auxiliary Models](/user-guide/configuration#auxiliary-models) для повного довідника та шаблонів перевизначення per‑task.

### Коли резюмування заважає

Якщо тобі потрібен саме сирий, не резюмований вміст сторінки — наприклад, ти скануєш структуровану сторінку, де резюме LLM пропустить важливі поля — використай `browser_navigate` + `browser_snapshot` замість цього. Інструмент браузера повертає живе дерево доступності без переписування auxiliary‑моделлю (з урахуванням власного ліміту у 8 000 символів на знімок великих сторінок).
## Налаштування

### Швидке налаштування за допомогою `hermes tools`

Запусти `hermes tools`, перейди до **Web Search & Extract** і вибери провайдера. Майстер запитає потрібний URL або API‑ключ і запише його у твій конфіг.

```bash
hermes tools
```

---

### Firecrawl (за замовчуванням)

Повнофункціональний пошук і екстракція. Рекомендовано для більшості користувачів.

```bash
# ~/.hermes/.env
FIRECRAWL_API_KEY=fc-your-key-here
```

Отримай ключ на [firecrawl.dev](https://firecrawl.dev). Безкоштовний тариф включає 500 кредитів/місяць.

**Самостійно розгорнутий Firecrawl:** вкажи свою інстанцію замість хмарного API:

```bash
# ~/.hermes/.env
FIRECRAWL_API_URL=http://localhost:3002
```

Коли встановлено `FIRECRAWL_API_URL`, API‑ключ є необов’язковим (вимкни серверну автентифікацію за допомогою `USE_DB_AUTHENTICATION=false`).

---

### SearXNG (безкоштовно, самостійно)

SearXNG — це орієнтований на конфіденційність, відкритий метапошуковий движок, який агрегує результати з більш ніж 70 пошукових систем. **API‑ключ не потрібен** — просто вкажи Hermes на працюючу інстанцію SearXNG.

SearXNG — це **лише пошук** — `web_extract` потребує окремого провайдера екстракції.

#### Варіант A — Самостійне розгортання з Docker (рекомендовано)

Це дає приватну інстанцію без обмежень швидкості.

**1. Створи робочу директорію:**

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

**4. Увімкни формат JSON API:**

SearXNG постачається з вимкненим виводом JSON за замовчуванням. Скопіюй згенерований конфіг і увімкни його:

```bash
# Copy the auto-generated config out of the container
docker cp searxng:/etc/searxng/settings.yml ~/searxng/searxng/settings.yml
```

Відкрий `~/searxng/searxng/settings.yml` і знайди блок `formats` (близько рядка 84):

```yaml
# Before (default — JSON disabled):
formats:
  - html

# After (enable JSON for Hermes):
formats:
  - html
  - json
```

**5. Перезапусти для застосування змін:**

```bash
docker cp ~/searxng/searxng/settings.yml searxng:/etc/searxng/settings.yml
docker restart searxng
```

**6. Перевір, що працює:**

```bash
curl -s "http://localhost:8888/search?q=test&format=json" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"results\"])} results')"
```

Ти маєш побачити щось на кшталт `10 results`. Якщо отримав `403 Forbidden`, формат JSON все ще вимкнено — перевір ще раз крок 4.

**7. Налаштуй Hermes:**

```bash
# ~/.hermes/.env
SEARXNG_URL=http://localhost:8888
```

Потім вибери SearXNG як бекенд пошуку у `~/.hermes/config.yaml`:

```yaml
web:
  search_backend: "searxng"
```

Або встанови через `hermes tools` → Web Search & Extract → SearXNG.

---

#### Варіант B — Використати публічну інстанцію

Публічні інстанції SearXNG перелічені на [searx.space](https://searx.space/). Фільтруй інстанції, у яких **включений формат JSON** (показано в таблиці).

```bash
# ~/.hermes/.env
SEARXNG_URL=https://searx.example.com
```

:::caution Публічні інстанції
Публічні інстанції мають обмеження швидкості, змінну доступність і можуть будь‑коли вимкнути формат JSON. Для продакшн‑використання настійно рекомендується самостійне розгортання.
:::

---

#### Поєднай SearXNG з провайдером екстракції

SearXNG відповідає за пошук; тобі потрібен окремий провайдер для `web_extract`. Використай ключі за можливостями:

```yaml
# ~/.hermes/config.yaml
web:
  search_backend: "searxng"
  extract_backend: "firecrawl"   # or tavily, exa, parallel
```

З таким конфігом Hermes використовує SearXNG для всіх пошукових запитів, а Firecrawl — для екстракції URL‑ів, поєднуючи безкоштовний пошук з високоякісною екстракцією.

---

### Tavily

AI‑оптимізований пошук і екстракція з щедрим безкоштовним тарифом.

```bash
# ~/.hermes/.env
TAVILY_API_KEY=tvly-your-key-here
```

Отримай ключ на [app.tavily.com](https://app.tavily.com/home). Безкоштовний тариф включає 1 000 пошуків/місяць.

---

### Exa

Нейронний пошук із семантичним розумінням. Добре підходить для досліджень і пошуку концептуально пов’язаного контенту.

```bash
# ~/.hermes/.env
EXA_API_KEY=your-exa-key-here
```

Отримай ключ на [exa.ai](https://exa.ai). Безкоштовний тариф включає 1 000 пошуків/місяць.

---

### Parallel

AI‑нативний пошук і екстракція з глибокими дослідницькими можливостями.

```bash
# ~/.hermes/.env
PARALLEL_API_KEY=your-parallel-key-here
```

Отримай доступ на [parallel.ai](https://parallel.ai).

---

### xAI (Grok) {#xai-grok}

Маршрутизує `web_search` через серверний інструмент [web_search tool](https://docs.x.ai/developers/tools/web-search) Grok у Responses API. Grok виконує фактичний пошук і повертає топ‑результати у вигляді структурованого JSON.

Працює з будь‑яким шляхом облікових даних — без нових змінних середовища, без нового майстра налаштувань:

```bash
# ~/.hermes/.env (env-var path)
XAI_API_KEY=sk-xai-your-key-here
```

або для підписників SuperGrok:

```bash
hermes auth login xai-oauth
```

Потім вибери xAI як бекенд пошуку:

```yaml
# ~/.hermes/config.yaml
web:
  backend: "xai"
```

**Додаткові налаштування:**

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

**Тільки пошук** — поєднуй з Firecrawl / Tavily / Exa / Parallel, якщо потрібен також `web_extract`. При 401 провайдер виконує одноразове примусове оновлення OAuth‑токену і повторює запит (покриває відкликання посередині вікна та непрозорі токени, які проактивна перевірка терміну дії не може розшифрувати); облікові дані у змінних середовища пропускають повторну спробу.

:::caution Модель довіри
На відміну від провайдерів, що працюють на індексах (Brave, Tavily, Exa), які повертають дослівні результати пошукових систем, xAI — це LLM, який обирає, які URL‑и показати, і сам формує заголовки та описи. *Зміст* запиту впливає на вихід, тому зловмисно сформований запит (наприклад, ін’єкція через недовірені вхідні дані, які агент отримав) може потенційно змусити Grok видавати URL‑и, обрані атакувальником. Обробляй повернені URL‑и так само, як будь‑яке посилання, згенероване моделлю — валідуй їх перед завантаженням, особливо якщо запит прийшов із недовіреного джерела.
:::
## Конфігурація

### Одиний бекенд

Встанови один провайдер для всіх веб‑можливостей:

```yaml
# ~/.hermes/config.yaml
web:
  backend: "searxng"   # firecrawl | searxng | brave-free | ddgs | tavily | exa | parallel | xai
```

### Конфігурація за можливістю

Використовуй різні провайдери для пошуку та витягування. Це дозволяє комбінувати безкоштовний пошук (SearXNG) з платним провайдером витягування, або навпаки:

```yaml
# ~/.hermes/config.yaml
web:
  search_backend: "searxng"     # used by web_search
  extract_backend: "firecrawl"  # used by web_extract
```

Коли ключі за можливістю порожні, обидва переходять до `web.backend`. Якщо `web.backend` також порожній, бекенд автоматично визначається за наявністю відповідного API‑ключа/URL.

**Порядок пріоритету (за можливістю):**
1. `web.search_backend` / `web.extract_backend` (явно задано за можливістю)
2. `web.backend` (спільний запасний (варіант))
3. Автовизначення зі змінних середовища

### Автовизначення

Якщо бекенд не вказано явно, Hermes вибирає перший доступний на основі наявних облікових даних:

| Присутня облікова дані | Автовибраний бекенд |
|-----------------------|---------------------|
| `FIRECRAWL_API_KEY` або `FIRECRAWL_API_URL` | firecrawl |
| `PARALLEL_API_KEY` | parallel |
| `TAVILY_API_KEY` | tavily |
| `EXA_API_KEY` | exa |
| `SEARXNG_URL` | searxng |

xAI Web Search **не** входить до ланцюжка автовизначення — наявність `XAI_API_KEY` (або вхід через xAI Grok OAuth) не перенаправляє веб‑трафік автоматично через xAI, оскільки ці облікові дані також використовуються для інференсу / TTS / генерації зображень, і користувач може захотіти інший бекенд для вебу. Увімкни його явно за допомогою `web.backend: "xai"`.

---
## Перевір налаштування

Run `hermes setup` to see which web backend is detected:

```
✅ Web Search & Extract (searxng)
```

Або перевір через CLI:

```bash
# Activate the venv and run the web tools module directly
source ~/.hermes/hermes-agent/.venv/bin/activate
python -m tools.web_tools
```

Це виводить активний веб‑бекенд та його статус:

```
✅ Web backend: searxng
   Using SearXNG (search only): http://localhost:8888
```

---
## Устранення проблем

### `web_search` повертає `{"success": false}`

- Перевір, чи доступний `SEARXNG_URL`: `curl -s "http://localhost:8888/search?q=test&format=json"`
- Якщо отримуєш HTTP 403, формат JSON вимкнено — додай `json` до списку `formats` у `settings.yml` і перезапусти
- Якщо виникає помилка підключення, контейнер може не працювати: `docker ps | grep searxng`

### `web_extract` повідомляє «search-only backend»

SearXNG не може витягати вміст URL. Встанови `web.extract_backend` на провайдера, який підтримує витяг:

```yaml
web:
  search_backend: "searxng"
  extract_backend: "firecrawl"  # or tavily / exa / parallel
```

### SearXNG повертає 0 результатів

Деякі публічні інстанси вимикають певні пошукові системи або категорії. Спробуй:
- інший запит
- інший публічний інстанс з [searx.space](https://searx.space/)
- самостійно розгорнути власний інстанс для надійних результатів

### Обмеження швидкості запитів на публічному інстансі

Перейди на самостійно розгорнутий інстанс (див. [Option A](#option-a--self-host-with-docker-recommended) вище). У Docker твій власний інстанс не має обмежень швидкості.

### `web_extract` повертає скорочений вміст з приміткою «summarization timed out»

Допоміжна модель не завершила підсумовування протягом налаштованого часу очікування. Можна:

- збільшити `auxiliary.web_extract.timeout` у `config.yaml` (за замовчуванням 360 s у нових інсталяціях, 30 s, якщо ключ відсутній)
- переключити допоміжне завдання `web_extract` на швидшу модель (наприклад `google/gemini-3-flash-preview`) — див. [How `web_extract` handles long pages](#how-web_extract-handles-long-pages)
- для сторінок, де підсумовування не підходить, використати `browser_navigate` замість цього

---
## Додаткова навичка: `searxng-search`

Для агентів, яким потрібно використовувати SearXNG через `curl` безпосередньо (наприклад, як запасний варіант, коли набір інструментів веб‑пошуку недоступний), встанови додаткову навичку `searxng-search`:

```bash
hermes skills install official/research/searxng-search
```

Це додає навичку, яка навчає агента:
- Викликати JSON‑API SearXNG через `curl` або Python
- Фільтрувати за категорією (`general`, `news`, `science` тощо)
- Обробляти пагінацію та випадки помилок
- Запасно (фолбек) працювати, коли SearXNG недоступний