from __future__ import annotations

import re
from typing import Any

class LanguageGuardError(ValueError):
    """Raised when proposed communication overclaims or lacks evidence."""

BLOCKED_WHEN_NOT_EXECUTED = {"fixed", "shipped", "resolved", "completed", "deployed"}


def validate_message(text: str, *, status: str, evidence_links: list[dict[str, Any]] | None = None, team_visible: bool = False) -> bool:
    evidence_links = evidence_links or []
    lower = text.lower()
    if status != "executed":
        for term in BLOCKED_WHEN_NOT_EXECUTED:
            if re.search(rf"\b{re.escape(term)}\b", lower):
                raise LanguageGuardError(f"Message claims '{term}' before work is executed")
    if team_visible and not evidence_links:
        raise LanguageGuardError("Team-visible messages require evidence links")
    if status == "executed" and any(re.search(rf"\b{re.escape(t)}\b", lower) for t in BLOCKED_WHEN_NOT_EXECUTED) and not evidence_links:
        raise LanguageGuardError("Completion claims require evidence links")
    return True
