---
title: "Hyperliquid — дані ринку Hyperliquid, історія акаунту, огляд торгів"
sidebar_label: "Hyperliquid"
description: "Дані ринку Hyperliquid, історія акаунту, огляд торгів"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Hyperliquid

Hyperliquid market data, account history, trade review.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/blockchain/hyperliquid` |
| Path | `optional-skills/blockchain/hyperliquid` |
| Version | `0.1.0` |
| Author | Hugo Sequier (Hugo-SEQUIER), Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Hyperliquid`, `Blockchain`, `Crypto`, `Trading`, `Perpetuals`, `Spot`, `DeFi` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Навичка Hyperliquid

Запитуй дані ринку та акаунту Hyperliquid через публічний `/info` endpoint.
Тільки для читання — без API‑ключа, без підпису, без розміщення ордерів.

12 команд: `dexs`, `markets`, `spots`, `candles`, `funding`, `l2`, `state`,
`spot-balances`, `fills`, `orders`, `review`, `export`. Тільки стандартна бібліотека
(`urllib`, `json`, `argparse`).

---

## Коли використовувати

- Користувач запитує дані ринку perp або spot Hyperliquid, свічки, фінансування або книгу L2
- Користувач хоче переглянути perp‑позиції гаманця, spot‑баланси, заповнення або ордери
- Користувач хоче пост‑трейд огляд, що поєднує останні заповнення з контекстом ринку
- Користувач хоче переглянути builder‑розгорнуті perp dex‑и або HIP‑3 ринки
- Користувач хоче нормалізований JSON‑експорт свічок + фінансування для підготовки бек‑тестування

---

## Передумови

Тільки стандартна бібліотека — без зовнішніх пакетів, без API‑ключа.

Скрипт читає `~/.hermes/.env` для двох необов’язкових значень за замовчуванням:

- `HYPERLIQUID_API_URL` — за замовчуванням `https://api.hyperliquid.xyz`. Встанови
  `https://api.hyperliquid-testnet.xyz` для тестової мережі.
- `HYPERLIQUID_USER_ADDRESS` — адреса за замовчуванням для `state`, `spot-balances`,
  `fills`, `orders` та `review`. Якщо не задано, передай адресу як перший позиційний аргумент.

Файл проекту `.env` у поточному робочому каталозі використовується як fallback для розробки.

Допоміжний скрипт: `~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py`

---

## Як запустити

Використай інструмент `terminal`:

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py <command> [args]
```

Додай `--json` до будь‑якої команди для машинного виводу.

---

## Швидка довідка

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

Для `state`, `spot-balances`, `fills`, `orders` та `review` адреса
необов’язкова, якщо `HYPERLIQUID_USER_ADDRESS` встановлено у `~/.hermes/.env`.

---

## Процедура

### 1. Відкриття DEX‑ів та ринків

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py dexs

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  markets --limit 15 --sort volume

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  spots --limit 15
```

- `--dex` застосовується лише до perp‑endpoint‑ів; пропусти його для першого perp dex.
- Spot‑пари можуть відображатися як `PURR/USDC` або як псевдоніми типу `@107`.
- HIP‑3 ринки мають префікс монети з dex, напр. `mydex:BTC`.

### 2. Завантаження історичних даних ринку

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  candles BTC --interval 1h --hours 72 --limit 48

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  funding BTC --hours 168 --limit 30
```

Endpoints з діапазоном часу пагінуються. Для великих вікон повторюй запит з пізнішим
`startTime` або використай `export` (нижче).

### 3. Перегляд живої книги ордерів

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  l2 BTC --levels 10
```

Використовуй, коли запитують глибину книги, короткострокову ліквідність або потенційний ринковий вплив великого ордеру.

### 4. Огляд акаунту

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  state 0xabc...

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  spot-balances
```

`state` повертає perp‑позиції; `spot-balances` повертає spot‑інвентар.
Використовуй це для «які у мене позиції?», «що я тримаю?», «скільки можна вивести?».

### 5. Огляд заповнень та ордерів

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  fills 0xabc... --hours 72 --limit 25

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  orders --limit 25
```

### 6. Генерація трейд‑огляду

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  review 0xabc... --hours 72 --fills 50

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  review --coin BTC --hours 168
```

Звітує про реалізований PnL, комісії, кількість виграшів/програшів, розподіл монет, ринковий тренд
та середнє фінансування для кожного торгованого perp, плюс евристики (витрати на комісію,
концентрація, втрати проти тренду).

Для глибшого пост‑трейд аналізу: спочатку запусти `review`, щоб знайти проблемні монети
або вікна → отримай `fills` та `orders` за цей період → отримай `candles`
і `funding` для кожної торгованої монети → оцінюй якість рішення окремо від якості результату.

### 7. Експорт повторно використовуваного набору даних

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  export BTC --interval 1h --hours 168 --output ./btc-1h-7d.json

python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  export BTC --interval 15m --hours 72 --end-time-ms 1760000000000
```

Вихідний JSON містить: версію схеми, метадані джерела, точний часовий інтервал,
нормалізовані рядки свічок, нормалізовані рядки фінансування, підсумкову статистику. Використовуй
`--end-time-ms` для відтворюваних вікон.

---

## Підводні камені

- Публічні info‑endpoint‑и мають обмеження швидкості. Великі історичні запити можуть
  повертати обмежені вікна; ітеруй з пізнішими значеннями `startTime`.
- `fills --hours ...` використовує `userFillsByTime`, який показує лише
  недавнє ковзне вікно — не всю історію архіву.
- `historicalOrders` повертає лише недавні ордери; не повний експорт.
- Команда `review` є евристичною. Вона не може відтворити намір,
  якість розміщення ордеру або реальне прослизання лише з заповнень.
- Команда `export` записує нормалізований набір даних, а не бек‑тестовий движок. Ти все ще потребуєш власну модель прослизання/заповнення.
- Spot‑псевдоніми типу `@107` є дійсними ідентифікаторами, навіть коли UI показує більш дружню назву.
- `l2` — це знімок у певний момент часу, а не часовий ряд.

---

## Перевірка

```bash
python3 ~/.hermes/skills/blockchain/hyperliquid/scripts/hyperliquid_client.py \
  markets --limit 5
```

Повинно вивести топові perp‑ринки Hyperliquid за 24‑годинним об’ємом нотіоналу.