"""Tests for hermes_cli.uninstall desktop-app removal functions.

Covers:
  - ``_kill_desktop_process``: per-platform process killing
  - ``remove_desktop_app``: full desktop-only uninstall
  - ``_remove_desktop_external_artifacts``: external-only cleanup used by
    the standard uninstall flow
  - ``_electron_user_data_dir``: platform-specific userData resolution
  - ``run_uninstall``: managed-install no-op
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import hermes_cli.uninstall as uninstall


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_install(tmp_path):
    """Create a fake project root with apps/desktop subtree and hermes_home."""
    project_root = tmp_path / "hermes-agent"
    project_root.mkdir()
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()

    # apps/desktop with release/, dist/, node_modules/
    desktop = project_root / "apps" / "desktop"
    desktop.mkdir(parents=True)

    (desktop / "release" / "mac-arm64" / "Hermes.app" / "Contents" / "MacOS").mkdir(parents=True)
    (desktop / "release" / "mac-arm64" / "Hermes.app" / "Contents" / "MacOS" / "Hermes").write_text("#!bin")

    (desktop / "dist" / "index.html").parent.mkdir(parents=True, exist_ok=True)
    (desktop / "dist" / "index.html").write_text("<html></html>")

    (desktop / "node_modules" / "electron" / "package.json").parent.mkdir(parents=True, exist_ok=True)
    (desktop / "node_modules" / "electron" / "package.json").write_text('{"name":"electron"}')

    # desktop-build-stamp.json in hermes_home
    (hermes_home / "desktop-build-stamp.json").write_text('{"contentHash":"abc123"}')

    return project_root, hermes_home


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect Path.home() so Electron userData dir lands in tmp."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return home


# ---------------------------------------------------------------------------
# _electron_user_data_dir
# ---------------------------------------------------------------------------

class TestElectronUserDataDir:
    def test_macos(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "darwin")
        result = uninstall._electron_user_data_dir()
        assert result == fake_home / "Library" / "Application Support" / "Hermes"

    def test_linux(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        result = uninstall._electron_user_data_dir()
        assert result == fake_home / ".config" / "Hermes"

    def test_linux_xdg(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        xdg = fake_home / "xdg-config"
        xdg.mkdir()
        monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
        result = uninstall._electron_user_data_dir()
        assert result == xdg / "Hermes"

    def test_windows_appdata(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("APPDATA", str(fake_home / "AppData" / "Roaming"))
        result = uninstall._electron_user_data_dir()
        assert result == Path(os.environ["APPDATA"]) / "Hermes"

    def test_windows_no_appdata(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.delenv("APPDATA", raising=False)
        result = uninstall._electron_user_data_dir()
        assert result == fake_home / "AppData" / "Roaming" / "Hermes"


# ---------------------------------------------------------------------------
# remove_desktop_app
# ---------------------------------------------------------------------------

class TestRemoveDesktopApp:
    def test_removes_built_artifacts(self, fake_install, fake_home, monkeypatch):
        """All three apps/desktop subdirs + stamp are removed."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")

        removed = uninstall.remove_desktop_app(project_root, hermes_home)

        desktop = project_root / "apps" / "desktop"
        assert not (desktop / "release").exists()
        assert not (desktop / "dist").exists()
        assert not (desktop / "node_modules").exists()
        assert not (hermes_home / "desktop-build-stamp.json").exists()

        # Should report what was removed
        assert "apps/desktop/release/" in removed
        assert "apps/desktop/dist/" in removed
        assert "apps/desktop/node_modules/" in removed
        assert "desktop-build-stamp.json" in removed

    def test_no_artifacts_is_noop(self, tmp_path, fake_home, monkeypatch):
        """If nothing exists, function returns empty list without error."""
        monkeypatch.setattr(sys, "platform", "linux")
        project_root = tmp_path / "empty-agent"
        project_root.mkdir()
        hermes_home = tmp_path / ".hermes-empty"
        hermes_home.mkdir()

        removed = uninstall.remove_desktop_app(project_root, hermes_home)
        assert removed == []

    def test_partial_artifacts(self, fake_install, fake_home, monkeypatch):
        """Only some artifacts exist — removes what's there, skips the rest."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")

        # Delete release and dist before running — only node_modules and stamp remain
        desktop = project_root / "apps" / "desktop"
        import shutil
        shutil.rmtree(desktop / "release")
        shutil.rmtree(desktop / "dist")

        removed = uninstall.remove_desktop_app(project_root, hermes_home)

        assert "apps/desktop/release/" not in removed
        assert "apps/desktop/dist/" not in removed
        assert "apps/desktop/node_modules/" in removed
        assert "desktop-build-stamp.json" in removed

    def test_removes_electron_user_data(self, fake_install, fake_home, monkeypatch):
        """Electron userData directory is removed when present."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")

        # Create fake Electron userData
        user_data = fake_home / ".config" / "Hermes"
        user_data.mkdir(parents=True)
        (user_data / "connection.json").write_text("{}")
        (user_data / "composer-images").mkdir()
        (user_data / "dock-pinned.json").write_text("{}")

        removed = uninstall.remove_desktop_app(project_root, hermes_home)

        assert not user_data.exists()
        assert any("Electron userData" in r for r in removed)

    def test_macos_removes_app_bundle(self, fake_install, fake_home, monkeypatch):
        """On macOS, /Applications/Hermes.app is removed."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "darwin")

        # We can't actually write to /Applications. Patch is_dir to return True
        # ONLY for the Hermes.app bundle — patching it globally would make every
        # other Path.is_dir() check in this code path (and any future one) lie,
        # which is exactly the kind of silent false positive the review guide
        # warns about. Scope the truthiness to the one instance we care about.
        app_bundle = Path("/Applications/Hermes.app")
        real_is_dir = Path.is_dir

        def fake_is_dir(self):
            if self == app_bundle:
                return True
            return real_is_dir(self)

        with patch.object(Path, "is_dir", fake_is_dir), \
             patch("shutil.rmtree") as mock_rmtree:
            removed = uninstall.remove_desktop_app(project_root, hermes_home)

        # rmtree should have been called for /Applications/Hermes.app
        rmtree_args = [call[0][0] for call in mock_rmtree.call_args_list]
        assert app_bundle in rmtree_args

    def test_preserves_desktop_source(self, fake_install, fake_home, monkeypatch):
        """Source files in apps/desktop/src/ are NOT removed."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")

        # Add source files that should survive
        desktop = project_root / "apps" / "desktop"
        (desktop / "src").mkdir(exist_ok=True)
        (desktop / "src" / "App.tsx").write_text("// source")
        (desktop / "package.json").write_text('{"name":"hermes-desktop"}')

        uninstall.remove_desktop_app(project_root, hermes_home)

        # Source and package.json should still exist
        assert (desktop / "src" / "App.tsx").exists()
        assert (desktop / "package.json").exists()

    def test_preserves_root_node_modules(self, fake_install, fake_home, monkeypatch):
        """Root node_modules/ is NOT removed (TUI depends on it)."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")

        root_nm = project_root / "node_modules"
        root_nm.mkdir()
        (root_nm / "ink" / "package.json").parent.mkdir(parents=True, exist_ok=True)
        (root_nm / "ink" / "package.json").write_text('{"name":"ink"}')

        uninstall.remove_desktop_app(project_root, hermes_home)

        assert root_nm.exists()
        assert (root_nm / "ink" / "package.json").exists()


# ---------------------------------------------------------------------------
# _remove_desktop_external_artifacts
# ---------------------------------------------------------------------------

class TestRemoveDesktopExternalArtifacts:
    def test_removes_electron_user_data(self, fake_install, fake_home, monkeypatch):
        """Electron userData is removed by the external-artifacts helper."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")

        user_data = fake_home / ".config" / "Hermes"
        user_data.mkdir(parents=True)
        (user_data / "connection.json").write_text("{}")

        uninstall._remove_desktop_external_artifacts(project_root, hermes_home)

        assert not user_data.exists()

    def test_no_user_data_is_noop(self, fake_install, fake_home, monkeypatch):
        """If no Electron userData exists, no error."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")

        # Should not raise
        uninstall._remove_desktop_external_artifacts(project_root, hermes_home)

    def test_does_not_touch_install_dir(self, fake_install, fake_home, monkeypatch):
        """Internal artifacts (apps/desktop/*) are NOT removed by the external helper."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")

        uninstall._remove_desktop_external_artifacts(project_root, hermes_home)

        desktop = project_root / "apps" / "desktop"
        # These should all still exist — external helper only touches
        # /Applications, Dock, and userData
        assert (desktop / "release").exists()
        assert (desktop / "dist").exists()
        assert (desktop / "node_modules").exists()
        assert (hermes_home / "desktop-build-stamp.json").exists()


# ---------------------------------------------------------------------------
# _unpin_from_dock (macOS-only, best-effort)
# ---------------------------------------------------------------------------

class TestUnpinFromDock:
    def test_noop_on_linux(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        assert uninstall._unpin_from_dock() is False

    def test_noop_on_windows(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        assert uninstall._unpin_from_dock() is False

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only")
    def test_macos_no_hermes_in_dock(self, monkeypatch):
        """If Hermes.app is not in the Dock output, return False."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "some other apps"
            assert uninstall._unpin_from_dock() is False


# ---------------------------------------------------------------------------
# _kill_desktop_process
# ---------------------------------------------------------------------------

class TestKillDesktopProcess:
    def test_macos_uses_killall(self, monkeypatch):
        """On macOS, killall Hermes is called (targets Electron binary, not CLI)."""
        monkeypatch.setattr(sys, "platform", "darwin")
        with patch("subprocess.run") as mock_run:
            uninstall._kill_desktop_process()
            mock_run.assert_called_once_with(
                ["killall", "Hermes"], capture_output=True, check=False,
            )

    def test_windows_uses_taskkill(self, monkeypatch):
        """On Windows, taskkill /F /IM Hermes.exe is called."""
        monkeypatch.setattr(sys, "platform", "win32")
        with patch("subprocess.run") as mock_run:
            uninstall._kill_desktop_process()
            mock_run.assert_called_once_with(
                ["taskkill", "/F", "/IM", "Hermes.exe"],
                capture_output=True, check=False,
            )

    def test_linux_uses_pkill(self, monkeypatch):
        """On Linux, pkill targets the desktop app path."""
        monkeypatch.setattr(sys, "platform", "linux")
        with patch("subprocess.run") as mock_run:
            uninstall._kill_desktop_process()
            mock_run.assert_called_once_with(
                ["pkill", "-f", "apps/desktop/release/linux-unpacked/Hermes"],
                capture_output=True, check=False,
            )

    def test_exception_is_swallowed(self, monkeypatch):
        """If the kill command raises, the function does not propagate."""
        monkeypatch.setattr(sys, "platform", "darwin")
        with patch("subprocess.run", side_effect=OSError("nope")):
            uninstall._kill_desktop_process()  # should not raise

    def test_is_called_by_remove_desktop_app(self, fake_install, fake_home, monkeypatch):
        """remove_desktop_app delegates to _kill_desktop_process."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")
        with patch.object(uninstall, "_kill_desktop_process") as mock_kill:
            uninstall.remove_desktop_app(project_root, hermes_home)
            mock_kill.assert_called_once()

    def test_is_called_by_external_artifacts(self, fake_install, fake_home, monkeypatch):
        """_remove_desktop_external_artifacts delegates to _kill_desktop_process."""
        project_root, hermes_home = fake_install
        monkeypatch.setattr(sys, "platform", "linux")
        with patch.object(uninstall, "_kill_desktop_process") as mock_kill:
            uninstall._remove_desktop_external_artifacts(project_root, hermes_home)
            mock_kill.assert_called_once()


# ---------------------------------------------------------------------------
# run_uninstall — managed-install no-op
# ---------------------------------------------------------------------------

class TestRunUninstallManagedNoop:
    def test_managed_install_bails_early(self, monkeypatch, capsys):
        """When is_managed() is True, run_uninstall prints an error and returns."""
        monkeypatch.setattr("hermes_cli.config.is_managed", lambda: True)
        monkeypatch.setattr("hermes_cli.config.get_managed_update_command",
                            lambda: "nix-env -e hermes")

        # Provide a minimal args namespace
        args = type("Args", (), {"desktop": False, "yes": False})()
        uninstall.run_uninstall(args)

        output = capsys.readouterr().out
        assert "not available for managed installs" in output
        assert "nix-env -e hermes" in output

    def test_unmanaged_install_proceeds(self, monkeypatch, capsys):
        """When is_managed() is False, run_uninstall continues past the check."""
        monkeypatch.setattr("hermes_cli.config.is_managed", lambda: False)
        # Patch both path helpers so the uninstaller gets past them
        # without hitting the real FS or an interactive prompt.
        monkeypatch.setattr(uninstall, "get_project_root",
                            lambda: Path("/tmp/nope"))
        monkeypatch.setattr(uninstall, "get_hermes_home",
                            lambda: Path("/tmp/nope-hh"))

        args = type("Args", (), {"desktop": False, "yes": False})()

        # The interactive menu will try to read stdin; feed it "4" (cancel).
        monkeypatch.setattr("builtins.input", lambda _: "4")
        uninstall.run_uninstall(args)

        output = capsys.readouterr().out
        # Should NOT have the managed-install error — it got past that gate.
        assert "not available for managed installs" not in output


# ---------------------------------------------------------------------------
# run_uninstall — desktop-only dispatch (the actual entry points users hit)
# ---------------------------------------------------------------------------

class TestRunUninstallDesktopDispatch:
    """Cover the two routes into the desktop-only flow: the ``--desktop`` flag
    fast-path and interactive menu choice "3". These guard against the kind of
    off-by-one that the cancel-option renumber (3 -> 4) could introduce.
    """

    @pytest.fixture
    def unmanaged(self, monkeypatch):
        """Get past the managed-install gate with stub path helpers."""
        monkeypatch.setattr("hermes_cli.config.is_managed", lambda: False)
        monkeypatch.setattr(uninstall, "get_project_root",
                            lambda: Path("/tmp/nope"))
        monkeypatch.setattr(uninstall, "get_hermes_home",
                            lambda: Path("/tmp/nope-hh"))

    def test_desktop_flag_routes_to_desktop_uninstall(self, unmanaged, monkeypatch):
        """``hermes uninstall --desktop`` calls remove_desktop_app and never
        touches the standard (code/data) removal flow."""
        spy = []
        monkeypatch.setattr(uninstall, "remove_desktop_app",
                            lambda pr, hh: spy.append((pr, hh)) or [])
        # If the standard flow were entered it would prompt; make that explode
        # so a mis-route is a hard failure rather than a hang.
        monkeypatch.setattr("builtins.input",
                            lambda _: pytest.fail("standard flow should not prompt"))

        args = type("Args", (), {"desktop": True, "yes": True})()
        uninstall.run_uninstall(args)

        assert spy == [(Path("/tmp/nope"), Path("/tmp/nope-hh"))]

    def test_menu_choice_3_routes_to_desktop_uninstall(self, unmanaged, monkeypatch):
        """Interactive menu choice "3" routes to the desktop-only flow."""
        spy = []
        monkeypatch.setattr(uninstall, "remove_desktop_app",
                            lambda pr, hh: spy.append((pr, hh)) or [])
        # First prompt = menu choice "3"; second = the desktop confirm "yes".
        answers = iter(["3", "yes"])
        monkeypatch.setattr("builtins.input", lambda _: next(answers))

        args = type("Args", (), {"desktop": False, "yes": False})()
        uninstall.run_uninstall(args)

        assert spy == [(Path("/tmp/nope"), Path("/tmp/nope-hh"))]


class TestRunDesktopUninstall:
    """The desktop-only flow's own confirm/cancel handling."""

    def test_skips_confirm_with_yes(self, monkeypatch):
        spy = []
        monkeypatch.setattr(uninstall, "remove_desktop_app",
                            lambda pr, hh: spy.append((pr, hh)) or [])
        monkeypatch.setattr("builtins.input",
                            lambda _: pytest.fail("should not prompt when --yes"))

        args = type("Args", (), {"yes": True})()
        uninstall._run_desktop_uninstall(Path("/p"), Path("/h"), args)

        assert spy == [(Path("/p"), Path("/h"))]

    def test_cancels_on_non_yes(self, monkeypatch, capsys):
        spy = []
        monkeypatch.setattr(uninstall, "remove_desktop_app",
                            lambda pr, hh: spy.append((pr, hh)) or [])
        monkeypatch.setattr("builtins.input", lambda _: "no")

        args = type("Args", (), {"yes": False})()
        uninstall._run_desktop_uninstall(Path("/p"), Path("/h"), args)

        # remove_desktop_app must NOT run when the user declines.
        assert spy == []
        assert "cancel" in capsys.readouterr().out.lower()

    def test_cancels_on_eof(self, monkeypatch):
        """Ctrl-D / EOF at the confirm prompt cancels cleanly."""
        spy = []
        monkeypatch.setattr(uninstall, "remove_desktop_app",
                            lambda pr, hh: spy.append((pr, hh)) or [])

        def raise_eof(_):
            raise EOFError

        monkeypatch.setattr("builtins.input", raise_eof)

        args = type("Args", (), {"yes": False})()
        uninstall._run_desktop_uninstall(Path("/p"), Path("/h"), args)

        assert spy == []
