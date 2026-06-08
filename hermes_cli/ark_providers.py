"""Shared definitions for Volcengine and BytePlus Ark providers."""

from __future__ import annotations

from providers.base import ProviderProfile

VOLCENGINE_PROVIDER = "volcengine"
VOLCENGINE_CODING_PROVIDER = "volcengine-coding-plan"
BYTEPLUS_PROVIDER = "byteplus"
BYTEPLUS_CODING_PROVIDER = "byteplus-coding-plan"

VOLCENGINE_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
VOLCENGINE_CODING_PLAN_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
BYTEPLUS_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"
BYTEPLUS_CODING_PLAN_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/coding/v3"

VOLCENGINE_DEFAULT_MODEL = "doubao-seed-2-0-pro-260215"
VOLCENGINE_CODING_DEFAULT_MODEL = "doubao-seed-2.0-pro"
BYTEPLUS_DEFAULT_MODEL = "seed-2-0-pro-260328"
BYTEPLUS_CODING_DEFAULT_MODEL = "dola-seed-2.0-pro"

VOLCENGINE_STANDARD_MODELS = (VOLCENGINE_DEFAULT_MODEL,)
BYTEPLUS_STANDARD_MODELS = (BYTEPLUS_DEFAULT_MODEL,)

VOLCENGINE_CODING_PLAN_MODELS = (
    "doubao-seed-code",
    "deepseek-v3.2",
    "doubao-seed-2.0-code",
    "doubao-seed-2.0-pro",
    "doubao-seed-2.0-lite",
    "minimax-m2.7",
    "glm-5.1",
    "kimi-k2.6",
    "deepseek-v4-pro",
    "deepseek-v4-flash",
)

BYTEPLUS_CODING_PLAN_MODELS = (
    "bytedance-seed-code",
    "glm-4.7",
    "gpt-oss-120b",
    "kimi-k2.5",
    "dola-seed-2.0-pro",
    "dola-seed-2.0-lite",
    "dola-seed-2.0-code",
    "glm-5.1",
    "deepseek-v4-pro",
    "deepseek-v4-flash",
)

ARK_PROVIDER_IDS = (
    VOLCENGINE_PROVIDER,
    VOLCENGINE_CODING_PROVIDER,
    BYTEPLUS_PROVIDER,
    BYTEPLUS_CODING_PROVIDER,
)

ARK_CODING_PLAN_PROVIDER_IDS = frozenset(
    (VOLCENGINE_CODING_PROVIDER, BYTEPLUS_CODING_PROVIDER)
)
ARK_STANDARD_PROVIDER_IDS = frozenset((VOLCENGINE_PROVIDER, BYTEPLUS_PROVIDER))

ARK_PROVIDER_MODELS = {
    VOLCENGINE_PROVIDER: VOLCENGINE_STANDARD_MODELS,
    VOLCENGINE_CODING_PROVIDER: VOLCENGINE_CODING_PLAN_MODELS,
    BYTEPLUS_PROVIDER: BYTEPLUS_STANDARD_MODELS,
    BYTEPLUS_CODING_PROVIDER: BYTEPLUS_CODING_PLAN_MODELS,
}

ARK_PROVIDER_DEFAULT_MODELS = {
    VOLCENGINE_PROVIDER: VOLCENGINE_DEFAULT_MODEL,
    VOLCENGINE_CODING_PROVIDER: VOLCENGINE_CODING_DEFAULT_MODEL,
    BYTEPLUS_PROVIDER: BYTEPLUS_DEFAULT_MODEL,
    BYTEPLUS_CODING_PROVIDER: BYTEPLUS_CODING_DEFAULT_MODEL,
}


class StaticArkProviderProfile(ProviderProfile):
    """Provider profile whose model catalog is intentionally static.

    Ark's standard and coding-plan endpoints are OpenAI-compatible for chat
    completions, but Hermes should not live-probe ``/models`` for these
    integrations. Standard API-key users can enter any model ID manually, and
    coding-plan users see the curated subscription model list.
    """

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        del api_key, timeout
        return list(self.fallback_models)


def ark_provider_models(provider_id: str) -> list[str]:
    """Return the static model list for an Ark provider."""

    return list(ARK_PROVIDER_MODELS.get(provider_id, ()))


def ark_provider_default_model(provider_id: str) -> str:
    """Return the default model for an Ark provider."""

    return ARK_PROVIDER_DEFAULT_MODELS.get(provider_id, "")


def is_ark_provider(provider_id: str) -> bool:
    """Return true when *provider_id* is one of Hermes' Ark providers."""

    return provider_id in ARK_PROVIDER_IDS
