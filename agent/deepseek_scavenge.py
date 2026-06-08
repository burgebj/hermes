"""DeepSeek R1 scavenge: extract tool calls leaked into reasoning_content.

DeepSeek R1 thinking models occasionally generate well-formed tool call JSON
inside their `reasoning_content` but fail to emit them as actual `tool_calls`
in the response. This module provides a recovery function that scans
reasoning text for these lost tool calls.

Based on Reasonix (esengine/DeepSeek-Reasonix) scavenge pass.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def _parse_arguments(raw: str) -> dict:
    """Try to parse a JSON arguments block, with brace-balancing fallback."""
    raw = raw.strip()
    if not raw:
        return {}
    # Simple case — valid JSON
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Fallback: count braces and balance. Walk through the string
    # counting braces; when depth returns to 0 we've found the end.
    if raw[0] == "{":
        depth = 0
        end = len(raw)
        for i, ch in enumerate(raw):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end:
            try:
                return json.loads(raw[:end])
            except json.JSONDecodeError:
                pass
    return {}


def scavenge_tool_calls_from_reasoning(
    reasoning: str,
    valid_tool_names: set,
) -> tuple[Optional[List[Any]], str]:
    """Scan reasoning_content for tool calls that R1 forgot to emit."""
    if not reasoning or not valid_tool_names:
        return None, "skipped: empty reasoning or no tool names"

    # Scan for tool-call patterns: {"name": "tool", "arguments": {...}}
    # with brace-balanced argument extraction.
    candidates: list[tuple[str, dict]] = []
    pattern = re.compile(r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*', re.DOTALL)
    for match in pattern.finditer(reasoning):
        name = match.group(1)
        if name not in valid_tool_names:
            continue
        # Find brace-balanced arguments block starting at match end
        start = match.end()
        args_str = _extract_balanced_braces(reasoning, start)
        if args_str is None:
            continue
        args = _parse_arguments(args_str)
        if not isinstance(args, dict):
            continue
        candidates.append((name, args))

    if not candidates:
        return None, "skipped: no valid tool calls found in reasoning"

    # Deduplicate by (name, sorted-json-args)
    seen: set[str] = set()
    unique: list[tuple[str, dict]] = []
    for name, args in candidates:
        key = f"{name}\x00{json.dumps(args, sort_keys=True)}"
        if key not in seen:
            seen.add(key)
            unique.append((name, args))

    # Build ToolCall-like objects (simple namespace with .function)
    class _FauxFunction:
        def __init__(self, name: str, arguments: str):
            self.name = name
            self.arguments = arguments

    class _FauxToolCall:
        def __init__(self, id: str, name: str, arguments: dict):
            self.id = id
            self.function = _FauxFunction(name, json.dumps(arguments))

    tool_calls = [
        _FauxToolCall(f"scavenged_{i:03d}", name, args)
        for i, (name, args) in enumerate(unique)
    ]

    names = ", ".join(f"{n}({len(json.dumps(a))}b)" for n, a in unique)
    msg = f"scavenged {len(unique)} tool(s) from reasoning: {names}"
    return tool_calls, msg


def _extract_balanced_braces(text: str, start: int) -> Optional[str]:
    """Extract a brace-balanced JSON object starting at position *start*.

    Returns the substring (including the opening `{`) or None.
    """
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def deepseek_scavenge_enabled(agent) -> bool:
    """Check whether R1 tool-call scavenge should run for this agent.

    Only active for DeepSeek providers when the ``agent.deepseek_scavenge``
    config key is true.
    """
    provider = getattr(agent, "provider", "").lower()
    if provider not in ("deepseek",):
        return False
    # Check instance-level override first (test/mock path)
    if hasattr(agent, "deepseek_scavenge"):
        return bool(agent.deepseek_scavenge)
    # Fall back to config file
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        return bool(cfg.get("agent", {}).get("deepseek_scavenge", False))
    except Exception:
        return False
