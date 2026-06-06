"""Smoke tests for the Stability video gen plugin — load & register surface."""

from __future__ import annotations

import pytest

from agent import video_gen_registry


@pytest.fixture(autouse=True)
def _reset_registry():
    video_gen_registry._reset_for_tests()
    yield
    video_gen_registry._reset_for_tests()


def test_stability_provider_registers():
    from plugins.video_gen.stability import StabilityProvider

    provider = StabilityProvider()
    video_gen_registry.register_provider(provider)

    assert video_gen_registry.get_provider("stability") is provider
    assert provider.display_name == "Stability AI"
    assert provider.default_model() == "svd-xt"


def test_stability_capabilities_image_only():
    """SVD is image-to-video only."""
    from plugins.video_gen.stability import StabilityProvider

    caps = StabilityProvider().capabilities()
    assert caps["modalities"] == ["image"]
    assert caps["max_reference_images"] == 0


def test_stability_models():
    from plugins.video_gen.stability import StabilityProvider

    models = StabilityProvider().list_models()
    assert len(models) == 2
    model_ids = {m["id"] for m in models}
    assert "svd" in model_ids
    assert "svd-xt" in model_ids


def test_stability_unavailable_without_key(monkeypatch):
    from plugins.video_gen.stability import StabilityProvider

    monkeypatch.delenv("STABILITY_API_KEY", raising=False)
    assert StabilityProvider().is_available() is False


def test_stability_generate_requires_key(monkeypatch):
    from plugins.video_gen.stability import StabilityProvider

    monkeypatch.delenv("STABILITY_API_KEY", raising=False)
    result = StabilityProvider().generate("animate", image_url="https://example.com/img.jpg")
    assert result["success"] is False
    assert result["error_type"] == "missing_api_key"


def test_stability_requires_image(monkeypatch):
    """SVD should reject text-only generation."""
    from plugins.video_gen.stability import StabilityProvider

    monkeypatch.setenv("STABILITY_API_KEY", "fake-key")
    result = StabilityProvider().generate("a beautiful scene")
    assert result["success"] is False
    assert result["error_type"] == "modality_unsupported"
    assert "image_url" in result["error"].lower()


def test_stability_setup_schema():
    from plugins.video_gen.stability import StabilityProvider

    schema = StabilityProvider().get_setup_schema()
    assert schema["name"] == "Stability AI"
    assert schema["badge"] == "paid"
    assert schema["env_vars"][0]["key"] == "STABILITY_API_KEY"
