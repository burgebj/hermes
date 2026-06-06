"""Telemus platform adapter for Hermes Agent.

This adapter talks to the Telemus / VR AI Chat desktop headless devtools
protocol: newline-delimited JSON requests like
``{"id": 1, "method": "Devtools.getInfo"}`` and responses shaped as
``{"id": 1, "ok": true, "result": {...}}``.

The initial implementation intentionally stays conservative: it uses the
existing ``AI.sendMessage`` and ``AI.getTranscript`` methods so Hermes can act
as a first-class gateway client before Telemus grows a push/event channel API.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import BasePlatformAdapter, MessageEvent, MessageType, SendResult

logger = logging.getLogger(__name__)


class TelemusProtocolError(RuntimeError):
    """Raised when the devtools endpoint returns malformed or failed responses."""


class TelemusJsonlClient:
    """Small async JSONL-RPC client for Telemus desktop devtools.

    The Telemus endpoint serves one JSON object per line. Requests are
    serialized under a write lock and responses are correlated by ``id``.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765, timeout: float = 10.0):
        self.host = host
        self.port = int(port)
        self.timeout = float(timeout)
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._ids = itertools.count(1)
        self._lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> None:
        if self.connected:
            return
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port),
            timeout=self.timeout,
        )

    async def close(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None
        if writer and not writer.is_closing():
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def request(self, method: str, **params: Any) -> Dict[str, Any]:
        import json

        await self.connect()
        assert self._reader is not None and self._writer is not None
        req_id = next(self._ids)
        payload: Dict[str, Any] = {"id": req_id, "method": method}
        payload.update(params)
        raw = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")

        async with self._lock:
            self._writer.write(raw)
            await asyncio.wait_for(self._writer.drain(), timeout=self.timeout)
            while True:
                line = await asyncio.wait_for(self._reader.readline(), timeout=self.timeout)
                if not line:
                    raise TelemusProtocolError("devtools connection closed")
                try:
                    response = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    raise TelemusProtocolError(f"invalid JSON response: {exc}") from exc
                if response.get("id") != req_id:
                    logger.debug("Telemus: ignoring response for unexpected id %r", response.get("id"))
                    continue
                if not response.get("ok", False):
                    raise TelemusProtocolError(str(response.get("error") or "devtools request failed"))
                result = response.get("result")
                return result if isinstance(result, dict) else {"value": result}

    async def get_info(self) -> Dict[str, Any]:
        return await self.request("Devtools.getInfo")

    async def get_state(self) -> Dict[str, Any]:
        return await self.request("App.getState")

    async def send_message(self, text: str, agent_index: int = -1) -> Dict[str, Any]:
        return await self.request("AI.sendMessage", text=text, agentIndex=int(agent_index))

    async def send_channel_message(
        self, text: str, agent_index: int = -1, correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"text": text, "agentIndex": int(agent_index)}
        if correlation_id:
            params["correlationId"] = correlation_id
        return await self.request("Channels.sendMessage", **params)

    async def get_transcript(self, agent_index: int = -1) -> Dict[str, Any]:
        return await self.request("AI.getTranscript", agentIndex=int(agent_index))

    async def channel_status(self) -> Dict[str, Any]:
        return await self.request("Channels.status")

    async def poll_events(self, after_event_id: int = 0, limit: int = 50) -> Dict[str, Any]:
        return await self.request("Channels.pollEvents", afterEventId=int(after_event_id), limit=int(limit))

    async def ack_events(self, through_event_id: int) -> Dict[str, Any]:
        return await self.request("Channels.ack", throughEventId=int(through_event_id))

    async def list_agents(self) -> Dict[str, Any]:
        return await self.request("Agents.list")


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_agent_index(chat_id: str, default: int = -1) -> int:
    raw = str(chat_id or "").strip()
    if raw.startswith("agent:"):
        raw = raw.split(":", 1)[1]
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


class TelemusAdapter(BasePlatformAdapter):
    """Hermes gateway platform backed by Telemus devtools JSONL."""

    def __init__(self, config: PlatformConfig, **kwargs: Any):
        super().__init__(config=config, platform=Platform("telemus"))
        extra = getattr(config, "extra", {}) or {}

        self.host = os.getenv("TELEMUS_DEVTOOLS_HOST") or extra.get("host", "127.0.0.1")
        self.port = int(os.getenv("TELEMUS_DEVTOOLS_PORT") or extra.get("port", 8765))
        self.default_agent_index = int(os.getenv("TELEMUS_AGENT_INDEX") or extra.get("agent_index", -1))
        self.poll_interval = float(os.getenv("TELEMUS_POLL_INTERVAL_SECONDS") or extra.get("poll_interval_seconds", 1.0))
        self.poll_transcripts = _as_bool(os.getenv("TELEMUS_POLL_TRANSCRIPTS"), extra.get("poll_transcripts", True))
        self.prefer_channels = _as_bool(os.getenv("TELEMUS_PREFER_CHANNELS"), extra.get("prefer_channels", True))
        self.home_channel = os.getenv("TELEMUS_HOME_CHANNEL") or extra.get("home_channel", f"agent:{self.default_agent_index}")
        inbound = os.getenv("TELEMUS_INBOUND_SPEAKERS") or extra.get("inbound_speakers", "User,Human,You")
        if isinstance(inbound, str):
            inbound = [part.strip() for part in inbound.split(",")]
        self.inbound_speakers = {str(name).strip().lower() for name in inbound if str(name).strip()}
        self.client = TelemusJsonlClient(self.host, self.port, timeout=float(extra.get("timeout", 10.0)))
        self._poll_task: Optional[asyncio.Task] = None
        self._seen_transcript_keys: set[str] = set()
        self._last_event_id = 0
        self._supports_channels = False

    @property
    def name(self) -> str:
        return "Telemus"

    async def connect(self) -> bool:
        if not self._acquire_platform_lock("telemus", f"{self.host}:{self.port}", "Telemus devtools endpoint"):
            return False
        try:
            info = await self.client.get_info()
        except Exception as exc:
            self._release_platform_lock()
            logger.error("Telemus: failed to connect to %s:%s — %s", self.host, self.port, exc)
            self._set_fatal_error("connect_failed", str(exc), retryable=True)
            return False
        logger.info("Telemus: connected to %s:%s (%s)", self.host, self.port, info.get("protocol", "jsonl"))
        commands = info.get("commands") or []
        self._supports_channels = self.prefer_channels and "Channels.pollEvents" in commands
        if self._supports_channels:
            try:
                status = await self.client.channel_status()
                self._last_event_id = int(status.get("lastEventId") or 0)
            except Exception as exc:
                logger.debug("Telemus: channel status probe failed, falling back to transcripts: %s", exc)
                self._supports_channels = False
        self._mark_connected()
        if self._supports_channels or self.poll_transcripts:
            self._poll_task = asyncio.create_task(self._poll_loop())
        return True

    async def disconnect(self) -> None:
        self._mark_disconnected()
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        self._poll_task = None
        await self.client.close()
        self._release_platform_lock()

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        metadata = metadata or {}
        agent_index = int(metadata.get("agent_index", _parse_agent_index(chat_id, self.default_agent_index)))
        try:
            if self._supports_channels:
                correlation_id = str(metadata.get("correlation_id") or uuid.uuid4())
                result = await self.client.send_channel_message(
                    content, agent_index=agent_index, correlation_id=correlation_id
                )
            else:
                result = await self.client.send_message(content, agent_index=agent_index)
        except Exception as exc:
            logger.warning("Telemus: send failed: %s", exc)
            return SendResult(success=False, error=str(exc), retryable=True)
        message_id = f"telemus-{agent_index}-{int(time.time() * 1000)}"
        return SendResult(success=True, message_id=message_id, raw_response=result)

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        agent_index = _parse_agent_index(chat_id, self.default_agent_index)
        return {"name": f"Telemus agent {agent_index}", "type": "dm", "agent_index": agent_index}

    async def _poll_loop(self) -> None:
        while self.is_connected:
            try:
                if self._supports_channels:
                    await self._poll_events_once()
                else:
                    await self._poll_transcript_once(self.default_agent_index)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("Telemus: poll failed: %s", exc)
            await asyncio.sleep(max(0.2, self.poll_interval))

    async def _poll_events_once(self) -> None:
        data = await self.client.poll_events(after_event_id=self._last_event_id, limit=50)
        events = data.get("events") or []
        if not isinstance(events, list):
            return
        max_event_id = self._last_event_id
        for item in events:
            if not isinstance(item, dict):
                continue
            event_id = int(item.get("eventId") or item.get("id") or 0)
            if event_id <= self._last_event_id:
                continue
            text = str(item.get("text") or "").strip()
            role = str(item.get("role") or "").strip().lower()
            speaker = str(item.get("speaker") or "").strip()
            agent_index = int(item.get("agentIndex", self.default_agent_index))
            if event_id > max_event_id:
                max_event_id = event_id
            if not text or role != "user":
                continue
            source = self.build_source(
                chat_id=f"agent:{agent_index}",
                chat_name=f"Telemus agent {agent_index}",
                chat_type="dm",
                user_id=speaker or "telemus-user",
                user_name=speaker or "Telemus User",
                message_id=str(event_id),
            )
            event = MessageEvent(
                text=text,
                message_type=MessageType.TEXT,
                source=source,
                raw_message=item,
                message_id=str(event_id),
            )
            await self.handle_message(event)
        if max_event_id > self._last_event_id:
            self._last_event_id = max_event_id
            try:
                await self.client.ack_events(max_event_id)
            except Exception as exc:
                logger.debug("Telemus: event ack failed: %s", exc)

    async def _poll_transcript_once(self, agent_index: int) -> None:
        data = await self.client.get_transcript(agent_index=agent_index)
        entries = data.get("entries") or []
        if not isinstance(entries, list):
            return
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            text = str(entry.get("text") or "").strip()
            speaker = str(entry.get("speaker") or "").strip()
            idx = entry.get("index", len(self._seen_transcript_keys))
            if not text or speaker.lower() not in self.inbound_speakers:
                continue
            key = f"{agent_index}:{idx}:{speaker}:{text}"
            if key in self._seen_transcript_keys:
                continue
            self._seen_transcript_keys.add(key)
            source = self.build_source(
                chat_id=f"agent:{agent_index}",
                chat_name=f"Telemus agent {agent_index}",
                chat_type="dm",
                user_id=speaker or "telemus-user",
                user_name=speaker or "Telemus User",
                message_id=key,
            )
            event = MessageEvent(
                text=text,
                message_type=MessageType.TEXT,
                source=source,
                raw_message=entry,
                message_id=key,
            )
            await self.handle_message(event)


def check_requirements() -> bool:
    return True


def validate_config(config: PlatformConfig) -> list[str]:
    extra = getattr(config, "extra", {}) or {}
    errors: list[str] = []
    port = os.getenv("TELEMUS_DEVTOOLS_PORT") or extra.get("port", 8765)
    try:
        int(port)
    except (TypeError, ValueError):
        errors.append("TELEMUS_DEVTOOLS_PORT / extra.port must be an integer")
    return errors


def interactive_setup() -> None:
    from hermes_cli.config import get_env_value, save_env_value
    from hermes_cli.ui import print_info, print_success, prompt

    host = prompt("Telemus devtools host", default=get_env_value("TELEMUS_DEVTOOLS_HOST") or "127.0.0.1")
    port = prompt("Telemus devtools port", default=get_env_value("TELEMUS_DEVTOOLS_PORT") or "8765")
    agent_index = prompt("Default agent index", default=get_env_value("TELEMUS_AGENT_INDEX") or "-1")
    save_env_value("TELEMUS_DEVTOOLS_HOST", host.strip() or "127.0.0.1")
    save_env_value("TELEMUS_DEVTOOLS_PORT", port.strip() or "8765")
    save_env_value("TELEMUS_AGENT_INDEX", agent_index.strip() or "-1")
    save_env_value("TELEMUS_HOME_CHANNEL", f"agent:{agent_index.strip() or '-1'}")
    print_success("Telemus configuration saved to ~/.hermes/.env")
    print_info("Start Telemus headless, then restart the gateway: hermes gateway restart")


def is_connected(config: PlatformConfig) -> bool:
    extra = getattr(config, "extra", {}) or {}
    return bool(os.getenv("TELEMUS_DEVTOOLS_PORT") or extra.get("port") or extra.get("host"))


def _env_enablement() -> dict | None:
    host = os.getenv("TELEMUS_DEVTOOLS_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = os.getenv("TELEMUS_DEVTOOLS_PORT", "").strip()
    if not port:
        return None
    try:
        parsed_port = int(port)
    except ValueError:
        return None
    agent_index = int(os.getenv("TELEMUS_AGENT_INDEX", "-1") or -1)
    home = os.getenv("TELEMUS_HOME_CHANNEL") or f"agent:{agent_index}"
    return {
        "host": host,
        "port": parsed_port,
        "agent_index": agent_index,
        "home_channel": {"chat_id": home, "name": "Telemus"},
    }


def register(ctx: Any) -> None:
    ctx.register_platform(
        name="telemus",
        label="Telemus",
        adapter_factory=lambda cfg: TelemusAdapter(cfg),
        check_fn=check_requirements,
        validate_config=validate_config,
        is_connected=is_connected,
        required_env=[],
        install_hint="Start Telemus headless with: vrai_headless --socket 8765",
        setup_fn=interactive_setup,
        env_enablement_fn=_env_enablement,
        cron_deliver_env_var="TELEMUS_HOME_CHANNEL",
        max_message_length=4096,
        emoji="🧠",
        pii_safe=False,
        allow_update_command=False,
        platform_hint=(
            "You are connected through Telemus / VR AI Chat. Keep responses concise; "
            "messages are routed into a spatial/headless agent session."
        ),
    )
