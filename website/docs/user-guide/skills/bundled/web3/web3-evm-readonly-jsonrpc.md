---
title: "Evm Readonly Jsonrpc — Safe, whitelist-gated read-only Ethereum-compatible JSON-RPC (no signing or sends)"
sidebar_label: "Evm Readonly Jsonrpc"
description: "Safe, whitelist-gated read-only Ethereum-compatible JSON-RPC (no signing or sends)"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Evm Readonly Jsonrpc

Safe, whitelist-gated read-only Ethereum-compatible JSON-RPC (no signing or sends).

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/web3/evm-readonly-jsonrpc` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Tags | `web3`, `evm`, `json-rpc`, `blockchain`, `ethereum`, `readonly` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# EVM Read-Only JSON-RPC

Call **Ethereum-compatible HTTP JSON-RPC endpoints** using a tight **method whitelist**.
This skill covers chain inspection and `eth_call`-style simulation only — **never** submits
transactions, holds private keys, or enables `eth_send*` methods.

Prefer this for: chain id discovery, latest block probes, lightweight view calls (`eth_call`), and RPC health checks.
For MCP-based multi-chain tooling, use Hermes MCP configuration — this bundle is complementary and stdlib-only.

## When to Use

- User asks for **chain ID**, gas price sanity, balance of a published address (read-only), or contract bytecode via `eth_getCode`
- User wants **`eth_call`** against a verified contract ABI input (already encoded hex) — no wallet required
- User needs **fallback across multiple HTTPS RPC URLs** without adding `web3.py`
- Explicitly avoid when the user needs **transactions, signing, or wallet management** — use dedicated wallet flows / optional Web3 MCP instead

## Prerequisites

- **`HERMES_SKILL_EVM_RPC_URL`** — single HTTPS endpoint, **or**
- **`HERMES_SKILL_EVM_RPC_URLS`** — comma-separated HTTPS endpoints (same chain); tried in order with short backoff
- Public providers often require API keys in the URL query string — rotate keys if rate-limited

## Safety Model

| Rule | Enforcement |
|------|--------------|
| No transactions | Methods like `eth_sendRawTransaction`, `debug_*`, `personal_*`, `miner_*`, `admin_*`, `txpool_*` are **blocked** |
| Stateless | CLI reads env + stdin JSON payload only; writes only structured JSON on stdout |
| Size limits | `eth_call` `data` field rejected if hex length exceeds a fixed cap |

## Canonical CLI (`scripts/evm_jsonrpc.py`)

```bash
python skills/web3/evm-readonly-jsonrpc/scripts/evm_jsonrpc.py rpc \
  --method eth_chainId \
  --params-json '[]'
```

Or stdin JSON (`--stdin`) matching **`EvmRpcCliPayload`** (`method`, optional `params`, optional `rpc_urls` override).

Stdout is always `{ "success": bool, ... }` — inspect `result` vs `error` before presenting to the user.

See `references/rpc-methods.md` for allowed JSON-RPC parameters and pitfalls.
