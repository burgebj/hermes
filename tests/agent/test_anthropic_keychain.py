"""Tests for Bug #12905 fixes in agent/anthropic_adapter.py — macOS Keychain support."""

import json
import hashlib
import platform
from unittest.mock import patch, MagicMock

import pytest

from agent.anthropic_adapter import (
    _read_claude_code_credentials_from_keychain,
    read_claude_code_credentials,
)


class TestReadClaudeCodeCredentialsFromKeychain:
    """Bug 4: macOS Keychain support for Claude Code >=2.1.114."""

    def test_returns_none_on_linux(self):
        """Keychain reading is Darwin-only; must return None on other platforms."""
        with patch("agent.anthropic_adapter.platform.system", return_value="Linux"):
            assert _read_claude_code_credentials_from_keychain() is None

    def test_returns_none_on_windows(self):
        with patch("agent.anthropic_adapter.platform.system", return_value="Windows"):
            assert _read_claude_code_credentials_from_keychain() is None

    def test_returns_none_when_security_command_not_found(self):
        """OSError from missing security binary must be handled gracefully."""
        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run",
                   side_effect=OSError("security not found")):
            assert _read_claude_code_credentials_from_keychain() is None

    def test_returns_none_on_nonzero_exit_code(self):
        """security returns non-zero when the Keychain entry doesn't exist."""
        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            assert _read_claude_code_credentials_from_keychain() is None

    def test_returns_none_for_empty_stdout(self):
        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            assert _read_claude_code_credentials_from_keychain() is None

    def test_returns_none_for_non_json_payload(self):
        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="not valid json", stderr="")
            assert _read_claude_code_credentials_from_keychain() is None

    def test_returns_none_when_password_field_is_missing_claude_ai_oauth(self):
        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"someOtherService": {"accessToken": "tok"}}),
                stderr="",
            )
            assert _read_claude_code_credentials_from_keychain() is None

    def test_returns_none_when_access_token_is_empty(self):
        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"claudeAiOauth": {"accessToken": "", "refreshToken": "x"}}),
                stderr="",
            )
            assert _read_claude_code_credentials_from_keychain() is None

    def test_parses_valid_keychain_entry(self):
        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "claudeAiOauth": {
                        "accessToken": "kc-access-token-abc",
                        "refreshToken": "kc-refresh-token-xyz",
                        "expiresAt": 9999999999999,
                    }
                }),
                stderr="",
            )
            creds = _read_claude_code_credentials_from_keychain()
            assert creds is not None
            assert creds["accessToken"] == "kc-access-token-abc"
            assert creds["refreshToken"] == "kc-refresh-token-xyz"
            assert creds["expiresAt"] == 9999999999999
            assert creds["source"] == "macos_keychain"

    def test_reads_claude_code_home_scoped_keychain_entry(self, tmp_path, monkeypatch):
        """Claude Code stores alternate HOME auth under a service suffixed by sha256(HOME)."""
        expected_suffix = hashlib.sha256(str(tmp_path).encode()).hexdigest()[:8]
        monkeypatch.setenv("HERMES_CLAUDE_CODE_HOME", str(tmp_path))
        monkeypatch.setenv("USER", "beltsazar")

        def fake_run(cmd, **kwargs):
            assert f"Claude Code-credentials-{expected_suffix}" in cmd
            assert "beltsazar" in cmd
            return MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "claudeAiOauth": {
                        "accessToken": "home-scoped-access",
                        "refreshToken": "home-scoped-refresh",
                        "expiresAt": 9999999999999,
                    }
                }),
                stderr="",
            )

        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run", side_effect=fake_run):
            creds = _read_claude_code_credentials_from_keychain()

        assert creds is not None
        assert creds["accessToken"] == "home-scoped-access"
        assert creds["source"] == "macos_keychain"
        assert creds["_keychain_service"] == f"Claude Code-credentials-{expected_suffix}"


class TestReadClaudeCodeCredentialsPriority:
    """Bug 4: Keychain must be checked before the JSON file."""

    def test_keychain_takes_priority_over_json_file(self, tmp_path, monkeypatch):
        """When both Keychain and JSON file have credentials, Keychain wins."""
        # Set up JSON file with "older" token
        json_cred_file = tmp_path / ".claude" / ".credentials.json"
        json_cred_file.parent.mkdir(parents=True)
        json_cred_file.write_text(json.dumps({
            "claudeAiOauth": {
                "accessToken": "json-token",
                "refreshToken": "json-refresh",
                "expiresAt": 9999999999999,
            }
        }))
        monkeypatch.setattr("agent.anthropic_adapter.Path.home", lambda: tmp_path)
        monkeypatch.setattr("agent.anthropic_adapter.os.path.expanduser", lambda path: str(tmp_path) if path == "~" else path)

        # Mock Keychain to return a "newer" token
        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "claudeAiOauth": {
                        "accessToken": "keychain-token",
                        "refreshToken": "keychain-refresh",
                        "expiresAt": 9999999999999,
                    }
                }),
                stderr="",
            )
            creds = read_claude_code_credentials()

        # Keychain token should be returned, not JSON file token
        assert creds is not None
        assert creds["accessToken"] == "keychain-token"
        assert creds["source"] == "macos_keychain"

    def test_falls_back_to_json_when_keychain_returns_none(self, tmp_path, monkeypatch):
        """When Keychain has no entry, JSON file is used as fallback."""
        json_cred_file = tmp_path / ".claude" / ".credentials.json"
        json_cred_file.parent.mkdir(parents=True)
        json_cred_file.write_text(json.dumps({
            "claudeAiOauth": {
                "accessToken": "json-fallback-token",
                "refreshToken": "json-refresh",
                "expiresAt": 9999999999999,
            }
        }))
        monkeypatch.setattr("agent.anthropic_adapter.Path.home", lambda: tmp_path)

        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            # Simulate Keychain entry not found
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            creds = read_claude_code_credentials()

        assert creds is not None
        assert creds["accessToken"] == "json-fallback-token"
        assert creds["source"] == "claude_code_credentials_file"

    def test_uses_claude_code_home_for_json_fallback(self, tmp_path, monkeypatch):
        """HERMES_CLAUDE_CODE_HOME scopes both Keychain and JSON credential lookup."""
        json_cred_file = tmp_path / ".claude" / ".credentials.json"
        json_cred_file.parent.mkdir(parents=True)
        json_cred_file.write_text(json.dumps({
            "claudeAiOauth": {
                "accessToken": "home-json-token",
                "refreshToken": "home-json-refresh",
                "expiresAt": 9999999999999,
            }
        }))
        monkeypatch.setenv("HERMES_CLAUDE_CODE_HOME", str(tmp_path))

        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            creds = read_claude_code_credentials()

        assert creds is not None
        assert creds["accessToken"] == "home-json-token"
        assert creds["source"] == "claude_code_credentials_file"

    def test_returns_none_when_neither_keychain_nor_json_has_creds(self, tmp_path, monkeypatch):
        """No credentials anywhere — must return None cleanly."""
        monkeypatch.setattr("agent.anthropic_adapter.Path.home", lambda: tmp_path)

        with patch("agent.anthropic_adapter.platform.system", return_value="Darwin"), \
             patch("agent.anthropic_adapter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            creds = read_claude_code_credentials()

        assert creds is None
