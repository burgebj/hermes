---
title: "Morph GBrain Shell Jobs into Hermes Cron"
description: "Use GBrain v0.14 shell jobs to move deterministic cron work off the Hermes/OpenClaw gateway"
---

# Morph GBrain Shell Jobs into Hermes Cron

GBrain v0.14 added a proper `shell` Minion job type.
That is worth stealing.

Not for everything. For **deterministic cron work**.

Think:
- token refresh
- sync script
- scrape + write
- API fetch + file update
- anything that does not need reasoning

That work should not boot a full LLM session through the gateway. That's Einstein doing cash-register duty.

## What Hermes now supports

Hermes cron jobs can carry an optional `shell` block.
When present, `cron/scheduler.py` submits the work to the `gbrain jobs submit shell` CLI instead of launching an agent turn.

Example job shape:

```json
{
  "name": "sync deterministic feeds",
  "schedule": "*/15 * * * *",
  "prompt": "",
  "shell": {
    "cmd": "bash scripts/sync.sh",
    "cwd": "/abs/path/to/workspace",
    "queue": "default",
    "timeout_ms": 300000,
    "max_attempts": 3
  }
}
```

Required inside `shell`:

- exactly one of `cmd` or `argv`
- `cwd` must be absolute

Optional:

- `env`
- `queue`
- `timeout_ms`
- `max_attempts`
- `follow`

## Runtime behavior

When a cron job has `shell`, Hermes does this:

1. builds GBrain shell-job params
2. shells out to `gbrain jobs submit shell --params ...`
3. returns a cron run result marked `SHELL JOB SUBMITTED`
4. does **not** start `AIAgent`

That means:
- zero LLM tokens for the deterministic cron
- job visibility lives in GBrain Minions
- gateway CPU stays free for actual conversations

## Config knobs

Environment variables:

```bash
export HERMES_GBRAIN_CLI_PATH='gbrain'
export HERMES_GBRAIN_ALLOW_SHELL_JOBS=1
export HERMES_GBRAIN_AUTO_SHELL_CRON=1
export HERMES_GBRAIN_TIMEOUT=60
```

Default behavior already assumes `HERMES_GBRAIN_ALLOW_SHELL_JOBS=1` unless you explicitly turn it off.

`HERMES_GBRAIN_AUTO_SHELL_CRON=1` adds the no-brainer path: if a cron has **no prompt**, **no skills**, and only a `script`, Hermes auto-routes it to a GBrain shell job instead of booting `AIAgent` just to run Python. That gives existing script-only crons the calculator lane without making you hand-write a `shell` block every time.

## API server support

`POST /api/jobs` now accepts a `shell` field and passes it through to cron job creation.

So you can create these jobs via the Hermes API server, not just by editing JSON by hand.

## Example: move a sync off the gateway

Before:
- cron fires
- Hermes/OpenClaw starts a full agent turn
- same deterministic script every time
- tokens burned for no good reason

After:

```json
{
  "name": "nightly sync",
  "schedule": "0 2 * * *",
  "prompt": "",
  "shell": {
    "cmd": "bash scripts/sync.sh",
    "cwd": "/srv/brain",
    "timeout_ms": 600000,
    "max_attempts": 3
  }
}
```

Now the gateway only submits the job. GBrain Minions owns execution.

## When to use this

Use GBrain shell jobs for:
- deterministic cron tasks
- repeatable scripts
- zero-judgment collectors
- anything you'd trust in a shell script already

Do **not** use this for:
- research
- synthesis
- prioritization
- writing
- any task that actually needs judgment

Those still belong in agent jobs.

## Best pattern

The good split is:

- deterministic scheduled work -> `shell` Minion jobs
- judgment-heavy background work -> queue protocol + worker callbacks
- interactive reasoning -> live agent turn

That's the clean architecture. Not everything needs an LLM. Some things need a damn script.
