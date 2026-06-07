from __future__ import annotations

import pytest

from tui_gateway import ws as ws_mod


class _DisconnectingWebSocket:
    client = None

    def __init__(self) -> None:
        self.accepted = False
        self.closed = False
        self.sent: list[str] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_text(self, line: str) -> None:
        self.sent.append(line)

    async def receive_text(self) -> str:
        raise ws_mod._WebSocketDisconnect(1000)

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_ws_startup_starts_shared_mcp_discovery_before_ready(monkeypatch):
    calls: list[dict[str, object]] = []

    def _fake_start_background_mcp_discovery(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(
        "hermes_cli.mcp_startup.start_background_mcp_discovery",
        _fake_start_background_mcp_discovery,
    )

    websocket = _DisconnectingWebSocket()

    await ws_mod.handle_ws(websocket)

    assert websocket.accepted is True
    assert websocket.sent, "expected gateway.ready frame to be sent"
    assert calls == [
        {
            "logger": ws_mod._log,
            "thread_name": "tui-ws-mcp-discovery",
        }
    ]
