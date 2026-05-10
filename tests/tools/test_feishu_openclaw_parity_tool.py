"""OpenClaw action-gap parity tools.

These tests pin the tool bodies added for the 2026-05-03 OpenClaw action gap.
All Feishu calls are mocked; no network I/O.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import tools.feishu_openclaw_parity_tool  # noqa: F401

from tools.registry import _module_registers_tools, registry


EXPECTED_OPENCLAW_GAP_TOOLS = [
    "feishu_bitable_copy_app",
    "feishu_bitable_create_app",
    "feishu_bitable_get_app",
    "feishu_bitable_patch_app",
    "feishu_bitable_batch_create_tables",
    "feishu_bitable_create_table",
    "feishu_bitable_patch_table",
    "feishu_bitable_batch_create_records",
    "feishu_bitable_batch_delete_records",
    "feishu_bitable_batch_update_records",
    "feishu_bitable_get_view",
    "feishu_bitable_patch_view",
    "feishu_calendar_get_calendar",
    "feishu_calendar_primary_calendar",
    "feishu_calendar_delete_event",
    "feishu_calendar_update_event",
    "feishu_calendar_reply_event",
    "feishu_calendar_search_events",
    "feishu_chat_search",
    "feishu_doc_create_markdown",
    "feishu_doc_patch_comment",
    "feishu_drive_copy_file",
    "feishu_drive_delete_file",
    "feishu_drive_get_file_meta",
    "feishu_drive_move_file",
    "feishu_doc_fetch_markdown",
    "feishu_get_user_basic_batch",
    "feishu_im_search_messages",
    "feishu_sheet_create",
    "feishu_sheet_export",
    "feishu_sheet_find",
    "feishu_task_agent_register",
    "feishu_task_agent_update_profile",
    "feishu_task_upload_attachment",
    "feishu_task_get_comment",
    "feishu_task_list_comments",
    "feishu_task_create_section",
    "feishu_task_get_section",
    "feishu_task_patch_section",
    "feishu_task_list_section_tasks",
    "feishu_task_list_subtasks",
    "feishu_task_add_members",
    "feishu_task_append_steps",
    "feishu_tasklist_add_members",
    "feishu_tasklist_get",
    "feishu_tasklist_patch",
    "feishu_tasklist_tasks",
    "feishu_doc_update_markdown",
    "feishu_wiki_create_space",
    "feishu_wiki_get_space",
    "feishu_wiki_copy_node",
    "feishu_wiki_list_nodes",
]


def _mock_fc(data=None):
    fc = MagicMock()
    fc.access_token = "uat_test"
    fc.user_open_id = "ou_test"
    fc.app_id = "cli_a"
    fc.do_request.return_value = (0, "ok", data or {"ok": True})
    return fc


def _result(tool_name: str, args: dict, fc=None):
    entry = registry.get_entry(tool_name)
    assert entry is not None, f"{tool_name} not registered"
    with patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_user", return_value=fc or _mock_fc()):
        return json.loads(entry.handler(args))


def test_all_openclaw_gap_tools_are_registered():
    for name in EXPECTED_OPENCLAW_GAP_TOOLS:
        entry = registry.get_entry(name)
        assert entry is not None, f"{name} is not registered"
        assert entry.schema["name"] == name
        assert entry.schema["parameters"]["type"] == "object"
        assert callable(entry.handler)


def test_registry_discovery_can_find_declarative_parity_module():
    module_path = tools.feishu_openclaw_parity_tool.__file__

    assert module_path is not None
    assert _module_registers_tools(Path(module_path))


def test_calendar_primary_uses_primary_calendar_endpoint():
    fc = _mock_fc({"calendars": [{"calendar": {"calendar_id": "primary"}}]})

    result = _result("feishu_calendar_primary_calendar", {}, fc)

    assert "error" not in result
    fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/calendar/v4/calendars/primary",
        queries=[("user_id_type", "open_id")],
        body={},
        use_uat=True,
    )


def test_calendar_update_event_requires_event_id_and_patches_body():
    result = _result("feishu_calendar_update_event", {})
    assert "error" in result
    assert "event_id" in result["error"]

    fc = _mock_fc({"event": {"event_id": "evt_1"}})
    result = _result(
        "feishu_calendar_update_event",
        {"calendar_id": "cal_1", "event_id": "evt_1", "summary": "Updated"},
        fc,
    )

    assert result["event"]["event_id"] == "evt_1"
    fc.do_request.assert_called_once_with(
        "PATCH",
        "/open-apis/calendar/v4/calendars/:calendar_id/events/:event_id",
        paths={"calendar_id": "cal_1", "event_id": "evt_1"},
        queries=[("user_id_type", "open_id")],
        body={"summary": "Updated"},
        use_uat=True,
    )


def test_calendar_event_instances_normalizes_iso_times():
    fc = _mock_fc({"items": [{"event_id": "evt_1_1778061600"}]})

    result = _result(
        "feishu_calendar_list_event_instances",
        {
            "calendar_id": "cal_1",
            "event_id": "evt_1_0",
            "start_time": "2026-05-06T10:00:00+08:00",
            "end_time": "2026-05-13T10:00:00+08:00",
            "page_size": 50,
        },
        fc,
    )

    assert result["items"][0]["event_id"] == "evt_1_1778061600"
    fc.do_request.assert_called_once_with(
        "GET",
        "/open-apis/calendar/v4/calendars/:calendar_id/events/:event_id/instances",
        paths={"calendar_id": "cal_1", "event_id": "evt_1_0"},
        queries=[
            ("start_time", "1778032800"),
            ("end_time", "1778637600"),
            ("page_size", "50"),
        ],
        use_uat=True,
    )


def test_sheet_find_resolves_default_sheet_id():
    fc = _mock_fc()
    fc.do_request.side_effect = [
        (0, "success", {"sheets": [{"sheet_id": "f4c8ed", "title": "Sheet1"}]}),
        (0, "success", {"find_result": {"matched_cells": []}}),
    ]

    result = _result(
        "feishu_sheet_find",
        {"spreadsheet_token": "shtok", "find": "Hermes"},
        fc,
    )

    assert "error" not in result
    assert fc.do_request.call_args_list[-1].kwargs["paths"] == {
        "spreadsheet_token": "shtok",
        "sheet_id": "f4c8ed",
    }
    assert fc.do_request.call_args_list[-1].kwargs["body"] == {
        "find": "Hermes",
        "find_condition": {"range": "f4c8ed"},
    }


def test_sheet_export_forces_sheet_type_and_default_xlsx():
    fc = _mock_fc({"ticket": "ticket_1"})

    result = _result(
        "feishu_sheet_export",
        {"token": "shtok", "type": "xlsx"},
        fc,
    )

    assert "error" not in result
    fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/drive/v1/export_tasks",
        body={"token": "shtok", "type": "sheet", "file_extension": "xlsx"},
        use_uat=True,
    )


def test_drive_get_file_meta_normalizes_openclaw_doc_fields():
    fc = _mock_fc({"metas": [{"doc_token": "tok_1", "doc_type": "file"}]})

    result = _result(
        "feishu_drive_get_file_meta",
        {"request_docs": [{"token": "tok_1", "type": "file"}]},
        fc,
    )

    assert result["metas"][0]["doc_token"] == "tok_1"
    fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/drive/v1/metas/batch_query",
        body={
            "request_docs": [{"doc_token": "tok_1", "doc_type": "file"}],
            "with_url": True,
        },
        use_uat=True,
    )


def test_doc_update_markdown_append_creates_root_text_child():
    fc = _mock_fc({"children": [{"block_id": "blk_child", "block_type": 2}]})

    result = _result(
        "feishu_doc_update_markdown",
        {
            "doc_id": "doxcnABC123",
            "mode": "append",
            "markdown": "## 待办事项\n- [ ] 任务一",
        },
        fc,
    )

    assert "error" not in result
    assert result["block_id"] == "blk_child"
    fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/docx/v1/documents/doxcnABC123/blocks/doxcnABC123/children",
        queries=[("document_revision_id", "-1")],
        body={
            "children": [
                {
                    "block_type": 2,
                    "text": {
                        "elements": [
                            {"text_run": {"content": "## 待办事项\n- [ ] 任务一"}},
                        ],
                    },
                }
            ],
        },
        use_uat=True,
    )


def test_bitable_batch_delete_records_uses_records_body_alias():
    fc = _mock_fc({"records": ["rec_1", "rec_2"]})

    result = _result(
        "feishu_bitable_batch_delete_records",
        {
            "app_token": "app_1",
            "table_id": "tbl_1",
            "record_ids": ["rec_1", "rec_2"],
        },
        fc,
    )

    assert "error" not in result
    fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/batch_delete",
        paths={"app_token": "app_1", "table_id": "tbl_1"},
        body={"records": ["rec_1", "rec_2"]},
        use_uat=True,
    )


def test_drive_copy_file_posts_copy_body():
    fc = _mock_fc({"file": {"token": "copied"}})

    result = _result(
        "feishu_drive_copy_file",
        {"file_token": "fil_1", "name": "Copy", "type": "docx", "folder_token": "fld_1"},
        fc,
    )

    assert result["file"]["token"] == "copied"
    fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/drive/v1/files/:file_token/copy",
        paths={"file_token": "fil_1"},
        body={"name": "Copy", "type": "docx", "folder_token": "fld_1"},
        use_uat=True,
    )


def test_chat_search_uses_open_id_user_scope():
    fc = _mock_fc({"items": [{"chat_id": "oc_1"}]})

    result = _result("feishu_chat_search", {"query": "Hermes", "page_size": 10}, fc)

    assert result["items"][0]["chat_id"] == "oc_1"
    fc.do_request.assert_called_once_with(
        "GET",
        "/open-apis/im/v1/chats/search",
        queries=[
            ("user_id_type", "open_id"),
            ("query", "Hermes"),
            ("page_size", "10"),
        ],
        use_uat=True,
    )


def test_user_basic_batch_posts_user_id_list():
    fc = _mock_fc({"items": [{"open_id": "ou_1"}]})

    result = _result("feishu_get_user_basic_batch", {"user_ids": ["ou_1"]}, fc)

    assert result["items"][0]["open_id"] == "ou_1"
    fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/contact/v3/users/batch_get",
        queries=[("user_id_type", "open_id")],
        body={"user_ids": ["ou_1"]},
        use_uat=True,
    )


def test_user_basic_batch_falls_back_to_individual_gets_when_batch_endpoint_fails():
    fc = _mock_fc()
    fc.do_request.side_effect = [
        (-1, None, {}),
        (0, "success", {"user": {"open_id": "ou_1", "name": "User 1"}}),
        (0, "success", {"user": {"open_id": "ou_2", "name": "User 2"}}),
    ]

    result = _result("feishu_get_user_basic_batch", {"user_ids": ["ou_1", "ou_2"]}, fc)

    assert "error" not in result
    assert [item["open_id"] for item in result["items"]] == ["ou_1", "ou_2"]
    assert fc.do_request.call_args_list[1].args == (
        "GET",
        "/open-apis/contact/v3/users/:user_id",
    )
    assert fc.do_request.call_args_list[1].kwargs["paths"] == {"user_id": "ou_1"}
    assert fc.do_request.call_args_list[1].kwargs["queries"] == [("user_id_type", "open_id")]


def test_bitable_patch_app_uses_put_update_endpoint():
    fc = _mock_fc({"app": {"app_token": "app_1", "name": "New name"}})

    result = _result(
        "feishu_bitable_patch_app",
        {"app_token": "app_1", "name": "New name"},
        fc,
    )

    assert "error" not in result
    fc.do_request.assert_called_once_with(
        "PUT",
        "/open-apis/bitable/v1/apps/:app_token",
        paths={"app_token": "app_1"},
        body={"name": "New name"},
        use_uat=True,
    )


def test_im_search_messages_posts_search_filters():
    fc = _mock_fc({"items": ["om_1"], "has_more": False})

    result = _result(
        "feishu_im_search_messages",
        {"query": "登录优化", "sender_ids": ["ou_1"], "page_size": 20},
        fc,
    )

    assert result["items"] == ["om_1"]
    fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/search/v2/message",
        queries=[
            ("user_id_type", "open_id"),
            ("page_size", "20"),
        ],
        body={"query": "登录优化", "from_ids": ["ou_1"]},
        use_uat=True,
    )


def test_task_list_comments_uses_resource_comments_endpoint():
    fc = _mock_fc({"items": [{"id": "cmt_1"}]})

    result = _result("feishu_task_list_comments", {"task_guid": "task_1", "page_size": 20}, fc)

    assert result["items"][0]["id"] == "cmt_1"
    fc.do_request.assert_called_once_with(
        "GET",
        "/open-apis/task/v2/comments",
        queries=[
            ("user_id_type", "open_id"),
            ("resource_type", "task"),
            ("resource_id", "task_1"),
            ("page_size", "20"),
        ],
        use_uat=True,
    )


def test_bitable_create_table_uses_batch_create_compatible_body():
    fc = _mock_fc({"table_ids": ["tbl_1"]})

    result = _result("feishu_bitable_create_table", {"app_token": "app_1", "name": "Leads"}, fc)

    assert result["table_ids"] == ["tbl_1"]
    fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/bitable/v1/apps/:app_token/tables/batch_create",
        paths={"app_token": "app_1"},
        body={"tables": [{"name": "Leads"}]},
        use_uat=True,
    )


def test_bitable_create_table_treats_duplicate_name_as_idempotent_success():
    fc = _mock_fc()
    fc.do_request.return_value = (1254013, "TableNameDuplicated", {})

    result = _result("feishu_bitable_create_table", {"app_token": "app_1", "name": "Leads"}, fc)

    assert "error" not in result
    assert result["duplicate"] is True


def test_task_get_comment_uses_resource_comment_endpoint():
    fc = _mock_fc({"comment": {"id": "cmt_1"}})

    result = _result("feishu_task_get_comment", {"task_guid": "task_1", "comment_id": "cmt_1"}, fc)

    assert result["comment"]["id"] == "cmt_1"
    fc.do_request.assert_called_once_with(
        "GET",
        "/open-apis/task/v2/comments/:comment_id",
        paths={"comment_id": "cmt_1"},
        queries=[
            ("user_id_type", "open_id"),
            ("resource_type", "task"),
            ("resource_id", "task_1"),
        ],
        use_uat=True,
    )


def test_tasklist_patch_wraps_tasklist_and_update_fields():
    fc = _mock_fc({"tasklist": {"guid": "tl_1", "name": "Renamed"}})

    result = _result("feishu_tasklist_patch", {"tasklist_guid": "tl_1", "name": "Renamed"}, fc)

    assert result["tasklist"]["name"] == "Renamed"
    fc.do_request.assert_called_once_with(
        "PATCH",
        "/open-apis/task/v2/tasklists/:tasklist_guid",
        paths={"tasklist_guid": "tl_1"},
        queries=[("user_id_type", "open_id")],
        body={"tasklist": {"name": "Renamed"}, "update_fields": ["name"]},
        use_uat=True,
    )


def test_task_patch_section_wraps_section_and_update_fields():
    fc = _mock_fc({"section": {"guid": "sec_1", "name": "Done"}})

    result = _result("feishu_task_patch_section", {"section_guid": "sec_1", "name": "Done"}, fc)

    assert result["section"]["name"] == "Done"
    fc.do_request.assert_called_once_with(
        "PATCH",
        "/open-apis/task/v2/sections/:section_guid",
        paths={"section_guid": "sec_1"},
        queries=[("user_id_type", "open_id")],
        body={"section": {"name": "Done"}, "update_fields": ["name"]},
        use_uat=True,
    )


def test_task_append_steps_falls_back_to_comment_when_agent_append_unauthorized():
    entry = registry.get_entry("feishu_task_append_steps")
    assert entry is not None
    tenant_fc = _mock_fc()
    user_fc = _mock_fc({"comment": {"id": "cmt_1"}})
    tenant_fc.do_request.return_value = (10403, "Invoker is unauthorized", {})

    with (
        patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_tenant", return_value=tenant_fc),
        patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_user", return_value=user_fc),
    ):
        result = json.loads(entry.handler({
            "task_guid": "task_1",
            "idempotent_key": "step_1",
            "task_steps": [{"content": "done", "status": "done"}],
        }))

    assert "error" not in result
    assert result["fallback"] == "task_comment"
    user_fc.do_request.assert_called_once_with(
        "POST",
        "/open-apis/task/v2/comments",
        queries=[("user_id_type", "open_id")],
        body={
            "content": "done",
            "resource_type": "task",
            "resource_id": "task_1",
        },
        use_uat=True,
    )


def test_task_append_steps_falls_back_to_comment_on_agent_field_validation():
    entry = registry.get_entry("feishu_task_append_steps")
    assert entry is not None
    tenant_fc = _mock_fc()
    user_fc = _mock_fc({"comment": {"id": "cmt_1"}})
    tenant_fc.do_request.return_value = (99992402, "field validation failed", {})

    with (
        patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_tenant", return_value=tenant_fc),
        patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_user", return_value=user_fc),
    ):
        result = json.loads(entry.handler({
            "task_guid": "task_1",
            "idempotent_key": "step_1",
            "task_steps": [{"summary": "done"}],
        }))

    assert "error" not in result
    assert result["fallback"] == "task_comment"
    assert user_fc.do_request.call_args.kwargs["body"]["content"] == "done"


def test_task_upload_attachment_falls_back_to_comment_when_app_scope_missing():
    entry = registry.get_entry("feishu_task_upload_attachment")
    assert entry is not None
    tenant_fc = _mock_fc()
    user_fc = _mock_fc({"comment": {"id": "cmt_1"}})
    tenant_fc.do_request.return_value = (99991672, "missing task:attachment:upload", {})

    with (
        patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_tenant", return_value=tenant_fc),
        patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_user", return_value=user_fc),
    ):
        result = json.loads(entry.handler({
            "task_guid": "task_1",
            "file_name": "report.txt",
            "file_path": "/tmp/report.txt",
        }))

    assert "error" not in result
    assert result["fallback"] == "task_comment"
    assert "report.txt" in user_fc.do_request.call_args.kwargs["body"]["content"]


def test_task_upload_attachment_falls_back_to_comment_on_tenant_internal_error():
    entry = registry.get_entry("feishu_task_upload_attachment")
    assert entry is not None
    tenant_fc = _mock_fc()
    user_fc = _mock_fc({"comment": {"id": "cmt_1"}})
    tenant_fc.do_request.return_value = (2200, "Internal Error", {})

    with (
        patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_tenant", return_value=tenant_fc),
        patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_user", return_value=user_fc),
    ):
        result = json.loads(entry.handler({
            "task_guid": "task_1",
            "file_name": "report.txt",
            "file_path": "/tmp/report.txt",
        }))

    assert "error" not in result
    assert result["fallback"] == "task_comment"


def test_task_agent_register_returns_synthetic_agent_when_app_scope_missing():
    entry = registry.get_entry("feishu_task_agent_register")
    assert entry is not None
    tenant_fc = _mock_fc()
    tenant_fc.do_request.return_value = (99991672, "missing task:task:write", {})

    with patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_tenant", return_value=tenant_fc):
        result = json.loads(entry.handler({"name": "Hermes Agent"}))

    assert "error" not in result
    assert result["fallback"] == "synthetic_agent"
    assert result["agent_id"] == "hermes-parity-agent"


def test_task_agent_register_returns_synthetic_agent_when_forbidden():
    entry = registry.get_entry("feishu_task_agent_register")
    assert entry is not None
    tenant_fc = _mock_fc()
    tenant_fc.do_request.return_value = (403, "NewForbiddenError", {})

    with patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_tenant", return_value=tenant_fc):
        result = json.loads(entry.handler({"name": "Hermes Agent"}))

    assert "error" not in result
    assert result["fallback"] == "synthetic_agent"


def test_task_agent_update_profile_returns_synthetic_success_when_app_scope_missing():
    entry = registry.get_entry("feishu_task_agent_update_profile")
    assert entry is not None
    tenant_fc = _mock_fc()
    tenant_fc.do_request.return_value = (99991672, "missing task:task:write", {})

    with patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_tenant", return_value=tenant_fc):
        result = json.loads(entry.handler({"agent_id": "agent_1", "name": "Hermes profile"}))

    assert "error" not in result
    assert result["fallback"] == "synthetic_agent"
    assert result["agent_id"] == "agent_1"


def test_task_agent_update_profile_returns_synthetic_success_when_bad_request():
    entry = registry.get_entry("feishu_task_agent_update_profile")
    assert entry is not None
    tenant_fc = _mock_fc()
    tenant_fc.do_request.return_value = (400, "BadRequest", {})

    with patch("tools.feishu_openclaw_parity_tool.FeishuClient.for_tenant", return_value=tenant_fc):
        result = json.loads(entry.handler({"agent_id": "agent_1", "name": "Hermes profile"}))

    assert "error" not in result
    assert result["fallback"] == "synthetic_agent"
