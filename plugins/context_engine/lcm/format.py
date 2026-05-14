"""LCM Format mixin — formatting capabilities for LcmEngine."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from plugins.context_engine.lcm.dag import MessageId


class LcmFormatMixin:
    """Formatting capabilities.

    Expects the host class to provide:
    - self.active: list[ContextEntry]
    - self.context_length: int
    - self.expand(msg_ids) -> list[tuple[MessageId, dict]]
    - self.active_token_breakdown() -> dict
    - self.get_pinned() -> list[int]
    - self.metrics: dict  (for format_metrics)
    """

    def format_expanded(self, msg_ids: list) -> str:
        """Format expanded messages as '[msg N] role: content' lines."""
        pairs = self.expand(msg_ids)
        lines: list[str] = []
        for mid, msg in pairs:
            role = msg.get("role", "unknown")
            content = str(msg.get("content", "") or "")
            lines.append(f"[msg {mid}] {role}: {content}")
        return "\n".join(lines)

    def format_toc(self) -> str:
        """Format a table of contents of the active context."""
        if not self.active:
            return "Active context is empty."

        lines = ["Conversation Timeline:"]
        for i, entry in enumerate(self.active):
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

    def format_budget(self) -> str:
        """Format a token budget summary."""
        breakdown = self.active_token_breakdown()

        lines = [
            "LCM Context Budget:",
            f"  Active entries : {len(self.active)} ({breakdown['raw_count']} raw, {breakdown['summary_count']} summaries)",
            f"  Active tokens  : ~{breakdown['total']}",
            f"  Raw tokens     : ~{breakdown['raw']}",
            f"  Summary tokens : ~{breakdown['summary']}",
            f"  Store total    : {len(self.store)} messages (immutable)",
            f"  Context limit  : {self.context_length:,} tokens",
            f"  Pinned IDs     : {self.get_pinned() or 'none'}",
        ]
        return "\n".join(lines)

    def format_metrics(self) -> str:
        """Format a human-readable summary of compaction effectiveness metrics."""
        m = self.metrics
        total = m["total_compactions"]
        saved = m["tokens_saved"]
        before = m["tokens_before_total"]
        after = m["tokens_after_total"]
        avg_ratio = m.get("avg_compression_ratio", 0.0)
        last_time = m["last_compaction_time"] or "never"
        levels: dict = m.get("levels", {})

        level_parts = ", ".join(
            f"L{lvl}={count}" for lvl, count in sorted(levels.items())
        )

        compression_pct = round((1.0 - avg_ratio) * 100, 1) if before > 0 else 0.0

        lines = [
            "LCM Compaction Metrics:",
            f"  Total compactions    : {total}",
            f"  Tokens before (total): {before}",
            f"  Tokens after  (total): {after}",
            f"  Tokens saved  (total): {saved}",
            f"  Avg compression      : {compression_pct}% ({avg_ratio:.3f} ratio)",
            f"  Level distribution   : {level_parts or 'none'}",
            f"  Last compaction      : {last_time}",
        ]
        return "\n".join(lines)
