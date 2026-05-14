"""Tests for ``hermes mcp sync`` shared profile MCP configuration."""

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml


class TestSharedMcpServerLoading:
    def test_load_shared_mcp_servers_accepts_wrapped_mcp_servers(self, tmp_path):
        shared = tmp_path / "mcp_servers.yaml"
        shared.write_text("""
mcp_servers:
  prism:
    command: prism-mcp
""")

        from hermes_cli.mcp_config import _load_shared_mcp_servers

        assert _load_shared_mcp_servers(shared) == {"prism": {"command": "prism-mcp"}}

    def test_load_shared_mcp_servers_accepts_raw_mapping(self, tmp_path):
        shared = tmp_path / "mcp_servers.yaml"
        shared.write_text("""
prism:
  command: prism-mcp
""")

        from hermes_cli.mcp_config import _load_shared_mcp_servers

        assert _load_shared_mcp_servers(shared) == {"prism": {"command": "prism-mcp"}}

    def test_load_shared_mcp_servers_rejects_non_mapping_server_entry(self, tmp_path):
        shared = tmp_path / "mcp_servers.yaml"
        shared.write_text("mcp_servers:\n  prism: nope\n")

        from hermes_cli.mcp_config import _load_shared_mcp_servers

        with pytest.raises(ValueError, match="prism"):
            _load_shared_mcp_servers(shared)

    def test_load_shared_mcp_servers_reports_missing_file(self, tmp_path):
        from hermes_cli.mcp_config import _load_shared_mcp_servers

        with pytest.raises(FileNotFoundError, match="Shared MCP file not found"):
            _load_shared_mcp_servers(tmp_path / "missing.yaml")


class TestMcpSyncPlanning:
    def test_plan_mcp_sync_adds_missing_server(self):
        from hermes_cli.mcp_config import _plan_mcp_sync

        plan = _plan_mcp_sync(
            target_servers={},
            shared_servers={"prism": {"command": "prism-mcp"}},
            selected_names=None,
            force=False,
        )

        assert plan.merged_servers == {"prism": {"command": "prism-mcp"}}
        assert plan.added == ["prism"]
        assert plan.changed is True

    def test_plan_mcp_sync_skips_identical_server(self):
        from hermes_cli.mcp_config import _plan_mcp_sync

        cfg = {"command": "prism-mcp"}
        plan = _plan_mcp_sync(
            target_servers={"prism": cfg},
            shared_servers={"prism": cfg},
            selected_names=None,
            force=False,
        )

        assert plan.skipped == ["prism"]
        assert plan.changed is False

    def test_plan_mcp_sync_conflicts_without_force(self):
        from hermes_cli.mcp_config import _plan_mcp_sync

        plan = _plan_mcp_sync(
            target_servers={"prism": {"command": "old"}},
            shared_servers={"prism": {"command": "new"}},
            selected_names=None,
            force=False,
        )

        assert plan.conflicts == ["prism"]
        assert plan.merged_servers["prism"] == {"command": "old"}
        assert plan.changed is False

    def test_plan_mcp_sync_replaces_conflict_with_force(self):
        from hermes_cli.mcp_config import _plan_mcp_sync

        plan = _plan_mcp_sync(
            target_servers={"prism": {"command": "old"}},
            shared_servers={"prism": {"command": "new"}},
            selected_names=None,
            force=True,
        )

        assert plan.updated == ["prism"]
        assert plan.merged_servers["prism"] == {"command": "new"}
        assert plan.changed is True

    def test_plan_mcp_sync_respects_selected_names(self):
        from hermes_cli.mcp_config import _plan_mcp_sync

        plan = _plan_mcp_sync(
            target_servers={},
            shared_servers={"prism": {"command": "p"}, "qmd": {"url": "u"}},
            selected_names={"qmd"},
            force=False,
        )

        assert plan.added == ["qmd"]
        assert "prism" not in plan.merged_servers


class TestMcpSyncTargetResolution:
    def test_resolve_sync_targets_explicit_profiles(self, monkeypatch, tmp_path):
        from hermes_cli.mcp_config import _resolve_mcp_sync_targets

        (tmp_path / "main").mkdir()
        (tmp_path / "therapy").mkdir()
        monkeypatch.setattr(
            "hermes_cli.profiles.get_profile_dir", lambda name: tmp_path / name
        )

        targets = _resolve_mcp_sync_targets(
            profile_names=["main", "therapy"], all_profiles=False
        )

        assert [t.name for t in targets] == ["main", "therapy"]
        assert [t.config_path for t in targets] == [
            tmp_path / "main" / "config.yaml",
            tmp_path / "therapy" / "config.yaml",
        ]

    def test_resolve_sync_targets_all_profiles(self, monkeypatch, tmp_path):
        from hermes_cli.mcp_config import _resolve_mcp_sync_targets

        monkeypatch.setattr(
            "hermes_cli.profiles.list_profiles",
            lambda: [
                SimpleNamespace(name="default", path=tmp_path / "default"),
                SimpleNamespace(name="main", path=tmp_path / "main"),
            ],
        )

        targets = _resolve_mcp_sync_targets(profile_names=[], all_profiles=True)

        assert [t.name for t in targets] == ["default", "main"]
        assert [t.config_path for t in targets] == [
            tmp_path / "default" / "config.yaml",
            tmp_path / "main" / "config.yaml",
        ]

    def test_resolve_sync_targets_rejects_all_plus_explicit_profile(self):
        from hermes_cli.mcp_config import _resolve_mcp_sync_targets

        with pytest.raises(ValueError, match="either --all or --profile"):
            _resolve_mcp_sync_targets(profile_names=["main"], all_profiles=True)

    def test_resolve_sync_targets_rejects_invalid_profile_name(self):
        from hermes_cli.mcp_config import _resolve_mcp_sync_targets

        with pytest.raises(ValueError, match="Invalid profile name"):
            _resolve_mcp_sync_targets(profile_names=["../escape"], all_profiles=False)

    def test_resolve_sync_targets_rejects_missing_named_profile(self, monkeypatch, tmp_path):
        from hermes_cli.mcp_config import _resolve_mcp_sync_targets

        monkeypatch.setattr(
            "hermes_cli.profiles.get_profile_dir", lambda name: tmp_path / name
        )

        with pytest.raises(FileNotFoundError, match="Profile 'missing' does not exist"):
            _resolve_mcp_sync_targets(profile_names=["missing"], all_profiles=False)

        assert not (tmp_path / "missing" / "config.yaml").exists()

    def test_resolve_sync_targets_requires_a_target(self):
        from hermes_cli.mcp_config import _resolve_mcp_sync_targets

        with pytest.raises(ValueError, match="Specify --profile"):
            _resolve_mcp_sync_targets(profile_names=[], all_profiles=False)


class TestMcpSyncCommand:
    def test_cmd_mcp_sync_dry_run_does_not_write(self, tmp_path, monkeypatch, capsys):
        shared = tmp_path / "shared.yaml"
        shared.write_text("mcp_servers:\n  prism:\n    command: prism-mcp\n")
        profile = tmp_path / "main"
        profile.mkdir()
        config_path = profile / "config.yaml"
        config_path.write_text("model:\n  default: gpt-5.5\n")

        monkeypatch.setattr(
            "hermes_cli.mcp_config._resolve_mcp_sync_targets",
            lambda profile_names, all_profiles: [
                SimpleNamespace(name="main", config_path=config_path)
            ],
        )

        from hermes_cli.mcp_config import cmd_mcp_sync

        args = SimpleNamespace(
            shared=str(shared),
            profile=["main"],
            all=False,
            servers=None,
            dry_run=True,
            force=False,
        )
        cmd_mcp_sync(args)

        out = capsys.readouterr().out
        assert "DRY RUN" in out
        assert "prism" in out
        assert "mcp_servers" not in config_path.read_text()

    def test_cmd_mcp_sync_writes_config_preserving_other_sections(
        self, tmp_path, monkeypatch, capsys
    ):
        shared = tmp_path / "shared.yaml"
        shared.write_text("mcp_servers:\n  prism:\n    command: prism-mcp\n")
        profile = tmp_path / "main"
        profile.mkdir()
        config_path = profile / "config.yaml"
        config_path.write_text("model:\n  default: gpt-5.5\n")

        monkeypatch.setattr(
            "hermes_cli.mcp_config._resolve_mcp_sync_targets",
            lambda profile_names, all_profiles: [
                SimpleNamespace(name="main", config_path=config_path)
            ],
        )

        from hermes_cli.mcp_config import cmd_mcp_sync

        args = SimpleNamespace(
            shared=str(shared),
            profile=["main"],
            all=False,
            servers=None,
            dry_run=False,
            force=False,
        )
        cmd_mcp_sync(args)

        out = capsys.readouterr().out
        written = yaml.safe_load(config_path.read_text())
        assert "Synced" in out
        assert written["model"] == {"default": "gpt-5.5"}
        assert written["mcp_servers"] == {"prism": {"command": "prism-mcp"}}

    def test_cmd_mcp_sync_reports_conflict_without_force(
        self, tmp_path, monkeypatch, capsys
    ):
        shared = tmp_path / "shared.yaml"
        shared.write_text("mcp_servers:\n  prism:\n    command: new\n")
        profile = tmp_path / "main"
        profile.mkdir()
        config_path = profile / "config.yaml"
        config_path.write_text("mcp_servers:\n  prism:\n    command: old\n")

        monkeypatch.setattr(
            "hermes_cli.mcp_config._resolve_mcp_sync_targets",
            lambda profile_names, all_profiles: [
                SimpleNamespace(name="main", config_path=config_path)
            ],
        )

        from hermes_cli.mcp_config import cmd_mcp_sync

        args = SimpleNamespace(
            shared=str(shared),
            profile=["main"],
            all=False,
            servers=None,
            dry_run=False,
            force=False,
        )
        cmd_mcp_sync(args)

        out = capsys.readouterr().out
        written = yaml.safe_load(config_path.read_text())
        assert "conflict" in out.lower()
        assert written["mcp_servers"]["prism"] == {"command": "old"}

    def test_cmd_mcp_sync_selected_servers_only(self, tmp_path, monkeypatch):
        shared = tmp_path / "shared.yaml"
        shared.write_text(
            "mcp_servers:\n  prism:\n    command: p\n  qmd:\n    url: http://localhost/sse\n"
        )
        profile = tmp_path / "main"
        profile.mkdir()
        config_path = profile / "config.yaml"
        config_path.write_text("{}\n")

        monkeypatch.setattr(
            "hermes_cli.mcp_config._resolve_mcp_sync_targets",
            lambda profile_names, all_profiles: [
                SimpleNamespace(name="main", config_path=config_path)
            ],
        )

        from hermes_cli.mcp_config import cmd_mcp_sync

        args = SimpleNamespace(
            shared=str(shared),
            profile=["main"],
            all=False,
            servers=["qmd"],
            dry_run=False,
            force=False,
        )
        cmd_mcp_sync(args)

        written = yaml.safe_load(config_path.read_text())
        assert written["mcp_servers"] == {"qmd": {"url": "http://localhost/sse"}}

    def test_cmd_mcp_sync_unknown_selected_server_errors(
        self, tmp_path, monkeypatch, capsys
    ):
        shared = tmp_path / "shared.yaml"
        shared.write_text("mcp_servers:\n  prism:\n    command: p\n")
        profile = tmp_path / "main"
        profile.mkdir()
        config_path = profile / "config.yaml"
        config_path.write_text("{}\n")

        monkeypatch.setattr(
            "hermes_cli.mcp_config._resolve_mcp_sync_targets",
            lambda profile_names, all_profiles: [
                SimpleNamespace(name="main", config_path=config_path)
            ],
        )

        from hermes_cli.mcp_config import cmd_mcp_sync

        args = SimpleNamespace(
            shared=str(shared),
            profile=["main"],
            all=False,
            servers=["missing"],
            dry_run=False,
            force=False,
        )
        cmd_mcp_sync(args)

        out = capsys.readouterr().out
        assert "Unknown shared MCP server" in out
        assert yaml.safe_load(config_path.read_text()) == {}

    def test_cmd_mcp_sync_missing_profile_does_not_show_shared_file_hint(
        self, tmp_path, monkeypatch, capsys
    ):
        shared = tmp_path / "shared.yaml"
        shared.write_text("mcp_servers:\n  prism:\n    command: p\n")

        def raise_missing_profile(profile_names, all_profiles):
            raise FileNotFoundError("Profile 'missing' does not exist")

        monkeypatch.setattr(
            "hermes_cli.mcp_config._resolve_mcp_sync_targets",
            raise_missing_profile,
        )

        from hermes_cli.mcp_config import cmd_mcp_sync

        args = SimpleNamespace(
            shared=str(shared),
            profile=["missing"],
            all=False,
            servers=None,
            dry_run=False,
            force=False,
        )
        cmd_mcp_sync(args)

        out = capsys.readouterr().out
        assert "Profile 'missing' does not exist" in out
        assert "mkdir -p ~/.hermes/shared" not in out


def test_mcp_dispatcher_routes_sync(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "hermes_cli.mcp_config.cmd_mcp_sync",
        lambda args: calls.append(args.mcp_action),
    )

    from hermes_cli.mcp_config import mcp_command

    mcp_command(SimpleNamespace(mcp_action="sync"))

    assert calls == ["sync"]


def test_cli_mcp_sync_profile_flag_is_not_consumed_by_global_profile_override(tmp_path):
    """`mcp sync --profile` is a local flag, not the global profile override."""
    hermes_home = tmp_path / "hermes-home"
    hermes_home.mkdir()
    shared = tmp_path / "shared.yaml"
    shared.write_text("mcp_servers:\n  demo:\n    command: demo-mcp\n")

    env = os.environ.copy()
    env["HERMES_HOME"] = str(hermes_home)
    env["NO_COLOR"] = "1"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermes_cli.main",
            "mcp",
            "sync",
            "--shared",
            str(shared),
            "--profile",
            "default",
            "--dry-run",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 0
    assert "Profile: default" in combined
    assert "Specify --profile NAME or --all" not in combined
