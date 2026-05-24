---
description: Check the status of a specification — held, blocked, dependencies, and next allowed actions
arguments:
  - name: spec_id
    description: Specification identifier (e.g., 087, 088, 089, 090, 105, 110)
    required: true
---

# Spec Status Check: {{spec_id}}

## Step 1: Fetch spec context

1. `knowledge_read(artifact="held_spec_ledger")` — check if spec is held
2. `knowledge_read(artifact="latest_state")` — operational context
3. `knowledge_read(artifact="contradiction_ledger")` — conflicts affecting this spec
4. `learnings_read()` — any memory entries about this spec

## Step 2: Determine spec state

Possible states:
- **DRAFT** — under development
- **IN PROGRESS** — active work, phased
- **HELD** — blocked on dependency (identify the blocker)
- **AWAITING_FIRST_FIRE** — passed but needs production validation
- **HELD_SUPPRESSED** — blocked by external dependency
- **SPEC_REQUIRED** — degradation detected, spec needed
- **RESOLVED** — all acceptance criteria met
- **CLOSED** — formally closed

## Step 3: Identify blockers

If held:
- What spec(s) does it depend on?
- What is the blocking spec's status?
- Is there a timeline for the blocker to resolve?

## Step 4: Determine next allowed action

Based on current governance constraints:
- Is an architecture freeze active? (If yes, design-only work allowed)
- Does this spec touch Tier 0 code? (If yes, operator memo required)
- Is there a first-fire validation pending? (If yes, wait for production run)

## Step 5: Report

- Spec {{spec_id}} status: [STATE]
- Blocker(s): [list or "none"]
- Next allowed action: [specific action]
- Estimated unblock date: [date or "unknown"]
- Contradictions: [any conflicts]
