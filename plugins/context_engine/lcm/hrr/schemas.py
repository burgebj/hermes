"""Tool schemas for the unified memory_* tool surface (OpenAI function-calling format).

These five tools replace 11 fragmented lcm_* / dam_* tools with a single surface
that auto-routes across three memory layers:
- DAM  (in-session, fast)        via engine.retriever
- HRR  (cross-session, persistent) via engine.hrr_store
- LCM  (context management)       via the engine directly
"""

from __future__ import annotations

from typing import Any

MEMORY_SEARCH: dict[str, Any] = {
    "name": "memory_search",
    "description": (
        "Search across session memory and persistent knowledge. "
        "Use 'session' for current conversation, 'memory' for past sessions, "
        "or 'auto' to search both."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query.",
            },
            "source": {
                "type": "string",
                "enum": ["auto", "session", "memory"],
                "description": (
                    "Which memory layer(s) to search. "
                    "'session' = current conversation (DAM), "
                    "'memory' = persistent cross-session knowledge (HRR), "
                    "'auto' = both (default)."
                ),
            },
        },
        "required": ["query"],
    },
}

MEMORY_PIN: dict[str, Any] = {
    "name": "memory_pin",
    "description": (
        "Pin messages to prevent compaction and save them as persistent knowledge."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "message_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "List of message IDs to pin.",
            },
            "reason": {
                "type": "string",
                "description": "Why these messages are important (used as tags in persistent memory).",
            },
        },
        "required": ["message_ids"],
    },
}

MEMORY_EXPAND: dict[str, Any] = {
    "name": "memory_expand",
    "description": (
        "Expand compacted summaries to see original messages, "
        "or recall facts from persistent memory."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "message_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Message IDs to expand (for session source).",
            },
            "query": {
                "type": "string",
                "description": "Query for recalling persistent memories (for memory source).",
            },
            "source": {
                "type": "string",
                "enum": ["session", "memory"],
                "description": (
                    "'session' = expand compacted summaries in current context (default), "
                    "'memory' = recall facts from persistent cross-session storage."
                ),
            },
        },
        "required": [],
    },
}

MEMORY_FORGET: dict[str, Any] = {
    "name": "memory_forget",
    "description": (
        "Compact specified messages immediately. "
        "Optionally reduce trust of related persistent memories."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "message_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "List of message IDs to compact/forget.",
            },
            "reason": {
                "type": "string",
                "description": "Brief reason for forgetting (recorded in the summary placeholder).",
            },
            "lower_trust": {
                "type": "boolean",
                "description": (
                    "If true, also reduce trust score of related persistent memories "
                    "(default false)."
                ),
            },
        },
        "required": ["message_ids"],
    },
}

MEMORY_REASON: dict[str, Any] = {
    "name": "memory_reason",
    "description": (
        "Compositional reasoning across persistent knowledge. "
        "Find facts connected to entities through algebraic vector operations."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Entities to reason about (one or more names/concepts).",
            },
            "action": {
                "type": "string",
                "enum": ["probe", "related", "reason", "contradict"],
                "description": (
                    "'probe' = find facts structurally involving one entity (role-bound), "
                    "'related' = find facts connected to an entity in any structural role, "
                    "'reason' = multi-entity AND intersection (default), "
                    "'contradict' = find pairs of contradictory facts."
                ),
            },
        },
        "required": ["entities"],
    },
}

# Registry dict — used by the tool registration layer
MEMORY_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "memory_search": MEMORY_SEARCH,
    "memory_pin": MEMORY_PIN,
    "memory_expand": MEMORY_EXPAND,
    "memory_forget": MEMORY_FORGET,
    "memory_reason": MEMORY_REASON,
}
