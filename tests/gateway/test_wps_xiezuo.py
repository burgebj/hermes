"""Tests for the WPS Xiezuo platform-plugin adapter."""

import asyncio
import json
import os
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from gateway.platforms.base import SendResult
from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.session import SessionSource
from tests.gateway._plugin_adapter_loader import load_plugin_adapter

_wps = load_plugin_adapter("wps_xiezuo")


class TestWpsXiezuoCrypto(unittest.TestCase):
    def test_compute_signature(self):
        sig = _wps.compute_signature(
            app_id="wp_1",
            app_secret="sec",
            topic="kso.app_chat.message",
            nonce="n1",
            timestamp=1700000000,
            encrypted_data="Zm9v",
        )
        import base64
        import hashlib
        import hmac

        content = "wp_1:kso.app_chat.message:n1:1700000000:Zm9v"
        expected = base64.urlsafe_b64encode(
            hmac.new(b"sec", content.encode(), hashlib.sha256).digest()
        ).decode().rstrip("=")
        self.assertEqual(sig, expected)

    def test_verify_signature_valid(self):
        sig = _wps.compute_signature("wp_1", "sec", "topic", "n1", 123, "data")
        self.assertTrue(_wps.verify_signature(sig, "wp_1", "sec", "topic", "n1", 123, "data"))

    def test_verify_signature_invalid(self):
        self.assertFalse(_wps.verify_signature("bad", "wp_1", "sec", "topic", "n1", 123, "data"))

    def test_encrypt_decrypt_roundtrip(self):
        import base64
        import hashlib

        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as cp

        secret = "test_secret_key"
        nonce = "abcdefghijklmnop"
        plaintext = '{"message": {"id": "m1"}, "chat": {"id": "c1"}, "sender": {"id": "u1"}}'

        key = hashlib.md5(secret.encode()).hexdigest().encode("utf-8")
        iv = nonce.encode("utf-8")[:16]
        padder = cp.PKCS7(128).padder()
        padded = padder.update(plaintext.encode()) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        enc = cipher.encryptor()
        encrypted_data = base64.b64encode(enc.update(padded) + enc.finalize()).decode()

        decrypted = _wps.decrypt_event(encrypted_data, secret, nonce)
        self.assertEqual(json.loads(decrypted), json.loads(plaintext))

    def test_handshake_frame_structure(self):
        frame = _wps.build_handshake("wp_test", "my_secret", "abc123")
        self.assertEqual(frame["opcode"], 1)
        payload = json.loads(frame["payload"])
        self.assertEqual(payload["app_id"], "wp_test")
        self.assertEqual(payload["nonce"], "abc123")
        self.assertIn("signature", payload)


class TestAppTokenStore(unittest.TestCase):
    def test_fetch_and_cache(self):
        async def _run():
            store = _wps.AppTokenStore("https://example.com", "id", "secret")
            store._fetch_token = AsyncMock(return_value=("tok_abc", 7200))
            token = await store.get_token()
            self.assertEqual(token, "tok_abc")
            store._fetch_token = AsyncMock(return_value=("tok_should_not", 7200))
            token2 = await store.get_token()
            self.assertEqual(token2, "tok_abc")

        asyncio.get_event_loop().run_until_complete(_run())

    def test_fetch_token_accepts_nested_data_response(self):
        class FakeResponse:
            status = 200

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def json(self):
                return {
                    "code": 0,
                    "data": {
                        "access_token": "tok_nested",
                        "expires_in": 3600,
                    },
                }

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def post(self, *args, **kwargs):
                return FakeResponse()

        async def _run():
            store = _wps.AppTokenStore("https://example.com", "id", "secret")
            with patch("aiohttp.ClientSession", return_value=FakeSession()):
                token, ttl = await store._fetch_token()
            self.assertEqual(token, "tok_nested")
            self.assertEqual(ttl, 3600)

        asyncio.get_event_loop().run_until_complete(_run())

    def test_invalidate(self):
        async def _run():
            store = _wps.AppTokenStore("https://example.com", "id", "secret")
            store._token = "old"
            store._expires_at = time.time() + 9999
            store.invalidate()
            self.assertIsNone(store._token)

        asyncio.get_event_loop().run_until_complete(_run())


class TestWpsXiezuoAdapter(unittest.TestCase):
    def test_adapter_instantiation(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec", "connection_mode": "websocket"})
        adapter = _wps.WpsXiezuoAdapter(config)
        self.assertEqual(adapter._app_id, "wp_test")
        self.assertEqual(adapter._connection_mode, "websocket")
        self.assertFalse(adapter._connected)

    def test_parse_receiver_chat(self):
        self.assertEqual(_wps.WpsXiezuoAdapter._parse_receiver("123"), {"type": "chat", "receiver_id": "123"})
        self.assertEqual(_wps.WpsXiezuoAdapter._parse_receiver("chat:456"), {"type": "chat", "receiver_id": "456"})
        self.assertEqual(_wps.WpsXiezuoAdapter._parse_receiver("user:789"), {"type": "user", "receiver_id": "789"})
        self.assertIsNone(_wps.WpsXiezuoAdapter._parse_receiver(""))

    def test_normalize_content(self):
        msg = {"content": {"text": {"content": "hello", "type": "text"}}}
        self.assertEqual(_wps._normalize_message_content(msg), "hello")
        self.assertEqual(_wps._normalize_message_content({"content": "raw text"}), "raw text")
        self.assertEqual(_wps._strip_at_mention("hi <at user_id=bot>Bot</at> there"), "hi Bot there")

    def test_sanitize_dsml_tokens(self):
        raw = (
            '根据查询结果，金山云(KC)今日股价如下：\n'
            '<|｜DSML｜｜tool_calls> <|｜DSML｜｜invoke name="terminal"> '
            '<|｜DSML｜｜parameter name="command" string="true">curl -s "https://example.com"</|｜DSML｜｜parameter> '
            '</|｜DSML｜｜invoke> </|｜DSML｜｜tool_calls>'
        )
        cleaned = _wps._sanitize_model_output(raw)
        self.assertNotIn("DSML", cleaned)
        self.assertIn("金山云", cleaned)
        self.assertNotIn("\n\n\n", cleaned)


class TestWpsXiezuoInbound(unittest.TestCase):
    def test_dm_message_dispatched(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)
        adapter._connected = True
        adapter._wps_client = MagicMock()
        adapter.handle_message = AsyncMock()

        event = {
            "topic": "kso.app_chat.message",
            "operation": "create",
            "data": {
                "sender": {"id": "u1", "type": "user"},
                "message": {"id": "m1", "content": {"text": {"content": "hello", "type": "text"}}},
                "chat": {"id": "c1", "type": "p2p"},
            },
        }

        async def _run():
            await adapter._handle_inbound_event(event)
            adapter.handle_message.assert_called_once()

        asyncio.get_event_loop().run_until_complete(_run())

    def test_loopback_filtered(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)
        adapter._connected = True
        adapter._bot_user_id = "bot_1"
        adapter._wps_client = MagicMock()
        adapter.handle_message = AsyncMock()

        event = {
            "topic": "kso.app_chat.message",
            "operation": "create",
            "data": {
                "sender": {"id": "bot_1", "type": "robot"},
                "message": {"id": "m1", "content": {"text": {"content": "hello", "type": "text"}}},
                "chat": {"id": "c1", "type": "p2p"},
            },
        }

        async def _run():
            await adapter._handle_inbound_event(event)
            adapter.handle_message.assert_not_called()

        asyncio.get_event_loop().run_until_complete(_run())

    def test_dedup_same_msg_id(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)
        adapter._connected = True
        adapter._wps_client = MagicMock()
        adapter.handle_message = AsyncMock()

        event = {
            "topic": "kso.app_chat.message",
            "operation": "create",
            "data": {
                "sender": {"id": "u1", "type": "user"},
                "message": {"id": "m1", "content": {"text": {"content": "hello", "type": "text"}}},
                "chat": {"id": "c1", "type": "p2p"},
            },
        }

        async def _run():
            await adapter._handle_inbound_event(event)
            await adapter._handle_inbound_event(event)
            self.assertEqual(adapter.handle_message.call_count, 1)

        asyncio.get_event_loop().run_until_complete(_run())


class TestWpsXiezuoSend(unittest.TestCase):
    def test_send_not_connected(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)

        async def _run():
            result = await adapter.send("c1", "hello")
            self.assertFalse(result.success)
            self.assertIn("Not connected", result.error)

        asyncio.get_event_loop().run_until_complete(_run())

    def test_send_text_message(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)
        adapter._connected = True
        adapter._wps_client = MagicMock()
        adapter._token_store = MagicMock()
        adapter._wps_client.request = AsyncMock(return_value={"code": 0, "data": {"message_id": "msg_1"}})

        async def _run():
            with self.assertLogs("plugins.platforms.wps_xiezuo", level="INFO") as logs:
                result = await adapter.send("c1", "hello")
            self.assertTrue(result.success)
            self.assertEqual(result.message_id, "msg_1")
            self.assertTrue(any("message sent chat=c1 message_id=msg_1" in line for line in logs.output))

        asyncio.get_event_loop().run_until_complete(_run())

    def test_send_markdown_fallback_to_plain(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)
        adapter._connected = True
        adapter._wps_client = MagicMock()
        adapter._token_store = MagicMock()
        adapter._wps_client.request = AsyncMock(side_effect=[
            _wps.WpsRequestError("WPS API /v7/messages/create failed: InvalidArgument:can not get text info"),
            {"code": 0, "data": {"message_id": "msg_plain"}},
        ])

        async def _run():
            result = await adapter.send("c1", "**hello** world")
            self.assertTrue(result.success)
            self.assertEqual(result.message_id, "msg_plain")

        asyncio.get_event_loop().run_until_complete(_run())

    def test_standalone_sender_fn(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec", "base_url": "https://example.com"})

        async def _run():
            with patch.object(_wps, "WpsXiezuoAdapter") as mock_adapter_cls:
                mock_adapter = MagicMock()
                mock_adapter.send = AsyncMock(return_value=SendResult(success=True, message_id="msg_tool"))
                mock_adapter._base_url = "https://example.com"
                mock_adapter._app_id = "wp_test"
                mock_adapter._app_secret = "sec"
                mock_adapter_cls.return_value = mock_adapter
                result = await _wps._standalone_send(config, "chat:123", "**hello**")
            self.assertTrue(result["success"])
            self.assertEqual(result["platform"], "wps_xiezuo")
            self.assertEqual(result["message_id"], "msg_tool")

        asyncio.get_event_loop().run_until_complete(_run())


class TestWpsXiezuoWsHandling(unittest.TestCase):
    def test_goaway_connection_replaced(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)
        adapter._ws_client = MagicMock()
        adapter._ws_client.send_json = AsyncMock()
        adapter._ws_is_websockets_lib = False

        async def _run():
            await adapter._handle_ws_data({"type": "goaway", "reason": "connection_replaced", "message": "Another client connected"})
            self.assertFalse(adapter._stop_reconnect)
            self.assertFalse(adapter._connected)

        asyncio.get_event_loop().run_until_complete(_run())

    def test_event_sends_ack(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)
        adapter._ws_client = MagicMock()
        adapter._ws_client.send_json = AsyncMock()

        ack_time = [None]
        process_time = [None]

        async def fake_send_json(payload):
            if payload.get("type") == "ack":
                ack_time[0] = time.time()

        async def fake_process(evt):
            process_time[0] = time.time()

        adapter._ws_client.send_json = AsyncMock(side_effect=fake_send_json)
        adapter._handle_inbound_event = AsyncMock(side_effect=fake_process)

        async def _run():
            await adapter._handle_ws_data({"topic": "kso.app_chat.message", "operation": "create", "nonce": "order_test", "data": {}})
            self.assertIsNotNone(ack_time[0])
            self.assertIsNotNone(process_time[0])
            self.assertLess(ack_time[0], process_time[0])

        asyncio.get_event_loop().run_until_complete(_run())

    def test_ack_failure_does_not_skip_event_processing(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)
        adapter._ws_client = MagicMock()
        adapter._ws_client.send_json = AsyncMock(side_effect=RuntimeError("ack failed"))
        adapter._handle_inbound_event = AsyncMock()

        async def _run():
            await adapter._handle_ws_data({"topic": "kso.app_chat.message", "operation": "create", "nonce": "n1", "data": {}})
            adapter._handle_inbound_event.assert_called_once()

        asyncio.get_event_loop().run_until_complete(_run())

    def test_ack_sent_before_event_processing(self):
        config = PlatformConfig(enabled=True)
        config.extra.update({"app_id": "wp_test", "app_secret": "sec"})
        adapter = _wps.WpsXiezuoAdapter(config)
        adapter._ws_client = MagicMock()
        timeline = []

        async def fake_send_json(payload):
            if payload.get("type") == "ack":
                timeline.append("ack")

        async def fake_process(evt):
            timeline.append("process")

        adapter._ws_client.send_json = AsyncMock(side_effect=fake_send_json)
        adapter._handle_inbound_event = AsyncMock(side_effect=fake_process)

        async def _run():
            await adapter._handle_ws_data({"topic": "kso.app_chat.message", "operation": "create", "nonce": "n1", "data": {}})
            self.assertEqual(timeline[0], "ack")
            self.assertEqual(timeline[1], "process")

        asyncio.get_event_loop().run_until_complete(_run())


class TestWpsXiezuoConfig(unittest.TestCase):
    def test_check_requirements_false_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(_wps.check_wps_xiezuo_requirements())

    @patch.dict(os.environ, {
        "WPS_XIEZUO_APP_ID": "wp_xxx",
        "WPS_XIEZUO_APP_SECRET": "secret_xxx",
    }, clear=False)
    def test_check_requirements_true_when_set(self):
        self.assertTrue(_wps.check_wps_xiezuo_requirements())

    def test_platform_enum_value(self):
        from gateway.config import Platform
        self.assertEqual(Platform("wps_xiezuo").value, "wps_xiezuo")

    def test_send_message_target_parser_accepts_canonical_name(self):
        from tools.send_message_tool import _parse_target_ref

        self.assertEqual(_parse_target_ref("wps_xiezuo", "chat:123"), ("chat:123", None, True))

    @patch.dict(os.environ, {"WPS_XIEZUO_ALLOW_ALL_USERS": "true"}, clear=False)
    def test_gateway_auth_uses_plugin_allow_all_env(self):
        from gateway.platform_registry import PlatformEntry, platform_registry
        from gateway.run import GatewayRunner

        original_entry = platform_registry.get("wps_xiezuo")
        try:
            platform_registry.register(
                PlatformEntry(
                    name="wps_xiezuo",
                    label="WPS Xiezuo",
                    adapter_factory=lambda config: None,
                    check_fn=lambda: True,
                    allowed_users_env="WPS_XIEZUO_ALLOWED_USERS",
                    allow_all_env="WPS_XIEZUO_ALLOW_ALL_USERS",
                )
            )

            platform = Platform("wps_xiezuo")
            runner = object.__new__(GatewayRunner)
            runner.config = GatewayConfig(platforms={platform: PlatformConfig(enabled=True)})
            runner.pairing_store = MagicMock()
            runner.pairing_store.is_approved.return_value = False

            source = SessionSource(
                platform=platform,
                chat_id="chat_1",
                chat_type="dm",
                user_id="user_1",
                user_name="tester",
            )

            self.assertTrue(runner._is_user_authorized(source))
        finally:
            if original_entry is None:
                platform_registry._entries.pop("wps_xiezuo", None)
            else:
                platform_registry._entries["wps_xiezuo"] = original_entry

    def test_redacts_identifier_for_logs(self):
        self.assertEqual(_wps._redact_identifier("APPID1234567890"), "APPI...90")
        self.assertEqual(_wps._redact_identifier("short"), "***")
        self.assertEqual(_wps._redact_identifier(""), "")


class TestWpsXiezuoRegister(unittest.TestCase):
    def test_register_exports_plugin_entry(self):
        class Ctx:
            def __init__(self):
                self.kwargs = None

            def register_platform(self, **kwargs):
                self.kwargs = kwargs

        ctx = Ctx()
        _wps.register(ctx)
        self.assertIsNotNone(ctx.kwargs)
        self.assertEqual(ctx.kwargs["name"], "wps_xiezuo")
        self.assertEqual(ctx.kwargs["label"], "WPS Xiezuo")
        self.assertEqual(ctx.kwargs["cron_deliver_env_var"], "WPS_XIEZUO_HOME_CHANNEL")
        self.assertTrue(callable(ctx.kwargs["standalone_sender_fn"]))
        self.assertTrue(callable(ctx.kwargs["env_enablement_fn"]))
        self.assertTrue(callable(ctx.kwargs["apply_yaml_config_fn"]))
        self.assertEqual(ctx.kwargs["required_env"], ["WPS_XIEZUO_APP_ID", "WPS_XIEZUO_APP_SECRET"])


if __name__ == "__main__":
    unittest.main()
