import threading
from unittest.mock import patch

import cli as cli_module
from cli import HermesCLI


class _ImmediateApprovalQueue:
    def __init__(self, cli_obj, seen):
        self._cli = cli_obj
        self._seen = seen

    def get(self, timeout=1):
        self._seen["deadline"] = self._cli._approval_deadline
        return "once"


def _make_cli_stub():
    cli_obj = HermesCLI.__new__(HermesCLI)
    cli_obj._approval_lock = threading.Lock()
    cli_obj._approval_state = None
    cli_obj._approval_deadline = 0
    cli_obj._invalidate = lambda: None
    return cli_obj


def test_cli_approval_callback_honors_approvals_timeout_config():
    cli_obj = _make_cli_stub()
    seen = {}

    with patch.dict(cli_module.__dict__, {"CLI_CONFIG": {"approvals": {"timeout": 600}}}), patch(
        "cli.queue.Queue", side_effect=lambda: _ImmediateApprovalQueue(cli_obj, seen)
    ), patch("time.monotonic", return_value=100.0):
        result = cli_obj._approval_callback("rm -rf /tmp/example", "dangerous command")

    assert result == "once"
    assert seen["deadline"] == 700.0
    assert cli_obj._approval_state is None
    assert cli_obj._approval_deadline == 0


def test_cli_approval_callback_falls_back_for_malformed_approvals_config():
    malformed_configs = [
        None,
        "bad",
        [],
        {"timeout": False},
        {"timeout": True},
        {"timeout": -1},
        {"timeout": 0},
        {"timeout": float("inf")},
        {"timeout": 10**400},
    ]
    for approvals_config in malformed_configs:
        cli_obj = _make_cli_stub()
        seen = {}

        with patch.dict(cli_module.__dict__, {"CLI_CONFIG": {"approvals": approvals_config}}), patch(
            "cli.queue.Queue", side_effect=lambda: _ImmediateApprovalQueue(cli_obj, seen)
        ), patch("time.monotonic", return_value=100.0):
            result = cli_obj._approval_callback("rm -rf /tmp/example", "dangerous command")

        assert result == "once"
        assert seen["deadline"] == 160.0
        assert cli_obj._approval_state is None
        assert cli_obj._approval_deadline == 0
