"""Tests for Mem0 self-host (local) mode.

Verifies that ``Mem0MemoryProvider`` constructs the right backend client
based on ``mode`` and routes calls to the matching API surface:

* cloud (``MemoryClient``): ``filters={...}``, ``rerank=``, ``top_k=``
* local (``Memory``):       ``filters={...}``, ``limit=``, no ``rerank``

Both backends scope by ``filters={"user_id": ...}``; local rejects bare
top-level ``user_id=`` at runtime even though the function signature
suggests otherwise.

Cloud-mode behavior is covered by ``test_mem0_v2.py``; here we focus on the
local code path and the mode toggle itself.
"""

import json
import pytest

from plugins.memory.mem0 import Mem0MemoryProvider, _load_config


class FakeLocalMemory:
    """Stand-in for ``mem0.Memory`` — captures kwargs, returns v1.1-style dicts."""

    def __init__(self, search_results=None, all_results=None):
        self._search_results = search_results or {"results": []}
        self._all_results = all_results or {"results": []}
        self.captured_search = {}
        self.captured_get_all = {}
        self.captured_add = []

    def search(self, query, **kwargs):
        self.captured_search = {"query": query, **kwargs}
        return self._search_results

    def get_all(self, **kwargs):
        self.captured_get_all = kwargs
        return self._all_results

    def add(self, messages, **kwargs):
        self.captured_add.append({"messages": messages, **kwargs})


# ---------------------------------------------------------------------------
# Mode selection + config loading
# ---------------------------------------------------------------------------


class TestMem0Mode:
    """Mode resolution from env vars and mem0.json."""

    def test_default_mode_is_cloud(self, monkeypatch, tmp_path):
        monkeypatch.delenv("MEM0_MODE", raising=False)
        monkeypatch.setenv("MEM0_API_KEY", "test-key")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))

        cfg = _load_config()
        assert cfg["mode"] == "cloud"

    def test_mode_from_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MEM0_MODE", "local")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))

        cfg = _load_config()
        assert cfg["mode"] == "local"

    def test_invalid_mode_falls_back_to_cloud(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MEM0_MODE", "telepathic")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))

        cfg = _load_config()
        assert cfg["mode"] == "cloud"

    def test_mode_from_mem0_json_overrides_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MEM0_MODE", "cloud")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "mem0.json").write_text(json.dumps({"mode": "local"}))

        cfg = _load_config()
        assert cfg["mode"] == "local"

    def test_local_config_block_loaded_from_json(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        local_cfg = {
            "vector_store": {"provider": "qdrant", "config": {}},
            "llm": {"provider": "openai", "config": {}},
            "embedder": {"provider": "ollama", "config": {}},
        }
        (tmp_path / "mem0.json").write_text(json.dumps({
            "mode": "local",
            "config": local_cfg,
        }))

        cfg = _load_config()
        assert cfg["config"] == local_cfg


# ---------------------------------------------------------------------------
# is_available — gating logic per mode
# ---------------------------------------------------------------------------


class TestMem0Availability:
    def test_cloud_requires_api_key(self, monkeypatch, tmp_path):
        monkeypatch.delenv("MEM0_API_KEY", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        provider = Mem0MemoryProvider()
        assert provider.is_available() is False

    def test_cloud_available_with_api_key(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MEM0_API_KEY", "sk-test")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        provider = Mem0MemoryProvider()
        assert provider.is_available() is True

    def test_local_requires_config_block(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MEM0_MODE", "local")
        monkeypatch.delenv("MEM0_API_KEY", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        provider = Mem0MemoryProvider()
        assert provider.is_available() is False

    def test_local_available_with_config_block(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MEM0_MODE", "local")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "mem0.json").write_text(json.dumps({
            "mode": "local",
            "config": {"vector_store": {"provider": "qdrant", "config": {}}},
        }))
        provider = Mem0MemoryProvider()
        assert provider.is_available() is True


# ---------------------------------------------------------------------------
# Local-mode API shape — search / add / get_all
# ---------------------------------------------------------------------------


class TestMem0LocalApiShape:
    """Local Memory uses ``filters={}`` + ``limit=`` (not ``top_k=`` / ``rerank=``)."""

    def _make_provider(self, monkeypatch, client):
        provider = Mem0MemoryProvider()
        provider._mode = "local"
        provider._user_id = "u123"
        provider._agent_id = "hermes"
        provider._local_config = {"vector_store": {"provider": "qdrant", "config": {}}}
        monkeypatch.setattr(provider, "_get_client", lambda: client)
        return provider

    def test_search_uses_filters_and_limit(self, monkeypatch):
        client = FakeLocalMemory()
        provider = self._make_provider(monkeypatch, client)

        provider.handle_tool_call("mem0_search", {"query": "hello", "top_k": 7, "rerank": False})

        assert client.captured_search["query"] == "hello"
        assert client.captured_search["filters"] == {"user_id": "u123"}
        assert client.captured_search["limit"] == 7
        # local Memory.search rejects rerank and top_k kwargs
        assert "rerank" not in client.captured_search
        assert "top_k" not in client.captured_search

    def test_get_all_uses_filters(self, monkeypatch):
        client = FakeLocalMemory(all_results={"results": [{"memory": "alpha"}]})
        provider = self._make_provider(monkeypatch, client)

        provider.handle_tool_call("mem0_profile", {})

        assert client.captured_get_all == {"filters": {"user_id": "u123"}}

    def test_add_passes_user_and_agent(self, monkeypatch):
        client = FakeLocalMemory()
        provider = self._make_provider(monkeypatch, client)

        provider.handle_tool_call("mem0_conclude", {"conclusion": "user prefers dark mode"})

        assert len(client.captured_add) == 1
        call = client.captured_add[0]
        assert call["user_id"] == "u123"
        assert call["agent_id"] == "hermes"
        assert call["infer"] is False

    def test_sync_turn_uses_local_kwargs(self, monkeypatch):
        client = FakeLocalMemory()
        provider = self._make_provider(monkeypatch, client)

        provider.sync_turn("user said this", "assistant replied", session_id="s1")
        provider._sync_thread.join(timeout=2)

        assert len(client.captured_add) == 1
        call = client.captured_add[0]
        assert call["user_id"] == "u123"
        assert call["agent_id"] == "hermes"
        assert call["infer"] is True

    def test_prefetch_uses_local_search_shape(self, monkeypatch):
        client = FakeLocalMemory(search_results={"results": [{"memory": "user is rex"}]})
        provider = self._make_provider(monkeypatch, client)

        provider.queue_prefetch("who is the user")
        provider._prefetch_thread.join(timeout=2)

        assert client.captured_search["query"] == "who is the user"
        assert client.captured_search["filters"] == {"user_id": "u123"}
        assert client.captured_search["limit"] == 5


# ---------------------------------------------------------------------------
# Tool result shape — same JSON contract regardless of backend
# ---------------------------------------------------------------------------


class TestMem0LocalResults:
    """The user-facing tool output must match cloud-mode results."""

    def _make_provider(self, monkeypatch, client):
        provider = Mem0MemoryProvider()
        provider._mode = "local"
        provider._user_id = "u123"
        provider._agent_id = "hermes"
        provider._local_config = {"vector_store": {"provider": "qdrant", "config": {}}}
        monkeypatch.setattr(provider, "_get_client", lambda: client)
        return provider

    def test_search_results_unwrapped(self, monkeypatch):
        client = FakeLocalMemory(search_results={
            "results": [{"memory": "foo", "score": 0.9}, {"memory": "bar", "score": 0.7}]
        })
        provider = self._make_provider(monkeypatch, client)

        result = json.loads(provider.handle_tool_call(
            "mem0_search", {"query": "test", "top_k": 5}
        ))

        assert result["count"] == 2
        assert result["results"][0]["memory"] == "foo"

    def test_profile_empty_message(self, monkeypatch):
        client = FakeLocalMemory(all_results={"results": []})
        provider = self._make_provider(monkeypatch, client)

        result = json.loads(provider.handle_tool_call("mem0_profile", {}))
        assert "No memories" in result["result"]

    def test_search_empty_message(self, monkeypatch):
        client = FakeLocalMemory(search_results={"results": []})
        provider = self._make_provider(monkeypatch, client)

        result = json.loads(provider.handle_tool_call(
            "mem0_search", {"query": "missing"}
        ))
        assert "No relevant memories" in result["result"]


# ---------------------------------------------------------------------------
# Local-mode error path: missing config block
# ---------------------------------------------------------------------------


class TestMem0LocalErrors:
    def test_local_without_config_raises_helpful_error(self, monkeypatch, tmp_path):
        provider = Mem0MemoryProvider()
        provider._mode = "local"
        provider._local_config = None  # explicit: missing config

        # _get_client raises, handle_tool_call catches and returns tool_error JSON
        result = provider.handle_tool_call("mem0_search", {"query": "x"})
        payload = json.loads(result)
        # tool_error returns a string under "error"; surface contains the hint
        body = payload.get("error") or payload.get("result") or json.dumps(payload)
        assert "local mode" in body.lower()
        assert "config" in body.lower()


# ---------------------------------------------------------------------------
# initialize() picks up mode + local_config from env / json
# ---------------------------------------------------------------------------


class TestMem0Initialize:
    def test_initialize_local_mode(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        local_cfg = {
            "vector_store": {"provider": "qdrant", "config": {}},
            "llm": {"provider": "openai", "config": {}},
            "embedder": {"provider": "ollama", "config": {}},
        }
        (tmp_path / "mem0.json").write_text(json.dumps({
            "mode": "local",
            "user_id": "alice",
            "config": local_cfg,
        }))

        provider = Mem0MemoryProvider()
        provider.initialize("session-1")

        assert provider._mode == "local"
        assert provider._user_id == "alice"
        assert provider._local_config == local_cfg

    def test_initialize_cloud_mode_default(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MEM0_API_KEY", "sk-cloud")
        monkeypatch.delenv("MEM0_MODE", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))

        provider = Mem0MemoryProvider()
        provider.initialize("session-1")

        assert provider._mode == "cloud"
        assert provider._api_key == "sk-cloud"
        assert provider._local_config is None
