"""Alibaba Cloud DashScope provider profile."""

from providers import register_provider
from providers.base import ProviderProfile


class AlibabaProfile(ProviderProfile):
    """Alibaba Cloud DashScope — serves Qwen via OpenAI-compatible wire with
    envelope-layout cache_control support (matches the pi-mono 'alibaba'
    cacheControlFormat). Without markers, qwen3.6-plus reports 0% cached
    tokens and burns subscription quota on every turn.
    """

    def cache_strategy_for(self, model: str):
        from agent.prompt_cache_strategy import (
            AnthropicInlineCacheStrategy,
            NoCacheStrategy,
        )
        if "qwen" in (model or "").lower():
            return AnthropicInlineCacheStrategy(layout="envelope")
        return NoCacheStrategy()


alibaba = AlibabaProfile(
    name="alibaba",
    aliases=("dashscope", "alibaba-cloud", "qwen-dashscope"),
    env_vars=("DASHSCOPE_API_KEY",),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

register_provider(alibaba)
