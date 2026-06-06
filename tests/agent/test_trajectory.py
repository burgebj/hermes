import pytest
from agent.trajectory import has_incomplete_scratchpad


class TestHasIncompleteScratchpad:
    """Regression tests for has_incomplete_scratchpad false positives.

    See: https://github.com/NousResearch/hermes-agent/issues/11181
    """

    def test_bare_open_tag_returns_true(self):
        assert has_incomplete_scratchpad("<REASONING_SCRATCHPAD>thinking...") is True

    def test_matched_pair_returns_false(self):
        content = "<REASONING_SCRATCHPAD>thinking...</REASONING_SCRATCHPAD>"
        assert has_incomplete_scratchpad(content) is False

    def test_empty_string_returns_false(self):
        assert has_incomplete_scratchpad("") is False

    def test_none_returns_false(self):
        assert has_incomplete_scratchpad(None) is False

    # ── False-positive cases (issue #11181) ─────────────────────────────────

    def test_tag_in_fenced_code_block_no_false_positive(self):
        """Tag inside ```python ... ``` should not trigger incomplete."""
        content = "Here is some code:\n```\n<REASONING_SCRATCHPAD>\n# not really open\n```"
        assert has_incomplete_scratchpad(content) is False

    def test_tag_in_inline_code_no_false_positive(self):
        """Tag inside backtick inline code should not trigger incomplete."""
        assert has_incomplete_scratchpad("Use `<REASONING_SCRATCHPAD>` in your code.") is False

    def test_tag_in_blockquote_no_false_positive(self):
        """Tag inside a > blockquote should not trigger incomplete."""
        content = "> <REASONING_SCRATCHPAD> is the tag\n> don't use it like this"
        assert has_incomplete_scratchpad(content) is False

    def test_tag_in_indented_code_no_false_positive(self):
        """Tag in 4-space indented lines should not trigger incomplete."""
        content = "    <REASONING_SCRATCHPAD>\n    def foo():\n        pass"
        assert has_incomplete_scratchpad(content) is False

    def test_tag_in_grep_output_no_false_positive(self):
        """Tag appearing in grep/search output context should not trigger."""
        content = """$ grep -r REASONING_SCRATCHPAD src/\nsrc/utils.py:    <REASONING_SCRATCHPAD> if incomplete else ''"""
        assert has_incomplete_scratchpad(content) is False

    def test_genuine_unclosed_still_detected_in_mixed_content(self):
        """Real unclosed tag among false-positive contexts still detected."""
        content = """Check this code:
```
<REASONING_SCRATCHPAD>
```
<REASONING_SCRATCHPAD>this one is actually unclosed"""
        assert has_incomplete_scratchpad(content) is True

    def test_multiple_closes_more_than_opens_returns_false(self):
        """More close tags than open tags (e.g. already closed) is fine."""
        content = """</REASONING_SCRATCHPAD>
</REASONING_SCRATCHPAD>
<REASONING_SCRATCHPAD>actually closed</REASONING_SCRATCHPAD>"""
        assert has_incomplete_scratchpad(content) is False
