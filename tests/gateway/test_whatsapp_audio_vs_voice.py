"""WhatsApp: generic audio attachments must NOT collapse into voice notes.

WhatsApp's Baileys bridge (scripts/whatsapp-bridge/bridge.js) already
distinguishes the two audio payloads it can receive:

  - pttMessage  → ``mediaType: "ptt"``    → native voice note (Opus/OGG)
  - audioMessage → ``mediaType: "audio"``  → generic audio file attachment

The adapter must preserve that split — ``ptt`` → MessageType.VOICE,
``audio`` → MessageType.AUDIO — exactly like the Telegram adapter
(msg.voice → VOICE, msg.audio → AUDIO). Otherwise the gateway's
STT/file-attachment routing contract breaks: a plain .mp3/.m4a attachment
gets pushed into the speech-to-text pipeline as if it were a voice message.

See tests/gateway/test_telegram_audio_vs_voice.py for the sibling invariant
and the runner-level routing it guards.
"""

from unittest.mock import patch

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.base import MessageType
from gateway.platforms.whatsapp import WhatsAppAdapter
from gateway.session import SessionSource


def _make_adapter() -> WhatsAppAdapter:
    adapter = WhatsAppAdapter(PlatformConfig(enabled=True, extra={"session_name": "test"}))
    # Focus on media classification; bypass the DM/group policy gate.
    adapter._should_process_message = lambda data: True  # type: ignore[assignment]
    return adapter


def _media_payload(media_type: str, path: str) -> dict:
    return {
        "messageId": "m1",
        "chatId": "111@s.whatsapp.net",
        "senderId": "111@s.whatsapp.net",
        "senderName": "tester",
        "isGroup": False,
        "body": "",
        "hasMedia": True,
        "mediaType": media_type,
        "mediaUrls": [path],
    }


# ---------------------------------------------------------------------------
# Adapter classification: ptt vs audio map to distinct MessageTypes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ptt_maps_to_voice(tmp_path):
    """A native voice note (mediaType='ptt') must become MessageType.VOICE."""
    adapter = _make_adapter()
    path = str(tmp_path / "aud_deadbeef.ogg")
    event = await adapter._build_message_event(_media_payload("ptt", path))

    assert event is not None
    assert event.message_type == MessageType.VOICE
    assert event.media_urls == [path]
    assert event.media_types == ["audio/ogg"]


@pytest.mark.asyncio
async def test_audio_attachment_maps_to_audio(tmp_path):
    """A generic audio file (mediaType='audio') must become MessageType.AUDIO."""
    adapter = _make_adapter()
    path = str(tmp_path / "aud_cafef00d.m4a")
    event = await adapter._build_message_event(_media_payload("audio", path))

    assert event is not None
    assert event.message_type == MessageType.AUDIO
    assert event.media_urls == [path]
    # Audio-file MIME is derived from the extension, not hardcoded to ogg.
    assert event.media_types == ["audio/mp4"]


@pytest.mark.asyncio
async def test_audio_mp3_attachment_mime(tmp_path):
    """An .mp3 audio attachment keeps its proper MIME and AUDIO type."""
    adapter = _make_adapter()
    path = str(tmp_path / "aud_12345678.mp3")
    event = await adapter._build_message_event(_media_payload("audio", path))

    assert event is not None
    assert event.message_type == MessageType.AUDIO
    assert event.media_types == ["audio/mpeg"]


# ---------------------------------------------------------------------------
# End-to-end: the runner routes the adapter's WhatsApp AUDIO event away from STT
# ---------------------------------------------------------------------------


def _make_runner(stt_enabled: bool = True) -> "GatewayRunner":  # type: ignore[name-defined]
    from gateway.run import GatewayRunner

    runner = GatewayRunner.__new__(GatewayRunner)
    runner.config = GatewayConfig(stt_enabled=stt_enabled)
    runner.adapters = {}
    runner._model = "test-model"
    runner._base_url = ""
    runner._has_setup_skill = lambda: False
    return runner


@pytest.mark.asyncio
async def test_whatsapp_audio_attachment_bypasses_stt(tmp_path):
    """WhatsApp 'audio' → AUDIO event must NOT be routed to STT by the runner."""
    adapter = _make_adapter()
    path = str(tmp_path / "aud_99887766.mp3")
    event = await adapter._build_message_event(_media_payload("audio", path))
    assert event.message_type == MessageType.AUDIO

    runner = _make_runner(stt_enabled=True)
    source = SessionSource(platform=Platform.WHATSAPP, chat_id="111", chat_type="dm")

    with patch(
        "tools.transcription_tools.transcribe_audio",
        side_effect=AssertionError("audio file attachments must NOT be transcribed"),
    ):
        with patch(
            "tools.credential_files.to_agent_visible_cache_path",
            side_effect=lambda p: p,
        ):
            result = await runner._prepare_inbound_message_text(
                event=event,
                source=source,
                history=[],
            )

    assert result is not None
    assert path in result
    assert "audio file attachment" in result.lower()
    assert "voice message" not in result.lower()


@pytest.mark.asyncio
async def test_whatsapp_voice_note_still_transcribed(tmp_path):
    """WhatsApp 'ptt' → VOICE event must still flow through STT."""
    adapter = _make_adapter()
    path = str(tmp_path / "aud_55443322.ogg")
    event = await adapter._build_message_event(_media_payload("ptt", path))
    assert event.message_type == MessageType.VOICE

    runner = _make_runner(stt_enabled=True)
    source = SessionSource(platform=Platform.WHATSAPP, chat_id="111", chat_type="dm")

    with patch(
        "tools.transcription_tools.transcribe_audio",
        return_value={"success": True, "transcript": "hello there", "provider": "whisper"},
    ) as mock_transcribe:
        result = await runner._prepare_inbound_message_text(
            event=event,
            source=source,
            history=[],
        )

    mock_transcribe.assert_called_once_with(path)
    assert "hello there" in result
    assert "voice message" in result.lower()
