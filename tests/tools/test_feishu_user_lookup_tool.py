"""Unit tests for feishu_search_user and feishu_get_user handlers.

All SDK calls are mocked — no network I/O.
"""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_user_lookup_tool  # noqa: F401 — triggers registration

from tools.registry import registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_fc(access_token="uat_test", user_open_id="ou_test"):
    """Return a mock FeishuClient with stubbed do_request."""
    fc = MagicMock()
    fc.access_token = access_token
    fc.user_open_id = user_open_id
    fc.app_id = "app_test"
    return fc


# ---------------------------------------------------------------------------
# feishu_search_user
# ---------------------------------------------------------------------------

class TestSearchUser(unittest.TestCase):
    """Tests for feishu_search_user handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_search_user")
        return entry.handler

    def test_search_user_success(self):
        """Returns user list on successful API response."""
        users = [
            {"open_id": "ou_abc", "name": "Alice", "email": "alice@example.com"},
            {"open_id": "ou_def", "name": "Bob", "email": "bob@example.com"},
        ]
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0,
            "success",
            {"users": users, "has_more": False, "page_token": None},
        )

        with patch(
            "tools.feishu_user_lookup_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            handler = self._get_handler()
            result = handler({"query": "Alice", "page_size": 20})

        data = json.loads(result)
        self.assertNotIn("error", data)
        self.assertEqual(len(data["users"]), 2)
        self.assertEqual(data["users"][0]["open_id"], "ou_abc")
        mock_fc.do_request.assert_called_once()
        call_kwargs = mock_fc.do_request.call_args
        self.assertEqual(call_kwargs[0][0], "POST")
        self.assertIn("/open-apis/contact/v3/users/search", call_kwargs[0][1])
        self.assertEqual(call_kwargs.kwargs["body"], {"query": "Alice", "page_size": 20})
        self.assertEqual(call_kwargs.kwargs["queries"], [("user_id_type", "open_id")])

    def test_search_user_missing_query(self):
        """Returns error when query is empty."""
        handler = self._get_handler()
        result = handler({"query": ""})
        data = json.loads(result)
        self.assertIn("error", data)
        self.assertIn("query", data["error"].lower())

    def test_search_user_falls_back_to_current_user_when_directory_search_unauthorized(self):
        """Returns current user info when directory search lacks broader contact scopes."""
        mock_fc = _make_mock_fc(user_open_id="ou_self")
        mock_fc.do_request.side_effect = [
            (
                99991679,
                "Unauthorized. required one of these privileges: [contact:contact.base:readonly]",
                {},
            ),
            (
                0,
                "success",
                {
                    "name": "Alice",
                    "en_name": "Alice",
                    "open_id": "ou_self",
                    "user_id": "u_self",
                },
            ),
        ]

        with patch(
            "tools.feishu_user_lookup_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            handler = self._get_handler()
            result = handler({"query": "Alice", "page_size": 20})

        data = json.loads(result)
        self.assertNotIn("error", data)
        self.assertEqual(data["fallback"], "current_user_info")
        self.assertEqual(data["users"], [{"name": "Alice", "en_name": "Alice", "open_id": "ou_self", "user_id": "u_self"}])
        self.assertEqual(mock_fc.do_request.call_count, 2)
        fallback_call = mock_fc.do_request.call_args_list[1]
        self.assertEqual(fallback_call[0][0], "GET")
        self.assertEqual(fallback_call[0][1], "/open-apis/authen/v1/user_info")

    def test_search_user_falls_back_to_current_user_when_directory_search_param_errors(self):
        """Returns current user info when the directory endpoint rejects search."""
        mock_fc = _make_mock_fc(user_open_id="ou_self")
        mock_fc.do_request.side_effect = [
            (
                99992351,
                "The request you send is not a valid {open_id}",
                {},
            ),
            (
                0,
                "success",
                {
                    "name": "孙可",
                    "en_name": "孙可",
                    "open_id": "ou_self",
                    "user_id": "u_self",
                },
            ),
        ]

        with patch(
            "tools.feishu_user_lookup_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            handler = self._get_handler()
            result = handler({"query": "孙可", "page_size": 20})

        data = json.loads(result)
        self.assertNotIn("error", data)
        self.assertEqual(data["fallback"], "current_user_info")
        self.assertEqual(data["users"][0]["open_id"], "ou_self")


# ---------------------------------------------------------------------------
# feishu_get_user
# ---------------------------------------------------------------------------

class TestGetUser(unittest.TestCase):
    """Tests for feishu_get_user handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_get_user")
        return entry.handler

    def test_get_user_success(self):
        """Returns user detail on successful API response."""
        user_detail = {
            "open_id": "ou_abc",
            "name": "Alice",
            "email": "alice@example.com",
            "department_ids": ["od_dept1"],
        }
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0,
            "success",
            {"user": user_detail},
        )

        with patch(
            "tools.feishu_user_lookup_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            handler = self._get_handler()
            result = handler({"user_id": "ou_abc"})

        data = json.loads(result)
        self.assertNotIn("error", data)
        self.assertEqual(data["user"]["open_id"], "ou_abc")
        self.assertEqual(data["user"]["name"], "Alice")
        mock_fc.do_request.assert_called_once()
        call_kwargs = mock_fc.do_request.call_args
        self.assertEqual(call_kwargs[0][0], "GET")
        self.assertIn("/open-apis/contact/v3/users/", call_kwargs[0][1])

    def test_get_user_missing_user_id(self):
        """Returns error when user_id is empty."""
        handler = self._get_handler()
        result = handler({"user_id": ""})
        data = json.loads(result)
        self.assertIn("error", data)
        self.assertIn("user_id", data["error"].lower())


if __name__ == "__main__":
    unittest.main()
