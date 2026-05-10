"""Unit tests for tools/feishu_oapi_client.py — FeishuClient factory and error classes."""

import asyncio
import json
import os
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.feishu_oapi_client import (
    AppScopeMissingError,
    FeishuClient,
    NeedAuthorizationError,
    UserAuthRequiredError,
    UserScopeInsufficientError,
    TOOLS_METADATA,
    _load_uat,
    raise_for_feishu_errcode,
)


# ---------------------------------------------------------------------------
# Semantic error classes
# ---------------------------------------------------------------------------

class TestErrorClasses(unittest.TestCase):
    """Tests for the four semantic auth error classes."""

    def test_need_authorization_error_message_contains_open_id(self):
        exc = NeedAuthorizationError(user_open_id="ou_abc", reason="token expired")
        self.assertIn("ou_abc", str(exc))
        self.assertIn("token expired", str(exc))
        self.assertEqual(exc.user_open_id, "ou_abc")

    def test_need_authorization_error_defaults_to_unknown(self):
        exc = NeedAuthorizationError()
        self.assertIn("unknown", str(exc))

    def test_app_scope_missing_error_message_contains_scope(self):
        exc = AppScopeMissingError("app_123", "feishu_calendar_list_events", ["calendar:calendar"])
        self.assertIn("calendar:calendar", str(exc))
        self.assertIn("app_123", str(exc))
        self.assertEqual(exc.app_id, "app_123")
        self.assertEqual(exc.missing_scopes, ["calendar:calendar"])

    def test_user_auth_required_error_message_contains_user_id(self):
        exc = UserAuthRequiredError("ou_xyz", "feishu_doc_read", ["docs:document"])
        self.assertIn("ou_xyz", str(exc))
        self.assertEqual(exc.user_open_id, "ou_xyz")

    def test_user_scope_insufficient_error_message_contains_scope(self):
        exc = UserScopeInsufficientError("ou_abc", "feishu_bitable_list_records", ["bitable:app"])
        self.assertIn("bitable:app", str(exc))
        self.assertEqual(exc.missing_scopes, ["bitable:app"])


# ---------------------------------------------------------------------------
# raise_for_feishu_errcode
# ---------------------------------------------------------------------------

class TestRaiseForFeishuErrcode(unittest.TestCase):
    """Tests for errcode → semantic error mapping."""

    def test_errcode_99991672_raises_app_scope_missing(self):
        with self.assertRaises(AppScopeMissingError):
            raise_for_feishu_errcode(99991672, "scope missing", app_id="app_1", api_name="tool")

    def test_errcode_99991679_raises_user_auth_required(self):
        with self.assertRaises(UserAuthRequiredError):
            raise_for_feishu_errcode(99991679, "user not authorized", user_open_id="ou_1")

    def test_errcode_99991668_raises_need_authorization_token_invalid(self):
        with self.assertRaises(NeedAuthorizationError):
            raise_for_feishu_errcode(99991668, "token invalid")

    def test_errcode_99991677_raises_need_authorization_token_expired(self):
        with self.assertRaises(NeedAuthorizationError):
            raise_for_feishu_errcode(99991677, "token expired")

    def test_zero_errcode_does_not_raise(self):
        """code=0 means success — must not raise."""
        raise_for_feishu_errcode(0, "ok")  # should not raise

    def test_unknown_errcode_does_not_raise(self):
        """Unknown non-zero errcode is caller's responsibility."""
        raise_for_feishu_errcode(12345, "generic error")  # should not raise


# ---------------------------------------------------------------------------
# _load_uat
# ---------------------------------------------------------------------------

class TestLoadUat(unittest.TestCase):
    """Tests for _load_uat() freshness validation."""

    def _write_uat(self, path: Path, expires_at_ms: int, access_token: str = "tok_x"):
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "access_token": access_token,
            "user_open_id": "ou_test",
            "expires_at": expires_at_ms,
        }
        path.write_text(json.dumps(data))

    def test_raises_need_authorization_when_file_missing(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "no_uat.json"
            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", missing):
                with self.assertRaises(NeedAuthorizationError) as ctx:
                    _load_uat()
        self.assertIn("no token file", str(ctx.exception))

    def test_raises_need_authorization_when_token_expires_within_60s(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / "feishu_uat.json"
            # 30 seconds from now — within 60s headroom
            near_expiry_ms = int(time.time() * 1000) + 30 * 1000
            self._write_uat(uat_path, near_expiry_ms)

            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", uat_path):
                with self.assertRaises(NeedAuthorizationError) as ctx:
                    _load_uat()

        self.assertIn("expired or expiring soon", str(ctx.exception))

    def test_returns_token_dict_when_valid(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / "feishu_uat.json"
            # 2 hours from now — well within validity
            future_ms = int(time.time() * 1000) + 7200 * 1000
            self._write_uat(uat_path, future_ms, access_token="valid_tok")

            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", uat_path):
                data = _load_uat()

        self.assertEqual(data["access_token"], "valid_tok")

    def test_raises_need_authorization_when_access_token_empty(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / "feishu_uat.json"
            future_ms = int(time.time() * 1000) + 7200 * 1000
            uat_path.write_text(json.dumps({"access_token": "", "expires_at": future_ms}))

            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", uat_path):
                with self.assertRaises(NeedAuthorizationError):
                    _load_uat()

    def test_raises_need_authorization_on_corrupt_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / "feishu_uat.json"
            uat_path.write_text("{corrupt json")

            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", uat_path):
                with self.assertRaises(NeedAuthorizationError):
                    _load_uat()


# ---------------------------------------------------------------------------
# FeishuClient.for_user()
# ---------------------------------------------------------------------------

class TestFeishuClientForUser(unittest.TestCase):
    """Tests for FeishuClient.for_user() factory method."""

    def setUp(self):
        # Clear the class-level cache between tests
        FeishuClient._cache.clear()

    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_id", "FEISHU_APP_SECRET": "secret"})
    def test_raises_need_authorization_when_uat_file_missing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "no_uat.json"
            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", missing):
                with patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=None):
                    with self.assertRaises(NeedAuthorizationError):
                        FeishuClient.for_user()

    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_id", "FEISHU_APP_SECRET": "secret"})
    def test_raises_need_authorization_when_token_expires_within_60s(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / "feishu_uat.json"
            near_ms = int(time.time() * 1000) + 30 * 1000
            uat_path.write_text(json.dumps({
                "access_token": "tok",
                "expires_at": near_ms,
                "user_open_id": "ou_x",
            }))

            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", uat_path):
                with patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=None):
                    with self.assertRaises(NeedAuthorizationError):
                        FeishuClient.for_user()

    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_id", "FEISHU_APP_SECRET": "secret"})
    def test_returns_client_with_access_token_injected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_path = Path(tmpdir) / "feishu_uat.json"
            future_ms = int(time.time() * 1000) + 7200 * 1000
            uat_path.write_text(json.dumps({
                "access_token": "valid_uat",
                "expires_at": future_ms,
                "user_open_id": "ou_valid",
            }))

            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", uat_path):
                with patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=MagicMock()):
                    client = FeishuClient.for_user()

        self.assertEqual(client.access_token, "valid_uat")
        self.assertEqual(client.user_open_id, "ou_valid")
        self.assertTrue(client.ephemeral)

    def test_raises_value_error_when_env_vars_missing(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch("tools.feishu_oapi_client._resolve_feishu_credentials",
                   return_value=("", "", "feishu")):
            with self.assertRaises(ValueError):
                FeishuClient.for_user()

    # ----- US-004: ContextVar propagation -----

    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_id", "FEISHU_APP_SECRET": "secret"})
    def test_for_user_uses_contextvar_when_no_arg(self):
        """US-004: for_user() with no arg reads current_sender_open_id contextvar."""
        from tools.feishu_oapi_client import sender_open_id_scope
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()
            future_ms = int(time.time() * 1000) + 7200 * 1000
            (uat_dir / "ou_ctx_user.json").write_text(json.dumps({
                "access_token": "ctxvar_tok",
                "expires_at": future_ms,
                "user_open_id": "ou_ctx_user",
            }))

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir), \
                 patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=MagicMock()):
                with sender_open_id_scope("ou_ctx_user"):
                    client = FeishuClient.for_user()  # NO arg

            self.assertEqual(client.access_token, "ctxvar_tok")
            self.assertEqual(client.user_open_id, "ou_ctx_user")

    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_id", "FEISHU_APP_SECRET": "secret"})
    def test_for_user_arg_overrides_contextvar(self):
        """Explicit user_open_id arg wins over contextvar."""
        from tools.feishu_oapi_client import sender_open_id_scope
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()
            future_ms = int(time.time() * 1000) + 7200 * 1000
            (uat_dir / "ou_ctx.json").write_text(json.dumps({
                "access_token": "ctx_tok", "expires_at": future_ms, "user_open_id": "ou_ctx",
            }))
            (uat_dir / "ou_arg.json").write_text(json.dumps({
                "access_token": "arg_tok", "expires_at": future_ms, "user_open_id": "ou_arg",
            }))

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir), \
                 patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=MagicMock()):
                with sender_open_id_scope("ou_ctx"):
                    client = FeishuClient.for_user(user_open_id="ou_arg")  # arg wins

            self.assertEqual(client.access_token, "arg_tok")

    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_id", "FEISHU_APP_SECRET": "secret"})
    def test_for_user_auto_refreshes_expiring_per_user_uat(self):
        """Per-user tool calls refresh an expiring UAT immediately, not only via daemon."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()
            near_ms = int(time.time() * 1000) + 30 * 1000
            uat_path = uat_dir / "ou_refresh.json"
            uat_path.write_text(json.dumps({
                "access_token": "old_tok",
                "refresh_token": "old_refresh",
                "expires_at": near_ms,
                "user_open_id": "ou_refresh",
            }))
            calls = []

            def fake_refresh(open_id, app_id, app_secret):
                calls.append((open_id, app_id, app_secret))
                uat_path.write_text(json.dumps({
                    "access_token": "new_tok",
                    "refresh_token": "new_refresh",
                    "expires_at": int(time.time() * 1000) + 7200 * 1000,
                    "user_open_id": "ou_refresh",
                }))

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir), \
                 patch("hermes_cli.feishu_auth.refresh_uat_for_user", side_effect=fake_refresh), \
                 patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=MagicMock()):
                client = FeishuClient.for_user(user_open_id="ou_refresh")

            self.assertEqual(calls, [("ou_refresh", "app_id", "secret")])
            self.assertEqual(client.access_token, "new_tok")

    def test_sender_open_id_scope_resets_after_with_block(self):
        """ContextVar reverts after sender_open_id_scope() exits (no leak)."""
        from tools.feishu_oapi_client import sender_open_id_scope, current_sender_open_id
        self.assertIsNone(current_sender_open_id.get())
        with sender_open_id_scope("ou_inside"):
            self.assertEqual(current_sender_open_id.get(), "ou_inside")
        # After exit
        self.assertIsNone(current_sender_open_id.get())

    def test_sender_open_id_scope_resets_even_on_exception(self):
        """ContextVar reverts even if the with-block raises."""
        from tools.feishu_oapi_client import sender_open_id_scope, current_sender_open_id
        self.assertIsNone(current_sender_open_id.get())
        with self.assertRaises(RuntimeError):
            with sender_open_id_scope("ou_with_err"):
                raise RuntimeError("boom")
        self.assertIsNone(current_sender_open_id.get())

    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_id", "FEISHU_APP_SECRET": "secret"})
    def test_for_user_falls_back_to_legacy_when_contextvar_unset(self):
        """No arg + no contextvar → legacy single-file path."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            legacy = Path(tmpdir) / "feishu_uat.json"
            future_ms = int(time.time() * 1000) + 7200 * 1000
            legacy.write_text(json.dumps({
                "access_token": "legacy_only_tok",
                "expires_at": future_ms,
                "user_open_id": "ou_legacy",
            }))

            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", legacy), \
                 patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=MagicMock()):
                # No sender_open_id_scope, no arg
                client = FeishuClient.for_user()

            self.assertEqual(client.access_token, "legacy_only_tok")


class TestSenderContextVarConcurrentIsolation(unittest.IsolatedAsyncioTestCase):
    """US-004 AC#5: concurrent async tasks must not bleed open_id into each other."""

    async def test_concurrent_async_tasks_have_isolated_contextvars(self):
        from tools.feishu_oapi_client import sender_open_id_scope, current_sender_open_id
        observed: dict = {}

        async def worker(name: str, oid: str):
            with sender_open_id_scope(oid):
                # Yield control so scheduler interleaves the two workers
                await asyncio.sleep(0)
                observed[name] = current_sender_open_id.get()

        await asyncio.gather(
            worker("alice", "ou_alice_concurrent"),
            worker("bob", "ou_bob_concurrent"),
        )

        self.assertEqual(observed["alice"], "ou_alice_concurrent")
        self.assertEqual(observed["bob"], "ou_bob_concurrent")
        # After all tasks finish the outer (main) contextvar is still unset
        self.assertIsNone(current_sender_open_id.get())


    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_id", "FEISHU_APP_SECRET": "secret"})
    def test_for_user_with_open_id_loads_per_user_uat_not_legacy(self):
        """US-001 AC#5: for_user('ou_xxx') reads per-user file, ignores legacy single file."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            legacy = Path(tmpdir) / "feishu_uat.json"
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()
            future_ms = int(time.time() * 1000) + 7200 * 1000
            # Legacy single file has a token for "ou_legacy"
            legacy.write_text(json.dumps({
                "access_token": "legacy_token",
                "expires_at": future_ms,
                "user_open_id": "ou_legacy",
            }))
            # Per-user file for "ou_alice" has a different token
            (uat_dir / "ou_alice.json").write_text(json.dumps({
                "access_token": "alice_token",
                "expires_at": future_ms,
                "user_open_id": "ou_alice",
            }))

            with patch("tools.feishu_oapi_client.FEISHU_UAT_PATH", legacy), \
                 patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir), \
                 patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=MagicMock()):
                client = FeishuClient.for_user(user_open_id="ou_alice")

        # AC: for_user('ou_alice') gives Alice's token, NOT legacy
        self.assertEqual(client.access_token, "alice_token")
        self.assertEqual(client.user_open_id, "ou_alice")
        self.assertNotEqual(client.access_token, "legacy_token")


# ---------------------------------------------------------------------------
# FeishuClient.for_tenant()
# ---------------------------------------------------------------------------

class TestFeishuClientForTenant(unittest.TestCase):
    """Tests for FeishuClient.for_tenant() factory method."""

    def setUp(self):
        FeishuClient._cache.clear()

    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_t", "FEISHU_APP_SECRET": "sec_t"})
    def test_returns_client_with_no_access_token(self):
        with patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=MagicMock()):
            client = FeishuClient.for_tenant()

        self.assertEqual(client.app_id, "app_t")
        self.assertEqual(client.access_token, "")
        self.assertFalse(client.ephemeral)

    @patch.dict(os.environ, {"FEISHU_APP_ID": "app_t", "FEISHU_APP_SECRET": "sec_t"})
    def test_caches_and_returns_same_instance(self):
        with patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=MagicMock()):
            c1 = FeishuClient.for_tenant()
            c2 = FeishuClient.for_tenant()

        self.assertIs(c1, c2)

    def test_raises_value_error_when_env_missing(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch("tools.feishu_oapi_client._resolve_feishu_credentials",
                   return_value=("", "", "feishu")):
            with self.assertRaises(ValueError):
                FeishuClient.for_tenant()


# ---------------------------------------------------------------------------
# FeishuClient.do_request()
# ---------------------------------------------------------------------------

class TestFeishuClientDoRequest(unittest.TestCase):
    """Tests for FeishuClient.do_request() UAT vs TAT path routing."""

    def setUp(self):
        FeishuClient._cache.clear()

    def _make_client(self, access_token=""):
        client = FeishuClient.__new__(FeishuClient)
        client.app_id = "app_x"
        client.app_secret = "sec_x"
        client.account_id = "default"
        client.domain = "feishu"
        client.access_token = access_token
        client.user_open_id = "ou_x"
        client.ephemeral = False
        client.sdk = MagicMock()
        return client

    def test_do_request_use_uat_true_calls_sdk_with_request_option(self):
        client = self._make_client(access_token="uat_tok")

        mock_response = MagicMock()
        mock_response.code = 0
        mock_response.msg = "success"
        mock_response.raw = None
        mock_response.data = {"items": []}
        client.sdk.request = MagicMock(return_value=mock_response)

        try:
            import lark_oapi  # noqa: F401
        except ImportError:
            self.skipTest("lark_oapi not installed")

        code, msg, data = client.do_request(
            "GET",
            "/open-apis/calendar/v4/events",
            use_uat=True,
        )

        # With use_uat=True, sdk.request is called with 2 args (request + option)
        call_args = client.sdk.request.call_args
        self.assertEqual(client.sdk.request.call_count, 1)
        self.assertEqual(len(call_args[0]), 2)  # (request, option)

    def test_do_request_use_uat_false_calls_sdk_without_request_option(self):
        client = self._make_client(access_token="uat_tok")

        mock_response = MagicMock()
        mock_response.code = 0
        mock_response.msg = "ok"
        mock_response.raw = None
        mock_response.data = {}
        client.sdk.request = MagicMock(return_value=mock_response)

        try:
            import lark_oapi  # noqa: F401
        except ImportError:
            self.skipTest("lark_oapi not installed")

        client.do_request("GET", "/open-apis/some/v1/endpoint", use_uat=False)

        # With use_uat=False, sdk.request is called with 1 arg only
        call_args = client.sdk.request.call_args
        self.assertEqual(len(call_args[0]), 1)  # (request,)

    def test_do_request_returns_code_msg_data_tuple(self):
        client = self._make_client(access_token="uat_tok")

        mock_response = MagicMock()
        mock_response.code = 0
        mock_response.msg = "ok"
        raw = MagicMock()
        raw.content = json.dumps({"code": 0, "msg": "ok", "data": {"key": "val"}}).encode()
        mock_response.raw = raw
        mock_response.data = None
        client.sdk.request = MagicMock(return_value=mock_response)

        try:
            import lark_oapi  # noqa: F401
        except ImportError:
            self.skipTest("lark_oapi not installed")

        code, msg, data = client.do_request("GET", "/open-apis/x", use_uat=True)

        self.assertEqual(code, 0)
        self.assertEqual(msg, "ok")
        self.assertEqual(data.get("key"), "val")

    def test_do_request_preserves_patch_and_delete_methods(self):
        client = self._make_client(access_token="uat_tok")

        mock_response = MagicMock()
        mock_response.code = 0
        mock_response.msg = "ok"
        mock_response.raw = None
        mock_response.data = {}
        client.sdk.request = MagicMock(return_value=mock_response)

        try:
            import lark_oapi  # noqa: F401
        except ImportError:
            self.skipTest("lark_oapi not installed")

        client.do_request("PATCH", "/open-apis/x", use_uat=True)
        patch_request = client.sdk.request.call_args.args[0]
        client.do_request("DELETE", "/open-apis/x", use_uat=True)
        delete_request = client.sdk.request.call_args.args[0]

        self.assertEqual(getattr(patch_request, "http_method", None).name, "PATCH")
        self.assertEqual(getattr(delete_request, "http_method", None).name, "DELETE")


# ---------------------------------------------------------------------------
# TOOLS_METADATA registry
# ---------------------------------------------------------------------------

class TestToolsMetadata(unittest.TestCase):
    """Verify TOOLS_METADATA is populated by importing tool modules."""

    def test_tools_metadata_has_feishu_get_my_user_info(self):
        # feishu_oapi_client defines this entry by default
        self.assertIn("feishu_get_my_user_info", TOOLS_METADATA)

    def test_feishu_get_my_user_info_metadata_has_identity_user(self):
        meta = TOOLS_METADATA["feishu_get_my_user_info"]
        self.assertEqual(meta.get("identity"), "user")

    def test_calendar_tools_registered_after_module_import(self):
        import importlib
        importlib.import_module("tools.feishu_calendar_tool")

        expected = [
            "feishu_calendar_list_events",
            "feishu_calendar_get_event",
            "feishu_calendar_create_event",
            "feishu_calendar_freebusy",
        ]
        for tool in expected:
            self.assertIn(tool, TOOLS_METADATA, f"{tool} missing from TOOLS_METADATA")

    def test_bitable_tools_registered_after_module_import(self):
        import importlib
        importlib.import_module("tools.feishu_bitable_tool")

        expected = [
            "feishu_bitable_list_apps",
            "feishu_bitable_list_tables",
            "feishu_bitable_list_records",
            "feishu_bitable_search_records",
            "feishu_bitable_create_record",
            "feishu_bitable_update_record",
        ]
        for tool in expected:
            self.assertIn(tool, TOOLS_METADATA, f"{tool} missing from TOOLS_METADATA")

    def test_im_user_tools_registered_after_module_import(self):
        import importlib
        importlib.import_module("tools.feishu_im_user_tool")

        self.assertIn("feishu_im_send_message_as_user", TOOLS_METADATA)
        self.assertIn("feishu_im_reply_message_as_user", TOOLS_METADATA)


class TestUatCrossContextFallback(unittest.TestCase):
    """US-004: cross-context UAT fallback safety net.

    Feishu has separate `open_id` namespaces for the messaging layer
    (sender_id.open_id in events) and the OAuth user_info layer (the open_id
    stamped into a UAT after device flow). When the contextvar carries a
    messaging-layer open_id but the UAT was saved under the user_info
    open_id, the per-user file lookup misses. The fallback below picks the
    freshest valid UAT in the dir.
    """

    def _write_uat(self, path: Path, *, expires_at_ms: int, mtime=None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "access_token": f"tok_{path.stem}",
            "user_open_id": path.stem,
            "expires_at": expires_at_ms,
        }))
        if mtime is not None:
            os.utime(path, (mtime, mtime))

    def test_find_latest_returns_freshest_non_expired_uat(self):
        from tools.feishu_oapi_client import _find_latest_valid_uat_path
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir)
            future_ms = int(time.time() * 1000) + 7200 * 1000
            now = time.time()
            # 3 valid UATs with different mtimes; expect the newest mtime to win.
            self._write_uat(uat_dir / "ou_old.json", expires_at_ms=future_ms, mtime=now - 300)
            self._write_uat(uat_dir / "ou_mid.json", expires_at_ms=future_ms, mtime=now - 100)
            self._write_uat(uat_dir / "ou_new.json", expires_at_ms=future_ms, mtime=now)

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                result = _find_latest_valid_uat_path()

            self.assertIsNotNone(result)
            self.assertEqual(result.name, "ou_new.json")

    def test_find_latest_skips_sidecar_and_non_json_files(self):
        from tools.feishu_oapi_client import _find_latest_valid_uat_path
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir)
            future_ms = int(time.time() * 1000) + 7200 * 1000
            self._write_uat(uat_dir / "ou_real.json", expires_at_ms=future_ms)
            # Sidecars (needs_reauth) and dotfiles must be ignored
            (uat_dir / "ou_real.needs_reauth").write_text('{"reason":"x"}')
            (uat_dir / ".hidden.json").write_text("{}")
            (uat_dir / "junk.txt").write_text("nope")

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                result = _find_latest_valid_uat_path()

            self.assertIsNotNone(result)
            self.assertEqual(result.name, "ou_real.json")

    def test_find_latest_returns_none_when_all_expired(self):
        from tools.feishu_oapi_client import _find_latest_valid_uat_path
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir)
            past_ms = 1000  # ancient
            self._write_uat(uat_dir / "ou_a.json", expires_at_ms=past_ms)
            self._write_uat(uat_dir / "ou_b.json", expires_at_ms=past_ms)

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                result = _find_latest_valid_uat_path()

            self.assertIsNone(result)

    def test_find_latest_skips_explicit_skip_path_for_recursion_guard(self):
        from tools.feishu_oapi_client import _find_latest_valid_uat_path
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir)
            future_ms = int(time.time() * 1000) + 7200 * 1000
            now = time.time()
            self._write_uat(uat_dir / "ou_skip.json", expires_at_ms=future_ms, mtime=now)        # newest
            self._write_uat(uat_dir / "ou_keep.json", expires_at_ms=future_ms, mtime=now - 300)  # older

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                result = _find_latest_valid_uat_path(skip=uat_dir / "ou_skip.json")

            self.assertIsNotNone(result)
            self.assertEqual(result.name, "ou_keep.json")

    def test_load_uat_returns_fallback_when_per_user_path_missing(self):
        from tools.feishu_oapi_client import _load_uat
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir)
            future_ms = int(time.time() * 1000) + 7200 * 1000
            # Caller asks for ou_messaging (doesn't exist), fallback should
            # find ou_oauth (the freshest valid one in the dir).
            self._write_uat(uat_dir / "ou_oauth.json", expires_at_ms=future_ms)

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                data = _load_uat(open_id="ou_messaging_missing")

            self.assertEqual(data["access_token"], "tok_ou_oauth")


if __name__ == "__main__":
    unittest.main()
