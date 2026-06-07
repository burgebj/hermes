"""Tests for the OpenRouter video gen plugin — register, payload, async flow."""

from __future__ import annotations

import json

import pytest

from agent import video_gen_registry


@pytest.fixture(autouse=True)
def _reset_registry():
    video_gen_registry._reset_for_tests()
    yield
    video_gen_registry._reset_for_tests()


@pytest.fixture(autouse=True)
def _stub_models(monkeypatch):
    """Avoid live /videos/models network calls in unit tests."""
    from plugins.video_gen import openrouter as orv

    raw = [
        {
            "id": "google/veo-3.1",
            "name": "Veo 3.1",
            "description": "Google video model",
            "supported_aspect_ratios": ["16:9", "9:16"],
            "supported_resolutions": ["720p", "1080p"],
            "supported_durations": [4, 6, 8],
            "generate_audio": True,
            "supported_frame_images": ["first_frame", "last_frame"],
        },
        {
            "id": "openai/sora-2-pro",
            "name": "Sora 2 Pro",
            "supported_aspect_ratios": ["16:9", "9:16"],
            "supported_resolutions": ["720p", "1080p"],
            "supported_durations": [4, 8, 12],
            "generate_audio": True,
            "supported_frame_images": None,
        },
    ]
    monkeypatch.setattr(orv, "_fetch_models_raw", lambda: raw)
    return raw


def _provider(monkeypatch, api_key="sk-or-test"):
    from plugins.video_gen import openrouter as orv

    monkeypatch.setattr(
        orv, "_resolve_credentials",
        lambda: (api_key, "https://openrouter.ai/api/v1"),
    )
    return orv.OpenRouterVideoGenProvider()


def test_registers_and_basic_surface(monkeypatch):
    from plugins.video_gen.openrouter import OpenRouterVideoGenProvider, DEFAULT_MODEL

    provider = _provider(monkeypatch)
    video_gen_registry.register_provider(provider)

    assert video_gen_registry.get_provider("openrouter") is provider
    assert provider.name == "openrouter"
    assert provider.display_name == "OpenRouter"
    assert provider.default_model() == DEFAULT_MODEL == "google/veo-3.1"


def test_is_available_requires_key(monkeypatch):
    assert _provider(monkeypatch, api_key="").is_available() is False
    assert _provider(monkeypatch, api_key="sk-or-x").is_available() is True


def test_setup_schema_declares_openrouter_key(monkeypatch):
    schema = _provider(monkeypatch).get_setup_schema()
    assert schema["name"] == "OpenRouter Video"
    assert [e["key"] for e in schema["env_vars"]] == ["OPENROUTER_API_KEY"]


def test_list_models_marks_image_modality_from_frames(monkeypatch):
    models = _provider(monkeypatch).list_models()
    by_id = {m["id"]: m for m in models}
    # veo has frame support -> text+image; sora has none -> text only
    assert set(by_id["google/veo-3.1"]["modalities"]) == {"text", "image"}
    assert by_id["openai/sora-2-pro"]["modalities"] == ["text"]


def test_capabilities_aggregate_across_catalog(monkeypatch):
    caps = _provider(monkeypatch).capabilities()
    assert caps["max_duration"] == 12
    assert caps["supports_audio"] is True
    assert "16:9" in caps["aspect_ratios"]
    assert "1080p" in caps["resolutions"]
    assert caps["modalities"] == ["text", "image"]


def test_generate_requires_key(monkeypatch):
    out = _provider(monkeypatch, api_key="").generate("a cat")
    assert out["success"] is False
    assert out["error_type"] == "auth_required"


def test_generate_requires_prompt(monkeypatch):
    out = _provider(monkeypatch).generate("   ")
    assert out["success"] is False
    assert out["error_type"] == "missing_prompt"


# ---------------------------------------------------------------------------
# Async submit/poll flow — mock httpx.AsyncClient
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("err", request=None, response=self)

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Drives a scripted submit -> poll(pending) -> poll(completed) flow."""

    def __init__(self, submit_payload, poll_payloads, captured):
        self._submit_payload = submit_payload
        self._poll_payloads = list(poll_payloads)
        self._captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, json=None, timeout=None):
        self._captured["post_url"] = url
        self._captured["post_json"] = json
        return _FakeResponse(self._submit_payload)

    async def get(self, url, headers=None, timeout=None):
        self._captured.setdefault("get_urls", []).append(url)
        payload = self._poll_payloads.pop(0) if self._poll_payloads else {"status": "completed", "unsigned_urls": []}
        return _FakeResponse(payload)


def test_generate_text_to_video_success(monkeypatch):
    from plugins.video_gen import openrouter as orv

    provider = _provider(monkeypatch)
    captured: dict = {}

    def _client_factory(*a, **k):
        return _FakeAsyncClient(
            submit_payload={"id": "job-1", "polling_url": "/api/v1/videos/job-1", "status": "pending"},
            poll_payloads=[
                {"status": "in_progress"},
                {"status": "completed", "unsigned_urls": ["https://cdn.openrouter.ai/v.mp4"], "usage": {"cost": 0.5}},
            ],
            captured=captured,
        )

    monkeypatch.setattr(orv.httpx, "AsyncClient", _client_factory)
    monkeypatch.setattr(orv.asyncio, "sleep", _no_sleep)

    out = provider.generate("a serene mountain at sunset", aspect_ratio="16:9", resolution="720p", duration=8)
    assert out["success"] is True
    assert out["video"] == "https://cdn.openrouter.ai/v.mp4"
    assert out["modality"] == "text"
    assert out["provider"] == "openrouter"
    assert captured["post_url"].endswith("/videos")
    assert captured["post_json"]["model"] == "google/veo-3.1"
    assert captured["post_json"]["prompt"] == "a serene mountain at sunset"
    assert "frame_images" not in captured["post_json"]
    assert out["usage"] == {"cost": 0.5}


def test_generate_image_to_video_sets_first_frame(monkeypatch):
    from plugins.video_gen import openrouter as orv

    provider = _provider(monkeypatch)
    captured: dict = {}
    monkeypatch.setattr(
        orv.httpx, "AsyncClient",
        lambda *a, **k: _FakeAsyncClient(
            submit_payload={"id": "job-2", "status": "completed", "unsigned_urls": ["https://cdn/x.mp4"]},
            poll_payloads=[],
            captured=captured,
        ),
    )
    monkeypatch.setattr(orv.asyncio, "sleep", _no_sleep)

    out = provider.generate("animate", image_url="https://example.com/i.png")
    assert out["success"] is True
    assert out["modality"] == "image"
    frames = captured["post_json"]["frame_images"]
    assert frames[0]["frame_type"] == "first_frame"
    assert frames[0]["image_url"]["url"] == "https://example.com/i.png"


def test_generate_failed_status_surfaces_error(monkeypatch):
    from plugins.video_gen import openrouter as orv

    provider = _provider(monkeypatch)
    captured: dict = {}
    monkeypatch.setattr(
        orv.httpx, "AsyncClient",
        lambda *a, **k: _FakeAsyncClient(
            submit_payload={"id": "job-3", "status": "failed", "error": "content policy"},
            poll_payloads=[],
            captured=captured,
        ),
    )
    monkeypatch.setattr(orv.asyncio, "sleep", _no_sleep)

    out = provider.generate("bad prompt")
    assert out["success"] is False
    assert "content policy" in out["error"]
    assert out["error_type"] == "openrouter_failed"


async def _no_sleep(*a, **k):
    return None
