"""Guess matching for the on-this-day-art-trivia skill.

Match levels (in priority order):

1. **Exact normalised match** against any acceptable alias.
2. **Token-Jaccard fuzzy match** above a high threshold (>= 0.75).
3. **Anchor-token match** — the guess contains the strongest topical anchor
   token from the canonical answer (>= 5 chars, not a stopword) AND at least
   one supporting token. Returns ``"close"`` rather than ``"correct"`` so the
   bot can prompt the user to be more specific without revealing the answer.
4. Otherwise ``"wrong"``.

The matcher is intentionally conservative on partial matches: a guess of
"war" should never satisfy "Korean War" without supporting context. We
penalise single-token short guesses heavily.

Optional LLM-judge support is provided as a stub (:func:`maybe_llm_judge`)
that callers may swap in for harder cases — left disabled by default to keep
the package fully offline-capable.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set, Tuple

# Tokens that should never count as evidence of a match by themselves.
_STOPWORDS: Set[str] = {
    "the", "a", "an", "of", "in", "on", "at", "to", "and", "or", "but",
    "for", "with", "by", "is", "was", "were", "be", "been", "being",
    "as", "his", "her", "its", "their", "this", "that", "these", "those",
    "it", "he", "she", "they", "we", "you", "i", "from", "into", "during",
    "before", "after", "above", "below", "up", "down", "out", "off",
    "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "can", "will", "just",
    "don", "should", "now", "him", "us", "them", "us",
}

_NON_WORD = re.compile(r"[^a-z0-9\s]+")
_WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercase, strip diacritics, collapse non-word, keep digits."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    cleaned = _NON_WORD.sub(" ", lowered)
    return _WHITESPACE.sub(" ", cleaned).strip()


def tokens(text: str) -> List[str]:
    norm = normalize(text)
    if not norm:
        return []
    return [t for t in norm.split(" ") if t]


def content_tokens(text: str) -> List[str]:
    """Tokens excluding stopwords and very short tokens."""
    return [t for t in tokens(text) if t not in _STOPWORDS and len(t) >= 3]


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa = set(a)
    sb = set(b)
    if not sa or not sb:
        return 0.0
    inter = sa & sb
    union = sa | sb
    if not union:
        return 0.0
    return len(inter) / len(union)


@dataclass(frozen=True)
class Acceptable:
    alias: str
    alias_normalized: str
    precision_tier: int = 1


@dataclass(frozen=True)
class MatchResult:
    outcome: str  # "correct" | "close" | "wrong"
    matched_alias: Optional[str]
    score: float


def match_guess(
    guess: str,
    acceptable: Sequence[Acceptable],
    *,
    canonical_anchor_tokens: Optional[Sequence[str]] = None,
    fuzzy_threshold: float = 0.75,
    close_threshold: float = 0.45,
) -> MatchResult:
    """Score *guess* against *acceptable* aliases.

    Returns a :class:`MatchResult`. ``canonical_anchor_tokens`` are the rare
    high-information tokens drawn from the canonical answer (computed by
    :func:`build_anchor_tokens`); guesses that hit any anchor without a clean
    fuzzy match are flagged as ``"close"`` so the bot can ask for specificity.
    """
    g_norm = normalize(guess)
    if not g_norm:
        return MatchResult(outcome="wrong", matched_alias=None, score=0.0)

    g_tokens_content = content_tokens(guess)

    best_score = 0.0
    best_alias: Optional[str] = None
    best_tier: int = 99

    for entry in acceptable:
        if g_norm == entry.alias_normalized:
            return MatchResult(outcome="correct", matched_alias=entry.alias, score=1.0)

        a_tokens = content_tokens(entry.alias_normalized)
        score = jaccard(g_tokens_content, a_tokens)
        # Substring-style boost: if a multi-token alias appears in guess
        # contiguously, bump the score.
        if entry.alias_normalized and len(a_tokens) >= 2 and entry.alias_normalized in g_norm:
            score = max(score, 0.9)

        if score > best_score or (score == best_score and entry.precision_tier < best_tier):
            best_score = score
            best_alias = entry.alias
            best_tier = entry.precision_tier

    if best_score >= fuzzy_threshold and best_alias is not None:
        return MatchResult(outcome="correct", matched_alias=best_alias, score=best_score)

    if canonical_anchor_tokens:
        anchor_set = {a for a in canonical_anchor_tokens if len(a) >= 5}
        guess_set = set(g_tokens_content)
        if anchor_set & guess_set and len(g_tokens_content) >= 2:
            return MatchResult(outcome="close", matched_alias=best_alias, score=best_score)

    if best_score >= close_threshold and best_alias is not None and len(g_tokens_content) >= 2:
        return MatchResult(outcome="close", matched_alias=best_alias, score=best_score)

    return MatchResult(outcome="wrong", matched_alias=best_alias, score=best_score)


def build_anchor_tokens(canonical_answer: str, *, top_n: int = 4) -> List[str]:
    """Pick the most distinctive content tokens from the canonical answer.

    Heuristic: longer tokens tend to be proper nouns or rare words. We sort
    by length (descending) then alphabetically for determinism. This keeps
    the matcher dependency-free.
    """
    cands = list({t for t in content_tokens(canonical_answer)})
    cands.sort(key=lambda t: (-len(t), t))
    return cands[:max(1, top_n)]


# --------------------------------------------------------------------------- #
# Optional LLM judge stub
# --------------------------------------------------------------------------- #

def maybe_llm_judge(guess: str, canonical: str) -> Optional[str]:
    """Optional constrained LLM judge. Disabled by default.

    Returns ``"correct"`` / ``"close"`` / ``"wrong"`` if a judge is configured,
    otherwise ``None``. Hooked here so a deployment can add a model call
    without touching the matcher's deterministic path.
    """
    return None
