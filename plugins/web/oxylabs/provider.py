"""Oxylabs AI Studio web search + extract — plugin form.

Subclasses :class:`agent.web_search_provider.WebSearchProvider`. Two
capabilities advertised:

- ``supports_search()``  -> True  (Oxylabs ``AiSearch.search``)
- ``supports_extract()`` -> True  (Oxylabs ``AiScraper.scrape_async``)

The SDK exposes a native async variant for scrape, so the per-URL
extract loop goes straight through ``await`` — no ``asyncio.to_thread``
wrap needed. Search uses the sync variant; the dispatcher wraps when
the caller is async.

Config keys this provider responds to::

    web:
      search_backend: "oxylabs"     # explicit per-capability
      extract_backend: "oxylabs"    # explicit per-capability
      backend: "oxylabs"            # shared fallback for both

Env var::

    OXYLABS_AI_STUDIO_API_KEY=...   # https://aistudio.oxylabs.io/api-key

Forward-compat kwargs honored on ``extract``:

- ``render_javascript`` (bool)  — JS-render the page before extraction.
- ``geo_location`` (str)        — geo-target the request (e.g. "Germany").
- ``format`` (str)              — ``"markdown"`` (default), ``"json"``,
                                  ``"html"`` (mapped to ``markdown`` —
                                  Oxylabs does not return raw HTML from
                                  AiScraper).

Post-redirect URL re-check: the SDK does not expose the final URL after
redirects, so :func:`tools.website_policy.check_website_access` only runs
pre-flight against the URL the caller passed. Revisit when the SDK adds
redirect transparency.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from agent.web_search_provider import WebSearchProvider
from tools.website_policy import check_website_access

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SDK client construction (lazy import per Exa pattern)
# ---------------------------------------------------------------------------
#
# We instantiate the two SDK app classes (AiSearch, AiScraper) lazily on
# first use and cache them as attributes on the provider instance. The
# SDK construction itself is cheap (just stores the API key + builds an
# httpx client), but the package import path pulls Pydantic models for
# every app — better to defer until the user actually routes a call here.


_API_KEY_ENV = "OXYLABS_AI_STUDIO_API_KEY"
_API_KEY_URL = "https://aistudio.oxylabs.io/api-key"
_LAZY_DEPS_KEY = "search.oxylabs"

# Integration tag the Oxylabs SDK sends as User-Agent on every request so
# the vendor can attribute traffic back to Hermes.
_HERMES_INTEGRATION_TAG = "hermes-agent"
_integration_tag_set = False


def _read_api_key() -> str:
    """Return the configured API key, or raise ``ValueError`` if unset."""
    api_key = os.getenv(_API_KEY_ENV, "").strip()
    if not api_key:
        raise ValueError(
            f"{_API_KEY_ENV} environment variable not set. "
            f"Get your API key at {_API_KEY_URL}"
        )
    return api_key


def _ensure_sdk_installed() -> None:
    """Trigger a venv-scoped pip install of ``oxylabs-ai-studio`` if missing.

    Mirrors the ``ensure("search.<vendor>", prompt=False)`` pattern used
    by the other bundled web providers. Requires a matching entry in
    :data:`tools.lazy_deps.LAZY_DEPS` (added in this PR's core edit). Gated
    upstream by ``security.allow_lazy_installs`` (default True); users in
    locked-down environments who disable that flag will fall through to a
    plain ``ImportError`` at the actual SDK import site, with the standard
    install hint surfaced through the error envelope.
    """
    try:
        from tools.lazy_deps import ensure as _lazy_ensure  # noqa: WPS433

        _lazy_ensure(_LAZY_DEPS_KEY, prompt=False)
    except ImportError:
        # Older Hermes without lazy_deps — leave the SDK import to fail
        # naturally; the caller's ImportError handler surfaces the hint.
        pass
    except Exception as exc:  # noqa: BLE001 — lazy_deps surfaces install hints
        raise ImportError(str(exc))


def _set_integration_tag() -> None:
    """Stamp Hermes' integration tag into the SDK's User-Agent header.

    The Oxylabs SDK reads its User-Agent via ``_resolve_ua()`` which
    consults a module-level ``_UA_API`` variable, defaulting to
    ``"python-sdk"`` when unset. Setting it before any client is
    constructed means every outbound API call from Hermes carries
    ``User-Agent: hermes-agent``, giving Oxylabs accurate vendor-side
    attribution. Idempotent and lazy — only runs once per process and
    only after the SDK is importable.

    """
    global _integration_tag_set
    if _integration_tag_set:
        return
    try:
        import oxylabs_ai_studio.client as _client  # noqa: WPS433

        # Don't clobber a value the user already set.
        if not getattr(_client, "_UA_API", None):
            _client._UA_API = _HERMES_INTEGRATION_TAG
        _integration_tag_set = True
    except ImportError:
        # SDK not importable — let the actual client construction site
        # surface the install hint via its ImportError handler.
        pass


# ---------------------------------------------------------------------------
# Response shape normalization
# ---------------------------------------------------------------------------
#
# The SDK returns Pydantic models (AiSearchJob, AiScraperJob)
# whose ``data`` attribute is typed loosely:
#
#   AiSearchJob.data:  list[SearchResult] | None
#   AiScraperJob.data: dict[str, Any] | str | None


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    """Convert Pydantic / dict-like values to a plain dict."""
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:  # noqa: BLE001
            return {}
    if hasattr(value, "__dict__"):
        return {k: v for k, v in value.__dict__.items() if not k.startswith("_")}
    return {}


def _scrape_data_to_content(data: Any) -> str:
    """Reduce ``AiScraperJob.data`` to a string for ``content`` / ``raw_content``."""
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        # JSON output_format — keep the structured payload as a stringified
        # body so downstream LLM post-processing has something to chew on.
        # The dict is also surfaced separately under ``metadata``.
        import json

        try:
            return json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return str(data)
    return str(data)


# ---------------------------------------------------------------------------
# Kwarg unpacking
# ---------------------------------------------------------------------------


def _normalize_format_kwarg(format_value: Optional[str], default: str = "markdown") -> str:
    """Map dispatcher ``format`` values to Oxylabs ``output_format`` literals.

    Hermes' dispatcher passes ``"markdown"`` / ``"html"``; Oxylabs AiScraper
    supports ``"markdown"``, ``"json"``, ``"csv"``, ``"screenshot"``, and
    ``"toon"``. Map ``"html"`` to ``"markdown"`` and pass through
    Oxylabs-native values as-is.
    """
    if not format_value:
        return default
    if format_value == "html":
        return "markdown"
    if format_value in ("markdown", "json", "csv", "screenshot", "toon"):
        return format_value
    return default


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------


class OxylabsWebSearchProvider(WebSearchProvider):
    """Oxylabs AI Studio search + extract provider."""

    def __init__(self) -> None:
        self._search_client: Any = None
        self._scraper_client: Any = None
        self._cached_api_key: Optional[str] = None

    # ------------------------------------------------------------------ ABC

    @property
    def name(self) -> str:
        return "oxylabs"

    @property
    def display_name(self) -> str:
        return "Oxylabs AI Studio"

    def is_available(self) -> bool:
        """Return True when ``OXYLABS_AI_STUDIO_API_KEY`` is set."""
        return bool(os.getenv(_API_KEY_ENV, "").strip())

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return True

    # -------------------------------------------------------- client helpers

    def _invalidate_cache_if_key_changed(self, api_key: str) -> None:
        """Drop cached SDK clients when the API key changes between calls."""
        if self._cached_api_key != api_key:
            self._search_client = None
            self._scraper_client = None
            self._cached_api_key = api_key

    def _get_search_client(self) -> Any:
        api_key = _read_api_key()
        self._invalidate_cache_if_key_changed(api_key)
        if self._search_client is None:
            _ensure_sdk_installed()
            _set_integration_tag()
            from oxylabs_ai_studio.apps.ai_search import AiSearch  # noqa: WPS433

            self._search_client = AiSearch(api_key=api_key)
        return self._search_client

    def _get_scraper_client(self) -> Any:
        api_key = _read_api_key()
        self._invalidate_cache_if_key_changed(api_key)
        if self._scraper_client is None:
            _ensure_sdk_installed()
            _set_integration_tag()
            from oxylabs_ai_studio.apps.ai_scraper import AiScraper  # noqa: WPS433

            self._scraper_client = AiScraper(api_key=api_key)
        return self._scraper_client

    def _reset_clients_for_tests(self) -> None:
        """Drop cached SDK clients so tests can re-instantiate cleanly."""
        self._search_client = None
        self._scraper_client = None
        self._cached_api_key = None

    # ------------------------------------------------------------------ search

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Execute an Oxylabs AI search.

        Sync; matches the ``AiSearch.search`` SDK signature. Returns the
        legacy ``{"success": True, "data": {"web": [{...}, ...]}}`` envelope
        on success, ``{"success": False, "error": str}`` on in-flight failure.

        Pre-flight errors (``ValueError`` from missing
        ``OXYLABS_AI_STUDIO_API_KEY``, ``ImportError`` from missing SDK)
        propagate to the dispatcher's top-level handler, which wraps them
        as ``tool_error(...)`` — matching the legacy
        ``{"error": "Error searching web: ..."}`` envelope. Only in-flight
        errors are caught and surfaced as
        ``{"success": False, "error": ...}``.

        Drops the optional ``content`` field from each ``SearchResult`` —
        search results are listings only; per-URL content belongs in
        :meth:`extract`.
        """
        from tools.interrupt import is_interrupted

        if is_interrupted():
            return {"success": False, "error": "Interrupted"}

        logger.info(
            "Oxylabs search: query=%r limit=%d return_content=False",
            query,
            limit,
        )
        # _get_search_client() raises ValueError / ImportError on unconfigured
        # systems — let it propagate so the dispatcher emits the legacy
        # envelope shape ({"error": "Error searching web: ..."}).
        client = self._get_search_client()
        try:
            response = client.search(
                query=query,
                limit=limit,
                return_content=False,
            )

            web_results: List[Dict[str, Any]] = []
            for i, result in enumerate(response.data or []):
                result_map = _coerce_mapping(result)
                web_results.append(
                    {
                        "title": result_map.get("title", "") or "",
                        "url": result_map.get("url", "") or "",
                        "description": result_map.get("description", "") or "",
                        "position": i + 1,
                    }
                )

            return {"success": True, "data": {"web": web_results}}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Oxylabs search error: %s", exc)
            return {"success": False, "error": f"Oxylabs search failed: {exc}"}

    # ------------------------------------------------------------------ extract

    async def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """Extract content from one or more URLs via Oxylabs AI Scraper.

        Async; uses the SDK's native ``scrape_async``. Each URL is scraped
        with a 60s ``asyncio.wait_for`` guard. Per-URL failures (timeout,
        SSRF / policy block, SDK error) become items with an ``error``
        field rather than raising.

        Recognized kwargs (others ignored for forward compat):
        - ``format``: see :func:`_normalize_format_kwarg`. Default markdown.
        - ``render_javascript``: bool (default False).
        - ``geo_location``: str.
        """
        from tools.interrupt import is_interrupted as _is_interrupted

        if _is_interrupted():
            return [{"url": u, "error": "Interrupted", "title": ""} for u in urls]

        output_format = _normalize_format_kwarg(kwargs.get("format"))
        render_javascript = bool(kwargs.get("render_javascript", False))
        geo_location = kwargs.get("geo_location")

        # Pre-flight API key / SDK availability check — fail the whole
        # batch fast rather than per-URL.
        try:
            client = self._get_scraper_client()
        except ValueError as exc:
            return [
                {"url": u, "title": "", "content": "", "error": str(exc)} for u in urls
            ]
        except ImportError as exc:
            err = f"oxylabs-ai-studio SDK not installed: {exc}"
            return [{"url": u, "title": "", "content": "", "error": err} for u in urls]

        results: List[Dict[str, Any]] = []
        for url in urls:
            if _is_interrupted():
                results.append({"url": url, "error": "Interrupted", "title": ""})
                continue

            # Website-access policy gate. The SDK doesn't expose the
            # post-redirect URL, so we only gate on the input — see the
            # module docstring.
            blocked = check_website_access(url)
            if blocked:
                logger.info(
                    "Blocked Oxylabs extract for %s by rule %s",
                    blocked["host"],
                    blocked["rule"],
                )
                results.append(
                    {
                        "url": url,
                        "title": "",
                        "content": "",
                        "error": blocked["message"],
                        "blocked_by_policy": {
                            "host": blocked["host"],
                            "rule": blocked["rule"],
                            "source": blocked["source"],
                        },
                    }
                )
                continue

            try:
                logger.info(
                    "Oxylabs scrape: url=%r output_format=%r "
                    "render_javascript=%s geo_location=%r",
                    url,
                    output_format,
                    render_javascript,
                    geo_location,
                )
                try:
                    job = await asyncio.wait_for(
                        client.scrape_async(
                            url=url,
                            output_format=output_format,
                            render_javascript=render_javascript,
                            geo_location=geo_location,
                        ),
                        timeout=60,
                    )
                except asyncio.TimeoutError:
                    logger.warning("Oxylabs scrape timed out for %s", url)
                    results.append(
                        {
                            "url": url,
                            "title": "",
                            "content": "",
                            "error": (
                                "Scrape timed out after 60s — page may be too "
                                "large or unresponsive. Try browser_navigate "
                                "instead."
                            ),
                        }
                    )
                    continue

                content = _scrape_data_to_content(job.data)
                metadata: Dict[str, Any] = {"sourceURL": url}
                if isinstance(job.data, dict):
                    metadata["extracted"] = job.data
                if job.run_id:
                    metadata["oxylabs_run_id"] = job.run_id

                results.append(
                    {
                        "url": url,
                        "title": "",
                        "content": content,
                        "raw_content": content,
                        "metadata": metadata,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("Oxylabs scrape failed for %s: %s", url, exc)
                results.append(
                    {
                        "url": url,
                        "title": "",
                        "content": "",
                        "raw_content": "",
                        "error": str(exc),
                    }
                )

        return results

    # ------------------------------------------------------------ setup hint

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Oxylabs AI Studio",
            "badge": "paid",
            "tag": (
                "Search + extract backed by Oxylabs' AI Studio. "
                "Per-call render_javascript and geo_location supported."
            ),
            "env_vars": [
                {
                    "key": _API_KEY_ENV,
                    "prompt": "Oxylabs AI Studio API key",
                    "url": _API_KEY_URL,
                },
            ],
        }
