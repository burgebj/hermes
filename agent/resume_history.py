"""Helpers for building API-safe history at session-resume boundaries."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


_TOOL_TURN_PLACEHOLDER = (
    "[Prior tool activity omitted from resumed context.]"
)


def sanitize_resumed_conversation_history(
    history: Iterable[Dict[str, Any]] | None,
) -> List[Dict[str, Any]]:
    """Return a resume-safe conversation history for the next model turn.

    Stored transcripts intentionally preserve raw assistant tool calls, tool
    results, reasoning fields, and provider metadata for replay/debugging. A
    session resume is a context boundary: those private/internal payloads must
    not be fed back to the model as if the previous tool loop were still live.

    The projection keeps only user-visible dialogue:
    * user messages keep role/content;
    * assistant messages keep role/content only;
    * tool/function/debug/meta/system/developer messages are dropped;
    * assistant tool-call turns with no visible content become a short benign
      assistant placeholder so surrounding user turns do not collapse together.
    """
    if not history:
        return []

    sanitized: List[Dict[str, Any]] = []
    for msg in history:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role")
        if role == "user":
            sanitized.append({"role": "user", "content": msg.get("content", "")})
            continue

        if role != "assistant":
            continue

        content = msg.get("content", "")
        if content is None:
            content = ""

        has_visible_content = False
        if isinstance(content, str):
            has_visible_content = bool(content.strip())
        elif isinstance(content, list):
            has_visible_content = any(
                isinstance(part, dict)
                and part.get("type") == "text"
                and isinstance(part.get("text"), str)
                and part.get("text", "").strip()
                for part in content
            )
        else:
            has_visible_content = bool(content)

        if not has_visible_content:
            if msg.get("tool_calls"):
                content = _TOOL_TURN_PLACEHOLDER
            else:
                continue

        assistant_msg = {"role": "assistant", "content": content}
        if sanitized and sanitized[-1].get("role") == "assistant":
            previous = sanitized[-1]
            if previous.get("content") == _TOOL_TURN_PLACEHOLDER:
                sanitized[-1] = assistant_msg
            elif content == _TOOL_TURN_PLACEHOLDER:
                continue
            elif isinstance(previous.get("content"), str) and isinstance(content, str):
                previous["content"] = previous["content"].rstrip() + "\n\n" + content.lstrip()
            else:
                sanitized.append(assistant_msg)
            continue

        sanitized.append(assistant_msg)

    return sanitized
