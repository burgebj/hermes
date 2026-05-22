"""#22153: missing optional deps for one platform must not abort sending
to an unrelated platform.

The shared dispatcher `_send_to_platform` historically imported
`gateway.platforms.discord` and `gateway.platforms.slack` unconditionally
at function entry, so a missing optional dependency for either of those
platforms would raise ImportError before the QQ branch could run.
"""

import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest


@pytest.fixture
def force_missing_discord_slack(monkeypatch):
    """Make `from gateway.platforms.{discord,slack} import ...` raise ImportError.

    Setting a module entry to None is the documented Python trick that turns
    a subsequent `from x import y` into ImportError, simulating a missing
    optional dependency without uninstalling anything.
    """
    monkeypatch.setitem(sys.modules, "gateway.platforms.discord", None)
    monkeypatch.setitem(sys.modules, "gateway.platforms.slack", None)


def test_send_to_platform_qq_survives_missing_discord_and_slack(force_missing_discord_slack):
    from gateway.config import Platform
    from tools.send_message_tool import _send_to_platform

    pconfig = SimpleNamespace(token="secret", extra={"app_id": "1001"})

    async def _fake_qqbot(_pconfig, _chat_id, _message):
        return {
            "success": True,
            "platform": "qqbot",
            "chat_id": _chat_id,
            "message_id": "m-1",
        }

    with patch("tools.send_message_tool._send_qqbot", side_effect=_fake_qqbot):
        result = asyncio.run(
            _send_to_platform(
                platform=Platform.QQBOT,
                pconfig=pconfig,
                chat_id="user42",
                message="hello",
            )
        )

    assert result == {
        "success": True,
        "platform": "qqbot",
        "chat_id": "user42",
        "message_id": "m-1",
    }


def test_send_to_platform_signal_survives_missing_discord_and_slack(force_missing_discord_slack):
    """Signal text path also goes through the dispatcher loop."""
    from gateway.config import Platform
    from tools.send_message_tool import _send_to_platform

    pconfig = SimpleNamespace(token="", extra={"signal_url": "http://localhost:8080"})

    async def _fake_signal(_extra, _chat_id, _msg, **_kw):
        return {"success": True, "platform": "signal", "chat_id": _chat_id, "message_id": "ts-1"}

    with patch("tools.send_message_tool._send_signal", side_effect=_fake_signal):
        result = asyncio.run(
            _send_to_platform(
                platform=Platform.SIGNAL,
                pconfig=pconfig,
                chat_id="+15551234567",
                message="hi",
            )
        )

    assert result["success"] is True
    assert result["platform"] == "signal"


def test_send_to_platform_slack_chunk_limit_falls_back_when_slack_unavailable(force_missing_discord_slack):
    """When the Slack adapter import fails, the dispatcher must still know a
    safe MAX_MESSAGE_LENGTH for SLACK (used purely for chunking) instead of
    crashing on `SlackAdapter.MAX_MESSAGE_LENGTH`."""
    from gateway.config import Platform
    from tools.send_message_tool import _send_to_platform

    pconfig = SimpleNamespace(token="xoxb-fake", extra={})

    async def _fake_slack(_token, _chat_id, _msg, **_kw):
        return {"success": True, "platform": "slack", "chat_id": _chat_id, "message_id": "S1"}

    with patch("tools.send_message_tool._send_slack", side_effect=_fake_slack):
        result = asyncio.run(
            _send_to_platform(
                platform=Platform.SLACK,
                pconfig=pconfig,
                chat_id="C123",
                message="hello slack",
            )
        )

    assert isinstance(result, dict)
    assert result.get("success") is True
