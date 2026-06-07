"""Unit-Tests fuer agent.tool_audit — Redaction + Fail-Soft-Vertrag.

Run: .venv/bin/pytest tests/test_tool_audit.py -v
"""
import json
import logging
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agent.tool_audit import (
    ToolExecutionAudit,
    _redact_secrets,
    get_audit,
)


# ── Redaction ──────────────────────────────────────────────────────────────

class TestRedaction:
    def test_redact_top_level_api_key(self):
        result = _redact_secrets({"api_key": "secret123", "name": "X"})
        assert result["api_key"] == "<redacted>"
        assert result["name"] == "X"

    def test_redact_case_insensitive(self):
        result = _redact_secrets({"TOKEN": "x", "Auth_Header": "y", "PWD": "z"})
        assert all(v == "<redacted>" for v in result.values())

    def test_redact_nested_dict(self):
        result = _redact_secrets({"outer": {"secret_key": "x", "public": "y"}})
        assert result["outer"]["secret_key"] == "<redacted>"
        assert result["outer"]["public"] == "y"

    def test_redact_list_of_dicts(self):
        result = _redact_secrets({"arr": [{"token": "x"}, {"name": "y"}]})
        assert result["arr"][0]["token"] == "<redacted>"
        assert result["arr"][1]["name"] == "y"

    def test_redact_all_six_patterns(self):
        cases = {
            "user_key": "k",
            "access_token": "t",
            "client_secret": "s",
            "user_password": "p",
            "AUTH_HEADER": "a",
            "user_pwd": "pw",
        }
        result = _redact_secrets(cases)
        assert all(v == "<redacted>" for v in result.values()), result

    def test_redact_no_match_passes_through(self):
        result = _redact_secrets({"user_id": "42", "command": "ls"})
        assert result == {"user_id": "42", "command": "ls"}

    def test_redact_scalar_input_unchanged(self):
        assert _redact_secrets("just a string") == "just a string"
        assert _redact_secrets(42) == 42
        assert _redact_secrets(None) is None

    def test_redact_substring_match_is_conservative(self):
        # "monkey" enthaelt "key" → bewusste False-Positive (lieber redact als leak)
        result = _redact_secrets({"monkey": "X"})
        assert result["monkey"] == "<redacted>"


# ── ToolExecutionAudit ─────────────────────────────────────────────────────

class TestToolExecutionAudit:
    def test_disabled_when_script_missing(self, tmp_path):
        nonexistent = tmp_path / "nonexistent.sh"
        audit = ToolExecutionAudit(logger_path=nonexistent)
        assert audit._enabled is False

    def test_disabled_when_script_not_executable(self, tmp_path):
        script = tmp_path / "not_exec.sh"
        script.write_text("#!/bin/bash\necho hi\n")
        script.chmod(0o644)  # no exec bit
        audit = ToolExecutionAudit(logger_path=script)
        assert audit._enabled is False

    def test_enabled_when_script_executable(self, tmp_path):
        script = tmp_path / "exec.sh"
        script.write_text("#!/bin/bash\nexit 0\n")
        script.chmod(0o700)
        audit = ToolExecutionAudit(logger_path=script)
        assert audit._enabled is True

    def test_audit_noop_when_disabled(self, tmp_path):
        audit = ToolExecutionAudit(logger_path=tmp_path / "missing.sh")
        # Darf nicht raise + nicht subprocess.run aufrufen
        with patch("subprocess.run") as mock_run:
            audit.audit("agent-1", "tool-x", {"k": "v"})
            mock_run.assert_not_called()

    def test_audit_redacts_before_serialize(self, tmp_path):
        script = tmp_path / "exec.sh"
        script.write_text("#!/bin/bash\ncat > /dev/null\nexit 0\n")
        script.chmod(0o700)
        audit = ToolExecutionAudit(logger_path=script)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            audit.audit("a1", "tool", {"api_key": "SECRET", "name": "X"})
            payload = mock_run.call_args.kwargs["input"]
            data = json.loads(payload)
            assert data["args"]["api_key"] == "<redacted>"
            assert data["args"]["name"] == "X"
            assert "SECRET" not in payload

    def test_audit_fail_soft_on_timeout(self, tmp_path, caplog):
        script = tmp_path / "exec.sh"
        script.write_text("#!/bin/bash\nexit 0\n")
        script.chmod(0o700)
        audit = ToolExecutionAudit(logger_path=script, timeout=0.5)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=0.5)
            with caplog.at_level(logging.ERROR, logger="agent.tool_audit"):
                audit.audit("a1", "tool", {})  # darf nicht raise
            assert "timeout" in caplog.text.lower()

    def test_audit_fail_soft_on_nonzero_rc(self, tmp_path, caplog):
        script = tmp_path / "exec.sh"
        script.write_text("#!/bin/bash\nexit 0\n")
        script.chmod(0o700)
        audit = ToolExecutionAudit(logger_path=script)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="oops")
            with caplog.at_level(logging.ERROR, logger="agent.tool_audit"):
                audit.audit("a1", "tool", {})
            assert "rc=1" in caplog.text

    def test_audit_fail_soft_on_oserror(self, tmp_path, caplog):
        script = tmp_path / "exec.sh"
        script.write_text("#!/bin/bash\nexit 0\n")
        script.chmod(0o700)
        audit = ToolExecutionAudit(logger_path=script)

        with patch("subprocess.run", side_effect=PermissionError("nope")):
            with caplog.at_level(logging.ERROR, logger="agent.tool_audit"):
                audit.audit("a1", "tool", {})  # darf nicht raise
            assert "spawn failed" in caplog.text

    def test_audit_handles_non_serializable_args(self, tmp_path):
        """Tool-Args mit nicht-JSON-serialisierbaren Objekten → default=str fallback."""
        script = tmp_path / "exec.sh"
        script.write_text("#!/bin/bash\ncat > /dev/null\nexit 0\n")
        script.chmod(0o700)
        audit = ToolExecutionAudit(logger_path=script)

        class Weird:
            def __str__(self):
                return "weird-instance"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            audit.audit("a1", "tool", {"obj": Weird()})
            payload = mock_run.call_args.kwargs["input"]
            assert "weird-instance" in payload


# ── Singleton ──────────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_audit_returns_same_instance(self):
        a1 = get_audit()
        a2 = get_audit()
        assert a1 is a2
