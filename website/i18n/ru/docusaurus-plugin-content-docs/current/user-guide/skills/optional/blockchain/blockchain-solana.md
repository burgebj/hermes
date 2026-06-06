---
title: "Solana"
sidebar_label: "Solana"
description: "Запрос данных блокчейна Solana с указанием цен в USD — балансы кошельков, портфели токенов со стоимостью, детали транзакций, NFT, обнаружение китов и живой статус сети…"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Solana

Запрашивай данные блокчейна Solana с ценами в USD — балансы кошельков, портфели токенов со стоимостью, детали транзакций, NFT, обнаружение крупных переводов и живую статистику сети. Использует Solana RPC + CoinGecko. Ключ API не требуется.

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
Ниже полное определение навыка, которое Hermes загружает, когда навык активирован. Это то, что агент видит как инструкции при работе навыка.
:::

# Solana Blockchain Skill

Запрашивай данные Solana on-chain, обогащённые ценами в USD через CoinGecko.
8 команд: портфель кошелька, информация о токене, транзакции, активность, NFT, обнаружение крупных переводов, статистика сети и поиск цены.

Ключ API не нужен. Использует только стандартную библиотеку Python (urllib, json, argparse).

---

## When to Use

- Пользователь запрашивает баланс кошелька Solana, токенов или стоимость портфеля
- Пользователь хочет просмотреть конкретную транзакцию по подписи
- Пользователь хочет метаданные SPL‑токена, цену, эмиссию или топ‑держателей
- Пользователь хочет недавнюю историю транзакций для адреса
- Пользователь хочет NFT, принадлежащие кошельку
- Пользователь хочет найти крупные переводы SOL (обнаружение китов)
- Пользователь хочет состояние сети Solana, TPS, эпоху или цену SOL
- Пользователь спрашивает «какова цена BONK/JUP/SOL?»

---

## Prerequisites

Вспомогательный скрипт использует только стандартную библиотеку Python (urllib, json, argparse).
Внешних пакетов не требуется.

Данные о ценах берутся из бесплатного API CoinGecko (ключ не нужен, ограничение ≈ 10‑30 запросов/минуту). Для более быстрых запросов используй флаг `--no-prices`.

---

## Quick Reference

RPC‑endpoint (по умолчанию): https://api.mainnet-beta.solana.com
Переопределить: export SOLANA_RPC_URL=https://your-private-rpc.com

Путь к вспомогательному скрипту: ~/.hermes/skills/blockchain/solana/scripts/solana_client.py

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

Получить баланс SOL, holdings SPL‑токенов с ценами в USD, количество NFT и общую стоимость портфеля. Токены сортируются по стоимости, пыль отфильтрована, известные токены помечены именем (BONK, JUP, USDC и т.д.).

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  wallet 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
```

Флаги:
- `--limit N` — показать топ‑N токенов (по умолчанию: 20)
- `--all` — показать все токены, без фильтра пыли и без ограничения
- `--no-prices` — пропустить запросы цен к CoinGecko (быстрее, только RPC)

Вывод включает: баланс SOL + USD, список токенов с ценами, отсортированный по стоимости, количество пыли, сводка NFT, общая стоимость портфеля в USD.

### 2. Transaction Details

Просмотреть полную транзакцию по её base58‑подписи. Показывает изменения баланса как в SOL, так и в USD.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  tx 5j7s8K...your_signature_here
```

Вывод: слот, метка времени, комиссия, статус, изменения баланса (SOL + USD), вызовы программ.

### 3. Token Info

Получить метаданные SPL‑токена, текущую цену, рыночную капитализацию, эмиссию, количество десятичных знаков, полномочия mint/freeze и топ‑5 держателей.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  token DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```

Вывод: название, символ, десятичные знаки, эмиссия, цена, рыночная капитализация, топ‑5 держателей с процентами.

### 4. Recent Activity

Список недавних транзакций для адреса (по умолчанию: последние 10, максимум: 25).

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  activity 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM --limit 25
```

### 5. NFT Portfolio

Список NFT, принадлежащих кошельку (эвристика: SPL‑токены с amount=1, decimals=0).

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  nft 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
```

Примечание: сжатые NFT (cNFT) этой эвристикой не обнаруживаются.

### 6. Whale Detector

Сканировать самый последний блок на предмет крупных переводов SOL с указанием стоимости в USD.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py \
  whales --min-sol 500
```

Примечание: сканируется только последний блок — моментальный снимок, без исторических данных.

### 7. Network Stats

Живая статистика сети Solana: текущий слот, эпоха, TPS, эмиссия, версия валидатора, цена SOL и рыночная капитализация.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py stats
```

### 8. Price Lookup

Быстрый запрос цены любого токена по mint‑адресу или известному символу.

```bash
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price BONK
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price JUP
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price SOL
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py price DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```

Известные символы: SOL, USDC, USDT, BONK, JUP, WETH, JTO, mSOL, stSOL, PYTH, HNT, RNDR, WEN, W, TNSR, DRIFT, bSOL, JLP, WIF, MEW, BOME, PENGU.

---

## Pitfalls

- **Ограничения CoinGecko** — бесплатный тариф позволяет ~10‑30 запросов/минуту. Запросы цен используют 1 запрос на токен. В кошельках с большим количеством токенов цены могут не быть получены для всех. Используй `--no-prices` для ускорения.
- **Ограничения публичного RPC** — публичный RPC Solana mainnet ограничивает количество запросов. Для продакшна укажи SOLANA_RPC_URL на приватный endpoint (Helius, QuickNode, Triton).
- **Обнаружение NFT — эвристика** — amount=1 + decimals=0. Сжатые NFT (cNFT) и NFT Token‑2022 не будут отображаться.
- **Whale detector сканирует только последний блок** — не исторические данные. Результаты зависят от момента запроса.
- **История транзакций** — публичный RPC хранит ~2 дня. Более старые транзакции могут быть недоступны.
- **Имена токенов** — ~25 популярных токенов помечаются по имени. Остальные показывают сокращённые mint‑адреса. Используй команду `token` для полной информации.
- **Повторные попытки при 429** — как RPC, так и запросы к CoinGecko повторяют до 2 раз с экспоненциальным бэкофом при ошибках ограничения.

---

## Verification

```bash
# Should print current Solana slot, TPS, and SOL price
python3 ~/.hermes/skills/blockchain/solana/scripts/solana_client.py stats
```