import asyncio

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.base import MessageEvent, MessageType
from gateway.platforms.telegram import TelegramAdapter
from gateway.run import GatewayRunner
from gateway.session import SessionSource, build_session_key


class _DummyTask:
    def __init__(self):
        self.cancelled = False

    def done(self):
        return False

    def cancel(self):
        self.cancelled = True


def _source() -> SessionSource:
    return SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="273403055",
        chat_type="dm",
        user_id="273403055",
        user_name="Maxim E.",
        thread_id="363402",
    )


def _text_event(source: SessionSource) -> MessageEvent:
    return MessageEvent(
        text="Is this a real study?",
        message_type=MessageType.TEXT,
        source=source,
    )


def _photo_event(source: SessionSource, path: str = "/tmp/alcohol-study.jpg") -> MessageEvent:
    return MessageEvent(
        text="",
        message_type=MessageType.PHOTO,
        source=source,
        media_urls=[path],
        media_types=["image/jpeg"],
    )


def _make_adapter() -> TelegramAdapter:
    adapter = TelegramAdapter.__new__(TelegramAdapter)
    adapter.config = PlatformConfig(enabled=True, token="fake")
    adapter._pending_messages = {}
    adapter._pending_photo_batches = {}
    adapter._pending_photo_batch_tasks = {}
    adapter._media_group_events = {}
    adapter._media_group_tasks = {}
    adapter._media_downloads_in_progress_by_session = {}
    return adapter


def _make_runner(adapter: TelegramAdapter) -> GatewayRunner:
    runner = GatewayRunner.__new__(GatewayRunner)
    runner.config = GatewayConfig(
        platforms={Platform.TELEGRAM: PlatformConfig(enabled=True, token="fake")},
    )
    runner.adapters = {Platform.TELEGRAM: adapter}
    runner._model = "openai/gpt-4.1-mini"
    runner._base_url = None
    runner._decide_image_input_mode = lambda: "native"
    return runner


@pytest.mark.asyncio
async def test_gateway_merges_buffered_photo_batch_before_image_routing():
    source = _source()
    session_key = build_session_key(source)
    adapter = _make_adapter()
    runner = _make_runner(adapter)
    task = _DummyTask()
    adapter._pending_photo_batches[f"{session_key}:photo-burst"] = _photo_event(source)
    adapter._pending_photo_batch_tasks[f"{session_key}:photo-burst"] = task

    event = await runner._merge_startup_media_followups(
        _text_event(source),
        source,
        session_key,
    )
    message_text = await runner._prepare_inbound_message_text(
        event=event,
        source=source,
        history=[],
    )

    assert message_text == "Is this a real study?"
    assert event.message_type == MessageType.PHOTO
    assert event.media_urls == ["/tmp/alcohol-study.jpg"]
    assert runner._consume_pending_native_image_paths(session_key) == ["/tmp/alcohol-study.jpg"]
    assert adapter._pending_photo_batches == {}
    assert task.cancelled is True


@pytest.mark.asyncio
async def test_gateway_waits_for_in_progress_photo_download(monkeypatch):
    source = _source()
    session_key = build_session_key(source)
    adapter = _make_adapter()
    runner = _make_runner(adapter)
    adapter._media_downloads_in_progress_by_session[session_key] = 1
    monkeypatch.setenv("HERMES_TELEGRAM_STARTUP_MEDIA_GRACE_SECONDS", "0.2")

    async def finish_download():
        await asyncio.sleep(0.02)
        adapter._pending_photo_batches[f"{session_key}:photo-burst"] = _photo_event(
            source,
            "/tmp/late-photo.jpg",
        )
        adapter._media_downloads_in_progress_by_session.pop(session_key, None)

    producer = asyncio.create_task(finish_download())
    event = await runner._merge_startup_media_followups(
        _text_event(source),
        source,
        session_key,
    )
    await producer

    assert event.message_type == MessageType.PHOTO
    assert event.text == "Is this a real study?"
    assert event.media_urls == ["/tmp/late-photo.jpg"]
    assert adapter._pending_photo_batches == {}


@pytest.mark.asyncio
async def test_gateway_merges_priority_queued_photo_followup():
    source = _source()
    session_key = build_session_key(source)
    adapter = _make_adapter()
    runner = _make_runner(adapter)
    adapter._pending_messages[session_key] = _photo_event(source, "/tmp/queued-photo.jpg")

    event = await runner._merge_startup_media_followups(
        _text_event(source),
        source,
        session_key,
    )

    assert event.message_type == MessageType.PHOTO
    assert event.media_urls == ["/tmp/queued-photo.jpg"]
    assert session_key not in adapter._pending_messages
