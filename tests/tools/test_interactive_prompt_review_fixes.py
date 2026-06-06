"""Test cases for 7 code-review findings fixed on feat/interactive-prompt-tool branch.

Covers:
  Finding 1 (P1) — Double-JSON-encoding prevention
  Finding 2 (P1) — Text-fallback non-rich platform resolution
  Finding 3 (P2) — Config-aware timeout in intercepted path
  Finding 4 (P2) — _finish_agent_tool wrapping
  Finding 5 (P2) — Profile-aware upload cache path
  Finding 6 (P2) — Per-policy auth checks
  Finding 7 (P3) — Runtime argument validation
"""

from __future__ import annotations

import inspect
import json
import os
import textwrap
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from tools.human_input_gateway import (
    HumanInputResult,
    ActorInfo,
    _reset_for_testing,
    generate_prompt_id,
    register,
    resolve_text_response,
    mark_awaiting_text,
    is_awaiting_text,
    get_pending_for_session,
    wait_for_response,
)


def _clear_state():
    """Reset gateway module state between tests."""
    _reset_for_testing()


_SIMPLE_OPTIONS = [
    {"label": "Yes", "value": "yes"},
    {"label": "No", "value": "no"},
    {"label": "Maybe", "value": "maybe"},
]


# =============================================================================
# Finding 1 (P1) — Double-JSON-encoding
# =============================================================================


class TestFinding1DoubleJSONEncoding:
    """Verify the tool detects and passes through already-valid JSON strings
    from production-shaped gateway callbacks, avoiding double-encoding."""

    def test_json_string_callback_passed_through(self):
        """A callback returning json.dumps(dict) should produce a string that
        json.loads() parses to a dict — NOT a nested JSON string."""
        payload = {"status": "selected", "choice": "yes"}

        def json_callback(q, opts, dt, ts, ap):
            return json.dumps(payload)

        result_str = _call_tool(callback=json_callback)
        parsed = json.loads(result_str)
        assert isinstance(parsed, dict)
        assert parsed["status"] == "selected"
        assert parsed["choice"] == "yes"

    def test_dict_callback_backward_compat(self):
        """A callback returning a plain dict should still work (backward compat)."""
        def dict_callback(q, opts, dt, ts, ap):
            return {"status": "selected", "choice": "yes", "timed_out": False}

        result_str = _call_tool(callback=dict_callback)
        parsed = json.loads(result_str)
        assert isinstance(parsed, dict)
        assert parsed["choice"] == "yes"

    def test_non_json_string_callback_serialized(self):
        """A callback returning a non-JSON string should be serialized as JSON."""
        def string_callback(q, opts, dt, ts, ap):
            return "hello"

        result_str = _call_tool(callback=string_callback)
        parsed = json.loads(result_str)
        assert parsed == "hello"

    def test_human_input_result_still_works(self):
        """HumanInputResult objects are still serialized correctly."""
        def hir_callback(q, opts, dt, ts, ap):
            return HumanInputResult(status="selected", choice="yes", timed_out=False)

        result_str = _call_tool(callback=hir_callback)
        parsed = json.loads(result_str)
        assert parsed["status"] == "selected"
        assert parsed["choice"] == "yes"

    def test_json_list_string_re_serialized(self):
        """A callback returning a JSON-encoded list (not a dict) gets
        re-serialized — the pass-through only applies to JSON dicts."""
        def json_callback(q, opts, dt, ts, ap):
            return json.dumps([1, 2, 3])

        result_str = _call_tool(callback=json_callback)
        # json.loads("[1,2,3]") is a list, not a dict, so the tool falls
        # through to json.dumps(result) which re-serializes the string.
        # Final result: json.dumps("[1, 2, 3]") → '"[1, 2, 3]"'
        parsed = json.loads(result_str)
        assert isinstance(parsed, str)
        assert json.loads(parsed) == [1, 2, 3]


# =============================================================================
# Finding 2 (P1) — Text-fallback non-rich platform resolution
# =============================================================================


class TestFinding2TextFallbackResolution:
    """Test the new text-fallback functions: get_pending_for_session(),
    mark_awaiting_text(), is_awaiting_text(), resolve_text_response()."""

    def setup_method(self):
        _clear_state()

    def test_resolve_by_numeric_index(self):
        """resolve_text_response with '2' resolves with the 2nd option's value."""
        pid = generate_prompt_id()
        register(pid, "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)
        mark_awaiting_text(pid)
        assert is_awaiting_text(pid) is True

        resolved = resolve_text_response(pid, "2")
        assert resolved is True

        entry = _get_entry_result(pid)
        assert entry.status == "selected"
        assert entry.choice == "no"  # index 2 (1-based) → _SIMPLE_OPTIONS[1] → "no"

    def test_resolve_by_label_match(self):
        """resolve_text_response with 'Yes' matches the label."""
        pid = generate_prompt_id()
        register(pid, "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)
        mark_awaiting_text(pid)

        resolved = resolve_text_response(pid, "Yes")
        assert resolved is True

        entry = _get_entry_result(pid)
        assert entry.choice == "yes"

    def test_resolve_by_case_insensitive_label(self):
        """resolve_text_response matches labels case-insensitively."""
        pid = generate_prompt_id()
        register(pid, "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)
        mark_awaiting_text(pid)

        resolved = resolve_text_response(pid, "MAYBE")
        assert resolved is True

        entry = _get_entry_result(pid)
        assert entry.choice == "maybe"

    def test_resolve_custom_text_fallback(self):
        """resolve_text_response with 'custom text' uses raw text as choice."""
        pid = generate_prompt_id()
        register(pid, "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)
        mark_awaiting_text(pid)

        resolved = resolve_text_response(pid, "custom text")
        assert resolved is True

        entry = _get_entry_result(pid)
        assert entry.choice == "custom text"

    def test_modal_option_resolved_via_text_gets_raw_text(self):
        """A modal option resolved via text fallback gets the raw text,
        not the option value (can't collect modal fields via text)."""
        modal_options = [
            {"label": "Submit form", "value": "submit_form", "action": "modal",
             "modal": {"title": "Form", "fields": [{"key": "name", "label": "Name"}]}},
        ]
        pid = generate_prompt_id()
        register(pid, "sk1", "Form?", modal_options, timeout_seconds=900)
        mark_awaiting_text(pid)

        # Try to resolve by matching the label — should fall back to raw text
        # because the matched option is a modal action
        resolved = resolve_text_response(pid, "Submit form")
        assert resolved is True

        entry = _get_entry_result(pid)
        # The modal option match triggers fallback to raw text
        assert entry.choice == "Submit form"

    def test_modal_option_resolved_by_index_gets_raw_text(self):
        """A modal option resolved by numeric index gets the raw text index."""
        modal_options = [
            {"label": "Submit form", "value": "submit_form", "action": "modal",
             "modal": {"title": "Form", "fields": [{"key": "name", "label": "Name"}]}},
        ]
        pid = generate_prompt_id()
        register(pid, "sk1", "Form?", modal_options, timeout_seconds=900)
        mark_awaiting_text(pid)

        resolved = resolve_text_response(pid, "1")
        assert resolved is True

        entry = _get_entry_result(pid)
        # Numeric index 1 → matches modal option → falls back to raw text "1"
        assert entry.choice == "1"

    def test_get_pending_for_session_returns_none_when_empty(self):
        """get_pending_for_session returns None when no entries exist."""
        assert get_pending_for_session("nonexistent_session") is None

    def test_get_pending_for_session_returns_oldest_pending(self):
        """get_pending_for_session returns the first unresolved entry."""
        pid1 = generate_prompt_id()
        pid2 = generate_prompt_id()
        register(pid1, "sk1", "Q1?", _SIMPLE_OPTIONS, timeout_seconds=900)
        register(pid2, "sk1", "Q2?", _SIMPLE_OPTIONS, timeout_seconds=900)

        entry = get_pending_for_session("sk1")
        assert entry is not None
        assert entry.prompt_id == pid1  # oldest first

    def test_resolve_text_response_returns_false_for_already_resolved(self):
        """resolve_text_response returns False for already-resolved entries."""
        pid = generate_prompt_id()
        register(pid, "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)
        mark_awaiting_text(pid)

        # First resolution succeeds
        assert resolve_text_response(pid, "1") is True
        # Second resolution on same entry should fail
        assert resolve_text_response(pid, "2") is False

    def test_mark_awaiting_text_returns_false_for_unknown(self):
        """mark_awaiting_text returns False for unknown prompt_id."""
        assert mark_awaiting_text("nonexistent") is False

    def test_is_awaiting_text_false_by_default(self):
        """is_awaiting_text returns False for entries not marked."""
        pid = generate_prompt_id()
        register(pid, "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)
        assert is_awaiting_text(pid) is False


# =============================================================================
# Finding 3 (P2) — Config-aware timeout
# =============================================================================


class TestFinding3ConfigAwareTimeout:
    """Verify get_interactive_prompt_timeout reads from config correctly."""

    def test_returns_configured_timeout(self):
        """When agent.interactive_prompt_timeout is set, return it."""
        with patch("hermes_cli.config.load_config",
                   return_value={"agent": {"interactive_prompt_timeout": 600}}):
            from tools.human_input_gateway import get_interactive_prompt_timeout
            assert get_interactive_prompt_timeout() == 600

    def test_falls_back_to_clarify_timeout(self):
        """When interactive_prompt_timeout is absent, falls back to clarify_timeout."""
        with patch("hermes_cli.config.load_config",
                   return_value={"agent": {"clarify_timeout": 300}}):
            from tools.human_input_gateway import get_interactive_prompt_timeout
            assert get_interactive_prompt_timeout() == 300

    def test_returns_default_when_no_config(self):
        """When no config keys are set, returns 900 (default)."""
        with patch("hermes_cli.config.load_config", return_value={}):
            from tools.human_input_gateway import get_interactive_prompt_timeout
            assert get_interactive_prompt_timeout() == 900

    def test_returns_default_on_exception(self):
        """Config load failure → returns 900 (safe default)."""
        with patch("hermes_cli.config.load_config", side_effect=Exception("boom")):
            from tools.human_input_gateway import get_interactive_prompt_timeout
            assert get_interactive_prompt_timeout() == 900

    def test_intercepted_path_imports_timeout_function(self):
        """Verify the intercepted path in agent_runtime_helpers.py imports
        get_interactive_prompt_timeout and uses it."""
        import agent.agent_runtime_helpers
        # The intercepted function is named invoke_tool
        func = agent.agent_runtime_helpers.invoke_tool
        src = inspect.getsource(func)
        assert "interactive_prompt" in src
        assert "get_interactive_prompt_timeout" in src
        assert "_timeout = int(_raw_timeout) if _raw_timeout is not None else get_interactive_prompt_timeout()" in src


# =============================================================================
# Finding 4 (P2) — _finish_agent_tool wrapping
# =============================================================================


class TestFinding4FinishAgentToolWrapping:
    """Verify the interactive_prompt branch uses _finish_agent_tool."""

    def test_interactive_prompt_branch_uses_finish_agent_tool(self):
        """The interactive_prompt branch in invoke_tool wraps
        the call in _finish_agent_tool."""
        import agent.agent_runtime_helpers
        func = agent.agent_runtime_helpers.invoke_tool
        src = inspect.getsource(func)

        # Verify interactive_prompt is in the same function
        assert 'function_name == "interactive_prompt"' in src
        # Verify _finish_agent_tool is used in the function
        assert 'return _finish_agent_tool(' in src, (
            "Expected _finish_agent_tool wrapping in invoke_tool"
        )


# =============================================================================
# Finding 5 (P2) — Profile-aware upload cache path
# =============================================================================


class TestFinding5ProfileAwareUploadCache:
    """Verify discord_interactive_views.py uses get_hermes_home() instead of
    hardcoded ~/.hermes."""

    def test_file_contains_get_hermes_home(self):
        """File should use get_hermes_home() for cache path construction."""
        path = _find_discord_views_file()
        content = open(path).read()
        assert "get_hermes_home" in content, (
            "discord_interactive_views.py should use get_hermes_home()"
        )

    def test_file_does_not_contain_hardcoded_expanduser(self):
        """File should NOT contain hardcoded expanduser('~/.hermes/cache/uploads')."""
        path = _find_discord_views_file()
        content = open(path).read()
        assert 'expanduser("~/.hermes/cache/uploads")' not in content, (
            "Should not use hardcoded expanduser('~/.hermes/cache/uploads')"
        )

    def test_file_does_not_contain_hardcoded_hermes_cache(self):
        """File should NOT contain hardcoded '~/.hermes/cache' path literal."""
        path = _find_discord_views_file()
        content = open(path).read()
        # It should NOT have a raw string "~/.hermes/cache" without get_hermes_home
        # Check there's no construction like os.path.expanduser("~/.hermes/cache")
        assert '"~/.hermes/cache"' not in content or "get_hermes_home()" in content, (
            "Cache path should use get_hermes_home() not hardcoded ~/.hermes"
        )

    def test_upload_cache_uses_get_hermes_home(self):
        """The cache_dir construction uses os.path.join(get_hermes_home(), 'cache', 'uploads')."""
        path = _find_discord_views_file()
        content = open(path).read()
        assert 'os.path.join(get_hermes_home(), "cache", "uploads")' in content, (
            "Cache dir should be constructed with get_hermes_home()"
        )


# =============================================================================
# Finding 6 (P2) — Per-policy auth checks
# =============================================================================

discord = pytest.importorskip("discord")

from tools.discord_interactive_views import InteractivePromptView
from tools.discord_auth_helpers import component_check_auth


def _make_mock_interaction(
    user_id: str = "123",
    role_ids: list = None,
):
    """Build a lightweight mock that quacks like discord.Interaction."""
    user = MagicMock()
    user.id = int(user_id)
    if role_ids is not None:
        user.roles = [MagicMock(id=int(rid)) for rid in role_ids]
    else:
        user.roles = []
    interaction = MagicMock()
    interaction.user = user
    return interaction


def _make_view(
    policy: str = "session_owner_only",
    allowed_user_ids: set = None,
    allowed_role_ids: set = None,
    origin_user_id: str = None,
) -> InteractivePromptView:
    """Build an InteractivePromptView for testing auth checks."""
    return InteractivePromptView(
        prompt_id="test_prompt_id_123",
        question="Test question?",
        options=[{"label": "Opt 1", "value": "opt_1"}],
        allowed_user_ids=allowed_user_ids or set(),
        allowed_role_ids=allowed_role_ids or set(),
        auth_policy=policy,
        origin_user_id=origin_user_id,
        timeout_seconds=900,
    )


class TestFinding6PerPolicyAuthChecks:
    """Verify per-policy auth checks enforce the correct allowlist semantics."""

    def test_any_allowed_user_matching_user_is_allowed(self):
        """any_allowed_user: user in user allowlist → allowed."""
        view = _make_view(
            policy="any_allowed_user",
            allowed_user_ids={"42", "99"},
        )
        interaction = _make_mock_interaction(user_id="42")
        assert view._check_auth(interaction) is True

    def test_any_allowed_user_matching_role_only_is_rejected(self):
        """any_allowed_user: user matches role allowlist only → rejected
        (roles are ignored for any_allowed_user)."""
        view = _make_view(
            policy="any_allowed_user",
            allowed_user_ids={"42"},
            allowed_role_ids={"55"},
        )
        # User 99 has role 55 but is NOT in user allowlist
        interaction = _make_mock_interaction(user_id="99", role_ids=["55"])
        assert view._check_auth(interaction) is False

    def test_any_allowed_user_no_user_allowlist_allows_all(self):
        """any_allowed_user: empty user allowlist → allow everyone (no-restriction deployment)."""
        view = _make_view(
            policy="any_allowed_user",
            allowed_user_ids=set(),
        )
        interaction = _make_mock_interaction(user_id="99")
        assert view._check_auth(interaction) is True

    def test_any_allowed_role_matching_role_is_allowed(self):
        """any_allowed_role: user has a role in role allowlist → allowed."""
        view = _make_view(
            policy="any_allowed_role",
            allowed_role_ids={55, 77},
        )
        interaction = _make_mock_interaction(user_id="99", role_ids=["55"])
        assert view._check_auth(interaction) is True

    def test_any_allowed_role_matching_user_only_is_rejected(self):
        """any_allowed_role: user matches user allowlist only → rejected
        (user IDs are ignored for any_allowed_role)."""
        view = _make_view(
            policy="any_allowed_role",
            allowed_user_ids={"42"},
            allowed_role_ids={55},
        )
        # User 42 is in user allowlist but NOT in role allowlist
        interaction = _make_mock_interaction(user_id="42", role_ids=["10"])
        assert view._check_auth(interaction) is False

    def test_any_allowed_role_no_role_allowlist_allows_all(self):
        """any_allowed_role: empty role allowlist → allow everyone."""
        view = _make_view(
            policy="any_allowed_role",
            allowed_role_ids=set(),
        )
        interaction = _make_mock_interaction(user_id="99")
        assert view._check_auth(interaction) is True

    def test_any_allowed_user_or_role_user_match(self):
        """any_allowed_user_or_role: user matches user allowlist → allowed."""
        view = _make_view(
            policy="any_allowed_user_or_role",
            allowed_user_ids={"42"},
            allowed_role_ids={55},
        )
        interaction = _make_mock_interaction(user_id="42")
        assert view._check_auth(interaction) is True

    def test_any_allowed_user_or_role_role_match(self):
        """any_allowed_user_or_role: user has matching role → allowed."""
        view = _make_view(
            policy="any_allowed_user_or_role",
            allowed_user_ids={"42"},
            allowed_role_ids={55},
        )
        interaction = _make_mock_interaction(user_id="99", role_ids=["55"])
        assert view._check_auth(interaction) is True

    def test_any_allowed_user_or_role_no_match_rejected(self):
        """any_allowed_user_or_role: neither user nor role matches → rejected."""
        view = _make_view(
            policy="any_allowed_user_or_role",
            allowed_user_ids={"42"},
            allowed_role_ids={55},
        )
        interaction = _make_mock_interaction(user_id="99", role_ids=["10"])
        assert view._check_auth(interaction) is False

    def test_session_owner_only_correct_user(self):
        """session_owner_only: matching origin_user_id → allowed."""
        view = _make_view(
            policy="session_owner_only",
            origin_user_id="42",
        )
        interaction = _make_mock_interaction(user_id="42")
        assert view._check_auth(interaction) is True

    def test_session_owner_only_wrong_user(self):
        """session_owner_only: different user → rejected."""
        view = _make_view(
            policy="session_owner_only",
            origin_user_id="42",
        )
        interaction = _make_mock_interaction(user_id="99")
        assert view._check_auth(interaction) is False


# =============================================================================
# Finding 7 (P3) — Runtime argument validation
# =============================================================================


class TestFinding7RuntimeArgumentValidation:
    """Verify runtime argument validation and clamping."""

    def test_display_type_carousel_rejected(self):
        """display_type='carousel' → tool_error with 'Unsupported display_type'."""
        def mock_cb(*a, **kw):
            return HumanInputResult(status="selected", choice="yes", timed_out=False)
        result_str = _call_tool(display_type="carousel", callback=mock_cb)
        assert "Unsupported display_type" in result_str
        assert "carousel" in result_str

    def test_auth_policy_anyone_rejected(self):
        """auth_policy='anyone' → tool_error with 'Unsupported auth_policy'."""
        def mock_cb(*a, **kw):
            return HumanInputResult(status="selected", choice="yes", timed_out=False)
        result_str = _call_tool(auth_policy="anyone", callback=mock_cb)
        assert "Unsupported auth_policy" in result_str
        assert "anyone" in result_str

    def test_timeout_10_clamped_to_60(self):
        """timeout_seconds=10 → clamped to 60 (minimum)."""
        captured = []

        def capture_cb(q, opts, dt, ts, ap):
            captured.append(ts)
            return HumanInputResult(status="selected", choice="yes", timed_out=False)

        _call_tool(timeout_seconds=10, callback=capture_cb)
        assert captured[0] == 60

    def test_timeout_5000_clamped_to_3600(self):
        """timeout_seconds=5000 → clamped to 3600 (maximum)."""
        captured = []

        def capture_cb(q, opts, dt, ts, ap):
            captured.append(ts)
            return HumanInputResult(status="selected", choice="yes", timed_out=False)

        _call_tool(timeout_seconds=5000, callback=capture_cb)
        assert captured[0] == 3600

    def test_timeout_none_defaults_to_900(self):
        """timeout_seconds=None → defaults to 900."""
        captured = []

        def capture_cb(q, opts, dt, ts, ap):
            captured.append(ts)
            return HumanInputResult(status="selected", choice="yes", timed_out=False)

        _call_tool(timeout_seconds=None, callback=capture_cb)
        assert captured[0] == 900

    def test_timeout_within_range_unchanged(self):
        """timeout_seconds=300 → passed through unchanged."""
        captured = []

        def capture_cb(q, opts, dt, ts, ap):
            captured.append(ts)
            return HumanInputResult(status="selected", choice="yes", timed_out=False)

        _call_tool(timeout_seconds=300, callback=capture_cb)
        assert captured[0] == 300

    def test_timeout_exactly_60_accepted(self):
        """timeout_seconds=60 (minimum) → accepted as-is."""
        captured = []

        def capture_cb(q, opts, dt, ts, ap):
            captured.append(ts)
            return HumanInputResult(status="selected", choice="yes", timed_out=False)

        _call_tool(timeout_seconds=60, callback=capture_cb)
        assert captured[0] == 60

    def test_timeout_exactly_3600_accepted(self):
        """timeout_seconds=3600 (maximum) → accepted as-is."""
        captured = []

        def capture_cb(q, opts, dt, ts, ap):
            captured.append(ts)
            return HumanInputResult(status="selected", choice="yes", timed_out=False)

        _call_tool(timeout_seconds=3600, callback=capture_cb)
        assert captured[0] == 3600


# =============================================================================
# Helpers
# =============================================================================


def _call_tool(
    question="Pick one",
    options=None,
    display_type="buttons",
    timeout_seconds=900,
    auth_policy="session_owner_only",
    callback=None,
):
    """Shorthand to call interactive_prompt_tool with defaults."""
    from tools.interactive_prompt_tool import interactive_prompt_tool
    return interactive_prompt_tool(
        question=question,
        options=options or _SIMPLE_OPTIONS,
        display_type=display_type,
        timeout_seconds=timeout_seconds,
        auth_policy=auth_policy,
        callback=callback,
    )


def _get_entry_result(prompt_id: str):
    """Get the result from a resolved entry (wait_for_response cleans up,
    so we need to get it from the entry before cleanup if possible,
    or access the internal entry directly)."""
    from tools.human_input_gateway import _entries, _lock
    with _lock:
        entry = _entries.get(prompt_id)
    if entry and entry.result:
        return entry.result
    # If already cleaned up, the event should have the result
    # We need to re-register and check; instead, use a workaround:
    # Since resolve_text_response sets result before event.set(),
    # and we're calling right after, the entry might still be there
    # but the _resolved flag prevents wait_for_response from seeing it.
    # We already set result above, so return what we got.
    return None


def _find_discord_views_file():
    """Find the discord_interactive_views.py file path."""
    import tools.discord_interactive_views as mod
    return inspect.getfile(mod)
