"""Tests for the gateway-side clarify primitive (tools/clarify_gateway.py).

The clarify tool needs to ask the user a question and block the agent
thread until they respond.  These tests cover the module-level state
machine: register, wait, resolve via button, resolve via text-fallback,
"Other"-button text-capture flip, timeout, session boundary cleanup.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor



def _clear_clarify_state():
    """Reset module-level state between tests."""
    from tools import clarify_gateway as cm
    with cm._lock:
        cm._entries.clear()
        cm._session_index.clear()
        cm._notify_cbs.clear()


class TestClarifyPrimitive:
    """Core register/wait/resolve mechanics."""

    def setup_method(self):
        _clear_clarify_state()

    def test_button_choice_resolves_wait(self):
        """resolve_gateway_clarify unblocks wait_for_response with the chosen string."""
        from tools import clarify_gateway as cm

        cm.register("id1", "sk1", "Pick one", ["A", "B", "C"])

        def resolver():
            time.sleep(0.05)
            cm.resolve_gateway_clarify("id1", "B")

        threading.Thread(target=resolver).start()
        result = cm.wait_for_response("id1", timeout=2.0)
        assert result == "B"

    def test_open_ended_auto_awaits_text(self):
        """Clarify with no choices is in text-capture mode immediately."""
        from tools import clarify_gateway as cm

        entry = cm.register("id2", "sk2", "Free form?", None)
        assert entry.awaiting_text is True

        # get_pending_for_session returns the entry so the gateway
        # text-intercept can find it.
        pending = cm.get_pending_for_session("sk2")
        assert pending is not None
        assert pending.clarify_id == "id2"

    def test_button_choice_does_not_auto_await(self):
        """Multi-choice clarify should NOT be in text-capture mode initially."""
        from tools import clarify_gateway as cm

        entry = cm.register("id3", "sk3", "Pick", ["X", "Y"])
        assert entry.awaiting_text is False
        assert cm.get_pending_for_session("sk3") is None

    def test_other_button_flips_to_text_mode(self):
        """mark_awaiting_text makes get_pending_for_session find the entry."""
        from tools import clarify_gateway as cm

        cm.register("id4", "sk4", "Pick", ["X", "Y"])
        assert cm.get_pending_for_session("sk4") is None

        flipped = cm.mark_awaiting_text("id4")
        assert flipped is True

        pending = cm.get_pending_for_session("sk4")
        assert pending is not None
        assert pending.clarify_id == "id4"

    def test_mark_awaiting_text_unknown_id(self):
        """mark_awaiting_text on a non-existent id returns False."""
        from tools import clarify_gateway as cm

        assert cm.mark_awaiting_text("nope") is False

    def test_timeout_returns_none(self):
        """wait_for_response returns None when no resolve fires within the timeout."""
        from tools import clarify_gateway as cm

        cm.register("id5", "sk5", "Q?", ["A"])
        result = cm.wait_for_response("id5", timeout=0.2)
        assert result is None

    def test_resolve_unknown_id_returns_false(self):
        """resolve_gateway_clarify is idempotent on unknown ids."""
        from tools import clarify_gateway as cm

        assert cm.resolve_gateway_clarify("nope", "anything") is False

    def test_resolve_after_wait_completes_is_noop(self):
        """A late resolve on a finished entry doesn't blow up."""
        from tools import clarify_gateway as cm

        cm.register("id6", "sk6", "Q?", ["A"])
        # Time out, entry gets cleaned up
        cm.wait_for_response("id6", timeout=0.1)
        # Late button click — should not raise
        result = cm.resolve_gateway_clarify("id6", "A")
        assert result is False

    def test_clear_session_cancels_pending_entries(self):
        """clear_session unblocks blocked threads with empty response."""
        from tools import clarify_gateway as cm

        cm.register("id7", "sk7", "Q?", ["A"])

        def waiter():
            return cm.wait_for_response("id7", timeout=10.0)

        with ThreadPoolExecutor(1) as pool:
            fut = pool.submit(waiter)
            time.sleep(0.05)
            cancelled = cm.clear_session("sk7")
            assert cancelled == 1
            result = fut.result(timeout=2.0)
            # clear_session sets response="" then the wait returns it
            assert result == ""

    def test_has_pending(self):
        from tools import clarify_gateway as cm

        cm.register("id8", "sk8", "Q?", ["A"])
        assert cm.has_pending("sk8") is True
        assert cm.has_pending("nonexistent") is False

    def test_notify_register_unregister_clears_pending(self):
        """unregister_notify cancels any pending clarify so threads unwind."""
        from tools import clarify_gateway as cm

        cm.register("id9", "sk9", "Q?", ["A"])

        def waiter():
            return cm.wait_for_response("id9", timeout=10.0)

        with ThreadPoolExecutor(1) as pool:
            fut = pool.submit(waiter)
            time.sleep(0.05)

            cm.register_notify("sk9", lambda entry: None)
            cm.unregister_notify("sk9")

            # unregister_notify calls clear_session; thread unwinds
            result = fut.result(timeout=2.0)
            assert result == ""

    def test_session_index_isolation(self):
        """Entries from different sessions don't leak across get_pending lookups."""
        from tools import clarify_gateway as cm

        cm.register("idA", "alpha", "Q?", None)  # auto-await text
        cm.register("idB", "beta", "Q?", None)   # auto-await text

        a = cm.get_pending_for_session("alpha")
        b = cm.get_pending_for_session("beta")
        assert a is not None and a.clarify_id == "idA"
        assert b is not None and b.clarify_id == "idB"

    def test_clarify_timeout_config_default(self):
        """get_clarify_timeout returns 600 by default."""
        from tools import clarify_gateway as cm

        timeout = cm.get_clarify_timeout()
        # Default 600s OR whatever is in the user's loaded config.
        # Floor check: must be a positive int, not crashed.
        assert isinstance(timeout, int)
        assert timeout > 0


class TestGatewayTextIntercept:
    """The gateway's _handle_message intercepts text replies to pending clarifies."""

    def setup_method(self):
        _clear_clarify_state()

    def test_get_pending_for_session_returns_oldest_text_awaiting(self):
        """When two clarifies are pending, get_pending_for_session returns the
        first that is awaiting_text (the older one if both)."""
        from tools import clarify_gateway as cm

        # Older multi-choice (not awaiting text)
        cm.register("first", "sk", "Q1?", ["A"])
        # Newer open-ended (awaiting text)
        cm.register("second", "sk", "Q2?", None)

        pending = cm.get_pending_for_session("sk")
        # The newer one is awaiting text; the older isn't.
        assert pending is not None
        assert pending.clarify_id == "second"

        # Now flip the first to text mode too.  Both are awaiting text,
        # FIFO returns the older one.
        cm.mark_awaiting_text("first")
        pending2 = cm.get_pending_for_session("sk")
        assert pending2 is not None
        assert pending2.clarify_id == "first"
    def test_text_fallback_enables_awaiting_text_for_multi_choice(self):
        """When base send_clarify renders choices as text, mark_awaiting_text
        is called so the gateway text-intercept can capture the reply."""
        from tools import clarify_gateway as cm

        entry = cm.register("id-tf", "sk-tf", "Pick one", ["A", "B", "C"])
        # Initially, multi-choice does NOT await text (button path)
        assert entry.awaiting_text is False

        # After the base send_clarify text fallback calls mark_awaiting_text:
        flipped = cm.mark_awaiting_text("id-tf")
        assert flipped is True

        # Now get_pending_for_session should find it
        pending = cm.get_pending_for_session("sk-tf")
        assert pending is not None
        assert pending.clarify_id == "id-tf"

        # Clean up
        cm.clear_session("sk-tf")


# ===========================================================================
# Persistence (#32762) — entries survive a SIGTERM restart
# ===========================================================================

class TestClarifyPersistence:
    """Pending clarify entries must survive a gateway restart so late
    button taps are acknowledged instead of silently dropped (#32762).
    """

    def setup_method(self):
        _clear_clarify_state()

    def _isolate_persist(self, tmp_path):
        from tools import clarify_gateway as cm
        path = tmp_path / "clarify_pending.json"
        cm.set_persist_path(path)
        return path

    def _reset_persist(self):
        from tools import clarify_gateway as cm
        cm.set_persist_path(None)

    def test_register_writes_persist_file(self, tmp_path):
        """register() flushes the entry to the JSON sidecar."""
        from tools import clarify_gateway as cm
        import json

        path = self._isolate_persist(tmp_path)
        try:
            cm.register("p1", "sk-p1", "Pick?", ["a", "b"])
            assert path.exists()
            payload = json.loads(path.read_text())
            ids = [e["clarify_id"] for e in payload["entries"]]
            assert "p1" in ids
        finally:
            self._reset_persist()

    def test_restore_round_trip_survives_simulated_restart(self, tmp_path):
        """Register → wipe in-memory state (SIGTERM) → restore_pending
        rebuilds _entries with restored=True; resolve still acknowledges
        the late tap.
        """
        from tools import clarify_gateway as cm

        path = self._isolate_persist(tmp_path)
        try:
            cm.register("p2", "sk-p2", "Pick?", ["x", "y"])
            assert path.exists()

            # Simulate SIGTERM — new process boots with empty memory.
            with cm._lock:
                cm._entries.clear()
                cm._session_index.clear()

            # New gateway calls restore_pending on startup.
            restored = cm.restore_pending(timeout_seconds=600.0)
            assert len(restored) == 1
            entry = restored[0]
            assert entry.clarify_id == "p2"
            assert entry.session_key == "sk-p2"
            assert entry.choices == ["x", "y"]
            assert entry.restored is True
            assert cm.was_restored("p2") is True

            # Late button tap now lands on the restored entry instead of
            # returning False — this is the user-visible bug from #32762.
            # Capture the entry reference before resolve, since restored
            # entries are cleaned out of _entries immediately on resolve
            # (no waiter to do it).
            with cm._lock:
                live_entry = cm._entries["p2"]
            ok = cm.resolve_gateway_clarify("p2", "x")
            assert ok is True
            assert live_entry.response == "x"
            assert live_entry.event.is_set()
            with cm._lock:
                assert "p2" not in cm._entries
            # Persist file no longer references the resolved entry.
            import json
            payload = json.loads(path.read_text())
            assert all(e["clarify_id"] != "p2" for e in payload["entries"])
        finally:
            self._reset_persist()

    def test_restore_drops_expired_entries(self, tmp_path):
        """Entries older than the configured timeout are dropped — the
        agent that asked has long given up."""
        from tools import clarify_gateway as cm
        import time as _t

        path = self._isolate_persist(tmp_path)
        try:
            entry = cm.register("p3", "sk-p3", "Pick?", ["a"])
            # Backdate the on-disk record so restore_pending sees it as
            # past-timeout.
            import json
            payload = json.loads(path.read_text())
            for raw in payload["entries"]:
                raw["registered_at"] = _t.time() - 3600.0
            path.write_text(json.dumps(payload))

            # Clear in-memory and restore with a 600s timeout.
            with cm._lock:
                cm._entries.clear()
                cm._session_index.clear()
            restored = cm.restore_pending(timeout_seconds=600.0)
            assert restored == []
            assert "p3" not in cm._entries
            # And the persist file no longer references the dropped id.
            payload2 = json.loads(path.read_text())
            assert all(e["clarify_id"] != "p3" for e in payload2["entries"])
        finally:
            self._reset_persist()

    def test_wait_for_response_removes_persisted_entry(self, tmp_path):
        """When wait_for_response times out, the persisted record is
        removed so the next restart doesn't replay a stale entry."""
        from tools import clarify_gateway as cm
        import json

        path = self._isolate_persist(tmp_path)
        try:
            cm.register("p4", "sk-p4", "Pick?", ["a"])
            assert path.exists()
            cm.wait_for_response("p4", timeout=0.05)
            payload = json.loads(path.read_text())
            assert all(e["clarify_id"] != "p4" for e in payload["entries"])
        finally:
            self._reset_persist()

    def test_clear_session_removes_persisted_entries(self, tmp_path):
        """clear_session() prunes the JSON sidecar so suspended sessions
        don't leave ghost entries that a future restart would restore."""
        from tools import clarify_gateway as cm
        import json

        path = self._isolate_persist(tmp_path)
        try:
            cm.register("p5", "sk-p5", "Pick?", ["a"])
            cm.register("p6", "sk-p5", "Pick?", ["b"])
            cm.clear_session("sk-p5")
            payload = json.loads(path.read_text())
            ids = [e["clarify_id"] for e in payload["entries"]]
            assert "p5" not in ids
            assert "p6" not in ids
        finally:
            self._reset_persist()

    def test_restore_skips_duplicate_in_memory_entry(self, tmp_path):
        """If a clarify_id is already live in memory, restore_pending
        must not clobber the live entry (which has a real Event a thread
        may be waiting on)."""
        from tools import clarify_gateway as cm

        path = self._isolate_persist(tmp_path)
        try:
            live = cm.register("p7", "sk-p7", "Q?", ["a"])
            # Persist file now exists.  Restoring with the live entry
            # still in _entries must be a no-op for that id.
            restored = cm.restore_pending(timeout_seconds=600.0)
            assert restored == []
            with cm._lock:
                assert cm._entries["p7"] is live
        finally:
            self._reset_persist()

    def test_was_restored_false_for_live_entry(self, tmp_path):
        """was_restored() distinguishes live entries from rehydrated ones."""
        from tools import clarify_gateway as cm

        path = self._isolate_persist(tmp_path)
        try:
            cm.register("p8", "sk-p8", "Q?", ["a"])
            assert cm.was_restored("p8") is False
            assert cm.was_restored("nope") is False
        finally:
            self._reset_persist()
