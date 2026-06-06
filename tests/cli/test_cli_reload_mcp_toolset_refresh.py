"""Regression test for /reload-mcp refreshing enabled_toolsets from live config.

When an MCP server is added mid-session (via /mcp-add or by editing
config.yaml directly), its toolset name lands in
``platform_toolsets[cli]``.  ``/reload-mcp`` must re-read the live config
rather than reusing the snapshot the agent was constructed with — otherwise
the new MCP tools are registered but stay invisible to the model on the
next turn.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _make_cli(stale_toolsets):
    import cli as cli_mod

    obj = object.__new__(cli_mod.HermesCLI)
    obj.agent = SimpleNamespace(
        enabled_toolsets=set(stale_toolsets),
        tools=[],
        valid_tool_names=set(),
        _persist_session=lambda *_a, **_kw: None,
    )
    obj._command_running = True
    obj.conversation_history = []
    return obj


def test_reload_mcp_rereads_enabled_toolsets_from_live_config():
    cli_obj = _make_cli(stale_toolsets={"web", "terminal"})

    # The user added an MCP server "github" mid-session, so the live config
    # now lists it under platform_toolsets.cli.
    fresh_toolsets = {"web", "terminal", "github"}

    with patch("tools.mcp_tool.shutdown_mcp_servers"), \
         patch("tools.mcp_tool.discover_mcp_tools", return_value=[]), \
         patch("tools.mcp_tool._servers", {"github": object()}), \
         patch("tools.mcp_tool._lock", MagicMock(__enter__=lambda *_: None,
                                                 __exit__=lambda *_: None)), \
         patch("hermes_cli.tools_config._get_platform_tools",
               return_value=fresh_toolsets) as mock_get_tools, \
         patch("hermes_cli.config.load_config", return_value={"fake": "cfg"}), \
         patch("cli.get_tool_definitions", return_value=[]):
        cli_obj._reload_mcp()

    mock_get_tools.assert_called_once()
    args, kwargs = mock_get_tools.call_args
    assert args[0] == {"fake": "cfg"}
    assert args[1] == "cli"
    assert cli_obj.agent.enabled_toolsets == fresh_toolsets
