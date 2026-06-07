"""Native Trello webhook handling for board activity routes."""

import base64
import hashlib
import hmac
import json

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from gateway.config import PlatformConfig
from gateway.platforms.webhook import WebhookAdapter


def _make_adapter(callback_url="https://webhooks.example.com/webhooks/trello-board-activity"):
    routes = {
        "trello-board-activity": {
            "signature_provider": "trello",
            "secret": "trello-app-secret",
            "callback_url": callback_url,
            "events": ["commentCard", "updateCard:idList", "createCard"],
            "prompt": "Trello {action.type}: {action.data.card.name}",
            "deliver": "log",
        }
    }
    return WebhookAdapter(PlatformConfig(enabled=True, extra={"routes": routes}))


def _create_app(adapter: WebhookAdapter) -> web.Application:
    app = web.Application()
    app.router.add_get("/health", adapter._handle_health)
    app.router.add_head("/webhooks/{route_name}", adapter._handle_webhook_head)
    app.router.add_post("/webhooks/{route_name}", adapter._handle_webhook)
    return app


def _trello_signature(body: bytes, secret: str, callback_url: str) -> str:
    digest = hmac.new(secret.encode(), body + callback_url.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


TRELLO_COMMENT_PAYLOAD = {
    "action": {
        "id": "6a1800000000000000000001",
        "type": "commentCard",
        "date": "2026-05-27T19:50:00.000Z",
        "data": {
            "text": "Please wake Charlie",
            "card": {
                "id": "6a16b1dc3e938f411c0ad0cb",
                "name": "Review updated Charlie / Razza Trello operating system",
                "shortLink": "abc12345",
            },
            "board": {"id": "6a16b1d6ab84d89c0f84b58e", "name": "Charlie / Razza Kanban"},
        },
        "memberCreator": {"fullName": "Ryan Laubscher", "username": "ryanlaubscher"},
    },
    "model": {"id": "6a16b1d6ab84d89c0f84b58e", "name": "Charlie / Razza Kanban"},
    "webhook": {"id": "6a18000000000000000000ff"},
}


class TestNativeTrelloWebhook:
    @pytest.mark.asyncio
    async def test_trello_head_validation_request_returns_ok(self):
        adapter = _make_adapter()
        app = _create_app(adapter)

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.head("/webhooks/trello-board-activity")
            assert resp.status == 200

    @pytest.mark.asyncio
    async def test_signed_trello_comment_event_wakes_agent_with_action_id(self):
        callback_url = "https://webhooks.example.com/webhooks/trello-board-activity"
        adapter = _make_adapter(callback_url=callback_url)
        captured_events = []

        async def _capture(event):
            captured_events.append(event)

        adapter.handle_message = _capture
        app = _create_app(adapter)
        body = json.dumps(TRELLO_COMMENT_PAYLOAD, separators=(",", ":")).encode()
        signature = _trello_signature(body, "trello-app-secret", callback_url)

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.post(
                "/webhooks/trello-board-activity",
                data=body,
                headers={"Content-Type": "application/json", "X-Trello-Webhook": signature},
            )
            assert resp.status == 202
            data = await resp.json()
            assert data["event"] == "commentCard"
            assert data["delivery_id"] == "trello-action:6a1800000000000000000001"

        assert len(captured_events) == 1
        event = captured_events[0]
        assert event.message_id == "trello-action:6a1800000000000000000001"
        assert "Trello commentCard" in event.text
        assert "Review updated Charlie" in event.text

    @pytest.mark.asyncio
    async def test_trello_signature_uses_exact_registered_callback_url(self):
        registered_callback = "https://webhooks.example.com/webhooks/trello-board-activity"
        wrong_callback = "https://webhooks.example.com/webhooks/trello-board-activity/"
        adapter = _make_adapter(callback_url=registered_callback)
        app = _create_app(adapter)
        body = json.dumps(TRELLO_COMMENT_PAYLOAD, separators=(",", ":")).encode()
        signature_for_wrong_url = _trello_signature(body, "trello-app-secret", wrong_callback)

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.post(
                "/webhooks/trello-board-activity",
                data=body,
                headers={"Content-Type": "application/json", "X-Trello-Webhook": signature_for_wrong_url},
            )
            assert resp.status == 401

    @pytest.mark.asyncio
    async def test_trello_duplicate_action_id_is_deduped(self):
        callback_url = "https://webhooks.example.com/webhooks/trello-board-activity"
        adapter = _make_adapter(callback_url=callback_url)
        captured_events = []

        async def _capture(event):
            captured_events.append(event)

        adapter.handle_message = _capture
        app = _create_app(adapter)
        body = json.dumps(TRELLO_COMMENT_PAYLOAD, separators=(",", ":")).encode()
        signature = _trello_signature(body, "trello-app-secret", callback_url)

        async with TestClient(TestServer(app)) as cli:
            first = await cli.post(
                "/webhooks/trello-board-activity",
                data=body,
                headers={"Content-Type": "application/json", "X-Trello-Webhook": signature},
            )
            second = await cli.post(
                "/webhooks/trello-board-activity",
                data=body,
                headers={"Content-Type": "application/json", "X-Trello-Webhook": signature},
            )
            assert first.status == 202
            assert second.status == 200
            assert (await second.json())["status"] == "duplicate"

        assert len(captured_events) == 1

    @pytest.mark.asyncio
    async def test_trello_route_rejects_generic_signature_even_with_same_secret(self):
        adapter = _make_adapter()
        app = _create_app(adapter)
        body = json.dumps(TRELLO_COMMENT_PAYLOAD, separators=(",", ":")).encode()
        generic_signature = hmac.new(
            b"trello-app-secret", body, hashlib.sha256
        ).hexdigest()

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.post(
                "/webhooks/trello-board-activity",
                data=body,
                headers={"Content-Type": "application/json", "X-Webhook-Signature": generic_signature},
            )
            assert resp.status == 401

    @pytest.mark.asyncio
    async def test_trello_update_card_list_move_maps_to_id_list_event(self):
        callback_url = "https://webhooks.example.com/webhooks/trello-board-activity"
        adapter = _make_adapter(callback_url=callback_url)
        captured_events = []

        async def _capture(event):
            captured_events.append(event)

        adapter.handle_message = _capture
        app = _create_app(adapter)
        payload = {
            "action": {
                "id": "6a1800000000000000000002",
                "type": "updateCard",
                "date": "2026-05-27T20:15:00.000Z",
                "data": {
                    "card": {"id": "card1", "name": "Move me"},
                    "board": {"id": "board1", "name": "Charlie / Razza Kanban"},
                    "listBefore": {"id": "list-a", "name": "Inbox / Captured"},
                    "listAfter": {"id": "list-b", "name": "Ready for Charlie"},
                },
                "memberCreator": {"fullName": "Ryan Laubscher"},
            },
            "model": {"id": "board1", "name": "Charlie / Razza Kanban"},
        }
        body = json.dumps(payload, separators=(",", ":")).encode()
        signature = _trello_signature(body, "trello-app-secret", callback_url)

        async with TestClient(TestServer(app)) as cli:
            resp = await cli.post(
                "/webhooks/trello-board-activity",
                data=body,
                headers={"Content-Type": "application/json", "X-Trello-Webhook": signature},
            )
            assert resp.status == 202
            data = await resp.json()
            assert data["event"] == "updateCard:idList"

        assert len(captured_events) == 1
