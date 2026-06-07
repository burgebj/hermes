---
title: "Polymarket Ready — Fund a Polygon wallet for Polymarket trading"
sidebar_label: "Polymarket Ready"
description: "Fund a Polygon wallet for Polymarket trading"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Polymarket Ready

Fund a Polygon wallet for Polymarket trading. Buy POL for gas and bridge or buy USDC.e so the wallet is ready to trade.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/moonpay/polymarket-ready` |
| Path | `optional-skills/moonpay/polymarket-ready` |
| Version | `0.1.0` |
| Author | MoonPay (tonyagents), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `MoonPay`, `Trading`, `Setup` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Polymarket ready

## Goal

Get a Polygon wallet funded with POL (gas) and USDC.e (trading) so it's ready for Polymarket.

Polymarket runs on Polygon. To trade, the user needs:
- **POL** — native gas token for transaction fees
- **USDC.e** (`0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`) — the token Polymarket uses for bets

## Key addresses

| Token | Chain | Address |
|-------|-------|---------|
| POL (native) | Polygon | `0x0000000000000000000000000000000000000000` |
| USDC.e | Polygon | `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` |
| ETH (native) | Ethereum | `0x0000000000000000000000000000000000000000` |

## Workflow

### 1. Check or create wallet

```bash
mp wallet list
```

The user's Polygon address is the same as their Ethereum address (EVM wallets share one address across all EVM chains).

If no wallets exist, create one:

```bash
mp wallet create --name main
```

### 2. Check existing Polygon balances

```bash
mp token balance list --wallet <eth-address> --chain polygon
```

If the wallet already has POL and USDC.e, they're set.

### 3. Get POL for gas

Buy POL directly with fiat — easiest way to get gas on Polygon:

```bash
mp buy --token pol_polygon --amount 5 --wallet <eth-address> --email <email>
```

Alternatively, bridge ETH → POL if the user already has ETH:

```bash
mp token bridge \
  --from-wallet <wallet-name> --from-chain ethereum \
  --from-token 0x0000000000000000000000000000000000000000 \
  --from-amount 0.001 \
  --to-chain polygon \
  --to-token 0x0000000000000000000000000000000000000000
```

~$2-5 worth of POL covers hundreds of transactions.

### 4. Get USDC.e for trading

Bridge ETH on Ethereum to USDC.e on Polygon in one step:

```bash
mp token bridge \
  --from-wallet <wallet-name> --from-chain ethereum \
  --from-token 0x0000000000000000000000000000000000000000 \
  --from-amount 0.005 \
  --to-chain polygon \
  --to-token 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
```

Alternatively, if the user already has USDC on Ethereum, bridge it directly:

```bash
mp token bridge \
  --from-wallet <wallet-name> --from-chain ethereum \
  --from-token 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 \
  --from-amount 10 \
  --to-chain polygon \
  --to-token 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
```

### 5. Verify

```bash
mp token balance list --wallet <eth-address> --chain polygon
```

Confirm both POL and USDC.e are present.

## Tips

- Bridge times from Ethereum → Polygon are typically 5-20 seconds
- POL is very cheap for gas — a few dollars covers hundreds of transactions
- The fiat buy option (`mp buy`) is the fastest path if the user has no crypto yet

## Related skills

- **moonpay-swap-tokens** — Bridge commands and supported chains
- **moonpay-check-wallet** — Check Polygon balances
- **moonpay-buy-crypto** — Buy POL or ETH with fiat
