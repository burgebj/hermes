"""Nebius Token Factory provider profile."""

from providers import register_provider
from providers.base import ProviderProfile


nebius_token_factory = ProviderProfile(
    name="nebius-token-factory",
    aliases=(
        "nebius",
        "nebius-tokenfactory",
        "nebius-tf",
        "token-factory",
        "tokenfactory",
    ),
    display_name="Nebius Token Factory",
    description="Nebius Token Factory — OpenAI-compatible inference",
    signup_url="https://tokenfactory.nebius.com/",
    env_vars=(
        "NEBIUS_API_KEY",
        "NEBIUS_TOKEN_FACTORY_API_KEY",
        "NEBIUS_BASE_URL",
    ),
    base_url="https://api.tokenfactory.nebius.com/v1",
    models_url="https://api.tokenfactory.nebius.com/v1/models",
    auth_type="api_key",
    default_aux_model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    fallback_models=(
        "Qwen/Qwen3.5-397B-A17B-fast",
        "deepseek-ai/DeepSeek-V4-Pro",
        "zai-org/GLM-5.1",
        "moonshotai/Kimi-K2.5-fast",
        "MiniMaxAI/MiniMax-M2.5-fast",
        "deepseek-ai/DeepSeek-V3.2-fast",
        "NousResearch/Hermes-4-70B",
        "openai/gpt-oss-120b-fast",
        "meta-llama/Llama-3.3-70B-Instruct",
    ),
)

register_provider(nebius_token_factory)
