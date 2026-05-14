from __future__ import annotations
from dataclasses import dataclass


@dataclass
class LcmConfig:
    """Configuration for LCM context management.

    Attributes:
        enabled: Whether LCM is active (default True for new unified system)
        tau_soft: Soft threshold ratio for async compaction (0.0-1.0)
        tau_hard: Hard threshold ratio for blocking compaction (0.0-1.0)
        deterministic_target: Target tokens for deterministic summaries
        protect_last_n: Number of tail messages to always protect
        summary_model: Override model for summarization (empty = use main model)
        max_pinned: Maximum number of messages that can be pinned
        semantic_search: Enable embedding-based search (requires OPENAI_API_KEY)
    """
    enabled: bool = True
    tau_soft: float = 0.50
    tau_hard: float = 0.85
    deterministic_target: int = 512
    protect_last_n: int = 4
    summary_model: str = ""
    max_pinned: int = 20
    semantic_search: bool = False
    max_store_size: int = 1000

    @classmethod
    def from_dict(cls, d: dict) -> "LcmConfig":
        return cls(
            enabled=str(d.get("enabled", True)).lower() in ("true", "1", "yes"),
            tau_soft=float(d.get("tau_soft", 0.50)),
            tau_hard=float(d.get("tau_hard", 0.85)),
            deterministic_target=int(d.get("deterministic_target", 512)),
            protect_last_n=int(d.get("protect_last_n", 4)),
            summary_model=str(d.get("summary_model", "")),
            max_pinned=int(d.get("max_pinned", 20)),
            semantic_search=str(d.get("semantic_search", False)).lower() in ("true", "1", "yes"),
            max_store_size=int(d.get("max_store_size", 1000)),
        )
