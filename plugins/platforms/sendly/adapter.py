"""Sendly platform adapter for Hermes Agent.

Lets people text a Sendly number and chat with your Hermes agent over SMS —
the same conversational experience as Telegram or Discord, but over standard
text messages. Unlike the built-in Twilio gateway, Sendly handles carrier
verification for you (toll-free for US/Canada, instant for international), so
there's no approval gauntlet to send.

This is a drop-in Hermes plugin — no core Hermes changes required. Place this
directory at ``~/.hermes/plugins/sendly/`` (alongside ``PLUGIN.yaml``) and the
plugin system auto-wires it into ``hermes gateway setup``, status, cron
delivery, allowlists, and the rest.

Flow:
  inbound : Sendly POSTs a signed ``message.received`` webhook to this adapter's
            HTTP server -> we verify ``X-Sendly-Signature`` -> build a
            MessageEvent -> hand it to the agent.
  outbound: the agent's reply -> POST /api/v1/messages on the Sendly API.

Implements the documented BasePlatformAdapter contract; modelled on the
reference webhook adapters (bluebubbles / wecom_callback / line).
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
import time
from typing import Any

import aiohttp
from aiohttp import web

from gateway.platforms.base import (
    BasePlatformAdapter,
    MessageEvent,
    MessageType,
    SendResult,
)
from gateway.config import Platform, PlatformConfig

DEFAULT_BASE_URL = "https://sendly.live"
DEFAULT_PORT = 8080
DEFAULT_PATH = "/webhooks/sendly"
# Reject webhooks whose signed timestamp is older than this (replay defense).
TIMESTAMP_TOLERANCE_SECONDS = 5 * 60
# SMS renders markdown as literal characters, so strip the common tokens.
_MD_TOKENS = re.compile(r"(\*\*|__|\*|_|`|^#{1,6}\s+|^>\s+)", re.MULTILINE)

logger = logging.getLogger(__name__)


class SendlyAdapter(BasePlatformAdapter):
    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform("sendly"))
        extra = config.extra or {}

        self.api_key: str = os.getenv("SENDLY_API_KEY") or extra.get("api_key", "")
        self.from_number: str = (
            os.getenv("SENDLY_PHONE_NUMBER") or extra.get("phone_number", "")
        ).strip()
        self.base_url: str = (
            os.getenv("SENDLY_BASE_URL") or extra.get("base_url") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.webhook_secret: str = (
            os.getenv("SENDLY_WEBHOOK_SECRET") or extra.get("webhook_secret", "")
        )
        self.webhook_host: str = os.getenv("SENDLY_WEBHOOK_HOST", "0.0.0.0")
        self.webhook_port: int = int(os.getenv("SENDLY_WEBHOOK_PORT", str(DEFAULT_PORT)))
        self.insecure_no_signature: bool = (
            os.getenv("SENDLY_INSECURE_NO_SIGNATURE", "").lower() == "true"
        )

        self._runner: web.AppRunner | None = None
        self._http: aiohttp.ClientSession | None = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def connect(self) -> bool:
        if not self.api_key or not self.from_number:
            logger.error(
                "Sendly adapter needs SENDLY_API_KEY and SENDLY_PHONE_NUMBER"
            )
            return False
        if not self.webhook_secret and not self.insecure_no_signature:
            logger.error(
                "Sendly adapter needs SENDLY_WEBHOOK_SECRET (the signing secret "
                "of the webhook you created in Sendly), or set "
                "SENDLY_INSECURE_NO_SIGNATURE=true for local dev only."
            )
            return False

        self._http = aiohttp.ClientSession()

        app = web.Application()
        app.router.add_post(DEFAULT_PATH, self._handle_webhook)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.webhook_host, self.webhook_port)
        await site.start()

        masked = self.from_number[:5] + "***" + self.from_number[-4:]
        logger.info(
            "[sendly] webhook server listening on %s:%s%s, from: %s",
            self.webhook_host,
            self.webhook_port,
            DEFAULT_PATH,
            masked,
        )
        self._mark_connected()
        return True

    async def disconnect(self) -> None:
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
        if self._http is not None:
            await self._http.close()
            self._http = None
        self._mark_disconnected()

    # ------------------------------------------------------------------ #
    # Inbound: Sendly message.received webhook -> agent
    # ------------------------------------------------------------------ #
    async def _handle_webhook(self, request: web.Request) -> web.Response:
        raw = await request.read()
        timestamp = request.headers.get("X-Sendly-Timestamp", "")
        signature = request.headers.get("X-Sendly-Signature", "")

        if not self._verify_signature(raw, timestamp, signature):
            logger.warning("[sendly] rejected webhook: bad signature")
            return web.Response(status=401, text="invalid signature")

        # Acknowledge immediately — the agent reply is delivered later via the
        # Sendly send API (agent runs can take minutes; never block the webhook).
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return web.Response(status=400, text="bad payload")

        if payload.get("type") != "message.received":
            return web.Response(text="ignored")

        obj = (payload.get("data") or {}).get("object") or {}
        if obj.get("direction") != "inbound":
            return web.Response(text="ignored")

        sender = (obj.get("from") or "").strip()
        text = obj.get("text") or ""

        # Echo prevention — never re-ingest our own number.
        if sender and sender == self.from_number:
            return web.Response(text="ignored (self)")
        if not sender:
            return web.Response(text="ignored (no sender)")

        asyncio.create_task(self._dispatch(obj, sender, text))
        return web.Response(text="ok")

    async def _dispatch(self, obj: dict[str, Any], sender: str, text: str) -> None:
        try:
            source = self.build_source(
                chat_id=sender,
                chat_name=sender,
                chat_type="dm",
                user_id=sender,
                user_name=sender,
            )
            event = MessageEvent(
                text=text,
                message_type=MessageType.TEXT,
                source=source,
                message_id=str(obj.get("id") or ""),
            )
            await self.handle_message(event)
        except Exception as exc:  # noqa: BLE001 — never crash the listener
            logger.error("[sendly] dispatch failed: %s", exc)

    def _verify_signature(self, raw: bytes, timestamp: str, signature: str) -> bool:
        if self.insecure_no_signature:
            return True
        if not signature or not timestamp or not self.webhook_secret:
            return False
        try:
            if abs(int(time.time()) - int(timestamp)) > TIMESTAMP_TOLERANCE_SECONDS:
                return False
        except ValueError:
            return False
        signed = f"{timestamp}.".encode("utf-8") + raw
        expected = (
            "sha256="
            + hmac.new(self.webhook_secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
        )
        return hmac.compare_digest(expected, signature)

    # ------------------------------------------------------------------ #
    # Outbound: agent reply -> Sendly send API
    # ------------------------------------------------------------------ #
    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: str | None = None,
        metadata: dict | None = None,
    ) -> SendResult:
        body = _strip_markdown(content)
        if self._http is None:
            self._http = aiohttp.ClientSession()
        try:
            async with self._http.post(
                f"{self.base_url}/api/v1/messages",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps(
                    {
                        "to": chat_id,
                        "text": body,
                        "from": self.from_number,
                        "messageType": "transactional",
                    }
                ),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    err = (data or {}).get("message") or (data or {}).get("error") or f"HTTP {resp.status}"
                    return SendResult(success=False, error=str(err))
                msg_id = (data or {}).get("id") or ((data or {}).get("message") or {}).get("id")
                return SendResult(success=True, message_id=str(msg_id or ""))
        except Exception as exc:  # noqa: BLE001
            return SendResult(success=False, error=str(exc))

    async def get_chat_info(self, chat_id: str) -> dict:
        return {"name": chat_id, "type": "dm"}


def _strip_markdown(text: str) -> str:
    return _MD_TOKENS.sub("", text)


# ---------------------------------------------------------------------- #
# Plugin entry points
# ---------------------------------------------------------------------- #
def check_requirements() -> bool:
    return bool(os.getenv("SENDLY_API_KEY") and os.getenv("SENDLY_PHONE_NUMBER"))


def validate_config(config) -> bool:
    extra = getattr(config, "extra", {}) or {}
    return bool(
        (os.getenv("SENDLY_API_KEY") or extra.get("api_key"))
        and (os.getenv("SENDLY_PHONE_NUMBER") or extra.get("phone_number"))
    )


def _env_enablement() -> dict | None:
    api_key = os.getenv("SENDLY_API_KEY", "").strip()
    number = os.getenv("SENDLY_PHONE_NUMBER", "").strip()
    if not (api_key and number):
        return None
    seed: dict[str, Any] = {"api_key": api_key, "phone_number": number}
    secret = os.getenv("SENDLY_WEBHOOK_SECRET", "").strip()
    if secret:
        seed["webhook_secret"] = secret
    base = os.getenv("SENDLY_BASE_URL", "").strip()
    if base:
        seed["base_url"] = base
    home = os.getenv("SENDLY_HOME_CHANNEL")
    if home:
        seed["home_channel"] = {
            "chat_id": home,
            "name": os.getenv("SENDLY_HOME_CHANNEL_NAME", "Home"),
        }
    return seed


def register(ctx):
    """Plugin entry point — called by the Hermes plugin system."""
    ctx.register_platform(
        name="sendly",
        label="SMS (Sendly)",
        adapter_factory=lambda cfg: SendlyAdapter(cfg),
        check_fn=check_requirements,
        validate_config=validate_config,
        required_env=["SENDLY_API_KEY", "SENDLY_PHONE_NUMBER"],
        install_hint="pip install aiohttp",
        env_enablement_fn=_env_enablement,
        cron_deliver_env_var="SENDLY_HOME_CHANNEL",
        allowed_users_env="SENDLY_ALLOWED_USERS",
        allow_all_env="SENDLY_ALLOW_ALL_USERS",
        # SMS segments are 160 chars; Sendly splits long sends, but keep Hermes'
        # chunker aligned so boundaries stay natural.
        max_message_length=1600,
        platform_hint=(
            "You are chatting via SMS. Reply in plain text only — markdown is "
            "rendered as literal characters. Keep replies concise; long replies "
            "are split across multiple texts."
        ),
        emoji="📱",
    )
