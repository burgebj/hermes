"""Tests for ``gateway.run._build_status_thread_metadata``.

Covers status routing metadata plus approval-only requester metadata.
"""

from gateway.run import _build_exec_approval_metadata, _build_status_thread_metadata
from gateway.session import SessionSource
from gateway.config import Platform


def _src(**kwargs) -> SessionSource:
    defaults = dict(
        platform=Platform.DISCORD,
        chat_id="555",
        user_id="42",
        user_name="ada",
        thread_id=None,
        is_bot=False,
    )
    defaults.update(kwargs)
    return SessionSource(**defaults)


def test_no_metadata_when_no_thread_or_special_platform():
    src = _src(platform=Platform.SLACK, user_id=None, user_name=None)
    assert _build_status_thread_metadata(src, None) is None


def test_thread_id_only_for_non_discord_non_feishu():
    src = _src(platform=Platform.SLACK, user_id="999", user_name="bob")
    md = _build_status_thread_metadata(src, "thread-abc")
    assert md == {"thread_id": "thread-abc"}


def test_telegram_dm_topic_fallback_metadata_preserved():
    src = _src(
        platform=Platform.TELEGRAM,
        chat_id="555",
        user_id="42",
        user_name="ada",
        chat_type="dm",
        message_id="msg-source",
    )
    md = _build_status_thread_metadata(src, "topic-42", event_message_id="msg-event")
    assert md == {
        "thread_id": "topic-42",
        "telegram_dm_topic_reply_fallback": True,
        "direct_messages_topic_id": "topic-42",
        "telegram_reply_to_message_id": "msg-event",
    }


def test_telegram_dm_topic_fallback_uses_source_message_when_event_missing():
    src = _src(
        platform=Platform.TELEGRAM,
        chat_id="555",
        user_id="42",
        user_name="ada",
        chat_type="dm",
        message_id="msg-source",
    )
    md = _build_status_thread_metadata(src, "topic-42")
    assert md == {
        "thread_id": "topic-42",
        "telegram_dm_topic_reply_fallback": True,
        "direct_messages_topic_id": "topic-42",
        "telegram_reply_to_message_id": "msg-source",
    }


def test_telegram_non_dm_uses_thread_id_only():
    src = _src(platform=Platform.TELEGRAM, chat_type="group", message_id="msg-source")
    md = _build_status_thread_metadata(src, "topic-42", event_message_id="msg-event")
    assert md == {"thread_id": "topic-42"}


def test_discord_status_metadata_uses_thread_id_only():
    src = _src(platform=Platform.DISCORD, user_id="42", user_name="ada")
    md = _build_status_thread_metadata(src, "555")
    assert md == {"thread_id": "555"}


def test_discord_approval_metadata_includes_requester_id():
    src = _src(platform=Platform.DISCORD, user_id="42", user_name="ada")
    md = _build_exec_approval_metadata(src, {"thread_id": "555"})
    assert md == {"thread_id": "555", "requester_user_id": "42"}


def test_discord_approval_metadata_present_even_without_thread():
    src = _src(platform=Platform.DISCORD, user_id="42", user_name="ada")
    md = _build_exec_approval_metadata(src, None)
    assert md == {"requester_user_id": "42"}


def test_discord_approval_metadata_skips_missing_user_id():
    src = _src(platform=Platform.DISCORD, user_id=None, user_name="ada")
    md = _build_exec_approval_metadata(src, {"thread_id": "555"})
    assert md == {"thread_id": "555"}


def test_discord_approval_metadata_skips_bot_source():
    src = _src(platform=Platform.DISCORD, user_id="42", user_name="webhook", is_bot=True)
    md = _build_exec_approval_metadata(src, {"thread_id": "555"})
    assert md == {"thread_id": "555"}


def test_feishu_reply_to_message_id_only_with_thread_id():
    src = _src(platform=Platform.FEISHU, thread_id="topic-x", user_id=None, user_name=None)
    md = _build_status_thread_metadata(src, "topic-x", event_message_id="msg-1")
    assert md == {"thread_id": "topic-x", "reply_to_message_id": "msg-1"}


def test_feishu_no_reply_to_when_thread_id_missing():
    src = _src(platform=Platform.FEISHU, thread_id=None, user_id=None, user_name=None)
    md = _build_status_thread_metadata(src, None, event_message_id="msg-1")
    assert md is None
