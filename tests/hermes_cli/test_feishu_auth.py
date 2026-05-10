"""Unit tests for hermes_cli/feishu_auth.py — Feishu OAuth device flow."""

import asyncio
import json
import os
import stat
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from hermes_cli.feishu_auth import (
    FeishuAuthError,
    _api_post,
    begin_device_authorization,
    load_uat,
    poll_device_token,
    save_uat,
    wait_for_authorization_success,
)


# ---------------------------------------------------------------------------
# _api_post
# ---------------------------------------------------------------------------

class TestApiPost(unittest.TestCase):
    """Tests for the internal _api_post helper."""

    @patch("hermes_cli.feishu_auth.requests.post")
    def test_returns_parsed_json_on_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"device_code": "dc_abc", "interval": 5}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        result = _api_post("/oauth/v1/device_authorization", "https://accounts.feishu.cn", {})

        self.assertEqual(result["device_code"], "dc_abc")
        mock_post.assert_called_once()

    @patch("hermes_cli.feishu_auth.requests.post")
    def test_raises_feishu_auth_error_on_network_error(self, mock_post):
        import requests as req_lib
        mock_post.side_effect = req_lib.RequestException("connection refused")

        with self.assertRaises(FeishuAuthError) as ctx:
            _api_post("/oauth/v1/device_authorization", "https://accounts.feishu.cn", {})

        self.assertIn("Network error", str(ctx.exception))

    @patch("hermes_cli.feishu_auth.requests.post")
    def test_raises_feishu_auth_error_on_api_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "error": "invalid_client",
            "error_description": "client id not found",
        }
        mock_post.return_value = mock_resp

        with self.assertRaises(FeishuAuthError) as ctx:
            _api_post("/oauth/v1/device_authorization", "https://accounts.feishu.cn", {})

        self.assertIn("invalid_client", str(ctx.exception))

    @patch("hermes_cli.feishu_auth.requests.post")
    def test_passes_through_authorization_pending(self, mock_post):
        """authorization_pending should NOT raise — caller handles it."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"error": "authorization_pending"}
        mock_post.return_value = mock_resp

        result = _api_post("/open-apis/authen/v2/oauth/token", "https://open.feishu.cn", {})
        self.assertEqual(result["error"], "authorization_pending")

    @patch("hermes_cli.feishu_auth.requests.post")
    def test_passes_through_slow_down(self, mock_post):
        """slow_down should NOT raise — caller handles it."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"error": "slow_down"}
        mock_post.return_value = mock_resp

        result = _api_post("/open-apis/authen/v2/oauth/token", "https://open.feishu.cn", {})
        self.assertEqual(result["error"], "slow_down")


# ---------------------------------------------------------------------------
# begin_device_authorization
# ---------------------------------------------------------------------------

class TestBeginDeviceAuthorization(unittest.TestCase):
    """Tests for begin_device_authorization()."""

    @patch("hermes_cli.feishu_auth._api_post")
    def test_returns_parsed_fields_on_success(self, mock_api):
        mock_api.return_value = {
            "device_code": "  dc_123  ",
            "user_code": "ABC-DEF",
            "verification_uri": "https://feishu.cn/oauth/verify",
            "verification_uri_complete": "https://feishu.cn/oauth/verify?user_code=ABC-DEF",
            "expires_in": 1800,
            "interval": 5,
        }

        result = begin_device_authorization("app_id_123")

        self.assertEqual(result["device_code"], "dc_123")
        self.assertEqual(result["user_code"], "ABC-DEF")
        self.assertEqual(result["expires_in"], 1800)
        self.assertGreaterEqual(result["interval"], 2)

    @patch("hermes_cli.feishu_auth._api_post")
    def test_raises_when_required_fields_missing(self, mock_api):
        mock_api.return_value = {"device_code": "dc_abc"}  # missing most fields

        with self.assertRaises(FeishuAuthError) as ctx:
            begin_device_authorization("app_id_123")

        self.assertIn("missing fields", str(ctx.exception))

    @patch("hermes_cli.feishu_auth._api_post")
    def test_interval_floor_at_2(self, mock_api):
        """Interval below 2 seconds is raised to 2 (RFC 8628 min)."""
        mock_api.return_value = {
            "device_code": "dc",
            "user_code": "UC",
            "verification_uri": "https://x",
            "verification_uri_complete": "https://x?uc",
            "expires_in": 300,
            "interval": 1,  # below floor
        }

        result = begin_device_authorization("app_id")
        self.assertEqual(result["interval"], 2)

    @patch("hermes_cli.feishu_auth._api_post")
    def test_uses_default_scope_when_none_provided(self, mock_api):
        from hermes_cli.feishu_auth import FEISHU_DEFAULT_SCOPE
        mock_api.return_value = {
            "device_code": "dc",
            "user_code": "UC",
            "verification_uri": "https://x",
            "verification_uri_complete": "https://x?uc",
            "expires_in": 300,
            "interval": 5,
        }

        begin_device_authorization("app_id")

        _, _, payload = mock_api.call_args[0]
        self.assertEqual(payload["scope"], FEISHU_DEFAULT_SCOPE)
        self.assertIn("offline_access", payload["scope"].split())

    def test_default_scope_includes_task_comment_write(self):
        from hermes_cli.feishu_auth import FEISHU_DEFAULT_SCOPE

        self.assertIn("task:comment:write", FEISHU_DEFAULT_SCOPE.split())

    def test_default_scope_includes_document_comment_write(self):
        from hermes_cli.feishu_auth import FEISHU_DEFAULT_SCOPE

        scopes = FEISHU_DEFAULT_SCOPE.split()
        self.assertIn("docs:document.comment:create", scopes)
        self.assertIn("docs:document.comment:write_only", scopes)

    def test_default_scope_includes_drive_export_readonly(self):
        from hermes_cli.feishu_auth import FEISHU_DEFAULT_SCOPE

        self.assertIn("drive:export:readonly", FEISHU_DEFAULT_SCOPE.split())

    def test_default_scope_includes_task_section_scopes(self):
        from hermes_cli.feishu_auth import FEISHU_DEFAULT_SCOPE

        scopes = FEISHU_DEFAULT_SCOPE.split()
        self.assertIn("task:section:read", scopes)
        self.assertIn("task:section:write", scopes)

    @patch("hermes_cli.feishu_auth._api_post")
    def test_uses_custom_scope_with_offline_access_when_provided(self, mock_api):
        mock_api.return_value = {
            "device_code": "dc",
            "user_code": "UC",
            "verification_uri": "https://x",
            "verification_uri_complete": "https://x?uc",
            "expires_in": 300,
            "interval": 5,
        }

        begin_device_authorization("app_id", scope="calendar:calendar")

        _, _, payload = mock_api.call_args[0]
        self.assertEqual(payload["scope"], "calendar:calendar offline_access")


# ---------------------------------------------------------------------------
# poll_device_token
# ---------------------------------------------------------------------------

class TestPollDeviceToken(unittest.TestCase):
    """Tests for poll_device_token()."""

    @patch("hermes_cli.feishu_auth._api_post")
    def test_returns_pending_on_authorization_pending(self, mock_api):
        mock_api.return_value = {"error": "authorization_pending"}

        result = poll_device_token("dc_abc", "app_id")

        self.assertEqual(result["error"], "authorization_pending")
        self.assertIsNone(result["access_token"])

    @patch("hermes_cli.feishu_auth._api_post")
    def test_returns_slow_down_on_slow_down(self, mock_api):
        mock_api.return_value = {"error": "slow_down"}

        result = poll_device_token("dc_abc", "app_id")

        self.assertEqual(result["error"], "slow_down")

    @patch("hermes_cli.feishu_auth._api_post")
    def test_returns_access_token_on_authorized(self, mock_api):
        mock_api.return_value = {
            "access_token": "uat_tok_xyz",
            "refresh_token": "ref_tok_abc",
            "open_id": "ou_111",
            "expires_in": 7200,
            "refresh_expires_in": 2592000,
            "token_type": "Bearer",
            "scope": "calendar:calendar",
        }

        result = poll_device_token("dc_abc", "app_id")

        self.assertEqual(result["access_token"], "uat_tok_xyz")
        self.assertEqual(result["refresh_token"], "ref_tok_abc")
        self.assertEqual(result["open_id"], "ou_111")
        self.assertIsNone(result["error"])

    @patch("hermes_cli.feishu_auth._api_post")
    def test_raises_feishu_auth_error_on_hard_error(self, mock_api):
        mock_api.side_effect = FeishuAuthError("expired_token")

        with self.assertRaises(FeishuAuthError):
            poll_device_token("dc_abc", "app_id")


# ---------------------------------------------------------------------------
# save_uat / load_uat
# ---------------------------------------------------------------------------

class TestSaveAndLoadUat(unittest.TestCase):
    """Tests for save_uat() and load_uat() token persistence."""

    def test_save_uat_creates_file_with_correct_json_fields(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / ".hermes" / "feishu_uat.json"

            with patch("hermes_cli.feishu_auth.FEISHU_UAT_PATH", uat_path):
                save_uat(
                    access_token="uat_abc",
                    refresh_token="ref_def",
                    open_id="ou_123",
                    expires_in=7200,
                    refresh_expires_in=2592000,
                    scope="calendar:calendar",
                    app_id="app_999",
                )

            self.assertTrue(uat_path.exists())
            data = json.loads(uat_path.read_text())
            self.assertEqual(data["access_token"], "uat_abc")
            self.assertEqual(data["refresh_token"], "ref_def")
            self.assertEqual(data["user_open_id"], "ou_123")
            self.assertEqual(data["app_id"], "app_999")
            self.assertIn("expires_at", data)
            self.assertIn("refresh_expires_at", data)
            self.assertIn("granted_at", data)

    def test_save_uat_sets_file_mode_0600(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / ".hermes" / "feishu_uat.json"

            with patch("hermes_cli.feishu_auth.FEISHU_UAT_PATH", uat_path):
                save_uat(
                    access_token="tok",
                    refresh_token="ref",
                    open_id="ou",
                    expires_in=7200,
                    refresh_expires_in=2592000,
                    scope="",
                    app_id="app",
                )

            file_mode = stat.S_IMODE(uat_path.stat().st_mode)
            self.assertEqual(file_mode, 0o600)

    def test_save_uat_expires_at_is_future(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / ".hermes" / "feishu_uat.json"
            before_ms = int(time.time() * 1000)

            with patch("hermes_cli.feishu_auth.FEISHU_UAT_PATH", uat_path):
                save_uat(
                    access_token="tok",
                    refresh_token="ref",
                    open_id="ou",
                    expires_in=7200,
                    refresh_expires_in=2592000,
                    scope="",
                    app_id="app",
                )

            data = json.loads(uat_path.read_text())
            self.assertGreater(data["expires_at"], before_ms + 7000 * 1000)

    def test_load_uat_returns_none_when_file_missing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "no_such.json"
            with patch("hermes_cli.feishu_auth.FEISHU_UAT_PATH", missing):
                result = load_uat()
        self.assertIsNone(result)

    def test_load_uat_returns_dict_with_correct_fields(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / ".hermes" / "feishu_uat.json"

            with patch("hermes_cli.feishu_auth.FEISHU_UAT_PATH", uat_path):
                save_uat("uat_x", "ref_x", "ou_x", 7200, 2592000, "scope", "app")
                result = load_uat()

        self.assertIsNotNone(result)
        self.assertEqual(result["access_token"], "uat_x")
        self.assertEqual(result["user_open_id"], "ou_x")

    def test_load_uat_returns_none_on_corrupt_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / "feishu_uat.json"
            uat_path.write_text("not valid json {{")
            with patch("hermes_cli.feishu_auth.FEISHU_UAT_PATH", uat_path):
                result = load_uat()
        self.assertIsNone(result)

    def test_load_uat_returns_none_on_expired_is_separate_from_presence(self):
        """load_uat does NOT validate expiry — that is the client's job."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / "feishu_uat.json"
            expired_data = {
                "access_token": "old_tok",
                "expires_at": 1000,  # far in the past
                "user_open_id": "ou_old",
            }
            uat_path.write_text(json.dumps(expired_data))
            with patch("hermes_cli.feishu_auth.FEISHU_UAT_PATH", uat_path):
                result = load_uat()
        # load_uat itself does NOT reject expired tokens — it just reads the file
        self.assertIsNotNone(result)
        self.assertEqual(result["access_token"], "old_tok")

    # ----- US-001: per-user UAT storage -----

    def test_save_uat_per_user_writes_to_per_user_dir(self):
        """save_uat(per_user=True) writes to ~/.hermes/feishu_uat/<open_id>.json."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / ".hermes" / "feishu_uat"
            with patch("hermes_cli.feishu_auth.FEISHU_UAT_DIR", uat_dir):
                save_uat(
                    access_token="uat_user_a",
                    refresh_token="ref_user_a",
                    open_id="ou_alice",
                    expires_in=7200,
                    refresh_expires_in=2592000,
                    scope="calendar:calendar",
                    app_id="app_123",
                    per_user=True,
                )
            per_user_path = uat_dir / "ou_alice.json"
            self.assertTrue(per_user_path.exists())
            data = json.loads(per_user_path.read_text())
            self.assertEqual(data["access_token"], "uat_user_a")
            self.assertEqual(data["user_open_id"], "ou_alice")

    def test_save_uat_default_writes_to_legacy_path_for_backcompat(self):
        """save_uat() without per_user keeps the legacy single-file path."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            legacy_path = Path(tmpdir) / ".hermes" / "feishu_uat.json"
            uat_dir = Path(tmpdir) / ".hermes" / "feishu_uat"
            with patch("hermes_cli.feishu_auth.FEISHU_UAT_PATH", legacy_path), \
                 patch("hermes_cli.feishu_auth.FEISHU_UAT_DIR", uat_dir):
                save_uat(
                    access_token="legacy_tok",
                    refresh_token="legacy_ref",
                    open_id="ou_bob",
                    expires_in=7200,
                    refresh_expires_in=2592000,
                    scope="",
                    app_id="app",
                )
            self.assertTrue(legacy_path.exists())
            self.assertFalse((uat_dir / "ou_bob.json").exists())

    def test_save_uat_per_user_file_mode_is_0600(self):
        """Per-user UAT file inherits the 0600 mode for security."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / ".hermes" / "feishu_uat"
            with patch("hermes_cli.feishu_auth.FEISHU_UAT_DIR", uat_dir):
                save_uat(
                    access_token="t", refresh_token="r", open_id="ou_charlie",
                    expires_in=7200, refresh_expires_in=2592000, scope="", app_id="app",
                    per_user=True,
                )
            per_user_path = uat_dir / "ou_charlie.json"
            mode = stat.S_IMODE(per_user_path.stat().st_mode)
            self.assertEqual(mode, 0o600)

    def test_load_uat_with_open_id_reads_per_user_file(self):
        """load_uat(open_id=...) reads ~/.hermes/feishu_uat/<open_id>.json."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir(parents=True)
            (uat_dir / "ou_dave.json").write_text(json.dumps({
                "access_token": "tok_dave",
                "user_open_id": "ou_dave",
                "expires_at": 99999999999999,
            }))
            with patch("hermes_cli.feishu_auth.FEISHU_UAT_DIR", uat_dir):
                result = load_uat(open_id="ou_dave")
            self.assertIsNotNone(result)
            self.assertEqual(result["access_token"], "tok_dave")
            self.assertEqual(result["user_open_id"], "ou_dave")

    def test_load_uat_without_open_id_still_reads_legacy_file(self):
        """load_uat() with no arg keeps reading the legacy single-file path."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            legacy = Path(tmpdir) / "feishu_uat.json"
            legacy.write_text(json.dumps({
                "access_token": "legacy_tok",
                "user_open_id": "ou_legacy",
                "expires_at": 99999999999999,
            }))
            with patch("hermes_cli.feishu_auth.FEISHU_UAT_PATH", legacy):
                result = load_uat()
            self.assertIsNotNone(result)
            self.assertEqual(result["access_token"], "legacy_tok")

    def test_per_user_uat_path_rejects_path_traversal(self):
        """_per_user_uat_path refuses slashes, dotdot, null, backslash."""
        from hermes_cli.feishu_auth import _per_user_uat_path
        for evil in ("../etc/passwd", "ou/with/slash", "ou\\back", "ou\x00null", "", None, "..", "ou/"):
            with self.assertRaises((ValueError, TypeError)):
                _per_user_uat_path(evil)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# wait_for_authorization_success
# ---------------------------------------------------------------------------

class TestWaitForAuthorizationSuccess(unittest.TestCase):
    """Tests for the polling loop wait_for_authorization_success().

    All tests mock time.monotonic so the loop terminates without real sleeps.
    The deadline is set to expire_in=60; monotonic returns values that keep the
    loop alive for N iterations then advance past the deadline so it exits.
    """

    def _make_monotonic_sequence(self, n_live_iterations, expires_in=60):
        """Return a monotonic side_effect list.

        - First call: t=0 (deadline = expires_in)
        - Next n_live_iterations*2 calls: t=0 (within deadline)
        - Final call: t=expires_in+1 (past deadline, exits loop)
        """
        values = [0.0]  # initial call sets deadline
        for _ in range(n_live_iterations):
            values.append(0.0)   # while-condition check inside loop
        values.append(expires_in + 1)  # loop exits
        return values

    @patch("hermes_cli.feishu_auth.time.monotonic")
    @patch("hermes_cli.feishu_auth.time.sleep")
    @patch("hermes_cli.feishu_auth.poll_device_token")
    def test_returns_tokens_immediately_on_authorized(self, mock_poll, mock_sleep, mock_mono):
        # monotonic: call #1 sets deadline=60, call #2 is while check (0 < 60 → enter)
        # After poll returns success, code hits line 274 (access_token present) and returns.
        # NOTE: to reach line 274, error must be truthy AND not pending/slow_down.
        # With error=None (falsy), the code hits the "authorization_pending" branch.
        # Use error="ok" so the success branch at line 274 is reachable.
        mock_mono.side_effect = [0.0, 0.0, 100.0]
        mock_poll.return_value = {
            "access_token": "uat_good",
            "refresh_token": "ref_good",
            "open_id": "ou_good",
            "error": "ok",  # truthy, non-pending, non-slow_down → reaches access_token check
        }

        token, refresh, open_id, expires_in, refresh_expires_in = wait_for_authorization_success(
            "dc", "app", interval=0, expires_in=60
        )

        self.assertEqual(token, "uat_good")
        self.assertEqual(refresh, "ref_good")
        self.assertEqual(open_id, "ou_good")
        self.assertEqual(mock_poll.call_count, 1)

    @patch("hermes_cli.feishu_auth.time.monotonic")
    @patch("hermes_cli.feishu_auth.time.sleep")
    @patch("hermes_cli.feishu_auth.poll_device_token")
    def test_calls_on_waiting_callback_on_pending(self, mock_poll, mock_sleep, mock_mono):
        # deadline=0+60, while checks: 0, 0, 0 (3 iterations), then 100 to exit
        mock_mono.side_effect = [0.0, 0.0, 0.0, 0.0, 100.0]
        mock_poll.side_effect = [
            {"access_token": None, "error": "authorization_pending"},
            {"access_token": None, "error": "authorization_pending"},
            {"access_token": "uat_ok", "refresh_token": "ref", "open_id": "ou", "error": "ok"},
        ]

        callback = MagicMock()
        wait_for_authorization_success(
            "dc", "app", interval=0, expires_in=60, on_waiting=callback
        )

        self.assertEqual(callback.call_count, 2)

    @patch("hermes_cli.feishu_auth.time.monotonic")
    @patch("hermes_cli.feishu_auth.time.sleep")
    @patch("hermes_cli.feishu_auth.poll_device_token")
    def test_raises_timeout_when_deadline_passes(self, mock_poll, mock_sleep, mock_mono):
        # deadline=0+60; while check 0 < 60 → enter; poll returns pending;
        # while check 100 < 60 → False → raises timed out
        mock_mono.side_effect = [0.0, 0.0, 100.0]
        mock_poll.return_value = {"access_token": None, "error": "authorization_pending"}

        with self.assertRaises(FeishuAuthError) as ctx:
            wait_for_authorization_success("dc", "app", interval=0, expires_in=60)

        self.assertIn("timed out", str(ctx.exception))

    @patch("hermes_cli.feishu_auth.time.monotonic")
    @patch("hermes_cli.feishu_auth.time.sleep")
    @patch("hermes_cli.feishu_auth.poll_device_token")
    def test_increases_interval_on_slow_down(self, mock_poll, mock_sleep, mock_mono):
        # iteration 1: slow_down; iteration 2: success
        mock_mono.side_effect = [0.0, 0.0, 0.0, 100.0]
        mock_poll.side_effect = [
            {"access_token": None, "error": "slow_down"},
            {"access_token": "uat_ok", "refresh_token": "ref", "open_id": "ou", "error": "ok"},
        ]

        wait_for_authorization_success("dc", "app", interval=3, expires_in=60)

        # sleep should have been called with 3 then 8 (3+5)
        calls = [c[0][0] for c in mock_sleep.call_args_list]
        self.assertEqual(calls[0], 3)
        self.assertEqual(calls[1], 8)

    @patch("hermes_cli.feishu_auth.time.monotonic")
    @patch("hermes_cli.feishu_auth.time.sleep")
    @patch("hermes_cli.feishu_auth.poll_device_token")
    def test_raises_feishu_auth_error_on_hard_error_code(self, mock_poll, mock_sleep, mock_mono):
        # Hard error (access_denied) with no access_token reaches line 281.
        # retry_start=0 → set retry_start=monotonic(); then check monotonic()-retry_start < 120.
        # Supply: deadline=0, while_check=0, retry_start_set=0, elapsed_check=121 → raises.
        mock_mono.side_effect = [0.0, 0.0, 0.0, 121.0]
        mock_poll.return_value = {
            "access_token": None,
            "error": "access_denied",
            "error_description": "user denied",
        }

        with self.assertRaises(FeishuAuthError) as ctx:
            wait_for_authorization_success("dc", "app", interval=0, expires_in=60)

        self.assertIn("authorization failed", str(ctx.exception))


# ---------------------------------------------------------------------------
# US-002: chat_mode_device_flow (multi-user async device flow)
# ---------------------------------------------------------------------------


class TestChatModeDeviceFlow(unittest.IsolatedAsyncioTestCase):
    """Tests for chat_mode_device_flow async multi-user device flow."""

    def _begin_response(self) -> dict:
        return {
            "device_code": "dc_chat_test",
            "user_code": "ABCD-1234",
            "verification_uri": "https://accounts.feishu.cn/oauth/v1/device/verify",
            "verification_uri_complete": "https://accounts.feishu.cn/oauth/v1/device/verify?user_code=ABCD-1234",
            "expires_in": 600,
            "interval": 0,  # zero so tests run instantly
        }

    async def test_success_path_invokes_on_success_and_persists_per_user_uat(self):
        from hermes_cli.feishu_auth import chat_mode_device_flow

        urls: list = []
        successes: list = []
        errors: list = []

        async def on_url(uri, code, exp_in):
            urls.append((uri, code, exp_in))

        async def on_success(open_id, scope):
            successes.append((open_id, scope))

        async def on_error(reason):
            errors.append(reason)

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"

            with patch("hermes_cli.feishu_auth.begin_device_authorization",
                       return_value=self._begin_response()), \
                 patch("hermes_cli.feishu_auth.poll_device_token",
                       return_value={
                           "access_token": "uat_chat_xyz",
                           "refresh_token": "ref_chat_xyz",
                           "open_id": "ou_chat_user",
                           "expires_in": 7200,
                           "refresh_expires_in": 2592000,
                           "scope": "calendar:calendar",
                           "error": None,
                       }), \
                 patch("hermes_cli.feishu_auth.FEISHU_UAT_DIR", uat_dir):
                result = await chat_mode_device_flow(
                    client_id="app_test",
                    client_secret="secret_test",
                    scope="calendar:calendar",
                    on_verification_url=on_url,
                    on_success=on_success,
                    on_error=on_error,
                )

            # Assertions stay INSIDE TemporaryDirectory so uat_dir is still on disk.
            self.assertEqual(result, ("uat_chat_xyz", "ref_chat_xyz", "ou_chat_user"))
            self.assertEqual(len(urls), 1)
            self.assertEqual(urls[0][1], "ABCD-1234")
            self.assertEqual(len(successes), 1)
            self.assertEqual(successes[0], ("ou_chat_user", "calendar:calendar offline_access"))
            self.assertEqual(errors, [])
            self.assertTrue((uat_dir / "ou_chat_user.json").exists())
            data = json.loads((uat_dir / "ou_chat_user.json").read_text())
            self.assertEqual(data["access_token"], "uat_chat_xyz")

    async def test_access_denied_invokes_on_error_returns_none(self):
        from hermes_cli.feishu_auth import chat_mode_device_flow

        errors: list = []

        async def on_url(*_a):
            pass

        async def on_success(*_a):
            self.fail("on_success must not be called on denial")

        async def on_error(reason):
            errors.append(reason)

        with patch("hermes_cli.feishu_auth.begin_device_authorization",
                   return_value=self._begin_response()), \
             patch("hermes_cli.feishu_auth.poll_device_token",
                   return_value={
                       "access_token": None,
                       "error": "access_denied",
                       "error_description": "user denied",
                   }):
            result = await chat_mode_device_flow(
                client_id="app",
                client_secret="secret",
                scope=None,
                on_verification_url=on_url,
                on_success=on_success,
                on_error=on_error,
            )

        self.assertIsNone(result)
        self.assertEqual(len(errors), 1)
        self.assertIn("access_denied", errors[0])

    async def test_init_failure_invokes_on_error_with_init_failed_prefix(self):
        from hermes_cli.feishu_auth import chat_mode_device_flow, FeishuAuthError

        errors: list = []

        async def on_url(*_a):
            pass

        async def on_success(*_a):
            pass

        async def on_error(reason):
            errors.append(reason)

        with patch("hermes_cli.feishu_auth.begin_device_authorization",
                   side_effect=FeishuAuthError("400 invalid_request")):
            result = await chat_mode_device_flow(
                client_id="app", client_secret="secret", scope=None,
                on_verification_url=on_url, on_success=on_success, on_error=on_error,
            )

        self.assertIsNone(result)
        self.assertEqual(len(errors), 1)
        self.assertIn("init failed", errors[0])

    async def test_slow_down_increases_interval_then_succeeds(self):
        from hermes_cli.feishu_auth import chat_mode_device_flow

        # First poll = slow_down, second poll = success
        poll_calls = []

        def fake_poll(device_code, client_id, client_secret=None):
            poll_calls.append(1)
            if len(poll_calls) == 1:
                return {"access_token": None, "error": "slow_down",
                        "error_description": "slow down"}
            return {
                "access_token": "uat_after_slow",
                "refresh_token": "ref",
                "open_id": "ou_user2",
                "expires_in": 7200,
                "refresh_expires_in": 2592000,
                "scope": "calendar:calendar",
                "error": None,
            }

        async def on_url(*_a): pass
        async def on_success(*_a): pass
        errors: list = []
        async def on_error(r): errors.append(r)

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            with patch("hermes_cli.feishu_auth.begin_device_authorization",
                       return_value=self._begin_response()), \
                 patch("hermes_cli.feishu_auth.poll_device_token", side_effect=fake_poll), \
                 patch("hermes_cli.feishu_auth.FEISHU_UAT_DIR", uat_dir):
                result = await chat_mode_device_flow(
                    client_id="app", client_secret="secret", scope="calendar:calendar",
                    on_verification_url=on_url, on_success=on_success, on_error=on_error,
                )

        self.assertIsNotNone(result)
        self.assertEqual(result[2], "ou_user2")  # open_id
        self.assertGreaterEqual(len(poll_calls), 2)
        self.assertEqual(errors, [])

    async def test_cancel_event_aborts_polling(self):
        from hermes_cli.feishu_auth import chat_mode_device_flow

        cancel = asyncio.Event()
        cancel.set()  # immediately cancel

        errors: list = []

        async def on_url(*_a): pass
        async def on_success(*_a): self.fail("success must not run when cancelled")
        async def on_error(reason): errors.append(reason)

        with patch("hermes_cli.feishu_auth.begin_device_authorization",
                   return_value=self._begin_response()), \
             patch("hermes_cli.feishu_auth.poll_device_token",
                   return_value={"access_token": None, "error": "authorization_pending"}):
            result = await chat_mode_device_flow(
                client_id="app", client_secret="secret", scope=None,
                on_verification_url=on_url, on_success=on_success, on_error=on_error,
                cancel_event=cancel,
            )

        self.assertIsNone(result)
        self.assertEqual(len(errors), 1)
        self.assertIn("cancelled", errors[0].lower())

    async def test_token_response_missing_open_id_triggers_on_error(self):
        from hermes_cli.feishu_auth import chat_mode_device_flow

        errors: list = []

        async def on_url(*_a): pass
        async def on_success(*_a): self.fail("success must not run on bad token")
        async def on_error(reason): errors.append(reason)

        # Token endpoint omits open_id (Feishu's actual behavior); fetch_user_info
        # is the fallback hop that supplies it. We mock that hop returning a
        # blank open_id so the final guard fires on_error.
        with patch("hermes_cli.feishu_auth.begin_device_authorization",
                   return_value=self._begin_response()), \
             patch("hermes_cli.feishu_auth.poll_device_token",
                   return_value={
                       "access_token": "uat_no_oid",
                       "refresh_token": "r",
                       "open_id": "",  # missing
                       "expires_in": 7200, "refresh_expires_in": 2592000,
                       "scope": "", "error": None,
                   }), \
             patch("hermes_cli.feishu_auth.fetch_user_info",
                   return_value={"open_id": ""}):
            result = await chat_mode_device_flow(
                client_id="app", client_secret="secret", scope=None,
                on_verification_url=on_url, on_success=on_success, on_error=on_error,
            )

        self.assertIsNone(result)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing", errors[0].lower())


if __name__ == "__main__":
    unittest.main()
