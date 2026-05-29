"""Tests for the TUI gateway → ``gateway.hooks`` bridge.

Every call into ``tui_gateway.server._emit`` should mirror the event onto the
process-wide ``HookRegistry`` under the ``tui:`` namespace so in-process
plugins can subscribe via :func:`gateway.hooks.get_default_registry`.

The mirror runs as a side-effect after ``write_json`` and is wrapped in a
broad try/except so a buggy subscriber can never break the main JSON-RPC
dispatch path.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from gateway.hooks import (
    HookRegistry,
    _reset_default_registry_for_tests,
    get_default_registry,
    install_as_default,
)
from tui_gateway import server


@pytest.fixture(autouse=True)
def _reset_registry_and_module_cache():
    """Reset the default registry and the TUI module-level cache before each test.

    Without this the cache from a previous test (or a previous run within the
    same process) would shadow our fresh install_as_default call and the
    mirrored event would land on the wrong registry.
    """
    _reset_default_registry_for_tests()
    # Force the deferred-import cache in the TUI module to re-resolve.
    server._hook_registry = None
    yield
    _reset_default_registry_for_tests()
    server._hook_registry = None


class _StubTransport:
    """Captures write_json calls so the test doesn't actually touch stdout."""

    def __init__(self):
        self.written: list[dict] = []

    def write(self, obj):
        self.written.append(obj)
        return True


def test_emit_mirrors_to_default_registry():
    transport = _StubTransport()
    captured: list = []
    reg = HookRegistry()
    install_as_default(reg)
    reg.register("tui:tool.start", lambda e, c: captured.append((e, c)))

    with patch.object(server, "_stdio_transport", transport):
        server._emit("tool.start", "sid-123", {"name": "search_files"})

    # The JSON-RPC event was written as before.
    assert len(transport.written) == 1
    assert transport.written[0]["params"]["type"] == "tool.start"

    # The hook bus saw a tui:-prefixed mirror.
    assert captured == [
        (
            "tui:tool.start",
            {"session_id": "sid-123", "payload": {"name": "search_files"}},
        )
    ]


def test_emit_with_no_payload_yields_empty_payload_dict():
    transport = _StubTransport()
    captured: list = []
    reg = HookRegistry()
    install_as_default(reg)
    reg.register("tui:session.info", lambda _e, c: captured.append(c))

    with patch.object(server, "_stdio_transport", transport):
        server._emit("session.info", "sid-1", None)

    assert captured == [{"session_id": "sid-1", "payload": {}}]


def test_emit_subscriber_exception_does_not_break_dispatch():
    transport = _StubTransport()
    reg = HookRegistry()
    install_as_default(reg)

    def broken(_e, _c):
        raise RuntimeError("subscriber blew up")

    reg.register("tui:tool.start", broken)

    # If _publish_tui_hook propagated, this would raise.
    with patch.object(server, "_stdio_transport", transport):
        server._emit("tool.start", "sid-1", {"name": "x"})

    # JSON-RPC event still landed on stdout — host pipeline intact.
    assert len(transport.written) == 1
    assert transport.written[0]["params"]["type"] == "tool.start"


def test_wildcard_subscriber_sees_all_tui_events():
    transport = _StubTransport()
    seen_types: list = []
    reg = HookRegistry()
    install_as_default(reg)
    reg.register("tui:*", lambda e, _c: seen_types.append(e))

    with patch.object(server, "_stdio_transport", transport):
        server._emit("tool.start", "s", {})
        server._emit("message.delta", "s", {"text": "hi"})
        server._emit("session.info", "s", {})

    assert seen_types == [
        "tui:tool.start",
        "tui:message.delta",
        "tui:session.info",
    ]


def test_emit_does_not_blow_up_when_no_subscribers():
    transport = _StubTransport()
    # No registry installed beyond the lazy default — and no handlers.
    with patch.object(server, "_stdio_transport", transport):
        server._emit("tool.start", "s", {"name": "x"})

    # Dispatch worked, no subscribers fired (default registry is empty).
    assert len(transport.written) == 1


def test_hook_registry_resolved_lazily_via_get_default_registry():
    """The TUI module caches whatever ``get_default_registry`` returns at first
    use. Re-set the default before the first ``_emit`` and confirm the cache
    picks up the new instance, not a stale or never-installed one."""
    transport = _StubTransport()
    captured: list = []
    custom = HookRegistry()
    install_as_default(custom)
    custom.register("tui:tool.start", lambda _e, c: captured.append(c))

    # Sanity: server._hook_registry starts unset thanks to the fixture.
    assert server._hook_registry is None

    with patch.object(server, "_stdio_transport", transport):
        server._emit("tool.start", "s", {"x": 1})

    # The cache now points at the installed registry.
    assert server._hook_registry is custom
    assert captured == [{"session_id": "s", "payload": {"x": 1}}]

    # Subsequent emits keep using the cached reference even if the default
    # is swapped — the contract is "resolve once, cache thereafter."
    new_reg = HookRegistry()
    install_as_default(new_reg)
    second: list = []
    new_reg.register("tui:tool.start", lambda _e, c: second.append(c))
    custom.register("tui:tool.start", lambda _e, c: captured.append({"second": c}))

    with patch.object(server, "_stdio_transport", transport):
        server._emit("tool.start", "s", {"x": 2})

    # The cached registry (``custom``) saw the new event, the freshly-installed
    # ``new_reg`` did not.
    assert second == []
    # ``custom`` has two handlers registered now (the original lambda still
    # fires on every event, plus the second one that wraps payload in
    # ``{"second": ...}``). Both fire on the second ``_emit`` call.
    assert captured == [
        {"session_id": "s", "payload": {"x": 1}},
        {"session_id": "s", "payload": {"x": 2}},
        {"second": {"session_id": "s", "payload": {"x": 2}}},
    ]
    assert get_default_registry() is new_reg
