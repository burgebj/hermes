"""Tests for the hermes-tools-as-MCP server module surface.

We don't run a live MCP session in unit tests — that requires the codex
subprocess + client + an event loop. These tests pin the static
contract: the module imports, the EXPOSED_TOOLS list is sane, and the
build helper assembles a server when the SDK is present.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import patch

import pytest


class TestModuleSurface:
    def test_module_imports_clean(self):
        from agent.transports import hermes_tools_mcp_server as m
        assert callable(m.main)
        assert callable(m._build_server)
        assert isinstance(m.EXPOSED_TOOLS, tuple)
        assert len(m.EXPOSED_TOOLS) > 0

    def test_exposed_tools_are_safe_subset(self):
        """We MUST NOT expose tools codex already has, because codex'
        own builtins are better-integrated with its sandbox + approvals.
        Specifically: no terminal/shell, no read_file/write_file, no
        patch — those are codex's built-in tools."""
        from agent.transports.hermes_tools_mcp_server import EXPOSED_TOOLS
        forbidden = {
            "terminal", "shell", "read_file", "write_file", "patch",
            "search_files", "process",
        }
        leaked = forbidden & set(EXPOSED_TOOLS)
        assert not leaked, (
            f"these tools must NOT be exposed via the codex callback "
            f"because codex has built-in equivalents: {leaked}"
        )

    def test_expected_hermes_specific_tools_listed(self):
        """The Hermes-specific tools should be present so users on the
        codex runtime keep access to them."""
        from agent.transports.hermes_tools_mcp_server import EXPOSED_TOOLS
        for required in (
            "web_search",
            "web_extract",
            "browser_navigate",
            "vision_analyze",
            "image_generate",
            "skill_view",
        ):
            assert required in EXPOSED_TOOLS, f"missing {required!r}"

    def test_agent_loop_tools_not_exposed(self):
        """delegate_task / memory / session_search / todo require the
        running AIAgent context to dispatch, so a stateless MCP callback
        can't drive them. They must NOT be in EXPOSED_TOOLS."""
        from agent.transports.hermes_tools_mcp_server import EXPOSED_TOOLS
        for agent_loop_tool in ("delegate_task", "memory", "session_search", "todo"):
            assert agent_loop_tool not in EXPOSED_TOOLS, (
                f"{agent_loop_tool!r} requires the agent loop context "
                "and can't be reached through a stateless MCP callback"
            )

    def test_kanban_worker_tools_exposed(self):
        """Kanban workers run as `hermes chat -q` subprocesses; if they
        come up on the codex_app_server runtime, the worker can do the
        actual work via codex's shell but needs the kanban tools through
        the MCP callback to report back to the kernel. Without these
        tools available, the worker would hang at completion time."""
        from agent.transports.hermes_tools_mcp_server import EXPOSED_TOOLS
        # Worker handoff tools — every dispatched worker uses at least
        # one of {complete, block, comment} to close out its task.
        for worker_tool in (
            "kanban_complete",
            "kanban_block",
            "kanban_comment",
            "kanban_heartbeat",
        ):
            assert worker_tool in EXPOSED_TOOLS, (
                f"{worker_tool!r} missing from codex callback — kanban "
                "workers on codex_app_server runtime would hang"
            )

    def test_kanban_orchestrator_tools_exposed(self):
        """Orchestrator agents need to dispatch new tasks, query the
        board, and unblock/link tasks. Exposed so an orchestrator on
        codex_app_server can do its job."""
        from agent.transports.hermes_tools_mcp_server import EXPOSED_TOOLS
        for orch_tool in (
            "kanban_create",
            "kanban_show",
            "kanban_list",
            "kanban_unblock",
            "kanban_link",
        ):
            assert orch_tool in EXPOSED_TOOLS, (
                f"{orch_tool!r} missing from codex callback"
            )

    def test_memory_tool_specs_from_dynamic_provider(self):
        """Memory-provider tools are dynamic and do not live in the static
        Hermes registry. The codex MCP bridge must still be able to surface
        them, otherwise providers like MemOS are invisible on codex runtime."""
        from agent.transports import hermes_tools_mcp_server as m

        class FakeMemoryManager:
            def get_all_tool_schemas(self):
                return [
                    {
                        "name": "memos_search",
                        "description": "Search MemOS",
                        "parameters": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"],
                        },
                    }
                ]

        specs = m._memory_tool_specs(FakeMemoryManager())
        assert "memos_search" in specs
        assert specs["memos_search"]["parameters"]["required"] == ["query"]

    def test_memory_enabled_respects_toolset_filter(self, monkeypatch):
        from agent.transports import hermes_tools_mcp_server as m

        cfg = {
            "memory": {
                "enabled": True,
                "memory_enabled": True,
                "provider": "memtensor",
            }
        }

        monkeypatch.setenv("HERMES_ENABLED_TOOLSETS", "development")
        assert not m._memory_enabled(cfg)

        monkeypatch.setenv("HERMES_ENABLED_TOOLSETS", "development,memory")
        assert m._memory_enabled(cfg)

        monkeypatch.setenv("HERMES_ENABLED_TOOLSETS", "all")
        assert m._memory_enabled(cfg)

        monkeypatch.setenv("HERMES_ENABLED_TOOLSETS", "*")
        assert m._memory_enabled(cfg)

        monkeypatch.setenv("HERMES_DISABLED_TOOLSETS", "memory")
        assert not m._memory_enabled(cfg)

        monkeypatch.setenv("HERMES_DISABLED_TOOLSETS", "all")
        assert not m._memory_enabled(cfg)

        monkeypatch.setenv("HERMES_DISABLED_TOOLSETS", "*")
        assert not m._memory_enabled(cfg)

        monkeypatch.delenv("HERMES_ENABLED_TOOLSETS", raising=False)
        monkeypatch.delenv("HERMES_DISABLED_TOOLSETS", raising=False)
        monkeypatch.setenv("HERMES_SKIP_MEMORY", "1")
        assert not m._memory_enabled(cfg)

    def test_build_server_applies_parent_toolset_filters(self, monkeypatch):
        """Static Hermes tools must respect the parent agent's toolset filter.

        Otherwise a codex_app_server session with enabled_toolsets=["memory"]
        can still see web/browser tools through the MCP callback.
        """
        from agent.transports import hermes_tools_mcp_server as m
        import mcp.server.fastmcp as fastmcp_mod
        import model_tools

        captured = {}

        class FakeFastMCP:
            def __init__(self, *args, **kwargs):
                self.tools = {}

            def add_tool(self, fn, *, name, description):
                self.tools[name] = fn

        def fake_get_tool_definitions(**kwargs):
            captured.update(kwargs)
            if kwargs.get("enabled_toolsets") == ["memory"]:
                return []
            return [
                {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search web",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ]

        monkeypatch.setenv("HERMES_ENABLED_TOOLSETS", "memory")
        monkeypatch.setenv("HERMES_DISABLED_TOOLSETS", "browser")
        monkeypatch.setattr(fastmcp_mod, "FastMCP", FakeFastMCP)
        monkeypatch.setattr(model_tools, "get_tool_definitions", fake_get_tool_definitions)
        monkeypatch.setattr(m, "_build_memory_manager_for_mcp", lambda: None)

        server = m._build_server()

        assert captured["enabled_toolsets"] == ["memory"]
        assert captured["disabled_toolsets"] == ["browser"]
        assert "web_search" not in server.tools

    def test_build_server_registers_dynamic_memory_tools(self, monkeypatch):
        """Regression guard for MemOS under codex_app_server: memos_search is
        not in get_tool_definitions(), so _build_server must merge the active
        MemoryManager schemas explicitly."""
        from agent.transports import hermes_tools_mcp_server as m
        import mcp.server.fastmcp as fastmcp_mod
        import model_tools

        class FakeMemoryManager:
            def __init__(self):
                self.shutdown_called = False

            def get_all_tool_schemas(self):
                return [
                    {
                        "name": "memos_search",
                        "description": "Search MemOS",
                        "parameters": {"type": "object", "properties": {}},
                    }
                ]

            def handle_tool_call(self, tool_name, args):
                return '{"ok": true}'

            def shutdown_all(self):
                self.shutdown_called = True

        class FakeFastMCP:
            def __init__(self, *args, **kwargs):
                self.tools = {}

            def add_tool(self, fn, *, name, description):
                self.tools[name] = {
                    "fn": fn,
                    "description": description,
                }

        fake_manager = FakeMemoryManager()
        monkeypatch.setattr(fastmcp_mod, "FastMCP", FakeFastMCP)
        monkeypatch.setattr(
            model_tools,
            "get_tool_definitions",
            lambda **kwargs: [],
        )
        monkeypatch.setattr(m, "_build_memory_manager_for_mcp", lambda: fake_manager)

        server = m._build_server()

        assert "memos_search" in server.tools
        assert server.tools["memos_search"]["fn"](query="abc") == '{"ok": true}'

    def test_memory_manager_bootstrap_passes_session_title(self, monkeypatch, tmp_path):
        """MCP memory tools must resolve provider scope like the parent agent."""
        from agent.transports import hermes_tools_mcp_server as m
        import agent.memory_manager as memory_manager_mod
        import hermes_cli.config as config_mod
        import hermes_constants as constants_mod
        import plugins.memory as memory_plugins_mod

        captured = {}

        class FakeProvider:
            name = "memtensor"

            def is_available(self):
                return True

        class FakeMemoryManager:
            def add_provider(self, provider):
                captured["provider"] = provider.name

            def initialize_all(self, session_id, **kwargs):
                captured["session_id"] = session_id
                captured.update(kwargs)

        monkeypatch.setattr(
            config_mod,
            "load_config",
            lambda: {
                "memory": {
                    "enabled": True,
                    "memory_enabled": True,
                    "provider": "memtensor",
                }
            },
        )
        monkeypatch.setattr(memory_plugins_mod, "load_memory_provider", lambda name: FakeProvider())
        monkeypatch.setattr(memory_manager_mod, "MemoryManager", FakeMemoryManager)
        monkeypatch.setattr(constants_mod, "get_hermes_home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_SESSION_ID", "sess-123")
        monkeypatch.setenv("HERMES_SESSION_TITLE", "Project Alpha")

        assert m._build_memory_manager_for_mcp() is not None
        assert captured["session_id"] == "sess-123"
        assert captured["session_title"] == "Project Alpha"

    def test_generated_handler_uses_schema_args_not_kwargs(self):
        """FastMCP must see `query`, not a synthetic `kwargs` argument."""
        from agent.transports import hermes_tools_mcp_server as m
        from mcp.server.fastmcp.tools import Tool

        handler = m._make_mcp_handler(
            tool_name="memos_search",
            description="Search MemOS",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "maxResults": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
            dispatcher=lambda kwargs: json.dumps(kwargs),
        )
        tool = Tool.from_function(
            handler,
            name="memos_search",
            description="Search MemOS",
        )

        assert "query" in tool.parameters["properties"]
        assert "kwargs" not in tool.parameters["properties"]
        result = asyncio.run(tool.run({"query": "abc", "maxResults": 3}))
        assert json.loads(result) == {"query": "abc", "maxResults": 3}


class TestMain:
    def test_main_returns_2_when_mcp_unavailable(self, monkeypatch):
        """When the mcp package isn't installed, main() should exit
        cleanly with code 2 and an install hint, not crash."""
        import agent.transports.hermes_tools_mcp_server as m

        def boom_build(*a, **kw):
            raise ImportError("mcp not installed")

        monkeypatch.setattr(m, "_build_server", boom_build)
        rc = m.main(["--verbose"])
        assert rc == 2

    def test_main_handles_keyboard_interrupt(self, monkeypatch):
        import agent.transports.hermes_tools_mcp_server as m

        class FakeServer:
            def run(self):
                raise KeyboardInterrupt()

        monkeypatch.setattr(m, "_build_server", lambda: FakeServer())
        rc = m.main([])
        assert rc == 0

    def test_main_returns_1_on_runtime_error(self, monkeypatch):
        import agent.transports.hermes_tools_mcp_server as m

        class CrashingServer:
            def run(self):
                raise RuntimeError("boom")

        monkeypatch.setattr(m, "_build_server", lambda: CrashingServer())
        rc = m.main([])
        assert rc == 1
