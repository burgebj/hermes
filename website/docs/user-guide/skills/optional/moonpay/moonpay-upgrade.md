---
title: "Upgrade — Increase your MoonPay API rate limit by paying with crypto via x402"
sidebar_label: "Upgrade"
description: "Increase your MoonPay API rate limit by paying with crypto via x402"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Upgrade

Increase your MoonPay API rate limit by paying with crypto via x402.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/moonpay/upgrade` |
| Path | `optional-skills/moonpay/upgrade` |
| Version | `0.1.0` |
| Author | MoonPay (tonyagents), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `MoonPay`, `Payments` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Upgrade Rate Limit

Increase your MoonPay API rate limit by paying with crypto via x402.

## Options

| Duration | Length | Price |
|----------|--------|-------|
| day | 24 hours | $1 USDC |
| month | 30 days | $20 USDC |

## Usage

```bash
# Upgrade for 24 hours ($1 USDC)
mp upgrade --duration day --wallet <wallet-name> --chain solana

# Upgrade for 30 days ($20 USDC)
mp upgrade --duration month --wallet <wallet-name> --chain base
```

## Requirements

- Must be logged in (`mp login`)
- Need a funded local wallet with USDC on Solana or Base
- Payment is handled automatically via x402

## How It Works

1. Run `mp upgrade` with your duration, wallet, and chain
2. x402 automatically pays from your local wallet
3. Your rate limit is increased immediately
4. Upgrades stack — buying again extends your expiry

## Check Status

Run `mp user retrieve` to see your current `upgradeExpiresAt`.
