# Agent Office Operator Runbook

Status: current MVP runbook
Owner: docs for wording; Akhil/default profile for operation; DevOps for cron deployment; reviewer/QA/Security for their gates
Last verified: 2026-05-13T01:12:55Z

## Purpose

Use this runbook when Akhil or the default Hermes profile needs to inspect, triage, recommend fixes, reroute, or close out Agent Office/Kanban work with evidence. It is written for local operation inside the Hermes Agent repository and matches the current Office Doctor/Watchdog MVP: dry-run diagnostics, evidence scorecard validation, and local runner support. Live notification and safe repair remain follow-up work.

## Scope

In scope:

- Running Doctor and Watchdog diagnostics.
- Inspecting report outbox status.
- Validating gate scorecards.
- Deciding whether to complete, create a specialist child task, or block for a real external blocker.
- Keeping secrets, raw PII, tokens, cookies, and credentials out of durable artifacts.

Out of scope:

- Destructive production actions.
- Bypassing reviewer/QA/Security gates.
- Live Telegram sender implementation changes.
- Credential creation or token inspection.
- Local GPU proof.

## Prerequisites

- Current working directory is the Hermes Agent repository root.
- Python environment can import the repo modules.
- Kanban database and profile configuration are available locally.
- Do not run npm, pnpm, yarn, npx, or add JavaScript packages for this workflow.
- Do not print or paste secrets into Kanban comments, docs, logs, or messages.

## Quick health check

```bash
python3 scripts/office_doctor.py --json > /tmp/office_doctor.json
python3 scripts/office_watchdog.py --dry-run --json > /tmp/office_watchdog.json
python3 scripts/office_report_outbox.py status --json > /tmp/office_report_outbox_status.json
```

Expected output:

- Doctor JSON has `schema_version`, `policy_version`, `overall_status`, and `sections`.
- Watchdog JSON has `schema_version`, `policy_version`, `findings`, and `summary`.
- Outbox status JSON has `path`, `exists`, `total`, and `counts`.

Exit code interpretation:

- Doctor: `0` means pass/warn, `1` means a failing section exists.
- Watchdog: `0` means no findings, `1` means warning/error findings, `2` means critical findings.
- Current-board findings are actionable alerts, not proof that the script is broken.

## Standard operator procedure

### 1. Orient

Use Kanban task state, parent results, comments, events, and workspace files as ground truth. Extract acceptance gates before touching files or task state.

Checklist:

- Task id, title, assignee, status, workspace, parents, and children are known.
- Parent handoffs and caveats are read.
- Deliverables and constraints are explicit.
- Review/QA/Security coverage is preserved.

### 2. Diagnose

Run Doctor first, then Watchdog:

```bash
python3 scripts/office_doctor.py --json
python3 scripts/office_watchdog.py --dry-run --json
```

Look for:

- stale running claims;
- repeated failure clusters;
- ready tasks not spawning;
- nonspawnable assignees;
- blocked protocol violations;
- outbox backlog;
- secret-risk payloads;
- completions missing evidence scorecards.

### 3. Classify the issue

Routine issues that should be recommended for repair, rerouted, or completed with evidence rather than blocked:

- review-required handoff when review can be routed to reviewer/QA;
- stale or crashed worker with no credential/hardware blocker, noting that automatic reclaim/repair is not current behavior;
- nonspawnable assignee that has an equivalent configured profile;
- missing docs or tests within a specialist lane;
- outbox backlog when delivery can be retried safely or kept local.

Real blockers that justify `kanban_block`:

- credentials, login, OAuth, tokens, cookies, or 2FA required;
- paid/cloud permission or quota purchase required;
- destructive irreversible action is required;
- legal/license ambiguity requires human decision;
- missing runtime/hardware is essential, including GPU proof when no Colab artifact exists;
- a claim cannot be verified after serious attempts;
- Akhil explicitly requested human approval before proceeding;
- unsafe secret/PII handling requires Security/human intervention;
- a human browser profile or manual login is required.

### 4. Act within authority

Allowed routine actions:

- add a redacted Kanban comment with evidence and rationale;
- create child tasks for the correct specialist profile;
- complete the current docs/research task when the requested artifact is the deliverable;
- run safe local scripts and tests;
- validate scorecards;
- inspect logs/paths without printing credentials;
- keep Watchdog cron local until Telegram smoke testing is confirmed.

Denied actions without explicit approval:

- destructive changes outside the workspace;
- production deploy/release claims without artifacts;
- credential/token exposure;
- legal/license decisions;
- bypassing reviewer/QA/Security gates;
- claiming GPU, benchmark, or live Telegram proof without artifacts.

### 5. Record evidence

Use this structure in task metadata or a durable comment:

```json
{
  "gate_scorecard": [
    {
      "gate": "Deliverable exists",
      "command_or_check": "test -f docs/office-superpowers/README.md",
      "exit_code_or_artifact": "exit 0",
      "artifact_paths": ["docs/office-superpowers/README.md"],
      "verdict": "PASS",
      "rationale": "The required document exists in the workspace."
    }
  ],
  "handoff_for_supervisor_review": true,
  "human_review_required": false
}
```

Use `scripts/office_scorecard_validate.py` for JSON or markdown scorecards:

```bash
python3 scripts/office_scorecard_validate.py --json-file docs/office-superpowers/DEPLOYMENT_GATE_SCORECARD.json --workspace "$PWD" --json
```

## Scope-change protocol

Do not silently reduce scope. If a requirement cannot be satisfied after serious attempts, add a durable comment with:

```text
SCOPE_CHANGE_REQUEST
requirement_ref: <requirement or deliverable>
requested_change: <what should change>
reason: <blocking reason>
attempted_evidence: <commands/checks/artifacts tried>
impact: <which acceptance gates become partial/blocked>
options:
  - <option 1>
  - <option 2>
```

Then block only if the blocker is real and external.

## Report outbox operation

Check status:

```bash
python3 scripts/office_report_outbox.py status --json
```

Current MVP limitation: `send-due` and `retry-failed` are dry-run only. Do not claim live Telegram delivery from this script until a reviewed sender is implemented and smoke-tested.

## Watchdog cron operation

See `docs/office-superpowers/DEPLOYMENT.md` for full setup. Common commands:

```bash
python3 scripts/office_watchdog_cron_install.py status
python3 scripts/office_watchdog_cron_install.py disable
python3 scripts/office_watchdog_cron_install.py enable
python3 scripts/office_watchdog_cron_install.py smoke --json
```

Default safe delivery is `local`. Switch to Telegram only after a one-shot Telegram smoke test succeeds and current alert volume is acceptable.

## Rollback and remediation

If watchdog cron is noisy:

```bash
python3 scripts/office_watchdog_cron_install.py disable
```

If the job should be removed:

```bash
python3 scripts/office_watchdog_cron_install.py remove
```

If a durable artifact contains secret-like material:

1. Stop delivery or sharing.
2. Redact locally as `[REDACTED]`.
3. Route Security/reviewer follow-up if the secret may have escaped.
4. Do not paste the raw value into a new comment or log.

If a completion lacks evidence:

1. Do not accept the claim as final.
2. Ask the owning worker/QA to provide a scorecard or artifact.
3. Mark the gate `PARTIAL` or `FAIL` until evidence exists.

## Troubleshooting

Problem: Doctor exits `1`.

- Inspect `overall_status` and failing sections in `/tmp/office_doctor.json`.
- Run Watchdog for board-specific findings.
- Treat warnings as operator context; treat failures as actionable local issues.

Problem: Watchdog exits `1` or `2`.

- Inspect `summary` and `findings`.
- Critical secret-risk findings take priority.
- Repeated failure or nonspawnable assignee findings should route to the owning specialist or DevOps.

Problem: Telegram reports are not delivered.

- Check Doctor messaging section for configuration presence only.
- Check gateway/cron status using existing Hermes CLI if available.
- Keep delivery `local` until a credential-safe smoke test passes.
- Do not print token values.

Problem: GPU proof is requested.

- Use `COLAB_GPU_GUIDE.md`.
- If Colab or GPU proof is required and unavailable, emit `SCOPE_CHANGE_REQUEST` instead of claiming success.

## Escalation path

- Security/privacy concern: Security or reviewer profile.
- Runtime/cron/gateway issue: DevOps/tooling profile.
- Ambiguous requirements: PM/chief.
- Implementation defect: owning builder/backend/frontend profile.
- Documentation mismatch: docs profile.
- License/legal ambiguity: human decision required.

## Closeout checklist

Before completing a task:

- All requested deliverables exist or scope change is recorded.
- Claims are current or labeled planned/proposed/demo-only.
- Commands/checks and exit codes are captured.
- Artifact paths are included for heavy claims.
- Secret scan or review was performed on touched docs.
- No npm/pnpm/yarn/npx/package mutations occurred.
- No local GPU proof is claimed.
- Reviewer/QA handoff metadata is included when substantive implementation work is involved.
