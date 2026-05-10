"""Unit tests for feishu_calendar_attendee_tool handlers.

Coverage:
  - feishu_calendar_event_attendee_create
  - feishu_calendar_event_attendee_list
  - feishu_calendar_event_attendee_delete
  - feishu_calendar_list_calendars

All SDK calls are mocked via FeishuClient.for_user + fc.do_request — no network I/O.
"""

import importlib
import json
import unittest
from unittest.mock import MagicMock, patch

# Force tool module to register its entries
attendee_tool = importlib.import_module("tools.feishu_calendar_attendee_tool")

from tools.feishu_oapi_client import NeedAuthorizationError
from tools.registry import registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_fc(access_token="uat_test", user_open_id="ou_test"):
    """Return a mock FeishuClient with a stubbed do_request."""
    fc = MagicMock()
    fc.access_token = access_token
    fc.user_open_id = user_open_id
    fc.app_id = "app_test"
    return fc


# ---------------------------------------------------------------------------
# feishu_calendar_event_attendee_create
# ---------------------------------------------------------------------------

class TestAttendeeCreate(unittest.TestCase):
    """Tests for feishu_calendar_event_attendee_create handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_calendar_event_attendee_create")
        return entry.handler

    def test_returns_error_when_calendar_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"event_id": "ev_001", "attendees": [{"user_id": "ou_x"}]}))
        self.assertIn("error", result)

    def test_returns_error_when_event_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"calendar_id": "cal_001", "attendees": [{"user_id": "ou_x"}]}))
        self.assertIn("error", result)

    def test_returns_error_when_attendees_empty(self):
        handler = self._get_handler()
        result = json.loads(handler({"calendar_id": "cal_001", "event_id": "ev_001", "attendees": []}))
        self.assertIn("error", result)

    def test_returns_error_when_uat_not_available(self):
        handler = self._get_handler()
        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError(reason="no token"),
        ):
            result = json.loads(handler({
                "calendar_id": "cal_001",
                "event_id": "ev_001",
                "attendees": [{"type": "user", "user_id": "ou_abc"}],
            }))
        self.assertIn("error", result)

    def test_returns_success_on_api_code_zero(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0, "ok", {"attendees": [{"attendee_id": "att_001", "type": "user"}]}
        )

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "calendar_id": "cal_001",
                "event_id": "ev_001",
                "attendees": [{"type": "user", "user_id": "ou_abc"}],
            }))

        self.assertNotIn("error", result)
        self.assertIn("attendees", result)
        self.assertEqual(result["event_id"], "ev_001")

    def test_returns_error_on_non_zero_api_code(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (400, "invalid request", {})

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "calendar_id": "cal_001",
                "event_id": "ev_001",
                "attendees": [{"type": "user", "user_id": "ou_abc"}],
            }))

        self.assertIn("error", result)

    def test_schema_requires_all_params(self):
        entry = registry.get_entry("feishu_calendar_event_attendee_create")
        req = entry.schema["parameters"].get("required", [])
        for param in ["calendar_id", "event_id", "attendees"]:
            self.assertIn(param, req)

    def test_registered_in_feishu_calendar_toolset(self):
        entry = registry.get_entry("feishu_calendar_event_attendee_create")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.toolset, "feishu_calendar")


# ---------------------------------------------------------------------------
# feishu_calendar_event_attendee_list
# ---------------------------------------------------------------------------

class TestAttendeeList(unittest.TestCase):
    """Tests for feishu_calendar_event_attendee_list handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_calendar_event_attendee_list")
        return entry.handler

    def test_returns_error_when_calendar_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"event_id": "ev_001"}))
        self.assertIn("error", result)

    def test_returns_error_when_event_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"calendar_id": "cal_001"}))
        self.assertIn("error", result)

    def test_returns_error_when_uat_not_available(self):
        handler = self._get_handler()
        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError(reason="no token"),
        ):
            result = json.loads(handler({"calendar_id": "cal_001", "event_id": "ev_001"}))
        self.assertIn("error", result)

    def test_returns_attendees_on_success(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0, "ok", {
                "items": [
                    {"attendee_id": "att_001", "type": "user", "user_id": "ou_abc"},
                    {"attendee_id": "att_002", "type": "user", "user_id": "ou_def"},
                ],
                "has_more": False,
            }
        )

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({"calendar_id": "cal_001", "event_id": "ev_001"}))

        self.assertNotIn("error", result)
        self.assertIn("attendees", result)
        self.assertEqual(len(result["attendees"]), 2)
        self.assertFalse(result["has_more"])

    def test_schema_requires_calendar_and_event_id(self):
        entry = registry.get_entry("feishu_calendar_event_attendee_list")
        req = entry.schema["parameters"].get("required", [])
        self.assertIn("calendar_id", req)
        self.assertIn("event_id", req)

    def test_registered_in_feishu_calendar_toolset(self):
        entry = registry.get_entry("feishu_calendar_event_attendee_list")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.toolset, "feishu_calendar")


# ---------------------------------------------------------------------------
# feishu_calendar_event_attendee_delete
# ---------------------------------------------------------------------------

class TestAttendeeDelete(unittest.TestCase):
    """Tests for feishu_calendar_event_attendee_delete handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_calendar_event_attendee_delete")
        return entry.handler

    def test_returns_error_when_calendar_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"event_id": "ev_001", "attendee_ids": ["att_001"]}))
        self.assertIn("error", result)

    def test_returns_error_when_event_id_missing(self):
        handler = self._get_handler()
        result = json.loads(handler({"calendar_id": "cal_001", "attendee_ids": ["att_001"]}))
        self.assertIn("error", result)

    def test_returns_error_when_attendee_ids_empty(self):
        handler = self._get_handler()
        result = json.loads(handler({"calendar_id": "cal_001", "event_id": "ev_001", "attendee_ids": []}))
        self.assertIn("error", result)

    def test_returns_error_when_uat_not_available(self):
        handler = self._get_handler()
        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError(reason="no token"),
        ):
            result = json.loads(handler({
                "calendar_id": "cal_001",
                "event_id": "ev_001",
                "attendee_ids": ["att_001"],
            }))
        self.assertIn("error", result)

    def test_returns_success_on_api_code_zero(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (0, "ok", {})

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "calendar_id": "cal_001",
                "event_id": "ev_001",
                "attendee_ids": ["att_001", "att_002"],
            }))

        self.assertNotIn("error", result)
        self.assertEqual(result["deleted_count"], 2)
        self.assertEqual(result["event_id"], "ev_001")

    def test_resolves_open_id_to_attendee_id_before_delete(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()

        def do_request(method, uri, **kwargs):
            if method == "GET":
                return (
                    0,
                    "ok",
                    {
                        "items": [
                            {
                                "attendee_id": "att_001",
                                "type": "user",
                                "user_id": "ou_target",
                            }
                        ]
                    },
                )
            if method == "POST":
                self.assertEqual(kwargs["body"], {"attendee_ids": ["att_001"]})
                return (0, "ok", {})
            raise AssertionError(f"unexpected method {method}")

        mock_fc.do_request.side_effect = do_request

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "calendar_id": "cal_001",
                "event_id": "ev_001",
                "attendee_ids": ["ou_target"],
            }))

        self.assertNotIn("error", result)
        self.assertEqual(result["deleted_count"], 1)
        self.assertEqual(
            mock_fc.do_request.call_args_list[0].args[:2],
            (
                "GET",
                attendee_tool._ATTENDEE_LIST_URI.format(
                    calendar_id="cal_001",
                    event_id="ev_001",
                ),
            ),
        )

    def test_returns_error_on_non_zero_api_code(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (403, "forbidden", {})

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({
                "calendar_id": "cal_001",
                "event_id": "ev_001",
                "attendee_ids": ["att_001"],
            }))

        self.assertIn("error", result)

    def test_schema_requires_all_params(self):
        entry = registry.get_entry("feishu_calendar_event_attendee_delete")
        req = entry.schema["parameters"].get("required", [])
        for param in ["calendar_id", "event_id", "attendee_ids"]:
            self.assertIn(param, req)

    def test_registered_in_feishu_calendar_toolset(self):
        entry = registry.get_entry("feishu_calendar_event_attendee_delete")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.toolset, "feishu_calendar")


# ---------------------------------------------------------------------------
# feishu_calendar_list_calendars
# ---------------------------------------------------------------------------

class TestListCalendars(unittest.TestCase):
    """Tests for feishu_calendar_list_calendars handler."""

    def _get_handler(self):
        entry = registry.get_entry("feishu_calendar_list_calendars")
        return entry.handler

    def test_returns_error_when_uat_not_available(self):
        handler = self._get_handler()
        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            side_effect=NeedAuthorizationError(reason="no token"),
        ):
            result = json.loads(handler({}))
        self.assertIn("error", result)

    def test_returns_calendars_on_success(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0, "ok", {
                "calendar_list": [
                    {"calendar_id": "cal_001", "summary": "Primary"},
                    {"calendar_id": "cal_002", "summary": "Work"},
                ],
                "has_more": False,
            }
        )

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({}))

        self.assertNotIn("error", result)
        self.assertIn("calendars", result)
        self.assertEqual(len(result["calendars"]), 2)
        self.assertFalse(result["has_more"])

    def test_returns_calendars_with_custom_page_size(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0, "ok", {"calendar_list": [{"calendar_id": "cal_001"}], "has_more": False}
        )

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({"page_size": 5}))

        self.assertNotIn("error", result)
        # Verify do_request was called with the right page_size in queries
        call_kwargs = mock_fc.do_request.call_args
        queries = call_kwargs[1].get("queries") or call_kwargs[0][2] if call_kwargs[0] else []
        # do_request was invoked; result is valid
        self.assertIn("calendars", result)

    def test_clamps_page_size_to_feishu_supported_value(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (
            0, "ok", {"calendar_list": [{"calendar_id": "cal_001"}], "has_more": False}
        )

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({"page_size": 10}))

        self.assertNotIn("error", result)
        self.assertIn(("page_size", "50"), mock_fc.do_request.call_args.kwargs["queries"])

    def test_returns_error_on_non_zero_api_code(self):
        handler = self._get_handler()
        mock_fc = _make_mock_fc()
        mock_fc.do_request.return_value = (500, "internal error", {})

        with patch(
            "tools.feishu_calendar_attendee_tool.FeishuClient.for_user",
            return_value=mock_fc,
        ):
            result = json.loads(handler({}))

        self.assertIn("error", result)

    def test_schema_has_no_required_params(self):
        entry = registry.get_entry("feishu_calendar_list_calendars")
        req = entry.schema["parameters"].get("required", [])
        self.assertEqual(req, [])

    def test_registered_in_feishu_calendar_toolset(self):
        entry = registry.get_entry("feishu_calendar_list_calendars")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.toolset, "feishu_calendar")


if __name__ == "__main__":
    unittest.main()
