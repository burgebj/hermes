"""Tests for gateway.subprocess_env credential scrubbing."""

import os
import re

import pytest

from gateway.subprocess_env import CREDENTIAL_ENV_VARS, scrubbed_env


class TestScrubCredentialVars:
    def test_removes_credential_vars(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "secret-token")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-secret")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-secret")
        monkeypatch.setenv("MY_APP_VAR", "safe-value")

        result = scrubbed_env()

        assert "TELEGRAM_BOT_TOKEN" not in result
        assert "OPENAI_API_KEY" not in result
        assert "ANTHROPIC_API_KEY" not in result

    def test_preserves_non_credential_vars(self, monkeypatch):
        monkeypatch.setenv("MY_APP_VAR", "safe-value")

        result = scrubbed_env()

        assert result.get("MY_APP_VAR") == "safe-value"

    def test_preserves_path(self):
        result = scrubbed_env()

        assert "PATH" in result

    def test_keep_exemption_restores_scrubbed_var(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token-value")

        result = scrubbed_env(keep={"TELEGRAM_BOT_TOKEN"})

        assert result.get("TELEGRAM_BOT_TOKEN") == "bot-token-value"

    def test_keep_does_not_add_missing_vars(self):
        # Requesting keep for a var that isn't in os.environ produces no entry.
        result = scrubbed_env(keep={"SOME_KEY_THAT_DOES_NOT_EXIST"})

        assert "SOME_KEY_THAT_DOES_NOT_EXIST" not in result

    def test_no_side_effects_on_os_environ(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-secret")
        original_keys = set(os.environ.keys())

        result = scrubbed_env()
        result["INJECTED_KEY"] = "injected"

        # os.environ must be untouched
        assert set(os.environ.keys()) == original_keys
        assert "INJECTED_KEY" not in os.environ


class TestCredentialListCoversConfigKeys:
    """Verify CREDENTIAL_ENV_VARS includes every secret read in gateway/config.py."""

    def _extract_config_secrets(self) -> set[str]:
        """Parse gateway/config.py and collect env var names with secret suffixes."""
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "gateway", "config.py"
        )
        with open(config_path, encoding="utf-8") as f:
            source = f.read()

        # Match os.getenv("VAR_NAME") where VAR_NAME ends with a secret suffix
        pattern = re.compile(
            r'os\.getenv\(\s*["\']([A-Z_]+(?:KEY|TOKEN|SECRET|PASSWORD|SID|AES_KEY))["\']'
        )
        return {m.group(1) for m in pattern.finditer(source)}

    def test_credential_list_covers_config_secrets(self):
        config_secrets = self._extract_config_secrets()
        missing = config_secrets - CREDENTIAL_ENV_VARS
        assert not missing, (
            f"The following secret env vars appear in gateway/config.py but are "
            f"missing from CREDENTIAL_ENV_VARS: {sorted(missing)}"
        )
