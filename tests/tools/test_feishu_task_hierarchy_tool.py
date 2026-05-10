"""Unit tests for feishu_task_hierarchy_tool -- mock-based, no network I/O."""

import json
import unittest
from unittest.mock import MagicMock, patch

import tools.feishu_task_hierarchy_tool  # noqa: F401 -- trigger registration

from tools.registry import registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_fc(access_token="uat_test", user_open_id="ou_test"):
    fc = MagicMock()
    fc.access_token = access_token
    fc.user_open_id = user_open_id
    fc.app_id = "app_test"
    return fc


def _make_sdk_response(code=0, msg="success", data=None):
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
# feishu_task_list_tasklists
# ---------------------------------------------------------------------------

class TestTaskListTasklists(unittest.TestCase):
    """Tests for feishu_task_list_tasklists handler."""

    def _get_handler(self):
        return registry.get_entry("feishu_task_list_tasklists").handler

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_list_tasklists_success(self, mock_for_user):
        fc = _make_mock_fc()
        mock_for_user.return_value = fc

        tasklist_data = {
            "items": [
                {"guid": "tl_guid_001", "name": "Work"},
                {"guid": "tl_guid_002", "name": "Personal"},
            ],
            "has_more": False,
        }
        fc.sdk.request.return_value = _make_sdk_response(data=tasklist_data)

        result = json.loads(self._get_handler()({}))
        self.assertNotIn("error", result)
        items = result.get("items", [])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["guid"], "tl_guid_001")

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_list_tasklists_api_error(self, mock_for_user):
        fc = _make_mock_fc()
        mock_for_user.return_value = fc
        fc.sdk.request.return_value = _make_sdk_response(code=99400, msg="bad request")

        result = json.loads(self._get_handler()({}))
        self.assertIn("error", result)
        self.assertIn("List tasklists failed", result["error"])


# ---------------------------------------------------------------------------
# feishu_task_create_tasklist
# ---------------------------------------------------------------------------

class TestTaskCreateTasklist(unittest.TestCase):
    """Tests for feishu_task_create_tasklist handler."""

    def _get_handler(self):
        return registry.get_entry("feishu_task_create_tasklist").handler

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_create_tasklist_success(self, mock_for_user):
        fc = _make_mock_fc()
        mock_for_user.return_value = fc

        created = {"tasklist": {"guid": "tl_new_001", "name": "Q2 Goals"}}
        fc.sdk.request.return_value = _make_sdk_response(data=created)

        result = json.loads(self._get_handler()({"name": "Q2 Goals"}))
        self.assertNotIn("error", result)
        self.assertIn("tasklist", result)
        self.assertEqual(result["tasklist"]["guid"], "tl_new_001")

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_create_tasklist_missing_name(self, mock_for_user):
        mock_for_user.return_value = _make_mock_fc()
        result = json.loads(self._get_handler()({}))
        self.assertIn("error", result)
        self.assertIn("name is required", result["error"])

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_create_tasklist_with_members(self, mock_for_user):
        fc = _make_mock_fc()
        mock_for_user.return_value = fc

        created = {"tasklist": {"guid": "tl_new_002", "name": "Team Sprint"}}
        fc.sdk.request.return_value = _make_sdk_response(data=created)

        args = {
            "name": "Team Sprint",
            "members": [{"id": "ou_member1", "type": "user"}],
        }
        result = json.loads(self._get_handler()(args))
        self.assertNotIn("error", result)
        self.assertIn("tasklist", result)


# ---------------------------------------------------------------------------
# feishu_task_list_sections
# ---------------------------------------------------------------------------

class TestTaskListSections(unittest.TestCase):
    """Tests for feishu_task_list_sections handler."""

    def _get_handler(self):
        return registry.get_entry("feishu_task_list_sections").handler

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_list_sections_success(self, mock_for_user):
        fc = _make_mock_fc()
        mock_for_user.return_value = fc

        sections_data = {
            "items": [
                {"guid": "sec_001", "name": "Backlog"},
                {"guid": "sec_002", "name": "In Progress"},
            ],
            "has_more": False,
        }
        fc.sdk.request.return_value = _make_sdk_response(data=sections_data)

        result = json.loads(self._get_handler()({"tasklist_guid": "tl_guid_001"}))
        self.assertNotIn("error", result)
        items = result.get("items", [])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[1]["name"], "In Progress")

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_list_sections_missing_guid(self, mock_for_user):
        mock_for_user.return_value = _make_mock_fc()
        result = json.loads(self._get_handler()({}))
        self.assertIn("error", result)
        self.assertIn("tasklist_guid is required", result["error"])

    def test_list_sections_declares_section_read_scope(self):
        self.assertEqual(
            tools.feishu_task_hierarchy_tool.TOOLS_METADATA["feishu_task_list_sections"]["scopes"],
            ["task:section:read"],
        )

    def test_list_sections_uses_resource_sections_endpoint(self):
        client = _make_mock_fc()
        with patch("tools.feishu_task_hierarchy_tool._get_user_client", return_value=(client, None)), \
             patch(
                 "tools.feishu_task_hierarchy_tool._do_request",
                 return_value=(0, "success", {"items": [], "has_more": False}),
             ) as mock_request:
            result = json.loads(self._get_handler()({"tasklist_guid": "tl_guid_001", "page_size": 20}))

        self.assertNotIn("error", result)
        self.assertEqual(mock_request.call_args.args[:3], (
            client,
            "GET",
            "/open-apis/task/v2/sections",
        ))
        self.assertEqual(
            mock_request.call_args.kwargs["queries"],
            [
                ("user_id_type", "open_id"),
                ("resource_type", "tasklist"),
                ("resource_id", "tl_guid_001"),
                ("page_size", "20"),
            ],
        )


# ---------------------------------------------------------------------------
# feishu_task_create_subtask
# ---------------------------------------------------------------------------

class TestTaskCreateSubtask(unittest.TestCase):
    """Tests for feishu_task_create_subtask handler."""

    def _get_handler(self):
        return registry.get_entry("feishu_task_create_subtask").handler

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_create_subtask_success(self, mock_for_user):
        fc = _make_mock_fc()
        mock_for_user.return_value = fc

        subtask = {"task": {"guid": "sub_task_001", "summary": "Write tests"}}
        fc.sdk.request.return_value = _make_sdk_response(data=subtask)

        args = {"task_guid": "parent_task_001", "summary": "Write tests"}
        result = json.loads(self._get_handler()(args))
        self.assertNotIn("error", result)
        self.assertIn("task", result)
        self.assertEqual(result["task"]["guid"], "sub_task_001")

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_create_subtask_missing_task_guid(self, mock_for_user):
        mock_for_user.return_value = _make_mock_fc()
        result = json.loads(self._get_handler()({"summary": "Do something"}))
        self.assertIn("error", result)
        self.assertIn("task_guid is required", result["error"])

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_create_subtask_missing_summary(self, mock_for_user):
        mock_for_user.return_value = _make_mock_fc()
        result = json.loads(self._get_handler()({"task_guid": "parent_001"}))
        self.assertIn("error", result)
        self.assertIn("summary is required", result["error"])

    @patch("tools.feishu_task_hierarchy_tool.FeishuClient.for_user")
    def test_create_subtask_with_due(self, mock_for_user):
        fc = _make_mock_fc()
        mock_for_user.return_value = fc

        subtask = {"task": {"guid": "sub_task_002", "summary": "Review PR"}}
        fc.sdk.request.return_value = _make_sdk_response(data=subtask)

        args = {
            "task_guid": "parent_002",
            "summary": "Review PR",
            "due": {"timestamp": "2026-05-10T18:00:00+08:00", "is_all_day": False},
        }
        result = json.loads(self._get_handler()(args))
        self.assertNotIn("error", result)
        self.assertIn("task", result)


# ---------------------------------------------------------------------------
# Registration smoke test
# ---------------------------------------------------------------------------

class TestHierarchyToolRegistration(unittest.TestCase):
    """Verify all four tools are registered under feishu_task toolset."""

    EXPECTED_TOOLS = [
        "feishu_task_list_tasklists",
        "feishu_task_create_tasklist",
        "feishu_task_list_sections",
        "feishu_task_create_subtask",
    ]

    def test_all_tools_registered(self):
        for name in self.EXPECTED_TOOLS:
            entry = registry.get_entry(name)
            self.assertIsNotNone(entry, f"{name} not registered")
            self.assertEqual(entry.toolset, "feishu_task", f"{name} wrong toolset")

    def test_schemas_valid(self):
        for name in self.EXPECTED_TOOLS:
            entry = registry.get_entry(name)
            schema = entry.schema
            self.assertEqual(schema["name"], name)
            self.assertIn("description", schema)
            self.assertEqual(schema["parameters"]["type"], "object")

    def test_handlers_callable(self):
        for name in self.EXPECTED_TOOLS:
            entry = registry.get_entry(name)
            self.assertTrue(callable(entry.handler))

    def test_tasklist_tools_declare_tasklist_scopes(self):
        from tools.feishu_oapi_client import TOOLS_METADATA

        self.assertEqual(
            TOOLS_METADATA["feishu_task_list_tasklists"]["scopes"],
            ["task:tasklist:read"],
        )
        self.assertEqual(
            TOOLS_METADATA["feishu_task_create_tasklist"]["scopes"],
            ["task:tasklist:write"],
        )


if __name__ == "__main__":
    unittest.main()
