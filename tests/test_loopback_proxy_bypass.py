"""Tests for loopback-aware urlopen helper (GitHub #31421).

Internal HTTP probes to ``127.0.0.1`` / ``localhost`` must bypass any
configured ``HTTP_PROXY`` / ``HTTPS_PROXY``; external hosts must keep using
the proxy.
"""

import urllib.request
from unittest.mock import patch

import pytest

from utils import is_loopback_host, urlopen_bypass_proxy_for_loopback


@pytest.mark.parametrize(
    "host",
    ["127.0.0.1", "localhost", "LOCALHOST", "::1", "127.0.0.5", "localhost."],
)
def test_is_loopback_host_true(host):
    assert is_loopback_host(host) is True


@pytest.mark.parametrize(
    "host",
    ["", None, "gw", "example.com", "10.0.0.1", "192.168.1.1", "8.8.8.8"],
)
def test_is_loopback_host_false(host):
    assert is_loopback_host(host) is False


def test_loopback_url_bypasses_proxy():
    """A loopback URL is opened via an empty-proxy opener, not plain urlopen."""
    proxies_seen = {}

    class _FakeOpener:
        def open(self, request, timeout=None):  # noqa: ARG002
            return "loopback-response"

    def _fake_build_opener(*handlers):
        for h in handlers:
            if isinstance(h, urllib.request.ProxyHandler):
                proxies_seen.update(h.proxies)
        return _FakeOpener()

    with (
        patch("urllib.request.build_opener", side_effect=_fake_build_opener),
        patch("urllib.request.urlopen", side_effect=AssertionError("proxy path used")),
    ):
        result = urlopen_bypass_proxy_for_loopback(
            "http://127.0.0.1:8765/health", timeout=1
        )

    assert result == "loopback-response"
    # ProxyHandler({}) => no proxies configured => direct connection.
    assert proxies_seen == {}


def test_loopback_request_object_bypasses_proxy():
    """Works when passed a Request object, not just a URL string."""

    class _FakeOpener:
        def open(self, request, timeout=None):  # noqa: ARG002
            return "ok"

    with (
        patch("urllib.request.build_opener", return_value=_FakeOpener()),
        patch("urllib.request.urlopen", side_effect=AssertionError("proxy path used")),
    ):
        req = urllib.request.Request("http://localhost:9119/api/status", method="GET")
        assert urlopen_bypass_proxy_for_loopback(req, timeout=1) == "ok"


def test_external_url_uses_proxy_path():
    """Non-loopback hosts keep going through the normal proxy-aware urlopen."""
    with (
        patch(
            "urllib.request.urlopen", return_value="external-response"
        ) as mock_urlopen,
        patch(
            "urllib.request.build_opener",
            side_effect=AssertionError("bypass path used"),
        ),
    ):
        result = urlopen_bypass_proxy_for_loopback("http://gw:8642/health", timeout=1)

    assert result == "external-response"
    mock_urlopen.assert_called_once()
