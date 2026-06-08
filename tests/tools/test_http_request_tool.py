"""Tests for the HTTP Request tool.

Covers:
- Basic GET request shape (status, headers, body)
- POST with body and custom headers
- HTTPError handling (4xx, 5xx)
- URLError handling (network failure)
- SSRF / private-IP blocking
- URL scheme validation (file:// rejected)
- Secret exfiltration guard (URLs with embedded tokens blocked)
- Method validation
- Response size truncation
"""

import json
import urllib.error
from unittest.mock import patch, MagicMock

import pytest

from tools.http_request_tool import (
    http_request_tool,
    _check_http_request_requirements,
    _TIMEOUT_DEFAULT,
    _MAX_RESPONSE_SIZE_DEFAULT,
)


class _FakeResponse:
    """Mock urllib response."""

    def __init__(self, body_bytes=b"", status=200, reason="OK", headers=None):
        self._body = body_bytes
        self.code = status
        self.reason = reason
        self._headers = headers or {}

    def getcode(self):
        return self.code

    def getheaders(self):
        return list(self._headers.items())

    def read(self, size=-1):
        if size >= 0:
            return self._body[:size]
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# ---------------------------------------------------------------------------
# Success paths
# ---------------------------------------------------------------------------

def test_get_request_success(monkeypatch):
    """Basic GET returns structured JSON with all expected fields."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.method
        captured["headers"] = dict(req.headers)
        return _FakeResponse(
            body_bytes=b'{"data": "hello"}',
            status=200,
            reason="OK",
            headers={"Content-Type": "application/json"},
        )

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    result = json.loads(http_request_tool("https://api.example.com/v1/items"))

    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["status_text"] == "OK"
    assert result["headers"]["Content-Type"] == "application/json"
    assert result["body"] == '{"data": "hello"}'
    assert "elapsed_ms" in result
    assert result["elapsed_ms"] >= 0


def test_post_with_body_and_headers(monkeypatch):
    """POST with JSON body and custom headers forwarded correctly."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["method"] = req.method
        captured["body"] = req.data
        captured["headers"] = dict(req.headers)
        return _FakeResponse(
            body_bytes=b'{"id": 42}',
            status=201,
            reason="Created",
            headers={"Content-Type": "application/json"},
        )

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    result = json.loads(
        http_request_tool(
            "https://api.example.com/v1/items",
            method="POST",
            headers={"Authorization": "Bearer tok", "Content-Type": "application/json"},
            body='{"name": "foo"}',
        )
    )

    assert result["success"] is True
    assert result["status_code"] == 201
    assert captured["method"] == "POST"
    assert captured["body"] == b'{"name": "foo"}'
    assert captured["headers"]["Authorization"] == "Bearer tok"


def test_method_case_insensitive(monkeypatch):
    """Method is normalised to uppercase."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["method"] = req.method
        return _FakeResponse(body_bytes=b"", status=200)

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    http_request_tool("https://example.com", method="post")
    assert captured["method"] == "POST"


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_http_error_4xx(monkeypatch):
    """4xx responses are returned as structured error, not exceptions."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    class _FakeHTTPError(urllib.error.HTTPError):
        def __init__(self):
            # HTTPError expects (url, code, msg, hdrs, fp)
            super().__init__(
                "https://api.example.com/missing",
                404,
                "Not Found",
                {"Content-Type": "text/plain"},
                None,
            )
            self._body = b'{"error": "not found"}'

        def read(self, n=-1):
            return self._body[:n] if n >= 0 else self._body

    err = _FakeHTTPError()
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=None: (_ for _ in ()).throw(err))

    result = json.loads(http_request_tool("https://api.example.com/missing"))

    assert result["success"] is False
    assert result["status_code"] == 404
    assert result["status_text"] == "Not Found"
    assert result["error"] == "HTTP 404: Not Found"
    assert "body" in result


def test_url_error_network_failure(monkeypatch):
    """Network failures return structured error."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout=None: (_ for _ in ()).throw(
            urllib.error.URLError("Name or service not known")
        ),
    )

    result = json.loads(http_request_tool("https://dead-host.example"))

    assert result["success"] is False
    assert "Name or service not known" in result["error"]


# ---------------------------------------------------------------------------
# Security / validation
# ---------------------------------------------------------------------------

def test_rejects_non_http_scheme(monkeypatch):
    """file:// and ftp:// are rejected outright."""
    result = json.loads(http_request_tool("file:///etc/passwd"))
    assert result["success"] is False
    assert "http:// or https://" in result["error"]


def test_rejects_unsafe_url(monkeypatch):
    """SSRF protection blocks private/internal URLs."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: False
    )

    result = json.loads(http_request_tool("http://192.168.1.1/admin"))
    assert result["success"] is False
    assert "private" in result["error"].lower()


def test_rejects_url_with_embedded_secret(monkeypatch):
    """URLs containing API keys in query params are blocked."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    result = json.loads(
        http_request_tool("https://api.example.com?api_key=sk-12345678901234567890")
    )
    assert result["success"] is False
    assert "API key" in result["error"]


def test_rejects_unsupported_method():
    """Methods outside the allowed enum are rejected."""
    result = json.loads(http_request_tool("https://example.com", method="FOOBAR"))
    assert result["success"] is False
    assert "Unsupported" in result["error"]


# ---------------------------------------------------------------------------
# Response size cap
# ---------------------------------------------------------------------------

def test_response_truncation(monkeypatch):
    """Responses larger than max_response_size are truncated."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    large_body = b"x" * 200

    def _fake_urlopen(req, timeout=None):
        return _FakeResponse(body_bytes=large_body, status=200)

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    result = json.loads(
        http_request_tool(
            "https://example.com/big",
            max_response_size=50,
        )
    )

    assert result["success"] is True
    assert result["body"] == "x" * 50
    assert result["truncated"] is True
    assert "truncated" in result["note"].lower()


# ---------------------------------------------------------------------------
# Requirement check
# ---------------------------------------------------------------------------

def test_check_requirements_always_true():
    """http_request has no external dependency gate."""
    assert _check_http_request_requirements() is True


# ---------------------------------------------------------------------------
# Live integration (skipped if httpbin.org is down / unreachable)
# ---------------------------------------------------------------------------


def test_live_get_httpbin():
    """Smoke test against httpbin.org /get endpoint.

    Uses a short 5-second timeout so a slow/unreachable host is caught
    by the ``except`` block and converted to a skip rather than blowing
    the per-test 30-second pytest-timeout cap.
    """
    try:
        result = json.loads(http_request_tool("https://httpbin.org/get", timeout=5))
        assert result["success"] is True
        assert result["status_code"] == 200
        assert "headers" in result
    except Exception:
        pytest.skip("httpbin.org unreachable")


def test_live_post_httpbin():
    """Smoke test against httpbin.org /post endpoint.

    Uses a short 5-second timeout so a slow/unreachable host is caught
    by the ``except`` block and converted to a skip rather than blowing
    the per-test 30-second pytest-timeout cap.
    """
    try:
        result = json.loads(
            http_request_tool(
                "https://httpbin.org/post",
                method="POST",
                headers={"Content-Type": "application/json"},
                body='{"hello": "world"}',
                timeout=5,
            )
        )
        assert result["success"] is True
        assert result["status_code"] == 200
        # httpbin echoes the request body back in the response body
        assert "hello" in result["body"]
    except Exception:
        pytest.skip("httpbin.org unreachable")


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

def test_registry_has_http_request():
    """http_request is discoverable in the tool registry."""
    from tools.registry import discover_builtin_tools, registry

    discover_builtin_tools()
    entry = registry.get_entry("http_request")
    assert entry is not None
    assert entry.name == "http_request"
    assert entry.toolset == "web"
    assert entry.emoji == "🌐"


def test_toolset_includes_http_request():
    """http_request appears in the web toolset definitions."""
    from tools.registry import discover_builtin_tools, registry
    from toolsets import resolve_toolset

    discover_builtin_tools()
    web_tools = resolve_toolset("web")
    assert "http_request" in web_tools


# ---------------------------------------------------------------------------
# Handler dispatch through registry
# ---------------------------------------------------------------------------

def test_registry_dispatch(monkeypatch):
    """Registry.dispatch() correctly invokes the http_request handler."""
    from tools.registry import discover_builtin_tools, registry

    discover_builtin_tools()

    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    def _fake_urlopen(req, timeout=None):
        return _FakeResponse(
            body_bytes=b'{"ok": true}',
            status=200,
            headers={"Content-Type": "application/json"},
        )

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    result = json.loads(
        registry.dispatch("http_request", {"url": "https://api.example.com/test"})
    )

    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["body"] == '{"ok": true}'


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_url_rejected():
    """Empty or missing URL returns an error, not an exception."""
    result = json.loads(http_request_tool(""))
    assert result["success"] is False
    assert "URL" in result["error"]


def test_none_url_rejected():
    """None URL is coerced to empty string and rejected."""
    result = json.loads(http_request_tool(None))
    assert result["success"] is False
    assert "URL" in result["error"]


def test_head_request_no_body(monkeypatch):
    """HEAD request succeeds even with no response body."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    def _fake_urlopen(req, timeout=None):
        assert req.method == "HEAD"
        return _FakeResponse(body_bytes=b"", status=200, headers={"X-Count": "42"})

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    result = json.loads(
        http_request_tool("https://example.com/items", method="HEAD")
    )
    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["headers"]["X-Count"] == "42"


def test_delete_request(monkeypatch):
    """DELETE request is forwarded correctly."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["method"] = req.method
        return _FakeResponse(body_bytes=b"", status=204, reason="No Content")

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    result = json.loads(
        http_request_tool("https://api.example.com/items/42", method="DELETE")
    )
    assert result["success"] is True
    assert result["status_code"] == 204
    assert captured["method"] == "DELETE"


def test_unicode_body_and_response(monkeypatch):
    """Unicode characters round-trip correctly."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    def _fake_urlopen(req, timeout=None):
        return _FakeResponse(
            body_bytes='{"message": "Merhaba dünya 🌍"}'.encode("utf-8"),
            status=200,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    result = json.loads(
        http_request_tool(
            "https://api.example.com/greet",
            method="POST",
            body='{"msg": "Merhaba dünya 🌍"}',
        )
    )
    assert result["success"] is True
    assert "Merhaba dünya 🌍" in result["body"]


def test_5xx_error(monkeypatch):
    """5xx responses include status_code in the error JSON."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    err = urllib.error.HTTPError(
        "https://api.example.com/bad",
        503,
        "Service Unavailable",
        {"Retry-After": "120"},
        None,
    )

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout=None: (_ for _ in ()).throw(err),
    )

    result = json.loads(http_request_tool("https://api.example.com/bad"))
    assert result["success"] is False
    assert result["status_code"] == 503
    assert "Service Unavailable" in result["error"]


def test_patch_request(monkeypatch):
    """PATCH method is forwarded correctly."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["method"] = req.method
        captured["body"] = req.data
        return _FakeResponse(body_bytes=b'{"updated": true}', status=200)

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    result = json.loads(
        http_request_tool(
            "https://api.example.com/items/42",
            method="PATCH",
            body='{"name": "updated"}',
        )
    )
    assert result["success"] is True
    assert captured["method"] == "PATCH"
    assert captured["body"] == b'{"name": "updated"}'


def test_options_request(monkeypatch):
    """OPTIONS method returns allowed methods from server."""
    monkeypatch.setattr(
        "tools.http_request_tool.is_safe_url", lambda url: True
    )

    def _fake_urlopen(req, timeout=None):
        assert req.method == "OPTIONS"
        return _FakeResponse(
            body_bytes=b"",
            status=204,
            headers={"Allow": "GET, POST, HEAD, OPTIONS"},
        )

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)

    result = json.loads(
        http_request_tool("https://api.example.com/items", method="OPTIONS")
    )
    assert result["success"] is True
    assert result["status_code"] == 204
    assert result["headers"]["Allow"] == "GET, POST, HEAD, OPTIONS"
