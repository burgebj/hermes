"""Fireworks AI provider profile.

Fireworks is a fast inference platform for open-source and proprietary models.
API is OpenAI-compatible (Chat Completions) with structured output support
and function calling.

Serverless models accessible with a standard API key:
  - accounts/fireworks/models/deepseek-v4-pro
  - accounts/fireworks/models/kimi-k2p6  (Kimi K2.6)
  - accounts/fireworks/models/kimi-k2p5  (Kimi K2.5)
  - accounts/fireworks/models/glm-5p1    (GLM 5.1)
  - accounts/fireworks/models/gpt-oss-120b
  - accounts/fireworks/models/minimax-m2p7  (MiniMax M2.7)
  - accounts/fireworks/models/qwen3p6-plus  (Qwen3.6 Plus)
"""

from __future__ import annotations

from providers import register_provider
from providers.base import ProviderProfile


class FireworksProfile(ProviderProfile):
    """Fireworks AI — OpenAI-compatible Chat Completions provider."""


fireworks = FireworksProfile(
    name="fireworks",
    aliases=("fireworks-ai",),
    env_vars=("FIREWORKS_API_KEY",),
    base_url="https://api.fireworks.ai/inference/v1",
    fallback_models=(
        "accounts/fireworks/models/deepseek-v4-pro",
        "accounts/fireworks/models/kimi-k2p6",
        "accounts/fireworks/models/kimi-k2p5",
        "accounts/fireworks/models/glm-5p1",
        "accounts/fireworks/models/gpt-oss-120b",
        "accounts/fireworks/models/minimax-m2p7",
        "accounts/fireworks/models/qwen3p6-plus",
    ),
)

register_provider(fireworks)
