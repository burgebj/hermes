"""Unit tests for feishu_bitable_schema_full_tool -- field and view CRUD handlers.

All external calls are mocked — no network I/O.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_bitable_schema_full_tool  # noqa: F401 — triggers registration

from tools.feishu_oapi_client import NeedAuthorizationError
from tools.registry import registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_fc():
    """Return a mock FeishuClient with stubbed do_request and sdk.request."""
    fc = MagicMock()
    fc.access_token = "uat_test"
    fc.user_open_id = "ou_test"
    fc.app_id = "app_test"
    return fc


def _make_sdk_response(code=0, msg="success", data=None):
    """Return a mock SDK response suitable for _do_raw_request."""
    resp = MagicMock()
    resp.code = code
    resp.msg = msg
    # Simulate raw.content as a JSON-encoded body
    import json as _json
    body = {"code": code, "msg": msg, "data": data or {}}
    raw = MagicMock()
    raw.content = _json.dumps(body).encode()
    resp.raw = raw
    return resp


# ---------------------------------------------------------------------------
# feishu_bitable_create_field
# ---------------------------------------------------------------------------

class TestBitableCreateField(unittest.TestCase):
    """Tests for feishu_bitable_create_field handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_bitable_create_field")
        self.assertIsNotNone(entry)
        return entry.handler

    def test_returns_error_when_args_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"app_token": "tok", "table_id": "tbl"}))
        self.assertIn("error", result)

    def test_success_returns_field(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (0, "success", {
            "field": {"field_id": "fld_abc", "field_name": "Score", "type": 2}
        })
        with patch(
            "tools.feishu_bitable_schema_full_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
                "field_name": "Score",
                "type": 2,
            }))
        self.assertNotIn("error", result)
        self.assertIn("field", result)
        self.assertEqual(result["field"]["field_id"], "fld_abc")


# ---------------------------------------------------------------------------
# feishu_bitable_update_field
# ---------------------------------------------------------------------------

class TestBitableUpdateField(unittest.TestCase):
    """Tests for feishu_bitable_update_field handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_bitable_update_field")
        self.assertIsNotNone(entry)
        return entry.handler

    def test_returns_error_when_field_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({
            "app_token": "tok",
            "table_id": "tbl",
            "field_name": "Name",
            "type": 1,
        }))
        self.assertIn("error", result)

    def test_success_returns_updated_field(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.sdk.request.return_value = _make_sdk_response(
            data={"field": {"field_id": "fld_abc", "field_name": "NewName", "type": 1}}
        )
        with patch(
            "tools.feishu_bitable_schema_full_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
                "field_id": "fld_abc",
                "field_name": "NewName",
                "type": 1,
            }))
        self.assertNotIn("error", result)
        self.assertIn("field", result)
        self.assertEqual(result["field"]["field_name"], "NewName")


# ---------------------------------------------------------------------------
# feishu_bitable_delete_field
# ---------------------------------------------------------------------------

class TestBitableDeleteField(unittest.TestCase):
    """Tests for feishu_bitable_delete_field handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_bitable_delete_field")
        self.assertIsNotNone(entry)
        return entry.handler

    def test_returns_error_when_args_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"app_token": "tok", "table_id": "tbl"}))
        self.assertIn("error", result)

    def test_success_returns_deleted_true(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.sdk.request.return_value = _make_sdk_response(
            data={"deleted": True}
        )
        with patch(
            "tools.feishu_bitable_schema_full_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
                "field_id": "fld_abc",
            }))
        self.assertNotIn("error", result)
        self.assertTrue(result.get("deleted"))
        self.assertEqual(result.get("field_id"), "fld_abc")


# ---------------------------------------------------------------------------
# feishu_bitable_list_views
# ---------------------------------------------------------------------------

class TestBitableListViews(unittest.TestCase):
    """Tests for feishu_bitable_list_views handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_bitable_list_views")
        self.assertIsNotNone(entry)
        return entry.handler

    def test_returns_error_when_app_token_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"table_id": "tbl_xyz"}))
        self.assertIn("error", result)

    def test_success_returns_views_list(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        sample_views = [
            {"view_id": "vew_111", "view_name": "Grid View", "view_type": "grid"},
            {"view_id": "vew_222", "view_name": "Kanban View", "view_type": "kanban"},
        ]
        mock_fc.do_request.return_value = (0, "success", {
            "items": sample_views,
            "has_more": False,
            "page_token": "",
            "total": 2,
        })
        with patch(
            "tools.feishu_bitable_schema_full_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
            }))
        self.assertNotIn("error", result)
        self.assertIn("views", result)
        self.assertEqual(len(result["views"]), 2)
        self.assertEqual(result["views"][0]["view_type"], "grid")
        self.assertFalse(result.get("has_more"))


# ---------------------------------------------------------------------------
# feishu_bitable_create_view
# ---------------------------------------------------------------------------

class TestBitableCreateView(unittest.TestCase):
    """Tests for feishu_bitable_create_view handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_bitable_create_view")
        self.assertIsNotNone(entry)
        return entry.handler

    def test_returns_error_when_view_type_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({
            "app_token": "tok",
            "table_id": "tbl",
            "view_name": "My View",
        }))
        self.assertIn("error", result)

    def test_success_returns_view(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (0, "success", {
            "view": {"view_id": "vew_333", "view_name": "My Grid", "view_type": "grid"}
        })
        with patch(
            "tools.feishu_bitable_schema_full_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
                "view_name": "My Grid",
                "view_type": "grid",
            }))
        self.assertNotIn("error", result)
        self.assertIn("view", result)
        self.assertEqual(result["view"]["view_id"], "vew_333")


# ---------------------------------------------------------------------------
# feishu_bitable_delete_view
# ---------------------------------------------------------------------------

class TestBitableDeleteView(unittest.TestCase):
    """Tests for feishu_bitable_delete_view handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_bitable_delete_view")
        self.assertIsNotNone(entry)
        return entry.handler

    def test_returns_error_when_view_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"app_token": "tok", "table_id": "tbl"}))
        self.assertIn("error", result)

    def test_success_returns_deleted_true(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.sdk.request.return_value = _make_sdk_response(data={})
        with patch(
            "tools.feishu_bitable_schema_full_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "app_token": "app_abc",
                "table_id": "tbl_xyz",
                "view_id": "vew_444",
            }))
        self.assertNotIn("error", result)
        self.assertTrue(result.get("deleted"))
        self.assertEqual(result.get("view_id"), "vew_444")


if __name__ == "__main__":
    unittest.main()
