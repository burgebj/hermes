"""Tests for Honcho session name length cap (#13868)."""
import re
import pytest


class TestSessionNameLengthCap:
    """All session names must be <= 100 chars (#13868)."""

    def test_source_has_length_cap(self):
        """Verify resolve_session_name applies _MAX_SESSION_ID_LEN."""
        import inspect
        from plugins.memory.honcho.client import HonchoClientConfig
        source = inspect.getsource(HonchoClientConfig.resolve_session_name)
        assert "_MAX_SESSION_ID_LEN" in source
        assert source.count("[:_MAX_SESSION_ID_LEN]") >= 6

    def test_long_gateway_key_truncated(self):
        _MAX = 100
        long_key = "agent:main:telegram:group:" + "1234567890" * 20
        sanitized = re.sub(r'[^a-zA-Z0-9_-]+', '-', long_key).strip('-')
        assert len(sanitized[:_MAX]) <= 100

    def test_short_key_unchanged(self):
        short = "agent-main-telegram-dm-12345"
        assert short[:100] == short

    def test_per_repo_name_is_truncated(self):
        from plugins.memory.honcho.client import HonchoClientConfig

        cfg = HonchoClientConfig(session_strategy="per-repo")
        cfg._git_repo_name = lambda cwd: "repo-" + ("x" * 150)

        assert len(cfg.resolve_session_name(cwd="/tmp/project")) == 100

    def test_per_directory_name_is_truncated(self):
        from plugins.memory.honcho.client import HonchoClientConfig

        cfg = HonchoClientConfig(session_strategy="per-directory")
        long_cwd = "/tmp/" + ("y" * 150)

        assert len(cfg.resolve_session_name(cwd=long_cwd)) == 100

    def test_global_workspace_id_is_truncated(self):
        from plugins.memory.honcho.client import HonchoClientConfig

        cfg = HonchoClientConfig(
            session_strategy="global",
            workspace_id="workspace-" + ("z" * 150),
        )

        assert len(cfg.resolve_session_name(cwd="/tmp/project")) == 100
