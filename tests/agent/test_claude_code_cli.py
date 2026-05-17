from pathlib import Path


def test_build_cli_env_uses_scoped_claude_code_home(monkeypatch, tmp_path):
    from agent import claude_code_cli as ccc

    scoped_home = tmp_path / "claude-home"
    monkeypatch.setenv("HOME", str(tmp_path / "default-home"))
    monkeypatch.setenv("HERMES_CLAUDE_CODE_HOME", str(scoped_home))
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "must-not-leak")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "must-not-leak")

    env = ccc._build_cli_env()

    assert env["HOME"] == str(scoped_home)
    assert "ANTHROPIC_AUTH_TOKEN" not in env
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in env


def test_build_cli_env_keeps_config_dir_override(monkeypatch, tmp_path):
    from agent import claude_code_cli as ccc

    scoped_home = tmp_path / "claude-home"
    config_dir = tmp_path / "explicit-config"
    monkeypatch.setenv("HERMES_CLAUDE_CODE_HOME", str(scoped_home))
    monkeypatch.setenv("HERMES_CLAUDE_CODE_CONFIG_DIR", str(config_dir))

    env = ccc._build_cli_env()

    assert env["HOME"] == str(scoped_home)
    assert env["CLAUDE_CONFIG_DIR"] == str(config_dir)
    assert Path(env["CLAUDE_CONFIG_DIR"]).is_dir()


def test_claude_code_cli_transport_registered():
    from agent.transports import get_transport

    transport = get_transport("claude_code_cli")

    assert transport is not None
    assert transport.api_mode == "claude_code_cli"


def test_agent_accepts_claude_code_cli_mode(monkeypatch):
    from run_agent import AIAgent

    monkeypatch.setattr(
        "agent.agent_runtime_helpers.create_openai_client",
        lambda agent, client_kwargs, **_: object(),
    )

    agent = AIAgent(
        model="claude-sonnet-4-6",
        provider="claude-code",
        api_mode="claude_code_cli",
        api_key="claude-code",
        base_url="claude://local",
        skip_memory=True,
        skip_context_files=True,
        quiet_mode=True,
    )

    assert agent.api_mode == "claude_code_cli"
    assert agent.provider == "claude-code"
    assert agent.base_url == "claude://local"
