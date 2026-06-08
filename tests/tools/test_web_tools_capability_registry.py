"""Tests for plugin-provided web backends being selectable via
``web.{capability}_backend`` and for web_extract falling through to the
registry instead of dead-ending on a search-only fallback.

Regression coverage for two linked bugs in ``tools.web_tools``:

1. A backend named in ``web.extract_backend`` / ``web.search_backend`` that is
   registered in the web provider registry but absent from the hardcoded
   ``_is_backend_available`` allowlist was silently discarded in favor of
   ``web.backend`` (``_get_capability_backend``).
2. ``web_extract_tool`` returned a dead-end "search-only backend" error when
   the pre-selected backend was search-only, instead of consulting the
   registry's active extract provider (issue #32698).
"""

import json
from typing import Any, Dict, List

import pytest
from unittest.mock import patch

from agent import web_search_registry
from agent.web_search_provider import WebSearchProvider
import tools.web_tools as web_tools


def _make_provider(
    name: str,
    *,
    available: bool = True,
    search: bool = False,
    extract: bool = False,
    display_name: str = "",
) -> WebSearchProvider:
    """Build a fake WebSearchProvider with the given name and capabilities.

    Collapses what would otherwise be near-identical provider subclasses
    (extract-only plugin, search-only backend, registered-but-unavailable).
    """

    class _Fake(WebSearchProvider):
        @property
        def name(self) -> str:
            return name

        @property
        def display_name(self) -> str:
            return display_name or name

        def is_available(self) -> bool:
            return available

        def supports_search(self) -> bool:
            return search

        def supports_extract(self) -> bool:
            return extract

        def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
            return {"success": True, "data": {"web": []}}

        def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
            return [
                {"url": u, "title": "t", "content": "body", "raw_content": "body"}
                for u in urls
            ]

    return _Fake()


class TestCapabilityBackendRegistry:
    def setup_method(self):
        # Extract-only plugin (markdown-chain), search-only backend
        # (brave-free / searxng), and an extract-capable backend that is
        # registered but unavailable (e.g. exa with no API key).
        self._extract = _make_provider("myplugin-extract", extract=True)
        self._searchonly = _make_provider(
            "myplugin-searchonly", search=True,
            display_name="My Plugin (search only)",
        )
        self._unavailable = _make_provider(
            "myplugin-unavailable", available=False, search=True, extract=True,
        )
        for provider in (self._extract, self._searchonly, self._unavailable):
            web_search_registry.register_provider(provider)

    def teardown_method(self):
        # Remove only what this test added; leave any other providers intact.
        with web_search_registry._lock:
            web_search_registry._providers.pop("myplugin-extract", None)
            web_search_registry._providers.pop("myplugin-searchonly", None)
            web_search_registry._providers.pop("myplugin-unavailable", None)

    # --- Fix A: registry-aware selection -----------------------------------

    def test_plugin_extract_backend_is_selected(self):
        cfg = {"backend": "brave-free", "extract_backend": "myplugin-extract"}
        with patch.object(web_tools, "_load_web_config", return_value=cfg):
            assert web_tools._get_extract_backend() == "myplugin-extract"

    def test_plugin_search_backend_is_selected(self):
        cfg = {"backend": "firecrawl", "search_backend": "myplugin-searchonly"}
        with patch.object(web_tools, "_load_web_config", return_value=cfg):
            assert web_tools._get_search_backend() == "myplugin-searchonly"

    def test_search_only_plugin_not_selected_for_extract(self):
        # A registered provider that does NOT support extract must not win the
        # extract capability — fall back to _get_backend() instead.
        cfg = {"backend": "brave-free", "extract_backend": "myplugin-searchonly"}
        with patch.object(web_tools, "_load_web_config", return_value=cfg), \
             patch.object(web_tools, "_get_backend", return_value="firecrawl"):
            assert web_tools._get_extract_backend() == "firecrawl"

    def test_registered_but_unavailable_backend_not_selected(self):
        # A registered, extract-capable provider whose is_available() is False
        # (e.g. built-in backend with no API key configured) must NOT win the
        # capability — fall back to _get_backend(), not silently select it.
        cfg = {"backend": "brave-free", "extract_backend": "myplugin-unavailable"}
        with patch.object(web_tools, "_load_web_config", return_value=cfg), \
             patch.object(web_tools, "_get_backend", return_value="firecrawl"):
            assert web_tools._get_extract_backend() == "firecrawl"

    def test_unregistered_backend_falls_back(self):
        cfg = {"backend": "brave-free", "extract_backend": "does-not-exist"}
        with patch.object(web_tools, "_load_web_config", return_value=cfg), \
             patch.object(web_tools, "_get_backend", return_value="firecrawl"):
            assert web_tools._get_extract_backend() == "firecrawl"

    # --- Fix B: dead-end fall-through to the registry ----------------------

    def test_web_extract_falls_through_search_only_to_registry(self):
        # Pre-selector resolves a search-only backend, but an extract-capable
        # provider is configured/registered: web_extract must use it, not error.
        with patch.object(web_tools, "_get_extract_backend", return_value="myplugin-searchonly"), \
             patch.object(web_tools, "is_safe_url", return_value=True), \
             patch.object(web_tools, "check_auxiliary_model", return_value=False), \
             patch("agent.web_search_registry.get_active_extract_provider", return_value=self._extract):
            out = json.loads(_run(web_tools.web_extract_tool(["https://example.com"])))
        assert "results" in out, out
        assert out["results"][0]["content"] == "body"

    def test_web_extract_search_only_with_no_extract_provider_errors_clearly(self):
        # No extract-capable provider anywhere: still error, but the message
        # must reflect actually-available backends, not a stale hardcoded list.
        with patch.object(web_tools, "_get_extract_backend", return_value="myplugin-searchonly"), \
             patch.object(web_tools, "is_safe_url", return_value=True), \
             patch("agent.web_search_registry.get_active_extract_provider", return_value=None):
            out = json.loads(_run(web_tools.web_extract_tool(["https://example.com"])))
        assert out["success"] is False
        assert "search-only" in out["error"]


def _run(coro):
    import asyncio
    return asyncio.run(coro)
