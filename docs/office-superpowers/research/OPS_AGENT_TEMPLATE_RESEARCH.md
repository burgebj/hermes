# OPS Agent Template Research: Agent Operations and Reliability Templates

Accessed: 2026-05-13T00:29:29Z
Task: t_5c7f76ba
Lane: FAANG research lane B, agent/ops/reliability templates

## Question

What open-source, FAANG/top-tier operational patterns should Hermes use as references when building local templates for agent operations, job queues, watchdogs, SRE runbooks, on-call diagnostics, notification outboxes, evidence gates, and operational dashboards?

## Summary

The strongest template direction is not a single framework. It is a small, repo-local reliability kit that borrows proven primitives from SRE and workflow systems:

1. Durable task state and replayable execution from Temporal-style durable execution and LangGraph-style checkpointed agent runs.
2. Worker heartbeat, state registries, retry/error registries, and inspect/control commands from RQ and Celery.
3. Low-noise SLO-driven alerts from Google SRE, routed through Alertmanager-like grouping, inhibition, and silencing rather than raw spam.
4. Transactional outbox semantics for Telegram/gateway notifications so worker completion and notification enqueue are auditable and replayable.
5. OpenTelemetry-compatible traces/logs/metrics and Grafana-style dashboards for operator diagnosis.
6. Evidence gates modeled after SLSA provenance, OpenSSF Scorecard, and OPA/conftest: every consequential claim is tied to an artifact, command, exit code, provenance, or policy result.

For Hermes Office MVP, do not copy large orchestration systems. Build Python/shell templates around existing Kanban state and logs: `office_doctor.py`, `office_watchdog.py`, `office_report_outbox.py`, `office_scorecard_validate.py`, and markdown runbooks. These can satisfy the PRD without npm installs or GPU.

## Key findings

### 1. Job and agent execution should be observable before it is autonomous

Celery documents worker inspection/control, events, task lifecycle events, and Flower for real-time monitoring. RQ exposes worker state such as `state`, `current_job`, `last_heartbeat`, birth time, successful/failed counts, and total working time. Temporal documents workflow failure detection and observability hooks around application failures. LangGraph explicitly positions durable execution as a core agent reliability primitive.

Recommendation for Hermes: every Kanban run should be representable as an inspectable state row plus a derived health record. A watchdog should not infer health from prose. It should compute it from task status, run id, assignee, claim age, pid liveness where available, last heartbeat, recent event type, required report presence, and notification outbox state.

### 2. Watchdogs should diagnose first, repair only under explicit policy

The PM docs require YOLO repair/reroute, but safety depends on a diagnostic-first design. Google SRE material emphasizes practical alerting, on-call, troubleshooting, incident response, and postmortems. The same shape should apply locally: detect, classify, recommend, then repair only when the action is routine, reversible, and within default-profile authority.

Recommended watchdog issue classes:

| Issue class | Detection input | Default action | Human block? |
|---|---|---|---|
| stale_running | task running, claim/run older than TTL, no heartbeat or pid dead | comment plus reclaim/reroute if policy allows | no |
| repeated_crash | same task has repeated crashed runs with no evidence | reassign to spawnable equivalent profile or route diagnosis | no, unless profile config/credential is missing |
| ready_not_spawning | ready/todo task older than spawn SLA | flag dispatcher/profile health | no |
| nonspawnable_assignee | ready task assigned to profile with repeated spawn failures | reassign or create profile-repair task | no, unless credential/setup is missing |
| blocked_protocol_violation | blocked only for routine review-required handoff | unblock or route reviewer/QA child | no |
| missing_required_report | run lacks intake/start/progress/handoff/review/closeout where required | warn and request scorecard evidence | no |
| outbox_backlog | report rows queued too long or retry exhausted | retry safe sends, summarize backlog | only if credentials/config missing |
| secret_risk | output contains token/cookie/private-key patterns | stop send, redact, route security | yes if unsafe artifact must be handled |

### 3. Notification delivery needs an outbox, not direct best-effort sends

The transactional outbox pattern solves the classic problem where state changes and message sends can diverge. Hermes should commit state/report intent first, then let a replayable sender deliver Telegram/Slack messages. Alertmanager's routing model also shows that notifications need grouping, silencing, inhibition, and receivers to avoid noisy pages.

Recommended local adaptation:

- `office_report_outbox.jsonl` or SQLite table with `id`, `task_id`, `run_id`, `report_type`, `destination`, `redaction_status`, `payload_hash`, `payload_redacted`, `created_at`, `sent_at`, `attempt_count`, `last_error`, `next_retry_at`.
- Sender is idempotent by `(task_id, run_id, report_type, payload_hash)`.
- Failed sends never erase the completion evidence. They remain queued with a redacted error summary.
- Doctor prints backlog count and oldest age, not raw payloads by default.

### 4. Dashboards should answer operator questions, not just plot metrics

Grafana, OpenTelemetry, Prometheus, Sentry, Langfuse, and AgentOps all converge on trace/log/metric correlation. For Hermes Office, the dashboard should answer:

- What is stuck right now?
- Which profile/assignee is failing to spawn or crashing repeatedly?
- Which completions lack evidence scorecards?
- Which Telegram reports are queued, failed, or redacted?
- Which tasks are blocked for real external reasons versus routine review/QA?
- Which worker produced unverifiable benchmark, runtime, release, or deployment claims?

The template should produce a terminal-friendly Doctor first and only then a dashboard data contract. A static JSON summary is enough for MVP.

### 5. Evidence gates should be policy checks, not reviewer memory

SLSA provenance defines verifiable information about where, when, and how artifacts were produced, with verification as an explicit purpose. OpenSSF Scorecard uses automated checks to assess open-source project security risks. OPA/conftest provides policy tests over structured data. Hermes should apply the same pattern to Kanban handoffs:

- Completion metadata must include a gate scorecard array.
- Each gate needs `gate`, `command_or_check`, `exit_code_or_artifact`, `verdict`, and `rationale`.
- Benchmark/performance/release/deploy claims require artifact paths and measured outputs.
- Prose-only claims should fail validation.
- Scope reductions require parseable `SCOPE_CHANGE_REQUEST` blocks.

### 6. 2026 landscape check

A targeted web search via DuckDuckGo was blocked by bot challenge, so this brief uses inspected official documentation and GitHub API metadata instead of fabricated search results. GitHub repository metadata checked on 2026-05-13 shows active, high-signal projects for durable execution, orchestration, observability, and policy gates. Notable caveat: `Netflix/conductor` and `grafana/oncall` appeared archived in GitHub API metadata, so they are useful references but should not be primary implementation dependencies.

## Recommended local templates to build

### A. `docs/office-superpowers/templates/OFFICE_RUNBOOK_TEMPLATE.md`

Sections:

- Service or workflow name.
- Owner and escalation path.
- Customer/user impact.
- Golden signals and local equivalents.
- Normal state commands.
- Triage decision tree.
- Safe repair commands.
- Unsafe actions requiring block/approval.
- Rollback/retry procedure.
- Evidence artifacts to attach.
- Postmortem prompts.

### B. `docs/office-superpowers/templates/OFFICE_GATE_SCORECARD_TEMPLATE.md`

Fields:

```yaml
gate_scorecard:
  - gate: ""
    command_or_check: ""
    exit_code_or_artifact: ""
    verdict: "PASS|FAIL|PARTIAL|BLOCKED|NOT_APPLICABLE"
    rationale: ""
    artifact_paths: []
    redaction_status: "checked|redacted|unsafe_blocked"
```

Required policy:

- Every completion must include at least one scorecard item.
- Heavy claims must cite real artifact paths.
- `mock_only`, `readme_only`, and `template_only` are not valid evidence for performance/release/deploy claims.

### C. `scripts/office_doctor.py`

No npm. Python stdlib plus existing repo APIs only.

Output sections:

1. Gateway health.
2. Messaging health: Telegram/Slack configured, outbox backlog, last safe send status.
3. Kanban board stats: ready/running/blocked/done counts.
4. Stale claims and dead pids.
5. Failed runs and repeated crash clusters.
6. Nonspawnable or degraded assignees.
7. Evidence gate failures.
8. Logs: safe paths and last error summaries with redaction.
9. Browser/dashboard access boundary.
10. Recommendations.

Exit behavior:

- 0: healthy or only informational findings.
- 1: actionable local repair recommended.
- 2: external blocker or unsafe secret exposure found.

### D. `scripts/office_watchdog.py`

Modes:

- `--dry-run`: print JSON findings only.
- `--repair-routine`: perform only approved routine repairs.
- `--json`: machine-readable summary for cron or dashboard.

Finding schema:

```json
{
  "issue_type": "stale_running|repeated_crash|ready_not_spawning|nonspawnable_assignee|blocked_protocol_violation|missing_required_report|outbox_backlog|secret_risk",
  "severity": "info|warn|page|block",
  "task_id": "t_xxx",
  "run_id": 0,
  "assignee": "profile",
  "age_seconds": 0,
  "evidence": ["event ids, log paths, or artifact paths"],
  "recommended_action": "",
  "auto_repair_allowed": false,
  "redaction_status": "checked"
}
```

### E. `scripts/office_report_outbox.py`

Functions:

- `enqueue(report_type, task_id, run_id, payload)`.
- `redact(payload)`.
- `send_due()`.
- `status()`.
- `retry_failed(max_age)`.

Required reliability behaviors:

- Idempotency key on task/run/type/hash.
- Exponential backoff with jitter.
- No raw token/cookie/private-key printing.
- Safe final status if destination credentials are missing: mark `blocked_external_config`, do not claim delivery.

### F. `scripts/office_scorecard_validate.py`

Validates markdown or JSON handoff metadata:

- Required scorecard keys present.
- Verdict in allowed enum.
- Artifact paths exist for artifact claims when local.
- Heavy claims have measured artifacts.
- `SCOPE_CHANGE_REQUEST` blocks parse if present.
- No obvious secrets or credential patterns.

### G. `docs/office-superpowers/references/OPS_RELIABILITY_PATTERNS.md`

Human-readable reference of these patterns with source links and license cautions.

## Reliability patterns to adopt

| Pattern | Source inspiration | Local Hermes adaptation |
|---|---|---|
| Durable execution | Temporal, LangGraph | Persist run state transitions and checkpoint summaries so crash recovery starts from evidence, not memory. |
| Worker heartbeat | RQ, Celery | Require worker heartbeat events for long tasks and stale detection. |
| Inspect/control plane | Celery, Airflow | Doctor/watchdog inspect Kanban, logs, gateway, and outbox through safe APIs. |
| Failure registry | RQ failed job registry, Temporal failure visibility | Store recent failed runs by task/assignee/failure mode for cluster diagnosis. |
| Retry policy with backoff | Temporal, SRE alerting guidance | Use retry budgets and jitter for notification sends and routine dispatch retries. |
| SLO-oriented alerting | Google SRE, Prometheus Alertmanager | Alert on user/operator impact: stuck tasks, missed reports, unsafe evidence, not raw log noise. |
| Notification grouping/inhibition | Alertmanager | Group repeated task/profile failures; inhibit noisy repeats after summary sent. |
| Transactional outbox | microservices.io pattern | Queue report intents durably before gateway delivery. |
| Trace/log/metric correlation | OpenTelemetry, Grafana, Sentry, Langfuse | Link task id, run id, assignee, tool call, and artifact paths in logs and summaries. |
| Policy-as-code gates | OPA/conftest, OpenSSF Scorecard | Validate completion scorecards and heavy-claim evidence programmatically. |
| Provenance | SLSA | Capture who/what/when/how for generated artifacts and benchmark claims. |
| Blameless postmortem | Google SRE | Use incident notes for repeated crashes and protocol gaps, not blame. |

## Failure modes and mitigations

| Failure mode | Why it matters | Mitigation template |
|---|---|---|
| Worker crashes before handoff | Board shows running/crashed but no evidence | Watchdog flags missing closeout, clusters by assignee, reroutes if routine. |
| Worker completes with prose-only benchmark claim | False confidence and broken release gate | Scorecard validator rejects heavy claim without measured artifact. |
| Notification sent directly but task update fails | Akhil sees stale or false status | Outbox writes intent after state update, sender retries independently. |
| Task update succeeds but Telegram send fails | Operator misses final status | Outbox backlog visible in Doctor; no false delivery claim. |
| Runbook missing owner/escalation | 3am diagnosis stalls | Runbook template requires owner, escalation, safe repairs, unsafe blockers. |
| Dashboard shows counts but not next action | Pretty but operationally weak | Doctor and dashboard findings include recommended action and auto-repair eligibility. |
| Redaction failure leaks credentials | Durable artifact risk | Pre-send and pre-complete secret scans; unsafe payloads block. |
| Watchdog auto-repairs destructive action | Autonomy boundary violation | Auto-repair allowlist only; destructive/irreversible actions block. |
| Repeated crash loops spam Telegram | Low-signal alert fatigue | Alertmanager-style grouping, suppression, and digest reports. |
| Agent loops without checkpointing | Lost progress and duplicate side effects | Checkpoint task state, idempotency keys, and artifact hashes. |

## Source records

| ID | URL/path | Title | Publisher | Type | Reliability | Claims supported | License notes |
|---|---|---|---|---|---|---|---|
| S1 | https://sre.google/sre-book/monitoring-distributed-systems/ | Monitoring Distributed Systems | Google SRE | official book | high | Golden signals, monitoring philosophy, alerting context | Web content for reference. Do not copy prose wholesale. |
| S2 | https://sre.google/workbook/alerting-on-slos/ | Alerting on SLOs | Google SRE | official workbook | high | SLO-based alerting, retry/backoff references, low-noise alerting | Reference only. |
| S3 | https://sre.google/workbook/on-call/ | On-Call | Google SRE | official workbook | high | On-call diagnostics and operational expectations | Reference only. |
| S4 | https://sre.google/workbook/postmortem-culture/ | Postmortem Culture | Google SRE | official workbook | high | Blameless postmortem and learning from failure | Reference only. |
| S5 | https://docs.temporal.io/encyclopedia/detecting-workflow-failures | Detecting Workflow failures | Temporal | official docs | high | Workflow failure visibility and observability hooks | Docs reference; Temporal repo MIT but do not vendor. |
| S6 | https://docs.celeryq.dev/en/stable/userguide/monitoring.html | Monitoring and Management Guide | Celery | official docs | high | Worker inspect/control, events, task lifecycle events, Flower | Celery license via project should be checked before copying examples. |
| S7 | https://python-rq.org/docs/workers/ | RQ Workers | RQ | official docs | high | Worker state, current job, heartbeat, success/failure counters | RQ license metadata via GitHub API returned NOASSERTION, check before copying. |
| S8 | https://prometheus.io/docs/alerting/latest/alertmanager/ | Alertmanager | Prometheus | official docs | high | Routing, deduplication, receiver-style alert management | Apache-2.0 repo ecosystem. Reference only. |
| S9 | https://opentelemetry.io/docs/concepts/observability-primer/ | Observability primer | OpenTelemetry | official docs | high | Observability vocabulary, SLIs/SLOs, traces/logs/metrics | Apache-2.0 ecosystem. |
| S10 | https://opentelemetry.io/docs/collector/ | Collector | OpenTelemetry | official docs | high | Collector pattern for telemetry pipeline | Apache-2.0 ecosystem. |
| S11 | https://grafana.com/docs/grafana/latest/dashboards/ | Dashboards | Grafana | official docs | high | Dashboard model and visualization reference | Grafana repo AGPL-3.0, avoid copying implementation. |
| S12 | https://microservices.io/patterns/data/transactional-outbox.html | Transactional Outbox | microservices.io | pattern catalog | medium-high | Durable notification/event outbox semantics | Pattern description reference. |
| S13 | https://docs.langchain.com/oss/python/langgraph/durable-execution | Durable execution | LangChain/LangGraph | official docs | high | Agent durable execution/checkpoint concept | LangGraph repo MIT. |
| S14 | https://langfuse.com/docs/observability/overview | LLM Observability and Application Tracing | Langfuse | official docs | high | LLM traces, evals, prompt/run observability | GitHub license metadata NOASSERTION, check before copying. |
| S15 | https://docs.agentops.ai/v2/introduction | Introduction | AgentOps | official docs | medium-high | Agent monitoring, cost tracking, benchmarking positioning | AgentOps repo MIT. |
| S16 | https://openssf.org/projects/scorecard/ | OpenSSF Scorecard | OpenSSF | official project page | high | Automated OSS security checks and risk assessment | OpenSSF Scorecard repo Apache-2.0. |
| S17 | https://slsa.dev/spec/v1.1/provenance | SLSA Provenance | SLSA | official spec | high | Artifact provenance and verification purpose | Spec reference. Browser page marks v1.1 retired; prefer latest for implementation. |
| S18 | https://github.com/open-policy-agent/conftest | conftest repository | Open Policy Agent | primary repo | high | Policy tests over structured config | GitHub API license NOASSERTION, check before copying. |
| S19 | https://github.com/temporalio/temporal | temporal repository | Temporal | primary repo | high | Active durable execution platform, MIT, 20,204 stars, pushed 2026-05-13 | MIT. |
| S20 | https://github.com/apache/airflow | airflow repository | Apache | primary repo | high | Active workflow scheduling/monitoring reference, Apache-2.0, 45,381 stars | Apache-2.0. |
| S21 | https://github.com/dagster-io/dagster | dagster repository | Dagster | primary repo | high | Active orchestration and observation of data assets, Apache-2.0, 15,491 stars | Apache-2.0. |
| S22 | https://github.com/PrefectHQ/prefect | prefect repository | Prefect | primary repo | high | Python resilient data pipeline orchestration, Apache-2.0, 22,381 stars | Apache-2.0. |
| S23 | https://github.com/Netflix/conductor | conductor repository | Netflix | primary repo | medium | Microservices orchestration reference, but archived per GitHub API | Apache-2.0, archived so reference only. |
| S24 | https://github.com/grafana/oncall | oncall repository | Grafana | primary repo | medium | Incident response and chat integration patterns, but archived per GitHub API | AGPL-3.0, archived. Do not copy. |
| S25 | https://github.com/grafana/grafana | grafana repository | Grafana | primary repo | high | Active dashboard platform reference, AGPL-3.0, 73,697 stars | AGPL-3.0, avoid code copying. |
| S26 | https://github.com/getsentry/sentry | sentry repository | Sentry | primary repo | high | Error tracking and performance monitoring reference | License metadata NOASSERTION, check before copying. |
| S27 | https://github.com/langchain-ai/langgraph | langgraph repository | LangChain | primary repo | high | Active resilient agents repo, MIT, 31,888 stars | MIT. |
| S28 | https://github.com/langfuse/langfuse | langfuse repository | Langfuse | primary repo | high | LLM observability/evals/prompt management platform | License metadata NOASSERTION, check before copying. |
| S29 | https://github.com/AgentOps-AI/agentops | agentops repository | AgentOps | primary repo | medium-high | Agent monitoring/cost/benchmark SDK, MIT, 5,542 stars | MIT. |
| S30 | https://github.com/OpenLineage/OpenLineage | OpenLineage repository | OpenLineage | primary repo | medium-high | Lineage metadata collection reference, Apache-2.0 | Apache-2.0. |

## Comparison notes

### Durable execution and orchestration

- Temporal is the strongest conceptual reference for durable execution, retries, workflow history, and failure visibility. It is overkill to vendor or run for Hermes MVP.
- LangGraph is the closest agent-native reference, especially for checkpointed/resumable agent flows.
- Airflow, Dagster, and Prefect are useful for dashboard and run-state UX, but Hermes should avoid adopting their dependency footprint for this task.
- Netflix Conductor is useful historically, but archived status means it should not anchor new implementation decisions.

### Worker queues

- Celery is the richest Python reference for worker inspection/control and event streams.
- RQ is the simplest model to emulate locally: worker states, heartbeats, job registries, failure registries.
- Hermes already has Kanban state and process tracking, so the local template should emulate the observability primitives rather than introduce a new queue.

### Observability and dashboards

- OpenTelemetry should shape naming and correlation: traces, logs, metrics, attributes such as `task_id`, `run_id`, `assignee`, `tool`, `artifact_path`, `verdict`.
- Grafana-style dashboards should remain a downstream visualization target. The first artifact should be Doctor JSON that any UI can consume.
- Sentry and Langfuse suggest error/performance/LLM-run visibility, but license metadata should be checked before copying sample structures.

### Notification and incident response

- Alertmanager should shape low-noise routing, grouping, suppression, and receiver config.
- Grafana OnCall has useful incident response references but is archived and AGPL-licensed, so treat it as a cautionary source rather than a template to copy.
- Transactional outbox is the right local primitive for Telegram reports.

### Evidence and policy gates

- SLSA gives the provenance mental model: what produced this artifact, when, from which inputs, under which builder.
- OpenSSF Scorecard gives the automated health-check model.
- OPA/conftest gives the policy-as-code shape. Hermes can start with Python stdlib validators and later route to OPA only if already approved.

## Decision options

### Option 1: Adopt a workflow engine

Use Temporal, Airflow, Dagster, or Prefect to run Office work.

Pros:
- Mature retry, scheduling, dashboard, observability.
- Large ecosystems.

Cons:
- Heavy dependency and operational footprint.
- Does not respect this task's no-install/minimal local template goal.
- Would shift Hermes architecture rather than strengthen current Kanban.

Verdict: not recommended for this task.

### Option 2: Build a small Hermes-native reliability kit

Use existing Kanban, logs, gateway, Python stdlib, and markdown docs. Borrow patterns from the inspected sources.

Pros:
- Fits no npm/no GPU constraints.
- Aligns with existing Office/Kanban model.
- Easy to test with seeded local states.
- Avoids license and supply-chain risk from copying large systems.

Cons:
- Requires disciplined schema design.
- Less feature-rich than full orchestration platforms.

Verdict: recommended.

### Option 3: Documentation-only runbooks

Only create markdown runbooks and checklists.

Pros:
- Fast and safe.

Cons:
- Does not satisfy watchdog, Doctor, outbox, or evidence validation needs.
- Weak FAANG signal because nothing enforces behavior.

Verdict: insufficient.

## Recommendation

Build Option 2: a Hermes-native reliability kit with five executable Python/shell artifacts and four docs/reference artifacts. Use official source patterns but do not copy implementation code. Keep license checks in the scorecard before importing any snippets.

Priority order:

1. `office_scorecard_validate.py` so all downstream work can be judged honestly.
2. `office_doctor.py` so the operator can inspect state safely.
3. `office_watchdog.py` in dry-run mode.
4. `office_report_outbox.py` for Telegram reliability.
5. Runbook and pattern reference docs.
6. Optional dashboard JSON contract after Doctor output stabilizes.

## Assumptions

- Existing Hermes Kanban state, logs, and gateway configuration are locally inspectable by implementation workers.
- Python 3 is available in the workspace. The parent PM task already observed that `python` may be absent while `python3` works.
- This research task does not implement scripts. It recommends script/doc shapes for downstream owners.
- License ambiguity is a blocker for copying code or templates, but not for citing inspected sources as references.

## Contradictions and uncertainty

- Search engine results were not used because DuckDuckGo returned a bot challenge. This increases reliance on official docs and GitHub API metadata rather than broad web ranking.
- GitHub API returned `NOASSERTION` for some popular repositories, including Celery, RQ, Sentry, Langfuse, and conftest. Downstream implementers should verify license files before copying any content.
- SLSA v1.1 provenance page was inspected and marked retired in the browser snapshot. Use the latest SLSA version for implementation, but the provenance principle remains valid.
- Archived repositories can still contain useful historical patterns, but they should not become dependencies.

## Follow-up research tasks

1. License/security review of any source whose snippets or structures are proposed for local templates.
2. Architecture task to define the exact Hermes Kanban/outbox schema and allowed auto-repair actions.
3. QA/evals task to create seeded fixture states for stale claims, repeated crashes, missing reports, outbox backlog, and secret-risk output.
4. Docs task to synthesize the runbook, gate scorecard, and reliability pattern templates from this brief.
5. Builder task to implement Doctor/watchdog/outbox/validator scripts with Python stdlib only.

## Gate scorecard for this research artifact

| Gate | Command/check | Exit code/artifact | Verdict | Rationale |
|---|---|---|---|---|
| Source plan read | `read_file docs/akhil-default-profile-superpowers-plan.md` | Artifact read: 39 lines | PASS | Extracted mission, constraints, and target deliverable. |
| Parent PM docs read | `read_file docs/office-superpowers/PRD.md`, `GATE_SCORECARD.md`, `TASK_GRAPH.md` | Artifacts read: PRD 272 lines, scorecard 128 lines, task graph 206 lines | PASS | Research aligns with R2, R3, R4, R6, R7, R9, and R10. |
| Web research performed | `curl`/browser fetch of official docs and GitHub API metadata | Official docs and repository metadata inspected; DuckDuckGo search blocked by bot challenge | PASS_WITH_CAVEAT | Used inspected primary/official sources instead of unaudited search snippets. Caveat recorded. |
| Deliverable written | File artifact check | `docs/office-superpowers/research/OPS_AGENT_TEMPLATE_RESEARCH.md` | PASS | Required deliverable exists with sources, repo links, patterns, failure modes, and recommended scripts/docs. |
| No npm installs | Session command review | No npm/pnpm/yarn/npx commands used | PASS | Only file tools, browser navigation, curl via Python tool, and Python stdlib logic were used. |
| Secret safety | Pending local regex scan after write | See Kanban completion metadata | PENDING_AT_WRITE | Final completion will include scan result. |
