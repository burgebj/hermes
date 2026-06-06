"""Smart task router for hermes dgx.

Classifies user task complexity from natural language and recommends
the optimal DGX formation — so you don't have to think about which
model to use for each task.

Adapted from NeMoCode's core/router.py (MIT, NVIDIA Corporation).
Key difference: routes to hermes dgx formations and available Ollama/vLLM
endpoints rather than NeMoCode's endpoint registry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Task classification
# ---------------------------------------------------------------------------

class Tier:
    FAST    = "fast"     # Simple lookup / one-liner → smallest fast model
    STANDARD = "standard" # Single-file edit, explanation → capable model
    COMPLEX  = "complex"  # Multi-file, architecture, implementation → best model
    REVIEW   = "review"   # Code review, audit, bug hunt → careful slow model


_FAST_PATTERNS = [
    r"^what\s+(is|are|does)\b",
    r"^how\s+(do|does|to)\b",
    r"^explain\s+\w+$",          # "explain recursion" — one word target
    r"^show\s+me\b",
    r"^list\b",
    r"^where\s+(is|are)\b",
    r"^which\b",
    r"^find\s+\w+$",             # "find function" — one word target
    r"^define\b",
    r"^summarize\b",
]

_COMPLEX_PATTERNS = [
    r"\brefactor\b",
    r"\bmigrat(e|ion)\b",
    r"\barchitect(ure)?\b",
    r"\bredesign\b",
    r"\bimplement\b.*\band\b",   # "implement X and Y"
    r"\bmulti.?file\b",
    r"\bacross\s+(all|multiple|every|the\s+(whole|entire))\b",
    r"\bproject.?wide\b",
    r"\bend.?to.?end\b",
    r"\bfrom\s+scratch\b",
    r"\bcomplete\b.{0,20}\bsystem\b",
    r"\badd\s+\w+\s+(support|integration|backend|service)\b",
]

_REVIEW_PATTERNS = [
    r"\breview\b",
    r"\baudit\b",
    r"\bcheck\s+(for|my|the|this)\b",
    r"\bfind\s+(bugs?|issues?|problems?|errors?|vulnerabilit)\b",
    r"\bcode\s+quality\b",
    r"\bsecurity\b.{0,20}\b(check|review|audit|scan)\b",
    r"\btest\s+coverage\b",
    r"\bperformance\b.{0,20}\b(review|analysis|audit)\b",
]


def classify(text: str) -> str:
    """Classify task complexity. Returns a Tier constant."""
    lower = text.lower().strip()
    words = lower.split()

    # Review intent wins regardless of length
    for pat in _REVIEW_PATTERNS:
        if re.search(pat, lower):
            return Tier.REVIEW

    # Complex patterns win over short-input heuristic
    for pat in _COMPLEX_PATTERNS:
        if re.search(pat, lower):
            return Tier.COMPLEX

    # Very short → fast
    if len(words) <= 4:
        return Tier.FAST

    # Simple question patterns
    for pat in _FAST_PATTERNS:
        if re.search(pat, lower):
            return Tier.FAST

    # Medium length without strong signals → standard
    if len(words) <= 20:
        return Tier.STANDARD

    # Long, detailed requests are likely complex
    return Tier.COMPLEX


# ---------------------------------------------------------------------------
# Formation recommendation
# ---------------------------------------------------------------------------

# Default tier → formation mapping.
# Ordered by preference; first available formation wins.
_TIER_FORMATIONS: Dict[str, list[str]] = {
    Tier.FAST:     ["fast",       "vllm-fast",   "coding"],
    Tier.STANDARD: ["coding",     "vllm-fast",   "flagship"],
    Tier.COMPLEX:  ["vllm-coding","flagship",     "coding"],
    Tier.REVIEW:   ["flagship",   "vllm-coding",  "coding"],
}

_TIER_REASONING: Dict[str, str] = {
    Tier.FAST:    "Simple/short task — fast model avoids wasting large-model capacity.",
    Tier.STANDARD:"Single-concern task — a capable coding model handles it well.",
    Tier.COMPLEX: "Multi-step or cross-cutting task — use the largest available model.",
    Tier.REVIEW:  "Review/audit task — slower, more careful model finds more issues.",
}


@dataclass
class RouteResult:
    tier: str
    formation: str
    model: str
    endpoint: str
    reason: str
    fallback: Optional[str] = None   # next-best formation name
    endpoint_live: Optional[bool] = None  # None = not checked


def recommend(
    text: str,
    formations: Optional[Dict[str, Dict[str, str]]] = None,
    check_endpoints: bool = False,
) -> RouteResult:
    """Recommend a formation for the given task description.

    Args:
        text:             User task description.
        formations:       Available formations dict (from dgx config).
                          Defaults to DEFAULT_FORMATIONS if None.
        check_endpoints:  If True, probe each candidate endpoint before
                          recommending (adds latency).
    Returns:
        RouteResult with the recommended formation and reasoning.
    """
    from plugins.dgx._dgx_config import DEFAULT_FORMATIONS, load_dgx_config

    dgx = load_dgx_config()
    all_formations = dict(DEFAULT_FORMATIONS)
    all_formations.update(dgx.get("formations") or {})
    if formations:
        all_formations.update(formations)

    tier = classify(text)
    candidates = _TIER_FORMATIONS.get(tier, ["coding"])

    chosen = None
    fallback = None

    for name in candidates:
        if name not in all_formations:
            continue
        if chosen is None:
            if check_endpoints:
                live = _probe_formation(name, all_formations[name], dgx)
                if not live:
                    continue
            chosen = name
        elif fallback is None:
            fallback = name

    if chosen is None:
        # Nothing matched — fall back to active endpoint's default model
        chosen = dgx.get("active_endpoint", "ollama")
        spec = {"model": dgx.get("default_model", "unknown"), "endpoint": chosen}
    else:
        spec = all_formations[chosen]

    return RouteResult(
        tier=tier,
        formation=chosen,
        model=spec.get("model", "unknown"),
        endpoint=spec.get("endpoint", "ollama"),
        reason=_TIER_REASONING.get(tier, ""),
        fallback=fallback,
    )


def _probe_formation(name: str, spec: Dict[str, str], dgx: Dict) -> bool:
    """Quick health check for the endpoint backing a formation."""
    from plugins.dgx.cli import _check_endpoint, ollama_base, vllm_base
    from plugins.dgx._dgx_config import litellm_base

    ep = spec.get("endpoint", "ollama")
    node = dgx.get("_active_node", dgx)

    if ep == "ollama":
        ok, _ = _check_endpoint(f"{ollama_base(dgx)}/api/tags", timeout=3)
        return ok
    if ep == "vllm":
        ok, _ = _check_endpoint(f"{vllm_base(dgx)}/v1/models", timeout=3)
        return ok
    if ep == "vllm-32b":
        port = dgx.get("vllm_32b_port", 30881)
        host = node.get("host") or dgx.get("host")
        if not host:
            return False
        ok, _ = _check_endpoint(f"http://{host}:{port}/v1/models", timeout=3)
        return ok
    if ep == "litellm":
        base = litellm_base(dgx)
        if not base:
            return False
        ok, _ = _check_endpoint(f"{base}/health", timeout=3)
        return ok
    return True
