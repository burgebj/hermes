"""Tests for gateway.checklist_store — persistent emulated checklists."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from gateway.checklist_store import (
    STANDARD_AGENT_CHECKLIST,
    STANDARD_REVIEW_CHECKLIST,
    build_checklist_keyboard_rows,
    create_checklist,
    delete_checklist,
    get_checklist,
    render_checklist_text,
    toggle_item,
)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture()
def tmp_checklist_dir(tmp_path):
    """Redirect checklist storage to a temp directory."""
    with patch("gateway.checklist_store._checklist_dir", return_value=tmp_path):
        yield tmp_path


# --------------------------------------------------------------------------
# create_checklist
# --------------------------------------------------------------------------


def test_create_checklist_returns_id(tmp_checklist_dir):
    cl_id = create_checklist("Test", ["item A", "item B"], chat_id="100", thread_id="1")
    assert isinstance(cl_id, str)
    assert len(cl_id) == 12  # uuid4 hex[:12]


def test_create_checklist_persists_file(tmp_checklist_dir):
    cl_id = create_checklist("CI", STANDARD_AGENT_CHECKLIST, chat_id="200")
    path = tmp_checklist_dir / f"{cl_id}.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["title"] == "CI"
    assert data["items"] == STANDARD_AGENT_CHECKLIST


def test_create_checklist_done_initialized_false(tmp_checklist_dir):
    cl_id = create_checklist("Review", ["a", "b", "c"], chat_id="1")
    data = get_checklist(cl_id)
    assert data["done"] == [False, False, False]


def test_create_checklist_stores_chat_and_thread(tmp_checklist_dir):
    cl_id = create_checklist("T", ["x"], chat_id="-100123", thread_id="903", user_id="42")
    data = get_checklist(cl_id)
    assert data["chat_id"] == "-100123"
    assert data["thread_id"] == "903"
    assert data["user_id"] == "42"


# --------------------------------------------------------------------------
# get_checklist
# --------------------------------------------------------------------------


def test_get_checklist_returns_none_for_unknown(tmp_checklist_dir):
    assert get_checklist("nonexistentid12") is None


def test_get_checklist_returns_dict(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a"], chat_id="1")
    data = get_checklist(cl_id)
    assert isinstance(data, dict)
    assert data["id"] == cl_id


# --------------------------------------------------------------------------
# toggle_item
# --------------------------------------------------------------------------


def test_toggle_item_marks_done(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a", "b", "c"], chat_id="1")
    result = toggle_item(cl_id, 1)
    assert result is not None
    assert result["done"][1] is True


def test_toggle_item_unmarked_when_toggled_twice(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a", "b"], chat_id="1")
    toggle_item(cl_id, 0)
    result = toggle_item(cl_id, 0)
    assert result["done"][0] is False


def test_toggle_item_returns_none_for_unknown(tmp_checklist_dir):
    assert toggle_item("nonexistent12", 0) is None


def test_toggle_item_out_of_range_is_no_op(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a"], chat_id="1")
    result = toggle_item(cl_id, 99)
    assert result is not None
    assert result["done"] == [False]


def test_toggle_item_persists(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a", "b"], chat_id="1")
    toggle_item(cl_id, 0)
    # Reload from disk
    data = get_checklist(cl_id)
    assert data["done"][0] is True


# --------------------------------------------------------------------------
# delete_checklist
# --------------------------------------------------------------------------


def test_delete_checklist_removes_file(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a"], chat_id="1")
    assert delete_checklist(cl_id) is True
    assert get_checklist(cl_id) is None


def test_delete_checklist_returns_false_for_unknown(tmp_checklist_dir):
    assert delete_checklist("nonexistent") is False


# --------------------------------------------------------------------------
# render_checklist_text
# --------------------------------------------------------------------------


def test_render_checklist_text_shows_title(tmp_checklist_dir):
    cl_id = create_checklist("My Checklist", ["a", "b"], chat_id="1")
    data = get_checklist(cl_id)
    text = render_checklist_text(data)
    assert "My Checklist" in text


def test_render_checklist_text_unchecked_items_show_checkbox(tmp_checklist_dir):
    cl_id = create_checklist("T", ["item one", "item two"], chat_id="1")
    data = get_checklist(cl_id)
    text = render_checklist_text(data)
    assert "☐" in text


def test_render_checklist_text_checked_item_shows_checkmark(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a", "b"], chat_id="1")
    toggle_item(cl_id, 0)
    data = get_checklist(cl_id)
    text = render_checklist_text(data)
    assert "✅" in text


def test_render_checklist_text_shows_progress(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a", "b", "c"], chat_id="1")
    toggle_item(cl_id, 0)
    data = get_checklist(cl_id)
    text = render_checklist_text(data)
    assert "1/3" in text


# --------------------------------------------------------------------------
# build_checklist_keyboard_rows
# --------------------------------------------------------------------------


def test_build_keyboard_has_one_row_per_item_plus_close(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a", "b", "c"], chat_id="1")
    data = get_checklist(cl_id)
    rows = build_checklist_keyboard_rows(data)
    # 3 items + 1 close row
    assert len(rows) == 4


def test_build_keyboard_callback_data_under_64_bytes(tmp_checklist_dir):
    cl_id = create_checklist("T", STANDARD_AGENT_CHECKLIST, chat_id="1")
    data = get_checklist(cl_id)
    rows = build_checklist_keyboard_rows(data)
    for row in rows:
        for btn in row:
            cb = btn["callback_data"]
            assert len(cb.encode()) <= 64, f"callback_data too long: {cb!r} ({len(cb.encode())} bytes)"


def test_build_keyboard_close_row_last(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a", "b"], chat_id="1")
    data = get_checklist(cl_id)
    rows = build_checklist_keyboard_rows(data)
    last_btn = rows[-1][0]
    assert "close" in last_btn["callback_data"].lower() or "Close" in last_btn["text"]


def test_build_keyboard_toggle_prefix(tmp_checklist_dir):
    cl_id = create_checklist("T", ["a"], chat_id="1")
    data = get_checklist(cl_id)
    rows = build_checklist_keyboard_rows(data)
    toggle_cb = rows[0][0]["callback_data"]
    assert toggle_cb.startswith("chk:t:")


# --------------------------------------------------------------------------
# Standard checklists
# --------------------------------------------------------------------------


def test_standard_agent_checklist_has_six_items():
    assert len(STANDARD_AGENT_CHECKLIST) == 6


def test_standard_review_checklist_has_four_items():
    assert len(STANDARD_REVIEW_CHECKLIST) == 4
