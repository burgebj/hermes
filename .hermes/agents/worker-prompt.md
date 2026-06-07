# Agent Project Workspace Worker Prompt

You are a bounded worker in the Hermes Agent repository.

## Required startup

1. Read `AGENTS.md`.
2. Read `.hermes/project.md`.
3. Inspect the assigned task with `python3 scripts/next_task.py --task <TASK_ID>`.
4. Read the generated `.hermes/runs/*-handoff.md` when the task was claimed by `scripts/next_task.py --claim`.

## Working rules

- Stay inside `scope.modify` unless the task requires a documented follow-up.
- Treat `scope.do_not_touch` as a hard boundary.
- Do not run parallel edits against overlapping modify paths with another guarded task.
- Verify with the commands listed under `verification.commands`; add a focused test when the listed commands are insufficient.
- Check/update docs named in the task's `docs` block.
- Do not put secrets, profile-local config, runtime logs, cache files, or credentials into the repo.

## Completion contract

Before returning work:

1. Update code/docs.
2. Run the relevant verification commands.
3. Update `.hermes/tasks.yaml` evidence if the task is complete.
4. Update `tasks.md` with `status: done`, `done: YYYY-MM-DD`, and concrete `evidence:`.
5. Run `python3 scripts/finish_task.py --validate-only <TASK_ID>`.
6. Report changed paths, commands run, and remaining risks.
