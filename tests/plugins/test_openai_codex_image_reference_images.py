from __future__ import annotations

import base64
import importlib.util
from pathlib import Path


def _load_openai_codex_plugin():
    path = Path(__file__).resolve().parents[2] / "plugins" / "image_gen" / "openai-codex" / "__init__.py"
    spec = importlib.util.spec_from_file_location("openai_codex_image_plugin_for_tests", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_generate_passes_reference_images_to_codex_responses_call(monkeypatch, tmp_path):
    mod = _load_openai_codex_plugin()
    captured = {}

    monkeypatch.setattr(mod, "_read_codex_access_token", lambda: "token")
    monkeypatch.setattr(mod, "_build_codex_client", lambda: object())
    monkeypatch.setattr(mod, "save_b64_image", lambda b64, prefix, extension="png": tmp_path / f"out.{extension}")

    def fake_collect(
        client,
        *,
        prompt,
        size,
        quality,
        reference_images=None,
        n=1,
        output_format="png",
        mask_image=None,
    ):
        captured["prompt"] = prompt
        captured["size"] = size
        captured["quality"] = quality
        captured["reference_images"] = reference_images
        captured["n"] = n
        captured["output_format"] = output_format
        captured["mask_image"] = mask_image
        return [base64.b64encode(b"png").decode("ascii")]

    monkeypatch.setattr(mod, "_collect_image_b64", fake_collect)

    result = mod.OpenAICodexImageGenProvider().generate(
        "turn this into a poster",
        aspect_ratio="portrait",
        reference_images=["https://example.com/ref.png"],
        size="1024x1024",
        quality="high",
        n=2,
        output_format="webp",
        mask_image="/tmp/mask.png",
    )

    assert result["success"] is True
    assert captured == {
        "prompt": "turn this into a poster",
        "size": "1024x1024",
        "quality": "high",
        "reference_images": ["https://example.com/ref.png"],
        "n": 2,
        "output_format": "webp",
        "mask_image": "/tmp/mask.png",
    }


def test_collect_image_b64_forwards_controls_to_responses_tool():
    mod = _load_openai_codex_plugin()
    captured = {}

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def __iter__(self):
            return iter([])

        def get_final_response(self):
            item = type("Item", (), {
                "type": "image_generation_call",
                "result": base64.b64encode(b"png").decode("ascii"),
            })()
            return type("Response", (), {"output": [item]})()

    class FakeResponses:
        def stream(self, **kwargs):
            captured.update(kwargs)
            return FakeStream()

    class FakeClient:
        responses = FakeResponses()

    b64_images = mod._collect_image_b64(
        FakeClient(),
        prompt="draw",
        size="1024x1024",
        quality="high",
        reference_images=["https://example.com/ref.png"],
        n=3,
        output_format="webp",
    )

    assert b64_images == [base64.b64encode(b"png").decode("ascii")]
    tool = captured["tools"][0]
    assert tool["size"] == "1024x1024"
    assert tool["quality"] == "high"
    assert tool["n"] == 3
    assert tool["output_format"] == "webp"


def test_collect_image_b64_returns_all_final_images():
    mod = _load_openai_codex_plugin()
    first = base64.b64encode(b"one").decode("ascii")
    second = base64.b64encode(b"two").decode("ascii")

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def __iter__(self):
            return iter([])

        def get_final_response(self):
            items = [
                type("Item", (), {"type": "image_generation_call", "result": first})(),
                type("Item", (), {"type": "image_generation_call", "result": second})(),
            ]
            return type("Response", (), {"output": items})()

    class FakeResponses:
        def stream(self, **kwargs):
            return FakeStream()

    class FakeClient:
        responses = FakeResponses()

    assert mod._collect_image_b64(
        FakeClient(),
        prompt="draw",
        size="1024x1024",
        quality="high",
        n=2,
    ) == [first, second]


def test_collect_image_b64_merges_partial_stream_with_final_response():
    mod = _load_openai_codex_plugin()
    first = base64.b64encode(b"one").decode("ascii")
    second = base64.b64encode(b"two").decode("ascii")

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def __iter__(self):
            item = type("Item", (), {"type": "image_generation_call", "result": first})()
            event = type("Event", (), {"type": "response.output_item.done", "item": item})()
            return iter([event])

        def get_final_response(self):
            items = [
                type("Item", (), {"type": "image_generation_call", "result": first})(),
                type("Item", (), {"type": "image_generation_call", "result": second})(),
            ]
            return type("Response", (), {"output": items})()

    class FakeResponses:
        def stream(self, **kwargs):
            return FakeStream()

    class FakeClient:
        responses = FakeResponses()

    assert mod._collect_image_b64(
        FakeClient(),
        prompt="draw",
        size="1024x1024",
        quality="high",
        n=2,
    ) == [first, second]


def test_collect_image_b64_preserves_duplicate_final_images():
    mod = _load_openai_codex_plugin()
    image = base64.b64encode(b"same").decode("ascii")

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def __iter__(self):
            return iter([])

        def get_final_response(self):
            items = [
                type("Item", (), {"type": "image_generation_call", "result": image})(),
                type("Item", (), {"type": "image_generation_call", "result": image})(),
            ]
            return type("Response", (), {"output": items})()

    class FakeResponses:
        def stream(self, **kwargs):
            return FakeStream()

    class FakeClient:
        responses = FakeResponses()

    assert mod._collect_image_b64(
        FakeClient(),
        prompt="draw",
        size="1024x1024",
        quality="high",
        n=2,
    ) == [image, image]


def test_generate_returns_all_saved_images_when_n_gt_1(monkeypatch, tmp_path):
    mod = _load_openai_codex_plugin()
    saved = []

    monkeypatch.setattr(mod, "_read_codex_access_token", lambda: "token")
    monkeypatch.setattr(mod, "_build_codex_client", lambda: object())
    monkeypatch.setattr(
        mod,
        "_collect_image_b64",
        lambda *args, **kwargs: [
            base64.b64encode(b"one").decode("ascii"),
            base64.b64encode(b"two").decode("ascii"),
        ],
    )

    def fake_save(b64, prefix, extension="png"):
        path = tmp_path / f"out-{len(saved)}.{extension}"
        saved.append(path)
        return path

    monkeypatch.setattr(mod, "save_b64_image", fake_save)

    result = mod.OpenAICodexImageGenProvider().generate("draw", n=2, output_format="webp")

    assert result["image"] == str(saved[0])
    assert result["images"] == [str(saved[0]), str(saved[1])]


def test_generate_rejects_unsupported_size(monkeypatch):
    mod = _load_openai_codex_plugin()
    monkeypatch.setattr(mod, "_read_codex_access_token", lambda: "token")

    result = mod.OpenAICodexImageGenProvider().generate("draw", size="2048x2048")

    assert result["success"] is False
    assert result["error_type"] == "invalid_argument"


def test_local_reference_rejects_non_image_file(tmp_path):
    mod = _load_openai_codex_plugin()
    secret = tmp_path / "secret.txt"
    secret.write_text("not an image")

    try:
        mod._reference_image_to_input_item(str(secret))
    except ValueError as exc:
        assert "not an image" in str(exc)
    else:
        raise AssertionError("expected non-image local reference to be rejected")


def test_local_reference_rejects_unknown_mime_even_under_hermes_home(tmp_path, monkeypatch):
    mod = _load_openai_codex_plugin()
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    secret = tmp_path / ".env"
    secret.write_text("plain text, not an image")

    try:
        mod._reference_image_to_input_item(str(secret))
    except ValueError as exc:
        assert "not an image" in str(exc) or "must be under" in str(exc)
    else:
        raise AssertionError("expected extensionless local reference to be rejected")


def test_build_input_content_accepts_single_reference_string_without_iterating_characters():
    mod = _load_openai_codex_plugin()

    content = mod._build_input_content("use this", "https://example.com/ref.png")

    assert content == [
        {"type": "input_text", "text": "use this"},
        {"type": "input_image", "image_url": "https://example.com/ref.png"},
    ]


def test_build_input_content_converts_local_reference_image_to_data_url(tmp_path):
    mod = _load_openai_codex_plugin()
    ref = tmp_path / "ref.png"
    png_bytes = b"\x89PNG\r\n\x1a\nfake-png"
    ref.write_bytes(png_bytes)

    content = mod._build_input_content("use this style", [str(ref)])

    assert content[0] == {"type": "input_text", "text": "use this style"}
    assert content[1]["type"] == "input_image"
    assert content[1]["image_url"].startswith("data:image/png;base64,")
    assert content[1]["image_url"].endswith(base64.b64encode(png_bytes).decode("ascii"))


def test_local_reference_rejects_text_renamed_as_png(tmp_path):
    mod = _load_openai_codex_plugin()
    ref = tmp_path / "secret.png"
    ref.write_text("plain text with an image extension")

    try:
        mod._reference_image_to_input_item(str(ref))
    except ValueError as exc:
        assert "valid image" in str(exc)
    else:
        raise AssertionError("expected text renamed as png to be rejected")
