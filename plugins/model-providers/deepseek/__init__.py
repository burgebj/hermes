"""DeepSeek provider profile."""

from typing import Any

from providers import register_provider
from providers.base import ProviderProfile


_EFFORT_MAP = {
    "minimal": "low",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "xhigh",
}


class DeepSeekProfile(ProviderProfile):
    """DeepSeek native API profile.

    Emits ``reasoning_effort`` + ``extra_body.thinking`` per the DeepSeek
    thinking-mode contract (api-docs.deepseek.com/guides/thinking_mode).
    The hermes ``minimal`` effort is remapped to ``low`` because the
    DeepSeek API rejects ``minimal``. When thinking is disabled,
    ``reasoning_effort`` is omitted to avoid the API's documented 400
    conflict ("thinking options type cannot be disabled when
    reasoning_effort is set").
    """

    def build_api_kwargs_extras(
        self,
        *,
        reasoning_config: dict | None = None,
        **context: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not reasoning_config:
            return {}, {}

        thinking_enabled = reasoning_config.get("enabled", True) is not False
        extra_body: dict[str, Any] = {
            "thinking": {
                "type": "enabled" if thinking_enabled else "disabled",
            }
        }

        top_level: dict[str, Any] = {}
        if thinking_enabled:
            raw_effort = (reasoning_config.get("effort") or "high").strip().lower()
            top_level["reasoning_effort"] = _EFFORT_MAP.get(raw_effort, "high")

        return extra_body, top_level


deepseek = DeepSeekProfile(
    name="deepseek",
    aliases=(),
    env_vars=("DEEPSEEK_API_KEY",),
    display_name="DeepSeek",
    description="DeepSeek — native DeepSeek API",
    signup_url="https://platform.deepseek.com/",
    fallback_models=(
        "deepseek-v4-pro",
        "deepseek-v4-flash",
    ),
    base_url="https://api.deepseek.com/v1",
)

register_provider(deepseek)
