"""SmartRouter — token-efficient AI task routing (Hermes bundled plugin).

Classifies incoming messages by task complexity and injects
routing recommendations into the conversation context via the
``pre_llm_call`` hook.

The plugin does NOT modify the model selection directly — it
provides actionable context that the agent can use autonomously.

Installation
------------
This plugin is bundled with Hermes and activates automatically.
No manual installation is needed.

Slash commands
--------------
- ``/route <task>`` — manually classify a task
- ``/route-stats`` — show routing statistics and cost savings

Configuration
-------------
Set ``SMART_ROUTER_CONFIG`` to a YAML file path to customise
tier→model mappings.  Without it, sensible defaults are used:
  T0: deepseek-v4-flash (simple chat)
  T1: qwen3.7-max (analysis)
  T2: qwen3.7-max + reasoning (code)
  T3: claude-sonnet-4 (architecture/security)
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from .smart_router import (
    Classifier,
    ClassificationResult,
    TierLevel,
    estimate_cost,
)

logger = logging.getLogger(__name__)

# ── Global state ──────────────────────────────────────────────────
_classifier: Optional[Classifier] = None
_stats: Dict[str, Any] = {
    "total_routes": 0,
    "tier_counts": {t.name: 0 for t in TierLevel},
    "total_estimated_cost": 0.0,
    "records": [],
}


def _get_classifier() -> Classifier:
    global _classifier
    if _classifier is None:
        _classifier = Classifier()
        logger.info("SmartRouter: initialised with default tier config")
    return _classifier


# ═══════════════════════════════════════════════════════════════════
# Plugin registration
# ═══════════════════════════════════════════════════════════════════

def register(ctx) -> None:
    """Register the SmartRouter plugin with Hermes."""
    logger.info("SmartRouter plugin registering...")

    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_command(
        name="route",
        handler=_cmd_route,
        help="Classify and route a task to the optimal model",
    )
    ctx.register_command(
        name="route-stats",
        handler=_cmd_route_stats,
        help="Show SmartRouter routing statistics and cost savings report",
    )

    logger.info("SmartRouter plugin registered successfully")


# ═══════════════════════════════════════════════════════════════════
# pre_llm_call hook
# ═══════════════════════════════════════════════════════════════════

def on_pre_llm_call(
    session_id: str = "",
    user_message: str = "",
    conversation_history: Any = None,
    is_first_turn: bool = False,
    model: str = "",
    platform: str = "",
    sender_id: str = "",
    **kwargs,
) -> Optional[Dict[str, Any]]:
    """Classify the incoming message and inject routing context.

    Returns a dict with a ``context`` key whose value is appended
    to the current turn's user message.  The agent sees the
    recommendation and can act on it (e.g. delegate to a capable
    sub-agent) or ignore it for trivial responses.
    """
    if not user_message or user_message.startswith("/"):
        return None

    classifier = _get_classifier()
    result = classifier.classify(user_message)

    context = (
        f"[SmartRouter Analysis]\n"
        f"Task complexity: {result.tier.name} (score: {result.score:.0%})\n"
        f"Recommended model: {result.config.model}\n"
        f"Reason: {result.reason}\n"
        f"If this task requires advanced capabilities, consider delegating "
        f"it using /goal with the recommended model."
    )

    logger.info(
        "SmartRouter: [%s] → %s — %s",
        result.tier.name, result.config.model, result.reason,
    )

    # Collect stats
    _record_stats(result)

    return {"context": context}


# ═══════════════════════════════════════════════════════════════════
# Slash commands
# ═══════════════════════════════════════════════════════════════════

_COST_PER_1K = {
    "deepseek-v4-flash": 0.00015,
    "qwen3.7-max": 0.0015,
    "claude-sonnet-4-20250514": 0.003,
}


def _cmd_route(args: str = "") -> str:
    """``/route <task>`` — manually classify a task."""
    if not args.strip():
        return (
            "Usage: /route <your task description>\n"
            "Example: /route 帮我写一个分布式爬虫"
        )

    classifier = _get_classifier()
    result = classifier.classify(args)
    est = estimate_cost(args, classifier)

    lines = [
        "📊 SmartRouter Analysis",
        "",
        f"  Tier:      {result.tier.name}  (score: {result.score:.0%})",
        f"  Model:     {result.config.model}",
        f"  Provider:  {result.config.provider or '(default)'}",
    ]
    if result.config.reasoning_effort:
        lines.append(f"  Reasoning: {result.config.reasoning_effort}")
    lines.extend([
        f"  Reason:    {result.reason}",
        f"  Est. cost: ${est['estimated_cost_usd']:.6f}",
        f"  Savings:   {est.get('savings_vs_t3', 0):.0f}% vs T3",
        f"",
        f"  Message preview: \"{args[:80]}{'…' if len(args) > 80 else ''}\"",
    ])
    return "\n".join(lines)


def _cmd_route_stats(args: str = "") -> str:
    """``/route-stats`` — show routing statistics and cost savings."""
    if _stats["total_routes"] == 0:
        return "📊 No routing data collected yet. Send some messages first."

    s = _stats
    total = s["total_routes"]
    cost = s["total_estimated_cost"]
    cost_if_t3 = total * 0.003  # rough T3 cost per call
    savings = cost_if_t3 - cost
    savings_pct = (savings / cost_if_t3 * 100) if cost_if_t3 > 0 else 0

    lines = [
        "📊 SmartRouter Statistics",
        "",
        f"  Total routes:  {total}",
        f"  Tier distribution:",
    ]
    for tier in sorted(s["tier_counts"].keys()):
        count = s["tier_counts"][tier]
        pct = round(count / total * 100, 1)
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"    {tier:4s}  {bar}  {count:4d} ({pct:.1f}%)")

    lines.extend([
        "",
        f"  Est. cost:      ${cost:.4f}",
        f"  Cost if all T3: ${cost_if_t3:.4f}",
        f"  Savings:        ${savings:.4f} ({savings_pct:.1f}%)",
        "",
        "  Recent routes (last 10, newest first):",
    ])

    for rec in s["records"][-10:][::-1]:
        ts = time.strftime("%H:%M:%S", time.localtime(rec["timestamp"]))
        lines.append(f"    [{ts}] {rec['tier']:4s} → {rec['model']}")
        if rec.get("message_preview"):
            lines.append(f"           \"{rec['message_preview'][:60]}\"")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Stats tracking
# ═══════════════════════════════════════════════════════════════════

def _record_stats(result: ClassificationResult) -> None:
    """Record a routing decision for reporting."""
    s = _stats
    s["total_routes"] += 1
    tier_name = result.tier.name
    s["tier_counts"][tier_name] = s["tier_counts"].get(tier_name, 0) + 1
    cost = _COST_PER_1K.get(result.config.model, 0.001)
    s["total_estimated_cost"] += cost

    s["records"].append({
        "timestamp": time.time(),
        "tier": tier_name,
        "model": result.config.model,
        "provider": result.config.provider,
        "message_preview": result.features.text[:80],
        "reason": result.reason,
        "score": result.score,
    })

    # Cap records at 1000 to avoid unbounded memory
    if len(s["records"]) > 1000:
        s["records"] = s["records"][-500:]
