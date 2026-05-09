"""Thin Last.fm Web API client used by Hermes native tools.

No OAuth required — Last.fm read-only endpoints only need a free API key.
Set LASTFM_API_KEY in your environment (or pass it at construction time).

Get a free key at: https://www.last.fm/api/account/create
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_BASE_URL = "https://ws.audioscrobbler.com/2.0/"
_DEFAULT_TIMEOUT = 12


class LastFmError(RuntimeError):
    """Base Last.fm client error."""


class LastFmAuthError(LastFmError):
    """Raised when LASTFM_API_KEY is missing or invalid."""


class LastFmAPIError(LastFmError):
    """Structured Last.fm API error (error code + message)."""

    def __init__(self, message: str, *, code: Optional[int] = None) -> None:
        super().__init__(message)
        self.code = code


class LastFmClient:
    """Minimal Last.fm API client (read-only, no auth flow needed)."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        # ~/.hermes/.env is loaded into os.environ at Hermes startup,
        # so os.getenv works after `hermes env` has saved the key.
        self._api_key = (api_key or os.getenv("LASTFM_API_KEY", "")).strip()
        if not self._api_key:
            raise LastFmAuthError(
                "LASTFM_API_KEY is not set. "
                "Run `hermes env` to configure it, or get a free key at "
                "https://www.last.fm/api/account/create"
            )

    # ── low-level ────────────────────────────────────────────────────────────

    def _call(self, method: str, **params: Any) -> Dict[str, Any]:
        """Make a GET request to the Last.fm API and return the parsed JSON."""
        qs = urllib.parse.urlencode({
            "method": method,
            "api_key": self._api_key,
            "format": "json",
            **{k: v for k, v in params.items() if v is not None},
        })
        url = f"{_BASE_URL}?{qs}"
        try:
            with urllib.request.urlopen(url, timeout=_DEFAULT_TIMEOUT) as resp:
                data: Dict[str, Any] = json.loads(resp.read())
        except Exception as exc:
            raise LastFmError(f"HTTP request failed ({method}): {exc}") from exc

        if "error" in data:
            raise LastFmAPIError(
                data.get("message", "Unknown Last.fm error"),
                code=int(data.get("error", 0)),
            )
        return data

    # ── artist ───────────────────────────────────────────────────────────────

    def artist_get_info(self, artist: str) -> Dict[str, Any]:
        return self._call("artist.getInfo", artist=artist)

    def artist_get_similar(self, artist: str, limit: int = 30) -> Dict[str, Any]:
        return self._call("artist.getSimilar", artist=artist, limit=limit)

    def artist_get_top_tracks(self, artist: str, limit: int = 10) -> Dict[str, Any]:
        return self._call("artist.getTopTracks", artist=artist, limit=limit)

    def artist_get_top_albums(self, artist: str, limit: int = 10) -> Dict[str, Any]:
        return self._call("artist.getTopAlbums", artist=artist, limit=limit)

    def artist_get_top_tags(self, artist: str) -> Dict[str, Any]:
        return self._call("artist.getTopTags", artist=artist)

    def artist_search(self, artist: str, limit: int = 10) -> Dict[str, Any]:
        return self._call("artist.search", artist=artist, limit=limit)

    # ── track ────────────────────────────────────────────────────────────────

    def track_get_info(self, artist: str, track: str) -> Dict[str, Any]:
        return self._call("track.getInfo", artist=artist, track=track)

    def track_get_similar(self, artist: str, track: str, limit: int = 20) -> Dict[str, Any]:
        return self._call("track.getSimilar", artist=artist, track=track, limit=limit)

    def track_search(self, track: str, artist: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        return self._call("track.search", track=track, artist=artist, limit=limit)

    # ── album ────────────────────────────────────────────────────────────────

    def album_get_info(self, artist: str, album: str) -> Dict[str, Any]:
        return self._call("album.getInfo", artist=artist, album=album)

    # ── tag / genre ──────────────────────────────────────────────────────────

    def tag_get_info(self, tag: str) -> Dict[str, Any]:
        return self._call("tag.getInfo", tag=tag)

    def tag_get_top_artists(self, tag: str, limit: int = 20) -> Dict[str, Any]:
        return self._call("tag.getTopArtists", tag=tag, limit=limit)

    def tag_get_top_tracks(self, tag: str, limit: int = 20) -> Dict[str, Any]:
        return self._call("tag.getTopTracks", tag=tag, limit=limit)

    def tag_get_top_albums(self, tag: str, limit: int = 10) -> Dict[str, Any]:
        return self._call("tag.getTopAlbums", tag=tag, limit=limit)

    def tag_get_similar(self, tag: str) -> Dict[str, Any]:
        return self._call("tag.getSimilar", tag=tag)

    # ── charts ───────────────────────────────────────────────────────────────

    def chart_get_top_artists(self, limit: int = 20) -> Dict[str, Any]:
        return self._call("chart.getTopArtists", limit=limit)

    def chart_get_top_tracks(self, limit: int = 20) -> Dict[str, Any]:
        return self._call("chart.getTopTracks", limit=limit)

    def geo_get_top_artists(self, country: str, limit: int = 20) -> Dict[str, Any]:
        return self._call("geo.getTopArtists", country=country, limit=limit)

    def geo_get_top_tracks(self, country: str, limit: int = 20) -> Dict[str, Any]:
        return self._call("geo.getTopTracks", country=country, limit=limit)

    # ── user ─────────────────────────────────────────────────────────────────

    def user_get_recent_tracks(self, user: str, limit: int = 20) -> Dict[str, Any]:
        return self._call("user.getRecentTracks", user=user, limit=limit)

    def user_get_top_artists(
        self, user: str, period: str = "overall", limit: int = 20
    ) -> Dict[str, Any]:
        return self._call("user.getTopArtists", user=user, period=period, limit=limit)

    def user_get_top_tracks(
        self, user: str, period: str = "overall", limit: int = 20
    ) -> Dict[str, Any]:
        return self._call("user.getTopTracks", user=user, period=period, limit=limit)

    def user_get_loved_tracks(self, user: str, limit: int = 20) -> Dict[str, Any]:
        return self._call("user.getLovedTracks", user=user, limit=limit)

    def user_get_info(self, user: str) -> Dict[str, Any]:
        return self._call("user.getInfo", user=user)
