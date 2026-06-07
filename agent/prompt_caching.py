"""Anthropic prompt caching strategy.

Single layout: ``system_and_3``. 4 cache_control breakpoints — system
prompt + last 3 non-system messages, all at the same TTL (5m or 1h).
Reduces input token costs by ~75% on multi-turn conversations within a
single session.

Pure functions -- no class state, no AIAgent dependency.
"""

import copy
from typing import Any, Dict, List


def _apply_cache_marker(msg: dict, cache_marker: dict, native_anthropic: bool = False) -> None:
    """Add cache_control to a single message, handling all format variations."""
    role = msg.get("role", "")
    content = msg.get("content")

    if role == "tool":
        if native_anthropic:
            msg["cache_control"] = cache_marker
        return

    if content is None or content == "":
        msg["cache_control"] = cache_marker
        return

    if isinstance(content, str):
        msg["content"] = [
            {"type": "text", "text": content, "cache_control": cache_marker}
        ]
        return

    if isinstance(content, list) and content:
        last = content[-1]
        if isinstance(last, dict):
            last["cache_control"] = cache_marker


def _build_marker(ttl: str) -> Dict[str, str]:
    """Build a cache_control marker dict for the given TTL ('5m' or '1h')."""
    marker: Dict[str, str] = {"type": "ephemeral"}
    if ttl == "1h":
        marker["ttl"] = "1h"
    return marker


def apply_anthropic_cache_control(
    api_messages: List[Dict[str, Any]],
    cache_ttl: str = "5m",
    native_anthropic: bool = False,
    reserved_breakpoints: int = 0,
) -> List[Dict[str, Any]]:
    """Apply system_and_3 caching strategy to messages for Anthropic models.

    Places up to 4 cache_control breakpoints: system prompt + last N non-system
    messages, all at the same TTL.  When *reserved_breakpoints* > 0, that many
    slots are held back for other cacheable sections (e.g. tools), reducing the
    number of message breakpoints accordingly.

    Returns:
        Deep copy of messages with cache_control breakpoints injected.
    """
    messages = copy.deepcopy(api_messages)
    if not messages:
        return messages

    marker = _build_marker(cache_ttl)

    breakpoints_used = 0

    if messages[0].get("role") == "system":
        _apply_cache_marker(messages[0], marker, native_anthropic=native_anthropic)
        breakpoints_used += 1

    remaining = max(0, 4 - breakpoints_used - reserved_breakpoints)
    if remaining:
        non_sys = [i for i in range(len(messages)) if messages[i].get("role") != "system"]
        for idx in non_sys[-remaining:]:
            _apply_cache_marker(messages[idx], marker, native_anthropic=native_anthropic)

    return messages


def apply_tool_cache_control(
    tools: List[Dict[str, Any]],
    cache_ttl: str = "5m",
) -> List[Dict[str, Any]]:
    """Add cache_control to the last tool definition for Anthropic caching.

    Anthropic caches everything up to and including the marked tool.  Marking
    the last tool in the array caches the entire tools schema.  Uses one of
    the 4 available cache breakpoints.

    Returns a shallow copy of the list with the last tool dict deep-copied
    and marked; other tools are shared references (schemas are read-only).
    """
    if not tools:
        return tools

    result = list(tools)
    last = copy.deepcopy(result[-1])
    last["cache_control"] = _build_marker(cache_ttl)
    result[-1] = last
    return result
