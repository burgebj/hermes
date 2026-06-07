# Post-Merge Verification

Merging a PR is the *start* of the base-branch lifecycle, not the end. The squash
commit that lands on `main` triggers a fresh, independent set of workflow runs —
CI re-runs against the integrated tree, and deploy pipelines fire. The checks you
watched on the PR branch (Section 4 of the skill) do **not** cover these. This
reference documents the verification loop Hermes/Coop sessions should run after
every merge.

## Why base-branch runs differ from PR-branch runs

- PR-branch checks run against the *merge preview* (your branch + a test merge).
  Base-branch runs run against the *actual squash commit*.
- Deploy workflows are almost always gated on `push` to `main`, so they only
  exist after the merge.
- A stale PR branch can pass its own checks yet break `main` once squashed — the
  AGENTS.md "stale squash merge silently reverts fixes" pitfall. Base-branch runs
  are where that shows up.

The reliable key tying a merge to its runs is the **merge commit SHA**, exposed
as `mergeCommit.oid` on the PR. Filter `actions/runs?head_sha=<SHA>` to get
exactly the runs that commit produced.

## Pre-merge `mergeStateStatus` cheat sheet

`gh pr view N --json mergeable,mergeStateStatus,reviewDecision` returns the gate
state. `mergeStateStatus` values:

| Value | Meaning | Action |
|-------|---------|--------|
| `CLEAN` | Mergeable, all checks green | merge |
| `UNSTABLE` | Mergeable, a non-required check is failing/pending | usually safe to merge; confirm the failing check isn't load-bearing |
| `HAS_HOOKS` | Mergeable with pre-receive hooks | merge |
| `BEHIND` | Branch is behind base | update branch first (`gh pr update-branch N`) |
| `BLOCKED` | Required review or check not satisfied | resolve before merging |
| `DIRTY` | Merge conflict | rebase/resolve |
| `DRAFT` | PR is a draft | mark ready first |

`mergeable` is the coarse signal (`MERGEABLE` / `CONFLICTING` / `UNKNOWN`);
`UNKNOWN` means GitHub is still computing — re-query after a few seconds.

## The verification loop

1. **Resolve the merge commit.** `SHA=$(gh pr view N --json mergeCommit -q .mergeCommit.oid)`.
   Empty ⇒ the PR is not actually merged; stop.
2. **Discover base-branch runs by SHA.** `gh api repos/$OWNER/$REPO/actions/runs?head_sha=$SHA`.
3. **Classify.** failure if any run concluded `failure`/`timed_out`/`startup_failure`;
   pending if any run is not `completed`; otherwise success.
4. **Watch** the runs to completion (`gh run watch <id>`, or the script's `--watch`).
5. **Probe deployment surfaces.** Once runs are green, GET the live health/probe
   endpoints and confirm the expected status. A green deploy job does not prove
   the app actually came up.

`scripts/post_merge_verify.py` automates steps 1–5. It shells out to `gh` (which
carries its own auth), parses JSON in Python (no `jq`), never reads or prints a
token, and redacts token-shaped strings from any captured output defensively.

## Deploy / probe checklist

After CI is green on the base branch, verify the surface that actually changed:

- **HTTP service** — GET a health endpoint (`/healthz`, `/api/status`) and assert
  the status code. Prefer a probe that exercises a real code path over a static
  `200`.
- **Gateway / bot** — confirm the process reconnected (platform "online" state)
  and that a `/status`-style command responds, rather than only checking the
  deploy job's exit code.
- **CLI / package** — install the freshly published artifact in a clean
  environment and run `--version` / a smoke command.
- **Static site / docs** — fetch a known URL and grep for content that only the
  new build contains, to defeat CDN cache false-positives.

Probe *after* runs succeed, not in parallel — a probe against a half-deployed
surface produces misleading flakes.

## Exit-code contract (`post_merge_verify.py`)

| Code | Meaning |
|------|---------|
| 0 | Merge verified — base-branch runs succeeded (and probes returned expected status) |
| 1 | A run concluded in failure, or a probe failed |
| 2 | Usage / environment error (`gh` missing, PR not merged, repo unresolved) |
| 3 | Runs still pending after `--timeout` (only with `--watch`) |

Wire these into automation: treat `1` as a rollback/alert trigger, `3` as
"keep watching", and `2` as a setup bug.
