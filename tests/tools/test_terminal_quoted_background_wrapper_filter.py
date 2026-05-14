"""Regression tests for issue #20064.

`_foreground_background_guidance()` previously used a naive
`\\b(?:nohup|disown|setsid)\\b` regex that fired on any occurrence of
those words anywhere in the command string, including inside quoted
arguments. This blocked legitimate commands such as commit messages,
`echo` text, and Python code passed via `-c`.

These tests pin down the fix:

* The four representative false-positive cases from the bug report MUST
  pass through the filter unblocked.
* Genuine `setsid`/`nohup`/`disown` usage at command position MUST still
  be redirected to `background=true`.
* The unit-level helpers `_strip_shell_quoted_spans` and
  `_SHELL_LEVEL_BACKGROUND_RE` are exercised directly so future
  refactors that drop quote-stripping will fail loudly.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helper-level tests (pure functions, no terminal_tool mocking required).
# ---------------------------------------------------------------------------
class TestForegroundGuidanceQuotedFalsePositives:
    """`_foreground_background_guidance` should ignore keywords inside quotes."""

    @pytest.mark.parametrize(
        "command",
        [
            # The four canonical false-positive cases from issue #20064.
            "python3 -c \"x = 'preexec_fn=os.setsid'\"",
            'git commit -m "fix: replace preexec_fn=os.setsid with process_group=0"',
            'gh pr create --body "We removed preexec_fn=os.setsid..."',
            'echo "The function os.setsid() creates a new session"',
            # A few extra plausible cases that were collateral damage.
            "echo 'use nohup ./server &'",
            'grep -r "disown" src/',
            "git log --grep='nohup'",
            'python3 -c "import os; help(os.setsid)"',
        ],
    )
    def test_quoted_keywords_do_not_trigger_background_wrapper_guidance(self, command):
        from tools.terminal_tool import _foreground_background_guidance

        guidance = _foreground_background_guidance(command)

        # Either no guidance at all, or guidance that is NOT the
        # nohup/disown/setsid wrapper warning. (Some commands like
        # `nohup ./server &` inside quotes still contain a literal `&`
        # which we don't pretend to parse — but the *wrapper* warning
        # must not fire.)
        if guidance is not None:
            assert "nohup/disown/setsid" not in guidance, (
                f"Filter false-positive: {command!r} → {guidance!r}"
            )


class TestForegroundGuidanceGenuineWrappers:
    """Genuine command-position usage must still be flagged."""

    @pytest.mark.parametrize(
        "command",
        [
            "setsid my_server",
            "nohup ./script.sh &",
            "nohup pnpm dev > /tmp/sg-server.log 2>&1 &",
            "disown %1",
            # After common shell separators.
            "cmd1; setsid foo",
            "cmd1 && nohup foo",
            "cmd1 || setsid foo",
            "cmd1 | nohup foo",
            # Inside a subshell.
            "(setsid foo)",
            # After a newline (multi-line command).
            "echo hi\nsetsid foo",
            # Trailing disown after a real command.
            "echo hi; disown",
            # Mixed case still matches (regex is IGNORECASE).
            "NoHuP ./script.sh",
        ],
    )
    def test_command_position_wrapper_still_flagged(self, command):
        from tools.terminal_tool import _foreground_background_guidance

        guidance = _foreground_background_guidance(command)
        assert guidance is not None, (
            f"Genuine wrapper not flagged: {command!r}"
        )
        # We accept either the wrapper-specific warning or the inline-`&`
        # warning, since `nohup foo &` legitimately matches both.
        assert (
            "nohup/disown/setsid" in guidance
            or "'&' backgrounding" in guidance
        ), f"Unexpected guidance for {command!r}: {guidance!r}"


# ---------------------------------------------------------------------------
# Direct unit tests for the helpers, so a future refactor that drops
# quote-stripping or weakens the boundary regex fails loudly here.
# ---------------------------------------------------------------------------
class TestStripShellQuotedSpans:
    def test_blanks_double_quoted_content_only(self):
        from tools.terminal_tool import _strip_shell_quoted_spans

        out = _strip_shell_quoted_spans('echo "setsid"')
        assert out == 'echo "      "'

    def test_blanks_single_quoted_content_only(self):
        from tools.terminal_tool import _strip_shell_quoted_spans

        out = _strip_shell_quoted_spans("echo 'setsid'")
        assert out == "echo '      '"

    def test_preserves_unquoted_content(self):
        from tools.terminal_tool import _strip_shell_quoted_spans

        out = _strip_shell_quoted_spans('setsid foo')
        assert out == 'setsid foo'

    def test_preserves_string_length(self):
        from tools.terminal_tool import _strip_shell_quoted_spans

        cmd = 'git commit -m "fix: os.setsid stuff"'
        assert len(_strip_shell_quoted_spans(cmd)) == len(cmd)

    def test_handles_escaped_double_quote_inside_string(self):
        from tools.terminal_tool import _strip_shell_quoted_spans

        cmd = r'echo "she said \"setsid\" out loud"'
        out = _strip_shell_quoted_spans(cmd)
        # The whole double-quoted span should be blanked — the escaped
        # inner quotes must NOT terminate the string prematurely.
        assert "setsid" not in out
        assert out.startswith('echo "') and out.endswith('"')


class TestShellLevelBackgroundRegex:
    """Direct regex tests so failures point at the regex, not the wrapper."""

    @pytest.mark.parametrize(
        "command,should_match",
        [
            # Quoted-string false positives (post quote-stripping these
            # have no command-position keyword).
            ('echo "setsid foo"', False),
            ("echo 'nohup bar'", False),
            ('git commit -m "fix os.setsid"', False),
            # Unquoted command-position usage.
            ("setsid foo", True),
            ("nohup foo", True),
            ("foo; setsid bar", True),
            ("foo && nohup bar", True),
            ("foo || setsid bar", True),
            ("foo | nohup bar", True),
            ("(setsid foo)", True),
        ],
    )
    def test_regex_only_matches_command_position_after_strip(
        self, command, should_match
    ):
        from tools.terminal_tool import (
            _SHELL_LEVEL_BACKGROUND_RE,
            _strip_shell_quoted_spans,
        )

        scannable = _strip_shell_quoted_spans(command)
        match = _SHELL_LEVEL_BACKGROUND_RE.search(scannable)
        assert bool(match) is should_match, (
            f"command={command!r} stripped={scannable!r} match={match!r}"
        )
