"""Regression coverage for Slack markdown-table rendering (issue #26947).

Slack's mrkdwn does not natively render GitHub-flavored markdown
tables — pipe characters survive as literal text and the columns
smear together.  Block Kit has no public ``table`` block either, so
the practical fix (used by every other agent that handles this) is
to detect tables and convert them into a column-padded monospace
code block before the message reaches ``chat.postMessage``.

These tests pin both the converter helper and its integration into
``format_message`` so neither half can silently regress.
"""

from __future__ import annotations

import importlib

import pytest

from gateway.platforms.base import PlatformConfig
from gateway.platforms.slack import (
    SlackAdapter,
    _convert_markdown_tables_to_monospace as convert,
)


@pytest.fixture()
def adapter():
    a = SlackAdapter(PlatformConfig(enabled=True, token="xoxb-fake"))
    return a


# ---------------------------------------------------------------------------
# Converter: basic shapes
# ---------------------------------------------------------------------------


def test_basic_table_is_wrapped_in_triple_backticks():
    """The minimal repro from #26947 must render as a monospace block."""
    md = (
        "| Header 1 | Header 2 |\n"
        "| -------- | -------- |\n"
        "| Cell 1   | Cell 2   |\n"
        "| Cell 3   | Cell 4   |"
    )
    out = convert(md)
    assert out.startswith("```\n"), (
        "Tables must be wrapped in a fence so Slack renders them as "
        "preformatted monospace text."
    )
    assert out.endswith("\n```")
    # Header row preserved.
    assert "| Header 1 | Header 2 |" in out
    # Separator row regenerated with dashes matching column width.
    assert "|----------|----------|" in out
    # Body rows preserved.
    assert "| Cell 1   | Cell 2   |" in out
    assert "| Cell 3   | Cell 4   |" in out


def test_columns_are_padded_to_widest_cell():
    """The whole point — columns must line up in fixed-width font."""
    md = (
        "| a | bbb |\n"
        "|---|-----|\n"
        "| longer cell | x |"
    )
    out = convert(md)
    # Header cells get padded to widest cell width.
    assert "| a           | bbb |" in out
    assert "| longer cell | x   |" in out


def test_alignment_hints_are_honoured():
    """``:---:`` → centered, ``---:`` → right-aligned."""
    md = (
        "| L | C | R |\n"
        "|:---|:---:|---:|\n"
        "| 1 | 2 | 3 |\n"
        "| longer | x | yz |"
    )
    out = convert(md)
    # Right column ``R``: ``3`` and ``yz`` should be right-padded.
    assert "|  3 |" in out
    assert "| yz |" in out
    # Center column ``C``: single-char cells stay roughly centered.
    # ``len("C") == 1``, max width == 1, so centering is a no-op here —
    # widen the column to make the assertion meaningful.
    md2 = (
        "| L | Center | R |\n"
        "|:---|:---:|---:|\n"
        "| 1 | 2 | 3 |"
    )
    out2 = convert(md2)
    # Centered ``2`` in a 6-wide column must have whitespace on both sides.
    assert "|   2    |" in out2 or "|  2     |" in out2


def test_headerless_form_with_no_leading_pipe_is_supported():
    """Some authors omit the leading ``|`` — still a valid GFM table."""
    md = (
        "a | b\n"
        "---|---\n"
        "1 | 2"
    )
    out = convert(md)
    assert out.startswith("```\n")
    assert "| a | b |" in out
    assert "| 1 | 2 |" in out


def test_escaped_pipe_inside_cell_is_preserved():
    """``\\|`` inside a cell must survive as a literal pipe."""
    md = "| a | b |\n|---|---|\n| x \\| y | z |"
    out = convert(md)
    assert "x | y" in out


def test_ragged_rows_get_padded_to_column_count():
    """A row with fewer cells than the header must not corrupt alignment."""
    md = (
        "| a | b | c |\n"
        "|---|---|---|\n"
        "| 1 | 2 |\n"        # short row
        "| x | y | z |"
    )
    out = convert(md)
    # Short row got a synthetic empty third cell.
    assert "| 1 | 2 |   |" in out
    assert "| x | y | z |" in out


def test_empty_body_table_still_renders():
    """Header + separator with no rows is still a valid (if useless) table."""
    md = "| a | b |\n|---|---|"
    out = convert(md)
    assert out.startswith("```\n")
    assert "| a | b |" in out
    assert "|---|---|" in out


# ---------------------------------------------------------------------------
# Converter: rejection of non-table input
# ---------------------------------------------------------------------------


def test_prose_with_pipes_is_left_alone():
    """We must NOT convert arbitrary prose just because it has pipes."""
    text = "Use `foo | bar` to chain commands; bash uses | as a pipe."
    assert convert(text) == text


def test_single_column_pseudo_table_is_rejected():
    """One-column ``tables`` are almost always false positives
    (bulleted lists, log lines etc.).  Leave them alone."""
    text = "| only |\n|---|\n| one |"
    assert convert(text) == text


def test_text_without_any_pipe_short_circuits():
    """Performance / correctness: no pipes → no work."""
    text = "Hello world\nNo tables here.\nJust prose."
    assert convert(text) == text


def test_empty_and_none_inputs_pass_through():
    assert convert("") == ""
    assert convert(None) is None


def test_table_inside_fenced_code_block_is_left_alone():
    """If the user is *showing* a markdown table inside a code sample,
    we must not reformat it — that would corrupt their example."""
    text = (
        "Here's a markdown table:\n"
        "```\n"
        "| a | b |\n"
        "|---|---|\n"
        "| 1 | 2 |\n"
        "```\n"
        "End."
    )
    out = convert(text)
    # The whole fenced region must come back byte-identical.
    assert "```\n| a | b |\n|---|---|\n| 1 | 2 |\n```" in out


def test_separator_row_must_be_proper_dashes():
    """A line of ``|`` separators alone is not a separator row.
    Without a valid separator, we have no table."""
    text = "| a | b |\n| c | d |\n| 1 | 2 |"
    assert convert(text) == text


# ---------------------------------------------------------------------------
# Converter: surrounding context
# ---------------------------------------------------------------------------


def test_table_is_converted_in_place_inside_a_larger_message():
    md = (
        "Status update:\n"
        "\n"
        "| service | state |\n"
        "|---------|-------|\n"
        "| api     | up    |\n"
        "\n"
        "See dashboard for details."
    )
    out = convert(md)
    assert out.startswith("Status update:")
    assert out.endswith("See dashboard for details.")
    assert "```\n| service | state |" in out


def test_two_consecutive_tables_are_each_converted():
    md = (
        "| a | b |\n"
        "|---|---|\n"
        "| 1 | 2 |\n"
        "\n"
        "| c | d |\n"
        "|---|---|\n"
        "| 3 | 4 |"
    )
    out = convert(md)
    # Two distinct fenced blocks, one per table.
    assert out.count("```") == 4


# ---------------------------------------------------------------------------
# Integration: format_message + send pipeline
# ---------------------------------------------------------------------------


def test_format_message_renders_tables_as_monospace(adapter):
    """``format_message`` must invoke the converter and leave the
    generated code fence un-mangled by later mrkdwn passes."""
    md = (
        "**Status**\n"
        "\n"
        "| Service | State |\n"
        "|---------|-------|\n"
        "| api     | **up** |\n"
    )
    out = adapter.format_message(md)
    # Surrounding bold still converted to mrkdwn bold.
    assert out.startswith("*Status*")
    # Table fenced; ``**up**`` inside the cell stays literal because
    # the code fence protects it from the bold-conversion pass.
    assert "```\n| Service | State  |" in out
    assert "| api     | **up** |" in out


def test_format_message_preserves_existing_code_block_with_table_inside(adapter):
    """A pre-existing code block must not be touched.  This is the
    critical contract — users who paste markdown tutorials must see
    their code samples come through verbatim."""
    md = (
        "Example:\n"
        "```\n"
        "| h1 | h2 |\n"
        "|----|----|\n"
        "| a  | b  |\n"
        "```\n"
    )
    out = adapter.format_message(md)
    assert "```\n| h1 | h2 |\n|----|----|\n| a  | b  |\n```" in out


def test_format_message_no_table_no_change(adapter):
    """Non-table content must be byte-identical to the pre-fix path —
    no perf regression, no whitespace drift."""
    md = "**hello** _world_"
    assert adapter.format_message(md) == "*hello* _world_"


# ---------------------------------------------------------------------------
# Off-switch: SLACK_RENDER_MARKDOWN_TABLES=false
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "FALSE", "Off"])
def test_off_switch_disables_table_rendering(monkeypatch, adapter, value):
    monkeypatch.setenv("SLACK_RENDER_MARKDOWN_TABLES", value)
    md = "| a | b |\n|---|---|\n| 1 | 2 |"
    out = adapter.format_message(md)
    # No code fence emitted — original pipes survive (mangled but
    # un-mangled by us, exactly the pre-fix behavior the operator
    # explicitly opted into).
    assert "```" not in out
    assert "| a | b |" in out


def test_off_switch_default_is_on(monkeypatch, adapter):
    """Empty / unset env defaults to ON — most users want tables fixed."""
    monkeypatch.delenv("SLACK_RENDER_MARKDOWN_TABLES", raising=False)
    md = "| a | b |\n|---|---|\n| 1 | 2 |"
    out = adapter.format_message(md)
    assert "```" in out


def test_off_switch_garbage_value_falls_back_to_on(monkeypatch, adapter):
    """A typo'd value (``yes``, ``true``, ``maybe``) must not silently
    disable the feature."""
    monkeypatch.setenv("SLACK_RENDER_MARKDOWN_TABLES", "maybe")
    md = "| a | b |\n|---|---|\n| 1 | 2 |"
    out = adapter.format_message(md)
    assert "```" in out
