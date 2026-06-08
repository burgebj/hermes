"""Regression tests for #28712 and #32747 — kanban dispatcher must
not auto-promote worker-initiated ``kanban_block`` or protocol-violation
sticky blocks, but must keep auto-recovering transient circuit-breaker
blocks (crash / timeout / spawn-failure).

The bug: when a worker called ``kanban_block(reason="review-required:
...")`` to hand off to a human, the dispatcher's ``recompute_ready``
would promote the task back to ``ready`` on the next tick.  The fresh
worker found nothing to do (work already applied), exited cleanly, and
got recorded as a ``protocol_violation`` → ``gave_up`` → promote → loop
until manual intervention.

These tests pin down:

* Worker / operator-initiated blocks are sticky and survive
  ``recompute_ready``.
* Circuit-breaker blocks (``gave_up`` event, status flipped via
  ``_record_task_failure``) still auto-recover — the original intent
  of #40c1decb3 is preserved.
* An explicit ``kanban_unblock`` clears the sticky state.
* The full block → promote → crash → ``gave_up`` loop is broken after
  this fix: subsequent ticks leave the task blocked.

The tangentially related schema-init ordering bug originally reported
in #28712 (``init_db`` crashing on legacy DBs that pre-dated the
``session_id`` migration) is covered separately by
``test_kanban_db.py::test_connect_migrates_legacy_db_before_optional_column_indexes``,
landed via #28754 / #28781 ahead of this fix.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb


@pytest.fixture
def kanban_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated HERMES_HOME with an empty kanban DB."""
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb.init_db()
    return home


# ---------------------------------------------------------------------------
# Worker-initiated kanban_block must be sticky
# ---------------------------------------------------------------------------


def test_worker_block_is_not_auto_promoted_by_recompute_ready(kanban_home: Path) -> None:
    """A standalone task that a worker explicitly blocks for review
    must stay blocked across an arbitrary number of dispatcher ticks.
    Before #28712's fix, ``recompute_ready`` would silently flip it
    back to ``ready`` on the very next tick."""
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="needs human review")
        kb.claim_task(conn, tid)
        assert kb.block_task(
            conn, tid,
            reason="review-required: please verify ACL change",
            expected_run_id=kb.get_task(conn, tid).current_run_id,
        )
        assert kb.get_task(conn, tid).status == "blocked"

        # Hammer the promotion code — exactly the dispatcher loop's
        # behaviour, just compressed in time.
        for _ in range(5):
            promoted = kb.recompute_ready(conn)
            assert promoted == 0, "worker-blocked task must not auto-promote"
            assert kb.get_task(conn, tid).status == "blocked"


def test_worker_block_on_child_with_done_parents_is_still_sticky(kanban_home: Path) -> None:
    """The parent-completion path is the one ``recompute_ready`` was
    designed for, so it's the most dangerous false-positive: even when
    every parent is done, a worker-initiated block on the child must
    stay blocked."""
    with kb.connect() as conn:
        parent = kb.create_task(conn, title="parent")
        child = kb.create_task(conn, title="child", parents=[parent])
        kb.complete_task(conn, parent, result="parent ok")

        kb.claim_task(conn, child)
        kb.block_task(
            conn, child,
            reason="review-required: child needs sign-off",
            expected_run_id=kb.get_task(conn, child).current_run_id,
        )
        assert kb.get_task(conn, child).status == "blocked"

        promoted = kb.recompute_ready(conn)
        assert promoted == 0
        assert kb.get_task(conn, child).status == "blocked"


# ---------------------------------------------------------------------------
# Circuit-breaker blocks still auto-recover (preserve #40c1decb3 intent)
# ---------------------------------------------------------------------------


def test_circuit_breaker_block_still_auto_promotes(kanban_home: Path) -> None:
    """A child that was put into ``blocked`` *without* a worker-issued
    ``kanban_block`` (e.g. a transient crash, manual DB triage) and whose
    ``consecutive_failures`` is still *below* the circuit-breaker limit
    must get auto-promoted when its parents complete — preserves the
    pre-#28712 recovery semantics for genuinely transient failures.

    The complementary case — a block whose failure count has *reached*
    the limit must stay blocked — is covered by
    ``test_kanban_db.py::test_recompute_ready_skips_tasks_at_failure_limit``
    (#35072).  Together they pin the contract: ``recompute_ready`` defers
    the give-up decision to the same effective limit the breaker uses, so
    the two never disagree.
    """
    with kb.connect() as conn:
        parent = kb.create_task(conn, title="parent")
        child = kb.create_task(conn, title="child", parents=[parent])
        kb.complete_task(conn, parent, result="ok")

        # Simulate a transient circuit-breaker / direct triage that flips
        # status without emitting a ``blocked`` event — exactly what
        # ``_record_task_failure`` does below the limit.  One failure is
        # under the default limit (2), so recovery is still correct.
        conn.execute(
            "UPDATE tasks SET status='blocked', consecutive_failures=1, "
            "last_failure_error='transient error' WHERE id=?",
            (child,),
        )
        conn.commit()

        promoted = kb.recompute_ready(conn)
        assert promoted == 1
        task = kb.get_task(conn, child)
        assert task.status == "ready"
        # Counter is preserved across recovery (not reset) so the breaker
        # can still accumulate if the task keeps failing (#35072).
        assert task.consecutive_failures == 1


def test_gave_up_event_alone_does_not_make_block_sticky(kanban_home: Path) -> None:
    """The circuit-breaker emits ``gave_up`` (not ``blocked``).  Make
    sure ``_has_sticky_block`` doesn't accidentally treat ``gave_up``
    as sticky — otherwise we'd regress the safety net for genuinely
    transient crashes."""
    with kb.connect() as conn:
        parent = kb.create_task(conn, title="parent")
        child = kb.create_task(conn, title="child", parents=[parent])
        kb.complete_task(conn, parent, result="ok")

        # Status + event match what _record_task_failure writes when
        # the breaker trips.
        conn.execute(
            "UPDATE tasks SET status='blocked' WHERE id=?", (child,),
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'gave_up', NULL, ?)",
            (child, int(time.time())),
        )
        conn.commit()

        promoted = kb.recompute_ready(conn)
        assert promoted == 1
        assert kb.get_task(conn, child).status == "ready"


def test_protocol_violation_block_is_sticky(
    kanban_home: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test for #32747 — a task that hit a protocol
    violation (worker exited rc=0 without calling
    ``kanban_complete`` / ``kanban_block``) must stay blocked across
    ``recompute_ready`` ticks.  Pre-fix, ``_has_sticky_block`` ignored
    the ``protocol_violation`` event and the dispatcher would promote
    the task back to ``ready``, only for the next worker spawn to do
    the exact same thing and trip the breaker again — burning API
    budget indefinitely (37 tasks × 270+ cycles in the field report).
    """
    import hermes_cli.kanban_db as _kb
    # detect_crashed_workers' grace window would otherwise skip the
    # liveness check on a just-claimed task.
    monkeypatch.setenv("HERMES_KANBAN_CRASH_GRACE_SECONDS", "0")
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="quiet", assignee="worker")
        host_prefix = _kb._claimer_id().split(":", 1)[0]
        kb.claim_task(conn, tid, claimer=f"{host_prefix}:mock")
        fake_pid = 999996
        kb._set_worker_pid(conn, tid, fake_pid)

        # Simulate a clean rc=0 exit by the worker subprocess.
        _kb._record_worker_exit(fake_pid, 0)
        original_alive = _kb._pid_alive
        _kb._pid_alive = lambda p: False
        try:
            kb.detect_crashed_workers(conn)
        finally:
            _kb._pid_alive = original_alive

        # detect_crashed_workers already auto-blocked it on the first
        # occurrence (existing behavior).  The new contract is the
        # *next* tick must NOT un-block it.
        assert kb.get_task(conn, tid).status == "blocked"
        kinds = [e.kind for e in kb.list_events(conn, tid)]
        assert "protocol_violation" in kinds, kinds

        for _ in range(5):
            promoted = kb.recompute_ready(conn)
            assert promoted == 0, (
                "protocol-violation block must survive recompute_ready"
            )
            assert kb.get_task(conn, tid).status == "blocked"


def test_protocol_violation_block_clears_on_unblock(kanban_home: Path) -> None:
    """Operator must still be able to unblock a protocol-violation
    sticky.  After ``unblock_task`` the most-recent
    ``{blocked, unblocked, protocol_violation}`` event is
    ``"unblocked"``, so the sticky predicate returns False and the
    task can be re-dispatched."""
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="t")
        # Synthesize the post-protocol-violation state directly: the
        # detect_crashed_workers path is covered by the test above; here
        # we want to pin down only the unblock semantics.
        conn.execute(
            "UPDATE tasks SET status='blocked', consecutive_failures=1 "
            "WHERE id=?",
            (tid,),
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'protocol_violation', NULL, ?)",
            (tid, int(time.time())),
        )
        conn.commit()

        # Pre-unblock: sticky guard fires, no promotion.
        assert kb.recompute_ready(conn) == 0
        assert kb.get_task(conn, tid).status == "blocked"

        assert kb.unblock_task(conn, tid)
        # unblock_task flips straight to 'ready' when there are no
        # undone parents, and emits the 'unblocked' event that clears
        # the sticky predicate.
        assert kb.get_task(conn, tid).status == "ready"
        assert kb.get_task(conn, tid).consecutive_failures == 0


def test_rejected_completion_after_reclaim_counts_and_stays_blocked(
    kanban_home: Path,
) -> None:
    """A worker that calls ``kanban_complete`` after its run was
    reclaimed must count toward the same breaker as other terminal
    non-successes.  Before #32747's follow-up, this path returned
    False but left ``consecutive_failures`` unchanged, so the task
    could re-dispatch forever.
    """

    def reclaim_current_run(conn, task_id: str) -> int:
        run = kb.latest_run(conn, task_id)
        assert run is not None
        conn.execute(
            "UPDATE tasks SET claim_expires=? WHERE id=?",
            (int(time.time()) - 1, task_id),
        )
        conn.commit()
        assert kb.release_stale_claims(conn) == 1
        assert kb.get_task(conn, task_id).status == "ready"
        return int(run.id)

    with kb.connect() as conn:
        tid = kb.create_task(conn, title="late completion", assignee="worker")

        kb.claim_task(conn, tid)
        run1_id = reclaim_current_run(conn, tid)
        assert not kb.complete_task(
            conn,
            tid,
            summary="late completion after reclaim",
            expected_run_id=run1_id,
        )
        task = kb.get_task(conn, tid)
        assert task.status == "ready"
        assert task.consecutive_failures == 1

        kb.claim_task(conn, tid)
        run2_id = reclaim_current_run(conn, tid)
        assert not kb.complete_task(
            conn,
            tid,
            summary="late completion after second reclaim",
            expected_run_id=run2_id,
        )
        task = kb.get_task(conn, tid)
        assert task.status == "blocked"
        assert task.consecutive_failures == 2

        kinds = [e.kind for e in kb.list_events(conn, tid)]
        assert kinds.count("completion_rejected") == 2
        assert "gave_up" in kinds

        for _ in range(3):
            assert kb.recompute_ready(conn) == 0
            assert kb.get_task(conn, tid).status == "blocked"


def test_old_rejected_completion_does_not_make_transient_block_sticky(
    kanban_home: Path,
) -> None:
    """A below-limit rejected completion should not poison later
    transient circuit-breaker recovery for the same task.
    """
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="mixed failures", assignee="worker")

        kb.claim_task(conn, tid)
        run = kb.latest_run(conn, tid)
        assert run is not None
        conn.execute(
            "UPDATE tasks SET claim_expires=? WHERE id=?",
            (int(time.time()) - 1, tid),
        )
        conn.commit()
        assert kb.release_stale_claims(conn) == 1
        assert not kb.complete_task(
            conn,
            tid,
            summary="late completion below limit",
            expected_run_id=run.id,
        )
        assert kb.get_task(conn, tid).status == "ready"

        conn.execute(
            "UPDATE tasks SET status='blocked', consecutive_failures=2, "
            "last_failure_error='pid 123 killed by signal 9' WHERE id=?",
            (tid,),
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'gave_up', NULL, ?)",
            (tid, int(time.time())),
        )
        conn.commit()

        assert kb.recompute_ready(conn) == 1
        task = kb.get_task(conn, tid)
        assert task.status == "ready"
        assert task.consecutive_failures == 0


# ---------------------------------------------------------------------------
# unblock_task clears the sticky state
# ---------------------------------------------------------------------------


def test_unblock_clears_sticky_state_and_lets_block_recover(kanban_home: Path) -> None:
    """``hermes kanban unblock`` (or the ``kanban_unblock`` tool) is
    the only legitimate way out of a worker-initiated block.  After
    unblock, a *subsequent* circuit-breaker block on the same task
    must again be eligible for auto-recovery."""
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="t")
        kb.claim_task(conn, tid)
        kb.block_task(
            conn, tid,
            reason="review-required: ...",
            expected_run_id=kb.get_task(conn, tid).current_run_id,
        )
        assert kb.unblock_task(conn, tid)
        # After unblock the task is no longer blocked at all.
        assert kb.get_task(conn, tid).status == "ready"

        # Now simulate a *later* circuit-breaker block (no new
        # ``blocked`` event, just status flip).  The most recent
        # block/unblock event is ``unblocked`` → guard does not fire
        # → recompute can recover.
        conn.execute(
            "UPDATE tasks SET status='blocked' WHERE id=?", (tid,),
        )
        conn.commit()

        promoted = kb.recompute_ready(conn)
        assert promoted == 1
        assert kb.get_task(conn, tid).status == "ready"


# ---------------------------------------------------------------------------
# Full bug-shaped loop: block → promote → crash → gave_up → next tick
# ---------------------------------------------------------------------------


def test_protocol_violation_loop_is_broken(kanban_home: Path) -> None:
    """Reproduces the exact #28712 loop and asserts the dispatcher
    leaves the task blocked instead of cycling.

    Loop shape from the issue:

    1. Worker calls ``kanban_block`` → status='blocked',
       ``task_runs.outcome='blocked'``, ``blocked`` event.
    2. (Bug) Dispatcher promotes back to ``ready``.
    3. Fresh worker exits cleanly without terminal tool call →
       ``protocol_violation`` event.
    4. ``_record_task_failure(failure_limit=1)`` → ``gave_up`` event,
       status='blocked' again.
    5. (Bug) Dispatcher promotes again → infinite loop.

    With the fix in place, step 2 never happens — the test simulates
    one would-be loop cycle by faking the crash-then-gave_up entries
    that *would* have been written and asserts the *next* tick still
    leaves the task blocked.
    """
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="loop reproducer")
        kb.claim_task(conn, tid)
        kb.block_task(
            conn, tid,
            reason="review-required: human eyes please",
            expected_run_id=kb.get_task(conn, tid).current_run_id,
        )
        assert kb.get_task(conn, tid).status == "blocked"

        # First dispatcher tick — must NOT promote.
        assert kb.recompute_ready(conn) == 0
        assert kb.get_task(conn, tid).status == "blocked"

        # Simulate the (hypothetical) protocol_violation + gave_up
        # entries that the dispatcher would have written if the bug
        # were still present.  Even with those event rows in place,
        # the worker-initiated ``blocked`` event is the most recent
        # of the ``{blocked, unblocked}`` pair, so the sticky guard
        # still fires.
        now = int(time.time())
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'protocol_violation', NULL, ?)",
            (tid, now),
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'gave_up', NULL, ?)",
            (tid, now + 1),
        )
        conn.commit()

        # Subsequent ticks must still leave it blocked.
        for _ in range(3):
            promoted = kb.recompute_ready(conn)
            assert promoted == 0
            assert kb.get_task(conn, tid).status == "blocked"


# ---------------------------------------------------------------------------
# Schema-init recovery on legacy DBs is covered by
# tests/hermes_cli/test_kanban_db.py::test_connect_migrates_legacy_db_before_optional_column_indexes
# (landed via #28754 / #28781).  The original PR shipped a duplicate test
# here; dropped during salvage to avoid two assertions of the same contract.
# ---------------------------------------------------------------------------
