"""US-005 + US-009 — End-to-end chains for the openclaw-lark UX port.

Each test exercises a full code path with mock OAuth endpoints / mock SDK
responses; nothing actually hits Feishu. The point is to validate the
hand-offs between modules (chat command → device flow → save_uat → tool
loads per-user UAT, etc.) so a refactor in any single layer is caught
before a real bot session breaks.
"""

from __future__ import annotations

import asyncio
import json
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.integration


def _future_ms(seconds: int = 7200) -> int:
    return int((time.time() + seconds) * 1000)


# ---------------------------------------------------------------------------
# US-005: T1 chat /feishu_auth → per-user UAT → tool call uses it
# ---------------------------------------------------------------------------

class TestT1ChatAuthEndToEnd(unittest.IsolatedAsyncioTestCase):
    """T1 chain: chat command → device flow → save_uat per-user → for_user(open_id)."""

    async def test_chat_auth_writes_per_user_uat_then_for_user_loads_it(self):
        from gateway.platforms.feishu import FeishuAdapter
        from tools.feishu_oapi_client import FeishuClient

        # Lightweight adapter stub exposing only what _handle_feishu_auth_command needs
        class Stub:
            def __init__(self):
                self.send = AsyncMock(return_value=MagicMock(success=True))
                self.sent_cards: list = []
                self.patched_cards: list = []
                async def _send_auth_card(chat_id, card, reply_to=None):
                    self.sent_cards.append({"chat_id": chat_id, "card": card})
                    return "om_card_e2e"
                async def _patch_auth_card(message_id, card):
                    if not message_id:
                        return False
                    self.patched_cards.append({"message_id": message_id, "card": card})
                    return True
                self._send_auth_card = _send_auth_card
                self._patch_auth_card = _patch_auth_card
            _handle_feishu_auth_command = FeishuAdapter._handle_feishu_auth_command

        adapter = Stub()

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"

            # Mock OAuth endpoints inside chat_mode_device_flow
            begin_response = {
                "device_code": "dc_e2e",
                "user_code": "ABCD-9999",
                "verification_uri_complete": "https://example.com/v?code=ABCD-9999",
                "expires_in": 600,
                "interval": 0,
            }
            poll_response = {
                "access_token": "uat_e2e",
                "refresh_token": "ref_e2e",
                "open_id": "ou_e2e_user",
                "expires_in": 7200,
                "refresh_expires_in": 2592000,
                "scope": "calendar:calendar",
                "error": None,
            }

            from hermes_cli.feishu_auth import save_uat as real_save_uat

            async def fake_chat_flow(client_id, client_secret, scope,
                                     on_verification_url, on_success, on_error,
                                     cancel_event=None):
                # Behave like the real flow: announce URL, persist UAT, announce success.
                await on_verification_url(begin_response["verification_uri_complete"],
                                          begin_response["user_code"], 600)
                real_save_uat(
                    access_token=poll_response["access_token"],
                    refresh_token=poll_response["refresh_token"],
                    open_id=poll_response["open_id"],
                    expires_in=poll_response["expires_in"],
                    refresh_expires_in=poll_response["refresh_expires_in"],
                    scope=poll_response["scope"],
                    app_id=client_id,
                    per_user=True,
                )
                await on_success(poll_response["open_id"], poll_response["scope"])
                return (poll_response["access_token"],
                        poll_response["refresh_token"],
                        poll_response["open_id"])

            with patch("hermes_cli.config.get_env_value",
                       side_effect=lambda k: {"FEISHU_APP_ID": "app", "FEISHU_APP_SECRET": "secret"}.get(k, "")), \
                 patch("hermes_cli.feishu_auth.chat_mode_device_flow", side_effect=fake_chat_flow), \
                 patch("hermes_cli.feishu_auth.FEISHU_UAT_DIR", uat_dir), \
                 patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir), \
                 patch("tools.feishu_oapi_client.FeishuClient._build_sdk", return_value=MagicMock()), \
                 patch("tools.feishu_oapi_client._resolve_feishu_credentials",
                       return_value=("app", "secret", "feishu")):

                # Step 1: simulate /feishu_auth in chat
                await adapter._handle_feishu_auth_command(
                    text="/feishu_auth calendar:calendar",
                    sender_open_id="ou_e2e_user",
                    chat_id="oc_e2e",
                    message_id="om_e2e",
                )

                # Wait for the background asyncio.create_task to finish.
                for _ in range(100):
                    await asyncio.sleep(0.02)
                    pending = [
                        t for t in asyncio.all_tasks()
                        if t is not asyncio.current_task() and not t.done()
                        and t.get_name().startswith("feishu-auth:")
                    ]
                    if not pending:
                        break

                # Step 2: per-user UAT file is on disk
                self.assertTrue((uat_dir / "ou_e2e_user.json").exists())

                # Step 3: pending card sent + success card patched in place
                self.assertEqual(len(adapter.sent_cards), 1)
                pending = adapter.sent_cards[0]["card"]
                self.assertEqual(pending["header"]["template"], "blue")
                self.assertEqual(len(adapter.patched_cards), 1)
                self.assertEqual(
                    adapter.patched_cards[0]["card"]["header"]["template"],
                    "green",
                )

                # Step 4: a subsequent UAT tool call loads ou_e2e_user's file
                client = FeishuClient.for_user(user_open_id="ou_e2e_user")
                self.assertEqual(client.access_token, "uat_e2e")
                self.assertEqual(client.user_open_id, "ou_e2e_user")


# ---------------------------------------------------------------------------
# US-009 — T2 chains: onboarding + refresh daemon + scope manager
# ---------------------------------------------------------------------------

class TestT2AutoOnboardingChain(unittest.IsolatedAsyncioTestCase):
    """T2 chain: bot.added → onboarding hint → user runs /feishu_auth → next message no card."""

    async def test_onboarding_then_post_auth_skips_card(self):
        from gateway.platforms.feishu import FeishuAdapter

        class Stub:
            def __init__(self):
                self.send = AsyncMock(return_value=MagicMock(success=True))
            _maybe_send_onboarding_card = FeishuAdapter._maybe_send_onboarding_card

        adapter = Stub()

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                # 1. First inbound, no UAT yet → onboarding card
                first_sent = await adapter._maybe_send_onboarding_card(
                    "oc_t2", "ou_t2_user", "om_first")
                self.assertTrue(first_sent)
                self.assertEqual(adapter.send.call_count, 1)

                # 2. User completes /feishu_auth, UAT lands on disk
                (uat_dir / "ou_t2_user.json").write_text(json.dumps({
                    "access_token": "uat_t2", "user_open_id": "ou_t2_user",
                    "expires_at": _future_ms(),
                }))
                # Build a fresh stub instance for the post-auth message — we
                # specifically want to test the "user already has UAT" branch
                # against a clean dedup set so the previous send doesn't mask it.
                adapter2 = Stub()
                second_sent = await adapter2._maybe_send_onboarding_card(
                    "oc_t2", "ou_t2_user", "om_second")
                self.assertFalse(second_sent)
                adapter2.send.assert_not_called()


class TestT2RefreshDaemonChain(unittest.IsolatedAsyncioTestCase):
    """T2 chain: pre-set near-expiry per-user UAT → daemon tick → refresh → file updated."""

    async def test_daemon_refreshes_near_expiry_uat(self):
        from hermes_cli.feishu_refresh_daemon import refresh_daemon_loop

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()
            now_ms = int(time.time() * 1000)
            uat_path = uat_dir / "ou_t2_refresh.json"
            uat_path.write_text(json.dumps({
                "app_id": "app",
                "user_open_id": "ou_t2_refresh",
                "access_token": "old_tok",
                "refresh_token": "ref_old",
                "expires_at": now_ms + 60 * 1000,  # 60s → near-expiry under 300s headroom
                "refresh_expires_at": now_ms + 86400 * 1000,
                "scope": "calendar:calendar",
            }))

            calls: list = []

            def fake_refresh(open_id, app_id, app_secret):
                calls.append(open_id)
                # Simulate token refresh by rewriting the file with new access_token
                with open(uat_path, encoding="utf-8") as fh:
                    d = json.load(fh)
                d["access_token"] = "new_tok"
                d["expires_at"] = int(time.time() * 1000) + 7200 * 1000
                uat_path.write_text(json.dumps(d))

            stop = asyncio.Event()

            async def stopper():
                await asyncio.sleep(0.05)
                stop.set()

            with patch(
                "hermes_cli.feishu_refresh_daemon.refresh_uat_for_user",
                side_effect=fake_refresh,
            ):
                await asyncio.gather(
                    refresh_daemon_loop(
                        "app", "secret",
                        interval_s=0.01,
                        headroom_s=300,
                        uat_dir=uat_dir,
                        stop_event=stop,
                    ),
                    stopper(),
                )

            self.assertIn("ou_t2_refresh", calls)
            updated = json.loads(uat_path.read_text())
            self.assertEqual(updated["access_token"], "new_tok")


class TestT2ScopeManagerChain(unittest.TestCase):
    """T2 chain: tool raises UserScopeInsufficientError → format_scope_error returns
    a Chinese reply that contains the missing scopes + /feishu_auth merged scope cmd."""

    def test_scope_error_to_friendly_card_text(self):
        from tools.feishu_oapi_client import UserScopeInsufficientError
        from tools.feishu_scope_mapping import format_scope_error

        exc = UserScopeInsufficientError(
            user_open_id="ou_t2_scope",
            api_name="feishu_calendar_list_events",
            missing_scopes=["calendar:calendar", "drive:drive"],
        )
        out = format_scope_error(exc)

        # Chinese friendly labels
        self.assertIn("日历(读写)", out)
        self.assertIn("云盘(读写)", out)
        # Merged-scope re-auth command
        self.assertIn("/feishu_auth calendar:calendar drive:drive", out)


if __name__ == "__main__":
    unittest.main()
