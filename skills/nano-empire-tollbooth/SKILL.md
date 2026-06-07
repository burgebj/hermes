---
name: nano-empire-tollbooth
description: Payment rails for AI agents. Route any API call through the tollbooth with automatic x402 payment challenges, HMAC verification, cryptographic proof packs, and revenue tracking. 100 free credits. No API key needed.
version: 1.0.0
author: Nano Empire AI
license: MIT
metadata:
  hermes:
    tags: [x402, tollbooth, agent-payments, m2m, a2a, proof-packs, commerce, monetization]
    categories: [agent-commerce, payments, ai-agents]
---

# Nano Empire Tollbooth — Payment Rails for AI Agents

## What It Does

Routes any skill or API call through a payment layer. Agents receive HTTP 402 challenges, sign with HMAC, and the service executes. Cryptographic proof packs verify every transaction. Built for autonomous agent-to-agent commerce.

## Quick Start

```bash
pip install nano-empire-guardrails
```

```python
from nano_empire_guardrails import monetize

@monetize(credits_per_call=1)
def my_skill(text: str) -> str:
    return f"Processed: {text}"

# First call gets HTTP 402 challenge with payment terms
# Agent signs, replays, and the skill executes
```

## Features

- **402 Payment Challenges** — Agents receive payment terms before execution
- **HMAC Verification** — Cryptographic signatures prevent replay attacks
- **Proof Packs** — Every transaction generates a verifiable SHA256 hash chain
- **Credit System** — Buy credits via Stripe. Spend on any gated skill.
- **Revenue Dashboard** — Real-time metrics. Credits, transactions, revenue.
- **Free Tier** — 100 free credits on signup. No credit card needed.
- **API Proxy** — Route any third-party API through the tollbooth. 0.25% take-rate.
- **PAPER_MODE Safety** — Safe by default. Override with env var for production.

## Pricing

| Package | Credits | Price |
|---------|---------|-------|
| Starter | 500 | $10 |
| Builder | 2,500 | $45 |
| Operator | 10,000 | $150 |

## Deployment

```bash
docker run -p 8403:8403 aiagentssignals/tollbooth:v0.1.0
```

## Links

- Website: https://nanoempireai.com
- PyPI: https://pypi.org/project/nano-empire-guardrails
- Docker: https://hub.docker.com/r/aiagentssignals/tollbooth
- API: http://147.5.105.20:8403/healthz
- Revenue: $105+ earned, 132 tests passing

## Monetize Your Skill

Skill developers earn 80% of every transaction. Add one line to your skill:

```python
from nano_empire_guardrails import monetize
```

Your skill becomes a paid service. You earn. We handle payments, verification, and proof packs.
