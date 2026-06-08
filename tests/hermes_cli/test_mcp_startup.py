"""Regression tests for bounded/lazy CLI MCP startup."""

from __future__ import annotations

from argparse import Namespace
import sys
import threading
import time
import types

import pytest

import cli as cli_mod
from hermes_cli import main as main_mod
from hermes_cli import mcp_startup


@pytest.fixture(autouse=True)
def _reset_mcp_startup_state():
    saved_started = mcp_startup._mcp_discovery_started
    saved_thread = mcp_startup._mcp_discovery_thread
    try:
        mcp_startup._mcp_discovery_started = False
        mcp_startup._mcp_discovery_thread = None
        yield
    finally:
        thread = mcp_startup._mcp_discovery_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)
        mcp_startup._mcp_discovery_started = saved_started
        mcp_startup._mcp_discovery_thread = saved_thread


def _agent_args(**overrides) -> Namespace:
    base = {
        "accept_hooks": False,
        "command": "chat",
        "cron_command": None,
        "gateway_command": None,
        "mcp_action": None,
        "tui": False,
    }
    base.update(overrides)
    return Namespace(**base)


def test_prepare_agent_startup_backgrounds_blocking_mcp_for_chat(monkeypatch):
    stop = threading.Event()
    calls = {"mcp": 0}

    def _blocking_discover():
        calls["mcp"] += 1
        stop.wait()

    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.plugins",
        types.SimpleNamespace(discover_plugins=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.config",
        types.SimpleNamespace(
            read_raw_config=lambda: {"mcp_servers": {"demo": {"transport": "stdio"}}},
            load_config=lambda: {},
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "agent.shell_hooks",
        types.SimpleNamespace(register_from_config=lambda *_a, **_k: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "tools.mcp_tool",
        types.SimpleNamespace(discover_mcp_tools=_blocking_discover),
    )

    try:
        start = time.monotonic()
        main_mod._prepare_agent_startup(_agent_args())
        elapsed = time.monotonic() - start
        assert elapsed < 0.2
        assert calls["mcp"] == 1
        assert mcp_startup._mcp_discovery_thread is not None
        assert mcp_startup._mcp_discovery_thread.is_alive()
    finally:
        stop.set()


def test_prepare_agent_startup_skips_mcp_bootstrap_for_tui_chat(monkeypatch):
    calls = {"mcp": 0}

    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.plugins",
        types.SimpleNamespace(discover_plugins=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.config",
        types.SimpleNamespace(load_config=lambda: {}),
    )
    monkeypatch.setitem(
        sys.modules,
        "agent.shell_hooks",
        types.SimpleNamespace(register_from_config=lambda *_a, **_k: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "tools.mcp_tool",
        types.SimpleNamespace(
            discover_mcp_tools=lambda: calls.__setitem__("mcp", calls["mcp"] + 1)
        ),
    )

    main_mod._prepare_agent_startup(_agent_args(tui=True))

    assert calls["mcp"] == 0
    assert mcp_startup._mcp_discovery_thread is None


def test_cli_get_tool_definitions_briefly_waits_for_fast_mcp_thread(monkeypatch):
    thread = threading.Thread(target=lambda: time.sleep(0.05), daemon=True)
    thread.start()
    mcp_startup._mcp_discovery_thread = thread

    monkeypatch.setitem(
        sys.modules,
        "model_tools",
        types.SimpleNamespace(get_tool_definitions=lambda *_a, **_k: ["ok"]),
    )

    start = time.monotonic()
    result = cli_mod.get_tool_definitions(enabled_toolsets=["web"], quiet_mode=True)
    elapsed = time.monotonic() - start

    assert result == ["ok"]
    assert elapsed >= 0.04
    assert not thread.is_alive()


def test_init_agent_waits_for_mcp_discovery_before_agent_build(monkeypatch):
    waited = {"done": False}

    cli = cli_mod.HermesCLI(compact=True)
    cli._session_db = object()
    cli._resumed = False
    cli.conversation_history = []
    cli._install_tool_callbacks = lambda: None
    cli._ensure_tirith_security = lambda: None
    cli._ensure_runtime_credentials = lambda: True

    monkeypatch.setattr(
        mcp_startup,
        "wait_for_mcp_discovery",
        lambda timeout=0.75: waited.__setitem__("done", True),
    )

    def _fake_agent(*_a, **_k):
        assert waited["done"] is True
        return types.SimpleNamespace()

    monkeypatch.setattr(cli_mod, "AIAgent", _fake_agent)

    assert cli._init_agent() is True


# ---------------------------------------------------------------------------
# ensure_mcp_discovered() — three-case coverage (#38448)
# ---------------------------------------------------------------------------

def test_ensure_mcp_discovered_noop_inside_async_event_loop(monkeypatch):
    """Case 1: inside a running asyncio event loop, discover_mcp_tools must NOT be called."""
    import asyncio
    from tools.mcp_tool import ensure_mcp_discovered

    called = {"n": 0}

    monkeypatch.setattr(
        "tools.mcp_tool.discover_mcp_tools",
        lambda: called.__setitem__("n", called["n"] + 1),
    )

    async def _run():
        ensure_mcp_discovered()

    asyncio.run(_run())
    assert called["n"] == 0, "discover_mcp_tools must not be called inside an event loop"


def test_ensure_mcp_discovered_joins_background_thread_without_direct_call(monkeypatch):
    """Case 2: when a background thread is in flight, join it — don't call discover again."""
    import time
    from tools.mcp_tool import ensure_mcp_discovered

    called = {"discover": 0}
    thread_ran = {"done": False}

    def _slow_discovery():
        time.sleep(0.05)
        thread_ran["done"] = True

    thread = threading.Thread(target=_slow_discovery, daemon=True)
    thread.start()
    mcp_startup._mcp_discovery_thread = thread

    monkeypatch.setattr(
        "tools.mcp_tool.discover_mcp_tools",
        lambda: called.__setitem__("discover", called["discover"] + 1),
    )

    start = time.monotonic()
    ensure_mcp_discovered()
    elapsed = time.monotonic() - start

    assert thread_ran["done"] is True, "ensure_mcp_discovered must wait for background thread"
    assert elapsed >= 0.04, "should have blocked until thread finished"
    assert called["discover"] == 0, "discover_mcp_tools must not be called when thread handles it"


def test_ensure_mcp_discovered_calls_discover_when_no_thread(monkeypatch):
    """Case 3: no background thread (batch_runner, delegate_tool, …) → discover synchronously."""
    from tools.mcp_tool import ensure_mcp_discovered

    called = {"n": 0}

    # Ensure no background thread is set
    mcp_startup._mcp_discovery_thread = None

    monkeypatch.setattr(
        "tools.mcp_tool.discover_mcp_tools",
        lambda: called.__setitem__("n", called["n"] + 1),
    )

    ensure_mcp_discovered()
    assert called["n"] == 1, "discover_mcp_tools must be called when no background thread exists"


def test_init_agent_calls_ensure_mcp_discovered(monkeypatch):
    """Integration: init_agent() must call ensure_mcp_discovered() so that all
    AIAgent construction paths — oneshot, batch_runner, delegate_tool, etc. —
    get MCP tools without each entry point handling it explicitly (#38448).
    """
    import tools.mcp_tool as mcp_tool_mod
    from agent import agent_init

    called = {"n": 0}

    monkeypatch.setattr(mcp_tool_mod, "ensure_mcp_discovered", lambda: called.__setitem__("n", called["n"] + 1))

    stub = types.SimpleNamespace()
    try:
        agent_init.init_agent(stub, model="test-model", quiet_mode=True)
    except Exception:
        # init_agent may fail later (no real provider) — that's fine
        pass

    assert called["n"] == 1, "init_agent must call ensure_mcp_discovered exactly once"


def test_ensure_mcp_discovered_oneshot_path_joins_thread_not_double_calls(monkeypatch):
    """Regression for the hermes -z race: background thread started by main.py,
    then init_agent runs immediately. ensure_mcp_discovered must join the thread
    rather than calling discover_mcp_tools concurrently.
    """
    import time
    from tools.mcp_tool import ensure_mcp_discovered

    direct_calls = {"n": 0}
    thread_done = {"v": False}

    def _slow_discovery():
        time.sleep(0.05)
        thread_done["v"] = True

    thread = threading.Thread(target=_slow_discovery, daemon=True)
    thread.start()
    mcp_startup._mcp_discovery_thread = thread

    monkeypatch.setattr(
        "tools.mcp_tool.discover_mcp_tools",
        lambda: direct_calls.__setitem__("n", direct_calls["n"] + 1),
    )

    ensure_mcp_discovered()

    assert thread_done["v"] is True, "must have waited for the background thread"
    assert direct_calls["n"] == 0, "must not call discover_mcp_tools directly when thread handles it"
