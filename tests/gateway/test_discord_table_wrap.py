"""Tests for Discord markdown table code-fence wrapping (issue #21168).

Discord does not render GFM pipe tables — raw pipe characters display as
garbage.  ``_wrap_tables_in_code_fence`` detects tables and wraps them in
triple-backtick fences so they render as readable monospaced text.
"""

import pytest

from plugins.platforms.discord.adapter import _wrap_tables_in_code_fence


class TestWrapTablesInCodeFence:
    """Unit tests for the table-wrapping helper."""

    def test_basic_table_is_wrapped(self):
        text = (
            "| Name | Value |\n"
            "|------|-------|\n"
            "| foo  | 1     |\n"
            "| bar  | 2     |"
        )
        result = _wrap_tables_in_code_fence(text)
        assert result.startswith("```\n")
        assert result.endswith("\n```")
        # Original table lines are preserved inside the fences
        assert "| Name | Value |" in result
        assert "| foo  | 1     |" in result

    def test_table_with_surrounding_text(self):
        text = (
            "Here is a comparison:\n"
            "\n"
            "| Model | Speed |\n"
            "|-------|-------|\n"
            "| A     | fast  |\n"
            "| B     | slow  |\n"
            "\n"
            "Hope that helps!"
        )
        result = _wrap_tables_in_code_fence(text)
        # Surrounding text is untouched
        assert result.startswith("Here is a comparison:\n")
        assert result.endswith("\nHope that helps!")
        # Table is wrapped
        assert "```\n| Model | Speed |" in result
        assert "| B     | slow  |\n```" in result

    def test_table_inside_code_fence_is_untouched(self):
        text = (
            "```\n"
            "| A | B |\n"
            "|---|---|\n"
            "| 1 | 2 |\n"
            "```"
        )
        result = _wrap_tables_in_code_fence(text)
        assert result == text  # unchanged

    def test_no_table_passthrough(self):
        text = "Just a regular message with no pipes or tables."
        assert _wrap_tables_in_code_fence(text) == text

    def test_pipe_without_separator_is_untouched(self):
        # A line with '|' but no separator row below is NOT a table
        text = "Use the | operator in bash for piping."
        assert _wrap_tables_in_code_fence(text) == text

    def test_empty_input(self):
        assert _wrap_tables_in_code_fence("") == ""

    def test_table_without_leading_pipe(self):
        # GFM tables can omit leading/trailing pipes
        text = (
            "Name | Value\n"
            "------|-------\n"
            "foo  | 1\n"
            "bar  | 2"
        )
        result = _wrap_tables_in_code_fence(text)
        assert result.startswith("```\n")
        assert result.endswith("\n```")

    def test_multiple_tables(self):
        text = (
            "| A | B |\n"
            "|---|---|\n"
            "| 1 | 2 |\n"
            "\n"
            "Some text\n"
            "\n"
            "| C | D |\n"
            "|---|---|\n"
            "| 3 | 4 |"
        )
        result = _wrap_tables_in_code_fence(text)
        # Both tables should be wrapped
        assert result.count("```") == 4  # 2 opening + 2 closing fences

    def test_table_with_alignment_row(self):
        text = (
            "| Left | Center | Right |\n"
            "|:-----|:------:|------:|\n"
            "| a    | b      | c     |"
        )
        result = _wrap_tables_in_code_fence(text)
        assert result.startswith("```\n")
        assert result.endswith("\n```")

    def test_single_column_separator_not_matched(self):
        # A separator with only one column (no '|') should not match
        text = "-----\nnot a table"
        assert _wrap_tables_in_code_fence(text) == text

    def test_format_message_integration(self):
        """Verify format_message calls the wrapping function."""
        from plugins.platforms.discord.adapter import DiscordAdapter

        # Create adapter instance bypassing __init__
        adapter = DiscordAdapter.__new__(DiscordAdapter)
        text = (
            "| X | Y |\n"
            "|---|---|\n"
            "| 1 | 2 |"
        )
        result = adapter.format_message(text)
        assert result.startswith("```\n")
        assert result.endswith("\n```")
