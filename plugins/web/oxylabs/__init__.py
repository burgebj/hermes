"""Oxylabs AI Studio web provider plugin — bundled, auto-loaded.

Backed by the official ``oxylabs-ai-studio`` SDK. Exposes the three
``WebSearchProvider`` capabilities (search + extract + crawl) backed by
the AiSearch, AiScraper, and AiCrawler apps respectively.

Browser Agent and AI-Map are not surfaced through this provider — the
ABC has no slot for them. They're candidates for a future sibling tool
plugin under ``plugins/oxylabs/``.
"""

from __future__ import annotations

from plugins.web.oxylabs.provider import OxylabsWebSearchProvider


def register(ctx) -> None:
    """Register the Oxylabs provider with the plugin context."""
    ctx.register_web_search_provider(OxylabsWebSearchProvider())
