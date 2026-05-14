"""DAM tool handlers."""
from __future__ import annotations

import json
from typing import Any

_retriever = None


def _get_retriever():
    return _retriever


def _format_snippet(msg_id: int) -> str:
    """Look up a message by ID from the active LCM engine and format a snippet."""
    try:
        from plugins.context_engine.lcm.tools import get_engine
        engine = get_engine()
        if engine is None:
            return f"[msg {msg_id}]"
        msg = engine.store.get(msg_id)
        if msg is None:
            return f"[msg {msg_id}]"
        role = msg.get("role", "unknown")
        content = str(msg.get("content", "") or "")
        snippet = content[:120].replace("\n", " ")
        return f"[msg {msg_id}] {role}: {snippet}"
    except Exception:
        return f"[msg {msg_id}]"


def handle_dam_search(args: dict[str, Any], **kwargs) -> str:
    """Semantic search across conversation messages."""
    r = _get_retriever()
    if r is None:
        try:
            from plugins.context_engine.lcm.tools import handle_lcm_search
            return handle_lcm_search(args)
        except Exception:
            return json.dumps({"error": "DAM not initialized and LCM fallback unavailable"})

    query = str(args.get("query", "")).strip()
    if not query:
        return json.dumps({"error": "query is required"})

    try:
        limit = int(args.get("limit", 10))
        results = r.search(query, limit=limit)
        if not results:
            try:
                from plugins.context_engine.lcm.tools import handle_lcm_search
                fallback = handle_lcm_search({"query": query, "limit": limit})
                return f"(keyword fallback)\n{fallback}"
            except Exception:
                return f"No matches for: {query!r}"

        lines = [f"DAM search ({len(results)} matches):"]
        for msg_id, score in results:
            lines.append(_format_snippet(msg_id))
        return "\n".join(lines)
    except Exception as e:
        return json.dumps({"error": str(e)})


def handle_dam_recall(args: dict[str, Any], **kwargs) -> str:
    """Find messages similar to a specific message by ID."""
    r = _get_retriever()
    if r is None:
        return json.dumps({"error": "DAM not initialized"})

    msg_id = args.get("message_id")
    if msg_id is None:
        return json.dumps({"error": "message_id is required"})

    try:
        results = r.recall_similar(int(msg_id), limit=int(args.get("limit", 5)))
        if not results:
            return f"No similar messages found for msg {msg_id}"

        lines = [f"Messages similar to msg {msg_id}:"]
        for similar_id, score in results:
            lines.append(_format_snippet(similar_id))
        return "\n".join(lines)
    except Exception as e:
        return json.dumps({"error": str(e)})


def handle_dam_compose(args: dict[str, Any], **kwargs) -> str:
    """Compositional search combining multiple concept queries."""
    r = _get_retriever()
    if r is None:
        return json.dumps({"error": "DAM not initialized"})

    queries = args.get("queries", [])
    if not queries or len(queries) < 2:
        return json.dumps({"error": "At least 2 queries required"})

    op = str(args.get("operation", "AND")).upper()
    if op not in ("AND", "OR", "NOT"):
        return json.dumps({"error": f"Invalid operation: {op!r}. Must be AND, OR, or NOT"})

    try:
        limit = int(args.get("limit", 10))
        results = r.compose(queries, operation=op, limit=limit)
        if not results:
            return f"No matches for {op} of: {queries}"

        lines = [f"DAM {op} ({', '.join(queries)}):"]
        for msg_id, score in results:
            lines.append(_format_snippet(msg_id))
        return "\n".join(lines)
    except Exception as e:
        return json.dumps({"error": str(e)})


def handle_dam_status(args: dict[str, Any], **kwargs) -> str:
    """Return Dense Associative Memory network statistics."""
    r = _get_retriever()
    if r is None:
        return "DAM plugin loaded but not initialized (LCM disabled or numpy unavailable)"

    try:
        s = r.get_status()
        nh = s["nh"]
        return "\n".join([
            "Dense Associative Memory Status:",
            f"  Nv={s['nv']}, Nh={nh}",
            f"  Capacity: 2^{nh} = {2 ** nh:,}",
            f"  Patterns stored: {s['patterns_stored']}",
            f"  Patterns trained: {s.get('n_patterns_trained', 'N/A')}",
            f"  Last indexed: msg {s['last_indexed_id']}",
        ])
    except Exception as e:
        return json.dumps({"error": str(e)})
