"""Tests for the Zoom Team Chat platform plugin."""

from __future__ import annotations

import json

from gateway.config import PlatformConfig
from plugins.platforms.zoom.adapter import (
    ZoomChatClient,
    ZoomChatCredentials,
    ZoomTeamChatAdapter,
    compute_zoom_request_signature,
    compute_zoom_webhook_response_token,
    normalize_zoom_chat_event,
    register,
)


def test_zoom_signature_helpers_are_stable():
    body = b'{"hello":"world"}'
    sig = compute_zoom_request_signature("secret", "1700000000", body)
    assert sig == compute_zoom_request_signature("secret", "1700000000", body)
    assert len(sig) == 64

    token = compute_zoom_webhook_response_token("secret", "plain-token")
    assert token == compute_zoom_webhook_response_token("secret", "plain-token")
    assert len(token) == 64


def test_normalize_zoom_chat_event_handles_nested_payload():
    payload = {
        "event": "chat.message.sent",
        "payload": {
            "object": {
                "to_jid": "chat-123",
                "channel_name": "Hermes Ops",
                "message_id": "m-1",
                "sender_name": "Dilek",
                "sender_id": "user-9",
                "message": {
                    "text": "please prepare the rollout notes",
                },
            }
        },
    }
    normalized = normalize_zoom_chat_event(payload)
    assert normalized["chat_id"] == "chat-123"
    assert normalized["chat_topic"] == "Hermes Ops"
    assert normalized["message_id"] == "m-1"
    assert normalized["user_name"] == "Dilek"
    assert normalized["text"] == "please prepare the rollout notes"


def test_zoom_chat_client_builds_structured_send_payload():
    client = ZoomChatClient(
        ZoomChatCredentials(
            account_id="acct",
            client_id="cid",
            client_secret="sec",
            bot_jid="bot-jid",
        )
    )
    payload = client.build_send_payload(chat_id="chat-1", content="Hello Zoom", reply_to="root-1")
    assert payload["robot_jid"] == "bot-jid"
    assert payload["to_jid"] == "chat-1"
    assert payload["reply_main_message_id"] == "root-1"
    assert payload["content"]["body"][0]["text"] == "Hello Zoom"


def test_register_adds_zoom_platform_entry():
    calls = {}

    class _Ctx:
        def register_platform(self, **kw):
            calls.update(kw)

    register(_Ctx())
    assert calls["name"] == "zoom"
    assert calls["label"] == "Zoom Team Chat"
    assert callable(calls["adapter_factory"])


def test_send_uses_client_and_preserves_reply_to(monkeypatch):
    adapter = ZoomTeamChatAdapter(
        PlatformConfig(
            enabled=True,
            extra={
                "account_id": "acct",
                "client_id": "cid",
                "client_secret": "sec",
                "bot_jid": "bot-jid",
                "webhook_secret": "zoom-secret",
            },
        )
    )

    captured = {}

    class _FakeClient:
        def send_message(self, *, chat_id: str, content: str, reply_to: str | None = None):
            captured["chat_id"] = chat_id
            captured["content"] = content
            captured["reply_to"] = reply_to
            return {"message_id": "out-1"}

    monkeypatch.setattr(adapter, "_client", lambda: _FakeClient())

    import asyncio

    result = asyncio.run(adapter.send("chat-1", "hello zoom", reply_to="root-9"))
    assert result.success is True
    assert result.message_id == "out-1"
    assert captured == {
        "chat_id": "chat-1",
        "content": "hello zoom",
        "reply_to": "root-9",
    }


def test_send_returns_retryable_error_on_client_failure(monkeypatch):
    adapter = ZoomTeamChatAdapter(
        PlatformConfig(
            enabled=True,
            extra={
                "account_id": "acct",
                "client_id": "cid",
                "client_secret": "sec",
                "bot_jid": "bot-jid",
                "webhook_secret": "zoom-secret",
            },
        )
    )

    class _FailingClient:
        def send_message(self, *, chat_id: str, content: str, reply_to: str | None = None):
            raise RuntimeError("send failed")

    monkeypatch.setattr(adapter, "_client", lambda: _FailingClient())

    import asyncio

    result = asyncio.run(adapter.send("chat-1", "hello zoom"))
    assert result.success is False
    assert result.retryable is True
    assert "send failed" in result.error


def test_webhook_handler_validates_and_dispatches(monkeypatch):
    adapter = ZoomTeamChatAdapter(
        PlatformConfig(
            enabled=True,
            extra={
                "account_id": "acct",
                "client_id": "cid",
                "client_secret": "sec",
                "bot_jid": "bot-jid",
                "webhook_secret": "zoom-secret",
            },
        )
    )

    captured = {}

    async def _fake_handle_message(event):
        captured["event"] = event

    monkeypatch.setattr(adapter, "handle_message", _fake_handle_message)

    class _Request:
        def __init__(self, payload: dict, headers: dict[str, str]):
            self._body = json.dumps(payload).encode("utf-8")
            self.headers = headers

        async def read(self) -> bytes:
            return self._body

    async def _run():
        validation_payload = {"event": "endpoint.url_validation", "payload": {"plainToken": "abc123"}}
        timestamp = "1700000000"
        validation_sig = compute_zoom_request_signature(
            "zoom-secret",
            timestamp,
            json.dumps(validation_payload).encode("utf-8"),
        )
        validation_req = _Request(
            validation_payload,
            {
                "x-zm-request-timestamp": timestamp,
                "x-zm-signature": f"v0={validation_sig}",
            },
        )
        validation_resp = await adapter._handle_webhook(validation_req)
        validation_body = json.loads(validation_resp.text)
        assert validation_body["plainToken"] == "abc123"

        message_payload = {
            "event": "chat.message.sent",
            "payload": {
                "object": {
                    "to_jid": "chat-123",
                    "message_id": "m-1",
                    "sender_name": "Dilek",
                    "sender_id": "user-9",
                    "message": {"text": "zoom adapter smoke"},
                }
            },
        }
        message_sig = compute_zoom_request_signature(
            "zoom-secret",
            timestamp,
            json.dumps(message_payload).encode("utf-8"),
        )
        message_req = _Request(
            message_payload,
            {
                "x-zm-request-timestamp": timestamp,
                "x-zm-signature": f"v0={message_sig}",
            },
        )
        message_resp = await adapter._handle_webhook(message_req)
        body = json.loads(message_resp.text)
        assert body["ok"] is True

    import asyncio

    asyncio.run(_run())
    assert captured["event"].text == "zoom adapter smoke"
    assert captured["event"].source.chat_id == "chat-123"


def test_webhook_handler_ignores_self_messages(monkeypatch):
    adapter = ZoomTeamChatAdapter(
        PlatformConfig(
            enabled=True,
            extra={
                "account_id": "acct",
                "client_id": "cid",
                "client_secret": "sec",
                "bot_jid": "bot-jid",
                "webhook_secret": "zoom-secret",
            },
        )
    )

    called = {"count": 0}

    async def _fake_handle_message(event):
        called["count"] += 1

    monkeypatch.setattr(adapter, "handle_message", _fake_handle_message)

    class _Request:
        def __init__(self, payload: dict, headers: dict[str, str]):
            self._body = json.dumps(payload).encode("utf-8")
            self.headers = headers

        async def read(self) -> bytes:
            return self._body

    async def _run():
        payload = {
            "event": "chat.message.sent",
            "payload": {
                "object": {
                    "to_jid": "chat-123",
                    "message_id": "m-self",
                    "sender_jid": "bot-jid",
                    "sender_name": "Hermes",
                    "message": {"text": "ignore me"},
                }
            },
        }
        timestamp = "1700000000"
        sig = compute_zoom_request_signature(
            "zoom-secret",
            timestamp,
            json.dumps(payload).encode("utf-8"),
        )
        req = _Request(payload, {"x-zm-request-timestamp": timestamp, "x-zm-signature": f"v0={sig}"})
        response = await adapter._handle_webhook(req)
        body = json.loads(response.text)
        assert body["ignored"] is True
        assert body["reason"] == "self_message"

    import asyncio

    asyncio.run(_run())
    assert called["count"] == 0
