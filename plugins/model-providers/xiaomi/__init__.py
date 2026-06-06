"""Xiaomi MiMo provider profile."""

from typing import Any
from providers import register_provider
from providers.base import ProviderProfile


class XiaomiProfile(ProviderProfile):
    """Xiaomi MiMo provider — requires list→string flattening for tool content."""

    def prepare_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Flatten list-type tool message content to strings.

        Xiaomi's API rejects tool messages whose ``content`` is a list of
        content parts (e.g. ``[{"type": "text", "text": "..."}]``) with
        ``Param Incorrect - text is not set``.  Some Hermes tools
        (computer_use, vision_analyze, etc.) return structured list content.
        Flatten these to plain strings before sending.
        """
        patched = []
        for msg in messages:
            if msg.get("role") == "tool" and isinstance(msg.get("content"), list):
                parts = []
                for part in msg["content"]:
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        parts.append(part)
                msg = {**msg, "content": "\n".join(parts) if parts else str(msg["content"])}
            patched.append(msg)
        return patched


xiaomi = XiaomiProfile(
    name="xiaomi",
    aliases=("mimo", "xiaomi-mimo"),
    env_vars=("XIAOMI_API_KEY",),
    base_url="https://api.xiaomimimo.com/v1",
    supports_health_check=False,  # /v1/models returns 401 even with valid key
    supports_vision=True,  # mimo-v2-omni is vision-capable
)

register_provider(xiaomi)
