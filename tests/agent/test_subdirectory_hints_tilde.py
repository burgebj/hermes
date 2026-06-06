"""Drop-in test cases for the home-directory RuntimeError bug.

Append these inside the existing ``class TestSubdirectoryHintTracker`` in
``tests/agent/test_subdirectory_hints.py``, or save as a new file in the
same directory.  Without the fix to
``agent/subdirectory_hints.py:138/198/202`` (add ``RuntimeError`` to the
except clauses), the first test raises ``RuntimeError`` from inside the
hint walker.
"""

from agent.subdirectory_hints import SubdirectoryHintTracker


class TestSubdirectoryHintTrackerTildeRobustness:
    """Regression: literal ``~`` in tool-call args must not crash the walker."""

    def test_tilde_approximately_in_command_does_not_crash(self, project):
        """LLMs use ``~`` for "approximately" (e.g. ``~500 agencies``).

        ``pathlib.Path('~500-700').expanduser()`` raises ``RuntimeError`` —
        the walker must catch this, not propagate it as a tool failure.
        """
        tracker = SubdirectoryHintTracker(working_dir=str(project))
        # Heredoc-style terminal command body containing "~500-700"
        # used as "approximately 500-700"
        cmd = (
            "cat > out.md <<EOF\n"
            "Segment size signal: ~500-700 agencies in DACH region.\n"
            "CVE volume: ~45,000 disclosed in 2025.\n"
            "Founder blended rate: ~80/hr.\n"
            "EOF"
        )
        # Must not raise — return value can be None / empty
        result = tracker.check_tool_call("terminal", {"command": cmd})
        # No assertion on result content; the success criterion is "no exception"

    def test_tilde_with_unknown_user_does_not_crash(self, project):
        """``~unknown_user`` similarly raises RuntimeError on POSIX systems
        whose /etc/passwd does not contain that user.  Walker must absorb it."""
        tracker = SubdirectoryHintTracker(working_dir=str(project))
        cmd = "echo path: ~nonexistent_user_xyzzy_12345/some/file"
        # Must not raise
        tracker.check_tool_call("terminal", {"command": cmd})

    def test_valid_tilde_user_still_works(self, project):
        """The fix must not regress the legitimate-tilde-user path.

        ``~`` alone resolves to ``Path.home()`` and should still be
        recognised as a candidate path (no exception either way).
        """
        tracker = SubdirectoryHintTracker(working_dir=str(project))
        tracker.check_tool_call("terminal", {"command": "ls ~/Documents"})
        # No exception, no assertion required
