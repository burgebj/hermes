"""Regression tests for the parentless crash-loop bug.

When a task has no parents (no task_links rows), ``recompute_ready`` previously
promoted it from ``blocked`` back to ``ready`` on every dispatcher tick because
``all([]) is True`` (vacuous truth).  The circuit-breaker would block it, the
dispatcher would immediately promote it, and an infinite loop resulted:

    gave_up → promote → spawn → crash → gave_up → promote → …

The fix (two parts):

1. **Vacuous-truth guard**: ``recompute_ready`` now skips promotion of
   parentless blocked tasks.  A task with no parents has no dependency to
   wait for; promoting it only re-queues a deterministic crash.

2. **Failure-counter reset guard**: When a blocked task **with** parents is
   promoted (because a parent just completed), ``consecutive_failures`` is
   reset to 0 as before — the conditions that caused the failure may have
   changed.  But we never reach this code path for parentless tasks now.

See: kanban_db.py ``recompute_ready()``, PR #XXXXX
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
# Part 1: Vacuous-truth guard — parentless blocked tasks stay blocked
# ---------------------------------------------------------------------------


def test_parentless_circuit_breaker_block_is_not_promoted(kanban_home: Path) -> None:
    """A parentless task blocked by the circuit breaker (no ``blocked`` event,
    only ``gave_up``) must NOT be promoted back to ``ready`` by
    ``recompute_ready``.  Promoting it would create an infinite crash loop
    because there's no dependency to wait for — the task will fail the
    same way on every dispatch tick."""
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="orphan task", assignee="worker")
        # Simulate circuit-breaker block: flip status directly, no
        # ``blocked`` event, plus a ``gave_up`` event — exactly what
        # ``_record_task_failure`` produces.
        conn.execute(
            "UPDATE tasks SET status='blocked', "
            "consecutive_failures=3, last_failure_error='unauthorized' "
            "WHERE id=?",
            (tid,),
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'gave_up', '{\"failures\": 3}', ?)",
            (tid, int(time.time())),
        )
        conn.commit()

        # Must NOT promote — parentless circuit-breaker blocks stay blocked.
        for _ in range(5):
            promoted = kb.recompute_ready(conn)
            assert promoted == 0, (
                "parentless circuit-breaker block must not be promoted"
            )
            assert kb.get_task(conn, tid).status == "blocked"


def test_parentless_circuit_breaker_block_stays_blocked_across_dispatch_ticks(kanban_home: Path) -> None:
    """Full end-to-end simulation of the crash loop.  After the dispatcher
    auto-blocks a parentless task (via ``gave_up``), subsequent
    ``recompute_ready`` calls must not promote it — the loop is broken."""
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="crash loop reproducer", assignee="worker")
        # Simulate: worker crashes, dispatcher auto-blocks.
        claim = kb.claim_task(conn, tid)
        assert claim is not None
        # Worker exits with code 1 → detect_crashed_workers flips to ready,
        # _record_task_failure trips breaker → blocked + gave_up.
        # We simulate that end state:
        conn.execute(
            "UPDATE tasks SET status='blocked', "
            "consecutive_failures=3, last_failure_error='pid 999 exited with code 1' "
            "WHERE id=?",
            (tid,),
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'crashed', '{\"pid\": 999}', ?)",
            (tid, int(time.time())),
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'gave_up', '{\"failures\": 3, \"error\": \"pid 999\"}', ?)",
            (tid, int(time.time()) + 1),
        )
        conn.commit()

        # Subsequent dispatcher ticks — must NOT promote.
        for _ in range(10):
            assert kb.recompute_ready(conn) == 0
            task = kb.get_task(conn, tid)
            assert task.status == "blocked"
            assert task.consecutive_failures == 3


def test_parentless_task_with_manual_kanban_block_is_also_sticky(kanban_home: Path) -> None:
    """A parentless task that a worker explicitly blocked via
    ``kanban_block`` is sticky (the #28712 guard) AND is also a
    parentless blocked task.  Both guards should keep it blocked."""
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="review request", assignee="worker")
        kb.claim_task(conn, tid)
        kb.block_task(
            conn, tid,
            reason="review-required: please check",
            expected_run_id=kb.get_task(conn, tid).current_run_id,
        )
        assert kb.get_task(conn, tid).status == "blocked"

        for _ in range(5):
            assert kb.recompute_ready(conn) == 0
            assert kb.get_task(conn, tid).status == "blocked"


# ---------------------------------------------------------------------------
# Part 2: Parented tasks still auto-recover (existing semantics preserved)
# ---------------------------------------------------------------------------


def test_blocked_task_with_done_parents_still_auto_promotes(kanban_home: Path) -> None:
    """A blocked task with a completed parent should still be promoted to
    ``ready`` and have its failure counter reset.  This preserves the
    pre-existing auto-recovery semantics for tasks that have a legitimate
    dependency waiting to resolve."""
    with kb.connect() as conn:
        parent = kb.create_task(conn, title="parent", assignee="a")
        child = kb.create_task(
            conn, title="child", assignee="a", parents=[parent],
        )
        kb.claim_task(conn, parent)
        kb.complete_task(conn, parent, result="ok")

        # Circuit-breaker block (no ``blocked`` event, ``gave_up`` only).
        conn.execute(
            "UPDATE tasks SET status='blocked', "
            "consecutive_failures=5, last_failure_error='auth error' "
            "WHERE id=?",
            (child,),
        )
        conn.commit()

        promoted = kb.recompute_ready(conn)
        assert promoted == 1
        task = kb.get_task(conn, child)
        assert task.status == "ready"
        assert task.consecutive_failures == 0
        assert task.last_failure_error is None


def test_blocked_task_with_incomplete_parents_stays_blocked(kanban_home: Path) -> None:
    """A blocked task whose parent is NOT done stays blocked — no vacuous
    truth issue because the task actually has a parent, just not done yet."""
    with kb.connect() as conn:
        parent = kb.create_task(conn, title="parent", assignee="a")
        child = kb.create_task(
            conn, title="child", assignee="a", parents=[parent],
        )
        # Parent is still todo, not done.
        conn.execute(
            "UPDATE tasks SET status='blocked', "
            "consecutive_failures=2, last_failure_error='error' "
            "WHERE id=?",
            (child,),
        )
        conn.commit()

        assert kb.recompute_ready(conn) == 0
        task = kb.get_task(conn, child)
        assert task.status == "blocked"
        assert task.consecutive_failures == 2


# ---------------------------------------------------------------------------
# Part 3: Failure counter reset guard
# ---------------------------------------------------------------------------


def test_parentless_blocked_task_failure_counter_not_reset(kanban_home: Path) -> None:
    """For a parentless blocked task, ``recompute_ready`` must skip it
    entirely -- neither promote nor reset ``consecutive_failures``.
    If the counter were reset without promoting, it would defeat the
    circuit breaker on the next dispatch tick."""
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="orphan", assignee="worker")
        conn.execute(
            "UPDATE tasks SET status='blocked', "
            "consecutive_failures=7, last_failure_error='unauthorized' "
            "WHERE id=?",
            (tid,),
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'gave_up', NULL, ?)",
            (tid, int(time.time())),
        )
        conn.commit()

        kb.recompute_ready(conn)
        task = kb.get_task(conn, tid)
        # Task stays blocked, counter stays at 7 — not promoted, not reset.
        assert task.status == "blocked"
        assert task.consecutive_failures == 7
        assert task.last_failure_error == "unauthorized"


# ---------------------------------------------------------------------------
# Part 4: Unblocked parentless task can still be dispatched
# ---------------------------------------------------------------------------


def test_unblocked_parentless_task_becomes_ready(kanban_home: Path) -> None:
    """After ``kanban_unblock``, a parentless task should transition to
    ``ready`` so it can be dispatched again (e.g. after an operator fixes
    the underlying issue like a bad API key)."""
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="will unblock", assignee="worker")
        # Block it (circuit-breaker style, no ``blocked`` event).
        conn.execute(
            "UPDATE tasks SET status='blocked', "
            "consecutive_failures=2, last_failure_error='bad auth' "
            "WHERE id=?",
            (tid,),
        )
        conn.execute(
            "INSERT INTO task_events (task_id, kind, payload, created_at) "
            "VALUES (?, 'gave_up', NULL, ?)",
            (tid, int(time.time())),
        )
        conn.commit()
        assert kb.get_task(conn, tid).status == "blocked"

        # Operator fixes the issue and unblocks.
        assert kb.unblock_task(conn, tid)
        task = kb.get_task(conn, tid)
        assert task.status == "ready"
        # unblock_task resets failure counters.
        assert task.consecutive_failures == 0


def test_parentless_todo_task_is_promoted_normally(kanban_home: Path) -> None:
    """A parentless task in ``todo`` status (manually set) should still be
    promoted to ``ready`` by ``recompute_ready`` -- todo -> ready is the
    normal promotion path and is unrelated to the circuit breaker.
    
    Note: ``create_task`` with no parents already sets status to ``ready``,
    so we manually flip a task to ``todo`` to test this path."""
    with kb.connect() as conn:
        tid = kb.create_task(conn, title="normal todo", assignee="worker")
        # Create_task with no parents sets status='ready'. Manually flip to todo.
        conn.execute("UPDATE tasks SET status='todo' WHERE id=?", (tid,))
        conn.commit()
        assert kb.get_task(conn, tid).status == "todo"
        # With no parents, this should be promoted to ready.
        promoted = kb.recompute_ready(conn)
        assert promoted == 1
        assert kb.get_task(conn, tid).status == "ready"