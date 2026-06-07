---
title: "Check Wallet — Check wallet balances and holdings"
sidebar_label: "Check Wallet"
description: "Check wallet balances and holdings"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Check Wallet

Check wallet balances and holdings. Use for "what's in my wallet", portfolio breakdown, token balances, allocation percentages, and USD values.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/moonpay/check-wallet` |
| Path | `optional-skills/moonpay/check-wallet` |
| Version | `0.1.0` |
| Author | MoonPay (tonyagents), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `MoonPay`, `Portfolio` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Check wallet

## Goal

List all token balances in a wallet with USD values, allocation breakdown, and total portfolio value.

## Commands

```bash
# List balances for a Solana wallet
mp token balance list --wallet <address> --chain solana

# List balances for an EVM wallet
mp token balance list --wallet 0x... --chain ethereum
mp token balance list --wallet 0x... --chain base

# Find wallet address
mp wallet list
```

## Supported chains

`solana`, `ethereum`, `base`, `polygon`, `arbitrum`, `optimism`, `bnb`, `avalanche`, `tron`, `bitcoin`, `ton`

Bitcoin uses a separate command: `mp bitcoin balance retrieve --wallet <btc-address>`

## Workflow

1. Run `mp wallet list` to find the user's wallet address.
2. Run `mp token balance list --wallet <address> --chain solana`.
3. Sort holdings by USD value descending.
4. Calculate allocation percentages (each holding's USD / total USD).
5. Present: top holdings, dust balances, total value.

## Example flow

1. User: "What's in my wallet?" or "Generate a portfolio report."
2. Run: `mp token balance list --wallet <address> --chain solana`
3. Present:
   - **Total value:** $168.05
   - **SOL** — 0.61 ($51.87) — 30.9%
   - **WBTC** — 0.00127 ($85.48) — 50.9%
   - **USDC** — 29.81 ($29.81) — 17.7%
   - **Dust:** none

## Output formats

Use `mp -f table token balance list ...` for a quick table view, or `mp -f json ...` for programmatic processing.

## Related skills

- **moonpay-auth** — Set up wallets if none exist.
- **moonpay-discover-tokens** — Research specific tokens in the portfolio.
- **moonpay-prediction-market** — Check prediction market positions and PnL.
