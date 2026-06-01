"""Tests for the zulip_search_messages tool."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from tools.zulip_search_messages import zulip_search_messages


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _set_zulip_env(monkeypatch):
    """Set the Zulip env vars needed for the tool."""
    monkeypatch.setenv("ZULIP_SITE_URL", "https://test.zulipchat.com")
    monkeypatch.setenv("ZULIP_BOT_EMAIL", "bot@test.zulipchat.com")
    monkeypatch.setenv("ZULIP_API_KEY", "test-api-key")


def _make_messages(count: int = 3, start_id: int = 100):
    """Create synthetic Zulip messages for testing."""
    return [
        {
            "id": start_id + i,
            "sender_full_name": f"User {i + 1}",
            "sender_email": f"user{i + 1}@example.com",
            "content": f"Message content {i + 1}",
            "timestamp": 1700000000 + i * 60,
        }
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestZulipSearchMessages:
    """Verify the zulip_search_messages tool."""

    def test_search_by_stream_and_topic(self, monkeypatch):
        """Basic search with stream+topic narrowing returns formatted messages."""
        _set_zulip_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(3),
            "found_newest": True,
            "found_oldest": False,
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages(stream="general", topic="database")

        data = json.loads(result)
        assert data["count"] == 3
        assert data["messages"][0]["sender"] == "User 1"
        assert data["messages"][0]["id"] == 100
        assert data["messages"][0]["is_bot"] is False
        assert data["oldest_message_id"] == 100
        assert data["newest_message_id"] == 102
        assert "pagination_hint" in data

        # Verify the correct narrow was passed to the Zulip client.
        call_args = mock_client.get_messages.call_args[0][0]
        assert call_args["narrow"] == [
            ["stream", "general"],
            ["topic", "database"],
        ]

    def test_search_with_text_query(self, monkeypatch):
        """Full-text search with a query string."""
        _set_zulip_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(1),
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages(query="postgresql", stream="general")

        call_args = mock_client.get_messages.call_args[0][0]
        assert call_args["narrow"] == [
            ["stream", "general"],
            ["search", "postgresql"],
        ]

    def test_anchor_pagination(self, monkeypatch):
        """Pagination with a numeric anchor."""
        _set_zulip_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(5, start_id=50),
            "found_newest": False,
            "found_oldest": False,
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages(
                stream="general",
                topic="database",
                anchor="42",
                num_before=5,
            )

        call_args = mock_client.get_messages.call_args[0][0]
        assert call_args["anchor"] == "42"
        assert call_args["num_before"] == 5
        assert call_args["num_after"] == 0

        data = json.loads(result)
        assert data["count"] == 5
        assert data["oldest_message_id"] == 50
        assert data["newest_message_id"] == 54

    def test_no_results(self, monkeypatch):
        """Empty result set returns descriptive note."""
        _set_zulip_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": [],
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages(stream="nonexistent")

        data = json.loads(result)
        assert data["count"] == 0
        assert "No messages matched" in data.get("note", "")

    def test_api_error(self, monkeypatch):
        """Zulip API errors are returned as error JSON."""
        _set_zulip_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "error",
            "msg": "Invalid API key",
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages(stream="general")

        data = json.loads(result)
        assert "error" in data

    def test_missing_credentials(self, monkeypatch):
        """Missing credentials return a helpful error unless session context says Zulip."""
        # Don't set any env vars — simulate standalone usage with no gateway.
        monkeypatch.delenv("ZULIP_SITE_URL", raising=False)
        monkeypatch.delenv("ZULIP_BOT_EMAIL", raising=False)
        monkeypatch.delenv("ZULIP_API_KEY", raising=False)

        result = zulip_search_messages(stream="general")

        data = json.loads(result)
        assert "error" in data
        assert "credentials" in data["error"].lower()

    def test_check_fn_session_platform_zulip(self, monkeypatch):
        """When session platform is 'zulip', the tool should be available even
        without explicit env vars (gateway passes config internally)."""
        monkeypatch.setenv("HERMES_SESSION_PLATFORM", "zulip")

        from tools.zulip_search_messages import _check_zulip_search_requirements
        assert _check_zulip_search_requirements() is True

    def test_check_fn_other_platform_no_creds(self, monkeypatch):
        """On non-Zulip platforms without env vars, tool is unavailable."""
        monkeypatch.setenv("HERMES_SESSION_PLATFORM", "telegram")
        monkeypatch.delenv("ZULIP_SITE_URL", raising=False)
        monkeypatch.delenv("ZULIP_BOT_EMAIL", raising=False)
        monkeypatch.delenv("ZULIP_API_KEY", raising=False)

        # When gateway not running and no creds, tool is unavailable
        from tools.zulip_search_messages import _check_zulip_search_requirements
        # The check will try is_gateway_running() which may be False or raise
        # Either way, with no creds it should be False
        result = _check_zulip_search_requirements()
        # On non-Zulip platforms without creds, should be False
        assert result is False

    def test_bot_messages_flagged(self, monkeypatch):
        """Messages from the bot itself are flagged with is_bot=True."""
        _set_zulip_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": [
                {
                    "id": 1,
                    "sender_full_name": "Hermes Bot",
                    "sender_email": "bot@test.zulipchat.com",
                    "content": "I can help with that",
                    "timestamp": 1700000000,
                },
            ],
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages(stream="general")

        data = json.loads(result)
        assert data["messages"][0]["is_bot"] is True

    def test_default_parameters(self, monkeypatch):
        """Default anchor='newest', num_before=20, num_after=0."""
        _set_zulip_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": [],
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            zulip_search_messages()

        call_args = mock_client.get_messages.call_args[0][0]
        assert call_args["anchor"] == "newest"
        assert call_args["num_before"] == 20
        assert call_args["num_after"] == 0

    def test_num_after_for_surrounding_context(self, monkeypatch):
        """num_after > 0 fetches messages after the anchor for context."""
        _set_zulip_env(monkeypatch)

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(10),
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            zulip_search_messages(anchor="500", num_before=5, num_after=5)

        call_args = mock_client.get_messages.call_args[0][0]
        assert call_args["anchor"] == "500"
        assert call_args["num_before"] == 5
        assert call_args["num_after"] == 5


class TestZulipSearchSessionRestriction:
    """Verify that searches from Zulip sessions are restricted to the current conversation.

    This prevents a user in a private DM from asking the bot to exfiltrate
    messages from streams or other DMs the bot is subscribed to.
    """

    def test_stream_session_restricts_to_current_topic(self, monkeypatch):
        """When in a stream session, search is restricted to that stream+topic."""
        _set_zulip_env(monkeypatch)
        monkeypatch.setenv("HERMES_SESSION_PLATFORM", "zulip")
        monkeypatch.setenv("HERMES_SESSION_CHAT_ID", "123:database")
        monkeypatch.setenv("HERMES_SESSION_CHAT_NAME", "engineering")

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(2),
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            # Agent tries to search a different stream — should be overridden.
            result = zulip_search_messages(stream="general", topic="other")

        data = json.loads(result)
        assert data["count"] == 2

        call_args = mock_client.get_messages.call_args[0][0]
        # Should be restricted to current session's stream+topic, not agent's params.
        assert call_args["narrow"] == [
            ["stream", "engineering"],
            ["topic", "database"],
        ]

    def test_dm_session_restricts_to_current_dm(self, monkeypatch):
        """When in a DM session, search is restricted to that DM."""
        _set_zulip_env(monkeypatch)
        monkeypatch.setenv("HERMES_SESSION_PLATFORM", "zulip")
        monkeypatch.setenv("HERMES_SESSION_CHAT_ID", "dm:alice@example.com")
        monkeypatch.setenv("HERMES_SESSION_CHAT_NAME", "alice@example.com")

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(1),
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            # Agent tries to search a stream — should be overridden to DM.
            result = zulip_search_messages(stream="general", query="hello")

        data = json.loads(result)
        assert data["count"] == 1

        call_args = mock_client.get_messages.call_args[0][0]
        assert call_args["narrow"] == [
            ["pm-with", "alice@example.com"],
            ["search", "hello"],
        ]

    def test_group_dm_session_restricts_to_current_group(self, monkeypatch):
        """When in a group DM session, search is restricted to that group DM."""
        _set_zulip_env(monkeypatch)
        monkeypatch.setenv("HERMES_SESSION_PLATFORM", "zulip")
        monkeypatch.setenv("HERMES_SESSION_CHAT_ID", "group_dm:alice@example.com,bob@example.com")
        monkeypatch.setenv("HERMES_SESSION_CHAT_NAME", "alice@example.com, bob@example.com")

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(1),
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages()

        call_args = mock_client.get_messages.call_args[0][0]
        assert call_args["narrow"] == [
            ["pm-with", "alice@example.com,bob@example.com"],
        ]

    def test_non_zulip_session_allows_full_search(self, monkeypatch):
        """When called from CLI (no Zulip session), agent's params are respected."""
        _set_zulip_env(monkeypatch)
        # No HERMES_SESSION_PLATFORM set — simulates CLI usage.

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(1),
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages(stream="general", topic="database")

        data = json.loads(result)
        assert data["count"] == 1

        call_args = mock_client.get_messages.call_args[0][0]
        assert call_args["narrow"] == [
            ["stream", "general"],
            ["topic", "database"],
        ]

    def test_query_sanitization_strips_scope_operators(self, monkeypatch):
        """stream: and pm-with: operators are stripped in restricted sessions."""
        _set_zulip_env(monkeypatch)
        monkeypatch.setenv("HERMES_SESSION_PLATFORM", "zulip")
        monkeypatch.setenv("HERMES_SESSION_CHAT_ID", "123:database")
        monkeypatch.setenv("HERMES_SESSION_CHAT_NAME", "engineering")

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(1),
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages(
                query="stream:general pm-with:alice@example.com postgresql"
            )

        call_args = mock_client.get_messages.call_args[0][0]
        # Should have session narrow + sanitized query (scope operators removed).
        assert call_args["narrow"] == [
            ["stream", "engineering"],
            ["topic", "database"],
            ["search", "postgresql"],
        ]

    def test_query_sanitization_all_operators_removed(self, monkeypatch):
        """If query contains only scope operators, no search narrow is added."""
        _set_zulip_env(monkeypatch)
        monkeypatch.setenv("HERMES_SESSION_PLATFORM", "zulip")
        monkeypatch.setenv("HERMES_SESSION_CHAT_ID", "123:database")
        monkeypatch.setenv("HERMES_SESSION_CHAT_NAME", "engineering")

        mock_client = MagicMock()
        mock_client.get_messages.return_value = {
            "result": "success",
            "messages": _make_messages(1),
            "found_newest": True,
            "found_oldest": True,
        }

        with patch("zulip.Client", return_value=mock_client):
            result = zulip_search_messages(query="stream:general pm-with:bob@example.com")

        call_args = mock_client.get_messages.call_args[0][0]
        # Only session narrow — no search narrow since query was fully sanitized.
        assert call_args["narrow"] == [
            ["stream", "engineering"],
            ["topic", "database"],
        ]
