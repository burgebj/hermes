"""Regression tests for QQBot inline approval authorization."""

import asyncio
import sys
import types
from unittest import mock

from gateway.config import PlatformConfig
from gateway.platforms.base import SendResult
from gateway.platforms.qqbot.adapter import QQAdapter
from gateway.platforms.qqbot.keyboards import parse_interaction_event


def _make_adapter(**extra):
    return QQAdapter(PlatformConfig(enabled=True, extra=extra))


def _approval_event(*, session_key: str, operator: str, group_openid: str = "group-1"):
    return parse_interaction_event({
        "id": "interaction-1",
        "chat_type": 1,
        "group_openid": group_openid,
        "group_member_openid": operator,
        "data": {
            "type": 11,
            "resolved": {
                "button_data": f"approve:{session_key}:allow-always",
                "button_id": "always",
            },
        },
    })


def _install_fake_approval(monkeypatch):
    calls = []
    fake = types.ModuleType("tools.approval")

    def resolve_gateway_approval(session_key, choice):
        calls.append((session_key, choice))
        return 1

    fake.resolve_gateway_approval = resolve_gateway_approval
    monkeypatch.setitem(sys.modules, "tools.approval", fake)
    return calls


def test_qqbot_group_approval_button_rejects_other_group_member(monkeypatch):
    calls = _install_fake_approval(monkeypatch)
    adapter = _make_adapter(app_id="a", client_secret="b")
    session_key = "agent:main:qqbot:group:group-1"
    adapter._approval_context[session_key] = {
        "operator": "victim-openid",
        "chat_id": "group-1",
        "chat_type": "group",
    }

    event = _approval_event(session_key=session_key, operator="attacker-openid")
    asyncio.run(adapter._default_interaction_dispatch(event))

    assert calls == []
    assert session_key in adapter._approval_context


def test_qqbot_group_approval_button_allows_bound_operator(monkeypatch):
    calls = _install_fake_approval(monkeypatch)
    adapter = _make_adapter(app_id="a", client_secret="b")
    session_key = "agent:main:qqbot:group:group-1"
    adapter._approval_context[session_key] = {
        "operator": "victim-openid",
        "chat_id": "group-1",
        "chat_type": "group",
    }

    event = _approval_event(session_key=session_key, operator="victim-openid")
    asyncio.run(adapter._default_interaction_dispatch(event))

    assert calls == [(session_key, "always")]
    assert session_key not in adapter._approval_context


def test_qqbot_send_exec_approval_binds_expected_operator_from_metadata():
    adapter = _make_adapter(app_id="a", client_secret="b")
    adapter._chat_type_map["group-1"] = "group"
    adapter.send_approval_request = mock.AsyncMock(
        return_value=SendResult(success=True, message_id="approval-msg")
    )

    result = asyncio.run(
        adapter.send_exec_approval(
            chat_id="group-1",
            command="rm -rf /tmp/example",
            session_key="agent:main:qqbot:group:group-1",
            metadata={"user_id": "victim-openid", "chat_type": "group"},
        )
    )

    assert result.success is True
    context = adapter._approval_context["agent:main:qqbot:group:group-1"]
    assert context["operator"] == "victim-openid"
    assert context["chat_id"] == "group-1"
    assert context["chat_type"] == "group"
    assert float(context["created_at"]) > 0
    adapter.send_approval_request.assert_awaited_once()


def test_qqbot_group_exec_approval_without_operator_falls_back_to_text():
    adapter = _make_adapter(app_id="a", client_secret="b")
    adapter._chat_type_map["group-1"] = "group"
    adapter.send_approval_request = mock.AsyncMock(
        return_value=SendResult(success=True, message_id="approval-msg")
    )

    result = asyncio.run(
        adapter.send_exec_approval(
            chat_id="group-1",
            command="rm -rf /tmp/example",
            session_key="agent:main:qqbot:group:group-1",
            metadata={},
        )
    )

    assert result.success is False
    assert result.retryable is False
    assert "requires an expected operator" in (result.error or "")
    assert adapter._approval_context == {}
    adapter.send_approval_request.assert_not_awaited()
