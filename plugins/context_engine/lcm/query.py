"""LCM Query mixin — query and search capabilities for LcmEngine."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from plugins.context_engine.lcm.dag import MessageId


class LcmQueryMixin:
    """Query and search capabilities.

    Expects the host class to provide:
    - self.active: list[ContextEntry]
    - self.store: ImmutableStore
    - self.token_estimator: TokenEstimator
    - self.semantic_index: SemanticIndex
    - self.config: LcmConfig
    """

    # ------------------------------------------------------------------
    # Active context queries
    # ------------------------------------------------------------------

    def active_messages(self) -> list[dict[str, Any]]:
        """Return message dicts for all active entries, in order."""
        return [entry.message for entry in self.active]

    def active_tokens(self) -> int:
        """Estimate tokens currently in the active context."""
        return self.token_estimator.estimate(self.active_messages())

    def active_token_breakdown(self) -> dict[str, int]:
        """Return token breakdown for active context."""
        raw_entries = [e for e in self.active if e.kind == "raw"]
        summary_entries = [e for e in self.active if e.kind == "summary"]

        raw_tokens = self.token_estimator.estimate([e.message for e in raw_entries])
        summary_tokens = self.token_estimator.estimate([e.message for e in summary_entries])

        return {
            "total": raw_tokens + summary_tokens,
            "raw": raw_tokens,
            "summary": summary_tokens,
            "raw_count": len(raw_entries),
            "summary_count": len(summary_entries),
        }

    # ------------------------------------------------------------------
    # Store search
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> list[tuple[int, dict[str, Any]]]:
        """Search messages in the store.

        Priority order:
        1. Semantic index (if enabled and available)
        2. DAM retriever (if initialized and has indexed messages)
        3. Keyword fallback

        Returns list of (msg_id, message) tuples.
        """
        if self.semantic_index.is_available() and self.config.semantic_search:
            ids = self.semantic_index.search(query, k=limit)
            if ids:
                return self.store.get_many(ids)

        retriever = getattr(self, "retriever", None)
        if retriever is not None and retriever._pattern_cache:
            scores = retriever.search(query, limit=limit)
            if scores:
                ids = [msg_id for msg_id, _ in scores]
                results = self.store.get_many(ids)
                if results:
                    return results

        return self._keyword_search(query, limit)

    def _keyword_search(self, query: str, limit: int) -> list[tuple[int, dict[str, Any]]]:
        """Fallback keyword search."""
        query_lower = query.lower()
        results: list[tuple[int, dict[str, Any]]] = []

        for msg_id in range(len(self.store)):
            msg = self.store.get(msg_id)
            if msg is None:
                continue
            content = str(msg.get("content", "") or "")
            if query_lower in content.lower():
                results.append((msg_id, msg))
                if len(results) >= limit:
                    break

        return results

    def build_semantic_index(self) -> bool:
        """Build the semantic index for the store.

        Returns True if indexing succeeded.
        """
        if not self.semantic_index.is_available():
            return False
        return self.semantic_index.index(self.store)
