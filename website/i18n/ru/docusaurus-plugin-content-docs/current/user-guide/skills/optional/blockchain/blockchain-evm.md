---
title: "Evm — клиент EVM только для чтения: кошельки, токены, газ на 8 цепочках"
sidebar_label: "Evm"
description: "Клиент EVM только для чтения: кошельки, токены, газ на 8 цепочках"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Evm

Клиент EVM только для чтения: кошельки, токены, газ на 8 цепочках.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/blockchain/evm` |
| Path | `optional-skills/blockchain/evm` |
| Version | `1.0.0` |
| Author | Mibayy (@Mibayy), youssefea (@youssefea), ethernet8023 (@ethernet8023), Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `EVM`, `Ethereum`, `BNB`, `BSC`, `Base`, `Arbitrum`, `Polygon`, `Optimism`, `Avalanche`, `zkSync`, `Blockchain`, `Crypto`, `Web3`, `DeFi`, `NFT`, `ENS`, `Whale`, `Security` |
| Related skills | [`solana`](/docs/user-guide/skills/optional/blockchain/blockchain-solana) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при активном навыке.
:::

# EVM Blockchain Skill

Запрос данных совместимых с EVM блокчейнов на 8 цепочках с ценами в USD.
14 команд: портфолио кошелька, информация о токене, транзакции, активность, трекер газа, статистика сети, поиск цены, сканирование мультичейна, обнаружение китов, разрешение ENS, проверка разрешений, инспектор контрактов и декодер транзакций.

Поддерживает 8 цепочек: Ethereum, BNB Chain (BSC), Base, Arbitrum One, Polygon, Optimism, Avalanche (C‑Chain), zkSync Era.

Не требуется API‑ключ. Никаких внешних зависимостей — только стандартная библиотека Python (urllib, json, argparse, threading).

> **Заменяет отдельный навык `base`.** Токены, специфичные для Base (AERO, DEGEN, TOSHI, BRETT, WELL, cbETH, cbBTC, wstETH, rETH) и вся функциональность RPC Base, ранее находившиеся в `optional-skills/blockchain/base/`, теперь включены в этот навык. Передай `--chain base` любой команде для работы с Base.

---

## Когда использовать
- Пользователь запрашивает баланс или портфолио кошелька в любой цепочке EVM
- Пользователь хочет проверить один и тот же кошелек сразу на ВСЕХ цепочках
- Пользователь хочет просмотреть транзакцию по хэшу (или декодировать её)
- Пользователь хочет метаданные ERC‑20 токена, цену, эмиссию или рыночную капитализацию
- Пользователь хочет недавнюю историю транзакций для адреса
- Пользователь хочет текущие цены газа или сравнить комиссии между цепочками
- Пользователь хочет найти крупные переводы китов в последних блоках
- Пользователь запрашивает разрешение ENS‑имени (vitalik.eth) или обратный поиск адреса
- Пользователь хочет проверить, есть ли у контракта опасные одобрения токенов
- Пользователь хочет проанализировать смарт‑контракт (прокси? ERC‑20? ERC‑721? размер байткода?)
- Пользователь хочет сравнить затраты газа между цепочками перед отправкой транзакции

---

## Предварительные требования
Только стандартная библиотека Python 3.8+. Установка через pip не требуется.
Ценообразование: бесплатный API CoinGecko (ограничение по скорости, ~10‑30 запросов/мин).
ENS: публичный API ensideas.com.
Декодирование транзакций: публичный API 4byte.directory.

Переопределить RPC‑endpoint: `export EVM_RPC_URL=https://your-rpc.com`

Путь к вспомогательному скрипту: `~/.hermes/skills/blockchain/evm/scripts/evm_client.py`

---

## Быстрая справка

```
SCRIPT=~/.hermes/skills/blockchain/evm/scripts/evm_client.py

# Network & prices
python3 $SCRIPT stats                            # Ethereum stats
python3 $SCRIPT stats --chain arbitrum           # Arbitrum stats
python3 $SCRIPT compare                          # Gas + prices ALL 8 chains

# Wallet
python3 $SCRIPT wallet 0xd8dA...96045            # Portfolio (ETH + ERC-20)
python3 $SCRIPT wallet 0xd8dA...96045 --chain bsc
python3 $SCRIPT multichain 0xd8dA...96045        # Same wallet on ALL chains

# Tokens & prices
python3 $SCRIPT price ETH
python3 $SCRIPT price 0xdAC1...1ec7              # By contract address
python3 $SCRIPT token 0xdAC1...1ec7              # ERC-20 metadata + market cap

# Transactions
python3 $SCRIPT tx 0x5c50...f060                 # Transaction details
python3 $SCRIPT decode 0x5c50...f060             # Decode input data (4byte.directory)
python3 $SCRIPT activity 0xd8dA...96045          # Recent transactions

# Gas
python3 $SCRIPT gas                              # Gas prices + cost estimates
python3 $SCRIPT gas --chain optimism

# Security
python3 $SCRIPT allowance 0xd8dA...96045         # Dangerous ERC-20 approvals
python3 $SCRIPT contract 0xdAC1...1ec7           # Contract inspection (proxy? standards?)

# ENS
python3 $SCRIPT ens vitalik.eth                  # Name -> address + profile
python3 $SCRIPT ens 0xd8dA...96045               # Address -> ENS name

# Whale detection
python3 $SCRIPT whale                            # Large transfers (last 20 blocks, >$10k)
python3 $SCRIPT whale --blocks 50 --min-usd 100000 --chain arbitrum
```

---

## Процедура

### 0. Проверка настройки
```bash
python3 --version   # 3.8+ required
python3 ~/.hermes/skills/blockchain/evm/scripts/evm_client.py stats
```

### 1. Портфолио кошелька
Нативный баланс + известные ERC‑20 токены, отсортированные по стоимости в USD.
```bash
python3 $SCRIPT wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python3 $SCRIPT wallet 0xd8dA... --chain bsc --no-prices   # faster
```

### 2. Сканирование мультичейна
Одновременно сканирует все 8 цепочек для одного и того же адреса с помощью потоков.
```bash
python3 $SCRIPT multichain 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```
Вывод: нативный баланс по цепочке + токен‑холдинги + общий итог в USD.

### 3. Сравнение (газ + цены)
Все 8 цепочек запрашиваются параллельно. Показывает самую дешёвую и самую дорогую цепочку.
```bash
python3 $SCRIPT compare
```

### 4. Детали транзакции и декодирование
```bash
python3 $SCRIPT tx 0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060
python3 $SCRIPT decode 0x5c504ed...   # Shows human-readable function signature
```
Декодирование использует 4byte.directory для преобразования 0xa9059cbb → transfer(address,uint256).

### 5. Разрешение ENS
```bash
python3 $SCRIPT ens vitalik.eth          # -> 0xd8dA... + avatar + social links
python3 $SCRIPT ens 0xd8dA...96045       # -> vitalik.eth
```

### 6. Проверка разрешений (безопасность)
Проверяет одобрения ERC‑20, предоставленные известным DEX/мостовым контрактам.
```bash
python3 $SCRIPT allowance 0xYourWallet
```
Помечает НЕОГРАНИЧЕННЫЕ одобрения как высокий риск.

### 7. Инспектор контрактов
```bash
python3 $SCRIPT contract 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48   # USDC (proxy)
python3 $SCRIPT contract 0xdAC17F958D2ee523a2206206994597C13D831ec7   # USDT (ERC-20)
```
Обнаруживает: прокси (EIP‑1967/EIP‑1167), ERC‑20, ERC‑721, ERC‑165. Показывает размер байткода и адрес реализации для прокси.

### 8. Обнаружение китов
```bash
python3 $SCRIPT whale                                    # ETH, last 20 blocks, >$10k
python3 $SCRIPT whale --blocks 50 --min-usd 50000 --chain bsc
```

### 9. Трекер газа
```bash
python3 $SCRIPT gas
python3 $SCRIPT gas --chain polygon
```
Показывает цену в gwei + стоимость в USD для: обычный перевод, ERC‑20 перевод, approve, swap, mint NFT, перевод NFT.

---

## Поддерживаемые цепочки
| Key       | Name           | Native | Chain ID |
|-----------|----------------|--------|----------|
| ethereum  | Ethereum       | ETH    | 1        |
| bsc       | BNB Chain      | BNB    | 56       |
| base      | Base           | ETH    | 8453     |
| arbitrum  | Arbitrum One   | ETH    | 42161    |
| polygon   | Polygon        | POL    | 137      |
| optimism  | Optimism       | ETH    | 10       |
| avalanche | Avalanche C    | AVAX   | 43114    |
| zksync    | zkSync Era     | ETH    | 324      |

---

## Подводные камни
- Бесплатный тариф CoinGecko: ~10‑30 запросов/мин. Используй `--no-prices` для более быстрых сканирований кошельков.
- Публичные RPC могут ограничивать пропускную способность. Установи `EVM_RPC_URL` на приватный endpoint для продакшена.
- Команды `wallet` и `allowance` проверяют только известный список токенов (~30 токенов на цепочку). Для полного обнаружения токенов используй блок‑эксплорер.
- `activity` сканирует только последние блоки (максимум 200). Для полной истории используй API Etherscan.
- `multichain` запускает 8 параллельных потоков — может вызвать ограничения скорости на публичных RPC.
- Разрешение ENS зависит от единственного публичного эндпоинта (ensideas.com / ens.vitalik.ca) без резервных вариантов. Если он недоступен, `ens` завершится ошибкой — повтори позже или используй блок‑эксплорер.
- Декодирование транзакций зависит от единственного публичного эндпоинта (4byte.directory) без резервных вариантов. Селекторы, отсутствующие в их базе, отображаются как `unknown`.
- **Оценки газа L2 учитывают только выполнение на L2.** На ролапах типа Base, Arbitrum, Optimism и zkSync реальная стоимость транзакции также включает плату за запись данных в L1, зависящую от размера calldata и текущих цен газа в L1. Команда `gas` не оценивает эту L1‑компоненту. Для Base смотри оракул L1‑платы сети (контракт `0x420000000000000000000000000000000000000F`).
- Вводы адресов / хэшей транзакций проверяются на наличие префикса `0x`, правильную длину и шестнадцатеричный формат, но проверка контрольной суммы EIP‑55 **не** выполняется (RPC‑эндпоинты принимают любой регистр).

---

## Проверка
```bash
# Should print current block, gas price, ETH price
python3 ~/.hermes/skills/blockchain/evm/scripts/evm_client.py stats

# Should resolve vitalik.eth to 0xd8dA...
python3 ~/.hermes/skills/blockchain/evm/scripts/evm_client.py ens vitalik.eth
```