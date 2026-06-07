"""Tests for SessionDB._strip_image_blobs and the _encode_content integration.

Sending a photo as a file (uncompressed document) used to persist the full
base64 data URL blob in the session DB, which caused every subsequent turn to
re-inject several MB of image data into the conversation history and overflow
the context window.  _strip_image_blobs() is called by _encode_content() to
strip data: blobs before persistence, replacing them with a short placeholder.
The local path hint in the companion text part remains intact so the model can
re-access the image via vision_analyze or similar tools.
"""

import json
import pytest
from hermes_state import SessionDB

# ── helpers ──────────────────────────────────────────────────────────────────

PLACEHOLDER = "[Attached image — base64 stripped for storage; re-read from the path above if needed]"
PREFIX = SessionDB._CONTENT_JSON_PREFIX

DATA_URL = "data:image/png;base64," + "A" * 100  # fake base64 blob
HTTPS_URL = "https://cdn.example.com/photo.jpg"


def _img_part(url: str) -> dict:
    return {"type": "image_url", "image_url": {"url": url}}


def _text_part(text: str) -> dict:
    return {"type": "text", "text": text}


# ── _strip_image_blobs ────────────────────────────────────────────────────────


class TestStripImageBlobs:
    def test_scalar_passthrough(self):
        assert SessionDB._strip_image_blobs("hello") == "hello"
        assert SessionDB._strip_image_blobs(None) is None
        assert SessionDB._strip_image_blobs(42) == 42

    def test_no_images_unchanged(self):
        parts = [_text_part("just text")]
        assert SessionDB._strip_image_blobs(parts) is parts  # identity

    def test_https_url_unchanged(self):
        parts = [_text_part("caption"), _img_part(HTTPS_URL)]
        result = SessionDB._strip_image_blobs(parts)
        assert result is parts  # no copy needed

    def test_data_url_replaced(self):
        parts = [
            _text_part("[Image attached at: /tmp/img.png]"),
            _img_part(DATA_URL),
        ]
        result = SessionDB._strip_image_blobs(parts)
        assert result is not parts
        assert len(result) == 2
        assert result[0] == _text_part("[Image attached at: /tmp/img.png]")
        assert result[1] == {"type": "text", "text": PLACEHOLDER}

    def test_multiple_data_urls_all_replaced(self):
        parts = [
            _text_part("two images"),
            _img_part(DATA_URL),
            _img_part("data:image/jpeg;base64," + "B" * 50),
        ]
        result = SessionDB._strip_image_blobs(parts)
        assert len(result) == 3
        for part in result[1:]:
            assert part == {"type": "text", "text": PLACEHOLDER}

    def test_mixed_data_and_https_urls(self):
        """data: blobs stripped; https: URLs left intact."""
        parts = [
            _text_part("mixed"),
            _img_part(DATA_URL),
            _img_part(HTTPS_URL),
        ]
        result = SessionDB._strip_image_blobs(parts)
        assert result[1] == {"type": "text", "text": PLACEHOLDER}
        assert result[2] == _img_part(HTTPS_URL)

    def test_input_not_mutated(self):
        original_url = DATA_URL
        parts = [_text_part("x"), _img_part(original_url)]
        _ = SessionDB._strip_image_blobs(parts)
        # original list unchanged
        assert parts[1]["image_url"]["url"] == original_url

    def test_idempotent(self):
        """Calling twice on already-stripped content is a no-op (fast path)."""
        parts = [_text_part("x"), _img_part(DATA_URL)]
        first = SessionDB._strip_image_blobs(parts)
        second = SessionDB._strip_image_blobs(first)
        assert second is first  # identity — fast path triggered


# ── _encode_content integration ───────────────────────────────────────────────


class TestEncodeContentStripsBlobs:
    def test_scalar_passthrough(self):
        assert SessionDB._encode_content("hello") == "hello"
        assert SessionDB._encode_content(None) is None

    def test_data_url_stripped_in_encoded_json(self):
        parts = [
            _text_part("[Image attached at: /tmp/a.jpg]"),
            _img_part(DATA_URL),
        ]
        encoded = SessionDB._encode_content(parts)
        assert isinstance(encoded, str)
        assert encoded.startswith(PREFIX)
        decoded = json.loads(encoded[len(PREFIX):])
        # blob must not appear in the stored JSON
        assert DATA_URL not in encoded
        assert decoded[1] == {"type": "text", "text": PLACEHOLDER}

    def test_https_url_preserved_in_encoded_json(self):
        parts = [_text_part("caption"), _img_part(HTTPS_URL)]
        encoded = SessionDB._encode_content(parts)
        decoded = json.loads(encoded[len(PREFIX):])
        assert decoded[1] == _img_part(HTTPS_URL)

    def test_roundtrip_decode_has_no_blob(self):
        """encode → decode must never restore a base64 blob."""
        parts = [
            _text_part("[Image attached at: /tmp/b.png]"),
            _img_part(DATA_URL),
        ]
        encoded = SessionDB._encode_content(parts)
        decoded = SessionDB._decode_content(encoded)
        assert isinstance(decoded, list)
        # The image_url part is gone; only placeholder text remains
        urls = [
            p.get("image_url", {}).get("url", "")
            for p in decoded
            if isinstance(p, dict) and p.get("type") == "image_url"
        ]
        assert not any(u.startswith("data:") for u in urls)
