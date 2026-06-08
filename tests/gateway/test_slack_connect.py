"""Tests for Slack connect() non-retryable fatal error on missing credentials.

When Slack has no bot token, no app token, or slack-bolt not installed,
connect() must set a non-retryable fatal error so the gateway does not queue
it for background reconnection (#31049).
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock

from gateway.config import PlatformConfig


def _ensure_slack_mock():
    if "slack_bolt" in sys.modules and hasattr(sys.modules.get("slack_bolt"), "__file__"):
        return

    slack_bolt = MagicMock()
    slack_bolt.async_app.AsyncApp = MagicMock
    slack_bolt.adapter.socket_mode.async_handler.AsyncSocketModeHandler = MagicMock
    sys.modules.setdefault("slack_bolt", slack_bolt)
    sys.modules.setdefault("slack_bolt.async_app", MagicMock())
    sys.modules.setdefault("slack_bolt.adapter", MagicMock())
    sys.modules.setdefault("slack_bolt.adapter.socket_mode", MagicMock())
    sys.modules.setdefault("slack_bolt.adapter.socket_mode.async_handler", MagicMock())


_ensure_slack_mock()

import gateway.platforms.slack as slack_mod  # noqa: E402
from gateway.platforms.slack import SlackAdapter  # noqa: E402


class TestSlackUnconfiguredNonRetryable:
    """Verify that missing dependency/tokens sets a non-retryable fatal error."""

    def test_no_slack_bolt_sets_non_retryable_fatal(self, monkeypatch):
        """connect() with slack-bolt unavailable → non-retryable fatal error."""
        adapter = SlackAdapter(PlatformConfig(enabled=True, token="xoxb-fake"))
        monkeypatch.setattr(slack_mod, "SLACK_AVAILABLE", False)
        result = asyncio.get_event_loop().run_until_complete(adapter.connect())
        assert result is False
        assert adapter.has_fatal_error is True
        assert adapter.fatal_error_retryable is False
        assert adapter.fatal_error_code == "missing_dependency"

    def test_no_bot_token_sets_non_retryable_fatal(self, monkeypatch):
        """connect() with empty SLACK_BOT_TOKEN → non-retryable fatal error."""
        monkeypatch.setattr(slack_mod, "SLACK_AVAILABLE", True)
        adapter = SlackAdapter(PlatformConfig(enabled=True, token=""))
        monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
        result = asyncio.get_event_loop().run_until_complete(adapter.connect())
        assert result is False
        assert adapter.has_fatal_error is True
        assert adapter.fatal_error_retryable is False
        assert adapter.fatal_error_code == "missing_credentials"

    def test_no_app_token_sets_non_retryable_fatal(self, monkeypatch):
        """connect() with SLACK_BOT_TOKEN set but SLACK_APP_TOKEN missing
        → non-retryable fatal error."""
        monkeypatch.setattr(slack_mod, "SLACK_AVAILABLE", True)
        adapter = SlackAdapter(PlatformConfig(enabled=True, token="xoxb-fake"))
        monkeypatch.delenv("SLACK_APP_TOKEN", raising=False)
        result = asyncio.get_event_loop().run_until_complete(adapter.connect())
        assert result is False
        assert adapter.has_fatal_error is True
        assert adapter.fatal_error_retryable is False
        assert adapter.fatal_error_code == "missing_credentials"
