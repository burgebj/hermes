"""OrcaRouter provider profile.

OrcaRouter is an OpenAI-compatible meta-router across 150+ upstream models with
an adaptive routing strategy (LinUCB contextual bandit). It behaves like
OpenRouter for transport but uses per-vendor native reasoning fields instead of
OpenRouter's nested ``reasoning`` block.

API: https://api.orcarouter.ai/v1 (Bearer auth, ``sk-orca-...`` keys)
Docs: https://docs.orcarouter.ai
"""

from __future__ import annotations

import logging
from typing import Any

from providers import register_provider
from providers.base import ProviderProfile

logger = logging.getLogger(__name__)

_CACHE: list[str] | None = None

# effort → Anthropic thinking budget_tokens (must be >= 1024 and < max_tokens).
_ANTHROPIC_BUDGET = {"minimal": 1024, "low": 1024, "medium": 4096, "high": 8192}


def _is_anthropic_model(model: str) -> bool:
    return model.startswith("anthropic/")


def _is_deepseek_reasoner(model: str) -> bool:
    # DeepSeek r1 / reasoner: reasons by default, rejects reasoning_effort.
    return model.startswith("deepseek/") and (
        "reasoner" in model or "r1" in model
    )


class OrcaRouterProfile(ProviderProfile):
    """OrcaRouter meta-router — per-vendor reasoning, attribution headers."""

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        """Bearer-authenticated /v1/models with module-level cache."""
        global _CACHE  # noqa: PLW0603
        if _CACHE is not None:
            return _CACHE
        try:
            result = super().fetch_models(api_key=api_key, timeout=timeout)
            if result is not None:
                _CACHE = result
            return result
        except Exception as exc:
            logger.debug("fetch_models(orcarouter): %s", exc)
            return None

    def build_api_kwargs_extras(
        self,
        *,
        reasoning_config: dict | None = None,
        supports_reasoning: bool = False,
        model: str | None = None,
        max_tokens: int | None = None,
        **context: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Route reasoning config to the right field for each upstream family.

        OrcaRouter passes reasoning through to upstream providers using each
        vendor's native field shape — there is no OpenRouter-style nested
        ``reasoning`` block. Three branches:

        - ``anthropic/*``: top-level ``thinking={"type":"enabled","budget_tokens":N}``
        - ``deepseek/*reasoner*`` / ``deepseek/*r1*``: no reasoning field
          (model reasons by default, rejects ``reasoning_effort``)
        - everything else (OpenAI, Gemini, Grok, Qwen, Kimi, …): top-level
          ``reasoning_effort: "high|medium|low|minimal"``
        """
        if not supports_reasoning or not model:
            return {}, {}

        cfg = reasoning_config if isinstance(reasoning_config, dict) else {}
        if cfg.get("enabled") is False:
            return {}, {}

        if _is_deepseek_reasoner(model):
            return {}, {}

        effort = (cfg.get("effort") or "").strip().lower() or "medium"

        if _is_anthropic_model(model):
            budget = _ANTHROPIC_BUDGET.get(effort, 4096)
            # Budget must stay strictly below max_tokens. Cap with a small safety margin.
            if max_tokens and budget >= max_tokens:
                budget = max(1024, max_tokens - 256)
            return {}, {"thinking": {"type": "enabled", "budget_tokens": budget}}

        if effort not in {"minimal", "low", "medium", "high"}:
            effort = "medium"
        return {}, {"reasoning_effort": effort}


orcarouter = OrcaRouterProfile(
    name="orcarouter",
    aliases=("orca",),
    env_vars=("ORCAROUTER_API_KEY", "ORCAROUTER_BASE_URL"),
    display_name="OrcaRouter",
    description="OrcaRouter — adaptive routing across 150+ models",
    signup_url="https://www.orcarouter.ai/console",
    base_url="https://api.orcarouter.ai/v1",
    models_url="https://api.orcarouter.ai/v1/models",
    auth_type="api_key",
    default_headers={
        "HTTP-Referer": "https://hermes-agent.nousresearch.com/",
        "X-Title": "hermes-agent",
    },
    default_aux_model="google/gemini-3-flash-preview",
    fallback_models=(
        "orcarouter/auto",
        "openai/gpt-5.5",
        "anthropic/claude-opus-4.7",
        "google/gemini-3-flash-preview",
        "deepseek/deepseek-v4-pro",
        "grok/grok-4.3",
    ),
)

register_provider(orcarouter)
