import asyncio
import sys
import threading
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import gateway.run as gateway_run
from gateway.config import Platform
from gateway.session import SessionSource


SESSION_KEY = "agent:main:telegram:dm:12345"


class _SaveTrackingSessionStore:
    def __init__(self):
        self.entry = SimpleNamespace(session_id="session-before-compression")
        self._entries = {SESSION_KEY: self.entry}
        self.save_calls = 0

    def _save(self):
        self.save_calls += 1


class _CompressionThenFailureAgent:
    def __init__(self, **kwargs):
        self.session_id = kwargs["session_id"]
        self.model = kwargs["model"]
        self.tools = []
        self.context_compressor = SimpleNamespace(
            last_prompt_tokens=4321,
            context_length=200000,
        )
        self.session_prompt_tokens = 4321
        self.session_completion_tokens = 0

    def run_conversation(self, user_message, conversation_history=None, task_id=None):
        self.session_id = "session-after-compression"
        return {
            "failed": True,
            "error": (
                "APIConnectionError: Codex auxiliary Responses stream exceeded "
                "120.0s total timeout"
            ),
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "[Context compressed: previous long transcript was "
                        "summarized before retry]"
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            "api_calls": 1,
        }

    def interrupt(self, *_args, **_kwargs):
        pass


class _ImmediateStreamConsumer:
    final_response_sent = False

    def __init__(self, *_args, **_kwargs):
        pass

    async def run(self):
        return None

    def finish(self):
        pass


class _QuietAdapter:
    SUPPORTS_MESSAGE_EDITING = True
    _pending_messages = {}

    def get_pending_message(self, _session_key):
        return None


def _install_fake_agent(monkeypatch):
    fake_run_agent = types.ModuleType("run_agent")
    fake_run_agent.AIAgent = _CompressionThenFailureAgent
    monkeypatch.setitem(sys.modules, "run_agent", fake_run_agent)


def _make_runner(session_store):
    runner = object.__new__(gateway_run.GatewayRunner)
    runner.adapters = {
        Platform.TELEGRAM: _QuietAdapter(),
    }
    runner._ephemeral_system_prompt = ""
    runner._prefill_messages = []
    runner._reasoning_config = None
    runner._provider_routing = {}
    runner._fallback_model = None
    runner._running_agents = {}
    runner._pending_model_notes = {}
    runner._pending_skills_reload_notes = {}
    runner._session_db = None
    runner._agent_cache = {}
    runner._agent_cache_lock = threading.Lock()
    runner._session_model_overrides = {}
    runner._draining = False
    runner.config = SimpleNamespace(streaming=None)
    runner.hooks = SimpleNamespace(loaded_hooks=False, emit=AsyncMock())
    runner.session_store = session_store
    runner._get_proxy_url = lambda: None
    runner._resolve_session_agent_runtime = lambda **_kwargs: (
        "gpt-5.4",
        {
            "provider": "openai-codex",
            "api_mode": "codex_responses",
            "base_url": "https://chatgpt.com/backend-api/codex",
            "api_key": "token",
        },
    )
    runner._resolve_session_reasoning_config = lambda **_kwargs: None
    runner._resolve_turn_agent_config = lambda message, model, runtime: {
        "model": model,
        "runtime": runtime,
    }
    runner._load_service_tier = lambda: None
    runner._agent_config_signature = lambda *_args, **_kwargs: ("sig",)
    runner._extract_cache_busting_config = lambda _config: ()
    runner._thread_metadata_for_source = lambda *_args, **_kwargs: None
    runner._is_telegram_topic_lane = lambda _source: False
    runner._release_running_agent_state = MagicMock()
    return runner


def _source():
    return SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="12345",
        chat_type="dm",
        user_id="user-1",
    )


def test_failed_turn_still_syncs_compression_session_split(monkeypatch):
    """A post-compression API failure must not leave the session store on the
    stale pre-compression transcript.

    Production sample:

    - Preflight compression fires around 136k tokens.
    - The agent rotates ``session_id`` while compacting.
    - The follow-up Codex call times out and returns no ``final_response``.

    Before this regression fix, the early failure return skipped the session
    split sync block, so the next inbound message loaded the old long session
    again and the context kept growing.
    """
    _install_fake_agent(monkeypatch)
    monkeypatch.setenv("HERMES_TOOL_PROGRESS_MODE", "off")
    monkeypatch.setenv("HERMES_AGENT_TIMEOUT", "0")
    monkeypatch.setattr(gateway_run, "_load_gateway_config", lambda: {})
    monkeypatch.setattr(
        "gateway.stream_consumer.GatewayStreamConsumer",
        _ImmediateStreamConsumer,
    )

    import hermes_cli.tools_config as tools_config

    monkeypatch.setattr(
        tools_config,
        "_get_platform_tools",
        lambda *_args, **_kwargs: {"core"},
    )

    session_store = _SaveTrackingSessionStore()
    runner = _make_runner(session_store)

    result = asyncio.run(
        asyncio.wait_for(
            runner._run_agent(
                message="continue",
                context_prompt="",
                history=[
                    {"role": "user", "content": "old question"},
                    {"role": "assistant", "content": "old answer"},
                ],
                source=_source(),
                session_id="session-before-compression",
                session_key=SESSION_KEY,
            ),
            timeout=2,
        ),
    )

    assert result["failed"] is True
    assert result["session_id"] == "session-after-compression"
    assert result["history_offset"] == 0
    assert session_store.entry.session_id == "session-after-compression"
    assert session_store.save_calls == 1
