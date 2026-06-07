"""Unit tests for hooks/stop/session_audit.py.

Tests run the script as a subprocess, passing JSON via stdin and inspecting
the files written to a pytest tmp_path directory.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_SCRIPT = Path(__file__).parent.parent.parent / "hooks" / "stop" / "session_audit.py"


def _run(payload: dict | None, *, audit_dir: Path, proposals_dir: Path,
         extra_env: dict | None = None) -> subprocess.CompletedProcess:
    stdin = json.dumps(payload).encode() if payload is not None else b""
    env = {**os.environ,
           "HERMES_AUDIT_DIR": str(audit_dir),
           "HERMES_PROPOSALS_DIR": str(proposals_dir),
           **(extra_env or {})}
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=stdin,
        capture_output=True,
        env=env,
    )


@pytest.fixture()
def dirs(tmp_path):
    return tmp_path / "audits", tmp_path / "proposals"


class TestAuditFileIsWritten:
    def test_creates_audit_file(self, dirs):
        audit_dir, proposals_dir = dirs
        result = _run({"session_id": "test-123"}, audit_dir=audit_dir,
                      proposals_dir=proposals_dir)
        assert result.returncode == 0
        files = list(audit_dir.glob("*.yaml"))
        assert len(files) == 1

    def test_audit_file_contains_required_fields(self, dirs):
        audit_dir, proposals_dir = dirs
        _run({"session_id": "s-abc"}, audit_dir=audit_dir, proposals_dir=proposals_dir)
        content = next(audit_dir.glob("*.yaml")).read_text()
        for field in ("session_id", "goal", "outcome", "tools_called",
                      "entropy_events", "decisions_made", "what_worked",
                      "what_failed", "open_threads", "improvement"):
            assert field in content, f"Field '{field}' missing from audit YAML"

    def test_session_id_in_audit(self, dirs):
        audit_dir, proposals_dir = dirs
        _run({"session_id": "my-session"}, audit_dir=audit_dir,
             proposals_dir=proposals_dir)
        content = next(audit_dir.glob("*.yaml")).read_text()
        assert "my-session" in content


class TestEvolutionProposal:
    def test_proposal_written_when_improvement_present(self, dirs):
        audit_dir, proposals_dir = dirs
        result = _run({"session_id": "s1", "improvement": "add retry logic"},
                      audit_dir=audit_dir, proposals_dir=proposals_dir)
        assert result.returncode == 0
        proposals = list(proposals_dir.glob("*_proposal.yaml"))
        assert len(proposals) == 1

    def test_proposal_not_written_when_improvement_empty(self, dirs):
        audit_dir, proposals_dir = dirs
        _run({"session_id": "s2", "improvement": ""},
             audit_dir=audit_dir, proposals_dir=proposals_dir)
        proposals = list(proposals_dir.glob("*_proposal.yaml")) if proposals_dir.exists() else []
        assert len(proposals) == 0

    def test_proposal_contains_improvement_text(self, dirs):
        audit_dir, proposals_dir = dirs
        _run({"session_id": "s3", "improvement": "use caching"},
             audit_dir=audit_dir, proposals_dir=proposals_dir)
        content = next(proposals_dir.glob("*_proposal.yaml")).read_text()
        assert "use caching" in content

    def test_proposal_not_written_when_no_improvement_field(self, dirs):
        audit_dir, proposals_dir = dirs
        _run({"session_id": "s4"}, audit_dir=audit_dir, proposals_dir=proposals_dir)
        proposals = list(proposals_dir.glob("*_proposal.yaml")) if proposals_dir.exists() else []
        assert len(proposals) == 0


class TestEnvVarOverrides:
    def test_hermes_audit_dir_env_var(self, tmp_path):
        custom_dir = tmp_path / "custom_audits"
        proposals_dir = tmp_path / "p"
        result = _run({"session_id": "e1"}, audit_dir=custom_dir,
                      proposals_dir=proposals_dir)
        assert result.returncode == 0
        assert custom_dir.exists()
        assert len(list(custom_dir.glob("*.yaml"))) == 1

    def test_hermes_proposals_dir_env_var(self, tmp_path):
        audit_dir = tmp_path / "a"
        custom_proposals = tmp_path / "custom_proposals"
        result = _run({"session_id": "e2", "improvement": "test"},
                      audit_dir=audit_dir, proposals_dir=custom_proposals)
        assert result.returncode == 0
        assert custom_proposals.exists()
        assert len(list(custom_proposals.glob("*_proposal.yaml"))) == 1


class TestEdgeCases:
    def test_non_json_stdin_handled_gracefully(self, dirs):
        audit_dir, proposals_dir = dirs
        env = {**os.environ,
               "HERMES_AUDIT_DIR": str(audit_dir),
               "HERMES_PROPOSALS_DIR": str(proposals_dir)}
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=b"not valid json at all",
            capture_output=True,
            env=env,
        )
        assert result.returncode == 0
        assert len(list(audit_dir.glob("*.yaml"))) == 1

    def test_empty_stdin_handled_gracefully(self, dirs):
        audit_dir, proposals_dir = dirs
        env = {**os.environ,
               "HERMES_AUDIT_DIR": str(audit_dir),
               "HERMES_PROPOSALS_DIR": str(proposals_dir)}
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=b"",
            capture_output=True,
            env=env,
        )
        assert result.returncode == 0

    def test_stdout_message_on_success(self, dirs):
        audit_dir, proposals_dir = dirs
        result = _run({"session_id": "msg-test"}, audit_dir=audit_dir,
                      proposals_dir=proposals_dir)
        assert b"[session_audit] Audit written:" in result.stdout
