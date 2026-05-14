"""LCM Engine — manages active context, compaction, and expansion.

This is the core of the unified LCM system, combining:
- ImmutableStore: append-only archive of all messages
- SummaryDag: tracks summary→source mappings for reversibility
- TokenEstimator: accurate token counting
- Summarizer: structured summary generation
- SemanticIndex: optional embedding-based search
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Optional

from plugins.context_engine.lcm.config import LcmConfig
from plugins.context_engine.lcm.dag import MessageId, SummaryDag, SummaryNode
from plugins.context_engine.lcm.format import LcmFormatMixin
from plugins.context_engine.lcm.query import LcmQueryMixin
from plugins.context_engine.lcm.session import LcmSessionMixin
from plugins.context_engine.lcm.store import ImmutableStore
from plugins.context_engine.lcm.summarizer import Summarizer, SummarizerConfig
from plugins.context_engine.lcm.tokens import TokenEstimator, TokenEstimatorConfig
from plugins.context_engine.lcm.semantic import SemanticIndex, SemanticIndexConfig, create_semantic_index

logger = logging.getLogger(__name__)


class CompactionAction(Enum):
    NONE = auto()
    ASYNC = auto()
    BLOCKING = auto()


@dataclass
class ContextEntry:
    kind: str  # "raw" | "summary"
    msg_id: MessageId | None
    node_id: int | None
    message: dict[str, Any]

    @classmethod
    def raw(cls, msg_id: MessageId, message: dict[str, Any]) -> "ContextEntry":
        return cls(kind="raw", msg_id=msg_id, node_id=None, message=message)

    @classmethod
    def summary(cls, node_id: int, message: dict[str, Any]) -> "ContextEntry":
        return cls(kind="summary", msg_id=None, node_id=node_id, message=message)


class LcmEngine(LcmQueryMixin, LcmFormatMixin, LcmSessionMixin):
    """Core context management engine.

    Maintains an append-only store of all ingested messages and a mutable
    active list that may contain raw or summary entries. Compaction
    replaces a contiguous run of raw entries with a single summary entry,
    recording the mapping in the DAG so originals can always be recovered.

    Query, formatting, and session persistence are provided by mixins:
    - LcmQueryMixin: active_messages, active_tokens, search, ...
    - LcmFormatMixin: format_expanded, format_toc, format_budget
    - LcmSessionMixin: rebuild_from_session, to_session_metadata, reset
    """

    def __init__(
        self,
        config: LcmConfig,
        model: str = "",
        provider: str = "",
        context_length: int = 128_000,
    ) -> None:
        self.config = config
        self.model = model
        self.provider = provider

        # Core components
        self.store: ImmutableStore = ImmutableStore()
        self.dag: SummaryDag = SummaryDag()
        self.active: list[ContextEntry] = []

        # State
        self._async_compaction_pending: bool = False
        self._pinned_ids: set[int] = set()
        self._last_summary: Optional[str] = None
        self._compact_lock: threading.Lock = threading.Lock()

        # Token estimator
        token_config = TokenEstimatorConfig(
            model=model,
            provider=provider,
            context_length=context_length,
        )
        self.token_estimator = TokenEstimator(token_config)

        # Summarizer
        summarizer_config = SummarizerConfig(
            model=config.summary_model or model,
        )
        self.summarizer = Summarizer(summarizer_config, self.token_estimator)

        # Semantic index (optional)
        semantic_config = SemanticIndexConfig(enabled=config.semantic_search)
        self.semantic_index = create_semantic_index(semantic_config)

        # DAM retriever (optional — requires numpy)
        self.retriever = None
        self._dam_sync_interval: int = 5
        self._dam_messages_since_sync: int = 0
        try:
            from plugins.context_engine.lcm.dam import DenseAssociativeMemory, MessageEncoder, DAMRetriever
            self.retriever = DAMRetriever(
                net=DenseAssociativeMemory(nv=2048, nh=64),
                enc=MessageEncoder(nv=2048),
            )
        except (ImportError, Exception):
            pass  # numpy not available or DAM init failed

        # HRR persistent store for cross-session knowledge crystallization
        self.hrr_store = None

        # Compaction effectiveness metrics
        self.metrics: dict = self._empty_metrics()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def context_length(self) -> int:
        """Get the context length from the token estimator."""
        return self.token_estimator.context_length

    @context_length.setter
    def context_length(self, value: int):
        """Set the context length."""
        self.token_estimator.context_length = value

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_metrics() -> dict:
        """Return a fresh zeroed metrics dict."""
        return {
            "total_compactions": 0,
            "tokens_saved": 0,
            "tokens_before_total": 0,
            "tokens_after_total": 0,
            "levels": {1: 0, 2: 0, 3: 0},
            "last_compaction_time": None,
            "avg_compression_ratio": 0.0,
        }

    def _crystallize_to_hrr(self, node) -> None:
        """Store compaction summary as a persistent fact in the HRR store.

        Failures are logged and silently swallowed to never block compaction.
        """
        if self.hrr_store is None:
            return
        try:
            self.hrr_store.add_fact(
                content=node.text,
                category="compaction",
                tags=f"level:{node.level},sources:{len(node.source_ids)}",
            )
        except Exception as exc:
            logger.warning("HRR crystallization failed: %s", exc)

    def _record_compaction_metrics(
        self,
        original_tokens: int,
        summary_text: str,
        level: int,
    ) -> None:
        """Update self.metrics after a successful compaction.

        Uses ``len(summary_text) // 4`` as a rough token estimate for the
        summary so we don't pay for expensive counting in the hot path.
        """
        summary_tokens = len(summary_text) // 4

        self.metrics["total_compactions"] += 1
        self.metrics["tokens_before_total"] += original_tokens
        self.metrics["tokens_after_total"] += summary_tokens
        self.metrics["tokens_saved"] += max(0, original_tokens - summary_tokens)
        self.metrics["levels"][level] = self.metrics["levels"].get(level, 0) + 1
        self.metrics["last_compaction_time"] = datetime.now(timezone.utc).isoformat()

        # Running average: avg = total_after / total_before
        before_total = self.metrics["tokens_before_total"]
        after_total = self.metrics["tokens_after_total"]
        self.metrics["avg_compression_ratio"] = (
            after_total / before_total if before_total > 0 else 0.0
        )

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(self, message: dict[str, Any]) -> MessageId:
        """Append a message to the store and active list.

        Returns the stable MessageId assigned by the store.
        After appending, auto-prunes the store if it exceeds max_store_size.
        Periodically syncs the DAM retriever (every _dam_sync_interval messages).
        """
        msg_id = self.store.append(message)
        self.active.append(ContextEntry.raw(msg_id, message))
        self._maybe_prune_store()

        # Auto-sync DAM retriever every N messages
        self._dam_messages_since_sync += 1
        if self.retriever is not None and self._dam_messages_since_sync >= self._dam_sync_interval:
            self._sync_dam()

        return msg_id

    def _sync_dam(self) -> None:
        """Sync the DAM retriever with the current store contents."""
        if self.retriever is None:
            return
        try:
            self.retriever.sync_from_store(self.store)
            self._dam_messages_since_sync = 0
        except Exception as exc:
            logger.warning("DAM sync failed: %s", exc)

    def _referenced_store_ids(self) -> set[int]:
        """Collect all MessageIds referenced by active DAG summaries."""
        referenced: set[int] = set()
        for node in self.dag.nodes:
            referenced.update(self.dag.all_source_ids(node.id))
        return referenced

    def _maybe_prune_store(self) -> int:
        """Prune the store if it exceeds config.max_store_size.

        Protected IDs = pinned + referenced by active summaries.

        Returns the number of messages pruned (0 if no pruning needed).
        """
        if self.store.active_count <= self.config.max_store_size:
            return 0

        keep_ids = self._pinned_ids | self._referenced_store_ids()
        pruned = self.store.prune(keep_ids=keep_ids, max_size=self.config.max_store_size)
        if pruned:
            logger.info(
                "LCM: Auto-pruned %d messages from store (active=%d, limit=%d)",
                pruned, self.store.active_count, self.config.max_store_size,
            )
        return pruned

    # ------------------------------------------------------------------
    # Threshold checking
    # ------------------------------------------------------------------

    def check_thresholds(self, token_budget: int | None = None) -> CompactionAction:
        """Determine whether compaction is needed given the token budget.

        Args:
            token_budget: Optional override for context length. Uses
                         self.context_length if not provided.

        Returns:
            BLOCKING  — above tau_hard, must compact before next turn
            ASYNC     — above tau_soft, should compact in background (once)
            NONE      — below tau_soft, or ASYNC already pending
        """
        budget = token_budget or self.context_length
        usage = self.active_tokens()
        ratio = usage / budget if budget > 0 else 0.0

        if ratio >= self.config.tau_hard:
            logger.info(
                "LCM: Blocking compaction triggered (usage=%d, budget=%d, ratio=%.2f >= tau_hard=%.2f)",
                usage, budget, ratio, self.config.tau_hard,
            )
            return CompactionAction.BLOCKING

        if ratio >= self.config.tau_soft:
            if self._async_compaction_pending:
                return CompactionAction.NONE
            self._async_compaction_pending = True
            logger.info(
                "LCM: Async compaction suggested (usage=%d, budget=%d, ratio=%.2f >= tau_soft=%.2f)",
                usage, budget, ratio, self.config.tau_soft,
            )
            return CompactionAction.ASYNC

        return CompactionAction.NONE

    # ------------------------------------------------------------------
    # Block finding
    # ------------------------------------------------------------------

    def find_compactable_block(self) -> tuple[int, int] | None:
        """Find the oldest contiguous block of raw entries that can be compacted.

        Rules:
        - The tail of protect_last_n entries is never touched.
        - The block must start after any leading summary entries.
        - Tool-call/result pairs are never split: if the candidate end would
          leave a tool-result entry without its preceding tool-call entry,
          the boundary is moved backwards until the pair is intact.
        - Returns None if there is nothing useful to compact.

        Returns (start, end) slice indices into self.active [start, end).
        """
        protect = self.config.protect_last_n
        total = len(self.active)

        if total < protect + 2:
            return None

        compactable_limit = total - protect

        start = 0
        while start < compactable_limit and (
            self.active[start].kind == "summary"
            or self.active[start].msg_id in self._pinned_ids
        ):
            start += 1

        if start >= compactable_limit:
            return None

        end = start
        while end < compactable_limit and self.active[end].msg_id not in self._pinned_ids:
            end += 1

        if end - start < 1:
            return None

        end = self._retreat_from_tool_result(start, end)
        if end is None or end - start < 1:
            return None

        return (start, end)

    @staticmethod
    def _has_tool_calls(message: dict[str, Any]) -> bool:
        """Return True if *message* carries tool-call requests.

        Handles both formats used in this codebase:
        - OpenAI-style: top-level ``tool_calls`` list.
        - Anthropic-style: ``content`` is a list with at least one item whose
          ``type`` is ``"tool_use"``.
        """
        if message.get("tool_calls"):
            return True
        content = message.get("content")
        if isinstance(content, list):
            return any(
                isinstance(block, dict) and block.get("type") == "tool_use"
                for block in content
            )
        return False

    def _retreat_from_tool_result(self, start: int, end: int) -> int | None:
        """Retreat ``end`` so the block does not end mid tool-call/result pair.

        Two cases to guard against:

        1. The block's last entry is a ``tool`` role message whose paired
           ``assistant+tool_calls`` is *not* inside the block (it would be left
           orphaned in the protected tail).  Back off until the pair is either
           both inside the block or both outside.

        2. The block's last entry is an ``assistant`` message that carries
           ``tool_calls`` *and* the first entry of the protected tail (i.e.
           ``self.active[end]``) is a ``tool`` result for that call.  Compacting
           the assistant away would leave an orphan ``tool`` message at the
           start of the tail.  Back off by 1 (and repeat so rule 1 is
           re-checked for the new boundary).
        """
        while end > start:
            last_entry = self.active[end - 1]
            last_msg = last_entry.message

            # Rule 1: block ends with a bare tool-result — its paired
            # tool_calls must also be in the block.
            if last_msg.get("role") == "tool":
                if end - 1 > start:
                    preceding = self.active[end - 2]
                    if self._has_tool_calls(preceding.message):
                        break  # pair is intact inside the block
                end -= 1
                continue

            # Rule 2: block ends with an assistant+tool_calls whose result
            # sits in the protected tail.
            if self._has_tool_calls(last_msg) and end < len(self.active):
                next_entry = self.active[end]
                if next_entry.message.get("role") == "tool":
                    end -= 1
                    continue

            break

        return end if end > start else None

    # ------------------------------------------------------------------
    # Compaction
    # ------------------------------------------------------------------

    def compact(
        self,
        summary_text: str,
        level: int,
        block_start: int,
        block_end: int,
    ) -> SummaryNode:
        """Replace active[block_start:block_end] with a single summary entry.

        The original MessageIds are recorded in the DAG node so they can be
        expanded later. Returns the new SummaryNode.

        This is the low-level compact method. Use compact_block() for
        automatic summarization.
        """
        with self._compact_lock:
            block = self.active[block_start:block_end]
            source_ids: list[MessageId] = [
                e.msg_id for e in block if e.msg_id is not None
            ]

            tokens = self.token_estimator.estimate([e.message for e in block])
            node = self.dag.create_node(
                source_ids=source_ids,
                text=summary_text,
                level=level,
                tokens=tokens,
            )

            summary_message: dict[str, Any] = {
                "role": "user",
                "content": f"[Summary of {len(source_ids)} messages]\n{summary_text}",
                "_lcm_summary": True,
                "_lcm_node_id": node.id,
            }
            summary_entry = ContextEntry.summary(node.id, summary_message)

            self.active[block_start:block_end] = [summary_entry]
            self._async_compaction_pending = False

        self._record_compaction_metrics(tokens, summary_text, level)
        self._crystallize_to_hrr(node)

        logger.info(
            "LCM: Compacted %d messages into summary node %d (~%d tokens saved)",
            len(source_ids), node.id, tokens - len(summary_text) // 4,
        )

        return node

    def compact_block(self, start: int, end: int) -> SummaryNode | None:
        """Compact a block with automatic summarization.

        Uses the Summarizer to generate a structured summary of the block,
        then replaces the block with a single summary entry.

        Returns the new SummaryNode, or None if summarization fails.
        """
        if start >= end:
            logger.warning("LCM: Invalid block range [%d, %d)", start, end)
            return None

        block = self.active[start:end]
        block_messages = [e.message for e in block]

        summary = self.summarizer.summarize(
            block_messages,
            previous_summary=self._last_summary,
        )

        if summary is None:
            logger.warning("LCM: Summarization failed, block not compacted")
            return None

        self._last_summary = summary

        return self.compact(summary, level=1, block_start=start, block_end=end)

    def auto_compact(self) -> SummaryNode | None:
        """Find and compact the oldest compactable block.

        This is the main entry point for automatic compaction triggered
        by threshold checks.

        Returns the new SummaryNode, or None if no block found or
        summarization fails.
        """
        block = self.find_compactable_block()
        if block is None:
            return None
        return self.compact_block(block[0], block[1])

    def async_compact(self, callback=None) -> "threading.Thread | None":
        """Run compaction in a background thread.

        If a compaction is already in progress (``_async_compaction_pending``
        is True), this method returns ``None`` immediately without launching
        a second thread.

        Args:
            callback: Optional callable(SummaryNode | None).  Called with the
                      result when the background thread finishes.  Receives
                      ``None`` if compaction raised an exception.

        Returns:
            The ``threading.Thread`` that was started, or ``None`` if the call
            was skipped because a compaction was already pending.
        """
        with self._compact_lock:
            if self._async_compaction_pending:
                return None
            self._async_compaction_pending = True

        def _worker() -> None:
            try:
                result = self.auto_compact()
                if callback is not None:
                    callback(result)
            except Exception as exc:
                logger.error("Async compaction failed: %s", exc)
                if callback is not None:
                    callback(None)
            finally:
                self._async_compaction_pending = False

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    # ------------------------------------------------------------------
    # Expansion
    # ------------------------------------------------------------------

    def expand(self, msg_ids: list[MessageId]) -> list[tuple[MessageId, dict[str, Any]]]:
        """Return (id, message) tuples for the given MessageIds from the store."""
        return self.store.get_many(msg_ids)

    def expand_summary(self, node_id: int) -> list[tuple[MessageId, dict[str, Any]]]:
        """Recursively expand all source messages for a DAG node.

        Pruned messages are returned as placeholder entries with content
        '[Message pruned from store]' so callers always receive a result
        for every source ID.
        """
        all_ids = self.dag.all_source_ids(node_id)
        result: list[tuple[MessageId, dict[str, Any]]] = []
        for mid in all_ids:
            msg = self.store.get(mid)
            if msg is None:
                placeholder: dict[str, Any] = {
                    "role": "user",
                    "content": "[Message pruned from store]",
                    "_lcm_pruned": True,
                }
                result.append((mid, placeholder))
            else:
                result.append((mid, msg))
        return result

    def focus_summary(self, node_id: int) -> bool:
        """Expand a summary entry back into raw messages in the active list.

        Returns True if successful, False if node not found.
        """
        summary_index: int | None = None
        for i, entry in enumerate(self.active):
            if entry.kind == "summary" and entry.node_id == node_id:
                summary_index = i
                break

        if summary_index is None:
            return False

        pairs = self.expand_summary(node_id)
        if not pairs:
            return False

        expanded_entries = [
            ContextEntry.raw(mid, msg) for mid, msg in pairs
        ]

        self.active[summary_index:summary_index + 1] = expanded_entries

        self._async_compaction_pending = False

        logger.info(
            "LCM: Expanded summary node %d into %d raw messages",
            node_id, len(expanded_entries),
        )

        return True

    # ------------------------------------------------------------------
    # Pinning
    # ------------------------------------------------------------------

    def pin(self, msg_ids: list[int]) -> int:
        """Pin message IDs so they are never compacted.

        Returns the number of newly pinned IDs.
        """
        new_ids = set(msg_ids) - self._pinned_ids

        if len(self._pinned_ids) + len(new_ids) > self.config.max_pinned:
            remaining = self.config.max_pinned - len(self._pinned_ids)
            new_ids = set(list(new_ids)[:remaining])

        self._pinned_ids.update(new_ids)
        return len(new_ids)

    def unpin(self, msg_ids: list[int]) -> int:
        """Unpin message IDs.

        Returns the number of IDs that were unpinned.
        """
        removed = len(self._pinned_ids.intersection(msg_ids))
        self._pinned_ids.difference_update(msg_ids)
        return removed

    def get_pinned(self) -> list[int]:
        """Return sorted list of pinned message IDs."""
        return sorted(self._pinned_ids)
