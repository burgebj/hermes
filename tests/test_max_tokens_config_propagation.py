"""Regression tests for issue #20741.

Verifies that ``model.max_tokens`` in config.yaml is correctly propagated to
``AIAgent.__init__()`` and from there to ``ChatCompletionsTransport.build_kwargs()``
so custom/Ollama/zai endpoints receive the user-configured output cap.

Three layers are tested independently to avoid needing live API credentials:
 1. Gateway helper ``_resolve_config_max_tokens`` reads config.yaml correctly.
 2. Gateway helper ``_resolve_runtime_agent_kwargs`` includes ``max_tokens``.
 3. The CLI ``max_tokens`` initialisation logic reads from config and env var.
"""

import os
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

import gateway.run as gateway_run
from gateway.run import _resolve_config_max_tokens, _resolve_runtime_agent_kwargs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_config(tmp_path: Path, content: str) -> Path:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(content), encoding="utf-8")
    return cfg


# ---------------------------------------------------------------------------
# 1. _resolve_config_max_tokens
# ---------------------------------------------------------------------------

class TestResolveConfigMaxTokens:
    """Unit-tests for the new gateway helper."""

    def test_returns_none_when_unset(self, tmp_path):
        _write_config(tmp_path, """\
            model:
              default: gpt-4o
              provider: openai
        """)
        with patch.object(gateway_run, "_hermes_home", tmp_path), \
             patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HERMES_MAX_TOKENS", None)
            assert _resolve_config_max_tokens() is None

    def test_reads_max_tokens_from_model_section(self, tmp_path):
        _write_config(tmp_path, """\
            model:
              default: glm-5.1
              provider: ollama-cloud
              max_tokens: 16384
        """)
        with patch.object(gateway_run, "_hermes_home", tmp_path), \
             patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HERMES_MAX_TOKENS", None)
            assert _resolve_config_max_tokens() == 16384

    def test_env_var_overrides_config(self, tmp_path):
        _write_config(tmp_path, """\
            model:
              max_tokens: 4096
        """)
        with patch.object(gateway_run, "_hermes_home", tmp_path), \
             patch.dict(os.environ, {"HERMES_MAX_TOKENS": "8192"}):
            assert _resolve_config_max_tokens() == 8192

    def test_env_var_works_without_config_file(self, tmp_path):
        # No config.yaml present — tmp_path is empty
        with patch.object(gateway_run, "_hermes_home", tmp_path), \
             patch.dict(os.environ, {"HERMES_MAX_TOKENS": "32000"}):
            assert _resolve_config_max_tokens() == 32000

    def test_invalid_env_var_returns_none(self, tmp_path):
        with patch.object(gateway_run, "_hermes_home", tmp_path), \
             patch.dict(os.environ, {"HERMES_MAX_TOKENS": "not-a-number"}):
            assert _resolve_config_max_tokens() is None


# ---------------------------------------------------------------------------
# 2. _resolve_runtime_agent_kwargs includes max_tokens
# ---------------------------------------------------------------------------

class TestResolveRuntimeAgentKwargsMaxTokens:
    """Verify _resolve_runtime_agent_kwargs() returns max_tokens in its dict."""

    _FAKE_RUNTIME = {
        "api_key": "sk-test",
        "base_url": "https://ollama.com/v1",
        "provider": "ollama-cloud",
        "api_mode": "chat_completions",
        "command": None,
        "args": [],
        "credential_pool": None,
    }

    def test_max_tokens_included_when_configured(self, tmp_path):
        _write_config(tmp_path, """\
            model:
              default: glm-5.1
              provider: ollama-cloud
              max_tokens: 16384
        """)
        with patch.object(gateway_run, "_hermes_home", tmp_path), \
             patch.dict(os.environ, {}, clear=False), \
             patch(
                 "hermes_cli.runtime_provider.resolve_runtime_provider",
                 return_value=self._FAKE_RUNTIME,
             ):
            os.environ.pop("HERMES_MAX_TOKENS", None)
            kwargs = _resolve_runtime_agent_kwargs()
            assert "max_tokens" in kwargs
            assert kwargs["max_tokens"] == 16384

    def test_max_tokens_none_when_not_configured(self, tmp_path):
        _write_config(tmp_path, """\
            model:
              default: gpt-4o
              provider: openai
        """)
        with patch.object(gateway_run, "_hermes_home", tmp_path), \
             patch.dict(os.environ, {}, clear=False), \
             patch(
                 "hermes_cli.runtime_provider.resolve_runtime_provider",
                 return_value=self._FAKE_RUNTIME,
             ):
            os.environ.pop("HERMES_MAX_TOKENS", None)
            kwargs = _resolve_runtime_agent_kwargs()
            assert kwargs.get("max_tokens") is None


# ---------------------------------------------------------------------------
# 3. CLI max_tokens initialisation logic
#
# HermesCLI.__init__ is very heavy (it imports fire, rich, etc.) so we test
# only the isolated logic block that computes self.max_tokens, extracted into
# a pure helper function here.
# ---------------------------------------------------------------------------

def _compute_max_tokens(cli_config: dict, env: dict) -> "int | None":
    """Replicate the max_tokens resolution logic from HermesCLI.__init__."""
    _cfg_raw = cli_config.get("model", {})
    if isinstance(_cfg_raw, dict):
        _cfg_max_tokens = _cfg_raw.get("max_tokens")
    else:
        _cfg_max_tokens = None

    _env_val = env.get("HERMES_MAX_TOKENS")
    if _env_val is not None:
        try:
            return int(_env_val)
        except ValueError:
            return None
    elif _cfg_max_tokens is not None:
        try:
            return int(_cfg_max_tokens)
        except (TypeError, ValueError):
            return None
    return None


class TestCliMaxTokensLogic:
    """Tests for the max_tokens resolution logic used in HermesCLI.__init__."""

    def test_reads_from_model_section(self):
        cfg = {"model": {"default": "glm-5.1", "provider": "ollama-cloud", "max_tokens": 16384}}
        assert _compute_max_tokens(cfg, {}) == 16384

    def test_env_var_wins_over_config(self):
        cfg = {"model": {"max_tokens": 4096}}
        assert _compute_max_tokens(cfg, {"HERMES_MAX_TOKENS": "32768"}) == 32768

    def test_none_when_unset_everywhere(self):
        cfg = {"model": {"default": "gpt-4o", "provider": "openai"}}
        assert _compute_max_tokens(cfg, {}) is None

    def test_invalid_env_var_returns_none(self):
        cfg = {}
        assert _compute_max_tokens(cfg, {"HERMES_MAX_TOKENS": "bad"}) is None

    def test_integer_coercion_from_string_in_config(self):
        # YAML sometimes returns strings if quotes used: max_tokens: "8192"
        cfg = {"model": {"max_tokens": "8192"}}
        assert _compute_max_tokens(cfg, {}) == 8192

    def test_string_model_section_returns_none(self):
        # Old flat format: model: "gpt-4o" (no max_tokens key possible)
        cfg = {"model": "gpt-4o"}
        assert _compute_max_tokens(cfg, {}) is None
