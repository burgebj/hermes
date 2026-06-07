import json
import subprocess

from hermes_cli import antfarm_bridge


def test_intake_calls_antfarm_operator_and_binds_kanban(monkeypatch):
    calls = []
    bindings = []

    def fake_run(cmd, check, text, stdout, stderr):
        calls.append(cmd)
        assert check is False
        assert text is True
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.PIPE
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout=json.dumps({"ok": True, "factory_item_id": "fi_123", "audit_event_id": "ae_123"}),
            stderr="",
        )

    monkeypatch.setattr(antfarm_bridge.subprocess, "run", fake_run)
    monkeypatch.setattr(
        antfarm_bridge,
        "_bind_kanban_task",
        lambda **kwargs: bindings.append(kwargs),
    )

    parser = antfarm_bridge.build_parser(_Subparsers())
    args = parser.parse_args([
        "intake",
        "--title", "Build command audit bridge",
        "--repo", "fchaudhryspear/antfarm",
        "--kanban-task", "t_123",
        "--board", "factory",
    ])

    assert antfarm_bridge.antfarm_command(args) == 0
    assert calls == [[
        "antfarm",
        "factory",
        "operator",
        "intake",
        "--title", "Build command audit bridge",
        "--operator", "hermes",
        "--source", "hermes-kanban",
        "--repo", "fchaudhryspear/antfarm",
        "--external-ref", "kanban:t_123",
    ]]
    assert bindings == [{
        "board": "factory",
        "task_id": "t_123",
        "factory_item_id": "fi_123",
        "audit_event_id": "ae_123",
        "author": "hermes",
    }]


def test_pause_resume_retry_commands_call_antfarm_without_kanban_db(monkeypatch):
    calls = []

    def fake_run(cmd, check, text, stdout, stderr):
        calls.append(cmd)
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout=json.dumps({"ok": True, "command": cmd[3], "audit_event_id": "ae"}),
            stderr="",
        )

    monkeypatch.setattr(antfarm_bridge.subprocess, "run", fake_run)
    parser = antfarm_bridge.build_parser(_Subparsers())

    for action in ("pause-run", "resume-run", "retry-run"):
        args = parser.parse_args([
            action,
            "--factory-run-id", "fr_123",
            "--expected-updated-at", "2026-05-24T00:00:00.000Z",
            "--reason", "operator smoke",
        ])
        assert antfarm_bridge.antfarm_command(args) == 0

    assert [call[3] for call in calls] == ["pause-run", "resume-run", "retry-run"]
    assert all(call[:3] == ["antfarm", "factory", "operator"] for call in calls)


class _Subparsers:
    def add_parser(self, *args, **kwargs):
        import argparse

        parser = argparse.ArgumentParser(prog=args[0])
        return parser
