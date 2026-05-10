"""Unit tests for Feishu task tool handlers."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_task_tool  # ensure registry side-effects run

from tools.registry import registry


def _parse(raw: str) -> dict:
    return json.loads(raw)


def _make_mock_client():
    client = MagicMock()
    client.access_token = "uat_test"
    client.user_open_id = "ou_test"
    return client


class TestTaskAddComment(unittest.TestCase):
    def _get_handler(self):
        return registry.get_entry("feishu_task_add_comment").handler

    def test_add_comment_uses_comment_resource_api(self):
        client = _make_mock_client()
        with patch("tools.feishu_task_tool._get_user_client", return_value=(client, None)), \
             patch(
                 "tools.feishu_task_tool._do_request",
                 return_value=(0, "success", {"comment": {"comment_id": "cmt_1"}}),
             ) as mock_request:
            result = _parse(self._get_handler()({"task_id": "task_123", "content": "done"}))

        self.assertNotIn("error", result)
        self.assertEqual(result["data"], {"comment": {"comment_id": "cmt_1"}})
        self.assertEqual(mock_request.call_args.args[:3], (
            client,
            "POST",
            "/open-apis/task/v2/comments",
        ))
        self.assertEqual(
            mock_request.call_args.kwargs["body"],
            {
                "content": "done",
                "resource_type": "task",
                "resource_id": "task_123",
            },
        )
        self.assertEqual(mock_request.call_args.kwargs["queries"], [("user_id_type", "open_id")])

    def test_add_comment_declares_comment_write_scope(self):
        self.assertEqual(
            tools.feishu_task_tool.TOOLS_METADATA["feishu_task_add_comment"]["scopes"],
            ["task:comment:write"],
        )


if __name__ == "__main__":
    unittest.main()
