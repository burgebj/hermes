"""Tests for the top-level `./hermes` launcher script."""

import json
import runpy
import sys
import types
from pathlib import Path


def test_launcher_delegates_to_argparse_entrypoint(monkeypatch):
    """`./hermes` should use `hermes_cli.main`, not the legacy Fire wrapper."""
    launcher_path = Path(__file__).resolve().parents[2] / "hermes"
    called = []

    fake_main_module = types.ModuleType("hermes_cli.main")

    def fake_main():
        called.append("hermes_cli.main")

    fake_main_module.main = fake_main
    monkeypatch.setitem(sys.modules, "hermes_cli.main", fake_main_module)

    fake_cli_module = types.ModuleType("cli")

    def legacy_cli_main(*args, **kwargs):
        raise AssertionError("launcher should not import cli.main")

    fake_cli_module.main = legacy_cli_main
    monkeypatch.setitem(sys.modules, "cli", fake_cli_module)

    fake_fire_module = types.ModuleType("fire")

    def legacy_fire(*args, **kwargs):
        raise AssertionError("launcher should not invoke fire.Fire")

    fake_fire_module.Fire = legacy_fire
    monkeypatch.setitem(sys.modules, "fire", fake_fire_module)

    monkeypatch.setattr(sys, "argv", [str(launcher_path), "gateway", "status"])

    runpy.run_path(str(launcher_path), run_name="__main__")

    assert called == ["hermes_cli.main"]


def test_launcher_suppresses_desktop_auto_gateway_when_configured(monkeypatch, tmp_path, capsys):
    """Desktop can opt out of spawning a local gateway from the app wrapper."""
    launcher_path = Path(__file__).resolve().parents[2] / "hermes"
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "desktop.json").write_text(
        json.dumps({"disableAutoGateway": True}), encoding="utf-8"
    )

    fake_main_module = types.ModuleType("hermes_cli.main")

    def fake_main():
        raise AssertionError("suppressed Desktop gateway start should not call main")

    fake_main_module.main = fake_main
    monkeypatch.setitem(sys.modules, "hermes_cli.main", fake_main_module)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv(
        "HERMES_DESKTOP_PARENT_CMD_TEST",
        "/Applications/Hermes Agent.app/Contents/MacOS/Hermes Agent",
    )
    monkeypatch.setattr(sys, "argv", [str(launcher_path), "gateway", "run"])

    try:
        runpy.run_path(str(launcher_path), run_name="__main__")
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("expected launcher suppression to exit")

    assert "auto gateway start suppressed" in capsys.readouterr().out


def test_launcher_does_not_suppress_non_desktop_gateway(monkeypatch, tmp_path):
    """The Desktop guard must not affect normal CLI gateway use."""
    launcher_path = Path(__file__).resolve().parents[2] / "hermes"
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "desktop.json").write_text(
        json.dumps({"disableAutoGateway": True}), encoding="utf-8"
    )
    called = []

    fake_main_module = types.ModuleType("hermes_cli.main")

    def fake_main():
        called.append("hermes_cli.main")

    fake_main_module.main = fake_main
    monkeypatch.setitem(sys.modules, "hermes_cli.main", fake_main_module)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_DESKTOP_PARENT_CMD_TEST", "/bin/zsh")
    monkeypatch.setattr(sys, "argv", [str(launcher_path), "gateway", "run"])

    runpy.run_path(str(launcher_path), run_name="__main__")

    assert called == ["hermes_cli.main"]
