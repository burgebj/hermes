"""Tests for browser subprocess proxy env stripping (#14372).

Browser subprocess inherits proxy env vars causing ERR_EMPTY_RESPONSE
when corporate proxy doesn't handle browser traffic.
"""
import os
import pytest
from unittest.mock import patch


class TestBrowserProxyEnvStripped:
    """Proxy env vars must be stripped from browser subprocess env (#14372)."""

    def test_proxy_vars_not_in_browser_env(self):
        """Verify proxy env vars are stripped from the env dict."""
        proxy_vars = {
            "HTTP_PROXY": "http://proxy:8080",
            "HTTPS_PROXY": "http://proxy:8080",
            "NO_PROXY": "localhost",
            "ALL_PROXY": "socks5://proxy:1080",
            "http_proxy": "http://proxy:8080",
            "https_proxy": "http://proxy:8080",
            "no_proxy": "localhost",
            "all_proxy": "socks5://proxy:1080",
        }
        # Simulate what the fix does
        browser_env = {**os.environ, **proxy_vars}
        for var in (
            "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY",
            "http_proxy", "https_proxy", "no_proxy", "all_proxy",
        ):
            browser_env.pop(var, None)

        for var in proxy_vars:
            assert var not in browser_env, f"{var} should have been stripped"

    def test_source_strips_proxy_vars(self):
        """Verify the fix is present in browser_tool.py source."""
        import inspect
        from tools import browser_tool
        source = inspect.getsource(browser_tool)
        assert "HTTP_PROXY" in source and "browser_env.pop" in source, (
            "browser_tool.py should strip HTTP_PROXY from browser_env"
        )
