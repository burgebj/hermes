---
title: "X402 Analyst"
sidebar_label: "X402 Analyst"
description: "Research agent that pays for real-time market intelligence via x402 APIs, synthesizes a trade recommendation, and optionally executes it"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# X402 Analyst

Research agent that pays for real-time market intelligence via x402 APIs, synthesizes a trade recommendation, and optionally executes it. Total cost per research run: $0.03.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/moonpay/x402-analyst` |
| Path | `optional-skills/moonpay/x402-analyst` |
| Version | `0.1.0` |
| Author | MoonPay (tonyagents), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `MoonPay`, `Research`, `Trading`, `x402`, `Payments` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# x402 Market Research Agent

## Goal

The agent pays for real-time intelligence before trading — not for free data, but for the best data. Three API calls at $0.01 each: market overview, token deep-dive, trending pools. Agent synthesizes, recommends, executes.

**Total cost per research run: $0.03 USDC**

This is what "agents pay for their own brain" looks like.

## Demo flow

```
User: "Research the Solana market and tell me the best trade right now"

→ Agent pays $0.01 → MoonPay market digest (top movers, volume, sentiment)
→ Agent pays $0.01 → MoonPay token digest on top opportunity found
→ Agent pays $0.01 → CoinGecko trending pools on Solana
→ Agent synthesizes: "JUP up 8.2%, whale inflows up 3×, trending pool volume +200%"
→ Agent recommends: "Buy $50 JUP — strong momentum, low risk"
→ User confirms → Agent executes the swap
```

## Prerequisites

- Funded wallet with USDC on Solana: `mp token balance list --wallet main --chain solana`
- If low on USDC: `mp token swap --wallet main --chain solana --from-token <SOL> --from-amount 10 --to-token <USDC>`

## Step 1 — Get the market overview ($0.01)

```bash
mp x402 request \
  --method POST \
  --url "https://agents.moonpay.com/api/x402/tools/market_digest_retrieve" \
  --body '{"chain": "solana"}' \
  --wallet main \
  --chain solana
```

Returns: top movers, volume leaders, market sentiment, notable events. Use this to identify which token to dig into.

## Step 2 — Token deep-dive on top opportunity ($0.01)

Replace `<TOKEN_MINT>` with the mint address from Step 1's top mover:

```bash
mp x402 request \
  --method POST \
  --url "https://agents.moonpay.com/api/x402/tools/token_digest_retrieve" \
  --body '{"token": "<TOKEN_MINT>", "chain": "solana"}' \
  --wallet main \
  --chain solana
```

Returns: price action, holder concentration, liquidity depth, whale wallet activity, risk flags.

## Step 3 — Trending pools on Solana ($0.01)

```bash
mp x402 request \
  --method GET \
  --url "https://pro-api.coingecko.com/api/v3/x402/onchain/networks/solana/trending_pools" \
  --wallet main \
  --chain solana
```

Returns: top liquidity pools ranked by 24h volume, price change, and transaction count. Cross-reference with Steps 1–2 to confirm the opportunity.

## Step 4 — Full research run (one command)

Run all three queries and save the output:

```bash
#!/bin/bash
# research-run.sh — $0.03 market research sweep

MP="$(which mp)"
WALLET="main"
CHAIN="solana"
OUT="$HOME/.config/moonpay/research/$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$(dirname "$OUT")"

echo "=== MoonPay Market Digest ===" | tee "${OUT}-market.json"
"$MP" x402 request \
  --method POST \
  --url "https://agents.moonpay.com/api/x402/tools/market_digest_retrieve" \
  --body '{"chain": "'"$CHAIN"'"}' \
  --wallet "$WALLET" --chain "$CHAIN" | tee -a "${OUT}-market.json"

echo ""
echo "=== CoinGecko Trending Pools ===" | tee "${OUT}-pools.json"
"$MP" x402 request \
  --method GET \
  --url "https://pro-api.coingecko.com/api/v3/x402/onchain/networks/$CHAIN/trending_pools" \
  --wallet "$WALLET" --chain "$CHAIN" | tee -a "${OUT}-pools.json"

echo ""
echo "Research saved to $OUT-*.json"
echo "Total cost: ~\$0.02 USDC"
echo ""
echo "Next: run token digest on your top pick:"
echo "  mp x402 request --method POST --url \"https://agents.moonpay.com/api/x402/tools/token_digest_retrieve\" \\"
echo "    --body '{\"token\": \"<MINT>\", \"chain\": \"solana\"}' --wallet main --chain solana"
```

## Step 5 — Execute the trade (after reviewing intel)

Once you've identified the opportunity from Steps 1–3:

```bash
# Swap USDC → target token
mp token swap \
  --wallet main \
  --chain solana \
  --from-token EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v \
  --from-amount <AMOUNT_USDC> \
  --to-token <TARGET_TOKEN_MINT>
```

## All available x402 endpoints

| Endpoint | Cost | Method | What it returns |
|----------|------|--------|----------------|
| `https://agents.moonpay.com/api/x402/tools/market_digest_retrieve` | $0.01 | POST `{"chain": "solana"}` | Market overview, top movers, sentiment |
| `https://agents.moonpay.com/api/x402/tools/token_digest_retrieve` | $0.01 | POST `{"token": "<mint>", "chain": "solana"}` | Deep token analysis, whale activity, risk |
| `https://agents.moonpay.com/api/x402/tools/wallet_digest_retrieve` | $0.01 | POST `{"wallet": "<address>", "chain": "solana"}` | Wallet intelligence, holdings, behavior |
| `https://pro-api.coingecko.com/api/v3/x402/simple/price` | $0.01 | GET | Current prices, market caps, 24h volume |
| `https://pro-api.coingecko.com/api/v3/x402/onchain/networks/{network}/trending_pools` | $0.01 | GET | Trending liquidity pools by trading activity |
| `https://pro-api.coingecko.com/api/v3/x402/onchain/networks/{network}/tokens/{address}` | $0.01 | GET | Token details: price, supply, FDV, top pools |
| `https://agents.moonpay.com/x402/upgrade` | $1–$20 | POST `{"duration": "day"}` | Rate limit upgrade (day or month) |

### Upcoming x402 APIs (ecosystem)

| Service | What it offers | Payment chain |
|---------|---------------|--------------|
| `x402.twit.sh` | Real-time X/Twitter data, no API key | Base (USDC) |
| `Einstein AI` | Whale tracking, DEX analytics | Base/Solana |
| `Gloria AI` | Real-time news for agents | Base |
| `x402engine` | LLM inference, image gen, audio transcription | Base |

## How x402 payment works under the hood

1. `mp x402 request` sends your HTTP request to the endpoint
2. If it returns `402 Payment Required`, the CLI reads the payment requirements from the response
3. CLI builds a USDC payment transaction, signs it locally (key never leaves your machine)
4. Retries the request with `X-PAYMENT` proof header
5. Endpoint verifies payment on-chain and returns the data
6. If the endpoint fails (status ≥ 400), payment is not settled — you only pay for successful responses

## Scheduled research (daily morning brief)

```bash
# Run research sweep every morning at 7am
(crontab -l 2>/dev/null; echo '0 7 * * * ~/.config/moonpay/scripts/research-run.sh # moonpay:research') | crontab -
```

macOS launchd — same pattern as other skills, `StartCalendarInterval` with `Hour: 7`.

## Notes

- **CLI version:** MoonPay proprietary x402 endpoints (`agents.moonpay.com/api/x402/tools/*`) require CLI ≥ 0.12.2. Update with: `npm i -g @moonpay/cli`
- **CoinGecko endpoints work on all versions** — use these as the primary data source until updated
- Always check your USDC balance before a research run: `mp token balance list --wallet main --chain solana --json | grep -v "^Update"`
- The agent should read the market digest first, pick the top opportunity, then pull the token digest — don't blindly buy without the token-level risk check
- Payment is on Solana mainnet — you need USDC on Solana, not Base
- CoinGecko x402 uses network identifiers: `solana`, `eth`, `base`, `polygon`, `arbitrum`

## Related skills

- **moonpay-x402** — Core x402 request documentation
- **moonpay-swap-tokens** — Execute the trade after research
- **moonpay-discover-tokens** — Lookup token addresses after research identifies a ticker
- **moonpay-budget-agent** — Cap daily spend including research costs
- **moonpay-arb-bot** — Use research intel to spot cross-chain opportunities
