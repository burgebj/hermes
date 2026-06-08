"""Regression tests for #34253 — Feishu (and other platforms) session
cancellation could orphan the session guard, permanently blocking
subsequent messages.

When ``cancel_session_processing()`` waits 5s for the old task to exit
and the task doesn't exit in time (``asyncio.TimeoutError``), the
previous code path:

1. Removed the task from ``_session_tasks`` but the task kept running
   (orphaned).
2. When the orphan eventually finished, its ``finally`` block checked
   ``self._session_tasks.get(session_key) is current_task`` — False,
   because the task had already been popped. So
   ``_release_session_guard()`` was never called.
3. ``_active_sessions[session_key]`` was never released.
4. All subsequent messages for that session went into
   ``_pending_messages`` with no runner to dispatch them.

This was particularly common when multiple platforms accessed the same
session (e.g. ``/stop`` from CLI cancelling a Feishu DM mid-task).

The fix:
- On ``TimeoutError``, force-clear ``_expected_cancelled_tasks`` +
  ``_active_sessions`` so the next message can start fresh.
- When releasing the guard, check ``_pending_messages`` and respawn any
  orphan-blocked message so it doesn't sit in the queue forever.
"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import (
    BasePlatformAdapter,
    MessageEvent,
    MessageType,
)


class _StubAdapter(BasePlatformAdapter):
    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def send(self, chat_id, text, **kwargs):
        pass

    async def get_chat_info(self, chat_id):
        return {}


def _make_adapter():
    config = PlatformConfig(enabled=True, token="test-token")
    return _StubAdapter(config, Platform.FEISHU)


def _make_event(session_key: str) -> MessageEvent:
    """Build a minimal MessageEvent for queue/respawn tests."""
    return MessageEvent(
        text="hello",
        message_type=MessageType.TEXT,
        message_id="m_1",
    )


# ---------------------------------------------------------------------------
# Timeout path: orphaned state must be cleaned up
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_timeout_clears_active_session_and_expected_cancelled():
    """#34253: When the cancelled task doesn't exit within 5s, the
    ``TimeoutError`` handler must remove the orphan from both
    ``_expected_cancelled_tasks`` and ``_active_sessions`` so the next
    inbound message for that session can install a fresh guard."""
    adapter = _make_adapter()
    session_key = "feishu:oc_test_session"

    # Build a task that will refuse to exit within 5s. Implementation:
    # an asyncio task that sleeps for 30s and catches CancelledError to
    # delay its own teardown, but our test patches asyncio.wait_for to
    # raise TimeoutError immediately so we don't actually wait 5s.
    async def _stubborn():
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            # Simulate a stubborn cleanup path that delays exit.
            await asyncio.sleep(0.1)
            raise

    task = asyncio.create_task(_stubborn())
    adapter._session_tasks[session_key] = task
    adapter._active_sessions[session_key] = "current-message-id"

    # Patch wait_for to raise TimeoutError synthetically. Patch the
    # module-local ``asyncio.wait_for`` (gateway.platforms.base imports
    # asyncio at module top, so we monkey-patch through that reference).
    from gateway.platforms import base as base_mod

    async def _wait_for_raises_timeout(coro, timeout):
        # Close the shield coroutine we were handed so we don't leak it.
        # The coro here is asyncio.shield(task); closing the shield
        # doesn't cancel the underlying task — that's the whole point of
        # the production code path.
        try:
            coro.close()
        except Exception:
            pass
        raise asyncio.TimeoutError()

    with patch.object(base_mod.asyncio, "wait_for", side_effect=_wait_for_raises_timeout):
        await adapter.cancel_session_processing(session_key, release_guard=True, discard_pending=True)

    # The bug fix invariants:
    assert session_key not in adapter._active_sessions, (
        "active_sessions must be cleared on cancel-timeout (#34253)"
    )
    assert task not in adapter._expected_cancelled_tasks, (
        "expected_cancelled_tasks must be cleared on cancel-timeout (#34253)"
    )

    # Cleanup: cancel the stubborn task so the test doesn't leak.
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# Respawn path: pending messages must not be orphaned
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pending_message_respawned_after_orphan_release():
    """#34253: When the guard is released after a timeout-cancellation,
    any message that arrived while we were waiting for the orphan must
    be respawned — otherwise it sits in ``_pending_messages`` forever."""
    adapter = _make_adapter()
    session_key = "feishu:oc_test_session"

    # No active task — the guard release path runs directly. Simulate
    # the orphan having already exited.
    pending_event = _make_event(session_key)
    adapter._pending_messages[session_key] = pending_event

    # Patch _start_session_processing so we can verify it was called.
    spawn_calls = []

    def _record_spawn(event, key):
        spawn_calls.append((event, key))

    with patch.object(adapter, "_start_session_processing", side_effect=_record_spawn):
        with patch.object(adapter, "_release_session_guard"):
            await adapter.cancel_session_processing(
                session_key,
                release_guard=True,
                discard_pending=False,  # critical: don't discard, let respawn pick it up
            )

    assert len(spawn_calls) == 1, "Pending message must be respawned (#34253)"
    respawned_event, respawned_key = spawn_calls[0]
    assert respawned_event is pending_event
    assert respawned_key == session_key
    # The pending message must have been consumed by the respawn.
    assert session_key not in adapter._pending_messages


@pytest.mark.asyncio
async def test_no_respawn_when_discard_pending_is_true():
    """When ``discard_pending=True`` (e.g. /reset semantics), the
    pending-message respawn path must NOT fire — the operator explicitly
    asked us to drop the queue."""
    adapter = _make_adapter()
    session_key = "feishu:oc_test_session"
    pending_event = _make_event(session_key)
    adapter._pending_messages[session_key] = pending_event

    spawn_calls = []

    def _record_spawn(event, key):
        spawn_calls.append((event, key))

    with patch.object(adapter, "_start_session_processing", side_effect=_record_spawn):
        with patch.object(adapter, "_release_session_guard"):
            await adapter.cancel_session_processing(
                session_key,
                release_guard=True,
                discard_pending=True,
            )

    # discard_pending=True pops the pending message before the respawn
    # check runs, so no respawn should happen.
    assert spawn_calls == []
    assert session_key not in adapter._pending_messages


@pytest.mark.asyncio
async def test_no_respawn_when_session_is_still_active():
    """If another message somehow re-installed _active_sessions before the
    guard release (shouldn't happen, but the check is defensive), the
    respawn must not fire — the new task will handle the pending message."""
    adapter = _make_adapter()
    session_key = "feishu:oc_test_session"
    pending_event = _make_event(session_key)
    adapter._pending_messages[session_key] = pending_event
    adapter._active_sessions[session_key] = "some-other-message-id"

    spawn_calls = []

    def _record_spawn(event, key):
        spawn_calls.append((event, key))

    with patch.object(adapter, "_start_session_processing", side_effect=_record_spawn):
        with patch.object(adapter, "_release_session_guard"):
            await adapter.cancel_session_processing(
                session_key,
                release_guard=True,
                discard_pending=False,
            )

    # session is still in _active_sessions → no respawn
    assert spawn_calls == []
    # And the pending message stays queued for the active task to pick up.
    assert adapter._pending_messages.get(session_key) is pending_event
