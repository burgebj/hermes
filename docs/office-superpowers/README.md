# Agent Office Superpowers

Status: current MVP plus documented policy boundaries
Last verified: 2026-05-13T01:12:55Z
Audience: Akhil as the default-profile operator, Office workers, reviewers, QA, and DevOps maintainers

## What this package is

`docs/office-superpowers/` documents the default-profile Office reliability kit: the policy, scripts, evidence gates, templates, and runbooks that let Akhil operate Hermes Agent Office with less babysitting while still requiring evidence for completion claims.

The current implementation is Hermes-native and local-first. It uses existing Kanban state, the gateway/cron system, Python scripts, structured handoff metadata, and documentation. It does not add JavaScript dependencies and does not claim local GPU availability.

Current honest capability statement: this package provides dry-run Office diagnostics, evidence scorecard validation, and a local watchdog runner; live notification and safe repair remain follow-up work.

## Current capability matrix

| Capability | Current state | Evidence / caveat |
|---|---|---|
| Office Doctor diagnostics | Implemented | `scripts/office_doctor.py` builds local JSON/terminal diagnostics without printing credential values. |
| Office Watchdog findings | Implemented as dry-run diagnostics | `scripts/office_watchdog.py --dry-run --json` reports stale/risky states and may exit non-zero when findings exist; it does not mutate Kanban state. |
| Evidence scorecard validation | Implemented for schema and artifact-presence checks | `scripts/office_scorecard_validate.py` validates required fields and heavy-claim artifact presence; it does not prove artifact semantic truth. |
| Report outbox | Implemented as durable local queued/dry-run intent | `scripts/office_report_outbox.py status --json` reports local outbox state. Enqueued records include pending/sent/failed state fields, attempts, last_error, next_attempt_at, and sent_at. `send-due` and `retry-failed` preview only until a reviewed live sender exists. See `OUTBOX_DELIVERY_DEFERRAL.md`. |
| Watchdog cron runner | Implemented locally, deployment is profile-scoped | `scripts/office_watchdog_cron.py` and `scripts/office_watchdog_cron_install.py` exist. Installed job status depends on the active `HERMES_HOME`/profile and scheduler; absence in another profile is not proof of protection. |
| Live Telegram delivery | Explicitly deferred / not current | Requires gateway configuration, reviewed sender wiring, live smoke evidence, and alert-volume controls before any doc may claim delivery. |
| Autonomous safe repair, reassignment, or unblock | Planned / not current | Current scripts may recommend actions but do not safely reclaim, unblock, reassign, or repair Kanban tasks. |
| Security boundary enforcement | Policy-only residual risk | Docs define protected artifacts and redaction expectations, but current code is not an enforceable permission boundary for files, browser state, secrets, or approval records. |
| Browser/dashboard access | Bounded diagnostics only | Remote browser tool access, local dashboard HTTP checks, and logged-in Chrome profile access are distinct; human login/profile/cookie access remains an explicit blocker. |

## Current implemented surfaces

These paths were inspected or inherited from parent task evidence:

- `hermes_cli/office_superpowers.py`: shared helpers for redaction, Doctor reports, Watchdog reports, scorecard validation, and report outbox handling.
- `scripts/office_doctor.py`: one-shot Office health diagnostics.
- `scripts/office_watchdog.py`: dry-run board watchdog for stale/risky states.
- `scripts/office_scorecard_validate.py`: scorecard validator entrypoint.
- `scripts/office_report_outbox.py`: report outbox entrypoint; live Telegram sending is dry-run only in the MVP.
- `scripts/office_watchdog_cron.py`: quiet no-agent watchdog cron runner.
- `scripts/office_watchdog_cron_install.py`: safe install/status/enable/disable/remove/smoke wrapper.
- `docs/office-superpowers/templates/OFFICE_GATE_SCORECARD_TEMPLATE.md`: completion evidence template.
- `docs/office-superpowers/templates/COLAB_GPU_POLICY_TEMPLATE.md`: GPU/Colab policy template.
- `docs/office-superpowers/templates/TELEGRAM_REPORT_CONTRACT.md`: Telegram/report payload contract.
- `docs/office-superpowers/references/OFFICE_OPERATOR_POLICY.md`: default-profile autonomy policy.
- `docs/office-superpowers/references/BROWSER_DASHBOARD_LOG_ACCESS.md`: browser/dashboard/log boundary reference.
- `docs/office-superpowers/DEPLOYMENT.md`: DevOps deployment runbook for Doctor/Watchdog.

## What this package does not do

- It does not grant unrestricted browser profile, cookie, or logged-in Chrome access.
- It does not send live Telegram messages from `office_report_outbox.py`; the MVP outbox sender is dry-run until reviewed gateway sender wiring exists.
- It does not perform destructive automatic Kanban repairs in the current scripts.
- No local GPU: it does not make local GPU claims. Colab is optional remote evidence only.
- It does not replace reviewer, QA, Security, or human approval gates when those gates are genuinely required.
- It does not permit npm, pnpm, yarn, or npx installs for this package.

## Quick start

Run from the Hermes Agent repository root:

```bash
python3 scripts/office_doctor.py --json
python3 scripts/office_watchdog.py --dry-run --json
python3 scripts/office_report_outbox.py status --json
python3 scripts/office_scorecard_validate.py --markdown-file docs/office-superpowers/templates/OFFICE_GATE_SCORECARD_TEMPLATE.md --workspace "$PWD" --json
```

Expected behavior:

- Doctor returns JSON with sections for runtime, gateway, messaging, Kanban, worker profiles, notifications, evidence gates, logs, browser/dashboard, and recommendations.
- Watchdog returns JSON findings and exits non-zero when current board findings are actionable; this is alert behavior, not necessarily script failure.
- Report outbox status prints counts and path without credential values.
- Scorecard validation succeeds for a complete scorecard and fails when required fields or heavy-claim artifacts are missing.

## Operating model

1. Orient from Kanban state, parent handoffs, comments, and workspace files.
2. Classify problems as routine, specialist-owned, or real external blockers.
3. Recommend or route routine fixes with evidence; perform manual repairs only when a reviewed implementation and policy allow it.
4. Use child tasks for cross-lane work; do not silently take authority from another profile.
5. Complete only with evidence: commands/checks, exit codes or artifact paths, verdicts, and rationale.
6. Use `SCOPE_CHANGE_REQUEST` when a requirement cannot honestly be met.
7. Redact secrets as `[REDACTED]` before durable comments, docs, logs, outbox rows, or messages.

Real blockers are limited to credentials, paid/cloud permissions, destructive irreversible actions, legal/license ambiguity, missing runtime/hardware, unverifiable claims, explicit human approval, unsafe secret/PII handling, or required human login/browser profile state.

## Documentation map

- `PRD.md`: product requirements for the superpowers.
- `ARCHITECTURE.md`: architecture and contracts.
- `GATE_SCORECARD.md`: PM-level acceptance scorecard.
- `TASK_GRAPH.md`: work package graph.
- `DEPLOYMENT.md`: deployment runbook and cron setup.
- `OPERATOR_RUNBOOK.md`: day-to-day operator procedure.
- `TEMPLATE_LIBRARY.md`: synthesized FAANG/open-source template library.
- `COLAB_GPU_GUIDE.md`: optional Colab/GPU evidence guide.
- `BROWSER_ACCESS.md`: browser, dashboard, and log access boundary.
- `SECURITY_MODEL.md` and `THREAT_MODEL.md`: security and risk references.
- `research/ML_TEMPLATE_RESEARCH.md`: ML/reproducibility template source research.
- `research/OPS_AGENT_TEMPLATE_RESEARCH.md`: ops/agent reliability template source research.

## Evidence and safety rules

Every completion should include a gate scorecard with:

- gate;
- command or check;
- exit code or artifact inspection result;
- artifact paths when applicable;
- verdict: `PASS`, `FAIL`, `PARTIAL`, `BLOCKED`, `NOT_APPLICABLE`, or `PASS_WITH_CAVEAT`;
- rationale.

Benchmark, performance, latency, throughput, GPU, Colab, release, deploy, production, model metric, accuracy, F1, AUC, and speedup claims require real measured artifacts. A script, mock-only test, template, or README statement is not enough.

## Related docs

- Operator runbook: `docs/office-superpowers/OPERATOR_RUNBOOK.md`
- Template library: `docs/office-superpowers/TEMPLATE_LIBRARY.md`
- Colab/GPU guide: `docs/office-superpowers/COLAB_GPU_GUIDE.md`
- Browser access guide: `docs/office-superpowers/BROWSER_ACCESS.md`
- Deployment runbook: `docs/office-superpowers/DEPLOYMENT.md`
