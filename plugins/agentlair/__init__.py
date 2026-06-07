"""AgentLair plugin for Hermes Agent.

Connects Hermes to AgentLair's persistent agent identity infrastructure,
enabling reliable async messaging between agents across sessions, crashes,
and platform boundaries (Telegram, Discord, CLI, etc.).

## Why this matters

``delegate_task`` creates ephemeral children that return summaries and
disconnect.  That works within a single runtime, but for cross-platform
coordination — or any case where an external system needs to reach a Hermes
agent asynchronously — there's no persistent address to send to.

AgentLair provides each agent with a stable ``@agentlair.dev`` email address
that survives crashes, container restarts, and model switches.  This plugin
drains that inbox at session startup so cross-agent messages are never lost.

## Integration shape (per voidborne-d's recommendation, issue #344)

1. **Lifecycle hook** (``on_session_start``): drain inbox before local
   planning starts.  Solving coordination without forcing every agent prompt
   to remember to call a tool first.

2. **Thin tool wrapper** (``agentlair_send_message``): explicit user/agent-
   driven send only where intentional messaging is needed.  Tool also supports
   ``agentlair_read_inbox`` for on-demand refresh mid-session.

3. **Delegate fallback**: crash-resilient at-least-once delivery.  The inbox
   cursor only advances when a session ends cleanly (``on_session_end``).  If
   a session crashes mid-task, the same unprocessed messages are re-delivered
   on the next ``kickoff()``.

## Configuration

Set in ``~/.hermes/.env`` or environment:

    AGENTLAIR_API_KEY=al_live_...   # Required: your AgentLair API key
    AGENTLAIR_EMAIL=myagent@agentlair.dev  # Required: your claimed address
    AGENTLAIR_BASE_URL=https://agentlair.dev  # Optional: defaults shown

Get a free API key and claim your address at https://agentlair.dev.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_BASE_URL = "https://agentlair.dev"
_CURSOR_VAULT_KEY = "agentlair_inbox_cursor"

# ---------------------------------------------------------------------------
# Session-scoped state (reset each session)
# ---------------------------------------------------------------------------

_session_lock = threading.Lock()
_pending_messages: List[Dict[str, Any]] = []   # messages drained at startup
_delivered_cursor: Optional[str] = None        # newest message_id delivered this session


# ---------------------------------------------------------------------------
# AgentLair HTTP client
# ---------------------------------------------------------------------------

class _AgentLairClient:
    """Minimal HTTP client for AgentLair v1 API."""

    def __init__(self, api_key: str, base_url: str, email: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.email = email
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "hermes-agent/agentlair-plugin",
        }

    def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> Optional[Dict]:
        """HTTP GET, returns parsed JSON or None on error."""
        try:
            import urllib.request, urllib.parse, json
            url = f"{self.base_url}{path}"
            if params:
                url = f"{url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers=self._headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as exc:
            logger.debug("AgentLair GET %s failed: %s", path, exc)
            return None

    def _post(self, path: str, body: Dict) -> Optional[Dict]:
        """HTTP POST with JSON body, returns parsed JSON or None on error."""
        try:
            import urllib.request, json
            url = f"{self.base_url}{path}"
            data = json.dumps(body).encode()
            req = urllib.request.Request(url, data=data, headers=self._headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as exc:
            logger.debug("AgentLair POST %s failed: %s", path, exc)
            return None

    def _put(self, path: str, body: Dict) -> Optional[Dict]:
        """HTTP PUT with JSON body, returns parsed JSON or None on error."""
        try:
            import urllib.request, json
            url = f"{self.base_url}{path}"
            data = json.dumps(body).encode()
            req = urllib.request.Request(url, data=data, headers=self._headers, method="PUT")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as exc:
            logger.debug("AgentLair PUT %s failed: %s", path, exc)
            return None

    def read_inbox(self, since_id: Optional[str] = None) -> List[Dict]:
        """
        Return inbox messages newer than ``since_id``.

        Uses the ``read`` field as a proxy for "unprocessed" when no cursor
        is stored in the vault yet — i.e. on first run, only unread messages
        are surfaced.  After the first clean session end, the cursor advances
        and all messages since that cursor are delivered (at-least-once).
        """
        result = self._get("/v1/email/inbox", {"address": self.email})
        if not result or "messages" not in result:
            return []
        messages = result["messages"]

        if since_id:
            # Deliver all messages newer than the stored cursor.
            # AgentLair returns messages newest-first; find cursor position
            # and take everything before it.
            new_messages = []
            for msg in messages:
                if msg.get("message_id") == since_id:
                    break
                new_messages.append(msg)
            return list(reversed(new_messages))  # oldest first for context
        else:
            # No cursor yet: only surface unread messages (conservative default)
            unread = [m for m in messages if not m.get("read", True)]
            return list(reversed(unread))  # oldest first

    def read_message(self, message_id_url: str) -> Optional[str]:
        """Fetch full message body by URL-encoded message ID."""
        result = self._get(f"/v1/email/messages/{message_id_url}",
                           {"address": self.email})
        if not result:
            return None
        return result.get("body") or result.get("snippet") or ""

    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> Dict:
        """Send a message from this agent's address."""
        result = self._post("/v1/email/send", {
            "from": self.email,
            "to": to,
            "subject": subject,
            "body": body,
        })
        return result or {"error": "send failed (network or API error)"}

    def vault_get(self, key: str) -> Optional[str]:
        """Read a value from AgentLair vault."""
        result = self._get(f"/v1/vault/{key}")
        if result and "value" in result:
            return result["value"]
        return None

    def vault_put(self, key: str, value: str) -> bool:
        """Store a value in AgentLair vault."""
        result = self._put(f"/v1/vault/{key}", {"value": value})
        return bool(result)


# ---------------------------------------------------------------------------
# Client factory (cached per session, lazy)
# ---------------------------------------------------------------------------

_client: Optional[_AgentLairClient] = None
_client_lock = threading.Lock()


def _get_client() -> Optional[_AgentLairClient]:
    """Return the singleton client, or None if not configured."""
    global _client
    with _client_lock:
        if _client is not None:
            return _client

        api_key = os.environ.get("AGENTLAIR_API_KEY", "").strip()
        email = os.environ.get("AGENTLAIR_EMAIL", "").strip()
        base_url = os.environ.get("AGENTLAIR_BASE_URL", _DEFAULT_BASE_URL).strip()

        if not api_key:
            logger.debug("AgentLair plugin: AGENTLAIR_API_KEY not set — skipping")
            return None
        if not email:
            logger.debug("AgentLair plugin: AGENTLAIR_EMAIL not set — skipping")
            return None

        _client = _AgentLairClient(api_key, base_url, email)
        return _client


# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------

def _on_session_start(session_id: str, model: str, platform: str, **_) -> None:
    """
    Drain the AgentLair inbox at session start.

    Reads all messages newer than the last processed cursor (stored in
    AgentLair vault for crash resilience).  Messages are held in
    ``_pending_messages`` and injected as context on the first LLM call.

    Crash recovery: the cursor is only advanced on clean session end
    (``on_session_end`` hook).  If this session crashes, the same messages
    will be re-delivered on the next ``kickoff()``.
    """
    global _pending_messages, _delivered_cursor

    client = _get_client()
    if client is None:
        return

    # Reset session state
    with _session_lock:
        _pending_messages = []
        _delivered_cursor = None

    # Load last-processed cursor from vault
    cursor = client.vault_get(_CURSOR_VAULT_KEY)
    logger.debug("AgentLair: inbox drain — cursor=%s", cursor or "none")

    # Drain inbox since cursor
    messages = client.read_inbox(since_id=cursor)
    if not messages:
        logger.debug("AgentLair: inbox empty (no new messages since cursor)")
        return

    logger.info("AgentLair: %d new message(s) drained from inbox", len(messages))

    with _session_lock:
        _pending_messages = messages
        # Track the newest message ID for cursor advancement on clean end
        if messages:
            _delivered_cursor = messages[-1].get("message_id")


def _pre_llm_call(
    session_id: str,
    user_message: str,
    is_first_turn: bool,
    **_,
) -> Optional[str]:
    """
    Inject drained inbox messages as context on the first turn only.

    Returns a formatted string with message summaries, or None if no
    messages were drained.  The agent core appends this to the user
    message for the first LLM call.
    """
    if not is_first_turn:
        return None

    with _session_lock:
        messages = list(_pending_messages)

    if not messages:
        return None

    client = _get_client()
    lines = [
        f"📬 **AgentLair inbox: {len(messages)} new message(s) received**\n"
    ]
    for i, msg in enumerate(messages, 1):
        frm = msg.get("from", "unknown")
        subj = msg.get("subject", "(no subject)")
        snippet = msg.get("snippet", "")
        received = msg.get("received_at", "")
        auth = msg.get("auth", {})
        auth_status = "✓ authenticated" if auth.get("authenticated") else "⚠ unverified"

        lines.append(
            f"**Message {i}** — From: {frm} | Subject: {subj}\n"
            f"Received: {received} | {auth_status}\n"
            f"Preview: {snippet[:200]}"
        )
        if i < len(messages):
            lines.append("")

    lines.append(
        "\n*(Reply using the `agentlair_send_message` tool. "
        "Messages persist across sessions — the sender will receive your reply "
        "even if they're offline.)*"
    )

    return "\n".join(lines)


def _on_session_end(session_id: str, **_) -> None:
    """
    Advance the inbox cursor on clean session end.

    Only called when the session completes normally — not on crash.
    This ensures at-least-once delivery: messages are re-delivered if
    the session dies before the agent can act on them.
    """
    client = _get_client()
    if client is None:
        return

    with _session_lock:
        cursor = _delivered_cursor

    if cursor:
        logger.debug("AgentLair: advancing inbox cursor to %s", cursor)
        client.vault_put(_CURSOR_VAULT_KEY, cursor)


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

SEND_MESSAGE_SCHEMA = {
    "name": "agentlair_send_message",
    "description": (
        "Send an async message to another agent or human via AgentLair email. "
        "The recipient gets a persistent @agentlair.dev address — messages "
        "survive crashes and offline periods and are delivered at next session start. "
        "Use for: coordinating with other Hermes agents, replying to inbox messages, "
        "or sending results to any email address."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": (
                    "Recipient address. Can be any @agentlair.dev agent address "
                    "or any standard email address."
                ),
            },
            "subject": {
                "type": "string",
                "description": "Message subject line.",
            },
            "body": {
                "type": "string",
                "description": "Message body (plain text).",
            },
        },
        "required": ["to", "subject", "body"],
    },
}

READ_INBOX_SCHEMA = {
    "name": "agentlair_read_inbox",
    "description": (
        "Refresh and read the AgentLair inbox mid-session. "
        "Returns new messages received since session start. "
        "The inbox is also drained automatically at session startup — "
        "use this tool only if you need to poll for late-arriving replies."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of messages to return (default 10).",
            },
        },
        "required": [],
    },
}


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def _handle_send_message(to: str, subject: str, body: str, **_) -> str:
    """Send a message via AgentLair email."""
    import json
    client = _get_client()
    if client is None:
        return json.dumps({
            "error": "AgentLair not configured",
            "hint": (
                "Set AGENTLAIR_API_KEY and AGENTLAIR_EMAIL in ~/.hermes/.env. "
                "Get a free API key at https://agentlair.dev"
            ),
        })

    result = client.send_message(to=to, subject=subject, body=body)
    if result.get("sent") or result.get("message_id"):
        return json.dumps({
            "sent": True,
            "to": to,
            "subject": subject,
            "from": client.email,
            "message_id": result.get("message_id"),
        })
    return json.dumps({"error": result.get("error", "Unknown error"), "raw": result})


def _handle_read_inbox(limit: int = 10, **_) -> str:
    """Read inbox mid-session (on-demand refresh)."""
    import json
    client = _get_client()
    if client is None:
        return json.dumps({
            "error": "AgentLair not configured",
            "hint": "Set AGENTLAIR_API_KEY and AGENTLAIR_EMAIL in ~/.hermes/.env",
        })

    with _session_lock:
        cursor = _delivered_cursor

    messages = client.read_inbox(since_id=cursor)
    if not messages:
        return json.dumps({"messages": [], "count": 0})

    # Limit and format
    messages = messages[:limit]
    formatted = []
    for msg in messages:
        formatted.append({
            "from": msg.get("from"),
            "subject": msg.get("subject"),
            "snippet": msg.get("snippet", "")[:300],
            "received_at": msg.get("received_at"),
            "authenticated": msg.get("auth", {}).get("authenticated", False),
            "message_id": msg.get("message_id"),
        })

    return json.dumps({"messages": formatted, "count": len(formatted)})


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def _check_available() -> bool:
    """Return True if AgentLair is configured."""
    return bool(
        os.environ.get("AGENTLAIR_API_KEY", "").strip()
        and os.environ.get("AGENTLAIR_EMAIL", "").strip()
    )


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Called once at plugin load. Register hooks and tools."""

    # Register lifecycle hooks
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("on_session_end", _on_session_end)

    # Register tools
    ctx.register_tool(
        name="agentlair_send_message",
        toolset="agentlair",
        schema=SEND_MESSAGE_SCHEMA,
        handler=_handle_send_message,
        check_fn=_check_available,
        requires_env=["AGENTLAIR_API_KEY", "AGENTLAIR_EMAIL"],
        description="Send async message to agent or human via AgentLair",
        emoji="📤",
    )

    ctx.register_tool(
        name="agentlair_read_inbox",
        toolset="agentlair",
        schema=READ_INBOX_SCHEMA,
        handler=_handle_read_inbox,
        check_fn=_check_available,
        requires_env=["AGENTLAIR_API_KEY", "AGENTLAIR_EMAIL"],
        description="Read AgentLair inbox (on-demand mid-session refresh)",
        emoji="📬",
    )

    logger.debug("AgentLair plugin registered (hooks: on_session_start, pre_llm_call, on_session_end)")
