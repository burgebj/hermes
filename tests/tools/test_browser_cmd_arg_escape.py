"""Tests for cmd.exe-safe argument quoting when invoking the agent-browser
.cmd shim on Windows. Regression coverage for issue #35654.

The bug: on Windows, npm-installed `agent-browser` resolves to a `.cmd`
wrapper that re-evaluates `%*` through cmd.exe. Args containing cmd
metacharacters (`&`, `|`, `<`, `>`) — common in URL query strings — get
interpreted as shell tokens and the URL is split mid-flight.

CPython 3.11.9+ / 3.12.3+ fix this automatically (CVE-2024-1874), but
older patch levels of supported Pythons remain vulnerable. The fix
here is a portable backport: render the argv as a cmd.exe-safe string
and hand that to subprocess.Popen instead of a list.
"""

import os
import subprocess
from unittest.mock import patch, MagicMock

import pytest

import tools.browser_tool as _bt
from tools.browser_tool import (
    _build_bat_cmdline,
    _is_windows_bat_target,
    _quote_arg_for_cmd,
)


class TestQuoteArgForCmd:
    """Unit tests for the per-argument quoting helper."""

    def test_plain_arg_unchanged(self):
        assert _quote_arg_for_cmd("plain") == "plain"

    def test_url_with_ampersand_gets_quoted(self):
        assert (
            _quote_arg_for_cmd("https://x.example.com/?a=1&b=2")
            == '"https://x.example.com/?a=1&b=2"'
        )

    def test_arg_with_pipe_gets_quoted(self):
        assert _quote_arg_for_cmd("a|b") == '"a|b"'

    def test_arg_with_redirect_gets_quoted(self):
        assert _quote_arg_for_cmd("a<b") == '"a<b"'
        assert _quote_arg_for_cmd("a>b") == '"a>b"'

    def test_arg_with_caret_gets_quoted(self):
        assert _quote_arg_for_cmd("a^b") == '"a^b"'

    def test_arg_with_space_gets_quoted(self):
        assert _quote_arg_for_cmd("hello world") == '"hello world"'

    def test_arg_with_internal_quote_doubled(self):
        # cmd.exe convention: doubled quotes inside a quoted region.
        assert _quote_arg_for_cmd('a"b&c') == '"a""b&c"'

    def test_empty_arg_quoted(self):
        # An empty positional arg must survive as `""` so it isn't dropped.
        assert _quote_arg_for_cmd("") == '""'

    def test_arg_with_percent_quoted(self):
        # `%FOO%` would expand inside a .cmd; quoting blocks expansion.
        assert _quote_arg_for_cmd("%PATH%") == '"%PATH%"'


class TestBuildBatCmdline:
    """Unit tests for the full cmdline string builder."""

    def test_empty_parts(self):
        assert _build_bat_cmdline([]) == ""

    def test_executable_only(self):
        assert _build_bat_cmdline(["agent-browser.cmd"]) == "agent-browser.cmd"

    def test_simple_args_unchanged(self):
        out = _build_bat_cmdline(["agent-browser.cmd", "--json", "open"])
        assert out == "agent-browser.cmd --json open"

    def test_url_with_ampersand_protected(self):
        # The original bug: this URL gets split on `&` inside the .cmd shim.
        out = _build_bat_cmdline([
            "agent-browser.cmd",
            "--json",
            "open",
            "https://example.com/search?q=test&page=2",
        ])
        # The URL is one quoted token; cmd.exe and the .cmd's %* see it whole.
        assert '"https://example.com/search?q=test&page=2"' in out
        # And nothing outside the quotes contains a bare `&`.
        unquoted = out.replace('"https://example.com/search?q=test&page=2"', "")
        assert "&" not in unquoted

    def test_executable_path_with_spaces_quoted(self):
        out = _build_bat_cmdline([
            r"C:\Program Files\nodejs\agent-browser.cmd",
            "--json",
        ])
        assert out.startswith('"C:\\Program Files\\nodejs\\agent-browser.cmd"')

    def test_executable_path_without_spaces_unquoted(self):
        out = _build_bat_cmdline([r"C:\nodejs\agent-browser.cmd", "--json"])
        assert out == r"C:\nodejs\agent-browser.cmd --json"

    def test_javascript_with_pipe_protected(self):
        # `evaluate` payloads can carry `|` as a logical-OR operator.
        out = _build_bat_cmdline([
            "agent-browser.cmd",
            "evaluate",
            "x || y",
        ])
        assert '"x || y"' in out


class TestIsWindowsBatTarget:
    """Detection of .cmd / .bat shims, gated on os.name == 'nt'."""

    def test_cmd_extension_on_windows(self):
        with patch.object(_bt.os, "name", "nt"):
            assert _is_windows_bat_target(r"C:\foo\agent-browser.cmd") is True

    def test_bat_extension_on_windows(self):
        with patch.object(_bt.os, "name", "nt"):
            assert _is_windows_bat_target(r"C:\foo\thing.bat") is True

    def test_uppercase_extension_on_windows(self):
        # PATHEXT on Windows is case-insensitive.
        with patch.object(_bt.os, "name", "nt"):
            assert _is_windows_bat_target(r"C:\foo\AGENT-BROWSER.CMD") is True

    def test_no_extension_on_windows(self):
        with patch.object(_bt.os, "name", "nt"):
            assert _is_windows_bat_target(r"C:\foo\agent-browser") is False

    def test_cmd_extension_on_posix_returns_false(self):
        # A path that happens to end in `.cmd` on POSIX must NOT be routed
        # through the cmd.exe quoter — there's no cmd.exe involved.
        with patch.object(_bt.os, "name", "posix"):
            assert _is_windows_bat_target("/tmp/agent-browser.cmd") is False
