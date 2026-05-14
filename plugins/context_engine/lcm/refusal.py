"""LLM refusal pattern detection for LCM summaries."""
from __future__ import annotations

REFUSAL_PATTERNS: list[str] = [
    "i cannot", "i can't", "i'm unable", "i am unable",
    "i apologize", "i'm sorry", "as an ai", "as a language model",
    "unable to help", "cannot assist", "can't assist",
    "cannot fulfill", "can't fulfill", "not able to provide",
    "unable to provide", "i won't", "i will not",
    "against my guidelines", "violates my",
    "i'm not comfortable", "i am not comfortable",
]

def contains_refusal(text: str) -> bool:
    """Check if text contains an LLM refusal pattern."""
    if not text:
        return False
    lower = text.lower()
    return any(pattern in lower for pattern in REFUSAL_PATTERNS)
