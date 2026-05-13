# Implementation Plan: Default-profile Office Operator Superpowers

Status: proposed implementation plan
Last verified: 2026-05-13T00:39:21Z
Source task: t_18c840af

## Scope

This plan turns the Office superpowers architecture into small PR-sized implementation slices. It is intentionally Python/shell-first and does not require npm installs, local GPU, or new JavaScript packages.

Deliverables covered:
- default-profile operator authority boundaries
- Office watchdog data model and repair actions
- Office Doctor CLI/script output
- Telegram reporting contract
- evidence gate schema/artifacts
- Colab/GPU policy
- browser/dashboard/log access boundary
- skill/memory maintenance loop
- exact files/scripts/modules to edit
- no-npm testing plan
- rollback plan

## Implementation principles

- Build read-only diagnostics before repair actions.
- Use existing Kanban state and gateway facilities before adding new storage.
- Put policy and redaction in shared helpers so Doctor, watchdog, outbox, and tests use the same logic.
- Keep live Telegram delivery optional in tests; unit tests validate the contract without credentials.
- Any schema migration must be separately reviewed; JSONL outbox is acceptable for MVP.
- All durable artifacts must redact secrets and raw PII as `[REDACTED]`.
- Every PR must include a gate scorecard and commands/checks with exit codes or artifact results.

## Exact files/modules to edit or add

### New files

1. `docs/office-superpowers/ARCHITECTURE.md`
   - Architecture, components, data model, control flow, boundaries, failure modes, tests, rollout.
2. `docs/office-superpowers/IMPLEMENTATION_PLAN.md`
   - This plan.
3. `docs/office-superpowers/SECURITY_MODEL.md`
   - Threat model, permission boundary, redaction rules, approval blockers.
4. `scripts/office_scorecard_validate.py`
   - Python stdlib validator for scorecards, heavy claims, scope-change blocks, and secret patterns.
5. `scripts/office_doctor.py`
   - Terminal/JSON health diagnostic for Office/Kanban/gateway/messaging/log/browser state.
6. `scripts/office_watchdog.py`
   - Dry-run and routine-repair watchdog for stale/risky Office states.
7. `scripts/office_report_outbox.py`
   - JSONL or SQLite-backed redacted notification outbox and sender/status utility.
8. `docs/office-superpowers/templates/OFFICE_GATE_SCORECARD_TEMPLATE.md`
   - Reusable scorecard template for workers.
9. `docs/office-superpowers/templates/OFFICE_RUNBOOK_TEMPLATE.md`
   - Runbook template for Office workflows.
10. `docs/office-superpowers/templates/COLAB_GPU_POLICY_TEMPLATE.md`
    - GPU classification and Colab artifact capture template.
11. `docs/office-superpowers/references/OFFICE_OPERATOR_POLICY.md`
    - User-facing operator policy and blocker taxonomy.
12. `tests/hermes_cli/test_office_scorecard_validate.py`
    - Validator unit tests.
13. `tests/hermes_cli/test_office_doctor.py`
    - Doctor output, JSON, exit-code, redaction tests.
14. `tests/hermes_cli/test_office_watchdog.py`
    - Seeded board findings and repair-policy tests.
15. `tests/hermes_cli/test_office_report_outbox.py`
    - Outbox idempotency, redaction, retry, missing config tests.
16. `tests/hermes_cli/test_office_policy.py`
    - Blocker taxonomy and auto-repair allowlist tests.

### Existing files likely to edit

1. `hermes_cli/commands.py`
   - Add CLI registry entry only if exposing `office` as a first-class command or adding `doctor --office` alias. For MVP scripts, this can wait.
2. `hermes_cli/main.py`
   - Wire new top-level command only if not using scripts-only MVP.
3. `hermes_cli/doctor.py`
   - Optional: add `--office` section that calls shared Office Doctor helpers after script MVP stabilizes.
4. `hermes_cli/kanban_db.py`
   - Prefer read-only helper functions first. Add schema tables only in a later reviewed migration.
5. `hermes_cli/kanban.py`
   - Optional: add output helpers for Office diagnostics if needed.
6. `gateway/run.py`
   - Later integration: emit/consume Office report outbox or expose a report-send hook.
7. `gateway/platforms/telegram.py`
   - Avoid direct changes unless gateway/builder identifies a missing send primitive. Use existing send-message facilities first.
8. `hermes_cli/config.py`
   - Add `office.*` default config only after MVP validates fields.
9. `website/docs/user-guide/features/kanban.md`
   - Later docs update after scripts/CLI are real.
10. `AGENTS.md`
    - Only update if Office policy becomes general repo guidance; do not modify during MVP unless requested.

### Existing files to inspect but avoid editing unless necessary

- `tools/kanban_tools.py`: worker-facing Kanban tools; avoid expanding unless agent tool surface must include Office actions.
- `tests/hermes_cli/test_kanban_*.py`: patterns for fixture boards and DB assertions.
- `tests/gateway/test_kanban_notifier.py`: patterns for notification tests.
- `hermes_cli/kanban_diagnostics.py`: reuse if it already exposes board diagnostics.
- `hermes_constants.py`: use `get_hermes_home()` / root helpers; do not hardcode `~/.hermes`.

## Milestones and PR slices

### PR 0: docs/contracts only

Owner: architect/docs

Files:
- `docs/office-superpowers/ARCHITECTURE.md`
- `docs/office-superpowers/IMPLEMENTATION_PLAN.md`
- `docs/office-superpowers/SECURITY_MODEL.md`

Acceptance gates:
- All requested architecture sections present.
- Exact implementation files and testing plan listed.
- No runtime behavior changes.
- Secret scan passes.
- No npm commands used.

Suggested check:
```bash
python3 - <<'PY'
from pathlib import Path
required = [
    'docs/office-superpowers/ARCHITECTURE.md',
    'docs/office-superpowers/IMPLEMENTATION_PLAN.md',
    'docs/office-superpowers/SECURITY_MODEL.md',
]
for p in required:
    path = Path(p)
    assert path.exists(), p
    text = path.read_text(encoding='utf-8')
    assert len(text) > 1000, p
print('office docs present')
PY
```

### PR 1: shared policy/redaction/scorecard validator

Owner: QA/evals + backend-tooling

Files:
- Add `scripts/office_scorecard_validate.py`
- Add `tests/hermes_cli/test_office_scorecard_validate.py`
- Add `tests/hermes_cli/test_office_policy.py`
- Optionally add shared module `hermes_cli/office_superpowers.py`

Implementation details:
- Use Python stdlib only: `argparse`, `json`, `re`, `pathlib`, `dataclasses`, `hashlib`, `datetime`.
- Input modes: `--json-file`, `--markdown-file`, `--stdin`.
- Output modes: text and `--json`.
- Exit codes: 0 pass, 1 validation failure, 2 unsafe secret risk or unparseable required schema.
- Include a reusable `redact_text(text: str) -> tuple[str, RedactionStatus]` helper.
- Include heavy-claim keyword detector for benchmark/performance/release/deploy/GPU/model metric claims.
- Include local artifact existence checks when paths are local and expected.

Acceptance gates:
- Valid sample scorecard passes.
- Missing required keys fail.
- Invalid verdict enum fails.
- Heavy claim with no artifact fails.
- SCOPE_CHANGE_REQUEST block parses.
- Secret-like sample strings are redacted or unsafe-blocked.

No-npm test command:
```bash
scripts/run_tests.sh tests/hermes_cli/test_office_scorecard_validate.py tests/hermes_cli/test_office_policy.py -v --tb=short
```

### PR 2: Office Doctor MVP, diagnostic-only

Owner: backend-tooling / DevOps

Files:
- Add `scripts/office_doctor.py`
- Add `tests/hermes_cli/test_office_doctor.py`
- Optionally factor shared helpers into `hermes_cli/office_health.py`

Implementation details:
- Read Kanban board via `hermes_cli.kanban_db` helper functions; do not shell out to `hermes kanban` from tests.
- Gateway health: use existing `gateway.status.get_running_pid()` when importable, and config `kanban.dispatch_in_gateway` from `hermes_cli.config.load_config()`.
- Messaging health: check presence/config shape only, never print credential values. It is acceptable to report `configured_unknown` or `not_configured`.
- Logs: print paths under Hermes home and redacted tail summaries only if safe; large log tail should be opt-in.
- Browser/dashboard: print boundary and known local dashboard/API route checks if safe to probe.
- JSON output follows `schema_version: 1` contract.
- Exit code: 0 healthy/info, 1 local actionable repair, 2 external blocker/unsafe secret.

Required terminal sections:
- Runtime
- Gateway
- Messaging
- Kanban board
- Workers/profiles
- Notifications
- Evidence gates
- Logs
- Browser/dashboard
- Recommendations

Acceptance gates:
- Plain output contains every required section.
- JSON output validates expected keys.
- Redaction test proves no token value is printed.
- Healthy synthetic state exits 0.
- Seeded stale/outbox state exits non-zero with recommendation.

No-npm test command:
```bash
scripts/run_tests.sh tests/hermes_cli/test_office_doctor.py -v --tb=short
```

Manual smoke:
```bash
python3 scripts/office_doctor.py --json
python3 scripts/office_doctor.py
```

### PR 3: Watchdog dry-run

Owner: orchestration-builder / backend-tooling

Files:
- Add `scripts/office_watchdog.py`
- Add `tests/hermes_cli/test_office_watchdog.py`
- Reuse `hermes_cli/office_health.py` if introduced.

Implementation details:
- First mode only: `--dry-run --json` and text summary.
- Inputs: Kanban tasks/runs/comments/events, claim TTL, dispatcher status, outbox status file if present.
- Findings are derived using the architecture's `office_health_finding` schema.
- No mutation by default.
- `--repair-routine` flag exists but can initially error with a clear message until PR 5.

Seeded test cases:
- stale running claim
- repeated crash cluster
- ready task not spawning
- nonspawnable assignee
- blocked protocol violation
- missing scorecard/report
- outbox backlog
- secret-risk payload

Acceptance gates:
- Each seeded case produces expected `issue_type`, severity, task id, and recommendation.
- Healthy board produces no actionable findings or low-noise summary.
- No raw secrets in output.
- No npm/local GPU dependency.

No-npm test command:
```bash
scripts/run_tests.sh tests/hermes_cli/test_office_watchdog.py -v --tb=short
```

Manual smoke:
```bash
python3 scripts/office_watchdog.py --dry-run --json
```

### PR 4: Report outbox MVP

Owner: gateway/builder + security review

Files:
- Add `scripts/office_report_outbox.py`
- Add `tests/hermes_cli/test_office_report_outbox.py`
- Optionally add docs template for report payloads.

Implementation details:
- Start with JSONL storage under Kanban home or board directory to avoid DB migration risk.
- Commands:
  - `enqueue --type completed --task-id ... --run-id ... --payload-file ...`
  - `status --json`
  - `send-due --dry-run`
  - `retry-failed --dry-run`
- Compute idempotency key from board/task/run/report_type/payload_hash.
- Redact before writing payload.
- Missing Telegram/gateway config sets status `blocked_external_config`; it does not fail task completion or claim delivery.
- Sender should use existing Hermes messaging/gateway mechanisms only after gateway/builder confirms safe interface.

Acceptance gates:
- Duplicate enqueue does not create duplicate send intent.
- Redaction removes token/cookie/private-key samples.
- Missing config produces `blocked_external_config` and safe error.
- Retry fields advance predictably.
- Status output shows counts and oldest age but not raw payload by default.

No-npm test command:
```bash
scripts/run_tests.sh tests/hermes_cli/test_office_report_outbox.py -v --tb=short
```

### PR 5: routine repair mode

Owner: orchestration-builder + permission-gateway + QA

Files:
- Update `scripts/office_watchdog.py`
- Update shared policy helpers.
- Add tests for mutation actions.

Implementation details:
- Add `--repair-routine` with explicit allowlist:
  - write audit comment
  - retry due outbox sends
  - route reviewer/QA/security child task
  - unblock protocol-only review-required block when evidence exists and no real blocker remains
  - reassign nonspawnable assignee to explicitly configured equivalent profile
- Deny by default:
  - archive/delete task
  - destructive workspace commands
  - credential changes
  - paid/cloud actions
  - legal/license decisions
  - production deploys
- Require `--confirm-routine-policy` or config `office.operator.routine_repair_mode=repair_routine` for non-dry-run.

Acceptance gates:
- All allowed actions create audit comments.
- Denied actions return blocked recommendations.
- Repairs are idempotent on repeated invocation.
- Tests verify role-boundary preservation.

No-npm test command:
```bash
scripts/run_tests.sh tests/hermes_cli/test_office_watchdog.py tests/hermes_cli/test_office_policy.py -v --tb=short
```

### PR 6: CLI integration and docs templates

Owner: docs + CLI/tooling

Files:
- Add templates under `docs/office-superpowers/templates/`.
- Optionally update `hermes_cli/commands.py`, `hermes_cli/main.py`, `hermes_cli/doctor.py`.
- Optionally update website docs after scripts stabilize.

Implementation details:
- If adding CLI command, prefer:
  - `hermes doctor --office`
  - or `hermes office doctor`, `hermes office watchdog`, `hermes office outbox`
- Keep scripts working even if CLI integration is not complete.
- Docs must clearly mark current vs planned behavior.

Acceptance gates:
- CLI help lists commands if integrated.
- Script entrypoints remain callable directly.
- Docs templates include required sections and warnings.
- No untested claims of live Telegram delivery or GPU proof.

No-npm test command:
```bash
scripts/run_tests.sh tests/hermes_cli/test_doctor.py tests/hermes_cli/test_office_doctor.py -v --tb=short
```

### PR 7: Telegram smoke and end-to-end QA

Owner: gateway/builder + QA/evals + security

Files:
- Tests may live in `tests/gateway/test_office_reporting.py` if gateway integration is added.
- QA artifact under `docs/office-superpowers/GATE_SCORECARD_IMPLEMENTATION.md` or similar.

Implementation details:
- Unit tests do not require credentials.
- Live Telegram smoke is conditional:
  - If configured: send a safe test status, record delivery evidence without tokens/PII.
  - If missing: record `blocked_external_config` honestly and do not fail unrelated unit tests.
- QA validates all 10 superpower acceptance gates.

Acceptance gates:
- Conditional smoke proves delivery or honest external-config block.
- Security scan passes for docs, sample messages, outbox, and logs produced by tests.
- Watchdog and Doctor seeded fixtures pass.
- Evidence validator rejects prose-only heavy claims.

No-npm test command:
```bash
scripts/run_tests.sh tests/hermes_cli/test_office_*.py tests/gateway/test_office_reporting.py -v --tb=short
```

## Data and contract details

### Operator action record

```json
{
  "schema_version": 1,
  "action_id": "hash or uuid",
  "board": "default",
  "task_id": "t_xxx",
  "run_id": 0,
  "actor_profile": "default",
  "action": "comment|reclaim|unblock|reassign|create_child|enqueue_report|retry_outbox|route_security",
  "reason": "safe concise reason",
  "evidence": ["safe artifact paths or event ids"],
  "policy_decision": "allowed|denied|requires_human|requires_specialist",
  "redaction_status": "checked|redacted|unsafe_blocked",
  "created_at": "iso8601"
}
```

### Report payload fields

```json
{
  "schema_version": 1,
  "report_type": "started|blocked|completed|qa_failed|scope_change|watchdog_digest|doctor_summary",
  "task_id": "t_xxx",
  "title": "safe title",
  "state": "started|blocked|done|qa_failed|scope_change",
  "assignee": "profile",
  "evidence_summary": "short safe summary",
  "artifact_paths": ["safe path"],
  "next_owner_or_action": "profile or action",
  "blocker_type": null,
  "redaction_status": "checked"
}
```

### Required verdict enum

Allowed scorecard verdicts:
- `PASS`
- `FAIL`
- `PARTIAL`
- `BLOCKED`
- `NOT_APPLICABLE`
- `PASS_WITH_CAVEAT`

### Real blocker enum

Allowed blocker types:
- `credentials`
- `paid_cloud_permission`
- `destructive_irreversible_action`
- `legal_license_ambiguity`
- `missing_runtime_or_hardware`
- `unverifiable_claim`
- `explicit_approval_mode`
- `unsafe_secret_or_pii`
- `human_login_or_browser_profile_required`

Routine review/QA/security pipeline work is not a human blocker by itself.

## No-npm testing plan

Global rule: do not run `npm install`, `pnpm install`, `yarn install`, `npx`, or add JS packages. Do not run web or TUI tests that require missing npm installs unless existing dependencies are already present and the task explicitly calls for them.

Preferred commands:

```bash
scripts/run_tests.sh tests/hermes_cli/test_office_scorecard_validate.py -v --tb=short
scripts/run_tests.sh tests/hermes_cli/test_office_doctor.py -v --tb=short
scripts/run_tests.sh tests/hermes_cli/test_office_watchdog.py -v --tb=short
scripts/run_tests.sh tests/hermes_cli/test_office_report_outbox.py -v --tb=short
scripts/run_tests.sh tests/hermes_cli/test_office_policy.py -v --tb=short
```

Smoke commands:

```bash
python3 scripts/office_scorecard_validate.py --help
python3 scripts/office_doctor.py --json
python3 scripts/office_watchdog.py --dry-run --json
python3 scripts/office_report_outbox.py status --json
```

Static/content checks:

```bash
python3 - <<'PY'
from pathlib import Path
required = [
    'docs/office-superpowers/ARCHITECTURE.md',
    'docs/office-superpowers/IMPLEMENTATION_PLAN.md',
    'docs/office-superpowers/SECURITY_MODEL.md',
]
for p in required:
    text = Path(p).read_text(encoding='utf-8')
    for term in ['No npm', 'redact', 'SCOPE_CHANGE_REQUEST', 'Colab', 'Telegram', 'Office Doctor', 'watchdog']:
        assert term.lower() in text.lower(), (p, term)
print('content check passed')
PY
```

Secret scan:

```bash
python3 - <<'PY'
from pathlib import Path
import re, sys
patterns = [
    re.compile(r'(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[A-Za-z0-9_./+\-=]{12,}'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'(?i)bearer\s+[A-Za-z0-9_./+\-=]{12,}'),
]
findings = []
for p in Path('docs/office-superpowers').rglob('*.md'):
    text = p.read_text(encoding='utf-8')
    for pat in patterns:
        if pat.search(text):
            findings.append(str(p))
if findings:
    print('SECRET_SCAN_FAIL', findings)
    sys.exit(1)
print('SECRET_SCAN_PASS')
PY
```

Full suite gate before merge:

```bash
scripts/run_tests.sh
```

## Rollback plan

### Docs-only rollback

If PR 0 docs are wrong:
- Revert or edit only the affected files under `docs/office-superpowers/`.
- No runtime state is changed.
- Verify with content and secret scan.

### Validator rollback

If `scripts/office_scorecard_validate.py` causes failures:
- Remove the script and tests, or disable only the new Office validator integration.
- Existing Kanban/Doctor behavior remains unaffected.
- No DB migration is involved.

### Doctor rollback

If `scripts/office_doctor.py` has false positives or crashes:
- Revert script/tests or mark command experimental.
- Since Doctor is read-only, no state repair is needed.
- Keep logs of false positive fixtures for follow-up tests.

### Watchdog dry-run rollback

If dry-run findings are noisy/wrong:
- Disable scheduling/cron integration and keep script manual-only.
- Revert finding thresholds or issue classifiers.
- No task mutations occur in dry-run.

### Outbox rollback

If JSONL outbox has bugs:
- Stop sender process/schedule.
- Preserve outbox file for audit; do not delete unless it contains unsafe data.
- Mark queued rows as `dead_letter` or move file to `*.disabled` after redaction check.
- Existing Kanban completions remain source of truth.

### Routine repair rollback

If repair mode misbehaves:
- Set config `office.operator.routine_repair_mode: dry_run` or remove the flag/scheduler.
- Revert repair PR.
- Use audit comments/action records to identify and undo reversible actions:
  - Reassign task back if still appropriate.
  - Re-block if a real blocker was incorrectly unblocked.
  - Comment correction with safe rationale.
- Destructive actions should never be in the allowlist; if they occur, treat as security incident.

### CLI integration rollback

If CLI command wiring breaks:
- Remove `office` subcommand or `doctor --office` integration.
- Keep standalone scripts if they pass tests.
- Existing Hermes CLI commands remain unaffected.

### Schema migration rollback

If a later DB migration adds Office tables:
- Migration must be additive only.
- Rollback disables readers/writers and leaves tables inert.
- Do not drop data automatically; preserve for audit.
- Provide a manual backup/restore command before migration.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
| Watchdog over-repairs | Medium | High | dry-run first, allowlist, idempotency, audit comments |
| Telegram leaks sensitive info | Medium | High | shared redaction, secret scan, payload hashes, no raw logs |
| Doctor overclaims health | Medium | Medium | clear `unknown` states, nonzero only for actionable issues, tests |
| Outbox duplicate sends | Medium | Medium | idempotency key and dedupe before send |
| Review/QA bypass | Low | High | policy forbids bypass; route child tasks instead |
| GPU false claims | Low | High | GPU decision matrix and SCOPE_CHANGE_REQUEST path |
| License ambiguity in templates | Medium | Medium | concept-only adaptation; Security/legal block before copying |
| npm supply-chain violation | Low | High | no-npm gate and session command review |

## Downstream task handoff suggestions

After architecture approval, create/route child tasks rather than scope-creeping this architecture task:

1. QA/evals: implement scorecard validator and tests.
2. Backend/tooling: implement Office Doctor MVP.
3. Orchestration-builder: implement Watchdog dry-run, then routine repair mode.
4. Gateway/builder: implement report outbox and conditional Telegram smoke.
5. Security-threat-model: review redaction, browser boundary, policy gates, and repair allowlist.
6. Documentation: create runbook, scorecard, GPU/Colab, and operator policy templates.
7. QA/reviewer: end-to-end seeded Office superpowers validation.

## Done definition for implementation program

The Office superpowers implementation is done when:
- Doctor prints all required sections, redacts secrets, and exits with documented codes.
- Watchdog detects stale/crashed/nonspawnable/blocked/missing-report/outbox/secret-risk fixture states.
- Report outbox dedupes, redacts, retries, and either sends a configured Telegram smoke or honestly reports missing external config.
- Evidence validator rejects malformed/prose-only heavy claims and accepts valid scorecards.
- Colab/GPU policy prevents local GPU claims and provides honest GPU-required blocking.
- Browser/dashboard/log boundary is visible in docs and Doctor output.
- Skill/memory maintenance rules are documented and tested via examples.
- `scripts/run_tests.sh` passes for the new test set, and full suite is run before merge.
- No npm install commands are used.
- No secrets/tokens/raw PII appear in docs, Kanban handoffs, logs, outbox samples, or Telegram samples.
