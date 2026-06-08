"""IRC (Internet Relay Chat) gateway adapter."""
from __future__ import annotations
import asyncio, logging, os, re, time
from collections import deque
from typing import Any, Dict, List, Optional, Set
from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import BasePlatformAdapter, MessageEvent, MessageType, SendResult

logger = logging.getLogger(__name__)
MAX_MESSAGE_LENGTH = 400
FLOOD_MAX_MESSAGES = 3
FLOOD_WINDOW_SECONDS = 4

def _parse_comma_list(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]

def _normalize_nick(nick: str) -> str:
    return nick.lower()

def _parse_user_mask(mask: str) -> tuple:
    if "!" in mask and "@" in mask:
        parts = mask.split("!")
        nick = parts[0]
        user_host = parts[1] if len(parts) > 1 else ""
        if "@" in user_host:
            user, host = user_host.split("@", 1)
        else:
            user, host = user_host, ""
        return nick, user, host
    return mask, "", ""

def _mask_matches(pattern: str, target_mask: str) -> bool:
    target_nick, _, _ = _parse_user_mask(target_mask)
    if "*" in pattern:
        regex_pattern = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
        return bool(re.match(regex_pattern, target_mask, re.IGNORECASE))
    elif "!" in pattern and "@" in pattern:
        pn, pu, ph = _parse_user_mask(pattern)
        return (_normalize_nick(pn) == _normalize_nick(target_nick) and
                pu == _parse_user_mask(target_mask)[1] and ph == _parse_user_mask(target_mask)[2])
    else:
        return _normalize_nick(pattern) == _normalize_nick(target_nick)

def check_irc_requirements() -> bool:
    if not os.getenv("IRC_SERVER"):
        logger.warning("IRC: IRC_SERVER not set")
        return False
    if not os.getenv("IRC_NICK"):
        logger.warning("IRC: IRC_NICK not set")
        return False
    try:
        import irc3
        return True
    except ImportError:
        logger.warning("IRC: irc3 not installed. Run: pip install irc3")
        return False

class IRCAdapter(BasePlatformAdapter):
    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform.IRC)
        self._server = config.extra.get("server") or os.getenv("IRC_SERVER", "")
        self._port = int(str(config.extra.get("port") or os.getenv("IRC_PORT", "6667")).strip())
        self._nick = config.extra.get("nick") or os.getenv("IRC_NICK", "hermes-bot")
        self._username = config.extra.get("username") or os.getenv("IRC_USERNAME", self._nick)
        self._realname = config.extra.get("realname") or os.getenv("IRC_REALNAME", "Hermes Agent")
        self._channels = _parse_comma_list(os.getenv("IRC_CHANNELS", ""))
        self._use_tls = (config.extra.get("tls") or os.getenv("IRC_TLS", "")).lower() in ("true", "1", "yes")
        self._sasl_user = os.getenv("IRC_SASL_USERNAME", "")
        self._sasl_pass = os.getenv("IRC_SASL_PASSWORD", "")
        self._allowed_users = set(_parse_comma_list(os.getenv("IRC_ALLOWED_USERS", "")))
        self._allow_all = os.getenv("IRC_ALLOW_ALL_USERS", "").lower() in ("true", "1", "yes")
        self._flood_protect = (config.extra.get("flood_protect") or os.getenv("IRC_FLOOD_PROTECT", "true")).lower() not in ("false", "0", "no")
        self._msg_times: Dict[str, deque] = {}
        self._irc = None
        self._running = False
        self._current_nick = self._nick
        self._processed: Set[str] = set()

    def _is_flooded(self, target: str) -> bool:
        if not self._flood_protect:
            return False
        now = time.time()
        if target not in self._msg_times:
            self._msg_times[target] = deque()
        msg_times = self._msg_times[target]
        while msg_times and now - msg_times[0] > FLOOD_WINDOW_SECONDS:
            msg_times.popleft()
        return len(msg_times) >= FLOOD_MAX_MESSAGES

    def _record_msg(self, target: str) -> None:
        if not self._flood_protect:
            return
        self._msg_times.setdefault(target, deque()).append(time.time())

    async def _wait_flood(self, target: str) -> None:
        while self._is_flooded(target):
            await asyncio.sleep(1.0)

    def _is_duplicate(self, event_id: str) -> bool:
        if event_id in self._processed:
            return True
        self._processed.add(event_id)
        if len(self._processed) > 10000:
            items = list(self._processed)
            self._processed.difference_update(items[:len(items) // 2])
        return False

    def _is_authorized(self, user_mask: str) -> bool:
        if self._allow_all:
            return True
        if not self._allowed_users:
            return False
        return any(_mask_matches(pattern, user_mask) for pattern in self._allowed_users)

    async def connect(self) -> bool:
        if not self._server or not self._nick:
            logger.error("IRC: IRC_SERVER and IRC_NICK are required")
            return False
        try:
            import irc3
        except ImportError:
            logger.error("IRC: irc3 not installed")
            return False
        self._running = True
        scheme = "ircs" if self._use_tls else "irc"
        if self._sasl_user and self._sasl_pass:
            url = f"{scheme}://{self._sasl_user}:{self._sasl_pass}@{self._server}:{self._port}"
        else:
            url = f"{scheme}://{self._server}:{self._port}"
        logger.info("IRC: connecting to %s", url.replace(self._sasl_pass, "***") if self._sasl_pass else url)
        try:
            self._irc = irc3.IRC(url=url, nick=self._nick, username=self._username, realname=self._realname, plugins=[])
            self._irc.add_hook('ready', lambda i: self._on_ready(i))
            self._irc.add_hook('privmsg', lambda i, s, t, m: asyncio.create_task(self._on_message(i, s, t, m)))
            self._irc.add_hook('action', lambda i, s, t, a: asyncio.create_task(self._on_message(i, s, t, f"* {a}")))
            self._irc.add_hook('ctcp_ping', lambda i, s, t, d: i.ctcp_ping(s, d))
            self._irc.add_hook('ctcp_version', lambda i, s, t: i.ctcp_version(s, "Hermes Agent / irc3"))
            self._irc.add_hook('ctcp_time', lambda i, s, t: i.ctcp_time(s, time.strftime("%a %b %d %H:%M:%S %Y")))
            async def run_irc():
                while self._running:
                    try:
                        self._irc.run_forever(reconnect=True)
                    except Exception as e:
                        if self._running:
                            logger.error("IRC: run_forever error: %s", e)
                            await asyncio.sleep(5)
            self._irc_task = asyncio.create_task(run_irc())
            await asyncio.sleep(2.0)
            return True
        except Exception as e:
            logger.error("IRC: connection failed: %s", e)
            self._running = False
            return False

    def _on_ready(self, irc) -> None:
        logger.info("IRC: connected to %s:%d", self._server, self._port)
        self._mark_connected()
        for channel in self._channels:
            logger.info("IRC: joining channel %s", channel)
            irc.join(channel)

    async def disconnect(self) -> None:
        logger.info("IRC: disconnecting...")
        self._running = False
        if hasattr(self, '_irc_task') and self._irc_task:
            self._irc_task.cancel()
            try:
                await self._irc_task
            except asyncio.CancelledError:
                pass
        if self._irc:
            try:
                self._irc.quit("Hermes Agent shutting down")
            except Exception:
                pass
            self._irc = None
        logger.info("IRC: disconnected")

    async def _on_message(self, irc, source, target, message) -> None:
        source_nick, _, _ = _parse_user_mask(source)
        if _normalize_nick(source_nick) == _normalize_nick(self._current_nick):
            return
        event_id = f"{source}:{target}:{message[:100]}:{time.time()}"
        if self._is_duplicate(event_id):
            return
        if not self._is_authorized(source):
            logger.debug("IRC: message from unauthorized user %s", source)
            return
        is_dm = not target.startswith("#") and not target.startswith("&")
        chat_type = "dm" if is_dm else "channel"
        if not await self._should_respond(source, target, message):
            return
        source_obj = self.build_source(chat_id=target, chat_type=chat_type, user_id=source, user_name=source_nick)
        msg_type = MessageType.COMMAND if message.startswith("!") or message.startswith("/") else MessageType.TEXT
        event = MessageEvent(text=message, message_type=msg_type, source=source_obj, raw_message={"source": source, "target": target, "message": message}, message_id=event_id)
        await self.handle_message(event)

    async def _should_respond(self, source, target, message) -> bool:
        if not target.startswith("#") and not target.startswith("&"):
            return True
        mention_patterns = [rf"@{re.escape(self._current_nick)}\\b", rf"{re.escape(self._current_nick)}:", rf"{re.escape(self._current_nick)}，"]
        for pattern in mention_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        if message.startswith("!") or message.startswith("/"):
            return True
        return False

    async def send(self, chat_id: str, content: str, reply_to: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> SendResult:
        if not content:
            return SendResult(success=True)
        if not self._irc:
            return SendResult(success=False, error="Not connected")
        formatted = self.format_message(content)
        chunks = self.truncate_message(formatted, MAX_MESSAGE_LENGTH)
        for chunk in chunks:
            await self._wait_flood(chat_id)
            try:
                self._irc.msg(chat_id, chunk)
                self._record_msg(chat_id)
                logger.debug("IRC: sent to %s: %s...", chat_id, chunk[:50])
            except Exception as e:
                logger.error("IRC: failed to send to %s: %s", chat_id, e)
                return SendResult(success=False, error=str(e))
            if len(chunks) > 1:
                await asyncio.sleep(0.5)
        return SendResult(success=True)

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        is_channel = chat_id.startswith("#") or chat_id.startswith("&")
        return {"name": chat_id, "type": "channel" if is_channel else "dm", "chat_id": chat_id}

    async def send_typing(self, chat_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        pass

    def format_message(self, content: str) -> str:
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
        content = re.sub(r'\*(.+?)\*', r'\1', content)
        content = re.sub(r'__(.+?)__', r'\1', content)
        content = re.sub(r'_(.+?)_', r'\1', content)
        content = re.sub(r'```[\s\S]*?```', '', content)
        content = re.sub(r'`([^`]+)`', r'\1', content)
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        return content
