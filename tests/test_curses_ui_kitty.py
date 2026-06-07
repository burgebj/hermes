"""Tests for the Kitty keyboard protocol mitigation in ``hermes_cli.curses_ui``.

Regression coverage for the bug where config wizards (``hermes tools``,
``hermes skills``, plugin selectors) ignored arrow keys under terminals that
implement the Kitty keyboard protocol (Ghostty, Kitty, foot, WezTerm).

When that protocol is active the terminal encodes arrow keys as CSI-u
sequences (e.g. ``\\x1b[57352u``) instead of the legacy ``\\x1bOA`` form.
Python's ``curses`` was built against the legacy terminfo definition and
cannot decode CSI-u, so ``getch()`` returns a bare ``ESC`` (27) which every
wizard treats as cancel. ``pop_kitty_keyboard()`` disables the protocol
before each ``curses.wrapper()`` so legacy encoding is used for the duration
of the curses screen.
"""

import io

import curses as _curses

import hermes_cli.curses_ui as curses_ui

# The pop sequence Hermes uses elsewhere (cli.py) to leave Kitty keyboard mode.
POP_SEQ = "\x1b[<u"


class _FakeTTY(io.StringIO):
    """StringIO that reports as a TTY (or not, per ``_isatty``)."""

    def __init__(self, isatty=True):
        super().__init__()
        self._isatty = isatty

    def isatty(self):
        return self._isatty


def test_pop_kitty_keyboard_emits_sequence_on_tty(monkeypatch):
    fake = _FakeTTY(isatty=True)
    monkeypatch.setattr(curses_ui.sys, "stdout", fake)
    curses_ui.pop_kitty_keyboard()
    assert fake.getvalue() == POP_SEQ


def test_pop_kitty_keyboard_noop_on_non_tty(monkeypatch):
    fake = _FakeTTY(isatty=False)
    monkeypatch.setattr(curses_ui.sys, "stdout", fake)
    curses_ui.pop_kitty_keyboard()
    assert fake.getvalue() == ""


def test_pop_kitty_keyboard_swallows_exceptions(monkeypatch):
    class _Boom:
        def isatty(self):
            return True

        def write(self, _):
            raise OSError("broken pipe")

        def flush(self):
            raise OSError("broken pipe")

    monkeypatch.setattr(curses_ui.sys, "stdout", _Boom())
    # Must not raise — terminal-control failures should never crash a wizard.
    curses_ui.pop_kitty_keyboard()


def _assert_pops_before_wrapper(monkeypatch, func, *args, **kwargs):
    """Run ``func`` with curses.wrapper stubbed and assert pop happened first."""
    calls = []

    def fake_pop():
        calls.append("pop")

    def fake_wrapper(draw, *a, **k):
        calls.append("wrapper")
        # Do not invoke ``draw`` — it needs a real curses screen. The function
        # under test falls through to its post-wrapper return logic.
        return None

    # The wizards short-circuit when stdin is not a TTY (e.g. under pytest),
    # returning before the pop/wrapper path. Force the TTY branch.
    class _TTYStdin:
        def isatty(self):
            return True

    monkeypatch.setattr(curses_ui.sys, "stdin", _TTYStdin())
    monkeypatch.setattr(curses_ui, "pop_kitty_keyboard", fake_pop)
    monkeypatch.setattr(_curses, "wrapper", fake_wrapper)
    monkeypatch.setattr(curses_ui, "flush_stdin", lambda: None)

    func(*args, **kwargs)
    assert calls == ["pop", "wrapper"], (
        f"{func.__name__}: expected pop before wrapper, got {calls}"
    )


def test_checklist_pops_before_wrapper(monkeypatch):
    _assert_pops_before_wrapper(
        monkeypatch, curses_ui.curses_checklist, "Title", ["a", "b", "c"], set()
    )


def test_radiolist_pops_before_wrapper(monkeypatch):
    _assert_pops_before_wrapper(
        monkeypatch, curses_ui.curses_radiolist, "Title", ["a", "b", "c"], 0
    )


def test_single_select_pops_before_wrapper(monkeypatch):
    _assert_pops_before_wrapper(
        monkeypatch, curses_ui.curses_single_select, "Title", ["a", "b", "c"], 0
    )
