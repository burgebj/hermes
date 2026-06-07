"""Tests for the WeCom callback-mode adapter."""

import asyncio
from xml.etree import ElementTree as ET

import pytest

from gateway.config import PlatformConfig
from gateway.platforms.wecom_callback import (
    AIOHTTP_AVAILABLE,
    WecomCallbackAdapter,
)
from gateway.platforms.wecom_crypto import WXBizMsgCrypt


class _FakeRequest:
    def __init__(self, *, query=None, remote="127.0.0.1", body=""):
        self.query = query or {}
        self.remote = remote
        self._body = body

    async def text(self):
        return self._body


def _app(name="test-app", corp_id="ww1234567890", agent_id="1000002"):
    return {
        "name": name,
        "corp_id": corp_id,
        "corp_secret": "test-secret",
        "agent_id": agent_id,
        "token": "test-callback-token",
        "encoding_aes_key": "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG",
    }


def _config(apps=None):
    return PlatformConfig(
        enabled=True,
        extra={"mode": "callback", "host": "127.0.0.1", "port": 0, "apps": apps or [_app()]},
    )


class TestWecomCrypto:
    def test_roundtrip_encrypt_decrypt(self):
        app = _app()
        crypt = WXBizMsgCrypt(app["token"], app["encoding_aes_key"], app["corp_id"])
        encrypted_xml = crypt.encrypt(
            "<xml><Content>hello</Content></xml>", nonce="nonce123", timestamp="123456",
        )
        root = ET.fromstring(encrypted_xml)
        decrypted = crypt.decrypt(
            root.findtext("MsgSignature", default=""),
            root.findtext("TimeStamp", default=""),
            root.findtext("Nonce", default=""),
            root.findtext("Encrypt", default=""),
        )
        assert b"<Content>hello</Content>" in decrypted

    def test_signature_mismatch_raises(self):
        app = _app()
        crypt = WXBizMsgCrypt(app["token"], app["encoding_aes_key"], app["corp_id"])
        encrypted_xml = crypt.encrypt("<xml/>", nonce="n", timestamp="1")
        root = ET.fromstring(encrypted_xml)
        from gateway.platforms.wecom_crypto import SignatureError
        with pytest.raises(SignatureError):
            crypt.decrypt("bad-sig", "1", "n", root.findtext("Encrypt", default=""))


class TestWecomCallbackEventConstruction:
    def test_build_event_extracts_text_message(self):
        adapter = WecomCallbackAdapter(_config())
        xml_text = """
        <xml>
          <ToUserName>ww1234567890</ToUserName>
          <FromUserName>zhangsan</FromUserName>
          <CreateTime>1710000000</CreateTime>
          <MsgType>text</MsgType>
          <Content>\u4f60\u597d</Content>
          <MsgId>123456789</MsgId>
        </xml>
        """
        event = adapter._build_event(_app(), xml_text)
        assert event is not None
        assert event.source is not None
        assert event.source.user_id == "zhangsan"
        assert event.source.chat_id == "ww1234567890:zhangsan"
        assert event.message_id == "123456789"
        assert event.text == "\u4f60\u597d"

    def test_build_event_returns_none_for_subscribe(self):
        adapter = WecomCallbackAdapter(_config())
        xml_text = """
        <xml>
          <ToUserName>ww1234567890</ToUserName>
          <FromUserName>zhangsan</FromUserName>
          <CreateTime>1710000000</CreateTime>
          <MsgType>event</MsgType>
          <Event>subscribe</Event>
        </xml>
        """
        event = adapter._build_event(_app(), xml_text)
        assert event is None


class TestWecomCallbackRouting:
    def test_user_app_key_scopes_across_corps(self):
        adapter = WecomCallbackAdapter(_config())
        assert adapter._user_app_key("corpA", "alice") == "corpA:alice"
        assert adapter._user_app_key("corpB", "alice") == "corpB:alice"
        assert adapter._user_app_key("corpA", "alice") != adapter._user_app_key("corpB", "alice")

    @pytest.mark.asyncio
    async def test_send_selects_correct_app_for_scoped_chat_id(self):
        apps = [
            _app(name="corp-a", corp_id="corpA", agent_id="1001"),
            _app(name="corp-b", corp_id="corpB", agent_id="2002"),
        ]
        adapter = WecomCallbackAdapter(_config(apps=apps))
        adapter._user_app_map["corpB:alice"] = "corp-b"
        adapter._access_tokens["corp-b"] = {"token": "tok-b", "expires_at": 9999999999}

        calls = {}

        class FakeResponse:
            def json(self):
                return {"errcode": 0, "msgid": "ok1"}

        class FakeClient:
            async def post(self, url, json):
                calls["url"] = url
                calls["json"] = json
                return FakeResponse()

        adapter._http_client = FakeClient()
        result = await adapter.send("corpB:alice", "hello")

        assert result.success is True
        assert calls["json"]["touser"] == "alice"
        assert calls["json"]["agentid"] == 2002
        assert "tok-b" in calls["url"]

    @pytest.mark.asyncio
    async def test_send_falls_back_from_bare_user_id_when_unique(self):
        apps = [_app(name="corp-a", corp_id="corpA", agent_id="1001")]
        adapter = WecomCallbackAdapter(_config(apps=apps))
        adapter._user_app_map["corpA:alice"] = "corp-a"
        adapter._access_tokens["corp-a"] = {"token": "tok-a", "expires_at": 9999999999}

        calls = {}

        class FakeResponse:
            def json(self):
                return {"errcode": 0, "msgid": "ok2"}

        class FakeClient:
            async def post(self, url, json):
                calls["url"] = url
                calls["json"] = json
                return FakeResponse()

        adapter._http_client = FakeClient()
        result = await adapter.send("alice", "hello")

        assert result.success is True
        assert calls["json"]["agentid"] == 1001


class TestWecomCallbackSendTokenRefresh:
    @pytest.mark.asyncio
    async def test_send_retries_with_fresh_token_on_errcode_40001(self):
        """errcode=40001 must evict the cached token, refresh, and retry once."""
        adapter = WecomCallbackAdapter(_config())
        adapter._access_tokens["test-app"] = {"token": "stale", "expires_at": 9999999999}
        adapter._user_app_map["ww1234567890:alice"] = "test-app"

        responses = [
            {"errcode": 40001, "errmsg": "invalid credential"},
            {"errcode": 0, "msgid": "msg-ok"},
        ]
        post_calls = []

        class FakeClient:
            async def post(self, url, json=None, **kw):
                post_calls.append(url)

                class R:
                    def json(inner):
                        return responses[len(post_calls) - 1]
                return R()

            async def get(self, url, params=None, **kw):
                class R:
                    def json(inner):
                        return {"errcode": 0, "access_token": "fresh", "expires_in": 7200}
                return R()

        adapter._http_client = FakeClient()
        result = await adapter.send("ww1234567890:alice", "hello")

        assert result.success is True
        assert result.message_id == "msg-ok"
        assert len(post_calls) == 2
        assert "fresh" in post_calls[1]
        assert adapter._access_tokens["test-app"]["token"] == "fresh"

    @pytest.mark.asyncio
    async def test_send_retries_with_fresh_token_on_errcode_42001(self):
        """errcode=42001 (token expired) must also trigger the refresh-retry path."""
        adapter = WecomCallbackAdapter(_config())
        adapter._access_tokens["test-app"] = {"token": "expired", "expires_at": 9999999999}

        responses = [
            {"errcode": 42001, "errmsg": "access_token expired"},
            {"errcode": 0, "msgid": "msg-42"},
        ]
        post_calls = []

        class FakeClient:
            async def post(self, url, json=None, **kw):
                post_calls.append(url)

                class R:
                    def json(inner):
                        return responses[len(post_calls) - 1]
                return R()

            async def get(self, url, params=None, **kw):
                class R:
                    def json(inner):
                        return {"errcode": 0, "access_token": "renewed", "expires_in": 7200}
                return R()

        adapter._http_client = FakeClient()
        result = await adapter.send("alice", "hello")

        assert result.success is True
        assert len(post_calls) == 2

    @pytest.mark.asyncio
    async def test_send_does_not_retry_on_non_token_errcode(self):
        """Errors unrelated to token validity must fail immediately without retrying."""
        adapter = WecomCallbackAdapter(_config())
        adapter._access_tokens["test-app"] = {"token": "good", "expires_at": 9999999999}

        post_calls = []

        class FakeClient:
            async def post(self, url, json=None, **kw):
                post_calls.append(url)

                class R:
                    def json(inner):
                        return {"errcode": 60020, "errmsg": "not allow to access"}
                return R()

        adapter._http_client = FakeClient()
        result = await adapter.send("alice", "hello")

        assert result.success is False
        assert len(post_calls) == 1

    @pytest.mark.asyncio
    async def test_send_fails_cleanly_when_retry_also_fails(self):
        """If the refreshed token is also rejected, return failure without looping further."""
        adapter = WecomCallbackAdapter(_config())
        adapter._access_tokens["test-app"] = {"token": "bad1", "expires_at": 9999999999}

        post_calls = []

        class FakeClient:
            async def post(self, url, json=None, **kw):
                post_calls.append(url)

                class R:
                    def json(inner):
                        return {"errcode": 42001, "errmsg": "access_token expired"}
                return R()

            async def get(self, url, params=None, **kw):
                class R:
                    def json(inner):
                        return {"errcode": 0, "access_token": "bad2", "expires_in": 7200}
                return R()

        adapter._http_client = FakeClient()
        result = await adapter.send("alice", "hello")

        assert result.success is False
        assert len(post_calls) == 2


class TestWecomCallbackPollLoop:
    @pytest.mark.asyncio
    async def test_poll_loop_dispatches_handle_message(self, monkeypatch):
        adapter = WecomCallbackAdapter(_config())
        calls = []

        async def fake_handle_message(event):
            calls.append(event.text)

        monkeypatch.setattr(adapter, "handle_message", fake_handle_message)
        event = adapter._build_event(
            _app(),
            """
            <xml>
              <ToUserName>ww1234567890</ToUserName>
              <FromUserName>lisi</FromUserName>
              <CreateTime>1710000000</CreateTime>
              <MsgType>text</MsgType>
              <Content>test</Content>
              <MsgId>m2</MsgId>
            </xml>
            """,
        )
        task = asyncio.create_task(adapter._poll_loop())
        await adapter._message_queue.put(event)
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert calls == ["test"]


def _config_with(host="127.0.0.1", port=0, allowed_source_cidrs=None, apps=None):
    extra = {
        "mode": "callback",
        "host": host,
        "port": port,
        "apps": apps or [_app()],
    }
    if allowed_source_cidrs is not None:
        extra["allowed_source_cidrs"] = allowed_source_cidrs
    return PlatformConfig(enabled=True, extra=extra)


class TestWecomCallbackSourceIPAllowlist:
    @pytest.mark.asyncio
    async def test_connect_refuses_public_bind_without_allowlist(self):
        """Binding 0.0.0.0 without allowed_source_cidrs must fail closed."""
        if not AIOHTTP_AVAILABLE:
            pytest.skip("aiohttp not installed")
        adapter = WecomCallbackAdapter(
            _config_with(host="0.0.0.0", allowed_source_cidrs=[])
        )
        connected = await adapter.connect()
        assert connected is False
        assert adapter.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_allows_loopback_without_allowlist(self):
        """Loopback binds may omit allowed_source_cidrs (tunnel / reverse-proxy)."""
        if not AIOHTTP_AVAILABLE:
            pytest.skip("aiohttp not installed")
        adapter = WecomCallbackAdapter(
            _config_with(host="127.0.0.1", port=0, allowed_source_cidrs=[])
        )
        try:
            connected = await adapter.connect()
            assert connected is True
            assert adapter.is_connected is True
        finally:
            await adapter.disconnect()

    @pytest.mark.asyncio
    async def test_callback_from_disallowed_ip_rejected(self):
        adapter = WecomCallbackAdapter(
            _config_with(allowed_source_cidrs=["10.0.0.0/8"])
        )
        resp = await adapter._handle_callback(
            _FakeRequest(remote="203.0.113.99", body="<xml/>")
        )
        assert resp.status == 403

    @pytest.mark.asyncio
    async def test_callback_from_allowed_ip_passes_source_check(self):
        """Allowed source IPs reach the signature-verify path (no 403)."""
        adapter = WecomCallbackAdapter(
            _config_with(allowed_source_cidrs=["10.0.0.0/8", "203.0.113.0/24"])
        )
        resp = await adapter._handle_callback(
            _FakeRequest(remote="203.0.113.5", body="<xml/>")
        )
        # IP check passes; signature decryption then fails and the
        # handler returns 400, NOT 403. This proves the allowlist
        # admitted the request — distinguishing it from the rejected
        # 203.0.113.99 case above.
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_verify_handshake_respects_allowlist(self):
        """URL verification handshake must not bypass the allowlist."""
        adapter = WecomCallbackAdapter(
            _config_with(allowed_source_cidrs=["10.0.0.0/8"])
        )
        resp = await adapter._handle_verify(
            _FakeRequest(
                query={
                    "msg_signature": "x",
                    "timestamp": "0",
                    "nonce": "n",
                    "echostr": "probe",
                },
                remote="203.0.113.99",
            )
        )
        assert resp.status == 403

    @pytest.mark.asyncio
    async def test_health_endpoint_respects_allowlist(self):
        """The health endpoint must not leak status to arbitrary sources."""
        adapter = WecomCallbackAdapter(
            _config_with(allowed_source_cidrs=["10.0.0.0/8"])
        )
        resp = await adapter._handle_health(_FakeRequest(remote="203.0.113.99"))
        assert resp.status == 403

    @pytest.mark.asyncio
    async def test_public_bind_without_allowlist_rejects_inbound(self):
        """Even at request time, a public bind with no allowlist fails closed."""
        adapter = WecomCallbackAdapter(
            _config_with(host="0.0.0.0", allowed_source_cidrs=[])
        )
        resp = await adapter._handle_callback(
            _FakeRequest(remote="127.0.0.1", body="<xml/>")
        )
        assert resp.status == 403

    def test_invalid_cidr_entries_are_ignored_at_init(self):
        """Malformed CIDR strings should log a warning and be ignored, not crash."""
        adapter = WecomCallbackAdapter(
            _config_with(
                allowed_source_cidrs=["10.0.0.0/8", "not-a-cidr", "", "203.0.113.0/24"]
            )
        )
        assert len(adapter._allowed_source_networks) == 2

    def test_cidr_list_accepts_comma_string(self):
        """Env-var-style 'cidr1, cidr2' strings parse as a list."""
        adapter = WecomCallbackAdapter(
            _config_with(allowed_source_cidrs="10.0.0.0/8, 203.0.113.0/24")
        )
        assert len(adapter._allowed_source_networks) == 2

    def test_missing_remote_address_is_rejected(self):
        """A request with no remote attribute should fail closed, not error."""
        adapter = WecomCallbackAdapter(
            _config_with(allowed_source_cidrs=["10.0.0.0/8"])
        )
        assert adapter._source_ip_allowed(_FakeRequest(remote="")) is False

    def test_unparseable_remote_address_is_rejected(self):
        """A non-IP remote (e.g. a UNIX socket peer) should fail closed."""
        adapter = WecomCallbackAdapter(
            _config_with(allowed_source_cidrs=["10.0.0.0/8"])
        )
        assert adapter._source_ip_allowed(_FakeRequest(remote="not-an-ip")) is False


class TestWecomCallbackEnvOverrides:
    def test_env_override_populates_allowed_source_cidrs(self, monkeypatch):
        from gateway.config import GatewayConfig, Platform, _apply_env_overrides

        config = GatewayConfig()
        monkeypatch.setenv("WECOM_CALLBACK_CORP_ID", "ww123")
        monkeypatch.setenv("WECOM_CALLBACK_CORP_SECRET", "secret")
        monkeypatch.setenv(
            "WECOM_CALLBACK_ALLOWED_SOURCE_CIDRS",
            "10.0.0.0/8, 203.0.113.0/24",
        )

        _apply_env_overrides(config)

        extra = config.platforms[Platform.WECOM_CALLBACK].extra
        assert extra["allowed_source_cidrs"] == [
            "10.0.0.0/8",
            "203.0.113.0/24",
        ]
