"""Tests for Bedrock Opus sampling params guard (issue #36151)."""

import pytest

from agent.bedrock_adapter import (
    _bedrock_forbids_sampling_params,
    _BEDROCK_NO_SAMPLING_PARAMS_SUBSTRINGS,
    build_converse_kwargs,
)


class TestBedrockForbidsSamplingParams:
    """Tests for _bedrock_forbids_sampling_params()."""

    def test_opus_4_7_variants(self):
        """All Opus 4.7 variants reject sampling params."""
        for model_id in [
            "anthropic.claude-opus-4-7",
            "anthropic.claude-opus-4.7",
            "us.anthropic.claude-opus-4-7",
            "us.anthropic.claude-opus-4.7",
            "global.anthropic.claude-opus-4-7",
            "global.anthropic.claude-opus-4.7",
        ]:
            assert _bedrock_forbids_sampling_params(model_id), f"{model_id} should forbid sampling params"

    def test_opus_4_8_variants(self):
        """All Opus 4.8 variants reject sampling params."""
        for model_id in [
            "anthropic.claude-opus-4-8",
            "anthropic.claude-opus-4.8",
            "us.anthropic.claude-opus-4-8",
            "us.anthropic.claude-opus-4.8",
            "global.anthropic.claude-opus-4-8",
            "global.anthropic.claude-opus-4.8",
        ]:
            assert _bedrock_forbids_sampling_params(model_id), f"{model_id} should forbid sampling params"

    def test_opus_4_6_allows_sampling_params(self):
        """Opus 4.6 and earlier models allow sampling params."""
        for model_id in [
            "anthropic.claude-opus-4-6",
            "anthropic.claude-opus-4-5",
            "anthropic.claude-opus-4",
            "anthropic.claude-3-5-sonnet",
            "anthropic.claude-3-haiku",
        ]:
            assert not _bedrock_forbids_sampling_params(model_id), f"{model_id} should allow sampling params"

    def test_non_anthropic_models_allows_sampling_params(self):
        """Non-Anthropic models allow sampling params."""
        for model_id in [
            "meta.llama-3-70b",
            "mistral.mistral-large-2402",
            "amazon.titan-text-premier-v1:0:8k",
        ]:
            assert not _bedrock_forbids_sampling_params(model_id), f"{model_id} should allow sampling params"


class TestBuildConverseKwargsOpusSamplingParams:
    """Tests for build_converse_kwargs() sampling params guard."""

    def test_opus_4_8_strips_temperature_and_top_p(self):
        """Opus 4.8 should have temperature and topP stripped from inferenceConfig."""
        kwargs = build_converse_kwargs(
            model="us.anthropic.claude-opus-4-8",
            messages=[{"role": "user", "content": "test"}],
            temperature=1.0,
            top_p=0.9,
            max_tokens=32,
        )
        inference_config = kwargs["inferenceConfig"]
        assert inference_config == {"maxTokens": 32}, f"Expected only maxTokens, got {inference_config}"

    def test_opus_4_7_strips_temperature_and_top_p(self):
        """Opus 4.7 should have temperature and topP stripped from inferenceConfig."""
        kwargs = build_converse_kwargs(
            model="anthropic.claude-opus-4.7",
            messages=[{"role": "user", "content": "test"}],
            temperature=0.7,
            top_p=0.8,
            max_tokens=64,
        )
        inference_config = kwargs["inferenceConfig"]
        assert inference_config == {"maxTokens": 64}, f"Expected only maxTokens, got {inference_config}"

    def test_opus_4_6_includes_temperature_and_top_p(self):
        """Opus 4.6 should include temperature and topP in inferenceConfig."""
        kwargs = build_converse_kwargs(
            model="anthropic.claude-opus-4-6",
            messages=[{"role": "user", "content": "test"}],
            temperature=0.5,
            top_p=0.7,
            max_tokens=128,
        )
        inference_config = kwargs["inferenceConfig"]
        assert inference_config["maxTokens"] == 128
        assert inference_config["temperature"] == 0.5
        assert inference_config["topP"] == 0.7

    def test_sonnet_includes_temperature_and_top_p(self):
        """Sonnet models should include temperature and topP in inferenceConfig."""
        kwargs = build_converse_kwargs(
            model="anthropic.claude-3-5-sonnet",
            messages=[{"role": "user", "content": "test"}],
            temperature=0.8,
            top_p=0.9,
            max_tokens=4096,
        )
        inference_config = kwargs["inferenceConfig"]
        assert inference_config["maxTokens"] == 4096
        assert inference_config["temperature"] == 0.8
        assert inference_config["topP"] == 0.9

    def test_none_temperature_preserves_behavior(self):
        """None temperature should not be added regardless of model."""
        for model_id in ["anthropic.claude-opus-4-8", "anthropic.claude-3-5-sonnet"]:
            kwargs = build_converse_kwargs(
                model=model_id,
                messages=[{"role": "user", "content": "test"}],
                temperature=None,
                max_tokens=32,
            )
            assert "temperature" not in kwargs["inferenceConfig"]

    def test_none_top_p_preserves_behavior(self):
        """None top_p should not be added regardless of model."""
        for model_id in ["anthropic.claude-opus-4-8", "anthropic.claude-3-5-sonnet"]:
            kwargs = build_converse_kwargs(
                model=model_id,
                messages=[{"role": "user", "content": "test"}],
                top_p=None,
                max_tokens=32,
            )
            assert "topP" not in kwargs["inferenceConfig"]
