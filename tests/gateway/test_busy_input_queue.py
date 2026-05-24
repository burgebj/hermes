"""Tests for busy_input_mode: queue FIFO behavior.

When busy_input_mode is "queue", rapid follow-up messages must be
preserved in FIFO order and NOT silently overwritten in a single slot.

The gateway uses _enqueue_fifo (slot + overflow list) to maintain a proper
FIFO: messages go into the pending slot if free, otherwise into the
overflow list.  After each run drains, _promote_queued_event moves the
next overflow item into the slot.

Bug: before fix, the busy path called merge_pending_message_event which
replaces the slot, causing messages 2-5 to overwrite each other, so only
message 5 was processed.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.base import MessageEvent, MessageType
from gateway.session import SessionEntry, SessionSource


def _make_source(platform: Platform = Platform.TELEGRAM) -> SessionSource:
    return SessionSource(
        platform=platform,
        user_id="u1",
        chat_id="c1",
        user_name="tester",
        chat_type="dm",
    )


def _make_event(text: str, msg_id: str = "m1") -> MessageEvent:
    return MessageEvent(
        text=text,
        source=_make_source(),
        message_id=msg_id,
        message_type=MessageType.TEXT,
    )


def _make_runner():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig(
        platforms={Platform.TELEGRAM: PlatformConfig(enabled=True, token="***")}
    )
    runner._running_agents = {}
    runner._queued_events = {}
    runner._draining = False
    runner._busy_input_mode = "queue"
    runner._busy_ack_ts = {}
    return runner


def test_fifo_queue_preserves_multiple_rapid_messages():
    """Rapid follow-ups while agent is busy must all be queued, not overwritten."""
    from gateway.run import GatewayRunner

    runner = _make_runner()

    adapter = MagicMock()
    adapter._pending_messages = {}  # empty = slot is free initially
    runner.adapters = {Platform.TELEGRAM: adapter}

    session_key = "telegram:u1:c1"

    # First message arrives — slot is free
    runner._enqueue_fifo(session_key, _make_event("msg1", "m1"), adapter)
    assert session_key in adapter._pending_messages
    assert adapter._pending_messages[session_key].text == "msg1"
    assert runner._queued_events == {}  # no overflow yet

    # Second message arrives while agent is still processing m1
    runner._enqueue_fifo(session_key, _make_event("msg2", "m2"), adapter)
    # Slot occupied → goes to overflow
    assert session_key in adapter._pending_messages
    assert adapter._pending_messages[session_key].text == "msg1"  # slot unchanged
    assert session_key in runner._queued_events
    assert len(runner._queued_events[session_key]) == 1
    assert runner._queued_events[session_key][0].text == "msg2"

    # Third and fourth messages
    runner._enqueue_fifo(session_key, _make_event("msg3", "m3"), adapter)
    runner._enqueue_fifo(session_key, _make_event("msg4", "m4"), adapter)
    assert len(runner._queued_events[session_key]) == 3
    assert [e.text for e in runner._queued_events[session_key]] == [
        "msg2", "msg3", "msg4"
    ]


def test_busy_message_uses_fifo_not_merge():
    """_handle_active_session_busy_message with queue mode must use FIFO, not replace."""
    from gateway.run import GatewayRunner

    runner = _make_runner()

    adapter = MagicMock()
    adapter._pending_messages = {}  # empty = agent not busy (slot free)
    runner.adapters = {Platform.TELEGRAM: adapter}
    runner._running_agents = {}  # no running agent

    session_key = "telegram:u1:c1"

    # Agent is "busy" — simulate by having a running agent
    running_agent = MagicMock()
    running_agent.is_running = True
    runner._running_agents[session_key] = running_agent

    # Mock _is_user_authorized to return True
    with patch.object(runner, "_is_user_authorized", return_value=True):
        import asyncio

        async def run_test():
            evt = _make_event("first message", "m1")
            handled = await runner._handle_active_session_busy_message(evt, session_key)
            assert handled is True

            # Slot should have first message
            assert session_key in adapter._pending_messages
            first_text = adapter._pending_messages[session_key].text

            # Second message
            evt2 = _make_event("second message", "m2")
            await runner._handle_active_session_busy_message(evt2, session_key)

            # Should use FIFO, not replace
            if session_key in runner._queued_events:
                assert runner._queued_events[session_key][0].text == "second message"
            else:
                # If slot is still first message, that's the BUG
                assert adapter._pending_messages[session_key].text == first_text, (
                    "Second message must NOT overwrite first — FIFO required"
                )

        asyncio.get_event_loop().run_until_complete(run_test())


def test_promote_overflow_after_drain():
    """After a turn drains, _promote_queued_event moves overflow into slot."""
    from gateway.run import GatewayRunner

    runner = _make_runner()

    adapter = MagicMock()
    adapter._pending_messages = {}  # slot is free
    runner.adapters = {Platform.TELEGRAM: adapter}
    runner._queued_events = {}  # will be set by _enqueue_fifo

    session_key = "telegram:u1:c1"

    # Enqueue 3 messages
    runner._enqueue_fifo(session_key, _make_event("msg1", "m1"), adapter)
    runner._enqueue_fifo(session_key, _make_event("msg2", "m2"), adapter)
    runner._enqueue_fifo(session_key, _make_event("msg3", "m3"), adapter)

    # Now simulate drain: pending slot gets consumed (set to None temporarily)
    # The current pending is m1
    pending_slot = adapter._pending_messages.get(session_key)
    assert pending_slot.text == "msg1"

    # After drain, slot is empty (consumed by _dequeue_pending_event).
    # Call _promote_queued_event with pending_event=None to promote m2.
    result = runner._promote_queued_event(session_key, adapter, None)

    # m2 should now be returned as the next pending event
    assert result.text == "msg2"
    # m3 should still be in overflow (msg1 was already consumed in prior drain)
    assert len(runner._queued_events.get(session_key, [])) == 1
    assert runner._queued_events[session_key][0].text == "msg3"


def test_merge_pending_still_works_for_photo_burst():
    """Photo burst merging via merge_pending_message_event is unaffected."""
    from gateway.platforms.base import merge_pending_message_event

    pending = {}
    session_key = "test"

    # First photo
    evt1 = MessageEvent(
        text="photo1",
        source=_make_source(),
        message_id="p1",
        message_type=MessageType.PHOTO,
        media_urls=["http://img1.jpg"],
    )
    merge_pending_message_event(pending, session_key, evt1)

    # Second photo burst
    evt2 = MessageEvent(
        text="photo2 caption",
        source=_make_source(),
        message_id="p2",
        message_type=MessageType.PHOTO,
        media_urls=["http://img2.jpg"],
    )
    merge_pending_message_event(pending, session_key, evt2)

    # Should be merged into one event
    assert len(pending[session_key].media_urls) == 2
    assert "photo1" in pending[session_key].text
    assert "photo2 caption" in pending[session_key].text
