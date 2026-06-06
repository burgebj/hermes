from __future__ import annotations

import json
from types import SimpleNamespace


def test_handle_image_generate_passes_reference_images_to_plugin(monkeypatch):
    from tools import image_generation_tool

    monkeypatch.setattr(
        image_generation_tool,
        "_read_configured_image_provider",
        lambda: "openai-codex",
    )
    monkeypatch.setattr(
        image_generation_tool,
        "_read_configured_image_model",
        lambda: None,
    )

    class _Provider:
        name = "openai-codex"

        def generate(self, **kwargs):
            return {
                "success": True,
                "image": "/tmp/fake.png",
                "provider": "openai-codex",
                "echo": kwargs,
            }

    monkeypatch.setitem(__import__("sys").modules, "agent.image_gen_registry", SimpleNamespace(get_provider=lambda name: _Provider()))
    monkeypatch.setitem(__import__("sys").modules, "hermes_cli.plugins", SimpleNamespace(_ensure_plugins_discovered=lambda force=False: None))

    result = image_generation_tool._handle_image_generate({
        "prompt": "edit this image",
        "aspect_ratio": "landscape",
        "reference_images": ["https://example.com/ref.png"],
    })
    payload = json.loads(result)
    assert payload["success"] is True
    assert payload["echo"]["reference_images"] == ["https://example.com/ref.png"]
