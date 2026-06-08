"""Tests for Volcengine and BytePlus Ark provider integrations."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import yaml


VOLCENGINE_CODING_MODELS = [
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
]

BYTEPLUS_CODING_MODELS = [
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
]


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    home.mkdir()
    (home / "config.yaml").write_text("model: old-model\n", encoding="utf-8")
    (home / ".env").write_text("", encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(home))
    for key in (
        "VOLCENGINE_API_KEY",
        "VOLCENGINE_BASE_URL",
        "VOLCENGINE_CODING_PLAN_API_KEY",
        "VOLCENGINE_CODING_PLAN_BASE_URL",
        "BYTEPLUS_API_KEY",
        "BYTEPLUS_BASE_URL",
        "BYTEPLUS_CODING_PLAN_API_KEY",
        "BYTEPLUS_CODING_PLAN_BASE_URL",
        "HERMES_INFERENCE_PROVIDER",
    ):
        monkeypatch.delenv(key, raising=False)
    return home


class TestArkProviderProfiles:
    def test_provider_profiles_load_with_static_catalogs(self):
        from providers import get_provider_profile

        volc = get_provider_profile("volcengine")
        assert volc is not None
        assert volc.display_name == "Volcengine"
        assert volc.base_url == "https://ark.cn-beijing.volces.com/api/v3"
        assert volc.env_vars == ("VOLCENGINE_API_KEY", "VOLCENGINE_BASE_URL")
        assert volc.default_aux_model == "doubao-seed-2-0-pro-260215"
        assert volc.fetch_models(api_key="unused") == ["doubao-seed-2-0-pro-260215"]

        volc_coding = get_provider_profile("volcengine-coding-plan")
        assert volc_coding is not None
        assert volc_coding.default_aux_model == "doubao-seed-2.0-pro"

        byteplus_coding = get_provider_profile("byteplus_coding_plan")
        assert byteplus_coding is not None
        assert byteplus_coding.name == "byteplus-coding-plan"
        assert byteplus_coding.base_url == "https://ark.ap-southeast.bytepluses.com/api/coding/v3"
        assert byteplus_coding.env_vars == (
            "BYTEPLUS_CODING_PLAN_API_KEY",
            "BYTEPLUS_CODING_PLAN_BASE_URL",
        )
        assert byteplus_coding.default_aux_model == "dola-seed-2.0-pro"
        assert byteplus_coding.fetch_models(api_key="unused") == BYTEPLUS_CODING_MODELS

    @pytest.mark.parametrize(
        "alias,canonical",
        [
            ("volcano", "volcengine"),
            ("volcano-engine", "volcengine"),
            ("volcengine_coding_plan", "volcengine-coding-plan"),
            ("byteplus_coding_plan", "byteplus-coding-plan"),
        ],
    )
    def test_aliases_resolve(self, alias, canonical):
        from hermes_cli.auth import resolve_provider

        assert resolve_provider(alias) == canonical

    @pytest.mark.parametrize(
        "requested,canonical,base_url",
        [
            (
                "byteplus",
                "byteplus",
                "https://ark.ap-southeast.bytepluses.com/api/v3",
            ),
            (
                "volcano",
                "volcengine",
                "https://ark.cn-beijing.volces.com/api/v3",
            ),
        ],
    )
    def test_provider_full_resolver_knows_plugin_providers(
        self,
        requested,
        canonical,
        base_url,
    ):
        from hermes_cli.providers import resolve_provider_full

        resolved = resolve_provider_full(requested)

        assert resolved is not None
        assert resolved.id == canonical
        assert resolved.base_url == base_url
        assert resolved.transport == "openai_chat"

    def test_registry_contains_expected_endpoints_and_envs(self):
        from hermes_cli.auth import PROVIDER_REGISTRY

        assert PROVIDER_REGISTRY["volcengine"].inference_base_url == (
            "https://ark.cn-beijing.volces.com/api/v3"
        )
        assert PROVIDER_REGISTRY["volcengine"].api_key_env_vars == ("VOLCENGINE_API_KEY",)
        assert PROVIDER_REGISTRY["volcengine"].base_url_env_var == "VOLCENGINE_BASE_URL"

        assert PROVIDER_REGISTRY["volcengine-coding-plan"].inference_base_url == (
            "https://ark.cn-beijing.volces.com/api/coding/v3"
        )
        assert PROVIDER_REGISTRY["volcengine-coding-plan"].api_key_env_vars == (
            "VOLCENGINE_CODING_PLAN_API_KEY",
        )
        assert (
            PROVIDER_REGISTRY["volcengine-coding-plan"].base_url_env_var
            == "VOLCENGINE_CODING_PLAN_BASE_URL"
        )

    def test_picker_order_and_coding_plan_labels(self):
        from hermes_cli.models import CANONICAL_PROVIDERS

        entries = {entry.slug: entry for entry in CANONICAL_PROVIDERS}
        slugs = [entry.slug for entry in CANONICAL_PROVIDERS]

        assert entries["byteplus-coding-plan"].tui_desc == (
            "BytePlus ModelArk Coding Plan — Subscription Plan"
        )
        assert entries["volcengine-coding-plan"].tui_desc == (
            "Volcengine Ark Coding Plan — Subscription Plan"
        )
        assert slugs.index("volcengine") < slugs.index("volcengine-coding-plan")
        assert slugs.index("volcengine-coding-plan") < slugs.index("custom")


class TestArkProviderCatalogs:
    def test_models_py_catalogs_are_static_and_exact(self):
        from hermes_cli.models import _PROVIDER_MODELS

        assert _PROVIDER_MODELS["volcengine"] == ["doubao-seed-2-0-pro-260215"]
        assert _PROVIDER_MODELS["byteplus"] == ["seed-2-0-pro-260328"]
        assert _PROVIDER_MODELS["volcengine-coding-plan"] == VOLCENGINE_CODING_MODELS
        assert _PROVIDER_MODELS["byteplus-coding-plan"] == BYTEPLUS_CODING_MODELS

    def test_provider_model_ids_does_not_live_probe_ark_providers(self, monkeypatch):
        from hermes_cli.models import provider_model_ids

        def fail_probe(*_args, **_kwargs):
            raise AssertionError("Ark providers must not probe live /models")

        monkeypatch.setattr("hermes_cli.models.fetch_api_models", fail_probe)

        assert provider_model_ids("volcengine-coding-plan") == VOLCENGINE_CODING_MODELS
        assert provider_model_ids("byteplus") == ["seed-2-0-pro-260328"]


class TestArkProviderRuntimeResolution:
    def test_standard_provider_uses_base_url_override(self, monkeypatch):
        from hermes_cli.auth import resolve_api_key_provider_credentials

        monkeypatch.setenv("VOLCENGINE_API_KEY", "volc-key")
        monkeypatch.setenv("VOLCENGINE_BASE_URL", "https://proxy.example.com/api/v3")

        creds = resolve_api_key_provider_credentials("volcengine")

        assert creds["api_key"] == "volc-key"
        assert creds["base_url"] == "https://proxy.example.com/api/v3"

    @pytest.mark.parametrize(
        "provider,standard_env,coding_env,coding_base_url",
        [
            (
                "byteplus-coding-plan",
                "BYTEPLUS_API_KEY",
                "BYTEPLUS_CODING_PLAN_API_KEY",
                "https://ark.ap-southeast.bytepluses.com/api/coding/v3",
            ),
            (
                "volcengine-coding-plan",
                "VOLCENGINE_API_KEY",
                "VOLCENGINE_CODING_PLAN_API_KEY",
                "https://ark.cn-beijing.volces.com/api/coding/v3",
            ),
        ],
    )
    def test_coding_plan_does_not_reuse_standard_api_key(
        self,
        monkeypatch,
        provider,
        standard_env,
        coding_env,
        coding_base_url,
    ):
        from hermes_cli.auth import resolve_api_key_provider_credentials

        monkeypatch.setenv(standard_env, "standard-key")

        creds = resolve_api_key_provider_credentials(provider)

        assert creds["api_key"] == ""
        assert creds["source"] == "default"
        assert creds["base_url"] == coding_base_url

        monkeypatch.setenv(coding_env, "coding-key")
        creds = resolve_api_key_provider_credentials(provider)

        assert creds["api_key"] == "coding-key"
        assert creds["source"] == coding_env
        assert creds["base_url"] == coding_base_url


class TestArkProviderModelFlow:
    def test_active_config_provider_does_not_warn_unknown(
        self,
        isolated_home,
        capsys,
        monkeypatch,
    ):
        from hermes_cli.config import load_config, save_config
        from hermes_cli.main import select_provider_and_model

        cfg = load_config()
        cfg["model"] = {
            "provider": "byteplus",
            "default": "seed-2-0-pro-260328",
        }
        save_config(cfg)

        def choose_leave_unchanged(choices, *, default=0):
            for idx, label in enumerate(choices):
                if label == "Leave unchanged":
                    return idx
            raise AssertionError("Leave unchanged not in provider list")

        monkeypatch.setattr(
            "hermes_cli.main._prompt_provider_choice",
            choose_leave_unchanged,
        )

        select_provider_and_model()

        out = capsys.readouterr().out
        assert "Warning: Unknown provider 'byteplus'" not in out
        assert "Active provider:  BytePlus" in out

    def test_standard_flow_uses_default_model_without_live_probe(self, isolated_home):
        from hermes_cli.config import load_config
        from hermes_cli.main import _model_flow_ark_provider

        with patch(
            "hermes_cli.main._prompt_api_key",
            return_value=("volc-key", False),
        ), patch(
            "hermes_cli.models.fetch_api_models",
            side_effect=AssertionError("must not live-probe Ark models"),
        ), patch(
            "builtins.input",
            return_value="",
        ), patch("hermes_cli.auth.deactivate_provider"):
            _model_flow_ark_provider(load_config(), "volcengine", "old-model")

        cfg = yaml.safe_load((isolated_home / "config.yaml").read_text()) or {}
        model = cfg["model"]
        assert model["provider"] == "volcengine"
        assert model["default"] == "doubao-seed-2-0-pro-260215"
        assert model["base_url"] == "https://ark.cn-beijing.volces.com/api/v3"
        assert "api_mode" not in model

    def test_coding_plan_flow_uses_static_picker_without_live_probe(self, isolated_home):
        from hermes_cli.config import load_config
        from hermes_cli.main import _model_flow_ark_provider

        with patch(
            "hermes_cli.main._prompt_api_key",
            return_value=("coding-key", False),
        ), patch(
            "hermes_cli.models.fetch_api_models",
            side_effect=AssertionError("must not live-probe Ark models"),
        ), patch(
            "hermes_cli.auth._prompt_model_selection",
            return_value="deepseek-v4-flash",
        ) as prompt_model, patch("hermes_cli.auth.deactivate_provider"):
            _model_flow_ark_provider(load_config(), "volcengine-coding-plan", "old-model")

        prompt_model.assert_called_once()
        assert prompt_model.call_args.args[0] == VOLCENGINE_CODING_MODELS

        cfg = yaml.safe_load((isolated_home / "config.yaml").read_text()) or {}
        model = cfg["model"]
        assert model["provider"] == "volcengine-coding-plan"
        assert model["default"] == "deepseek-v4-flash"
        assert model["base_url"] == "https://ark.cn-beijing.volces.com/api/coding/v3"
        assert "api_mode" not in model
