#!/usr/bin/env bash
set -euo pipefail

# Phase Tracker Watchdog
# Runs via cron to detect stalled upstream contribution workflows.
# If a workflow hasn't been updated in STALL_HOURS hours, alerts the user.

HERMES_AGENT_HOME="${HOME}/.hermes/hermes-agent"
TRACKER="$HERMES_AGENT_HOME/.dev-workflow/phase-tracker.json"
STALL_HOURS=4

if [ ! -f "$TRACKER" ]; then
    exit 0  # No active workflow
fi

STATE=$(python3 -c "
import json
with open('$TRACKER') as f:
    d = json.load(f)
print(json.dumps({
    'state': d.get('state', 'unknown'),
    'phase': d.get('current_phase', 0),
    'issue': d.get('issue_number', 'N/A'),
    'updated': d.get('last_updated', ''),
    'started': d.get('started_at', ''),
}))
" 2>/dev/null || echo '{}')

STATE_VAL=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('state',''))" 2>/dev/null || echo "")
PHASE=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('phase',0))" 2>/dev/null || echo "0")
ISSUE=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('issue','N/A'))" 2>/dev/null || echo "N/A")
UPDATED=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('updated',''))" 2>/dev/null || echo "")
STARTED=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('started',''))" 2>/dev/null || echo "")

if [ "$STATE_VAL" != "active" ]; then
    exit 0  # Completed or aborted
fi

# Check if stalled
if [ -n "$UPDATED" ]; then
    NOW=$(date +%s)
    UPDATED_TS=$(date -d "$UPDATED" +%s 2>/dev/null || echo "0")
    if [ "$UPDATED_TS" -gt 0 ]; then
        ELAPSED=$(( (NOW - UPDATED_TS) / 3600 ))
        if [ "$ELAPSED" -ge "$STALL_HOURS" ]; then
            PHASE_NAME=$(python3 -c "
PHASE_NAMES = {
    1: 'Deep Triage', 2: 'Branch Setup', 3: 'Code Understanding',
    4: 'Security Baseline', 5: 'Implementation', 6: 'Test Suite',
    7: 'Code Review', 8: 'PR Readiness Check', 9: 'Create Pull Request',
    10: 'Self Evolution', 11: 'Insight Feature Request', 12: 'Plugin Improve',
    13: 'Cleanup',
}
print(PHASE_NAMES.get($PHASE, 'unknown'))
" 2>/dev/null || echo "unknown")

            cat <<WATCHDOG
⚠️  Phase Tracker STALLED

Workflow for issue #${ISSUE} has been stuck at Phase ${PHASE} (${PHASE_NAME}) for ${ELAPSED} hours.

To continue:
  cd $HERMES_HOME/hermes-agent
  python3 scripts/phase_tracker.py current    # check current phase
  python3 scripts/phase_tracker.py advance    # advance to next phase

Or to abort:
  python3 scripts/phase_tracker.py abort

Last updated: ${UPDATED}
WATCHDOG
        fi
    fi
fi

exit 0
