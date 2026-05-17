"""Token-count selection helpers for gateway context hygiene."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence


@dataclass(frozen=True)
class HygieneTokenDecision:
    tokens: int
    source: str


def choose_hygiene_token_count(
    history: Sequence[Any],
    *,
    stored_prompt_tokens: int | None,
    estimate_tokens: Callable[[Sequence[Any]], int],
    implausible_multiplier: int = 8,
    implausible_extra_tokens: int = 50_000,
) -> HygieneTokenDecision:
    """Prefer API token counts unless they are implausibly larger than history."""
    estimated = max(0, int(estimate_tokens(history) or 0))
    stored = max(0, int(stored_prompt_tokens or 0))
    if stored <= 0:
        return HygieneTokenDecision(tokens=estimated, source="estimated")

    plausible_ceiling = max(
        estimated * implausible_multiplier,
        estimated + implausible_extra_tokens,
    )
    if estimated > 0 and stored > plausible_ceiling:
        return HygieneTokenDecision(
            tokens=estimated,
            source="estimated_stored_implausible",
        )
    return HygieneTokenDecision(tokens=stored, source="actual")
