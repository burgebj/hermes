# Task Graph: Default-profile Office Operator Superpowers

Status: target work graph. Current implementation is limited to dry-run Office diagnostics, evidence scorecard validation, and a local watchdog runner. Live notification, autonomous safe repair/reassignment/unblock behavior, and whole-system security-boundary enforcement stay as downstream remediation work until their cards produce evidence.

## Graph principles
- PM owns scope, requirements, acceptance gates, sequencing, and work packages.
- Architecture, implementation, QA/evals, security, docs, and DevOps/tooling are downstream owners.
- No npm installs are allowed in any work package unless Akhil explicitly approves.
- No local GPU proof may be claimed; Colab is optional when GPU execution is required.
- Secrets, tokens, raw PII, cookies, and credentials must be redacted as `[REDACTED]` in durable artifacts.
- Routine review/QA gates continue hands-free; human blocks are only for real external blockers or explicit approval mode.

## Milestone dependency graph

```text
M0 PM specification
  -> M1 Control-plane architecture
    -> M2 Safety and policy foundations
      -> M3 Watchdog + Office Doctor MVP
      -> M4 Telegram reporting + evidence scorecards
        -> M6 QA/evals + operational hardening
    -> M5 GPU/Colab + FAANG template research
      -> M6 QA/evals + operational hardening
```

## Work packages

### WP0 PM specification package
Owner: PM
Status: completed by this card when PRD.md, GATE_SCORECARD.md, and TASK_GRAPH.md are written.

Scope:
- Convert the source plan into requirements, non-goals, milestones, risks, and acceptance gates.
- Preserve constraints: no npm installs, no local GPU, Colab optional, broad access OK within browser boundary, evidence-backed completion.

Acceptance gates:
- Docs exist under docs/office-superpowers/.
- All 10 superpower areas have explicit gates.
- Gate scorecard records commands/checks, artifacts, verdicts, and rationale.

### WP1 Control-plane architecture
Suggested owner: system architect
Depends on: WP0

Scope:
- Design default-profile operator authority for Kanban inspect, recommended reclaim/unblock/reassign, dispatch, and review-required handling; actual mutation paths require reviewed implementation evidence.
- Define state transitions, escalation paths, audit comments, redaction boundaries, and supervisor/reviewer coverage.
- Define watchdog and Office Doctor data sources without requiring npm installs.

Acceptance gates:
- Architecture doc maps each operator action to allowed inputs, side effects, audit events, and rollback/repair behavior.
- Review-required flow preserves QA/reviewer gates without unnecessary human blocks.
- Unsafe actions are explicitly excluded or routed to human/security approval.

### WP2 Security and autonomy policy
Suggested owner: security/reviewer
Depends on: WP0, WP1

Scope:
- Validate autonomy policy, blocker taxonomy, secrets redaction, browser access boundary, and durable artifact safety.
- Define when broad access is acceptable and when human approval is mandatory.

Acceptance gates:
- Policy lists real blockers: credentials, paid/cloud permissions, destructive irreversible actions, legal/license ambiguity, missing runtime/hardware, unverifiable claims, and explicit approval mode.
- Redaction standard covers Kanban rows, docs, logs, Telegram, browser screenshots, and diagnostics.
- Browser boundary distinguishes automation tools from logged-in Chrome profile/cookie access.

### WP3 Office watchdog implementation
Suggested owner: backend/tooling builder
Depends on: WP1, WP2

Scope:
- Implement a local watchdog script/job that detects stale running tasks, blocked protocol violations, ready tasks not spawning, nonspawnable assignees, missing reports, repeated crashes, and notification backlog.
- Prefer dry-run/diagnostic output first; repair actions must follow the approved architecture.

Acceptance gates:
- Watchdog smoke tests cover stale claim, crashed worker, nonspawnable assignee, ready-not-spawned task, missing report, and notification backlog.
- Output includes task id, assignee, run id where applicable, issue type, severity, and recommended action.
- No npm install or local GPU dependency.
- No secrets/raw PII in output.

### WP4 Office Doctor implementation
Suggested owner: backend/tooling builder
Depends on: WP1, WP2

Scope:
- Build a local diagnostic command/script that prints gateway health, Telegram/Slack health, board stats, stale claims, failed runs, nonspawnable tasks, notification backlog, browser/dashboard/log routes, and recommended fixes.

Acceptance gates:
- Doctor output sections: gateway, messaging, Kanban board, workers, notifications, logs, browser/dashboard, recommendations.
- Healthy state exits 0; actionable unhealthy state exits non-zero with concise remediation hints.
- Supports safe redaction and does not print credential values.
- Runs with existing Python/shell tooling only.

### WP5 Telegram reporting contract and integration
Suggested owner: gateway/builder plus QA
Depends on: WP1, WP2

Scope:
- Standardize and implement low-noise Telegram reports for started, blocked, completed, QA-failed, and scope-change events.
- Include evidence summaries and artifact paths where safe.

Acceptance gates:
- Message schemas exist for each report type.
- Integration smoke proves at least one safe test status can be delivered through the configured path or honestly blocks on missing credentials/config.
- Reports redact secrets/raw PII and do not include large logs.
- Blocked and scope-change messages are distinguishable and actionable.

### WP6 Evidence gate enforcement
Suggested owner: QA/evals plus reviewer
Depends on: WP0, WP2

Scope:
- Define and validate a standard scorecard for commands/checks, exit codes, artifact paths, verdicts, and rationale.
- Ensure benchmark/runtime/release/deploy claims require real artifacts.

Acceptance gates:
- Scorecard template is used by sample worker handoffs.
- Tests or evals reject completion claims with prose-only benchmark/release evidence.
- SCOPE_CHANGE_REQUEST format is validated for unmet requirements.
- QA can inspect diffs plus scorecards before approval.

### WP7 GPU/Colab policy and templates
Suggested owner: documentation/research plus ML tooling reviewer
Depends on: WP0, WP2

Scope:
- Document GPU decision matrix: CPU-sufficient, Colab-optional, GPU-required.
- Provide Colab guidance/templates for GPU workloads without claiming local GPU proof.

Acceptance gates:
- GPU-required unavailable path emits SCOPE_CHANGE_REQUEST.
- Colab guidance explains artifact capture, secret hygiene, and reproducibility limitations.
- No local GPU checks are represented as GPU proof.

### WP8 FAANG-level template research
Suggested owner: research agent plus documentation
Depends on: WP0, WP2

Scope:
- Research open-source, production-grade templates for ML projects, agent systems, reproducibility, docs, model cards, evals, runbooks, and operational maturity.
- Synthesize local template/reference docs without npm installs.

Acceptance gates:
- Research includes source URLs, license notes, comparison criteria, strengths/weaknesses, and recommendation rationale.
- Legal/license ambiguity is blocked for human decision.
- Synthesized templates avoid copying unsafe licensed content.

### WP9 Skill/memory discipline package
Suggested owner: documentation plus PM/reviewer
Depends on: WP0, WP2

Scope:
- Define procedures for when to create/update skills and when to save durable memory.
- Explicitly forbid saving temporary task progress, PR numbers, issue numbers, commit SHAs, and phase completion logs as memory.

Acceptance gates:
- Procedure differentiates skills, user memory, project memory, and ephemeral task state.
- Examples use declarative stable facts for memory and procedural steps for skills.
- Loaded stale/incomplete skill update path is documented.

### WP10 Browser/dashboard/log access diagnostics
Suggested owner: tooling builder plus docs
Depends on: WP1, WP2, WP4

Scope:
- Document and verify routes for browser automation, dashboard/API inspection, and Hermes logs.
- Add diagnostic checks to Office Doctor where appropriate.

Acceptance gates:
- Browser boundary is visible in docs and Doctor output.
- Dashboard/API/log checks have safe failure messages and redaction rules.
- Tasks requiring logged-in profile state or human login block honestly.

### WP11 End-to-end QA and release readiness
Suggested owner: QA/evals/reviewer
Depends on: WP3, WP4, WP5, WP6, WP7, WP8, WP9, WP10

Scope:
- Validate the complete operator upgrade across stale-task recovery, diagnostics, Telegram reporting, evidence gates, GPU honesty, browser boundary, and skill/memory discipline.

Acceptance gates:
- QA scorecard records command/check, exit code/artifact, verdict, and rationale for each superpower area.
- No npm install commands are required or executed.
- No local GPU proof is claimed.
- Secret scan/redaction check passes for docs, sample messages, and logs produced by the test.
- Reviewer approves evidence quality or files specific follow-up tasks.

## Suggested Kanban sequencing
1. Architect WP1.
2. Security/reviewer WP2 in parallel with architecture review.
3. Builder WP3 and WP4 after architecture/security boundaries are accepted.
4. Gateway/builder WP5 and QA WP6 after reporting/evidence schemas are approved.
5. Docs/research WP7, WP8, and WP9 can run after WP2.
6. Tooling/docs WP10 integrates with Office Doctor after WP4.
7. QA/reviewer WP11 fans in all implementation outputs.

## Cross-work-package release gates
- Office supervision: architecture and QA demonstrate stale/crashed/nonspawnable work recovery paths.
- Watchdog: smoke tests detect all specified issue classes.
- Telegram reporting: safe messages exist for started, blocked, completed, QA-failed, and scope-change states.
- Office Doctor: local diagnostic command covers required sections and redaction.
- Colab/GPU: policy prevents false local GPU claims and supports optional Colab artifact capture.
- FAANG template research: source/license/comparison evidence is documented.
- Evidence gates: scorecards and artifact requirements are enforced.
- Skill/memory discipline: reusable workflows and durable facts are routed correctly.
- Browser/dashboard/log access: automation boundary and diagnostics are documented.
- Autonomy policy: hands-free repair/reroute is default; real blockers are explicit.
