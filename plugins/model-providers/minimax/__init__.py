"""MiniMax provider profiles (international + China).

Both use anthropic_messages api_mode — their inference_base_url
ends with /anthropic which triggers auto-detection to anthropic_messages.
"""

from providers import register_provider
from providers.base import ProviderProfile


class MiniMaxProfile(ProviderProfile):
    """MiniMax variants serve Claude AND their own MiniMax-M2.x models
    on the native Anthropic wire format, with documented cache_control
    support (0.1× read pricing, 5-minute TTL).
    Docs: https://platform.minimax.io/docs/api-reference/anthropic-api-compatible-cache
    """

    def cache_strategy_for(self, model: str):
        from agent.prompt_cache_strategy import (
            AnthropicInlineCacheStrategy,
            NoCacheStrategy,
        )
        m = (model or "").lower()
        if "claude" in m or "minimax" in m:
            return AnthropicInlineCacheStrategy(layout="native")
        return NoCacheStrategy()


minimax = MiniMaxProfile(
    name="minimax",
    aliases=("mini-max",),
    api_mode="anthropic_messages",
    env_vars=("MINIMAX_API_KEY",),
    base_url="https://api.minimax.io/anthropic",
    auth_type="api_key",
    default_aux_model="MiniMax-M2.7",
)

minimax_cn = MiniMaxProfile(
    name="minimax-cn",
    aliases=("minimax-china", "minimax_cn"),
    api_mode="anthropic_messages",
    env_vars=("MINIMAX_CN_API_KEY",),
    base_url="https://api.minimaxi.com/anthropic",
    auth_type="api_key",
    default_aux_model="MiniMax-M2.7",
)

minimax_oauth = MiniMaxProfile(
    name="minimax-oauth",
    aliases=("minimax_oauth", "minimax-oauth-io"),
    api_mode="anthropic_messages",
    display_name="MiniMax (OAuth)",
    description="MiniMax via OAuth browser flow — no API key required",
    signup_url="https://api.minimax.io/",
    env_vars=(),  # OAuth — tokens in auth.json, not env
    base_url="https://api.minimax.io/anthropic",
    auth_type="oauth_external",
    default_aux_model="MiniMax-M2.7-highspeed",
)

register_provider(minimax)
register_provider(minimax_cn)
register_provider(minimax_oauth)
