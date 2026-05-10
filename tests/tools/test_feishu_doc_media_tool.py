"""Unit tests for feishu_doc_media_tool handlers.

Coverage:
  - feishu_doc_media_upload   -- success path, missing param, invalid parent_type,
                                  nonexistent file_path, auth error
  - feishu_doc_media_download -- success path (binary response), missing token,
                                  API error

All SDK / FeishuClient calls are mocked — no network I/O.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_doc_media_tool  # ensure registration runs

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
# feishu_doc_media_upload
# ---------------------------------------------------------------------------

class TestDocMediaUpload(unittest.TestCase):
    """Tests for feishu_doc_media_upload handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_doc_media_upload")
        return entry.handler

    def test_upload_success(self):
        """Success path: raw multipart upload returns file_token."""
        fc = _make_mock_fc()
        post_resp = MagicMock()
        post_resp.json.return_value = {"code": 0, "msg": "success", "data": {"file_token": "media_tok_abc"}}

        with patch("tools.feishu_doc_media_tool.FeishuClient.for_user", return_value=fc), \
             patch("tools.feishu_doc_media_tool.requests.post", return_value=post_resp) as mock_post:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
                tmp_path = tmp.name
            try:
                handler = self._get_handler()
                result = handler({
                    "file_name": "image.png",
                    "parent_type": "docx_image",
                    "parent_node": "doxcABC123",
                    "file_path": tmp_path,
                })
            finally:
                os.unlink(tmp_path)

        parsed = json.loads(result)
        self.assertNotIn("error", parsed)
        self.assertEqual(parsed["file_token"], "media_tok_abc")
        self.assertFalse(fc.sdk.drive.v1.media.upload_all.called)
        post_kwargs = mock_post.call_args.kwargs
        self.assertEqual(post_kwargs["data"]["parent_type"], "docx_image")
        self.assertEqual(post_kwargs["data"]["parent_node"], "doxcABC123")
        self.assertTrue(hasattr(post_kwargs["files"]["file"][1], "read"))

    def test_docx_image_document_parent_creates_block_uploads_and_patches(self):
        """docx_image with a document token performs the required three-step insert."""
        fc = _make_mock_fc()
        fc.do_request.side_effect = [
            (
                0,
                "success",
                {
                    "children": [
                        {"block_id": "doxcn_image_block", "block_type": 27, "image": {}}
                    ]
                },
            ),
            (
                0,
                "success",
                {
                    "blocks": [
                        {
                            "block_id": "doxcn_image_block",
                            "block_type": 27,
                            "image": {"token": "media_tok_inserted"},
                        }
                    ]
                },
            ),
        ]
        post_resp = MagicMock()
        post_resp.json.return_value = {"code": 0, "msg": "success", "data": {"file_token": "media_tok_inserted"}}

        with patch("tools.feishu_doc_media_tool.FeishuClient.for_user", return_value=fc), \
             patch("tools.feishu_doc_media_tool.requests.post", return_value=post_resp) as mock_post:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
                tmp_path = tmp.name
            try:
                handler = self._get_handler()
                result = handler({
                    "file_name": "image.png",
                    "parent_type": "docx_image",
                    "parent_node": "DocxParentToken123",
                    "file_path": tmp_path,
                })
            finally:
                os.unlink(tmp_path)

        parsed = json.loads(result)
        self.assertNotIn("error", parsed)
        self.assertEqual(parsed["file_token"], "media_tok_inserted")
        self.assertEqual(parsed["block_id"], "doxcn_image_block")
        create_call, patch_call = fc.do_request.call_args_list
        self.assertEqual(create_call.args[:2], (
            "POST",
            "/open-apis/docx/v1/documents/DocxParentToken123/blocks/DocxParentToken123/children",
        ))
        self.assertEqual(create_call.kwargs["body"], {"children": [{"block_type": 27, "image": {}}]})
        self.assertEqual(mock_post.call_args.kwargs["data"]["parent_node"], "doxcn_image_block")
        self.assertEqual(mock_post.call_args.kwargs["data"]["extra"], '{"drive_route_token":"DocxParentToken123"}')
        self.assertEqual(patch_call.args[:2], (
            "PATCH",
            "/open-apis/docx/v1/documents/DocxParentToken123/blocks/batch_update",
        ))
        self.assertEqual(
            patch_call.kwargs["body"],
            {"requests": [{"block_id": "doxcn_image_block", "replace_image": {"token": "media_tok_inserted", "align": 2}}]},
        )

    def test_upload_missing_file_name(self):
        """Missing file_name returns tool_error immediately without calling API."""
        handler = self._get_handler()
        result = handler({
            "parent_type": "docx_image",
            "parent_node": "doxcABC123",
            "file_path": "/tmp/x.png",
        })
        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("file_name", parsed["error"])

    def test_upload_invalid_parent_type(self):
        """Invalid parent_type returns tool_error listing valid values."""
        handler = self._get_handler()
        result = handler({
            "file_name": "img.png",
            "parent_type": "invalid_type",
            "parent_node": "doxcABC123",
            "file_path": "/tmp/x.png",
        })
        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("parent_type", parsed["error"])

    def test_upload_nonexistent_file_path(self):
        """Nonexistent file_path returns tool_error without calling API."""
        fc = _make_mock_fc()
        with patch("tools.feishu_doc_media_tool.FeishuClient.for_user", return_value=fc):
            handler = self._get_handler()
            result = handler({
                "file_name": "ghost.png",
                "parent_type": "docx_image",
                "parent_node": "doxcABC123",
                "file_path": "/nonexistent/path/ghost.png",
            })
        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("file_path", parsed["error"])

    def test_upload_auth_error(self):
        """NeedAuthorizationError from for_user surfaces as tool_error."""
        with patch(
            "tools.feishu_doc_media_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError("ou_x", "token expired"),
        ):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(b"data")
                tmp_path = tmp.name
            try:
                handler = self._get_handler()
                result = handler({
                    "file_name": "img.png",
                    "parent_type": "docx_image",
                    "parent_node": "doxcABC123",
                    "file_path": tmp_path,
                })
            finally:
                os.unlink(tmp_path)

        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("authorization", parsed["error"].lower())

    def test_upload_api_error(self):
        """Non-zero Feishu code from API surfaces as tool_error."""
        fc = _make_mock_fc()
        post_resp = MagicMock()
        post_resp.json.return_value = {"code": 99991672, "msg": "scope missing", "data": {}}

        with patch("tools.feishu_doc_media_tool.FeishuClient.for_user", return_value=fc), \
             patch("tools.feishu_doc_media_tool.requests.post", return_value=post_resp):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(b"data")
                tmp_path = tmp.name
            try:
                handler = self._get_handler()
                result = handler({
                    "file_name": "img.png",
                    "parent_type": "sheet_image",
                    "parent_node": "sheetXYZ",
                    "file_path": tmp_path,
                })
            finally:
                os.unlink(tmp_path)

        parsed = json.loads(result)
        self.assertIn("error", parsed)


# ---------------------------------------------------------------------------
# feishu_doc_media_download
# ---------------------------------------------------------------------------

class TestDocMediaDownload(unittest.TestCase):
    """Tests for feishu_doc_media_download handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_doc_media_download")
        return entry.handler

    def test_download_success_png(self):
        """Binary PNG download returns summary with file_token, size, and mime."""
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        fc = _make_mock_fc()
        fc.sdk.request.return_value = _make_binary_sdk_response(png_content)

        with patch("tools.feishu_doc_media_tool.FeishuClient.for_user", return_value=fc):
            handler = self._get_handler()
            result = handler({"file_token": "media_tok_png"})

        parsed = json.loads(result)
        self.assertNotIn("error", parsed)
        self.assertEqual(parsed["file_token"], "media_tok_png")
        self.assertEqual(parsed["size"], len(png_content))
        self.assertEqual(parsed["mime"], "image/png")

    def test_download_missing_token(self):
        """Empty file_token returns tool_error immediately."""
        handler = self._get_handler()
        result = handler({"file_token": ""})
        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("file_token", parsed["error"])

    def test_download_api_error(self):
        """JSON error response from API surfaces as tool_error."""
        fc = _make_mock_fc()
        error_resp = MagicMock()
        error_resp.code = 403001
        error_resp.msg = "permission denied"
        raw = MagicMock()
        raw.content = json.dumps({"code": 403001, "msg": "permission denied", "data": {}}).encode()
        error_resp.raw = raw
        fc.sdk.request.return_value = error_resp

        with patch("tools.feishu_doc_media_tool.FeishuClient.for_user", return_value=fc):
            handler = self._get_handler()
            result = handler({"file_token": "media_bad"})

        parsed = json.loads(result)
        self.assertIn("error", parsed)

    def test_download_auth_error(self):
        """NeedAuthorizationError from for_user surfaces as tool_error."""
        with patch(
            "tools.feishu_doc_media_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError("ou_y", "no token"),
        ):
            handler = self._get_handler()
            result = handler({"file_token": "media_tok_xyz"})

        parsed = json.loads(result)
        self.assertIn("error", parsed)
        self.assertIn("authorization", parsed["error"].lower())


# ---------------------------------------------------------------------------
# Registration sanity
# ---------------------------------------------------------------------------

class TestRegistration(unittest.TestCase):
    """Verify both tools are registered under toolset feishu_drive_file."""

    def test_all_tools_registered(self):
        for name in ("feishu_doc_media_upload", "feishu_doc_media_download"):
            entry = registry.get_entry(name)
            self.assertIsNotNone(entry, f"{name} not registered")
            self.assertEqual(entry.toolset, "feishu_drive_file")


if __name__ == "__main__":
    unittest.main()
