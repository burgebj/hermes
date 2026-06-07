"""Digital-brain tools — read-only access to the bot's personal semantic memory.

The bot reaches the brain through the youself gateway (never the brain
directly): the gateway resolves this VM to its own isolated tenant+vault and
forwards the read request. Credentials never live in the VM — these tools only
need the gateway URL + bearer token that cloud-init already injects:

    YOUSELF_GATEWAY_URL    e.g. https://agent.youself.io/youself-gateway/v1
    YOUSELF_GATEWAY_TOKEN  per-VM gateway bearer token

The brain read surface is mounted under <YOUSELF_GATEWAY_URL>/brain/...

Pair this with the ``digital-brain`` skill, which enforces the search-first
workflow ("always check the brain before answering").
"""

import json
import logging
import os

import httpx

from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


def _base_and_token() -> tuple[str, str]:
    base = (os.environ.get("YOUSELF_GATEWAY_URL") or "").rstrip("/")
    token = os.environ.get("YOUSELF_GATEWAY_TOKEN") or ""
    return base, token


def _brain_available() -> bool:
    base, token = _base_and_token()
    return bool(base and token)


def _request(method: str, path: str, *, params=None, json_body=None) -> str:
    """Call the gateway brain proxy and return the response body as a string.

    The gateway already returns JSON; we forward it verbatim so the model sees
    the brain's native shape (results/excerpt/scores, note bodies, graph, ...).
    """
    base, token = _base_and_token()
    if not base or not token:
        return tool_error("digital brain not configured (missing gateway URL/token)")
    url = f"{base}/brain{path}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = httpx.request(
            method, url, params=params, json=json_body, headers=headers, timeout=_TIMEOUT
        )
    except httpx.HTTPError as e:
        logger.warning("brain request failed: %s", e)
        return tool_error(f"brain request failed: {e}")

    if resp.status_code == 503:
        return tool_error("brain not provisioned for this bot yet; try again shortly")
    if resp.status_code // 100 != 2:
        return tool_error(
            f"brain returned status {resp.status_code}", body=resp.text[:2000]
        )
    return resp.text


def brain_search(query: str, mode: str = "", limit: int = 5) -> str:
    """Search the bot's memory. mode: text|vector|hybrid (gateway default if empty)."""
    if not query or not query.strip():
        return tool_error("query is required")
    params = {"q": query, "limit": limit}
    if mode:
        params["mode"] = mode
    return _request("GET", "/search", params=params)


def brain_get_note(note_id: str) -> str:
    """Fetch a single note by id (use ids returned by brain_search)."""
    if not note_id or not note_id.strip():
        return tool_error("note_id is required")
    return _request("GET", f"/notes/{note_id}")


def brain_graph(note_id: str = "") -> str:
    """Link-graph of one note's neighbourhood (note_id set) or the whole vault."""
    if note_id and note_id.strip():
        return _request("GET", f"/notes/{note_id}/graph")
    return _request("GET", "/graph")


BRAIN_SEARCH_SCHEMA = {
    "name": "brain_search",
    "description": (
        "Search the user's digital brain (personal semantic memory) for relevant "
        "notes BEFORE answering. Returns ranked notes with excerpts and ids. "
        "Always try this first for any substantive question."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural-language search query"},
            "mode": {
                "type": "string",
                "enum": ["text", "vector", "hybrid"],
                "description": "Search mode; leave empty to use the gateway default",
            },
            "limit": {"type": "integer", "description": "Max results (default 5)"},
        },
        "required": ["query"],
    },
}

BRAIN_GET_NOTE_SCHEMA = {
    "name": "brain_get_note",
    "description": "Fetch the full content of one note from the digital brain by its id.",
    "parameters": {
        "type": "object",
        "properties": {
            "note_id": {"type": "string", "description": "Note id from brain_search results"},
        },
        "required": ["note_id"],
    },
}

BRAIN_GRAPH_SCHEMA = {
    "name": "brain_graph",
    "description": (
        "Get the link graph around a note (pass note_id) or the whole vault graph "
        "(omit note_id) to discover related knowledge in the digital brain."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "note_id": {
                "type": "string",
                "description": "Optional note id; omit for the full vault graph",
            },
        },
        "required": [],
    },
}

registry.register(
    name="brain_search",
    toolset="brain",
    schema=BRAIN_SEARCH_SCHEMA,
    handler=lambda args, **kw: brain_search(
        args.get("query", ""), mode=args.get("mode", ""), limit=args.get("limit", 5)
    ),
    check_fn=_brain_available,
    requires_env=["YOUSELF_GATEWAY_URL", "YOUSELF_GATEWAY_TOKEN"],
    emoji="🧠",
    max_result_size_chars=100_000,
)
registry.register(
    name="brain_get_note",
    toolset="brain",
    schema=BRAIN_GET_NOTE_SCHEMA,
    handler=lambda args, **kw: brain_get_note(args.get("note_id", "")),
    check_fn=_brain_available,
    requires_env=["YOUSELF_GATEWAY_URL", "YOUSELF_GATEWAY_TOKEN"],
    emoji="🧠",
    max_result_size_chars=100_000,
)
registry.register(
    name="brain_graph",
    toolset="brain",
    schema=BRAIN_GRAPH_SCHEMA,
    handler=lambda args, **kw: brain_graph(args.get("note_id", "")),
    check_fn=_brain_available,
    requires_env=["YOUSELF_GATEWAY_URL", "YOUSELF_GATEWAY_TOKEN"],
    emoji="🧠",
    max_result_size_chars=100_000,
)
