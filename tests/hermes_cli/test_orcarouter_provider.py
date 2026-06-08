"""Unit tests for the OrcaRouter provider plugin.

Mirrors the structure of tests/hermes_cli/test_arcee_provider.py and the
Novita test block in test_api_key_providers.py: verifies the plugin loads,
aliases resolve, the API-key auto-extension picks it up, and the reasoning
protocol dispatcher routes per upstream family correctly.

No live network calls — fetch_models is exercised via httpx mock-style
urllib stubbing, and reasoning dispatch is pure-function.
"""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch

import pytest


def _orcarouter_profile():
    from providers import get_provider_profile

    return get_provider_profile("orcarouter")


class TestOrcaRouterProfile:
    def test_profile_loads(self):
        profile = _orcarouter_profile()
        assert profile is not None
        assert profile.name == "orcarouter"
        assert profile.display_name == "OrcaRouter"
        assert profile.base_url == "https://api.orcarouter.ai/v1"
        assert profile.models_url == "https://api.orcarouter.ai/v1/models"
        assert profile.api_mode == "chat_completions"
        assert profile.auth_type == "api_key"

    def test_aliases(self):
        profile = _orcarouter_profile()
        assert "orca" in profile.aliases

    def test_env_vars(self):
        profile = _orcarouter_profile()
        assert "ORCAROUTER_API_KEY" in profile.env_vars
        assert "ORCAROUTER_BASE_URL" in profile.env_vars

    def test_attribution_headers(self):
        profile = _orcarouter_profile()
        assert profile.default_headers.get("HTTP-Referer", "").startswith(
            "https://hermes-agent.nousresearch.com"
        )
        assert profile.default_headers.get("X-Title") == "hermes-agent"

    def test_fallback_models_include_auto_first(self):
        profile = _orcarouter_profile()
        assert profile.fallback_models[0] == "orcarouter/auto"
        # Spot-check a few flagship models from the curated list.
        assert any("openai/" in m for m in profile.fallback_models)
        assert any("anthropic/" in m for m in profile.fallback_models)

    def test_aux_model_set(self):
        profile = _orcarouter_profile()
        assert profile.default_aux_model  # non-empty

    def test_signup_url_points_to_console(self):
        profile = _orcarouter_profile()
        assert "orcarouter.ai" in profile.signup_url


class TestOrcaRouterAliasResolution:
    def test_alias_resolves(self):
        from hermes_cli.auth import resolve_provider

        assert resolve_provider("orca") == "orcarouter"
        assert resolve_provider("orcarouter") == "orcarouter"


class TestOrcaRouterAutoRegistry:
    def test_provider_registry_entry_auto_extended(self):
        # The plugin should be picked up by the auto-extension block in
        # hermes_cli/auth.py:459-491. No explicit ProviderConfig was added.
        from hermes_cli.auth import PROVIDER_REGISTRY

        assert "orcarouter" in PROVIDER_REGISTRY
        pconfig = PROVIDER_REGISTRY["orcarouter"]
        assert pconfig.id == "orcarouter"
        assert pconfig.inference_base_url == "https://api.orcarouter.ai/v1"
        assert "ORCAROUTER_API_KEY" in pconfig.api_key_env_vars
        assert pconfig.base_url_env_var == "ORCAROUTER_BASE_URL"

    def test_alias_registered_in_registry(self):
        from hermes_cli.auth import PROVIDER_REGISTRY

        assert "orca" in PROVIDER_REGISTRY

    def test_canonical_providers_entry(self):
        from hermes_cli.models import CANONICAL_PROVIDERS

        slugs = {p.slug for p in CANONICAL_PROVIDERS}
        assert "orcarouter" in slugs


class TestOrcaRouterFetchModels:
    def test_fetch_models_uses_bearer_auth(self, monkeypatch):
        # Reset the module-level cache so this test is hermetic. The plugin
        # is loaded via spec_from_file_location under a synthetic module name,
        # so we reach it through sys.modules after triggering discovery.
        import sys

        from providers import list_providers

        list_providers()
        plugin = sys.modules["plugins.model_providers.orcarouter"]
        monkeypatch.setattr(plugin, "_CACHE", None)

        captured = {}

        class _FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def read(self):
                return self._payload

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def _fake_urlopen(req, timeout):  # noqa: ARG001
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            body = json.dumps({"data": [{"id": "openai/gpt-5"}, {"id": "anthropic/claude-opus-4.7"}]}).encode()
            return _FakeResponse(body)

        with patch("urllib.request.urlopen", _fake_urlopen):
            models = plugin.orcarouter.fetch_models(api_key="sk-orca-test")

        assert models == ["openai/gpt-5", "anthropic/claude-opus-4.7"]
        assert captured["url"] == "https://api.orcarouter.ai/v1/models"
        # urllib's Request capitalizes header names — match leniently.
        header_keys = {k.lower() for k in captured["headers"]}
        assert "authorization" in header_keys
        auth_val = next(v for k, v in captured["headers"].items() if k.lower() == "authorization")
        assert auth_val == "Bearer sk-orca-test"

    def test_fetch_models_caches(self, monkeypatch):
        import sys

        from providers import list_providers

        list_providers()
        plugin = sys.modules["plugins.model_providers.orcarouter"]
        monkeypatch.setattr(plugin, "_CACHE", None)

        call_count = {"n": 0}

        class _FakeResponse:
            def read(self):
                return json.dumps({"data": [{"id": "openai/gpt-5"}]}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def _fake_urlopen(req, timeout):  # noqa: ARG001
            call_count["n"] += 1
            return _FakeResponse()

        with patch("urllib.request.urlopen", _fake_urlopen):
            plugin.orcarouter.fetch_models(api_key="sk-orca-test")
            plugin.orcarouter.fetch_models(api_key="sk-orca-test")

        assert call_count["n"] == 1  # Second call served from cache.


class TestOrcaRouterReasoningDispatch:
    """Per-vendor reasoning protocol — the core OrcaRouter quirk."""

    def _dispatch(self, *, model, reasoning_config=None, supports_reasoning=True, max_tokens=None):
        profile = _orcarouter_profile()
        return profile.build_api_kwargs_extras(
            reasoning_config=reasoning_config,
            supports_reasoning=supports_reasoning,
            model=model,
            max_tokens=max_tokens,
        )

    def test_openai_uses_top_level_reasoning_effort(self):
        extra_body, top_level = self._dispatch(
            model="openai/gpt-5", reasoning_config={"enabled": True, "effort": "high"}
        )
        assert extra_body == {}
        assert top_level == {"reasoning_effort": "high"}

    def test_gemini_uses_top_level_reasoning_effort(self):
        _, top_level = self._dispatch(
            model="google/gemini-3-flash-preview",
            reasoning_config={"enabled": True, "effort": "medium"},
        )
        assert top_level == {"reasoning_effort": "medium"}

    def test_grok_uses_top_level_reasoning_effort(self):
        _, top_level = self._dispatch(
            model="grok/grok-4.3", reasoning_config={"enabled": True, "effort": "low"}
        )
        assert top_level == {"reasoning_effort": "low"}

    def test_anthropic_uses_thinking_block(self):
        extra_body, top_level = self._dispatch(
            model="anthropic/claude-opus-4.7",
            reasoning_config={"enabled": True, "effort": "high"},
            max_tokens=32000,
        )
        assert extra_body == {}
        assert top_level == {
            "thinking": {"type": "enabled", "budget_tokens": 8192}
        }

    def test_anthropic_budget_capped_below_max_tokens(self):
        # If max_tokens is small, budget_tokens must stay strictly below it.
        _, top_level = self._dispatch(
            model="anthropic/claude-opus-4.7",
            reasoning_config={"enabled": True, "effort": "high"},
            max_tokens=2000,
        )
        budget = top_level["thinking"]["budget_tokens"]
        assert 1024 <= budget < 2000

    def test_anthropic_low_effort_uses_min_budget(self):
        _, top_level = self._dispatch(
            model="anthropic/claude-opus-4.7",
            reasoning_config={"enabled": True, "effort": "low"},
            max_tokens=32000,
        )
        assert top_level["thinking"]["budget_tokens"] == 1024

    def test_deepseek_reasoner_skipped(self):
        # DeepSeek r1 / reasoner reasons by default and rejects reasoning_effort.
        extra_body, top_level = self._dispatch(
            model="deepseek/deepseek-reasoner",
            reasoning_config={"enabled": True, "effort": "high"},
        )
        assert extra_body == {}
        assert top_level == {}

    def test_deepseek_r1_skipped(self):
        _, top_level = self._dispatch(
            model="deepseek/deepseek-r1",
            reasoning_config={"enabled": True, "effort": "high"},
        )
        assert top_level == {}

    def test_deepseek_chat_uses_top_level_effort(self):
        # Plain deepseek-chat / v4-pro etc. accept reasoning_effort.
        _, top_level = self._dispatch(
            model="deepseek/deepseek-v4-pro", reasoning_config={"enabled": True, "effort": "medium"}
        )
        assert top_level == {"reasoning_effort": "medium"}

    def test_supports_reasoning_false_returns_empty(self):
        extra_body, top_level = self._dispatch(
            model="openai/gpt-5",
            reasoning_config={"enabled": True, "effort": "high"},
            supports_reasoning=False,
        )
        assert extra_body == {} and top_level == {}

    def test_explicit_disable_skips(self):
        _, top_level = self._dispatch(
            model="openai/gpt-5", reasoning_config={"enabled": False, "effort": "high"}
        )
        assert top_level == {}

    def test_unknown_effort_falls_back_to_medium(self):
        _, top_level = self._dispatch(
            model="openai/gpt-5", reasoning_config={"enabled": True, "effort": "bogus"}
        )
        assert top_level == {"reasoning_effort": "medium"}

    def test_no_reasoning_config_falls_back_to_medium(self):
        _, top_level = self._dispatch(
            model="openai/gpt-5", reasoning_config=None
        )
        assert top_level == {"reasoning_effort": "medium"}


@pytest.mark.parametrize(
    "model,expected_field",
    [
        ("openai/gpt-5", "reasoning_effort"),
        ("openai/gpt-5.5", "reasoning_effort"),
        ("anthropic/claude-opus-4.7", "thinking"),
        ("anthropic/claude-sonnet-4.6", "thinking"),
        ("google/gemini-3-flash-preview", "reasoning_effort"),
        ("grok/grok-4.3", "reasoning_effort"),
        ("qwen/qwen3.6-flash", "reasoning_effort"),
        ("kimi/kimi-k2.6", "reasoning_effort"),
    ],
)
def test_reasoning_field_matrix(model, expected_field):
    profile = _orcarouter_profile()
    _, top_level = profile.build_api_kwargs_extras(
        reasoning_config={"enabled": True, "effort": "medium"},
        supports_reasoning=True,
        model=model,
        max_tokens=32000,
    )
    assert expected_field in top_level
