"""Xiaomi MiMo provider profile."""

import copy
from typing import Any

from providers import register_provider
from providers.base import ProviderProfile

# Content part types that carry image data — MiMo rejects these in tool messages.
_IMAGE_PART_TYPES = frozenset({"image_url", "input_image"})


class XiaomiProfile(ProviderProfile):
    """Xiaomi MiMo — handles API-specific quirks.

    1. MiMo API requires non-empty ``content`` on every assistant message,
       even those carrying only ``tool_calls`` with no natural-language body.
       Without this, replay of tool-call-only assistant turns causes
       HTTP 400 "text is not set".

    2. MiMo rejects ``role: "tool"`` messages whose ``content`` is a list
       containing image parts (e.g. ``{"type": "image_url", ...}``).  The
       ``prepare_messages`` hook proactively downgrades those to plain-text
       strings so the request doesn't 400 on the first attempt.  This
       mirrors the reactive recovery in
       ``run_agent._try_strip_image_parts_from_tool_messages`` but runs
       *before* the API call rather than after a failed round-trip.
    """

    def prepare_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """MiMo-specific message normalization.

        * Pad empty content on assistant messages that carry ``tool_calls``.
        * Downgrade tool messages with list-type content containing image
          parts to plain-text strings.
        """
        prepared = copy.deepcopy(messages)
        for msg in prepared:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")

            # ── Assistant: pad empty content ────────────────────────────
            if role == "assistant" and msg.get("tool_calls"):
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    pass  # already has content
                elif isinstance(content, list) and content:
                    pass  # already has content
                else:
                    msg["content"] = " "

            # ── Tool: downgrade list content with images ───────────────
            elif role == "tool":
                content = msg.get("content")
                if isinstance(content, list):
                    msg["content"] = _tool_list_content_to_str(content)

        return prepared


def _tool_list_content_to_str(content: list) -> str:
    """Convert a tool message's list content to a plain string.

    MiMo rejects list-type tool content in ``role: "tool"`` messages.
    Salvage text parts; discard image parts; fall back to a placeholder
    if nothing survives.
    """
    text_parts: list[str] = []
    has_image = False
    for part in content:
        if not isinstance(part, dict):
            if isinstance(part, str) and part.strip():
                text_parts.append(part.strip())
            continue
        ptype = part.get("type")
        if ptype in _IMAGE_PART_TYPES:
            has_image = True
            continue
        if ptype in {"text", "input_text"}:
            text = str(part.get("text") or "").strip()
            if text:
                text_parts.append(text)

    if text_parts:
        return "\n\n".join(text_parts)
    if has_image:
        return "[image content removed — MiMo does not accept images in tool messages]"
    return ""


xiaomi = XiaomiProfile(
    name="xiaomi",
    aliases=("mimo", "xiaomi-mimo"),
    env_vars=("XIAOMI_API_KEY",),
    base_url="https://api.xiaomimimo.com/v1",
    supports_health_check=False,  # /v1/models returns 401 even with valid key
    supports_vision=True,  # mimo-v2-omni is vision-capable
)

register_provider(xiaomi)
