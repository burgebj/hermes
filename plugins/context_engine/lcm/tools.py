"""LCM agent tools — give the agent active control over its context window."""
from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from plugins.context_engine.lcm.engine import LcmEngine

# ---------------------------------------------------------------------------
# Per-context engine reference (thread- and task-safe via ContextVar)
# ---------------------------------------------------------------------------

_engine_var: ContextVar[LcmEngine | None] = ContextVar("lcm_engine", default=None)


def set_engine(engine: LcmEngine | None) -> None:
    """Register the active LcmEngine instance used by all tool handlers."""
    _engine_var.set(engine)


def get_engine() -> LcmEngine | None:
    """Return the currently registered LcmEngine, or None."""
    return _engine_var.get()


def _require_engine() -> LcmEngine | str:
    """Return engine or an error string if not active."""
    e = get_engine()
    if e is None:
        return "Error: LCM not active. No engine registered."
    return e


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def handle_lcm_expand(args: dict[str, Any]) -> str:
    """Expand raw message IDs back from the immutable store."""
    result = _require_engine()
    if isinstance(result, str):
        return result

    engine = result
    raw = args.get("message_ids", "")
    try:
        ids = [int(x.strip()) for x in str(raw).split(",") if x.strip()]
    except (ValueError, AttributeError):
        return "Invalid message_ids: must be comma-separated integers."

    if not ids:
        return "Invalid message_ids: no valid integers found."

    return engine.format_expanded(ids)


def handle_lcm_pin(args: dict[str, Any]) -> str:
    """Pin message IDs so they are never compacted away."""
    engine = _require_engine()
    if isinstance(engine, str):
        return engine

    raw = args.get("message_ids", "")
    try:
        new_ids = [int(x.strip()) for x in str(raw).split(",") if x.strip()]
    except (ValueError, AttributeError):
        return "Invalid message_ids: must be comma-separated integers."

    if not new_ids:
        return "Invalid message_ids: no valid integers found."

    if len(engine._pinned_ids) + len(new_ids) > engine.config.max_pinned:
        return (
            f"Cannot pin: would exceed limit of {engine.config.max_pinned} pinned messages. "
            f"Currently {len(engine._pinned_ids)} pinned."
        )

    engine._pinned_ids.update(new_ids)
    id_list = ", ".join(str(i) for i in sorted(new_ids))
    return f"Pinned message IDs: {id_list}. Total pinned: {len(engine._pinned_ids)}."


def handle_lcm_forget(args: dict[str, Any]) -> str:
    """Immediately compact specified messages out of the active context."""
    result = _require_engine()
    if isinstance(result, str):
        return result

    engine = result
    raw = args.get("message_ids", "")
    reason = args.get("reason", "agent-requested forget")

    try:
        target_ids = set(int(x.strip()) for x in str(raw).split(",") if x.strip())
    except (ValueError, AttributeError):
        return "Invalid message_ids: must be comma-separated integers."

    if not target_ids:
        return "Invalid message_ids: no valid integers found."

    # Find active entries that match the target ids
    indices = [
        i for i, entry in enumerate(engine.active)
        if entry.msg_id is not None and entry.msg_id in target_ids
    ]

    if not indices:
        return "No matching active entries found for the given message IDs."

    # Compact contiguous runs; process from oldest to newest
    compacted_count = 0
    # Group consecutive indices into runs
    runs: list[list[int]] = []
    current_run: list[int] = []
    for idx in sorted(indices):
        if not current_run or idx == current_run[-1] + 1:
            current_run.append(idx)
        else:
            runs.append(current_run)
            current_run = [idx]
    if current_run:
        runs.append(current_run)

    # Process runs in reverse order so indices stay valid
    for run in reversed(runs):
        block_start = run[0]
        block_end = run[-1] + 1
        summary_text = f"[Forgotten: {reason}]"
        engine.compact(summary_text, level=1, block_start=block_start, block_end=block_end)
        compacted_count += len(run)

    return f"Compacted {compacted_count} message(s) with reason: {reason}."


def handle_lcm_search(args: dict[str, Any]) -> str:
    """Keyword search across all ingested messages in the immutable store."""
    result = _require_engine()
    if isinstance(result, str):
        return result

    engine = result
    query = str(args.get("query", "")).strip()
    limit = int(args.get("limit", 10))

    if not query:
        return "Error: query is required."

    query_lower = query.lower()
    matches: list[str] = []

    for msg_id in range(len(engine.store)):
        msg = engine.store.get(msg_id)
        if msg is None:
            continue
        content = str(msg.get("content", "") or "")
        if query_lower in content.lower():
            role = msg.get("role", "unknown")
            snippet = content[:120].replace("\n", " ")
            matches.append(f"[msg {msg_id}] {role}: {snippet}")
            if len(matches) >= limit:
                break

    if not matches:
        return f"No matches found for query: {query!r}"

    return "\n".join(matches)


def handle_lcm_budget(args: dict[str, Any]) -> str:
    """Return token usage breakdown for the current active context."""
    result = _require_engine()
    if isinstance(result, str):
        return result

    engine = result

    raw_entries = [e for e in engine.active if e.kind == "raw"]
    summary_entries = [e for e in engine.active if e.kind == "summary"]

    raw_tokens = sum(
        len(str(e.message.get("content", "") or "")) // 4 + 4
        for e in raw_entries
    )
    summary_tokens = sum(
        len(str(e.message.get("content", "") or "")) // 4 + 4
        for e in summary_entries
    )
    active_tokens = engine.active_tokens()
    store_count = len(engine.store)

    lines = [
        "LCM Context Budget:",
        f"  Active entries : {len(engine.active)} ({len(raw_entries)} raw, {len(summary_entries)} summaries)",
        f"  Active tokens  : ~{active_tokens}",
        f"  Raw tokens     : ~{raw_tokens}",
        f"  Summary tokens : ~{summary_tokens}",
        f"  Store total    : {store_count} messages (immutable)",
        f"  Pinned IDs     : {sorted(engine._pinned_ids) or 'none'}",
    ]
    return "\n".join(lines)


def handle_lcm_toc(args: dict[str, Any]) -> str:
    """Return a table of contents / timeline of the active conversation."""
    result = _require_engine()
    if isinstance(result, str):
        return result

    engine = result

    if not engine.active:
        return "Active context is empty."

    lines = ["Conversation Timeline:"]
    for i, entry in enumerate(engine.active):
        if entry.kind == "raw":
            role = entry.message.get("role", "?")
            content = str(entry.message.get("content", "") or "")
            snippet = content[:60].replace("\n", " ")
            lines.append(f"  [{i}] msg {entry.msg_id} ({role}): {snippet}")
        else:
            content = str(entry.message.get("content", "") or "")
            snippet = content[:60].replace("\n", " ")
            lines.append(f"  [{i}] summary node={entry.node_id}: {snippet}")

    return "\n".join(lines)


def handle_lcm_focus(args: dict[str, Any]) -> str:
    """Expand a summary node back into its original raw entries in the active context."""
    result = _require_engine()
    if isinstance(result, str):
        return result

    engine = result
    raw_node_id = args.get("node_id")
    if raw_node_id is None:
        return "Error: node_id is required."

    try:
        node_id = int(raw_node_id)
    except (ValueError, TypeError):
        return "Invalid node_id: must be an integer."

    # Find the summary entry in active
    summary_index: int | None = None
    for i, entry in enumerate(engine.active):
        if entry.kind == "summary" and entry.node_id == node_id:
            summary_index = i
            break

    if summary_index is None:
        return f"No active summary entry found for node_id={node_id}."

    # Retrieve original messages for this node
    pairs = engine.expand_summary(node_id)
    if not pairs:
        return f"Summary node {node_id} has no source messages to expand."

    from plugins.context_engine.lcm.engine import ContextEntry

    expanded_entries = [
        ContextEntry.raw(mid, msg) for mid, msg in pairs
    ]

    # Replace the summary entry with the expanded raw entries
    engine.active[summary_index : summary_index + 1] = expanded_entries

    # Expanding a summary increases token count; clear the pending flag so the
    # next check_thresholds() call can trigger async compaction if needed.
    engine._async_compaction_pending = False

    return (
        f"Expanded summary node {node_id} into {len(expanded_entries)} raw message(s). "
        f"Active context now has {len(engine.active)} entries."
    )


# ---------------------------------------------------------------------------
# Tool schemas (OpenAI function-calling format)
# ---------------------------------------------------------------------------

LCM_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "lcm_expand": {
        "name": "lcm_expand",
        "description": (
            "Retrieve the full original text of one or more messages by their numeric IDs. "
            "Use this when a summary references earlier content you need to read verbatim."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message_ids": {
                    "type": "string",
                    "description": "Comma-separated message IDs to expand (e.g. '0,1,5').",
                },
            },
            "required": ["message_ids"],
        },
    },
    "lcm_pin": {
        "name": "lcm_pin",
        "description": (
            "Pin message IDs so they are never automatically compacted away. "
            "Use for critical reference material that must stay verbatim."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message_ids": {
                    "type": "string",
                    "description": "Comma-separated message IDs to pin (e.g. '2,3').",
                },
            },
            "required": ["message_ids"],
        },
    },
    "lcm_forget": {
        "name": "lcm_forget",
        "description": (
            "Immediately compact specified messages out of the active context. "
            "Use when you know a conversation segment is no longer relevant."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message_ids": {
                    "type": "string",
                    "description": "Comma-separated message IDs to forget (e.g. '0,1,2').",
                },
                "reason": {
                    "type": "string",
                    "description": "Brief reason for forgetting (recorded in the summary placeholder).",
                },
            },
            "required": ["message_ids"],
        },
    },
    "lcm_search": {
        "name": "lcm_search",
        "description": (
            "Keyword search across all ingested messages, including those already compacted. "
            "Returns matching message IDs and snippets."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keyword or phrase to search for.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 10).",
                },
            },
            "required": ["query"],
        },
    },
    "lcm_budget": {
        "name": "lcm_budget",
        "description": (
            "Show the current token usage breakdown: active entries, raw vs summary split, "
            "store size, and pinned IDs."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "lcm_toc": {
        "name": "lcm_toc",
        "description": (
            "Show a table of contents / timeline of all active context entries. "
            "Lists each entry with its index, type, role, and a short snippet."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "lcm_focus": {
        "name": "lcm_focus",
        "description": (
            "Expand a summary node back into its original raw messages in the active context. "
            "Use when you need full detail from a section that was previously summarised."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "integer",
                    "description": "The summary node ID to expand (visible in lcm_toc output).",
                },
            },
            "required": ["node_id"],
        },
    },
}
