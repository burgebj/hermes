---
description: Check current daily production pipeline status — last run, anomalies, knowledge layer freshness
---

# Pipeline Status Check

## Step 1: Fetch operational state

1. `knowledge_read(artifact="latest_state")` — current state snapshot
2. `knowledge_read(artifact="operator_brief")` — latest daily brief
3. `agent_health_summary()` — quick anomaly check

## Step 2: Assess pipeline health

Check the latest_state for:
- **Last snapshot date** — should be today (weekday) or last Friday (weekend)
- **Pipeline step completion** — all 13 steps should show completed
- **Anomalies** — any unresolved items from ops supervisor

## Step 3: Check knowledge layer freshness

- `latest_state.json` mtime should be < 24h on weekdays
- `held_spec_ledger` should reflect current governance decisions
- `contradiction_ledger` should show 0 hard contradictions

## Step 4: Report

Summarize:
- Pipeline last ran: [date/time]
- All 13 steps: [PASS/FAIL with details]
- Stale agents: [count and names]
- Active contradictions: [count]
- Held specs: [count and IDs]
- Freeze status: [active/lifted]

If any issues found, provide the priority-ordered fix sequence from `signal-agents.mdc`.
