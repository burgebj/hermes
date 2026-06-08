"""Regression tests for Telegram voice/audio media cache failures.

If Telegram getFile/download times out, the gateway must not dispatch an empty
turn to the agent. It should retry briefly, then notify the user to resend.
"""

import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import PlatformConfig
from gateway.platforms.base import MessageType


# ---------------------------------------------------------------------------
# Mock the telegram package if it is not installed in the test environment.
# ---------------------------------------------------------------------------
def _ensure_telegram_mock():
    if "telegram" in sys.modules and hasattr(sys.modules["telegram"], "__file__"):
        return

    telegram_mod = types.ModuleType("telegram")
    telegram_mod.Update = object
    telegram_mod.Bot = object
    telegram_mod.Message = object
    telegram_mod.InlineKeyboardButton = object
    telegram_mod.InlineKeyboardMarkup = object

    constants_mod = types.ModuleType("telegram.constants")
    constants_mod.ParseMode = SimpleNamespace(MARKDOWN_V2="MarkdownV2")
    constants_mod.ChatType = SimpleNamespace(
        GROUP="group",
        SUPERGROUP="supergroup",
        CHANNEL="channel",
        PRIVATE="private",
    )

    ext_mod = types.ModuleType("telegram.ext")
    ext_mod.Application = object
    ext_mod.CommandHandler = object
    ext_mod.CallbackQueryHandler = object
    ext_mod.MessageHandler = object
    ext_mod.ContextTypes = SimpleNamespace(DEFAULT_TYPE=object)
    ext_mod.filters = SimpleNamespace(
        TEXT=object(),
        COMMAND=object(),
        LOCATION=object(),
        PHOTO=object(),
        VIDEO=object(),
        AUDIO=object(),
        VOICE=object(),
        Document=SimpleNamespace(ALL=object()),
        Sticker=SimpleNamespace(ALL=object()),
    )

    request_mod = types.ModuleType("telegram.request")
    request_mod.HTTPXRequest = object

    telegram_mod.constants = constants_mod
    telegram_mod.ext = ext_mod
    telegram_mod.request = request_mod

    sys.modules.setdefault("telegram", telegram_mod)
    sys.modules.setdefault("telegram.ext", ext_mod)
    sys.modules.setdefault("telegram.constants", constants_mod)
    sys.modules.setdefault("telegram.request", request_mod)


_ensure_telegram_mock()
from gateway.platforms.telegram import TelegramAdapter  # noqa: E402


def _make_file_obj(data: bytes = b"voice-bytes"):
    file_obj = AsyncMock()
    file_obj.download_as_bytearray = AsyncMock(return_value=bytearray(data))
    file_obj.file_path = "voice/file.ogg"
    return file_obj


def _make_voice_message(voice=None):
    msg = MagicMock()
    msg.message_id = 42
    msg.text = ""
    msg.caption = None
    msg.date = None
    msg.photo = None
    msg.video = None
    msg.audio = None
    msg.voice = voice
    msg.sticker = None
    msg.document = None
    msg.media_group_id = None
    msg.reply_to_message = None
    msg.forum_topic_created = None
    msg.message_thread_id = None
    msg.is_topic_message = False
    msg.chat = MagicMock()
    msg.chat.id = 100
    msg.chat.type = "private"
    msg.chat.title = None
    msg.chat.full_name = "Test User"
    msg.from_user = MagicMock()
    msg.from_user.id = 1
    msg.from_user.full_name = "Test User"
    msg.reply_text = AsyncMock()
    return msg


def _make_update(msg):
    update = MagicMock()
    update.message = msg
    update.update_id = 123
    return update


@pytest.fixture()
def adapter():
    config = PlatformConfig(enabled=True, token="fake-token")
    adapter = TelegramAdapter(config)
    adapter.handle_message = AsyncMock()
    adapter._is_callback_user_authorized = lambda user_id, **_kw: True
    return adapter


@pytest.mark.asyncio
async def test_voice_cache_timeout_replies_and_does_not_dispatch_empty_turn(adapter, monkeypatch):
    monkeypatch.setenv("HERMES_TELEGRAM_MEDIA_DOWNLOAD_ATTEMPTS", "1")
    voice = MagicMock()
    voice.get_file = AsyncMock(side_effect=RuntimeError("Timed out"))
    msg = _make_voice_message(voice=voice)

    await adapter._handle_media_message(_make_update(msg), MagicMock())

    adapter.handle_message.assert_not_called()
    msg.reply_text.assert_awaited_once()
    notice = msg.reply_text.await_args.args[0]
    assert "voice message" in notice
    assert "couldn't download" in notice
    assert "Please resend" in notice


@pytest.mark.asyncio
async def test_voice_cache_retries_then_dispatches_transcribable_media(adapter, monkeypatch):
    monkeypatch.setenv("HERMES_TELEGRAM_MEDIA_DOWNLOAD_ATTEMPTS", "2")
    monkeypatch.setenv("HERMES_TELEGRAM_MEDIA_DOWNLOAD_RETRY_DELAY_SECONDS", "0")
    file_obj = _make_file_obj(b"ogg-bytes")
    voice = MagicMock()
    voice.get_file = AsyncMock(side_effect=[RuntimeError("Timed out"), file_obj])
    msg = _make_voice_message(voice=voice)

    with patch("gateway.platforms.telegram.cache_audio_from_bytes", return_value="/tmp/cached.ogg") as cache_mock:
        await adapter._handle_media_message(_make_update(msg), MagicMock())

    assert voice.get_file.await_count == 2
    cache_mock.assert_called_once_with(b"ogg-bytes", ext=".ogg")
    msg.reply_text.assert_not_awaited()
    adapter.handle_message.assert_awaited_once()
    event = adapter.handle_message.await_args.args[0]
    assert event.message_type == MessageType.VOICE
    assert event.media_urls == ["/tmp/cached.ogg"]
    assert event.media_types == ["audio/ogg"]
