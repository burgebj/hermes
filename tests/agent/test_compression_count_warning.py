"""Regression: compression count warning must use _emit_status, not _vprint.

Issue #36908: In TUI mode, ``_vprint`` writes to stdout which the Ink UI
does not consume — the warning is silently swallowed.  The fix routes the
warning through ``agent._compression_warning`` + ``agent._emit_status()``
so it reaches all platforms (CLI, TUI, Telegram, Discord, etc.).

This test verifies the invariant at the code level: the warning path in
``compress_context`` must call ``_emit_status`` (not ``_vprint``).
"""

import ast
import textwrap
from pathlib import Path


def test_warning_uses_emit_status_not_vprint():
    """The compression-count warning block must use _emit_status, not _vprint.

    This is a source-level invariant check: parse the function and verify
    that the ``if _cc >= 2:`` block calls ``_emit_status`` and does NOT
    call ``_vprint``.
    """
    source = Path(__file__).resolve().parents[2] / "agent" / "conversation_compression.py"
    tree = ast.parse(source.read_text())

    # Find the compress_context function
    compress_fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "compress_context":
            compress_fn = node
            break
    assert compress_fn is not None, "compress_context function not found"

    # Find the ``if _cc >= 2:`` block
    warning_block = None
    for node in ast.walk(compress_fn):
        if isinstance(node, ast.If):
            # Check for ``_cc >= 2``
            test = node.test
            if (isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "_cc"
                    and len(test.ops) == 1
                    and isinstance(test.ops[0], ast.GtE)
                    and len(test.comparators) == 1
                    and isinstance(test.comparators[0], ast.Constant)
                    and test.comparators[0].value == 2):
                warning_block = node
                break
    assert warning_block is not None, "if _cc >= 2 block not found"

    # Collect all attribute calls in the warning block
    calls = []
    for node in ast.walk(warning_block):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
            elif isinstance(node.func, ast.Name):
                calls.append(node.func.id)

    # Must call _emit_status
    assert "_emit_status" in calls, (
        f"_emit_status not called in warning block. Found: {calls}"
    )

    # Must NOT call _vprint
    assert "_vprint" not in calls, (
        f"_vprint still called in warning block (should use _emit_status). Found: {calls}"
    )


def test_warning_stored_for_gateway_replay():
    """The warning must be stored in agent._compression_warning for gateway replay."""
    source = Path(__file__).resolve().parents[2] / "agent" / "conversation_compression.py"
    content = source.read_text()

    # The warning block must assign to _compression_warning
    assert "agent._compression_warning = msg" in content or \
           "agent._compression_warning=" in content, \
        "_compression_warning assignment not found in conversation_compression.py"
