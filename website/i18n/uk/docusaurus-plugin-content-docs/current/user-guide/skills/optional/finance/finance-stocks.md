---
title: "Акції — котирування, історія, пошук, порівняння, криптовалюти через Yahoo"
sidebar_label: "Stocks"
description: "Котирування акцій, історія, пошук, порівняння, крипто через Yahoo"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Акції

Котирування акцій, історія, пошук, порівняння, крипто через Yahoo.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/finance/stocks` |
| Path | `optional-skills/finance/stocks` |
| Version | `0.1.0` |
| Author | Mibay (Mibayy), Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Stocks`, `Finance`, `Market`, `Crypto`, `Investing` |
| Related skills | [`dcf-model`](/docs/user-guide/skills/optional/finance/finance-dcf-model), [`comps-analysis`](/docs/user-guide/skills/optional/finance/finance-comps-analysis), [`lbo-model`](/docs/user-guide/skills/optional/finance/finance-lbo-model) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Навичка Stocks

Дані ринку лише для читання через Yahoo Finance. П’ять команд: `quote`, `search`,
`history`, `compare`, `crypto`. Тільки стандартна бібліотека Python 3.8+ — без API‑ключа, без встановлення пакетів. Точка доступу Yahoo неофіційна і може мати обмеження швидкості або змінюватися.

## Коли використовувати

- Користувач запитує поточну ціну акції (AAPL, TSLA, MSFT, …)
- Користувач хоче знайти тикер за назвою компанії
- Користувач потребує історію OHLCV або показники за певний діапазон дат
- Користувач хоче порівняти кілька тикерів поруч
- Користувач запитує ціну криптовалюти (BTC, ETH, SOL, …)

## Передумови

Тільки стандартна бібліотека Python 3.8+. За бажанням: встановити `ALPHA_VANTAGE_KEY` для збагачення
`market_cap`, `pe_ratio` та 52‑тижневих рівнів, коли поля Yahoo, захищені crumb, повертаються `null`. Безкоштовний ключ: https://www.alphavantage.co/support/#api-key

## Як запустити

Використовуй інструмент `terminal`. Після встановлення:

```
SCRIPT=~/.hermes/skills/finance/stocks/scripts/stocks_client.py
python3 $SCRIPT quote AAPL
```

Увесь вивід — JSON у stdout — можеш передати через `jq`, якщо потрібно відфільтрувати.

## Швидка довідка

```
python3 $SCRIPT quote AAPL
python3 $SCRIPT quote AAPL MSFT GOOGL TSLA
python3 $SCRIPT search "Tesla"
python3 $SCRIPT history NVDA --range 6mo
python3 $SCRIPT compare AAPL MSFT GOOGL
python3 $SCRIPT crypto BTC ETH SOL
```

## Команди

### `quote SYMBOL [SYMBOL2 ...]`

Поточна ціна, зміна, зміна %, обсяг, 52‑тижневий максимум/мінімум.

### `search QUERY`

Знаходить тикери за назвою компанії. Повертає топ‑5: символ, назва, біржа, тип.

### `history SYMBOL [--range RANGE]`

Денна OHLCV плюс статистика (мін., макс., серед., загальна прибутковість %). Діапазони: `1mo`,
`3mo`, `6mo`, `1y`, `5y`. За замовчуванням: `1mo`.

### `compare SYMBOL1 SYMBOL2 [...]`

Порівняння поруч: ціна, зміна %, 52‑тижнева прибутковість.

### `crypto SYMBOL [SYMBOL2 ...]`

Ціни криптовалют. Передай `BTC` (скрипт автоматично додає `-USD`).

## Підводні камені

- API Yahoo Finance неофіційне. Точки доступу можуть змінюватися або вводити обмеження швидкості без попередження — якщо запити починають падати, це причина.
- `market_cap` і `pe_ratio` можуть повертати `null` у `quote`, коли сесія crumb Yahoo не встановлена. Встанови `ALPHA_VANTAGE_KEY` для заповнення.
- Додай невелику затримку між масовими запитами, щоб уникнути обмежень швидкості.
- Це лише читання — без розміщення ордерів, без інтеграції облікових записів.

## Перевірка

```
python3 ~/.hermes/skills/finance/stocks/scripts/stocks_client.py quote AAPL
```

Повертає JSON‑об’єкт з `symbol: "AAPL"` та числовим полем `price`.