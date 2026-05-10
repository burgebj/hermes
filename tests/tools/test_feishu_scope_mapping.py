"""US-008 tests for feishu_scope_mapping helpers."""

from __future__ import annotations

import unittest

from tools.feishu_oapi_client import (
    AppScopeMissingError,
    UserAuthRequiredError,
    UserScopeInsufficientError,
)
from tools.feishu_scope_mapping import (
    SCOPE_LABELS,
    build_auth_error_card,
    build_auth_pending_card,
    build_auth_success_card,
    build_feishu_auth_card,
    format_scope_error,
    label_for_scope,
    labels_for_scopes,
)


class TestScopeLabels(unittest.TestCase):

    def test_scope_labels_has_at_least_10_entries(self):
        # AC: scope-to-label mapping has ≥10 entries
        self.assertGreaterEqual(len(SCOPE_LABELS), 10)

    def test_known_scope_returns_chinese_label(self):
        self.assertEqual(label_for_scope("calendar:calendar"), "日历(读写)")
        self.assertEqual(label_for_scope("drive:drive"), "云盘(读写)")

    def test_unknown_scope_falls_back_to_raw_string(self):
        self.assertEqual(label_for_scope("totally:made:up"), "totally:made:up")

    def test_empty_scope_returns_placeholder(self):
        self.assertEqual(label_for_scope(""), "(未知权限)")

    def test_labels_for_scopes_dedupes_and_preserves_order(self):
        out = labels_for_scopes([
            "calendar:calendar",
            "drive:drive",
            "calendar:calendar",  # dup
            "",  # skipped
            "docs:document",
        ])
        self.assertEqual(out, ["日历(读写)", "云盘(读写)", "文档(读写)"])


class TestFormatScopeError(unittest.TestCase):

    def test_app_scope_missing_mentions_admin_and_app_id(self):
        exc = AppScopeMissingError(
            app_id="cli_test_app",
            api_name="feishu_calendar_list_events",
            missing_scopes=["calendar:calendar", "calendar:freebusy:readonly"],
        )
        out = format_scope_error(exc)
        self.assertIn("cli_test_app", out)
        self.assertIn("管理员", out)
        # Friendly labels included
        self.assertIn("日历(读写)", out)
        self.assertIn("忙闲查询", out)

    def test_user_scope_insufficient_includes_reauth_command(self):
        exc = UserScopeInsufficientError(
            user_open_id="ou_alice",
            api_name="feishu_calendar_list_events",
            missing_scopes=["calendar:calendar", "drive:drive"],
        )
        out = format_scope_error(exc)
        self.assertIn("/feishu_auth", out)
        self.assertIn("calendar:calendar", out)
        self.assertIn("drive:drive", out)
        self.assertIn("日历(读写)", out)
        self.assertIn("云盘(读写)", out)

    def test_user_auth_required_uses_required_scopes(self):
        exc = UserAuthRequiredError(
            user_open_id="ou_bob",
            api_name="feishu_drive_list",
            required_scopes=["drive:drive"],
            app_id="app_x",
        )
        out = format_scope_error(exc)
        self.assertIn("/feishu_auth", out)
        self.assertIn("drive:drive", out)
        self.assertIn("云盘(读写)", out)

    def test_suggest_command_can_be_disabled(self):
        exc = UserScopeInsufficientError(
            user_open_id="ou_x",
            api_name="x",
            missing_scopes=["calendar:calendar"],
        )
        out = format_scope_error(exc, suggest_command=False)
        self.assertNotIn("/feishu_auth", out)
        # Friendly label still included
        self.assertIn("日历(读写)", out)

    def test_unknown_exception_returns_short_fallback(self):
        out = format_scope_error(RuntimeError("weird"))
        self.assertIn("飞书授权错误", out)


class TestBuildFeishuAuthCard(unittest.TestCase):
    """P1.1 follow-up: card builder for the click → /feishu_auth button flow."""

    def test_card_has_button_with_feishu_auth_action_marker(self):
        card = build_feishu_auth_card("点击下面授权", "立即授权")
        # action element has a button whose value carries hermes_action="feishu_auth"
        action_elem = next(e for e in card["elements"] if e["tag"] == "action")
        button = action_elem["actions"][0]
        self.assertEqual(button["tag"], "button")
        self.assertEqual(button["value"]["hermes_action"], "feishu_auth")

    def test_card_passes_scope_through_button_value(self):
        card = build_feishu_auth_card(
            "需要日历+云盘权限", "重新授权",
            scope="calendar:calendar drive:drive",
        )
        action_elem = next(e for e in card["elements"] if e["tag"] == "action")
        button = action_elem["actions"][0]
        self.assertEqual(button["value"]["scope"], "calendar:calendar drive:drive")

    def test_card_omits_scope_when_blank(self):
        card = build_feishu_auth_card("hi", "go")
        button = card["elements"][1]["actions"][0]
        self.assertNotIn("scope", button["value"])

    def test_card_body_text_is_in_markdown_element(self):
        card = build_feishu_auth_card("**重要** 请立即授权", "Authorize")
        md_elem = next(e for e in card["elements"] if e["tag"] == "markdown")
        self.assertIn("重要", md_elem["content"])


class TestPatchableAuthCards(unittest.TestCase):
    """Tests for the openclaw-lark-style 3-state PATCH cards."""

    def test_pending_card_has_blue_header_and_url_button(self):
        card = build_auth_pending_card(
            verification_uri="https://accounts.feishu.cn/oauth/v1/device/verify?code=ABCD",
            user_code="ABCD-1234",
            expires_in_s=600,
        )
        self.assertEqual(card["header"]["template"], "blue")
        self.assertIn("飞书授权请求", card["header"]["title"]["content"])
        action = next(e for e in card["elements"] if e["tag"] == "action")
        button = action["actions"][0]
        # Pending card uses URL link (direct browser jump), not value callback
        self.assertEqual(
            button["url"],
            "https://accounts.feishu.cn/oauth/v1/device/verify?code=ABCD",
        )
        # User code surfaces in the fallback markdown
        joined = "".join(
            e.get("content", "") for e in card["elements"] if e["tag"] == "markdown"
        )
        self.assertIn("ABCD-1234", joined)
        self.assertIn("10 分钟", joined)

    def test_pending_card_includes_scope_info_when_provided(self):
        card = build_auth_pending_card(
            "https://x", "CODE", 600, scope="calendar:calendar drive:drive",
        )
        joined = "".join(
            e.get("content", "") for e in card["elements"] if e["tag"] == "markdown"
        )
        self.assertIn("calendar:calendar", joined)
        self.assertIn("drive:drive", joined)

    def test_success_card_has_green_header_and_open_id(self):
        card = build_auth_success_card(open_id="ou_xyz", scope="calendar:calendar drive:drive")
        self.assertEqual(card["header"]["template"], "green")
        joined = "".join(
            e.get("content", "") for e in card["elements"] if e["tag"] == "markdown"
        )
        self.assertIn("ou_xyz", joined)
        self.assertIn("2", joined)  # 2 scopes

    def test_error_card_has_red_header_and_retry_button(self):
        card = build_auth_error_card(reason="access_denied: user denied")
        self.assertEqual(card["header"]["template"], "red")
        joined = "".join(
            e.get("content", "") for e in card["elements"] if e["tag"] == "markdown"
        )
        self.assertIn("access_denied", joined)
        action = next(e for e in card["elements"] if e["tag"] == "action")
        button = action["actions"][0]
        self.assertEqual(button["value"]["hermes_action"], "feishu_auth")

    def test_error_card_truncates_long_reason(self):
        card = build_auth_error_card(reason="X" * 500)
        joined = "".join(
            e.get("content", "") for e in card["elements"] if e["tag"] == "markdown"
        )
        # Reason capped at 200 chars to keep card from blowing up
        self.assertLess(joined.count("X"), 250)


if __name__ == "__main__":
    unittest.main()
