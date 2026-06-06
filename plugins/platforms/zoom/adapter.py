"""Zoom Team Chat platform adapter for Hermes.

This adapter is intentionally webhook-first and API-driven:

- inbound Team Chat events come in through an aiohttp webhook server
- Zoom webhook URL validation and request signature checks are supported
- outbound messages use server-to-server OAuth plus a bot JID

The exact Team Chat event payloads vary across Zoom app types, so the
normalizer is deliberately defensive and accepts several likely field shapes.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    from aiohttp import web

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None  # type: ignore[assignment]

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None  # type: ignore[assignment]

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import BasePlatformAdapter, MessageEvent, MessageType, SendResult
from gateway.platforms.helpers import MessageDeduplicator

logger = logging.getLogger(__name__)

_DEFAULT_PORT = 8762
_DEFAULT_PATH = "/zoom/chat/webhook"
_DEFAULT_BASE_URL = "https://api.zoom.us"
_DEFAULT_SEND_PATH = "/v2/im/chat/messages"


def _hmac_sha256(secret: str, payload: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def compute_zoom_webhook_response_token(secret: str, plain_token: str) -> str:
    return _hmac_sha256(secret, plain_token)


def compute_zoom_request_signature(secret: str, timestamp: str, body: bytes) -> str:
    return _hmac_sha256(secret, f"v0:{timestamp}:{body.decode('utf-8')}")


def _coerce_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _deep_get(node: Any, *keys: str) -> Any:
    current = node
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _find_first(node: Any, candidate_keys: tuple[str, ...]) -> Any:
    stack = [node]
    wanted = {item.lower() for item in candidate_keys}
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if str(key).lower() in wanted and value not in (None, ""):
                    return value
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(reversed(current))
    return None


def normalize_zoom_chat_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    event_name = _coerce_text(payload.get("event") or payload.get("event_type") or payload.get("type")) or "unknown"
    obj = _deep_get(payload, "payload", "object") or payload.get("object") or payload
    body = _deep_get(obj, "message") or obj

    message_text = ""
    for key in ("text", "message", "content", "body", "cmd"):
        message_text = _coerce_text(_find_first(body, (key,)))
        if message_text:
            break

    user_name = _coerce_text(
        _find_first(obj, ("user_name", "sender_name", "display_name", "name", "user"))
    )
    user_id = _coerce_text(
        _find_first(obj, ("user_id", "sender_id", "account_id", "email", "sender"))
    )
    chat_id = _coerce_text(
        _find_first(obj, ("to_jid", "chat_id", "channel_id", "session_id", "conversation_id"))
    )
    thread_id = _coerce_text(_find_first(obj, ("thread_id", "message_thread_id", "parent_id")))
    message_id = _coerce_text(_find_first(obj, ("message_id", "id")))
    chat_topic = _coerce_text(_find_first(obj, ("channel_name", "topic", "session_name", "chat_name")))
    chat_type = "channel" if _find_first(obj, ("channel_id", "channel_name")) else "dm"

    return {
        "event": event_name,
        "text": message_text,
        "chat_id": chat_id,
        "chat_topic": chat_topic,
        "chat_type": chat_type,
        "thread_id": thread_id or None,
        "message_id": message_id or None,
        "user_id": user_id or None,
        "user_name": user_name or None,
        "raw": payload,
    }


@dataclass
class ZoomChatCredentials:
    account_id: str
    client_id: str
    client_secret: str
    bot_jid: str
    base_url: str = _DEFAULT_BASE_URL
    send_path: str = _DEFAULT_SEND_PATH


class ZoomChatClient:
    def __init__(self, credentials: ZoomChatCredentials):
        self.credentials = credentials
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    def _oauth_token_url(self) -> str:
        return "https://zoom.us/oauth/token"

    def get_access_token(self) -> str:
        now = time.time()
        if self._access_token and now < (self._expires_at - 60):
            return self._access_token
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests is not installed")

        response = requests.post(
            self._oauth_token_url(),
            params={
                "grant_type": "account_credentials",
                "account_id": self.credentials.account_id,
            },
            auth=(self.credentials.client_id, self.credentials.client_secret),
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        token = str(payload.get("access_token") or "").strip()
        if not token:
            raise RuntimeError("Zoom OAuth token response missing access_token")
        expires_in = int(payload.get("expires_in") or 3600)
        self._access_token = token
        self._expires_at = now + expires_in
        return token

    def _send_url(self) -> str:
        return f"{self.credentials.base_url.rstrip('/')}{self.credentials.send_path}"

    def build_send_payload(
        self,
        *,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "robot_jid": self.credentials.bot_jid,
            "to_jid": chat_id,
            "account_id": self.credentials.account_id,
            "content": {
                "head": {"text": "Hermes"},
                "body": [
                    {
                        "type": "message",
                        "text": content,
                    }
                ],
            },
        }
        if reply_to:
            body["reply_main_message_id"] = reply_to
        return body

    def send_message(self, *, chat_id: str, content: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests is not installed")
        response = requests.post(
            self._send_url(),
            headers={
                "Authorization": f"Bearer {self.get_access_token()}",
                "Content-Type": "application/json",
            },
            json=self.build_send_payload(chat_id=chat_id, content=content, reply_to=reply_to),
            timeout=20,
        )
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return {"status_code": response.status_code, "text": response.text}


def check_requirements() -> bool:
    return AIOHTTP_AVAILABLE and REQUESTS_AVAILABLE


def validate_config(config: PlatformConfig) -> bool:
    extra = config.extra or {}
    account_id = os.getenv("ZOOM_ACCOUNT_ID") or extra.get("account_id", "")
    client_id = os.getenv("ZOOM_CLIENT_ID") or extra.get("client_id", "")
    client_secret = os.getenv("ZOOM_CLIENT_SECRET") or extra.get("client_secret", "")
    bot_jid = os.getenv("ZOOM_CHAT_BOT_JID") or extra.get("bot_jid", "")
    secret = (
        os.getenv("ZOOM_WEBHOOK_SECRET_TOKEN")
        or os.getenv("ZOOM_WEBHOOK_SECRET")
        or extra.get("webhook_secret", "")
    )
    return bool(account_id and client_id and client_secret and bot_jid and secret)


def is_connected(config: PlatformConfig) -> bool:
    return validate_config(config)


class ZoomTeamChatAdapter(BasePlatformAdapter):
    MAX_MESSAGE_LENGTH = 4000

    def __init__(self, config: PlatformConfig):
        platform = Platform("zoom")
        super().__init__(config=config, platform=platform)
        extra = config.extra or {}
        self._account_id = os.getenv("ZOOM_ACCOUNT_ID") or extra.get("account_id", "")
        self._client_id = os.getenv("ZOOM_CLIENT_ID") or extra.get("client_id", "")
        self._client_secret = os.getenv("ZOOM_CLIENT_SECRET") or extra.get("client_secret", "")
        self._bot_jid = os.getenv("ZOOM_CHAT_BOT_JID") or extra.get("bot_jid", "")
        self._webhook_secret = (
            os.getenv("ZOOM_WEBHOOK_SECRET_TOKEN")
            or os.getenv("ZOOM_WEBHOOK_SECRET")
            or extra.get("webhook_secret", "")
        )
        self._base_url = extra.get("base_url", _DEFAULT_BASE_URL)
        self._send_path = extra.get("send_path", _DEFAULT_SEND_PATH)
        self._host = str(extra.get("host") or "0.0.0.0")
        self._port = int(extra.get("port") or _DEFAULT_PORT)
        self._path = str(extra.get("path") or _DEFAULT_PATH)
        self._runner: Optional["web.AppRunner"] = None
        self._dedup = MessageDeduplicator(max_size=1000)
        self._chat_cache: Dict[str, Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "Zoom Team Chat"

    def _client(self) -> ZoomChatClient:
        return ZoomChatClient(
            ZoomChatCredentials(
                account_id=self._account_id,
                client_id=self._client_id,
                client_secret=self._client_secret,
                bot_jid=self._bot_jid,
                base_url=self._base_url,
                send_path=self._send_path,
            )
        )

    def _verify_signature(self, timestamp: str, signature: str, body: bytes) -> bool:
        if not self._webhook_secret:
            return True
        if not timestamp or not signature:
            return False
        expected = compute_zoom_request_signature(self._webhook_secret, timestamp, body)
        actual = signature.split("=", 1)[-1]
        return hmac.compare_digest(expected.encode("utf-8"), actual.encode("utf-8"))

    def _is_self_event(self, normalized: Dict[str, Any]) -> bool:
        user_id = _coerce_text(normalized.get("user_id"))
        if user_id and self._bot_jid and user_id == self._bot_jid:
            return True

        raw = normalized.get("raw") or {}
        obj = _deep_get(raw, "payload", "object") or raw.get("object") or {}
        sender_jid = _coerce_text(_find_first(obj, ("sender_jid", "user_jid", "robot_jid", "bot_jid")))
        return bool(sender_jid and self._bot_jid and sender_jid == self._bot_jid)

    async def _handle_health(self, request: "web.Request") -> "web.Response":
        return web.json_response({"ok": True, "platform": "zoom"})

    async def _handle_webhook(self, request: "web.Request") -> "web.Response":
        raw_body = await request.read()
        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except Exception:
            return web.json_response({"ok": False, "error": "invalid JSON"}, status=400)

        timestamp = request.headers.get("x-zm-request-timestamp", "")
        signature = request.headers.get("x-zm-signature", "")
        if self._webhook_secret and not self._verify_signature(timestamp, signature, raw_body):
            return web.json_response({"ok": False, "error": "invalid signature"}, status=401)

        event_name = _coerce_text(payload.get("event") or payload.get("event_type") or payload.get("type"))
        if event_name == "endpoint.url_validation":
            plain_token = (
                _deep_get(payload, "payload", "plainToken")
                or _deep_get(payload, "payload", "plain_token")
                or payload.get("plainToken")
                or ""
            )
            if not plain_token:
                return web.json_response({"ok": False, "error": "missing plainToken"}, status=400)
            return web.json_response(
                {
                    "plainToken": plain_token,
                    "encryptedToken": compute_zoom_webhook_response_token(self._webhook_secret, plain_token),
                }
            )

        normalized = normalize_zoom_chat_event(payload)
        if self._is_self_event(normalized):
            return web.json_response({"ok": True, "ignored": True, "reason": "self_message"})
        if not normalized["text"] or not normalized["chat_id"]:
            return web.json_response(
                {"ok": True, "ignored": True, "reason": "no text/chat_id"},
                status=202,
            )

        message_id = normalized["message_id"]
        if message_id and self._dedup.is_duplicate(message_id):
            return web.json_response({"ok": True, "duplicate": True})

        source = self.build_source(
            chat_id=normalized["chat_id"],
            chat_name=normalized["chat_topic"] or normalized["chat_id"],
            chat_type=normalized["chat_type"],
            user_id=normalized["user_id"],
            user_name=normalized["user_name"],
            thread_id=normalized["thread_id"],
            message_id=message_id,
        )
        self._chat_cache[normalized["chat_id"]] = {
            "name": normalized["chat_topic"] or normalized["chat_id"],
            "type": normalized["chat_type"],
            "thread_id": normalized["thread_id"],
        }
        event = MessageEvent(
            text=normalized["text"],
            message_type=MessageType.TEXT,
            source=source,
            raw_message={
                "zoom_event": normalized["event"],
                "zoom_raw": normalized["raw"],
            },
            message_id=message_id,
        )
        await self.handle_message(event)
        return web.json_response({"ok": True, "chat_id": normalized["chat_id"], "event": normalized["event"]})

    async def connect(self) -> bool:
        if not AIOHTTP_AVAILABLE:
            self._set_fatal_error("MISSING_SDK", "aiohttp not installed. Run: pip install aiohttp", retryable=False)
            return False
        if not REQUESTS_AVAILABLE:
            self._set_fatal_error("MISSING_SDK", "requests not installed. Run: pip install requests", retryable=False)
            return False
        if not validate_config(self.config):
            self._set_fatal_error(
                "MISSING_CREDENTIALS",
                "Zoom Team Chat requires ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_CHAT_BOT_JID, and ZOOM_WEBHOOK_SECRET_TOKEN",
                retryable=False,
            )
            return False

        try:
            app = web.Application()
            app.router.add_get("/health", self._handle_health)
            app.router.add_post(self._path, self._handle_webhook)
            self._runner = web.AppRunner(app)
            await self._runner.setup()
            site = web.TCPSite(self._runner, self._host, self._port)
            await site.start()
            self._running = True
            self._mark_connected()
            logger.info("[zoom] Team Chat webhook listening on %s:%d%s", self._host, self._port, self._path)
            return True
        except Exception as exc:
            self._set_fatal_error("CONNECT_FAILED", f"Zoom Team Chat connection failed: {exc}", retryable=True)
            logger.error("[zoom] connect failed: %s", exc)
            return False

    async def disconnect(self) -> None:
        self._running = False
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
        self._mark_disconnected()

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        try:
            payload = await asyncio.to_thread(
                self._client().send_message,
                chat_id=chat_id,
                content=content,
                reply_to=reply_to,
            )
            message_id = _coerce_text(_find_first(payload, ("message_id", "id")))
            return SendResult(success=True, message_id=message_id or None, raw_response=payload)
        except Exception as exc:
            return SendResult(success=False, error=str(exc), retryable=True)

    async def send_typing(self, chat_id: str, metadata=None) -> None:
        return None

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        cached = self._chat_cache.get(chat_id)
        if cached:
            return {"name": cached.get("name", chat_id), "type": cached.get("type", "dm"), "chat_id": chat_id}
        return {"name": chat_id, "type": "dm", "chat_id": chat_id}


def interactive_setup() -> None:
    from hermes_cli.config import get_env_value, save_env_value
    from hermes_cli.cli_output import print_info, print_success, print_warning, prompt

    print_info("Zoom Team Chat setup")
    account_id = prompt("Account ID", default=get_env_value("ZOOM_ACCOUNT_ID") or "")
    client_id = prompt("Client ID", default=get_env_value("ZOOM_CLIENT_ID") or "")
    client_secret = prompt("Client Secret", default=get_env_value("ZOOM_CLIENT_SECRET") or "", password=True)
    bot_jid = prompt("Chat bot JID", default=get_env_value("ZOOM_CHAT_BOT_JID") or "")
    secret = prompt(
        "Webhook secret token",
        default=(get_env_value("ZOOM_WEBHOOK_SECRET_TOKEN") or get_env_value("ZOOM_WEBHOOK_SECRET") or ""),
        password=True,
    )

    if not all([account_id, client_id, client_secret, bot_jid, secret]):
        print_warning("Zoom Team Chat setup skipped — all fields are required")
        return

    save_env_value("ZOOM_ACCOUNT_ID", account_id.strip())
    save_env_value("ZOOM_CLIENT_ID", client_id.strip())
    save_env_value("ZOOM_CLIENT_SECRET", client_secret.strip())
    save_env_value("ZOOM_CHAT_BOT_JID", bot_jid.strip())
    save_env_value("ZOOM_WEBHOOK_SECRET_TOKEN", secret.strip())
    print_success("Zoom Team Chat configuration saved to ~/.hermes/.env")


def register(ctx) -> None:
    ctx.register_platform(
        name="zoom",
        label="Zoom Team Chat",
        adapter_factory=lambda cfg: ZoomTeamChatAdapter(cfg),
        check_fn=check_requirements,
        validate_config=validate_config,
        is_connected=is_connected,
        required_env=[
            "ZOOM_ACCOUNT_ID",
            "ZOOM_CLIENT_ID",
            "ZOOM_CLIENT_SECRET",
            "ZOOM_CHAT_BOT_JID",
            "ZOOM_WEBHOOK_SECRET_TOKEN",
        ],
        install_hint="pip install aiohttp requests",
        setup_fn=interactive_setup,
        allowed_users_env="ZOOM_ALLOWED_USERS",
        allow_all_env="ZOOM_ALLOW_ALL_USERS",
        max_message_length=4000,
        emoji="🎥",
        allow_update_command=True,
        platform_hint=(
            "You are chatting via Zoom Team Chat. Keep formatting simple and readable. "
            "Prefer short paragraphs and bullets over complex markdown."
        ),
    )
