"""Tests for plugin dependency reinstallation after ``hermes update``.

``hermes update`` refreshes core dependencies with ``uv pip install -e .[all]``.
That sync can remove dependencies that are declared only by active plugins, so
``_reinstall_plugin_dependencies`` scans active plugin manifests and reinstalls
missing ``pip_dependencies``.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch


# A distribution name that should not exist in the test venv.
_FAKE_DEP = "nonexistent-test-pkg-xyz"


def _import_function():
    from hermes_cli.main import _reinstall_plugin_dependencies

    return _reinstall_plugin_dependencies


def _patch_env(tmp_path, config=None):
    """Patch plugin roots and config for update dependency tests."""
    bundled = tmp_path / "bundled"
    bundled.mkdir(exist_ok=True)
    hermes_home = tmp_path / "home"
    (hermes_home / "plugins").mkdir(parents=True, exist_ok=True)
    config = config if config is not None else {}
    return (
        patch("hermes_cli.plugins.get_bundled_plugins_dir", return_value=bundled),
        patch("hermes_cli.main.get_hermes_home", return_value=hermes_home),
        patch("hermes_constants.get_hermes_home", return_value=hermes_home),
        patch("hermes_cli.config.load_config", return_value=config),
    )


def _write_plugin(plugin_dir, *, name=None, deps=None, kind=None, init=False):
    plugin_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"name: {name or plugin_dir.name}", "version: '1.0'"]
    if kind:
        lines.append(f"kind: {kind}")
    if deps is not None:
        lines.append("pip_dependencies:")
        lines.extend(f"  - {dep}" for dep in deps)
    (plugin_dir / "plugin.yaml").write_text("\n".join(lines) + "\n")
    if init:
        (plugin_dir / "__init__.py").write_text("# MemoryProvider marker\n")


class TestReinstallPluginDependencies:
    """Core behaviour of _reinstall_plugin_dependencies."""

    def test_skips_when_no_active_plugin_yaml(self, tmp_path):
        plugin_dir = tmp_path / "home" / "plugins" / "my-plugin"
        plugin_dir.mkdir(parents=True)

        func = _import_function()
        patches = _patch_env(tmp_path, {"plugins": {"enabled": ["my-plugin"]}})
        with patches[0], patches[1], patches[2], patches[3]:
            func()  # no crash

    def test_skips_active_plugin_with_no_pip_dependencies(self, tmp_path):
        plugin_dir = tmp_path / "home" / "plugins" / "my-plugin"
        _write_plugin(plugin_dir, name="my-plugin", deps=None)

        func = _import_function()
        patches = _patch_env(tmp_path, {"plugins": {"enabled": ["my-plugin"]}})
        with patches[0], patches[1], patches[2], patches[3], patch("subprocess.run") as mock_run:
            func()
            mock_run.assert_not_called()

    def test_skips_active_plugin_with_empty_pip_dependencies(self, tmp_path):
        plugin_dir = tmp_path / "home" / "plugins" / "my-plugin"
        _write_plugin(plugin_dir, name="my-plugin", deps=[])

        func = _import_function()
        patches = _patch_env(tmp_path, {"plugins": {"enabled": ["my-plugin"]}})
        with patches[0], patches[1], patches[2], patches[3], patch("subprocess.run") as mock_run:
            func()
            mock_run.assert_not_called()

    def test_installs_missing_dependency_for_enabled_user_plugin(self, tmp_path):
        plugin_dir = tmp_path / "home" / "plugins" / "my-plugin"
        _write_plugin(plugin_dir, name="my-plugin", deps=[_FAKE_DEP])

        func = _import_function()
        patches = _patch_env(tmp_path, {"plugins": {"enabled": ["my-plugin"]}})
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("shutil.which", return_value="/usr/bin/uv"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    func()
                    assert mock_run.called
                    call_args = mock_run.call_args[0][0]
                    assert _FAKE_DEP in call_args

    def test_skips_already_installed_dependency(self, tmp_path):
        plugin_dir = tmp_path / "home" / "plugins" / "my-plugin"
        _write_plugin(plugin_dir, name="my-plugin", deps=["pytest"])

        func = _import_function()
        patches = _patch_env(tmp_path, {"plugins": {"enabled": ["my-plugin"]}})
        with patches[0], patches[1], patches[2], patches[3], patch("subprocess.run") as mock_run:
            func()
            mock_run.assert_not_called()

    def test_warns_when_uv_not_found_for_missing_active_dep(self, tmp_path, capsys):
        plugin_dir = tmp_path / "home" / "plugins" / "my-plugin"
        _write_plugin(plugin_dir, name="my-plugin", deps=[_FAKE_DEP])

        func = _import_function()
        patches = _patch_env(tmp_path, {"plugins": {"enabled": ["my-plugin"]}})
        with patches[0], patches[1], patches[2], patches[3], patch("shutil.which", return_value=None):
            func()
        output = capsys.readouterr().out
        assert "uv not found" in output

    def test_scans_selected_memory_provider_with_versioned_requirement(self, tmp_path):
        plugin_dir = tmp_path / "home" / "plugins" / "custom-memory"
        versioned_dep = f"{_FAKE_DEP}>=0.4.22"
        _write_plugin(
            plugin_dir,
            name="custom-memory",
            deps=[versioned_dep],
            init=True,
        )

        func = _import_function()
        patches = _patch_env(tmp_path, {"memory": {"provider": "custom-memory"}})
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("shutil.which", return_value="/usr/bin/uv"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    func()
                    assert mock_run.called
                    call_args = mock_run.call_args[0][0]
                    assert versioned_dep in call_args

    def test_batch_installs_all_missing_deps(self, tmp_path):
        enabled = []
        for i in range(3):
            name = f"plugin-{i}"
            enabled.append(name)
            pdir = tmp_path / "home" / "plugins" / name
            _write_plugin(pdir, name=name, deps=[f"{_FAKE_DEP}-{i}"])

        func = _import_function()
        patches = _patch_env(tmp_path, {"plugins": {"enabled": enabled}})
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("shutil.which", return_value="/usr/bin/uv"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    func()
                    assert mock_run.call_count == 1
                    call_args = mock_run.call_args[0][0]
                    for i in range(3):
                        assert f"{_FAKE_DEP}-{i}" in call_args

    def test_handles_active_category_layout_plugins(self, tmp_path):
        plugin_dir = tmp_path / "bundled" / "image_gen" / "openai"
        _write_plugin(plugin_dir, name="openai-image", deps=[_FAKE_DEP], kind="backend")

        func = _import_function()
        patches = _patch_env(tmp_path, {})
        with patches[0], patches[1], patches[2], patches[3]:
            with patch("shutil.which", return_value="/usr/bin/uv"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    func()
                    assert mock_run.called
                    call_args = mock_run.call_args[0][0]
                    assert _FAKE_DEP in call_args

    def test_invalid_yaml_skipped_gracefully(self, tmp_path):
        plugin_dir = tmp_path / "home" / "plugins" / "broken-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "plugin.yaml").write_text("{{invalid yaml::")

        func = _import_function()
        patches = _patch_env(tmp_path, {"plugins": {"enabled": ["broken-plugin"]}})
        with patches[0], patches[1], patches[2], patches[3]:
            func()  # should not raise
