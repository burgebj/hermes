"""BlueBubbles iMessage platform adapter.

Uses the local BlueBubbles macOS server for outbound REST sends and inbound
webhooks.  Supports text messaging, media attachments (images, voice, video,
documents), tapback reactions, typing indicators, and read receipts.

Architecture based on PR #5869 (benjaminsehl) with inbound attachment
downloading from PR #4588 (YuhangLin).
"""

import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import (
    BasePlatformAdapter,
    MessageEvent,
    MessageType,
    SendResult,
    cache_image_from_bytes,
    cache_audio_from_bytes,
    cache_document_from_bytes,
)
from gateway.platforms.helpers import strip_markdown

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_WEBHOOK_HOST = "127.0.0.1"
DEFAULT_WEBHOOK_PORT = 8645
DEFAULT_WEBHOOK_PATH = "/bluebubbles-webhook"
MAX_TEXT_LENGTH = 4000

# Tapback reaction codes (BlueBubbles associatedMessageType values)
_TAPBACK_ADDED = {
    2000: "love", 2001: "like", 2002: "dislike",
    2003: "laugh", 2004: "emphasize", 2005: "question",
}
_TAPBACK_REMOVED = {
    3000: "love", 3001: "like", 3002: "dislike",
    3003: "laugh", 3004: "emphasize", 3005: "question",
}

# Webhook event types that carry user messages
_MESSAGE_EVENTS = {"new-message", "message", "updated-message"}

# Log redaction patterns
_PHONE_RE = re.compile(r"\+?\d{7,15}")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def _redact(text: str) -> str:
    """Redact phone numbers and emails from log output."""
    text = _PHONE_RE.sub("[REDACTED]", text)
    text = _EMAIL_RE.sub("[REDACTED]", text)
    return text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_bluebubbles_requirements() -> bool:
    try:
        import aiohttp  # noqa: F401
        import httpx  # noqa: F401
    except ImportError:
        return False
    return True


def _normalize_server_url(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    if not re.match(r"^https?://", value, flags=re.I):
        value = f"http://{value}"
    return value.rstrip("/")





# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class BlueBubblesAdapter(BasePlatformAdapter):
    platform = Platform.BLUEBUBBLES
    SUPPORTS_MESSAGE_EDITING = False
    MAX_MESSAGE_LENGTH = MAX_TEXT_LENGTH

    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform.BLUEBUBBLES)
        extra = config.extra or {}
        self.server_url = _normalize_server_url(
            extra.get("server_url") or os.getenv("BLUEBUBBLES_SERVER_URL", "")
        )
        self.password = extra.get("password") or os.getenv("BLUEBUBBLES_PASSWORD", "")
        self.webhook_host = (
            extra.get("webhook_host")
            or os.getenv("BLUEBUBBLES_WEBHOOK_HOST", DEFAULT_WEBHOOK_HOST)
        )
        self.webhook_port = int(
            extra.get("webhook_port")
            or os.getenv("BLUEBUBBLES_WEBHOOK_PORT", str(DEFAULT_WEBHOOK_PORT))
        )
        self.webhook_path = (
            extra.get("webhook_path")
            or os.getenv("BLUEBUBBLES_WEBHOOK_PATH", DEFAULT_WEBHOOK_PATH)
        )
        if not str(self.webhook_path).startswith("/"):
            self.webhook_path = f"/{self.webhook_path}"
        self.send_read_receipts = bool(extra.get("send_read_receipts", True))
        self.client: Optional[httpx.AsyncClient] = None
        self._runner = None
        self._private_api_enabled: Optional[bool] = None
        self._helper_connected: bool = False
        self._guid_cache: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------

    def _api_url(self, path: str) -> str:
        sep = "&" if "?" in path else "?"
        return f"{self.server_url}{path}{sep}password={quote(self.password, safe='')}"

    async def _api_get(self, path: str) -> Dict[str, Any]:
        assert self.client is not None
        res = await self.client.get(self._api_url(path))
        res.raise_for_status()
        return res.json()

    async def _api_post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        assert self.client is not None
        res = await self.client.post(self._api_url(path), json=payload)
        res.raise_for_status()
        return res.json()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> bool:
        if not self.server_url or not self.password:
            logger.error(
                "[bluebubbles] BLUEBUBBLES_SERVER_URL and BLUEBUBBLES_PASSWORD are required"
            )
            return False
        from aiohttp import web

        # Tighter keepalive so idle CLOSE_WAIT drains promptly (#18451).
        from gateway.platforms._http_client_limits import platform_httpx_limits
        self.client = httpx.AsyncClient(timeout=30.0, limits=platform_httpx_limits())
        try:
            await self._api_get("/api/v1/ping")
            info = await self._api_get("/api/v1/server/info")
            server_data = (info or {}).get("data", {})
            self._private_api_enabled = bool(server_data.get("private_api"))
            self._helper_connected = bool(server_data.get("helper_connected"))
            logger.info(
                "[bluebubbles] connected to %s (private_api=%s, helper=%s)",
                self.server_url,
                self._private_api_enabled,
                self._helper_connected,
            )
        except Exception as exc:
            logger.error(
                "[bluebubbles] cannot reach server at %s: %s", self.server_url, exc
            )
            if self.client:
                await self.client.aclose()
                self.client = None
            return False

        app = web.Application()
        app.router.add_get("/health", lambda _: web.Response(text="ok"))
        app.router.add_post(self.webhook_path, self._handle_webhook)
        # The webhook auth value is carried in the query string because the
        # BlueBubbles webhook API cannot send custom headers. Do not let
        # aiohttp access logs write that request target to agent.log.
        self._runner = web.AppRunner(app, access_log=None)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.webhook_host, self.webhook_port)
        await site.start()
        self._mark_connected()
        logger.info(
            "[bluebubbles] webhook listening on http://%s:%s%s",
            self.webhook_host,
            self.webhook_port,
            self.webhook_path,
        )

        # Register webhook with BlueBubbles server
        # This is required for the server to know where to send events
        await self._register_webhook()

        return True

    async def disconnect(self) -> None:
        # Unregister webhook before cleaning up
        await self._unregister_webhook()

        if self.client:
            await self.client.aclose()
            self.client = None
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
        self._mark_disconnected()

    @property
    def _webhook_url(self) -> str:
        """Compute the external webhook URL for BlueBubbles registration."""
        host = self.webhook_host
        if host in {"0.0.0.0", "127.0.0.1", "localhost", "::"}:
            host = "localhost"
        return f"http://{host}:{self.webhook_port}{self.webhook_path}"

    @property
    def _webhook_register_url(self) -> str:
        """Webhook URL registered with BlueBubbles, including the password as
        a query param so inbound webhook POSTs carry credentials.

        BlueBubbles posts events to the exact URL registered via
        ``/api/v1/webhook``. Its webhook registration API does not support
        custom headers, so embedding the password in the URL is the only
        way to authenticate inbound webhooks without disabling auth.
        """
        base = self._webhook_url
        if self.password:
            return f"{base}?password={quote(self.password, safe='')}"
        return base

    @property
    def _webhook_register_url_for_log(self) -> str:
        """Webhook registration URL safe for logs."""
        base = self._webhook_url
        if self.password:
            return f"{base}?password=***"
        return base

    async def _find_registered_webhooks(self, url: str) -> list:
        """Return list of BB webhook entries matching *url*."""
        try:
            res = await self._api_get("/api/v1/webhook")
            data = res.get("data")
            if isinstance(data, list):
                return [wh for wh in data if wh.get("url") == url]
        except Exception:
            pass
        return []

    async def _register_webhook(self) -> bool:
        """Register this webhook URL with the BlueBubbles server.

        BlueBubbles requires webhooks to be registered via API before
        it will send events.  Checks for an existing registration first
        to avoid duplicates (e.g. after a crash without clean shutdown).
        """
        if not self.client:
            return False

        webhook_url = self._webhook_register_url

        # Crash resilience — reuse an existing registration if present
        existing = await self._find_registered_webhooks(webhook_url)
        if existing:
            logger.info(
                "[bluebubbles] webhook already registered: %s",
                self._webhook_register_url_for_log,
            )
            return True

        payload = {
            "url": webhook_url,
            "events": ["new-message", "updated-message"],
        }

        try:
            res = await self._api_post("/api/v1/webhook", payload)
            status = res.get("status", 0)
            if 200 <= status < 300:
                logger.info(
                    "[bluebubbles] webhook registered with server: %s",
                    self._webhook_register_url_for_log,
                )
                return True
            else:
                logger.warning(
                    "[bluebubbles] webhook registration returned status %s: %s",
                    status,
                    res.get("message"),
                )
                return False
        except Exception as exc:
            logger.warning(
                "[bluebubbles] failed to register webhook with server: %s",
                exc,
            )
            return False

    async def _unregister_webhook(self) -> bool:
        """Unregister this webhook URL from the BlueBubbles server.

        Removes *all* matching registrations to clean up any duplicates
        left by prior crashes.
        """
        if not self.client:
            return False

        webhook_url = self._webhook_register_url
        removed = False

        try:
            for wh in await self._find_registered_webhooks(webhook_url):
                wh_id = wh.get("id")
                if wh_id:
                    res = await self.client.delete(
                        self._api_url(f"/api/v1/webhook/{wh_id}")
                    )
                    res.raise_for_status()
                    removed = True
            if removed:
                logger.info(
                    "[bluebubbles] webhook unregistered: %s",
                    self._webhook_register_url_for_log,
                )
        except Exception as exc:
            logger.debug(
                "[bluebubbles] failed to unregister webhook (non-critical): %s",
                exc,
            )
        return removed

    # ------------------------------------------------------------------
    # Chat GUID resolution
    # ------------------------------------------------------------------

    async def _resolve_chat_guid(self, target: str) -> Optional[str]:
        """Resolve an email/phone to a BlueBubbles chat GUID.

        If *target* already contains a semicolon (raw GUID format like
        ``iMessage;-;user@example.com``), it is returned as-is.  Otherwise
        the adapter queries the BlueBubbles chat list and matches on
        ``chatIdentifier`` or participant address.
        """
        target = (target or "").strip()
        if not target:
            return None
        # Already a raw GUID
        if ";" in target:
            return target
        if target in self._guid_cache:
            return self._guid_cache[target]
        try:
            payload = await self._api_post(
                "/api/v1/chat/query",
                {"limit": 100, "offset": 0, "with": ["participants"]},
            )
            for chat in payload.get("data", []) or []:
                guid = chat.get("guid") or chat.get("chatGuid")
                identifier = chat.get("chatIdentifier") or chat.get("identifier")
                if identifier == target:
                    if guid:
                        self._guid_cache[target] = guid
                    return guid
                for part in chat.get("participants", []) or []:
                    if (part.get("address") or "").strip() == target and guid:
                        self._guid_cache[target] = guid
                        return guid
        except Exception:
            pass
        return None

    async def _create_chat_for_handle(
        self, address: str, message: str
    ) -> SendResult:
        """Create a new chat by sending the first message to *address*."""
        payload = {
            "addresses": [address],
            "message": message,
            "tempGuid": f"temp-{datetime.utcnow().timestamp()}",
        }
        try:
            res = await self._api_post("/api/v1/chat/new", payload)
            data = res.get("data") or {}
            msg_id = data.get("guid") or data.get("messageGuid") or "ok"
            return SendResult(success=True, message_id=str(msg_id), raw_response=res)
        except Exception as exc:
            return SendResult(success=False, error=str(exc))

    # ------------------------------------------------------------------
    # Text sending
    # ------------------------------------------------------------------

    @staticmethod
    def truncate_message(content: str, max_length: int = MAX_TEXT_LENGTH) -> List[str]:
        # Use the base splitter but skip pagination indicators — iMessage
        # bubbles flow naturally without "(1/3)" suffixes.
        chunks = BasePlatformAdapter.truncate_message(content, max_length)
        return [re.sub(r"\s*\(\d+/\d+\)$", "", c) for c in chunks]

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        text = self.format_message(content)
        if not text:
            return SendResult(success=False, error="BlueBubbles send requires text")
        # Split on paragraph breaks first (double newlines) so each thought
        # becomes its own iMessage bubble, then truncate any that are still
        # too long.
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        chunks: List[str] = []
        for para in (paragraphs or [text]):
            if len(para) <= self.MAX_MESSAGE_LENGTH:
                chunks.append(para)
            else:
                chunks.extend(self.truncate_message(para, max_length=self.MAX_MESSAGE_LENGTH))
        last = SendResult(success=True)
        for chunk in chunks:
            guid = await self._resolve_chat_guid(chat_id)
            if not guid:
                # If the target looks like an address, try creating a new chat
                if self._private_api_enabled and (
                    "@" in chat_id or re.match(r"^\+\d+", chat_id)
                ):
                    return await self._create_chat_for_handle(chat_id, chunk)
                return SendResult(
                    success=False,
                    error=f"BlueBubbles chat not found for target: {chat_id}",
                )
            payload: Dict[str, Any] = {
                "chatGuid": guid,
                "tempGuid": f"temp-{datetime.utcnow().timestamp()}",
                "message": chunk,
            }
            if reply_to and self._private_api_enabled and self._helper_connected:
                payload["method"] = "private-api"
                payload["selectedMessageGuid"] = reply_to
                payload["partIndex"] = 0
            try:
                res = await self._api_post("/api/v1/message/text", payload)
                data = res.get("data") or {}
                msg_id = data.get("guid") or data.get("messageGuid") or "ok"
                last = SendResult(
                    success=True, message_id=str(msg_id), raw_response=res
                )
            except Exception as exc:
                return SendResult(success=False, error=str(exc))
        return last

    # ------------------------------------------------------------------
    # Media sending (outbound)
    # ------------------------------------------------------------------

    async def _send_attachment(
        self,
        chat_id: str,
        file_path: str,
        filename: Optional[str] = None,
        caption: Optional[str] = None,
        is_audio_message: bool = False,
    ) -> SendResult:
        """Send a file attachment via BlueBubbles multipart upload."""
        if not self.client:
            return SendResult(success=False, error="Not connected")
        if not os.path.isfile(file_path):
            return SendResult(success=False, error=f"File not found: {file_path}")

        guid = await self._resolve_chat_guid(chat_id)
        if not guid:
            return SendResult(success=False, error=f"Chat not found: {chat_id}")

        fname = filename or os.path.basename(file_path)
        try:
            with open(file_path, "rb") as f:
                files = {"attachment": (fname, f, "application/octet-stream")}
                data: Dict[str, str] = {
                    "chatGuid": guid,
                    "name": fname,
                    "tempGuid": uuid.uuid4().hex,
                }
                if is_audio_message:
                    data["isAudioMessage"] = "true"
                res = await self.client.post(
                    self._api_url("/api/v1/message/attachment"),
                    files=files,
                    data=data,
                    timeout=120,
                )
                res.raise_for_status()
                result = res.json()

            if caption:
                await self.send(chat_id, caption)

            if result.get("status") == 200:
                rdata = result.get("data") or {}
                msg_id = rdata.get("guid") if isinstance(rdata, dict) else None
                return SendResult(
                    success=True, message_id=msg_id, raw_response=result
                )
            return SendResult(
                success=False,
                error=result.get("message", "Attachment upload failed"),
            )
        except Exception as e:
            return SendResult(success=False, error=str(e))

    async def send_image(
        self,
        chat_id: str,
        image_url: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        try:
            from gateway.platforms.base import cache_image_from_url

            local_path = await cache_image_from_url(image_url)
            return await self._send_attachment(chat_id, local_path, caption=caption)
        except Exception:
            return await super().send_image(chat_id, image_url, caption, reply_to)

    async def send_image_file(
        self,
        chat_id: str,
        image_path: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        **kwargs,
    ) -> SendResult:
        return await self._send_attachment(chat_id, image_path, caption=caption)

    async def send_voice(
        self,
        chat_id: str,
        audio_path: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        **kwargs,
    ) -> SendResult:
        return await self._send_attachment(
            chat_id, audio_path, caption=caption, is_audio_message=True
        )

    async def send_video(
        self,
        chat_id: str,
        video_path: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        **kwargs,
    ) -> SendResult:
        return await self._send_attachment(chat_id, video_path, caption=caption)

    async def send_document(
        self,
        chat_id: str,
        file_path: str,
        caption: Optional[str] = None,
        file_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        **kwargs,
    ) -> SendResult:
        return await self._send_attachment(
            chat_id, file_path, filename=file_name, caption=caption
        )

    async def send_animation(
        self,
        chat_id: str,
        animation_url: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        return await self.send_image(
            chat_id, animation_url, caption, reply_to, metadata
        )

    # ------------------------------------------------------------------
    # Typing indicators
    # ------------------------------------------------------------------

    async def send_typing(self, chat_id: str, metadata=None) -> None:
        if not self._private_api_enabled or not self._helper_connected or not self.client:
            return
        try:
            guid = await self._resolve_chat_guid(chat_id)
            if guid:
                encoded = quote(guid, safe="")
                await self.client.post(
                    self._api_url(f"/api/v1/chat/{encoded}/typing"), timeout=5
                )
        except Exception:
            pass

    async def stop_typing(self, chat_id: str) -> None:
        if not self._private_api_enabled or not self._helper_connected or not self.client:
            return
        try:
            guid = await self._resolve_chat_guid(chat_id)
            if guid:
                encoded = quote(guid, safe="")
                await self.client.delete(
                    self._api_url(f"/api/v1/chat/{encoded}/typing"), timeout=5
                )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Read receipts
    # ------------------------------------------------------------------

    async def mark_read(self, chat_id: str) -> bool:
        if not self._private_api_enabled or not self._helper_connected or not self.client:
            return False
        try:
            guid = await self._resolve_chat_guid(chat_id)
            if guid:
                encoded = quote(guid, safe="")
                await self.client.post(
                    self._api_url(f"/api/v1/chat/{encoded}/read"), timeout=5
                )
                return True
        except Exception:
            pass
        return False

    # ------------------------------------------------------------------
    # Tapback reactions
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Chat info
    # ------------------------------------------------------------------

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        is_group = ";+;" in (chat_id or "")
        info: Dict[str, Any] = {
            "name": chat_id,
            "type": "group" if is_group else "dm",
        }
        try:
            guid = await self._resolve_chat_guid(chat_id)
            if guid:
                encoded = quote(guid, safe="")
                res = await self._api_get(
                    f"/api/v1/chat/{encoded}?with=participants"
                )
                data = (res or {}).get("data", {})
                display_name = (
                    data.get("displayName")
                    or data.get("chatIdentifier")
                    or chat_id
                )
                participants = []
                for p in data.get("participants", []) or []:
                    addr = (p.get("address") or "").strip()
                    if addr:
                        participants.append(addr)
                info["name"] = display_name
                if participants:
                    info["participants"] = participants
        except Exception:
            pass
        return info

    def format_message(self, content: str) -> str:
        return strip_markdown(content)

    # ------------------------------------------------------------------
    # Inbound attachment downloading (from #4588)
    # ------------------------------------------------------------------

    async def _download_attachment(
        self, att_guid: str, att_meta: Dict[str, Any]
    ) -> Optional[str]:
        """Download an attachment from BlueBubbles and cache it locally.

        Returns the local file path on success, None on failure.
        """
        if not self.client:
            return None
        try:
            encoded = quote(att_guid, safe="")
            resp = await self.client.get(
                self._api_url(f"/api/v1/attachment/{encoded}/download"),
                timeout=60,
                follow_redirects=True,
            )
            resp.raise_for_status()
            data = resp.content

            mime = (att_meta.get("mimeType") or "").lower()
            transfer_name = att_meta.get("transferName", "")

            if mime.startswith("image/"):
                ext_map = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/gif": ".gif",
                    "image/webp": ".webp",
                    "image/heic": ".jpg",
                    "image/heif": ".jpg",
                    "image/tiff": ".jpg",
                }
                ext = ext_map.get(mime, ".jpg")
                return cache_image_from_bytes(data, ext)

            if mime.startswith("audio/"):
                ext_map = {
                    "audio/mp3": ".mp3",
                    "audio/mpeg": ".mp3",
                    "audio/ogg": ".ogg",
                    "audio/wav": ".wav",
                    "audio/x-caf": ".mp3",
                    "audio/mp4": ".m4a",
                    "audio/aac": ".m4a",
                }
                ext = ext_map.get(mime, ".mp3")
                return cache_audio_from_bytes(data, ext)

            # Videos, documents, and everything else
            filename = transfer_name or f"file_{uuid.uuid4().hex[:8]}"
            return cache_document_from_bytes(data, filename)

        except Exception as exc:
            logger.warning(
                "[bluebubbles] failed to download attachment %s: %s",
                _redact(att_guid),
                exc,
            )
            return None

    # ------------------------------------------------------------------
    # Webhook handling
    # ------------------------------------------------------------------

    def _extract_payload_record(
        self, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        data = payload.get("data")
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    return item
        if isinstance(payload.get("message"), dict):
            return payload.get("message")
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _value(*candidates: Any) -> Optional[str]:
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return None

    async def _handle_webhook(self, request):
        from aiohttp import web

        token = (
            request.query.get("password")
            or request.query.get("guid")
            or request.headers.get("x-password")
            or request.headers.get("x-guid")
            or request.headers.get("x-bluebubbles-guid")
        )
        if token != self.password:
            return web.json_response({"error": "unauthorized"}, status=401)
        try:
            raw = await request.read()
            body = raw.decode("utf-8", errors="replace")
            try:
                payload = json.loads(body)
            except Exception:
                from urllib.parse import parse_qs

                form = parse_qs(body)
                payload_str = (
                    form.get("payload")
                    or form.get("data")
                    or form.get("message")
                    or [""]
                )[0]
                payload = json.loads(payload_str) if payload_str else {}
        except Exception as exc:
            logger.error("[bluebubbles] webhook parse error: %s", exc)
            return web.json_response({"error": "invalid payload"}, status=400)

        event_type = self._value(payload.get("type"), payload.get("event")) or ""
        # Only process message events; silently acknowledge everything else
        if event_type and event_type not in _MESSAGE_EVENTS:
            return web.Response(text="ok")

        record = self._extract_payload_record(payload) or {}
        is_from_me = bool(
            record.get("isFromMe")
            or record.get("fromMe")
            or record.get("is_from_me")
        )
        if is_from_me:
            return web.Response(text="ok")

        # Skip tapback reactions delivered as messages
        assoc_type = record.get("associatedMessageType")
        if isinstance(assoc_type, int) and assoc_type in {
            **_TAPBACK_ADDED,
            **_TAPBACK_REMOVED,
        }:
            return web.Response(text="ok")

        text = (
            self._value(
                record.get("text"), record.get("message"), record.get("body")
            )
            or ""
        )

        # --- Inbound attachment handling ---
        attachments = record.get("attachments") or []
        media_urls: List[str] = []
        media_types: List[str] = []
        msg_type = MessageType.TEXT

        for att in attachments:
            att_guid = att.get("guid", "")
            if not att_guid:
                continue
            cached = await self._download_attachment(att_guid, att)
            if cached:
                mime = (att.get("mimeType") or "").lower()
                media_urls.append(cached)
                media_types.append(mime)
                if mime.startswith("image/"):
                    msg_type = MessageType.PHOTO
                elif mime.startswith("audio/") or (att.get("uti") or "").endswith(
                    "caf"
                ):
                    msg_type = MessageType.VOICE
                elif mime.startswith("video/"):
                    msg_type = MessageType.VIDEO
                else:
                    msg_type = MessageType.DOCUMENT

        # With multiple attachments, prefer PHOTO if any images present
        if len(media_urls) > 1:
            mime_prefixes = {(m or "").split("/")[0] for m in media_types}
            if "image" in mime_prefixes:
                msg_type = MessageType.PHOTO

        if not text and media_urls:
            text = "(attachment)"
        # --- End attachment handling ---

        chat_guid = self._value(
            record.get("chatGuid"),
            payload.get("chatGuid"),
            record.get("chat_guid"),
            payload.get("chat_guid"),
            payload.get("guid"),
        )
        # Fallback: BlueBubbles v1.9+ webhook payloads omit top-level chatGuid;
        # the chat GUID is nested under data.chats[0].guid instead.
        if not chat_guid:
            _chats = record.get("chats") or []
            if _chats and isinstance(_chats[0], dict):
                chat_guid = _chats[0].get("guid") or _chats[0].get("chatGuid")
        chat_identifier = self._value(
            record.get("chatIdentifier"),
            record.get("identifier"),
            payload.get("chatIdentifier"),
            payload.get("identifier"),
        )
        sender = (
            self._value(
                record.get("handle", {}).get("address")
                if isinstance(record.get("handle"), dict)
                else None,
                record.get("sender"),
                record.get("from"),
                record.get("address"),
            )
            or chat_identifier
            or chat_guid
        )
        if not (chat_guid or chat_identifier) and sender:
            chat_identifier = sender
        if not sender or not (chat_guid or chat_identifier) or not text:
            return web.json_response({"error": "missing message fields"}, status=400)

        session_chat_id = chat_guid or chat_identifier
        is_group = bool(record.get("isGroup")) or (";+;" in (chat_guid or ""))
        source = self.build_source(
            chat_id=session_chat_id,
            chat_name=chat_identifier or sender,
            chat_type="group" if is_group else "dm",
            user_id=sender,
            user_name=sender,
            chat_id_alt=chat_identifier,
        )
        event = MessageEvent(
            text=text,
            message_type=msg_type,
            source=source,
            raw_message=payload,
            message_id=self._value(
                record.get("guid"),
                record.get("messageGuid"),
                record.get("id"),
            ),
            reply_to_message_id=self._value(
                record.get("threadOriginatorGuid"),
                record.get("associatedMessageGuid"),
            ),
            media_urls=media_urls,
            media_types=media_types,
        )
        task = asyncio.create_task(self.handle_message(event))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # Fire-and-forget read receipt
        if self.send_read_receipts and session_chat_id:
            asyncio.create_task(self.mark_read(session_chat_id))

        return web.Response(text="ok")


# ---------------------------------------------------------------------------
# Standalone send (out-of-process cron delivery)
# ---------------------------------------------------------------------------


async def _standalone_send(
    pconfig,
    chat_id: str,
    message: str,
    *,
    thread_id: Optional[str] = None,
    media_files: Optional[list] = None,
    force_document: bool = False,
) -> Dict[str, Any]:
    """Send via the BlueBubbles REST API without a live gateway adapter.

    Used by ``tools/send_message_tool._send_via_adapter`` when the gateway
    runner is not in this process (typical for cron jobs running out-of-process).
    Reads ``BLUEBUBBLES_SERVER_URL`` and ``BLUEBUBBLES_PASSWORD`` from
    ``pconfig`` (set by the gateway config loader from env) and falls back
    to the environment variables.

    ``thread_id``, ``media_files``, and ``force_document`` are accepted for
    signature parity with other standalone senders.  BlueBubbles supports
    media attachments via multipart upload; text-only sends use the
    ``/api/v1/message/text`` endpoint.
    """
    server_url = (
        (getattr(pconfig, "extra", {}) or {}).get("server_url")
        or os.getenv("BLUEBUBBLES_SERVER_URL", "")
    ).rstrip("/")
    password = (getattr(pconfig, "token", None) or os.getenv("BLUEBUBBLES_PASSWORD", "")).strip()
    if not server_url or not password:
        return {
            "error": (
                "BlueBubbles standalone send: BLUEBUBBLES_SERVER_URL and "
                "BLUEBUBBLES_PASSWORD must both be set"
            )
        }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            guid = None
            # Try to resolve chat_id as a chat GUID first, or as a handle
            sep = "&" if "?" in "/api/v1/chat/find-chat" else "?"
            url = f"{server_url}/api/v1/chat/find-chat{sep}password={quote(password, safe='')}"
            res = await client.post(url, json={"target": chat_id})
            if res.status_code == 200:
                data = res.json()
                guid = (data.get("data") or {}).get("guid") if isinstance(data, dict) else None

            if not guid:
                # Fallback: assume chat_id is already a GUID
                guid = chat_id

            payload: Dict[str, Any] = {
                "chatGuid": guid,
                "tempGuid": f"temp-{datetime.utcnow().timestamp()}",
                "message": message,
            }

            sep2 = "&" if "?" in "/api/v1/message/text" else "?"
            send_url = f"{server_url}/api/v1/message/text{sep2}password={quote(password, safe='')}"
            resp = await client.post(send_url, json=payload)
            if resp.status_code not in {200, 201}:
                body = await resp.aread()
                return {
                    "error": (
                        f"BlueBubbles send failed ({resp.status_code}): "
                        f"{body[:400]}"
                    )
                }
            result = resp.json()
            msg_id = (result.get("data") or {}).get("guid") or "ok"

            return {
                "success": True,
                "platform": "bluebubbles",
                "chat_id": chat_id,
                "message_id": str(msg_id),
            }
    except httpx.HTTPError as exc:
        return {"error": f"BlueBubbles send failed (network): {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"BlueBubbles send failed: {exc}"}


# ---------------------------------------------------------------------------
# Interactive setup wizard (replaces hermes_cli/setup.py::_setup_bluebubbles)
# ---------------------------------------------------------------------------


def interactive_setup() -> None:
    """Guide the user through BlueBubbles bot setup.

    Mirrors the Mattermost/Discord ``interactive_setup`` shape: lazy-imports
    CLI helpers so the plugin's import surface stays small, prompts for the
    server URL + password, captures an allowlist, and offers to set a home
    channel.  Replaces the central
    ``hermes_cli/setup.py::_setup_bluebubbles`` function this migration
    removes.
    """
    from hermes_cli.config import get_env_value, save_env_value
    from hermes_cli.cli_output import (
        prompt,
        prompt_yes_no,
        print_header,
        print_info,
        print_success,
        print_warning,
    )

    print_header("BlueBubbles (iMessage)")
    existing = get_env_value("BLUEBUBBLES_SERVER_URL")
    if existing:
        print_info("BlueBubbles: already configured")
        if not prompt_yes_no("Reconfigure BlueBubbles?", False):
            return

    print_info("Connects Hermes to iMessage via BlueBubbles — a free, open-source")
    print_info("macOS server that bridges iMessage to any device.")
    print_info("   Requires a Mac running BlueBubbles Server v1.0.0+")
    print_info("   Download: https://bluebubbles.app/")
    print()
    print_info("In BlueBubbles Server → Settings → API, note your Server URL and Password.")
    print()

    server_url = prompt("BlueBubbles server URL (e.g. http://192.168.1.10:1234)")
    if not server_url:
        print_warning("Server URL is required — skipping BlueBubbles setup")
        return
    save_env_value("BLUEBUBBLES_SERVER_URL", server_url.rstrip("/"))

    password = prompt("BlueBubbles server password", password=True)
    if not password:
        print_warning("Password is required — skipping BlueBubbles setup")
        return
    save_env_value("BLUEBUBBLES_PASSWORD", password)
    print_success("BlueBubbles credentials saved")

    print()
    print_info("🔒 Security: Restrict who can message your bot")
    print_info("   Use iMessage addresses: email (user@icloud.com) or phone (+155****4567)")
    print()
    allowed_users = prompt("Allowed iMessage addresses (comma-separated, leave empty for open access)")
    if allowed_users:
        save_env_value("BLUEBUBBLES_ALLOWED_USERS", allowed_users.replace(" ", ""))
        print_success("BlueBubbles allowlist configured")
    else:
        print_info("⚠️  No allowlist set — anyone who can iMessage you can use the bot!")

    print()
    print_info("📬 Home Channel: phone or email for cron job delivery and notifications.")
    print_info("   You can also set this later with /set-home in your iMessage chat.")
    home_channel = prompt("Home channel address (leave empty to set later)")
    if home_channel:
        save_env_value("BLUEBUBBLES_HOME_CHANNEL", home_channel)

    print()
    print_info("Advanced settings (defaults are fine for most setups):")
    if prompt_yes_no("Configure webhook listener settings?", False):
        webhook_port = prompt("Webhook listener port (default: 8645)")
        if webhook_port:
            try:
                save_env_value("BLUEBUBBLES_WEBHOOK_PORT", str(int(webhook_port)))
                print_success(f"Webhook port set to {webhook_port}")
            except ValueError:
                print_warning("Invalid port number, using default 8645")

    print()
    print_info("Requires the BlueBubbles Private API helper for typing indicators,")
    print_info("read receipts, and tapback reactions. Basic messaging works without it.")
    print_info("   Install: https://docs.bluebubbles.app/helper-bundle/installation")
    print_info("   Open config in your editor:  hermes config edit")


# ---------------------------------------------------------------------------
# YAML → env config bridge (apply_yaml_config_fn, #25443)
# ---------------------------------------------------------------------------


def _apply_yaml_config(yaml_cfg: dict, bluebubbles_cfg: dict) -> dict | None:
    """Translate ``config.yaml`` ``bluebubbles:`` keys into env vars.

    Implements the ``apply_yaml_config_fn`` contract (#24836 / #25443).
    Mirrors the legacy ``bluebubbles_cfg`` block that used to live in
    ``gateway/config.py::load_gateway_config()`` before this migration.

    Env vars take precedence over YAML — every assignment is guarded
    by ``not os.getenv(...)`` so an explicit env var survives a config.yaml
    update.  Returns ``None`` because no extras are seeded into
    ``PlatformConfig.extra`` directly (everything flows through env).
    """
    sv = bluebubbles_cfg.get("server_url")
    if sv is not None and not os.getenv("BLUEBUBBLES_SERVER_URL"):
        os.environ["BLUEBUBBLES_SERVER_URL"] = str(sv).rstrip("/")
    pw = bluebubbles_cfg.get("password")
    if pw is not None and not os.getenv("BLUEBUBBLES_PASSWORD"):
        os.environ["BLUEBUBBLES_PASSWORD"] = str(pw)
    wh = bluebubbles_cfg.get("webhook_port")
    if wh is not None and not os.getenv("BLUEBUBBLES_WEBHOOK_PORT"):
        os.environ["BLUEBUBBLES_WEBHOOK_PORT"] = str(wh)
    au = bluebubbles_cfg.get("allowed_users")
    if au is not None and not os.getenv("BLUEBUBBLES_ALLOWED_USERS"):
        if isinstance(au, list):
            au = ",".join(str(v) for v in au)
        os.environ["BLUEBUBBLES_ALLOWED_USERS"] = str(au)
    hc = bluebubbles_cfg.get("home_channel")
    if hc is not None and not os.getenv("BLUEBUBBLES_HOME_CHANNEL"):
        os.environ["BLUEBUBBLES_HOME_CHANNEL"] = str(hc)
    return None  # all settings flow through env; nothing to merge into extras


# ---------------------------------------------------------------------------
# is_connected probe
# ---------------------------------------------------------------------------


def _is_connected(config) -> bool:
    """BlueBubbles is considered connected when BOTH BLUEBUBBLES_SERVER_URL
    and BLUEBUBBLES_PASSWORD are set.

    Looks up via ``hermes_cli.gateway.get_env_value`` at call time (not via
    the plugin's own bound import) so tests that patch
    ``gateway_mod.get_env_value`` can suppress ambient env vars.  Matches
    what the legacy connected-platforms check did before this migration.
    """
    import hermes_cli.gateway as gateway_mod
    return bool(
        (gateway_mod.get_env_value("BLUEBUBBLES_SERVER_URL") or "").strip()
        and (gateway_mod.get_env_value("BLUEBUBBLES_PASSWORD") or "").strip()
    )


# ---------------------------------------------------------------------------
# Plugin registration entry point
# ---------------------------------------------------------------------------


def _build_adapter(config):
    """Factory wrapper that constructs BlueBubblesAdapter from a PlatformConfig."""
    return BlueBubblesAdapter(config)


def register(ctx) -> None:
    """Plugin entry point — called by the Hermes plugin system."""
    ctx.register_platform(
        name="bluebubbles",
        label="BlueBubbles",
        adapter_factory=_build_adapter,
        check_fn=check_bluebubbles_requirements,
        is_connected=_is_connected,
        required_env=["BLUEBUBBLES_SERVER_URL", "BLUEBUBBLES_PASSWORD"],
        install_hint="pip install aiohttp httpx",
        # Interactive setup wizard — replaces the central
        # hermes_cli/setup.py::_setup_bluebubbles function.
        setup_fn=interactive_setup,
        # YAML→env config bridge — owns the translation of
        # ``config.yaml`` ``bluebubbles:`` keys into ``BLUEBUBBLES_*``
        # env vars that the adapter reads via ``os.getenv()``.  Replaces
        # the hardcoded block that used to live in ``gateway/config.py``.
        # Hook contract: #24836 / #25443.
        apply_yaml_config_fn=_apply_yaml_config,
        # Auth env vars for _is_user_authorized() integration.
        allowed_users_env="BLUEBUBBLES_ALLOWED_USERS",
        allow_all_env="BLUEBUBBLES_ALLOW_ALL_USERS",
        # Cron home-channel delivery.
        cron_deliver_env_var="BLUEBUBBLES_HOME_CHANNEL",
        # Out-of-process cron delivery via BlueBubbles REST API.  Without
        # this hook, ``deliver=bluebubbles`` cron jobs fail with "No live
        # adapter" when cron runs separately from the gateway.  Mirrors
        # the Mattermost / Discord / Teams pattern.
        standalone_sender_fn=_standalone_send,
        # BlueBubbles iMessage length limit.
        max_message_length=MAX_TEXT_LENGTH,
        # Display
        emoji="💬",
        allow_update_command=False,
    )
