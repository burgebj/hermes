import json
from unittest.mock import patch

from tools.send_message_tool import SEND_MESSAGE_SCHEMA, send_message_tool


def test_send_message_schema_requires_send_fields_unless_listing():
    params = SEND_MESSAGE_SCHEMA["parameters"]

    assert params["required"] == []
    assert params["allOf"] == [
        {
            "if": {
                "properties": {"action": {"const": "list"}},
                "required": ["action"],
            },
            "then": {},
            "else": {"required": ["target", "message"]},
        }
    ]


def test_list_action_still_accepts_no_target_or_message():
    with patch(
        "gateway.channel_directory.format_directory_for_display",
        return_value="telegram:home",
    ):
        result = json.loads(send_message_tool({"action": "list"}))

    assert result == {"targets": "telegram:home"}
