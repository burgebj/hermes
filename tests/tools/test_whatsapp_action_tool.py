"""Tests for tools/whatsapp_action_tool.py."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import Platform
from tools.whatsapp_action_tool import _post_bridge, whatsapp_action_tool


class _AsyncResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status = status
        self._payload = payload if payload is not None else {"success": True, "messageId": "msg1"}
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def json(self):
        return self._payload

    async def text(self):
        return self._text


def _run_async_immediately(coro):
    import asyncio
    return asyncio.run(coro)


def _config(port=18792):
    whatsapp_cfg = SimpleNamespace(enabled=True, extra={"bridge_port": port})
    return SimpleNamespace(platforms={Platform.WHATSAPP: whatsapp_cfg})


@pytest.mark.asyncio
async def test_post_bridge_uses_configured_whatsapp_bridge_port():
    response = _AsyncResponse(payload={"success": True, "messageId": "react1"})
    session = MagicMock()
    session.post = MagicMock(return_value=response)

    class SessionFactory:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *exc):
            return False

    with patch("aiohttp.ClientSession", return_value=SessionFactory()):
        result = await _post_bridge({"bridge_port": 18792}, "react", {"chatId": "chat", "messageId": "m1", "emoji": "💚"})

    assert result["success"] is True
    assert result["message_id"] == "react1"
    session.post.assert_called_once()
    assert session.post.call_args.args[0] == "http://127.0.0.1:18792/react"


def test_status_reply_posts_to_status_reply_endpoint():
    with patch("tools.whatsapp_action_tool.load_gateway_config", return_value=_config()), \
         patch("model_tools._run_async", side_effect=_run_async_immediately), \
         patch("tools.whatsapp_action_tool._post_bridge", new=AsyncMock(return_value={"success": True, "message_id": "msg1"})) as post_mock:
        result = json.loads(whatsapp_action_tool({
            "action": "status_reply",
            "status_message_id": "status1",
            "message": "Qué bonito ❤️",
            "status_author_jid": "5215559453922@s.whatsapp.net",
        }))

    assert result["success"] is True
    post_mock.assert_awaited_once_with(
        {"bridge_port": 18792},
        "status-reply",
        {
            "statusMessageId": "status1",
            "message": "Qué bonito ❤️",
            "statusAuthorJid": "5215559453922@s.whatsapp.net",
        },
    )


def test_post_text_status_requires_explicit_recipient_list():
    with patch("tools.whatsapp_action_tool.load_gateway_config", return_value=_config()):
        result = json.loads(whatsapp_action_tool({
            "action": "post_text_status",
            "message": "hello status",
        }))

    assert "explicit non-empty status_jid_list" in result["error"]


def test_dry_run_does_not_call_bridge():
    with patch("tools.whatsapp_action_tool.load_gateway_config", return_value=_config()), \
         patch("model_tools._run_async", side_effect=_run_async_immediately), \
         patch("tools.whatsapp_action_tool._post_bridge", new=AsyncMock()) as post_mock:
        result = json.loads(whatsapp_action_tool({
            "action": "status_react",
            "status_message_id": "status1",
            "emoji": "💚",
            "dry_run": True,
        }))

    assert result["success"] is True
    assert result["dry_run"] is True
    assert result["endpoint"] == "status-react"
    post_mock.assert_not_called()
