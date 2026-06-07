"""Regression tests for delegate_task runtime config reload.

A long-running gateway can have cli.CLI_CONFIG from process startup while
~/.hermes/config.yaml has since changed. delegate_task runtime knobs must read
fresh persistent config first so updates like delegation.child_timeout_seconds
are honored without relying on stale CLI_CONFIG values.
"""
from __future__ import annotations

import sys
from types import ModuleType


def test_load_config_prefers_fresh_persistent_config_over_stale_cli_config(monkeypatch):
    from tools import delegate_tool
    import hermes_cli.config as config_mod

    fake_cli = ModuleType("cli")
    setattr(
        fake_cli,
        "CLI_CONFIG",
        {
            "delegation": {
                "child_timeout_seconds": 300,
                "max_concurrent_children": 2,
            }
        },
    )
    monkeypatch.setitem(sys.modules, "cli", fake_cli)
    monkeypatch.setattr(
        config_mod,
        "load_config",
        lambda: {
            "delegation": {
                "child_timeout_seconds": 900,
                "max_concurrent_children": 5,
            }
        },
    )

    cfg = delegate_tool._load_config()

    assert cfg["child_timeout_seconds"] == 900
    assert delegate_tool._get_child_timeout() == 900.0
    assert delegate_tool._get_max_concurrent_children() == 5


def test_load_config_does_not_use_stale_cli_when_persistent_config_load_succeeds(monkeypatch):
    from tools import delegate_tool
    import hermes_cli.config as config_mod

    monkeypatch.delenv("DELEGATION_CHILD_TIMEOUT_SECONDS", raising=False)
    fake_cli = ModuleType("cli")
    setattr(fake_cli, "CLI_CONFIG", {"delegation": {"child_timeout_seconds": 300}})
    monkeypatch.setitem(sys.modules, "cli", fake_cli)
    monkeypatch.setattr(config_mod, "load_config", lambda: {})

    assert delegate_tool._load_config() == {}
    assert delegate_tool._get_child_timeout() == float(delegate_tool.DEFAULT_CHILD_TIMEOUT)


def test_load_config_falls_back_to_cli_config_when_persistent_config_unavailable(monkeypatch):
    from tools import delegate_tool
    import hermes_cli.config as config_mod

    fake_cli = ModuleType("cli")
    setattr(fake_cli, "CLI_CONFIG", {"delegation": {"child_timeout_seconds": 300}})
    monkeypatch.setitem(sys.modules, "cli", fake_cli)

    def _raise_load_config():
        raise RuntimeError("config unavailable")

    monkeypatch.setattr(config_mod, "load_config", _raise_load_config)

    cfg = delegate_tool._load_config()

    assert cfg["child_timeout_seconds"] == 300
    assert delegate_tool._get_child_timeout() == 300.0
