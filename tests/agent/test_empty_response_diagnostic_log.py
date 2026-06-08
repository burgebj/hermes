"""Regression tests for #34246 empty-response diagnostic logging.

When a custom OpenAI-compatible endpoint returns content but Hermes
treats it as empty, the user has no way to debug the discrepancy. The
warning log now includes content_type / content_len / content_preview /
has_structured / prefill_retries so the cause is visible from the log.
"""

from __future__ import annotations

import logging
import re

import pytest


def _read_warning_format() -> str:
    """Pull the actual warning format string out of conversation_loop.py
    so the test breaks if someone removes the diagnostic fields rather
    than testing a fake duplicate string."""
    from pathlib import Path

    src = Path("agent/conversation_loop.py").read_text(encoding="utf-8")
    # Find the # #34246 block and extract the format string
    match = re.search(
        r'#34246:.*?logger\.warning\(\s*"([^"]+)"',
        src,
        re.DOTALL,
    )
    assert match, "Could not find the #34246 diagnostic warning in conversation_loop.py"
    # The next consecutive string concatenation in the same call
    fmt_block = re.search(
        r'#34246:.*?logger\.warning\(\s*(?P<strs>(?:"[^"]+"\s*)+)',
        src,
        re.DOTALL,
    )
    assert fmt_block, "Could not extract concatenated format string"
    # Join consecutive Python string literals
    strs = re.findall(r'"([^"]+)"', fmt_block.group("strs"))
    return "".join(strs)


def test_diagnostic_log_format_includes_content_type():
    fmt = _read_warning_format()
    assert "content_type=%s" in fmt, fmt


def test_diagnostic_log_format_includes_content_len():
    fmt = _read_warning_format()
    assert "content_len=%s" in fmt, fmt


def test_diagnostic_log_format_includes_content_preview():
    fmt = _read_warning_format()
    assert "content_preview=" in fmt, fmt


def test_diagnostic_log_format_includes_has_structured():
    fmt = _read_warning_format()
    assert "has_structured=%s" in fmt, fmt


def test_diagnostic_log_format_includes_prefill_retries():
    fmt = _read_warning_format()
    assert "prefill_retries=%d" in fmt, fmt


def test_diagnostic_log_format_still_mentions_model():
    """Don't regress the existing model= field that downstream log scrapers
    might already match on."""
    fmt = _read_warning_format()
    assert "model=%s" in fmt, fmt


def test_diagnostic_log_format_still_mentions_retry_count():
    fmt = _read_warning_format()
    assert "retry %d/3" in fmt, fmt
