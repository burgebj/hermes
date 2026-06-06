"""Regression coverage for #29715 — the WhatsApp Node bridge launched
without ``creationflags`` on Windows, so ``node.exe`` was given a
fresh visible console window every time the gateway started the
adapter under ``pythonw.exe``. Closing the empty window killed the
bridge (``0xC000013A``); the reconnection watcher then relaunched it
and the popup came back.

The fix: route platform-specific ``subprocess.Popen`` extras through
the new ``_bridge_popen_extra_kwargs`` helper, which returns
``{"creationflags": CREATE_NO_WINDOW}`` on Windows and
``{"preexec_fn": os.setsid}`` on POSIX.

These tests pin the contract from three angles:

* Helper purity — the right kwargs on the right platform, no
  cross-contamination (no ``preexec_fn`` on Windows; no
  ``creationflags`` on POSIX).
* Wire-level — the real ``connect()`` path passes the correct kwargs
  through to ``subprocess.Popen`` (verified by patching ``Popen`` and
  inspecting the recorded call).
* Source guardrail — no future refactor reintroduces the bare
  ``Popen([..., bridge.js, ...])`` shape without ``creationflags``.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import Platform


class _AsyncCM:
    """Minimal async context manager — mirrors the helper in
    ``tests/gateway/test_whatsapp_connect.py`` so this file can stand
    alone without importing private test helpers."""

    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *exc):
        return False


# ---------------------------------------------------------------------------
# Helper contract — pure, no subprocess spawn
# ---------------------------------------------------------------------------


class TestBridgePopenExtraKwargsHelper:
    def test_posix_uses_setsid(self):
        from gateway.platforms.whatsapp import _bridge_popen_extra_kwargs
        kwargs = _bridge_popen_extra_kwargs(is_windows=False)
        assert kwargs.get("preexec_fn") is os.setsid
        assert "creationflags" not in kwargs, (
            "POSIX must not pass creationflags — it's a Windows-only Popen "
            "arg and silently no-ops elsewhere but signals the wrong intent."
        )

    def test_windows_uses_create_no_window(self):
        """Simulate Windows by flipping the shared ``IS_WINDOWS`` flag
        in ``hermes_cli._subprocess_compat`` (same pattern other
        Windows-on-POSIX tests use). On a real Windows host the helper
        already returns ``CREATE_NO_WINDOW`` (``0x08000000``);
        ``windows_hide_flags()`` simply mirrors ``_subprocess_compat.IS_WINDOWS``."""
        from hermes_cli import _subprocess_compat as sc
        from gateway.platforms.whatsapp import _bridge_popen_extra_kwargs

        with patch.object(sc, "IS_WINDOWS", True):
            kwargs = _bridge_popen_extra_kwargs(is_windows=True)
            assert "creationflags" in kwargs
            assert kwargs["creationflags"] & 0x08000000, (
                "missing CREATE_NO_WINDOW — bridge will pop a console "
                "window on Windows again (#29715)"
            )
        assert "preexec_fn" not in kwargs, (
            "Windows must not set preexec_fn — Popen treats it as a "
            "no-op on Windows but Python may emit a RuntimeWarning."
        )

    def test_windows_does_not_use_detached_process(self):
        """``DETACHED_PROCESS`` (0x00000008) would sever stdio and
        break ``stdout=bridge_log_fh``. The fix deliberately uses
        ``windows_hide_flags()`` (CREATE_NO_WINDOW only), NOT
        ``windows_detach_flags()`` (which includes DETACHED_PROCESS)."""
        from hermes_cli import _subprocess_compat as sc
        from gateway.platforms.whatsapp import _bridge_popen_extra_kwargs

        with patch.object(sc, "IS_WINDOWS", True):
            kwargs = _bridge_popen_extra_kwargs(is_windows=True)
            flags = kwargs.get("creationflags", 0)
            assert flags & 0x00000008 == 0, (
                "DETACHED_PROCESS would break stdout=bridge_log_fh "
                "redirect — fix must not include it"
            )

    def test_default_argument_follows_module_platform(self):
        """When called with no args, the helper reads the module-level
        ``_IS_WINDOWS`` constant. On a non-Windows test host this
        means POSIX-shaped kwargs."""
        from gateway.platforms import whatsapp
        from gateway.platforms.whatsapp import _bridge_popen_extra_kwargs

        kwargs = _bridge_popen_extra_kwargs()
        if whatsapp._IS_WINDOWS:
            assert "creationflags" in kwargs
        else:
            assert kwargs.get("preexec_fn") is os.setsid

    def test_returned_dict_is_safe_to_unpack_into_popen(self):
        """The dict must contain only keys ``subprocess.Popen``
        actually accepts on the target platform — no stray keys."""
        from gateway.platforms.whatsapp import _bridge_popen_extra_kwargs

        for is_windows in (True, False):
            kwargs = _bridge_popen_extra_kwargs(is_windows=is_windows)
            allowed = {"creationflags", "preexec_fn"}
            assert set(kwargs).issubset(allowed), (
                f"unexpected Popen kwargs: {set(kwargs) - allowed!r}"
            )
            # And mutually exclusive (Windows ⊕ POSIX), so we can't
            # accidentally pass both.
            assert not ({"creationflags", "preexec_fn"} <= set(kwargs)), (
                "must not set both creationflags AND preexec_fn — "
                "they belong to different platforms"
            )


# ---------------------------------------------------------------------------
# Wire-level — the ``connect()`` path actually plumbs the kwargs through
# to ``subprocess.Popen``.
# ---------------------------------------------------------------------------


def _make_minimal_adapter(tmp_path: Path):
    """Construct a ``WhatsAppAdapter`` via ``__new__`` (skipping
    ``__init__``) and stamp on just enough state for ``connect()`` to
    reach the bridge ``Popen`` call. Pattern borrowed from
    ``tests/gateway/test_whatsapp_connect.py``.

    Sets up bridge.js + node_modules + creds.json so every preflight
    check passes and the method falls through to the ``subprocess.Popen``
    site we want to inspect.
    """
    from gateway.platforms.whatsapp import WhatsAppAdapter

    bridge_dir = tmp_path / "bridge"
    bridge_dir.mkdir()
    (bridge_dir / "bridge.js").write_text("// stub for #29715\n", encoding="utf-8")
    (bridge_dir / "node_modules").mkdir()  # skip npm install branch

    session_dir = tmp_path / "session"
    session_dir.mkdir()
    (session_dir / "creds.json").write_text("{}", encoding="utf-8")  # skip not-paired guard

    adapter = WhatsAppAdapter.__new__(WhatsAppAdapter)
    adapter.platform = Platform.WHATSAPP
    adapter.config = MagicMock()
    adapter._bridge_port = 19877
    adapter._bridge_script = str(bridge_dir / "bridge.js")
    adapter._session_path = session_dir
    adapter._bridge_log_fh = None
    adapter._bridge_log = None
    adapter._bridge_process = None
    adapter._reply_prefix = None
    adapter._running = False
    adapter._message_handler = None
    adapter._fatal_error_code = None
    adapter._fatal_error_message = None
    adapter._fatal_error_retryable = True
    adapter._fatal_error_handler = None
    adapter._active_sessions = {}
    adapter._pending_messages = {}
    adapter._background_tasks = set()
    adapter._auto_tts_disabled_chats = set()
    adapter._message_queue = asyncio.Queue()
    adapter._http_session = None
    # The session-lock plumbing varies between platforms; sidestep it.
    adapter._acquire_platform_lock = MagicMock(return_value=True)
    # ``name`` is a read-only property bound to ``platform`` already.
    return adapter


def _mock_aiohttp_returning(status=500, json_data=None):
    """Build a callable that ``patch('aiohttp.ClientSession', ...)``
    can use to return an async-context-managed fake session. Mirrors
    ``_mock_aiohttp`` from ``tests/gateway/test_whatsapp_connect.py``."""
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data or {})
    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=_AsyncCM(mock_resp))
    return MagicMock(return_value=_AsyncCM(mock_session))


def _record_popen(recorded: list, exit_code: int = 1):
    """Return a fake ``subprocess.Popen`` that records each call's
    kwargs and yields a process stub whose ``poll()`` reports an
    immediate exit so the readiness loops bail fast."""
    class _FakeBridge:
        def __init__(self):
            self.pid = 90909
            self.returncode = exit_code

        def poll(self):
            return self.returncode

        def terminate(self):
            pass

        def kill(self):
            pass

        def wait(self, timeout=None):
            return self.returncode

    def fake(*args, **kwargs):
        recorded.append({"args": args, "kwargs": kwargs})
        return _FakeBridge()

    return fake


def _bridge_popen_calls(recorded: list) -> list:
    """Filter ``recorded`` Popen calls down to the bridge launch (the
    one whose first argv element is ``"node"``)."""
    out = []
    for call in recorded:
        if not call["args"]:
            continue
        argv = call["args"][0]
        if isinstance(argv, list) and argv and argv[0] == "node":
            out.append(call)
    return out


def _drive_connect_to_popen(
    adapter, monkeypatch, *, recorded: list, simulate_windows: bool
) -> None:
    """Run ``connect()`` with all the right things mocked so it
    deterministically reaches the bridge ``Popen`` call site and then
    bails (the bridge "fails to come up" on the first poll).

    Mirrors the patch list in ``_connect_patches`` from
    ``tests/gateway/test_whatsapp_connect.py``.
    """
    from gateway.platforms import whatsapp as wa
    from hermes_cli import _subprocess_compat as sc

    monkeypatch.setattr(wa, "_IS_WINDOWS", simulate_windows)
    monkeypatch.setattr(sc, "IS_WINDOWS", simulate_windows)

    with patch(
        "gateway.platforms.whatsapp.check_whatsapp_requirements",
        return_value=True,
    ), patch.object(Path, "exists", return_value=True), patch.object(
        Path, "mkdir", return_value=None
    ), patch(
        "subprocess.run", return_value=MagicMock(returncode=0)
    ), patch(
        "subprocess.Popen", new=_record_popen(recorded)
    ), patch(
        "builtins.open", return_value=MagicMock()
    ), patch(
        "gateway.platforms.whatsapp.asyncio.sleep", new_callable=AsyncMock
    ), patch(
        "gateway.platforms.whatsapp.asyncio.create_task"
    ), patch(
        "aiohttp.ClientSession", _mock_aiohttp_returning(status=500)
    ), patch(
        "gateway.platforms.whatsapp._kill_stale_bridge_by_pidfile"
    ), patch(
        "gateway.platforms.whatsapp._kill_port_process"
    ), patch(
        "gateway.platforms.whatsapp._write_bridge_pidfile"
    ):
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(asyncio.wait_for(adapter.connect(), timeout=5.0))
        except (asyncio.TimeoutError, Exception):
            pass
        finally:
            loop.close()


class TestConnectPlumbsExtraKwargsToPopen:
    """End-to-end verification that ``connect()`` passes the new
    platform-specific kwargs through to ``subprocess.Popen``."""

    def test_posix_path_passes_setsid_to_popen(self, tmp_path, monkeypatch):
        recorded: list = []
        adapter = _make_minimal_adapter(tmp_path)
        _drive_connect_to_popen(
            adapter, monkeypatch, recorded=recorded, simulate_windows=False
        )
        bridge_calls = _bridge_popen_calls(recorded)
        assert bridge_calls, "connect() never reached the Popen([node, ...]) call"
        kw = bridge_calls[0]["kwargs"]
        assert kw.get("preexec_fn") is os.setsid
        assert "creationflags" not in kw

    def test_windows_path_passes_creationflags_to_popen(
        self, tmp_path, monkeypatch
    ):
        recorded: list = []
        adapter = _make_minimal_adapter(tmp_path)
        _drive_connect_to_popen(
            adapter, monkeypatch, recorded=recorded, simulate_windows=True
        )
        bridge_calls = _bridge_popen_calls(recorded)
        assert bridge_calls, "connect() never reached the Popen([node, ...]) call"
        kw = bridge_calls[0]["kwargs"]
        assert "creationflags" in kw, (
            "Windows bridge launch must set creationflags so no console "
            "window pops up (#29715)"
        )
        assert kw["creationflags"] & 0x08000000, "missing CREATE_NO_WINDOW"
        assert kw["creationflags"] & 0x00000008 == 0, (
            "must not set DETACHED_PROCESS — would sever bridge stdio"
        )
        assert "preexec_fn" not in kw

    def test_windows_path_still_redirects_stdio_to_bridge_log(
        self, tmp_path, monkeypatch
    ):
        """Avoiding ``DETACHED_PROCESS`` is what keeps
        ``stdout=bridge_log_fh`` working. Assert the redirect is
        still wired up on the Windows branch."""
        recorded: list = []
        adapter = _make_minimal_adapter(tmp_path)
        _drive_connect_to_popen(
            adapter, monkeypatch, recorded=recorded, simulate_windows=True
        )
        bridge_calls = _bridge_popen_calls(recorded)
        assert bridge_calls
        kw = bridge_calls[0]["kwargs"]
        assert kw.get("stdout") is not None
        assert kw.get("stderr") is not None
        # Both stdout and stderr must point at the same file handle so a
        # single ``bridge.log`` collects everything.
        assert kw["stdout"] is kw["stderr"]


# ---------------------------------------------------------------------------
# Source guardrail — protect against future regressions
# ---------------------------------------------------------------------------


class TestWhatsAppSourceGuardrail:
    """Static asserts on ``gateway/platforms/whatsapp.py`` so a future
    refactor can't quietly drop the fix."""

    @pytest.fixture
    def source(self) -> str:
        path = (
            Path(__file__).resolve().parents[2]
            / "gateway"
            / "platforms"
            / "whatsapp.py"
        )
        assert path.exists(), f"missing {path}"
        return path.read_text(encoding="utf-8")

    def test_helper_is_defined(self, source):
        assert "def _bridge_popen_extra_kwargs(" in source

    def test_helper_is_used_at_popen_call_site(self, source):
        """The ``Popen([node, bridge.js, …])`` call must unpack
        ``_bridge_popen_extra_kwargs()`` — that's the wiring that
        actually puts ``CREATE_NO_WINDOW`` on the call."""
        assert "**_bridge_popen_extra_kwargs()" in source

    def test_no_bare_preexec_fn_at_popen_site(self, source):
        """The pre-fix shape was ``preexec_fn=None if _IS_WINDOWS else
        os.setsid`` directly inline on ``Popen``. Make sure nobody
        accidentally re-adds it (it would conflict with the helper's
        ``preexec_fn`` key on POSIX and silently no-op on Windows
        without ``creationflags``)."""
        assert "preexec_fn=None if _IS_WINDOWS else os.setsid" not in source

    def test_helper_imports_windows_hide_flags(self, source):
        """The blessed cross-platform helper from
        ``hermes_cli._subprocess_compat`` is the source of truth; the
        adapter must import it rather than inlining the magic number."""
        assert (
            "from hermes_cli._subprocess_compat import windows_hide_flags"
            in source
        )

    def test_helper_does_not_call_detach_flags(self, source):
        """``windows_detach_flags()`` would include ``DETACHED_PROCESS``,
        which severs stdio. The bridge must use the hide flags only —
        the detach helper may appear in docstrings/comments for
        contrast, but must never be *called* from this module."""
        assert "windows_detach_flags(" not in source, (
            "whatsapp.py must not call windows_detach_flags() — "
            "DETACHED_PROCESS would sever the bridge.log stdio redirect"
        )
