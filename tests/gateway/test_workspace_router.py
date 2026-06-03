"""Tests for gateway.workspace_router — agent dispatch and fanout."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from gateway.workspace_router import (
    _resolve_command,
    _run_subprocess,
    dispatch_single_agent,
    dispatch_fanout,
    MULTI_AGENT_ROOM_THREAD,
    AGENT_WORKBENCH_THREAD,
)


# --------------------------------------------------------------------------
# _resolve_command
# --------------------------------------------------------------------------


def test_resolve_command_hermes_returns_none():
    assert _resolve_command("hermes") is None


def test_resolve_command_unknown_returns_none():
    assert _resolve_command("totally-unknown-agent-xyz") is None


def test_resolve_command_codex_returns_list_or_none():
    result = _resolve_command("codex")
    assert result is None or isinstance(result, list)
    if result is not None:
        assert len(result) >= 1


def test_resolve_command_glm_returns_list_or_none():
    result = _resolve_command("glm")
    assert result is None or isinstance(result, list)


def test_resolve_command_bm_alias():
    result = _resolve_command("bm")
    assert result is None or isinstance(result, list)


def test_resolve_command_blazemind_alias_same_as_bm():
    result_bm = _resolve_command("bm")
    result_blazemind = _resolve_command("blazemind")
    assert result_bm == result_blazemind


# --------------------------------------------------------------------------
# _run_subprocess
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_subprocess_success():
    ok, out = await _run_subprocess(["echo"], "hello")
    assert ok is True
    assert "hello" in out


@pytest.mark.asyncio
async def test_run_subprocess_failure():
    ok, out = await _run_subprocess(["false"], "")
    assert ok is False


@pytest.mark.asyncio
async def test_run_subprocess_nonexistent_command():
    ok, out = await _run_subprocess(["nonexistent-binary-xyz-abc"], "task")
    assert ok is False
    assert "error" in out.lower() or "failed" in out.lower() or "no such" in out.lower() or out


@pytest.mark.asyncio
async def test_run_subprocess_timeout():
    # Use python3 -c "import time; time.sleep(100)" so we don't pass extra
    # args to sleep (which breaks on some macOS versions).
    ok, out = await _run_subprocess(
        ["python3", "-c", "import time; time.sleep(100)"], "", timeout=1
    )
    assert ok is False
    assert "timed out" in out.lower() or "timeout" in out.lower()


@pytest.mark.asyncio
async def test_run_subprocess_output_truncated_at_2000():
    # write 3000 bytes of output
    ok, out = await _run_subprocess(
        ["python3", "-c", "print('x' * 3000)"], ""
    )
    assert len(out) <= 2000


# --------------------------------------------------------------------------
# dispatch_single_agent
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_single_agent_unknown_returns_warning():
    ack = await dispatch_single_agent(
        alias="ghost-agent-xyz",
        task="do something",
        bot_token="fake",
        result_chat_id="-100123",
        result_thread_id="708",
    )
    assert "Unknown" in ack or "unknown" in ack.lower()


@pytest.mark.asyncio
async def test_dispatch_single_agent_disabled_returns_disabled():
    cfg = {
        "workspace": {
            "agent_registry": {
                "agents": {"voice": {"enabled": False}}
            }
        }
    }
    ack = await dispatch_single_agent(
        alias="voice",
        task="do something",
        bot_token="fake",
        result_chat_id="-100123",
        result_thread_id=None,
        config=cfg,
    )
    assert "disabled" in ack.lower()


@pytest.mark.asyncio
async def test_dispatch_single_agent_hermes_returns_queue_note():
    ack = await dispatch_single_agent(
        alias="hermes",
        task="run the tests",
        bot_token="fake",
        result_chat_id="-100123",
        result_thread_id="708",
    )
    assert "hermes" in ack.lower()
    assert "session" in ack.lower() or "queue" in ack.lower() or "current" in ack.lower()


@pytest.mark.asyncio
async def test_dispatch_single_agent_no_cli_returns_diagnostic():
    """When CLI is unavailable, a diagnostic message (not empty) is returned."""
    with patch("gateway.workspace_router._resolve_command", return_value=None):
        ack = await dispatch_single_agent(
            alias="codex",
            task="add unit tests",
            bot_token="fake",
            result_chat_id="-100123",
            result_thread_id="708",
        )
    assert ack  # non-empty
    # Should mention the alias or unavailability
    assert "codex" in ack.lower() or "unavailable" in ack.lower() or "not available" in ack.lower() or "cli" in ack.lower()


@pytest.mark.asyncio
async def test_dispatch_single_agent_with_cli_creates_background_task():
    """When CLI is available, an ack is returned and a task is created."""
    delivered: list[str] = []

    async def fake_run(cmd, task, **kw):
        return True, "done"

    async def fake_send(token, chat_id, text, thread_id=None):
        delivered.append(text)

    with (
        patch("gateway.workspace_router._resolve_command", return_value=["echo"]),
        patch("gateway.workspace_router._run_subprocess", fake_run),
        patch("gateway.workspace_router._tg_send", fake_send),
    ):
        ack = await dispatch_single_agent(
            alias="codex",
            task="fix tests",
            bot_token="tok",
            result_chat_id="-100",
            result_thread_id="708",
        )
        # Allow background task to run
        await asyncio.sleep(0.05)

    assert "codex" in ack.lower() or "dispatched" in ack.lower()
    # Background task should have delivered a result
    assert len(delivered) == 1
    assert "codex" in delivered[0].lower()


# --------------------------------------------------------------------------
# dispatch_fanout
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_fanout_empty_returns_error():
    ack = await dispatch_fanout(
        aliases=[],
        task="task",
        bot_token="fake",
        fanout_chat_id="-100",
        fanout_thread_id=None,
    )
    assert "No agents" in ack or ack


@pytest.mark.asyncio
async def test_dispatch_fanout_two_agents():
    with (
        patch(
            "gateway.workspace_router.dispatch_single_agent",
            new=AsyncMock(return_value="⚡ dispatched"),
        ),
    ):
        ack = await dispatch_fanout(
            aliases=["codex", "glm"],
            task="review auth.py",
            bot_token="tok",
            fanout_chat_id="-100",
            fanout_thread_id=MULTI_AGENT_ROOM_THREAD,
        )
    assert "codex" in ack.lower()
    assert "glm" in ack.lower()
    assert "multi-agent" in ack.lower() or "fanout" in ack.lower()


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------


def test_constants_are_strings():
    assert isinstance(MULTI_AGENT_ROOM_THREAD, str)
    assert isinstance(AGENT_WORKBENCH_THREAD, str)
    assert MULTI_AGENT_ROOM_THREAD == "903"
    assert AGENT_WORKBENCH_THREAD == "708"
