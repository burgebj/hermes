"""Tests for plugins/memory/openviking/__init__.py — URI normalization and payload handling."""

import json

import plugins.memory.openviking as openviking_module
from plugins.memory.openviking import OpenVikingMemoryProvider


class FakeVikingClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, path, params=None, **kwargs):
        self.calls.append((path, params or {}))
        response = self.responses[(path, tuple(sorted((params or {}).items())))]
        if isinstance(response, Exception):
            raise response
        return response


class FakeRecallClient:
    calls = []
    responses = {}

    def __init__(self, *args, **kwargs):
        pass

    def post(self, path, payload=None, **kwargs):
        payload = payload or {}
        self.__class__.calls.append(("post", path, dict(payload)))
        key = (path, payload.get("target_uri"), payload.get("query"))
        if key not in self.__class__.responses:
            key = (path, payload.get("target_uri"))
        response = self.__class__.responses[key]
        if isinstance(response, Exception):
            raise response
        return response

    def get(self, path, params=None, **kwargs):
        params = params or {}
        self.__class__.calls.append(("get", path, dict(params)))
        response = self.__class__.responses[(path, params.get("uri"))]
        if isinstance(response, Exception):
            raise response
        return response


def make_prefetch_provider(monkeypatch, responses, **env):
    monkeypatch.setattr(openviking_module, "_VikingClient", FakeRecallClient)
    FakeRecallClient.calls = []
    FakeRecallClient.responses = responses
    for key in (
        "OPENVIKING_RECALL_LIMIT",
        "OPENVIKING_RECALL_SCORE_THRESHOLD",
        "OPENVIKING_RECALL_MAX_INJECTED_CHARS",
        "OPENVIKING_RECALL_PREFER_ABSTRACT",
        "OPENVIKING_RECALL_RESOURCES",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, str(value))

    provider = OpenVikingMemoryProvider()
    provider._client = object()
    provider._endpoint = "http://openviking.test"
    provider._account = "default"
    provider._user = "default"
    provider._agent = "hermes"
    provider._session_id = "session-test"
    return provider


def wait_prefetch(provider, query="What should we recall?", session_id="session-test"):
    provider.queue_prefetch(query, session_id=session_id)
    if provider._prefetch_thread:
        provider._prefetch_thread.join(timeout=3.0)
    return provider.prefetch(query, session_id=session_id)


class TestOpenVikingSummaryUriNormalization:
    def test_normalize_summary_uri_maps_pseudo_files_to_parent_directory(self):
        assert OpenVikingMemoryProvider._normalize_summary_uri("viking://user/hermes/.overview.md") == "viking://user/hermes"
        assert OpenVikingMemoryProvider._normalize_summary_uri("viking://resources/.abstract.md") == "viking://resources"
        assert OpenVikingMemoryProvider._normalize_summary_uri("viking://") == "viking://"
        assert OpenVikingMemoryProvider._normalize_summary_uri("viking://user/hermes/memories/profile.md") == "viking://user/hermes/memories/profile.md"


class TestOpenVikingConfigSchema:
    def test_recall_policy_environment_options_are_declared(self):
        provider = OpenVikingMemoryProvider()

        schema = provider.get_config_schema()
        by_env = {entry.get("env_var"): entry for entry in schema}

        assert by_env["OPENVIKING_RECALL_LIMIT"]["default"] == 6
        assert by_env["OPENVIKING_RECALL_SCORE_THRESHOLD"]["default"] == 0.15
        assert by_env["OPENVIKING_RECALL_MAX_INJECTED_CHARS"]["default"] == 4000
        assert by_env["OPENVIKING_RECALL_PREFER_ABSTRACT"]["default"] is False
        assert by_env["OPENVIKING_RECALL_RESOURCES"]["default"] is False


class TestOpenVikingRead:
    def test_overview_read_normalizes_uri_and_unwraps_result(self):
        provider = OpenVikingMemoryProvider()
        provider._client = FakeVikingClient(
            {
                (
                    "/api/v1/content/overview",
                    (("uri", "viking://user/hermes"),),
                ): {"result": {"content": "overview text"}},
            }
        )

        result = json.loads(provider._tool_read({"uri": "viking://user/hermes/.overview.md", "level": "overview"}))

        assert result["uri"] == "viking://user/hermes/.overview.md"
        assert result["resolved_uri"] == "viking://user/hermes"
        assert result["level"] == "overview"
        assert result["content"] == "overview text"
        assert provider._client.calls == [(
            "/api/v1/content/overview",
            {"uri": "viking://user/hermes"},
        )]

    def test_full_read_keeps_original_uri(self):
        provider = OpenVikingMemoryProvider()
        provider._client = FakeVikingClient(
            {
                (
                    "/api/v1/content/read",
                    (("uri", "viking://user/hermes/memories/profile.md"),),
                ): {"result": "full text"},
            }
        )

        result = json.loads(provider._tool_read({"uri": "viking://user/hermes/memories/profile.md", "level": "full"}))

        assert result["uri"] == "viking://user/hermes/memories/profile.md"
        assert result["resolved_uri"] == "viking://user/hermes/memories/profile.md"
        assert result["level"] == "full"
        assert result["content"] == "full text"
        assert provider._client.calls == [(
            "/api/v1/content/read",
            {"uri": "viking://user/hermes/memories/profile.md"},
        )]

    def test_overview_file_uri_routes_straight_to_content_read_via_stat_probe(self):
        """Pre-check via fs/stat: file URIs skip the directory-only endpoint entirely."""
        provider = OpenVikingMemoryProvider()
        file_uri = "viking://user/hermes/memories/entities/mem_abc.md"
        provider._client = FakeVikingClient(
            {
                (
                    "/api/v1/fs/stat",
                    (("uri", file_uri),),
                ): {"result": {"isDir": False}},
                (
                    "/api/v1/content/read",
                    (("uri", file_uri),),
                ): {"result": {"content": "full content"}},
            }
        )

        result = json.loads(provider._tool_read({"uri": file_uri, "level": "overview"}))

        assert result["uri"] == file_uri
        assert result["resolved_uri"] == file_uri
        assert result["level"] == "overview"
        assert result["fallback"] == "content/read"
        assert result["content"] == "full content"
        assert provider._client.calls == [
            ("/api/v1/fs/stat", {"uri": file_uri}),
            ("/api/v1/content/read", {"uri": file_uri}),
        ]

    def test_overview_dir_uri_skips_stat_when_pseudo_summary(self):
        """Pseudo-URI path already resolves to dir, so no stat probe needed."""
        provider = OpenVikingMemoryProvider()
        provider._client = FakeVikingClient(
            {
                (
                    "/api/v1/content/overview",
                    (("uri", "viking://user/hermes"),),
                ): {"result": "overview"},
            }
        )

        result = json.loads(provider._tool_read({"uri": "viking://user/hermes/.overview.md", "level": "overview"}))

        assert result["content"] == "overview"
        # No fs/stat call — normalization already determined it's a directory.
        assert provider._client.calls == [
            ("/api/v1/content/overview", {"uri": "viking://user/hermes"}),
        ]


class TestOpenVikingAutoRecallPrefetch:
    def test_prefetch_searches_current_query_when_no_background_result(self, monkeypatch):
        responses = {
            (
                "/api/v1/search/find",
                "viking://user/memories",
                "Who is Caroline?",
            ): {
                "result": {
                    "memories": [
                        {
                            "uri": "viking://user/memories/caroline.md",
                            "score": 0.9,
                            "level": 1,
                            "category": "profile",
                            "abstract": "Caroline is a transgender woman.",
                        }
                    ]
                }
            },
            (
                "/api/v1/search/find",
                "viking://agent/memories",
                "Who is Caroline?",
            ): {"result": {"memories": []}},
        }
        provider = make_prefetch_provider(monkeypatch, responses)

        block = provider.prefetch("Who is Caroline?", session_id="session-test")

        assert "Caroline is a transgender woman." in block

    def test_prefetch_does_not_consume_other_session_query_result(self, monkeypatch):
        responses = {
            (
                "/api/v1/search/find",
                "viking://user/memories",
                "Who is Caroline?",
            ): {
                "result": {
                    "memories": [
                        {
                            "uri": "viking://user/memories/caroline.md",
                            "score": 0.9,
                            "level": 1,
                            "category": "profile",
                            "abstract": "Caroline context should stay scoped.",
                        }
                    ]
                }
            },
            (
                "/api/v1/search/find",
                "viking://agent/memories",
                "Who is Caroline?",
            ): {"result": {"memories": []}},
            (
                "/api/v1/search/find",
                "viking://user/memories",
                "When did Melanie run a charity race?",
            ): {
                "result": {
                    "memories": [
                        {
                            "uri": "viking://user/memories/melanie-race.md",
                            "score": 0.9,
                            "level": 1,
                            "category": "events",
                            "abstract": "Melanie ran the charity race on May 20.",
                        }
                    ]
                }
            },
            (
                "/api/v1/search/find",
                "viking://agent/memories",
                "When did Melanie run a charity race?",
            ): {"result": {"memories": []}},
        }
        provider = make_prefetch_provider(monkeypatch, responses)

        provider.queue_prefetch("Who is Caroline?", session_id="session-a")
        if provider._prefetch_thread:
            provider._prefetch_thread.join(timeout=3.0)
        block = provider.prefetch(
            "When did Melanie run a charity race?",
            session_id="session-b",
        )

        assert "Melanie ran the charity race on May 20." in block
        assert "Caroline context should stay scoped." not in block

    def test_prefetch_filters_low_score_items_with_local_threshold(self, monkeypatch):
        responses = {
            ("/api/v1/search/find", "viking://user/memories"): {
                "result": {
                    "memories": [
                        {
                            "uri": "viking://user/memories/keep.md",
                            "score": 0.22,
                            "level": 1,
                            "category": "preferences",
                            "abstract": "Keep this relevant memory.",
                        },
                        {
                            "uri": "viking://user/memories/drop.md",
                            "score": 0.12,
                            "level": 1,
                            "category": "preferences",
                            "abstract": "Drop this weak memory.",
                        },
                    ]
                }
            },
            ("/api/v1/search/find", "viking://agent/memories"): {"result": {"memories": []}},
        }
        provider = make_prefetch_provider(monkeypatch, responses)

        block = wait_prefetch(provider)

        assert block.startswith("## OpenViking Context\n")
        assert "Keep this relevant memory." in block
        assert "Drop this weak memory." not in block
        search_payloads = [call[2] for call in FakeRecallClient.calls if call[:2] == ("post", "/api/v1/search/find")]
        assert {payload["target_uri"] for payload in search_payloads} == {
            "viking://user/memories",
            "viking://agent/memories",
        }
        assert all(payload["top_k"] == 24 for payload in search_payloads)
        assert all(payload["score_threshold"] == 0 for payload in search_payloads)

    def test_prefetch_skips_complete_entries_that_do_not_fit_budget(self, monkeypatch):
        long_memory = "X" * 120
        responses = {
            ("/api/v1/search/find", "viking://user/memories"): {
                "result": {
                    "memories": [
                        {
                            "uri": "viking://user/memories/too-large.md",
                            "score": 0.9,
                            "level": 1,
                            "category": "memory",
                            "abstract": long_memory,
                        },
                        {
                            "uri": "viking://user/memories/small.md",
                            "score": 0.8,
                            "level": 1,
                            "category": "memory",
                            "abstract": "Small memory fits.",
                        },
                    ]
                }
            },
            ("/api/v1/search/find", "viking://agent/memories"): {"result": {"memories": []}},
        }
        provider = make_prefetch_provider(
            monkeypatch,
            responses,
            OPENVIKING_RECALL_MAX_INJECTED_CHARS="90",
        )

        block = wait_prefetch(provider)

        assert "Small memory fits." in block
        assert long_memory not in block
        assert "XXX" not in block

    def test_prefetch_reads_full_l2_content_by_default(self, monkeypatch):
        responses = {
            ("/api/v1/search/find", "viking://user/memories"): {
                "result": {
                    "memories": [
                        {
                            "uri": "viking://user/memories/full.md",
                            "score": 0.9,
                            "level": 2,
                            "category": "events",
                            "abstract": "Abstract only.",
                        }
                    ]
                }
            },
            ("/api/v1/search/find", "viking://agent/memories"): {"result": {"memories": []}},
            ("/api/v1/content/read", "viking://user/memories/full.md"): {
                "result": {"content": "Full L2 memory content."}
            },
        }
        provider = make_prefetch_provider(monkeypatch, responses)

        block = wait_prefetch(provider)

        assert "Full L2 memory content." in block
        assert "Abstract only." not in block
        assert ("get", "/api/v1/content/read", {"uri": "viking://user/memories/full.md"}) in FakeRecallClient.calls

    def test_prefetch_prefer_abstract_does_not_read_l2_content(self, monkeypatch):
        responses = {
            ("/api/v1/search/find", "viking://user/memories"): {
                "result": {
                    "memories": [
                        {
                            "uri": "viking://user/memories/full.md",
                            "score": 0.9,
                            "level": 2,
                            "category": "events",
                            "abstract": "Use the abstract.",
                        }
                    ]
                }
            },
            ("/api/v1/search/find", "viking://agent/memories"): {"result": {"memories": []}},
        }
        provider = make_prefetch_provider(
            monkeypatch,
            responses,
            OPENVIKING_RECALL_PREFER_ABSTRACT="true",
        )

        block = wait_prefetch(provider)

        assert "Use the abstract." in block
        assert not any(call[:2] == ("get", "/api/v1/content/read") for call in FakeRecallClient.calls)

    def test_prefetch_honors_configured_limit_candidate_limit_and_resources(self, monkeypatch):
        responses = {
            ("/api/v1/search/find", "viking://user/memories"): {"result": {"memories": []}},
            ("/api/v1/search/find", "viking://agent/memories"): {"result": {"memories": []}},
            ("/api/v1/search/find", "viking://resources"): {
                "result": {
                    "resources": [
                        {
                            "uri": "viking://resources/doc.md",
                            "score": 0.9,
                            "level": 1,
                            "category": "resource",
                            "abstract": "Resource recall enabled.",
                        }
                    ]
                }
            },
        }
        provider = make_prefetch_provider(
            monkeypatch,
            responses,
            OPENVIKING_RECALL_LIMIT="2",
            OPENVIKING_RECALL_RESOURCES="true",
        )

        block = wait_prefetch(provider)

        assert "Resource recall enabled." in block
        search_payloads = [call[2] for call in FakeRecallClient.calls if call[:2] == ("post", "/api/v1/search/find")]
        assert [payload["target_uri"] for payload in search_payloads] == [
            "viking://user/memories",
            "viking://agent/memories",
            "viking://resources",
        ]
        assert all(payload["top_k"] == 20 for payload in search_payloads)

    def test_queue_prefetch_skips_trivial_queries(self, monkeypatch):
        provider = make_prefetch_provider(monkeypatch, {})

        provider.queue_prefetch("  hey  ", session_id="session-test")

        assert provider._prefetch_thread is None
        assert FakeRecallClient.calls == []

    def test_overview_directory_uri_uses_stat_probe_then_overview(self):
        """Non-pseudo directory URI: stat → isDir=True → summary endpoint."""
        provider = OpenVikingMemoryProvider()
        dir_uri = "viking://user/hermes/memories"
        provider._client = FakeVikingClient(
            {
                (
                    "/api/v1/fs/stat",
                    (("uri", dir_uri),),
                ): {"result": {"isDir": True}},
                (
                    "/api/v1/content/overview",
                    (("uri", dir_uri),),
                ): {"result": "dir overview"},
            }
        )

        result = json.loads(provider._tool_read({"uri": dir_uri, "level": "overview"}))

        assert result["content"] == "dir overview"
        assert "fallback" not in result
        assert provider._client.calls == [
            ("/api/v1/fs/stat", {"uri": dir_uri}),
            ("/api/v1/content/overview", {"uri": dir_uri}),
        ]

    def test_overview_file_uri_falls_back_via_exception_when_stat_indeterminate(self):
        """If fs/stat raises or returns unknown shape, legacy exception fallback still kicks in."""
        provider = OpenVikingMemoryProvider()
        file_uri = "viking://user/hermes/memories/entities/mem_abc.md"
        provider._client = FakeVikingClient(
            {
                (
                    "/api/v1/fs/stat",
                    (("uri", file_uri),),
                ): RuntimeError("stat unavailable"),
                (
                    "/api/v1/content/overview",
                    (("uri", file_uri),),
                ): RuntimeError("500 Internal Server Error"),
                (
                    "/api/v1/content/read",
                    (("uri", file_uri),),
                ): {"result": {"content": "fallback full content"}},
            }
        )

        result = json.loads(provider._tool_read({"uri": file_uri, "level": "overview"}))

        assert result["uri"] == file_uri
        assert result["level"] == "overview"
        assert result["fallback"] == "content/read"
        assert result["content"] == "fallback full content"
        assert provider._client.calls == [
            ("/api/v1/fs/stat", {"uri": file_uri}),
            ("/api/v1/content/overview", {"uri": file_uri}),
            ("/api/v1/content/read", {"uri": file_uri}),
        ]

    def test_summary_uri_error_does_not_fallback_and_raises(self):
        provider = OpenVikingMemoryProvider()
        provider._client = FakeVikingClient(
            {
                (
                    "/api/v1/content/overview",
                    (("uri", "viking://user/hermes"),),
                ): RuntimeError("500 Internal Server Error"),
            }
        )

        try:
            provider._tool_read({"uri": "viking://user/hermes/.overview.md", "level": "overview"})
            assert False, "Expected summary endpoint error to be raised"
        except RuntimeError:
            pass

        assert provider._client.calls == [
            ("/api/v1/content/overview", {"uri": "viking://user/hermes"}),
        ]


class TestOpenVikingBrowse:
    def test_list_browse_unwraps_and_normalizes_entry_shapes(self):
        provider = OpenVikingMemoryProvider()
        provider._client = FakeVikingClient(
            {
                (
                    "/api/v1/fs/ls",
                    (("uri", "viking://user/hermes"),),
                ): {
                    "result": {
                        "entries": [
                            {"name": "memories", "uri": "viking://user/hermes/memories", "type": "dir"},
                            {"rel_path": "profile.md", "uri": "viking://user/hermes/memories/profile.md", "isDir": False, "abstract": "Profile"},
                        ]
                    }
                },
            }
        )

        result = json.loads(provider._tool_browse({"action": "list", "path": "viking://user/hermes"}))

        assert result["path"] == "viking://user/hermes"
        assert result["entries"] == [
            {"name": "memories", "uri": "viking://user/hermes/memories", "type": "dir", "abstract": ""},
            {"name": "profile.md", "uri": "viking://user/hermes/memories/profile.md", "type": "file", "abstract": "Profile"},
        ]
        assert provider._client.calls == [(
            "/api/v1/fs/ls",
            {"uri": "viking://user/hermes"},
        )]


class TestOpenVikingMemoryUriBuilder:
    """Regression tests for _build_memory_uri — fixes #36969.

    Before the fix the URI omitted /agent/{agent}/, causing all agents
    under the same user to share the same memory namespace.
    """

    def _make_provider(self, user="alice", agent="coder"):
        p = OpenVikingMemoryProvider.__new__(OpenVikingMemoryProvider)
        p._user = user
        p._agent = agent
        return p

    def test_uri_layout_includes_agent_segment(self):
        """URI must contain /agent/{agent}/ between user and memories."""
        p = self._make_provider(user="alice", agent="coder")
        uri = p._build_memory_uri("preferences")
        assert uri.startswith("viking://user/alice/agent/coder/memories/preferences/mem_")
        assert uri.endswith(".md")

    def test_uri_uses_configured_agent_not_default(self):
        """_agent value must be interpolated — not hardcoded to 'hermes'."""
        p = self._make_provider(user="alice", agent="research-bot")
        uri = p._build_memory_uri("entities")
        assert "/agent/research-bot/" in uri
        assert "/agent/hermes/" not in uri

    def test_uri_slug_is_twelve_hex_chars_and_unique(self):
        """Slug must be 12 hex chars and differ between calls."""
        import re
        p = self._make_provider()
        uri1 = p._build_memory_uri("preferences")
        uri2 = p._build_memory_uri("preferences")
        slug1 = uri1.split("/mem_")[1].replace(".md", "")
        slug2 = uri2.split("/mem_")[1].replace(".md", "")
        assert re.fullmatch(r"[0-9a-f]{12}", slug1)
        assert re.fullmatch(r"[0-9a-f]{12}", slug2)
        assert slug1 != slug2

    def test_uri_subdir_placed_correctly_for_all_categories(self):
        """All five category subdirs must appear between memories/ and slug."""
        p = self._make_provider(user="u", agent="a")
        subdirs = ["preferences", "entities", "events", "cases", "patterns"]
        for subdir in subdirs:
            uri = p._build_memory_uri(subdir)
            assert f"/memories/{subdir}/mem_" in uri, (
                f"subdir '{subdir}' not placed correctly in URI: {uri}"
            )
