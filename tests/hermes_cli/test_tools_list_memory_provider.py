"""Regression tests for the memory-provider section in `hermes tools list`.

Pins the contract from issue #30979: when `memory.provider` is set in
config.yaml, `_print_tools_list` must surface

- the provider name,
- the tool names it would inject on agent start, and
- a status that mirrors the runtime gate in agent/agent_init.py:
  ✓ injected (memory toolset) | ✓ injected (external provider) |
  ✗ skipped (empty toolset list).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from hermes_cli import tools_config


# ── _active_memory_provider_tools ──────────────────────────────────────────

class TestActiveMemoryProviderTools:
    def test_returns_empty_for_blank_provider(self):
        assert tools_config._active_memory_provider_tools("") == []

    def test_returns_tool_names_from_loaded_provider(self, monkeypatch):
        provider = SimpleNamespace(
            get_tool_schemas=lambda: [
                {"name": "hindsight_recall", "description": "x", "parameters": {}},
                {"name": "hindsight_retain", "description": "x", "parameters": {}},
                {"name": "hindsight_reflect", "description": "x", "parameters": {}},
            ]
        )
        monkeypatch.setattr(
            "plugins.memory.load_memory_provider",
            lambda name: provider if name == "hindsight" else None,
        )
        assert tools_config._active_memory_provider_tools("hindsight") == [
            "hindsight_recall",
            "hindsight_retain",
            "hindsight_reflect",
        ]

    def test_swallows_loader_exceptions(self, monkeypatch):
        def boom(name):
            raise RuntimeError("plugin import failed")
        monkeypatch.setattr("plugins.memory.load_memory_provider", boom)
        assert tools_config._active_memory_provider_tools("hindsight") == []

    def test_returns_empty_when_provider_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            "plugins.memory.load_memory_provider", lambda name: None
        )
        assert tools_config._active_memory_provider_tools("ghost") == []

    def test_skips_schemas_without_name(self, monkeypatch):
        provider = SimpleNamespace(
            get_tool_schemas=lambda: [
                {"name": "ok"},
                {"description": "no name"},
                {"name": ""},
            ]
        )
        monkeypatch.setattr(
            "plugins.memory.load_memory_provider", lambda name: provider
        )
        assert tools_config._active_memory_provider_tools("p") == ["ok"]


# ── _print_tools_list memory-provider section ─────────────────────────────

class TestPrintToolsListMemorySection:
    """Verify the gate-aware status label matches agent_init.py."""

    @pytest.fixture(autouse=True)
    def _stub_provider(self, monkeypatch):
        provider = SimpleNamespace(
            get_tool_schemas=lambda: [
                {"name": "hindsight_recall"},
                {"name": "hindsight_retain"},
                {"name": "hindsight_reflect"},
            ]
        )
        monkeypatch.setattr(
            "plugins.memory.load_memory_provider", lambda name: provider
        )

    def _run(self, enabled_toolsets, capsys, *, provider="hindsight"):
        config = {"memory": {"provider": provider}} if provider else {}
        tools_config._print_tools_list(
            set(enabled_toolsets), {}, "cli", config=config
        )
        return capsys.readouterr().out

    def test_no_provider_no_section(self, capsys):
        out = self._run(["terminal"], capsys, provider="")
        assert "Memory provider" not in out

    def test_memory_in_toolsets_shows_injected(self, capsys):
        out = self._run(["terminal", "memory", "web"], capsys)
        assert "Memory provider (cli):" in out
        assert "hindsight" in out
        assert "injected (memory toolset)" in out
        assert "hindsight_recall, hindsight_retain, hindsight_reflect" in out

    def test_external_provider_no_memory_toolset_shows_injected(self, capsys):
        """#30979: hindsight migration disables `memory` but still injects."""
        out = self._run(["terminal", "web"], capsys)
        assert "injected (external provider)" in out
        assert "hindsight_recall" in out

    def test_empty_toolsets_shows_skipped(self, capsys):
        """#5544: `platform_toolsets: …: []` still suppresses."""
        out = self._run([], capsys)
        assert "skipped (empty toolset list)" in out
        assert "hindsight" in out

    def test_provider_with_no_tools_renders_hint(self, capsys, monkeypatch):
        provider = SimpleNamespace(get_tool_schemas=lambda: [])
        monkeypatch.setattr(
            "plugins.memory.load_memory_provider", lambda name: provider
        )
        out = self._run(["terminal", "memory"], capsys)
        assert "no tools (context mode?)" in out
