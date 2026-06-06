---
title: "Evm — клієнт EVM лише для читання: гаманці, токени, газ у 8 ланцюгах"
sidebar_label: "Evm"
description: "Клієнт EVM лише для читання: гаманці, токени, газ на 8 ланцюгах"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# EVM

Клієнт EVM лише для читання: гаманці, токени, газ на 8 ланцюгах.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Навичка блокчейну EVM

Запит даних блокчейну, сумісного з EVM, на 8 ланцюгах з цінами в USD.
14 команд: портфоліо гаманця, інформація про токен, транзакції, активність, трекер газу, статистика мережі, пошук цін, сканування мульти‑ланцюга, виявлення китів, розв’язання ENS, перевірка дозволів, інспектор контракту та декодер транзакцій.

Підтримує 8 ланцюгів: Ethereum, BNB Chain (BSC), Base, Arbitrum One, Polygon, Optimism, Avalanche (C‑Chain), zkSync Era.

Не потрібен API‑ключ. Нуль зовнішніх залежностей — лише стандартна бібліотека Python (urllib, json, argparse, threading).

> **Замінює автономну навичку `base`.** Токени, специфічні для Base (AERO, DEGEN, TOSHI, BRETT, WELL, cbETH, cbBTC, wstETH, rETH) та вся функціональність RPC Base, раніше розташовані в `optional-skills/blockchain/base/`, включені в цю навичку. Передай `--chain base` будь‑якій команді для охоплення Base.

---

## Коли використовувати
- Користувач запитує баланс або портфоліо гаманця на будь‑якому ланцюзі EVM
- Користувач хоче перевірити один і той самий гаманець на ВСІХ ланцюгах одночасно
- Користувач хоче проаналізувати транзакцію за хешем (або декодувати, що вона робила)
- Користувач хоче метадані, ціну, емісію або ринкову капіталізацію ERC‑20 токену
- Користувач хоче історію останніх транзакцій для адреси
- Користувач хоче поточні ціни газу або порівняти комісії між ланцюгами
- Користувач хоче знайти великі переміщення токенів (кити) у недавніх блоках
- Користувач запитує розв’язання ENS‑імені (vitalik.eth) або зворотний пошук адреси
- Користувач хоче перевірити, чи контракт має небезпечні дозволи токенів
- Користувач хоче проаналізувати смарт‑контракт (проксі? ERC‑20? ERC‑721? розмір байткоду?)
- Користувач хоче порівняти витрати газу між ланцюгами перед транзакцією

---

## Передумови
Стандартна бібліотека Python 3.8+ без додаткових pip‑встановлень.
Ціноутворення: безкоштовний API CoinGecko (обмеження швидкості, ~10‑30 запитів/хв).
ENS: публічний API ensideas.com.
Декодування транзакцій: публічний API 4byte.directory.

Перевизначення RPC‑endpoint: `export EVM_RPC_URL=https://your-rpc.com`

Шлях до допоміжного скрипту: `~/.hermes/skills/blockchain/evm/scripts/evm_client.py`

---

## Швидка довідка

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

### 0. Перевірка налаштувань
```bash
python3 --version   # 3.8+ required
python3 ~/.hermes/skills/blockchain/evm/scripts/evm_client.py stats
```

### 1. Портфоліо гаманця
Нативний баланс + відомі ERC‑20 токени, відсортовано за вартістю в USD.
```bash
python3 $SCRIPT wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
python3 $SCRIPT wallet 0xd8dA... --chain bsc --no-prices   # faster
```

### 2. Сканування мульти‑ланцюга
Сканує всі 8 ланцюгів одночасно для однієї адреси за допомогою потоків.
```bash
python3 $SCRIPT multichain 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```
Вивід: нативний баланс per‑chain + токен‑вкладення + загальна сума в USD.

### 3. Порівняння (газ + ціни)
Запит усіх 8 ланцюгів паралельно. Показує найдешевший/найдорожчий ланцюг.
```bash
python3 $SCRIPT compare
```

### 4. Деталі транзакції та декодування
```bash
python3 $SCRIPT tx 0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060
python3 $SCRIPT decode 0x5c504ed...   # Shows human-readable function signature
```
Декодування використовує 4byte.directory для перетворення 0xa9059cbb → transfer(address,uint256).

### 5. Розв’язання ENS
```bash
python3 $SCRIPT ens vitalik.eth          # -> 0xd8dA... + avatar + social links
python3 $SCRIPT ens 0xd8dA...96045       # -> vitalik.eth
```

### 6. Перевірка дозволів (безпека)
Перевіряє ERC‑20 дозволи, надані відомим DEX/bridge‑контрактам.
```bash
python3 $SCRIPT allowance 0xYourWallet
```
Позначає НЕОБМЕЖЕНІ дозволи як ВИСОКИЙ ризик.

### 7. Інспектор контракту
```bash
python3 $SCRIPT contract 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48   # USDC (proxy)
python3 $SCRIPT contract 0xdAC17F958D2ee523a2206206994597C13D831ec7   # USDT (ERC-20)
```
Виявляє: проксі (EIP‑1967/EIP‑1167), ERC‑20, ERC‑721, ERC‑165. Показує розмір байткоду та адресу реалізації для проксі.

### 8. Виявлення китів
```bash
python3 $SCRIPT whale                                    # ETH, last 20 blocks, >$10k
python3 $SCRIPT whale --blocks 50 --min-usd 50000 --chain bsc
```

### 9. Трекер газу
```bash
python3 $SCRIPT gas
python3 $SCRIPT gas --chain polygon
```
Показує ціну в gwei + вартість в USD для: transfer, ERC‑20 transfer, approve, swap, NFT mint, NFT transfer.

---

## Підтримувані ланцюги
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

## Підводні камені
- Безкоштовний тариф CoinGecko: ~10‑30 запитів/хв. Використовуй `--no-prices` для швидшого сканування гаманців.
- Публічні RPC можуть обмежувати швидкість. Встанови `EVM_RPC_URL` на приватний endpoint для продакшну.
- `wallet` і `allowance` перевіряють лише відомий список токенів (~30 токенів на ланцюг). Для повного виявлення токенів користуйся block explorer.
- `activity` сканує лише недавні блоки (макс 200). Для повної історії використай API Etherscan.
- `multichain` запускає 8 паралельних потоків — може викликати обмеження швидкості на публічних RPC.
- Розв’язання ENS залежить від одного публічного endpoint (ensideas.com / ens.vitalik.ca) без резервного варіанту. Якщо він недоступний, `ens` завершиться помилкою — спробуй пізніше або використай block explorer.
- Декодування транзакцій залежить від одного публічного endpoint (4byte.directory) без резервного варіанту. Селектори, яких немає в їхній базі, позначаються як `unknown`.
- **Оцінки газу L2 — лише L2‑виконання.** На ролапах типу Base, Arbitrum, Optimism та zkSync фактична вартість транзакції включає додаткову L1‑комісію за розміщення даних, що залежить від розміру calldata та поточних цін газу L1. Команда `gas` не оцінює цей L1‑компонент. Для Base дивись оракул L1‑комісії мережі (контракт `0x420000000000000000000000000000000000000F`).
- Вхідні дані адрес/хешів транзакцій перевіряються на префікс `0x`, правильну довжину та шістнадцятковий формат, але контроль суми EIP‑55 **не** застосовується (RPC‑endpoint приймає будь‑який регістр).

---

## Перевірка
```bash
# Should print current block, gas price, ETH price
python3 ~/.hermes/skills/blockchain/evm/scripts/evm_client.py stats

# Should resolve vitalik.eth to 0xd8dA...
python3 ~/.hermes/skills/blockchain/evm/scripts/evm_client.py ens vitalik.eth
```