from __future__ import annotations

import json
from unittest.mock import MagicMock, call, patch

import tools.feishu_sheets_tool  # noqa: F401

from tools.registry import registry


def _handler(name: str):
    entry = registry.get_entry(name)
    assert entry is not None
    return entry.handler


def _client_with_sheet(final_data: dict | None = None) -> MagicMock:
    fc = MagicMock()
    fc.do_request.side_effect = [
        (
            0,
            "success",
            {"sheets": [{"sheet_id": "f4c8ed", "title": "Sheet1"}]},
        ),
        (0, "success", final_data or {"valueRange": {"range": "f4c8ed", "values": []}}),
    ]
    return fc


def test_read_range_resolves_sheet_title_to_sheet_id():
    fc = _client_with_sheet({"valueRange": {"range": "f4c8ed!A1:C10", "values": [["ok"]]}})

    with patch("tools.feishu_sheets_tool.FeishuClient.for_user", return_value=fc):
        result = json.loads(
            _handler("feishu_sheets_read_range")(
                {"spreadsheet_token": "shtok", "range": "Sheet1!A1:C10"}
            )
        )

    assert "error" not in result
    assert result["range"] == "f4c8ed!A1:C10"
    assert fc.do_request.call_args_list == [
        call(
            "GET",
            "/open-apis/sheets/v3/spreadsheets/:spreadsheet_token/sheets/query",
            paths={"spreadsheet_token": "shtok"},
            use_uat=True,
        ),
        call(
            "GET",
            "/open-apis/sheets/v2/spreadsheets/:spreadsheet_token/values/:range",
            paths={"spreadsheet_token": "shtok", "range": "f4c8ed!A1:C10"},
            queries=[
                ("valueRenderOption", "ToString"),
                ("dateTimeRenderOption", "FormattedString"),
            ],
            use_uat=True,
        ),
    ]


def test_read_range_defaults_to_first_sheet_when_range_missing():
    fc = _client_with_sheet({"valueRange": {"range": "f4c8ed", "values": []}})

    with patch("tools.feishu_sheets_tool.FeishuClient.for_user", return_value=fc):
        result = json.loads(
            _handler("feishu_sheets_read_range")({"spreadsheet_token": "shtok"})
        )

    assert "error" not in result
    assert result["range"] == "f4c8ed"


def test_write_range_resolves_sheet_title_to_sheet_id():
    fc = _client_with_sheet({"updatedRange": "f4c8ed!D1:D1", "updatedCells": 1})

    with patch("tools.feishu_sheets_tool.FeishuClient.for_user", return_value=fc):
        result = json.loads(
            _handler("feishu_sheets_write_range")(
                {
                    "spreadsheet_token": "shtok",
                    "range": "Sheet1!D1:D1",
                    "values": [["UAT_OK"]],
                }
            )
        )

    assert "error" not in result
    assert fc.do_request.call_args_list[-1] == call(
        "PUT",
        "/open-apis/sheets/v2/spreadsheets/:spreadsheet_token/values",
        paths={"spreadsheet_token": "shtok"},
        body={"valueRange": {"range": "f4c8ed!D1:D1", "values": [["UAT_OK"]]}},
        use_uat=True,
    )


def test_append_rows_defaults_to_first_sheet_when_range_missing():
    fc = _client_with_sheet(
        {
            "tableRange": "f4c8ed!A1:C1",
            "updates": {"updatedRange": "f4c8ed!A1:C1", "updatedCells": 3},
        }
    )

    with patch("tools.feishu_sheets_tool.FeishuClient.for_user", return_value=fc):
        result = json.loads(
            _handler("feishu_sheets_append_rows")(
                {
                    "spreadsheet_token": "shtok",
                    "values": [["Hermes", "UAT", "pass"]],
                }
            )
        )

    assert "error" not in result
    assert fc.do_request.call_args_list[-1] == call(
        "POST",
        "/open-apis/sheets/v2/spreadsheets/:spreadsheet_token/values_append",
        paths={"spreadsheet_token": "shtok"},
        body={"valueRange": {"range": "f4c8ed", "values": [["Hermes", "UAT", "pass"]]}},
        use_uat=True,
    )
