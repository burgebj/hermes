import json
import os
from pathlib import Path


def test_cursor_mcp_configs_use_portable_hermes_launcher():
    repo_root = Path(__file__).resolve().parents[1]

    for rel_path in (".cursor/mcp.json", "cursor-mcp-config.json"):
        config = json.loads((repo_root / rel_path).read_text(encoding="utf-8"))
        server = config["mcpServers"]["hermes"]

        assert server.get("command") == "${workspaceFolder}/hermes-mcp-serve"
        assert server.get("args") == []
        assert "/home/" not in server["command"]


def test_cursor_mcp_doctor_reports_portable_setup(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    cursor_dir = repo / ".cursor"
    cursor_dir.mkdir(parents=True)
    home.mkdir()

    config = {
        "mcpServers": {
            "hermes": {
                "command": "${workspaceFolder}/hermes-mcp-serve",
                "args": [],
            }
        }
    }
    (cursor_dir / "mcp.json").write_text(json.dumps(config), encoding="utf-8")
    (cursor_dir / "mcp.json.example").write_text(json.dumps(config), encoding="utf-8")
    launcher = repo / "hermes-mcp-serve"
    launcher.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    launcher.chmod(launcher.stat().st_mode | 0o111)
    agents_dir = repo / "agents"
    agents_dir.mkdir()
    (agents_dir / "AGENT_REGISTRY.json").write_text(
        json.dumps({"alpha": {"status": "active"}}),
        encoding="utf-8",
    )

    monkeypatch.setenv("HERMES_REPO", str(repo))
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("HERMES_AGENTS_DIR", raising=False)

    from hermes_cli.mcp_config import build_cursor_mcp_diagnostics

    result = build_cursor_mcp_diagnostics(str(repo))
    checks = {check["name"]: check for check in result["checks"]}

    assert checks["launcher"]["status"] == "ok"
    assert checks["cursor_config"]["status"] == "ok"
    assert checks["skills_context_tools"]["status"] == "ok"
    assert checks["agent_registry"]["status"] == "ok"
    assert "town_brief" in result["skills_context_tools"]
    assert result["suggested_cursor_mcp_json"]["mcpServers"]["hermes"]["command"] == (
        "${workspaceFolder}/hermes-mcp-serve"
    )
    assert os.environ["HERMES_HOME"] == str(home)
