"""Tests for user-facing MCP server status snapshots."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _make_mcp_tool(name="ping"):
    return SimpleNamespace(
        name=name,
        description=name,
        inputSchema={"type": "object", "properties": {}},
    )


def _make_mock_server(name, session=None, tools=None):
    from tools.mcp_tool import MCPServerTask

    server = MCPServerTask(name)
    server.session = session
    server._tools = tools or []
    return server


def _reset_mcp_status_state(mcp):
    with mcp._lock:
        mcp._servers.clear()
        mcp._connecting_servers.clear()
        mcp._failed_servers.clear()


def test_configured_enabled_server_is_pending_before_discovery_attempt():
    import tools.mcp_tool as mcp

    fake_config = {"slow": {"command": "npx", "args": ["demo"]}}
    _reset_mcp_status_state(mcp)

    with patch("tools.mcp_tool._MCP_AVAILABLE", True), \
         patch("tools.mcp_tool._load_mcp_config", return_value=fake_config):
        status = mcp.get_mcp_status()

    assert status == [{
        "name": "slow",
        "transport": "stdio",
        "tools": 0,
        "connected": False,
        "disabled": False,
        "status": "pending",
    }]


def test_register_mcp_servers_marks_connecting_then_failed():
    import tools.mcp_tool as mcp

    fake_config = {"broken": {"command": "npx", "args": ["bad"]}}
    observed_statuses = []

    async def fail_register(name, cfg):
        observed_statuses.append(mcp.get_mcp_status()[0]["status"])
        raise ConnectionError("cannot reach server")

    _reset_mcp_status_state(mcp)
    try:
        with patch("tools.mcp_tool._MCP_AVAILABLE", True), \
             patch("tools.mcp_tool._load_mcp_config", return_value=fake_config), \
             patch("tools.mcp_tool._discover_and_register_server", side_effect=fail_register), \
             patch("tools.mcp_tool._existing_tool_names", return_value=[]):
            mcp._ensure_mcp_loop()
            mcp.register_mcp_servers(fake_config)
            final_status = mcp.get_mcp_status()

        assert observed_statuses == ["connecting"]
        assert final_status[0]["status"] == "failed"
        assert final_status[0]["connected"] is False
        assert final_status[0]["disabled"] is False
    finally:
        _reset_mcp_status_state(mcp)


def test_register_mcp_servers_clears_connecting_after_success():
    import tools.mcp_tool as mcp

    fake_config = {"ok": {"command": "npx", "args": ["good"]}}
    observed_statuses = []

    async def ok_register(name, cfg):
        observed_statuses.append(mcp.get_mcp_status()[0]["status"])
        server = _make_mock_server(
            name,
            session=MagicMock(),
            tools=[_make_mcp_tool("ping")],
        )
        server._registered_tool_names = ["mcp_ok_ping"]
        mcp._servers[name] = server
        return ["mcp_ok_ping"]

    _reset_mcp_status_state(mcp)
    try:
        with patch("tools.mcp_tool._MCP_AVAILABLE", True), \
             patch("tools.mcp_tool._load_mcp_config", return_value=fake_config), \
             patch("tools.mcp_tool._discover_and_register_server", side_effect=ok_register), \
             patch("tools.mcp_tool._existing_tool_names", return_value=["mcp_ok_ping"]):
            mcp._ensure_mcp_loop()
            mcp.register_mcp_servers(fake_config)
            final_status = mcp.get_mcp_status()

        assert observed_statuses == ["connecting"]
        assert final_status[0]["status"] == "connected"
        assert final_status[0]["connected"] is True
        assert final_status[0]["tools"] == 1
        with mcp._lock:
            assert "ok" not in mcp._connecting_servers
            assert "ok" not in mcp._failed_servers
    finally:
        _reset_mcp_status_state(mcp)
