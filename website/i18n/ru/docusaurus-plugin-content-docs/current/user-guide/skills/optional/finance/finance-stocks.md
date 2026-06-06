---
title: "Акции — котировки, история, поиск, сравнение, криптовалюты через Yahoo"
sidebar_label: "Stocks"
description: "Котировки акций, история, поиск, сравнение, криптовалюты через Yahoo"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Акции

Котировки акций, история, поиск, сравнение, криптовалюты через Yahoo.

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Навык Stocks

Только для чтения: рыночные данные через Yahoo Finance. Пять команд: `quote`, `search`, `history`, `compare`, `crypto`. Только стандартная библиотека Python — без API‑ключа, без установки pip. Точка доступа Yahoo неофициальна и может ограничивать запросы или изменяться.

## Когда использовать

- Пользователь запрашивает текущую цену акции (AAPL, TSLA, MSFT, …)
- Пользователь хочет найти тикер по названию компании
- Пользователь хочет историю OHLCV или показатели за диапазон дат
- Пользователь хочет сравнить несколько тикеров рядом
- Пользователь запрашивает цену криптовалюты (BTC, ETH, SOL, …)

## Предварительные требования

Только стандартная библиотека Python 3.8+. Опционально: установить `ALPHA_VANTAGE_KEY` для обогащения `market_cap`, `pe_ratio` и уровней за 52 недели, когда поля Yahoo, защищённые crumb, возвращают null. Бесплатный ключ: https://www.alphavantage.co/support/#api-key

## Как запустить

Запусти через инструмент `terminal`. После установки:

```
SCRIPT=~/.hermes/skills/finance/stocks/scripts/stocks_client.py
python3 $SCRIPT quote AAPL
```

Весь вывод — JSON в stdout — можешь пропустить через `jq`, если нужно отфильтровать.

## Быстрая справка

```
python3 $SCRIPT quote AAPL
python3 $SCRIPT quote AAPL MSFT GOOGL TSLA
python3 $SCRIPT search "Tesla"
python3 $SCRIPT history NVDA --range 6mo
python3 $SCRIPT compare AAPL MSFT GOOGL
python3 $SCRIPT crypto BTC ETH SOL
```

## Команды

### `quote SYMBOL [SYMBOL2 ...]`

Текущая цена, изменение, изменение %, объём, максимум/минимум за 52 недели.

### `search QUERY`

Найти тикеры по названию компании. Возвращает топ‑5: символ, название, биржа, тип.

### `history SYMBOL [--range RANGE]`

Ежедневные OHLCV плюс статистика (min, max, avg, общий доход %). Диапазоны: `1mo`, `3mo`, `6mo`, `1y`, `5y`. По умолчанию: `1mo`.

### `compare SYMBOL1 SYMBOL2 [...]`

Сравнение рядом: цена, изменение %, результат за 52 недели.

### `crypto SYMBOL [SYMBOL2 ...]`

Цены криптовалют. Передай `BTC` (скрипт автоматически добавит `-USD`).

## Подводные камни

- API Yahoo Finance неофициально. Точки доступа могут измениться или ограничить запросы без предупреждения — если запросы начинают падать, это причина.
- `market_cap` и `pe_ratio` могут возвращать null в `quote`, когда сессия crumb Yahoo не установлена. Установи `ALPHA_VANTAGE_KEY` для заполнения.
- Добавь небольшую задержку между массовыми запросами, чтобы избежать ограничения частоты.
- Это только чтение — без размещения ордеров, без интеграции аккаунтов.

## Проверка

```
python3 ~/.hermes/skills/finance/stocks/scripts/stocks_client.py quote AAPL
```

Возвращает объект JSON с `symbol: "AAPL"` и числовым полем `price`.