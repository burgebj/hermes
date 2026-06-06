import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

from hermes_cli.uninstall import remove_wrapper_script, uninstall_gateway_service, _uninstall_profile


@pytest.fixture()
def home_env(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    return hermes_home


def test_remove_wrapper_script_removes_managed_wrapper_file(home_env):
    wrapper_dir = Path.home() / ".local" / "bin"
    wrapper_dir.mkdir(parents=True)
    managed_wrapper = wrapper_dir / "hermes"
    managed_wrapper.write_text("#!/bin/sh\npython -m hermes_cli.main \"$@\"\n")

    removed = remove_wrapper_script()

    assert removed == [managed_wrapper]
    assert not managed_wrapper.exists()


def test_uninstall_gateway_service_removes_macos_launchd_plist(home_env, tmp_path):
    plist = tmp_path / "ai.hermes.gateway.plist"
    plist.write_text("plist")

    with patch("platform.system", return_value="Darwin"), patch(
        "hermes_cli.gateway.find_gateway_pids", return_value=[]
    ), patch("hermes_cli.gateway.get_launchd_plist_path", return_value=plist), patch(
        "subprocess.run", return_value=MagicMock()
    ) as mock_run:
        removed = uninstall_gateway_service()

    assert removed is True
    assert not plist.exists()
    mock_run.assert_called_once_with(["launchctl", "unload", str(plist)], capture_output=True, check=False)


def test_uninstall_profile_stops_gateway_removes_alias_and_home(tmp_path):
    profile_home = tmp_path / "profiles" / "coder"
    profile_home.mkdir(parents=True)
    alias = tmp_path / "bin" / "coder"
    alias.parent.mkdir()
    alias.write_text("#!/bin/sh\n")
    profile = SimpleNamespace(name="coder", path=profile_home, alias_path=alias)

    with patch("subprocess.run", return_value=MagicMock()) as mock_run:
        _uninstall_profile(profile)

    assert not alias.exists()
    assert not profile_home.exists()
    assert mock_run.call_args_list == [
        call(
            [sys.executable, "-m", "hermes_cli.main", "--profile", "coder", "gateway", "stop"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        ),
        call(
            [sys.executable, "-m", "hermes_cli.main", "--profile", "coder", "gateway", "uninstall"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        ),
    ]
