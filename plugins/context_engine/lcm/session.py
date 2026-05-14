"""LCM Session mixin — session persistence for LcmEngine."""
from __future__ import annotations

import logging
from typing import Any

from plugins.context_engine.lcm.config import LcmConfig
from plugins.context_engine.lcm.store import ImmutableStore
from plugins.context_engine.lcm.dag import SummaryDag

logger = logging.getLogger(__name__)


class LcmSessionMixin:
    """Session persistence capabilities.

    Expects the host class to provide:
    - self.store: ImmutableStore
    - self.dag: SummaryDag
    - self.active: list[ContextEntry]
    - self._pinned_ids: set[int]
    - self._async_compaction_pending: bool
    - self._last_summary: Optional[str]
    - self.summarizer: Summarizer (has .reset())
    - self.semantic_index: SemanticIndex (has .clear())
    - cls(config, model, provider, context_length) constructor
    """

    @classmethod
    def rebuild_from_session(
        cls,
        session_data: dict,
        config: LcmConfig,
        model: str = "",
        provider: str = "",
        context_length: int = 128_000,
    ) -> "LcmSessionMixin":
        """Reconstruct engine state from persisted session data.

        Two modes:
        - With ``lcm.original_messages``: the full store backup is restored
          first; raw entries in the active list reference those store positions.
        - Without it (legacy or no prior compaction): each raw message in the
          active list is appended to the store directly.
        """
        # Import here to avoid circular imports; ContextEntry lives in engine
        from plugins.context_engine.lcm.engine import ContextEntry

        engine = cls(config, model, provider, context_length)
        messages = session_data.get("messages") or []
        # Tolerate "lcm": null (JSON null → Python None) and missing key
        lcm_meta = session_data.get("lcm") or {}
        summaries = lcm_meta.get("summaries") or []
        original_messages = lcm_meta.get("original_messages") or []

        for msg in original_messages:
            engine.store.append(msg)

        for s in sorted(summaries, key=lambda x: x.get("node_id", 0)):
            engine.dag.create_node(
                source_ids=s.get("source_ids", []),
                text=s.get("text", ""),
                level=s.get("level", 1),
                tokens=s.get("tokens", 0),
                children=s.get("child_summaries", []),
            )

        if original_messages:
            # Compute suffix-offset fallback for legacy sessions (no _lcm_raw_id)
            raw_in_active = sum(1 for m in messages if not m.get("_lcm_summary"))
            next_raw_id = len(engine.store) - raw_in_active
        else:
            next_raw_id = 0

        for msg in messages:
            if msg.get("_lcm_summary"):
                node_id = msg.get("_lcm_node_id", 0)
                engine.active.append(ContextEntry.summary(node_id, msg))
            else:
                if original_messages:
                    # Prefer the embedded id written by active_messages_for_session().
                    # Fall back to the suffix-offset formula for sessions saved before
                    # this fix was deployed (backward compatibility).
                    if "_lcm_raw_id" in msg:
                        msg_id = msg["_lcm_raw_id"]
                    else:
                        msg_id = next_raw_id
                        next_raw_id += 1
                else:
                    msg_id = engine.store.append(msg)
                # Strip the internal annotation before storing in active (it's
                # only meaningful for serialization, not at runtime).
                clean_msg = {k: v for k, v in msg.items() if k != "_lcm_raw_id"}
                engine.active.append(ContextEntry.raw(msg_id, clean_msg))

        pinned_ids = lcm_meta.get("pinned") or []
        store_size = len(engine.store)
        valid_pins = {pid for pid in pinned_ids if 0 <= pid < store_size}
        dropped_pins = set(pinned_ids) - valid_pins
        if dropped_pins:
            logger.warning(
                "LCM: Dropped %d out-of-range pinned ID(s) during rebuild: %s",
                len(dropped_pins),
                sorted(dropped_pins),
            )
        engine._pinned_ids = valid_pins

        engine._last_summary = lcm_meta.get("last_summary")

        # Restore metrics if present
        saved_metrics = lcm_meta.get("metrics")
        if saved_metrics:
            # Import here to avoid circular imports; _empty_metrics lives in engine
            from plugins.context_engine.lcm.engine import LcmEngine as _LcmEngine
            base = _LcmEngine._empty_metrics()
            base.update(saved_metrics)
            # Ensure levels dict has all expected keys
            for lvl in (1, 2, 3):
                base["levels"].setdefault(lvl, 0)
            engine.metrics = base

        # Restore DAM retriever state to avoid re-indexing on restart
        saved_dam = lcm_meta.get("dam") or {}
        if saved_dam and getattr(engine, "retriever", None) is not None:
            last_indexed_id = saved_dam.get("last_indexed_id", 0)
            engine.retriever._last_indexed_id = last_indexed_id

        logger.info(
            "LCM: Rebuilt from session: %d messages, %d summaries, %d pinned",
            len(engine.active), len(engine.dag.nodes), len(engine._pinned_ids),
        )

        return engine

    def active_messages_for_session(self) -> list[dict]:
        """Return active message dicts annotated for session persistence.

        Raw entries receive a ``_lcm_raw_id`` key so their store position can
        be restored exactly on rebuild, even when the active list is
        non-contiguous (e.g. after ``focus_summary`` pulls expanded entries
        back in).  Summary entries already carry ``_lcm_summary`` /
        ``_lcm_node_id`` markers set at compaction time and are returned as-is.
        """
        result = []
        for entry in self.active:
            if entry.kind == "raw" and entry.msg_id is not None:
                # Shallow-copy to avoid mutating the live message dict
                annotated = dict(entry.message)
                annotated["_lcm_raw_id"] = entry.msg_id
                result.append(annotated)
            else:
                result.append(entry.message)
        return result

    def to_session_metadata(self) -> dict:
        """Serialize engine state for session JSON persistence."""
        summaries = []
        for node in self.dag.nodes:
            summaries.append({
                "node_id": node.id,
                "source_ids": node.source_ids,
                "child_summaries": node.child_summaries,
                "text": node.text,
                "level": node.level,
                "tokens": node.tokens,
            })

        original_messages = []
        for i in range(len(self.store)):
            msg = self.store.get(i)
            if msg is not None:
                original_messages.append(msg)

        # Persist DAM retriever state so rebuild can skip re-indexing
        dam_state: dict = {}
        retriever = getattr(self, "retriever", None)
        if retriever is not None:
            dam_state = {
                "last_indexed_id": retriever._last_indexed_id,
                "n_patterns_trained": retriever.net.n_patterns_trained,
            }

        return {
            "summaries": summaries,
            "original_messages": original_messages,
            "store_size": len(self.store),
            "pinned": sorted(self._pinned_ids),
            "last_summary": self._last_summary,
            "metrics": dict(self.metrics),
            "dam": dam_state,
        }

    def reset(self):
        """Reset engine state for a new session."""
        self.store = ImmutableStore()
        self.dag = SummaryDag()
        self.active = []
        self._async_compaction_pending = False
        self._pinned_ids = set()
        self._last_summary = None
        self.summarizer.reset()
        self.semantic_index.clear()
        # Import here to avoid circular imports; _empty_metrics lives in engine
        from plugins.context_engine.lcm.engine import LcmEngine as _LcmEngine
        self.metrics = _LcmEngine._empty_metrics()
