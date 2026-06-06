"""Tests for plugins/dgx/__init__.py — plugin registration and YAML manifest."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Plugin manifest
# ---------------------------------------------------------------------------

class TestPluginYaml:
    def _manifest(self) -> dict:
        path = Path(__file__).parents[2] / "plugins" / "dgx" / "plugin.yaml"
        with open(path) as f:
            return yaml.safe_load(f)

    def test_manifest_is_valid_yaml(self):
        assert self._manifest() is not None

    def test_manifest_has_required_fields(self):
        m = self._manifest()
        for field in ("name", "version", "description"):
            assert field in m, f"missing field: {field}"

    def test_manifest_name_is_dgx(self):
        assert self._manifest()["name"] == "dgx"


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------

class TestRegister:
    def _register(self):
        from plugins.dgx import register
        tools = []
        commands = []

        class FakeCtx:
            def register_cli_command(self, **kw):
                commands.append(kw)

            def register_tool(self, name, **kw):
                tools.append(name)

        register(FakeCtx())
        return tools, commands

    def test_registers_dgx_cli_command(self):
        _, commands = self._register()
        names = [c["name"] for c in commands]
        assert "dgx" in names

    def test_dgx_command_has_help_text(self):
        _, commands = self._register()
        dgx_cmd = next(c for c in commands if c["name"] == "dgx")
        assert dgx_cmd.get("help")

    def test_handler_is_callable(self):
        _, commands = self._register()
        dgx_cmd = next(c for c in commands if c["name"] == "dgx")
        assert callable(dgx_cmd["handler_fn"])

    def test_setup_fn_accepts_argparse_subparser(self):
        import argparse
        _, commands = self._register()
        dgx_cmd = next(c for c in commands if c["name"] == "dgx")
        sub = argparse.ArgumentParser()
        dgx_cmd["setup_fn"](sub)  # should not raise
