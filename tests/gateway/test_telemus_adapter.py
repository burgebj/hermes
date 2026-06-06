"""Tests for the Telemus platform adapter plugin."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from tests.gateway._plugin_adapter_loader import load_plugin_adapter

_telemus_mod = load_plugin_adapter("telemus")
TelemusAdapter = _telemus_mod.TelemusAdapter
TelemusJsonlClient = _telemus_mod.TelemusJsonlClient
_parse_agent_index = _telemus_mod._parse_agent_index
_env_enablement = _telemus_mod._env_enablement
validate_config = _telemus_mod.validate_config


class FakeTelemusServer:
    def __init__(self):
        self.requests = []
        self._server = None
        self.port = None
        self.transcript = [
            {"index": 0, "speaker": "User", "text": "hello from telemus"},
            {"index": 1, "speaker": "Telemus AI", "text": "assistant reply"},
        ]
        self.events = [
            {"id": 1, "eventId": 1, "type": "transcript.entry", "agentIndex": -1, "speaker": "User", "role": "user", "text": "event hello"},
            {"id": 2, "eventId": 2, "type": "transcript.entry", "agentIndex": -1, "speaker": "Telemus AI", "role": "assistant", "text": "event reply"},
        ]
        self.acked = 0

    async def start(self):
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        sock = self._server.sockets[0]
        self.port = sock.getsockname()[1]
        return self

    async def close(self):
        self._server.close()
        await self._server.wait_closed()

    async def _handle(self, reader, writer):
        while True:
            line = await reader.readline()
            if not line:
                break
            request = json.loads(line.decode("utf-8"))
            self.requests.append(request)
            method = request.get("method")
            if method == "Devtools.getInfo":
                result = {"protocol": "jsonl", "commands": ["AI.sendMessage", "AI.getTranscript", "Channels.status", "Channels.pollEvents", "Channels.ack", "Channels.sendMessage"]}
            elif method == "Channels.status":
                result = {"protocol": "vrai.desktop.channels.v1", "lastEventId": 0, "pollEvents": True, "ack": True}
            elif method == "Channels.pollEvents":
                after = int(request.get("afterEventId") or 0)
                result = {"protocol": "vrai.desktop.channels.v1", "lastEventId": 2, "events": [e for e in self.events if int(e["eventId"]) > after]}
            elif method == "Channels.ack":
                self.acked = int(request.get("throughEventId") or 0)
                result = {"ackedThroughEventId": self.acked}
            elif method == "Channels.sendMessage":
                result = {"accepted": True, "agentIndex": request.get("agentIndex"), "correlationId": request.get("correlationId")}
            elif method == "AI.sendMessage":
                result = {"accepted": True, "agentIndex": request.get("agentIndex")}
            elif method == "AI.getTranscript":
                result = {"agentIndex": request.get("agentIndex"), "entries": self.transcript}
            else:
                writer.write(json.dumps({"id": request.get("id"), "ok": False, "error": "unknown"}).encode() + b"\n")
                await writer.drain()
                continue
            writer.write(json.dumps({"id": request.get("id"), "ok": True, "result": result}).encode() + b"\n")
            await writer.drain()
        writer.close()
        await writer.wait_closed()


@pytest_asyncio.fixture
async def fake_server():
    server = await FakeTelemusServer().start()
    try:
        yield server
    finally:
        await server.close()


def test_parse_agent_index():
    assert _parse_agent_index("agent:-1", 0) == -1
    assert _parse_agent_index("agent:2", -1) == 2
    assert _parse_agent_index("3", -1) == 3
    assert _parse_agent_index("bad", 7) == 7


@pytest.mark.asyncio
async def test_jsonl_client_round_trip(fake_server):
    client = TelemusJsonlClient("127.0.0.1", fake_server.port)
    try:
        info = await client.get_info()
        assert info["protocol"] == "jsonl"
        sent = await client.send_message("hello", agent_index=0)
        assert sent["accepted"] is True
        assert fake_server.requests[-1]["method"] == "AI.sendMessage"
        assert fake_server.requests[-1]["text"] == "hello"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_adapter_connect_send_and_poll(monkeypatch, fake_server):
    from gateway.config import PlatformConfig

    cfg = PlatformConfig(
        enabled=True,
        extra={
            "host": "127.0.0.1",
            "port": fake_server.port,
            "agent_index": -1,
            "poll_transcripts": False,
            "prefer_channels": False,
        },
    )
    adapter = TelemusAdapter(cfg)
    monkeypatch.setattr(adapter, "_acquire_platform_lock", lambda *a, **k: True)
    monkeypatch.setattr(adapter, "_release_platform_lock", lambda: None)

    assert await adapter.connect() is True
    result = await adapter.send("agent:0", "hi")
    assert result.success is True
    assert fake_server.requests[-1]["agentIndex"] == 0

    handler = AsyncMock()
    monkeypatch.setattr(adapter, "handle_message", handler)
    await adapter._poll_transcript_once(-1)
    handler.assert_awaited_once()
    event = handler.await_args.args[0]
    assert event.text == "hello from telemus"
    assert event.source.chat_id == "agent:-1"
    await adapter.disconnect()


@pytest.mark.asyncio
async def test_adapter_prefers_channel_events(monkeypatch, fake_server):
    from gateway.config import PlatformConfig

    cfg = PlatformConfig(
        enabled=True,
        extra={
            "host": "127.0.0.1",
            "port": fake_server.port,
            "agent_index": -1,
            "poll_transcripts": True,
            "prefer_channels": True,
        },
    )
    adapter = TelemusAdapter(cfg)
    monkeypatch.setattr(adapter, "_acquire_platform_lock", lambda *a, **k: True)
    monkeypatch.setattr(adapter, "_release_platform_lock", lambda: None)

    assert await adapter.connect() is True
    if adapter._poll_task:
        adapter._poll_task.cancel()
        try:
            await adapter._poll_task
        except asyncio.CancelledError:
            pass
        adapter._poll_task = None
        adapter._last_event_id = 0
    assert adapter._supports_channels is True
    result = await adapter.send("agent:-1", "hi via channel")
    assert result.success is True
    assert fake_server.requests[-1]["method"] == "Channels.sendMessage"

    handler = AsyncMock()
    monkeypatch.setattr(adapter, "handle_message", handler)
    await adapter._poll_events_once()
    handler.assert_awaited_once()
    event = handler.await_args.args[0]
    assert event.text == "event hello"
    assert event.source.chat_id == "agent:-1"
    assert fake_server.acked == 2
    await adapter.disconnect()


def test_env_enablement(monkeypatch):
    monkeypatch.setenv("TELEMUS_DEVTOOLS_PORT", "8765")
    monkeypatch.setenv("TELEMUS_AGENT_INDEX", "0")
    seed = _env_enablement()
    assert seed["port"] == 8765
    assert seed["agent_index"] == 0
    assert seed["home_channel"]["chat_id"] == "agent:0"


def test_validate_config_rejects_bad_port(monkeypatch):
    from gateway.config import PlatformConfig

    monkeypatch.delenv("TELEMUS_DEVTOOLS_PORT", raising=False)
    errors = validate_config(PlatformConfig(enabled=True, extra={"port": "bad"}))
    assert errors
