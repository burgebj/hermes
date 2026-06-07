"""Tests for the Jina AI search/research toolset."""

import json


def test_jina_search_builds_query_and_limits_results(monkeypatch):
    from tools import jina_ai_tool

    captured = {}

    def _fake_request_json(url, *, method="GET", payload=None):
        captured["url"] = url
        captured["method"] = method
        captured["payload"] = payload
        return {
            "data": [
                {"title": "one", "url": "https://example.com/1"},
                {"title": "two", "url": "https://example.com/2"},
                {"title": "three", "url": "https://example.com/3"},
            ]
        }

    monkeypatch.setattr(jina_ai_tool, "_request_json", _fake_request_json)

    result = json.loads(jina_ai_tool.jina_search("hermes agent", limit=2))

    assert result["success"] is True
    assert result["query"] == "hermes agent"
    assert [item["title"] for item in result["results"]] == ["one", "two"]
    assert captured["method"] == "GET"
    assert captured["payload"] is None
    assert captured["url"].startswith("https://s.jina.ai/?")
    assert "q=hermes+agent" in captured["url"]
    assert "num=2" in captured["url"]


def test_jina_read_is_best_effort_for_multiple_urls(monkeypatch):
    from tools import jina_ai_tool

    def _fake_request_text(url):
        if url.endswith("https://bad.example"):
            raise RuntimeError("boom")
        return "Title: OK\n\nContent"

    monkeypatch.setattr(jina_ai_tool, "_request_text", _fake_request_text)

    result = json.loads(
        jina_ai_tool.jina_read(["https://good.example", "https://bad.example"])
    )

    assert result["success"] is True
    assert result["results"][0] == {
        "url": "https://good.example",
        "content": "Title: OK\n\nContent",
        "error": None,
    }
    assert result["results"][1]["url"] == "https://bad.example"
    assert result["results"][1]["content"] == ""
    assert "boom" in result["results"][1]["error"]


def test_jina_embed_posts_default_model_and_task(monkeypatch):
    from tools import jina_ai_tool

    captured = {}

    def _fake_request_json(url, *, method="GET", payload=None):
        captured["url"] = url
        captured["method"] = method
        captured["payload"] = payload
        return {"data": [{"embedding": [0.1, 0.2]}], "usage": {"total_tokens": 3}}

    monkeypatch.setattr(jina_ai_tool, "_request_json", _fake_request_json)

    result = json.loads(jina_ai_tool.jina_embed("hello"))

    assert result["success"] is True
    assert captured["url"] == "https://api.jina.ai/v1/embeddings"
    assert captured["method"] == "POST"
    assert captured["payload"] == {
        "model": "jina-embeddings-v3",
        "task": "retrieval.query",
        "input": "hello",
    }
    assert result["data"][0]["embedding"] == [0.1, 0.2]


def test_jina_rerank_normalizes_string_and_object_documents(monkeypatch):
    from tools import jina_ai_tool

    captured = {}

    def _fake_request_json(url, *, method="GET", payload=None):
        captured["url"] = url
        captured["method"] = method
        captured["payload"] = payload
        return {
            "results": [
                {"index": 0, "relevance_score": 0.9, "document": "plain text"},
                {"index": 1, "relevance_score": 0.4, "document": {"text": "object text"}},
            ],
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setattr(jina_ai_tool, "_request_json", _fake_request_json)

    result = json.loads(
        jina_ai_tool.jina_rerank("query", ["plain text", "object text"], top_n=1)
    )

    assert result["success"] is True
    assert captured["url"] == "https://api.jina.ai/v1/rerank"
    assert captured["method"] == "POST"
    assert captured["payload"]["top_n"] == 1
    assert result["results"][0]["document"] == "plain text"
    assert result["results"][1]["document"] == "object text"


def test_jina_tools_are_registered_and_gated():
    import tools.jina_ai_tool  # noqa: F401 - ensure registration side effects run
    from tools.registry import registry

    expected = {
        "jina_search": "🔎",
        "jina_read": "📖",
        "jina_embed": "🧬",
        "jina_rerank": "🏁",
    }

    for name, emoji in expected.items():
        entry = registry.get_entry(name)
        assert entry is not None
        assert entry.toolset == "jina"
        assert entry.check_fn is not None
        assert entry.requires_env == ["JINA_API_KEY"]
        assert entry.emoji == emoji


def test_jina_toolset_resolves():
    import tools.jina_ai_tool  # noqa: F401 - ensure registration side effects run
    import toolsets

    assert toolsets.TOOLSETS["jina"]["tools"] == [
        "jina_search",
        "jina_read",
        "jina_embed",
        "jina_rerank",
    ]
    resolved = set(toolsets.resolve_toolset("jina"))
    assert {"jina_search", "jina_read", "jina_embed", "jina_rerank"} <= resolved
    assert all(
        name in toolsets._HERMES_CORE_TOOLS
        for name in ["jina_search", "jina_read", "jina_embed", "jina_rerank"]
    )
