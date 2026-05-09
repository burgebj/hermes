"""Tests for the lastfm plugin.

Covers:
  * LastFmClient: API key loading, request construction, error handling.
  * Tool handlers: each action for all 5 tools, exercised via mocked HTTP.
  * Auth guard: _check_lastfm_available() gates on LASTFM_API_KEY.
  * Schema structure: all 5 schemas have required fields in expected shape.
  * Error paths: missing artist/tag, unknown action, API error response.
  * Composite scoring: avg / max / boost modes, cross-seed tracking.

No real HTTP calls are made — urllib.request.urlopen is patched in all tests.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "plugins" / "lastfm"


# ── loader helpers ────────────────────────────────────────────────────────────

def _urlopen_mock(response_data: Any):
    """Context-manager mock for urllib.request.urlopen."""
    body = json.dumps(response_data).encode()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=body)))
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _cycle_urlopen(*responses):
    """side_effect that cycles through a list of payloads."""
    it = iter(responses)

    def _fake(url, timeout=None):
        try:
            payload = next(it)
        except StopIteration:
            payload = responses[-1]
        return _urlopen_mock(payload)

    return _fake


def _load_client():
    """Import client.py directly (no Hermes deps)."""
    spec = importlib.util.spec_from_file_location(
        "lastfm_client_under_test", PLUGIN_DIR / "client.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_tools():
    """Import tools.py with stubs for plugins.lastfm.client and tools.registry."""
    client_mod = _load_client()

    registry_stub = types.ModuleType("tools.registry")
    registry_stub.tool_result = lambda data: json.dumps({"ok": True, "data": data})
    registry_stub.tool_error = lambda msg, **kw: json.dumps({"ok": False, "error": msg})
    sys.modules.setdefault("tools", types.ModuleType("tools"))
    sys.modules["tools.registry"] = registry_stub

    sys.modules.setdefault("plugins", types.ModuleType("plugins"))
    sys.modules.setdefault("plugins.lastfm", types.ModuleType("plugins.lastfm"))
    sys.modules["plugins.lastfm.client"] = client_mod

    spec = importlib.util.spec_from_file_location(
        "lastfm_tools_under_test", PLUGIN_DIR / "tools.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ok(result: str) -> Any:
    parsed = json.loads(result)
    assert parsed.get("ok") is True, f"Expected ok=True, got: {result}"
    return parsed["data"]


def _err(result: str) -> str:
    parsed = json.loads(result)
    assert parsed.get("ok") is False, f"Expected ok=False, got: {result}"
    return parsed["error"]


# ── shared fixtures ───────────────────────────────────────────────────────────

_SIMILAR_ARTISTS = {
    "similarartists": {"artist": [
        {"name": "Autechre",    "match": "0.85"},
        {"name": "μ-Ziq",       "match": "0.72"},
        {"name": "Squarepusher","match": "0.61"},
    ]}
}
_TOP_TRACKS = {
    "toptracks": {"track": [
        {"name": "Gantz Graf", "playcount": "1200000", "listeners": "400000",
         "@attr": {"rank": "1"}, "url": ""}
    ]}
}
_TOP_TAGS = {
    "toptags": {"tag": [{"name": "IDM"}, {"name": "electronic"}, {"name": "experimental"}]}
}
_ARTIST_INFO = {
    "artist": {"name": "Autechre", "url": "https://www.last.fm/music/Autechre",
               "stats": {"listeners": "500000", "playcount": "9000000"},
               "bio": {}, "tags": {"tag": []}, "similar": {"artist": []}}
}


# ── tests: client ─────────────────────────────────────────────────────────────

class TestLastFmClient(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.pop("LASTFM_API_KEY", None)

    def tearDown(self):
        os.environ.pop("LASTFM_API_KEY", None)
        if self._orig is not None:
            os.environ["LASTFM_API_KEY"] = self._orig

    def test_raises_auth_error_without_key(self):
        client = _load_client()
        with self.assertRaises(client.LastFmAuthError):
            client.LastFmClient()

    def test_accepts_key_from_env(self):
        os.environ["LASTFM_API_KEY"] = "testkey123"
        client = _load_client()
        c = client.LastFmClient()
        self.assertEqual(c._api_key, "testkey123")

    def test_accepts_key_passed_directly(self):
        client = _load_client()
        c = client.LastFmClient(api_key="directkey")
        self.assertEqual(c._api_key, "directkey")

    def test_raises_api_error_on_lastfm_error_response(self):
        os.environ["LASTFM_API_KEY"] = "testkey"
        client = _load_client()
        payload = {"error": 6, "message": "Artist not found"}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            c = client.LastFmClient()
            with self.assertRaises(client.LastFmAPIError):
                c.artist_get_info("nonexistent xyz")

    def test_call_includes_api_key_and_method_in_url(self):
        os.environ["LASTFM_API_KEY"] = "mykey42"
        client = _load_client()
        captured = {}

        def fake_urlopen(url, timeout=None):
            captured["url"] = url
            return _urlopen_mock({"similarartists": {"artist": []}})

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            client.LastFmClient().artist_get_similar("test", limit=5)

        self.assertIn("api_key=mykey42", captured["url"])
        self.assertIn("method=artist.getSimilar", captured["url"])
        self.assertIn("limit=5", captured["url"])

    def test_raises_lastfm_error_on_network_failure(self):
        os.environ["LASTFM_API_KEY"] = "testkey"
        client = _load_client()
        with patch("urllib.request.urlopen", side_effect=OSError("refused")):
            with self.assertRaises(client.LastFmError):
                client.LastFmClient().chart_get_top_tracks()


# ── tests: auth guard ─────────────────────────────────────────────────────────

class TestAuthGuard(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.pop("LASTFM_API_KEY", None)

    def tearDown(self):
        os.environ.pop("LASTFM_API_KEY", None)
        if self._orig is not None:
            os.environ["LASTFM_API_KEY"] = self._orig

    def test_unavailable_without_key(self):
        tools = _load_tools()
        self.assertFalse(tools._check_lastfm_available())

    def test_available_with_key(self):
        os.environ["LASTFM_API_KEY"] = "present"
        tools = _load_tools()
        self.assertTrue(tools._check_lastfm_available())

    def test_discover_returns_auth_error_without_key(self):
        tools = _load_tools()
        result = tools._handle_lastfm_discover({"artists": ["Aphex Twin"]})
        self.assertIn("LASTFM_API_KEY", _err(result))


# ── tests: discover ───────────────────────────────────────────────────────────

class TestDiscover(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.pop("LASTFM_API_KEY", None)
        os.environ["LASTFM_API_KEY"] = "testkey"
        self.tools = _load_tools()

    def tearDown(self):
        os.environ.pop("LASTFM_API_KEY", None)
        if self._orig is not None:
            os.environ["LASTFM_API_KEY"] = self._orig

    def _enrich_responses(self, n=5):
        return [_TOP_TRACKS, _TOP_TAGS, _ARTIST_INFO] * n

    def test_artist_seed_returns_recommendations(self):
        responses = _cycle_urlopen(_SIMILAR_ARTISTS, *self._enrich_responses())
        with patch("urllib.request.urlopen", side_effect=responses):
            result = self.tools._handle_lastfm_discover(
                {"artists": ["Boards of Canada"], "count": 3}
            )
        data = _ok(result)
        self.assertGreaterEqual(data["count"], 1)
        rec = data["recommendations"][0]
        self.assertIn("artist", rec)
        self.assertIn("score", rec)
        self.assertEqual(rec["seed_type"], "artist")

    def test_missing_seeds_returns_error(self):
        result = self.tools._handle_lastfm_discover({})
        err = _err(result).lower()
        self.assertTrue("artist" in err or "seed" in err)

    def test_default_scoring_is_avg(self):
        responses = _cycle_urlopen(_SIMILAR_ARTISTS, *self._enrich_responses())
        with patch("urllib.request.urlopen", side_effect=responses):
            result = self.tools._handle_lastfm_discover({"artists": ["Aphex Twin"]})
        self.assertEqual(_ok(result)["scoring"], "avg")

    def test_scoring_max_accepted(self):
        responses = _cycle_urlopen(_SIMILAR_ARTISTS, *self._enrich_responses())
        with patch("urllib.request.urlopen", side_effect=responses):
            result = self.tools._handle_lastfm_discover(
                {"artists": ["Aphex Twin"], "scoring": "max"}
            )
        self.assertEqual(_ok(result)["scoring"], "max")

    def test_multi_seed_cross_seed_tracking(self):
        """Artist in both seeds gets seeds_matched=2."""
        both = {"similarartists": {"artist": [{"name": "Autechre", "match": "0.80"}]}}
        responses = _cycle_urlopen(both, both, *self._enrich_responses())
        with patch("urllib.request.urlopen", side_effect=responses):
            result = self.tools._handle_lastfm_discover(
                {"artists": ["Boards of Canada", "Aphex Twin"], "count": 5}
            )
        data = _ok(result)
        recs = {r["artist"]: r for r in data["recommendations"]}
        self.assertIn("Autechre", recs)
        self.assertEqual(recs["Autechre"]["seeds_matched"], 2)
        self.assertEqual(recs["Autechre"]["total_seeds"], 2)

    def test_track_seed_accepted(self):
        similar_tracks = {
            "similartracks": {"track": [
                {"name": "Gantz Graf", "artist": {"name": "Autechre"},
                 "match": "0.75", "playcount": "500000", "url": ""}
            ]}
        }
        responses = _cycle_urlopen(similar_tracks, *self._enrich_responses())
        with patch("urllib.request.urlopen", side_effect=responses):
            result = self.tools._handle_lastfm_discover(
                {"tracks": ["Boards of Canada:Roygbiv"], "count": 5}
            )
        data = _ok(result)
        self.assertGreaterEqual(data["count"], 1)
        self.assertEqual(data["recommendations"][0]["seed_type"], "track")

    def test_invalid_track_seed_format_does_not_crash(self):
        result = self.tools._handle_lastfm_discover({"tracks": ["Roygbiv"]})
        parsed = json.loads(result)
        self.assertIn("ok", parsed)  # did not raise


# ── tests: artist ─────────────────────────────────────────────────────────────

class TestArtistTool(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.pop("LASTFM_API_KEY", None)
        os.environ["LASTFM_API_KEY"] = "k"
        self.tools = _load_tools()

    def tearDown(self):
        os.environ.pop("LASTFM_API_KEY", None)
        if self._orig is not None:
            os.environ["LASTFM_API_KEY"] = self._orig

    _ARTIST_FULL = {
        "artist": {
            "name": "Aphex Twin",
            "url": "https://www.last.fm/music/Aphex+Twin",
            "stats": {"listeners": "1000000", "playcount": "50000000"},
            "tags": {"tag": [{"name": "IDM"}, {"name": "electronic"}]},
            "bio": {"summary": "Richard D. James. <a href='x'>Read more</a>"},
            "similar": {"artist": [{"name": "Autechre"}, {"name": "Squarepusher"}]},
        }
    }

    def test_info_action(self):
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(self._ARTIST_FULL)):
            data = _ok(self.tools._handle_lastfm_artist(
                {"action": "info", "artist": "Aphex Twin"}
            ))
        self.assertEqual(data["name"], "Aphex Twin")
        self.assertIn("IDM", data["tags"])
        self.assertEqual(data["listeners"], 1000000)
        self.assertNotIn("<a", data["summary"])  # bio anchor stripped

    def test_similar_action(self):
        payload = {"similarartists": {"artist": [
            {"name": "Autechre", "match": "0.90"},
            {"name": "μ-Ziq",    "match": "0.75"},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_artist(
                {"action": "similar", "artist": "Aphex Twin", "limit": 5}
            ))
        self.assertEqual(len(data["similar"]), 2)
        self.assertEqual(data["similar"][0]["name"], "Autechre")
        self.assertEqual(data["similar"][0]["match"], 90.0)

    def test_top_tracks_action(self):
        payload = {"toptracks": {"track": [
            {"name": "Windowlicker", "playcount": "5000000", "listeners": "900000",
             "@attr": {"rank": "1"}, "url": ""},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_artist(
                {"action": "top_tracks", "artist": "Aphex Twin"}
            ))
        self.assertEqual(data["top_tracks"][0]["name"], "Windowlicker")
        self.assertEqual(data["top_tracks"][0]["rank"], 1)

    def test_top_albums_action(self):
        payload = {"topalbums": {"album": [
            {"name": "Selected Ambient Works Volume II", "playcount": "3000000",
             "@attr": {"rank": "1"}, "url": ""},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_artist(
                {"action": "top_albums", "artist": "Aphex Twin"}
            ))
        self.assertIn("Selected Ambient Works", data["top_albums"][0]["name"])

    def test_top_tags_action(self):
        payload = {"toptags": {"tag": [
            {"name": "IDM", "count": "100"}, {"name": "electronic", "count": "80"},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_artist(
                {"action": "top_tags", "artist": "Aphex Twin"}
            ))
        self.assertEqual(data["tags"][0]["name"], "IDM")

    def test_search_action(self):
        payload = {"results": {"artistmatches": {"artist": [
            {"name": "Aphex Twin", "listeners": "1000000", "url": ""},
        ]}}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_artist(
                {"action": "search", "artist": "aphex"}
            ))
        self.assertEqual(data["results"][0]["name"], "Aphex Twin")

    def test_missing_artist_returns_error(self):
        result = self.tools._handle_lastfm_artist({"action": "info"})
        self.assertIn("artist", _err(result).lower())

    def test_unknown_action_returns_error(self):
        result = self.tools._handle_lastfm_artist({"action": "dance", "artist": "X"})
        self.assertIn("dance", _err(result))


# ── tests: track ──────────────────────────────────────────────────────────────

class TestTrackTool(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.pop("LASTFM_API_KEY", None)
        os.environ["LASTFM_API_KEY"] = "k"
        self.tools = _load_tools()

    def tearDown(self):
        os.environ.pop("LASTFM_API_KEY", None)
        if self._orig is not None:
            os.environ["LASTFM_API_KEY"] = self._orig

    def test_info_action(self):
        payload = {"track": {
            "name": "Roygbiv", "duration": "188000",
            "listeners": "300000", "playcount": "2000000",
            "url": "", "artist": {"name": "Boards of Canada"},
            "album": {"title": "Music Has the Right to Children", "url": ""},
            "toptags": {"tag": [{"name": "IDM"}, {"name": "ambient"}]},
            "wiki": {"summary": "A track. <a href='x'>Read more</a>"},
        }}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_track(
                {"action": "info", "artist": "Boards of Canada", "track": "Roygbiv"}
            ))
        self.assertEqual(data["name"], "Roygbiv")
        self.assertEqual(data["artist"], "Boards of Canada")
        self.assertIn("IDM", data["tags"])
        self.assertNotIn("<a", data["summary"])

    def test_similar_action(self):
        payload = {"similartracks": {"track": [
            {"name": "Turquoise Hexagon Sun",
             "artist": {"name": "Boards of Canada"},
             "match": "0.88", "playcount": "800000", "url": ""},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_track(
                {"action": "similar", "artist": "Boards of Canada", "track": "Roygbiv"}
            ))
        self.assertEqual(data["similar"][0]["match"], 88.0)

    def test_search_action(self):
        payload = {"results": {"trackmatches": {"track": [
            {"name": "Roygbiv", "artist": "Boards of Canada",
             "listeners": "300000", "url": ""},
        ]}}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_track(
                {"action": "search", "track": "Roygbiv"}
            ))
        self.assertEqual(data["results"][0]["artist"], "Boards of Canada")

    def test_info_requires_both_artist_and_track(self):
        result = self.tools._handle_lastfm_track({"action": "info", "artist": "X"})
        err = _err(result).lower()
        self.assertTrue("artist" in err or "track" in err)

    def test_unknown_action_returns_error(self):
        result = self.tools._handle_lastfm_track(
            {"action": "spin", "artist": "X", "track": "Y"}
        )
        self.assertIn("spin", _err(result))


# ── tests: tag ────────────────────────────────────────────────────────────────

class TestTagTool(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.pop("LASTFM_API_KEY", None)
        os.environ["LASTFM_API_KEY"] = "k"
        self.tools = _load_tools()

    def tearDown(self):
        os.environ.pop("LASTFM_API_KEY", None)
        if self._orig is not None:
            os.environ["LASTFM_API_KEY"] = self._orig

    def test_top_artists_action(self):
        payload = {"topartists": {"artist": [
            {"name": "Brian Eno", "url": "", "@attr": {"rank": "1"}},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_tag(
                {"action": "top_artists", "tag": "ambient"}
            ))
        self.assertEqual(data["tag"], "ambient")
        self.assertEqual(data["top_artists"][0]["name"], "Brian Eno")

    def test_top_tracks_action(self):
        payload = {"tracks": {"track": [
            {"name": "Music for Airports", "artist": {"name": "Brian Eno"},
             "url": "", "@attr": {"rank": "1"}},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_tag(
                {"action": "top_tracks", "tag": "ambient"}
            ))
        self.assertEqual(data["top_tracks"][0]["artist"], "Brian Eno")

    def test_top_albums_action(self):
        payload = {"albums": {"album": [
            {"name": "Ambient 1", "artist": {"name": "Brian Eno"},
             "url": "", "@attr": {"rank": "1"}},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_tag(
                {"action": "top_albums", "tag": "ambient"}
            ))
        self.assertEqual(data["top_albums"][0]["name"], "Ambient 1")

    def test_similar_action(self):
        payload = {"similartags": {"tag": [{"name": "drone"}, {"name": "dark ambient"}]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_tag(
                {"action": "similar", "tag": "ambient"}
            ))
        self.assertIn("drone", data["similar_tags"])

    def test_info_action_strips_bio_anchor(self):
        payload = {"tag": {"name": "ambient", "reach": "50000", "total": "9000000",
                           "wiki": {"summary": "Ambient. <a href='x'>Read more</a>"}}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_tag(
                {"action": "info", "tag": "ambient"}
            ))
        self.assertEqual(data["reach"], 50000)
        self.assertNotIn("<a", data["summary"])

    def test_missing_tag_returns_error(self):
        result = self.tools._handle_lastfm_tag({"action": "top_artists"})
        self.assertIn("tag", _err(result).lower())

    def test_unknown_action_returns_error(self):
        result = self.tools._handle_lastfm_tag({"action": "fly", "tag": "ambient"})
        self.assertIn("fly", _err(result))


# ── tests: charts ─────────────────────────────────────────────────────────────

class TestChartsTool(unittest.TestCase):
    def setUp(self):
        self._orig = os.environ.pop("LASTFM_API_KEY", None)
        os.environ["LASTFM_API_KEY"] = "k"
        self.tools = _load_tools()

    def tearDown(self):
        os.environ.pop("LASTFM_API_KEY", None)
        if self._orig is not None:
            os.environ["LASTFM_API_KEY"] = self._orig

    def test_global_top_tracks(self):
        payload = {"tracks": {"track": [
            {"name": "Running Up That Hill", "artist": {"name": "Kate Bush"},
             "listeners": "5000000", "url": "", "@attr": {"rank": "1"}},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_charts({"action": "top_tracks"}))
        self.assertEqual(data["scope"], "global")
        self.assertEqual(data["top_tracks"][0]["artist"], "Kate Bush")

    def test_global_top_artists(self):
        payload = {"artists": {"artist": [
            {"name": "Radiohead", "listeners": "4000000", "url": "",
             "@attr": {"rank": "1"}},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_charts({"action": "top_artists"}))
        self.assertEqual(data["scope"], "global")
        self.assertEqual(data["top_artists"][0]["name"], "Radiohead")

    def test_country_top_tracks(self):
        payload = {"tracks": {"track": [
            {"name": "99 Luftballons", "artist": {"name": "Nena"},
             "listeners": "1000000", "url": "", "@attr": {"rank": "1"}},
        ]}}
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(payload)):
            data = _ok(self.tools._handle_lastfm_charts(
                {"action": "top_tracks", "country": "Germany"}
            ))
        self.assertEqual(data["scope"], "Germany")

    def test_unknown_action_returns_error(self):
        result = self.tools._handle_lastfm_charts({"action": "weather"})
        self.assertIn("weather", _err(result))


# ── tests: composite scoring ──────────────────────────────────────────────────

class TestCompositeScore(unittest.TestCase):
    def setUp(self):
        self.tools = _load_tools()

    def _s(self, matches, n_seeds, mode):
        return self.tools._composite_score(matches, n_seeds, mode)

    def test_avg_single_seed(self):
        self.assertEqual(self._s([0.80], 1, "avg"), 80.0)

    def test_avg_penalises_partial_match(self):
        # 1/3 seeds should score lower than 3/3 seeds at same per-seed match
        full = self._s([0.60, 0.60, 0.60], 3, "avg")
        partial = self._s([0.60], 3, "avg")
        self.assertGreater(full, partial)

    def test_max_ignores_seed_count(self):
        self.assertEqual(self._s([0.50, 0.80], 3, "max"), 80.0)
        self.assertEqual(self._s([0.50, 0.80], 1, "max"), 80.0)

    def test_boost_rewards_extra_seeds(self):
        single = self._s([0.60], 3, "boost")
        double = self._s([0.60, 0.60], 3, "boost")
        self.assertGreater(double, single)

    def test_boost_caps_at_100(self):
        score = self._s([1.0, 1.0, 1.0, 1.0], 4, "boost")
        self.assertLessEqual(score, 100.0)

    def test_empty_matches_returns_zero(self):
        for mode in ("avg", "max", "boost"):
            self.assertEqual(self._s([], 3, mode), 0.0)


# ── tests: schemas ────────────────────────────────────────────────────────────

class TestSchemas(unittest.TestCase):
    def setUp(self):
        self.tools = _load_tools()
        self.schemas = [
            self.tools.LASTFM_DISCOVER_SCHEMA,
            self.tools.LASTFM_ARTIST_SCHEMA,
            self.tools.LASTFM_TRACK_SCHEMA,
            self.tools.LASTFM_TAG_SCHEMA,
            self.tools.LASTFM_CHARTS_SCHEMA,
        ]

    def test_five_schemas_total(self):
        self.assertEqual(len(self.schemas), 5)

    def test_all_names_unique(self):
        names = [s["name"] for s in self.schemas]
        self.assertEqual(len(names), len(set(names)))

    def test_all_have_required_top_level_keys(self):
        for s in self.schemas:
            for key in ("name", "description", "parameters"):
                self.assertIn(key, s, f"Missing '{key}' in {s.get('name')}")

    def test_parameters_are_object_type(self):
        for s in self.schemas:
            params = s["parameters"]
            self.assertEqual(params["type"], "object", s["name"])
            self.assertIn("properties", params, s["name"])

    def test_discover_has_artists_and_tracks_arrays(self):
        props = self.tools.LASTFM_DISCOVER_SCHEMA["parameters"]["properties"]
        self.assertIn("artists", props)
        self.assertIn("tracks", props)
        self.assertEqual(props["artists"]["type"], "array")
        self.assertEqual(props["tracks"]["type"], "array")

    def test_artist_schema_requires_action_and_artist(self):
        required = self.tools.LASTFM_ARTIST_SCHEMA["parameters"].get("required", [])
        self.assertIn("action", required)
        self.assertIn("artist", required)

    def test_tag_schema_requires_action_and_tag(self):
        required = self.tools.LASTFM_TAG_SCHEMA["parameters"].get("required", [])
        self.assertIn("action", required)
        self.assertIn("tag", required)

    def test_all_tool_names_prefixed_lastfm(self):
        for s in self.schemas:
            self.assertTrue(s["name"].startswith("lastfm_"), s["name"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
