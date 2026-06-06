"""Tests for the HERMES_SUPPRESS_SHUTDOWN_NOTIFY env-var gate.

When HERMES_SUPPRESS_SHUTDOWN_NOTIFY is set to a truthy value the gateway must
skip all outbound Telegram/messaging broadcasts on shutdown — the function
body still runs to completion (other code may reference the symbol) but no
adapter.send() call is made.

When the env var is absent or set to a falsy value ("false", "0", "no") the
function proceeds normally and sends notifications to active sessions.

Motivation: single-machine Fly.io apps emit SIGTERM on every ``fly deploy``
which, without this gate, broadcasts "Gateway shutting down" to every active
chat on every deploy.  Operators who only use Hermes as a scripted tool (no
interactive Telegram DMs) receive pure noise.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.platforms.base import SendResult
from gateway.session import build_session_key
from tests.gateway.restart_test_helpers import make_restart_runner, make_restart_source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "env_value",
    ["true", "True", "TRUE", "1", "yes", "Yes", "YES"],
)
async def test_shutdown_notify_suppressed_when_env_truthy(env_value, monkeypatch):
    """When HERMES_SUPPRESS_SHUTDOWN_NOTIFY is a truthy value, no message is sent."""
    monkeypatch.setenv("HERMES_SUPPRESS_SHUTDOWN_NOTIFY", env_value)

    runner, adapter = make_restart_runner()
    source = make_restart_source(chat_id="111")
    session_key = build_session_key(source)

    runner._running_agents[session_key] = object()
    runner._cache_session_source(session_key, source)
    adapter.send = AsyncMock(return_value=SendResult(success=True, message_id="msg"))

    await runner._notify_active_sessions_of_shutdown()

    adapter.send.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "env_value",
    [None, "false", "False", "FALSE", "0", "no", "No", "NO"],
)
async def test_shutdown_notify_fires_when_env_falsy(env_value, monkeypatch):
    """When HERMES_SUPPRESS_SHUTDOWN_NOTIFY is absent or falsy, messages are sent."""
    if env_value is None:
        monkeypatch.delenv("HERMES_SUPPRESS_SHUTDOWN_NOTIFY", raising=False)
    else:
        monkeypatch.setenv("HERMES_SUPPRESS_SHUTDOWN_NOTIFY", env_value)

    runner, adapter = make_restart_runner()
    source = make_restart_source(chat_id="222")
    session_key = build_session_key(source)

    runner._running_agents[session_key] = object()
    runner._cache_session_source(session_key, source)
    adapter.send = AsyncMock(return_value=SendResult(success=True, message_id="msg"))

    await runner._notify_active_sessions_of_shutdown()

    adapter.send.assert_awaited_once()
    call_args = adapter.send.call_args
    assert "222" == call_args[0][0]
    assert "shutting down" in call_args[0][1].lower() or "⚠️" in call_args[0][1]
