---
title: "Buy Crypto — Buy crypto with fiat via MoonPay"
sidebar_label: "Buy Crypto"
description: "Buy crypto with fiat via MoonPay"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Buy Crypto

Buy crypto with fiat via MoonPay. Returns a checkout URL to complete the purchase in a browser.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/moonpay/buy-crypto` |
| Path | `optional-skills/moonpay/buy-crypto` |
| Version | `0.1.0` |
| Author | MoonPay (tonyagents), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `MoonPay`, `Trading` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Buy crypto with fiat

## Goal

Generate a MoonPay checkout URL for buying crypto with a credit card or bank transfer. The user completes the purchase in their browser.

## Command

```bash
mp buy \
  --token <currency-code> \
  --amount <usd-amount> \
  --wallet <destination-address> \
  --email <buyer-email>
```

## Supported tokens

`btc`, `sol`, `eth`, `trx`, `pol_polygon`, `usdc`, `usdc_sol`, `usdc_base`, `usdc_arbitrum`, `usdc_optimism`, `usdc_polygon`, `usdt_trx`, `eth_polygon`, `eth_optimism`, `eth_base`, `eth_arbitrum`

## Example flow

1. User: "I want to buy $50 of SOL with my credit card."
2. Run: `mp buy --token sol --amount 50 --wallet <address> --email user@example.com`
3. Open the returned checkout URL in the user's browser so they can complete the purchase.

## Notes

- This is fiat-to-crypto (credit card / bank), not a token swap.
- For token-to-token swaps, use the **moonpay-swap-tokens** skill instead.
- The `--amount` flag is in USD (e.g. `--amount 50` = $50 worth of the token).
- The `--token` flag uses MoonPay currency codes, not mint addresses.
- The checkout URL handles KYC and payment processing.

## Related skills

- **moonpay-swap-tokens** — Swap between tokens (no fiat).
- **moonpay-discover-tokens** — Search for tokens.
- **moonpay-auth** — Ensure user is logged in.
