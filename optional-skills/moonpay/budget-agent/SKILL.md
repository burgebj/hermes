---
name: budget-agent
description: "Set a daily spending budget for your agent. Check spend, enforce limits before trades, and run an automated watchdog that alerts when the budget is hit."
version: 0.1.0
author: MoonPay (tonyagents), Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [MoonPay, Trading, Automation, Budget]
    related_skills: []
---

# Daily Spending Budget Agent

## Goal

Give your agent a daily spending cap. Before any trade, check how much has been spent today. Block execution if the budget is exceeded. Optionally run a background watchdog that alerts you when you're close.

## Demo flow

```
User: "Set my daily budget to $100 and check if I can buy $30 of SOL"
→ Agent checks today's spend from transaction history
→ Calculates remaining budget
→ If within limit: confirms and executes the swap
→ If over limit: blocks and reports status
```

## Step 1 — Check today's spend

```bash
# Get transaction history (compact JSON for parsing)
mp -f compact transaction list \
  --wallet <wallet-name> \
  --chain <chain>
```

Parse today's outbound swap amounts with jq:

```bash
TODAY=$(date -u +%Y-%m-%d)
SPENT=$(mp transaction list --wallet main --chain solana --json \
  | grep -v "^Update\|^Run " \
  | jq -r --arg today "$TODAY" '
    [.items[]
      | select(.createdAt | startswith($today))
      | select(.type == "swap")
      | (.usd // 0)
    ] | add // 0
  ')
echo "Spent today: \$$SPENT"
```

## Step 2 — Budget enforcement before a trade

Before executing any swap, run this check:

```bash
#!/bin/bash
# budget-check.sh — call before every trade
DAILY_BUDGET=${1:-100}   # default $100
TRADE_AMOUNT=${2:-0}     # amount of this trade

WALLET="main"
CHAIN="solana"
TODAY=$(date -u +%Y-%m-%d)

MP="$(which mp)"

SPENT=$("$MP" transaction list --wallet "$WALLET" --chain "$CHAIN" --json \
  | grep -v "^Update\|^Run " \
  | jq -r --arg today "$TODAY" '
    [.items[]
      | select(.createdAt | startswith($today))
      | select(.type == "swap")
      | (.usd // 0)
    ] | add // 0
  ')

AFTER=$(echo "$SPENT + $TRADE_AMOUNT" | bc -l)
REMAINING=$(echo "$DAILY_BUDGET - $SPENT" | bc -l)

echo "Daily budget:   \$$DAILY_BUDGET"
echo "Spent today:    \$$SPENT"
echo "This trade:     \$$TRADE_AMOUNT"
echo "After trade:    \$$AFTER"
echo "Remaining:      \$$REMAINING"

if (( $(echo "$AFTER > $DAILY_BUDGET" | bc -l) )); then
  echo "BLOCKED: trade would exceed daily budget (\$$AFTER > \$$DAILY_BUDGET)"
  exit 1
fi

echo "OK: trade approved — \$$REMAINING remaining after this trade"
exit 0
```

Save to `~/.config/moonpay/scripts/budget-check.sh` and `chmod +x`.

## Step 3 — Execute a budget-gated trade

```bash
# Check budget first, then swap if approved
~/.config/moonpay/scripts/budget-check.sh 100 30 && \
mp token swap \
  --wallet main \
  --chain solana \
  --from-token EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v \
  --from-amount 30 \
  --to-token So11111111111111111111111111111111111111111
```

## Step 4 — Automated budget watchdog (runs hourly)

Save as `~/.config/moonpay/scripts/budget-watchdog.sh`:

```bash
#!/bin/bash
set -euo pipefail

MP="$(which mp)"
LOG="$HOME/.config/moonpay/logs/budget.log"
WALLET="main"
CHAIN="solana"
DAILY_BUDGET=100
ALERT_THRESHOLD=80   # alert at 80% spent

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

TODAY=$(date -u +%Y-%m-%d)

SPENT=$("$MP" transaction list --wallet "$WALLET" --chain "$CHAIN" --json \
  | grep -v "^Update\|^Run " \
  | jq -r --arg today "$TODAY" '
    [.items[]
      | select(.createdAt | startswith($today))
      | select(.type == "swap")
      | (.usd // 0)
    ] | add // 0
  ')

REMAINING=$(echo "$DAILY_BUDGET - $SPENT" | bc -l)
PCT=$(echo "scale=0; $SPENT * 100 / $DAILY_BUDGET" | bc -l)

log "Budget: \$$SPENT / \$$DAILY_BUDGET spent (${PCT}%) — \$$REMAINING remaining"

if (( $(echo "$SPENT >= $DAILY_BUDGET" | bc -l) )); then
  log "ALERT: daily budget EXCEEDED — all trading blocked"
  [[ "$OSTYPE" == "darwin"* ]] && \
    osascript -e "display notification \"Budget exceeded: \$$SPENT / \$$DAILY_BUDGET\" with title \"MoonPay Budget Alert\" sound name \"Basso\""

elif (( $(echo "$PCT >= $ALERT_THRESHOLD" | bc -l) )); then
  log "WARNING: ${PCT}% of daily budget used — \$$REMAINING left"
  [[ "$OSTYPE" == "darwin"* ]] && \
    osascript -e "display notification \"${PCT}% budget used — \$$REMAINING remaining\" with title \"MoonPay Budget Warning\""
fi
```

### Schedule the watchdog (macOS — launchd)

Write to `~/Library/LaunchAgents/com.moonpay.budget-watchdog.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.moonpay.budget-watchdog</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/Users/YOUR_USERNAME/.config/moonpay/scripts/budget-watchdog.sh</string>
  </array>
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>StandardOutPath</key>
  <string>/Users/YOUR_USERNAME/.config/moonpay/logs/budget-watchdog.out</string>
  <key>StandardErrorPath</key>
  <string>/Users/YOUR_USERNAME/.config/moonpay/logs/budget-watchdog.err</string>
</dict>
</plist>
```

Replace `YOUR_USERNAME` with `$(whoami)`, then load:

```bash
launchctl load ~/Library/LaunchAgents/com.moonpay.budget-watchdog.plist
```

### Schedule the watchdog (Linux — cron)

```bash
# Run budget watchdog every hour — moonpay:budget-watchdog
(crontab -l 2>/dev/null; echo '0 * * * * ~/.config/moonpay/scripts/budget-watchdog.sh # moonpay:budget-watchdog') | crontab -
```

## View budget status anytime

```bash
tail -20 ~/.config/moonpay/logs/budget.log
```

## Stop the watchdog

```bash
# macOS
launchctl unload ~/Library/LaunchAgents/com.moonpay.budget-watchdog.plist

# Linux
crontab -l | grep -v "moonpay:budget-watchdog" | crontab -
```

## Notes

- Daily budget resets at midnight UTC
- The budget check script exits with code 1 if trade would exceed budget — use `&&` to gate any swap on it
- Scripts never store credentials — `mp` reads from OS keychain at runtime
- Adjust `DAILY_BUDGET` and `ALERT_THRESHOLD` at the top of the watchdog script
- For Iron virtual account fiat spend tracking, also run `mp virtual-account transaction list`

## Related skills

- **moonpay-swap-tokens** — Execute the budget-gated trade
- **moonpay-check-wallet** — Check current balances
- **moonpay-virtual-account** — Fund the agent via fiat onramp
- **moonpay-trading-automation** — DCA and limit orders to stay within budget
