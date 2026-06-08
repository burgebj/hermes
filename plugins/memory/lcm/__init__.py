"""LCM memory plugin — MemoryProvider interface.

Local Context Memory service: a containerized memory backend with
embedding-based recall, session-scoped turn tracking, and tool-based
recall/store/forget operations.

Config via environment variables:
  BUTTER_LCM_ENABLED        — enable/disable (default: true)
  BUTTER_LCM_SERVICE_URL    — service base URL (blank = http://localhost:18732)
  BUTTER_LCM_EMBED_PROVIDER — embedding provider (ollama|openai|azure|bedrock)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Dict, List

import httpx

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error

logger = logging.getLogger(__name__)

_CONTAINER_NAME = "hermes-lcm"
_DATA_VOLUME = "hermes-lcm-data"
_DEFAULT_PORT = 18732
_MAX_RETRIES = 2
_RETRY_BACKOFF = 0.5


def _base_url() -> str:
    url = os.environ.get("BUTTER_LCM_SERVICE_URL", "").strip()
    if url:
        return url.rstrip("/")
    return f"http://localhost:{_DEFAULT_PORT}"


def _enabled() -> bool:
    val = os.environ.get("BUTTER_LCM_ENABLED", "true").strip().lower()
    return val in ("true", "1", "yes", "on")


def _retry_get(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return client.get(url, **kwargs)
        except (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
        ) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF * (attempt + 1))
    raise last_exc  # type: ignore[misc]


def _retry_post(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return client.post(url, **kwargs)
        except (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
        ) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF * (attempt + 1))
    raise last_exc  # type: ignore[misc]


def _retry_delete(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return client.delete(url, **kwargs)
        except (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
        ) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF * (attempt + 1))
    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

STORE_SCHEMA = {
    "name": "lcm_store",
    "description": (
        "Store a durable fact or observation in LCM memory. Use for explicit "
        "preferences, corrections, decisions, or anything worth recalling later."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The fact or observation to store.",
            },
            "metadata": {
                "type": "object",
                "description": "Optional key-value metadata to attach.",
            },
        },
        "required": ["content"],
    },
}

RECALL_SCHEMA = {
    "name": "lcm_recall",
    "description": (
        "Recall memories from LCM by semantic similarity. Returns relevant "
        "facts ranked by relevance to the query."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to recall."},
            "top_k": {"type": "integer", "description": "Max results (default: 5)."},
        },
        "required": ["query"],
    },
}

LIST_SCHEMA = {
    "name": "lcm_list",
    "description": "List recent memories stored in LCM. Returns the latest entries.",
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Max entries to return (default: 20).",
            },
        },
        "required": [],
    },
}

FORGET_SCHEMA = {
    "name": "lcm_forget",
    "description": "Remove a specific memory from LCM by its ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "memory_id": {"type": "string", "description": "The memory ID to remove."},
        },
        "required": ["memory_id"],
    },
}

STATS_SCHEMA = {
    "name": "lcm_stats",
    "description": "Show LCM memory statistics: total memories, storage size, embedding count.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}


# ---------------------------------------------------------------------------
# MemoryProvider implementation
# ---------------------------------------------------------------------------


class LcmMemoryProvider(MemoryProvider):
    """LCM (Local Context Memory) provider — containerized memory backend."""

    def __init__(self):
        self._base_url = ""
        self._client: httpx.Client | None = None
        self._session_id = ""
        self._healthy = False
        self._prefetch_result = ""
        self._prefetch_lock = threading.Lock()
        self._prefetch_thread: threading.Thread | None = None
        self._sync_thread: threading.Thread | None = None

    @property
    def name(self) -> str:
        return "lcm"

    def is_available(self) -> bool:
        if not _enabled():
            return False
        try:
            base = _base_url()
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{base}/health")
                return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException, OSError):
            return False

    def get_config_schema(self):
        return [
            {
                "key": "enabled",
                "description": "Enable LCM memory provider",
                "default": "true",
                "choices": ["true", "false"],
                "env_var": "BUTTER_LCM_ENABLED",
            },
            {
                "key": "service_url",
                "description": "LCM service URL (blank = local container)",
                "default": "",
                "env_var": "BUTTER_LCM_SERVICE_URL",
            },
            {
                "key": "embed_provider",
                "description": "Embedding provider for vector search",
                "choices": ["ollama", "openai", "azure", "bedrock"],
                "required": True,
                "env_var": "BUTTER_LCM_EMBED_PROVIDER",
            },
        ]

    def save_config(self, values, hermes_home):
        pass

    def initialize(self, session_id: str, **kwargs) -> None:
        self._base_url = _base_url()
        self._session_id = session_id

        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

        try:
            resp = _retry_get(self._client, "/health")
            if resp.status_code == 200:
                self._healthy = True
                logger.info("LCM service connected at %s", self._base_url)
            else:
                logger.warning("LCM health check returned %d", resp.status_code)
                self._healthy = False
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as exc:
            logger.warning("LCM service unreachable at %s: %s", self._base_url, exc)
            self._healthy = False

    def system_prompt_block(self) -> str:
        if not self._healthy:
            return ""
        return (
            "# LCM Memory\n"
            "Active. Use lcm_store to persist facts, lcm_recall for semantic search, "
            "lcm_list to browse, lcm_forget to remove, lcm_stats for usage."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if self._prefetch_thread and self._prefetch_thread.is_alive():
            self._prefetch_thread.join(timeout=3.0)
        with self._prefetch_lock:
            result = self._prefetch_result
            self._prefetch_result = ""
        if not result:
            return ""
        return f"<lcm-context>\n{result}\n</lcm-context>"

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        if not self._healthy or self._client is None:
            return

        sid = session_id or self._session_id

        def _run():
            try:
                resp = _retry_post(
                    self._client,
                    "/memory/recall",
                    json={"query": query, "session_id": sid, "top_k": 5},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("results", [])
                    if items:
                        lines = [
                            f"- {item.get('content', item.get('memory', ''))}"
                            for item in items
                        ]
                        with self._prefetch_lock:
                            self._prefetch_result = "\n".join(lines)
                else:
                    logger.debug("LCM prefetch returned %d", resp.status_code)
            except (httpx.ConnectError, httpx.TimeoutException, OSError) as exc:
                logger.debug("LCM prefetch failed: %s", exc)

        self._prefetch_thread = threading.Thread(
            target=_run, daemon=True, name="lcm-prefetch"
        )
        self._prefetch_thread.start()

    def sync_turn(
        self, user_content: str, assistant_content: str, *, session_id: str = ""
    ) -> None:
        if not self._healthy or self._client is None:
            return

        sid = session_id or self._session_id

        def _sync():
            try:
                resp = _retry_post(
                    self._client,
                    "/memory/session/turn_pair",
                    json={
                        "session_id": sid,
                        "user": user_content,
                        "assistant": assistant_content,
                    },
                )
                if resp.status_code not in (200, 201, 204):
                    logger.warning(
                        "LCM sync_turn returned %d: %s",
                        resp.status_code,
                        resp.text[:200],
                    )
            except (httpx.ConnectError, httpx.TimeoutException, OSError) as exc:
                logger.warning("LCM sync_turn failed: %s", exc)

        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5.0)

        self._sync_thread = threading.Thread(target=_sync, daemon=True, name="lcm-sync")
        self._sync_thread.start()

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        if not self._healthy:
            return []
        return [STORE_SCHEMA, RECALL_SCHEMA, LIST_SCHEMA, FORGET_SCHEMA, STATS_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        if not self._healthy or self._client is None:
            return json.dumps({"error": "LCM service is not available."})

        try:
            if tool_name == "lcm_store":
                return self._handle_store(args)
            elif tool_name == "lcm_recall":
                return self._handle_recall(args)
            elif tool_name == "lcm_list":
                return self._handle_list(args)
            elif tool_name == "lcm_forget":
                return self._handle_forget(args)
            elif tool_name == "lcm_stats":
                return self._handle_stats()
            else:
                return tool_error(f"Unknown LCM tool: {tool_name}")
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as exc:
            logger.warning("LCM tool call %s failed: %s", tool_name, exc)
            return json.dumps({"error": f"LCM service error: {exc}"})

    def _handle_store(self, args: dict) -> str:
        content = args.get("content", "")
        if not content:
            return tool_error("Missing required parameter: content")
        payload: dict[str, Any] = {
            "content": content,
            "session_id": self._session_id,
            "source": "tool",
        }
        if args.get("metadata"):
            payload["metadata"] = args["metadata"]
        resp = _retry_post(self._client, "/memory/store", json=payload)
        if resp.status_code in (200, 201):
            data = resp.json()
            return json.dumps({"result": "Stored.", "id": data.get("id", "")})
        return tool_error(f"Store failed ({resp.status_code}): {resp.text[:200]}")

    def _handle_recall(self, args: dict) -> str:
        query = args.get("query", "")
        if not query:
            return tool_error("Missing required parameter: query")
        top_k = int(args.get("top_k", 5))
        resp = _retry_post(
            self._client,
            "/memory/recall",
            json={"query": query, "session_id": self._session_id, "top_k": top_k},
        )
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("results", [])
            return json.dumps({"results": items, "count": len(items)})
        return tool_error(f"Recall failed ({resp.status_code}): {resp.text[:200]}")

    def _handle_list(self, args: dict) -> str:
        limit = int(args.get("limit", 20))
        resp = _retry_get(
            self._client,
            "/memory/list",
            params={"session_id": self._session_id, "limit": limit},
        )
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("memories", data.get("results", []))
            return json.dumps({"memories": items, "count": len(items)})
        return tool_error(f"List failed ({resp.status_code}): {resp.text[:200]}")

    def _handle_forget(self, args: dict) -> str:
        memory_id = args.get("memory_id", "")
        if not memory_id:
            return tool_error("Missing required parameter: memory_id")
        resp = _retry_delete(
            self._client,
            f"/memory/{memory_id}",
        )
        if resp.status_code in (200, 204):
            return json.dumps({"result": "Forgotten."})
        return tool_error(f"Forget failed ({resp.status_code}): {resp.text[:200]}")

    def _handle_stats(self) -> str:
        resp = _retry_get(self._client, "/memory/stats")
        if resp.status_code == 200:
            return json.dumps(resp.json())
        return tool_error(f"Stats failed ({resp.status_code}): {resp.text[:200]}")

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if not self._healthy or self._client is None:
            return
        try:
            _retry_post(
                self._client,
                "/memory/session/end",
                json={"session_id": self._session_id},
            )
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as exc:
            logger.warning("LCM session end failed: %s", exc)

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        if not self._healthy or self._client is None:
            return
        try:
            payload: dict[str, Any] = {
                "content": content,
                "session_id": self._session_id,
                "source": "mirror",
                "metadata": {
                    "action": action,
                    "target": target,
                    **(metadata or {}),
                },
            }
            _retry_post(self._client, "/memory/store", json=payload)
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as exc:
            logger.warning("LCM memory mirror failed: %s", exc)

    def shutdown(self) -> None:
        for t in (self._prefetch_thread, self._sync_thread):
            if t and t.is_alive():
                t.join(timeout=5.0)
        if self._client is not None:
            self._client.close()
            self._client = None


def register(ctx) -> None:
    """Register LCM as a memory provider plugin."""
    ctx.register_memory_provider(LcmMemoryProvider())
