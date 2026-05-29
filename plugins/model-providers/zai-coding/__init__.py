"""ZAI / GLM Coding Plan provider profile."""

from providers import register_provider
from providers.base import ProviderProfile

zai_coding = ProviderProfile(
    name="zai-coding",
    aliases=(
        "zai-coding-plan",
        "z-ai-coding",
        "glm-coding",
        "glm-coding-plan",
        "zhipu-coding",
        "zhipu-coding-plan",
    ),
    env_vars=("GLM_API_KEY", "ZAI_API_KEY", "Z_AI_API_KEY"),
    display_name="Z.AI / GLM Coding Plan",
    description="Z.AI / GLM — Zhipu AI Coding Plan",
    signup_url="https://z.ai/",
    fallback_models=(
        "glm-5-turbo",
        "glm-5.1",
        "glm-4.7",
        "glm-4.5-air",
    ),
    base_url="https://api.z.ai/api/coding/paas/v4",
    default_aux_model="glm-5-turbo",
)

register_provider(zai_coding)
