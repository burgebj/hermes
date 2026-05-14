"""Session primer — inject cross-session knowledge into fresh LCM context."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plugins.context_engine.lcm.engine import LcmEngine

logger = logging.getLogger(__name__)


def prime_from_hrr(
    engine: "LcmEngine",
    hrr_store,
    topic: str,
    max_facts: int = 5,
) -> int:
    """Query HRR store for relevant facts and inject into active context.

    Inserts a single primer message at position 0 of engine.active so the
    model sees cross-session knowledge before any current-turn messages.

    Returns the number of facts injected (0 if store is None/empty/error).
    """
    if hrr_store is None or not topic.strip():
        return 0

    try:
        from plugins.context_engine.lcm.hrr.retrieval import FactRetriever
        retriever = FactRetriever(store=hrr_store)
        results = retriever.search(topic, limit=max_facts)
    except Exception as exc:
        logger.warning("Session primer failed to query HRR store: %s", exc)
        return 0

    if not results:
        return 0

    facts_text = "\n".join(
        f"- {r['content']} (trust: {r.get('trust_score', '?')})"
        for r in results
    )

    primer_message = {
        "role": "user",
        "content": f"[Prior Knowledge from previous sessions]\n{facts_text}",
        "_lcm_primer": True,
    }

    from plugins.context_engine.lcm.engine import ContextEntry
    msg_id = engine.store.append(primer_message)
    engine.active.insert(0, ContextEntry.raw(msg_id, primer_message))

    logger.info("Session primer: injected %d facts from HRR store", len(results))
    return len(results)
