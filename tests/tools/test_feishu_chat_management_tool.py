"""Unit tests for feishu_chat_management_tool -- mock-based, no network I/O."""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_chat_management_tool  # trigger registration

from tools.registry import registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_fc(access_token="uat_test", user_open_id="ou_test"):
    """Return a mock FeishuClient."""
    fc = MagicMock()
    fc.access_token = access_token
    fc.user_open_id = user_open_id
    fc.app_id = "app_test"
    return fc


def _make_do_request_response(code=0, msg="success", data=None):
    """Return (code, msg, data) tuple as do_request does."""
    return (code, msg, data or {})


def _make_sdk_response(code=0, msg="success", data=None):
    """Return a mock SDK response for sdk.request() calls."""
    resp = MagicMock()
    resp.code = code
    resp.msg = msg
    body = {"code": code, "msg": msg, "data": data or {}}
    raw = MagicMock()
    raw.content = json.dumps(body).encode()
    resp.raw = raw
    resp.data = data or {}
    return resp


# ---------------------------------------------------------------------------
# feishu_chat_create
# ---------------------------------------------------------------------------

class TestFeishuChatCreate(unittest.TestCase):
    """Tests for feishu_chat_create handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_chat_create")
        self.assertIsNotNone(entry, "feishu_chat_create not registered")
        return entry.handler

    def test_create_chat_success(self):
        """Create a chat and get back the chat_id."""
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = _make_do_request_response(
            code=0, msg="success", data={"chat_id": "oc_abc123"}
        )

        with patch("tools.feishu_chat_management_tool.FeishuClient.for_user", return_value=mock_fc):
            result = handler({"name": "Test Group", "user_id_list": ["ou_user1", "ou_user2"]})

        result_data = json.loads(result)
        self.assertNotIn("error", result_data)
        self.assertEqual(result_data["chat_id"], "oc_abc123")

    def test_create_chat_missing_name(self):
        """Returns error when name is missing."""
        handler = self._get_handler()
        result = handler({})
        result_data = json.loads(result)
        self.assertIn("error", result_data)
        self.assertIn("name", result_data["error"].lower())

    def test_create_chat_api_error(self):
        """Returns tool_error on non-zero Feishu API response."""
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = _make_do_request_response(
            code=99991234, msg="permission denied", data={}
        )

        with patch("tools.feishu_chat_management_tool.FeishuClient.for_user", return_value=mock_fc):
            result = handler({"name": "Fail Group"})

        result_data = json.loads(result)
        self.assertIn("error", result_data)
        self.assertIn("99991234", result_data["error"])


# ---------------------------------------------------------------------------
# feishu_chat_add_members
# ---------------------------------------------------------------------------

class TestFeishuChatAddMembers(unittest.TestCase):
    """Tests for feishu_chat_add_members handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_chat_add_members")
        self.assertIsNotNone(entry, "feishu_chat_add_members not registered")
        return entry.handler

    def test_add_members_success(self):
        """Add members and get empty invalid_id_list on success."""
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = _make_do_request_response(
            code=0, msg="success", data={"invalid_id_list": []}
        )

        with patch("tools.feishu_chat_management_tool.FeishuClient.for_user", return_value=mock_fc):
            result = handler({"chat_id": "oc_abc123", "id_list": ["ou_user1"]})

        result_data = json.loads(result)
        self.assertNotIn("error", result_data)
        self.assertEqual(result_data["invalid_id_list"], [])

    def test_add_members_missing_chat_id(self):
        """Returns error when chat_id is missing."""
        handler = self._get_handler()
        result = handler({"id_list": ["ou_user1"]})
        result_data = json.loads(result)
        self.assertIn("error", result_data)
        self.assertIn("chat_id", result_data["error"].lower())

    def test_add_members_empty_id_list(self):
        """Returns error when id_list is empty."""
        handler = self._get_handler()
        result = handler({"chat_id": "oc_abc123", "id_list": []})
        result_data = json.loads(result)
        self.assertIn("error", result_data)
        self.assertIn("id_list", result_data["error"].lower())


# ---------------------------------------------------------------------------
# feishu_chat_remove_members
# ---------------------------------------------------------------------------

class TestFeishuChatRemoveMembers(unittest.TestCase):
    """Tests for feishu_chat_remove_members handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_chat_remove_members")
        self.assertIsNotNone(entry, "feishu_chat_remove_members not registered")
        return entry.handler

    def test_remove_members_success(self):
        """Remove members and get empty invalid_id_list on success."""
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_sdk_resp = _make_sdk_response(code=0, msg="success", data={"invalid_id_list": []})
        mock_fc.sdk.request.return_value = mock_sdk_resp

        with patch("tools.feishu_chat_management_tool.FeishuClient.for_user", return_value=mock_fc):
            result = handler({"chat_id": "oc_abc123", "id_list": ["ou_user1"]})

        result_data = json.loads(result)
        self.assertNotIn("error", result_data)
        self.assertEqual(result_data["invalid_id_list"], [])

    def test_remove_members_missing_chat_id(self):
        """Returns error when chat_id is missing."""
        handler = self._get_handler()
        result = handler({"id_list": ["ou_user1"]})
        result_data = json.loads(result)
        self.assertIn("error", result_data)
        self.assertIn("chat_id", result_data["error"].lower())

    def test_remove_members_api_error(self):
        """Returns tool_error on non-zero Feishu API response."""
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_sdk_resp = _make_sdk_response(code=99991234, msg="not found", data={})
        mock_fc.sdk.request.return_value = mock_sdk_resp

        with patch("tools.feishu_chat_management_tool.FeishuClient.for_user", return_value=mock_fc):
            result = handler({"chat_id": "oc_abc123", "id_list": ["ou_user1"]})

        result_data = json.loads(result)
        self.assertIn("error", result_data)
        self.assertIn("99991234", result_data["error"])


if __name__ == "__main__":
    unittest.main()
