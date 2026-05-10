"""US-006 tests for FeishuAdapter._maybe_send_onboarding_card / chat-added onboarding.

Auto-onboarding fires for senders who have no per-user UAT yet, hinting them
to run /feishu_auth. It is idempotent within a process (in-memory dedup),
silently skipped for senders who already have a UAT, and triggered on
``bot.added`` events as well.
"""

from __future__ import annotations

import asyncio
import json
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from gateway.platforms.feishu import FeishuAdapter


class _AdapterStub:
    """Tiny stand-in exposing only the attrs the onboarding helpers use."""

    def __init__(self):
        self.send = AsyncMock(return_value=MagicMock(success=True))

    _maybe_send_onboarding_card = FeishuAdapter._maybe_send_onboarding_card
    _send_chat_added_onboarding = FeishuAdapter._send_chat_added_onboarding


class TestAutoOnboarding(unittest.IsolatedAsyncioTestCase):
    """Tests for the inbound-message-driven onboarding flow."""

    async def test_onboarding_sent_when_sender_has_no_uat(self):
        adapter = _AdapterStub()
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()  # empty: no per-user UAT for ou_new

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                sent = await adapter._maybe_send_onboarding_card(
                    chat_id="oc_chat",
                    sender_open_id="ou_new",
                    message_id="om_1",
                )

            self.assertTrue(sent)
            adapter.send.assert_called_once()
            content = adapter.send.call_args.args[1]
            self.assertIn("/feishu_auth", content)

    async def test_onboarding_skipped_when_sender_already_has_uat(self):
        adapter = _AdapterStub()
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()
            (uat_dir / "ou_existing.json").write_text(json.dumps({
                "access_token": "t", "user_open_id": "ou_existing",
                "expires_at": int(time.time() * 1000) + 7200 * 1000,
            }))

            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                sent = await adapter._maybe_send_onboarding_card(
                    chat_id="oc_chat",
                    sender_open_id="ou_existing",
                    message_id="om_1",
                )

            self.assertFalse(sent)
            adapter.send.assert_not_called()

    async def test_onboarding_idempotent_within_session(self):
        """Same (chat, sender) pair only triggers onboarding once."""
        adapter = _AdapterStub()
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()
            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                sent1 = await adapter._maybe_send_onboarding_card(
                    chat_id="oc_x", sender_open_id="ou_y", message_id="om_a",
                )
                sent2 = await adapter._maybe_send_onboarding_card(
                    chat_id="oc_x", sender_open_id="ou_y", message_id="om_b",
                )

            self.assertTrue(sent1)
            self.assertFalse(sent2)
            self.assertEqual(adapter.send.call_count, 1)

    async def test_onboarding_per_chat_per_sender_independent(self):
        """Different (chat, sender) pairs each get their own onboarding."""
        adapter = _AdapterStub()
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            uat_dir = Path(tmpdir) / "feishu_uat"
            uat_dir.mkdir()
            with patch("tools.feishu_oapi_client.FEISHU_UAT_DIR", uat_dir):
                # Same sender, two different chats → two cards
                s1 = await adapter._maybe_send_onboarding_card(
                    "oc_A", "ou_z", "m1")
                s2 = await adapter._maybe_send_onboarding_card(
                    "oc_B", "ou_z", "m2")
                # Same chat, two different senders → two cards
                s3 = await adapter._maybe_send_onboarding_card(
                    "oc_A", "ou_w", "m3")

            self.assertTrue(s1 and s2 and s3)
            self.assertEqual(adapter.send.call_count, 3)

    async def test_invalid_open_id_silently_skipped(self):
        adapter = _AdapterStub()
        # Path-traversal-ish open_id should not raise, just return False
        for bad in ("ou/with/slash", "..", "ou\x00"):
            sent = await adapter._maybe_send_onboarding_card(
                chat_id="oc_x", sender_open_id=bad, message_id="m",
            )
            self.assertFalse(sent)
        adapter.send.assert_not_called()

    async def test_empty_chat_or_sender_returns_false_no_send(self):
        adapter = _AdapterStub()
        s1 = await adapter._maybe_send_onboarding_card("", "ou_x", "m")
        s2 = await adapter._maybe_send_onboarding_card("oc_x", "", "m")
        self.assertFalse(s1)
        self.assertFalse(s2)
        adapter.send.assert_not_called()

    async def test_chat_added_onboarding_sends_welcome(self):
        adapter = _AdapterStub()
        await adapter._send_chat_added_onboarding("oc_newchat")
        adapter.send.assert_called_once()
        args, _kwargs = adapter.send.call_args
        self.assertEqual(args[0], "oc_newchat")
        self.assertIn("/feishu_auth", args[1])


if __name__ == "__main__":
    unittest.main()
