# Hermes Project Contract

## Purpose

Hermes Agent development workspace. The repository is the durable source of truth for code changes, documentation changes, task state, verification evidence, and agent handoffs.

## Repo Type

open-source software / agent runtime

## Startup

Read in order:

1. `AGENTS.md`
2. `.hermes/project.md`
3. `.hermes/task-schema.yaml`
4. `.hermes/tasks.yaml`
5. `tasks.md`
6. `README.md`
7. Relevant source files, tests, and docs for the claimed task

## Task Source

- Primary machine-readable queue: `.hermes/tasks.yaml`
- Human cockpit: `tasks.md`
- Run evidence and generated handoffs: `.hermes/runs/`

Agents should claim exactly one ready task before editing repository content when `.hermes/tasks.yaml` contains runnable work.

## Commands

- List tasks: `python3 scripts/next_task.py --list`
- Claim next task: `python3 scripts/next_task.py --claim --agent <agent-name>`
- Inspect task: `python3 scripts/next_task.py --task HERMES-T###`
- Validate workspace/task queue: `python3 scripts/finish_task.py --validate-only HERMES-T###`
- Finish and commit a completed task: `python3 scripts/finish_task.py HERMES-T### "short description" --all`

## Git Policy

- Default branch: `main`
- Commit granularity: one commit per task unless tasks are inseparable
- Push policy: push only after verification is complete and the task is explicitly ready to ship
- Dirty-state policy: never mix unrelated changes silently; report and isolate pre-existing dirt

## Documentation Policy

Check `README.md`, `AGENTS.md`, `.hermes/project.md`, `.hermes/task-schema.yaml`, `.hermes/tasks.yaml`, `tasks.md`, and relevant `website/docs/`, `tests/`, or code comments when behavior, workflow, configuration, command behavior, public APIs, or developer workflow changes.

## Version / Evidence

Evidence is exact command output, changed file paths, task ledger status, generated handoff path, and git commit hash when committed.
