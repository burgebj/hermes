from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_invalid_ogg_voice_is_not_sent_as_document(monkeypatch, tmp_path):
    from gateway.config import Platform
    from gateway.platforms.telegram import TelegramAdapter

    adapter = object.__new__(TelegramAdapter)
    adapter.platform = Platform.TELEGRAM
    adapter._bot = AsyncMock()
    adapter._missing_media_path_error = lambda label, path: f"{label} file not found: {path}"
    adapter._metadata_thread_id = lambda metadata: None
    adapter._reply_to_message_id_for_send = lambda reply_to, metadata, reply_to_mode=None: None
    adapter._thread_kwargs_for_send = lambda *args, **kwargs: {}
    adapter._notification_kwargs = lambda metadata: {}
    adapter._reply_to_mode = "auto"
    adapter._send_with_dm_topic_reply_anchor_retry = AsyncMock()
    adapter.send_document = AsyncMock()

    path = tmp_path / "bad.ogg"
    path.write_bytes(b"mp3-bytes")
    monkeypatch.setattr(
        "tools.tts_tool._is_telegram_voice_artifact",
        lambda audio_path: False,
        raising=False,
    )

    result = await adapter.send_voice(chat_id="123", audio_path=str(path))

    assert result.success is False
    assert "valid telegram voice" in result.error.lower()
    adapter._send_with_dm_topic_reply_anchor_retry.assert_not_called()
    adapter.send_document.assert_not_called()
