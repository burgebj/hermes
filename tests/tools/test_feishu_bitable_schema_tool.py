"""Unit tests for feishu_bitable_schema_tool -- delete_record and list_fields handlers.

All external calls are mocked — no network I/O.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_bitable_schema_tool  # noqa: F401 — triggers registration

from tools.feishu_oapi_client import NeedAuthorizationError
from tools.registry import registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_fc():
    """Return a mock FeishuClient with stubbed do_request."""
    fc = MagicMock()
    fc.access_token = "uat_test"
    fc.user_open_id = "ou_test"
    fc.app_id = "app_test"
    return fc


# ---------------------------------------------------------------------------
# feishu_bitable_delete_record
# ---------------------------------------------------------------------------

class TestBitableDeleteRecord(unittest.TestCase):
    """Tests for feishu_bitable_delete_record handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_bitable_delete_record")
        self.assertIsNotNone(entry)
        return entry.handler

    def test_returns_error_when_args_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"app_token": "tok", "table_id": "tbl"}))
        self.assertIn("error", result)

    def test_returns_error_when_uat_not_available(self):
        handler = self._get_handler()
        with patch(
            "tools.feishu_bitable_schema_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError(reason="no token"),
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
                "record_id": "rec_123",
            }))
        self.assertIn("error", result)
        self.assertIn("authorization", result["error"].lower())

    def test_success_returns_deleted_true(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (0, "success", {"deleted": True})
        with patch(
            "tools.feishu_bitable_schema_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
                "record_id": "rec_123",
            }))
        self.assertNotIn("error", result)
        self.assertTrue(result.get("deleted"))
        self.assertEqual(result.get("record_id"), "rec_123")

    def test_api_error_returns_tool_error(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (1254000, "not found", {})
        with patch(
            "tools.feishu_bitable_schema_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
                "record_id": "rec_bad",
            }))
        self.assertIn("error", result)


# ---------------------------------------------------------------------------
# feishu_bitable_list_fields
# ---------------------------------------------------------------------------

class TestBitableListFields(unittest.TestCase):
    """Tests for feishu_bitable_list_fields handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_bitable_list_fields")
        self.assertIsNotNone(entry)
        return entry.handler

    def test_returns_error_when_app_token_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"table_id": "tbl_xyz"}))
        self.assertIn("error", result)

    def test_returns_error_when_uat_not_available(self):
        handler = self._get_handler()
        with patch(
            "tools.feishu_bitable_schema_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError(reason="no token"),
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
            }))
        self.assertIn("error", result)
        self.assertIn("authorization", result["error"].lower())

    def test_success_returns_fields_list(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        sample_fields = [
            {"field_name": "Name", "type": 1, "property": {}},
            {"field_name": "Status", "type": 3, "property": {"options": []}},
        ]
        mock_fc.do_request.return_value = (0, "success", {
            "items": sample_fields,
            "has_more": False,
            "page_token": "",
            "total": 2,
        })
        with patch(
            "tools.feishu_bitable_schema_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
            }))
        self.assertIn("fields", result)
        self.assertEqual(len(result["fields"]), 2)
        self.assertEqual(result["fields"][0]["field_name"], "Name")
        self.assertFalse(result.get("has_more"))

    def test_api_error_returns_tool_error(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (1254000, "table not found", {})
        with patch(
            "tools.feishu_bitable_schema_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_bad",
            }))
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
