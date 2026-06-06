---
title: "Solana"
sidebar_label: "Solana"
description: "Запит даних блокчейну Solana з цінами в USD — баланси гаманців, портфелі токенів зі значеннями, деталі транзакцій, NFT, виявлення китів та живий стан мережі..."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Solana

Запитуй дані блокчейну Solana з цінами в USD — баланси гаманців, портфелі токенів зі значеннями, деталі транзакцій, NFT, виявлення китів і живу статистику мережі. Використовує Solana RPC + CoinGecko. Ключ API не потрібен.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/blockchain/solana` |
| Path | `optional-skills/blockchain/solana` |
| Version | `0.2.0` |
| Author | Deniz Alagoz (gizdusum), enhanced by Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Solana`, `Blockchain`, `Crypto`, `Web3`, `RPC`, `DeFi`, `NFT` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Solana Blockchain Skill

Запитуй on-chain дані Solana, збагачені цінами в USD через CoinGecko.
8 команд: портфоліо гаманця, інформація про токен, транзакції, активність, NFT, виявлення китів, статистика мережі та пошук цін.

Ключ API не потрібен. Використовує лише стандартну бібліотеку Python (`urllib`, `json`, `argparse`).

---

## When to Use

- Користувач просить баланс гаманця Solana, токени або вартість портфеля
- Користувач хоче переглянути конкретну транзакцію за підписом
- Користувач хоче метадані SPL‑токену, ціну, емісію або топ‑власників
- Користувач хоче історію останніх транзакцій для адреси
- Користувач хоче NFT, що належать гаманцю
- Користувач хоче знайти великі перекази SOL (виявлення китів)
- Користувач хоче здоров’я мережі Solana, TPS, епоху або ціну SOL
- Користувач запитує «яка ціна BONK/JUP/SOL?»

---

## Prerequisites

Допоміжний скрипт використовує лише стандартну бібліотеку Python (`urllib`, `json`, `argparse`).
Зовнішніх пакетів не потрібно.

Дані про ціни беруться з безкоштовного API CoinGecko (ключ не потрібен, обмеження ≈ 10‑30 запитів/хвилину). Для швидших пошуків використай прапорець `--no-prices`.

---

## Quick Reference

RPC‑endpoint (за замовчуванням): https://api.mainnet-beta.solana.com
Перевизначення: `export SOLANA_RPC_URL=https://your-private-rpc.com`

Шлях до допоміжного скрипту: `~/.hermes/skills/blockchain/solana/scripts/solana_client.py`

```
python3 solana_client.py wallet   <address> [--limit N] [--all] [--no-prices]
python3 solana_client.py tx       <signature>
python3 solana_client.py token    <mint_address>
python3 solana_client.py activity <address> [--limit N]
python3 solana_client.py nft      <address>
python3 solana_client.py whales   [--min-sol N]
python3 solana_client.py stats
python3 solana_client.py price    <mint_or_symbol>
```

---

## Procedure

### 0. Setup Check

```bash
python3 --version

# Optional: set a private RPC for better rate limits
export SOLANA_RPC_URL="https://api.mainnet-beta.solana.com"

# Confirm connectivity
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py stats
```

### 1. Wallet Portfolio

Отримай баланс SOL, утримання SPL‑токенів з вартістю в USD, кількість NFT та загальну вартість портфеля. Токени сортуються за вартістю, пил (dust) фільтрується, відомі токени позначаються назвою (BONK, JUP, USDC тощо).

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  wallet 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
```

Flags:
- `--limit N` — показати топ‑N токенів (за замовчуванням: 20)
- `--all` — показати всі токени, без фільтрації пилу та без обмеження
- `--no-prices` — пропустити пошук цін у CoinGecko (швидше, лише RPC)

Вивід включає: баланс SOL + вартість в USD, список токенів з цінами, відсортованих за вартістю, кількість пилу, підсумок NFT, загальну вартість портфеля в USD.

### 2. Transaction Details

Переглянь повну транзакцію за її base58‑підписом. Показує зміни балансу в SOL і USD.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  tx 5j7s8K...your_signature_here
```

Вивід: slot, timestamp, fee, status, зміни балансу (SOL + USD), виклики програм.

### 3. Token Info

Отримай метадані SPL‑токену, поточну ціну, ринкову капіталізацію, емісію, кількість десяткових знаків, mint/freeze‑authorities та топ‑5 власників.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  token DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```

Вивід: назва, символ, decimals, supply, price, market cap, топ‑5 власників з відсотками.

### 4. Recent Activity

Список останніх транзакцій для адреси (за замовчуванням: останні 10, максимум 25).

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  activity 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM --limit 25
```

### 5. NFT Portfolio

Список NFT, що належать гаманцю (евристика: SPL‑токени з `amount=1`, `decimals=0`).

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  nft 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
```

Примітка: стиснені NFT (cNFTs) не виявляються цією евристикою.

### 6. Whale Detector

Сканує найновіший блок на предмет великих переказів SOL з вартістю в USD.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  whales --min-sol 500
```

Примітка: сканує лише останній блок — моментальний знімок, не історичний.

### 7. Network Stats

Жива статистика мережі Solana: поточний slot, epoch, TPS, supply, версія валідатора, ціна SOL і ринкова капіталізація.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py stats
```

### 8. Price Lookup

Швидка перевірка ціни будь‑якого токену за mint‑адресою або відомим символом.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price BONK
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price JUP
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price SOL
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```

Відомі символи: SOL, USDC, USDT, BONK, JUP, WETH, JTO, mSOL, stSOL, PYTH, HNT, RNDR, WEN, W, TNSR, DRIFT, bSOL, JLP, WIF, MEW, BOME, PENGU.

---

## Pitfalls

- **CoinGecko rate‑limits** — безкоштовний тариф дозволяє ~10‑30 запитів/хвилину. Пошук цін виконує 1 запит на токен. Гаманці з великою кількістю токенів можуть не отримати ціни для всіх. Використай `--no-prices` для швидкості.
- **Public RPC rate‑limits** — публічний RPC Solana mainnet обмежує кількість запитів. Для продакшн‑використання встанови `SOLANA_RPC_URL` на приватний endpoint (Helius, QuickNode, Triton).
- **NFT detection is heuristic** — `amount=1` + `decimals=0`. Стиснені NFT (cNFTs) та Token‑2022 NFT не будуть показані.
- **Whale detector scans latest block only** — не історичний. Результати залежать від моменту запиту.
- **Transaction history** — публічний RPC зберігає ~2 дні. Старіші транзакції можуть бути недоступні.
- **Token names** — ~25 добре відомих токенів позначені іменем. Інші показують скорочені mint‑адреси. Використай команду `token` для повної інформації.
- **Retry on 429** — і RPC, і виклики CoinGecko повторюються до 2 разів з експоненціальним бекоффом при помилках обмеження швидкості.

---

## Verification

```bash
# Should print current Solana slot, TPS, and SOL price
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py stats
```