---
description: Guided workflow for promoting a new decision ruleset version — hash rotation, dual-pin update, governance compliance
arguments:
  - name: new_version
    description: New ruleset version identifier (e.g., v1.15.0)
    required: true
---

# Ruleset Promotion: {{new_version}}

## Pre-flight Checks

Before proceeding, verify ALL conditions:

1. `knowledge_read(artifact="held_spec_ledger")` — no active holds blocking promotion
2. `knowledge_read(artifact="latest_state")` — no architecture freeze active
3. Promotion battery results exist and pass:
   - [ ] Forward Momentum (FM) test
   - [ ] Bootstrap confidence interval
   - [ ] FDR (False Discovery Rate) control
   - [ ] LOSO (Leave-One-Session-Out) cross-validation

**If any check fails: STOP. Do not proceed. Report the blocker.**

## Step 1: Identify the hash rotation

- Current active ruleset hash: (read from `run_screen.py`)
- New ruleset file: `production_data/decision_rulesets/{{new_version}}_*.json`
- New hash: (compute SHA256 of the new file)

## Step 2: Write HASH_ROTATIONS.md entry

Add to `governance/HASH_ROTATIONS.md`:

```markdown
| [old_hash] | [new_hash] | [today's date] | run_screen.py + run_phase2_snapshot_delta.py | Promotion: {{new_version}} | [downstream impact] | [operator] |
```

## Step 3: Update pinned hashes (BOTH files must stay in sync)

1. `run_screen.py` — update the ruleset hash constant
2. `run_phase2_snapshot_delta.py` — update the same hash constant

**CRITICAL: These two files MUST reference the same hash. Mismatch = governance violation.**

## Step 4: Update CLAUDE.md

Update the "Active Ruleset" reference in the root CLAUDE.md:
- ID: [new_hash_prefix]
- Version: {{new_version}}
- File: `production_data/decision_rulesets/{{new_version}}_*.json`

## Step 5: Validate

```bash
scripts/run_tests.sh tests/test_decision_ruleset.py
```

All tests must pass before committing.

## Step 6: Commit

```bash
git add governance/HASH_ROTATIONS.md run_screen.py run_phase2_snapshot_delta.py CLAUDE.md
git commit -m "promote: {{new_version}} ruleset (hash rotation)"
```
