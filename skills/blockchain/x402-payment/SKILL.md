---
name: x402-payment
version: 1.0.0
description: Autonomous x402 micropayment skill — detects HTTP 402 Payment Required responses and pays with USDC on Arc Testnet (Chain ID 5042002). No human intervention required.
author: consumeobeydie
tags: [blockchain, payments, arc, usdc, x402, web3, autonomous]
platforms: [linux, macos, wsl2]
requires:
  pip: [web3>=6.0.0, eth-account>=0.11.0, requests>=2.33.0, python-dotenv>=1.0.0]
---

# x402 Payment Skill

Teaches Hermes to autonomously handle HTTP 402 Payment Required responses by paying with USDC on Arc Testnet.

## When to use

- User asks Hermes to access an x402-protected API endpoint
- Hermes encounters HTTP 402 during a web request
- User wants to make autonomous USDC micropayments on Arc Testnet
- User is building or testing x402 payment flows

## Prerequisites

1. Wallet private key configured in `~/.hermes/.env`:


