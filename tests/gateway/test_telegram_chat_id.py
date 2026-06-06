"""Tests for Telegram username-format chat_id support in gateway/platforms/telegram.py.

Covers: _normalize_chat_id helper, send() with username chat_id, edit_message
with username chat_id.

Bug: #13206 — TELEGRAM_HOME_CHANNEL set to a username like @some_user caused
int(chat_id) to raise ValueError in send and edit_message paths.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import PlatformConfig


from gateway.platforms.telegram import (
    TelegramAdapter,
    _normalize_chat_id,
)


# ---------------------------------------------------------------------------
# _normalize_chat_id
# ---------------------------------------------------------------------------

class TestNormalizeChatId:
    """Unit tests for the _normalize_chat_id helper."""

    def test_numeric_string_returns_int(self):
        assert _normalize_chat_id("12345") == 12345
        assert isinstance(_normalize_chat_id("12345"), int)

    def test_negative_numeric_string_returns_int(self):
        assert _normalize_chat_id("-1001234567") == -1001234567
        assert isinstance(_normalize_chat_id("-1001234567"), int)

    def test_username_string_returns_str(self):
        assert _normalize_chat_id("@channel_name") == "@channel_name"
        assert isinstance(_normalize_chat_id("@channel_name"), str)

    def test_username_without_at_returns_str(self):
        # plain username without @
        result = _normalize_chat_id("some_user")
        assert result == "some_user"
        assert isinstance(result, str)

    def test_leading_at_sign_stripped_user(self):
        # username with @ should be returned as-is per Telegram Bot API
        result = _normalize_chat_id("@valid_user")
        assert result == "@valid_user"

    def test_chat_id_already_int_passthrough(self):
        # When chat_id arrives as a string representation of an int
        # (e.g. from env vars), it gets converted to int
        assert _normalize_chat_id("999999999") == 999999999


# ---------------------------------------------------------------------------
# send() with username chat_id
# ---------------------------------------------------------------------------

class TestSendWithUsernameChatId:
    """Integration tests for TelegramAdapter.send() with username-format chat_id."""

    @pytest.fixture
    def adapter(self):
        config = PlatformConfig(enabled=True, token="fake-token")
        return TelegramAdapter(config)

    @pytest.fixture
    def mock_bot(self):
        bot = MagicMock()
        bot.send_message = AsyncMock(return_value=MagicMock(message_id=42))
        return bot

    @pytest.mark.asyncio
    async def test_send_message_with_username_chat_id(self, adapter, mock_bot):
        """send() should not crash when chat_id is a Telegram username."""
        adapter._bot = mock_bot

        result = await adapter.send(
            chat_id="@some_user",
            content="Hello from the test",
            reply_to=None,
            metadata=None,
        )

        assert result.success is True
        # Verify the bot was called with the username string, not int()
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == "@some_user"
        assert call_kwargs["text"] == "Hello from the test"

    @pytest.mark.asyncio
    async def test_send_message_with_numeric_chat_id_still_works(self, adapter, mock_bot):
        """send() should still handle numeric chat_id correctly."""
        adapter._bot = mock_bot

        result = await adapter.send(
            chat_id="123456789",
            content="Hello numeric",
            reply_to=None,
            metadata=None,
        )

        assert result.success is True
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == 123456789  # converted to int

    @pytest.mark.asyncio
    async def test_send_message_with_negative_chat_id(self, adapter, mock_bot):
        """send() should handle negative numeric chat_id (Telegram supergroup format)."""
        adapter._bot = mock_bot

        result = await adapter.send(
            chat_id="-1001234567890",
            content="Hello supergroup",
            reply_to=None,
            metadata=None,
        )

        assert result.success is True
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs["chat_id"] == -1001234567890


# ---------------------------------------------------------------------------
# edit_message with username chat_id
# ---------------------------------------------------------------------------

class TestEditMessageWithUsernameChatId:
    """Integration tests for TelegramAdapter.edit_message() with username-format chat_id."""

    @pytest.fixture
    def adapter(self):
        config = PlatformConfig(enabled=True, token="fake-token")
        return TelegramAdapter(config)

    @pytest.fixture
    def mock_bot(self):
        bot = MagicMock()
        bot.edit_message_text = AsyncMock(return_value=MagicMock(message_id=42))
        return bot

    @pytest.mark.asyncio
    async def test_edit_message_with_username_chat_id(self, adapter, mock_bot):
        """edit_message() should not crash when chat_id is a Telegram username."""
        adapter._bot = mock_bot

        result = await adapter.edit_message(
            chat_id="@channel_name",
            message_id="12345",
            content="Updated text",
        )

        assert result.success is True
        mock_bot.edit_message_text.assert_called_once()
        call_kwargs = mock_bot.edit_message_text.call_args.kwargs
        assert call_kwargs["chat_id"] == "@channel_name"
        # message_id should still be int
        assert call_kwargs["message_id"] == 12345

    @pytest.mark.asyncio
    async def test_edit_message_with_numeric_chat_id_still_works(self, adapter, mock_bot):
        """edit_message() should still handle numeric chat_id correctly."""
        adapter._bot = mock_bot

        result = await adapter.edit_message(
            chat_id="123456789",
            message_id="999",
            content="Updated numeric",
        )

        assert result.success is True
        call_kwargs = mock_bot.edit_message_text.call_args.kwargs
        assert call_kwargs["chat_id"] == 123456789
        assert call_kwargs["message_id"] == 999
