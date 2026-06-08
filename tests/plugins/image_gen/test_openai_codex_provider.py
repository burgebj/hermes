"""Tests for the bundled ``openai-codex`` image_gen plugin.

Mirrors ``test_openai_provider.py`` but targets the standalone
Codex/ChatGPT-OAuth-backed provider that uses the Responses
``image_generation`` tool path instead of the ``images.generate`` REST
endpoint.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

# The plugin directory uses a hyphen, which is not a valid Python identifier
# for the dotted-import form. Load it via importlib so tests don't need to
# touch sys.path or rename the directory.
codex_plugin = importlib.import_module("plugins.image_gen.openai-codex")


# 1×1 transparent PNG — valid bytes for save_b64_image()
_PNG_HEX = (
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6300010000000500010d0a2db40000000049454e44"
    "ae426082"
)


def _b64_png() -> str:
    import base64
    return base64.b64encode(bytes.fromhex(_PNG_HEX)).decode()


@pytest.fixture(autouse=True)
def _tmp_hermes_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    yield tmp_path


@pytest.fixture
def provider(monkeypatch):
    # Codex plugin is API-key-independent; clear it to make the test honest.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return codex_plugin.OpenAICodexImageGenProvider()


# ── Metadata ────────────────────────────────────────────────────────────────


class TestMetadata:
    def test_name(self, provider):
        assert provider.name == "openai-codex"

    def test_display_name(self, provider):
        assert provider.display_name == "OpenAI (Codex auth)"

    def test_default_model(self, provider):
        assert provider.default_model() == "gpt-image-2-medium"

    def test_list_models_three_tiers(self, provider):
        ids = [m["id"] for m in provider.list_models()]
        assert ids == ["gpt-image-2-low", "gpt-image-2-medium", "gpt-image-2-high"]

    def test_setup_schema_has_no_required_env_vars(self, provider):
        schema = provider.get_setup_schema()
        assert schema["env_vars"] == []
        assert schema["badge"] == "free"


# ── Availability ────────────────────────────────────────────────────────────


class TestAvailability:
    def test_unavailable_without_codex_token(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: None)
        assert codex_plugin.OpenAICodexImageGenProvider().is_available() is False

    def test_available_with_codex_token(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: "codex-token")
        assert codex_plugin.OpenAICodexImageGenProvider().is_available() is True

    def test_openai_api_key_alone_is_not_enough(self, monkeypatch):
        # Codex plugin is intentionally orthogonal to the API-key plugin —
        # the API key alone must NOT make it appear available.
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: None)
        assert codex_plugin.OpenAICodexImageGenProvider().is_available() is False


# ── Generate ────────────────────────────────────────────────────────────────


class TestGenerate:
    def test_returns_auth_error_without_codex_token(self, provider, monkeypatch):
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: None)
        result = provider.generate("a cat")
        assert result["success"] is False
        assert result["error_type"] == "auth_required"

    def test_returns_invalid_argument_for_empty_prompt(self, provider, monkeypatch):
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: "codex-token")
        result = provider.generate("   ")
        assert result["success"] is False
        assert result["error_type"] == "invalid_argument"

    def test_generate_uses_codex_stream_path(self, provider, monkeypatch, tmp_path):
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: "codex-token")
        monkeypatch.setattr(codex_plugin, "_collect_image_b64", lambda *a, **kw: _b64_png())

        result = provider.generate("a cat", aspect_ratio="landscape")

        assert result["success"] is True
        assert result["model"] == "gpt-image-2-medium"
        assert result["provider"] == "openai-codex"
        assert result["quality"] == "medium"

        saved = Path(result["image"])
        assert saved.exists()
        assert saved.parent == tmp_path / "cache" / "images"
        # Filename prefix differs from the API-key plugin so cache audits can
        # tell the two backends apart.
        assert saved.name.startswith("openai_codex_")

    def test_codex_stream_request_shape(self, provider, monkeypatch):
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: "codex-token")

        captured = {}

        def _collect(token, *, prompt, size, quality):
            captured.update(codex_plugin._build_responses_payload(
                prompt=prompt,
                size=size,
                quality=quality,
            ))
            return _b64_png()

        monkeypatch.setattr(codex_plugin, "_collect_image_b64", _collect)

        result = provider.generate("a cat", aspect_ratio="portrait")
        assert result["success"] is True

        assert captured["model"] == "gpt-5.5"
        assert captured["store"] is False
        assert captured["input"][0]["type"] == "message"
        assert captured["input"][0]["role"] == "user"
        assert captured["input"][0]["content"][0]["type"] == "input_text"
        assert captured["tool_choice"]["type"] == "allowed_tools"
        assert captured["tool_choice"]["mode"] == "required"
        assert captured["tool_choice"]["tools"] == [{"type": "image_generation"}]

        tool = captured["tools"][0]
        assert tool["type"] == "image_generation"
        assert tool["model"] == "gpt-image-2"
        assert tool["quality"] == "medium"
        assert tool["size"] == "1024x1536"
        assert tool["output_format"] == "png"
        assert tool["background"] == "opaque"
        assert tool["partial_images"] == 1

    def test_partial_image_event_used_when_done_missing(self):
        """If output_item.done is missing, partial_image_b64 is accepted."""
        payload = {
            "type": "response.image_generation_call.partial_image",
            "partial_image_b64": _b64_png(),
        }
        assert codex_plugin._extract_image_b64(payload) == _b64_png()

    def test_sse_parser_handles_event_and_data_lines(self):
        class _Response:
            def iter_lines(self):
                return iter([
                    "event: response.output_item.done",
                    'data: {"item": {"type": "image_generation_call", "result": "abc"}}',
                    "",
                ])

        events = list(codex_plugin._iter_sse_json(_Response()))
        assert events == [{
            "type": "response.output_item.done",
            "item": {"type": "image_generation_call", "result": "abc"},
        }]

    def test_final_response_sweep_recovers_image(self):
        """Completed response output is found by recursive payload scanning."""
        payload = {
            "type": "response.completed",
            "response": {
                "output": [{
                    "type": "image_generation_call",
                    "status": "completed",
                    "id": "ig_final",
                    "result": _b64_png(),
                }],
            },
        }
        assert codex_plugin._extract_image_b64(payload) == _b64_png()

    def test_empty_response_returns_error(self, provider, monkeypatch):
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: "codex-token")
        monkeypatch.setattr(codex_plugin, "_collect_image_b64", lambda *a, **kw: None)

        result = provider.generate("a cat")
        assert result["success"] is False
        assert result["error_type"] == "empty_response"

    def test_stream_exception_returns_api_error(self, provider, monkeypatch):
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: "codex-token")

        def _boom(*args, **kwargs):
            raise RuntimeError("cloudflare 403")

        monkeypatch.setattr(codex_plugin, "_collect_image_b64", _boom)

        result = provider.generate("a cat")
        assert result["success"] is False
        assert result["error_type"] == "api_error"
        assert "cloudflare 403" in result["error"]


# ── Plugin entry point ──────────────────────────────────────────────────────


class TestRegistration:
    def test_register_calls_register_image_gen_provider(self):
        registered = []

        class _Ctx:
            def register_image_gen_provider(self, prov):
                registered.append(prov)

        codex_plugin.register(_Ctx())
        assert len(registered) == 1
        assert registered[0].name == "openai-codex"


# ── Reference images (input_image) ───────────────────────────────────────────


class TestToInputImagePart:
    def test_http_url_passthrough(self):
        part = codex_plugin._to_input_image_part("https://example.com/m.png")
        assert part == {"type": "input_image", "image_url": "https://example.com/m.png"}

    def test_data_image_url_passthrough(self):
        ref = "data:image/png;base64," + _b64_png()
        part = codex_plugin._to_input_image_part(ref)
        assert part == {"type": "input_image", "image_url": ref}

    def test_absolute_path_becomes_data_url(self, tmp_path):
        img = tmp_path / "mascot.png"
        img.write_bytes(bytes.fromhex(_PNG_HEX))
        part = codex_plugin._to_input_image_part(str(img))
        assert part["type"] == "input_image"
        assert part["image_url"].startswith("data:image/png;base64,")

    def test_jpg_extension_maps_to_jpeg_mime(self, tmp_path):
        img = tmp_path / "mascot.jpg"
        img.write_bytes(bytes.fromhex(_PNG_HEX))  # content bytes irrelevant for mime mapping
        part = codex_plugin._to_input_image_part(str(img))
        assert part["image_url"].startswith("data:image/jpeg;base64,")

    def test_relative_path_rejected(self):
        with pytest.raises(ValueError, match="absolute"):
            codex_plugin._to_input_image_part("mascot.png")

    def test_missing_file_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="not found"):
            codex_plugin._to_input_image_part(str(tmp_path / "nope.png"))

    def test_unsupported_extension_rejected(self, tmp_path):
        bad = tmp_path / "mascot.bmp"
        bad.write_bytes(bytes.fromhex(_PNG_HEX))
        with pytest.raises(ValueError, match="unsupported"):
            codex_plugin._to_input_image_part(str(bad))

    def test_oversize_file_rejected(self, tmp_path, monkeypatch):
        monkeypatch.setattr(codex_plugin, "MAX_REFERENCE_IMAGE_BYTES", 4)
        img = tmp_path / "big.png"
        img.write_bytes(bytes.fromhex(_PNG_HEX))  # > 4 bytes
        with pytest.raises(ValueError, match="exceeds"):
            codex_plugin._to_input_image_part(str(img))

    def test_non_image_data_url_rejected(self):
        with pytest.raises(ValueError, match="data:image"):
            codex_plugin._to_input_image_part("data:text/plain;base64,QQ==")

    def test_empty_rejected(self):
        with pytest.raises(ValueError, match="non-empty"):
            codex_plugin._to_input_image_part("   ")


class TestPayloadReferenceImages:
    def test_text_only_when_no_parts(self):
        payload = codex_plugin._build_responses_payload(
            prompt="a cat", size="1024x1024", quality="medium"
        )
        content = payload["input"][0]["content"]
        assert content == [{"type": "input_text", "text": "a cat"}]

    def test_parts_appended_after_text(self):
        parts = [{"type": "input_image", "image_url": "https://x/y.png"}]
        payload = codex_plugin._build_responses_payload(
            prompt="a cat", size="1024x1024", quality="medium", image_parts=parts
        )
        content = payload["input"][0]["content"]
        assert content[0] == {"type": "input_text", "text": "a cat"}
        assert content[1:] == parts


class TestGenerateReferenceImages:
    def test_generate_forwards_reference_images_into_payload(self, provider, monkeypatch):
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: "codex-token")
        captured = {}

        def _collect(token, *, prompt, size, quality, image_parts=None):
            captured["payload"] = codex_plugin._build_responses_payload(
                prompt=prompt, size=size, quality=quality, image_parts=image_parts
            )
            return _b64_png()

        monkeypatch.setattr(codex_plugin, "_collect_image_b64", _collect)

        result = provider.generate(
            "hamster mascot on a bike",
            aspect_ratio="square",
            reference_images=["https://mojapteczka.pl/brand/mascot.jpeg"],
        )

        assert result["success"] is True
        content = captured["payload"]["input"][0]["content"]
        assert content[0]["type"] == "input_text"
        assert {
            "type": "input_image",
            "image_url": "https://mojapteczka.pl/brand/mascot.jpeg",
        } in content[1:]

    def test_generate_rejects_too_many_references(self, provider, monkeypatch):
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: "codex-token")

        def _boom(*a, **kw):
            raise AssertionError("network call must not happen for invalid refs")

        monkeypatch.setattr(codex_plugin, "_collect_image_b64", _boom)

        refs = [f"https://x/{i}.png" for i in range(codex_plugin.MAX_REFERENCE_IMAGES + 1)]
        result = provider.generate("a cat", reference_images=refs)

        assert result["success"] is False
        assert result["error_type"] == "invalid_reference_image"

    def test_generate_rejects_bad_reference(self, provider, monkeypatch):
        monkeypatch.setattr(codex_plugin, "_read_codex_access_token", lambda: "codex-token")

        def _boom(*a, **kw):
            raise AssertionError("network call must not happen for invalid refs")

        monkeypatch.setattr(codex_plugin, "_collect_image_b64", _boom)

        result = provider.generate("a cat", reference_images=["relative/mascot.png"])

        assert result["success"] is False
        assert result["error_type"] == "invalid_reference_image"
