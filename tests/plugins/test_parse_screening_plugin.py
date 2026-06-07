from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from hermes_cli.plugins import PluginContext, PluginManager, PluginManifest


def _load_parse_screening_plugin_register():
    plugin_path = Path(__file__).resolve().parents[2] / "plugins" / "parse-screening" / "__init__.py"
    spec = importlib.util.spec_from_file_location("parse_screening_plugin_for_test", plugin_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.register


def test_register_adds_parse_cli_command():
    mgr = PluginManager()
    manifest = PluginManifest(name="parse-screening")
    ctx = PluginContext(manifest, mgr)

    register = _load_parse_screening_plugin_register()
    register(ctx)

    assert "parse" in mgr._cli_commands
    entry = mgr._cli_commands["parse"]
    assert entry["plugin"] == "parse-screening"
    assert callable(entry["setup_fn"])
    assert callable(entry["handler_fn"])


def test_parse_cli_status_subcommand_parses():
    mgr = PluginManager()
    manifest = PluginManifest(name="parse-screening")
    ctx = PluginContext(manifest, mgr)
    register = _load_parse_screening_plugin_register()
    register(ctx)
    entry = mgr._cli_commands["parse"]

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    parse_parser = subparsers.add_parser("parse")
    entry["setup_fn"](parse_parser)
    parse_parser.set_defaults(func=entry["handler_fn"])

    args = parser.parse_args(["parse", "status"])
    assert args.command == "parse"
    assert args.parse_command == "status"
    assert callable(args.func)
