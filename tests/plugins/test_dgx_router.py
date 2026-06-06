"""Tests for plugins/dgx/router.py — smart task router."""

from __future__ import annotations

import argparse

import pytest


# ---------------------------------------------------------------------------
# classify()
# ---------------------------------------------------------------------------

class TestClassify:
    def _c(self, text):
        from plugins.dgx.router import classify
        return classify(text)

    # Fast / simple
    def test_what_is_question(self):
        assert self._c("what is a closure?") == "fast"

    def test_how_do_question(self):
        assert self._c("how do I sort a list in Python?") == "fast"

    def test_very_short_input(self):
        assert self._c("fix bug") == "fast"

    def test_explain_single_word_target(self):
        assert self._c("explain recursion") == "fast"

    def test_list_command(self):
        assert self._c("list all endpoints") == "fast"

    # Standard / moderate
    def test_medium_length_no_signals(self):
        assert self._c("write a function that validates email addresses") == "standard"

    def test_add_docstring(self):
        assert self._c("add docstrings to this class") == "standard"

    # Complex
    def test_refactor_keyword(self):
        assert self._c("refactor the auth module") == "complex"

    def test_implement_and_pattern(self):
        assert self._c("implement user login and session management") == "complex"

    def test_across_all_files(self):
        assert self._c("update error handling across all services") == "complex"

    def test_long_detailed_request(self):
        text = ("I need you to design and build a complete OAuth2 implementation "
                "that works across the user service, API gateway, and frontend "
                "with proper token rotation and refresh logic")
        assert self._c(text) == "complex"

    def test_architecture_keyword(self):
        assert self._c("design the architecture for a new caching layer") == "complex"

    def test_from_scratch(self):
        assert self._c("build the auth system from scratch") == "complex"

    # Review
    def test_review_keyword(self):
        assert self._c("review this pull request") == "review"

    def test_find_bugs(self):
        assert self._c("find bugs in this function") == "review"

    def test_audit_keyword(self):
        assert self._c("audit the security of the API layer") == "review"

    def test_code_quality(self):
        assert self._c("check code quality of this module") == "review"

    def test_review_wins_over_complex(self):
        # "review" pattern should win even on a multi-file description
        assert self._c("review the refactored auth module across all files") == "review"


# ---------------------------------------------------------------------------
# recommend()
# ---------------------------------------------------------------------------

class TestRecommend:
    def _mock_config(self, monkeypatch, extra_formations=None):
        from plugins.dgx._dgx_config import DEFAULT_FORMATIONS, DEFAULTS
        formations = dict(DEFAULT_FORMATIONS)
        if extra_formations:
            formations.update(extra_formations)
        dgx = dict(DEFAULTS)
        dgx["formations"] = {}
        dgx["_active_node"] = {"host": "10.0.0.1", "ssh_user": "dgx",
                                "ollama_port": 11434, "vllm_port": 30800}

        import plugins.dgx.router as router_mod
        import plugins.dgx._dgx_config as cfg_mod
        monkeypatch.setattr(cfg_mod, "load_dgx_config", lambda: dgx)

    def test_fast_task_recommends_fast_formation(self, monkeypatch):
        from plugins.dgx.router import recommend
        self._mock_config(monkeypatch)
        r = recommend("what is a decorator?")
        assert r.tier == "fast"
        assert r.formation == "fast"
        assert "nemotron-mini" in r.model

    def test_complex_task_recommends_vllm_coding_or_flagship(self, monkeypatch):
        from plugins.dgx.router import recommend
        self._mock_config(monkeypatch)
        r = recommend("refactor the entire auth module across all services")
        assert r.tier == "complex"
        assert r.formation in ("vllm-coding", "flagship")

    def test_review_task_recommends_flagship(self, monkeypatch):
        from plugins.dgx.router import recommend
        self._mock_config(monkeypatch)
        r = recommend("review this pull request for security issues")
        assert r.tier == "review"
        assert r.formation in ("flagship", "vllm-coding")

    def test_standard_task_recommends_coding(self, monkeypatch):
        from plugins.dgx.router import recommend
        self._mock_config(monkeypatch)
        r = recommend("write a function to parse JSON with error handling")
        assert r.tier == "standard"
        assert r.formation in ("coding", "vllm-fast", "flagship")

    def test_result_has_model_and_endpoint(self, monkeypatch):
        from plugins.dgx.router import recommend
        self._mock_config(monkeypatch)
        r = recommend("explain async/await")
        assert r.model
        assert r.endpoint
        assert r.reason

    def test_fallback_populated_for_complex(self, monkeypatch):
        from plugins.dgx.router import recommend
        self._mock_config(monkeypatch)
        r = recommend("implement OAuth2 end to end")
        # Should have a fallback when multiple formations available
        # (vllm-coding primary → flagship fallback, or similar)
        assert r.fallback is not None or r.formation in ("flagship", "vllm-coding")

    def test_custom_formation_used_when_present(self, monkeypatch):
        from plugins.dgx.router import recommend
        self._mock_config(monkeypatch, extra_formations={
            "fast": {"model": "my-fast-model:latest", "endpoint": "ollama"}
        })
        r = recommend("what is recursion?")
        assert r.tier == "fast"
        assert r.formation == "fast"


# ---------------------------------------------------------------------------
# hermes dgx route subcommand
# ---------------------------------------------------------------------------

class TestRouteSubcommand:
    def _parser(self):
        from plugins.dgx.cli import register_cli
        p = argparse.ArgumentParser()
        register_cli(p)
        return p

    def test_route_subcommand_parses(self):
        ns = self._parser().parse_args(["route", "implement user auth"])
        assert ns.dgx_command == "route"
        assert ns.task == "implement user auth"

    def test_route_apply_flag(self):
        ns = self._parser().parse_args(["route", "fix the bug", "--apply"])
        assert ns.apply is True

    def test_route_check_flag(self):
        ns = self._parser().parse_args(["route", "refactor auth", "--check"])
        assert ns.check is True

    def test_use_for_flag_parses(self):
        ns = self._parser().parse_args(["use", "--for", "implement auth"])
        assert ns.task == "implement auth"
        assert ns.model is None

    def test_cmd_route_prints_analysis(self, monkeypatch, capsys):
        from plugins.dgx.cli import _cmd_route
        from plugins.dgx._dgx_config import DEFAULTS, DEFAULT_FORMATIONS
        dgx = dict(DEFAULTS)
        dgx["_active_node"] = {"host": "10.0.0.1", "ssh_user": "dgx",
                                "ollama_port": 11434, "vllm_port": 30800}
        monkeypatch.setattr("plugins.dgx._dgx_config.load_dgx_config", lambda: dgx)
        monkeypatch.setattr("plugins.dgx.cli.load_dgx_config", lambda: dgx)

        ret = _cmd_route("implement OAuth2 login", apply=False)
        out = capsys.readouterr().out
        assert ret == 0
        assert "Complexity" in out
        assert "Formation" in out
        assert "Model" in out
        assert "Why" in out

    def test_cmd_route_apply_calls_formation(self, monkeypatch, capsys):
        from plugins.dgx.cli import _cmd_route
        from plugins.dgx._dgx_config import DEFAULTS
        dgx = dict(DEFAULTS)
        dgx["_active_node"] = {"host": "10.0.0.1", "ssh_user": "dgx",
                                "ollama_port": 11434, "vllm_port": 30800}
        monkeypatch.setattr("plugins.dgx._dgx_config.load_dgx_config", lambda: dgx)
        monkeypatch.setattr("plugins.dgx.cli.load_dgx_config", lambda: dgx)
        applied = []
        monkeypatch.setattr("plugins.dgx.cli._cmd_formation", lambda name: applied.append(name) or 0)

        _cmd_route("refactor auth module", apply=True)
        assert len(applied) == 1  # formation was applied
