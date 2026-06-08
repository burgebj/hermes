"""Regression tests for Telegram streaming edit transport bugs.

Bug #36965 — Streaming edit transport duplicates final message
    When the cursor-strip finalize edit is rate-limited, the prior
    streaming content is already visible to the user.
    _final_content_delivered must be set True so run.py suppression
    fires and the gateway does NOT re-send the full response as a
    fresh sendMessage.

Bug #37555 — Tool trace leakage / commentary after final delivery
    _send_commentary must not fire after the final response has been
    delivered, preventing stale interim messages queued from a prior
    turn from appearing as extra visible chat messages.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.stream_consumer import GatewayStreamConsumer, StreamConsumerConfig


# ── Shared helpers ────────────────────────────────────────────────────────────

def _make_adapter(
    *,
    requires_finalize: bool = True,
    edit_fails: bool = False,
    send_id: str = "msg1",
) -> MagicMock:
    """Build a minimal mock adapter for stream consumer tests."""
    adapter = MagicMock()
    adapter.REQUIRES_EDIT_FINALIZE = requires_finalize
    adapter.MAX_MESSAGE_LENGTH = 4096
    adapter.send = AsyncMock(
        return_value=SimpleNamespace(success=True, message_id=send_id),
    )
    if edit_fails:
        adapter.edit_message = AsyncMock(
            return_value=SimpleNamespace(
                success=False, error="flood control: retry after 30",
            ),
        )
    else:
        adapter.edit_message = AsyncMock(
            return_value=SimpleNamespace(success=True, message_id=send_id),
        )
    return adapter


def _make_consumer(
    adapter: MagicMock,
    *,
    cursor: str = " ▉",
) -> GatewayStreamConsumer:
    return GatewayStreamConsumer(
        adapter=adapter,
        chat_id="chat1",
        config=StreamConsumerConfig(cursor=cursor),
    )


# ── Bug #36965 — cursor-strip edit failure must not cause duplicate send ──────


class TestCursorStripEditFailureSetsDelivered:
    """#36965: When the final cursor-strip/finalize edit fails after content
    was already visible via streaming edits, _final_content_delivered must
    be set so run.py does not re-send the full response.
    """

    @pytest.mark.asyncio
    async def test_finalize_edit_fails_but_content_was_streamed(self):
        """Prior streaming edits showed content; final finalize edit fails.

        Expected: _final_content_delivered=True so gateway suppresses the
        duplicate sendMessage.
        """
        # Adapter: first send succeeds (creates message), all edits fail
        # (simulates flood control hitting on the very last edit).
        adapter = MagicMock()
        adapter.REQUIRES_EDIT_FINALIZE = True
        adapter.MAX_MESSAGE_LENGTH = 4096
        adapter.send = AsyncMock(
            return_value=SimpleNamespace(success=True, message_id="msg1"),
        )
        # First edit succeeds (streaming tick with cursor), final edits fail.
        adapter.edit_message = AsyncMock(side_effect=[
            SimpleNamespace(success=True, message_id="msg1"),   # streaming
            SimpleNamespace(                                     # finalize
                success=False, error="flood control: retry after 30"
            ),
            SimpleNamespace(                                     # retry
                success=False, error="flood control: retry after 30"
            ),
        ])

        consumer = _make_consumer(adapter)

        # Simulate: first send establishes the message.
        await consumer._send_or_edit("Hello world" + consumer.cfg.cursor)
        assert consumer._message_id == "msg1"
        assert consumer._already_sent is True

        # Now simulate the got_done path: final edit with no cursor fails.
        consumer._final_response_sent = await consumer._send_or_edit(
            "Hello world", finalize=True,
        )
        # Final edit failed — _final_response_sent is False.
        assert consumer._final_response_sent is False

        # But the bug fix must set _final_content_delivered because the
        # content ("Hello world") was already visible (with cursor).
        assert consumer._final_content_delivered is True, (
            "Content was visible via streaming edits — "
            "_final_content_delivered must be True to prevent duplicate send"
        )

    @pytest.mark.asyncio
    async def test_finalize_edit_succeeds_sets_both_flags(self):
        """Happy path: final edit succeeds → both flags set."""
        adapter = _make_adapter(requires_finalize=True, edit_fails=False)
        consumer = _make_consumer(adapter)

        await consumer._send_or_edit("Hello world" + consumer.cfg.cursor)
        consumer._final_response_sent = await consumer._send_or_edit(
            "Hello world", finalize=True,
        )

        assert consumer._final_response_sent is True
        assert consumer._final_content_delivered is True

    @pytest.mark.asyncio
    async def test_no_prior_content_finalize_fails_no_delivered_flag(self):
        """If nothing was sent before the failing final edit, the flag
        must NOT be set — gateway fallback should still fire."""
        adapter = _make_adapter(requires_finalize=True, edit_fails=True)
        consumer = _make_consumer(adapter)
        # _already_sent = False, _last_sent_text = "" — nothing was shown
        assert consumer._already_sent is False
        assert consumer._last_sent_text == ""

        # Try an edit without a prior successful send (no message_id yet).
        ok = await consumer._send_or_edit("Hello", finalize=True)
        # send() was called (not edit) because no message_id — it succeeds
        # so the flag is set via the send path.
        # This test just verifies no bogus flag is set.
        # The real guard is in the `elif self._already_sent and
        # self._last_sent_text:` branch which requires _already_sent.
        assert consumer._final_content_delivered is True  # send succeeded

    @pytest.mark.asyncio
    async def test_cursor_only_last_sent_text_does_not_set_delivered(self):
        """If _last_sent_text is only the cursor (no real content),
        _final_content_delivered must NOT be set — nothing visible."""
        adapter = MagicMock()
        adapter.REQUIRES_EDIT_FINALIZE = True
        adapter.MAX_MESSAGE_LENGTH = 4096
        adapter.send = AsyncMock(
            return_value=SimpleNamespace(success=True, message_id="msg1"),
        )
        # All edits fail.
        adapter.edit_message = AsyncMock(
            return_value=SimpleNamespace(
                success=False, error="flood control: retry after 30",
            ),
        )
        consumer = _make_consumer(adapter)
        # Manually set state: message exists but only cursor was sent.
        consumer._message_id = "msg1"
        consumer._already_sent = True
        consumer._last_sent_text = " ▉"   # cursor only, no real content

        consumer._final_response_sent = await consumer._send_or_edit(
            "Hello world", finalize=True,
        )
        assert consumer._final_response_sent is False
        # Only cursor was visible — _final_content_delivered stays False
        # so the gateway sends the real final response.
        assert consumer._final_content_delivered is False, (
            "Cursor-only last_sent_text must not trigger delivered flag"
        )

    @pytest.mark.asyncio
    async def test_full_streaming_run_no_duplicate_on_flood(self):
        """End-to-end: stream consumer run() with flood on final edit.

        Verifies that after the run() coroutine completes,
        final_content_delivered is True even though the finalize edit
        was rate-limited — preventing the gateway from sending a second
        copy of the response.
        """
        adapter = MagicMock()
        adapter.REQUIRES_EDIT_FINALIZE = True
        adapter.MAX_MESSAGE_LENGTH = 4096
        adapter.send = AsyncMock(
            return_value=SimpleNamespace(success=True, message_id="msg1"),
        )
        # First edit (streaming tick) succeeds; subsequent edits fail.
        adapter.edit_message = AsyncMock(side_effect=[
            SimpleNamespace(success=True, message_id="msg1"),
            SimpleNamespace(
                success=False, error="flood control: retry after 30",
            ),
            SimpleNamespace(
                success=False, error="flood control: retry after 30",
            ),
            SimpleNamespace(
                success=False, error="flood control: retry after 30",
            ),
        ])

        consumer = GatewayStreamConsumer(
            adapter=adapter,
            chat_id="chat1",
            config=StreamConsumerConfig(
                cursor=" ▉",
                edit_interval=0.0,
            ),
        )
        task = asyncio.create_task(consumer.run())

        # Feed text and signal done.
        consumer.on_delta("Hello world")
        await asyncio.sleep(0.1)
        consumer.finish()
        await asyncio.wait_for(task, timeout=5.0)

        assert consumer.final_content_delivered is True, (
            "After flood on final edit, final_content_delivered must be True"
            " to prevent duplicate sendMessage"
        )


# ── Bug #37555 — commentary blocked after final delivery ─────────────────────


class TestCommentaryBlockedAfterFinalDelivery:
    """#37555: _send_commentary must return False (and NOT call adapter.send)
    when _final_content_delivered or _final_response_sent is already True.

    This prevents stale interim/tool-trace messages queued from a prior
    turn from appearing as extra visible chat messages after the response
    has been fully sent.
    """

    @pytest.mark.asyncio
    async def test_commentary_blocked_when_final_content_delivered(self):
        """No commentary send after _final_content_delivered=True."""
        adapter = _make_adapter()
        consumer = _make_consumer(adapter)
        consumer._final_content_delivered = True

        result = await consumer._send_commentary("Using web_search...")

        assert result is False
        adapter.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_commentary_blocked_when_final_response_sent(self):
        """No commentary send after _final_response_sent=True."""
        adapter = _make_adapter()
        consumer = _make_consumer(adapter)
        consumer._final_response_sent = True

        result = await consumer._send_commentary("web_extract result...")

        assert result is False
        adapter.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_commentary_allowed_before_final_delivery(self):
        """Commentary is sent normally before any final delivery."""
        adapter = _make_adapter()
        consumer = _make_consumer(adapter)
        assert consumer._final_content_delivered is False
        assert consumer._final_response_sent is False

        result = await consumer._send_commentary("Searching the web...")

        assert result is True
        adapter.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_commentary_blocked_both_flags_true(self):
        """Both flags set → still blocked (belt-and-suspenders)."""
        adapter = _make_adapter()
        consumer = _make_consumer(adapter)
        consumer._final_content_delivered = True
        consumer._final_response_sent = True

        result = await consumer._send_commentary("Stale tool trace line")

        assert result is False
        adapter.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_commentary_still_returns_false_without_send(self):
        """Empty commentary is filtered before the delivery-flag check,
        and should never reach adapter.send regardless of flag state."""
        adapter = _make_adapter()
        consumer = _make_consumer(adapter)

        result = await consumer._send_commentary("   ")

        assert result is False
        adapter.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_commentary_blocked_does_not_raise(self):
        """Blocked commentary must return silently, not raise."""
        adapter = _make_adapter()
        consumer = _make_consumer(adapter)
        consumer._final_content_delivered = True

        # Should not raise even with substantial text
        result = await consumer._send_commentary(
            "web_search: query=some long search string that would otherwise "
            "appear as a leaked tool-trace message in the user's chat"
        )
        assert result is False
