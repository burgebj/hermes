"""Tests for tools/session_search_tool.py — helper functions and search dispatcher."""

import asyncio
import json
import time
import pytest

from tools.session_search_tool import (
    _format_timestamp,
    _format_conversation,
    _truncate_around_matches,
    _get_session_search_max_concurrency,
    _list_recent_sessions,
    _HIDDEN_SESSION_SOURCES,
    MAX_SESSION_CHARS,
    SESSION_SEARCH_SCHEMA,
)


# =========================================================================
# Tool schema guidance
# =========================================================================

class TestHiddenSessionSources:
    """Verify the _HIDDEN_SESSION_SOURCES constant used for third-party isolation."""

    def test_tool_source_is_hidden(self):
        assert "tool" in _HIDDEN_SESSION_SOURCES

    def test_standard_sources_not_hidden(self):
        for src in ("cli", "telegram", "discord", "slack", "cron"):
            assert src not in _HIDDEN_SESSION_SOURCES


class TestSessionSearchSchema:
    def test_keeps_cross_session_recall_guidance_without_current_session_nudge(self):
        description = SESSION_SEARCH_SCHEMA["description"]
        assert "past conversations" in description
        assert "recent turns of the current session" not in description


# =========================================================================
# _format_timestamp
# =========================================================================

class TestFormatTimestamp:
    def test_unix_float(self):
        ts = 1700000000.0  # Nov 14, 2023
        result = _format_timestamp(ts)
        assert "2023" in result or "November" in result

    def test_unix_int(self):
        result = _format_timestamp(1700000000)
        assert isinstance(result, str)
        assert len(result) > 5

    def test_iso_string(self):
        result = _format_timestamp("2024-01-15T10:30:00")
        assert isinstance(result, str)

    def test_none_returns_unknown(self):
        assert _format_timestamp(None) == "unknown"

    def test_numeric_string(self):
        result = _format_timestamp("1700000000.0")
        assert isinstance(result, str)
        assert "unknown" not in result.lower()


# =========================================================================
# _format_conversation
# =========================================================================

class TestFormatConversation:
    def test_basic_messages(self):
        msgs = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        result = _format_conversation(msgs)
        assert "[USER]: Hello" in result
        assert "[ASSISTANT]: Hi there!" in result

    def test_tool_message(self):
        msgs = [
            {"role": "tool", "content": "search results", "tool_name": "web_search"},
        ]
        result = _format_conversation(msgs)
        assert "[TOOL:web_search]" in result

    def test_long_tool_output_truncated(self):
        msgs = [
            {"role": "tool", "content": "x" * 1000, "tool_name": "terminal"},
        ]
        result = _format_conversation(msgs)
        assert "[truncated]" in result

    def test_assistant_with_tool_calls(self):
        msgs = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "web_search"}},
                    {"function": {"name": "terminal"}},
                ],
            },
        ]
        result = _format_conversation(msgs)
        assert "web_search" in result
        assert "terminal" in result

    def test_empty_messages(self):
        result = _format_conversation([])
        assert result == ""


# =========================================================================
# _truncate_around_matches
# =========================================================================

class TestTruncateAroundMatches:
    def test_short_text_unchanged(self):
        text = "Short text about docker"
        result = _truncate_around_matches(text, "docker")
        assert result == text

    def test_long_text_truncated(self):
        # Create text longer than MAX_SESSION_CHARS with query term in middle
        padding = "x" * (MAX_SESSION_CHARS + 5000)
        text = padding + " KEYWORD_HERE " + padding
        result = _truncate_around_matches(text, "KEYWORD_HERE")
        assert len(result) <= MAX_SESSION_CHARS + 100  # +100 for prefix/suffix markers
        assert "KEYWORD_HERE" in result

    def test_truncation_adds_markers(self):
        text = "a" * 50000 + " target " + "b" * (MAX_SESSION_CHARS + 5000)
        result = _truncate_around_matches(text, "target")
        assert "truncated" in result.lower()

    def test_no_match_takes_from_start(self):
        text = "x" * (MAX_SESSION_CHARS + 5000)
        result = _truncate_around_matches(text, "nonexistent")
        # Should take from the beginning
        assert result.startswith("x")

    def test_match_at_beginning(self):
        text = "KEYWORD " + "x" * (MAX_SESSION_CHARS + 5000)
        result = _truncate_around_matches(text, "KEYWORD")
        assert "KEYWORD" in result

    def test_multiword_phrase_match_beats_individual_term(self):
        """Full phrase deep in text should be found even when a single term
        appears much earlier in boilerplate."""
        boilerplate = "The project setup is complex. " * 500  # ~15K, has 'project' early
        filler = "x" * (MAX_SESSION_CHARS + 20000)
        target = "We reviewed the keystone project roadmap in detail."
        text = boilerplate + filler + target + filler
        result = _truncate_around_matches(text, "keystone project")
        assert "keystone project" in result.lower()

    def test_multiword_proximity_cooccurrence(self):
        """When exact phrase is absent, terms co-occurring within proximity
        should be preferred over a lone early term."""
        early = "project " + "a" * (MAX_SESSION_CHARS + 20000)
        # Place 'keystone' and 'project' near each other (but not as exact phrase)
        cooccur = "this keystone initiative for the project was pivotal"
        tail = "b" * (MAX_SESSION_CHARS + 20000)
        text = early + cooccur + tail
        result = _truncate_around_matches(text, "keystone project")
        assert "keystone" in result.lower()
        assert "project" in result.lower()

    def test_multiword_window_maximises_coverage(self):
        """Sliding window should capture as many match clusters as possible."""
        # Place two phrase matches: one at ~50K, one at ~60K, both should fit
        pre = "z" * 50000
        match1 = " alpha beta "
        gap = "z" * 10000
        match2 = " alpha beta "
        post = "z" * (MAX_SESSION_CHARS + 40000)
        text = pre + match1 + gap + match2 + post
        result = _truncate_around_matches(text, "alpha beta")
        assert result.lower().count("alpha beta") == 2


class TestSessionSearchConcurrency:
    def test_defaults_to_three(self):
        assert _get_session_search_max_concurrency() == 3

    def test_reads_and_clamps_configured_value(self, monkeypatch):
        monkeypatch.setattr(
            "hermes_cli.config.load_config",
            lambda: {"auxiliary": {"session_search": {"max_concurrency": 9}}},
        )
        assert _get_session_search_max_concurrency() == 5

    def test_session_search_respects_configured_concurrency_limit(self, monkeypatch):
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        monkeypatch.setattr(
            "hermes_cli.config.load_config",
            lambda: {"auxiliary": {"session_search": {"max_concurrency": 1}}},
        )

        max_seen = {"value": 0}
        active = {"value": 0}

        async def fake_summarize(_text, _query, _meta):
            active["value"] += 1
            max_seen["value"] = max(max_seen["value"], active["value"])
            await asyncio.sleep(0.01)
            active["value"] -= 1
            return "summary"

        monkeypatch.setattr("tools.session_search_tool._summarize_session", fake_summarize)
        monkeypatch.setattr("model_tools._run_async", lambda coro: asyncio.run(coro))

        mock_db = MagicMock()
        mock_db.search_messages.return_value = [
            {"session_id": "s1", "source": "cli", "session_started": 1709500000, "model": "test"},
            {"session_id": "s2", "source": "cli", "session_started": 1709500001, "model": "test"},
            {"session_id": "s3", "source": "cli", "session_started": 1709500002, "model": "test"},
        ]
        mock_db.get_session.side_effect = lambda sid: {
            "id": sid,
            "parent_session_id": None,
            "source": "cli",
            "started_at": 1709500000,
        }
        mock_db.get_messages_as_conversation.side_effect = lambda sid: [
            {"role": "user", "content": f"message from {sid}"},
            {"role": "assistant", "content": "response"},
        ]

        result = json.loads(session_search(query="message", db=mock_db, limit=3))

        assert result["success"] is True
        assert result["count"] == 3
        assert max_seen["value"] == 1


class TestRecentSessionListing:
    def test_recent_mode_requests_last_active_ordering(self):
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_db.list_sessions_rich.return_value = []

        result = json.loads(_list_recent_sessions(mock_db, limit=5))

        assert result["success"] is True
        mock_db.list_sessions_rich.assert_called_once_with(
            limit=10,
            exclude_sources=["tool"],
            order_by_last_active=True,
        )

    def test_current_child_session_excludes_root_lineage_even_when_child_id_is_longer(self):
        from unittest.mock import MagicMock

        mock_db = MagicMock()
        mock_db.list_sessions_rich.return_value = [
            {
                "id": "root",
                "title": "Current conversation",
                "source": "cli",
                "started_at": 1709500000,
                "last_active": 1709500100,
                "message_count": 4,
                "preview": "current root",
                "parent_session_id": None,
            },
            {
                "id": "other_session",
                "title": "Other conversation",
                "source": "cli",
                "started_at": 1709400000,
                "last_active": 1709400100,
                "message_count": 3,
                "preview": "other root",
                "parent_session_id": None,
            },
        ]

        def _get_session(session_id):
            if session_id == "child_session_id_that_is_definitely_longer":
                return {"parent_session_id": "root"}
            if session_id == "root":
                return {"parent_session_id": None}
            return None

        mock_db.get_session.side_effect = _get_session

        result = json.loads(_list_recent_sessions(
            mock_db,
            limit=5,
            current_session_id="child_session_id_that_is_definitely_longer",
        ))

        assert result["success"] is True
        assert [item["session_id"] for item in result["results"]] == ["other_session"]
        assert all(item["session_id"] != "root" for item in result["results"])


# =========================================================================
# session_search (dispatcher)
# =========================================================================

class TestSessionSearch:
    def test_no_db_lazily_opens_default_session_db(self, monkeypatch):
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        mock_db.search_messages.return_value = []

        class FakeSessionDB:
            def __new__(cls):
                return mock_db

        import types
        import sys

        fake_state = types.ModuleType("hermes_state")
        fake_state.SessionDB = FakeSessionDB
        monkeypatch.setitem(sys.modules, "hermes_state", fake_state)

        result = json.loads(session_search(query="test"))
        assert result["success"] is True
        mock_db.search_messages.assert_called_once()

    def test_empty_query_returns_error(self):
        from tools.session_search_tool import session_search
        mock_db = object()
        result = json.loads(session_search(query="", db=mock_db))
        assert result["success"] is False

    def test_whitespace_query_returns_error(self):
        from tools.session_search_tool import session_search
        mock_db = object()
        result = json.loads(session_search(query="   ", db=mock_db))
        assert result["success"] is False

    def test_current_session_excluded(self):
        """session_search should never return the current session."""
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        current_sid = "20260304_120000_abc123"

        # Simulate FTS5 returning matches only from the current session
        mock_db.search_messages.return_value = [
            {"session_id": current_sid, "content": "test match", "source": "cli",
             "session_started": 1709500000, "model": "test"},
        ]
        mock_db.get_session.return_value = {"parent_session_id": None}

        result = json.loads(session_search(
            query="test", db=mock_db, current_session_id=current_sid,
        ))
        assert result["success"] is True
        assert result["count"] == 0
        assert result["results"] == []

    def test_current_session_excluded_keeps_others(self):
        """Other sessions should still be returned when current is excluded."""
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        current_sid = "20260304_120000_abc123"
        other_sid = "20260303_100000_def456"

        mock_db.search_messages.return_value = [
            {"session_id": current_sid, "content": "match 1", "source": "cli",
             "session_started": 1709500000, "model": "test"},
            {"session_id": other_sid, "content": "match 2", "source": "telegram",
             "session_started": 1709400000, "model": "test"},
        ]
        mock_db.get_session.return_value = {"parent_session_id": None}
        mock_db.get_messages_as_conversation.return_value = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]

        # Mock async_call_llm to raise RuntimeError → summarizer returns None
        from unittest.mock import AsyncMock, patch as _patch
        with _patch("tools.session_search_tool.async_call_llm",
                     new_callable=AsyncMock,
                     side_effect=RuntimeError("no provider")):
            result = json.loads(session_search(
                query="test", db=mock_db, current_session_id=current_sid,
            ))

        assert result["success"] is True
        # Current session should be skipped, only other_sid should appear
        assert result["sessions_searched"] == 1
        assert current_sid not in [r.get("session_id") for r in result.get("results", [])]

    def test_current_child_session_excludes_parent_lineage(self):
        """Compression/delegation parents should be excluded for the active child session."""
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        mock_db.search_messages.return_value = [
            {"session_id": "parent_sid", "content": "match", "source": "cli",
             "session_started": 1709500000, "model": "test"},
        ]

        def _get_session(session_id):
            if session_id == "child_sid":
                return {"parent_session_id": "parent_sid"}
            if session_id == "parent_sid":
                return {"parent_session_id": None}
            return None

        mock_db.get_session.side_effect = _get_session

        result = json.loads(session_search(
            query="test", db=mock_db, current_session_id="child_sid",
        ))

        assert result["success"] is True
        assert result["count"] == 0
        assert result["results"] == []
        assert result["sessions_searched"] == 0

    def test_limit_none_coerced_to_default(self):
        """Model sends limit=null → should fall back to 3, not TypeError."""
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        mock_db.search_messages.return_value = []

        result = json.loads(session_search(
            query="test", db=mock_db, limit=None,
        ))
        assert result["success"] is True

    def test_limit_type_object_coerced_to_default(self):
        """Model sends limit as a type object → should fall back to 3, not TypeError."""
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        mock_db.search_messages.return_value = []

        result = json.loads(session_search(
            query="test", db=mock_db, limit=int,
        ))
        assert result["success"] is True

    def test_limit_string_coerced(self):
        """Model sends limit as string '2' → should coerce to int."""
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        mock_db.search_messages.return_value = []

        result = json.loads(session_search(
            query="test", db=mock_db, limit="2",
        ))
        assert result["success"] is True

    def test_limit_clamped_to_range(self):
        """Negative or zero limit should be clamped to 1."""
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        mock_db.search_messages.return_value = []

        result = json.loads(session_search(
            query="test", db=mock_db, limit=-5,
        ))
        assert result["success"] is True

        result = json.loads(session_search(
            query="test", db=mock_db, limit=0,
        ))
        assert result["success"] is True

    def test_current_root_session_excludes_child_lineage(self):
        """Delegation child hits should be excluded when they resolve to the current root session."""
        from unittest.mock import MagicMock
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        mock_db.search_messages.return_value = [
            {"session_id": "child_sid", "content": "match", "source": "cli",
             "session_started": 1709500000, "model": "test"},
        ]

        def _get_session(session_id):
            if session_id == "root_sid":
                return {"parent_session_id": None}
            if session_id == "child_sid":
                return {"parent_session_id": "root_sid"}
            return None

        mock_db.get_session.side_effect = _get_session

        result = json.loads(session_search(
            query="test", db=mock_db, current_session_id="root_sid",
        ))

        assert result["success"] is True
        assert result["count"] == 0
        assert result["results"] == []
        assert result["sessions_searched"] == 0

    def test_source_from_resolved_parent_not_fts5_child(self):
        """source in output must reflect the resolved parent session, not the child that matched FTS5.

        Regression test for #15909: when a delegation child session (source='telegram')
        resolves to a parent (source='api_server'), the result entry must report
        'api_server', not 'telegram'.
        """
        from unittest.mock import MagicMock, AsyncMock, patch as _patch
        from tools.session_search_tool import session_search

        mock_db = MagicMock()
        # FTS5 hit is in the child delegation session which carries source='telegram'
        mock_db.search_messages.return_value = [
            {
                "session_id": "child_sid",
                "content": "hello world",
                "source": "telegram",       # child session source — wrong value to surface
                "session_started": 1709400000,
                "model": "gpt-4o-mini",
            },
        ]

        def _get_session(session_id):
            if session_id == "child_sid":
                return {
                    "id": "child_sid",
                    "parent_session_id": "parent_sid",
                    "source": "telegram",
                    "started_at": 1709400000,
                    "model": "gpt-4o-mini",
                }
            if session_id == "parent_sid":
                return {
                    "id": "parent_sid",
                    "parent_session_id": None,
                    "source": "api_server",  # correct parent source
                    "started_at": 1709300000,
                    "model": "gpt-4o-mini",
                }
            return None

        mock_db.get_session.side_effect = _get_session
        mock_db.get_messages_as_conversation.return_value = [
            {"role": "user", "content": "hello world"},
            {"role": "assistant", "content": "hi there"},
        ]

        with _patch(
            "tools.session_search_tool.async_call_llm",
            new_callable=AsyncMock,
            side_effect=RuntimeError("no provider"),
        ):
            result = json.loads(session_search(query="hello world", db=mock_db))

        assert result["success"] is True
        assert result["count"] == 1
        entry = result["results"][0]
        assert entry["session_id"] == "parent_sid", "should report resolved parent session ID"
        assert entry["source"] == "api_server", (
            f"source should be parent's 'api_server', got {entry['source']!r}"
        )


# =========================================================================
# get_messages_window — windowed message loading (#24280, #16671)
# =========================================================================

class TestGetMessagesWindow:
    """Verify SessionDB.get_messages_window() loads only messages near
    match positions, not the full conversation."""

    def test_window_limits_output_for_large_session(self):
        """100-message session: a window of size 3 around 1 match should
        return ≤7 messages (1 match + 3 before + 3 after), not all 100."""
        from hermes_state import SessionDB

        db = SessionDB()
        sid = "test_window_large"
        db.create_session(sid, source="cli")

        # Insert 100 messages with predictable content
        with db._lock:
            for i in range(100):
                db._conn.execute(
                    """INSERT INTO messages
                       (session_id, role, content, timestamp)
                       VALUES (?, ?, ?, ?)""",
                    (sid, "user", f"message number {i}", float(100_000_000 + i * 10)),
                )

        # Pick message #50 as the match
        with db._lock:
            match_row = db._conn.execute(
                "SELECT id FROM messages WHERE session_id = ? AND content = ?",
                (sid, "message number 50"),
            ).fetchone()
        match_id = match_row["id"]

        # Window size 3 → expect at most 1 + 3 + 3 = 7 messages
        result = db.get_messages_window(sid, [match_id], window_size=3)

        assert 3 <= len(result) <= 7, (
            f"Expected 3-7 messages with window_size=3, got {len(result)}"
        )
        # The match message must be in the result
        contents = {m["content"] for m in result}
        assert "message number 50" in contents, "Match message not in window"
        # Messages far from the match should NOT be present
        assert "message number 0" not in contents, "Far-away message leaked into window"
        assert "message number 99" not in contents, "Far-away message leaked into window"

    def test_multiple_matches_merge_overlapping_windows(self):
        """Two matches close together should merge into one window without
        duplicates, and results MUST be in conversation order."""
        from hermes_state import SessionDB

        db = SessionDB()
        sid = "test_window_merge"
        db.create_session(sid, source="cli")

        with db._lock:
            for i in range(30):
                db._conn.execute(
                    """INSERT INTO messages
                       (session_id, role, content, timestamp)
                       VALUES (?, ?, ?, ?)""",
                    (sid, "user", f"msg_{i}", float(100_000_000 + i * 10)),
                )

            # Get IDs for messages #10 and #12 (close together)
            row_a = db._conn.execute(
                "SELECT id FROM messages WHERE session_id = ? AND content = ?",
                (sid, "msg_10"),
            ).fetchone()
            row_b = db._conn.execute(
                "SELECT id FROM messages WHERE session_id = ? AND content = ?",
                (sid, "msg_12"),
            ).fetchone()

        result = db.get_messages_window(
            sid, [row_a["id"], row_b["id"]], window_size=5
        )

        # Should be deduplicated (DISTINCT in SQL)
        contents = [m["content"] for m in result]
        seen = set()
        for c in contents:
            assert c not in seen, f"Duplicate content in window: {c}"
            seen.add(c)

        # Both match messages must be present
        assert "msg_10" in contents and "msg_12" in contents

        # Must be in conversation order (monotonically increasing)
        msg_nums = [int(c.split("_")[1]) for c in contents]
        for i in range(1, len(msg_nums)):
            assert msg_nums[i] > msg_nums[i - 1], (
                f"Messages out of order: msg_{msg_nums[i-1]} before "
                f"msg_{msg_nums[i]}"
            )

    def test_falls_back_to_full_load_on_error(self):
        """When the SQL fails (e.g., bad params), gracefully fall back to
        get_messages_as_conversation()."""
        from hermes_state import SessionDB
        import logging

        db = SessionDB()
        sid = "test_window_fallback"
        db.create_session(sid, source="cli")

        with db._lock:
            db._conn.execute(
                """INSERT INTO messages (session_id, role, content, timestamp)
                   VALUES (?, ?, ?, ?)""",
                (sid, "user", "only message", 100_000_000.0),
            )

        # Empty match_ids → should return empty list (not fallback)
        result_empty = db.get_messages_window(sid, [], window_size=5)
        assert result_empty == [], "Empty match_ids should return empty list"

        # Valid match_ids return the right data
        with db._lock:
            row = db._conn.execute(
                "SELECT id FROM messages WHERE session_id = ?", (sid,)
            ).fetchone()

        result = db.get_messages_window(sid, [row["id"]], window_size=5)
        assert len(result) == 1
        assert result[0]["content"] == "only message"

    def test_window_preserves_message_format(self):
        """Window-loaded messages must have the same dict shape as
        get_messages_as_conversation()."""
        from hermes_state import SessionDB

        db = SessionDB()
        sid = "test_window_format"
        db.create_session(sid, source="cli")

        with db._lock:
            db._conn.execute(
                """INSERT INTO messages
                   (session_id, role, content, tool_name, tool_calls, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sid, "assistant", "I'll help", "test_tool",
                 '["call_1"]', 100_000_000.0),
            )
            db._conn.execute(
                """INSERT INTO messages
                   (session_id, role, content, tool_call_id, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (sid, "tool", '{"result": "ok"}', "call_1", 100_000_001.0),
            )
            row = db._conn.execute(
                "SELECT id FROM messages WHERE session_id = ? AND role = ?",
                (sid, "assistant"),
            ).fetchone()

        # Window-load
        window_result = db.get_messages_window(sid, [row["id"]], window_size=5)
        # Full-load for comparison
        full_result = db.get_messages_as_conversation(sid)

        # Both should have the same number of messages (small session)
        assert len(window_result) == len(full_result) == 2

        # Verify essential keys exist
        for msg in window_result:
            assert "role" in msg
            assert "content" in msg
