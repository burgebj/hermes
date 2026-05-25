"""Regression tests for FAL video-generation payload construction."""

from __future__ import annotations

from plugins.video_gen.fal import FAL_FAMILIES, _build_payload


def test_veo31_duration_uses_fal_literal_suffix():
    payload = _build_payload(
        FAL_FAMILIES["veo3.1"],
        prompt="smoke test",
        image_url=None,
        duration=4,
        aspect_ratio="16:9",
        resolution="720p",
        negative_prompt=None,
        audio=False,
        seed=None,
    )

    assert payload["duration"] == "4s"


def test_veo31_duration_clamps_then_suffixes():
    payload = _build_payload(
        FAL_FAMILIES["veo3.1"],
        prompt="smoke test",
        image_url=None,
        duration=5,
        aspect_ratio="16:9",
        resolution="720p",
        negative_prompt=None,
        audio=None,
        seed=None,
    )

    assert payload["duration"] in {"4s", "6s"}
