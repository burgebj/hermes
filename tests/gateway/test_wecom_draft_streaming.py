"""Tests for WeCom native draft streaming (REQUIRES_EDIT_FINALIZE framework)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import PlatformConfig
from gateway.platforms.base import SendResult


def _make_adapter():
    """Create a WeComAdapter with minimal config (no real credentials needed)."""
    from gateway.platforms.wecom import WeComAdapter

    return WeComAdapter(PlatformConfig(enabled=True))


# ---------------------------------------------------------------------------
# Class-level attribute tests
# ---------------------------------------------------------------------------


class TestWeComDraftStreamingClassAttrs:
    def test_requires_edit_finalize_is_true(self):
        from gateway.platforms.wecom import WeComAdapter

        assert WeComAdapter.REQUIRES_EDIT_FINALIZE is True

    def test_stream_message_max_bytes_is_20_kib(self):
        from gateway.platforms.wecom import WeComAdapter

        assert WeComAdapter.STREAM_MESSAGE_MAX_BYTES == 20 * 1024


# ---------------------------------------------------------------------------
# supports_draft_streaming
# ---------------------------------------------------------------------------


class TestSupportsDraftStreaming:
    def test_returns_false_when_ws_is_none(self):
        adapter = _make_adapter()
        assert adapter._ws is None
        assert adapter.supports_draft_streaming() is False

    def test_returns_false_when_ws_is_closed(self):
        adapter = _make_adapter()
        ws = MagicMock()
        ws.closed = True
        adapter._ws = ws
        assert adapter.supports_draft_streaming() is False

    def test_returns_true_when_ws_is_open(self):
        adapter = _make_adapter()
        ws = MagicMock()
        ws.closed = False
        adapter._ws = ws
        assert adapter.supports_draft_streaming() is True

    def test_returns_true_with_chat_type_when_connected(self):
        adapter = _make_adapter()
        ws = MagicMock()
        ws.closed = False
        adapter._ws = ws
        assert adapter.supports_draft_streaming(chat_type="group") is True

    def test_returns_true_with_metadata_when_connected(self):
        adapter = _make_adapter()
        ws = MagicMock()
        ws.closed = False
        adapter._ws = ws
        assert adapter.supports_draft_streaming(metadata={"x": 1}) is True


# ---------------------------------------------------------------------------
# _truncate_utf8
# ---------------------------------------------------------------------------


class TestTruncateUtf8:
    def test_short_text_returned_unchanged(self):
        from gateway.platforms.wecom import WeComAdapter

        text = "hello"
        assert WeComAdapter._truncate_utf8(text, 100) == text

    def test_ascii_exactly_at_limit_not_truncated(self):
        from gateway.platforms.wecom import WeComAdapter

        text = "a" * 10
        assert WeComAdapter._truncate_utf8(text, 10) == text

    def test_truncates_chinese_multibyte_chars_cleanly(self):
        from gateway.platforms.wecom import WeComAdapter

        # Each Chinese char is 3 UTF-8 bytes.
        text = "你好世界"  # 4 chars = 12 bytes
        result = WeComAdapter._truncate_utf8(text, 9)
        # 9 bytes = 3 complete Chinese chars → "你好世"
        assert result == "你好世"
        assert len(result.encode("utf-8")) <= 9

    def test_truncates_mixed_ascii_and_chinese(self):
        from gateway.platforms.wecom import WeComAdapter

        text = "ab你好"  # 2 + 6 = 8 bytes
        result = WeComAdapter._truncate_utf8(text, 5)
        # 5 bytes: "ab" (2) + "你" starts at byte 2 → 3 bytes for 你 → total 5 → "ab你"
        assert result == "ab你"
        assert len(result.encode("utf-8")) <= 5

    def test_empty_string_returned_as_empty(self):
        from gateway.platforms.wecom import WeComAdapter

        assert WeComAdapter._truncate_utf8("", 10) == ""

    def test_none_treated_as_empty(self):
        from gateway.platforms.wecom import WeComAdapter

        assert WeComAdapter._truncate_utf8(None, 10) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _resolve_stream_req_id
# ---------------------------------------------------------------------------


class TestResolveStreamReqId:
    def test_returns_req_id_when_cached(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-abc"
        assert adapter._resolve_stream_req_id("chat-1") == "req-abc"

    def test_returns_none_when_not_cached(self):
        adapter = _make_adapter()
        assert adapter._resolve_stream_req_id("unknown-chat") is None

    def test_strips_whitespace_from_chat_id(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-xyz"
        assert adapter._resolve_stream_req_id("  chat-1  ") == "req-xyz"

    def test_returns_none_for_empty_chat_id(self):
        adapter = _make_adapter()
        assert adapter._resolve_stream_req_id("") is None

    def test_returns_none_for_none_chat_id(self):
        adapter = _make_adapter()
        assert adapter._resolve_stream_req_id(None) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# send_draft — no req_id case
# ---------------------------------------------------------------------------


class TestSendDraftNoReqId:
    @pytest.mark.asyncio
    async def test_returns_failure_when_no_req_id(self):
        adapter = _make_adapter()
        # No req_id cached → should fail immediately.
        result = await adapter.send_draft("chat-1", draft_id=1, content="hi")
        assert result.success is False
        assert result.error == "no reply context available"

    @pytest.mark.asyncio
    async def test_does_not_call_send_json_when_no_req_id(self):
        adapter = _make_adapter()
        adapter._send_json = AsyncMock()
        await adapter.send_draft("chat-1", draft_id=1, content="hi")
        adapter._send_json.assert_not_awaited()


# ---------------------------------------------------------------------------
# send_draft — intermediate frame (finish=False)
# ---------------------------------------------------------------------------


class TestSendDraftIntermediateFrame:
    @pytest.mark.asyncio
    async def test_intermediate_frame_calls_send_json(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        adapter._send_json = AsyncMock()
        adapter._send_reply_request = AsyncMock()

        result = await adapter.send_draft("chat-1", draft_id=1, content="partial", finish=False)

        assert result.success is True
        adapter._send_json.assert_awaited_once()
        adapter._send_reply_request.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_intermediate_frame_payload_structure(self):
        from gateway.platforms.wecom import APP_CMD_RESPONSE

        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        captured = []

        async def capture(payload):
            captured.append(payload)

        adapter._send_json = capture

        await adapter.send_draft("chat-1", draft_id=42, content="hello", finish=False)

        assert len(captured) == 1
        payload = captured[0]
        assert payload["cmd"] == APP_CMD_RESPONSE
        assert payload["headers"]["req_id"] == "req-1"
        body = payload["body"]
        assert body["msgtype"] == "stream"
        assert body["stream"]["finish"] is False
        assert body["stream"]["content"] == "hello"

    @pytest.mark.asyncio
    async def test_intermediate_frame_does_not_clear_session(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        adapter._send_json = AsyncMock()

        await adapter.send_draft("chat-1", draft_id=1, content="partial", finish=False)

        # Session key must still be present after intermediate frame.
        assert ("chat-1", 1) in adapter._stream_sessions


# ---------------------------------------------------------------------------
# send_draft — finish frame (finish=True)
# ---------------------------------------------------------------------------


class TestSendDraftFinishFrame:
    @pytest.mark.asyncio
    async def test_finish_frame_calls_send_reply_request(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        adapter._send_json = AsyncMock()
        adapter._send_reply_request = AsyncMock(
            return_value={"errcode": 0, "errmsg": "ok"}
        )
        adapter._raise_for_wecom_error = MagicMock()

        result = await adapter.send_draft("chat-1", draft_id=1, content="full", finish=True)

        assert result.success is True
        adapter._send_reply_request.assert_awaited_once()
        adapter._send_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_finish_frame_clears_session_key_on_success(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        adapter._send_reply_request = AsyncMock(
            return_value={"errcode": 0, "errmsg": "ok"}
        )
        adapter._raise_for_wecom_error = MagicMock()

        await adapter.send_draft("chat-1", draft_id=1, content="full", finish=True)

        assert ("chat-1", 1) not in adapter._stream_sessions

    @pytest.mark.asyncio
    async def test_finish_frame_clears_session_key_on_error(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        adapter._send_reply_request = AsyncMock(
            side_effect=RuntimeError("some network error 99999")
        )

        result = await adapter.send_draft("chat-1", draft_id=7, content="full", finish=True)

        assert result.success is False
        # session key must be cleaned up even on failure (via finally)
        assert ("chat-1", 7) not in adapter._stream_sessions


# ---------------------------------------------------------------------------
# send_draft — 846609 fallback
# ---------------------------------------------------------------------------


class TestSendDraft846609Fallback:
    @pytest.mark.asyncio
    async def test_846609_falls_back_to_send(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        adapter._send_reply_request = AsyncMock(
            side_effect=RuntimeError("send stream finish frame failed: WeCom errcode 846609: req_id expired")
        )
        adapter.send = AsyncMock(return_value=SendResult(success=True))

        result = await adapter.send_draft("chat-1", draft_id=1, content="full answer", finish=True)

        adapter.send.assert_awaited_once_with(
            chat_id="chat-1",
            content="full answer",
            metadata=None,
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_non_846609_error_returns_failure(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        adapter._send_reply_request = AsyncMock(
            side_effect=RuntimeError("network timeout")
        )
        adapter.send = AsyncMock(return_value=SendResult(success=True))

        result = await adapter.send_draft("chat-1", draft_id=1, content="full answer", finish=True)

        adapter.send.assert_not_awaited()
        assert result.success is False
        assert "network timeout" in (result.error or "")


# ---------------------------------------------------------------------------
# send_draft — concurrent draft_ids get distinct stream_ids
# ---------------------------------------------------------------------------


class TestSendDraftConcurrentDraftIds:
    @pytest.mark.asyncio
    async def test_two_draft_ids_produce_different_stream_ids(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        adapter._send_json = AsyncMock()

        # First draft
        await adapter.send_draft("chat-1", draft_id=10, content="a", finish=False)
        # Second draft
        await adapter.send_draft("chat-1", draft_id=11, content="b", finish=False)

        stream_id_10 = adapter._stream_sessions[("chat-1", 10)]
        stream_id_11 = adapter._stream_sessions[("chat-1", 11)]
        assert stream_id_10 != stream_id_11

    @pytest.mark.asyncio
    async def test_same_draft_id_reuses_stream_id_across_frames(self):
        adapter = _make_adapter()
        adapter._last_chat_req_ids["chat-1"] = "req-1"
        adapter._send_json = AsyncMock()

        await adapter.send_draft("chat-1", draft_id=5, content="part 1", finish=False)
        first_stream_id = adapter._stream_sessions[("chat-1", 5)]

        await adapter.send_draft("chat-1", draft_id=5, content="part 1 part 2", finish=False)
        second_stream_id = adapter._stream_sessions[("chat-1", 5)]

        assert first_stream_id == second_stream_id


