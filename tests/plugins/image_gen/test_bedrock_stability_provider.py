"""Tests for the bundled ``bedrock-stability`` image_gen plugin.

Smoke tests only — generation hits the live AWS Bedrock API, so we don't run
that here. We verify metadata, model catalog, availability gating, prompt /
auth validation, the success path with a mocked ``invoke_model`` response,
content-filter handling, and config-driven model selection.
"""

from __future__ import annotations

import base64
import importlib
import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Folder name has a hyphen → not a valid Python identifier for dotted import.
bedrock_plugin = importlib.import_module("plugins.image_gen.bedrock-stability")


# 1×1 transparent PNG — valid bytes for save_b64_image()
_PNG_HEX = (
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6300010000000500010d0a2db40000000049454e44"
    "ae426082"
)


def _b64_png() -> str:
    return base64.b64encode(bytes.fromhex(_PNG_HEX)).decode()


@pytest.fixture(autouse=True)
def _tmp_hermes_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    yield tmp_path


@pytest.fixture
def provider():
    return bedrock_plugin.BedrockStabilityImageGenProvider()


# ── Metadata ────────────────────────────────────────────────────────────────


class TestMetadata:
    def test_name(self, provider):
        assert provider.name == "bedrock-stability"

    def test_default_model(self, provider):
        assert provider.default_model() == "stability.sd3-5-large-v1:0"

    def test_list_models_contains_all_three_stability_models(self, provider):
        ids = [m["id"] for m in provider.list_models()]
        assert "stability.sd3-5-large-v1:0" in ids
        assert "stability.stable-image-core-v1:1" in ids
        assert "stability.stable-image-ultra-v1:1" in ids

    def test_setup_schema_has_no_env_vars(self, provider):
        schema = provider.get_setup_schema()
        # Bedrock auth flows through AWS SDK chain — no env vars to prompt for.
        assert schema["env_vars"] == []
        assert schema["badge"] == "paid"


# ── Availability ────────────────────────────────────────────────────────────


class TestAvailability:
    def test_no_credentials_unavailable(self, monkeypatch):
        # Strip every AWS env var the probe might pick up, and force the
        # botocore fallback to report no credentials.
        for key in (
            "AWS_BEARER_TOKEN_BEDROCK",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_PROFILE",
            "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
            "AWS_WEB_IDENTITY_TOKEN_FILE",
            "AWS_REGION",
            "AWS_DEFAULT_REGION",
        ):
            monkeypatch.delenv(key, raising=False)

        with patch("agent.bedrock_adapter.has_aws_credentials", return_value=False):
            assert bedrock_plugin.BedrockStabilityImageGenProvider().is_available() is False

    def test_credentials_available(self):
        with patch("agent.bedrock_adapter.has_aws_credentials", return_value=True):
            assert bedrock_plugin.BedrockStabilityImageGenProvider().is_available() is True


# ── Generate ────────────────────────────────────────────────────────────────


class TestGenerate:
    def test_empty_prompt_rejected(self, provider):
        result = provider.generate("", aspect_ratio="square")
        assert result["success"] is False
        assert result["error_type"] == "invalid_argument"

    def test_missing_credentials_returns_auth_error(self, provider):
        with patch("agent.bedrock_adapter.has_aws_credentials", return_value=False):
            result = provider.generate("a cat", aspect_ratio="square")
        assert result["success"] is False
        assert result["error_type"] == "auth_required"

    def test_success_path_saves_image(self, provider, tmp_path):
        png_bytes = bytes.fromhex(_PNG_HEX)
        body = json.dumps({
            "seeds": [12345],
            "finish_reasons": [None],
            "images": [_b64_png()],
        }).encode()

        fake_client = MagicMock()
        fake_client.invoke_model.return_value = {"body": io.BytesIO(body)}

        with patch("agent.bedrock_adapter.has_aws_credentials", return_value=True), \
                patch("agent.bedrock_adapter._get_bedrock_runtime_client", return_value=fake_client):
            result = provider.generate("a cat", aspect_ratio="landscape")

        assert result["success"] is True
        assert result["model"] == "stability.sd3-5-large-v1:0"
        assert result["aspect_ratio"] == "landscape"
        assert result["provider"] == "bedrock-stability"
        assert result["aspect"] == "16:9"

        saved = Path(result["image"])
        assert saved.exists()
        assert saved.parent == tmp_path / "cache" / "images"
        assert saved.read_bytes() == png_bytes

        # Verify the request payload we send to Bedrock.
        call_kwargs = fake_client.invoke_model.call_args.kwargs
        assert call_kwargs["modelId"] == "stability.sd3-5-large-v1:0"
        assert call_kwargs["contentType"] == "application/json"
        sent = json.loads(call_kwargs["body"])
        assert sent["prompt"] == "a cat"
        assert sent["mode"] == "text-to-image"
        assert sent["aspect_ratio"] == "16:9"
        assert sent["output_format"] == "png"

    @pytest.mark.parametrize("aspect,expected_aspect", [
        ("landscape", "16:9"),
        ("square", "1:1"),
        ("portrait", "9:16"),
    ])
    def test_aspect_ratio_mapping(self, provider, aspect, expected_aspect):
        body = json.dumps({
            "seeds": [1],
            "finish_reasons": [None],
            "images": [_b64_png()],
        }).encode()
        fake_client = MagicMock()
        fake_client.invoke_model.return_value = {"body": io.BytesIO(body)}

        with patch("agent.bedrock_adapter.has_aws_credentials", return_value=True), \
                patch("agent.bedrock_adapter._get_bedrock_runtime_client", return_value=fake_client):
            provider.generate("a cat", aspect_ratio=aspect)

        sent = json.loads(fake_client.invoke_model.call_args.kwargs["body"])
        assert sent["aspect_ratio"] == expected_aspect

    def test_invoke_model_error_returns_api_error(self, provider):
        fake_client = MagicMock()
        fake_client.invoke_model.side_effect = RuntimeError("boom")

        with patch("agent.bedrock_adapter.has_aws_credentials", return_value=True), \
                patch("agent.bedrock_adapter._get_bedrock_runtime_client", return_value=fake_client):
            result = provider.generate("a cat")

        assert result["success"] is False
        assert result["error_type"] == "api_error"
        assert "boom" in result["error"]

    def test_content_filter_returns_empty_response_with_reason(self, provider):
        # Stability surfaces filter hits as finish_reasons without images.
        body = json.dumps({
            "finish_reasons": ["Filter reason: prompt"],
        }).encode()
        fake_client = MagicMock()
        fake_client.invoke_model.return_value = {"body": io.BytesIO(body)}

        with patch("agent.bedrock_adapter.has_aws_credentials", return_value=True), \
                patch("agent.bedrock_adapter._get_bedrock_runtime_client", return_value=fake_client):
            result = provider.generate("something disallowed")

        assert result["success"] is False
        assert result["error_type"] == "empty_response"
        assert "Filter reason: prompt" in result["error"]

    def test_empty_images_returns_empty_response(self, provider):
        body = json.dumps({
            "seeds": [1],
            "finish_reasons": [None],
            "images": [],
        }).encode()
        fake_client = MagicMock()
        fake_client.invoke_model.return_value = {"body": io.BytesIO(body)}

        with patch("agent.bedrock_adapter.has_aws_credentials", return_value=True), \
                patch("agent.bedrock_adapter._get_bedrock_runtime_client", return_value=fake_client):
            result = provider.generate("a cat")

        assert result["success"] is False
        assert result["error_type"] == "empty_response"


# ── Model selection via config ──────────────────────────────────────────────


class TestModelSelection:
    def _run_with_config_model(self, provider, configured_model):
        body = json.dumps({
            "seeds": [1],
            "finish_reasons": [None],
            "images": [_b64_png()],
        }).encode()
        fake_client = MagicMock()
        fake_client.invoke_model.return_value = {"body": io.BytesIO(body)}

        with patch.object(bedrock_plugin, "_backend_config", return_value={"model": configured_model}), \
                patch("agent.bedrock_adapter.has_aws_credentials", return_value=True), \
                patch("agent.bedrock_adapter._get_bedrock_runtime_client", return_value=fake_client):
            result = provider.generate("a cat", aspect_ratio="square")
        return result, fake_client

    def test_ultra_model_selected_via_config(self, provider):
        result, fake_client = self._run_with_config_model(
            provider, "stability.stable-image-ultra-v1:1"
        )
        assert result["success"] is True
        assert result["model"] == "stability.stable-image-ultra-v1:1"
        call_kwargs = fake_client.invoke_model.call_args.kwargs
        assert call_kwargs["modelId"] == "stability.stable-image-ultra-v1:1"

    def test_core_model_selected_via_config(self, provider):
        result, fake_client = self._run_with_config_model(
            provider, "stability.stable-image-core-v1:1"
        )
        assert result["success"] is True
        assert result["model"] == "stability.stable-image-core-v1:1"

    def test_unknown_model_falls_back_to_default(self, provider):
        result, fake_client = self._run_with_config_model(
            provider, "stability.does-not-exist-v9:9"
        )
        assert result["success"] is True
        assert result["model"] == "stability.sd3-5-large-v1:0"


# ── Region resolution ──────────────────────────────────────────────────────


class TestRegionResolution:
    def test_default_region_is_us_west_2(self, monkeypatch):
        # No backend config, no root config, no env vars, no botocore session.
        for key in ("AWS_REGION", "AWS_DEFAULT_REGION"):
            monkeypatch.delenv(key, raising=False)

        with patch.object(bedrock_plugin, "_backend_config", return_value={}), \
                patch.object(bedrock_plugin, "_load_root_config", return_value={}):
            # botocore Session.get_config_variable("region") returns None when
            # ~/.aws/config has no region set.
            with patch("botocore.session.Session") as mock_session:
                mock_session.return_value.get_config_variable.return_value = None
                assert bedrock_plugin._resolve_region() == "us-west-2"

    def test_backend_config_region_wins(self):
        with patch.object(bedrock_plugin, "_backend_config", return_value={"region": "eu-west-1"}):
            assert bedrock_plugin._resolve_region() == "eu-west-1"

    def test_root_bedrock_region_used_when_no_backend_override(self):
        with patch.object(bedrock_plugin, "_backend_config", return_value={}), \
                patch.object(bedrock_plugin, "_load_root_config", return_value={"bedrock": {"region": "ap-northeast-1"}}):
            assert bedrock_plugin._resolve_region() == "ap-northeast-1"


# ── Plugin entry point ──────────────────────────────────────────────────────


class TestPluginEntryPoint:
    def test_register_calls_ctx(self):
        ctx = MagicMock()
        bedrock_plugin.register(ctx)
        ctx.register_image_gen_provider.assert_called_once()
        provider_arg = ctx.register_image_gen_provider.call_args.args[0]
        assert provider_arg.name == "bedrock-stability"
