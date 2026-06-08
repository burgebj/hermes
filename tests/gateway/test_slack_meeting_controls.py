"""Regression tests for Slack meeting-room control payload replay.

These are production-adjacent boundary tests ported from the local
claudecode-hermes meeting MVP fake Slack payload replay spike. They exercise
only the Slack adapter boundary: feature flag, allowlist, real thread_ts
preservation, and no execution-lane entry.
"""

import copy
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Ensure the repo root is importable
# ---------------------------------------------------------------------------
_repo = str(Path(__file__).resolve().parents[2])
if _repo not in sys.path:
    sys.path.insert(0, _repo)


# ---------------------------------------------------------------------------
# Minimal Slack SDK mock so SlackAdapter can be imported
# ---------------------------------------------------------------------------
def _ensure_slack_mock():
    """Wire up the minimal mocks required to import SlackAdapter."""
    if "slack_bolt" in sys.modules:
        return
    slack_bolt = MagicMock()
    slack_bolt.async_app.AsyncApp = MagicMock
    sys.modules["slack_bolt"] = slack_bolt
    sys.modules["slack_bolt.async_app"] = slack_bolt.async_app
    handler_mod = MagicMock()
    handler_mod.AsyncSocketModeHandler = MagicMock
    sys.modules["slack_bolt.adapter"] = MagicMock()
    sys.modules["slack_bolt.adapter.socket_mode"] = MagicMock()
    sys.modules["slack_bolt.adapter.socket_mode.async_handler"] = handler_mod
    sdk_mod = MagicMock()
    sdk_mod.web = MagicMock()
    sdk_mod.web.async_client = MagicMock()
    sdk_mod.web.async_client.AsyncWebClient = MagicMock
    sys.modules["slack_sdk"] = sdk_mod
    sys.modules["slack_sdk.web"] = sdk_mod.web
    sys.modules["slack_sdk.web.async_client"] = sdk_mod.web.async_client


_ensure_slack_mock()

from gateway.config import PlatformConfig
from gateway.platforms.slack import SlackAdapter, SlackMeetingControlError


def _make_adapter(extra=None):
    config = PlatformConfig(enabled=True, token="***", extra=extra or {})
    adapter = SlackAdapter(config)
    adapter._app = MagicMock()
    adapter._bot_user_id = "UKIMBOT"
    adapter.handle_message = AsyncMock()
    return adapter


def _meeting_action_payload(
    *,
    action_id="hermes_meeting_start",
    control="start",
    user_id="UCEO",
    channel_id="CMEET",
    thread_ts="1780803000.000100",
    message_ts="1780803000.000101",
    action_ts="1780803001.000200",
    meeting_id="mtg-001",
):
    session_key = f"slack:{channel_id}:{thread_ts}"
    action = {
        "type": "button",
        "action_id": action_id,
        "action_ts": action_ts,
        "value": json.dumps(
            {
                "meeting_id": meeting_id,
                "control": control,
                "session_key": session_key,
            }
        ),
    }
    return {
        "type": "block_actions",
        "user": {"id": user_id, "name": "ceo"},
        "channel": {"id": channel_id, "name": "meeting-room"},
        "message": {"ts": message_ts, "thread_ts": thread_ts, "blocks": []},
        "container": {
            "type": "message",
            "channel_id": channel_id,
            "message_ts": message_ts,
            "thread_ts": thread_ts,
        },
        "actions": [action],
    }


@pytest.mark.asyncio
async def test_meeting_control_feature_flag_default_off_blocks_without_side_effects():
    adapter = _make_adapter()
    ack = AsyncMock()
    body = _meeting_action_payload()

    decision = await adapter._handle_meeting_control_action(ack, body, body["actions"][0])

    ack.assert_called_once()
    assert decision["action"] == "feature_disabled"
    assert decision["dispatched"] is False
    assert adapter._meeting_control_dispatches == []
    adapter.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_enabled_meeting_control_requires_non_empty_allowlist():
    adapter = _make_adapter({"meeting_controls_enabled": True})
    ack = AsyncMock()
    body = _meeting_action_payload()

    decision = await adapter._handle_meeting_control_action(ack, body, body["actions"][0])

    ack.assert_called_once()
    assert decision["action"] == "allowlist_required"
    assert decision["dispatched"] is False
    assert adapter._meeting_control_dispatches == []
    adapter.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_enabled_meeting_control_replays_start_next_close_fixture_boundary():
    adapter = _make_adapter(
        {
            "meeting_controls_enabled": True,
            "meeting_control_allowed_users": ["UCEO"],
        }
    )
    ack = AsyncMock()
    payloads = [
        _meeting_action_payload(
            action_id="hermes_meeting_start",
            control="start",
            action_ts="1780803001.000200",
        ),
        _meeting_action_payload(
            action_id="hermes_meeting_next",
            control="next",
            action_ts="1780803002.000200",
        ),
        _meeting_action_payload(
            action_id="hermes_meeting_close",
            control="close",
            action_ts="1780803003.000200",
        ),
    ]

    decisions = [
        await adapter._handle_meeting_control_action(ack, payload, payload["actions"][0])
        for payload in payloads
    ]

    assert [item["action"] for item in decisions] == [
        "start_meeting_control",
        "next_turn_control",
        "close_meeting_control",
    ]
    assert [item["dispatched"] for item in decisions] == [True, True, True]
    assert [item["thread_ts"] for item in adapter._meeting_control_dispatches] == [
        "1780803000.000100",
        "1780803000.000100",
        "1780803000.000100",
    ]
    assert [item["session_key"] for item in adapter._meeting_control_dispatches] == [
        "slack:CMEET:1780803000.000100",
        "slack:CMEET:1780803000.000100",
        "slack:CMEET:1780803000.000100",
    ]
    assert adapter._meeting_control_thread_state == {"slack:CMEET:1780803000.000100": "closed"}
    adapter.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_meeting_thread_state_is_scoped_by_channel_and_thread_session_key():
    adapter = _make_adapter(
        {
            "meeting_controls_enabled": True,
            "meeting_control_allowed_users": ["UCEO"],
        }
    )
    ack = AsyncMock()
    start = _meeting_action_payload(action_id="hermes_meeting_start", control="start")
    cross_channel_next = _meeting_action_payload(
        action_id="hermes_meeting_next",
        control="next",
        channel_id="COTHER",
        action_ts="1780803002.000200",
    )

    started = await adapter._handle_meeting_control_action(ack, start, start["actions"][0])
    orphan = await adapter._handle_meeting_control_action(
        ack,
        cross_channel_next,
        cross_channel_next["actions"][0],
    )

    assert started["action"] == "start_meeting_control"
    assert orphan["action"] == "orphan_action_ignored"
    assert adapter._meeting_control_thread_state == {"slack:CMEET:1780803000.000100": "active"}
    assert [item["session_key"] for item in adapter._meeting_control_dispatches] == [
        "slack:CMEET:1780803000.000100",
    ]
    adapter.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_duplicate_and_late_meeting_actions_are_ignored_without_execution():
    adapter = _make_adapter(
        {
            "meeting_controls_enabled": True,
            "meeting_control_allowed_users": ["UCEO"],
        }
    )
    ack = AsyncMock()
    start = _meeting_action_payload(action_id="hermes_meeting_start", control="start")
    close = _meeting_action_payload(
        action_id="hermes_meeting_close",
        control="close",
        action_ts="1780803002.000200",
    )
    late_next = _meeting_action_payload(
        action_id="hermes_meeting_next",
        control="next",
        action_ts="1780803003.000200",
    )

    first = await adapter._handle_meeting_control_action(ack, start, start["actions"][0])
    duplicate = await adapter._handle_meeting_control_action(ack, start, start["actions"][0])
    closed = await adapter._handle_meeting_control_action(ack, close, close["actions"][0])
    late = await adapter._handle_meeting_control_action(ack, late_next, late_next["actions"][0])

    assert [first["action"], duplicate["action"], closed["action"], late["action"]] == [
        "start_meeting_control",
        "duplicate_action_ignored",
        "close_meeting_control",
        "late_action_ignored",
    ]
    assert len(adapter._meeting_control_dispatches) == 2
    adapter.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_unauthorized_meeting_control_user_is_ignored():
    adapter = _make_adapter(
        {
            "meeting_controls_enabled": True,
            "meeting_control_allowed_users": ["UCEO"],
        }
    )
    ack = AsyncMock()
    body = _meeting_action_payload(user_id="UNOAH")

    decision = await adapter._handle_meeting_control_action(ack, body, body["actions"][0])

    ack.assert_called_once()
    assert decision["action"] == "unauthorized_action_ignored"
    assert decision["dispatched"] is False
    assert adapter._meeting_control_dispatches == []
    adapter.handle_message.assert_not_called()


def test_meeting_action_requires_real_thread_ts_and_matching_session_key():
    adapter = _make_adapter(
        {
            "meeting_controls_enabled": True,
            "meeting_control_allowed_users": ["UCEO"],
        }
    )

    missing = _meeting_action_payload()
    del missing["container"]["thread_ts"]
    with pytest.raises(SlackMeetingControlError) as missing_ctx:
        adapter._normalize_meeting_control_payload(missing, missing["actions"][0])
    assert missing_ctx.value.code == "missing_container_fields"

    synthetic = _meeting_action_payload(thread_ts="meeting:CMEET:mtg-001")
    with pytest.raises(SlackMeetingControlError) as synthetic_ctx:
        adapter._normalize_meeting_control_payload(synthetic, synthetic["actions"][0])
    assert synthetic_ctx.value.code == "invalid_thread_ts"

    mismatch = _meeting_action_payload()
    action_value = json.loads(mismatch["actions"][0]["value"])
    action_value["session_key"] = "slack:COTHER:1780803000.000100"
    mismatch["actions"][0]["value"] = json.dumps(action_value)
    with pytest.raises(SlackMeetingControlError) as mismatch_ctx:
        adapter._normalize_meeting_control_payload(mismatch, mismatch["actions"][0])
    assert mismatch_ctx.value.code == "session_key_mismatch"
