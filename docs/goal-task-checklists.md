# /goal implementation task checklist

This document is a copy-pasteable source for GitHub issues, PR descriptions, and implementation checklists for Hermes' persistent `/goal` feature.

## Feature snapshot

Hermes already ships a persistent `/goal` loop that keeps working across turns until the goal is done, paused, or budget-exhausted.

Core implementation surfaces:
- `hermes_cli/goals.py` — goal state, persistence, judge loop, continuation prompt
- `cli.py` — CLI `/goal` command handling and post-turn continuation
- `gateway/run.py` — gateway `/goal` command handling, FIFO continuation, status delivery
- `hermes_cli/commands.py` — slash-command registry entry
- `website/docs/user-guide/features/goals.md` — user-facing docs
- Tests:
  - `tests/hermes_cli/test_goals.py`
  - `tests/tui_gateway/test_goal_command.py`
  - `tests/gateway/test_goal_status_notice.py`
  - `tests/gateway/test_goal_verdict_send.py`
  - `tests/gateway/test_goal_max_turns_config.py`
  - `tests/cli/test_cli_goal_interrupt.py`

---

## 1) GitHub Issue: Persistent `/goal` standing-objective loop

**Title**

```text
Feature: persistent /goal loop that continues across turns until completion
```

**Body**

```md
## Summary
Add a persistent `/goal` feature that lets users set a standing objective Hermes keeps working on across turns until the goal is achieved, blocked, paused, cleared, or the turn budget is exhausted.

This is Hermes' take on the Ralph loop pattern popularized by Codex CLI's `/goal`, adapted to Hermes' architecture:
- persistence in SessionDB metadata
- continuation via normal user-role messages
- auxiliary-model judge after each turn
- CLI + gateway parity
- user-message preemption

## User experience
Supported commands:
- `/goal <text>` — set or replace the standing goal and kick off the first turn immediately
- `/goal` or `/goal status` — inspect current goal state
- `/goal pause` — pause the loop without clearing the goal
- `/goal resume` — resume the loop
- `/goal clear` — remove the goal

Expected behavior:
- After each turn, a judge checks whether the goal is complete.
- If not complete, Hermes automatically queues a continuation prompt into the same session.
- User messages always preempt queued continuations.
- If the judge fails, behavior is fail-open (`continue`) so the loop does not wedge.
- If the turn budget is exhausted, Hermes auto-pauses and explains how to proceed.
- If the judge returns unusable output repeatedly, Hermes auto-pauses and points the user to `auxiliary.goal_judge` config.

## Scope
### Core
- Persistent per-session goal state
- Goal lifecycle: active / paused / done / cleared
- Turn budget tracking
- Judge-based completion loop
- CLI support
- Gateway support
- User-facing docs
- Regression tests for continuation, pause/resume, status delivery, and config-driven budgets

### Non-goals
- No system-prompt mutation
- No special toolset swapping
- No multi-goal queueing
- No cross-session shared goals across unrelated sessions

## Implementation surfaces
- `hermes_cli/goals.py`
- `cli.py`
- `gateway/run.py`
- `hermes_cli/commands.py`
- `website/docs/user-guide/features/goals.md`

## Acceptance criteria
- `/goal <text>` persists the goal in session metadata and starts work immediately.
- CLI and gateway both support status / pause / resume / clear.
- After each successful turn, Hermes judges completion and either stops or enqueues continuation.
- Real user input preempts continuation on both CLI and gateway paths.
- Hitting `goals.max_turns` auto-pauses the goal.
- Repeated unparseable judge outputs auto-pause with actionable config guidance.
- State survives manager recreation and session resume.
- Tests cover parser behavior, fail-open semantics, pause/resume, config propagation, and interruption behavior.
```

---

## 2) PR Description: Core `/goal` implementation

**Title**

```text
feat: add persistent /goal loop across CLI and gateway
```

**Body**

```md
## Summary
This PR adds Hermes' persistent `/goal` loop: a standing objective that survives across turns and keeps the agent working until the goal is done, blocked, paused, cleared, or the configured turn budget is exhausted.

## What changed
- Added persistent goal state and judge loop in `hermes_cli/goals.py`
- Added `/goal` slash command registration in `hermes_cli/commands.py`
- Added CLI `/goal` command handling and post-turn continuation in `cli.py`
- Added gateway `/goal` command handling, queued kickoff, continuation, and status delivery in `gateway/run.py`
- Added user-facing docs in `website/docs/user-guide/features/goals.md`
- Added regression tests for parser behavior, persistence, config propagation, gateway notices, and interrupt behavior

## Design notes
- Goal state is stored in `SessionDB.state_meta` under `goal:<session_id>`.
- Continuations are appended as normal user-role messages rather than mutating the system prompt.
- Judge failures are fail-open so a broken judge does not wedge progress.
- Real user messages preempt continuations.
- Repeated judge parse failures auto-pause and point users to `auxiliary.goal_judge` config.

## Files touched
- `hermes_cli/goals.py`
- `hermes_cli/commands.py`
- `cli.py`
- `gateway/run.py`
- `website/docs/user-guide/features/goals.md`
- `tests/hermes_cli/test_goals.py`
- `tests/tui_gateway/test_goal_command.py`
- `tests/gateway/test_goal_status_notice.py`
- `tests/gateway/test_goal_verdict_send.py`
- `tests/gateway/test_goal_max_turns_config.py`
- `tests/cli/test_cli_goal_interrupt.py`

## Test plan
- [ ] Run `pytest tests/hermes_cli/test_goals.py`
- [ ] Run `pytest tests/tui_gateway/test_goal_command.py`
- [ ] Run `pytest tests/gateway/test_goal_status_notice.py`
- [ ] Run `pytest tests/gateway/test_goal_verdict_send.py`
- [ ] Run `pytest tests/gateway/test_goal_max_turns_config.py`
- [ ] Run `pytest tests/cli/test_cli_goal_interrupt.py`
- [ ] Verify `/goal` set / status / pause / resume / clear manually in CLI
- [ ] Verify gateway ordering: main reply arrives before goal-status notice

## Follow-ups
- Consider exposing richer `/goal` telemetry or history
- Consider multi-goal support only if a real use case emerges
- Consider additional judge hardening only if current parse-failure guard proves insufficient
```

---

## 3) Implementation checklist

```md
## Implementation checklist

### Goal state and persistence
- [ ] Define serializable `GoalState` with goal text, status, turns used, max turns, timestamps, verdict metadata, pause reason, and consecutive parse failures
- [ ] Persist state in `SessionDB.state_meta` under `goal:<session_id>`
- [ ] Provide load/save/clear helpers with defensive behavior when SessionDB is unavailable
- [ ] Ensure state survives GoalManager recreation and `/resume`

### Judge loop
- [ ] Add judge prompt templates for strict JSON verdicts
- [ ] Parse clean JSON, fenced JSON, and JSON embedded in prose
- [ ] Fail open on empty, malformed, or unavailable judge responses
- [ ] Track repeated parse failures separately from API/transport failures
- [ ] Auto-pause after repeated parse failures and include actionable `auxiliary.goal_judge` guidance

### Goal manager lifecycle
- [ ] Support `set`, `pause`, `resume`, `clear`, `status_line`, `is_active`, `has_goal`
- [ ] Increment turn count after each completed turn
- [ ] Mark goal `done` when judge says complete or blocked
- [ ] Auto-pause on turn-budget exhaustion
- [ ] Generate continuation prompt as a normal user-role message

### CLI integration
- [ ] Register `/goal` in `hermes_cli/commands.py`
- [ ] Implement CLI `/goal` subcommands in `cli.py`
- [ ] Kick off a newly set goal immediately by queueing the goal text
- [ ] After each turn, judge completion and requeue continuation when needed
- [ ] Auto-pause on Ctrl+C interruption instead of immediately re-continuing
- [ ] Skip judging on empty/whitespace-only responses

### Gateway integration
- [ ] Handle `/goal`, `/goal status`, `/goal pause`, `/goal resume`, `/goal clear`
- [ ] Reject setting a new goal mid-run when necessary to avoid continuation races
- [ ] Queue kickoff and continuation via adapter FIFO so real user messages preempt naturally
- [ ] Send goal-status notices after the main reply is delivered
- [ ] Clear pending continuations on pause/clear
- [ ] Honor `goals.max_turns` from config on gateway path

### Docs
- [ ] Document command semantics and behavior in `website/docs/user-guide/features/goals.md`
- [ ] Explain fail-open judge behavior
- [ ] Explain `goals.max_turns` config
- [ ] Explain optional `auxiliary.goal_judge` routing
- [ ] Credit Codex CLI / Ralph loop inspiration clearly

### Tests
- [ ] Parser tests for clean JSON, fenced JSON, prose-wrapped JSON, malformed JSON, and empty output
- [ ] Judge tests for done, continue, no aux client, and API failure cases
- [ ] GoalManager tests for set/pause/resume/clear/persistence
- [ ] Auto-pause tests for max-turn exhaustion and repeated parse failures
- [ ] CLI interruption tests for Ctrl+C pause behavior
- [ ] Gateway tests for command routing, queued continuation cleanup, ordering of status notices, and config-driven turn budgets
```

---

## 4) Optional PR split checklist

```md
## Suggested PR split

### PR 1 — core state + CLI
- [ ] Add `hermes_cli/goals.py`
- [ ] Register `/goal` command
- [ ] Wire CLI set/status/pause/resume/clear
- [ ] Add GoalManager unit tests
- [ ] Add CLI interrupt tests

### PR 2 — gateway integration
- [ ] Add gateway `/goal` command handling
- [ ] Add FIFO kickoff/continuation behavior
- [ ] Add post-delivery goal-status notices
- [ ] Add gateway tests for routing, pause/clear cleanup, and budget config

### PR 3 — docs + polish
- [ ] Add persistent goals docs page
- [ ] Add any copy/UX improvements
- [ ] Verify examples and config snippets
```
