"""Regression tests for binary file preservation through GitHub's Contents API.

GitHub serves binary blobs through the Contents API with
``Content-Type: application/vnd.github.v3.raw; charset=utf-8`` — a mislabel
that causes ``httpx.Response.text`` to UTF-8-decode binary content with
``errors='replace'``, silently corrupting every non-ASCII byte. A PNG's
leading 0x89 becomes the U+FFFD replacement char (``ef bf bd``), the file
roughly doubles in size, and ``file(1)`` reports ``data`` instead of
``PNG image data``.

These tests pin the GitHub source's fetch path to bytes-preserving behavior.
The writer (``quarantine_bundle``) already has binary coverage at
``TestQuarantineBundleBinaryAssets``; this file covers the missing fetch-side gap.
"""

import os
from unittest.mock import MagicMock, patch

import httpx

from tools.skills_hub import GitHubAuth, GitHubSource


# Canonical PNG file signature: 89 50 4e 47 0d 0a 1a 0a.
# The leading 0x89 is the byte that gets mangled to U+FFFD when decoded as UTF-8.
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def _github_raw_response(content: bytes) -> MagicMock:
    """Mock httpx response that mimics GitHub's Contents API raw view.

    GitHub returns binary content with a ``charset=utf-8`` Content-Type header
    on the raw view. The mock mirrors that so ``resp.text`` would corrupt the
    bytes — proving the fix doesn't rely on ``resp.text`` for the binary path.
    """
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.content = content
    resp.headers = {"content-type": "application/vnd.github.v3.raw; charset=utf-8"}
    resp.text = content.decode("utf-8", errors="replace")
    return resp


class TestFetchFileContentBinary:
    """`_fetch_file_content` must return raw bytes for binary files."""

    def _source(self) -> GitHubSource:
        auth = MagicMock(spec=GitHubAuth)
        auth.get_headers.return_value = {}
        return GitHubSource(auth=auth)

    @patch("tools.skills_hub.httpx.get")
    def test_png_header_preserved_byte_for_byte(self, mock_get):
        png_bytes = PNG_HEADER + os.urandom(1024)
        mock_get.return_value = _github_raw_response(png_bytes)

        # Sanity check the fixture: resp.text WOULD corrupt these bytes.
        assert mock_get.return_value.text.encode("utf-8") != png_bytes

        result = self._source()._fetch_file_content("owner/repo", "logo.png")

        assert isinstance(result, bytes)
        assert result == png_bytes
        assert result[:8] == PNG_HEADER

    @patch("tools.skills_hub.httpx.get")
    def test_jpeg_high_bytes_not_corrupted(self, mock_get):
        """JPEG's FF D8 FF E0 header has every byte >= 0x80 — worst case for UTF-8 decode."""
        jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + os.urandom(512)
        mock_get.return_value = _github_raw_response(jpeg_bytes)

        result = self._source()._fetch_file_content("owner/repo", "photo.jpg")

        assert result == jpeg_bytes
        assert result[:4] == b"\xff\xd8\xff\xe0"

    @patch("tools.skills_hub.httpx.get")
    def test_utf8_text_still_returned_as_bytes(self, mock_get):
        """SKILL.md and other text files still round-trip cleanly. Callers decode."""
        skill_md = b"---\nname: example\ndescription: A test.\n---\n\n# Body\n"
        mock_get.return_value = _github_raw_response(skill_md)

        result = self._source()._fetch_file_content("owner/repo", "SKILL.md")

        assert isinstance(result, bytes)
        assert result == skill_md
        assert result.decode("utf-8").startswith("---\nname: example")


class TestDownloadDirectoryBinary:
    """End-to-end: binary bytes survive `_download_directory_recursive` into the files dict."""

    def _source(self) -> GitHubSource:
        auth = MagicMock(spec=GitHubAuth)
        auth.get_headers.return_value = {}
        return GitHubSource(auth=auth)

    @patch.object(GitHubSource, "_fetch_file_content")
    @patch("tools.skills_hub.httpx.get")
    def test_recursive_download_preserves_binary_entries(self, mock_get, mock_fetch):
        png_bytes = PNG_HEADER + os.urandom(256)
        contents_resp = MagicMock(status_code=200, json=lambda: [
            {"name": "SKILL.md", "path": "skills/my-skill/SKILL.md", "type": "file"},
            {"name": "logo.png", "path": "skills/my-skill/logo.png", "type": "file"},
        ])
        mock_get.return_value = contents_resp
        mock_fetch.side_effect = lambda repo, path: (
            png_bytes if path.endswith(".png") else b"---\nname: x\n---\n"
        )

        files = self._source()._download_directory_recursive("owner/repo", "skills/my-skill")

        assert "logo.png" in files
        assert files["logo.png"] == png_bytes
        assert files["logo.png"][:8] == PNG_HEADER
        assert isinstance(files["SKILL.md"], bytes)
