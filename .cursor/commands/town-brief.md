---
description: Fetch a concise read-only Town/Cursor integration brief
---

# Town Brief

## Step 1: Fetch concise state

1. `town_brief()` — source-of-truth paths, health counts, held-spec flags, gateway mode.
2. If status is not `ok`, run `agent_health_summary()` for actionable anomalies.

## Step 2: Follow up by area

- Named agent work: `agents_get(name="<agent>")` then `skills_read(name="<agent>")`.
- Governed spec or pipeline work: `knowledge_read(artifact="held_spec_ledger")`.
- Broader bootstrap: `fleet_context_snapshot(summary=True)`.

## Step 3: Report

Summarize:
- Town status: `[ok/attention/degraded]`
- Source of truth: `[HERMES_AGENTS_DIR/HERMES_REPO/agents/etc.]`
- Gateway: `[reachable/not reachable]`
- Active issues: `[count and top items]`
- Next allowed action: `[specific action]`

Do not write to `.learnings/`, artifacts, registry, or SOUL files through MCP.
