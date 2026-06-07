"""A wedged adapter must never stall the gateway's shutdown path.

Adapter network ops reachable from ``_stop_impl`` are bounded at the call
site so one stuck socket can't hang shutdown into a SIGKILL that leaves
stale gateway.pid / gateway.lock. This suite covers each bounded op as
its commit lands (teardown, notify-sends, fatal-error disconnect).
"""

import asyncio
import types

import pytest

from gateway.config import Platform
from gateway.run import GatewayRunner


def _runner():
    return object.__new__(GatewayRunner)


def _platform(name="telegram"):
    return types.SimpleNamespace(value=name, platform=name)


class _HangingDisconnect:
    """cancel_background_tasks() returns; disconnect() never completes."""

    async def cancel_background_tasks(self):
        return None

    async def disconnect(self):
        await asyncio.Event().wait()


@pytest.mark.asyncio
async def test_hung_disconnect_does_not_stall_teardown(monkeypatch):
    monkeypatch.setenv("HERMES_GATEWAY_ADAPTER_DISCONNECT_TIMEOUT", "0.1")
    await asyncio.wait_for(
        _runner()._safe_adapter_teardown(_HangingDisconnect(), _platform()),
        timeout=2.0,
    )


class _HangingSend:
    """send() never completes — models a TCP black-hole platform."""

    platform = _platform()

    async def send(self, *args, **kwargs):
        await asyncio.Event().wait()


@pytest.mark.asyncio
async def test_hung_notify_send_is_bounded(monkeypatch):
    monkeypatch.setenv("HERMES_GATEWAY_ADAPTER_DISCONNECT_TIMEOUT", "0.1")
    result = await asyncio.wait_for(
        _runner()._bounded_shutdown_send(_HangingSend(), "chat-id", "bye"),
        timeout=2.0,
    )
    # A timed-out send yields None (no structured result); shutdown continues.
    assert result is None


class _FatalHangingAdapter:
    """disconnect() hangs; the adapter reports a non-retryable fatal error."""

    fatal_error_code = "boom"
    fatal_error_message = "unrecoverable"
    fatal_error_retryable = False

    def __init__(self, platform):
        self.platform = platform

    async def disconnect(self):
        await asyncio.Event().wait()


@pytest.mark.asyncio
async def test_fatal_error_disconnect_is_bounded(monkeypatch):
    monkeypatch.setenv("HERMES_GATEWAY_ADAPTER_DISCONNECT_TIMEOUT", "0.1")
    runner = _runner()
    pf = Platform.TELEGRAM
    other = Platform.DISCORD  # second adapter keeps shutdown off the all-gone path
    adapter = _FatalHangingAdapter(pf)
    runner.adapters = {pf: adapter, other: object()}
    runner.delivery_router = types.SimpleNamespace(adapters=runner.adapters)
    runner._failed_platforms = {}
    monkeypatch.setattr(runner, "_update_platform_runtime_status", lambda *a, **k: None)

    # A hung disconnect must not block popping the dead adapter so the
    # reconnection bookkeeping that follows still runs.
    await asyncio.wait_for(runner._handle_adapter_fatal_error(adapter), timeout=2.0)
    assert pf not in runner.adapters


@pytest.mark.asyncio
async def test_teardown_runs_adapters_concurrently(monkeypatch):
    monkeypatch.setenv("HERMES_GATEWAY_ADAPTER_DISCONNECT_TIMEOUT", "0.2")
    runner = _runner()
    runner.adapters = {Platform.TELEGRAM: _HangingDisconnect(), Platform.DISCORD: _HangingDisconnect()}

    loop = asyncio.get_running_loop()
    start = loop.time()
    await asyncio.wait_for(runner._teardown_adapters(), timeout=2.0)
    elapsed = loop.time() - start

    # Both adapters hang, so each is cut at the 0.2s bound. Run concurrently
    # the phase is ~one timeout; a sequential loop would take ~0.4s. The lower
    # bound proves the bound actually fired (not a short-circuit); the upper
    # bound proves concurrency, with slack for loaded CI.
    assert 0.18 < elapsed < 0.38


class _SlowSend:
    """send() takes longer than an insta-timeout would allow, then succeeds."""

    platform = _platform()

    async def send(self, *args, **kwargs):
        await asyncio.sleep(0.05)
        return "ok"


class _SlowTeardown:
    """disconnect() takes real time; records whether it ran to completion."""

    def __init__(self):
        self.disconnected = False

    async def cancel_background_tasks(self):
        return None

    async def disconnect(self):
        await asyncio.sleep(0.05)
        self.disconnected = True


# A timeout of 0 is the operator opt-out: every bounded site must take a bare
# ``await`` (truly unbounded), NOT ``wait_for(coro, timeout=0)`` — which would
# insta-timeout and either return None or abandon a mid-flight op. These three
# behavioral tests pin that contract for each helper: a 0.05s op set against a
# "0" timeout must run to completion / return its real result.


@pytest.mark.asyncio
async def test_zero_timeout_opts_out_bounded_send(monkeypatch):
    monkeypatch.setenv("HERMES_GATEWAY_ADAPTER_DISCONNECT_TIMEOUT", "0")
    result = await _runner()._bounded_shutdown_send(_SlowSend(), "chat-id", "bye")
    # Real result passes through — proves no wait_for(..., timeout=0) → None.
    assert result == "ok"


@pytest.mark.asyncio
async def test_zero_timeout_opts_out_teardown(monkeypatch):
    monkeypatch.setenv("HERMES_GATEWAY_ADAPTER_DISCONNECT_TIMEOUT", "0")
    adapter = _SlowTeardown()
    await _runner()._safe_adapter_teardown(adapter, _platform())
    # disconnect() ran to completion — a wait_for(timeout=0) would have
    # cancelled it mid-sleep, leaving this False.
    assert adapter.disconnected is True


@pytest.mark.asyncio
async def test_zero_timeout_opts_out_safe_disconnect(monkeypatch):
    monkeypatch.setenv("HERMES_GATEWAY_ADAPTER_DISCONNECT_TIMEOUT", "0")
    adapter = _SlowTeardown()
    await _runner()._safe_adapter_disconnect(adapter, _platform())
    assert adapter.disconnected is True
