"""Gateway session-scoped model/reasoning overrides survive restarts."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import gateway.run as gateway_run
from gateway.config import Platform
from gateway.platforms.base import MessageEvent
from gateway.session import SessionSource, build_session_key


class _FakeRuntimeOverrideDB:
    def __init__(self):
        self.model_overrides = {}
        self.reasoning_overrides = {}
        self.set_model_calls = []
        self.set_reasoning_calls = []
        self.del_model_calls = []
        self.del_reasoning_calls = []

    def get_gateway_session_model_overrides(self):
        return dict(self.model_overrides)

    def set_gateway_session_model_override(self, session_key, override):
        self.set_model_calls.append((session_key, dict(override)))
        self.model_overrides[session_key] = dict(override)

    def del_gateway_session_model_override(self, session_key):
        self.del_model_calls.append(session_key)
        self.model_overrides.pop(session_key, None)

    def get_gateway_session_reasoning_overrides(self):
        return dict(self.reasoning_overrides)

    def set_gateway_session_reasoning_override(self, session_key, override):
        self.set_reasoning_calls.append((session_key, dict(override)))
        self.reasoning_overrides[session_key] = dict(override)

    def del_gateway_session_reasoning_override(self, session_key):
        self.del_reasoning_calls.append(session_key)
        self.reasoning_overrides.pop(session_key, None)


def _make_source(thread_id: str | None = "351260") -> SessionSource:
    return SessionSource(
        platform=Platform.TELEGRAM,
        user_id="273403055",
        chat_id="273403055",
        user_name="Maxim",
        chat_type="dm",
        thread_id=thread_id,
    )


def _make_event(text: str = "/model gpt-5.5 --provider openai-codex") -> MessageEvent:
    return MessageEvent(text=text, source=_make_source(), message_id="m1")


def _make_runner(session_db=None):
    runner = object.__new__(gateway_run.GatewayRunner)
    runner.adapters = {}
    runner._session_db = session_db
    runner._session_model_overrides = {}
    runner._session_reasoning_overrides = {}
    runner._pending_model_notes = {}
    runner._agent_cache = {}
    runner._agent_cache_lock = None
    runner._evict_cached_agent = MagicMock()
    return runner


def _model_override(model="gpt-5.5"):
    return {
        "model": model,
        "provider": "openai-codex",
        "api_key": "***",
        "base_url": "https://chatgpt.com/backend-api/codex",
        "api_mode": "codex_responses",
    }


def test_sessiondb_persists_gateway_model_and_reasoning_overrides(tmp_path):
    """Persisted overrides survive closing/reopening state.db."""
    from hermes_state import SessionDB

    db_path = tmp_path / "state.db"
    session_key = "agent:main:telegram:dm:273403055:351260"
    model_override = _model_override()
    reasoning_override = {"enabled": True, "effort": "xhigh"}

    db = SessionDB(db_path=db_path)
    db.set_gateway_session_model_override(session_key, model_override)
    db.set_gateway_session_reasoning_override(session_key, reasoning_override)
    db.close()

    reopened = SessionDB(db_path=db_path)
    try:
        assert reopened.get_gateway_session_model_overrides()[session_key] == model_override
        assert reopened.get_gateway_session_reasoning_overrides()[session_key] == reasoning_override
    finally:
        reopened.close()


def test_gateway_loads_persisted_runtime_overrides_on_startup():
    """Gateway startup restores DB-backed model and reasoning overrides into memory."""
    session_key = build_session_key(_make_source())
    db = _FakeRuntimeOverrideDB()
    db.model_overrides[session_key] = _model_override()
    db.reasoning_overrides[session_key] = {"enabled": True, "effort": "xhigh"}
    runner = _make_runner(db)

    runner._load_persisted_session_runtime_overrides()

    assert runner._session_model_overrides[session_key] == _model_override()
    assert runner._session_reasoning_overrides[session_key] == {"enabled": True, "effort": "xhigh"}


@pytest.mark.asyncio
async def test_text_model_switch_writes_session_override_through_to_db(monkeypatch):
    """`/model <name>` text path must persist the per-topic session override."""
    db = _FakeRuntimeOverrideDB()
    runner = _make_runner(db)

    monkeypatch.setattr(
        gateway_run,
        "_load_gateway_config",
        lambda: {"model": {"default": "gpt-5.4", "provider": "openai-codex"}},
    )

    import hermes_cli.model_switch as model_switch

    monkeypatch.setattr(
        model_switch,
        "switch_model",
        lambda **_kwargs: SimpleNamespace(
            success=True,
            new_model="gpt-5.5",
            target_provider="openai-codex",
            api_key="***",
            base_url="https://chatgpt.com/backend-api/codex",
            api_mode="codex_responses",
            provider_label="OpenAI Codex",
            model_info=None,
            warning_message=None,
        ),
    )

    await runner._handle_model_command(_make_event())

    session_key = build_session_key(_make_source())
    assert db.set_model_calls == [(session_key, _model_override())]
    assert runner._session_model_overrides[session_key] == _model_override()


def test_reasoning_override_set_and_clear_write_through_to_db():
    """Session reasoning overrides are persisted and removed with the in-memory value."""
    db = _FakeRuntimeOverrideDB()
    runner = _make_runner(db)
    session_key = build_session_key(_make_source())

    runner._set_session_reasoning_override(session_key, {"enabled": True, "effort": "xhigh"})
    runner._set_session_reasoning_override(session_key, None)

    assert db.set_reasoning_calls == [(session_key, {"enabled": True, "effort": "xhigh"})]
    assert db.del_reasoning_calls == [session_key]
    assert session_key not in runner._session_reasoning_overrides


def test_clearing_session_runtime_overrides_removes_both_db_entries():
    """/new-style cleanup clears model and reasoning overrides for only that session."""
    session_key = build_session_key(_make_source())
    other_session_key = build_session_key(_make_source(thread_id="other"))
    db = _FakeRuntimeOverrideDB()
    runner = _make_runner(db)
    runner._session_model_overrides = {
        session_key: _model_override(),
        other_session_key: _model_override("gpt-5.4"),
    }
    runner._session_reasoning_overrides = {
        session_key: {"enabled": True, "effort": "xhigh"},
        other_session_key: {"enabled": True, "effort": "low"},
    }

    runner._clear_session_runtime_overrides(session_key)

    assert db.del_model_calls == [session_key]
    assert db.del_reasoning_calls == [session_key]
    assert session_key not in runner._session_model_overrides
    assert session_key not in runner._session_reasoning_overrides
    assert other_session_key in runner._session_model_overrides
    assert other_session_key in runner._session_reasoning_overrides
