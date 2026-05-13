# Security Model: Default-profile Office Operator Superpowers

Status: proposed security model with policy-fixture enforcement hooks
Last verified: 2026-05-13T00:39:21Z
Source task: t_18c840af

Runtime enforcement note: `hermes_cli.office_superpowers.evaluate_office_boundary_decision()` now provides a deterministic permission-policy fixture for Office protected paths. It is covered by unit tests and returns `allow`, `allow_read_only`, `requires_approval`, or `deny` for workspace paths, protected profile artifacts, active memory, permission policies, approval records, audit logs, production state, browser profile state, secret-bearing artifacts, and external paths. It is not yet a global tool-dispatcher hook; full enforcement requires wiring this fixture into the Hermes permission gateway/tool boundary before executing file/browser/memory/approval actions.

## Security objective

Give Akhil's default Hermes profile enough authority to operate Office/Kanban hands-free while preventing unsafe escalation, secret leakage, false evidence claims, uncontrolled browser/profile access, and hidden scope reduction.

The security model is evidence-first: every risky action has a control point, and every claim that affects trust must be backed by commands, exit codes, artifacts, or an honest blocker/scope-change request.

Current honest capability statement: this package provides dry-run Office diagnostics, evidence scorecard validation, and a local watchdog runner; live notification and safe repair remain follow-up work. The current implementation documents policy, uses redaction/diagnostic helpers, and includes a tested boundary-decision fixture; it is not yet a global tool/dispatcher enforcement boundary for protected artifacts, browser profile state, secrets, approval records, or profile memory.

## Assets to protect

- API keys, OAuth tokens, gateway credentials, Telegram/Slack tokens, cookies, browser profile data, private keys.
- Akhil's private files outside the authorized workspace.
- Kanban board integrity: task statuses, runs, comments, evidence, parent/child links, audit events.
- Reviewer/QA/Security gates and human approval records.
- Production state, deployed services, external paid/cloud resources, release artifacts.
- User PII and private message contents from Telegram/Slack/browser/logs.
- Long-term memory and skills, especially profile policy and protected profile artifacts.
- Trust in benchmark, runtime, release, GPU, and ML evaluation claims.

## Actors

| Actor | Role | Trust level |
|---|---|---|
| Akhil | Human owner/operator | highest; explicit approval source |
| default profile operator | Hands-free Office operator | trusted within policy only |
| Office workers | Specialist profiles executing Kanban tasks | scoped to assigned role/workspace |
| Reviewer/QA/Security profiles | Evidence and safety gates | trusted for their lane |
| Gateway/Telegram/Slack | Notification and remote control path | semi-trusted; must redact and authenticate |
| Browser automation target sites | External web state | untrusted input |
| Logs/artifacts | Evidence source | trusted only after redaction and provenance checks |
| External templates/repos | Research inputs | untrusted until license/security reviewed |

## Authority boundaries

### Default-profile operator authority

Allowed by policy for YOLO Office tasks after the corresponding implementation exists; current scripts are diagnostic/dry-run unless noted:
- Inspect Kanban tasks/runs/comments/events and workspace artifacts.
- Inspect safe gateway/dispatcher/log/Doctor/watchdog summaries.
- Comment with redacted rationale and evidence paths.
- Create child tasks for concrete specialist profiles.
- Route routine review/QA/security work through Kanban without blocking on Akhil.
- Recommend reclaiming stale/dead routine work when state proves no active worker remains; automatic reclaim is follow-up work.
- Recommend unblocking protocol-only stale blocks when evidence exists and no real blocker remains; automatic unblock is follow-up work.
- Recommend reassignment from nonspawnable worker tasks to an equivalent concrete profile when scope matches; automatic reassignment is follow-up work.
- Enqueue redacted Telegram report intents; live send remains dry-run/follow-up until reviewed sender evidence exists.

Requires specialist review or human approval:
- Security policy changes, permission gateway changes, approval policy changes.
- Protected profile artifacts: other profiles' `SOUL.md`, profile config, active memory, permission policies, approval records, audit logs.
- Any change outside `/Users/akhilkinnera/Documents/My Workspace` unless explicitly requested.
- Credential creation, token rotation, OAuth login, or private cookie/browser-profile handling.
- Paid/cloud/Colab resource use beyond documenting optional paths.
- Destructive irreversible actions, production deploys, public releases, package publishing.
- Legal/license ambiguity where code/templates may be copied or vendored.
- Human-login browser tasks, MFA, CAPTCHA, or terms/consent gates.

Denied actions:
- Silent scope reduction.
- Claiming benchmark/performance/release/GPU/deploy proof without real artifacts.
- Saving task progress, PR/issue numbers, commit SHAs, or phase-completion logs to long-term memory.
- Writing raw secrets, tokens, PII, cookies, or full private logs into Kanban, docs, Telegram, or memory.
- Installing npm/pnpm/yarn/npx packages under the stated no-npm constraint.

## Real blocker taxonomy

Only these categories should block and ask Akhil or a specialist for input:

1. `credentials`: missing/expired token, OAuth login, credential rotation, private cookie/session requirement.
2. `paid_cloud_permission`: paid API, cloud resource, GPU rental, paid Colab tier, billing-affecting action.
3. `destructive_irreversible_action`: delete/reset/publish/deploy/rotate/revoke actions that cannot be safely undone.
4. `legal_license_ambiguity`: unclear or incompatible license where copying/adapting code/templates is proposed.
5. `missing_runtime_or_hardware`: required hardware/runtime unavailable, including GPU-required proof with no Colab/exported artifact.
6. `unverifiable_claim`: benchmark/release/deploy/metric claim cannot be proven after serious attempts.
7. `explicit_approval_mode`: Akhil said ask/keep me in the loop/approval required/do not YOLO.
8. `unsafe_secret_or_pii`: candidate durable artifact contains raw secret/PII and cannot be safely redacted automatically.
9. `human_login_or_browser_profile_required`: task requires logged-in browser profile, MFA, cookies, or private account state.

Routine review, QA, Security review, and implementation follow-up are not human blockers by themselves; they should be routed as Kanban work unless one of the categories above applies.

## Threat model

### T1: Secret leakage into durable artifacts

Scenario:
- Worker or Doctor copies logs/env/browser output into Kanban comments, docs, reports, or Telegram with raw tokens/cookies/API keys.

Controls:
- Shared redaction helper used by Doctor, watchdog, outbox, and scorecard validator.
- Secret scan before durable writes/sends where practical.
- `evaluate_office_boundary_decision()` classifies `.env`, `auth.json`, credential/cookie/token/private-key filenames as `secret_bearing_artifact`; reads require approval and writes/deletes are denied for broad Office automation.
- Telegram reports summarize, never attach large raw logs.
- Doctor prints log paths and redacted summaries by default.
- `unsafe_secret_or_pii` blocks instead of sending if redaction cannot be trusted.

Residual risk:
- Regex cannot catch every secret format. Prefer minimizing raw log movement and keeping sensitive values out of prompts/artifacts.
- The policy fixture is not a whole-system DLP control until wired into the tool dispatcher/permission gateway for every file, browser, memory, and messaging action.

### T2: Default-profile authority escalation

Scenario:
- Operator treats broad access as permission to modify protected configs, bypass reviewer/QA, edit other profiles' policy, or perform destructive actions.

Controls:
- Documented allowlist of future routine repair actions; current watchdog remains dry-run unless a reviewed repair engine is added.
- Denylist/policy fixture for protected artifacts and destructive/external actions; full enforcement requires tool/dispatcher integration.
- `evaluate_office_boundary_decision()` maps protected profile artifacts (`SOUL.md`, profile `config.yaml`), active memory, permission policies, approval records, audit logs, production state, browser profile state, secret-bearing artifacts, Hermes-home state, external paths, and normal workspace paths to explicit policy decisions.
- Approval/audit records are read-only evidence by default and denied for patch/write/delete from broad Office automation.
- Audit comments for manual repair recommendations now and for executed repairs after a reviewed repair engine exists.
- Human/specialist routing for permission, security, approval, protected profile, production, and external resource changes.
- Reviewers/QA validate evidence after handoff.

Residual risk:
- Ambiguous task language may imply authority. If ambiguity changes permission boundary, block with a precise reason.
- Current fixture is an enforceable policy primitive, not yet a mandatory pre-execution hook for all Hermes tools.

### T3: False completion or evidence laundering

Scenario:
- Worker claims performance/release/GPU/deploy success using README prose, mock tests, templates, or planned scripts.

Controls:
- Scorecard schema requires command/check, exit code or artifact, path, verdict, rationale.
- Heavy claims require real artifacts.
- SCOPE_CHANGE_REQUEST required for unmet requirements.
- QA/reviewer rejects prose-only heavy claims.
- Colab/GPU policy distinguishes CPU proof, optional Colab, and GPU-required work.

Residual risk:
- Artifact existence is not the same as correctness. QA must inspect content for high-risk releases/benchmarks.

### T4: Unsafe auto-repair by watchdog

Scenario:
- Watchdog auto-unblocks or reassigns work incorrectly, causing lost context, duplicate work, or bypassed gates.

Controls:
- Dry-run first rollout.
- Repair action allowlist.
- Idempotency keys and audit comments.
- Reassign only to compatible concrete profiles.
- Deny destructive actions and real blockers.
- Thresholds based on claim TTL, heartbeat, PID liveness, and repeated events.

Residual risk:
- Stale state race with an active worker. Require heartbeat/PID checks and prefer comment-only for ambiguous cases.

### T5: Notification spoofing, spam, or divergence

Scenario:
- Telegram report says a task completed or blocked when Kanban state says otherwise; repeated crash loops spam Akhil.

Controls:
- Outbox writes report intent after state/evidence update.
- Idempotency key by board/task/run/type/hash.
- Report types are fixed enum.
- Low-noise grouping/digest for repeated findings.
- Doctor exposes queued/failed sends.
- Delivery success requires `sent_at` or gateway result, not optimistic send attempt.

Residual risk:
- Gateway can fail after accepting send. Keep outbox status honest and include conditional smoke tests.

### T6: Browser/profile privacy violation

Scenario:
- Operator assumes browser tool access means unrestricted logged-in Chrome user profile control or collects private cookies/screenshots.

Controls:
- Browser boundary documented in Doctor and security docs.
- `evaluate_office_boundary_decision()` classifies browser/Chrome profile paths and cookie/login-data files as `browser_profile_state`; reads require approval and writes are denied.
- Human login/profile state is a real blocker.
- Screenshots/logs require redaction review before durable sharing.
- No cookie/token extraction for Office automation.

Residual risk:
- Web pages can contain PII in visible content. Treat screenshots and page text as sensitive until reviewed/redacted.
- Remote browser tool output may not map to a local browser-profile path, so gateway/tool metadata must still tag screenshots, local storage, and page text as sensitive at dispatch time.

### T7: License/supply-chain risk from external templates

Scenario:
- Worker copies code/templates from AGPL/NOASSERTION/no-license sources or installs packages against constraints.

Controls:
- Research docs identify license ambiguity.
- Security/legal block before copying ambiguous content.
- Synthesize concepts, do not vendor code by default.
- No npm installs or JS package additions without explicit approval.
- Python stdlib and existing repo tooling only for MVP.

Residual risk:
- Permissive license metadata may not cover all files. File-level license review is required before copying exact content.

### T8: Memory/skill contamination

Scenario:
- Agent saves stale task progress, secrets, or temporary artifacts to long-term memory; or patches skills with task-specific hacks.

Controls:
- Memory rules distinguish stable declarative facts from ephemeral state.
- Procedures go into skills; progress stays in Kanban/session.
- No secrets or task IDs as durable memory unless they are stable non-sensitive configuration facts.
- Skill updates require reusable workflow, pitfalls, verification steps.

Residual risk:
- Overzealous memory writes. Workers should prefer not saving when value is likely stale within a week.

## Redaction standard

### Must redact as `[REDACTED]`

- API keys, bearer tokens, OAuth tokens, refresh tokens.
- Private keys and certificates with private key material.
- Session cookies, browser cookies, authorization headers.
- Passwords and app-specific passwords.
- Webhook secrets, signing secrets, bot tokens.
- Raw phone numbers, email addresses, chat IDs, user IDs when not needed for operation.
- Full private log excerpts that may include user messages or credentials.

### Safe to include when needed

- Local repo-relative artifact paths that do not encode secrets or private PII.
- Task IDs/run IDs and profile names on the local Kanban board.
- Exit codes and command names that do not include secret arguments.
- Redacted error summaries.
- Hashes of redacted payloads or artifacts when they do not reveal secrets.

### Candidate regex categories

The implementation should scan for at least:
- `(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*...`
- `(?i)authorization:\s*bearer ...`
- `-----BEGIN ... PRIVATE KEY-----`
- Common provider token prefixes when known.
- Cookie assignment/header patterns.

Regex is a backstop, not a reason to move raw logs unnecessarily.

## Permission decision table

| Action | Default decision | Required evidence | Notes |
|---|---|---|---|
| Inspect Kanban board | allow | board path/status | Read-only |
| Comment safe rationale | allow | redaction checked | No secrets/PII |
| Create child task | allow | correct owner/profile | Do not self-assign scope creep |
| Reclaim stale dead run | future reviewed repair only | TTL exceeded + PID/heartbeat absent | Current scripts should recommend/comment, not mutate. |
| Unblock routine review block | future reviewed repair only | evidence exists + no real blocker | Current scripts should preserve QA/reviewer routing and not auto-unblock. |
| Reassign nonspawnable profile | future reviewed repair only | crash/spawn evidence + compatible profile | Current scripts should recommend or create follow-up work, not auto-reassign. |
| Retry outbox send | future reviewed sender only | due retry + redacted payload | Current `office_report_outbox.py` retry path is dry-run. |
| Send Telegram report | future reviewed sender only | redacted payload + gateway result | If missing config, mark blocked_external_config; do not claim current live delivery. |
| Read logs | allow limited | path + redacted summary | Avoid full private dumps |
| Browser page automation | allow when public/available | tool output/screenshot redacted | No private cookies/profile assumption |
| Human login/MFA | block | blocker reason | Ask Akhil |
| Credential/token handling | block/specialist | credential need | Never print raw token |
| Paid cloud/GPU | block unless approved | cost/resource detail | Colab docs can be optional |
| Production deploy/release | block unless requested and gated | release artifacts, approval | Destructive/external risk |
| Copy ambiguous licensed code | block | license evidence | Legal/security decision |
| Protected profile artifact read | requires_approval | path category + requester + need | Other profiles' `SOUL.md` and profile configs are not workspace files. |
| Protected profile artifact write/delete | requires_approval | security/owner approval + exact diff | Prefer child task routed to owning lane; never silently rewrite. |
| Approval/audit record read | allow_read_only | record path + redacted summary | Evidence inspection only. |
| Approval/audit record write/delete | deny | N/A | Append-only systems own these records. |
| Browser cookie/profile read | requires_approval | human-login/privacy need | Do not extract cookies/local storage by default. |
| Browser cookie/profile write/delete | deny | N/A | Office automation must not mutate user browser profile state. |
| Secret-bearing artifact read | requires_approval | credential-owner approval | `.env`, `auth.json`, cookie/token/private-key paths. |
| Secret-bearing artifact write/delete | deny | N/A | Credential tooling/owner handles rotations, not broad Office repair. |
| Save memory | allow only stable facts | non-sensitive stable fact | No task progress |
| Patch skill | allow for reusable correction | reusable workflow evidence | Do not patch protected skill incorrectly |

## Evidence gate security

Every completion/handoff must include scorecard items with:
- gate
- command_or_check
- exit_code_or_artifact
- verdict
- rationale
- artifact_paths where applicable
- redaction_status

Security-specific validation:
- Any item that mentions benchmarks, performance, deployment, release, GPU, or model metrics must point to measured artifacts or be `BLOCKED`/`NOT_APPLICABLE`.
- Any scope reduction must use the parseable `SCOPE_CHANGE_REQUEST` block.
- Any unsafe secret finding must block or route Security; it cannot be hidden by omitting the artifact.

## Colab/GPU security and honesty

Rules:
- Local GPU is unavailable and must not be claimed.
- Colab is optional remote evidence unless a task explicitly requires GPU proof.
- If GPU proof is required and no Colab/GPU artifact is available, emit SCOPE_CHANGE_REQUEST or block for missing runtime/hardware.
- Do not store secrets in notebooks, notebook output, Colab cells, logs, or exported HTML.
- Colab artifact bundle must include environment/GPU type, command, seed/config, metrics/logs, and redaction scan.
- Paid Colab or cloud GPU use requires approval.

## Browser/dashboard/log access security

Browser:
- Treat page content and screenshots as potentially sensitive.
- Do not extract or persist cookies, local storage, credentials, or private profile state.
- Do not claim login-dependent checks unless a human login/setup occurred and evidence is safe.
- Block for human login, MFA, CAPTCHA, private account state, or site access restrictions.

Dashboard/API:
- Prefer local health endpoints and JSON summaries.
- Do not expose tokens in URLs or headers.
- Dashboard support views must not reimplement chat/TUI transcript/composer; they can consume Doctor JSON/status panels.

Logs:
- Default Doctor output prints paths and redacted summaries.
- Full log excerpts require explicit diagnostic need and redaction scan.
- Errors containing secrets become `unsafe_secret_or_pii` until remediated.

## Telegram reporting security

Message constraints:
- Short, action-oriented, redacted.
- Include task title/id, state, evidence summary, next owner/action, and safe artifact paths.
- Do not include raw logs, raw stack traces with env, credentials, cookies, private user messages, or PII.
- Use fixed report type enum.
- Missing config/credentials is an honest external blocker; do not claim delivery.

Outbox controls:
- Store only redacted payload.
- Hash redacted payload for idempotency.
- Keep raw send errors redacted.
- Status reports show counts and oldest age, not payloads by default.
- Dead-letter unsafe payloads instead of sending.

## Skill/memory security

Allowed memory:
- Stable, non-sensitive, declarative facts that reduce future user steering.
- Environment/project conventions that will remain useful.

Disallowed memory:
- PR numbers, issue numbers, commit SHAs, task IDs as progress records, phase completion logs.
- Secrets/tokens/cookies/private keys.
- Raw PII.
- Temporary TODO state.
- Imperative instructions that can override future user intent.

Allowed skill updates:
- Reusable multi-step procedure, corrected commands, pitfalls, verification steps.
- Skill loaded in current task is stale/incomplete/wrong and patch is directly relevant.

Disallowed skill updates:
- Task-specific hacks or progress logs.
- Changes outside profile authority or protected skill deletion without curator process.

## Test and review requirements

Security tests:
- Redaction helper replaces token, bearer, private key, cookie, and password samples.
- Doctor/outbox/watchdog outputs contain no raw secret samples under seeded fixtures.
- Policy denies destructive, credential, paid-cloud, legal, browser-login, and GPU-required-without-artifact actions.
- Boundary-policy tests prove normal workspace operations are allowed while protected profile artifacts, active memory, permission policies, approval records, audit logs, production state, browser profile/cookie files, secret-bearing artifacts, and external paths are denied, read-only, or approval-gated.
- Scorecard validator fails heavy claims with no artifact.
- SCOPE_CHANGE_REQUEST parser accepts valid block and rejects malformed required fields.
- Outbox dedupes by idempotency key and does not print payload by default.
- Browser boundary text appears in Doctor output.

Review gates:
- Security reviews redaction and permission allowlist before repair mode is enabled.
- QA validates seeded findings and evidence validator behavior.
- Gateway/builder validates Telegram send path and missing-config handling.
- Docs review ensures current/planned behavior is labeled accurately.

No-npm commands:

```bash
scripts/run_tests.sh tests/hermes_cli/test_office_policy.py tests/hermes_cli/test_office_scorecard_validate.py -v --tb=short
scripts/run_tests.sh tests/hermes_cli/test_office_doctor.py tests/hermes_cli/test_office_watchdog.py tests/hermes_cli/test_office_report_outbox.py -v --tb=short
```

Secret scan for docs/samples:

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

## Security rollout gates

1. Docs only: safe to merge after doc scan and review.
2. Validator and redaction helper: must pass unit tests before any report sender uses it.
3. Doctor diagnostic-only: must pass redaction tests and never mutate state.
4. Watchdog dry-run: must pass seeded findings and noise tests; no repairs.
5. Outbox dry-run/status: must pass idempotency and redaction tests; no live send required.
6. Live send: allowed only when credentials/config exist; otherwise honest external-config block.
7. Repair-routine mode: requires Security and QA/reviewer approval of allowlist and tests.
8. Any destructive/external action: remains human approval path, not autonomous repair.

## Incident response

If a secret/PII leak is detected:
1. Stop sending reports and mark outbox payload `unsafe_blocked` or `dead_letter`.
2. Do not paste the raw secret into Kanban or docs.
3. Add a redacted Kanban comment with impacted artifact path and recommended owner.
4. Route Security child task for triage/rotation decision.
5. Remove or redact unsafe durable artifact if safe and within authority; otherwise block for approval.
6. Update redaction tests to cover the missed pattern.

If watchdog mis-repairs:
1. Disable repair mode; set dry-run/comment-only.
2. Use audit comments/action records to identify affected tasks.
3. Apply reversible compensation: reassign back, re-block, or create correction child task.
4. Add regression test for the misclassification.
5. Require Security/QA review before re-enabling repair.

If Telegram reports are wrong/noisy:
1. Pause sender or set destination to disabled/dry-run.
2. Keep outbox rows for audit.
3. Fix report type/idempotency/grouping logic.
4. Send a correction only if it is safe and useful; otherwise record Kanban correction.

## Acceptance gates for this security model

| Gate | Command/check | Exit code / artifact | Verdict | Rationale |
|---|---|---|---|---|
| Source plan read | `read_file docs/akhil-default-profile-superpowers-plan.md` | 39-line artifact read | PASS | Security model preserves no npm, no local GPU, redaction, YOLO blocker taxonomy, browser boundary. |
| PRD/TASK_GRAPH read | `read_file docs/office-superpowers/PRD.md` and `TASK_GRAPH.md` | Artifacts read successfully | PASS | R1-R10 acceptance gates and work packages mapped to security controls. |
| Research artifacts read | `read_file ML_TEMPLATE_RESEARCH.md` and `OPS_AGENT_TEMPLATE_RESEARCH.md` | Artifacts read successfully | PASS | Outbox, evidence, Colab, watchdog, and license-risk patterns incorporated. |
| Security deliverable | File path | `docs/office-superpowers/SECURITY_MODEL.md` | PASS | Covers assets, actors, boundaries, threat model, redaction, tests, incident response. |
| No npm installs | Session command review | No npm/pnpm/yarn/npx commands executed | PASS | This is a docs/security design task using file and shell/Python checks only. |
| No local GPU claim | Content review | This document states no local GPU proof is available | PASS | GPU proof requires remote artifacts or honest block/scope-change. |
| Secret safety | Planned verification | regex scan in final task scorecard | PENDING_FINAL_SCAN | No secrets intentionally included; final verification will scan docs. |
docs. |
