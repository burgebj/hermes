"""Tests for the MiniMax video generation plugin."""

from __future__ import annotations

import pytest

from agent import video_gen_registry


@pytest.fixture(autouse=True)
def _reset_registry():
    video_gen_registry._reset_for_tests()
    yield
    video_gen_registry._reset_for_tests()


def test_minimax_provider_registers():
    from plugins.video_gen.minimax import MiniMaxVideoGenProvider

    provider = MiniMaxVideoGenProvider()
    video_gen_registry.register_provider(provider)

    assert video_gen_registry.get_provider("minimax") is provider
    assert provider.display_name == "MiniMax"
    assert provider.default_model() == "MiniMax-Hailuo-2.3"


def test_minimax_models_and_capabilities():
    from plugins.video_gen.minimax import MiniMaxVideoGenProvider

    provider = MiniMaxVideoGenProvider()
    ids = [entry["id"] for entry in provider.list_models()]
    assert ids == [
        "MiniMax-Hailuo-2.3",
        "MiniMax-Hailuo-02",
        "T2V-01-Director",
        "T2V-01",
    ]
    caps = provider.capabilities()
    assert caps["modalities"] == ["text", "image"]
    assert caps["supports_audio"] is False
    assert caps["supports_negative_prompt"] is False
    assert caps["max_reference_images"] == 0


def test_minimax_unavailable_without_key(monkeypatch):
    from plugins.video_gen.minimax import MiniMaxVideoGenProvider

    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    assert MiniMaxVideoGenProvider().is_available() is False


def test_minimax_available_with_key(monkeypatch):
    from plugins.video_gen.minimax import MiniMaxVideoGenProvider

    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    assert MiniMaxVideoGenProvider().is_available() is True


def test_minimax_text_payload_shape(monkeypatch):
    import plugins.video_gen.minimax as minimax

    captured = {}

    async def fake_submit(client, payload, *, api_key, base_url):
        captured["payload"] = payload
        captured["api_key"] = api_key
        captured["base_url"] = base_url
        return "task-1"

    async def fake_poll(client, task_id, *, api_key, base_url, timeout_seconds, poll_interval):
        return {
            "status": minimax.SUCCESS_STATUS,
            "body": {"file_id": "file-1", "video_width": 1366, "video_height": 768},
        }

    async def fake_retrieve(client, file_id, *, api_key, base_url):
        return "https://cdn.example/video.mp4"

    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.test")
    monkeypatch.setattr(minimax, "_submit_task", fake_submit)
    monkeypatch.setattr(minimax, "_poll_task", fake_poll)
    monkeypatch.setattr(minimax, "_retrieve_file_url", fake_retrieve)

    result = minimax.MiniMaxVideoGenProvider().generate(
        "cinematic clouds",
        duration=9,
        resolution="1080p",
    )

    assert result["success"] is True
    assert result["video"] == "https://cdn.example/video.mp4"
    assert result["provider"] == "minimax"
    assert result["modality"] == "text"
    assert result["task_id"] == "task-1"
    assert result["file_id"] == "file-1"
    assert result["video_width"] == 1366
    assert result["video_height"] == 768
    assert captured["api_key"] == "test-minimax-key"
    assert captured["base_url"] == "https://api.test"
    assert captured["payload"] == {
        "model": "MiniMax-Hailuo-2.3",
        "prompt": "cinematic clouds",
        "duration": 10,
        "resolution": "1080P",
    }


def test_minimax_image_to_video_maps_first_frame_image(monkeypatch):
    import plugins.video_gen.minimax as minimax

    captured = {}

    async def fake_submit(client, payload, *, api_key, base_url):
        captured["payload"] = payload
        return "task-2"

    async def fake_poll(client, task_id, *, api_key, base_url, timeout_seconds, poll_interval):
        return {"status": minimax.SUCCESS_STATUS, "body": {"file_id": "file-2"}}

    async def fake_retrieve(client, file_id, *, api_key, base_url):
        return "https://cdn.example/i2v.mp4"

    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    monkeypatch.setattr(minimax, "_submit_task", fake_submit)
    monkeypatch.setattr(minimax, "_poll_task", fake_poll)
    monkeypatch.setattr(minimax, "_retrieve_file_url", fake_retrieve)

    result = minimax.MiniMaxVideoGenProvider().generate(
        "animate this image",
        image_url="https://example.com/frame.png",
        duration=6,
        resolution="768P",
    )

    assert result["success"] is True
    assert result["modality"] == "image"
    assert captured["payload"]["first_frame_image"] == "https://example.com/frame.png"
    assert "image_url" not in captured["payload"]


def test_minimax_text_only_model_rejects_image_url(monkeypatch):
    from plugins.video_gen.minimax import MiniMaxVideoGenProvider

    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    result = MiniMaxVideoGenProvider().generate(
        "animate this image",
        model="T2V-01",
        image_url="https://example.com/frame.png",
    )

    assert result["success"] is False
    assert result["error_type"] == "modality_unsupported"


def test_minimax_fail_status_returns_error(monkeypatch):
    import plugins.video_gen.minimax as minimax

    async def fake_submit(client, payload, *, api_key, base_url):
        return "task-fail"

    async def fake_poll(client, task_id, *, api_key, base_url, timeout_seconds, poll_interval):
        return {"status": minimax.FAIL_STATUS, "body": {"message": "generation failed"}}

    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    monkeypatch.setattr(minimax, "_submit_task", fake_submit)
    monkeypatch.setattr(minimax, "_poll_task", fake_poll)

    result = minimax.MiniMaxVideoGenProvider().generate("bad weather")

    assert result["success"] is False
    assert result["error_type"] == "minimax_fail"
    assert "generation failed" in result["error"]


def test_minimax_timeout_returns_error(monkeypatch):
    import plugins.video_gen.minimax as minimax

    async def fake_submit(client, payload, *, api_key, base_url):
        return "task-timeout"

    async def fake_poll(client, task_id, *, api_key, base_url, timeout_seconds, poll_interval):
        return {"status": "timeout", "body": {"status": "Processing"}}

    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    monkeypatch.setattr(minimax, "_submit_task", fake_submit)
    monkeypatch.setattr(minimax, "_poll_task", fake_poll)

    result = minimax.MiniMaxVideoGenProvider().generate("slow weather")

    assert result["success"] is False
    assert result["error_type"] == "timeout"


def test_video_generate_dispatch_selects_minimax(monkeypatch, tmp_path):
    import yaml
    import hermes_cli.plugins as plugins_module
    import plugins.video_gen.minimax as minimax

    from tools import video_generation_tool

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("MINIMAX_API_KEY", "test-minimax-key")
    (tmp_path / "config.yaml").write_text(
        yaml.safe_dump({"video_gen": {"provider": "minimax", "model": "MiniMax-Hailuo-2.3"}})
    )
    video_gen_registry.register_provider(minimax.MiniMaxVideoGenProvider())
    monkeypatch.setattr(plugins_module, "_ensure_plugins_discovered", lambda *a, **kw: None)

    async def fake_submit(client, payload, *, api_key, base_url):
        return "task-dispatch"

    async def fake_poll(client, task_id, *, api_key, base_url, timeout_seconds, poll_interval):
        return {"status": minimax.SUCCESS_STATUS, "body": {"file_id": "file-dispatch"}}

    async def fake_retrieve(client, file_id, *, api_key, base_url):
        return "https://cdn.example/dispatch.mp4"

    monkeypatch.setattr(minimax, "_submit_task", fake_submit)
    monkeypatch.setattr(minimax, "_poll_task", fake_poll)
    monkeypatch.setattr(minimax, "_retrieve_file_url", fake_retrieve)

    import json

    result = json.loads(video_generation_tool._handle_video_generate({"prompt": "dispatch me"}))

    assert result["success"] is True
    assert result["provider"] == "minimax"
    assert result["video"] == "https://cdn.example/dispatch.mp4"
