"""Regressions for the Claude Code ACP subprocess client.

ClaudeCodeACPClient subclasses ACPSubprocessClient (defined in
agent.copilot_acp_client), so the safety layer is shared with Copilot ACP.
These tests confirm the shared behaviour still holds for the Claude Code
client and that the provider-specific surface (command, marker URL, error
text, api_key) is wired correctly.
"""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from agent.claude_code_acp_client import ClaudeCodeACPClient
from agent.copilot_acp_client import ACPSubprocessClient


class _FakeProcess:
    def __init__(self) -> None:
        self.stdin = io.StringIO()


class ClaudeCodeACPClientConfigTests(unittest.TestCase):
    def test_is_acp_subprocess_client(self) -> None:
        self.assertTrue(issubclass(ClaudeCodeACPClient, ACPSubprocessClient))

    def test_provider_defaults(self) -> None:
        client = ClaudeCodeACPClient(acp_cwd="/tmp")
        self.assertEqual(client.api_key, "claude-code-acp")
        self.assertEqual(client.base_url, "acp://claude-code")
        # Default command is the bridge binary; no extra args by default.
        self.assertEqual(client._acp_command, "claude-code-acp")
        self.assertEqual(client._acp_args, [])

    def test_command_env_override(self) -> None:
        with patch.dict(
            os.environ,
            {
                "HERMES_CLAUDE_CODE_ACP_COMMAND": "/opt/bin/cc-acp",
                "HERMES_CLAUDE_CODE_ACP_ARGS": "--foo --bar",
            },
            clear=False,
        ):
            client = ClaudeCodeACPClient(acp_cwd="/tmp")
        self.assertEqual(client._acp_command, "/opt/bin/cc-acp")
        self.assertEqual(client._acp_args, ["--foo", "--bar"])

    def test_explicit_command_wins_over_env(self) -> None:
        client = ClaudeCodeACPClient(
            acp_cwd="/tmp", command="explicit-bin", args=["--x"]
        )
        self.assertEqual(client._acp_command, "explicit-bin")
        self.assertEqual(client._acp_args, ["--x"])


class ClaudeCodeACPClientSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ClaudeCodeACPClient(acp_cwd="/tmp")

    def _dispatch(self, message: dict, *, cwd: str) -> dict:
        process = _FakeProcess()
        handled = self.client._handle_server_message(
            message,
            process=process,
            cwd=cwd,
            text_parts=[],
            reasoning_parts=[],
        )
        self.assertTrue(handled)
        payload = process.stdin.getvalue().strip()
        self.assertTrue(payload)
        return json.loads(payload)

    def test_request_permission_is_not_auto_allowed(self) -> None:
        response = self._dispatch(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "session/request_permission",
                "params": {},
            },
            cwd="/tmp",
        )
        outcome = (((response.get("result") or {}).get("outcome") or {}).get("outcome"))
        self.assertEqual(outcome, "cancelled")

    def test_write_text_file_reuses_write_denylist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir) / "home"
            target = home / ".ssh" / "id_rsa"
            target.parent.mkdir(parents=True, exist_ok=True)

            # The fs handler lives in the shared base (copilot_acp_client module).
            with patch("agent.copilot_acp_client.is_write_denied", return_value=True, create=True):
                response = self._dispatch(
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "fs/write_text_file",
                        "params": {
                            "path": str(target),
                            "content": "fake-private-key",
                        },
                    },
                    cwd=str(home),
                )

        self.assertIn("error", response)
        self.assertFalse(target.exists())


def _fake_popen_capture(captured):
    def _fake(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        raise FileNotFoundError("claude-code-acp not found")
    return _fake


def test_startup_error_mentions_claude_code(monkeypatch, tmp_path):
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.delenv("HERMES_HOME", raising=False)

    captured = {}
    client = ClaudeCodeACPClient(acp_cwd=str(tmp_path))

    # _run_prompt is inherited from the base class in copilot_acp_client.
    with patch("agent.copilot_acp_client.subprocess.Popen", side_effect=_fake_popen_capture(captured)):
        with pytest.raises(RuntimeError, match="Could not start Claude Code ACP command"):
            client._run_prompt("hello", timeout_seconds=1)

    assert captured["cmd"][0] == "claude-code-acp"
    assert captured["kwargs"]["env"]["HOME"]


if __name__ == "__main__":
    unittest.main()
