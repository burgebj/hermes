"""Unit tests for feishu_docx_tool handlers.

Coverage:
  - feishu_docx_create
  - feishu_docx_update
  - feishu_docx_get_blocks

All SDK calls are mocked via FeishuClient.for_user — no network I/O.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_docx_tool  # noqa: F401 — triggers registry.register at import time

from tools.feishu_oapi_client import NeedAuthorizationError
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
# feishu_docx_create
# ---------------------------------------------------------------------------

class TestDocxCreate(unittest.TestCase):
    """Tests for feishu_docx_create handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_docx_create")
        self.assertIsNotNone(entry, "feishu_docx_create must be registered")
        return entry.handler

    def test_returns_document_id_and_title_on_success(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0,
            "ok",
            {"document": {"document_id": "doxcnABC123", "title": "My Doc"}},
        )

        with patch("tools.feishu_docx_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(handler({"title": "My Doc", "folder_token": "fldXYZ"}))

        self.assertNotIn("error", result)
        self.assertEqual(result["document_id"], "doxcnABC123")
        self.assertEqual(result["title"], "My Doc")

    def test_returns_error_when_uat_not_available(self):
        handler = self._get_handler()
        with patch(
            "tools.feishu_docx_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError(reason="no token"),
        ):
            result = json.loads(handler({}))

        self.assertIn("error", result)
        self.assertIn("authorization", result["error"].lower())

    def test_returns_error_on_non_zero_api_code(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (403, "permission denied", {})

        with patch("tools.feishu_docx_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(handler({"title": "Fail Doc"}))

        self.assertIn("error", result)


# ---------------------------------------------------------------------------
# feishu_docx_update
# ---------------------------------------------------------------------------

class TestDocxUpdate(unittest.TestCase):
    """Tests for feishu_docx_update handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_docx_update")
        self.assertIsNotNone(entry, "feishu_docx_update must be registered")
        return entry.handler

    def test_returns_updated_block_on_success(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0,
            "ok",
            {"block": {"block_id": "blk001", "block_type": 2}},
        )

        with patch("tools.feishu_docx_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(handler({
                "document_id": "doxcnABC123",
                "block_id": "blk001",
                "update_body": {"update_text_elements": [{"text_run": {"content": "hello"}}]},
            }))

        self.assertNotIn("error", result)
        self.assertEqual(result["document_id"], "doxcnABC123")
        self.assertEqual(result["block_id"], "blk001")
        self.assertIn("block", result)
        self.assertEqual(mock_fc.do_request.call_args.args[0], "PATCH")

    def test_wraps_text_element_list_for_block_patch(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0,
            "ok",
            {"block": {"block_id": "blk001", "block_type": 2}},
        )

        with patch("tools.feishu_docx_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(handler({
                "document_id": "doxcnABC123",
                "block_id": "blk001",
                "update_body": {
                    "update_text_elements": [
                        {"text_run": {"content": "hello"}},
                    ],
                },
            }))

        self.assertNotIn("error", result)
        self.assertEqual(
            mock_fc.do_request.call_args.kwargs["body"],
            {"update_text_elements": {"elements": [{"text_run": {"content": "hello"}}]}},
        )

    def test_unwraps_llm_text_block_shape_for_block_patch(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0,
            "ok",
            {"block": {"block_id": "blk001", "block_type": 2}},
        )

        with patch("tools.feishu_docx_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(handler({
                "document_id": "doxcnABC123",
                "block_id": "blk001",
                "update_body": {
                    "update_text_elements": [
                        {
                            "elements": [{"text_run": {"content": "hello"}}],
                            "style": {"align": 1},
                        },
                    ],
                },
            }))

        self.assertNotIn("error", result)
        self.assertEqual(
            mock_fc.do_request.call_args.kwargs["body"],
            {"update_text_elements": {"elements": [{"text_run": {"content": "hello"}}]}},
        )

    def test_normalizes_index_text_element_shape_for_block_patch(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0,
            "ok",
            {"block": {"block_id": "blk001", "block_type": 2}},
        )

        with patch("tools.feishu_docx_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(handler({
                "document_id": "doxcnABC123",
                "block_id": "blk001",
                "update_body": {
                    "update_text_elements": [
                        {"index": 0, "text_element": {"content": "hello"}},
                    ],
                },
            }))

        self.assertNotIn("error", result)
        self.assertEqual(
            mock_fc.do_request.call_args.kwargs["body"],
            {
                "update_text_elements": {
                    "elements": [
                        {
                            "text_element_index": 0,
                            "text_run": {
                                "content": "hello",
                                "text_element_style": {
                                    "bold": False,
                                    "inline_code": False,
                                    "italic": False,
                                    "strikethrough": False,
                                    "underline": False,
                                },
                            },
                        },
                    ],
                },
            },
        )

    def test_root_block_text_update_creates_first_text_child(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0,
            "ok",
            {"children": [{"block_id": "blk_child", "block_type": 2}]},
        )

        with patch("tools.feishu_docx_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(handler({
                "document_id": "doxcnABC123",
                "block_id": "doxcnABC123",
                "update_body": {
                    "update_text_elements": [
                        {"text_run": {"content": "hello"}},
                    ],
                },
            }))

        self.assertNotIn("error", result)
        self.assertEqual(result["block_id"], "blk_child")
        self.assertEqual(mock_fc.do_request.call_args.args[0], "POST")
        self.assertEqual(
            mock_fc.do_request.call_args.args[1],
            "/open-apis/docx/v1/documents/doxcnABC123/blocks/doxcnABC123/children",
        )
        self.assertEqual(
            mock_fc.do_request.call_args.kwargs["body"],
            {
                "children": [
                    {
                        "block_type": 2,
                        "text": {
                            "elements": [{"text_run": {"content": "hello"}}],
                        },
                    }
                ],
            },
        )

    def test_returns_error_when_document_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({
            "block_id": "blk001",
            "update_body": {"update_text_elements": []},
        }))
        self.assertIn("error", result)

    def test_returns_error_when_block_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({
            "document_id": "doxcnABC123",
            "update_body": {"update_text_elements": []},
        }))
        self.assertIn("error", result)

    def test_returns_error_when_update_body_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({
            "document_id": "doxcnABC123",
            "block_id": "blk001",
        }))
        self.assertIn("error", result)

    def test_returns_error_when_uat_not_available(self):
        handler = self._get_handler()
        with patch(
            "tools.feishu_docx_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError(reason="no token"),
        ):
            result = json.loads(handler({
                "document_id": "doxcnABC123",
                "block_id": "blk001",
                "update_body": {"update_text_elements": []},
            }))
        self.assertIn("error", result)


# ---------------------------------------------------------------------------
# feishu_docx_get_blocks
# ---------------------------------------------------------------------------

class TestDocxGetBlocks(unittest.TestCase):
    """Tests for feishu_docx_get_blocks handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_docx_get_blocks")
        self.assertIsNotNone(entry, "feishu_docx_get_blocks must be registered")
        return entry.handler

    def test_returns_blocks_list_on_success(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0,
            "ok",
            {
                "items": [
                    {"block_id": "blk001", "block_type": 1},
                    {"block_id": "blk002", "block_type": 2},
                ],
                "has_more": False,
                "page_token": None,
            },
        )

        with patch("tools.feishu_docx_tool.FeishuClient.for_user", return_value=mock_fc):
            result = json.loads(handler({"document_id": "doxcnABC123", "page_size": 100}))

        self.assertNotIn("error", result)
        self.assertEqual(result["document_id"], "doxcnABC123")
        self.assertEqual(len(result["items"]), 2)
        self.assertFalse(result["has_more"])

    def test_returns_error_when_document_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({}))
        self.assertIn("error", result)

    def test_returns_error_when_uat_not_available(self):
        handler = self._get_handler()
        with patch(
            "tools.feishu_docx_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError(reason="no token"),
        ):
            result = json.loads(handler({"document_id": "doxcnABC123"}))
        self.assertIn("error", result)

    def test_schema_requires_document_id(self):
        entry = registry.get_entry("feishu_docx_get_blocks")
        req = entry.schema["parameters"].get("required", [])
        self.assertIn("document_id", req)


if __name__ == "__main__":
    unittest.main()
