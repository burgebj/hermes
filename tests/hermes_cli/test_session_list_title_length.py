"""Tests for session list title display length (#14082).

Users copy-paste truncated titles for /resume but matching fails when
the stored title is longer than the displayed truncation.
"""
import pytest


class TestSessionListTitleLength:
    """Session titles should display at least 50 chars (#14082)."""

    def test_title_truncation_at_50(self):
        """Verify the display truncation is [:50], not [:30]."""
        import inspect
        import hermes_cli.main as mod
        source = inspect.getsource(mod)
        # The fix changes [:30] to [:50] in session list display
        assert "[:50]" in source, "Title truncation should be [:50]"
