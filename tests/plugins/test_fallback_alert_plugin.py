"""Tests for the bundled observability/fallback-alert plugin."""
from __future__ import annotations

import importlib
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_DIR = REPO_ROOT / "plugins" / "observability" / "fallback-alert"


def _load_plugin():
    """Load the plugin __init__.py directly — the hyphen in the directory
    name prevents a regular ``import plugins.observability.fallback-alert``."""
    if "hermes_plugins_under_test" not in sys.modules:
        ns = types.ModuleType("hermes_plugins_under_test")
        ns.__path__ = []
        sys.modules["hermes_plugins_under_test"] = ns
    mod_name = "hermes_plugins_under_test.fallback_alert"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(
        mod_name,
        PLUGIN_DIR / "__init__.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def plugin(monkeypatch):
    """Fresh module + cleared state + cleared env vars for each test."""
    for var in (
        "FALLBACK_ALERT_TELEGRAM_BOT_TOKEN",
        "FALLBACK_ALERT_TELEGRAM_CHAT_ID",
        "FALLBACK_ALERT_THROTTLE_SECONDS",
        "FALLBACK_ALERT_DEBUG",
    ):
        monkeypatch.delenv(var, raising=False)
    mod = _load_plugin()
    mod._reset_state_for_tests()
    return mod


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

class TestManifest:
    def test_directory_layout(self):
        assert PLUGIN_DIR.is_dir()
        assert (PLUGIN_DIR / "plugin.yaml").exists()
        assert (PLUGIN_DIR / "__init__.py").exists()

    def test_manifest_fields(self):
        data = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text())
        assert data["name"] == "fallback-alert"
        assert data["version"]
        assert data["hooks"] == ["post_api_request"]
        assert set(data["requires_env"]) == {
            "FALLBACK_ALERT_TELEGRAM_BOT_TOKEN",
            "FALLBACK_ALERT_TELEGRAM_CHAT_ID",
        }


# ---------------------------------------------------------------------------
# Hook behaviour
# ---------------------------------------------------------------------------

class TestHookBehaviour:
    def test_noop_when_credentials_missing(self, plugin):
        """No Telegram env vars => hook is silent, no _send_telegram call."""
        with patch.object(plugin, "_send_telegram") as sender:
            plugin.on_post_api_request(
                session_id="s1", provider="anthropic", model="claude-haiku-4-5-20251001"
            )
            sender.assert_not_called()

    def test_first_call_records_primary_no_alert(self, plugin, monkeypatch):
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_BOT_TOKEN", "bot:tok")
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_CHAT_ID", "1234")
        with patch.object(plugin, "_send_telegram") as sender:
            plugin.on_post_api_request(
                session_id="s1", provider="anthropic", model="claude-haiku-4-5-20251001"
            )
            sender.assert_not_called()
        assert plugin._PRIMARY_BY_SESSION["s1"] == (
            "anthropic", "claude-haiku-4-5-20251001",
        )

    def test_same_provider_model_no_alert(self, plugin, monkeypatch):
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_BOT_TOKEN", "bot:tok")
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_CHAT_ID", "1234")
        with patch.object(plugin, "_send_telegram") as sender:
            for _ in range(3):
                plugin.on_post_api_request(
                    session_id="s1", provider="anthropic", model="claude-haiku-4-5-20251001"
                )
            sender.assert_not_called()

    def test_different_provider_triggers_alert(self, plugin, monkeypatch):
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_BOT_TOKEN", "bot:tok")
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_CHAT_ID", "1234")
        with patch.object(plugin, "_send_telegram", return_value=True) as sender:
            # First call sets primary.
            plugin.on_post_api_request(
                session_id="s1", provider="anthropic", model="claude-haiku-4-5-20251001"
            )
            # Second call: different provider — fallback active.
            plugin.on_post_api_request(
                session_id="s1", provider="openrouter",
                model="anthropic/claude-haiku-4-5",
                platform="telegram", finish_reason="tool_use",
            )
            assert sender.call_count == 1
            args, _kwargs = sender.call_args
            token, chat, text = args
            assert token == "bot:tok"
            assert chat == "1234"
            assert "anthropic/claude-haiku-4-5-20251001" in text
            assert "openrouter/anthropic/claude-haiku-4-5" in text
            assert "tool_use" in text
            assert "telegram" in text

    def test_throttle_suppresses_repeated_alerts(self, plugin, monkeypatch):
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_BOT_TOKEN", "bot:tok")
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_CHAT_ID", "1234")
        monkeypatch.setenv("FALLBACK_ALERT_THROTTLE_SECONDS", "300")
        with patch.object(plugin, "_send_telegram", return_value=True) as sender:
            plugin.on_post_api_request(
                session_id="s1", provider="anthropic", model="claude-haiku-4-5-20251001"
            )
            for _ in range(5):
                plugin.on_post_api_request(
                    session_id="s1", provider="openrouter",
                    model="anthropic/claude-haiku-4-5",
                )
            assert sender.call_count == 1

    def test_hook_swallows_exceptions(self, plugin, monkeypatch):
        """Any unexpected error must NOT propagate (would crash Hermes loop)."""
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_BOT_TOKEN", "bot:tok")
        monkeypatch.setenv("FALLBACK_ALERT_TELEGRAM_CHAT_ID", "1234")
        with patch.object(
            plugin, "_send_telegram", side_effect=RuntimeError("boom")
        ):
            plugin.on_post_api_request(
                session_id="s1", provider="anthropic", model="claude-haiku-4-5-20251001"
            )
            # Trigger fallback — _send_telegram raises but hook must not.
            plugin.on_post_api_request(
                session_id="s1", provider="openrouter",
                model="anthropic/claude-haiku-4-5",
            )

    def test_register_wires_post_api_request(self, plugin):
        seen: list[tuple[str, callable]] = []

        class Ctx:
            def register_hook(self, name, cb):
                seen.append((name, cb))

        plugin.register(Ctx())
        assert seen == [("post_api_request", plugin.on_post_api_request)]
