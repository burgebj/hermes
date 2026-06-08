import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hermes_cli import mission


def test_build_preview_has_ack_watchdog_and_no_side_effects():
    spec = {
        "mission": {
            "name": "overnight mission wrapper dry-run",
            "origin": "discord:#hermes-main",
            "return_to": "discord:#hermes-main",
        },
        "graph": [
            {"id": "impl", "title": "Implement dry-run", "assignee": "ccsupervisor"},
            {"id": "review", "title": "Review dry-run", "assignee": "ccreviewer", "depends_on": ["impl"]},
        ],
        "ack": {"final_task": "review"},
        "watchdog": {"schedule": "every 15m"},
    }

    preview = mission.build_preview(spec)

    assert preview["status"] == "mission_dry_run_preview"
    assert preview["sent"] is False
    assert preview["created"] is False
    assert preview["live_dispatch"] is False
    assert preview["safety"] == {
        "dry_run_only": True,
        "would_send": False,
        "would_write_kanban": False,
        "would_create_cron": False,
        "would_trigger_agent": False,
    }
    assert [task["id"] for task in preview["would_create_tasks"]] == ["impl", "review"]
    assert preview["would_subscribe_final_ack"] == {
        "enabled": True,
        "origin": "discord:#hermes-main",
        "return_to": "discord:#hermes-main",
        "final_task": "review",
        "verdict_schema": ["GO", "BLOCK", "NEED_MORE"],
    }
    assert preview["would_create_watchdog"] == {
        "enabled": True,
        "schedule": "every 15m",
        "material_change_only": True,
        "deliver": "discord:#hermes-main",
    }


def test_create_requires_dry_run_before_reading_file(capsys):
    args = argparse.Namespace(dry_run=False, file="/path/that/should/not/be/read.yml", json=True)

    rc = mission.mission_create(args)

    assert rc == 2
    assert "pass --dry-run" in capsys.readouterr().err


def test_create_dry_run_json_from_yaml_file(tmp_path, capsys):
    spec = tmp_path / "mission.yml"
    spec.write_text(
        """
mission:
  name: Agent OS MISSION-M0
  objective: overnight mission wrapper dry-run
  origin: discord:#hermes-main
  return_to: discord:#hermes-mission-control
graph:
  - id: create
    title: hermes mission create --dry-run
    assignee: ccsupervisor
  - id: review
    title: review preview contract
    assignee: ccreviewer
    depends_on: create
watchdog:
  schedule: every 15m
""".strip(),
        encoding="utf-8",
    )
    args = argparse.Namespace(dry_run=True, file=str(spec), json=True)

    rc = mission.mission_create(args)

    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mission"]["name"] == "Agent OS MISSION-M0"
    assert out["mission"]["return_to"] == "discord:#hermes-mission-control"
    assert out["would_create_tasks"][1]["depends_on"] == ["create"]
    assert out["would_create_watchdog"]["enabled"] is True
    assert out["safety"]["would_create_cron"] is False


def test_build_parser_wires_create_command():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    mission.build_parser(subparsers)

    args = parser.parse_args(["mission", "create", "--dry-run", "--json"])

    assert args.command == "mission"
    assert args.mission_command == "create"
    assert args.dry_run is True
    assert args.json is True
    assert args.func is mission.mission_command


def test_depends_on_entries_must_be_stringish():
    spec = {
        "graph": [
            {"id": "one", "title": "one"},
            {"id": "two", "title": "two", "depends_on": [{"nested": "not allowed"}]},
        ]
    }

    with pytest.raises(mission.MissionSpecError, match="depends_on entries"):
        mission.build_preview(spec)


def test_top_level_cli_missing_dry_run_exits_nonzero(tmp_path):
    spec = tmp_path / "mission.json"
    spec.write_text('{"graph": ["preview only"]}', encoding="utf-8")
    env = {**os.environ, "HERMES_HOME": str(tmp_path / "hermes-home")}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hermes_cli.main",
            "mission",
            "create",
            "--file",
            str(spec),
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 2
    assert "pass --dry-run" in result.stderr
