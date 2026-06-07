# Subscription Sprint — High-Throughput Parallel Lanes on a Short Quota Window

A **subscription sprint** maximizes useful work in the time before a Pro/Max
rate-limit window resets. Subscription billing runs on a rolling ~5-hour session
window with a fixed message/token allowance; when only a slice of that window is
left, the goal flips from "do one task well" to "land as many independent,
*harvestable* lanes as possible before the limit hits" — without sacrificing
safety.

Use this when: quota is partially burned, several **independent** chunks of work
are queued, and you want them running concurrently rather than serially. Do NOT
use it for tightly-coupled work (one lane's output feeds another) — serialize
that instead.

## 1. Pre-flight: measure the remaining window

Never start a sprint blind. Confirm auth and how much budget is left first.

```
# Auth + plan sanity (JSON is parseable; --text for humans)
terminal(command="claude auth status", timeout=20)

# In an interactive pane, /usage shows plan limits + rate-limit reset time
terminal(command="tmux new-session -d -s probe -x 140 -y 40 && tmux send-keys -t probe 'claude' Enter")
terminal(command="sleep 5 && tmux send-keys -t probe Enter")              # trust dialog
terminal(command="sleep 2 && tmux send-keys -t probe '/usage' Enter")
terminal(command="sleep 3 && tmux capture-pane -t probe -p -S -40")       # read reset time + remaining
terminal(command="tmux send-keys -t probe '/exit' Enter && tmux kill-session -t probe")
```

A quick print-mode probe also returns real spend in its JSON envelope — read
`total_cost_usd` and `usage` from any `--output-format json` run to calibrate how
expensive each lane is before fanning out.

**Budget math:** decide a per-lane turn/dollar cap from the remaining window.
If ~30 min and ~$2 of headroom remain, 3 lanes × `--max-turns 8`
× `--max-budget-usd 0.60` is a safe envelope. Leave ~20% slack — the window can
close mid-run.

## 2. Decompose into independent, idempotent lanes

Each lane must be:

- **Independent** — no lane reads another lane's uncommitted output.
- **Idempotent / re-runnable** — if it dies at the limit, re-running is harmless.
- **Isolated** — separate git worktree per lane so parallel writes never collide.
- **Scoped** — `--allowedTools` restricted to exactly what the lane needs.

```
# One isolated worktree per lane → no working-tree contention
terminal(command="cd /repo && git worktree add ../wt-auth   -b sprint/auth")
terminal(command="cd /repo && git worktree add ../wt-tests  -b sprint/tests")
terminal(command="cd /repo && git worktree add ../wt-docs   -b sprint/docs")
```

(Claude's own `-w <name>` flag creates `.claude/worktrees/<name>`; explicit
`git worktree` lanes are easier to harvest and clean up across many sessions.)

## 3. Launch the lanes (print mode, parallel)

Print mode (`-p`) is preferred for sprints: no PTY dialogs, structured JSON to
harvest, and a hard `--max-turns` / `--max-budget-usd` stop. Run each lane in its
own backgrounded tmux session and capture JSON to a file per lane.

```
# Lane A — bugfix, read+edit only
terminal(command="tmux new-session -d -s lane-auth -x 140 -y 40 && tmux send-keys -t lane-auth 'cd ../wt-auth && claude -p \"Fix the token-refresh race in src/auth.py. Do not touch other files.\" --allowedTools \"Read,Edit\" --max-turns 8 --max-budget-usd 0.60 --output-format json > /tmp/lane-auth.json 2>&1' Enter")

# Lane B — tests, no network, no destructive bash
terminal(command="tmux new-session -d -s lane-tests -x 140 -y 40 && tmux send-keys -t lane-tests 'cd ../wt-tests && claude -p \"Add pytest coverage for the API error paths.\" --allowedTools \"Read,Write,Bash(pytest*)\" --max-turns 12 --max-budget-usd 0.80 --output-format json > /tmp/lane-tests.json 2>&1' Enter")

# Lane C — docs, read+edit only
terminal(command="tmux new-session -d -s lane-docs -x 140 -y 40 && tmux send-keys -t lane-docs 'cd ../wt-docs && claude -p \"Update README API section to match current endpoints.\" --allowedTools \"Read,Edit\" --max-turns 5 --max-budget-usd 0.40 --output-format json > /tmp/lane-docs.json 2>&1' Enter")
```

**Why `--max-budget-usd` per lane:** a lane that hits the window limit returns
`subtype: "error_budget"` (or rate-limit retries surface as
`system/api_retry` events with `error: "rate_limit"` in stream-json). The cap
stops a stuck lane from eating the entire remaining quota.

**Throttle the fan-out.** 3–5 concurrent lanes is the practical ceiling on a
subscription — too many in flight and they collectively trip the rate limit, so
*all* lanes start failing instead of finishing. Stage extra lanes; launch the
next only as one frees up.

Add `--fallback-model haiku` to lower-stakes lanes so model overload degrades
gracefully instead of failing the lane.

## 4. Monitor + harvest

Poll all lanes together, then collect results from the JSON envelopes.

```
# Liveness sweep
terminal(command="sleep 45 && for s in lane-auth lane-tests lane-docs; do echo '=== '$s' ==='; tmux capture-pane -t $s -p -S -4 2>/dev/null; done")

# Harvest verdicts: success / which error / spend
terminal(command="for f in /tmp/lane-*.json; do echo \"== $f ==\"; jq -r '\"subtype=\\(.subtype) turns=\\(.num_turns) cost=$\\(.total_cost_usd)\"' \"$f\" 2>/dev/null || tail -3 \"$f\"; done")
```

Classify each lane by `subtype`:

| `subtype` | Meaning | Action |
|-----------|---------|--------|
| `success` | Lane finished | Review diff, then proceed to verify |
| `error_max_turns` | Hit turn cap | Inspect partial diff; resume with `--resume <id>` if window allows |
| `error_budget` | Hit `--max-budget-usd` | Likely stuck; read diff, decide manually |
| (rate_limit retries) | Window exhausted | Stop launching; wait for reset time from step 1 |

### Harvest checklist (run per lane before keeping anything)

- [ ] `subtype == "success"` (or a partial diff worth keeping).
- [ ] `git -C ../wt-<lane> diff` reviewed by a human — scope matches the lane brief, no stray files.
- [ ] Lane stayed in its worktree (no edits leaked to other branches/dirs).
- [ ] Tests/lint pass **inside the lane** before the branch is considered done.
- [ ] No secrets, tokens, or `.env` values introduced (see Safety Gates).
- [ ] Spend (`total_cost_usd`) summed across lanes is within the window budget.

## 5. Safety gates (non-negotiable)

A sprint trades oversight for throughput, so the guardrails are explicit:

1. **No secrets, ever.** Deny secret reads at the source so a fast lane can't
   exfiltrate or hard-code them. Put this in each worktree's
   `.claude/settings.json` (or pass `--disallowedTools`):
   ```json
   { "permissions": { "deny": ["Read(.env)", "Read(.env.*)", "Read(**/secrets/**)", "Bash(rm -rf*)", "Bash(git push*)"] } }
   ```
2. **No deploy / no merge without human approval.** Sprint lanes produce
   *branches and diffs only*. Never add `git push`, `gh pr merge`, or any deploy
   command to a lane's `--allowedTools`. Merging and deploying happen after a
   human reviews the harvested diffs — out of band from the sprint.
3. **Restrict tools per lane.** Default to `Read,Edit`. Add `Write`/`Bash(...)`
   only where the lane truly needs it, and scope `Bash(...)` to a command prefix
   (e.g. `Bash(pytest*)`) rather than blanket `Bash`.
4. **Avoid `--dangerously-skip-permissions` in unattended sprints.** It
   auto-approves everything; combined with parallel unmonitored lanes that is how
   an accident scales. If you must, pair it with the `deny` list above and a
   `PreToolUse` hook that blocks destructive commands.
5. **Hard caps on every lane.** Always set both `--max-turns` and
   `--max-budget-usd`. An uncapped lane can drain the whole remaining window.

## 6. Cleanup

```
# Kill all sprint panes
terminal(command="for s in lane-auth lane-tests lane-docs probe; do tmux kill-session -t $s 2>/dev/null; done")

# Remove worktrees once their branches are harvested/merged by a human
terminal(command="cd /repo && git worktree remove ../wt-auth && git worktree remove ../wt-tests && git worktree remove ../wt-docs")
terminal(command="cd /repo && git worktree prune")
```

## Pitfalls specific to sprints

1. **Too many concurrent lanes trip the shared rate limit** — and then *every*
   lane fails, not just the marginal one. 3–5 is the safe ceiling; stage the rest.
2. **Shared working tree = corrupted diffs.** Parallel lanes in the *same*
   directory clobber each other. One worktree per lane, always.
3. **The window closes mid-run.** Lanes in flight at reset return rate-limit
   errors; they are not "done." Re-check `subtype` before trusting any output.
4. **Unbounded lanes drain the window.** A single uncapped `--max-turns` lane can
   consume the quota you budgeted for five lanes. Cap everything.
5. **Silent partial work.** `error_max_turns` still leaves a real (incomplete)
   diff on the branch. Review it — don't auto-discard or auto-keep.
6. **Background tmux sessions persist** across the sprint and leak resources.
   Kill every session and prune every worktree in cleanup.
7. **Harvesting before verifying.** A `success` subtype means Claude finished, not
   that the code is correct. Tests/lint/human review gate the merge — the sprint
   does not.
