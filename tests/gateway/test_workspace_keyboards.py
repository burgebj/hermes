"""Tests for gateway.workspace_keyboards — keyboard builders and pending state."""

from __future__ import annotations

import pytest

from gateway.workspace_keyboards import (
    get_pending,
    media_keyboard_rows,
    pop_pending,
    route_keyboard_rows,
    store_media,
    store_summon,
    store_swarm,
    store_tts,
    summon_keyboard_rows,
    swarm_keyboard_rows,
    tts_keyboard_rows,
    voice_status_keyboard_rows,
)


# --------------------------------------------------------------------------
# Pending state store
# --------------------------------------------------------------------------


def test_store_summon_returns_cid():
    cid = store_summon("codex", "fix the tests")
    assert isinstance(cid, str)
    assert len(cid) == 12


def test_get_pending_returns_payload():
    cid = store_summon("codex", "task one")
    data = get_pending(cid)
    assert data is not None
    assert data["alias"] == "codex"
    assert data["task"] == "task one"


def test_pop_pending_removes_entry():
    cid = store_tts("hello world")
    data = pop_pending(cid)
    assert data is not None
    assert data["text"] == "hello world"
    # Should be gone now
    assert get_pending(cid) is None


def test_get_pending_unknown_returns_none():
    assert get_pending("nonexistentcid12") is None


def test_store_swarm_roundtrip():
    cid = store_swarm(["codex", "glm"], "review auth")
    data = get_pending(cid)
    assert data["aliases"] == ["codex", "glm"]
    assert data["task"] == "review auth"


def test_store_media_roundtrip():
    cid = store_media("-100", "903", "photo", "/tmp/img.jpg", "caption text")
    data = get_pending(cid)
    assert data["chat_id"] == "-100"
    assert data["thread_id"] == "903"
    assert data["media_type"] == "photo"


# --------------------------------------------------------------------------
# summon_keyboard_rows
# --------------------------------------------------------------------------


def test_summon_keyboard_rows_has_buttons():
    cid = store_summon("codex", "fix test")
    rows = summon_keyboard_rows("codex", cid)
    assert len(rows) >= 1
    all_buttons = [btn for row in rows for btn in row]
    assert len(all_buttons) >= 2


def test_summon_keyboard_callback_data_under_64():
    cid = store_summon("blazemind", "a complex task")
    rows = summon_keyboard_rows("blazemind", cid)
    for row in rows:
        for btn in row:
            cb = btn["callback_data"]
            assert len(cb.encode()) <= 64, f"Too long: {cb!r}"


def test_summon_keyboard_has_cancel():
    cid = store_summon("hermes", "task")
    rows = summon_keyboard_rows("hermes", cid)
    all_cbs = [btn["callback_data"] for row in rows for btn in row]
    assert "ws:cancel" in all_cbs


def test_summon_keyboard_has_summon_button():
    cid = store_summon("codex", "task")
    rows = summon_keyboard_rows("codex", cid)
    all_cbs = [btn["callback_data"] for row in rows for btn in row]
    assert any(c.startswith("ws:s:") for c in all_cbs)


# --------------------------------------------------------------------------
# swarm_keyboard_rows
# --------------------------------------------------------------------------


def test_swarm_keyboard_has_confirm_and_cancel():
    cid = store_swarm(["codex", "glm"], "task")
    rows = swarm_keyboard_rows(["codex", "glm"], cid)
    all_cbs = [btn["callback_data"] for row in rows for btn in row]
    assert any(c.startswith("ws:sw:") for c in all_cbs)
    assert "ws:cancel" in all_cbs


def test_swarm_keyboard_callback_data_under_64():
    cid = store_swarm(["codex", "glm", "hermes", "nexus"], "task")
    rows = swarm_keyboard_rows(["codex", "glm", "hermes", "nexus"], cid)
    for row in rows:
        for btn in row:
            cb = btn["callback_data"]
            assert len(cb.encode()) <= 64, f"Too long: {cb!r}"


# --------------------------------------------------------------------------
# route_keyboard_rows
# --------------------------------------------------------------------------


def test_route_keyboard_has_summon_and_cancel():
    rows = route_keyboard_rows("codex")
    all_cbs = [btn["callback_data"] for row in rows for btn in row]
    assert "ws:cancel" in all_cbs
    assert any(c.startswith("ws:s:") for c in all_cbs)


def test_route_keyboard_callback_data_under_64():
    rows = route_keyboard_rows("blazemind")
    for row in rows:
        for btn in row:
            assert len(btn["callback_data"].encode()) <= 64


# --------------------------------------------------------------------------
# media_keyboard_rows
# --------------------------------------------------------------------------


def test_media_keyboard_has_four_actions():
    cid = store_media("-100", "16", "photo", "/tmp/a.jpg", None)
    rows = media_keyboard_rows(cid)
    all_buttons = [btn for row in rows for btn in row]
    assert len(all_buttons) == 4


def test_media_keyboard_action_prefixes():
    cid = store_media("-100", "16", "photo", "/tmp/a.jpg", None)
    rows = media_keyboard_rows(cid)
    all_cbs = [btn["callback_data"] for row in rows for btn in row]
    assert any(c.startswith("ws:m:a:") for c in all_cbs)
    assert any(c.startswith("ws:m:o:") for c in all_cbs)
    assert any(c.startswith("ws:m:d:") for c in all_cbs)
    assert any(c.startswith("ws:m:c:") for c in all_cbs)


def test_media_keyboard_callback_data_under_64():
    cid = store_media("-100", "16", "photo", "/tmp/a.jpg", None)
    rows = media_keyboard_rows(cid)
    for row in rows:
        for btn in row:
            assert len(btn["callback_data"].encode()) <= 64


# --------------------------------------------------------------------------
# tts_keyboard_rows
# --------------------------------------------------------------------------


def test_tts_keyboard_has_read_and_cancel():
    cid = store_tts("Hello, this is a test announcement.")
    rows = tts_keyboard_rows(cid)
    all_cbs = [btn["callback_data"] for row in rows for btn in row]
    assert any(c.startswith("ws:tts:") for c in all_cbs)
    assert "ws:cancel" in all_cbs


def test_tts_keyboard_callback_data_under_64():
    cid = store_tts("text")
    rows = tts_keyboard_rows(cid)
    for row in rows:
        for btn in row:
            assert len(btn["callback_data"].encode()) <= 64


# --------------------------------------------------------------------------
# voice_status_keyboard_rows
# --------------------------------------------------------------------------


def test_voice_status_keyboard_has_three_modes():
    rows = voice_status_keyboard_rows()
    all_cbs = [btn["callback_data"] for row in rows for btn in row]
    assert "ws:voice:tts" in all_cbs
    assert "ws:voice:on" in all_cbs
    assert "ws:voice:off" in all_cbs


def test_voice_status_callback_data_under_64():
    rows = voice_status_keyboard_rows()
    for row in rows:
        for btn in row:
            assert len(btn["callback_data"].encode()) <= 64
