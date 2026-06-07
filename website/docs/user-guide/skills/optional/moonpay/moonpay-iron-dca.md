---
title: "Iron Dca — Wire fiat to your Iron virtual account"
sidebar_label: "Iron Dca"
description: "Wire fiat to your Iron virtual account"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Iron Dca

Wire fiat to your Iron virtual account. Agent detects the deposit, splits it into equal chunks, and automatically DCA's into any token on a daily schedule. Full loop from bank wire to on-chain position — no manual steps.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/moonpay/iron-dca` |
| Path | `optional-skills/moonpay/iron-dca` |
| Version | `0.1.0` |
| Author | MoonPay (tonyagents), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `MoonPay`, `Fiat`, `Trading`, `Automation`, `Iron`, `DCA` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Iron Fiat-to-DCA Agent

## Goal

Wire USD to your Iron IBAN. The agent detects the deposit, splits it into equal daily chunks, and executes one swap per day until fully deployed. Fiat in. On-chain position out. Fully automated.

This is the bank account story. No other agent framework does this.

## Demo flow

```
User: "Set up a DCA strategy — wire $500 into SOL over 7 days"

→ Agent checks virtual account status
→ Agent shows your Iron deposit account (IBAN / ACH details)
→ User wires $500 from their bank
→ Iron converts to USDC, lands in wallet
→ Agent detects deposit, creates DCA schedule: $71.43/day × 7 days
→ Daily at 9am: agent swaps $71.43 USDC → SOL automatically
→ After 7 days: $500 fully deployed, average cost across 7 price points
```

## Step 1 — Check virtual account status

```bash
mp virtual-account retrieve --json 2>&1 | grep -v "^Update\|^Run "
```

If no account exists yet:

```bash
mp virtual-account create
# Opens KYC verification URL — complete in browser
# Then accept required agreements:
mp virtual-account agreement list
mp virtual-account agreement accept --contentId <id>
```

## Step 2 — Register your wallet

```bash
mp virtual-account wallet register --wallet main --chain solana
```

Verify:

```bash
mp virtual-account wallet list
```

## Step 3 — Create the Iron onramp

```bash
mp virtual-account onramp create \
  --name "Iron DCA Onramp" \
  --fiat USD \
  --stablecoin USDC \
  --wallet <registered-wallet-address> \
  --chain solana
```

Get your deposit details (IBAN or ACH routing + account number):

```bash
mp virtual-account onramp retrieve --onrampId <id>
```

The output includes the bank details to wire to. Wire your fiat here. Iron converts it to USDC and sends it to your Solana wallet automatically.

## Step 4 — Detect the deposit

Poll until the USDC lands:

```bash
# Check for incoming transactions
mp virtual-account transaction list --json 2>&1 | grep -v "^Update\|^Run " \
  | jq '[.items[] | {status, fiatAmount, stablecoinAmount, createdAt}]'

# Or just watch the balance
mp token balance list --wallet main --chain solana --json 2>&1 \
  | grep -v "^Update\|^Run " \
  | jq '.items[] | select(.symbol == "USDC") | {amount: .balance.amount, usd: .balance.value}'
```

## Step 5 — Initialize DCA schedule

Once deposit lands, run the DCA setup script. Save as `~/.config/moonpay/scripts/iron-dca-setup.sh`:

```bash
#!/bin/bash
# iron-dca-setup.sh — call once when deposit is confirmed

DEPOSIT_AMOUNT=${1:?"Usage: iron-dca-setup.sh <deposit_amount> <days> <token_mint>"}
DCA_DAYS=${2:?"Usage: iron-dca-setup.sh <deposit_amount> <days> <token_mint>"}
TARGET_TOKEN=${3:?"Usage: iron-dca-setup.sh <deposit_amount> <days> <token_mint>"}

STATE_FILE="$HOME/.config/moonpay/iron-dca-state.json"
mkdir -p "$(dirname "$STATE_FILE")"

CHUNK=$(awk "BEGIN { printf \"%.6f\", $DEPOSIT_AMOUNT / $DCA_DAYS }")
START_DATE=$(date -u +%Y-%m-%d)

cat > "$STATE_FILE" <<EOF
{
  "depositAmount": $DEPOSIT_AMOUNT,
  "dcaDays": $DCA_DAYS,
  "chunkSize": $CHUNK,
  "targetToken": "$TARGET_TOKEN",
  "startDate": "$START_DATE",
  "executedDays": 0,
  "totalDeployed": 0
}
EOF

echo "DCA schedule initialized:"
echo "  Deposit:      \$$DEPOSIT_AMOUNT USDC"
echo "  Days:         $DCA_DAYS"
echo "  Daily chunk:  \$$CHUNK USDC"
echo "  Target:       $TARGET_TOKEN"
echo "  Start date:   $START_DATE"
echo ""
echo "State saved to $STATE_FILE"
echo "Now schedule the daily runner — see Step 6."
```

Example: deploy $500 into SOL over 7 days:

```bash
chmod +x ~/.config/moonpay/scripts/iron-dca-setup.sh
~/.config/moonpay/scripts/iron-dca-setup.sh 500 7 So11111111111111111111111111111111111111111
```

## Step 6 — Daily DCA runner

Save as `~/.config/moonpay/scripts/iron-dca-run.sh`:

<!-- ascii-guard-ignore -->
```bash
#!/bin/bash
set -euo pipefail

MP="$(which mp)"
STATE_FILE="$HOME/.config/moonpay/iron-dca-state.json"
LOG="$HOME/.config/moonpay/logs/iron-dca.log"
mkdir -p "$(dirname "$LOG")"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

# ─── Load state ───────────────────────────────────────────
if [ ! -f "$STATE_FILE" ]; then
  log "ERROR: No DCA state found. Run iron-dca-setup.sh first."
  exit 1
fi

CHUNK=$(jq -r '.chunkSize' "$STATE_FILE")
TARGET=$(jq -r '.targetToken' "$STATE_FILE")
EXECUTED=$(jq -r '.executedDays' "$STATE_FILE")
TOTAL_DAYS=$(jq -r '.dcaDays' "$STATE_FILE")
DEPLOYED=$(jq -r '.totalDeployed' "$STATE_FILE")

WALLET="main"
CHAIN="solana"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# ─── Check if complete ────────────────────────────────────
if (( $(echo "$EXECUTED >= $TOTAL_DAYS" | bc -l) )); then
  log "DCA COMPLETE: $EXECUTED/$TOTAL_DAYS days executed, \$$DEPLOYED deployed"
  exit 0
fi

# ─── Check USDC balance ───────────────────────────────────
BALANCE=$("$MP" token balance list --wallet "$WALLET" --chain "$CHAIN" --json \
  | grep -v "^Update\|^Run " \
  | jq -r --arg addr "$USDC" '.items[] | select(.address == $addr) | .balance.amount // 0')

log "Day $((EXECUTED + 1))/$TOTAL_DAYS | USDC balance: \$$BALANCE | chunk: \$$CHUNK"

if (( $(echo "$BALANCE < $CHUNK" | bc -l) )); then
  log "WARN: Insufficient USDC (\$$BALANCE < \$$CHUNK) — deposit may not have arrived yet"
  exit 1
fi

# ─── Execute swap ─────────────────────────────────────────
log "Swapping \$$CHUNK USDC → $TARGET..."

RESULT=$("$MP" token swap \
  --wallet "$WALLET" \
  --chain "$CHAIN" \
  --from-token "$USDC" \
  --from-amount "$CHUNK" \
  --to-token "$TARGET" \
  --json 2>&1 | grep -v "^Update\|^Run ") || {
  log "SWAP FAILED: $RESULT"
  exit 1
}

TX=$(echo "$RESULT" | jq -r '.transactionHash // .hash // "pending"')
log "SWAP OK: tx $TX"

# ─── Update state ─────────────────────────────────────────
NEW_EXECUTED=$((EXECUTED + 1))
NEW_DEPLOYED=$(awk "BEGIN { printf \"%.6f\", $DEPLOYED + $CHUNK }")

jq --argjson e "$NEW_EXECUTED" --argjson d "$NEW_DEPLOYED" \
  '.executedDays = $e | .totalDeployed = $d' \
  "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

REMAINING=$((TOTAL_DAYS - NEW_EXECUTED))
log "Progress: $NEW_EXECUTED/$TOTAL_DAYS days | \$$NEW_DEPLOYED deployed | $REMAINING days left"

# ─── macOS notification ───────────────────────────────────
if [[ "$OSTYPE" == "darwin"* ]]; then
  osascript -e "display notification \"Day $NEW_EXECUTED/$TOTAL_DAYS: \$$CHUNK deployed → $(echo $TARGET | cut -c1-8)...\" with title \"Iron DCA\""
fi
```
<!-- ascii-guard-ignore-end -->

```bash
chmod +x ~/.config/moonpay/scripts/iron-dca-run.sh
```

## Step 7 — Schedule daily execution

### macOS — launchd (fires even if machine was asleep)

Write to `~/Library/LaunchAgents/com.moonpay.iron-dca.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.moonpay.iron-dca</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/Users/YOUR_USERNAME/.config/moonpay/scripts/iron-dca-run.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>/Users/YOUR_USERNAME/.config/moonpay/logs/iron-dca.out</string>
  <key>StandardErrorPath</key>
  <string>/Users/YOUR_USERNAME/.config/moonpay/logs/iron-dca.err</string>
</dict>
</plist>
```

```bash
# Replace YOUR_USERNAME with $(whoami), then:
launchctl load ~/Library/LaunchAgents/com.moonpay.iron-dca.plist
```

### Linux — cron

```bash
(crontab -l 2>/dev/null; echo '0 9 * * * ~/.config/moonpay/scripts/iron-dca-run.sh # moonpay:iron-dca') | crontab -
```

## Monitor progress

```bash
# Live log
tail -f ~/.config/moonpay/logs/iron-dca.log

# Current state
cat ~/.config/moonpay/iron-dca-state.json | jq .

# Run manually (test without waiting for 9am)
bash ~/.config/moonpay/scripts/iron-dca-run.sh
```

## Stop / pause

```bash
# macOS
launchctl unload ~/Library/LaunchAgents/com.moonpay.iron-dca.plist

# Linux
crontab -l | grep -v "moonpay:iron-dca" | crontab -
```

## Common tokens to DCA into

| Token | Symbol | Solana mint |
|-------|--------|-------------|
| Solana | SOL | `So11111111111111111111111111111111111111111` |
| Jupiter | JUP | `JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN` |
| Bonk | BONK | `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263` |
| Pyth | PYTH | `HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3` |

To find any other token: `mp token search --query "TOKEN" --chain solana --limit 5`

## Notes

- Wire transfers typically settle in 1–3 business days; ACH is 1 business day
- USDC lands in your Solana wallet automatically — no manual steps after the wire
- The state file at `~/.config/moonpay/iron-dca-state.json` tracks progress — don't delete it mid-run
- Re-initialize for a new deposit by running `iron-dca-setup.sh` again with new values
- To change the target token mid-run: edit `targetToken` in the state file directly

## Related skills

- **moonpay-virtual-account** — Full Iron account setup, KYC, bank registration
- **moonpay-budget-agent** — Add a daily spend cap on top of the DCA
- **moonpay-x402-analyst** — Run intel before choosing which token to DCA into
- **moonpay-swap-tokens** — Manual swap syntax reference
