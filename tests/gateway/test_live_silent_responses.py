from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.config import Platform
from gateway.platforms.base import MessageEvent, MessageType
from gateway.response_filters import (
    SILENT_REPLY_TOKEN,
    normalize_live_gateway_response,
)
from gateway.run import GatewayRunner
from gateway.session import SessionSource


@pytest.mark.parametrize(
    ("raw_text", "expected"),
    [
        ("(No message)", ""),
        ("[SILENT]", ""),
        ("`(No reply)`", ""),
        ("**(No response generated)**", ""),
        ("(empty)", ""),
        ("[SILENT] means stay quiet", "[SILENT] means stay quiet"),
        ("No message received from Discord", "No message received from Discord"),
    ],
)
def test_normalize_live_gateway_response(raw_text, expected):
    assert normalize_live_gateway_response(raw_text) == expected


def test_normalize_live_gateway_response_preserves_failed_output():
    assert normalize_live_gateway_response("[SILENT]", failed=True) == "[SILENT]"


@pytest.mark.parametrize(
    "raw_text",
    [
        SILENT_REPLY_TOKEN,
        f"  {SILENT_REPLY_TOKEN}\n",
        SILENT_REPLY_TOKEN.lower(),
        f"**{SILENT_REPLY_TOKEN}**",
        f"({SILENT_REPLY_TOKEN})",
        f"`{SILENT_REPLY_TOKEN}`",
    ],
)
def test_canonical_silent_token_is_suppressed(raw_text):
    """The canonical NO_REPLY token must always be suppressed.

    Locks the control-token contract independently of how
    _canonicalize_live_gateway_response normalizes punctuation/case, so a
    future tweak to the canonicalizer can't silently start leaking the token
    into live chats.
    """
    assert normalize_live_gateway_response(raw_text) == ""


def test_canonical_silent_token_survives_when_failed():
    """A real generation failure must never be silently swallowed.

    failed=True means the empty output is a model/transport failure, not an
    intentional silent turn, so the gateway keeps the sentinel for the
    user-facing error path rather than suppressing it.
    """
    assert normalize_live_gateway_response(SILENT_REPLY_TOKEN, failed=True) == SILENT_REPLY_TOKEN


def test_prose_mentioning_canonical_token_is_delivered():
    """Ordinary prose that merely mentions NO_REPLY must still be delivered."""
    text = f"Return {SILENT_REPLY_TOKEN} when you have nothing to add."
    assert normalize_live_gateway_response(text) == text


def _make_runner():
    runner = GatewayRunner.__new__(GatewayRunner)
    runner.config = MagicMock()
    runner.session_store = MagicMock()
    runner.hooks = SimpleNamespace(emit=AsyncMock())
    runner.adapters = {}
    runner._show_reasoning = False
    runner._session_db = None
    runner._set_session_env = MagicMock(return_value=[])
    runner._clear_session_env = MagicMock()
    runner._should_send_voice_reply = MagicMock(return_value=False)
    runner._deliver_media_from_response = AsyncMock()
    return runner


@pytest.mark.asyncio
async def test_handle_message_with_agent_suppresses_placeholder(monkeypatch):
    runner = _make_runner()

    session_entry = SimpleNamespace(
        session_id="sess-1",
        session_key="key-1",
        created_at=1,
        updated_at=2,
        was_auto_reset=False,
        last_prompt_tokens=0,
    )
    history = [{"role": "assistant", "content": "Earlier reply"}]

    runner.session_store.get_or_create_session.return_value = session_entry
    runner.session_store.load_transcript.return_value = history
    runner.session_store.has_any_sessions.return_value = True
    runner.session_store.append_to_transcript = MagicMock()
    runner.session_store.update_session = MagicMock()

    runner._run_agent = AsyncMock(
        return_value={
            "final_response": "(No message)",
            "messages": history,
            "api_calls": 1,
            "last_prompt_tokens": 0,
        }
    )
    # _handle_message_with_agent now guards against stale runs via
    # _is_session_run_current(session_key, generation); treat this run as current.
    runner._is_session_run_current = MagicMock(return_value=True)

    monkeypatch.setattr("gateway.run.build_session_context", lambda *_a, **_kw: {})
    monkeypatch.setattr("gateway.run.build_session_context_prompt", lambda *_a, **_kw: "")

    source = SessionSource(
        platform=Platform.LOCAL,
        chat_id="chat-1",
        user_id="user-1",
        user_name="tester",
    )
    event = MessageEvent(text="test", message_type=MessageType.TEXT, source=source)

    result = await runner._handle_message_with_agent(event, source, "key-1", 1)

    assert result == ""
    appended = [call.args[1] for call in runner.session_store.append_to_transcript.call_args_list]
    assert any(entry["role"] == "user" for entry in appended)
    assert not any(entry.get("content") == "(No message)" for entry in appended)


@pytest.mark.asyncio
async def test_handle_message_with_agent_empty_failure_surfaces_notice(monkeypatch):
    """A genuine empty-generation FAILURE must still surface a user notice.

    Regression guard for #13248: intentional silence is suppressed, but a real
    failure (api_calls>0, no text, not a silence marker) must NOT be silently
    swallowed by the intentional-silence bypass — the user needs to know the
    turn produced nothing so they can retry.
    """
    runner = _make_runner()

    session_entry = SimpleNamespace(
        session_id="sess-2",
        session_key="key-2",
        created_at=1,
        updated_at=2,
        was_auto_reset=False,
        last_prompt_tokens=0,
    )
    history = [{"role": "assistant", "content": "Earlier reply"}]

    runner.session_store.get_or_create_session.return_value = session_entry
    runner.session_store.load_transcript.return_value = history
    runner.session_store.has_any_sessions.return_value = True
    runner.session_store.append_to_transcript = MagicMock()
    runner.session_store.update_session = MagicMock()

    # Empty final_response with api_calls>0 and no silence marker == failure.
    runner._run_agent = AsyncMock(
        return_value={
            "final_response": "",
            "messages": history,
            "api_calls": 1,
            "last_prompt_tokens": 0,
        }
    )
    runner._is_session_run_current = MagicMock(return_value=True)

    monkeypatch.setattr("gateway.run.build_session_context", lambda *_a, **_kw: {})
    monkeypatch.setattr("gateway.run.build_session_context_prompt", lambda *_a, **_kw: "")

    source = SessionSource(
        platform=Platform.LOCAL,
        chat_id="chat-2",
        user_id="user-2",
        user_name="tester",
    )
    event = MessageEvent(text="test", message_type=MessageType.TEXT, source=source)

    result = await runner._handle_message_with_agent(event, source, "key-2", 1)

    # An empty failure is NOT intentional silence — the notice must be returned.
    assert result
    assert "no response was generated" in result
