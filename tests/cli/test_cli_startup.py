"""Regression test: HermesCLI startup with OpenViking orphan commit path.

Verifies that ``HermesCLI.__init__`` can complete without raising
``AttributeError`` even when OpenViking orphan-session recovery is
configured — the ``session_id`` attribute must exist before any
startup-side-effect helper references it.

See GitHub issue #31429 and the fix in ``cli.py`` (2026-05-24):
``_commit_orphaned_openviking_sessions`` was called before
``self.session_id`` was assigned in the constructor.
"""

from __future__ import annotations

import importlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest


def _make_cli(**kwargs):
    """Create a HermesCLI instance with minimal mocking.

    Stubs out prompt_toolkit (GUI dependency) and injects a minimal
    CLI_CONFIG so the constructor passes through cleanly without a real
    config.yaml or terminal.
    """
    _clean_config = {
        "model": {
            "default": "anthropic/claude-opus-4.6",
            "base_url": "https://openrouter.ai/api/v1",
            "provider": "auto",
        },
        "display": {"compact": False, "tool_progress": "all"},
        "agent": {},
        "terminal": {"env_type": "local"},
    }
    clean_env = {"LLM_MODEL": "", "HERMES_MAX_ITERATIONS": ""}
    prompt_toolkit_stubs = {
        "prompt_toolkit": MagicMock(),
        "prompt_toolkit.history": MagicMock(),
        "prompt_toolkit.styles": MagicMock(),
        "prompt_toolkit.patch_stdout": MagicMock(),
        "prompt_toolkit.application": MagicMock(),
        "prompt_toolkit.layout": MagicMock(),
        "prompt_toolkit.layout.processors": MagicMock(),
        "prompt_toolkit.filters": MagicMock(),
        "prompt_toolkit.layout.dimension": MagicMock(),
        "prompt_toolkit.layout.menus": MagicMock(),
        "prompt_toolkit.widgets": MagicMock(),
        "prompt_toolkit.key_binding": MagicMock(),
        "prompt_toolkit.completion": MagicMock(),
        "prompt_toolkit.formatted_text": MagicMock(),
        "prompt_toolkit.auto_suggest": MagicMock(),
    }
    with patch.dict(sys.modules, prompt_toolkit_stubs), patch.dict(
        "os.environ", clean_env, clear=False
    ):
        import cli as _cli_mod

        _cli_mod = importlib.reload(_cli_mod)
        with patch.object(_cli_mod, "get_tool_definitions", return_value=[]), patch.dict(
            _cli_mod.__dict__, {"CLI_CONFIG": _clean_config}
        ):
            return _cli_mod.HermesCLI(**kwargs)


def test_hermes_cli_init_does_not_crash():
    """HermesCLI() constructor completes without raising.

    This is the primary regression test for the orphan-commit ordering
    bug: if ``self.session_id`` is not initialized before the orphan
    commit call, ``AttributeError`` is raised and the CLI is unusable.
    """
    cli = _make_cli()
    assert cli is not None
    assert hasattr(cli, "session_id")
    assert isinstance(cli.session_id, str)
    assert len(cli.session_id) > 0


def test_hermes_cli_init_with_orphan_failure():
    """HermesCLI() survives a simulated orphan commit crash.

    Verifies that the try/except wrapper around the orphan commit
    call prevents a failing OpenViking recovery from blocking startup.
    """
    _clean_config = {
        "model": {
            "default": "anthropic/claude-opus-4.6",
            "base_url": "https://openrouter.ai/api/v1",
            "provider": "auto",
        },
        "display": {"compact": False, "tool_progress": "all"},
        "agent": {},
        "terminal": {"env_type": "local"},
    }
    clean_env = {"LLM_MODEL": "", "HERMES_MAX_ITERATIONS": ""}
    prompt_toolkit_stubs = {
        "prompt_toolkit": MagicMock(),
        "prompt_toolkit.history": MagicMock(),
        "prompt_toolkit.styles": MagicMock(),
        "prompt_toolkit.patch_stdout": MagicMock(),
        "prompt_toolkit.application": MagicMock(),
        "prompt_toolkit.layout": MagicMock(),
        "prompt_toolkit.layout.processors": MagicMock(),
        "prompt_toolkit.filters": MagicMock(),
        "prompt_toolkit.layout.dimension": MagicMock(),
        "prompt_toolkit.layout.menus": MagicMock(),
        "prompt_toolkit.widgets": MagicMock(),
        "prompt_toolkit.key_binding": MagicMock(),
        "prompt_toolkit.completion": MagicMock(),
        "prompt_toolkit.formatted_text": MagicMock(),
        "prompt_toolkit.auto_suggest": MagicMock(),
    }
    with patch.dict(sys.modules, prompt_toolkit_stubs), patch.dict(
        "os.environ", clean_env, clear=False
    ):
        import cli as _cli_mod

        _cli_mod = importlib.reload(_cli_mod)

        def _raise_exc(*_args, **_kw):
            raise RuntimeError("Simulated OpenViking failure")

        with patch.object(_cli_mod, "get_tool_definitions", return_value=[]), patch.dict(
            _cli_mod.__dict__, {"CLI_CONFIG": _clean_config}
        ), patch.object(
            _cli_mod, "_commit_orphaned_openviking_sessions", side_effect=_raise_exc
        ):
            cli = _cli_mod.HermesCLI()

    assert cli is not None
    assert cli.session_id
