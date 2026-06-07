"""DuckDuckGo search — plugin form (via the ``ddgs`` package).

Subclasses the plugin-facing :class:`agent.web_search_provider.WebSearchProvider`.
The legacy in-tree module ``tools.web_providers.ddgs`` was removed in the
same commit that moved this code under ``plugins/``; this file is now the
canonical implementation.

The ``ddgs`` package is an optional dependency. ``is_available()`` reflects
whether the package is importable; the plugin still registers either way so
``hermes tools`` can prompt the user to install it.
"""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Any, Dict

from agent.web_search_provider import WebSearchProvider

logger = logging.getLogger(__name__)

# Maximum wall-clock time (seconds) for a single DDGS search call.
# DuckDuckGo's HTML-scrape backend can chain multiple engines; without an
# overall timeout a slow/rate-limited backend can block the agent loop
# indefinitely (#36776).
_DDGS_SEARCH_TIMEOUT = 30


class DDGSWebSearchProvider(WebSearchProvider):
    """DuckDuckGo HTML-scrape search provider.

    No API key needed. Rate limits are enforced server-side by DuckDuckGo;
    the provider surfaces ``DuckDuckGoSearchException`` and other ddgs errors
    as ``{"success": False, "error": ...}`` rather than raising.
    """

    @property
    def name(self) -> str:
        return "ddgs"

    @property
    def display_name(self) -> str:
        return "DuckDuckGo (ddgs)"

    def is_available(self) -> bool:
        """Return True when the ``ddgs`` package is importable.

        Probes the import once; cheap because Python caches the import. Must
        NOT perform network I/O — runs at tool-registration time and on every
        ``hermes tools`` paint.
        """
        try:
            import ddgs  # noqa: F401

            return True
        except ImportError:
            return False

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return False

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Execute a DuckDuckGo search and return normalized results."""
        try:
            from ddgs import DDGS  # type: ignore
        except ImportError:
            return {
                "success": False,
                "error": "ddgs package is not installed — run `pip install ddgs`",
            }

        # DDGS().text yields at most `max_results` items; we cap defensively
        # in case the package ignores the hint.
        safe_limit = max(1, int(limit))

        try:
            # Run the blocking DDGS().text() call in a worker thread so we can
            # enforce an overall wall-clock timeout.  The DDGS constructor's
            # ``timeout`` parameter only governs individual HTTP requests;
            # multi-engine chaining in ``_search_sync`` can still hang
            # indefinitely when a backend rate-limits or stalls (#36776).
            def _do_search():
                web_results = []
                with DDGS(timeout=10) as client:
                    for i, hit in enumerate(client.text(query, max_results=safe_limit)):
                        if i >= safe_limit:
                            break
                        url = str(hit.get("href") or hit.get("url") or "")
                        web_results.append(
                            {
                                "title": str(hit.get("title", "")),
                                "url": url,
                                "description": str(hit.get("body", "")),
                                "position": i + 1,
                            }
                        )
                return web_results

            web_results = concurrent.futures.ThreadPoolExecutor(
                max_workers=1
            ).submit(_do_search).result(timeout=_DDGS_SEARCH_TIMEOUT)
        except concurrent.futures.TimeoutError:
            logger.warning("DDGS search timed out after %ds: '%s'", _DDGS_SEARCH_TIMEOUT, query)
            return {"success": False, "error": f"DuckDuckGo search timed out after {_DDGS_SEARCH_TIMEOUT}s"}
        except Exception as exc:  # noqa: BLE001 — ddgs raises its own exceptions
            logger.warning("DDGS search error: %s", exc)
            return {"success": False, "error": f"DuckDuckGo search failed: {exc}"}

        logger.info("DDGS search '%s': %d results (limit %d)", query, len(web_results), limit)
        return {"success": True, "data": {"web": web_results}}

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "DuckDuckGo (ddgs)",
            "badge": "free · no key · search only",
            "tag": "Search via the ddgs Python package — no API key (pair with any extract provider)",
            "env_vars": [],
            # Trigger `_run_post_setup("ddgs")` after the user picks this row
            # so the ddgs Python package gets pip-installed on first selection.
            "post_setup": "ddgs",
        }
