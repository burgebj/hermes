import json
from unittest.mock import Mock, patch

import pytest

from agent.gbrain_cli_jobs import build_shell_submit_command, submit_shell_job


def test_build_shell_submit_command_includes_required_flags():
    cmd = build_shell_submit_command(
        params={"cmd": "bash scripts/sync.sh", "cwd": "/abs"},
        cli_path="gbrain",
        allow_shell_jobs=True,
        follow=False,
        queue="default",
        timeout_ms=300000,
        max_attempts=3,
    )
    command = cmd["command"]
    env = cmd["env"]
    assert command[:4] == ["gbrain", "jobs", "submit", "shell"]
    assert "--params" in command
    assert "--queue" in command
    assert env["GBRAIN_ALLOW_SHELL_JOBS"] == "1"


def test_submit_shell_job_parses_json_stdout():
    proc = Mock(returncode=0, stdout=json.dumps({"id": 42, "status": "waiting"}), stderr="")
    with patch("agent.gbrain_cli_jobs.subprocess.run", return_value=proc) as run_mock:
        result = submit_shell_job(
            params={"cmd": "echo hi", "cwd": "/tmp"},
            cli_path="gbrain",
            allow_shell_jobs=True,
        )

    assert result["id"] == 42
    assert run_mock.call_args.kwargs["env"]["GBRAIN_ALLOW_SHELL_JOBS"] == "1"


def test_submit_shell_job_surfaces_nonzero_exit():
    proc = Mock(returncode=1, stdout="", stderr="boom")
    with patch("agent.gbrain_cli_jobs.subprocess.run", return_value=proc):
        with pytest.raises(RuntimeError, match="boom"):
            submit_shell_job(params={"cmd": "echo hi", "cwd": "/tmp"}, cli_path="gbrain")
