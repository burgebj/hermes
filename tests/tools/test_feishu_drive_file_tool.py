"""Unit tests for feishu_drive_file_tool handlers.

Coverage:
  - feishu_drive_list_files   -- success path + auth error branch
  - feishu_drive_upload_file  -- success path (do_request mocked entirely)
  - feishu_drive_download_file -- success path (binary response)

All SDK / FeishuClient calls are mocked — no network I/O.
"""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_drive_file_tool  # ensure registration runs

from tools.feishu_oapi_client import NeedAuthorizationError
from tools.registry import registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_fc(access_token="uat_test", user_open_id="ou_test"):
    """Return a mock FeishuClient with a stubbed sdk.request."""
    fc = MagicMock()
    fc.access_token = access_token
    fc.user_open_id = user_open_id
    fc.app_id = "app_test"
    return fc


def _make_sdk_response(code=0, msg="success", data=None):
    """Return a mock SDK response object with a raw.content JSON payload."""
    resp = MagicMock()
    resp.code = code
    resp.msg = msg
    body = {"code": code, "msg": msg, "data": data or {}}
    raw = MagicMock()
    raw.content = json.dumps(body).encode()
    resp.raw = raw
    resp.data = data or {}
    return resp


def _make_binary_sdk_response(content: bytes):
    """Return a mock SDK response simulating a successful binary download."""
    resp = MagicMock()
    resp.code = None
    resp.msg = ""
    raw = MagicMock()
    raw.content = content
    resp.raw = raw
    resp.data = {}
    return resp


# ---------------------------------------------------------------------------
# feishu_drive_list_files
# ---------------------------------------------------------------------------

class TestDriveListFiles(unittest.TestCase):
    """Tests for feishu_drive_list_files handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_drive_list_files")
        return entry.handler

    def test_list_files_success(self):
        """Success path: returns files list with has_more flag."""
        files = [
            {"name": "Report.docx", "token": "tok_abc", "type": "file"},
            {"name": "Data", "token": "tok_folder", "type": "folder"},
        ]
        fc = _make_mock_fc()
        fc.do_request.return_value = (0, "success", {"files": files, "has_more": False})

        with patch("tools.feishu_drive_file_tool.FeishuClient.for_user", return_value=fc):
            handler = self._get_handler()
            result = handler({"folder_token": "fldr_001", "page_size": 20})

        parsed = json.loads(result)
        self.assertNotIn("error", parsed)
        self.assertEqual(len(parsed["files"]), 2)
        self.assertFalse(parsed["has_more"])

    def test_list_files_auth_error(self):
        """NeedAuthorizationError from for_user surfaces as tool_error."""
        with patch(
            "tools.feishu_drive_file_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError("ou_x", "token expired"),
        ):
            handler = self._get_handler()
            result = handler({"folder_token": "fldr_001"})

        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("authorization", parsed.get("error", "").lower())

    def test_list_files_api_error(self):
        """Non-zero Feishu code surfaces as tool_error."""
        fc = _make_mock_fc()
        fc.do_request.return_value = (99991672, "scope missing", {})

        with patch("tools.feishu_drive_file_tool.FeishuClient.for_user", return_value=fc):
            handler = self._get_handler()
            result = handler({"folder_token": "fldr_001"})

        parsed = json.loads(result)
        self.assertIn("error", parsed)


# ---------------------------------------------------------------------------
# feishu_drive_upload_file
# ---------------------------------------------------------------------------

class TestDriveUploadFile(unittest.TestCase):
    """Tests for feishu_drive_upload_file handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_drive_upload_file")
        return entry.handler

    def test_upload_file_success(self):
        """Success path: raw multipart upload returns the file_token."""
        fc = _make_mock_fc()
        post_resp = MagicMock()
        post_resp.json.return_value = {"code": 0, "msg": "success", "data": {"file_token": "ftok_xyz789"}}

        with patch("tools.feishu_drive_file_tool.FeishuClient.for_user", return_value=fc), \
             patch("tools.feishu_drive_file_tool.requests.post", return_value=post_resp) as mock_post:
            # Create a real temp file so os.path.isfile passes
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                tmp.write(b"hello feishu drive")
                tmp_path = tmp.name
            try:
                handler = self._get_handler()
                result = handler({
                    "file_name": "hello.txt",
                    "parent_node": "fldr_parent",
                    "file_path": tmp_path,
                })
            finally:
                os.unlink(tmp_path)

        parsed = json.loads(result)
        self.assertNotIn("error", parsed)
        self.assertEqual(parsed["file_token"], "ftok_xyz789")
        self.assertFalse(fc.sdk.drive.v1.file.upload_all.called)
        post_kwargs = mock_post.call_args.kwargs
        self.assertEqual(post_kwargs["data"]["parent_node"], "fldr_parent")
        self.assertEqual(post_kwargs["data"]["parent_type"], "explorer")
        self.assertEqual(post_kwargs["headers"], {"Authorization": "Bearer uat_test"})
        self.assertTrue(hasattr(post_kwargs["files"]["file"][1], "read"))

    def test_upload_file_defaults_parent_node_to_root(self):
        """Natural-language uploads without a folder use an empty root parent_node."""
        fc = _make_mock_fc()
        post_resp = MagicMock()
        post_resp.json.return_value = {"code": 0, "msg": "success", "data": {"file_token": "ftok_root"}}

        with patch("tools.feishu_drive_file_tool.FeishuClient.for_user", return_value=fc), \
             patch("tools.feishu_drive_file_tool.requests.post", return_value=post_resp) as mock_post:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                tmp.write(b"hello root")
                tmp_path = tmp.name
            try:
                handler = self._get_handler()
                result = handler({
                    "file_name": "hello.txt",
                    "file_path": tmp_path,
                })
            finally:
                os.unlink(tmp_path)

        parsed = json.loads(result)
        self.assertNotIn("error", parsed)
        self.assertEqual(mock_post.call_args.kwargs["data"]["parent_node"], "")

    def test_upload_file_api_error_from_raw_response(self):
        """Non-zero raw upload response surfaces as tool_error."""
        fc = _make_mock_fc()
        post_resp = MagicMock()
        post_resp.json.return_value = {"code": 1061004, "msg": "forbidden.", "data": {}}

        with patch("tools.feishu_drive_file_tool.FeishuClient.for_user", return_value=fc), \
             patch("tools.feishu_drive_file_tool.requests.post", return_value=post_resp):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                tmp.write(b"hello root")
                tmp_path = tmp.name
            try:
                handler = self._get_handler()
                result = handler({
                    "file_name": "hello.txt",
                    "parent_node": "fldr_parent",
                    "file_path": tmp_path,
                })
            finally:
                os.unlink(tmp_path)

        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("1061004", parsed["error"])

    def test_upload_file_missing_param(self):
        """Missing required param file_name returns tool_error immediately."""
        handler = self._get_handler()
        result = handler({"parent_node": "fldr", "file_path": "/tmp/x.txt"})
        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("file_name", parsed.get("error", ""))

    def test_upload_file_nonexistent_path(self):
        """Nonexistent file_path returns tool_error without calling API."""
        fc = _make_mock_fc()
        with patch("tools.feishu_drive_file_tool.FeishuClient.for_user", return_value=fc):
            handler = self._get_handler()
            result = handler({
                "file_name": "ghost.txt",
                "parent_node": "fldr",
                "file_path": "/nonexistent/path/ghost.txt",
            })
        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("file_path", parsed.get("error", ""))


# ---------------------------------------------------------------------------
# feishu_drive_download_file
# ---------------------------------------------------------------------------

class TestDriveDownloadFile(unittest.TestCase):
    """Tests for feishu_drive_download_file handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_drive_download_file")
        return entry.handler

    def test_download_file_success(self):
        """Binary download returns summary with file_token, download_url, size."""
        binary_content = b"PDF content here" * 100
        fc = _make_mock_fc()
        fc.sdk.request.return_value = _make_binary_sdk_response(binary_content)

        with patch("tools.feishu_drive_file_tool.FeishuClient.for_user", return_value=fc):
            handler = self._get_handler()
            result = handler({"file_token": "ftok_abc123"})

        parsed = json.loads(result)
        self.assertNotIn("error", parsed)
        self.assertEqual(parsed["file_token"], "ftok_abc123")
        self.assertIn("/download", parsed["download_url"])
        self.assertEqual(parsed["size"], len(binary_content))

    def test_download_file_missing_token(self):
        """Empty file_token returns tool_error immediately."""
        handler = self._get_handler()
        result = handler({"file_token": ""})
        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("file_token", parsed.get("error", ""))

    def test_download_file_api_error(self):
        """JSON error response from API surfaces as tool_error."""
        fc = _make_mock_fc()
        error_resp = MagicMock()
        error_resp.code = 403001
        error_resp.msg = "permission denied"
        raw = MagicMock()
        raw.content = json.dumps({"code": 403001, "msg": "permission denied", "data": {}}).encode()
        error_resp.raw = raw
        fc.sdk.request.return_value = error_resp

        with patch("tools.feishu_drive_file_tool.FeishuClient.for_user", return_value=fc):
            handler = self._get_handler()
            result = handler({"file_token": "ftok_bad"})

        parsed = json.loads(result)
        self.assertIn("error", parsed)


# ---------------------------------------------------------------------------
# Registration sanity
# ---------------------------------------------------------------------------

class TestRegistration(unittest.TestCase):
    """Verify all three tools are registered under toolset feishu_drive_file."""

    def test_all_tools_registered(self):
        for name in (
            "feishu_drive_list_files",
            "feishu_drive_upload_file",
            "feishu_drive_download_file",
        ):
            entry = registry.get_entry(name)
            self.assertIsNotNone(entry, f"{name} not registered")
            self.assertEqual(entry.toolset, "feishu_drive_file")


if __name__ == "__main__":
    unittest.main()
