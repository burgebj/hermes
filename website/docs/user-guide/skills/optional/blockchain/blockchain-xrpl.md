---
title: "Xrpl"
sidebar_label: "Xrpl"
description: "Instruction-first XRP Ledger audit playbook for read-only account, trust-line, transaction, fee, reserve, and network checks using public XRPL JSON-RPC"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Xrpl

Instruction-first XRP Ledger audit playbook for read-only account, trust-line, transaction, fee, reserve, and network checks using public XRPL JSON-RPC. No bundled executable, API key, private key handling, signing, or transaction submission.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/blockchain/xrpl` |
| Path | `optional-skills/blockchain/xrpl` |
| Version | `0.1.0` |
| Author | Osraka, Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `XRP`, `XRPL`, `XRP Ledger`, `Blockchain`, `Crypto`, `Web3`, `RPC`, `DeFi`, `Audit` |
| Related skills | [`solana`](/docs/user-guide/skills/optional/blockchain/blockchain-solana), [`base`](/docs/user-guide/skills/optional/blockchain/blockchain-base) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# XRP Ledger Audit Playbook

Use this skill when a user needs a careful, read-only review of XRP Ledger
accounts, trust lines, recent transactions, fees, reserves, or network status.
The workflow is intentionally instruction-first: it uses public XRPL JSON-RPC
requests and small shell/Python snippets instead of shipping a maintained CLI.

Safety boundaries:

- Do not request, store, print, sign with, or transmit private keys, seed phrases,
  family seeds, mnemonics, or wallet files.
- Do not submit transactions. This skill is for observation and explanation only.
- Treat price data as optional context, not investment advice.
- Prefer a user-provided trusted RPC endpoint for sensitive investigations.

---

## When to Use

- User asks for an XRP Ledger account balance, reserve, or spendable-XRP estimate
- User wants trust-line, IOU, issuer, gateway, or rippling exposure reviewed
- User wants recent account activity summarized from public ledger data
- User wants a transaction hash explained without signing or broadcasting anything
- User wants live XRPL network, fee, reserve, or validated-ledger context
- User asks for a compact read-only risk summary for an XRPL account

---

## Prerequisites

Use tools already available in most agent environments:

- `curl` for JSON-RPC requests
- `python3` only for optional local formatting/parsing snippets
- No external Python package, npm package, API key, wallet, or private key

Default public endpoint:

```bash
export XRPL_RPC_URL="${XRPL_RPC_URL:-https://s1.ripple.com:51234/}"
```

For high-sensitivity work, ask the user whether they want to provide their own
trusted XRPL node endpoint. Public endpoints can rate-limit, log metadata, or
have incomplete historical ranges.

---

## Quick RPC Pattern

All examples use the same JSON-RPC shape:

```bash
curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d '{"method":"server_info","params":[{}]}'
```

If the user needs easier reading, pipe to Python's standard JSON formatter:

```bash
curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d '{"method":"server_info","params":[{}]}' \
  | python3 -m json.tool
```

Common methods:

- `server_info` - validated ledger, reserve values, load factor, server state
- `fee` - current open-ledger fee, median fee, and expected queue behavior
- `account_info` - XRP balance in drops, sequence, flags, and `OwnerCount`
- `account_lines` - trust lines, limits, balances, issuers, and NoRipple flags
- `account_tx` - historical transactions affecting an account
- `tx` - detailed transaction lookup by hash

---

## Procedure

### 1. Establish Network Context

Start with network status before interpreting an account. A stale or unhealthy
server can make every downstream conclusion look sharper than it really is.

```bash
export XRPL_RPC_URL="${XRPL_RPC_URL:-https://s1.ripple.com:51234/}"

curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d '{"method":"server_info","params":[{}]}' \
  | python3 -m json.tool

curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d '{"method":"fee","params":[{}]}' \
  | python3 -m json.tool
```

Read these fields carefully:

- `info.validated_ledger.seq` or equivalent validated ledger index
- `info.validated_ledger.reserve_base_xrp`
- `info.validated_ledger.reserve_inc_xrp`
- `info.load_factor` and `info.server_state`
- `fee.drops.open_ledger_fee`, `fee.drops.median_fee`, and `fee.expected_ledger_size`

### 2. Inspect Account Reserve and Spendable XRP

Fetch the account state with `account_info`. Use `ledger_index: validated` so the
answer is anchored to a validated ledger rather than an open ledger.

```bash
ACCOUNT='rEXAMPLE_REPLACE_WITH_CLASSIC_ADDRESS'

curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d "{\"method\":\"account_info\",\"params\":[{\"account\":\"$ACCOUNT\",\"ledger_index\":\"validated\",\"strict\":true}]}" \
  | python3 -m json.tool
```

Interpretation checklist:

- `Balance` is denominated in drops. Divide by 1,000,000 for XRP.
- `OwnerCount` increases reserve requirements for ledger objects such as trust
  lines, offers, escrows, checks, tickets, and signer lists.
- Spendable estimate is roughly `balance_xrp - reserve_base_xrp - OwnerCount * reserve_inc_xrp`.
- Negative spendable estimates usually mean the account is close to reserve
  pressure, not necessarily that funds are missing.
- Flags can matter. If account flags are present, explain what they indicate and
  avoid overstating risk when the flag is normal for an issuer or gateway.

Optional local calculation after saving the JSON response to `account.json` and
`server.json`:

```bash
python3 - <<'PY'
import json
from decimal import Decimal

server = json.load(open('server.json'))
account = json.load(open('account.json'))
info = server['result'].get('info', {})
ledger = info.get('validated_ledger') or info.get('closed_ledger') or {}
base = Decimal(str(ledger.get('reserve_base_xrp', '10')))
inc = Decimal(str(ledger.get('reserve_inc_xrp', '2')))
data = account['result']['account_data']
balance = Decimal(data['Balance']) / Decimal('1000000')
owner_count = Decimal(str(data.get('OwnerCount', 0)))
reserve = base + owner_count * inc
print(json.dumps({
    'balance_xrp': str(balance),
    'owner_count': str(owner_count),
    'reserve_xrp': str(reserve),
    'estimated_spendable_xrp': str(balance - reserve),
}, indent=2))
PY
```

### 3. Review Trust Lines and IOU Exposure

Trust lines are where XRPL analysis becomes more nuanced. They can represent
issued assets, gateway relationships, credit limits, and rippling configuration.

```bash
curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d "{\"method\":\"account_lines\",\"params\":[{\"account\":\"$ACCOUNT\",\"ledger_index\":\"validated\",\"limit\":100}]}" \
  | python3 -m json.tool
```

Trust-line checklist:

- `currency` identifies the issued asset. Some currencies are 160-bit hex codes;
  decode only when confident, otherwise preserve the exact code.
- `account` is the counterparty/issuer for that line.
- `balance` is from the queried account's perspective. Negative values can mean
  the account owes that issued asset to the counterparty.
- `limit` and `limit_peer` reveal credit limits in each direction.
- `no_ripple` and `no_ripple_peer` matter for pathfinding and unintended
  rippling exposure.
- Large nonzero balances, unusual issuers, open rippling, or many dormant lines
  are worth highlighting as review items, not automatic vulnerabilities.

If the response includes a `marker`, repeat the call with that marker until all
relevant pages are reviewed:

```bash
curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d "{\"method\":\"account_lines\",\"params\":[{\"account\":\"$ACCOUNT\",\"ledger_index\":\"validated\",\"limit\":100,\"marker\":\"MARKER_FROM_PREVIOUS_RESPONSE\"}]}"
```

### 4. Summarize Recent Account Activity

Use `account_tx` for recent activity. Keep the initial limit small so the agent
can explain clearly before expanding the search.

```bash
curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d "{\"method\":\"account_tx\",\"params\":[{\"account\":\"$ACCOUNT\",\"ledger_index_min\":-1,\"ledger_index_max\":-1,\"limit\":10,\"binary\":false,\"forward\":false}]}" \
  | python3 -m json.tool
```

For each transaction, capture:

- Hash, ledger index, validation status, and transaction result
- `TransactionType`, `Account`, `Destination`, and `Fee`
- XRP or issued-asset amount fields such as `Amount`, `DeliverMax`, or delivered amount metadata
- Whether the transaction changes trust lines, offers, account settings, signer
  lists, escrows, checks, tickets, NFTs, or AMM objects

Be careful with partial payments. If metadata contains delivered amount fields,
prefer those over the nominal `Amount` field when explaining what was actually
received.

### 5. Inspect a Specific Transaction Hash

Use `tx` for transaction-level explanations.

```bash
TX_HASH='REPLACE_WITH_64_HEX_TRANSACTION_HASH'

curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d "{\"method\":\"tx\",\"params\":[{\"transaction\":\"$TX_HASH\",\"binary\":false}]}" \
  | python3 -m json.tool
```

Explain the transaction in layers:

- What the transaction attempted to do
- Whether it was validated and what result code it received
- Which account initiated it and which accounts/assets were affected
- Fees paid in drops/XRP
- Metadata changes that matter, especially trust lines, owner count, offers, AMM
  positions, signer lists, and account flags
- Any uncertainty caused by missing metadata or non-full-history endpoints

### 6. Optional XRP/USD Context

Only fetch market price when it helps the user interpret magnitude. Do not make
price predictions.

```bash
curl -sS 'https://api.coingecko.com/api/v3/simple/price?ids=ripple&vs_currencies=usd' \
  | python3 -m json.tool
```

When using price data, state the source and that it is a spot quote from a third
party. If the price endpoint fails, continue the ledger analysis without it.

---

## Risk Heuristics

Useful findings to surface:

- Account has many owner objects, increasing reserve lock-up
- Spendable XRP estimate is close to zero after reserve requirements
- Trust lines have nonzero balances with issuers the user does not recognize
- Rippling appears open where the account is not intentionally acting as a gateway
- Recent `AccountSet`, `SignerListSet`, `TrustSet`, `OfferCreate`, `AMM*`, or
  `Payment` activity is unexpected
- Transaction result codes show failures, retries, or suspicious repeated attempts
- Public endpoint lacks full history for the requested investigation window

Avoid overstating:

- A trust line is not automatically malicious.
- A negative IOU balance is not automatically theft.
- A high `OwnerCount` is not automatically suspicious for active traders, issuers,
  NFT users, AMM users, or accounts with many open offers.
- Public ledger data cannot prove wallet compromise without user-side context.

---

## Response Template

When reporting to a user, keep the answer evidence-based:

```text
XRPL read-only review for <account>

Network context:
- Validated ledger: <ledger index>
- Base reserve / owner reserve: <values>
- Fee context: <open ledger fee / median fee>

Account summary:
- Balance: <xrp>
- OwnerCount: <count>
- Estimated reserve: <xrp>
- Estimated spendable XRP: <xrp>

Trust-line observations:
- <issuer/currency/balance/flags>

Recent activity:
- <hash/type/result/amount/fee/why it matters>

Review notes:
- <risk or uncertainty>
- <recommended next read-only check>
```

---

## Verification

Before opening or updating a PR, verify the contribution remains documentation
and instruction-only:

```bash
git diff --check
python3 scripts/check-windows-footguns.py
```

A basic live connectivity smoke test can be run manually when network access is
available:

```bash
export XRPL_RPC_URL="${XRPL_RPC_URL:-https://s1.ripple.com:51234/}"
curl -sS "$XRPL_RPC_URL" \
  -H 'Content-Type: application/json' \
  -d '{"method":"server_info","params":[{}]}' \
  | python3 -m json.tool
```
