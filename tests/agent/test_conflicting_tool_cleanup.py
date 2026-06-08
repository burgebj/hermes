"""Regression tests for conflicting tool name cleanup (#40466).

When a memory provider registers a tool whose name collides with a built-in
tool, ``agent_init`` skips adding the schema to ``agent.tools`` — but the
entry in ``_memory_manager._tool_to_provider`` was previously left intact.
This caused ``invoke_tool()`` to dispatch to the provider handler instead of
the built-in, producing errors.

The fix adds ``MemoryManager.unregister_tool()`` and calls it during init.
"""

from agent.memory_manager import MemoryManager


class _FakeProvider:
    """Minimal memory provider for testing."""

    def __init__(self, name, tools=None):
        self.name = name
        self._tools = tools or []

    def get_tool_schemas(self):
        return self._tools

    def is_available(self):
        return True

    def initialize(self, session_id, **kwargs):
        pass

    def shutdown(self):
        pass


class TestUnregisterTool:
    """Unit tests for MemoryManager.unregister_tool()."""

    def test_unregister_removes_tool(self):
        mm = MemoryManager()
        provider = _FakeProvider("p1", [{"name": "clarify", "description": "x"}])
        mm.add_provider(provider)
        assert mm.has_tool("clarify")

        mm.unregister_tool("clarify")
        assert not mm.has_tool("clarify")

    def test_unregister_nonexistent_is_noop(self):
        mm = MemoryManager()
        # Should not raise
        mm.unregister_tool("nonexistent_tool")

    def test_unregister_does_not_affect_other_tools(self):
        mm = MemoryManager()
        provider = _FakeProvider("p1", [
            {"name": "tool_a", "description": "a"},
            {"name": "tool_b", "description": "b"},
        ])
        mm.add_provider(provider)

        mm.unregister_tool("tool_a")
        assert not mm.has_tool("tool_a")
        assert mm.has_tool("tool_b")


class TestConflictCleanupIntegration:
    """Test that conflicting tools are cleaned up from _tool_to_provider."""

    def test_conflicting_tool_removed_from_routing_table(self):
        """Simulate the agent_init conflict-detection logic."""
        mm = MemoryManager()

        # Provider registers a tool named "clarify" (conflicts with built-in)
        provider = _FakeProvider("ext", [
            {"name": "clarify", "description": "external clarify"},
            {"name": "my_custom_tool", "description": "custom"},
        ])
        mm.add_provider(provider)

        # Both tools should be registered initially
        assert mm.has_tool("clarify")
        assert mm.has_tool("my_custom_tool")

        # Simulate agent_init's conflict detection:
        # "clarify" is already in _existing_tool_names (built-in)
        existing_tool_names = {"clarify", "memory", "todo"}
        for schema in mm.get_all_tool_schemas():
            tname = schema.get("name", "")
            if tname and tname in existing_tool_names:
                mm.unregister_tool(tname)
                continue
            # Would add to agent.tools here

        # "clarify" should be removed from routing table
        assert not mm.has_tool("clarify")
        # "my_custom_tool" should remain
        assert mm.has_tool("my_custom_tool")

    def test_unaffected_tools_still_dispatch(self):
        """Non-conflicting tools should still be callable after cleanup."""
        mm = MemoryManager()

        class _CallableProvider(_FakeProvider):
            def handle_tool_call(self, tool_name, args, **kwargs):
                return f"handled:{tool_name}"

        provider = _CallableProvider("ext", [
            {"name": "clarify", "description": "conflicts"},
            {"name": "my_tool", "description": "no conflict"},
        ])
        mm.add_provider(provider)

        # Simulate conflict cleanup
        existing = {"clarify"}
        for schema in mm.get_all_tool_schemas():
            tname = schema.get("name", "")
            if tname and tname in existing:
                mm.unregister_tool(tname)

        # my_tool should still dispatch correctly
        assert mm.has_tool("my_tool")
        result = mm.handle_tool_call("my_tool", {})
        assert result == "handled:my_tool"

        # clarify should NOT dispatch
        assert not mm.has_tool("clarify")
