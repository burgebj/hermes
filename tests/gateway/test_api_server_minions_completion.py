import json
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from gateway.config import PlatformConfig
from gateway.platforms.api_server import APIServerAdapter, cors_middleware


def _make_adapter(api_key: str = "") -> APIServerAdapter:
    extra = {}
    if api_key:
        extra["key"] = api_key
    return APIServerAdapter(PlatformConfig(enabled=True, extra=extra))


def _create_app(adapter: APIServerAdapter) -> web.Application:
    app = web.Application(middlewares=[cors_middleware])
    app["api_server_adapter"] = adapter
    app.router.add_post("/api/minions/completions", adapter._handle_minions_completion)
    return app


@pytest.mark.asyncio
async def test_minions_completion_endpoint_delivers_completion():
    adapter = _make_adapter()
    app = _create_app(adapter)
    envelope = {
        "version": "1.0",
        "kind": "background",
        "task_id": "bg_1",
        "status": "succeeded",
        "callback": {"type": "none"},
        "summary": "done",
    }
    async with TestClient(TestServer(app)) as cli:
        with patch("agent.job_callbacks.deliver_completion", return_value=None) as deliver_mock:
            resp = await cli.post("/api/minions/completions", json=envelope)
            assert resp.status == 200
            data = await resp.json()
            assert data == {"ok": True}
            deliver_mock.assert_called_once_with(envelope)


@pytest.mark.asyncio
async def test_minions_completion_endpoint_requires_auth_when_configured():
    adapter = _make_adapter(api_key="sk-secret")
    app = _create_app(adapter)
    async with TestClient(TestServer(app)) as cli:
        resp = await cli.post("/api/minions/completions", json={"task_id": "x"})
        assert resp.status == 401


@pytest.mark.asyncio
async def test_minions_completion_endpoint_rejects_invalid_json():
    adapter = _make_adapter()
    app = _create_app(adapter)
    async with TestClient(TestServer(app)) as cli:
        resp = await cli.post(
            "/api/minions/completions",
            data="{not valid}",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data


@pytest.mark.asyncio
async def test_minions_completion_endpoint_reports_delivery_errors():
    adapter = _make_adapter()
    app = _create_app(adapter)
    envelope = {
        "version": "1.0",
        "kind": "background",
        "task_id": "bg_1",
        "status": "failed",
        "callback": {"type": "session"},
        "error": "boom",
    }
    async with TestClient(TestServer(app)) as cli:
        with patch("agent.job_callbacks.deliver_completion", return_value="bad callback"):
            resp = await cli.post("/api/minions/completions", json=envelope)
            assert resp.status == 400
            data = await resp.json()
            assert data["error"] == "bad callback"
