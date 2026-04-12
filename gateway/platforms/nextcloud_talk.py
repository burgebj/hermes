"""Nextcloud Talk gateway platform adapter.

Phase 2: User API long-polling. Uses TalkUserClient (Basic Auth + app password)
instead of the old Bot API HMAC webhook approach.

See docs/superpowers/specs/2026-04-08-nextcloud-talk-gateway-design.md
for the full design and rationale.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import (
    BasePlatformAdapter,
    MessageEvent,
    MessageType,
    SendResult,
)

logger = logging.getLogger(__name__)

MEDIA_TEMP_DIR = "/tmp/hermes-media"


def _parse_user_message(
    msg, *, own_user_id: str,
):
    # Parse a Talk User-API message dict into a normalized dict.
    # Returns None for own/system messages.
    if msg.get("actorId") == own_user_id:
        return None
    if msg.get("systemMessage"):
        return None

    text = msg.get("message", "")
    attachment = None

    params = msg.get("messageParameters") or {}
    file_info = params.get("file")
    if isinstance(file_info, dict) and file_info.get("type") == "file":
        attachment = {
            "type": "file",
            "id": str(file_info.get("id", "")),
            "name": str(file_info.get("name", "")),
            "path": str(file_info.get("path", "")),
            "link": str(file_info.get("link", "")),
            "mimetype": str(file_info.get("mimetype", "")),
            "size": str(file_info.get("size", "0")),
        }
        text = text.replace("{file}", "").strip()

    return {
        "text": text,
        "message_id": msg.get("id"),
        "chat_id": msg.get("token", ""),
        "user_id": msg.get("actorId", ""),
        "user_name": msg.get("actorDisplayName", ""),
        "attachment": attachment,
    }


def _classify_attachment(mimetype: str) -> str:
    """Classify a mimetype into a handler category."""
    if mimetype.startswith("image/"):
        return "image"
    if mimetype.startswith("audio/") or mimetype.startswith("video/"):
        return "audio"
    if mimetype.startswith("text/") or mimetype in (
        "application/pdf", "application/json", "application/xml",
    ):
        return "document"
    return "other"


class TalkUserClient:
    """HTTP client for Nextcloud Talk User API (Phase 2).

    Uses Basic Auth (username + app_password) and the standard OCS REST
    endpoints (Phase 2 polling architecture).
    """

    _OCS_HEADERS = {"OCS-APIRequest": "true", "Accept": "application/json"}

    def __init__(self, *, base_url: str, username: str, password: str,
                 poll_timeout: int = 30, http_client=None):
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._auth = (username, password)
        self._poll_timeout = poll_timeout
        if http_client is not None:
            self._http = http_client
        else:
            self._http = httpx.AsyncClient(
                auth=self._auth,
                headers=self._OCS_HEADERS,
                timeout=poll_timeout + 15,
            )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def send_message(self, token: str, message: str, reply_to=None) -> "tuple[bool, Optional[int], Optional[str]]":
        url = f"{self._base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
        data: Dict[str, Any] = {"message": message}
        if reply_to is not None:
            data["replyTo"] = reply_to
        try:
            resp = await self._http.post(url, data=data)
        except Exception as exc:
            return False, None, f"connection error: {exc}"
        if resp.status_code in (200, 201):
            try:
                return True, resp.json()["ocs"]["data"]["id"], None
            except Exception:
                return True, None, None
        return False, None, f"HTTP {resp.status_code}: {resp.text[:200]}"

    async def edit_message(self, token: str, message_id: int, new_text: str) -> "tuple[bool, Optional[str]]":
        url = f"{self._base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}/{message_id}"
        data = {"message": new_text}
        try:
            resp = await self._http.put(url, data=data)
        except Exception as exc:
            return False, f"connection error: {exc}"
        if resp.status_code == 200:
            return True, None
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

    async def get_messages(self, token: str, last_known_id: int, timeout=None) -> "tuple[int, list]":
        url = f"{self._base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
        params = {
            "lookIntoFuture": 1,
            "lastKnownMessageId": last_known_id,
            "timeout": timeout or self._poll_timeout,
            "setReadMarker": 0,
            "includeLastKnown": 0,
        }
        try:
            resp = await self._http.get(url, params=params)
        except Exception:
            raise
        if resp.status_code == 304:
            return 304, []
        if resp.status_code == 200:
            data = resp.json().get("ocs", {}).get("data", [])
            return 200, data if isinstance(data, list) else []
        return resp.status_code, []

    async def join_conversation(self, token: str) -> "tuple[bool, Optional[str]]":
        url = f"{self._base_url}/ocs/v2.php/apps/spreed/api/v1/room/{token}/participants/active"
        try:
            resp = await self._http.post(url)
        except Exception as exc:
            return False, f"connection error: {exc}"
        if resp.status_code in (200, 201):
            return True, None
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

    async def list_conversations(self) -> "tuple[bool, list, Optional[str]]":
        url = f"{self._base_url}/ocs/v2.php/apps/spreed/api/v1/room"
        try:
            resp = await self._http.get(url)
        except Exception as exc:
            return False, [], f"connection error: {exc}"
        if resp.status_code == 200:
            data = resp.json().get("ocs", {}).get("data", [])
            return True, data if isinstance(data, list) else [], None
        return False, [], f"HTTP {resp.status_code}: {resp.text[:200]}"

    async def get_latest_message_id(self, token: str) -> int:
        url = f"{self._base_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
        params = {
            "lookIntoFuture": 0,
            "limit": 1,
            "setReadMarker": 0,
            "includeLastKnown": 1,
        }
        try:
            resp = await self._http.get(url, params=params)
        except Exception:
            return 0
        if resp.status_code == 200:
            data = resp.json().get("ocs", {}).get("data", [])
            if data and isinstance(data, list):
                return max(m.get("id", 0) for m in data)
        return 0

    async def upload_file(self, remote_path: str, local_path: str) -> "tuple[bool, Optional[str]]":
        url = f"{self._base_url}/remote.php/dav/files/{self._username}/{remote_path.lstrip('/')}"
        try:
            with open(local_path, "rb") as f:
                data = f.read()
            resp = await self._http.put(url, content=data)
            if resp.status_code in (200, 201, 204):
                return True, None
            # Auto-create parent directory on 404 (folder doesn't exist yet)
            if resp.status_code in (404, 409):
                parent = remote_path.rsplit("/", 1)[0] if "/" in remote_path else ""
                if parent:
                    mkcol_url = f"{self._base_url}/remote.php/dav/files/{self._username}/{parent}/"
                    await self._http.request("MKCOL", mkcol_url)
                    # Retry upload
                    resp2 = await self._http.put(url, content=data)
                    if resp2.status_code in (200, 201, 204):
                        return True, None
                    return False, f"HTTP {resp2.status_code} (after MKCOL)"
            return False, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, f"upload error: {exc}"

    async def share_file_to_chat(self, token: str, file_path: str, talk_meta: dict = None) -> "tuple[bool, Optional[int], Optional[str]]":
        url = f"{self._base_url}/ocs/v2.php/apps/files_sharing/api/v1/shares"
        data = {"shareType": "10", "shareWith": token, "path": file_path}
        if talk_meta:
            import json as _json
            data["talkMetaData"] = _json.dumps(talk_meta)
        try:
            resp = await self._http.post(url, data=data)
            if resp.status_code == 200:
                return True, resp.json()["ocs"]["data"]["id"], None
            return False, None, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as exc:
            return False, None, f"share error: {exc}"

    async def download_file(self, remote_path: str, local_path: str) -> "tuple[bool, Optional[str], Optional[str]]":
        url = f"{self._base_url}/remote.php/dav/files/{self._username}/{remote_path.lstrip('/')}"
        try:
            resp = await self._http.get(url)
            if resp.status_code == 200:
                import os as _os
                _os.makedirs(_os.path.dirname(local_path) or ".", exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                return True, local_path, None
            return False, None, f"HTTP {resp.status_code}"
        except Exception as exc:
            return False, None, f"download error: {exc}"


def check_nextcloud_talk_requirements() -> bool:
    """Check if this platform's dependencies are available."""
    try:
        import httpx  # noqa: F401
        return True
    except ImportError:
        return False


class PlaceholderSTT:
    """STT placeholder when no provider is configured."""
    async def transcribe(self, audio_path: str):
        return None


class LlamaCppSTT:
    """STT via local llama.cpp router with Whisper-compatible endpoint."""
    def __init__(self, base_url: str, api_key: str = ""):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    async def transcribe(self, audio_path: str) -> Optional[str]:
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
                with open(audio_path, "rb") as f:
                    resp = await client.post(
                        f"{self._base_url}/v1/audio/transcriptions",
                        files={"file": (os.path.basename(audio_path), f)},
                        data={"model": "whisper"},
                    )
                if resp.status_code == 200:
                    return resp.json().get("text", "").strip() or None
                logger.warning("STT HTTP %d: %s", resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning("STT transcription failed: %s", exc)
        return None


class NextcloudTalkPlatform(BasePlatformAdapter):
    """Nextcloud Talk User API adapter (Phase 2: long-poll)."""

    # Talk's hard limit per message is 32KB, but Hermes' convention is
    # to split at ~4KB so messages stay readable in mobile clients.
    MAX_MESSAGE_LENGTH = 4096

    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform.NEXTCLOUD_TALK)
        extra = getattr(config, "extra", {}) or {}

        self._nextcloud_url = str(extra.get("nextcloud_url", "")).rstrip("/")
        if not self._nextcloud_url:
            raise ValueError(
                "NextcloudTalk: 'nextcloud_url' is required in config.extra"
            )

        self._username = str(extra.get("username", "")).strip()
        if not self._username:
            raise ValueError(
                "NextcloudTalk: 'username' is required in config.extra"
            )

        app_password_env = str(extra.get("app_password_env", "NC_TALK_APP_PASSWORD"))
        self._password = (os.environ.get(app_password_env) or "").strip()
        if not self._password:
            raise ValueError(
                f"NextcloudTalk: env var {app_password_env} is missing or empty. "
                f"Set it before starting the gateway."
            )

        raw_conversations = extra.get("conversations") or []
        if not raw_conversations:
            raise ValueError(
                "NextcloudTalk: 'conversations' list is required and must not be empty"
            )
        self._conversations: List[Dict[str, Any]] = [
            dict(c) for c in raw_conversations
        ]

        self._edit_ack_into_response = bool(extra.get("edit_ack_into_response", True))
        self._show_status_updates = bool(extra.get("show_status_updates", True))
        self._poll_timeout = int(extra.get("poll_timeout", 30))

        # Channel alias map: user-friendly name -> conversation token.
        # Built from two sources:
        # 1. conversations[].alias  (e.g. {"token": "abc123", "alias": "alice"})
        # 2. channel_aliases dict   (manual overrides in config)
        self._channel_aliases: Dict[str, str] = {}
        for conv in self._conversations:
            alias = conv.get("alias", "").strip()
            token = conv.get("token", "").strip()
            if alias and token:
                self._channel_aliases[alias] = token

        raw_aliases = extra.get("channel_aliases") or {}
        if isinstance(raw_aliases, dict):
            for k, v in raw_aliases.items():
                k = str(k).strip()
                v = str(v).strip()
                if k and v:
                    self._channel_aliases[k] = v

        # STT provider (pluggable)
        stt_config = extra.get("stt") or {}
        stt_provider = stt_config.get("provider", "")
        if stt_provider == "llamacpp" and stt_config.get("base_url"):
            self._stt = LlamaCppSTT(
                base_url=stt_config["base_url"],
                api_key=stt_config.get("api_key", ""),
            )
        else:
            self._stt = PlaceholderSTT()

        # Learned display names from polling (token -> display_name)
        self._chat_name_cache: Dict[str, str] = {}

        # Runtime state (populated in connect())
        self._client: Optional[TalkUserClient] = None
        self._poll_tasks: List[asyncio.Task] = []
        self._shutdown: bool = False
        self._pending_ack: Optional[Dict[str, Any]] = None

    def _classify_chat(self, chat_id: str) -> str:
        """Return 'group' if the chat is a known conversation token, else 'dm'."""
        configured_tokens = {c["token"] for c in self._conversations}
        if chat_id in configured_tokens:
            return "group"
        return "dm"

    def _is_chat_allowed(self, chat_id: str) -> bool:
        """Decide whether to process messages from this chat."""
        configured_tokens = {c["token"] for c in self._conversations}
        return chat_id in configured_tokens

    async def _download_attachment(self, attachment):
        """Download incoming attachment to temp file. Returns local path or None."""
        import uuid as _uuid
        name = attachment.get("name", "attachment")
        unique = _uuid.uuid4().hex[:8]
        local_path = os.path.join(MEDIA_TEMP_DIR, f"{unique}-{name}")
        os.makedirs(MEDIA_TEMP_DIR, exist_ok=True)

        # Try WebDAV download (file in sender's Talk folder, hermes may have access)
        # path from NC already includes Talk/ prefix (e.g. "Talk/Vineyard.jpg")
        remote_path = attachment.get("path", name)
        ok, path, err = await self._client.download_file(remote_path, local_path)
        if ok:
            return path

        # Fallback: share link as authenticated user
        link = attachment.get("link", "")
        if link:
            share_token = link.rstrip("/").split("/")[-1]
            share_url = f"index.php/s/{share_token}/download"
            ok2, path2, err2 = await self._client.download_file(share_url, local_path)
            if ok2:
                return path2

        logger.warning("talk: could not download %s: %s", name, err)
        return None

    _LOCAL_COMMANDS = {"/new", "/reset", "/help"}

    async def _handle_command(
        self, text: str, chat_id: str,
    ) -> Optional[str]:
        """Handle adapter-local commands. Returns reply text or None
        to forward to the runtime.
        """
        cmd = text.strip().split(maxsplit=1)[0].lower()
        if cmd not in self._LOCAL_COMMANDS:
            return None

        if cmd in ("/new", "/reset"):
            from gateway.session import build_session_key
            source = self.build_source(
                chat_id=chat_id,
                chat_type=self._classify_chat(chat_id),
            )
            session_key = build_session_key(source)
            try:
                self._session_store.reset_session(session_key)
            except Exception as exc:
                logger.exception("talk: reset session failed")
                return f"❌ Konnte Session nicht zurücksetzen: {exc}"
            return "✓ Session zurückgesetzt."

        if cmd == "/help":
            return (
                "**Hermes auf Nextcloud Talk**\n\n"
                "Befehle:\n"
                "- `/new` oder `/reset` — Session zurücksetzen\n"
                "- `/help` — diese Hilfe\n\n"
                "Alles andere wird von Hermes verarbeitet. "
                "Für Hermes-interne Befehle wie `/model`, `/status` "
                "usw. einfach eingeben."
            )

        return None

    def _record_chat_name(self, chat_id: str, name: str) -> None:
        """Cache the human-readable chat name learned from polling."""
        if name:
            self._chat_name_cache[chat_id] = name

    def _resolve_chat_identifier(self, name: Optional[str]) -> Optional[str]:
        """Resolve a user-supplied name to a conversation token.

        Resolution order:
        1. Exact config alias match (case-insensitive) -> configured token
        2. Exact learned display name match (case-insensitive)
        3. If the input looks like a raw NC Talk conversation token
           (alphanumeric, with optional `-` and `_`), return it unchanged
        4. Otherwise None
        """
        if not name:
            return None
        name_stripped = name.strip()
        if not name_stripped:
            return None

        # 1. Config alias (case-insensitive)
        lowered = name_stripped.lower()
        for alias, token in self._channel_aliases.items():
            if alias.lower() == lowered:
                return token

        # 2. Learned display name from polling
        for chat_id, display_name in self._chat_name_cache.items():
            if display_name and display_name.strip().lower() == lowered:
                return chat_id

        # 3. Raw-token fallback: NC Talk tokens are alphanumeric, some
        #    use `-` or `_`. Tokens don't contain whitespace.
        if all(ch.isalnum() or ch in ("-", "_") for ch in name_stripped):
            return name_stripped

        return None

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        return {
            "chat_id": chat_id,
            "name": self._chat_name_cache.get(chat_id, chat_id),
            "type": self._classify_chat(chat_id),
        }

    async def connect(self) -> bool:
        if self._poll_tasks:
            return True
        if self._client is None:
            self._client = TalkUserClient(
                base_url=self._nextcloud_url,
                username=self._username,
                password=self._password,
                poll_timeout=self._poll_timeout,
            )
        self._shutdown = False

        ok, rooms, err = await self._client.list_conversations()
        if ok:
            room_tokens = {r.get("token") for r in rooms}
            for conv in self._conversations:
                token = conv["token"]
                if token not in room_tokens:
                    logger.warning("talk: not a member of %s", token)
                await self._client.join_conversation(token)
        else:
            logger.warning("talk: could not list conversations: %s", err)

        for conv in self._conversations:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            task = loop.create_task(
                self._poll_loop(conv["token"])
            )
            self._poll_tasks.append(task)

        logger.info("NextcloudTalk: polling %d conversation(s) as %s",
                    len(self._conversations), self._username)
        return True

    async def disconnect(self) -> None:
        self._shutdown = True
        for task in self._poll_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._poll_tasks.clear()
        if self._client:
            await self._client.close()
            self._client = None

    async def _poll_loop(self, token: str) -> None:
        last_known_id = await self._client.get_latest_message_id(token)
        logger.info("talk: poll started for %s (from ID %d)", token, last_known_id)
        while not self._shutdown:
            try:
                status, messages = await self._client.get_messages(
                    token, last_known_id, timeout=self._poll_timeout,
                )
                if status == 304:
                    continue
                if status == 401:
                    logger.error("talk: auth failed, stopping poll for %s", token)
                    break
                for msg in messages:
                    msg_id = msg.get("id", 0)
                    if msg_id > last_known_id:
                        last_known_id = msg_id
                    await self._on_poll_message(msg, token)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("talk: poll error, retrying in 5s")
                await asyncio.sleep(5)

    async def _on_poll_message(self, msg: Dict[str, Any], token: str) -> None:
        parsed = _parse_user_message(msg, own_user_id=self._username)
        if parsed is None:
            return

        chat_id = parsed["chat_id"] or token
        text = parsed["text"]

        # Check conversation is configured
        if not self._is_chat_allowed(chat_id):
            return

        self._record_chat_name(chat_id, parsed.get("user_name", ""))

        # Normalize ! prefix to / (Talk intercepts / commands, so users use !)
        if text.startswith("!"):
            text = "/" + text[1:]

        # Commands
        if text.startswith("/"):
            reply = await self._handle_command(text, chat_id)
            if reply is not None:
                await self.send(chat_id, reply)
                return

        # Ack
        ack_msg_id = None
        if self._show_status_updates:
            try:
                ok, mid, _ = await self._client.send_message(chat_id, "\u23f3 denke nach...")
                if ok:
                    ack_msg_id = mid
            except Exception:
                pass

        if ack_msg_id is not None:
            self._pending_ack = {"chat_id": chat_id, "message_id": ack_msg_id}

        # Attachment handling
        media_urls = []
        event_type = MessageType.TEXT
        attachment = parsed.get("attachment")
        if attachment:
            local_path = await self._download_attachment(attachment)
            if local_path:
                media_urls.append(local_path)
                category = _classify_attachment(attachment.get("mimetype", ""))
                if category == "image":
                    event_type = MessageType.PHOTO
                elif category == "audio":
                    transcribed = await self._stt.transcribe(local_path)
                    if transcribed:
                        text = transcribed
                        event_type = MessageType.TEXT
                    else:
                        if not text:
                            text = (
                                f"Voice memo received ({attachment['name']}, "
                                f"{attachment['size']} bytes) but speech-to-text "
                                f"is not available."
                            )
                        event_type = MessageType.VOICE
                elif category == "document":
                    event_type = MessageType.DOCUMENT
                else:
                    if not text:
                        text = f"User shared {attachment['name']} ({attachment['mimetype']})"
                    event_type = MessageType.DOCUMENT
            else:
                if not text:
                    text = f"[Attachment {attachment['name']} could not be downloaded]"

        # Build event
        source = self.build_source(
            chat_id=chat_id,
            chat_type=self._classify_chat(chat_id),
            user_id=parsed["user_id"],
            user_name=parsed.get("user_name", ""),
        )
        event = MessageEvent(
            text=text or "",
            message_type=event_type,
            source=source,
            raw_message=msg,
            message_id=str(parsed["message_id"]) if parsed["message_id"] else None,
            media_urls=media_urls,
        )

        try:
            await self.handle_message(event)
        except Exception:
            logger.exception("talk: handle_message raised")

    async def _upload_and_share(self, chat_id, local_path, caption=None, talk_meta=None):
        """Upload file to WebDAV and share in conversation."""
        # Strip markdown artifacts (e.g. **path** from bold-wrapped MEDIA tags)
        local_path = local_path.strip()
        while local_path and local_path[0] in "*_`\'\"":
            local_path = local_path[1:]
        while local_path and local_path[-1] in "*_`\'\"":
            local_path = local_path[:-1]

        if self._client is None:
            return SendResult(success=False, error="Not connected")
        import uuid as _uuid
        filename = os.path.basename(local_path)
        remote_path = f"Talk-Uploads/{_uuid.uuid4().hex[:8]}-{filename}"
        ok, err = await self._client.upload_file(remote_path, local_path)
        if not ok:
            return SendResult(success=False, error=f"Upload: {err}")
        ok, share_id, err = await self._client.share_file_to_chat(
            chat_id, f"/{remote_path}", talk_meta=talk_meta,
        )
        if not ok:
            return SendResult(success=False, error=f"Share: {err}")
        if caption:
            await self._client.send_message(chat_id, caption)
        return SendResult(success=True, message_id=str(share_id) if share_id else None)

    async def send_voice(self, chat_id, audio_path, caption=None, reply_to=None, **kwargs):
        # Talk voice-message type ONLY works with audio/mpeg or audio/wav.
        # OGG/Opus is explicitly rejected by Talk's fixMimeTypeOfVoiceMessage().
        # The TTS tool auto-converts MP3→OGG for Telegram compat, but the
        # original MP3 is still on disk. Prefer the MP3 if available.
        if audio_path.lower().endswith(".ogg"):
            mp3_path = audio_path.rsplit(".", 1)[0] + ".mp3"
            if os.path.exists(mp3_path):
                audio_path = mp3_path
                logger.info("talk: using MP3 instead of OGG for voice-message compat")
        return await self._upload_and_share(
            chat_id, audio_path, caption,
            talk_meta={"messageType": "voice-message"},
        )

    async def send_image(self, chat_id, image_url, caption=None, reply_to=None, metadata=None):
        return await self._upload_and_share(chat_id, image_url, caption)

    async def send_document(self, chat_id, file_path, caption=None, file_name=None, reply_to=None, **kwargs):
        return await self._upload_and_share(chat_id, file_path, caption)

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        if self._client is None:
            return SendResult(
                success=False,
                error="NextcloudTalk not connected",
                retryable=False,
            )

        # Ack-edit: if there's a pending ack for this chat, edit it instead of sending new
        ack = self._pending_ack
        if ack and ack["chat_id"] == chat_id and self._edit_ack_into_response:
            self._pending_ack = None
            ok, err = await self._client.edit_message(
                chat_id, ack["message_id"], content,
            )
            if ok:
                return SendResult(success=True, message_id=str(ack["message_id"]))
            logger.warning("talk: ack edit failed (%s), sending new message", err)

        chunks = self.truncate_message(content, self.MAX_MESSAGE_LENGTH)
        last_id = None
        for i, chunk in enumerate(chunks):
            ok, msg_id, err = await self._client.send_message(
                chat_id, chunk,
                reply_to=reply_to if i == 0 else None,
            )
            if not ok:
                retryable = bool(err and ("HTTP 5" in err or "connection" in err.lower()))
                return SendResult(
                    success=False,
                    error=err,
                    retryable=retryable,
                )
            last_id = msg_id
        return SendResult(success=True, message_id=str(last_id) if last_id is not None else None)

    async def edit_message(
        self,
        chat_id: str,
        message_id: str,
        content: str,
    ) -> SendResult:
        if self._client is None:
            return SendResult(
                success=False,
                error="NextcloudTalk not connected",
                retryable=False,
            )
        try:
            mid_int = int(message_id)
        except (ValueError, TypeError):
            return SendResult(success=False, error=f"invalid message_id: {message_id}", retryable=False)

        ok, err = await self._client.edit_message(chat_id, mid_int, content)
        if ok:
            return SendResult(success=True, message_id=message_id)
        retryable = bool(err and ("HTTP 5" in err or "connection" in err.lower()))
        return SendResult(success=False, error=err, retryable=retryable)

    async def send_typing(self, chat_id: str, metadata=None) -> None:
        """No-op — ack message in _on_poll_message provides equivalent feedback."""
        return

    async def stop_typing(self, chat_id: str) -> None:
        return
