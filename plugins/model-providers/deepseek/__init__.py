"""DeepSeek provider profile.

DeepSeek V4+ thinking mode uses ``extra_body.thinking`` + top-level
``reasoning_effort`` (same protocol as Kimi/Z.AI, NOT OpenRouter's
``extra_body.reasoning``).
"""

from typing import Any

from providers import register_provider
from providers.base import ProviderProfile


class DeepSeekProfile(ProviderProfile):
    """DeepSeek — extra_body.thinking + reasoning_effort (native protocol)."""

    def build_api_kwargs_extras(
        self, *, reasoning_config: dict | None = None, **context
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        extra_body: dict[str, Any] = {}
        top_level: dict[str, Any] = {}

        if not reasoning_config or not isinstance(reasoning_config, dict):
            # No config → thinking enabled, default effort (high for DeepSeek)
            extra_body["thinking"] = {"type": "enabled"}
            top_level["reasoning_effort"] = "high"
            return extra_body, top_level

        enabled = reasoning_config.get("enabled", True)
        if enabled is False:
            extra_body["thinking"] = {"type": "disabled"}
            return extra_body, top_level

        # Enabled — map Hermes effort levels to DeepSeek's accepted values.
        # DeepSeek only accepts "high" and "max"; low/medium → high, xhigh → max.
        extra_body["thinking"] = {"type": "enabled"}
        effort = (reasoning_config.get("effort") or "").strip().lower()
        if effort in ("low", "medium", "high"):
            top_level["reasoning_effort"] = "high"
        elif effort == "xhigh":
            top_level["reasoning_effort"] = "max"
        else:
            top_level["reasoning_effort"] = "high"

        return extra_body, top_level


deepseek = DeepSeekProfile(
    name="deepseek",
    aliases=("deepseek-chat",),
    env_vars=("DEEPSEEK_API_KEY",),
    display_name="DeepSeek",
    description="DeepSeek — native DeepSeek API",
    signup_url="https://platform.deepseek.com/",
    fallback_models=(
        "deepseek-chat",
        "deepseek-reasoner",
    ),
    base_url="https://api.deepseek.com/v1",
)

register_provider(deepseek)
