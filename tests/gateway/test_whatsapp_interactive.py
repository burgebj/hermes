"""Tests for WhatsApp interactive messages (buttons and list menus).

Covers the send_clarify override in WhatsAppAdapter:
- Multi-choice prompts → interactive buttons (≤3) or list messages (>3)
- Open-ended prompts → delegates to base class (unchanged)
- Graceful fallback when bridge doesn't support interactive messages
- Button label truncation at 20 chars (WhatsApp hard limit)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import Platform
from gateway.platforms.base import SendResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_adapter():
    """Create a WhatsAppAdapter with test attributes (bypass __init__)."""
    from gateway.platforms.whatsapp import WhatsAppAdapter

    adapter = WhatsAppAdapter.__new__(WhatsAppAdapter)
    adapter.platform = Platform.WHATSAPP
    adapter.config = MagicMock()
    adapter.config.extra = {}
    adapter._bridge_port = 3000
    adapter._bridge_script = "/tmp/test-bridge.js"
    adapter._session_path = MagicMock()
    adapter._bridge_log_fh = None
    adapter._bridge_log = None
    adapter._bridge_process = None
    adapter._reply_prefix = None
    adapter._running = True
    adapter._message_handler = None
    adapter._fatal_error_code = None
    adapter._fatal_error_message = None
    adapter._fatal_error_retryable = True
    adapter._fatal_error_handler = None
    adapter._active_sessions = {}
    adapter._pending_messages = {}
    adapter._background_tasks = set()
    adapter._auto_tts_disabled_chats = set()
    adapter._message_queue = asyncio.Queue()
    adapter._http_session = MagicMock()
    adapter._mention_patterns = []
    adapter._dm_policy = "open"
    adapter._allow_from = set()
    adapter._group_policy = "open"
    adapter._group_allow_from = set()
    adapter._shutting_down = False
    adapter._text_batch_delay_seconds = 5.0
    adapter._text_batch_split_delay_seconds = 10.0
    adapter._pending_text_batches = {}
    adapter._pending_text_batch_tasks = {}
    return adapter


class _AsyncCM:
    """Minimal async context manager returning a fixed value."""

    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *args):
        pass


def _mock_response(status, json_data=None):
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data or {})
    resp.text = AsyncMock(return_value="")
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_ended_delegates_to_base():
    """No choices → delegates to base class, no interactive HTTP call."""
    adapter = _make_adapter()
    with patch.object(
        type(adapter).__bases__[0], "send_clarify", new_callable=AsyncMock
    ) as mock_base:
        mock_base.return_value = SendResult(success=True)
        result = await adapter.send_clarify(
            "123@s.whatsapp.net", "What is your name?", None, "c1", "s1"
        )
        assert result.success
        mock_base.assert_called_once()
        adapter._http_session.post.assert_not_called()


@pytest.mark.asyncio
async def test_two_choices_sends_buttons():
    """2 choices + Other = 3 buttons total (at the WhatsApp limit)."""
    adapter = _make_adapter()
    resp = _mock_response(200, {"messageId": "msg123"})
    adapter._http_session.post.return_value = _AsyncCM(resp)

    result = await adapter.send_clarify(
        "123@s.whatsapp.net", "Pick one", ["Yes", "No"], "c1", "s1"
    )
    assert result.success

    call_args = adapter._http_session.post.call_args
    assert call_args[0][0] == "http://127.0.0.1:3000/send-interactive"
    payload = call_args[1]["json"]
    assert payload["chatId"] == "123@s.whatsapp.net"
    msg = payload["interactive"]["buttonsMessage"]
    assert msg["contentText"] == "Pick one"
    assert msg["headerType"] == 1  # EMPTY
    assert len(msg["buttons"]) == 3  # Yes, No, Other
    assert msg["buttons"][0]["buttonText"]["displayText"] == "Yes"
    assert msg["buttons"][0]["buttonId"] == "c1:0"
    assert msg["buttons"][0]["type"] == 1  # RESPONSE
    assert msg["buttons"][2]["buttonText"]["displayText"] == "\u270f\ufe0f Other"
    assert msg["buttons"][2]["buttonId"] == "c1:other"


@pytest.mark.asyncio
async def test_three_choices_at_limit():
    """3 choices + Other = 4 buttons → exceeds 3 limit → sends listMessage."""
    adapter = _make_adapter()
    resp = _mock_response(200, {"messageId": "msg456"})
    adapter._http_session.post.return_value = _AsyncCM(resp)

    choices = ["A", "B", "C"]
    result = await adapter.send_clarify(
        "123@s.whatsapp.net", "Pick one", choices, "c2", "s2"
    )
    assert result.success

    payload = adapter._http_session.post.call_args[1]["json"]
    # 3 choices + Other = 4 > 3 → listMessage
    assert "listMessage" in payload["interactive"]
    rows = payload["interactive"]["listMessage"]["sections"][0]["rows"]
    assert len(rows) == 4  # A, B, C, Other


@pytest.mark.asyncio
async def test_five_choices_sends_list():
    """5 choices + Other = 6 → listMessage."""
    adapter = _make_adapter()
    resp = _mock_response(200, {"messageId": "msg789"})
    adapter._http_session.post.return_value = _AsyncCM(resp)

    choices = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    result = await adapter.send_clarify(
        "123@s.whatsapp.net", "Pick one", choices, "c3", "s3"
    )
    assert result.success

    payload = adapter._http_session.post.call_args[1]["json"]
    assert "listMessage" in payload["interactive"]
    rows = payload["interactive"]["listMessage"]["sections"][0]["rows"]
    assert len(rows) == 6  # 5 choices + Other
    assert rows[0]["title"] == "Alpha"
    assert rows[0]["rowId"] == "c3:0"
    assert rows[5]["title"] == "\u270f\ufe0f Other"
    assert rows[5]["rowId"] == "c3:other"


@pytest.mark.asyncio
async def test_bridge_error_falls_back():
    """Bridge returns 500 → falls back to text-list behaviour."""
    adapter = _make_adapter()
    resp = _mock_response(500)
    adapter._http_session.post.return_value = _AsyncCM(resp)

    with patch.object(
        type(adapter).__bases__[0], "send_clarify", new_callable=AsyncMock
    ) as mock_base:
        mock_base.return_value = SendResult(success=True, message_id="fallback")
        result = await adapter.send_clarify(
            "123@s.whatsapp.net", "Pick one", ["X", "Y"], "c4", "s4"
        )
        assert result.success
        mock_base.assert_called_once()


@pytest.mark.asyncio
async def test_bridge_unreachable_falls_back():
    """Connection refused → falls back to text-list behaviour."""
    import aiohttp

    adapter = _make_adapter()
    adapter._http_session.post.side_effect = aiohttp.ClientError("refused")

    with patch.object(
        type(adapter).__bases__[0], "send_clarify", new_callable=AsyncMock
    ) as mock_base:
        mock_base.return_value = SendResult(success=True)
        result = await adapter.send_clarify(
            "123@s.whatsapp.net", "Pick one", ["X", "Y"], "c5", "s5"
        )
        assert result.success
        mock_base.assert_called_once()


@pytest.mark.asyncio
async def test_long_choice_truncated():
    """Choice text longer than 20 chars is truncated."""
    adapter = _make_adapter()
    resp = _mock_response(200, {"messageId": "msg999"})
    adapter._http_session.post.return_value = _AsyncCM(resp)

    await adapter.send_clarify(
        "123@s.whatsapp.net",
        "Pick one",
        ["This is a very long option text that exceeds limits"],
        "c6",
        "s6",
    )
    payload = adapter._http_session.post.call_args[1]["json"]
    label = payload["interactive"]["buttonsMessage"]["buttons"][0][
        "buttonText"
    ]["displayText"]
    assert len(label) == 20
    assert label == "This is a very long "


@pytest.mark.asyncio
async def test_other_button_always_present():
    """The 'Other' free-text button is always included."""
    adapter = _make_adapter()
    resp = _mock_response(200, {"messageId": "msg111"})
    adapter._http_session.post.return_value = _AsyncCM(resp)

    await adapter.send_clarify(
        "123@s.whatsapp.net", "Pick one", ["Only"], "c7", "s7"
    )
    payload = adapter._http_session.post.call_args[1]["json"]
    buttons = payload["interactive"]["buttonsMessage"]["buttons"]
    assert len(buttons) == 2  # Only, Other
    assert buttons[-1]["buttonId"] == "c7:other"
    assert buttons[-1]["type"] == 1  # RESPONSE


@pytest.mark.asyncio
async def test_list_message_payload_structure():
    """Verify listMessage payload has correct structure for Baileys."""
    adapter = _make_adapter()
    resp = _mock_response(200, {"messageId": "msg222"})
    adapter._http_session.post.return_value = _AsyncCM(resp)

    await adapter.send_clarify(
        "123@s.whatsapp.net", "Choose", ["A", "B", "C", "D"], "c8", "s8"
    )
    payload = adapter._http_session.post.call_args[1]["json"]
    lm = payload["interactive"]["listMessage"]
    assert lm["listType"] == 1  # SINGLE_SELECT
    assert lm["buttonText"] == "Select"
    assert lm["description"] == "Choose"
    assert len(lm["sections"]) == 1
    assert lm["sections"][0]["title"] == ""
