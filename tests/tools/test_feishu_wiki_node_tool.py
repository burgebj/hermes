"""Tests for feishu_wiki_node_tool -- create_node, move_node, list_spaces."""

import importlib
import json
import unittest
from unittest.mock import MagicMock, patch

from tools.registry import registry, tool_error, tool_result

# Trigger registration
importlib.import_module("tools.feishu_wiki_node_tool")


def _make_fc(code=0, msg="success", data=None):
    """Build a mock FeishuClient whose do_request returns (code, msg, data)."""
    fc = MagicMock()
    fc.user_open_id = "ou_test_user"
    fc.do_request.return_value = (code, msg, data or {})
    return fc


class TestFeishuWikiNodeRegistration(unittest.TestCase):
    """Verify all three wiki node tools are registered under toolset feishu_wiki."""

    EXPECTED_TOOLS = [
        "feishu_wiki_create_node",
        "feishu_wiki_move_node",
        "feishu_wiki_list_spaces",
    ]

    def test_all_tools_registered(self):
        for name in self.EXPECTED_TOOLS:
            entry = registry.get_entry(name)
            self.assertIsNotNone(entry, f"{name} not registered")
            self.assertEqual(entry.toolset, "feishu_wiki", f"{name} wrong toolset")

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


class TestWikiCreateNode(unittest.TestCase):
    """Unit tests for feishu_wiki_create_node handler."""

    def _handler(self):
        return registry.get_entry("feishu_wiki_create_node").handler

    def test_missing_space_id_returns_error(self):
        result = json.loads(self._handler()({"obj_type": "docx"}))
        self.assertIn("error", result)
        self.assertIn("space_id", result.get("error", ""))

    def test_missing_obj_type_returns_error(self):
        result = json.loads(self._handler()({"space_id": "sp_abc"}))
        self.assertIn("error", result)
        self.assertIn("obj_type", result.get("error", ""))

    def test_successful_create_returns_node(self):
        node_data = {"node_token": "wik_tok_123", "obj_type": "docx", "title": "My Doc"}
        fc = _make_fc(code=0, data={"node": node_data})

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            result = json.loads(self._handler()({
                "space_id": "sp_abc",
                "obj_type": "docx",
                "title": "My Doc",
            }))

        self.assertNotIn("error", result, result)
        self.assertEqual(result["node"]["node_token"], "wik_tok_123")
        fc.do_request.assert_called_once()
        call_kwargs = fc.do_request.call_args
        self.assertEqual(call_kwargs[0][0], "POST")
        self.assertIn("sp_abc", call_kwargs[0][1])

    def test_api_error_propagated(self):
        fc = _make_fc(code=1234, msg="permission denied")

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            result = json.loads(self._handler()({
                "space_id": "sp_abc",
                "obj_type": "docx",
            }))

        self.assertIn("error", result)
        self.assertIn("1234", result.get("error", ""))

    def test_optional_parent_and_node_type_passed_in_body(self):
        node_data = {"node_token": "wik_tok_456"}
        fc = _make_fc(code=0, data={"node": node_data})

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            self._handler()({
                "space_id": "sp_abc",
                "obj_type": "sheet",
                "parent_node_token": "parent_tok",
                "node_type": "shortcut",
            })

        _, call_kwargs = fc.do_request.call_args
        body = call_kwargs.get("body", {})
        self.assertEqual(body.get("parent_node_token"), "parent_tok")
        self.assertEqual(body.get("node_type"), "shortcut")


class TestWikiMoveNode(unittest.TestCase):
    """Unit tests for feishu_wiki_move_node handler."""

    def _handler(self):
        return registry.get_entry("feishu_wiki_move_node").handler

    def test_missing_required_fields(self):
        for missing_key, args in [
            ("space_id", {"node_token": "nt", "target_parent_token": "tp"}),
            ("node_token", {"space_id": "sp", "target_parent_token": "tp"}),
            ("target_parent_token", {"space_id": "sp", "node_token": "nt"}),
        ]:
            result = json.loads(self._handler()(args))
            self.assertIn("error", result, f"Should fail when {missing_key} missing")
            self.assertIn(missing_key, result.get("error", ""))

    def test_successful_move(self):
        node_data = {"node_token": "nt_abc", "parent_node_token": "new_parent"}
        fc = _make_fc(code=0, data={"node": node_data})

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            result = json.loads(self._handler()({
                "space_id": "sp_abc",
                "node_token": "nt_abc",
                "target_parent_token": "new_parent",
            }))

        self.assertNotIn("error", result, result)
        self.assertEqual(result["node"]["node_token"], "nt_abc")
        call_args = fc.do_request.call_args
        self.assertIn("nt_abc", call_args[0][1])
        self.assertIn("move", call_args[0][1])

    def test_cross_space_move_sends_target_space_id(self):
        fc = _make_fc(code=0, data={"node": {}})

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            self._handler()({
                "space_id": "sp_src",
                "node_token": "nt_abc",
                "target_parent_token": "tp_abc",
                "target_space_id": "sp_dst",
            })

        _, call_kwargs = fc.do_request.call_args
        body = call_kwargs.get("body", {})
        self.assertEqual(body.get("target_space_id"), "sp_dst")

    def test_api_error_propagated(self):
        fc = _make_fc(code=500, msg="internal error")

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            result = json.loads(self._handler()({
                "space_id": "sp_abc",
                "node_token": "nt_abc",
                "target_parent_token": "tp_abc",
            }))

        self.assertIn("error", result)
        self.assertIn("500", result.get("error", ""))


class TestWikiListSpaces(unittest.TestCase):
    """Unit tests for feishu_wiki_list_spaces handler."""

    def _handler(self):
        return registry.get_entry("feishu_wiki_list_spaces").handler

    def test_returns_spaces_list(self):
        spaces = [
            {"space_id": "sp_1", "name": "Engineering"},
            {"space_id": "sp_2", "name": "Product"},
        ]
        fc = _make_fc(code=0, data={"items": spaces, "has_more": False})

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            result = json.loads(self._handler()({}))

        self.assertNotIn("error", result, result)
        self.assertEqual(len(result["spaces"]), 2)
        self.assertFalse(result["has_more"])

    def test_page_size_capped_at_50(self):
        fc = _make_fc(code=0, data={"items": [], "has_more": False})

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            self._handler()({"page_size": 999})

        _, call_kwargs = fc.do_request.call_args
        queries = dict(call_kwargs.get("queries", []))
        self.assertEqual(queries.get("page_size"), "50")

    def test_page_token_forwarded(self):
        fc = _make_fc(code=0, data={"items": [], "has_more": True, "page_token": "tok_next"})

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            result = json.loads(self._handler()({"page_token": "tok_curr"}))

        _, call_kwargs = fc.do_request.call_args
        queries = dict(call_kwargs.get("queries", []))
        self.assertIn("page_token", queries)
        self.assertTrue(result["has_more"])
        self.assertEqual(result["page_token"], "tok_next")

    def test_api_error_propagated(self):
        fc = _make_fc(code=403, msg="forbidden")

        with patch("tools.feishu_wiki_node_tool.FeishuClient.for_user", return_value=fc):
            result = json.loads(self._handler()({}))

        self.assertIn("error", result)
        self.assertIn("403", result.get("error", ""))

    def test_no_auth_returns_error(self):
        from tools.feishu_oapi_client import NeedAuthorizationError

        with patch(
            "tools.feishu_wiki_node_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError("ou_x", "token expired"),
        ):
            result = json.loads(self._handler()({}))

        self.assertIn("error", result)
        self.assertIn("authorization", result.get("error", "").lower())


if __name__ == "__main__":
    unittest.main()
