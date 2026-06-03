"""Tests for tools/human_input_gateway.py - Shared blocking primitive for human input.

Covers: register, wait_for_response, resolve_choice, resolve_modal,
clear_session, session isolation, custom_id helpers, and timeout.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from tools.human_input_gateway import (
    HumanInputResult,
    ActorInfo,
    FileResult,
    generate_prompt_id,
    make_component_custom_id,
    make_modal_custom_id,
    parse_custom_id,
    register,
    wait_for_response,
    resolve_choice,
    resolve_modal,
    get_entry,
    get_option_by_index,
    has_pending,
    clear_session,
    register_notify,
    unregister_notify,
    get_notify,
)


def _clear_state():
    """Reset module-level state between tests."""
    from tools.human_input_gateway import _reset_for_testing
    _reset_for_testing()


_SIMPLE_OPTIONS = [
    {"label": "Yes", "value": "yes"},
    {"label": "No", "value": "no"},
]

_MODAL_OPTIONS = [
    {
        "label": "Submit report",
        "value": "submit",
        "action": "modal",
        "modal": {
            "title": "Report Details",
            "fields": [
                {"key": "title", "label": "Title"},
                {"key": "notes", "label": "Notes"},
            ],
        },
    },
]


class TestCustomIdHelpers:
    """Tests for custom_id encode/decode helpers."""

    def test_component_roundtrip(self):
        pid = "abc123"
        aid = "opt_0"
        cid = make_component_custom_id(pid, aid)
        assert len(cid) <= 100
        parsed = parse_custom_id(cid)
        assert parsed == ("ip", pid, aid)

    def test_modal_roundtrip(self):
        pid = "abc123"
        aid = "opt_1"
        cid = make_modal_custom_id(pid, aid)
        parsed = parse_custom_id(cid)
        assert parsed == ("ip-modal", pid, aid)

    def test_parse_invalid_prefix(self):
        assert parse_custom_id("garbage") is None
        assert parse_custom_id("hp_opt_0") is None

    def test_parse_custom_id_with_colon_in_value(self):
        """Values containing colons should be preserved after split(":", 3)."""
        pid = "abc123"
        aid = "foo:bar:baz"
        cid = make_component_custom_id(pid, aid)
        parsed = parse_custom_id(cid)
        assert parsed == ("ip", pid, "foo:bar:baz")

    def test_generate_prompt_id_unique(self):
        ids = {generate_prompt_id() for _ in range(100)}
        assert len(ids) == 100


class TestRegisterAndWait:
    """Core register/wait mechanics."""

    def setup_method(self):
        _clear_state()

    def test_resolve_choice_unblocks_wait(self):
        """resolve_choice unblocks wait_for_response."""
        register("p1", "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)

        def resolver():
            time.sleep(0.05)
            resolve_choice(
                "p1", "yes",
                actor=ActorInfo(platform="test", user_id="u1", display_name="T"),
            )

        threading.Thread(target=resolver).start()
        result = wait_for_response("p1", timeout=2.0)
        assert result is not None
        assert result.status == "selected"
        assert result.choice == "yes"
        assert result.actor.display_name == "T"

    def test_resolve_modal_unblocks_wait(self):
        """resolve_modal unblocks wait_for_response with fields + files."""
        register("p2", "sk2", "Submit?", _MODAL_OPTIONS, timeout_seconds=900)

        files = [
            FileResult(
                field_key="attachment",
                attachment_id="att_1",
                filename="doc.pdf",
                content_type="application/pdf",
                size=2048,
                cached_path="/tmp/doc.pdf",
            )
        ]

        def resolver():
            time.sleep(0.05)
            resolve_modal(
                "p2",
                choice_value="submit",
                fields={"title": "My Report", "notes": "See attached"},
                files=files,
                actor=ActorInfo(platform="test", user_id="u1", display_name="T"),
            )

        threading.Thread(target=resolver).start()
        result = wait_for_response("p2", timeout=2.0)
        assert result is not None
        assert result.status == "submitted"
        assert result.choice == "submit"
        assert result.fields["title"] == "My Report"
        assert result.files[0].filename == "doc.pdf"

    def test_timeout_returns_timeout_result(self):
        """wait_for_response returns a timeout HumanInputResult on timeout."""
        register("p3", "sk3", "Q?", _SIMPLE_OPTIONS, timeout_seconds=900)
        result = wait_for_response("p3", timeout=0.2)
        assert result is not None
        assert result.status == "timeout"
        assert result.timed_out is True

    def test_resolve_unknown_id_is_noop(self):
        """resolve_choice on unknown prompt_id returns False."""
        assert resolve_choice("nonexistent", "x") is False

    def test_resolve_modal_unknown_id_is_noop(self):
        """resolve_modal on unknown prompt_id returns False."""
        assert resolve_modal("nonexistent", "x", {}, []) is False


class TestSessionManagement:
    """Session index, clear_session, has_pending."""

    def setup_method(self):
        _clear_state()

    def test_has_pending(self):
        register("p1", "sk1", "Q?", _SIMPLE_OPTIONS, timeout_seconds=900)
        assert has_pending("sk1") is True
        assert has_pending("other") is False

    def test_clear_session_unblocks_wait(self):
        """clear_session cancels pending entries and unblocks waiters."""
        register("p1", "sk1", "Q?", _SIMPLE_OPTIONS, timeout_seconds=900)

        def waiter():
            return wait_for_response("p1", timeout=10.0)

        with ThreadPoolExecutor(1) as pool:
            fut = pool.submit(waiter)
            time.sleep(0.05)
            cancelled = clear_session("sk1")
            assert cancelled == 1
            result = fut.result(timeout=2.0)
            # clear_session resolves with cancelled status
            assert result is not None
            assert result.status == "cancelled"

    def test_clear_session_isolation(self):
        """Clearing one session doesn't affect another."""
        register("p1", "sk_a", "Q?", _SIMPLE_OPTIONS, timeout_seconds=900)
        register("p2", "sk_b", "Q?", _SIMPLE_OPTIONS, timeout_seconds=900)

        cleared = clear_session("sk_a")
        assert cleared == 1
        assert has_pending("sk_b") is True
        assert has_pending("sk_a") is False

    def test_session_index_isolation(self):
        """Entries from different sessions don't leak."""
        register("pA", "alpha", "Q?", _SIMPLE_OPTIONS, timeout_seconds=900)
        register("pB", "beta", "Q?", _SIMPLE_OPTIONS, timeout_seconds=900)

        assert has_pending("alpha") is True
        assert has_pending("beta") is True


class TestGetHelpers:
    """get_entry and get_option_by_index."""

    def setup_method(self):
        _clear_state()

    def test_get_entry_returns_entry(self):
        register("p1", "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)
        entry = get_entry("p1")
        assert entry is not None
        assert entry.prompt_id == "p1"

    def test_get_entry_unknown_returns_none(self):
        assert get_entry("nonexistent") is None

    def test_get_option_by_index(self):
        register("p1", "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)
        opt = get_option_by_index("p1", 0)
        assert opt is not None
        assert opt["value"] == "yes"

    def test_get_option_out_of_range(self):
        register("p1", "sk1", "Pick?", _SIMPLE_OPTIONS, timeout_seconds=900)
        assert get_option_by_index("p1", 99) is None

    def test_get_option_unknown_prompt(self):
        assert get_option_by_index("nonexistent", 0) is None


class TestNotifyCallbacks:
    """register_notify / unregister_notify / get_notify."""

    def setup_method(self):
        _clear_state()

    def test_register_and_get_notify(self):
        cb = lambda entry: None
        register_notify("sk1", cb)
        assert get_notify("sk1") is cb

    def test_get_notify_unknown_session(self):
        assert get_notify("nonexistent") is None

    def test_unregister_notify_clears_pending(self):
        """unregister_notify calls clear_session to unwind threads."""
        register("p1", "sk1", "Q?", _SIMPLE_OPTIONS, timeout_seconds=900)

        def waiter():
            return wait_for_response("p1", timeout=10.0)

        with ThreadPoolExecutor(1) as pool:
            fut = pool.submit(waiter)
            time.sleep(0.05)
            register_notify("sk1", lambda e: None)
            unregister_notify("sk1")
            result = fut.result(timeout=2.0)
            assert result is not None
            assert result.status == "cancelled"

    def test_register_overwrites_previous(self):
        cb1 = lambda e: None
        cb2 = lambda e: None
        register_notify("sk1", cb1)
        register_notify("sk1", cb2)
        assert get_notify("sk1") is cb2

    def test_modal_custom_id_within_discord_limit(self):
        """Modal custom_id must never exceed Discord's 100-char limit."""
        pid = "x" * 16  # max prompt_id length from generate_prompt_id
        for idx in (0, 9, 24):  # single-digit, double-digit, max index
            cid = f"hermes:ip-modal:{pid}:{idx}"
            assert len(cid) <= 100, f"custom_id too long ({len(cid)}): {cid}"


class TestHumanInputResultToDict:
    """Tests for HumanInputResult.to_dict() serialization."""

    def test_minimal_result(self):
        r = HumanInputResult(status="timeout", timed_out=True)
        d = r.to_dict()
        assert d == {"status": "timeout", "choice": None, "timed_out": True}

    def test_full_result(self):
        r = HumanInputResult(
            status="submitted",
            choice="opt_1",
            timed_out=False,
            actor=ActorInfo(platform="discord", user_id="123", display_name="TestUser"),
            fields={"name": "Alice", "reason": "debug"},
            files=[
                FileResult(
                    field_key="attachment",
                    attachment_id="att_001",
                    filename="log.txt",
                    content_type="text/plain",
                    size=1024,
                    cached_path="/tmp/log.txt",
                )
            ],
        )
        d = r.to_dict()
        assert d["status"] == "submitted"
        assert d["choice"] == "opt_1"
        assert d["timed_out"] is False
        assert d["actor"] == {
            "platform": "discord",
            "user_id": "123",
            "display_name": "TestUser",
        }
        assert d["fields"] == {"name": "Alice", "reason": "debug"}
        assert len(d["files"]) == 1
        assert d["files"][0]["field_key"] == "attachment"
        assert d["files"][0]["filename"] == "log.txt"
        assert d["files"][0]["size"] == 1024

    def test_optional_fields_omitted(self):
        """Actor/fields/files should be absent from dict when None."""
        r = HumanInputResult(status="selected", choice="yes", timed_out=False)
        d = r.to_dict()
        assert "actor" not in d
        assert "fields" not in d
        assert "files" not in d
