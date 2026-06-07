import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from gateway.config import Platform
from gateway.run import (
    GatewayRunner,
    _load_post_turn_compression_config,
    _post_turn_compression_due,
)
from gateway.session import SessionEntry, SessionSource, build_session_key


def _source() -> SessionSource:
    return SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="chat-1",
        chat_type="dm",
        user_id="user-1",
    )


def test_post_turn_compression_defaults_disabled():
    cfg = _load_post_turn_compression_config({})

    assert cfg["enabled"] is False
    assert cfg["delay_seconds"] == 60.0
    assert cfg["threshold_ratio"] == 0.75
    assert cfg["min_message_count"] == 80


def test_post_turn_compression_config_accepts_nested_settings():
    cfg = _load_post_turn_compression_config(
        {
            "compression": {
                "threshold": 0.6,
                "post_turn": {
                    "enabled": "true",
                    "delay_seconds": "12.5",
                    "threshold_ratio": "0.8",
                    "min_message_count": "120",
                    "platforms": "telegram, feishu",
                },
            }
        }
    )

    assert cfg["enabled"] is True
    assert cfg["delay_seconds"] == 12.5
    assert cfg["threshold_ratio"] == 0.8
    assert cfg["min_message_count"] == 120
    assert cfg["platforms"] == ["telegram", "feishu"]
    assert cfg["compression_threshold"] == 0.6


def test_post_turn_compression_respects_global_compression_disable():
    cfg = _load_post_turn_compression_config(
        {
            "compression": {
                "enabled": False,
                "post_turn": {"enabled": True},
            }
        }
    )

    assert cfg["enabled"] is False


def test_post_turn_compression_due_uses_ratio_of_compression_threshold():
    cfg = {
        "enabled": True,
        "compression_threshold": 0.5,
        "threshold_ratio": 0.75,
        "min_message_count": 80,
    }

    assert not _post_turn_compression_due(
        cfg,
        last_prompt_tokens=74_999,
        context_length=200_000,
        message_count=20,
    )
    assert _post_turn_compression_due(
        cfg,
        last_prompt_tokens=75_000,
        context_length=200_000,
        message_count=20,
    )


@pytest.mark.asyncio
async def test_pending_post_turn_compression_cancels_when_new_message_arrives(monkeypatch):
    runner = GatewayRunner.__new__(GatewayRunner)
    runner._post_turn_compression_tasks = {}
    runner._post_turn_compression_started = set()
    runner._background_tasks = set()
    runner._running_agents = {}
    runner._running_agents_ts = {}

    async def never_run(**_kwargs):
        await asyncio.sleep(3600)

    monkeypatch.setattr(runner, "_run_post_turn_compression", never_run)
    monkeypatch.setattr(
        "gateway.run._load_post_turn_compression_config",
        lambda: {
            "enabled": True,
            "delay_seconds": 60.0,
            "threshold_ratio": 0.75,
            "min_message_count": 4,
            "compression_threshold": 0.5,
            "platforms": [],
        },
    )

    session_key = build_session_key(_source())
    runner._schedule_post_turn_compression_if_needed(
        source=_source(),
        session_key=session_key,
        session_id="sess-1",
        last_prompt_tokens=0,
        context_length=0,
        message_count=4,
    )
    task = runner._post_turn_compression_tasks[session_key]

    runner._cancel_pending_post_turn_compression(session_key)
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert task.cancelled()
    assert session_key not in runner._post_turn_compression_tasks


@pytest.mark.asyncio
async def test_post_turn_compression_rewrites_new_session(monkeypatch):
    source = _source()
    session_key = build_session_key(source)
    entry = SessionEntry(
        session_key=session_key,
        session_id="sess-old",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        platform=Platform.TELEGRAM,
        chat_type="dm",
    )
    history = [
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "two"},
        {"role": "user", "content": "three"},
        {"role": "assistant", "content": "four"},
    ]
    compressed = [
        {"role": "user", "content": "summary"},
        {"role": "assistant", "content": "tail"},
    ]

    class Store:
        def __init__(self):
            self._entries = {session_key: entry}
            self.rewrite_transcript = MagicMock()
            self.update_session = MagicMock()
            self._save = MagicMock()

        def _ensure_loaded(self):
            return None

        def load_transcript(self, session_id):
            assert session_id == "sess-old"
            return history

    class FakeCompressor:
        threshold_tokens = 100
        _last_compress_aborted = False

        def has_content_to_compress(self, messages):
            return messages == history

    class FakeAgent:
        def __init__(self, **kwargs):
            self.session_id = kwargs["session_id"]
            self.context_compressor = FakeCompressor()
            self._cached_system_prompt = ""
            self.tools = None
            self.shutdown_memory_provider = MagicMock()
            self.close = MagicMock()

        def _compress_context(self, messages, _system_message, **_kwargs):
            assert messages == history
            self.session_id = "sess-new"
            return compressed, ""

    runner = GatewayRunner.__new__(GatewayRunner)
    runner.session_store = Store()
    runner._running_agents = {}
    runner._running_agents_ts = {}
    runner._post_turn_compression_started = set()
    runner._session_model_overrides = {}
    runner._agent_cache = {}
    runner._agent_cache_lock = None

    monkeypatch.setattr(
        runner,
        "_resolve_session_agent_runtime",
        lambda **_kwargs: ("test-model", {"api_key": "test-key"}),
    )

    with (
        patch("gateway.run._load_gateway_config", return_value={}),
        patch("run_agent.AIAgent", FakeAgent),
        patch(
            "agent.model_metadata.estimate_request_tokens_rough",
            side_effect=[1000, 100],
        ),
    ):
        await runner._run_post_turn_compression(
            source=source,
            session_key=session_key,
            expected_session_id="sess-old",
            expected_message_count=4,
            cfg={
                "enabled": True,
                "delay_seconds": 0,
                "threshold_ratio": 0.75,
                "min_message_count": 4,
            },
        )

    assert entry.session_id == "sess-new"
    runner.session_store._save.assert_called_once()
    runner.session_store.rewrite_transcript.assert_called_once_with(
        "sess-new",
        compressed,
    )
    runner.session_store.update_session.assert_called_once_with(
        session_key,
        last_prompt_tokens=0,
    )
    assert session_key not in runner._running_agents


@pytest.mark.asyncio
async def test_post_turn_compression_discards_if_session_generation_changes(monkeypatch):
    source = _source()
    session_key = build_session_key(source)
    entry = SessionEntry(
        session_key=session_key,
        session_id="sess-old",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        platform=Platform.TELEGRAM,
        chat_type="dm",
    )
    history = [
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "two"},
        {"role": "user", "content": "three"},
        {"role": "assistant", "content": "four"},
    ]

    class Store:
        def __init__(self):
            self._entries = {session_key: entry}
            self.rewrite_transcript = MagicMock()
            self.update_session = MagicMock()
            self._save = MagicMock()

        def _ensure_loaded(self):
            return None

        def load_transcript(self, session_id):
            assert session_id == "sess-old"
            return history

    class FakeCompressor:
        threshold_tokens = 100
        _last_compress_aborted = False

        def has_content_to_compress(self, messages):
            return messages == history

    runner = GatewayRunner.__new__(GatewayRunner)
    runner.session_store = Store()
    runner._running_agents = {}
    runner._running_agents_ts = {}
    runner._post_turn_compression_started = set()
    runner._session_model_overrides = {}
    runner._session_run_generation = {}
    runner._agent_cache = {}
    runner._agent_cache_lock = None

    class FakeAgent:
        def __init__(self, **kwargs):
            self.session_id = kwargs["session_id"]
            self.context_compressor = FakeCompressor()
            self._cached_system_prompt = ""
            self.tools = None
            self.shutdown_memory_provider = MagicMock()
            self.close = MagicMock()

        def _compress_context(self, messages, _system_message, **_kwargs):
            assert messages == history
            runner._invalidate_session_run_generation(
                session_key,
                reason="test_interrupt",
            )
            runner._release_running_agent_state(session_key)
            self.session_id = "sess-new"
            return [{"role": "user", "content": "summary"}], ""

    monkeypatch.setattr(
        runner,
        "_resolve_session_agent_runtime",
        lambda **_kwargs: ("test-model", {"api_key": "test-key"}),
    )

    with (
        patch("gateway.run._load_gateway_config", return_value={}),
        patch("run_agent.AIAgent", FakeAgent),
        patch("agent.model_metadata.estimate_request_tokens_rough", return_value=1000),
    ):
        await runner._run_post_turn_compression(
            source=source,
            session_key=session_key,
            expected_session_id="sess-old",
            expected_message_count=4,
            cfg={
                "enabled": True,
                "delay_seconds": 0,
                "threshold_ratio": 0.75,
                "min_message_count": 4,
            },
        )

    assert entry.session_id == "sess-old"
    runner.session_store._save.assert_not_called()
    runner.session_store.rewrite_transcript.assert_not_called()
    runner.session_store.update_session.assert_not_called()
    assert session_key not in runner._running_agents
