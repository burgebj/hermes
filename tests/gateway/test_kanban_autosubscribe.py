"""Gateway auto-subscription for Kanban cards created via the kanban_create tool.

A model-issued ``kanban_create`` (as opposed to the ``/kanban create`` slash
command) leaves ``kanban_notify_subs`` empty, so the worker's terminal event is
delivered to no one. ``GatewayRunner._subscribe_chat_to_kanban_cards`` closes
that gap, scoped to the current turn so a long-lived session transcript never
re-subscribes previously created cards.
"""
import asyncio
import json
from types import SimpleNamespace

from gateway.config import Platform
from gateway.run import GatewayRunner
from hermes_cli import kanban_db as kb


def _runner():
    runner = GatewayRunner.__new__(GatewayRunner)
    runner._kanban_notifier_profile = "main"
    return runner


def _source(platform=Platform.DISCORD, chat_id="chat-1", thread_id="thread-1", user_id="user-1"):
    return SimpleNamespace(
        platform=platform, chat_id=chat_id, thread_id=thread_id, user_id=user_id
    )


def _create_msgs(call_id, task_id, *, ok=True, board=None, args=None):
    result = {"task_id": task_id}
    result["ok" if ok else "error"] = True if ok else "kanban_create: failed"
    if board:
        result["board"] = board
    return [
        {
            "role": "assistant",
            "tool_calls": [{
                "id": call_id, "type": "function",
                "function": {"name": "kanban_create",
                             "arguments": json.dumps(args or {"title": "t", "assignee": "worker"})},
            }],
        },
        {"role": "tool", "tool_call_id": call_id, "content": json.dumps(result)},
    ]


def test_subscribes_card_created_this_turn(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_KANBAN_DB", str(tmp_path / "a.db"))
    kb.init_db()
    conn = kb.connect()
    try:
        tid = kb.create_task(conn, title="tool-created", assignee="worker")
    finally:
        conn.close()

    subscribed = asyncio.run(
        _runner()._subscribe_chat_to_kanban_cards(_source(), _create_msgs("c1", tid))
    )

    assert subscribed == [tid]
    conn = kb.connect()
    try:
        subs = kb.list_notify_subs(conn, tid)
    finally:
        conn.close()
    assert len(subs) == 1
    assert subs[0]["platform"] == "discord"
    assert subs[0]["chat_id"] == "chat-1"
    assert subs[0]["thread_id"] == "thread-1"
    assert subs[0]["user_id"] == "user-1"
    assert subs[0]["notifier_profile"] == "main"


def test_turn_start_excludes_prior_turn_cards(tmp_path, monkeypatch):
    """The key guarantee: cards created in earlier turns of a long-lived
    session are NOT re-subscribed; only cards at/after ``turn_start`` are."""
    monkeypatch.setenv("HERMES_KANBAN_DB", str(tmp_path / "b.db"))
    kb.init_db()
    conn = kb.connect()
    try:
        old_tid = kb.create_task(conn, title="old", assignee="worker")
        new_tid = kb.create_task(conn, title="new", assignee="worker")
    finally:
        conn.close()

    # Simulated long-lived transcript: a prior turn that created old_tid, then
    # this turn (after the second user message) that created new_tid.
    messages = (
        [{"role": "user", "content": "first request"}]
        + _create_msgs("c_old", old_tid)
        + [{"role": "user", "content": "second request"}]
        + _create_msgs("c_new", new_tid)
    )
    turn_start = 4  # index of the second user message

    subscribed = asyncio.run(
        _runner()._subscribe_chat_to_kanban_cards(_source(), messages, turn_start=turn_start)
    )

    assert subscribed == [new_tid]
    conn = kb.connect()
    try:
        assert kb.list_notify_subs(conn, old_tid) == []
        assert len(kb.list_notify_subs(conn, new_tid)) == 1
    finally:
        conn.close()


def test_ignores_failed_create(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_KANBAN_DB", str(tmp_path / "c.db"))
    kb.init_db()
    subscribed = asyncio.run(
        _runner()._subscribe_chat_to_kanban_cards(
            _source(), _create_msgs("c1", "t_deadbeef", ok=False)
        )
    )
    assert subscribed == []
    conn = kb.connect()
    try:
        assert kb.list_notify_subs(conn) == []
    finally:
        conn.close()


def test_respects_result_board_field(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("HERMES_KANBAN_DB", raising=False)
    kb._INITIALIZED_PATHS.clear()
    conn = kb.connect(board="custom-board")
    try:
        tid = kb.create_task(conn, title="tool-created", assignee="worker")
    finally:
        conn.close()

    subscribed = asyncio.run(
        _runner()._subscribe_chat_to_kanban_cards(
            _source(platform=Platform.TELEGRAM, chat_id="tg", thread_id=""),
            _create_msgs("c1", tid, board="custom-board"),
        )
    )

    assert subscribed == [tid]
    default_conn, custom_conn = kb.connect(), kb.connect(board="custom-board")
    try:
        assert kb.list_notify_subs(default_conn) == []
        subs = kb.list_notify_subs(custom_conn, tid)
    finally:
        default_conn.close()
        custom_conn.close()
    assert len(subs) == 1
    assert subs[0]["platform"] == "telegram"
    assert subs[0]["thread_id"] == ""


def test_ignores_malformed_tool_content(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_KANBAN_DB", str(tmp_path / "d.db"))
    kb.init_db()
    messages = [
        {"role": "assistant", "tool_calls": [{
            "id": "c1", "type": "function",
            "function": {"name": "kanban_create", "arguments": "{not-json"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "{not-json"},
    ]
    subscribed = asyncio.run(
        _runner()._subscribe_chat_to_kanban_cards(_source(), messages)
    )
    assert subscribed == []
    conn = kb.connect()
    try:
        assert kb.list_notify_subs(conn) == []
    finally:
        conn.close()
