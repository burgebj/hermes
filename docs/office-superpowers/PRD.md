# PRD: Default-profile Office Operator Superpowers

Status: product requirements / target state, not proof of current implementation.

Current implementation note: as of the latest docs pass, the shipped package provides dry-run Office diagnostics, evidence scorecard validation, and a local watchdog runner. Live notification, autonomous safe repair/reassignment/unblock behavior, and whole-system security-boundary enforcement remain follow-up implementation work.

## Goal
Make the default Hermes profile, Akhil, a reliable hands-free Office/Kanban operator that can plan, inspect, recommend or perform reviewed repairs, dispatch, supervise, verify, and report work with evidence-backed honesty.

## Target user
Akhil, operating Hermes Agent Office from the default profile while delegating work to specialist Office seats through Kanban.

## Problem
Office tasks can stall, crash, silently miss reports, overclaim completion, or require manual triage even when the expected policy is YOLO/hands-free execution. The default profile needs explicit operator authority, diagnostics, reporting contracts, and evidence gates so it can recommend fixes, route specialist work, and eventually repair or reroute routine issues before asking Akhil for help.

## Solution
Create a documented product specification and executable task graph for the default-profile operator upgrade across 10 superpower areas: Office supervision, watchdog, Telegram reporting, Office Doctor, GPU/Colab policy, FAANG template research, evidence gates, skill/memory discipline, browser/dashboard/log access, and autonomy policy.

## Non-negotiable constraints
- No npm installs: do not run npm install, pnpm install, yarn install, npx, or add JavaScript packages without explicit approval.
- No local GPU claims: local GPU is unavailable; Colab may be documented as an optional GPU target.
- Secrets hygiene: keep secrets, tokens, raw PII, and credentials out of durable Kanban rows, docs, logs, and notifications; redact as `[REDACTED]`.
- YOLO/hands-free default: block only for credentials, paid/cloud permissions, destructive irreversible actions, legal/license ambiguity, missing runtime/hardware, or unverifiable claims.
- Browser boundary: browser automation can open pages, click/type, inspect console, capture screenshots, and use screenshot vision when tools are available; it is not unrestricted logged-in Chrome profile control.

## User journeys / jobs to be done
1. As Akhil, I want the default profile to inspect Office state and recommend or recover from routine failures so I do not babysit stalled cards.
2. As Akhil, I want concise Telegram status updates only when useful so I can track progress away from the computer.
3. As Akhil, I want heavy claims to require artifacts, commands, exit codes, and scorecards so I can trust completions.
4. As an Office worker, I want clear policy and acceptance gates so I know when to complete, block, escalate, or create follow-up tasks.
5. As a reviewer/QA worker, I want task handoffs and evidence to be machine-readable enough to validate without redoing discovery.

## Priority and sequencing
P0 establishes safety and control-plane correctness before broad autonomy:
1. P0: autonomy policy, supervision authority, evidence gates, secrets discipline.
2. P0: Office Doctor and watchdog diagnostics for stale/crashed/nonspawnable work.
3. P0: Telegram reporting contract for started, blocked, completed, QA-failed, and scope-change states.
4. P1: browser/dashboard/log access documentation and diagnostics.
5. P1: GPU/Colab policy and templates.
6. P2: FAANG-level template research and synthesized local references.
7. P2: memory/skills discipline refinements and reusable templates.

## Requirements
### R1 Office supervision authority
The default profile must have a documented operator role for inspecting Kanban state, identifying stuck work, reclaiming stale runs, unblocking routine protocol failures, reassigning nonspawnable seats, dispatching follow-up work, and preserving reviewer/QA gates.

Acceptance gates:
- Given a stale running card or crashed worker, when the operator inspects the board, then it identifies status, run id, assignee, failure mode, and next action.
- Given a routine review-required handoff, when the worker completed with evidence, then the operator does not block for human review unless explicit approval is required.
- Given a reassignment or unblock action, when durable records are written, then the comment explains rationale without secrets or raw PII.

### R2 Office watchdog
A local watchdog must detect stale running tasks, blocked protocol violations, ready tasks not spawning, nonspawnable assignees, missing required reports, notification outbox backlog, and repeated worker crashes.

Acceptance gates:
- Given a stale claim older than the configured TTL, the watchdog reports task id, assignee, run id, age, and proposed repair.
- Given a nonspawnable assignee with ready cards, the watchdog flags the assignee and recommends reassignment or profile repair.
- Given no actionable issue, the watchdog stays quiet or prints a low-noise healthy summary.
- Watchdog checks run without npm installs and without requiring local GPU.

### R3 Telegram reporting contract
Standardize low-noise Telegram reports for YOLO Office goals: started, blocked, completed, QA-failed, and scope-change.

Acceptance gates:
- Reports include task title/id, state, concise evidence summary, next owner/action, and artifact paths where safe.
- Reports omit secrets, tokens, raw PII, and large logs; sensitive values are redacted as `[REDACTED]`.
- Blocked reports distinguish real external blockers from routine review gates.
- Completed reports include gate scorecard path or summary.

### R4 Office Doctor
Provide a local diagnostic command/script that prints gateway health, Telegram/Slack health, board stats, stale claims, failed runs, nonspawnable tasks, notification backlog, browser/dashboard/log inspection routes, and recommended fixes.

Acceptance gates:
- Doctor output has sections for gateway, messaging, Kanban board, workers, notifications, logs, browser/dashboard access, and recommendations.
- Doctor does not print secrets or raw credential values.
- Doctor exits non-zero only for actionable unhealthy states; otherwise exits zero.
- Doctor can run with Python/shell tooling already available in the repo.

### R5 Colab/GPU policy
Document that no local GPU exists and define a Colab-first optional path for GPU-heavy proof.

Acceptance gates:
- GPU-dependent tasks state whether CPU proof is sufficient, Colab proof is optional, or GPU proof is required.
- If GPU proof is required and unavailable, the worker emits SCOPE_CHANGE_REQUEST instead of claiming success.
- Colab guidance avoids storing secrets in notebooks and does not claim local reproducibility.

### R6 FAANG template research
Create a research workflow for production-grade templates covering ML projects, agent systems, reproducibility, docs, model cards, evals, runbooks, and operational maturity.

Acceptance gates:
- Research work package names source criteria, license checks, comparison dimensions, and synthesis output.
- Local templates/reference docs are synthesized without npm installs.
- Any license or legal ambiguity blocks for human decision instead of copying unsafe material.

### R7 Truth-over-completion evidence gates
Codify hard gates for benchmark, runtime, metrics, dataset audits, model/eval claims, deployment, and release assertions.

Acceptance gates:
- Every completion includes commands/checks, exit codes or artifact-check results, paths, verdicts, and rationale.
- Benchmark/performance claims cite real artifacts such as benchmark output, JSON reports, live-server tests, or logs.
- Mock-only tests, README prose, or generated scripts do not satisfy runtime/performance/release claims.
- Scope reductions use parseable SCOPE_CHANGE_REQUEST blocks.

### R8 Skill/memory discipline
Define when reusable workflows become skills, when durable facts become memory, and what must not be saved.

Acceptance gates:
- Reusable multi-step workflows or corrected procedures are captured as skills.
- Memories are compact declarative stable facts, not temporary task progress.
- PR numbers, issue numbers, commit SHAs, and phase completion logs are not written to long-term memory.
- Skill updates happen when a loaded skill is discovered to be stale, incomplete, or wrong.

### R9 Browser/dashboard/log access
Document operational access boundaries and diagnostics for browser automation, dashboard/API inspection, and logs.

Acceptance gates:
- Browser automation boundary states available actions and logged-in Chrome profile limitations.
- Dashboard/API/log inspection routes are documented with safe redaction requirements.
- Doctor/watchdog diagnostics include links or paths for logs and dashboard health where available.
- Tasks needing a human login or specific browser profile block honestly.

### R10 Autonomy policy
Persist a default-profile policy for hands-free operation: repair/reroute before explaining, ask only for real blockers, and complete with evidence.

Acceptance gates:
- Policy identifies real blockers: credentials, paid/cloud permissions, destructive irreversible actions, legal/license ambiguity, missing runtime/hardware, or unverifiable claims.
- Policy forbids silent scope reduction and requires SCOPE_CHANGE_REQUEST for unmet requirements.
- Policy preserves reviewer/QA/security gates without forcing unnecessary human approval.

## Functional requirements
- Define operator authorities and boundaries for default-profile Office/Kanban supervision.
- Define watchdog signals, thresholds, outputs, and low-noise behavior.
- Define Telegram message schemas for Office state changes.
- Define Office Doctor sections, health checks, exit behavior, and redaction rules.
- Define Colab/GPU decision matrix and honest-block behavior.
- Define research task package for FAANG-level templates.
- Define evidence scorecard standard for all downstream workers.
- Define memory/skill decision rules.
- Define browser/dashboard/log access policy and diagnostics.
- Define autonomy policy and blocker taxonomy.

## Nonfunctional requirements
- Safe by default: no secrets or raw PII in durable artifacts.
- Evidence-first: completion claims must be backed by artifacts or explicit checks.
- Low-noise: status reports and watchdog output should avoid spam.
- No new JS dependency installation unless explicitly approved.
- Works on the current macOS repository workspace using existing Python/shell tooling.
- Maintains role boundaries: PM owns requirements and work packages, not implementation architecture.

## Non-goals
- Implementing the watchdog, Office Doctor, Telegram integration, dashboard changes, or templates in this PM task.
- Granting unrestricted logged-in Chrome profile control.
- Providing local GPU support or claiming local GPU reproducibility.
- Bypassing Security, QA, reviewer, or human approval gates when they are genuinely required.
- Persisting secrets, credentials, raw PII, or stale task progress in memory or docs.
- Installing npm packages or adding JavaScript dependencies.

## UX notes
- Operator reports should be short, direct, and action-oriented.
- Doctor output should be scannable in terminal sections with PASS/WARN/FAIL verdicts.
- Telegram reports should include a concise evidence summary and next action, not large logs.
- SCOPE_CHANGE_REQUEST blocks should be parseable and easy to route.

## Data model notes
Suggested durable fields for downstream implementation:
- task_id, run_id, assignee, status, age_seconds, failure_mode, recommended_action.
- report_type: started | blocked | completed | qa_failed | scope_change.
- gate_scorecard: gate, check, exit_code_or_artifact, verdict, rationale.
- redaction_status: checked | redacted | unsafe_blocked.

## API notes
- Kanban tool/API interactions should prefer existing Kanban operations and durable comments/handoffs.
- Telegram reporting should route through existing gateway/send-message facilities and avoid raw tokens.
- Doctor/watchdog should read local state and logs through safe repo-supported interfaces where possible.

## Security notes
- Redact secrets as `[REDACTED]`.
- Do not expose raw token values, credentials, cookies, raw PII, or private browser profile data.
- Browser automation tasks requiring authenticated user state must document login/profile requirements and block if unavailable.
- FAANG template research must respect licenses and block on legal ambiguity.

## Analytics / observability events
- office_operator_started(task_id, assignee, run_id)
- office_operator_repaired(task_id, action, reason)
- office_watchdog_issue_detected(issue_type, task_id, severity)
- office_doctor_run(verdict, failing_sections)
- office_report_sent(report_type, task_id, channel)
- evidence_gate_failed(task_id, gate, reason)
- scope_change_requested(task_id, requirement_ref)
- skill_memory_action(action_type, target_type, reason)

## Edge cases and failure states
- Worker crashes before emitting any summary.
- Task is running but PID is dead or stale.
- Assignee is nonspawnable but has ready work.
- Notification outbox backlog prevents Telegram delivery.
- Dashboard is reachable but embedded TUI or API is degraded.
- Browser automation is available but logged-in Chrome profile state is not.
- Benchmark/release claim lacks real artifact evidence.
- GPU proof is required but only CPU/local environment is available.
- Research source has unclear license.
- Loaded skill is wrong or stale.
- Human approval is explicitly requested by Akhil.

## Release gates
- PM docs exist at docs/office-superpowers/PRD.md, GATE_SCORECARD.md, and TASK_GRAPH.md.
- The PRD covers all 10 superpower areas and preserves all non-negotiable constraints.
- Acceptance gates are explicit for Office supervision, watchdog, Telegram reporting, Office Doctor, Colab/GPU policy, FAANG template research, evidence gates, skill/memory discipline, browser/dashboard/log access, and autonomy policy.
- Gate scorecard includes commands/checks, exit codes or artifact checks, artifact paths, verdicts, and rationale.
- No npm install or JS package commands were used.
- No secrets, tokens, raw PII, or credentials are present in the created docs.

## Risks
- Overbroad operator authority could bypass reviewer/QA/security expectations unless boundaries are explicit.
- Watchdog automation could create noisy or unsafe repairs if thresholds and dry-run behavior are poorly designed.
- Telegram reports could leak sensitive details without strict redaction.
- Doctor checks could overclaim health if they only inspect static files and not live runtime state.
- Colab workflows may not be reproducible without careful artifact capture.
- External template research may introduce license or supply-chain risk.
- Browser automation may be mistaken for unrestricted Chrome profile access.

## Assumptions
- Existing Hermes/Kanban tooling is available in the workspace.
- Python/shell tooling may be used; npm installs are prohibited.
- Office implementation will be routed to architect, builder, QA/evals, security, docs, and DevOps/tooling profiles as appropriate.
- Telegram/report outbox queued-intent path exists for implementation workers; live Telegram delivery remains deferred until a reviewed sender and smoke artifact prove it.

## Open questions
- What exact watchdog TTL thresholds should be used for each status class?
- Which channel(s) besides Telegram should receive Office reports by default?
- Should Office Doctor offer auto-fix mode, or remain diagnostic-only for MVP?
- Which FAANG template sources are approved after license/security review?

## Milestones
### M0 PM specification complete
Deliver this PRD, gate scorecard, and task graph.

### M1 Control-plane architecture
Architect designs operator authority, watchdog, Doctor, reporting contracts, and data flows.

### M2 Safety and policy foundations
Security/reviewer define redaction, autonomy, browser boundary, and approval rules.

### M3 Watchdog and Office Doctor MVP
Builder implements local diagnostics and stale-work detection without npm installs.

### M4 Telegram reporting and evidence scorecards
Builder integrates low-noise reports and scorecard enforcement; QA validates message redaction.

### M5 GPU/Colab and template research package
Research/docs create Colab guidance and FAANG-template synthesis with license checks.

### M6 QA/evals and operational hardening
QA validates gates, failure modes, smoke checks, and no-local-GPU honesty.

## Success metrics
- 100% of Office operator completions include gate scorecards.
- Watchdog detects stale/crashed/nonspawnable Office work in smoke tests.
- Office Doctor reports health sections and recommended fixes without leaking secrets.
- Telegram reports are sent for required state transitions in integration smoke tests.
- GPU-required tasks without GPU evidence produce SCOPE_CHANGE_REQUEST instead of false completion.
- No npm install commands are required for MVP validation.
- No secret/token/raw PII leaks are found in docs, Kanban summaries, or sample reports.

## Agent-ready work packages
See TASK_GRAPH.md for sequenced work packages, owners, dependencies, and acceptance gates.

## Decision log
- D1: PM task produces specifications and acceptance gates only; implementation is delegated later.
- D2: No local GPU support is in scope; Colab is the optional GPU path.
- D3: Browser access is documented as automation-bound, not unrestricted logged-in Chrome profile control.
- D4: YOLO/hands-free is default, but real blockers still require honest block/scope-change behavior.
- D5: Evidence-backed completion is a hard release gate, not a nice-to-have.

## Done definition
This PM task is done when PRD.md, GATE_SCORECARD.md, and TASK_GRAPH.md exist, cover all requested superpower areas and constraints, include explicit acceptance gates, and pass repository-local artifact verification without npm installs or unsafe claims.
