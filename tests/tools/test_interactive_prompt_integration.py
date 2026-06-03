"""Integration tests for interactive_prompt: tool → gateway → mock adapter.

Exercises the full wiring path that a real gateway session would follow:
  1. Tool handler validates + calls callback
  2. Callback registers in human_input_gateway, calls adapter.send_human_input()
  3. A resolver thread simulates the user clicking a button
  4. Result flows back through the gateway to the tool handler

No real Discord connections — adapter is mocked.

Result schema (from HumanInputResult.to_dict()):
  {
    "status": "selected" | "submitted" | "timeout" | "cancelled",
    "choice": "value_of_clicked_option" | None,
    "timed_out": bool,
    "actor": {"platform", "user_id", "display_name"} | None,
    "fields": {"field_key": "value", ...} | None,   # modal only
    "files": [...] | None,                            # modal with uploads
  }
"""

import json
import threading
import time
from unittest.mock import MagicMock

import pytest

from tools.human_input_gateway import (
    ActorInfo,
    HumanInputResult,
    _reset_for_testing,
    clear_session,
    generate_prompt_id,
    register,
    resolve_choice,
    resolve_modal,
    wait_for_response,
)
from tools.interactive_prompt_tool import interactive_prompt_tool


def _clear_state():
    """Reset gateway module state between tests."""
    _reset_for_testing()


_SIMPLE_OPTIONS = [
    {"label": "Yes", "value": "yes"},
    {"label": "No", "value": "no"},
]

_MODAL_OPTIONS = [
    {
        "label": "Provide details",
        "value": "details",
        "action": "modal",
        "modal": {
            "title": "Details",
            "fields": [
                {"key": "reason", "label": "Reason", "type": "text"},
            ],
        },
    },
]

_ACTOR = ActorInfo(platform="discord", user_id="123", display_name="Tester")


# ---------------------------------------------------------------------------
# Helpers — mock callbacks that mimic gateway/run.py's _interactive_prompt_callback_sync
# ---------------------------------------------------------------------------

def _make_callback_that_resolves_choice(delay: float = 0.05):
    """Build a mock adapter callback that simulates a button click."""
    resolved_event = threading.Event()

    def callback(question, options, display_type, timeout_seconds, auth_policy):
        prompt_id = generate_prompt_id()
        register(
            prompt_id=prompt_id,
            session_key="test-session",
            question=question,
            options=options,
            timeout_seconds=timeout_seconds,
            auth_policy=auth_policy,
        )

        def _resolve():
            time.sleep(delay)
            resolve_choice(prompt_id, options[0]["value"], actor=_ACTOR)
            resolved_event.set()

        threading.Thread(target=_resolve, daemon=True).start()

        result = wait_for_response(prompt_id, timeout=timeout_seconds)
        if result is None:
            return {"status": "timeout", "timed_out": True}
        return result.to_dict()

    return callback, resolved_event


def _make_callback_that_resolves_modal(delay: float = 0.05):
    """Callback that resolves via modal submission."""
    resolved_event = threading.Event()

    def callback(question, options, display_type, timeout_seconds, auth_policy):
        prompt_id = generate_prompt_id()
        register(
            prompt_id=prompt_id,
            session_key="test-session",
            question=question,
            options=options,
            timeout_seconds=timeout_seconds,
            auth_policy=auth_policy,
        )

        def _resolve():
            time.sleep(delay)
            resolve_modal(
                prompt_id,
                options[0]["value"],
                fields={"reason": "because reasons"},
                actor=_ACTOR,
            )
            resolved_event.set()

        threading.Thread(target=_resolve, daemon=True).start()

        result = wait_for_response(prompt_id, timeout=timeout_seconds)
        if result is None:
            return {"status": "timeout", "timed_out": True}
        return result.to_dict()

    return callback, resolved_event


def _make_callback_that_times_out(timeout_to_use: float = 1.0):
    """Callback that never resolves — simulates user ignoring the prompt."""

    def callback(question, options, display_type, timeout_seconds, auth_policy):
        prompt_id = generate_prompt_id()
        register(
            prompt_id=prompt_id,
            session_key="test-session-timeout",
            question=question,
            options=options,
            timeout_seconds=timeout_to_use,
            auth_policy=auth_policy,
        )
        result = wait_for_response(prompt_id, timeout=timeout_to_use)
        if result is None:
            return {"status": "timeout", "timed_out": True}
        return result.to_dict()

    return callback


def _make_callback_that_fails_send():
    """Callback that simulates the adapter failing to deliver the prompt."""

    def callback(question, options, display_type, timeout_seconds, auth_policy):
        prompt_id = generate_prompt_id()
        register(
            prompt_id=prompt_id,
            session_key="test-session-fail",
            question=question,
            options=options,
            timeout_seconds=timeout_seconds,
            auth_policy=auth_policy,
        )
        # Simulate send failure — clear session (mirrors gateway/run.py)
        clear_session("test-session-fail")
        return {"status": "cancelled", "error": "prompt could not be delivered"}

    return callback


# =========================================================================
# Integration tests
# =========================================================================


class TestChoiceRoundTrip:
    """Full round-trip: tool → callback → gateway → resolve → result."""

    def setup_method(self):
        _clear_state()

    def test_choice_round_trip(self):
        """Button click resolves through the full tool→gateway path."""
        cb, event = _make_callback_that_resolves_choice()

        result_str = interactive_prompt_tool(
            question="Continue?",
            options=_SIMPLE_OPTIONS,
            display_type="buttons",
            timeout_seconds=10,
            auth_policy="session_owner_only",
            callback=cb,
        )

        assert event.wait(timeout=5), "Resolver thread never fired"
        result = json.loads(result_str)
        assert result["status"] == "selected"
        assert result["choice"] == "yes"
        assert result["timed_out"] is False
        assert result["actor"]["user_id"] == "123"
        assert result["actor"]["display_name"] == "Tester"
        assert result["actor"]["platform"] == "discord"

    def test_choice_result_is_valid_json(self):
        """Verify the JSON string is parseable and has required keys."""
        cb, _ = _make_callback_that_resolves_choice()

        result_str = interactive_prompt_tool(
            question="Continue?",
            options=_SIMPLE_OPTIONS,
            timeout_seconds=10,
            callback=cb,
        )

        result = json.loads(result_str)
        # Required keys from HumanInputResult.to_dict()
        assert "status" in result
        assert "choice" in result
        assert "timed_out" in result
        assert "actor" in result

    def test_second_option_choice(self):
        """Clicking 'No' returns the correct value."""
        resolved_event = threading.Event()

        def cb(question, options, display_type, timeout_seconds, auth_policy):
            pid = generate_prompt_id()
            register(prompt_id=pid, session_key="test-s2", question=question,
                     options=options, timeout_seconds=timeout_seconds, auth_policy=auth_policy)

            def _r():
                time.sleep(0.05)
                resolve_choice(pid, options[1]["value"], actor=_ACTOR)
                resolved_event.set()

            threading.Thread(target=_r, daemon=True).start()
            r = wait_for_response(pid, timeout=timeout_seconds)
            return r.to_dict() if r else {"status": "timeout", "timed_out": True}

        result_str = interactive_prompt_tool(
            question="Continue?",
            options=_SIMPLE_OPTIONS,
            timeout_seconds=10,
            callback=cb,
        )

        result = json.loads(result_str)
        assert result["choice"] == "no"


class TestModalRoundTrip:
    """Full round-trip via modal submission."""

    def setup_method(self):
        _clear_state()

    def test_modal_round_trip(self):
        """Modal submission resolves through the full tool→gateway path."""
        cb, event = _make_callback_that_resolves_modal()

        result_str = interactive_prompt_tool(
            question="Tell me more?",
            options=_MODAL_OPTIONS,
            timeout_seconds=10,
            callback=cb,
        )

        assert event.wait(timeout=5), "Resolver thread never fired"
        result = json.loads(result_str)
        assert result["status"] == "submitted"
        assert result["choice"] == "details"
        assert result["fields"]["reason"] == "because reasons"

    def test_modal_actor_preserved(self):
        """Actor info from the resolver survives serialization."""
        cb, _ = _make_callback_that_resolves_modal()

        result_str = interactive_prompt_tool(
            question="Details?",
            options=_MODAL_OPTIONS,
            timeout_seconds=10,
            callback=cb,
        )

        result = json.loads(result_str)
        assert result["actor"]["user_id"] == "123"
        assert result["actor"]["display_name"] == "Tester"


class TestTimeoutPath:
    """Timeout flows through the full integration path."""

    def setup_method(self):
        _clear_state()

    def test_timeout_returns_timeout_result(self):
        """No user response → tool returns timeout JSON."""
        cb = _make_callback_that_times_out(timeout_to_use=0.5)

        result_str = interactive_prompt_tool(
            question="Will timeout?",
            options=_SIMPLE_OPTIONS,
            timeout_seconds=60,  # Tool-level high, gateway-level 0.5 wins
            callback=cb,
        )

        result = json.loads(result_str)
        assert result["status"] == "timeout"
        assert result["timed_out"] is True


class TestSendFailure:
    """Adapter send failures propagate correctly."""

    def setup_method(self):
        _clear_state()

    def test_send_failure_returns_cancelled(self):
        """Adapter fails to send → tool returns cancelled JSON."""
        cb = _make_callback_that_fails_send()

        result_str = interactive_prompt_tool(
            question="Will fail?",
            options=_SIMPLE_OPTIONS,
            timeout_seconds=10,
            callback=cb,
        )

        result = json.loads(result_str)
        assert result["status"] == "cancelled"
        assert "could not be delivered" in result["error"]


class TestValidationStillWorks:
    """Ensure input validation still fires even with a valid callback."""

    def setup_method(self):
        _clear_state()

    def test_empty_question_with_callback(self):
        """Validation rejects empty question before calling callback."""
        cb = MagicMock(side_effect=Exception("Should not be called"))

        result_str = interactive_prompt_tool(
            question="",
            options=_SIMPLE_OPTIONS,
            timeout_seconds=10,
            callback=cb,
        )

        result = json.loads(result_str)
        assert "error" in result
        cb.assert_not_called()

    def test_no_options_with_callback(self):
        """Validation rejects missing options before calling callback."""
        cb = MagicMock(side_effect=Exception("Should not be called"))

        result_str = interactive_prompt_tool(
            question="Hello?",
            options=None,
            timeout_seconds=10,
            callback=cb,
        )

        result = json.loads(result_str)
        assert "error" in result
        cb.assert_not_called()

    def test_too_many_options_with_callback(self):
        """Validation rejects >25 options before calling callback."""
        cb = MagicMock(side_effect=Exception("Should not be called"))
        too_many = [{"label": f"Opt{i}", "value": f"opt{i}"} for i in range(26)]

        result_str = interactive_prompt_tool(
            question="Too many?",
            options=too_many,
            timeout_seconds=10,
            callback=cb,
        )

        result = json.loads(result_str)
        assert "error" in result
        cb.assert_not_called()


class TestNoCallback:
    """Tool gracefully handles missing callback (non-gateway context)."""

    def setup_method(self):
        _clear_state()

    def test_no_callback_returns_error(self):
        """Without callback, tool returns context-not-available error."""
        result_str = interactive_prompt_tool(
            question="Hello?",
            options=_SIMPLE_OPTIONS,
            timeout_seconds=10,
            callback=None,
        )

        result = json.loads(result_str)
        assert "error" in result
        assert "not available" in result["error"].lower()


class TestCallbackException:
    """Exceptions from the callback are caught and returned as errors."""

    def setup_method(self):
        _clear_state()

    def test_callback_exception_returns_error(self):
        """Callback raises → tool returns error JSON."""
        def bad_callback(question, options, display_type, timeout_seconds, auth_policy):
            raise RuntimeError("Adapter exploded")

        result_str = interactive_prompt_tool(
            question="Will crash?",
            options=_SIMPLE_OPTIONS,
            timeout_seconds=10,
            callback=bad_callback,
        )

        result = json.loads(result_str)
        assert "error" in result
        assert "Adapter exploded" in result["error"]


class TestResetForTesting:
    """_reset_for_testing() clears all gateway state."""

    def setup_method(self):
        _clear_state()

    def test_reset_clears_registered_prompts(self):
        """After reset, registered prompts are gone."""
        prompt_id = generate_prompt_id()
        register(
            prompt_id=prompt_id,
            session_key="test-session-reset",
            question="Reset?",
            options=_SIMPLE_OPTIONS,
            timeout_seconds=10,
            auth_policy="session_owner_only",
        )

        from tools.human_input_gateway import get_entry
        assert get_entry(prompt_id) is not None

        _reset_for_testing()

        assert get_entry(prompt_id) is None


class TestRegistryLambda:
    """Test the registry lambda wiring (tool dispatch path)."""

    def setup_method(self):
        _clear_state()

    def test_registry_passes_args_correctly(self):
        """Verify the registry lambda maps args to handler params."""
        from tools.registry import registry

        entry = registry._tools.get("interactive_prompt")
        assert entry is not None, "interactive_prompt not registered"

        cb, event = _make_callback_that_resolves_choice()

        result_str = entry.handler(
            {
                "question": "From registry?",
                "options": _SIMPLE_OPTIONS,
                "display_type": "buttons",
                # timeout_seconds omitted → config default via `or`
            },
            callback=cb,
        )

        result = json.loads(result_str)
        assert result["status"] == "selected"
        assert result["choice"] == "yes"

    def test_registry_schema_has_required_fields(self):
        """Schema is present and has the right function name."""
        from tools.registry import registry

        entry = registry._tools.get("interactive_prompt")
        schema = entry.schema
        assert schema["name"] == "interactive_prompt"
        assert "question" in schema["parameters"]["properties"]
        assert "options" in schema["parameters"]["properties"]


class TestConcurrentSessions:
    """Multiple concurrent prompts don't interfere."""

    def setup_method(self):
        _clear_state()

    def test_two_concurrent_prompts_isolated(self):
        """Two simultaneous prompts resolve independently."""
        barrier = threading.Barrier(2, timeout=5)

        def make_cb(session_key):
            def callback(question, options, display_type, timeout_seconds, auth_policy):
                prompt_id = generate_prompt_id()
                register(
                    prompt_id=prompt_id,
                    session_key=session_key,
                    question=question,
                    options=options,
                    timeout_seconds=timeout_seconds,
                    auth_policy=auth_policy,
                )

                def _resolve():
                    barrier.wait()  # Ensure both are registered before resolving
                    time.sleep(0.05)
                    actor = ActorInfo(platform="discord", user_id=session_key,
                                      display_name=session_key)
                    resolve_choice(prompt_id, options[0]["value"], actor=actor)

                threading.Thread(target=_resolve, daemon=True).start()
                result = wait_for_response(prompt_id, timeout=timeout_seconds)
                return result.to_dict() if result else {"status": "timeout"}

            return callback

        # Run both in parallel threads
        r1_holder = [None]
        r2_holder = [None]

        def run1():
            r1_holder[0] = interactive_prompt_tool(
                question="Prompt 1?",
                options=_SIMPLE_OPTIONS,
                timeout_seconds=10,
                callback=make_cb("session-A"),
            )

        def run2():
            r2_holder[0] = interactive_prompt_tool(
                question="Prompt 2?",
                options=_SIMPLE_OPTIONS,
                timeout_seconds=10,
                callback=make_cb("session-B"),
            )

        t1 = threading.Thread(target=run1)
        t2 = threading.Thread(target=run2)
        t1.start()
        t2.start()
        t1.join(timeout=15)
        t2.join(timeout=15)

        j1 = json.loads(r1_holder[0])
        j2 = json.loads(r2_holder[0])
        assert j1["status"] == "selected"
        assert j2["status"] == "selected"
        # Different choice values = isolated sessions
        assert j1["actor"]["user_id"] == "session-A"
        assert j2["actor"]["user_id"] == "session-B"
