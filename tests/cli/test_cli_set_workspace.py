"""Tests for the /set-workspace slash command.

Covers _handle_set_workspace_command on HermesCLI:
  - no-arg shows current TERMINAL_CWD + usage hint (no env mutation)
  - bad path is rejected, env unchanged
  - valid path updates TERMINAL_CWD
  - ~ and $VAR expansion
  - relative paths resolve against current TERMINAL_CWD
  - quoted paths (single + double) handled
  - same-dir is a no-op
  - active terminal envs and cached file_ops have their .cwd synced
  - the command is registered with the expected aliases (cd, workspace, ...)

We don't go through the full HermesCLI __init__ -- the command handler is
self-contained, so we instantiate the class via __new__ and call the method
directly. _cprint is patched (it goes through prompt_toolkit which doesn't
play nice with capsys), and we assert on its call args instead of stdout.
That mirrors the pattern in test_cli_prefix_matching / test_busy_input_mode.
"""

from unittest.mock import MagicMock, patch

import os
import pytest

import cli as cli_mod
from cli import HermesCLI


@pytest.fixture
def bare_cli():
    return object.__new__(HermesCLI)


@pytest.fixture
def two_dirs(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    return a, b


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    """Pin TERMINAL_CWD to a known temp dir so tests don't bleed into each other."""
    start = tmp_path / "_start"
    start.mkdir()
    monkeypatch.setenv("TERMINAL_CWD", str(start))


@pytest.fixture
def patched_caches(monkeypatch):
    """Empty out the terminal_tool / file_tools caches so we can inject fakes."""
    import threading
    import tools.terminal_tool as tt
    import tools.file_tools as ft

    monkeypatch.setattr(tt, "_active_environments", {}, raising=True)
    monkeypatch.setattr(tt, "_env_lock", threading.Lock(), raising=True)
    monkeypatch.setattr(ft, "_file_ops_cache", {}, raising=True)
    monkeypatch.setattr(ft, "_file_ops_lock", threading.Lock(), raising=True)
    return tt, ft


def _printed(mock_cprint) -> str:
    return " ".join(str(c) for c in mock_cprint.call_args_list)


class TestSetWorkspaceArgParsing:
    def test_no_arg_shows_current_and_does_not_mutate(self, bare_cli):
        before = os.environ["TERMINAL_CWD"]
        with patch.object(cli_mod, "_cprint") as cprint:
            bare_cli._handle_set_workspace_command("/set-workspace")
        out = _printed(cprint)
        assert "Current workspace" in out
        assert before in out
        assert "Usage" in out
        assert os.environ["TERMINAL_CWD"] == before

    def test_blank_arg_treated_as_no_arg(self, bare_cli):
        before = os.environ["TERMINAL_CWD"]
        with patch.object(cli_mod, "_cprint") as cprint:
            bare_cli._handle_set_workspace_command("/set-workspace    ")
        out = _printed(cprint)
        assert "Current workspace" in out
        assert os.environ["TERMINAL_CWD"] == before

    def test_strips_double_quotes(self, bare_cli, two_dirs):
        a, _ = two_dirs
        with patch.object(cli_mod, "_cprint"):
            bare_cli._handle_set_workspace_command(f'/set-workspace "{a}"')
        assert os.environ["TERMINAL_CWD"] == os.path.realpath(str(a))

    def test_strips_single_quotes(self, bare_cli, two_dirs):
        a, _ = two_dirs
        with patch.object(cli_mod, "_cprint"):
            bare_cli._handle_set_workspace_command(f"/set-workspace '{a}'")
        assert os.environ["TERMINAL_CWD"] == os.path.realpath(str(a))


class TestSetWorkspacePathResolution:
    def test_tilde_expansion(self, bare_cli):
        with patch.object(cli_mod, "_cprint"):
            bare_cli._handle_set_workspace_command("/set-workspace ~")
        assert os.environ["TERMINAL_CWD"] == os.path.realpath(os.path.expanduser("~"))

    def test_envvar_expansion(self, bare_cli, two_dirs, monkeypatch):
        a, _ = two_dirs
        monkeypatch.setenv("MY_TEST_DIR", str(a))
        with patch.object(cli_mod, "_cprint"):
            bare_cli._handle_set_workspace_command("/set-workspace $MY_TEST_DIR")
        assert os.environ["TERMINAL_CWD"] == os.path.realpath(str(a))

    def test_relative_path_resolves_against_current_terminal_cwd(self, bare_cli, two_dirs, monkeypatch):
        """The anchor for relative paths must be TERMINAL_CWD, not os.getcwd().

        This is the load-bearing invariant -- if it ever flips to os.getcwd(),
        switching workspaces and then doing /set-workspace ./subdir will land
        you somewhere unrelated.
        """
        a, _ = two_dirs
        monkeypatch.setenv("TERMINAL_CWD", str(a.parent))
        # Move the process cwd elsewhere so we'd notice if it leaked through.
        monkeypatch.chdir(os.path.expanduser("~"))
        with patch.object(cli_mod, "_cprint"):
            bare_cli._handle_set_workspace_command("/set-workspace a")
        assert os.environ["TERMINAL_CWD"] == os.path.realpath(str(a))


class TestSetWorkspaceValidation:
    def test_nonexistent_path_rejected(self, bare_cli):
        before = os.environ["TERMINAL_CWD"]
        with patch.object(cli_mod, "_cprint") as cprint:
            bare_cli._handle_set_workspace_command("/set-workspace /no/such/dir/zzz/qqq")
        assert "Not a directory" in _printed(cprint)
        assert os.environ["TERMINAL_CWD"] == before

    def test_file_rejected(self, bare_cli, tmp_path):
        f = tmp_path / "a-file.txt"
        f.write_text("x")
        before = os.environ["TERMINAL_CWD"]
        with patch.object(cli_mod, "_cprint") as cprint:
            bare_cli._handle_set_workspace_command(f"/set-workspace {f}")
        assert "Not a directory" in _printed(cprint)
        assert os.environ["TERMINAL_CWD"] == before

    def test_unreadable_dir_rejected(self, bare_cli, tmp_path):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            pytest.skip("root bypasses POSIX mode bits")
        d = tmp_path / "noperm"
        d.mkdir()
        before = os.environ["TERMINAL_CWD"]
        try:
            d.chmod(0o000)
            with patch.object(cli_mod, "_cprint") as cprint:
                bare_cli._handle_set_workspace_command(f"/set-workspace {d}")
            out = _printed(cprint)
            assert ("Not readable" in out) or ("Not a directory" in out)
            assert os.environ["TERMINAL_CWD"] == before
        finally:
            d.chmod(0o700)

    def test_same_dir_is_noop(self, bare_cli, two_dirs):
        a, _ = two_dirs
        with patch.object(cli_mod, "_cprint"):
            bare_cli._handle_set_workspace_command(f"/set-workspace {a}")
        with patch.object(cli_mod, "_cprint") as cprint2:
            bare_cli._handle_set_workspace_command(f"/set-workspace {a}")
        assert "unchanged" in _printed(cprint2).lower()


class TestSetWorkspaceCacheSync:
    def test_active_terminal_envs_synced(self, bare_cli, two_dirs, patched_caches):
        tt, _ = patched_caches
        a, _ = two_dirs

        env = MagicMock()
        env.cwd = "/old"
        tt._active_environments["task-1"] = env

        with patch.object(cli_mod, "_cprint"):
            bare_cli._handle_set_workspace_command(f"/set-workspace {a}")
        assert env.cwd == os.path.realpath(str(a))

    def test_file_ops_cache_synced(self, bare_cli, two_dirs, patched_caches):
        _, ft = patched_caches
        a, _ = two_dirs

        fops = MagicMock()
        fops.cwd = "/old"
        ft._file_ops_cache["task-1"] = fops

        with patch.object(cli_mod, "_cprint"):
            bare_cli._handle_set_workspace_command(f"/set-workspace {a}")
        assert fops.cwd == os.path.realpath(str(a))

    def test_env_sync_failure_does_not_abort_other_updates(self, bare_cli, two_dirs, patched_caches):
        """A misbehaving remote backend that rejects cwd assignment must not
        block the env-var update or the file_ops update."""
        tt, ft = patched_caches
        a, _ = two_dirs

        bad_env = MagicMock()
        type(bad_env).cwd = property(
            lambda self: "/old",
            lambda self, value: (_ for _ in ()).throw(RuntimeError("nope")),
        )
        tt._active_environments["bad"] = bad_env

        good_fops = MagicMock()
        good_fops.cwd = "/old"
        ft._file_ops_cache["fops"] = good_fops

        with patch.object(cli_mod, "_cprint"):
            bare_cli._handle_set_workspace_command(f"/set-workspace {a}")

        assert os.environ["TERMINAL_CWD"] == os.path.realpath(str(a))
        assert good_fops.cwd == os.path.realpath(str(a))


class TestSetWorkspaceRegistryWiring:
    def test_command_registered_with_aliases(self):
        from hermes_cli.commands import resolve_command

        for name in ("set-workspace", "setworkspace", "workspace", "cd"):
            cd = resolve_command(name)
            assert cd is not None, f"'/{name}' did not resolve"
            assert cd.name == "set-workspace"
            assert cd.cli_only is True
