"""Volcengine Ark Coding Plan provider profile."""

from hermes_cli.ark_providers import (
    VOLCENGINE_CODING_DEFAULT_MODEL,
    VOLCENGINE_CODING_PLAN_BASE_URL,
    VOLCENGINE_CODING_PLAN_MODELS,
    VOLCENGINE_CODING_PROVIDER,
    StaticArkProviderProfile,
)
from providers import register_provider

volcengine_coding_plan = StaticArkProviderProfile(
    name=VOLCENGINE_CODING_PROVIDER,
    aliases=(
        "volcengine_coding_plan",
        "volcengine-coding",
        "volcengine_coding",
        "volcano-coding-plan",
        "volcano_coding_plan",
    ),
    display_name="Volcengine Coding Plan",
    description="Volcengine Ark Coding Plan — Subscription Plan",
    signup_url="https://console.volcengine.com/ark",
    env_vars=(
        "VOLCENGINE_CODING_PLAN_API_KEY",
        "VOLCENGINE_CODING_PLAN_BASE_URL",
    ),
    base_url=VOLCENGINE_CODING_PLAN_BASE_URL,
    auth_type="api_key",
    supports_health_check=False,
    fallback_models=VOLCENGINE_CODING_PLAN_MODELS,
    default_aux_model=VOLCENGINE_CODING_DEFAULT_MODEL,
)

register_provider(volcengine_coding_plan)
