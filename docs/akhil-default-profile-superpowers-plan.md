# Akhil Default Profile Superpowers Plan

## Mission
Make the default Hermes profile, "Akhil", a reliable operator for Office/Kanban: able to plan, inspect, repair, dispatch, supervise, verify, and notify without babysitting. The system must prefer evidence over optimistic completion.

## Non-negotiable constraints
- No npm installs for this project because of current supply-chain attack concerns. Use existing repo dependencies, Python stdlib, shell, and already-installed tooling only unless a worker blocks for explicit approval.
- No local GPU is available. For GPU-heavy tasks, support Colab as an optional documented execution target, but do not claim local GPU reproducibility.
- Keep secrets out of durable Kanban rows, logs, docs, and notifications. Redact raw tokens as `[REDACTED]`.
- Default policy for Office YOLO tasks: hands-free progress; block only for credentials, paid/cloud permissions, destructive irreversible actions, legal/license ambiguity, missing runtime/hardware, or unverifiable benchmark claims.

## Browser/Chrome access answer
The default profile has browser automation tools available in this environment through the browser toolset. I can open pages, click/type, inspect console output, capture screenshots, and use vision on browser screenshots when the active session has those tools. This is not the same as unrestricted interactive Chrome user-profile control; if a task needs logged-in browser state, cookies, or a specific Chrome profile, it may require explicit browser/profile setup or a human login step.

## Scope across the 10 requested superpowers
1. Office supervision authority: implement documented default-profile operator powers for Kanban inspection, reclaim, unblock, reassign, dispatch, and review-required handling.
2. Office watchdog: create a reliable watchdog script/job that detects stale running tasks, blocked protocol violations, ready tasks not spawning, nonspawnable assignees, missing reports, and notification outbox backlog.
3. Telegram reporting contract: standardize started/blocked/completed/QA-failed/scope-change messages for YOLO Office goals, with low-noise defaults.
4. Office Doctor: build a local diagnostic command/script that prints gateway health, Telegram/Slack health, board stats, stale claims, failed runs, nonspawnable tasks, notification backlog, and recommended fixes.
5. GPU strategy: no local GPU. Add Colab-first guidance/templates for GPU projects and make Office block honestly when GPU proof is required and unavailable.
6. FAANG-level templates: assemble a research team to identify open-source, production-grade templates for ML projects, agent systems, reproducibility, docs, model cards, evals, and runbooks; synthesize into local templates/reference docs without npm installs.
7. Truth-over-completion evidence gates: codify hard gates for metrics, runtime, benchmark artifacts, dataset audits, and reproducibility so workers cannot close heavy claims with prose only.
8. Memory/skills discipline: add/update concise skills and references when workflows become reusable; avoid stale task-progress memories.
9. Browser/dashboard/log access: document the browser automation boundary, verify dashboard/API/log inspection routes, and build diagnostics around them.
10. Autonomy policy: persist a default-profile policy that says act hands-free, repair/reroute before explaining, ask only for real blockers, and always provide evidence-backed completions.

## Implementation outcomes expected from Office
- A checked-in implementation plan and design docs.
- Local scripts/commands for Office Doctor and Office Watchdog where appropriate.
- Tests or smoke checks that run without npm install.
- A Telegram notification path proving final status delivery.
- A FAANG reviewer pass focused on reliability, security, and operational maturity.
- A QA scorecard with exact commands, exit codes, artifacts, and pass/fail/blocked verdicts.

## Target workspace
Repository: `/Users/akhilkinnera/Documents/My Workspace/Hermes/hermes-agent`

## Final report
Notify Akhil on Telegram when the Office pipeline finishes or blocks honestly.
