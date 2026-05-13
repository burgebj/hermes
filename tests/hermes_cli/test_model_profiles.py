from hermes_cli.model_profiles import (
    detect_openrouter_free_model,
    load_model_profile,
    normalize_profile_name,
    profile_missing_message,
)


def test_normalize_profile_name_accepts_common_aliases():
    assert normalize_profile_name(" Main ") == "main"
    assert normalize_profile_name("escalate_profile") == "escalate-profile"
    assert normalize_profile_name("") == ""


def test_load_model_profile_main_falls_back_to_root_defaults():
    cfg = {
        "model": {
            "default": "owl-alpha",
            "provider": "openrouter",
            "base_url": "https://openrouter.ai/api/v1",
            "api_mode": "openrouter",
        }
    }

    profile = load_model_profile(cfg, "main")

    assert profile is not None
    assert profile.profile == "main"
    assert profile.provider == "openrouter"
    assert profile.model == "owl-alpha"
    assert profile.source == "model.default/provider"


def test_load_model_profile_escalate_requires_explicit_config():
    cfg = {
        "model": {
            "default": "owl-alpha",
            "provider": "openrouter",
        }
    }

    assert load_model_profile(cfg, "escalate") is None
    assert "Set it with `/model escalate <provider/model>`" in profile_missing_message("escalate")


def test_detect_openrouter_free_model_heuristic():
    assert detect_openrouter_free_model("openrouter/whatever:free")
    assert detect_openrouter_free_model("mistralai/mistral-small/free")
    assert not detect_openrouter_free_model("openrouter/owl-alpha")
