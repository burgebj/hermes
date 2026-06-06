import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tools import telegram_group_ops_tool as tool


def _run_tool(args):
    return json.loads(asyncio.run(tool.telegram_group_ops_tool(args)))


def _patch_config(monkeypatch, bot):
    monkeypatch.setattr(
        tool,
        "_telegram_config",
        lambda: (
            None,
            SimpleNamespace(token="test-token"),
            None,
        ),
    )
    monkeypatch.setattr(tool, "_make_bot", lambda _token: bot)


def _bot_with_member(member):
    bot = SimpleNamespace()
    bot.get_me = AsyncMock(return_value=SimpleNamespace(id=42, username="hermes_bot"))
    bot.get_chat_member = AsyncMock(return_value=member)
    return bot


def test_parse_target_accepts_group_and_topic():
    assert tool._parse_target("telegram:-1001234567890:17585") == (-1001234567890, 17585)
    assert tool._parse_target("-444") == (-444, None)


@pytest.mark.parametrize(
    "target",
    [
        "",
        "telegram:123456",
        "telegram:-100123:0",
        "slack:-100123",
        "telegram:abc",
    ],
)
def test_parse_target_rejects_non_group_or_invalid_target(target):
    with pytest.raises(ValueError):
        tool._parse_target(target)


def test_validate_poll_args_bounds():
    question, options, open_period = tool._validate_poll_args(
        {
            "question": "Where should we meet?",
            "options": ["Cafe", "Office"],
            "open_period": 60,
        }
    )

    assert question == "Where should we meet?"
    assert options == ["Cafe", "Office"]
    assert open_period == 60


@pytest.mark.parametrize(
    "args,error",
    [
        ({"question": "", "options": ["A", "B"]}, "question is required"),
        ({"question": "Q", "options": ["A"]}, "2 to 10"),
        ({"question": "Q", "options": ["A", ""]}, "must not be empty"),
        ({"question": "Q", "options": ["A", "B"], "open_period": 4}, "between 5 and 600"),
    ],
)
def test_validate_poll_args_rejects_invalid_inputs(args, error):
    with pytest.raises(ValueError, match=error):
        tool._validate_poll_args(args)


def test_send_poll_uses_explicit_topic(monkeypatch):
    bot = SimpleNamespace()
    bot.send_poll = AsyncMock(
        return_value=SimpleNamespace(
            message_id=77,
            poll=SimpleNamespace(id="poll-1"),
        )
    )
    _patch_config(monkeypatch, bot)

    result = _run_tool(
        {
            "action": "send_poll",
            "target": "telegram:-1001234567890:17585",
            "question": "Ship it?",
            "options": ["Yes", "No"],
            "open_period": 30,
        }
    )

    assert result["success"] is True
    assert result["message_id"] == 77
    assert result["poll_id"] == "poll-1"
    kwargs = bot.send_poll.await_args.kwargs
    assert kwargs["chat_id"] == -1001234567890
    assert kwargs["message_thread_id"] == 17585
    assert kwargs["question"] == "Ship it?"
    assert kwargs["options"] == ["Yes", "No"]


def test_send_poll_omits_general_topic_thread(monkeypatch):
    bot = SimpleNamespace()
    bot.send_poll = AsyncMock(
        return_value=SimpleNamespace(
            message_id=78,
            poll=SimpleNamespace(id="poll-2"),
        )
    )
    _patch_config(monkeypatch, bot)

    result = _run_tool(
        {
            "action": "send_poll",
            "target": "telegram:-1001234567890:1",
            "question": "General topic?",
            "options": ["Yes", "No"],
        }
    )

    assert result["success"] is True
    assert "message_thread_id" not in bot.send_poll.await_args.kwargs


def test_stop_poll(monkeypatch):
    bot = SimpleNamespace()
    bot.stop_poll = AsyncMock(
        return_value=SimpleNamespace(
            id="poll-closed",
            is_closed=True,
            total_voter_count=12,
        )
    )
    _patch_config(monkeypatch, bot)

    result = _run_tool(
        {
            "action": "stop_poll",
            "target": "telegram:-1001234567890",
            "message_id": 99,
        }
    )

    assert result == {
        "success": True,
        "action": "stop_poll",
        "chat_id": "-1001234567890",
        "message_id": 99,
        "poll_id": "poll-closed",
        "is_closed": True,
        "total_voter_count": 12,
    }
    bot.stop_poll.assert_awaited_once_with(chat_id=-1001234567890, message_id=99)


def test_pin_message_checks_capability_before_pinning(monkeypatch):
    member = SimpleNamespace(status="administrator", can_pin_messages=True)
    bot = _bot_with_member(member)
    bot.pin_chat_message = AsyncMock(return_value=True)
    _patch_config(monkeypatch, bot)

    result = _run_tool(
        {
            "action": "pin_message",
            "target": "telegram:-1001234567890",
            "message_id": 12,
        }
    )

    assert result["success"] is True
    assert result["capabilities"]["can_pin_messages"] is True
    bot.get_chat_member.assert_awaited_once_with(chat_id=-1001234567890, user_id=42)
    bot.pin_chat_message.assert_awaited_once_with(
        chat_id=-1001234567890,
        message_id=12,
        disable_notification=True,
    )


def test_pin_message_stops_when_bot_cannot_pin(monkeypatch):
    member = SimpleNamespace(status="member", can_pin_messages=False)
    bot = _bot_with_member(member)
    bot.pin_chat_message = AsyncMock(return_value=True)
    _patch_config(monkeypatch, bot)

    result = _run_tool(
        {
            "action": "pin_message",
            "target": "telegram:-1001234567890",
            "message_id": 12,
        }
    )

    assert result["success"] is False
    assert "not allowed to pin" in result["error"]
    bot.pin_chat_message.assert_not_called()


def test_unpin_message_allows_optional_message_id(monkeypatch):
    member = SimpleNamespace(status="administrator", can_pin_messages=True)
    bot = _bot_with_member(member)
    bot.unpin_chat_message = AsyncMock(return_value=True)
    _patch_config(monkeypatch, bot)

    result = _run_tool(
        {
            "action": "unpin_message",
            "target": "telegram:-1001234567890",
        }
    )

    assert result["success"] is True
    bot.unpin_chat_message.assert_awaited_once_with(chat_id=-1001234567890)


def test_capabilities_reports_bot_permissions(monkeypatch):
    member = SimpleNamespace(
        status="administrator",
        can_pin_messages=True,
        can_manage_topics=False,
        can_manage_chat=True,
        can_delete_messages=False,
        can_restrict_members=False,
        can_promote_members=False,
        can_invite_users=True,
    )
    bot = _bot_with_member(member)
    _patch_config(monkeypatch, bot)

    result = _run_tool(
        {
            "action": "capabilities",
            "target": "telegram:-1001234567890",
        }
    )

    assert result["success"] is True
    assert result["bot_id"] == "42"
    assert result["bot_username"] == "hermes_bot"
    assert result["can_pin_messages"] is True
    assert result["can_manage_topics"] is False


def test_tool_errors_redact_bot_token(monkeypatch):
    bot = SimpleNamespace()
    _patch_config(monkeypatch, bot)
    token = "123456:" + "abcdefghijklmnopqrstuvwxyzABCDE"
    monkeypatch.setattr(
        tool,
        "_make_bot",
        lambda _token: (_ for _ in ()).throw(
            RuntimeError(f"failed with {token}")
        ),
    )

    result = _run_tool(
        {
            "action": "capabilities",
            "target": "telegram:-1001234567890",
        }
    )

    assert "123456:***" in result["error"]
    assert "abcdefghijklmnopqrstuvwxyzABCDE" not in result["error"]
