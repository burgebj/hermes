---
title: "Hyperliquid — данные рынка Hyperliquid, история аккаунта, обзор сделок"
sidebar_label: "Hyperliquid"
description: "данные рынка Hyperliquid, история аккаунта, обзор сделок"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Hyperliquid

Данные рынка Hyperliquid, история аккаунта, обзор сделок.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/blockchain/hyperliquid` |
| Path | `optional-skills/blockchain/hyperliquid` |
| Version | `0.1.0` |
| Author | Hugo Sequier (Hugo-SEQUIER), Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Hyperliquid`, `Blockchain`, `Crypto`, `Trading`, `Perpetuals`, `Spot`, `DeFi` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Навык Hyperliquid

Запрашивает рыночные и аккаунтные данные Hyperliquid через публичный эндпоинт `/info`.
Только чтение — без API‑ключа, без подписи, без размещения ордеров.

12 команд: `dexs`, `markets`, `spots`, `candles`, `funding`, `l2`, `state`,
`spot-balances`, `fills`, `orders`, `review`, `export`. Только стандартная библиотека
(`urllib`, `json`, `argparse`).

---

## Когда использовать

- Пользователь запрашивает данные рынка perp или spot Hyperliquid, свечи, финансирование или книгу L2
- Пользователь хочет просмотреть позиции perp, балансы spot, заполнения или ордеры кошелька
- Пользователь хочет пост‑трейд обзор, комбинирующий последние заполнения с рыночным контекстом
- Пользователь хочет исследовать развернутые builder‑ом perp dex‑ы или рынки HIP‑3
- Пользователь хочет нормализованный JSON‑экспорт свечей + финансирования для подготовки бэктестинга

---

## Предварительные требования

Только стандартная библиотека — без внешних пакетов, без API‑ключа.

Скрипт читает `~/.hermes/.env` для двух необязательных значений по умолчанию:

- `HYPERLIQUID_API_URL` — по умолчанию `https://api.hyperliquid.xyz`. Установи
  `https://api.hyperliquid-testnet.xyz` для тестовой сети.
- `HYPERLIQUID_USER_ADDRESS` — адрес по умолчанию для `state`, `spot-balances`,
  `fills`, `orders` и `review`. Если не задан, передай адрес как первый
  позиционный аргумент.

Файл проекта `.env` в текущей рабочей директории учитывается как fallback для разработки.

Вспомогательный скрипт: `~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py`

---

## Как запустить

Запусти через инструмент `terminal`:

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py <command> [args]
```

Добавь `--json` к любой команде для машинно‑читаемого вывода.

---

## Быстрая справка

```bash
hyperliquid_client.py dexs
hyperliquid_client.py markets [--dex DEX] [--limit N] [--sort volume|oi|funding_abs|change_abs|name]
hyperliquid_client.py spots [--limit N]
hyperliquid_client.py candles <coin> [--interval 1h] [--hours 24] [--limit N]
hyperliquid_client.py funding <coin> [--hours 72] [--limit N]
hyperliquid_client.py l2 <coin> [--levels N]
hyperliquid_client.py state [address] [--dex DEX]
hyperliquid_client.py spot-balances [address] [--limit N]
hyperliquid_client.py fills [address] [--hours N] [--limit N] [--aggregate-by-time]
hyperliquid_client.py orders [address] [--limit N]
hyperliquid_client.py review [address] [--coin COIN] [--hours N] [--fills N]
hyperliquid_client.py export <coin> [--interval 1h] [--hours N] [--output PATH]
```

Для `state`, `spot-balances`, `fills`, `orders` и `review` адрес
необязателен, если `HYPERLIQUID_USER_ADDRESS` установлен в `~/.hermes/.env`.

---

## Процедура

### 1. Обнаружить DEX‑ы и рынки

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py dexs

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  markets --limit 15 --sort volume

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  spots --limit 15
```

- `--dex` применяется только к perp‑эндпоинтам; опусти для первого perp dex.
- Пары spot могут отображаться как `PURR/USDC` или алиасами вроде `@107`.
- Рынки HIP‑3 префиксируют монету dex‑ом, например `mydex:BTC`.

### 2. Получить исторические рыночные данные

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  candles BTC --interval 1h --hours 72 --limit 48

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  funding BTC --hours 168 --limit 30
```

Эндпоинты с диапазоном времени пагинируются. Для больших окон повторяй запрос с более поздним
`startTime` или используй `export` (см. ниже).

### 3. Просмотреть живую книгу ордеров

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  l2 BTC --levels 10
```

Используй, когда спрашивают о глубине книги, краткосрочной ликвидности или потенциальном рыночном воздействии большого ордера.

### 4. Обзор аккаунта

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  state 0xabc...

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  spot-balances
```

`state` возвращает позиции perp; `spot-balances` — инвентарь spot.
Используй их для вопросов «каковы мои позиции?», «что я держу?», «сколько можно вывести?».

### 5. Обзор заполнений и ордеров

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  fills 0xabc... --hours 72 --limit 25

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  orders --limit 25
```

### 6. Сгенерировать обзор сделки

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  review 0xabc... --hours 72 --fills 50

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  review --coin BTC --hours 168
```

Отчёт включает реализованный PnL, комиссии, количество побед/поражений, разбивку по монетам, рыночный тренд
и среднее финансирование для каждой торгуемой perp, а также эвристики (fee drag, концентрация, потери от контртренда).

Для более глубокого пост‑трейд анализа: начни с `review`, чтобы найти проблемные монеты
или окна → получи `fills` и `orders` за этот период → получи `candles`
и `funding` для каждой торгуемой монеты → оцени качество решения отдельно
от качества результата.

### 7. Экспортировать переиспользуемый набор данных

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  export BTC --interval 1h --hours 168 --output ./btc-1h-7d.json

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  export BTC --interval 15m --hours 72 --end-time-ms 1760000000000
```

JSON‑вывод содержит: версию схемы, метаданные источника, точный временной интервал,
нормализованные строки свечей, нормализованные строки финансирования, сводную статистику. Используй
`--end-time-ms` для воспроизводимых окон.

---

## Подводные камни

- Публичные эндпоинты информации ограничены по частоте запросов. Большие исторические запросы могут возвращать усечённые окна; повторяй с более поздними значениями `startTime`.
- `fills --hours ...` использует `userFillsByTime`, который показывает только недавнее скользящее окно — не полную архивную историю.
- `historicalOrders` возвращает только недавние ордеры; не полный экспорт.
- Команда `review` эвристическая. Она не может восстановить намерения, качество размещения ордеров или истинный проскальзывание только из заполнений.
- Команда `export` пишет нормализованный набор данных, а не движок бэктестинга. Тебе всё равно понадобится собственная модель проскальзывания/заполнения.
- Алиасы spot, такие как `@107`, являются валидными идентификаторами, даже если UI показывает более дружелюбное название.
- `l2` — снимок в конкретный момент времени, а не временной ряд.

---

## Проверка

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  markets --limit 5
```

Должен вывести топовые perp‑рынки Hyperliquid по 24‑часовому объёму номинального объёма.