from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path

import pytest


PLUGIN_INIT = (
    Path(__file__).resolve().parents[2]
    / "plugins"
    / "image_gen"
    / "fal-gpt-image-edit"
    / "__init__.py"
)


def _load_plugin_module():
    spec = importlib.util.spec_from_file_location(
        "fal_gpt_image_edit_plugin_under_test",
        PLUGIN_INIT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def plugin_module():
    return _load_plugin_module()


@pytest.fixture(autouse=True)
def _reset_image_edit_tool():
    from tools.registry import registry

    registry.deregister("image_edit")
    yield
    registry.deregister("image_edit")


def _png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def _jpeg_bytes() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 16


def _webp_bytes() -> bytes:
    return b"RIFF" + b"\x10\x00\x00\x00" + b"WEBP" + b"\x00" * 16


class TestPluginRegistration:
    def test_bundled_plugin_registers_image_edit_under_image_gen_toolset(self):
        from hermes_cli.plugins import PluginManager
        from toolsets import get_toolset
        from tools.registry import registry

        mgr = PluginManager()
        mgr.discover_and_load()

        loaded = mgr._plugins["image_gen/fal-gpt-image-edit"]
        assert loaded.manifest.source == "bundled"
        assert loaded.manifest.kind == "backend"
        assert loaded.enabled is True, f"error: {loaded.error}"

        entry = registry.get_entry("image_edit")
        assert entry is not None
        assert entry.toolset == "image_gen"
        assert "FAL_KEY" in entry.requires_env
        assert "image_edit" in get_toolset("image_gen")["tools"]


class TestLocalImageReferences:
    @pytest.mark.parametrize(
        ("suffix", "data", "mime_type"),
        [
            (".png", _png_bytes(), "image/png"),
            (".jpg", _jpeg_bytes(), "image/jpeg"),
            (".webp", _webp_bytes(), "image/webp"),
        ],
    )
    def test_local_image_path_converts_to_data_uri(
        self,
        plugin_module,
        tmp_path,
        suffix,
        data,
        mime_type,
    ):
        image_path = tmp_path / f"reference{suffix}"
        image_path.write_bytes(data)

        data_uri = plugin_module._local_image_to_data_uri(str(image_path))

        assert data_uri.startswith(f"data:{mime_type};base64,")
        encoded = data_uri.split(",", 1)[1]
        assert base64.b64decode(encoded) == data

    @pytest.mark.parametrize(
        ("path_factory", "error_type"),
        [
            (lambda tmp_path: tmp_path / "missing.png", "missing_image_path"),
            (lambda tmp_path: tmp_path, "invalid_image_path"),
        ],
    )
    def test_image_path_errors(self, plugin_module, tmp_path, path_factory, error_type):
        payload = json.loads(
            plugin_module.image_edit_tool(
                {
                    "prompt": "edit",
                    "image_paths": [str(path_factory(tmp_path))],
                }
            )
        )

        assert payload["success"] is False
        assert payload["error_type"] == error_type

    def test_non_image_path_error(self, plugin_module, tmp_path):
        text_path = tmp_path / "reference.txt"
        text_path.write_text("not an image")

        payload = json.loads(
            plugin_module.image_edit_tool(
                {"prompt": "edit", "image_paths": [str(text_path)]}
            )
        )

        assert payload["success"] is False
        assert payload["error_type"] == "unsupported_image_type"

    def test_oversized_image_path_error(self, plugin_module, tmp_path, monkeypatch):
        image_path = tmp_path / "reference.png"
        image_path.write_bytes(_png_bytes())
        monkeypatch.setattr(plugin_module, "MAX_REFERENCE_IMAGE_BYTES", 4)

        payload = json.loads(
            plugin_module.image_edit_tool(
                {"prompt": "edit", "image_paths": [str(image_path)]}
            )
        )

        assert payload["success"] is False
        assert payload["error_type"] == "image_too_large"

    def test_unreadable_image_path_error(self, plugin_module, tmp_path, monkeypatch):
        image_path = tmp_path / "reference.png"
        image_path.write_bytes(_png_bytes())

        def fail_read(path):
            raise OSError("permission denied")

        monkeypatch.setattr(plugin_module, "_read_image_bytes", fail_read)

        payload = json.loads(
            plugin_module.image_edit_tool(
                {"prompt": "edit", "image_paths": [str(image_path)]}
            )
        )

        assert payload["success"] is False
        assert payload["error_type"] == "unreadable_image_path"


class TestPayloadConstruction:
    def test_build_payload_maps_portrait_defaults_and_mask(self, plugin_module, tmp_path):
        reference = tmp_path / "reference.png"
        mask = tmp_path / "mask.webp"
        reference.write_bytes(_png_bytes())
        mask.write_bytes(_webp_bytes())

        payload = plugin_module._build_fal_payload(
            prompt="make a poster",
            image_paths=[str(reference)],
            image_urls=["https://example.com/reference.jpg"],
            mask_image_path=str(mask),
            aspect_ratio="portrait",
        )

        assert payload["prompt"] == "make a poster"
        assert payload["image_urls"][0].startswith("data:image/png;base64,")
        assert payload["image_urls"][1] == "https://example.com/reference.jpg"
        assert payload["mask_url"].startswith("data:image/webp;base64,")
        assert payload["image_size"] == "portrait_16_9"
        assert payload["quality"] == "high"
        assert payload["num_images"] == 1
        assert payload["output_format"] == "png"

    def test_extracts_hermes_upload_hint_paths(self, plugin_module, tmp_path):
        reference = tmp_path / "reference.png"
        reference.write_bytes(_png_bytes())

        payload = plugin_module._build_fal_payload(
            prompt=f"make it clean [Image attached at: {reference}]",
        )

        assert payload["prompt"] == "make it clean"
        assert payload["image_urls"][0].startswith("data:image/png;base64,")


class TestFalDispatch:
    def test_fal_result_url_is_cached_when_possible(self, plugin_module, tmp_path, monkeypatch):
        cached_path = tmp_path / "edited.png"
        captured = {}

        class FakeHandle:
            def get(self):
                return {"images": [{"url": "https://fal.example/edited.png"}]}

        class FakeFal:
            def submit(self, application, arguments):
                captured["application"] = application
                captured["arguments"] = arguments
                return FakeHandle()

        monkeypatch.setattr(plugin_module, "_ensure_fal_key_available", lambda: True)
        monkeypatch.setattr(plugin_module, "_load_fal_client", lambda: FakeFal())
        monkeypatch.setattr(
            plugin_module,
            "_cache_generated_image",
            lambda url, output_format: str(cached_path),
        )

        payload = json.loads(
            plugin_module.image_edit_tool(
                {
                    "prompt": "edit",
                    "image_urls": ["https://example.com/reference.png"],
                    "aspect_ratio": "portrait",
                }
            )
        )

        assert captured["application"] == "openai/gpt-image-2/edit"
        assert captured["arguments"]["image_size"] == "portrait_16_9"
        assert captured["arguments"]["quality"] == "high"
        assert captured["arguments"]["output_format"] == "png"
        assert captured["arguments"]["num_images"] == 1
        assert payload["success"] is True
        assert payload["image"] == str(cached_path)
        assert payload["remote_image"] == "https://fal.example/edited.png"
        assert payload["provider"] == "fal"
        assert payload["model"] == "openai/gpt-image-2/edit"
        assert payload["prompt"] == "edit"

    def test_fal_result_url_falls_back_when_cache_write_fails(
        self,
        plugin_module,
        monkeypatch,
    ):
        class FakeHandle:
            def get(self):
                return {"images": [{"url": "https://fal.example/edited.png"}]}

        class FakeFal:
            def submit(self, application, arguments):
                return FakeHandle()

        def fail_cache(url, output_format):
            raise RuntimeError("cache unavailable")

        monkeypatch.setattr(plugin_module, "_ensure_fal_key_available", lambda: True)
        monkeypatch.setattr(plugin_module, "_load_fal_client", lambda: FakeFal())
        monkeypatch.setattr(plugin_module, "_cache_generated_image", fail_cache)

        payload = json.loads(
            plugin_module.image_edit_tool(
                {"prompt": "edit", "image_urls": ["https://example.com/reference.png"]}
            )
        )

        assert payload["success"] is True
        assert payload["image"] == "https://fal.example/edited.png"
        assert payload["cache_warning"] == "cache unavailable"
