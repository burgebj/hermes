# Office Superpowers Template Library

Status: synthesized local templates from inspected parent research
Last verified: 2026-05-13T01:12:55Z
Sources: `research/OPS_AGENT_TEMPLATE_RESEARCH.md`, `research/ML_TEMPLATE_RESEARCH.md`, `PRD.md`, `ARCHITECTURE.md`, and current MVP scripts

## Purpose

This library turns the FAANG/open-source research lanes into local Hermes templates. It is not a vendor import and does not copy upstream projects wholesale. It adapts proven patterns into original, repo-local structures that Office workers can use without npm installs, without local GPU claims, and without unsafe license assumptions.

## Source principles

Use patterns, not wholesale scaffolds:

- Google SRE / Alertmanager style: low-noise, impact-oriented alerts with grouping and inhibition.
- Temporal / LangGraph style: durable state and replayable evidence.
- Celery / RQ style: inspectable worker state, heartbeat, failure registries, and control-plane commands.
- Transactional outbox pattern: state transition and notification intent are durable and replayable. The local template uses a transactional outbox-style report intent before delivery.
- OpenTelemetry / Grafana / Sentry / Langfuse style: correlate task id, run id, logs, and artifacts.
- OPA / OpenSSF Scorecard / SLSA style: policy-as-code and provenance for important claims.
- Cookiecutter Data Science style: clear ML project directory shape.
- DVC / MLflow style: dataset, run, metrics, and artifact provenance.
- Hugging Face Model/Dataset Cards and TensorFlow Model Card Toolkit concepts: structured model/data documentation.
- MLCommons/MLPerf style: predeclared benchmark protocols and raw result artifacts.
- W&B Reports style: narrative experiment reports, but not SaaS as a required gate.
- Kedro / Vertex AI samples style: modular pipelines and notebooks, with cloud coupling optional only.

License policy:

- Apache-2.0 and MIT references are conceptually safe to adapt with attribution.
- Sources with no API-detected license, archived status, or service-specific terms should be treated as conceptual references only.
- Any legal ambiguity should block for human/legal decision before copying code, prose, or result tables.

## Template 1: Office runbook

Recommended path: `docs/<area>/RUNBOOK.md`

```markdown
# <Service or workflow> Runbook

Status: current | proposed | planned | demo-only
Owner: <profile/team>
Last verified: <UTC timestamp>

## Purpose
<What this workflow/service does for users/operators.>

## Scope
In scope:
- <actions covered>

Out of scope:
- <actions not covered>

## Prerequisites
- <local env, credentials presence without values, workspace, permissions>

## Normal operation
```bash
<exact command>
```
Expected output:
- <safe summary, never raw secrets>

## Triage decision tree
1. If <critical symptom>, run <check>.
2. If <routine issue>, repair/reroute with evidence.
3. If <real blocker>, add SCOPE_CHANGE_REQUEST and block.

## Safe repair commands
```bash
<reversible command>
```

## Unsafe actions requiring approval
- credentials or secrets;
- paid/cloud actions;
- destructive irreversible actions;
- legal/license decisions;
- missing runtime/hardware;
- unverifiable claims.

## Rollback
```bash
<rollback command>
```

## Evidence to attach
- command/check;
- exit code;
- artifact path;
- verdict;
- rationale.

## Troubleshooting
| Symptom | Check | Remediation | Escalation |
|---|---|---|---|
| <symptom> | <command> | <safe action> | <owner> |
```

## Template 2: Agent/ops reliability scorecard

Recommended path: `docs/<area>/GATE_SCORECARD.md` or completion metadata.

```json
{
  "schema_version": 1,
  "task_id": "t_xxxxxxxx",
  "policy_version": "office-superpowers-v1",
  "created_at": "YYYY-MM-DDTHH:MM:SSZ",
  "gates": [
    {
      "gate": "Task orientation",
      "command_or_check": "kanban_show(<task_id>)",
      "exit_code_or_artifact": "worker_context loaded; parent handoffs reviewed",
      "artifact_paths": [],
      "verdict": "PASS",
      "rationale": "Acceptance gates and constraints were extracted before work."
    },
    {
      "gate": "Deliverable exists",
      "command_or_check": "test -f <path>",
      "exit_code_or_artifact": "exit 0",
      "artifact_paths": ["<path>"],
      "verdict": "PASS",
      "rationale": "The required artifact exists in the workspace."
    },
    {
      "gate": "No secret leakage",
      "command_or_check": "python3 <secret-scan-script-or-inline-check>",
      "exit_code_or_artifact": "exit 0; no matches",
      "artifact_paths": [],
      "verdict": "PASS",
      "rationale": "Touched files contain no obvious token/private-key/credential patterns."
    }
  ],
  "scope_change_requests": []
}
```

Rules:

- Heavy claims require artifact paths.
- `README says so` is not evidence for runtime, deployment, release, performance, benchmark, or GPU claims.
- `PASS_WITH_CAVEAT` is acceptable only when the caveat is explicit and does not invalidate the gate.

## Template 3: Office Doctor report

Current implementation: `scripts/office_doctor.py` backed by `hermes_cli/office_superpowers.py`.

Expected JSON shape:

```json
{
  "schema_version": 1,
  "policy_version": "office-superpowers-v1",
  "created_at": "<UTC>",
  "board": "default",
  "overall_status": "pass|warn|fail",
  "sections": [
    {
      "id": "runtime",
      "status": "pass|warn|fail",
      "summary": "Local runtime inspected",
      "details": {}
    }
  ]
}
```

Required sections for future extensions:

- runtime;
- gateway;
- messaging;
- Kanban board;
- worker profiles;
- notifications;
- evidence gates;
- logs;
- browser/dashboard;
- recommendations.

## Template 4: Watchdog finding

Current implementation: `scripts/office_watchdog.py` backed by `hermes_cli/office_superpowers.py`.

```json
{
  "issue_type": "stale_running_claim|repeated_failure_cluster|ready_task_not_spawning|nonspawnable_assignee|blocked_protocol_violation|missing_gate_scorecard|outbox_backlog|secret_risk_payload",
  "severity": "warning|error|critical",
  "task_id": "t_xxxxxxxx",
  "assignee": "profile-name",
  "recommendation": "specific safe next action",
  "safe_auto_repair": "comment_only|audit_comment_only|route_qa_child_task|reassign_to_configured_equivalent_only|ping_or_reclaim_if_dispatcher_policy_allows"
}
```

Design rules:

- Diagnose before repair.
- Default mode is dry-run/no mutation.
- Non-empty cron stdout is an alert; empty stdout means healthy/silent.
- Redact task text and errors before delivery.

## Template 5: Report outbox payload

Current implementation: `scripts/office_report_outbox.py` and helper functions in `hermes_cli/office_superpowers.py`.

```json
{
  "schema_version": 1,
  "policy_version": "office-superpowers-v1",
  "report_type": "started|blocked|completed|qa_failed|scope_change|watchdog_digest|doctor_summary",
  "task_id": "t_xxxxxxxx",
  "title": "Task title",
  "state": "running|blocked|done|failed",
  "assignee": "profile-name",
  "evidence_summary": "short redacted evidence summary",
  "artifact_paths": ["safe/path.json"],
  "next_owner_or_action": "profile or next action",
  "blocker_type": null,
  "created_at": "<UTC>",
  "redaction_status": "checked|redacted"
}
```

Current limitation: the outbox has a durable local state machine (`pending`, `sent`, `failed`, `attempts`, `last_error`, `next_attempt_at`, `sent_at`) for reviewed sender injection, but the CLI `send-due` and `retry-failed` surfaces are queued/dry-run previews only. Live Telegram/gateway delivery is explicitly deferred; see `OUTBOX_DELIVERY_DEFERRAL.md`.

## Template 6: ML/reproducibility project skeleton

Recommended path for future ML projects such as Gradient:

```text
project/
  README.md
  LICENSE
  CITATION.cff
  pyproject.toml
  configs/
    train.example.yaml
    eval.example.yaml
  data/
    README.md
    manifests/
      dataset_manifest.example.json
  notebooks/
    colab/
      README.md
      <project>_colab.ipynb
  src/<package>/
    __init__.py
    data.py
    train.py
    evaluate.py
    report.py
  tests/
  artifacts/
    experiments/
      README.md
    benchmarks/
      README.md
  reports/
    MODEL_CARD.md
    DATASET_CARD.md
    EVALUATION_REPORT.md
    BENCHMARKS.md
    LIMITATIONS.md
```

Keep DVC, MLflow, W&B, and cloud tools optional unless the task explicitly requires them and credentials are available safely. A local JSON/CSV artifact is preferred over screenshots for acceptance gates.

## Template 7: Dataset manifest

```json
{
  "dataset_name": "",
  "version": "",
  "source_url_or_path": "",
  "license": "",
  "download_or_access_command": "",
  "checksum": "",
  "split_policy": "",
  "preprocessing_command": "",
  "pii_or_sensitive_data_review": "not_applicable|passed|blocked",
  "known_limitations": []
}
```

Rules:

- Public does not mean license-safe.
- Do not commit large datasets by default.
- Do not include private data or raw PII in examples.

## Template 8: Experiment run manifest

```json
{
  "run_id": "",
  "created_at": "",
  "git_commit": "",
  "git_dirty": true,
  "hardware": "CPU|Colab GPU artifact path|other",
  "python_version": "",
  "command": "",
  "config_path": "",
  "dataset_manifest": "",
  "seed": 0,
  "metrics_path": "artifacts/experiments/<run_id>/metrics.json",
  "logs_path": "artifacts/experiments/<run_id>/run.log",
  "model_artifact_path": "",
  "limitations": []
}
```

Rules:

- If hardware says GPU or Colab, include exported Colab/runtime artifacts.
- If metrics are compared, dataset version, split policy, and preprocessing must match.

## Template 9: Model card

```markdown
# Model Card: <model>

## Status
current | experimental | demo-only

## Summary

## Intended use

## Out-of-scope use

## Training data
- Dataset manifest: <path>

## Evaluation data
- Dataset manifest or split: <path>

## Metrics
| Metric | Value | Artifact | Command |
|---|---:|---|---|

## Risks and limitations

## Bias/fairness/safety notes

## Environmental or compute notes

## License and citation
```

## Template 10: Benchmark report

```markdown
# Benchmarks

Status: measured | reproduced | failed | not_applicable | blocked
Last verified: <UTC>

## Protocol
- Task:
- Dataset/version:
- Hardware/runtime:
- Command:
- Seeds:
- Success threshold:

## Results
| Run | Metric | Value | Raw artifact | Log |
|---|---|---:|---|---|

## Caveats

## Reproduction
```bash
<exact command>
```
```

Rules:

- Define threshold before running.
- Store raw logs and summary JSON/CSV.
- Do not compare across changed hardware/data/splits without labeling the comparison invalid or exploratory.

## Template 11: Colab handoff artifact

```json
{
  "colab_required": false,
  "reason": "optional remote GPU proof only",
  "notebook_path": "notebooks/colab/<name>.ipynb",
  "runtime": {
    "gpu_type": "",
    "python_version": "",
    "cuda_version": ""
  },
  "command_cells_executed": [],
  "artifacts_exported": [],
  "secrets_used": false,
  "limitations": []
}
```

Rules:

- Notebook output alone is not enough; export artifacts back to the repo or a safe storage path.
- Never store tokens in notebook cells or outputs.

## Template 12: Scope change request

```text
SCOPE_CHANGE_REQUEST
requirement_ref: <requirement or deliverable>
requested_change: <specific change>
reason: <why current requirement cannot be met>
attempted_evidence: <commands/checks/artifacts tried>
impact: <gates affected>
options:
  - <option A>
  - <option B>
```

Use this when the honest answer is partial or blocked, not when more routine work can satisfy the requirement.

## Copy/adapt/reject summary

| Source family | Copy/adapt | Reject |
|---|---|---|
| SRE/Alertmanager | low-noise alerts, grouping, runbook shape | alert spam or paging on every log line |
| Temporal/LangGraph | durable state and resumability concepts | replacing Kanban for MVP |
| Celery/RQ | inspect/control and worker health concepts | adding external queue dependency for this MVP |
| OpenTelemetry/Grafana/Sentry | task/run/log/artifact correlation | dashboards without operator actionability |
| OPA/OpenSSF/SLSA | policy checks and provenance | prose-only evidence gates |
| Cookiecutter Data Science | directory hygiene | treating directory shape as reproducibility |
| DVC/MLflow | manifests, metrics, artifacts | requiring SaaS/cloud/remote credentials by default |
| Hugging Face cards | model/dataset card sections | cards without data provenance or limitations |
| MLCommons/MLPerf | benchmark discipline | copying code/results with unclear license |
| Colab | optional GPU runtime | claiming local GPU proof or storing secrets in notebooks |
