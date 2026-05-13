# Agent Office Watchdog/Doctor deployment

This runbook packages the Office Doctor and Office Watchdog MVP into a safe, reversible local runner for Akhil's Hermes Agent Office. It does not by itself prove that any active profile currently has a ticking cron job.

## Scope

Current honest capability statement: this package provides dry-run Office diagnostics, evidence scorecard validation, and a local watchdog runner; live notification and safe repair remain follow-up work.

Component status:

- `scripts/office_doctor.py`: one-shot diagnostics for runtime, gateway, messaging config presence, kanban board readability, worker profiles, evidence gates, logs, browser/dashboard policy, and recommendations.
- `scripts/office_watchdog.py`: one-shot board watchdog that reports stale/risky Office states. It is dry-run by default and does not mutate the board unless a future reviewed repair path is added.
- `scripts/office_watchdog_cron.py`: quiet no-agent cron runner. Empty stdout means healthy/silent; non-empty stdout is a redacted alert suitable for local delivery; Telegram delivery remains gated on the live-sender/smoke-test follow-up.
- `scripts/office_watchdog_cron_install.py`: safe install/status/enable/disable/remove/smoke wrapper.
- `scripts/office_report_outbox.py`: redacted report outbox. It stores durable pending/sent/failed state fields and its CLI send/retry commands are queued/dry-run previews until a reviewed gateway sender is wired.

Out of scope:

- Production deploy approval.
- Secret or token inspection.
- Live Telegram sender implementation inside `office_report_outbox.py`.
- Destructive/automatic board mutation.

## Safety model

The local runner is designed to be safe because:

1. The persistent cron job runs `--no-agent`; it does not invoke an LLM, spend model tokens, or expand tool authority.
2. The cron runner only calls Doctor/Watchdog builders and prints redacted alerts. It does not repair, reassign, unblock, delete, or edit tasks.
3. The runner is copied to `HERMES_HOME/scripts/office_watchdog_cron.py`, which is the only location accepted by Hermes cron script validation.
4. Disable is a pause operation by default. Removal is a separate explicit command.
5. Any installed job should use `deliver=local` to avoid Telegram spam while the current board has known actionable findings. Switch to `deliver=telegram` only after the live notification follow-up is implemented, reviewed, and smoke-tested, and alert volume is acceptable.

## Current installed state is profile-scoped

Do not treat this document as proof that a watchdog is currently deployed or ticking. Cron jobs and copied scripts are scoped to the active Hermes profile and `HERMES_HOME`. A status check from one profile can legitimately report `runner_exists=false` and `jobs=[]` even if another profile installed a job.

The intended production Office watchdog scheduling profile is `telegram`: Hermes cron ticks from the gateway process, and the local `telegram` profile is the active launch gateway namespace. DevOps still owns this runbook and rollback evidence, but the cron runner/job must be installed and verified in the live gateway profile rather than in a dormant worker profile. Launch signoff must therefore use `python3 scripts/office_watchdog_cron_install.py --profile telegram status` and must not claim active protection from a job stored in any other profile namespace.

Expected installed job shape when the intended Office profile has been configured:

- Name: `Agent Office Watchdog (no-agent)`
- Schedule: `every 30m`
- Script: `office_watchdog_cron.py` under that profile's `HERMES_HOME/scripts/`
- Mode: `no_agent=true`
- Delivery: `local` until live notification smoke tests pass
- Workdir: `/Users/akhilkinnera/Documents/My Workspace/Hermes/hermes-agent`

Verify the exact profile, job id, delivery target, scheduler state, and next run locally:

```bash
python3 scripts/office_watchdog_cron_install.py --profile telegram status
hermes cron list --all
hermes cron status
```

If `python3 scripts/office_watchdog_cron_install.py --profile telegram status` reports `ok=false`, missing runner/jobs, `profile_alignment_ok=false`, or `scheduler_liveness.summary.ok=false`, launch signoff cannot claim active cron protection. If `hermes cron status` reports that the gateway/scheduler is not running, cron jobs may exist but will not fire automatically until the `telegram` profile gateway is running. On macOS installs under TCC-protected folders such as `~/Documents`, `hermes gateway start` may leave the launchd service loaded but crashed with a `pyvenv.cfg` permission error; in that case use `hermes gateway run --replace` for live scheduler evidence and record the service persistence risk until the install is moved or granted permissions.

## Recommended cron mode

Recommended mode: no-agent script cron.

Use no-agent because this is a watchdog, not an analysis task:

- deterministic checks;
- no token cost;
- no prompt-injection exposure from board text beyond the redacted script output;
- empty stdout stays silent;
- failures surface as scheduler errors.

Use an LLM-driven cron job only for a separate daily/weekly digest that summarizes already-collected Doctor/Watchdog artifacts. Do not use an LLM-driven job for the high-frequency watchdog path.

## Install / enable / disable / remove

From the Hermes Agent repository root:

```bash
# Install if missing. Default schedule is every 30m; default delivery is telegram.
# For conservative local-only deployment, pass --deliver local.
python3 scripts/office_watchdog_cron_install.py install --schedule 'every 30m' --deliver local

# Show copied runner and matching jobs.
python3 scripts/office_watchdog_cron_install.py status

# Pause matching jobs without deleting them.
python3 scripts/office_watchdog_cron_install.py disable

# Resume paused matching jobs.
python3 scripts/office_watchdog_cron_install.py enable

# Remove matching cron jobs. This does not delete source files.
python3 scripts/office_watchdog_cron_install.py remove

# Recreate matching jobs from scratch.
python3 scripts/office_watchdog_cron_install.py install --replace --schedule 'every 30m' --deliver local
```

Equivalent direct Hermes CLI creation command:

```bash
hermes cron create 'every 30m' \
  'Run the Agent Office Watchdog no-agent runner. Empty stdout means healthy/silent; non-empty stdout is a redacted alert.' \
  --name 'Agent Office Watchdog (no-agent)' \
  --script office_watchdog_cron.py \
  --no-agent \
  --deliver local \
  --workdir '/Users/akhilkinnera/Documents/My Workspace/Hermes/hermes-agent'
```

Important: `--script` must be relative to `HERMES_HOME/scripts/`. Do not pass an absolute path.

## Smoke tests

Run the one-shot Doctor and Watchdog checks:

```bash
python3 scripts/office_doctor.py --json > /tmp/office_doctor.json
python3 scripts/office_watchdog.py --dry-run --json > /tmp/office_watchdog.json
python3 scripts/office_watchdog_cron.py --always-print --json > /tmp/office_watchdog_cron_smoke.json
python3 scripts/office_watchdog_cron_install.py smoke --json > /tmp/office_watchdog_install_smoke.json
```

Expected outcomes:

- Doctor exits `0` for pass/warn and `1` for fail.
- Watchdog exits `0` when no findings, `1` when warning/error findings exist, and `2` when critical findings exist.
- The cron runner exits `0` when silent/healthy, `1` when warning/error alerts exist, and `2` when critical alerts exist.
- Existing findings on the board are not deployment failures; they prove alerting works.

## Telegram smoke-test instructions

Live Telegram notification is not a current capability of `office_report_outbox.py`, and cron delivery must remain `local` until a reviewed sender/state machine and smoke evidence exist. Use a one-shot/manual smoke only to prove the broader gateway can deliver a redacted test message before a future implementation switches the persistent job to Telegram delivery:

1. Confirm the gateway can see Telegram config without printing secrets:

```bash
python3 scripts/office_doctor.py --json | python3 -c 'import json,sys; d=json.load(sys.stdin); print([s for s in d["sections"] if s["id"]=="messaging"][0])'
```

2. Confirm gateway/cron scheduler state:

```bash
hermes gateway status
hermes cron status
```

3. Send a direct redacted test message with the Hermes messaging tool or from an interactive Hermes session. Message body should contain no tokens, chat ids, or user ids:

```text
Agent Office Watchdog Telegram smoke: redacted dry-run test from local deployment. No secrets included.
```

4. Only after the live sender remediation is reviewed and the one-shot Telegram test is received, switch the cron job delivery from local to Telegram:

```bash
python3 scripts/office_watchdog_cron_install.py disable
hermes cron list --all
hermes cron edit <job_id> --deliver telegram
python3 scripts/office_watchdog_cron_install.py enable
```

5. Trigger one scheduler run only after checking current alert volume:

```bash
python3 scripts/office_watchdog_cron.py --always-print
hermes cron run <job_id>
hermes cron tick
```

If Telegram delivery fails, immediately revert to local delivery:

```bash
hermes cron edit <job_id> --deliver local
```

Do not paste bot tokens, chat ids, raw user ids, or gateway credentials into logs, docs, Kanban comments, or Telegram smoke messages.

## Rollback

Fast rollback (pause only):

```bash
python3 scripts/office_watchdog_cron_install.py disable
```

Full rollback (remove cron job):

```bash
python3 scripts/office_watchdog_cron_install.py remove
hermes cron list --all
```

Optional cleanup of copied runner after removal:

```bash
rm "$HOME/Documents/My Workspace/Hermes/.hermes/profiles/devops/scripts/office_watchdog_cron.py"
```

Source files in the repository should be reverted through Git if the feature is rejected:

```bash
git status --short
git diff -- docs/office-superpowers/DEPLOYMENT.md scripts/office_watchdog_cron.py scripts/office_watchdog_cron_install.py
```

## No-npm verification

This deployment path uses only Python stdlib plus existing Hermes repository modules. It does not require or perform any npm, pnpm, yarn, or npx command.

Verification commands:

```bash
git diff -- docs/office-superpowers/DEPLOYMENT.md scripts/office_watchdog_cron.py scripts/office_watchdog_cron_install.py
python3 -m py_compile scripts/office_watchdog_cron.py scripts/office_watchdog_cron_install.py
python3 scripts/office_watchdog_cron_install.py smoke --json
```

## Operational response

When the watchdog alerts:

1. Run `python3 scripts/office_doctor.py --json` and `python3 scripts/office_watchdog.py --dry-run --json`.
2. Triage critical/error findings before warnings.
3. Do not apply automatic repairs unless a reviewed repair routine exists and the relevant policy flag is explicitly confirmed.
4. Keep evidence in task metadata or scorecard artifacts, not in raw Telegram prose.
