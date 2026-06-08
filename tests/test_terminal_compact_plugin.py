import importlib.util
import sys
from pathlib import Path

from hermes_cli.plugins import PluginManager


def _load_rewrite_module():
    path = Path(__file__).resolve().parents[1] / ".hermes" / "plugins" / "terminal_compact" / "rewrite.py"
    spec = importlib.util.spec_from_file_location("terminal_compact_rewrite", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_rewrite_command_skips_dangerous_prefixes():
    rewrite = _load_rewrite_module()
    assert rewrite.rewrite_command("rm -rf tmp") is None
    assert rewrite.rewrite_command("git push origin main") is None


def test_rewrite_command_skips_shell_chains():
    rewrite = _load_rewrite_module()
    assert rewrite.rewrite_command("git status && git diff") is None
    assert rewrite.rewrite_command("rg foo | head") is None


def test_rewrite_command_rewrites_git_status():
    rewrite = _load_rewrite_module()
    result = rewrite.rewrite_command("git status")
    assert result is not None
    assert result.command == "git status --short --branch"
    assert result.reason == "compact git status"


def test_project_plugin_loads_and_rewrites_terminal_calls(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo_root)
    monkeypatch.setenv("HERMES_ENABLE_PROJECT_PLUGINS", "true")
    monkeypatch.setattr("hermes_cli.plugins._get_enabled_plugins", lambda: {"terminal_compact"})

    mgr = PluginManager()
    mgr.discover_and_load()

    assert "terminal_compact" in mgr._plugins
    plugin = mgr._plugins["terminal_compact"]
    assert plugin.enabled is True

    result = mgr.invoke_hook(
        "pre_tool_call",
        tool_name="terminal",
        args={"command": "git status"},
        task_id="t1",
        session_id="s1",
        tool_call_id="c1",
    )
    assert result == [{
        "action": "rewrite_args",
        "args": {"command": "git status --short --branch"},
        "reason": "compact git status",
    }]
