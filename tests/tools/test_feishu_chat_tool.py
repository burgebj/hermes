"""Unit tests for Feishu chat info tools."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import tools.feishu_chat_tool  # trigger registration
from gateway.session_context import clear_session_vars, set_session_vars
from tools.registry import registry


def _make_mock_fc():
    fc = MagicMock()
    fc.access_token = "uat_test"
    fc.user_open_id = "ou_test"
    fc.app_id = "app_test"
    return fc


def test_chat_get_info_defaults_to_current_session_chat_id():
    entry = registry.get_entry("feishu_chat_get_info")
    mock_fc = _make_mock_fc()
    mock_fc.do_request.return_value = (
        0,
        "success",
        {"chat_id": "oc_current", "name": "Current Group"},
    )
    tokens = set_session_vars(platform="feishu", chat_id="oc_current")
    try:
        with patch("tools.feishu_chat_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(entry.handler({}))
    finally:
        clear_session_vars(tokens)

    assert result["chat_id"] == "oc_current"
    mock_fc.do_request.assert_called_once()
    assert mock_fc.do_request.call_args.kwargs["paths"] == {"chat_id": "oc_current"}


def test_chat_list_members_defaults_to_current_session_chat_id():
    entry = registry.get_entry("feishu_chat_list_members")
    mock_fc = _make_mock_fc()
    mock_fc.do_request.return_value = (
        0,
        "success",
        {"items": [{"member_id": "ou_user"}]},
    )
    tokens = set_session_vars(platform="feishu", chat_id="oc_current")
    try:
        with patch("tools.feishu_chat_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(entry.handler({}))
    finally:
        clear_session_vars(tokens)

    assert result["items"][0]["member_id"] == "ou_user"
    mock_fc.do_request.assert_called_once()
    assert mock_fc.do_request.call_args.kwargs["paths"] == {"chat_id": "oc_current"}


def test_chat_schemas_make_chat_id_optional_for_current_chat():
    get_schema = registry.get_entry("feishu_chat_get_info").schema
    list_schema = registry.get_entry("feishu_chat_list_members").schema

    assert "chat_id" not in get_schema["parameters"].get("required", [])
    assert "chat_id" not in list_schema["parameters"].get("required", [])
