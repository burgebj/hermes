"""Tests for the Linux X11 backend of the computer_use toolset.

These tests don't need an X server — every subprocess call is mocked so
the suite runs hermetically on the CI runner (which has neither
``$DISPLAY`` nor xdotool installed).
"""

from __future__ import annotations

import base64
import subprocess
import sys
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Module-level availability check
# ---------------------------------------------------------------------------

class TestAvailabilityProbe:
    """``linux_backend_available()`` is the gating function the registry
    consults at import time, so its negative cases must be tight."""

    def test_returns_false_on_non_linux_platform(self):
        from tools.computer_use.linux_backend import linux_backend_available
        with patch("tools.computer_use.linux_backend.sys") as fake_sys:
            fake_sys.platform = "darwin"
            assert linux_backend_available() is False

    def test_returns_false_on_wayland_session(self):
        from tools.computer_use.linux_backend import linux_backend_available
        with patch("tools.computer_use.linux_backend.sys") as fake_sys, \
             patch.dict(
                 "tools.computer_use.linux_backend.os.environ",
                 {"XDG_SESSION_TYPE": "wayland", "DISPLAY": ":0"},
                 clear=True,
             ):
            fake_sys.platform = "linux"
            assert linux_backend_available() is False

    def test_returns_false_when_display_not_set(self):
        from tools.computer_use.linux_backend import linux_backend_available
        with patch("tools.computer_use.linux_backend.sys") as fake_sys, \
             patch.dict(
                 "tools.computer_use.linux_backend.os.environ",
                 {"XDG_SESSION_TYPE": "x11"},
                 clear=True,
             ):
            fake_sys.platform = "linux"
            assert linux_backend_available() is False

    def test_returns_false_when_required_tool_missing(self):
        from tools.computer_use.linux_backend import linux_backend_available
        with patch("tools.computer_use.linux_backend.sys") as fake_sys, \
             patch.dict(
                 "tools.computer_use.linux_backend.os.environ",
                 {"XDG_SESSION_TYPE": "x11", "DISPLAY": ":0"},
                 clear=True,
             ), \
             patch(
                 "tools.computer_use.linux_backend.shutil.which",
                 side_effect=lambda name: None if name == "scrot" else f"/usr/bin/{name}",
             ):
            fake_sys.platform = "linux"
            assert linux_backend_available() is False

    def test_returns_true_when_all_conditions_met(self):
        from tools.computer_use.linux_backend import linux_backend_available
        with patch("tools.computer_use.linux_backend.sys") as fake_sys, \
             patch.dict(
                 "tools.computer_use.linux_backend.os.environ",
                 {"XDG_SESSION_TYPE": "x11", "DISPLAY": ":0"},
                 clear=True,
             ), \
             patch(
                 "tools.computer_use.linux_backend.shutil.which",
                 side_effect=lambda name: f"/usr/bin/{name}",
             ):
            fake_sys.platform = "linux"
            assert linux_backend_available() is True


# ---------------------------------------------------------------------------
# Backend lifecycle + subprocess plumbing
# ---------------------------------------------------------------------------

def _completed(rc: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=rc, stdout=stdout, stderr=stderr
    )


@pytest.fixture
def backend():
    """A LinuxBackend with all tools resolved to fake paths."""
    from tools.computer_use.linux_backend import LinuxBackend
    b = LinuxBackend()
    with patch(
        "tools.computer_use.linux_backend.shutil.which",
        side_effect=lambda name: f"/usr/bin/{name}",
    ):
        b.start()
    return b


class TestLifecycle:
    def test_start_resolves_tool_paths(self, backend):
        assert backend._tools["xdotool"] == "/usr/bin/xdotool"
        assert backend._tools["scrot"] == "/usr/bin/scrot"
        assert backend._tools["wmctrl"] == "/usr/bin/wmctrl"

    def test_stop_clears_state(self, backend):
        backend.stop()
        assert backend._tools == {}
        assert backend._started is False

    def test_start_is_idempotent(self, backend):
        # Calling start twice should not double-resolve or raise.
        with patch(
            "tools.computer_use.linux_backend.shutil.which",
            side_effect=lambda name: f"/other/{name}",
        ):
            backend.start()
        # Original paths preserved (start short-circuits when already started).
        assert backend._tools["xdotool"] == "/usr/bin/xdotool"


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

class TestCapture:
    def test_vision_capture_returns_base64_png(self, backend):
        fake_png = b"\x89PNG\r\n\x1a\nfakepng"
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0, "1920 1080\n"),
        ), patch(
            "tools.computer_use.linux_backend.Path.read_bytes",
            return_value=fake_png,
        ), patch(
            "tools.computer_use.linux_backend.Path.exists",
            return_value=True,
        ):
            result = backend.capture(mode="vision")
        assert result.mode == "vision"
        assert result.png_b64 == base64.b64encode(fake_png).decode("ascii")
        assert result.elements == []
        assert result.png_bytes_len == len(fake_png)

    def test_som_mode_degrades_to_vision(self, backend):
        """SOM has no AT-SPI on Linux — backend transparently falls back."""
        fake_png = b"png-bytes"
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0, "1024 768\n"),
        ), patch(
            "tools.computer_use.linux_backend.Path.read_bytes",
            return_value=fake_png,
        ), patch(
            "tools.computer_use.linux_backend.Path.exists",
            return_value=True,
        ):
            result = backend.capture(mode="som")
        assert result.mode == "vision"
        assert result.elements == []

    def test_ax_mode_returns_empty_elements(self, backend):
        """AX is unsupported — must return cleanly, not raise."""
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0, "1920 1080\n"),
        ):
            result = backend.capture(mode="ax")
        assert result.mode == "ax"
        assert result.elements == []
        assert result.png_b64 is None

    def test_capture_handles_scrot_failure(self, backend):
        """scrot non-zero must not crash — return empty PNG."""
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(1, "", "scrot: cannot capture"),
        ):
            result = backend.capture(mode="vision")
        assert result.png_b64 is None


# ---------------------------------------------------------------------------
# Pointer actions
# ---------------------------------------------------------------------------

def _capture_calls(run_mock: MagicMock) -> List[List[str]]:
    """Return the argv list passed to each subprocess.run call."""
    return [c.args[0] for c in run_mock.call_args_list]


class TestClick:
    def test_click_xy_invokes_xdotool_mousemove_then_click(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            r = backend.click(x=100, y=200, button="left")
        assert r.ok
        calls = _capture_calls(run_mock)
        # First call: mousemove --sync 100 200
        assert calls[0] == ["/usr/bin/xdotool", "mousemove", "--sync", "100", "200"]
        # Second call: click 1
        assert calls[1] == ["/usr/bin/xdotool", "click", "1"]

    def test_click_button_mapping(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            backend.click(x=10, y=10, button="right")
        calls = _capture_calls(run_mock)
        assert calls[-1] == ["/usr/bin/xdotool", "click", "3"]

    def test_click_with_element_returns_error(self, backend):
        r = backend.click(element=5)
        assert r.ok is False
        assert "accessibility" in r.message.lower() or "element" in r.message.lower()

    def test_click_count_repeats(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            backend.click(x=5, y=5, click_count=3)
        # mousemove + 3 clicks = 4 calls
        assert run_mock.call_count == 4

    def test_click_with_modifiers_holds_then_releases(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            backend.click(x=1, y=1, modifiers=["shift", "ctrl"])
        calls = _capture_calls(run_mock)
        # Verify shift+ctrl keydown then keyup (release order is reversed).
        keydowns = [c for c in calls if len(c) > 1 and c[1] == "keydown"]
        keyups = [c for c in calls if len(c) > 1 and c[1] == "keyup"]
        assert [c[2] for c in keydowns] == ["shift", "ctrl"]
        assert [c[2] for c in keyups] == ["ctrl", "shift"]


class TestScroll:
    def test_scroll_down_uses_button_5(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            backend.scroll(direction="down", amount=2)
        clicks = [c for c in _capture_calls(run_mock) if c[1:2] == ["click"]]
        assert all(c[2] == "5" for c in clicks)
        assert len(clicks) == 2

    def test_scroll_up_uses_button_4(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            backend.scroll(direction="up")
        clicks = [c for c in _capture_calls(run_mock) if c[1:2] == ["click"]]
        assert all(c[2] == "4" for c in clicks)

    def test_scroll_unknown_direction_returns_error(self, backend):
        r = backend.scroll(direction="diagonal")
        assert r.ok is False


# ---------------------------------------------------------------------------
# Keyboard
# ---------------------------------------------------------------------------

class TestKeyboard:
    def test_type_text_calls_xdotool_with_separator(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            backend.type_text("hello world")
        argv = _capture_calls(run_mock)[0]
        # Crucial: "--" separator before user text prevents flag injection.
        assert "--" in argv
        assert argv[argv.index("--") + 1] == "hello world"

    def test_type_empty_text_is_noop(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            r = backend.type_text("")
        assert r.ok
        assert run_mock.call_count == 0

    def test_key_translates_macos_cmd_to_super(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            r = backend.key("cmd+s")
        assert r.ok
        argv = _capture_calls(run_mock)[0]
        # The combo passed to xdotool should be "super+s", not "cmd+s".
        assert argv[-1] == "super+s"

    def test_key_translates_option_to_alt(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            backend.key("option+left")
        argv = _capture_calls(run_mock)[0]
        assert argv[-1] == "alt+left"

    def test_key_preserves_native_x11_combos(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            backend.key("ctrl+shift+t")
        argv = _capture_calls(run_mock)[0]
        assert argv[-1] == "ctrl+shift+t"

    def test_key_empty_returns_error(self, backend):
        r = backend.key("")
        assert r.ok is False


# ---------------------------------------------------------------------------
# Introspection
# ---------------------------------------------------------------------------

class TestListApps:
    def test_parses_wmctrl_output(self, backend):
        wmctrl_out = (
            "0x05400003  0 12345 Navigator.firefox     host  Mozilla Firefox\n"
            "0x05400004  0 12346 Navigator.firefox     host  Reddit - Firefox\n"
            "0x05400005  0 23456 code.Code             host  hermes-agent — Code\n"
        )
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0, wmctrl_out),
        ):
            apps = backend.list_apps()
        names = sorted(a["name"] for a in apps)
        assert names == ["Code", "firefox"]
        firefox = next(a for a in apps if a["name"] == "firefox")
        assert firefox["windows"] == 2
        assert firefox["pid"] == 12345

    def test_returns_empty_list_when_wmctrl_unavailable(self, backend):
        backend._tools.pop("wmctrl", None)
        assert backend.list_apps() == []


class TestFocusApp:
    def test_focus_app_via_wmctrl(self, backend):
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            return_value=_completed(0),
        ) as run_mock:
            r = backend.focus_app("firefox")
        assert r.ok
        # First call should be wmctrl -a firefox.
        first = run_mock.call_args_list[0].args[0]
        assert first == ["/usr/bin/wmctrl", "-a", "firefox"]

    def test_focus_app_empty_name_returns_error(self, backend):
        r = backend.focus_app("")
        assert r.ok is False

    def test_focus_app_falls_back_to_xdotool_when_wmctrl_misses(self, backend):
        # wmctrl returns rc=1, xdotool --class succeeds.
        responses = [_completed(1), _completed(0)]
        with patch(
            "tools.computer_use.linux_backend.subprocess.run",
            side_effect=responses,
        ) as run_mock:
            r = backend.focus_app("Code")
        assert r.ok
        second = run_mock.call_args_list[1].args[0]
        assert second[0] == "/usr/bin/xdotool"
        assert "search" in second


# ---------------------------------------------------------------------------
# Native-value mutation (intentionally unsupported on Linux)
# ---------------------------------------------------------------------------

class TestSetValue:
    def test_returns_actionable_error(self, backend):
        r = backend.set_value("hello", element=1)
        assert r.ok is False
        # Error message must point the agent at the click+type workaround.
        assert "click" in r.message.lower()


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------

class TestRegistryDispatch:
    """Confirm ``HERMES_COMPUTER_USE_BACKEND=linux`` selects LinuxBackend."""

    def test_get_backend_returns_linux_when_env_set(self):
        from tools.computer_use.linux_backend import LinuxBackend
        from tools.computer_use.tool import _get_backend, reset_backend_for_tests

        reset_backend_for_tests()
        with patch.dict(
            "os.environ", {"HERMES_COMPUTER_USE_BACKEND": "linux"}, clear=False
        ), patch(
            "tools.computer_use.linux_backend.shutil.which",
            side_effect=lambda name: f"/usr/bin/{name}",
        ):
            backend = _get_backend()
        try:
            assert isinstance(backend, LinuxBackend)
        finally:
            reset_backend_for_tests()

    def test_check_requirements_routes_to_linux_on_linux_platform(self):
        from tools.computer_use.tool import check_computer_use_requirements

        with patch("tools.computer_use.tool.sys") as fake_sys, \
             patch.dict("os.environ", {"HERMES_COMPUTER_USE_BACKEND": ""}, clear=False), \
             patch(
                 "tools.computer_use.linux_backend.linux_backend_available",
                 return_value=True,
             ):
            fake_sys.platform = "linux"
            assert check_computer_use_requirements() is True

    def test_check_requirements_noop_override_always_true(self):
        from tools.computer_use.tool import check_computer_use_requirements
        with patch.dict(
            "os.environ", {"HERMES_COMPUTER_USE_BACKEND": "noop"}, clear=False
        ):
            assert check_computer_use_requirements() is True
