# Gate Scorecard: PM Spec for Default-profile Office Operator Superpowers

Status: PM specification evidence, not launch signoff. Current implementation should be described as dry-run Office diagnostics, evidence scorecard validation, and a local watchdog runner; live notification, autonomous safe repair/reassignment/unblock behavior, and whole-system security-boundary enforcement remain follow-up work.

## Evidence summary

| Gate | Command/check | Exit code / artifact | Verdict | Rationale |
|---|---|---:|---|---|
| Source plan read | `read_file docs/akhil-default-profile-superpowers-plan.md` | Artifact: source plan, 39 lines | PASS | Requirements and constraints were extracted from the requested source document. |
| PRD created | File artifact check | `docs/office-superpowers/PRD.md` | PASS | PRD contains goal, user, problem, solution, requirements, acceptance gates, milestones, risks, and done definition. |
| Task graph created | File artifact check | `docs/office-superpowers/TASK_GRAPH.md` | PASS | Task graph defines downstream work packages, owners, dependencies, sequencing, and cross-package release gates. |
| Scorecard created | File artifact check | `docs/office-superpowers/GATE_SCORECARD.md` | PASS | This file records evidence, checks, verdicts, and remaining validation expectations. |
| No npm installs | Session command review | No npm/pnpm/yarn/npx install commands used | PASS | This PM task used file tools and Python/shell verification only; no JS package command was run. Constraint prose mentions banned commands so downstream workers know not to run them. |
| No local GPU claim | Content review | PRD and task graph artifacts | PASS | Docs explicitly state no local GPU is available and Colab is optional only. |
| Secrets/PII safety | `python3` regex scan over `docs/office-superpowers/*.md` | Exit 0: `SECRET_SCAN_PASS no token/credential patterns found` | PASS | Docs contain policy language and `[REDACTED]` placeholder only; no token/credential patterns were found. |
| Artifact/keyword verification | `python3` file and required-term check | Exit 0: PRD 17489 bytes/273 lines; GATE_SCORECARD 7049 bytes/127 lines before this update; TASK_GRAPH 10018 bytes/207 lines; `VERIFICATION_PASS` | PASS | Required artifacts exist and include required superpower/constraint terms. Initial `python` invocation failed with exit 127 because `python` is not installed; reran with `python3` successfully. |
| Git workspace evidence | `git status --short docs/office-superpowers docs/akhil-default-profile-superpowers-plan.md && git diff -- docs/office-superpowers` | Exit 0; output shows `?? docs/office-superpowers/` and source plan currently untracked | PASS | Created docs are visible as untracked workspace artifacts. `git diff` is empty because the docs are new untracked files. |
| Browser access boundary | Content review | PRD R9 and constraints | PASS | Browser automation is documented as available tooling, not unrestricted logged-in Chrome profile control. |
| YOLO autonomy preserved | Content review | PRD R10 and constraints | PASS | Hands-free operation is default, with real blockers and SCOPE_CHANGE_REQUEST behavior defined. |

## Required superpower acceptance gates

### 1. Office supervision authority
Verdict: PASS for PM specification.

Acceptance gates defined:
- Inspect stale/crashed Kanban state with task id, run id, assignee, failure mode, and next action.
- For target implementation: reclaim/unblock/reassign routine issues with durable rationale and no secrets. For current implementation: report/recommend these actions only unless a reviewed repair path exists.
- Preserve reviewer/QA/security gates without treating routine review as human blocker.

### 2. Office watchdog
Verdict: PASS for PM specification.

Acceptance gates defined:
- Detect stale running tasks, blocked protocol violations, ready tasks not spawning, nonspawnable assignees, missing reports, repeated crashes, and notification backlog.
- Report issue type, affected task/run/assignee, severity, and recommended repair.
- Stay low-noise when healthy.
- Run without npm installs or local GPU.

### 3. Telegram/report outbox
Verdict: PASS for schema/queued-intent specification; live delivery explicitly deferred.

Acceptance gates defined:
- Message schemas for started, blocked, completed, QA-failed, and scope-change.
- Include task title/id, state, concise evidence, safe artifact paths, and next action.
- Redact secrets/tokens/raw PII as `[REDACTED]`.
- Distinguish real blockers from routine review gates.
- Treat `send-due` and `retry-failed` as queued/dry-run previews until a reviewed live sender and smoke artifact exist.

### 4. Office Doctor
Verdict: PASS for PM specification.

Acceptance gates defined:
- Output sections for gateway, Telegram/Slack, Kanban board, workers, notifications, logs, browser/dashboard, and recommendations.
- Redact secrets and raw credential values.
- Exit zero when healthy and non-zero for actionable unhealthy states.
- Use existing Python/shell tooling only.

### 5. Colab/GPU policy
Verdict: PASS for PM specification.

Acceptance gates defined:
- State CPU-sufficient, Colab-optional, or GPU-required per task.
- If GPU proof is required and unavailable, emit SCOPE_CHANGE_REQUEST instead of claiming success.
- Do not claim local GPU reproducibility.
- Document Colab artifact capture and secret hygiene.

### 6. FAANG template research
Verdict: PASS for PM specification.

Acceptance gates defined:
- Research package includes source criteria, license checks, comparison dimensions, and synthesis outputs.
- Cover ML projects, agent systems, reproducibility, docs, model cards, evals, and runbooks.
- Block on legal/license ambiguity.
- No npm installs for synthesis.

### 7. Evidence gates
Verdict: PASS for PM specification.

Acceptance gates defined:
- Every completion includes commands/checks, exit codes or artifact-check results, artifact paths, verdicts, and rationale.
- Benchmark/performance/release/deploy claims require real measured artifacts.
- Mock-only tests, README prose, and template-only scripts do not satisfy heavy claims.
- Unmet requirements require parseable SCOPE_CHANGE_REQUEST.

### 8. Skill/memory discipline
Verdict: PASS for PM specification.

Acceptance gates defined:
- Reusable multi-step workflows become skills.
- Stable facts may become compact declarative memory.
- Temporary task progress, PR/issue numbers, commit SHAs, and phase-completion logs are not saved to memory.
- Loaded stale/incomplete skills are patched.

### 9. Browser/dashboard/log access
Verdict: PASS for PM specification.

Acceptance gates defined:
- Document browser automation boundary and logged-in profile limitations.
- Document safe dashboard/API/log inspection routes.
- Include browser/dashboard/log diagnostics in Office Doctor.
- Block honestly when human login or specific browser profile is required.

### 10. Autonomy policy
Verdict: PASS for PM specification.

Acceptance gates defined:
- Hands-free repair/reroute is default.
- Ask/block only for credentials, paid/cloud permissions, destructive irreversible actions, legal/license ambiguity, missing runtime/hardware, unverifiable claims, or explicit approval mode.
- No silent scope reduction.
- Reviewer/QA/security gates are preserved.

## Scope-change assessment
No SCOPE_CHANGE_REQUEST is required for this PM task.

Reason:
- The task requested PM deliverables and acceptance gates, not live implementation of watchdog, Doctor, Telegram delivery, browser automation, or GPU proof.
- Unsafe or impossible authorities were constrained rather than granted: no local GPU claim, no unrestricted Chrome profile control, no secrets in durable artifacts, no npm installs, and real blocker taxonomy retained.

## Remaining downstream validation gates
These are intentionally not claimed as complete by this PM task and must be validated by downstream implementation/review work:
- Live watchdog detection against seeded Kanban states.
- Live Office Doctor command output and exit code behavior.
- Telegram status delivery smoke test through configured gateway credentials.
- Security review of redaction behavior in generated messages/logs.
- QA/evals enforcement of scorecard and SCOPE_CHANGE_REQUEST formats.
- FAANG template source/license review.
- Colab notebook or guidance artifact review for GPU-heavy workflows.

## Final PM verdict
PASS: The requested PM specification artifacts are created and cover all required superpower areas, constraints, risks, and acceptance gates. Downstream architecture, implementation, security, QA/evals, docs, and research tasks should proceed from TASK_GRAPH.md.
