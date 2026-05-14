"""Unified memory tools — auto-route across LCM, DAM, and HRR layers.

Five tools replace 11 fragmented lcm_* / dam_* tools:
  memory_search  — unified search (DAM -> HRR -> keyword fallback)
  memory_pin     — pin in LCM + crystallize to HRR
  memory_expand  — expand summaries (session) or recall facts (cross-session)
  memory_forget  — compact in LCM + optionally lower HRR trust
  memory_reason  — HRR compositional query (probe/related/reason/contradict)

The old lcm_* and dam_* tools remain fully functional (backward compat).
"""

from __future__ import annotations

import logging
from typing import Any

from plugins.context_engine.lcm.tools import get_engine

logger = logging.getLogger(__name__)


def _require_engine():
    """Return the active engine or raise RuntimeError."""
    engine = get_engine()
    if engine is None:
        raise RuntimeError("Memory system not initialized. No LCM engine registered.")
    return engine


def _normalize_ids(raw) -> list[int]:
    """Normalize message_ids from various input formats to list[int]."""
    if isinstance(raw, int):
        return [raw]
    if isinstance(raw, (list, tuple)):
        return [int(i) for i in raw]
    return []


# ---------------------------------------------------------------------------
# memory_search
# ---------------------------------------------------------------------------


def handle_memory_search(args: dict[str, Any]) -> str:
    """Unified search across DAM (session) and HRR (persistent) layers."""
    engine = _require_engine()
    query = str(args.get("query", "")).strip()
    source = args.get("source", "auto")
    limit = 10

    if not query:
        return "Error: query is required."

    results: list[str] = []

    # Layer 1: DAM (in-session semantic search) — skip when source == "memory"
    if source in ("auto", "session") and engine.retriever is not None:
        try:
            dam_results = engine.retriever.search(query, limit=limit)
            for msg_id, score in dam_results:
                msg = engine.store.get(msg_id)
                if msg:
                    role = msg.get("role", "unknown")
                    snippet = str(msg.get("content", "") or "")[:200].replace("\n", " ")
                    results.append(
                        f"[Session msg#{msg_id} score={score:.2f}] {role}: {snippet}"
                    )
        except Exception as exc:
            logger.warning("DAM search failed, falling back: %s", exc)

    # Layer 2: HRR (cross-session persistent knowledge) — skip when source == "session"
    if source in ("auto", "memory") and engine.hrr_store is not None:
        try:
            from plugins.context_engine.lcm.hrr.retrieval import FactRetriever

            retriever = FactRetriever(store=engine.hrr_store)
            hrr_results = retriever.search(query, limit=limit - len(results))
            for fact in hrr_results:
                results.append(
                    f"[Memory fact#{fact['fact_id']} trust={fact.get('trust_score', '?')}]"
                    f" {fact['content']}"
                )
        except Exception as exc:
            logger.warning("HRR search failed, falling back: %s", exc)

    # Layer 3: Keyword fallback (LCM store linear scan).
    # Only used for source="auto" or source="session".  When the caller
    # explicitly requests source="memory" (cross-session HRR only) we must
    # not fall back to the in-session store — that would leak session content
    # into what the caller expects to be persistent-memory results.
    if not results and source != "memory":
        try:
            from plugins.context_engine.lcm.tools import handle_lcm_search

            return handle_lcm_search({"query": query})
        except Exception as exc:
            logger.warning("LCM keyword fallback failed: %s", exc)

    if not results:
        return f"No results found for '{query}'."

    return "\n".join(results)


# ---------------------------------------------------------------------------
# memory_pin
# ---------------------------------------------------------------------------


def handle_memory_pin(args: dict[str, Any]) -> str:
    """Pin messages in LCM and crystallize them as persistent HRR facts."""
    engine = _require_engine()
    message_ids = _normalize_ids(args.get("message_ids", []))
    reason = str(args.get("reason", "")).strip()

    ids_str = ",".join(str(i) for i in message_ids)

    # Delegate to LCM pin
    from plugins.context_engine.lcm.tools import handle_lcm_pin

    result = handle_lcm_pin({"message_ids": ids_str})

    # Auto-crystallize to HRR persistent store
    if engine.hrr_store is not None:
        crystallized = 0
        for mid in message_ids:
            try:
                msg = engine.store.get(mid)
                if msg and msg.get("content"):
                    engine.hrr_store.add_fact(
                        content=str(msg["content"]),
                        category="pinned",
                        tags=reason or "memory_pin",
                    )
                    crystallized += 1
            except Exception as exc:
                logger.warning(
                    "Failed to crystallize pinned message %s: %s", mid, exc
                )
        if crystallized:
            result += f" Crystallized {crystallized} message(s) to persistent memory."

    return result


# ---------------------------------------------------------------------------
# memory_expand
# ---------------------------------------------------------------------------


def handle_memory_expand(args: dict[str, Any]) -> str:
    """Expand session summaries or recall persistent facts by query."""
    engine = _require_engine()
    source = args.get("source", "session")

    if source == "session":
        # Delegate to LCM expand — normalize list[int] to comma-separated string
        expand_args = dict(args)
        raw_ids = expand_args.get("message_ids")
        if raw_ids is not None:
            expand_args["message_ids"] = ",".join(
                str(i) for i in _normalize_ids(raw_ids)
            )
        from plugins.context_engine.lcm.tools import handle_lcm_expand

        return handle_lcm_expand(expand_args)

    # Cross-session: query HRR persistent store
    query = str(args.get("query", "")).strip()
    if not query:
        return "No query provided. Supply 'query' when using source='memory'."

    if engine.hrr_store is None:
        return "Persistent memory not available for cross-session recall."

    try:
        from plugins.context_engine.lcm.hrr.retrieval import FactRetriever

        retriever = FactRetriever(store=engine.hrr_store)
        results = retriever.search(query, limit=5)
        if not results:
            return f"No persistent memories found for '{query}'."

        lines = [
            f"- [{r.get('category', 'general')}] {r['content']}"
            f" (trust: {r.get('trust_score', '?')})"
            for r in results
        ]
        return "Persistent memories:\n" + "\n".join(lines)
    except Exception as exc:
        return f"Error querying persistent memory: {exc}"


# ---------------------------------------------------------------------------
# memory_forget
# ---------------------------------------------------------------------------


def handle_memory_forget(args: dict[str, Any]) -> str:
    """Compact messages in LCM and optionally lower HRR trust for related facts."""
    engine = _require_engine()
    lower_trust = bool(args.get("lower_trust", False))
    message_ids = _normalize_ids(args.get("message_ids", []))

    ids_str = ",".join(str(i) for i in message_ids)

    from plugins.context_engine.lcm.tools import handle_lcm_forget

    forget_args = dict(args)
    forget_args["message_ids"] = ids_str
    result = handle_lcm_forget(forget_args)

    # Optionally lower HRR trust for related persistent facts
    if lower_trust and engine.hrr_store is not None:
        for mid in message_ids:
            try:
                msg = engine.store.get(mid)
                if msg and msg.get("content"):
                    content_snippet = str(msg["content"])[:100]
                    matches = engine.hrr_store.search_facts(content_snippet, limit=3)
                    for match in matches:
                        engine.hrr_store.record_feedback(match["fact_id"], helpful=False)
            except Exception as exc:
                logger.warning(
                    "Failed to lower trust for message %s: %s", mid, exc
                )

    return result


# ---------------------------------------------------------------------------
# memory_reason
# ---------------------------------------------------------------------------


def handle_memory_reason(args: dict[str, Any]) -> str:
    """Compositional reasoning over persistent HRR knowledge."""
    engine = _require_engine()
    entities = [str(e).strip() for e in args.get("entities", []) if isinstance(e, str) and str(e).strip()]
    action = str(args.get("action", "reason")).strip()

    if not entities:
        return "No valid entities provided. Pass a list of entity names."

    if engine.hrr_store is None:
        return (
            "Persistent memory not available. "
            "The memory_reason tool requires cross-session knowledge (hrr_store)."
        )

    try:
        from plugins.context_engine.lcm.hrr.retrieval import FactRetriever

        retriever = FactRetriever(store=engine.hrr_store)

        if action == "probe":
            if len(entities) != 1:
                return "Error: 'probe' action requires exactly one entity."
            results = retriever.probe(entities[0], limit=10)

        elif action == "related":
            if len(entities) != 1:
                return "Error: 'related' action requires exactly one entity."
            results = retriever.related(entities[0], limit=10)

        elif action == "contradict":
            contradictions = retriever.contradict(limit=10)
            if not contradictions:
                return "No contradictions found in persistent memory."
            lines: list[str] = []
            for c in contradictions:
                lines.append(
                    f"Contradiction (score={c['contradiction_score']}):"
                )
                lines.append(f"  A: {c['fact_a']['content']}")
                lines.append(f"  B: {c['fact_b']['content']}")
                shared = ", ".join(c.get("shared_entities", []))
                lines.append(f"  Shared entities: {shared or 'none'}")
            return "\n".join(lines)

        else:
            # Default: "reason" — multi-entity AND intersection
            results = retriever.reason(entities, limit=10)

        if not results:
            return f"No facts found for entities: {', '.join(entities)}"

        lines = [
            f"- {r['content']}"
            f" (score: {r.get('score', 0.0):.2f}, trust: {r.get('trust_score', '?')})"
            for r in results
        ]
        return f"Facts related to {', '.join(entities)}:\n" + "\n".join(lines)

    except Exception as exc:
        return f"Error in compositional reasoning: {exc}"


# ---------------------------------------------------------------------------
# Schema dict for tool registration
# ---------------------------------------------------------------------------

try:
    from plugins.context_engine.lcm.hrr.schemas import MEMORY_TOOL_SCHEMAS
except ImportError:
    MEMORY_TOOL_SCHEMAS: dict[str, Any] = {}  # type: ignore[no-redef]

# Handler dispatch table — maps tool name to handler function
MEMORY_TOOL_HANDLERS: dict[str, Any] = {
    "memory_search": handle_memory_search,
    "memory_pin": handle_memory_pin,
    "memory_expand": handle_memory_expand,
    "memory_forget": handle_memory_forget,
    "memory_reason": handle_memory_reason,
}
