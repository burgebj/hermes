"""Unit tests for feishu_im_history_tool handlers.

Covers:
  - feishu_im_get_messages
  - feishu_im_get_thread_messages
  - feishu_im_fetch_resource

All SDK calls are mocked — no network I/O.
"""

import json
import sys
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_im_history_tool  # ensure registration side-effects run

from tools.registry import registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_fc(access_token="uat_test", user_open_id="ou_test"):
    """Return a mock FeishuClient with stubbed sdk."""
    fc = MagicMock()
    fc.access_token = access_token
    fc.user_open_id = user_open_id
    fc.app_id = "app_test"
    return fc


def _make_sdk_response(code=0, content=b"binary_data", content_type="image/jpeg"):
    """Return a mock SDK response with raw binary content."""
    resp = MagicMock()
    resp.code = code
    resp.msg = "success" if code == 0 else "error"
    raw = MagicMock()
    raw.content = content
    raw.headers = {"content-type": content_type}
    resp.raw = raw
    return resp


def _parse(raw_str):
    """Parse tool handler output into dict."""
    return json.loads(raw_str)


def _is_error(result: dict) -> bool:
    """Return True if result contains an 'error' key (tool_error format)."""
    return "error" in result


def _is_success(result: dict) -> bool:
    """Return True if result does NOT contain an 'error' key."""
    return "error" not in result


# ---------------------------------------------------------------------------
# TestImGetMessages
# ---------------------------------------------------------------------------

class TestImGetMessages(unittest.TestCase):
    """Tests for feishu_im_get_messages handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_im_get_messages")
        return entry.handler

    def test_missing_chat_id_returns_error(self):
        handler = self._get_handler()
        result = _parse(handler({}))
        self.assertTrue(_is_error(result))
        self.assertIn("chat_id", result["error"])

    def test_success_returns_messages(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        messages = [{"message_id": "om_001", "body": {"content": '{"text":"hello"}'}}]
        mock_fc.do_request.return_value = (0, "success", {
            "items": messages, "has_more": False, "page_token": None
        })

        with patch("tools.feishu_im_history_tool._get_fc", return_value=mock_fc):
            result = _parse(handler({"chat_id": "oc_abc123", "page_size": 10}))

        self.assertTrue(_is_success(result))
        self.assertEqual(result["messages"], messages)
        self.assertFalse(result["has_more"])
        # Verify query params passed correctly
        call_kwargs = mock_fc.do_request.call_args
        queries = call_kwargs[1]["queries"]
        query_dict = dict(queries)
        self.assertEqual(query_dict["container_id_type"], "chat")
        self.assertEqual(query_dict["container_id"], "oc_abc123")

    def test_api_error_returns_tool_error(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (100004, "chat not found", {})

        with patch("tools.feishu_im_history_tool._get_fc", return_value=mock_fc):
            result = _parse(handler({"chat_id": "oc_notexist"}))

        self.assertTrue(_is_error(result))
        self.assertIn("Get messages failed", result["error"])


# ---------------------------------------------------------------------------
# TestImGetThreadMessages
# ---------------------------------------------------------------------------

class TestImGetThreadMessages(unittest.TestCase):
    """Tests for feishu_im_get_thread_messages handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_im_get_thread_messages")
        return entry.handler

    def test_missing_thread_id_returns_error(self):
        handler = self._get_handler()
        result = _parse(handler({}))
        self.assertTrue(_is_error(result))
        self.assertIn("thread_id", result["error"])

    def test_success_returns_thread_messages(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        messages = [
            {"message_id": "om_t01", "body": {"content": '{"text":"reply1"}'}},
            {"message_id": "om_t02", "body": {"content": '{"text":"reply2"}'}},
        ]
        mock_fc.do_request.return_value = (0, "success", {
            "items": messages, "has_more": True, "page_token": "tok_next"
        })

        with patch("tools.feishu_im_history_tool._get_fc", return_value=mock_fc):
            result = _parse(handler({"thread_id": "thr_xyz", "page_size": 20}))

        self.assertTrue(_is_success(result))
        self.assertEqual(len(result["messages"]), 2)
        self.assertTrue(result["has_more"])
        self.assertEqual(result["page_token"], "tok_next")
        # Verify container_id_type=thread
        call_kwargs = mock_fc.do_request.call_args
        queries = call_kwargs[1]["queries"]
        query_dict = dict(queries)
        self.assertEqual(query_dict["container_id_type"], "thread")
        self.assertEqual(query_dict["container_id"], "thr_xyz")

    def test_api_error_propagated(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (230002, "thread not found", {})

        with patch("tools.feishu_im_history_tool._get_fc", return_value=mock_fc):
            result = _parse(handler({"thread_id": "thr_bad"}))

        self.assertTrue(_is_error(result))
        self.assertIn("Get thread messages failed", result["error"])


# ---------------------------------------------------------------------------
# TestImFetchResource
# ---------------------------------------------------------------------------

def _patch_lark_for_fetch(mock_fc, binary_content=b"\xff\xd8\xff" + b"\x00" * 100):
    """Patch lark_oapi imports and sdk.request for fetch_resource tests.

    Returns a context manager stack (use as: with _patch_lark_for_fetch(...) as ctx).
    Actually returns a tuple of (mock_response, patch objects) — call within
    a manual with-block using ExitStack or nesting.
    """
    mock_response = _make_sdk_response(code=0, content=binary_content)
    mock_fc.sdk.request.return_value = mock_response

    mock_builder = MagicMock()
    for method in ("http_method", "uri", "token_types", "paths", "queries", "build"):
        getattr(mock_builder, method).return_value = mock_builder

    mock_base_request_cls = MagicMock()
    mock_base_request_cls.builder.return_value = mock_builder

    mock_request_option = MagicMock()
    mock_request_option.builder.return_value.user_access_token.return_value.build.return_value = MagicMock()

    mock_http_method = MagicMock()

    mock_lark_module = MagicMock()
    mock_lark_module.AccessTokenType = MagicMock()
    mock_lark_module.RequestOption = mock_request_option

    patched_modules = {
        "lark_oapi": mock_lark_module,
        "lark_oapi.core": MagicMock(),
        "lark_oapi.core.enum": MagicMock(HttpMethod=mock_http_method),
        "lark_oapi.core.model": MagicMock(),
        "lark_oapi.core.model.base_request": MagicMock(BaseRequest=mock_base_request_cls),
    }
    return mock_response, patched_modules


class TestImFetchResource(unittest.TestCase):
    """Tests for feishu_im_fetch_resource handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_im_fetch_resource")
        return entry.handler

    def test_missing_message_id_returns_error(self):
        handler = self._get_handler()
        result = _parse(handler({"file_key": "fk_abc"}))
        self.assertTrue(_is_error(result))
        self.assertIn("message_id", result["error"])

    def test_missing_file_key_returns_error(self):
        handler = self._get_handler()
        result = _parse(handler({"message_id": "om_abc"}))
        self.assertTrue(_is_error(result))
        self.assertIn("file_key", result["error"])

    def test_invalid_type_returns_error(self):
        handler = self._get_handler()
        result = _parse(handler({
            "message_id": "om_abc", "file_key": "fk_abc", "type": "video"
        }))
        self.assertTrue(_is_error(result))
        self.assertIn("type", result["error"])

    def test_success_returns_metadata_summary(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        binary_content = b"\xff\xd8\xff" + b"\x00" * 1024

        mock_response, patched_modules = _patch_lark_for_fetch(mock_fc, binary_content)

        saved = {}
        for k, v in patched_modules.items():
            saved[k] = sys.modules.get(k)
            sys.modules[k] = v

        try:
            with patch("tools.feishu_im_history_tool._get_fc", return_value=mock_fc):
                result = _parse(handler({
                    "message_id": "om_abc123",
                    "file_key": "fk_img001",
                    "type": "image",
                }))
        finally:
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v

        self.assertTrue(_is_success(result))
        self.assertEqual(result["resource_id"], "fk_img001")
        self.assertEqual(result["size"], len(binary_content))
        self.assertIn("mime", result)
