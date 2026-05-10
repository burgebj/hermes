"""US-003 tests for FeishuAdapter._handle_feishu_auth_command.

The chat-driven /feishu_auth slash command runs the OAuth device flow on
behalf of the inbound chat sender, replying with a verification card +
success/error messages.  Tests use a lightweight stand-in for FeishuAdapter
to avoid pulling in the full lark.Client SDK initialization.
"""

from __future__ import annotations

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from gateway.platforms.feishu import FeishuAdapter


class _AdapterStub:
    """Tiny stand-in that exposes only the attrs / methods the handler uses."""

    def __init__(self, sent_card_id: str = "om_card_initial"):
        self.send = AsyncMock(return_value=MagicMock(success=True))
        # Auth-card path: _send_auth_card returns a message_id; _patch_auth_card
        # records the patched card. Tests assert against these to verify the
        # pending → success / error transition.
        self.sent_cards: list = []
        self.patched_cards: list = []
        self._sent_card_id = sent_card_id

        async def _send_auth_card(chat_id, card, reply_to=None):
            self.sent_cards.append({"chat_id": chat_id, "card": card, "reply_to": reply_to})
            return self._sent_card_id

        async def _patch_auth_card(message_id, card):
            # Mirror production behavior: empty message_id → no-op + False
            if not message_id:
                return False
            self.patched_cards.append({"message_id": message_id, "card": card})
            return True

        self._send_auth_card = _send_auth_card
        self._patch_auth_card = _patch_auth_card

    # Steal the real implementation so we test the genuine code path.
    _handle_feishu_auth_command = FeishuAdapter._handle_feishu_auth_command


class TestFeishuAuthCommand(unittest.IsolatedAsyncioTestCase):
    """Tests for the /feishu_auth slash command handler."""

    async def _wait_for_background_task(self, max_wait_s: float = 1.0) -> None:
        """Yield to the event loop a few times so background tasks finish."""
        for _ in range(50):
            await asyncio.sleep(0.01)
            # If all task callbacks have run, return early
            pending = [t for t in asyncio.all_tasks() if not t.done() and t is not asyncio.current_task()]
            # Filter feishu-auth ones only
            pending = [t for t in pending if t.get_name().startswith("feishu-auth:")]
            if not pending:
                return

    async def test_missing_credentials_sends_error_message(self):
        adapter = _AdapterStub()
        with patch("hermes_cli.config.get_env_value", return_value=""):
            await adapter._handle_feishu_auth_command(
                text="/feishu_auth",
                sender_open_id="ou_test",
                chat_id="oc_chat",
                message_id="om_msg",
            )

        adapter.send.assert_called_once()
        args, kwargs = adapter.send.call_args
        # chat_id positional, content positional, reply_to kwarg
        self.assertEqual(args[0], "oc_chat")
        self.assertIn("not configured", args[1])
        self.assertEqual(kwargs.get("reply_to"), "om_msg")

    async def test_spawns_device_flow_with_credentials_and_no_scope(self):
        adapter = _AdapterStub()

        async def fake_flow(client_id, client_secret, scope,
                            on_verification_url, on_success, on_error,
                            cancel_event=None):
            # Simulate the flow finishing immediately on success
            await on_verification_url("https://example.com/verify", "ABCD-1234", 600)
            await on_success("ou_test_user", "calendar:calendar")
            return ("tok", "ref", "ou_test_user")

        with patch("hermes_cli.config.get_env_value",
                   side_effect=lambda k: {"FEISHU_APP_ID": "app", "FEISHU_APP_SECRET": "secret"}.get(k, "")), \
             patch("hermes_cli.feishu_auth.chat_mode_device_flow", side_effect=fake_flow):
            await adapter._handle_feishu_auth_command(
                text="/feishu_auth",
                sender_open_id="ou_caller",
                chat_id="oc_chat",
                message_id="om_msg",
            )
            await self._wait_for_background_task()

        # Patch model: 1 card sent (pending), 1 card patched (success).
        self.assertEqual(len(adapter.sent_cards), 1)
        pending = adapter.sent_cards[0]["card"]
        # Verification URL appears as a button URL inside the action element
        action = next(e for e in pending["elements"] if e["tag"] == "action")
        self.assertEqual(action["actions"][0]["url"], "https://example.com/verify")
        # User code appears in the fallback markdown text
        fallback_md = [e for e in pending["elements"]
                       if e["tag"] == "markdown" and "ABCD-1234" in e.get("content", "")]
        self.assertTrue(fallback_md)
        # Success card was patched onto the pending card's message_id
        self.assertEqual(len(adapter.patched_cards), 1)
        success_patch = adapter.patched_cards[0]
        self.assertEqual(success_patch["message_id"], adapter._sent_card_id)
        self.assertEqual(success_patch["card"]["header"]["template"], "green")

    async def test_passes_scope_arg_through_to_device_flow(self):
        adapter = _AdapterStub()
        captured_scope: list = []

        async def fake_flow(client_id, client_secret, scope, **kw):
            captured_scope.append(scope)
            await kw["on_error"]("immediate stop")
            return None

        with patch("hermes_cli.config.get_env_value",
                   side_effect=lambda k: {"FEISHU_APP_ID": "app", "FEISHU_APP_SECRET": "secret"}.get(k, "")), \
             patch("hermes_cli.feishu_auth.chat_mode_device_flow", side_effect=fake_flow):
            await adapter._handle_feishu_auth_command(
                text="/feishu_auth calendar:calendar drive:drive",
                sender_open_id="ou_x",
                chat_id="oc_x",
                message_id="om_x",
            )
            await self._wait_for_background_task()

        self.assertEqual(captured_scope, ["calendar:calendar drive:drive"])

    async def test_no_scope_passes_none_to_device_flow(self):
        adapter = _AdapterStub()
        captured_scope: list = []

        async def fake_flow(client_id, client_secret, scope, **kw):
            captured_scope.append(scope)
            await kw["on_error"]("done")
            return None

        with patch("hermes_cli.config.get_env_value",
                   side_effect=lambda k: {"FEISHU_APP_ID": "app", "FEISHU_APP_SECRET": "secret"}.get(k, "")), \
             patch("hermes_cli.feishu_auth.chat_mode_device_flow", side_effect=fake_flow):
            await adapter._handle_feishu_auth_command(
                text="/feishu_auth",
                sender_open_id="ou_x",
                chat_id="oc_x",
                message_id="om_x",
            )
            await self._wait_for_background_task()

        self.assertEqual(captured_scope, [None])

    async def test_error_callback_sends_failure_message_with_retry_hint(self):
        adapter = _AdapterStub()

        async def fake_flow(client_id, client_secret, scope,
                            on_verification_url, on_success, on_error,
                            cancel_event=None):
            # Realistic order: pending card sent first, then user denies on
            # the verification page; we PATCH the same card to red.
            await on_verification_url("https://example.com/verify", "ABCD-1234", 600)
            await on_error("access_denied: user clicked deny")
            return None

        with patch("hermes_cli.config.get_env_value",
                   side_effect=lambda k: {"FEISHU_APP_ID": "app", "FEISHU_APP_SECRET": "secret"}.get(k, "")), \
             patch("hermes_cli.feishu_auth.chat_mode_device_flow", side_effect=fake_flow):
            await adapter._handle_feishu_auth_command(
                text="/feishu_auth",
                sender_open_id="ou_y",
                chat_id="oc_y",
                message_id="om_y",
            )
            await self._wait_for_background_task()

        # Error card was patched onto the message_id with red header
        # (no pending card was sent because chat_mode_device_flow went to
        # error before on_verification_url; expect 0 sent + 1 patched OR 1+1).
        self.assertGreaterEqual(len(adapter.patched_cards), 1)
        red_patches = [p for p in adapter.patched_cards
                       if p["card"].get("header", {}).get("template") == "red"]
        self.assertGreaterEqual(len(red_patches), 1)
        error_text = json.dumps(red_patches[0]["card"], ensure_ascii=False)
        self.assertIn("access_denied", error_text)

    async def test_reply_to_uses_inbound_message_id_in_group_or_dm(self):
        """Replies thread to the inbound message id so /feishu_auth works in groups."""
        adapter = _AdapterStub()

        async def fake_flow(client_id, client_secret, scope, **kw):
            await kw["on_verification_url"]("https://x", "CODE", 300)
            return None

        with patch("hermes_cli.config.get_env_value",
                   side_effect=lambda k: {"FEISHU_APP_ID": "app", "FEISHU_APP_SECRET": "secret"}.get(k, "")), \
             patch("hermes_cli.feishu_auth.chat_mode_device_flow", side_effect=fake_flow):
            await adapter._handle_feishu_auth_command(
                text="/feishu_auth",
                sender_open_id="ou_in_group",
                chat_id="oc_groupchat",
                message_id="om_specific_msg",
            )
            await self._wait_for_background_task()

        # Every send invocation includes reply_to=om_specific_msg
        for call in adapter.send.call_args_list:
            self.assertEqual(call.kwargs.get("reply_to"), "om_specific_msg")
            self.assertEqual(call.args[0], "oc_groupchat")


class TestFeishuAuthCardActionButton(unittest.IsolatedAsyncioTestCase):
    """P1.1 follow-up: clicking the card button routes to /feishu_auth handler."""

    def _make_event(self, sender_open_id: str, chat_id: str, message_id: str):
        # Mimic the lark SDK's event structure (operator + context attribute access)
        event = MagicMock()
        event.operator.open_id = sender_open_id
        event.context.open_chat_id = chat_id
        event.context.open_message_id = message_id
        return event

    async def test_button_click_dispatches_synthetic_feishu_auth_command(self):
        # Create a stub adapter that exposes only the bits this handler touches.
        loop = asyncio.get_event_loop()

        captured_calls: list = []

        async def fake_handle(text, sender_open_id, chat_id, message_id):
            captured_calls.append({
                "text": text,
                "sender_open_id": sender_open_id,
                "chat_id": chat_id,
                "message_id": message_id,
            })

        class Stub:
            _handle_feishu_auth_card_action = FeishuAdapter._handle_feishu_auth_card_action

            def _submit_on_loop(self, _loop, coro):
                # Run the coroutine on the same loop synchronously for tests
                loop.create_task(coro)

            _handle_feishu_auth_command = staticmethod(fake_handle)

        adapter = Stub()
        event = self._make_event("ou_clicker", "oc_chat", "om_msg")

        adapter._handle_feishu_auth_card_action(
            event=event,
            action_value={"hermes_action": "feishu_auth", "scope": "calendar:calendar"},
            loop=loop,
        )

        # Yield so the scheduled task can run
        for _ in range(10):
            await asyncio.sleep(0)

        self.assertEqual(len(captured_calls), 1)
        call = captured_calls[0]
        self.assertEqual(call["sender_open_id"], "ou_clicker")
        self.assertEqual(call["chat_id"], "oc_chat")
        self.assertEqual(call["message_id"], "om_msg")
        self.assertEqual(call["text"], "/feishu_auth calendar:calendar")

    async def test_button_click_with_no_scope_omits_scope_arg(self):
        loop = asyncio.get_event_loop()
        captured: list = []

        async def fake_handle(text, **_):
            captured.append(text)

        class Stub:
            _handle_feishu_auth_card_action = FeishuAdapter._handle_feishu_auth_card_action
            def _submit_on_loop(self, _loop, coro):
                loop.create_task(coro)
            _handle_feishu_auth_command = staticmethod(fake_handle)

        adapter = Stub()
        event = self._make_event("ou_x", "oc_x", "om_x")
        adapter._handle_feishu_auth_card_action(
            event=event,
            action_value={"hermes_action": "feishu_auth"},
            loop=loop,
        )
        for _ in range(10):
            await asyncio.sleep(0)

        self.assertEqual(captured, ["/feishu_auth"])

    async def test_button_click_missing_sender_or_chat_is_silently_skipped(self):
        loop = asyncio.get_event_loop()
        captured: list = []

        async def fake_handle(*a, **kw):
            captured.append("called")

        class Stub:
            _handle_feishu_auth_card_action = FeishuAdapter._handle_feishu_auth_card_action
            def _submit_on_loop(self, _loop, coro):
                loop.create_task(coro)
            _handle_feishu_auth_command = staticmethod(fake_handle)

        adapter = Stub()
        # Missing operator → no sender_open_id
        event = MagicMock()
        event.operator.open_id = ""
        event.context.open_chat_id = "oc_x"
        event.context.open_message_id = "om_x"

        adapter._handle_feishu_auth_card_action(
            event=event,
            action_value={"hermes_action": "feishu_auth"},
            loop=loop,
        )
        for _ in range(10):
            await asyncio.sleep(0)

        # No call dispatched
        self.assertEqual(captured, [])


if __name__ == "__main__":
    unittest.main()
