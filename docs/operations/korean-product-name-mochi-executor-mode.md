# Korean Product Name Workflow: Mochi Executor Mode

Date: 2026-05-14

## Principle

The role rule is not that Mochi can never execute work. The rule is that the documented role and the actual executor must match.

Rules can be changed. After they are changed, execution must follow the updated rule.

Dodoli is not deleted and its function is not fully moved away. Dodoli remains available as a repeatable batch executor. The Korean product-name batch function is duplicated into Mochi so Mochi can operate as an executor when Slack agent slots are limited.

## Executor Modes

### `executor_mode: dodoli`

- Mochi coordinates, requests Pumi review, asks the user for final approval, and reports final status.
- Dodoli executes the batch, creates pending/review files, and after approval performs DB dry-run/apply/verification.
- Pumi reviews quality and policy.

### `executor_mode: mochi_absorbed_dodoli_function`

- Mochi coordinates and also executes the former Dodoli product-name batch function.
- Mochi may run schema check, read-only fetch, candidate generation, pending/review creation, approved DB dry-run/apply, and post-apply verification.
- Pumi still reviews quality and policy.
- Dodoli remains installed and available; this is functional duplication, not deletion or full migration.

## Required Safety Gates

- Pumi review before final user approval request.
- Explicit user final approval before DB apply.
- Timestamped/job-numbered pending file for DB work; do not use a bare `latest_pending_updates.json` as the apply target.
- Bind `job_number`, `item_ids`, and `source_fingerprint` before DB access.
- Dry-run before `--confirm-apply`.
- Re-query affected DB rows and compare expected vs actual Korean names after apply.
- Final report must include `executor_mode`.

## Runtime Skill Updates

Runtime profile skills were updated under `~/.hermes/profiles`:

- `mochi/skills/coordination/mochi-lead-coordinator`
- `mochi/skills/commerce/hermes-team-orchestration`
- `mochi/skills/commerce/korean-product-name-translation` (copied from Dodoli)
- `mochi/skills/commerce/commerce-product-name-apply-updates` (copied from Dodoli)
- `pumi/skills/commerce/korean-product-name-translation`
- `pumi/skills/commerce/pumi-commerce-specialist`
- Dodoli skills remain in place.

## Kanban

Default board task: `t_4ba3e77a`.
