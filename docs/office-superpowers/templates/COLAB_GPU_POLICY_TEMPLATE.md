# Colab / GPU Policy Template

Status: optional remote GPU evidence policy for Agent Office tasks.

## Baseline rule

Do not claim local GPU proof unless the current machine has a verified GPU and the command output is attached as evidence. For Akhil's default Office setup, assume no local GPU is available unless a live check proves otherwise.

## When Colab is acceptable

Colab is acceptable only as optional remote evidence for GPU-heavy workloads when:
- the task explicitly allows remote GPU evidence, or a scope-change block asks for it;
- no secrets/tokens are pasted into the notebook or logs;
- the notebook exports enough evidence for review: notebook file, runtime type, command output, dependency versions, and benchmark/model artifacts;
- paid Colab/Pro usage is treated as `paid_cloud_permission` and requires approval before use.

## Required evidence fields

- Task id:
- Colab notebook path or URL (redacted if private):
- Runtime type (CPU/T4/L4/A100/etc.):
- Commands run:
- Exit codes:
- Artifact paths:
- Limitations:
- Redaction status: checked/redacted

## Non-claims

A template, unchecked notebook, or screenshot without command output is not GPU proof. A CPU-only run cannot satisfy a GPU benchmark gate unless a `SCOPE_CHANGE_REQUEST` was accepted.
