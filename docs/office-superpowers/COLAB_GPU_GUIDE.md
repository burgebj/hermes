# Colab GPU Guide for Office Superpowers

Status: current policy and optional workflow
Last verified: 2026-05-13T01:12:55Z
Audience: Office workers handling GPU-heavy ML, benchmark, media, or model tasks

## Policy summary

There is no local GPU evidence for this Hermes Agent workspace. Do not claim local GPU, CUDA, or local accelerated benchmark proof unless a future task provides real hardware evidence.

Google Colab may be used as optional remote GPU proof when a task explicitly needs GPU execution and the operator has browser/login access. Colab is not required for CPU-sufficient tasks. If GPU proof is required and unavailable, emit `SCOPE_CHANGE_REQUEST` instead of claiming success.

## Decision matrix

| Task type | CPU/local proof enough? | Colab optional? | Required action |
|---|---:|---:|---|
| Docs, templates, policy, static analysis | Yes | No | State GPU not applicable. |
| Unit tests, py_compile, schema validation | Yes | No | Run local tests and record artifacts. |
| Small ML smoke test with tiny data | Usually yes | Optional | Record CPU command, metrics, runtime, limitations. |
| Training/inference proof that explicitly requires GPU | No | Yes | Use Colab or request scope change if unavailable. |
| Benchmark/performance claim involving GPU/CUDA | No | Yes | Capture exported Colab artifacts and raw result files. |
| Paid Colab Pro, cloud quota, or restricted data | No | Possibly blocked | Block for paid/cloud/credential/legal decision. |

## What counts as Colab evidence

Acceptable evidence:

- notebook path or link with no secrets in cells or outputs;
- exported executed notebook or HTML/PDF without tokens;
- runtime metadata: GPU type, Python version, CUDA/runtime information if available;
- exact command run inside the notebook;
- config path or inline config saved as an artifact;
- dataset manifest and checksum when applicable;
- raw logs and metrics JSON/CSV;
- output model/report artifact paths;
- limitations and failed cells if any.

Not sufficient by itself:

- a screenshot of a notebook cell;
- a README claim that Colab was used;
- a chart without raw metrics;
- a copied notebook that was not executed;
- a notebook output containing hidden local state or unexported files;
- any notebook containing tokens, cookies, private keys, or raw PII.

## Safe notebook pattern

Colab notebooks should be thin drivers around repository scripts. Avoid making notebook cells the only source of truth.

Recommended notebook flow:

1. Environment cell: print Python version, OS/runtime, GPU availability, and package versions already installed or explicitly installed by user-approved commands.
2. Repository cell: clone or mount the repo only if allowed by the task.
3. Data cell: fetch or mount data using a manifest; do not embed private data or credentials.
4. Command cell: call a repo script, for example `python -m project.train --config configs/train.yaml`.
5. Export cell: save metrics, logs, model artifacts, and notebook execution metadata.
6. Verification cell: print artifact paths and checksums.
7. Cleanup cell: remove temporary credentials if any were used; do not save them in output.

## Local template for a Colab artifact manifest

```json
{
  "schema_version": 1,
  "task_id": "t_xxxxxxxx",
  "colab_status": "not_required|optional_completed|required_completed|blocked_unavailable|failed",
  "created_at": "YYYY-MM-DDTHH:MM:SSZ",
  "notebook": {
    "path_or_url": "",
    "executed_export_path": "",
    "contains_secrets": false
  },
  "runtime": {
    "runtime_name": "Google Colab",
    "gpu_type": "",
    "python_version": "",
    "cuda_or_driver_summary": ""
  },
  "commands": [
    {
      "command": "",
      "exit_code_or_cell_status": "",
      "log_path": ""
    }
  ],
  "data": {
    "manifest_path": "",
    "checksum": "",
    "license": ""
  },
  "artifacts": [
    {
      "path": "",
      "kind": "metrics|log|model|report|notebook_export|other",
      "checksum": ""
    }
  ],
  "limitations": []
}
```

## Example gate scorecard entries

CPU-only task:

```json
{
  "gate": "GPU not required",
  "command_or_check": "content and task review",
  "exit_code_or_artifact": "Task is documentation/schema validation only; no GPU proof required",
  "artifact_paths": [],
  "verdict": "NOT_APPLICABLE",
  "rationale": "The requirement does not include GPU-dependent runtime claims."
}
```

GPU-required task completed in Colab:

```json
{
  "gate": "Colab GPU proof",
  "command_or_check": "executed notebook command cells listed in artifacts/colab_manifest.json",
  "exit_code_or_artifact": "required cells completed; metrics.json and run.log exported",
  "artifact_paths": ["artifacts/colab_manifest.json", "artifacts/metrics.json", "artifacts/run.log"],
  "verdict": "PASS",
  "rationale": "GPU-dependent claim is backed by exported Colab runtime metadata, command logs, and metrics artifacts."
}
```

GPU-required task unavailable:

```text
SCOPE_CHANGE_REQUEST
requirement_ref: GPU benchmark proof
requested_change: accept CPU smoke proof now and schedule Colab/GPU validation later, or provide Colab/cloud access
reason: no local GPU exists and no available Colab/runtime access was provided
attempted_evidence: local CPU tests completed; GPU runtime check unavailable
impact: benchmark/performance gate remains BLOCKED; implementation/functionality gate may be PARTIAL or PASS depending on CPU evidence
options:
  - provide Colab/cloud access for GPU run
  - downgrade requirement to CPU-only smoke proof
  - split GPU benchmark into a follow-up task
```

## Secret and data safety

- Never store API keys, OAuth tokens, cookies, private keys, SSH keys, phone numbers, raw user ids, or private dataset rows in notebook cells or outputs.
- Use `[REDACTED]` in exported logs when a value looks sensitive.
- If a notebook requires credentials, prefer environment/runtime secret mechanisms and do not persist values in the notebook.
- If private or licensed data is required, block for human/legal/data-owner approval.

## Colab is optional, not proof by default

Colab improves GPU availability, but it also introduces reproducibility risks: ephemeral runtimes, hidden notebook state, ad-hoc installs, user account state, and untracked files. Treat Colab as valid only when artifacts return to the repo or a safe referenced storage path and the scorecard points to those artifacts.

## Related files

- `docs/office-superpowers/templates/COLAB_GPU_POLICY_TEMPLATE.md`
- `docs/office-superpowers/research/ML_TEMPLATE_RESEARCH.md`
- `docs/office-superpowers/TEMPLATE_LIBRARY.md`
- `docs/office-superpowers/OPERATOR_RUNBOOK.md`
