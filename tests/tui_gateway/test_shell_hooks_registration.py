"""Regression test: tui_gateway must register configured shell hooks.

Without this, shell scripts declared under the ``hooks:`` block of
``config.yaml`` silently never fire for TUI sessions, even though the
same hooks work fine in the CLI (``hermes_cli/main.py``) and the
messaging gateway (``gateway/run.py``).  See issue/PR for diagnosis.
"""

import importlib
from unittest.mock import MagicMock, patch


def test_main_registers_shell_hooks():
    """``tui_gateway.entry.main`` must invoke ``register_from_config`` at
    startup so the TUI honors the same ``hooks:`` block as every other
    entry point."""
    register_mock = MagicMock(return_value=[])
    load_config_mock = MagicMock(return_value={"hooks": {}})

    # Stub the heavy imports pulled in by ``tui_gateway.server`` so the
    # entry module can load in a unit-test environment.
    stub_modules = {
        "hermes_constants": MagicMock(
            get_hermes_home=MagicMock(return_value="/tmp/hermes_test"),
        ),
        "hermes_cli.env_loader": MagicMock(),
        "hermes_cli.banner": MagicMock(),
        "hermes_state": MagicMock(),
    }
    with patch.dict("sys.modules", stub_modules):
        with patch(
            "agent.shell_hooks.register_from_config", register_mock,
        ), patch(
            "hermes_cli.config.load_config", load_config_mock,
        ), patch(
            "sys.stdin", iter([]),
        ), patch(
            "tui_gateway.entry.write_json", return_value=True,
        ):
            entry = importlib.import_module("tui_gateway.entry")
            importlib.reload(entry)
            entry.main()

    assert register_mock.call_count == 1, (
        "register_from_config must be called exactly once during TUI "
        "gateway startup so the hooks: config block actually wires up."
    )
    # Mirror gateway/run.py: accept_hooks=False — env/config resolves it.
    _, kwargs = register_mock.call_args
    assert kwargs.get("accept_hooks") is False


def test_register_failure_does_not_block_startup():
    """A broken hook config or import error must never prevent the TUI
    backend from starting — failures are logged at debug, swallowed
    otherwise."""
    register_mock = MagicMock(side_effect=RuntimeError("boom"))
    load_config_mock = MagicMock(return_value={"hooks": {}})

    stub_modules = {
        "hermes_constants": MagicMock(
            get_hermes_home=MagicMock(return_value="/tmp/hermes_test"),
        ),
        "hermes_cli.env_loader": MagicMock(),
        "hermes_cli.banner": MagicMock(),
        "hermes_state": MagicMock(),
    }
    with patch.dict("sys.modules", stub_modules):
        with patch(
            "agent.shell_hooks.register_from_config", register_mock,
        ), patch(
            "hermes_cli.config.load_config", load_config_mock,
        ), patch(
            "sys.stdin", iter([]),
        ), patch(
            "tui_gateway.entry.write_json", return_value=True,
        ):
            entry = importlib.import_module("tui_gateway.entry")
            importlib.reload(entry)
            # Must not raise.
            entry.main()
