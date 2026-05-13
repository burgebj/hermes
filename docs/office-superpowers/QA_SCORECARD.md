# QA Scorecard: Akhil Default Profile Superpowers

Task: `t_28b8e722`
Role: independent QA verification
Workspace: `/Users/akhilkinnera/Documents/My Workspace/Hermes/hermes-agent`
Generated: 2026-05-13

## Scope

Independently verified the 10 superpower areas in `docs/akhil-default-profile-superpowers-plan.md` using existing Python/shell tooling only. No npm/pnpm/yarn/npx/package install commands were run.

## Executive verdict

Overall: PASS_WITH_CAVEAT

The implementation and docs provide useful current-state Office superpowers: diagnostics, watchdog findings, redacted reporting/outbox, evidence gate validation, template research, GPU/Colab guidance, browser-access boundaries, and YOLO/default-profile policy. Caveats are operational and already visible in the evidence: live Telegram delivery is documented/represented by an outbox path rather than proven with a real send in this QA run; the profile-scoped cron watchdog is not installed for this QA profile (`runner_exists=false`); and watchdog repair behavior is diagnostic/dry-run in the checks below, not destructive auto-repair.

No `SCOPE_CHANGE_REQUEST` is needed for this QA task because all requested verification gates were either directly tested or documented with explicit caveats.

## Exact commands, exit codes, and artifacts

| # | Command/check | Exit code | Artifact(s) | Result summary |
|---|---|---:|---|---|
| 1 | `kanban_show(task_id="t_28b8e722")` | n/a tool success | Kanban worker context | Loaded acceptance criteria, constraints, and parent evidence before testing. |
| 2 | `python3 -m py_compile hermes_cli/office_superpowers.py scripts/office_doctor.py scripts/office_watchdog.py scripts/office_report_outbox.py scripts/office_scorecard_validate.py scripts/office_watchdog_cron.py scripts/office_watchdog_cron_install.py` | 0 | terminal output | All office-superpowers scripts/modules compile. |
| 3 | `python3 -m pytest tests/hermes_cli/test_office_superpowers.py tests/hermes_cli/test_office_verifier.py tests/cron/test_cron_no_agent.py tests/tools/test_cronjob_tools.py -q -o 'addopts='` | 0 | terminal output: `77 passed in 1.09s` | Targeted unit/regression tests passed, including redaction, evidence gates, watchdog cases, outbox idempotence, verifier policy, and cron no-agent coverage. |
| 4 | `python3 scripts/office_doctor.py --json > /tmp/hermes-office-qa/office_doctor.json` | 0 | `/tmp/hermes-office-qa/office_doctor.json` | Office Doctor runs and reports useful data. JSON parsed; `overall_status=warn`; 10 sections include runtime, gateway, messaging, kanban_board, worker profiles, notifications, evidence gates, logs, browser_dashboard, recommendations. Warns are actionable/expected for gateway/messaging/browser boundary visibility. |
| 5 | `python3 scripts/office_watchdog.py --dry-run --json > /tmp/hermes-office-qa/office_watchdog_dry_run.json` | 1 | `/tmp/hermes-office-qa/office_watchdog_dry_run.json` | Dry-run watchdog JSON parsed. Nonzero exit reflects actionable current-board findings, not malformed output. Summary: 21 findings, 4 errors, 17 warnings; issue types observed include `nonspawnable_assignee` and `missing_gate_scorecard`. |
| 6 | Synthetic watchdog matrix: inline Python creating stale/routine-blocked/ready-no-assignee/nonspawnable/done-no-scorecard/repeated-failure/outbox-backlog/secret-risk fixtures, then `build_watchdog_report(..., dry_run=True, outbox_path=...) > /tmp/hermes-office-qa/watchdog_synthetic_matrix.json` | 0 | `/tmp/hermes-office-qa/watchdog_synthetic_matrix.json` | Verified watchdog logic detects `stale_running_claim`, `blocked_protocol_violation`, `ready_task_not_spawning`, `nonspawnable_assignee`, `missing_gate_scorecard`, `repeated_failure_cluster`, `outbox_backlog`, and `secret_risk_payload`. |
| 7 | `python3 scripts/office_report_outbox.py --help | tee /tmp/hermes-office-qa/office_report_outbox_help.txt` | 0 | `/tmp/hermes-office-qa/office_report_outbox_help.txt` | Telegram/reporting outbox CLI exposes `status`, `enqueue`, `send-due`, and `retry-failed` commands. |
| 8 | `python3 scripts/office_report_outbox.py status --json > /tmp/hermes-office-qa/office_outbox_status.json` | 0 | `/tmp/hermes-office-qa/office_outbox_status.json` | Outbox status smoke parsed: default profile outbox path is `/Users/akhilkinnera/Documents/My Workspace/Hermes/.hermes/profiles/qa/office/report-outbox.jsonl`, `exists=false`, `total=0`, `counts={}`. This verifies the path/status smoke, not a live Telegram send. |
| 9 | `python3 scripts/office_watchdog_cron_install.py status > /tmp/hermes-office-qa/office_watchdog_cron_status.json` | 0 | `/tmp/hermes-office-qa/office_watchdog_cron_status.json` | Profile-scoped cron status JSON parsed: `runner_exists=false`, `jobs=0`. This is a deployment caveat, not a failure of the QA smoke. |
| 10 | `python3 scripts/office_watchdog_cron_install.py smoke --json > /tmp/hermes-office-qa/office_watchdog_cron_smoke.json` | 0 | `/tmp/hermes-office-qa/office_watchdog_cron_smoke.json` | Cron smoke wrapper returned `ok=true`; embedded runner `returncode=1` due to current watchdog alerts, which is expected/actionable. |
| 11 | `python3 scripts/office_scorecard_validate.py --json-file docs/office-superpowers/DOCS_GATE_SCORECARD.json --workspace "$PWD" --json > /tmp/hermes-office-qa/docs_gate_scorecard_validate.json` | 0 | `/tmp/hermes-office-qa/docs_gate_scorecard_validate.json` | Docs gate scorecard validates: `ok=true`, 0 errors, 0 warnings. |
| 12 | `python3 scripts/office_scorecard_validate.py --json-file docs/office-superpowers/DEPLOYMENT_GATE_SCORECARD.json --workspace "$PWD" --json > /tmp/hermes-office-qa/deployment_gate_scorecard_validate.json` | 0 | `/tmp/hermes-office-qa/deployment_gate_scorecard_validate.json` | Deployment scorecard validates: `ok=true`, 0 errors, 0 warnings. |
| 13 | Refined static docs audit over README, runbook, template library, ML/ops research, browser guide, operator policy, security/threat model, Telegram contract, and Colab guide: output to `/tmp/hermes-office-qa/docs_static_audit_refined.json` | 0 | `/tmp/hermes-office-qa/docs_static_audit_refined.json` | Audit passed: template research useful terms present; browser boundary accurate; default policy safe; recoverability documented; Telegram contract documented; no local GPU claim; no secret-like hits. |
| 14 | `git status --short -- docs/office-superpowers hermes_cli/office_superpowers.py hermes_cli/office_verifier.py hermes_cli/office_scope.py scripts/office_doctor.py scripts/office_watchdog.py scripts/office_report_outbox.py scripts/office_scorecard_validate.py scripts/office_watchdog_cron.py scripts/office_watchdog_cron_install.py tests/hermes_cli/test_office_superpowers.py tests/hermes_cli/test_office_verifier.py package.json package-lock.json pnpm-lock.yaml yarn.lock > /tmp/hermes-office-qa/git_status_scoped.txt` | 0 | `/tmp/hermes-office-qa/git_status_scoped.txt` | Scoped status shows office docs/scripts/tests untracked, and zero package/lockfile status lines. |
| 15 | `git diff -- package.json package-lock.json pnpm-lock.yaml yarn.lock > /tmp/hermes-office-qa/package_lock_diff.txt` | 0 | `/tmp/hermes-office-qa/package_lock_diff.txt` | Package/lockfile diff is empty (`0` bytes), supporting no npm install/package mutation evidence. |

## Gate verdicts

| Gate | Verdict | Evidence | Rationale |
|---|---|---|---|
| 1. Office supervision authority | PASS | `docs/office-superpowers/references/OFFICE_OPERATOR_POLICY.md`; `docs/office-superpowers/OPERATOR_RUNBOOK.md`; targeted tests in command #3 | Policy and runbook document hands-free Office operation, blocker taxonomy, specialist routing, evidence handoff, and no-npm constraints. Tests cover blocker taxonomy and completion gates. |
| 2. Office watchdog detects stale/blocked/nonspawnable/no-report/outbox issues | PASS | `/tmp/hermes-office-qa/office_watchdog_dry_run.json`; `/tmp/hermes-office-qa/watchdog_synthetic_matrix.json`; command #3 | Synthetic matrix confirms issue types for stale running claims, blocked protocol violations, ready tasks not spawning, nonspawnable assignees, missing gate scorecards/no-report, repeated failures, outbox backlog, and secret-risk payloads. |
| 3. Telegram reporting contract/path | PASS_WITH_CAVEAT | `docs/office-superpowers/templates/TELEGRAM_REPORT_CONTRACT.md`; `/tmp/hermes-office-qa/office_report_outbox_help.txt`; `/tmp/hermes-office-qa/office_outbox_status.json` | Contract and redacted outbox/status path exist and smoke-test locally. Live Telegram send was not performed because this QA run must avoid secrets and uses the qa profile, where the outbox currently has no due records. |
| 4. Office Doctor runs and reports useful data | PASS | `/tmp/hermes-office-qa/office_doctor.json` | Doctor exits 0, emits valid JSON, and reports runtime, gateway, messaging, board stats, worker profiles, notifications, evidence gates, logs, browser/dashboard, and recommendations. |
| 5. GPU strategy | PASS | `docs/office-superpowers/COLAB_GPU_GUIDE.md`; `/tmp/hermes-office-qa/docs_static_audit_refined.json` | Docs explicitly state no local GPU and position Colab as optional remote evidence; no local GPU proof is claimed. |
| 6. FAANG-level templates research exists and is useful | PASS | `docs/office-superpowers/TEMPLATE_LIBRARY.md`; `docs/office-superpowers/research/ML_TEMPLATE_RESEARCH.md`; `docs/office-superpowers/research/OPS_AGENT_TEMPLATE_RESEARCH.md`; `/tmp/hermes-office-qa/docs_static_audit_refined.json` | Research and template library cover DVC, MLflow, Hugging Face, MLCommons, SRE/runbooks, transactional outbox, and license cautions. |
| 7. Truth-over-completion evidence gates | PASS | `tests/hermes_cli/test_office_verifier.py`; `/tmp/hermes-office-qa/docs_gate_scorecard_validate.json`; `/tmp/hermes-office-qa/deployment_gate_scorecard_validate.json` | Tests reject benchmark/release/deploy claims without real artifacts, validate exact scorecard fields, and block scope changes/completions until evidence/review gates pass. |
| 8. Memory/skills discipline | PASS_WITH_CAVEAT | `docs/office-superpowers/references/OFFICE_OPERATOR_POLICY.md`; parent docs context; no memory writes in this QA task | Policy and docs include discipline around evidence and reusable workflow references. QA did not create new memories because this task produced task-specific evidence, not durable future preferences or reusable procedure changes. |
| 9. Browser/dashboard/log access boundary | PASS | `docs/office-superpowers/BROWSER_ACCESS.md`; `docs/office-superpowers/references/BROWSER_DASHBOARD_LOG_ACCESS.md`; Doctor `browser_dashboard` section in `/tmp/hermes-office-qa/office_doctor.json` | Browser automation is correctly documented as a controlled session, not unrestricted Akhil Chrome/cookie/private-dashboard access. Dashboard/log claims require route/status/log evidence and redaction. |
| 10. Autonomy/default-profile policy safe and recoverable | PASS_WITH_CAVEAT | `docs/office-superpowers/references/OFFICE_OPERATOR_POLICY.md`; `docs/office-superpowers/OPERATOR_RUNBOOK.md`; `docs/office-superpowers/DEPLOYMENT.md`; `/tmp/hermes-office-qa/docs_static_audit_refined.json` | Policy is safe on blockers/no-npm/evidence. Recoverability is documented across runbook/deployment via repair/reroute/rollback/restore/revert guidance; it is not a single enforceable code-level rollback mechanism in this QA run. |
| No secret exposure | PASS | `/tmp/hermes-office-qa/docs_static_audit_refined.json`; command #3 redaction tests | Static audit found zero secret-like hits after allowing safe prose such as authorization-header examples; unit tests verify token/cookie/private-key redaction. |
| No npm install / no JS package mutation | PASS | `/tmp/hermes-office-qa/git_status_scoped.txt`; `/tmp/hermes-office-qa/package_lock_diff.txt` | No npm/pnpm/yarn/npx commands were run by QA. Package/lockfile diff is empty and scoped status has zero package/lockfile status lines. |

## JSON scorecard

```json office_gate_scorecard
{
  "schema_version": 1,
  "task_id": "t_28b8e722",
  "overall_verdict": "PASS_WITH_CAVEAT",
  "gates": [
    {
      "gate": "Office Doctor runs and reports useful data",
      "command_or_check": "python3 scripts/office_doctor.py --json > /tmp/hermes-office-qa/office_doctor.json",
      "exit_code_or_artifact": "exit 0; valid JSON; overall_status=warn; section_count=10; artifact=/tmp/hermes-office-qa/office_doctor.json",
      "artifact_paths": ["/tmp/hermes-office-qa/office_doctor.json"],
      "verdict": "PASS",
      "rationale": "Doctor emits actionable diagnostics without printing credentials. Warn status reflects current gateway/messaging/browser-boundary caveats."
    },
    {
      "gate": "Watchdog detects stale blocked nonspawnable no-report outbox issues",
      "command_or_check": "python3 scripts/office_watchdog.py --dry-run --json > /tmp/hermes-office-qa/office_watchdog_dry_run.json; synthetic inline Python matrix > /tmp/hermes-office-qa/watchdog_synthetic_matrix.json",
      "exit_code_or_artifact": "watchdog dry-run exit 1 with valid findings; synthetic matrix exit 0 and includes stale_running_claim, blocked_protocol_violation, ready_task_not_spawning, nonspawnable_assignee, missing_gate_scorecard, repeated_failure_cluster, outbox_backlog, secret_risk_payload",
      "artifact_paths": ["/tmp/hermes-office-qa/office_watchdog_dry_run.json", "/tmp/hermes-office-qa/watchdog_synthetic_matrix.json"],
      "verdict": "PASS",
      "rationale": "Dry-run and synthetic tests cover the requested watchdog classes; nonzero dry-run exit is expected when actionable findings exist."
    },
    {
      "gate": "Telegram reporting path documented or smoke-tested",
      "command_or_check": "python3 scripts/office_report_outbox.py --help; python3 scripts/office_report_outbox.py status --json > /tmp/hermes-office-qa/office_outbox_status.json",
      "exit_code_or_artifact": "both exit 0; outbox status total=0 path=/Users/akhilkinnera/Documents/My Workspace/Hermes/.hermes/profiles/qa/office/report-outbox.jsonl; docs template exists",
      "artifact_paths": ["/tmp/hermes-office-qa/office_report_outbox_help.txt", "/tmp/hermes-office-qa/office_outbox_status.json", "docs/office-superpowers/templates/TELEGRAM_REPORT_CONTRACT.md"],
      "verdict": "PASS_WITH_CAVEAT",
      "rationale": "Local contract/status path is verified; live Telegram sending was not attempted in QA to avoid credential/PII exposure."
    },
    {
      "gate": "Templates research exists and is useful",
      "command_or_check": "refined static docs audit > /tmp/hermes-office-qa/docs_static_audit_refined.json",
      "exit_code_or_artifact": "exit 0; ok=true; template/research terms present",
      "artifact_paths": ["/tmp/hermes-office-qa/docs_static_audit_refined.json", "docs/office-superpowers/TEMPLATE_LIBRARY.md", "docs/office-superpowers/research/ML_TEMPLATE_RESEARCH.md", "docs/office-superpowers/research/OPS_AGENT_TEMPLATE_RESEARCH.md"],
      "verdict": "PASS",
      "rationale": "Docs include production-grade ML/ops template research and operational template vocabulary."
    },
    {
      "gate": "Browser access boundary accurate",
      "command_or_check": "manual/source-backed inspection plus refined static docs audit",
      "exit_code_or_artifact": "audit exit 0; browser_boundary_accurate=true; Doctor browser_dashboard section present",
      "artifact_paths": ["/tmp/hermes-office-qa/docs_static_audit_refined.json", "docs/office-superpowers/BROWSER_ACCESS.md", "docs/office-superpowers/references/BROWSER_DASHBOARD_LOG_ACCESS.md", "/tmp/hermes-office-qa/office_doctor.json"],
      "verdict": "PASS",
      "rationale": "Docs state controlled browser automation is not unrestricted logged-in Chrome/profile/cookie access and require evidence for dashboard/log claims."
    },
    {
      "gate": "No secret exposure and no npm install evidence",
      "command_or_check": "python3 -m pytest targeted tests; refined static docs audit; git status scoped; git diff package/lockfiles",
      "exit_code_or_artifact": "tests exit 0 (77 passed); docs audit exit 0 with 0 secret hits; package_lock_diff_bytes=0; no package/lockfile status lines",
      "artifact_paths": ["/tmp/hermes-office-qa/docs_static_audit_refined.json", "/tmp/hermes-office-qa/git_status_scoped.txt", "/tmp/hermes-office-qa/package_lock_diff.txt"],
      "verdict": "PASS",
      "rationale": "Redaction tests pass, docs audit finds no secret-like durable content, and package/lockfiles are unmodified. QA did not run npm/pnpm/yarn/npx/install commands."
    },
    {
      "gate": "Default-profile policy safe and recoverable",
      "command_or_check": "refined static docs audit; manual inspection of OFFICE_OPERATOR_POLICY, OPERATOR_RUNBOOK, DEPLOYMENT",
      "exit_code_or_artifact": "audit exit 0; default_policy_safe=true; recoverability_documented=true",
      "artifact_paths": ["/tmp/hermes-office-qa/docs_static_audit_refined.json", "docs/office-superpowers/references/OFFICE_OPERATOR_POLICY.md", "docs/office-superpowers/OPERATOR_RUNBOOK.md", "docs/office-superpowers/DEPLOYMENT.md"],
      "verdict": "PASS_WITH_CAVEAT",
      "rationale": "Policy is safe on blockers/evidence/no-npm, and recoverability is documented as repair/reroute/rollback guidance. QA did not prove a single automatic rollback mechanism."
    }
  ]
}
```

## Residual risks for reviewer/chief

- Live Telegram delivery remains conditional on gateway/Telegram config and should be proven by a separate credentialed smoke if release requires an end-to-end external notification.
- QA profile cron status reports `runner_exists=false`; if the product claim is persistent watchdog installation for every profile, DevOps/tooling needs profile-scoped deployment evidence.
- Watchdog output is diagnostic/dry-run in this verification. Any future auto-repair mode needs additional tests proving it only performs safe, reversible mutations.
