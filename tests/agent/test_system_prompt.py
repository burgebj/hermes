"""Tests for agent/system_prompt.py — context-file cwd wiring."""

from types import SimpleNamespace
from unittest.mock import patch

from agent.system_prompt import build_system_prompt, build_system_prompt_parts


class HonchoLikeMemoryManager:
    def __init__(self):
        self.prefetch_called = False

    def build_system_prompt(self):
        return "# Honcho Memory\nActive (hybrid mode)."

    def prefetch_all(self, query, *, session_id=""):
        self.prefetch_called = True
        return (
            "## Session Summary\nfresh session\n\n"
            "## User Representation\nfresh peer\n\n"
            "dialectic: current turn synthesis"
        )


def _make_agent(**overrides):
    base = dict(
        load_soul_identity=False,
        skip_context_files=False,
        valid_tool_names=[],
        _task_completion_guidance=False,
        _tool_use_enforcement=False,
        _environment_probe=False,
        _kanban_worker_guidance="",
        _memory_store=None,
        _memory_manager=None,
        model="",
        provider="",
        platform="",
        pass_session_id=False,
        session_id="",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _captured_context_cwd(agent):
    """The cwd build_system_prompt_parts hands to build_context_files_prompt."""
    captured = {}

    def fake_context_files(cwd=None, skip_soul=False):
        captured["cwd"] = cwd
        return ""

    with (
        patch("run_agent.load_soul_md", return_value=""),
        patch("run_agent.build_nous_subscription_prompt", return_value=""),
        patch("run_agent.build_environment_hints", return_value=""),
        patch("run_agent.build_context_files_prompt", side_effect=fake_context_files),
    ):
        build_system_prompt_parts(agent)
    return captured["cwd"]


class TestContextFileCwd:
    def test_none_when_terminal_cwd_unset(self, monkeypatch):
        # Unset → None, so discovery falls back to the launch dir inside
        # build_context_files_prompt (the local-CLI #19242 contract).
        monkeypatch.delenv("TERMINAL_CWD", raising=False)
        assert _captured_context_cwd(_make_agent()) is None

    def test_configured_dir_when_terminal_cwd_set(self, monkeypatch, tmp_path):
        monkeypatch.setenv("TERMINAL_CWD", str(tmp_path))
        assert _captured_context_cwd(_make_agent()) == tmp_path


class TestHonchoPromptCacheBoundary:
    def test_dynamic_honcho_context_stays_out_of_cached_prompt(self):
        memory_manager = HonchoLikeMemoryManager()
        agent = _make_agent(
            skip_context_files=True,
            _memory_manager=memory_manager,
        )

        with (
            patch("run_agent.load_soul_md", return_value=""),
            patch("run_agent.build_nous_subscription_prompt", return_value=""),
            patch("run_agent.build_environment_hints", return_value=""),
        ):
            prompt = build_system_prompt(agent)

        assert "Honcho Memory" in prompt
        assert "Active (hybrid mode)." in prompt
        assert "Session Summary" not in prompt
        assert "User Representation" not in prompt
        assert "current turn synthesis" not in prompt
        assert memory_manager.prefetch_called is False
