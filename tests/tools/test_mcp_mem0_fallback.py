"""Regression tests for the Mem0 MCP list/get_all compatibility shim."""

import json
from unittest.mock import MagicMock


class _AsyncLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _result(text: str, *, is_error: bool):
    result = MagicMock()
    result.isError = is_error
    block = MagicMock()
    block.text = text
    result.content = [block]
    result.structuredContent = None
    return result


def test_mem0_list_fallback_arguments_clamps_to_search_limit():
    from tools.mcp_tool import _mem0_list_fallback_arguments

    args = {"args": {"user_id": "jason", "limit": 500}}
    error = "Top-level entity parameters frozenset({'user_id'}) are not supported in get_all()."

    assert _mem0_list_fallback_arguments("mem0", "list_memories", args, error) == {
        "args": {"query": " ", "user_id": "jason", "limit": 50}
    }


def test_mem0_list_handler_falls_back_to_search(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    from tools import mcp_tool
    from tools.mcp_tool import _make_tool_handler

    calls = []

    async def _call_tool(name, arguments=None):
        calls.append((name, arguments))
        if name == "list_memories":
            return _result(
                "Top-level entity parameters frozenset({'user_id'}) are not supported in get_all(). "
                "Use filters={'user_id': '...'} instead.",
                is_error=True,
            )
        assert name == "search_memories"
        return _result('{"result":{"results":[{"memory":"alpha"}]}}', is_error=False)

    server = MagicMock()
    server.session = MagicMock()
    server.session.call_tool = _call_tool
    server._rpc_lock = _AsyncLock()
    mcp_tool._servers["mem0"] = server
    mcp_tool._server_error_counts.pop("mem0", None)
    if hasattr(mcp_tool, "_server_breaker_opened_at"):
        mcp_tool._server_breaker_opened_at.pop("mem0", None)
    mcp_tool._ensure_mcp_loop()

    try:
        handler = _make_tool_handler("mem0", "list_memories", 10.0)
        parsed = json.loads(handler({"args": {"user_id": "jason", "limit": 5}}))

        assert "error" not in parsed
        assert "alpha" in parsed["result"]
        assert calls == [
            ("list_memories", {"args": {"user_id": "jason", "limit": 5}}),
            ("search_memories", {"args": {"query": " ", "user_id": "jason", "limit": 5}}),
        ]
    finally:
        mcp_tool._servers.pop("mem0", None)
        mcp_tool._server_error_counts.pop("mem0", None)
        if hasattr(mcp_tool, "_server_breaker_opened_at"):
            mcp_tool._server_breaker_opened_at.pop("mem0", None)
