import tempfile
from pathlib import Path

from agent import tool_dispatch_helpers
from hermes_cli import path_compat
from tools import checkpoint_manager, code_execution_tool, delegate_tool, file_tools


def test_msys_drive_path_converts_to_native_windows(monkeypatch):
    monkeypatch.setattr(path_compat, "IS_WINDOWS", True)

    assert path_compat.msys_to_windows_path("/c/Users/Josh/project") == (
        r"C:\Users\Josh\project"
    )
    assert path_compat.msys_to_windows_path("/d") == "D:\\"


def test_msys_tmp_path_converts_to_native_temp(monkeypatch):
    monkeypatch.setattr(path_compat, "IS_WINDOWS", True)

    converted = path_compat.msys_to_windows_path("/tmp/hermes/socket")

    assert converted == str(Path(tempfile.gettempdir()) / "hermes" / "socket")


def test_non_windows_paths_are_unchanged(monkeypatch):
    monkeypatch.setattr(path_compat, "IS_WINDOWS", False)

    assert path_compat.msys_to_windows_path("/c/Users/Josh/project") == "/c/Users/Josh/project"


def test_file_tools_resolve_path_normalizes_terminal_cwd(monkeypatch, tmp_path):
    base = tmp_path / "repo"
    base.mkdir()
    monkeypatch.setattr(file_tools, "_get_live_tracking_cwd", lambda task_id: None)
    monkeypatch.setattr(file_tools, "native_path", lambda value: str(base) if value == "/c/repo" else value)
    monkeypatch.setenv("TERMINAL_CWD", "/c/repo")

    assert file_tools._resolve_path_for_task("notes.txt") == base / "notes.txt"


def test_code_execution_project_cwd_normalizes_terminal_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("TERMINAL_CWD", "/c/repo")
    monkeypatch.setattr(code_execution_tool, "native_path", lambda value: str(tmp_path) if value == "/c/repo" else value)

    assert code_execution_tool._resolve_child_cwd("project", "staging") == str(tmp_path)


def test_checkpoint_normalize_path_uses_native_form(monkeypatch, tmp_path):
    monkeypatch.setattr(checkpoint_manager, "native_path", lambda value: str(tmp_path) if value == "/c/repo" else value)

    assert checkpoint_manager._normalize_path("/c/repo") == tmp_path.resolve()


def test_delegate_workspace_hint_normalizes_terminal_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("TERMINAL_CWD", "/c/repo")
    monkeypatch.setattr(delegate_tool, "native_path", lambda value: str(tmp_path) if value == "/c/repo" else value)

    assert delegate_tool._resolve_workspace_hint(parent_agent=object()) == str(tmp_path)


def test_parallel_scope_path_normalizes_path_argument(monkeypatch, tmp_path):
    target = tmp_path / "notes.txt"
    monkeypatch.setattr(
        tool_dispatch_helpers,
        "native_path",
        lambda value: str(target) if value == "/c/repo/notes.txt" else value,
    )

    assert tool_dispatch_helpers._extract_parallel_scope_path(
        "write_file", {"path": "/c/repo/notes.txt"}
    ) == target
