import json
from unittest.mock import MagicMock, patch

import tools.feishu_drive_tool as drive_tool
from tools.registry import registry


def _handler(name: str):
    entry = registry.get_entry(name)
    assert entry is not None, f"{name} must be registered"
    return entry.handler


def test_list_comment_replies_falls_back_to_uat_without_injected_client():
    handler = _handler("feishu_drive_list_comment_replies")
    fc = MagicMock()

    with (
        patch("tools.feishu_oapi_client.FeishuClient.for_user", return_value=fc),
        patch("tools.feishu_drive_tool.get_client", return_value=None),
        patch("tools.feishu_drive_tool._do_request_uat", return_value=(0, "ok", {"items": []})) as do_request_uat,
    ):
        result = json.loads(handler({"file_token": "doc_1", "comment_id": "cmt_1"}))

    assert "error" not in result
    do_request_uat.assert_called_once()
    assert do_request_uat.call_args.args[:3] == (
        fc,
        "GET",
        "/open-apis/drive/v1/files/:file_token/comments/:comment_id/replies",
    )


def test_reply_comment_falls_back_to_uat_without_injected_client():
    handler = _handler("feishu_drive_reply_comment")
    fc = MagicMock()

    with (
        patch("tools.feishu_oapi_client.FeishuClient.for_user", return_value=fc),
        patch("tools.feishu_drive_tool.get_client", return_value=None),
        patch("tools.feishu_drive_tool._do_request_uat", return_value=(0, "ok", {"reply_id": "r_1"})) as do_request_uat,
    ):
        result = json.loads(handler({"file_token": "doc_1", "comment_id": "cmt_1", "content": "UAT ok"}))

    assert "error" not in result
    do_request_uat.assert_called_once()
    assert do_request_uat.call_args.args[:3] == (
        fc,
        "POST",
        "/open-apis/drive/v1/files/:file_token/comments/:comment_id/replies",
    )


def test_reply_comment_falls_back_to_whole_document_comment_when_replies_disabled():
    handler = _handler("feishu_drive_reply_comment")
    fc = MagicMock()

    with (
        patch("tools.feishu_oapi_client.FeishuClient.for_user", return_value=fc),
        patch("tools.feishu_drive_tool._do_request_uat") as do_request_uat,
    ):
        do_request_uat.side_effect = [
            (1069302, "The comment section does not allow replies", {}),
            (0, "ok", {"comment_id": "new_comment"}),
        ]
        result = json.loads(handler({"file_token": "doc_1", "comment_id": "cmt_1", "content": "UAT ok"}))

    assert "error" not in result
    assert result["fallback"] == "whole_document_comment"
    assert do_request_uat.call_args_list[1].args[:3] == (
        fc,
        "POST",
        "/open-apis/drive/v1/files/:file_token/new_comments",
    )
    assert do_request_uat.call_args_list[1].kwargs["paths"] == {"file_token": "doc_1"}
