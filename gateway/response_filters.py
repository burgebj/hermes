from __future__ import annotations

import re
from typing import Optional

# Canonical, harness-emitted silence token. The agent emits this verbatim to
# mean "this turn was processed, deliver nothing". It is a first-class control
# token (cf. OpenClaw's SILENT_REPLY_TOKEN), NOT just a placeholder the model
# stumbled into. Kept here as the single source of truth so prompt guidance,
# the agent loop, and delivery suppression all agree on the same string.
SILENT_REPLY_TOKEN = "NO_REPLY"

LIVE_GATEWAY_SILENT_MARKERS = frozenset(
    {
        # Explicit canonical silence token (and its underscore/space-folded
        # form). Listed verbatim so the contract is self-documenting and does
        # not depend on _canonicalize_live_gateway_response() happening to map
        # "NO_REPLY" -> "no reply". If the canonicalizer ever changes, the
        # canonical token must still be suppressed — that invariant is locked
        # by tests/gateway/test_live_silent_responses.py.
        "no reply",
        # Placeholder markers a model may emit when it decides to stay silent
        # but still produces visible filler instead of the canonical token.
        "[silent]",
        "silent",
        "no message",
        "no response",
        "no response generated",
        "empty",
    }
)


def _unwrap_live_gateway_response_text(text: str) -> str:
    normalized = text
    for _ in range(6):
        updated = normalized.strip()
        changed = False

        for wrapper in ("**", "__", "~~", "`"):
            if updated.startswith(wrapper) and updated.endswith(wrapper):
                inner = updated[len(wrapper) : -len(wrapper)].strip()
                if inner:
                    normalized = inner
                    changed = True
                    break
        if changed:
            continue

        for left, right in (("(", ")"), ("[", "]"), ("{", "}"), ('"', '"'), ("'", "'")):
            if updated.startswith(left) and updated.endswith(right):
                inner = updated[len(left) : -len(right)].strip()
                if inner:
                    normalized = inner
                    changed = True
                    break

        if not changed:
            normalized = updated
            break

    return normalized


def _canonicalize_live_gateway_response(text: str) -> str:
    normalized = _unwrap_live_gateway_response_text(text)
    return re.sub(r"[\s\-_]+", " ", normalized).strip(" .!?:;").casefold()


def normalize_live_gateway_response(
    response: Optional[str], *, failed: bool = False
) -> str:
    """Suppress placeholder silence markers before live message delivery."""
    if response is None:
        return ""

    text = str(response).strip()
    if not text or failed:
        return text

    if _canonicalize_live_gateway_response(text) in LIVE_GATEWAY_SILENT_MARKERS:
        return ""

    return text
