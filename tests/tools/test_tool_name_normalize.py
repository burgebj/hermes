"""Tests for tool name normalization fallback in ToolRegistry.dispatch().

Covers CamelCase and _tool-suffix drift that Claude models intermittently
emit (e.g. ``TodoTool_tool``, ``Patch_tool``, ``BrowserClick_tool``).
"""

import json

from tools.registry import ToolRegistry, _normalize_tool_name


def _dummy_handler(args, **kwargs):
    return json.dumps({"ok": True})


def _make_schema(name="test_tool"):
    return {
        "name": name,
        "description": f"A {name}",
        "parameters": {"type": "object", "properties": {}},
    }


def _make_registry_with_tools(*tool_names):
    """Return a ToolRegistry pre-populated with the given tool names."""
    reg = ToolRegistry()
    for tname in tool_names:
        reg.register(
            name=tname,
            toolset="core",
            schema=_make_schema(tname),
            handler=_dummy_handler,
        )
    return reg


# ------------------------------------------------------------------
# Unit tests for _normalize_tool_name helper
# ------------------------------------------------------------------

class TestNormalizeToolName:
    def test_todo_tool_tool_resolves_to_todo(self):
        """TodoTool_tool -> strip _tool -> TodoTool -> snake -> todo_tool -> strip _tool -> todo"""
        known = {"todo", "patch", "terminal", "browser_click"}
        assert _normalize_tool_name("TodoTool_tool", known) == "todo"

    def test_patch_tool_resolves_to_patch(self):
        """Patch_tool -> strip _tool -> Patch -> snake -> patch"""
        known = {"todo", "patch", "terminal", "browser_click"}
        assert _normalize_tool_name("Patch_tool", known) == "patch"

    def test_terminal_tool_resolves_to_terminal(self):
        """Terminal_tool -> strip _tool -> Terminal -> snake -> terminal"""
        known = {"todo", "patch", "terminal", "browser_click"}
        assert _normalize_tool_name("Terminal_tool", known) == "terminal"

    def test_browser_click_tool_resolves(self):
        """BrowserClick_tool -> strip _tool -> BrowserClick -> snake -> browser_click"""
        known = {"todo", "patch", "terminal", "browser_click"}
        assert _normalize_tool_name("BrowserClick_tool", known) == "browser_click"

    def test_exact_name_returns_none(self):
        """An already-exact name should not be found by normalize (caller uses exact match)."""
        known = {"todo", "patch"}
        assert _normalize_tool_name("todo", known) is None

    def test_unknown_tool_returns_none(self):
        """A name that doesn't match anything after normalization returns None."""
        known = {"todo", "patch", "terminal", "browser_click"}
        assert _normalize_tool_name("NotARealTool_tool", known) is None

    def test_camel_case_only_without_suffix(self):
        """BrowserClick (no _tool suffix) -> browser_click"""
        known = {"browser_click"}
        assert _normalize_tool_name("BrowserClick", known) == "browser_click"

    def test_already_snake_with_suffix(self):
        """browser_click_tool -> strip _tool -> browser_click"""
        known = {"browser_click"}
        assert _normalize_tool_name("browser_click_tool", known) == "browser_click"


# ------------------------------------------------------------------
# Integration tests through dispatch()
# ------------------------------------------------------------------

class TestDispatchNormalization:
    def test_todo_tool_tool_dispatches(self):
        reg = _make_registry_with_tools("todo", "patch", "terminal", "browser_click")
        result = json.loads(reg.dispatch("TodoTool_tool", {}))
        assert result == {"ok": True}

    def test_patch_tool_dispatches(self):
        reg = _make_registry_with_tools("todo", "patch", "terminal", "browser_click")
        result = json.loads(reg.dispatch("Patch_tool", {}))
        assert result == {"ok": True}

    def test_terminal_tool_dispatches(self):
        reg = _make_registry_with_tools("todo", "patch", "terminal", "browser_click")
        result = json.loads(reg.dispatch("Terminal_tool", {}))
        assert result == {"ok": True}

    def test_browser_click_tool_dispatches(self):
        reg = _make_registry_with_tools("todo", "patch", "terminal", "browser_click")
        result = json.loads(reg.dispatch("BrowserClick_tool", {}))
        assert result == {"ok": True}

    def test_exact_match_still_works(self):
        reg = _make_registry_with_tools("todo")
        result = json.loads(reg.dispatch("todo", {}))
        assert result == {"ok": True}

    def test_unknown_tool_still_returns_error(self):
        reg = _make_registry_with_tools("todo", "patch", "terminal", "browser_click")
        result = json.loads(reg.dispatch("NotARealTool_tool", {}))
        assert "error" in result
        assert "Unknown tool" in result["error"]

    def test_exact_match_wins_over_normalization(self):
        """If a tool is registered with the exact drifted name, use it directly."""
        reg = ToolRegistry()

        def exact_handler(args, **kw):
            return json.dumps({"handler": "exact"})

        def normalized_handler(args, **kw):
            return json.dumps({"handler": "normalized"})

        reg.register(
            name="Patch_tool",
            toolset="core",
            schema=_make_schema("Patch_tool"),
            handler=exact_handler,
        )
        reg.register(
            name="patch",
            toolset="core",
            schema=_make_schema("patch"),
            handler=normalized_handler,
        )
        # Exact match should win -- no normalization needed.
        result = json.loads(reg.dispatch("Patch_tool", {}))
        assert result["handler"] == "exact"

    def test_normalization_logs_warning(self, caplog):
        """Normalization should emit a warning so drift stays visible."""
        import logging

        reg = _make_registry_with_tools("todo")
        with caplog.at_level(logging.WARNING, logger="tools.registry"):
            reg.dispatch("TodoTool_tool", {})

        assert any("Tool name normalized" in msg for msg in caplog.messages)
        assert any("TodoTool_tool" in msg and "todo" in msg for msg in caplog.messages)
