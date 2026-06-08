"""Regression tests for `_extract_multimodal_parts` video_url handling (#21920).

Without the fix, the Gemini native adapter silently drops `video_url` content
blocks emitted by `tools/vision_tools.video_analyze`, so the model never sees
the video the user asked it to analyze.
"""

import base64

from agent.gemini_native_adapter import _extract_multimodal_parts


def _video_data_url(mime: str = "video/mp4", payload: bytes = b"\x00\x00\x00\x18ftypmp4") -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class TestExtractMultimodalPartsVideoUrl:
    def test_video_url_data_uri_becomes_inline_data_part(self):
        url = _video_data_url()
        content = [{"type": "video_url", "video_url": {"url": url}}]

        parts = _extract_multimodal_parts(content)

        assert len(parts) == 1
        assert "inlineData" in parts[0]
        assert parts[0]["inlineData"]["mimeType"] == "video/mp4"
        assert parts[0]["inlineData"]["data"] == base64.b64encode(b"\x00\x00\x00\x18ftypmp4").decode("ascii")

    def test_video_url_preserves_non_default_mime(self):
        url = _video_data_url(mime="video/webm", payload=b"webmpayload")
        content = [{"type": "video_url", "video_url": {"url": url}}]

        parts = _extract_multimodal_parts(content)

        assert parts[0]["inlineData"]["mimeType"] == "video/webm"

    def test_video_url_alongside_text_keeps_both_parts_in_order(self):
        url = _video_data_url()
        content = [
            {"type": "text", "text": "describe this video"},
            {"type": "video_url", "video_url": {"url": url}},
        ]

        parts = _extract_multimodal_parts(content)

        assert len(parts) == 2
        assert parts[0] == {"text": "describe this video"}
        assert "inlineData" in parts[1]

    def test_non_data_uri_video_url_is_skipped(self):
        content = [
            {"type": "video_url", "video_url": {"url": "https://example.com/v.mp4"}},
        ]

        parts = _extract_multimodal_parts(content)

        assert parts == []

    def test_malformed_base64_video_url_is_skipped_without_raising(self):
        content = [
            {"type": "video_url", "video_url": {"url": "data:video/mp4;base64,not!!base64"}},
        ]

        parts = _extract_multimodal_parts(content)

        assert parts == []

    def test_missing_video_url_key_is_skipped(self):
        content = [{"type": "video_url"}]

        parts = _extract_multimodal_parts(content)

        assert parts == []
