---
description: Diagnose a specific agent — fetch SOUL.md, heartbeat, registry entry, recent anomalies, and suggest fixes
arguments:
  - name: agent_name
    description: Name of the agent to diagnose (e.g., herald, bellringer, intraday_mover_watch)
    required: true
---

# Diagnose Agent: {{agent_name}}

## Step 1: Fetch agent context via MCP

Run these MCP calls in order:

1. `agents_get(name="{{agent_name}}")` — full agent detail
2. `skills_read(name="{{agent_name}}")` — SOUL.md behavioral contract
3. `knowledge_read(artifact="latest_state")` — check for anomalies mentioning this agent

## Step 2: Check heartbeat

- If heartbeat age > 48h: agent is STALE
- Check cron entry: `crontab -l | grep {{agent_name}}`
- Check recent logs: `tail -50 logs/{{agent_name}}_*.log`

## Step 3: Determine root cause

Common failure modes by lane:
- **Lane A (deterministic):** Cron missing, script error, data dependency stale
- **Lane B (monitoring):** Together API timeout, anomaly threshold miscalibrated
- **Lane C (manual):** Not applicable (manual-only agents don't have heartbeats)

## Step 4: Suggest fix

Based on the diagnosis, suggest the minimal fix:
1. If cron missing: provide the cron entry to add
2. If API timeout: check `together_latency.log`
3. If data dependency: identify upstream and check its heartbeat
4. If SOUL.md mismatch with registry: flag the inconsistency

## Step 5: Verify

After applying fix, verify:
```bash
python3 run_agent_direct.py --agent {{agent_name}}
```

Report success or escalate to operator.
