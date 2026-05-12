"""Tests for Telegram inline keyboard clarify buttons.

Mirrors test_telegram_approval_buttons.py — we mock the telegram package
enough to import TelegramAdapter, then exercise send_clarify and the
cq:-prefixed callback_query handler path.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure the repo root is importable
# ---------------------------------------------------------------------------
_repo = str(Path(__file__).resolve().parents[2])
if _repo not in sys.path:
    sys.path.insert(0, _repo)


# ---------------------------------------------------------------------------
# Minimal Telegram mock so TelegramAdapter can be imported
# ---------------------------------------------------------------------------
def _ensure_telegram_mock():
    if "telegram" in sys.modules and hasattr(sys.modules["telegram"], "__file__"):
        return
    mod = MagicMock()
    mod.ext.ContextTypes.DEFAULT_TYPE = type(None)
    mod.constants.ParseMode.MARKDOWN = "Markdown"
    mod.constants.ParseMode.MARKDOWN_V2 = "MarkdownV2"
    mod.constants.ParseMode.HTML = "HTML"
    mod.constants.ChatType.PRIVATE = "private"
    mod.constants.ChatType.GROUP = "group"
    mod.constants.ChatType.SUPERGROUP = "supergroup"
    mod.constants.ChatType.CHANNEL = "channel"
    mod.error.NetworkError = type("NetworkError", (OSError,), {})
    mod.error.TimedOut = type("TimedOut", (OSError,), {})
    mod.error.BadRequest = type("BadRequest", (Exception,), {})
    for name in ("telegram", "telegram.ext", "telegram.constants", "telegram.request"):
        sys.modules.setdefault(name, mod)
    sys.modules.setdefault("telegram.error", mod.error)


_ensure_telegram_mock()

from gateway.platforms.telegram import TelegramAdapter  # noqa: E402
from gateway.config import Platform, PlatformConfig  # noqa: E402


def _make_adapter(extra=None):
    config = PlatformConfig(enabled=True, token="test-token", extra=extra or {})
    adapter = TelegramAdapter(config)
    adapter._bot = AsyncMock()
    adapter._app = MagicMock()
    return adapter


# ===========================================================================
# send_clarify — inline keyboard buttons
# ===========================================================================


class TestTelegramSendClarify:
    """send_clarify should emit an InlineKeyboard with one button per choice."""

    @pytest.mark.asyncio
    async def test_sends_inline_keyboard_with_one_button_per_choice(self):
        adapter = _make_adapter()
        mock_msg = MagicMock()
        mock_msg.message_id = 77
        adapter._bot.send_message = AsyncMock(return_value=mock_msg)

        result = await adapter.send_clarify(
            chat_id="12345",
            question="Which branch?",
            choices=["main", "feat/x", "release"],
            session_key="agent:main:telegram:dm:12345:1",
        )

        assert result.success is True
        assert result.message_id == "77"

        adapter._bot.send_message.assert_called_once()
        kwargs = adapter._bot.send_message.call_args[1]
        assert kwargs["chat_id"] == 12345
        assert "Which branch?" in kwargs["text"]
        # InlineKeyboardMarkup is a mock in this test env — don't introspect
        # its shape here; test_stores_clarify_state below covers the wiring.
        assert kwargs["reply_markup"] is not None

    @pytest.mark.asyncio
    async def test_stores_clarify_state_with_session_and_choices(self):
        """After send_clarify the adapter remembers session_key + choice labels."""
        adapter = _make_adapter()
        mock_msg = MagicMock()
        mock_msg.message_id = 1
        adapter._bot.send_message = AsyncMock(return_value=mock_msg)

        await adapter.send_clarify(
            chat_id="12345",
            question="Q?",
            choices=["alpha", "beta", "gamma"],
            session_key="sk-1",
        )

        assert len(adapter._clarify_state) == 1
        clarify_id = list(adapter._clarify_state.keys())[0]
        session_key, choices = adapter._clarify_state[clarify_id]
        assert session_key == "sk-1"
        assert choices == ["alpha", "beta", "gamma"]

    @pytest.mark.asyncio
    async def test_sends_in_thread_when_metadata_has_thread_id(self):
        adapter = _make_adapter()
        mock_msg = MagicMock()
        mock_msg.message_id = 1
        adapter._bot.send_message = AsyncMock(return_value=mock_msg)

        await adapter.send_clarify(
            chat_id="12345",
            question="Q?",
            choices=["A", "B"],
            session_key="sk",
            metadata={"thread_id": "999"},
        )
        kwargs = adapter._bot.send_message.call_args[1]
        assert kwargs.get("message_thread_id") == 999

    @pytest.mark.asyncio
    async def test_not_connected_returns_error(self):
        adapter = _make_adapter()
        adapter._bot = None
        result = await adapter.send_clarify(
            chat_id="12345", question="Q?", choices=["A"], session_key="sk"
        )
        assert result.success is False

    @pytest.mark.asyncio
    async def test_open_ended_clarify_returns_no_choices_signal(self):
        """With no choices, send_clarify must signal fallback — don't send an empty keyboard."""
        adapter = _make_adapter()
        adapter._bot.send_message = AsyncMock()

        result = await adapter.send_clarify(
            chat_id="12345",
            question="What's your name?",
            choices=None,
            session_key="agent:main:telegram:dm:12345:1",
        )

        assert result.success is False
        assert result.error == "no_choices"
        adapter._bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_choices_returns_no_choices_signal(self):
        """Empty list behaves like None — fallback to plain text."""
        adapter = _make_adapter()
        adapter._bot.send_message = AsyncMock()

        result = await adapter.send_clarify(
            chat_id="12345",
            question="Pick...",
            choices=[],
            session_key="sk",
        )

        assert result.success is False
        assert result.error == "no_choices"
        adapter._bot.send_message.assert_not_called()


# ===========================================================================
# cq: callback — button clicks resolve the clarify
# ===========================================================================


class _AuthRunner:
    def __init__(self, authorized: bool):
        self.authorized = authorized

    async def _handle_message(self, event):
        return None

    def _is_user_authorized(self, source):
        return self.authorized


def _make_callback_query(data: str, user_id: int = 7785056549, user_name: str = "sx"):
    """Build a MagicMock Update object that looks like a Telegram callback_query."""
    update = MagicMock()
    q = update.callback_query
    q.data = data
    q.from_user.id = user_id
    q.from_user.first_name = user_name
    q.message.chat_id = 12345
    q.message.chat.type = "private"
    q.message.message_thread_id = None
    q.answer = AsyncMock()
    q.edit_message_text = AsyncMock()
    return update


class TestTelegramClarifyCallback:
    """_handle_callback_query should route cq:* data to resolve_gateway_clarify."""

    @pytest.mark.asyncio
    async def test_button_click_resolves_clarify(self):
        from tools import clarify_bridge

        adapter = _make_adapter()
        runner = _AuthRunner(True)
        adapter._message_handler = runner._handle_message
        # Seed adapter state as if send_clarify had just run.
        adapter._clarify_state[1] = ("test-session", ["option A", "option B", "option C"])

        # Register a no-op notifier so the bridge will accept entries, and
        # enqueue one so resolve has something to signal.
        clarify_bridge.register_gateway_clarify_notify("test-session", lambda q, c: None)
        # Manually create a blocking entry via the bridge's internals — the
        # happy-path integration test is in test_clarify_bridge.py; here we
        # just need resolve_gateway_clarify to return 1 to verify the wire-up.
        import threading as _th
        from tools.clarify_bridge import _ClarifyEntry, _queues
        entry = _ClarifyEntry("Q?", ["option A", "option B", "option C"])
        _queues.setdefault("test-session", []).append(entry)

        update = _make_callback_query("cq:1:1")  # pick index 1 -> "option B"
        await adapter._handle_callback_query(update, None)

        # Entry was signalled with the chosen label.
        assert entry.event.is_set()
        assert entry.result == "option B"
        # Button state was cleared (one-shot).
        assert 1 not in adapter._clarify_state
        # Feedback rendered.
        update.callback_query.answer.assert_awaited()
        update.callback_query.edit_message_text.assert_awaited()

        # Clean up bridge state.
        clarify_bridge.clear_session_clarifies("test-session")
        clarify_bridge.unregister_gateway_clarify_notify("test-session")

    @pytest.mark.asyncio
    async def test_cancel_button_clears_clarify(self):
        from tools import clarify_bridge
        from tools.clarify_bridge import _ClarifyEntry, _queues

        adapter = _make_adapter()
        runner = _AuthRunner(True)
        adapter._message_handler = runner._handle_message
        adapter._clarify_state[2] = ("cancel-session", ["A", "B"])

        clarify_bridge.register_gateway_clarify_notify("cancel-session", lambda q, c: None)
        entry = _ClarifyEntry("Q?", ["A", "B"])
        _queues.setdefault("cancel-session", []).append(entry)

        update = _make_callback_query("cq:2:cancel")
        await adapter._handle_callback_query(update, None)

        # Entry was signalled but with no result — agent will see ClarifyUnavailable.
        assert entry.event.is_set()
        assert entry.result is None
        assert 2 not in adapter._clarify_state

        clarify_bridge.unregister_gateway_clarify_notify("cancel-session")

    @pytest.mark.asyncio
    async def test_unauthorized_user_is_rejected(self):
        adapter = _make_adapter()
        runner = _AuthRunner(False)  # not authorized
        adapter._message_handler = runner._handle_message
        adapter._clarify_state[3] = ("sk", ["A", "B"])

        update = _make_callback_query("cq:3:0")
        await adapter._handle_callback_query(update, None)

        # Answer with a rejection; state must NOT be consumed.
        update.callback_query.answer.assert_awaited()
        assert 3 in adapter._clarify_state

    @pytest.mark.asyncio
    async def test_already_resolved_returns_friendly_message(self):
        adapter = _make_adapter()
        runner = _AuthRunner(True)
        adapter._message_handler = runner._handle_message
        # Nothing in _clarify_state — simulates a second click after the first
        # already resolved and popped the state.
        update = _make_callback_query("cq:99:0")
        await adapter._handle_callback_query(update, None)
        update.callback_query.answer.assert_awaited()

    @pytest.mark.asyncio
    async def test_invalid_clarify_id_returns_error(self):
        adapter = _make_adapter()
        runner = _AuthRunner(True)
        adapter._message_handler = runner._handle_message
        update = _make_callback_query("cq:notanint:0")
        await adapter._handle_callback_query(update, None)
        update.callback_query.answer.assert_awaited()

    @pytest.mark.asyncio
    async def test_out_of_range_index_returns_error(self):
        adapter = _make_adapter()
        runner = _AuthRunner(True)
        adapter._message_handler = runner._handle_message
        adapter._clarify_state[4] = ("sk", ["A"])  # only one choice
        update = _make_callback_query("cq:4:5")  # index 5 is OOB
        await adapter._handle_callback_query(update, None)
        update.callback_query.answer.assert_awaited()
