---
title: "Osint расследование"
sidebar_label: "Osint Investigation"
description: "Фреймворк OSINT-расследований публичных записей — документы SEC EDGAR, контракты USAspending, лоббизм Сената, санкции OFAC, утечки ICIJ offshore, недвижимость NYC."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Osint Investigation

Фреймворк OSINT‑расследований по публичным записям — документы SEC EDGAR, контракты USAspending, лоббизм Сената, санкции OFAC, утечки ICIJ offshore, записи о недвижимости NYC (ACRIS), реестры OpenCorporates, судебные записи CourtListener, архивы Wayback Machine, Wikipedia + Wikidata, мониторинг новостей GDELT. Разрешение сущностей между источниками, кросс‑ссылочный анализ, корреляция по времени, цепочки доказательств. Только стандартная библиотека Python.
## Метаданные навыка

| | |
|---|---|
| Источник | Опционально — установить с помощью `hermes skills install official/research/osint-investigation` |
| Путь | `optional-skills/research/osint-investigation` |
| Версия | `0.1.0` |
| Автор | Hermes Agent (адаптировано из ShinMegamiBoson/OpenPlanter, MIT) |
| Платформы | linux, macos, windows |
| Теги | `osint`, `investigation`, `public-records`, `sec`, `sanctions`, `corporate-registry`, `property`, `courts`, `due-diligence`, `journalism` |
| Связанные навыки | [`domain-intel`](/docs/user-guide/skills/optional/research/research-domain-intel), [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) |
:::info
Следующий текст — полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при активном навыке.
:::

# OSINT‑расследование — перекрёстная проверка публичных реестров

Исследовательская структура для OSINT публичных реестров: государственные контракты, корпоративные документы, лоббизм, санкции, утечки офшорных данных, реестры недвижимости, судебные записи, веб‑архивы, базы знаний и глобальные новости. Идентифицирует сущности из разнородных источников, строит перекрёстные ссылки с явной оценкой уверенности, проводит статистические тесты по времени и формирует структурированные цепочки доказательств.

**Только стандартная библиотека Python.** Без установки. Работает на Linux, macOS, Windows. Большинство источников работают без API‑ключа (OpenCorporates имеет необязательный бесплатный токен, повышающий лимиты запросов).

Адаптировано из проекта MIT‑лицензии ShinMegamiBoson/OpenPlanter; расширено для охвата идентификации / недвижимости / судебных дел / архивов / новостных источников, которые не покрывались в оригинале.
## Когда использовать этот инструмент

Используй, когда пользователь запрашивает:

- «follow the money» — государственные контракты, лоббизм → законодательство, санкции
- corporate due diligence — кто контролирует компанию X, где она зарегистрирована, кто входит в её совет директоров, какие документы она подавала
- sanctions screening — находится ли субъект X в списке OFAC SDN, утечки ICIJ Offshore
- pay‑to‑play investigation — подрядчики с офшорными связями, лоббистские клиенты, получающие награды
- property ownership — поиск записей о праве собственности/ипотеке по имени или адресу (NYC; для других округов направляй пользователей к соответствующему регистратору)
- litigation history — поиск федеральных и штатных судебных решений и дел в PACER
- multi‑source entity resolution, когда названия различаются (суффиксы LLC, аббревиатуры)
- построение цепочки доказательств с указанием уровня уверенности
- «what's been said about X» — международные новости (GDELT) + Wikipedia narrative + Wayback Machine для восстановления недоступных URL‑ов

Не используй этот инструмент для:

- общего веб‑исследования → `web_search` / `web_extract`
- OSINT доменов/инфраструктуры → `domain-intel` skill
- академической литературы → `arxiv` skill
- поиска профилей в соцсетях → `sherlock` skill (по желанию)
- федерального финансирования кампаний США — FEC намеренно НЕ покрывается здесь (API ненадёжно для запросов по имени вкладчика в режиме ad‑hoc на бесплатном тарифе DEMO_KEY). Для федеральных пожертвований направляй пользователей на https://www.fec.gov/data/ напрямую.
## Workflow

Агент запускает скрипты через инструмент `terminal`. `SKILL_DIR` — каталог, в котором находится этот SKILL.md.

### 1. Определить, какие источники применимы

Прочитай записи wiki о источниках данных, чтобы спланировать расследование:

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

Каждая запись следует 9‑разделному шаблону: summary, access, schema, coverage, cross‑reference keys, data quality, acquisition, legal, references.

Раздел **cross‑reference potential** сопоставляет ключи соединения между источниками — читай его первым, чтобы выбрать правильную пару.

### 2. Получить данные

У каждого источника есть скрипт‑загрузчик, использующий только stdlib, в `SKILL_DIR/scripts/`:

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

Все выводы нормализованы в CSV с заголовочной строкой. Перезапускай скрипты идемпотентно.

Когда частное лицо отсутствует в источнике (например, SEC EDGAR для не публичной компании, USAspending для человека, не являющегося федеральным подрядчиком, Senate LDA для не‑клиента лоббирования), скрипт возвращает 0 строк с чётким предупреждением, а не молча пишет пустой CSV. EDGAR специально отмечает, когда резолвер названия компании сопоставил индивидуального файло­вателя Form 3/4/5 вместо корпоративного регистранта.

Замечания о лимитах запросов находятся в wiki‑записях каждого источника. Стандартные загрузчики делают паузы между пагинированными запросами. **API‑ключи повышают лимиты** для источников, которые их поддерживают (`SEC_USER_AGENT`, `SENATE_LDA_TOKEN`, `OPENCORPORATES_API_TOKEN`, `COURTLISTENER_TOKEN`). Все скрипты сразу выводят ответы 429 с сообщением о квоте от upstream, чтобы пользователь знал, что нужно замедлиться или предоставить ключ.

### 3. Сопоставить сущности между источниками

Нормализуй имена и найди совпадения между двумя CSV‑файлами:

```bash
# Match lobbying clients (Senate LDA) against contract recipients (USAspending)
python3 SKILL_DIR/scripts/entity_resolution.py \
    --left  data/lobbying.csv   --left-name-col  client_name \
    --right data/contracts.csv  --right-name-col recipient_name \
    --out data/cross_links.csv
```

Три уровня сопоставления с явной уверенностью:

| Tier | Method | Confidence |
|------|--------|------------|
| `exact` | Normalized strings equal after suffix/punctuation strip | high |
| `fuzzy` | Sorted-token equality (word‑bag match) | medium |
| `token_overlap` | ≥60 % token overlap, ≥2 shared tokens, tokens ≥4 chars | low |

Вывод `cross_links.csv` содержит столбцы: `match_type, confidence, left_name, right_name, left_normalized, right_normalized, left_row, right_row`.

### 4. Статистическая корреляция по времени (опционально)

Проверь, объединяются ли два временных ряда подозрительно близко — например, лоббистские заявки рядом с присуждением контрактов — с помощью перестановочного теста:

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

Флаги столбцов скрипта намеренно общие — исходный инструмент был написан для сравнения пожертвований и наград, но работает с любыми (event, payee) временными рядами, соединёнными через cross‑links. Нулевая гипотеза: время события независимо от дат наград. Одностороннее p‑value = доля перестановок, у которых среднее расстояние до ближайшей награды ≤ наблюдаемому. Требуется минимум 3 события на пару (payer, vendor) для проведения теста.

### 5. Сформировать JSON‑отчёт (цепочка доказательств)

```bash
python3 SKILL_DIR/scripts/build_findings.py \
    --cross-links data/cross_links.csv \
    --timing data/timing.json \
    --out data/findings.json
```

Каждая находка имеет `id, title, severity, confidence, summary, evidence[], sources[]`. Каждый элемент `evidence` указывает на конкретную строку в CSV‑источнике. Пользователь (или последующий агент) может проверить каждое утверждение по его источнику.
## Дисциплина уверенности и доказательств

Это ключевое правило навыка. Сообщай пользователю:

- Каждое утверждение должно ссылаться на запись. Никаких голых заявлений.
- Уровень уверенности сопровождает утверждение. `match_type=fuzzy` означает «вероятно», а не «подтверждено».
- Разрешение сущностей генерирует кандидаты, а НЕ выводы. Сопоставление `fuzzy` между «ACME LLC» и «Acme Holdings Group» — это подсказка, а не факт.
- Статистическая значимость ≠ правонарушение. p < 0.05 означает, что шаблон во времени маловероятен при нулевой гипотезе. Это не доказывает коррупцию.
- Все источники данных здесь — публичные записи. Они всё равно могут содержать неточности, устаревшую информацию или редактирование (GDPR, запечатанные записи).
## Добавление нового источника данных

Используй шаблон:

```bash
cp SKILL_DIR/templates/source-template.md \
    SKILL_DIR/references/sources/<your-source>.md
```

Заполни все 9 разделов. Напиши скрипт `fetch_<source>.py` в `scripts/`, который
использует только стандартную библиотеку и записывает нормализованный CSV. Обнови список источников в
разделе «When to use» выше.
## Инструменты и их ограничения

- `entity_resolution.py` НЕ использует внешние библиотеки нечёткого поиска (нет rapidfuzz, нет jellyfish). Здесь верхней границей является сопоставление по набору токенов. Если нужны расстояние Левенштейна, транслитерация или фонетическое сопоставление, установи их отдельно через `pip install`.
- `timing_analysis.py` использует `random` из Python для перестановок. Для воспроизводимости передай `--seed N`.
- Скрипты `fetch_*.py` используют `urllib.request` и учитывают `Retry-After`. Интенсивное массовое использование всё равно может нарушать условия обслуживания — сначала прочитай юридический раздел каждого источника.
## Юридическое примечание

Все источники Phase‑1 являются публичными записями. Массовое получение данных разрешено в соответствии с их условиями доступа (FOIA, закон о публичных записях, явная публикация ICIJ, публичные данные OFAC). Однако:

- Некоторые источники строго ограничивают частоту запросов. Соблюдай их заголовки.
- Некоторые скрывают информацию о регистранте (GDPR в WHOIS, запечатанные документы).
- Сопоставление публичных записей для идентификации частных лиц может иметь этические последствия. Инструмент создаёт цепочки доказательств, а не обвинения.