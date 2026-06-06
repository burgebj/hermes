---
title: "Osint розслідування"
sidebar_label: "Osint Investigation"
description: "Фреймворк OSINT‑розслідувань за публічними записами — SEC EDGAR filings, USAspending contracts, Senate lobbying, OFAC sanctions, ICIJ offshore leaks, NYC property r..."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Osint Investigation

Фреймворк OSINT‑розслідувань за публічними даними — SEC EDGAR filings, USAspending contracts, Senate lobbying, OFAC sanctions, ICIJ offshore leaks, NYC property records (ACRIS), OpenCorporates registries, CourtListener court records, Wayback Machine archives, Wikipedia + Wikidata, GDELT news monitoring. Розв’язання сутностей між джерелами, крос‑лінковий аналіз, часова кореляція, ланцюги доказів. Лише Python stdlib.
## Метадані навички

| | |
|---|---|
| **Джерело** | Optional — install with `hermes skills install official/research/osint-investigation` |
| **Шлях** | `optional-skills/research/osint-investigation` |
| **Версія** | `0.1.0` |
| **Автор** | Hermes Agent (adapted from ShinMegamiBoson/OpenPlanter, MIT) |
| **Платформи** | linux, macos, windows |
| **Теги** | `osint`, `investigation`, `public-records`, `sec`, `sanctions`, `corporate-registry`, `property`, `courts`, `due-diligence`, `journalism` |
| **Пов’язані навички** | [`domain-intel`](/docs/user-guide/skills/optional/research/research-domain-intel), [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) |
:::info
Нижче наведено повне визначення **skill**, яке Hermes завантажує, коли цей **skill** активовано. Це інструкції, які бачить агент під час роботи **skill**.
:::

# OSINT‑розслідування — перехресна верифікація публічних реєстрів

Рамковий підхід для OSINT за публічними реєстрами: державні контракти, корпоративні документи, лобіювання, санкції, витоки даних офшорів, реєстри нерухомості, судові записи, веб‑архіви, бази знань та глобальні новини. Визначення сутностей у різнорідних джерелах, побудова перехресних зв’язків із зазначенням довіри, проведення статистичних тестів часу та формування структурованих ланцюжків доказів.

**Лише стандартна бібліотека Python.** Ніякої інсталяції. Працює на Linux, macOS, Windows. Більшість джерел працює без API‑ключа (OpenCorporates має необов’язковий безкоштовний токен, який підвищує ліміти запитів).

Адаптовано з проекту MIT‑ліцензії ShinMegamiBoson/OpenPlanter; розширено для охоплення ідентифікації, нерухомості, судових процесів, архівів та новинних джерел, які не були передбачені у оригіналі.
## Коли використовувати цей skill

Використовуй, коли користувач запитує:

- «follow the money» — державні контракти, лобіювання → законодавство, санкції
- корпоративна due‑diligence — хто контролює компанію X, де вона зареєстрована, хто входить до її ради, які документи подано
- перевірка санкцій — чи є суб’єкт X у списку OFAC SDN, розкриття ICIJ offshore leaks
- розслідування pay‑to‑play — підрядники з офшорними зв’язками, лобістські клієнти, які виграють нагороди
- власність нерухомості — знайти записані акти/іпотеку за ім’ям або адресою (NYC; для інших округів направляй користувачів до відповідного реєстратора)
- історія судових справ — знайти федеральні та штатні судові рішення та досьє PACER
- багатоджерельна ідентифікація сутностей, коли назви різняться (суфікси LLC, скорочення)
- побудова ланцюжка доказів з явними рівнями впевненості
- «what's been said about X» — міжнародні новини (GDELT) + наратив Wikipedia + Wayback Machine для відновлення недоступних URL

**Не використовуйте цей skill для:**

- загального веб‑дослідження → `web_search` / `web_extract`
- OSINT доменів/інфраструктури → `domain-intel` skill
- академічної літератури → `arxiv` skill
- виявлення профілів у соцмережах → `sherlock` skill (опціонально)
- фінансування федеральних виборчих кампаній США — FEC навмисно НЕ охоплюється тут (API ненадійний для довільних запитів за іменем внеска у безкоштовному тарифі DEMO_KEY). Для федеральних пожертвувань направляй користувачів до https://www.fec.gov/data/ .
## Робочий процес

Агент виконує скрипти за допомогою інструмента `terminal`. `SKILL_DIR` — це каталог,
в якому розташований цей SKILL.md.

### 1. Визначити, які джерела застосовні

Прочитай записи wiki про джерела даних, щоб спланувати розслідування:

```
ls SKILL_DIR/references/sources/

# Federal financial / regulatory
cat SKILL_DIR/references/sources/sec-edgar.md       # corporate filings
cat SKILL_DIR/references/sources/usaspending.md     # federal contracts
cat SKILL_DIR/references/sources/senate-ld.md       # lobbying
cat SKILL_DIR/references/sources/ofac-sdn.md        # sanctions
cat SKILL_DIR/references/sources/icij-offshore.md   # offshore leaks

# Identity / property / litigation / archives / news
cat SKILL_DIR/references/sources/nyc-acris.md       # NYC property records
cat SKILL_DIR/references/sources/opencorporates.md  # global corporate registry
cat SKILL_DIR/references/sources/courtlistener.md   # court records (federal + state)
cat SKILL_DIR/references/sources/wayback.md         # Wayback Machine archives
cat SKILL_DIR/references/sources/wikipedia.md       # Wikipedia + Wikidata
cat SKILL_DIR/references/sources/gdelt.md           # global news monitoring
```

Кожен запис слідує 9‑секційному шаблону: резюме, доступ, схема, охоплення,
ключі крос‑посилань, якість даних, отримання, юридичні аспекти, посилання.

Розділ **cross‑reference potential** містить мапу ключів з’єднання між джерелами — спочатку прочитай його, щоб вибрати правильну пару.

### 2. Отримати дані

Кожне джерело має скрипт лише зі стандартною бібліотекою в `SKILL_DIR/scripts/`:

**Federal financial / regulatory**

```bash
# SEC EDGAR filings (corporate disclosures)
python3 SKILL_DIR/scripts/fetch_sec_edgar.py --cik 0000320193 \
    --types 10-K,10-Q --out data/edgar_filings.csv

# USAspending federal contracts
python3 SKILL_DIR/scripts/fetch_usaspending.py --recipient "EXAMPLE CORP" \
    --fy 2024 --out data/contracts.csv

# Senate LD-1 / LD-2 lobbying disclosures
python3 SKILL_DIR/scripts/fetch_senate_ld.py --client "EXAMPLE CORP" \
    --year 2024 --out data/lobbying.csv

# OFAC SDN sanctions list (full snapshot)
python3 SKILL_DIR/scripts/fetch_ofac_sdn.py --out data/ofac_sdn.csv

# ICIJ Offshore Leaks — downloads ~70 MB bulk CSV on first use,
# then searches it locally. Cached for 30 days under
# $HERMES_OSINT_CACHE/icij/ (default: ~/.cache/hermes-osint/icij/).
python3 SKILL_DIR/scripts/fetch_icij_offshore.py --entity "EXAMPLE CORP" \
    --out data/icij.csv
```

**Identity / property / litigation / archives / news**

```bash
# NYC property records (deeds, mortgages, liens) — ACRIS via Socrata
python3 SKILL_DIR/scripts/fetch_nyc_acris.py --name "SMITH, JOHN" \
    --out data/acris.csv
python3 SKILL_DIR/scripts/fetch_nyc_acris.py --address "571 HUDSON" \
    --out data/acris_addr.csv

# OpenCorporates — 130+ jurisdiction corporate registry
# (free token required; set OPENCORPORATES_API_TOKEN or pass --token)
python3 SKILL_DIR/scripts/fetch_opencorporates.py --query "Example Corp" \
    --jurisdiction us_ny --out data/opencorporates.csv

# CourtListener — federal + state court opinions, PACER dockets
python3 SKILL_DIR/scripts/fetch_courtlistener.py --query "Smith v. Example Corp" \
    --type opinions --out data/courts.csv

# Wayback Machine — historical web captures
python3 SKILL_DIR/scripts/fetch_wayback.py --url "example.com" \
    --match host --collapse digest --out data/wayback.csv

# Wikipedia + Wikidata — narrative bio + structured facts
# Set HERMES_OSINT_UA=your-app/1.0 (your@email) to identify yourself
python3 SKILL_DIR/scripts/fetch_wikipedia.py --query "Bill Gates" \
    --out data/wp.csv

# GDELT — global news in 100+ languages, ~2015→present
python3 SKILL_DIR/scripts/fetch_gdelt.py --query '"Example Corp"' \
    --timespan 1y --out data/gdelt.csv
```

Усі результати — нормалізовані CSV з рядком‑заголовком. Перезапускай скрипти ідемпотентно.

Коли приватна особа не буде присутня у джерелі (наприклад, SEC EDGAR для особи, що не є публічною компанією, USAspending для того, хто не є федеральним підрядником, Senate LDA для того, хто не є клієнтом лобістської фірми), скрипт повертає 0 рядків з чітким попередженням замість того, щоб мовчки записати порожній CSV. EDGAR спеціально позначає, коли резолвер назви компанії збігся з особою‑файлером Form 3/4/5, а не з корпоративним реєстрантом.

Примітки про обмеження швидкості знаходяться в кожному wiki‑записі джерела. За замовчуванням fetch‑ери ввічливо сплять між пагінованими запитами. **API‑ключі підвищують ліміти** для джерел, які їх підтримують (`SEC_USER_AGENT`, `SENATE_LDA_TOKEN`, `OPENCORPORATES_API_TOKEN`, `COURTLISTENER_TOKEN`). Усі скрипти негайно повертають відповіді 429 разом із повідомленням про квоту від upstream, щоб користувач знав, що треба сповільнитися або надати ключ.

### 3. Вирішити сутності між джерелами

Нормалізуй імена та знайди збіги між двома CSV‑файлами:

```bash
# Match lobbying clients (Senate LDA) against contract recipients (USAspending)
python3 SKILL_DIR/scripts/entity_resolution.py \
    --left  data/lobbying.csv   --left-name-col  client_name \
    --right data/contracts.csv  --right-name-col recipient_name \
    --out data/cross_links.csv
```

Три рівні збігів з явно вказаною впевненістю:

| Tier | Method | Confidence |
|------|--------|------------|
| `exact` | Нормалізовані рядки рівні після видалення суфіксів/пунктуації | high |
| `fuzzy` | Рівність відсортованих токенів (збіг «мішка слів») | medium |
| `token_overlap` | ≥60 % перекриття токенів, ≥2 спільних токени, токени довжиною ≥4 символи | low |

Вихідний файл `cross_links.csv` містить стовпці: `match_type, confidence, left_name, right_name, left_normalized, right_normalized, left_row, right_row`.

### 4. Статистична кореляція за часом (необов’язково)

Перевір, чи два часових ряди кластеризуються підозріло близько один до одного — наприклад, лобістські подання поруч із нагородженням контрактів — за допомогою перестановочного тесту:

```bash
python3 SKILL_DIR/scripts/timing_analysis.py \
    --donations data/lobbying.csv --donation-date-col filing_date \
        --donation-amount-col income --donation-donor-col client_name \
        --donation-recipient-col registrant_name \
    --contracts data/contracts.csv --contract-date-col award_date \
        --contract-vendor-col recipient_name \
    --cross-links data/cross_links.csv \
    --permutations 1000 \
    --out data/timing.json
```

Прапці колонок скрипту навмисно загальні — оригінальний інструмент був написаний для порівняння пожертвувань і нагород, але працює для будь‑яких часових рядів (подія, отримувач), з’єднаних через крос‑посилання. Нульова гіпотеза: час події незалежний від дат нагород. Одностороннє p‑значення = частка перестановок, у яких середня відстань до найближчої нагороди ≤ спостережуваній. Мінімум 3 події на пару (payer, vendor) для проведення тесту.

### 5. Побудувати JSON‑висновків (ланцюжок доказів)

```bash
python3 SKILL_DIR/scripts/build_findings.py \
    --cross-links data/cross_links.csv \
    --timing data/timing.json \
    --out data/findings.json
```

Кожен висновок має `id, title, severity, confidence, summary, evidence[], sources[]`. Кожен елемент доказу посилається на конкретний рядок у CSV‑джерелі. Користувач (або наступний агент) може перевірити кожну заяву за її джерелом.
## Дисципліна впевненості та доказів

Це ключове правило навички. Скажи користувачеві:

- Кожне твердження має бути пов’язане з записом. Ніяких необґрунтованих тверджень.
- Рівень впевненості супроводжує твердження. `match_type=fuzzy` — це «ймовірно», а не «підтверджено».
- Розв’язання сутностей створює кандидатів, а НЕ висновки. `fuzzy` збіг між «ACME LLC» і «Acme Holdings Group» — це лід, а не факт.
- Статистична значущість ≠ порушення. p < 0.05 означає, що часовий шаблон малоймовірний за нульовою гіпотезою. Це не встановлює корупції.
- Усі джерела даних тут — публічні записи. Вони все ж можуть містити неточності, застарілі дані або редакції (GDPR, запечатані записи).
## Додавання нового джерела даних

Використай шаблон:

```bash
cp SKILL_DIR/templates/source-template.md \
    SKILL_DIR/references/sources/<your-source>.md
```

Заповни всі 9 розділів. Напиши скрипт `fetch_<source>.py` у каталозі `scripts/`, який
використовує лише стандартну бібліотеку і записує нормалізований CSV‑файл. Онови список джерел у
розділі «Коли використовувати» вище.
## Інструменти та їхні обмеження

- `entity_resolution.py` НЕ використовує зовнішні нечіткі бібліотеки (не rapidfuzz, не jellyfish). Збіг за набором токенів є верхньою межею тут. Якщо потрібен Levenshtein, транслитерація або фонетичне порівняння, встанови їх окремо за допомогою `pip install`.
- `timing_analysis.py` використовує `random` з Python для перестановок. Для відтворюваності передай `--seed N`.
- `fetch_*.py` скрипти використовують `urllib.request` і дотримуються `Retry-After`. Інтенсивне масове використання може порушувати ToS — спочатку ознайомся з юридичним розділом кожного джерела.
## Юридичне зауваження

Усі джерела Phase‑1 є публічними записами. Масове отримання дозволено згідно їхніх відповідних умов доступу (FOIA, закон про публічні записи, явна публікація ICIJ, публічні дані OFAC). Однак:

- Деякі джерела жорстко обмежують частоту запитів. Дотримуйся їхніх заголовків.
- Деякі затирають інформацію про реєстратора (GDPR у WHOIS, запечатані документи).
- Перехресне зіставлення публічних записів для ідентифікації приватних осіб може мати етичні наслідки. Навичка створює ланцюжки доказів, а не звинувачення.