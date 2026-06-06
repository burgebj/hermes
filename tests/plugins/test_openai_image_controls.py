from __future__ import annotations

import base64
import importlib.util
import sys
from pathlib import Path


def _load_openai_plugin():
    path = Path(__file__).resolve().parents[2] / "plugins" / "image_gen" / "openai" / "__init__.py"
    spec = importlib.util.spec_from_file_location("openai_image_plugin_for_tests", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_openai_provider_returns_all_saved_images_for_n_gt_1(monkeypatch, tmp_path):
    mod = _load_openai_plugin()
    first = base64.b64encode(b"one").decode("ascii")
    second = base64.b64encode(b"two").decode("ascii")
    captured = {}
    saved = []

    class FakeImages:
        def generate(self, **payload):
            captured.update(payload)
            items = [
                type("Item", (), {"b64_json": first, "url": None, "revised_prompt": None})(),
                type("Item", (), {"b64_json": second, "url": None, "revised_prompt": None})(),
            ]
            return type("Response", (), {"data": items})()

    class FakeOpenAIClient:
        images = FakeImages()

    fake_openai = type("FakeOpenAIModule", (), {"OpenAI": FakeOpenAIClient})()
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_save(b64, prefix, extension="png"):
        path = tmp_path / f"out-{len(saved)}.{extension}"
        saved.append(path)
        return path

    monkeypatch.setattr(mod, "save_b64_image", fake_save)

    result = mod.OpenAIImageGenProvider().generate(
        "draw",
        n=2,
        size="1024x1024",
        quality="high",
        output_format="webp",
    )

    assert captured["n"] == 2
    assert captured["size"] == "1024x1024"
    assert captured["quality"] == "high"
    assert captured["output_format"] == "webp"
    assert result["image"] == str(saved[0])
    assert result["images"] == [str(saved[0]), str(saved[1])]


def test_openai_provider_returns_all_urls_for_n_gt_1(monkeypatch):
    mod = _load_openai_plugin()

    class FakeImages:
        def generate(self, **payload):
            items = [
                type("Item", (), {"b64_json": None, "url": "https://example.com/1.png", "revised_prompt": None})(),
                type("Item", (), {"b64_json": None, "url": "https://example.com/2.png", "revised_prompt": None})(),
            ]
            return type("Response", (), {"data": items})()

    class FakeOpenAIClient:
        images = FakeImages()

    fake_openai = type("FakeOpenAIModule", (), {"OpenAI": FakeOpenAIClient})()
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    result = mod.OpenAIImageGenProvider().generate("draw", n=2)

    assert result["image"] == "https://example.com/1.png"
    assert result["images"] == ["https://example.com/1.png", "https://example.com/2.png"]


def test_openai_provider_rejects_unsupported_size(monkeypatch):
    mod = _load_openai_plugin()
    monkeypatch.setitem(sys.modules, "openai", type("FakeOpenAIModule", (), {"OpenAI": object})())
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    result = mod.OpenAIImageGenProvider().generate("draw", size="2048x2048")

    assert result["success"] is False
    assert result["error_type"] == "invalid_argument"
