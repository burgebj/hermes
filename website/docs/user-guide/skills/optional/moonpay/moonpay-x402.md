---
title: "X402 — Make paid API requests to x402-protected endpoints"
sidebar_label: "X402"
description: "Make paid API requests to x402-protected endpoints"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# X402

Make paid API requests to x402-protected endpoints. Automatically handles payment with your local wallet.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/moonpay/x402` |
| Path | `optional-skills/moonpay/x402` |
| Version | `0.1.0` |
| Author | MoonPay (tonyagents), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `MoonPay`, `Payments`, `API` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# x402 paid API requests

## Goal

Make HTTP requests to x402-protected endpoints. The CLI automatically detects 402 Payment Required responses, builds and signs a payment transaction with your local wallet, and retries the request with the payment proof.

## Command

```bash
mp x402 request \
  --method POST \
  --url <x402-endpoint-url> \
  --body '<json-body>' \
  --wallet <wallet-name-or-address> \
  --chain solana
```

## Available x402 endpoints

| Endpoint | Cost | Input |
|----------|------|-------|
| `https://agents.moonpay.com/x402/upgrade` | $1-$20 | `{"duration": "day"}` or `{"duration": "month"}` |

## Example flow

1. User: "Upgrade my rate limit for a day."
2. Run: `mp upgrade --duration day --wallet my-wallet --chain solana`
3. The CLI handles the 402 payment flow automatically and applies the upgrade.

## Notes

- Requires a local wallet with USDC on Solana or Base.
- Payments accepted on Solana mainnet and Base.
- If the request fails (status >= 400), the payment is not settled — you don't pay for errors.
- Use **moonpay-auth** to set up a local wallet first.

## Related skills

- **moonpay-auth** — Create or import a local wallet.
- **moonpay-check-wallet** — Check your wallet balance before making paid requests.
- **moonpay-upgrade** — Upgrade your rate limit via x402.
