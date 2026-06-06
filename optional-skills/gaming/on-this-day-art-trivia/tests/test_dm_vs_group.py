"""Group-vs-DM routing for the inbound-message plugin path.

The plugin's ``_on_pre_gateway_dispatch`` should:

* In DMs with an active challenge: treat any plain-text message as a guess
  and consume it via ``action: skip``.
* In groups: only consume messages that reply to the challenge image.

We exercise the function with synthetic event objects that mimic the
attribute surface Hermes provides.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

# Make the plugin importable.
ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = ROOT / "plugin"
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))


def _make_event(*, text, chat_id, chat_type, user_id, reply_to=None):
    src = SimpleNamespace(
        platform=SimpleNamespace(value="telegram"),
        chat_id=chat_id,
        chat_type=chat_type,
        user_id=user_id,
        user_name="alice",
        reply_to_message_id=reply_to,
    )
    return SimpleNamespace(text=text, source=src, reply_to_message_id=reply_to, metadata={})


def _make_gateway():
    return SimpleNamespace(adapters={})


def test_dm_plain_text_is_consumed_when_active(tmp_db):
    from scripts import state
    from on_this_day_art_trivia import plugin as plug

    cid = state.create_challenge(
        platform="telegram", chat_id="dm-1", scope="dm", user_id="user-1",
        event_date="April 28", event_year=1967,
        location="Houston", country="United States",
        canonical_answer="Muhammad Ali refused induction",
        short_summary="Muhammad Ali refused induction.",
        full_description=None, source="britannica",
        aliases=[("Muhammad Ali refused induction", 1)],
    )

    ev = _make_event(text="Muhammad Ali refused induction", chat_id="dm-1",
                     chat_type="dm", user_id="user-1")
    out = plug._on_pre_gateway_dispatch(event=ev, gateway=_make_gateway())
    assert isinstance(out, dict)
    assert out.get("action") == "skip"
    state.resolve_challenge(cid, "expired")  # cleanup


def test_dm_with_no_active_challenge_falls_through(tmp_db):
    from on_this_day_art_trivia import plugin as plug

    ev = _make_event(text="hello bot", chat_id="dm-2", chat_type="dm", user_id="u2")
    out = plug._on_pre_gateway_dispatch(event=ev, gateway=_make_gateway())
    assert out is None


def test_group_only_intercepts_replies_to_challenge(tmp_db):
    from scripts import state
    from on_this_day_art_trivia import plugin as plug

    cid = state.create_challenge(
        platform="telegram", chat_id="group-1", scope="group", user_id=None,
        event_date="April 28", event_year=1967,
        location="Houston", country="United States",
        canonical_answer="Muhammad Ali refused induction",
        short_summary=None, full_description=None, source="britannica",
        aliases=[("Muhammad Ali refused induction", 1)],
    )
    state.attach_telegram_message_id(cid, "msg-42")

    ev_drive_by = _make_event(text="random group chat", chat_id="group-1",
                              chat_type="group", user_id="u1")
    assert plug._on_pre_gateway_dispatch(event=ev_drive_by, gateway=_make_gateway()) is None

    ev_reply = _make_event(text="ali refused", chat_id="group-1",
                           chat_type="group", user_id="u1", reply_to="msg-42")
    out = plug._on_pre_gateway_dispatch(event=ev_reply, gateway=_make_gateway())
    assert isinstance(out, dict)
    assert out.get("action") == "skip"


def test_slash_commands_pass_through(tmp_db):
    from on_this_day_art_trivia import plugin as plug

    ev = _make_event(text="/help", chat_id="dm-3", chat_type="dm", user_id="u3")
    assert plug._on_pre_gateway_dispatch(event=ev, gateway=_make_gateway()) is None
