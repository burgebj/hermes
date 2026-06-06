---
title: "Карты — геокодирование, точки интереса, маршруты, часовые пояса через OpenStreetMap/OSRM"
sidebar_label: "Maps"
description: "Геокодирование, точки интереса, маршруты, часовые пояса через OpenStreetMap/OSRM"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Карты

Геокодирование, POI, маршруты, часовые пояса через OpenStreetMap/OSRM.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/maps` |
| Version | `1.2.0` |
| Author | Mibayy |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `maps`, `geocoding`, `places`, `routing`, `distance`, `directions`, `nearby`, `location`, `openstreetmap`, `nominatim`, `overpass`, `osrm` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Навык Maps

Интеллект местоположения, использующий бесплатные открытые источники данных. 8 команд, 44 категории POI, ноль зависимостей (только стандартная библиотека Python), ключ API не требуется.

Источники данных: OpenStreetMap/Nominatim, Overpass API, OSRM, TimeAPI.io.

Этот навык заменяет старый `find-nearby` — вся функциональность `find-nearby` покрыта командой `nearby` ниже, с тем же ярлыком `--near "<place>"` и поддержкой нескольких категорий.

## Когда использовать

- Пользователь отправляет pin местоположения Telegram (широта/долгота в сообщении) → `nearby`
- Пользователь хочет координаты для названия места → `search`
- Пользователь имеет координаты и хочет адрес → `reverse`
- Пользователь запрашивает рядом рестораны, больницы, аптеки, отели и т.д. → `nearby`
- Пользователь хочет расстояние или время в пути для автомобиля/пешком/велосипедом → `distance`
- Пользователь хочет пошаговую навигацию между двумя местами → `directions`
- Пользователь хочет информацию о часовом поясе для места → `timezone`
- Пользователь хочет искать POI внутри географической области → `area` + `bbox`

## Предварительные требования

Python 3.8+ (только стандартная библиотека — установки через pip не нужны).

Путь к скрипту: `~/.hermes/skills/maps/scripts/maps_client.py`

## Команды

```bash
MAPS=~/.hermes/skills/maps/scripts/maps_client.py
```

### search — Геокодировать название места

```bash
python3 $MAPS search "Eiffel Tower"
python3 $MAPS search "1600 Pennsylvania Ave, Washington DC"
```

Возвращает: широту, долготу, отображаемое название, тип, ограничивающий прямоугольник, оценку важности.

### reverse — Координаты в адрес

```bash
python3 $MAPS reverse 48.8584 2.2945
```

Возвращает: полное разбиение адреса (улица, город, штат, страна, почтовый индекс).

### nearby — Поиск мест по категории

```bash
# By coordinates (from a Telegram location pin, for example)
python3 $MAPS nearby 48.8584 2.2945 restaurant --limit 10
python3 $MAPS nearby 40.7128 -74.0060 hospital --radius 2000

# By address / city / zip / landmark — --near auto-geocodes
python3 $MAPS nearby --near "Times Square, New York" --category cafe
python3 $MAPS nearby --near "90210" --category pharmacy

# Multiple categories merged into one query
python3 $MAPS nearby --near "downtown austin" --category restaurant --category bar --limit 10
```

46 категорий: restaurant, cafe, bar, hospital, pharmacy, hotel, guest_house,
camp_site, supermarket, atm, gas_station, parking, museum, park, school,
university, bank, police, fire_station, library, airport, train_station,
bus_stop, church, mosque, synagogue, dentist, doctor, cinema, theatre, gym,
swimming_pool, post_office, convenience_store, bakery, bookshop, laundry,
car_wash, car_rental, bicycle_rental, taxi, veterinary, zoo, playground,
stadium, nightclub.

Каждый результат включает: `name`, `address`, `lat`/`lon`, `distance_m`,
`maps_url` (кликабельная ссылка Google Maps), `directions_url` (направления Google Maps от точки поиска) и продвигаемые теги, если доступны — `cuisine`, `hours` (opening_hours), `phone`, `website`.

### distance — Расстояние и время в пути

```bash
python3 $MAPS distance "Paris" --to "Lyon"
python3 $MAPS distance "New York" --to "Boston" --mode driving
python3 $MAPS distance "Big Ben" --to "Tower Bridge" --mode walking
```

Режимы: driving (по умолчанию), walking, cycling. Возвращает дорожное расстояние, продолжительность и прямое расстояние для сравнения.

### directions — Пошаговая навигация

```bash
python3 $MAPS directions "Eiffel Tower" --to "Louvre Museum" --mode walking
python3 $MAPS directions "JFK Airport" --to "Times Square" --mode driving
```

Возвращает нумерованные шаги с инструкцией, расстоянием, продолжительностью, названием дороги и типом манёвра (turn, depart, arrive и т.д.).

### timezone — Часовой пояс для координат

```bash
python3 $MAPS timezone 48.8584 2.2945
python3 $MAPS timezone 35.6762 139.6503
```

Возвращает название часового пояса, смещение UTC и текущее местное время.

### area — Ограничивающий прямоугольник и площадь для места

```bash
python3 $MAPS area "Manhattan, New York"
python3 $MAPS area "London"
```

Возвращает координаты ограничивающего прямоугольника, ширину/высоту в км и приблизительную площадь. Полезно как ввод для команды `bbox`.

### bbox — Поиск внутри ограничивающего прямоугольника

```bash
python3 $MAPS bbox 40.75 -74.00 40.77 -73.98 restaurant --limit 20
```

Ищет POI внутри географического прямоугольника. Сначала используйте `area`, чтобы получить координаты ограничивающего прямоугольника для названного места.

## Работа с pin‑ами местоположения Telegram

Когда пользователь отправляет pin местоположения, сообщение содержит поля `latitude:` и `longitude:`. Извлеките их и передайте напрямую в `nearby`:

```bash
# User sent a pin at 36.17, -115.14 and asked "find cafes nearby"
python3 $MAPS nearby 36.17 -115.14 cafe --radius 1500
```

Представляйте результаты в виде нумерованного списка с названиями, расстояниями и полем `maps_url`, чтобы пользователь получил ссылку, открывающуюся по нажатию в чате. Для вопросов типа «открыто сейчас?», проверяйте поле `hours`; если оно отсутствует или неясно, уточняйте с помощью `web_search`, так как часы OSM поддерживаются сообществом и не всегда актуальны.

## Примеры рабочих процессов

**«Найти итальянские рестораны рядом с Колизеем»:**
1. `nearby --near "Colosseum Rome" --category restaurant --radius 500` — одна команда, автогеокодирование

**«Что находится рядом с этим pin‑ом местоположения, который они отправили?»:**
1. Извлечь широту/долготу из сообщения Telegram
2. `nearby LAT LON cafe --radius 1500`

**«Как пройти пешком от отеля к конференц‑центру?»:**
1. `directions "Hotel Name" --to "Conference Center" --mode walking`

**«Какие рестораны находятся в центре Сиэтла?»:**
1. `area "Downtown Seattle"` → получить ограничивающий прямоугольник
2. `bbox S W N E restaurant --limit 30`

## Подводные камни

- ToS Nominatim: максимум 1 запрос/сек (обрабатывается автоматически скриптом)
- `nearby` требует широту/долготу ИЛИ `--near "<address>"` — необходимо одно из двух
- Покрытие маршрутизации OSRM лучше всего для Европы и Северной Америки
- Overpass API может работать медленно в часы пик; скрипт автоматически переключается между зеркалами (overpass-api.de → overpass.kumi.systems)
- `distance` и `directions` используют флаг `--to` для назначения (не позиционный аргумент)
- Если почтовый индекс сам по себе даёт неоднозначные результаты глобально, указывайте страну/штат

## Проверка

```bash
python3 ~/.hermes/skills/maps/scripts/maps_client.py search "Statue of Liberty"
# Should return lat ~40.689, lon ~-74.044

python3 ~/.hermes/skills/maps/scripts/maps_client.py nearby --near "Times Square" --category restaurant --limit 3
# Should return a list of restaurants within ~500m of Times Square
```