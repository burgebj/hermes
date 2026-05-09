"""Last.fm integration plugin for Hermes.

Provides 5 tools covering music discovery, artist/track/tag metadata and charts.
No OAuth required — only a free Last.fm API key (LASTFM_API_KEY env var).

Tools:
  lastfm_discover  — multi-seed similarity discovery
  lastfm_artist    — artist info, top tracks/albums/tags, similar artists
  lastfm_track     — track info, similar tracks, search
  lastfm_tag       — genre/mood exploration
  lastfm_charts    — trending charts (global or by country)

Setup:
  1. Get a free key at https://www.last.fm/api/account/create
  2. Add to your shell:  export LASTFM_API_KEY="your_key_here"
  3. Or set it in ~/.hermes/config.yaml under env_vars (if your Hermes build supports it)
"""

from __future__ import annotations

from plugins.lastfm.tools import (
    LASTFM_ARTIST_SCHEMA,
    LASTFM_CHARTS_SCHEMA,
    LASTFM_DISCOVER_SCHEMA,
    LASTFM_TAG_SCHEMA,
    LASTFM_TRACK_SCHEMA,
    _check_lastfm_available,
    _handle_lastfm_artist,
    _handle_lastfm_charts,
    _handle_lastfm_discover,
    _handle_lastfm_tag,
    _handle_lastfm_track,
)

_TOOLS = (
    ("lastfm_discover", LASTFM_DISCOVER_SCHEMA, _handle_lastfm_discover, "🎵"),
    ("lastfm_artist",   LASTFM_ARTIST_SCHEMA,   _handle_lastfm_artist,   "🎤"),
    ("lastfm_track",    LASTFM_TRACK_SCHEMA,    _handle_lastfm_track,    "🎶"),
    ("lastfm_tag",      LASTFM_TAG_SCHEMA,      _handle_lastfm_tag,      "🏷️"),
    ("lastfm_charts",   LASTFM_CHARTS_SCHEMA,   _handle_lastfm_charts,   "📈"),
)


def register(ctx) -> None:
    """Register all Last.fm tools. Called once by the plugin loader."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="lastfm",
            schema=schema,
            handler=handler,
            check_fn=_check_lastfm_available,
            emoji=emoji,
        )
