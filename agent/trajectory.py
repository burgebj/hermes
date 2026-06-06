"""Trajectory saving utilities and static helpers.

_convert_to_trajectory_format stays as an AIAgent method (batch_runner.py
calls agent._convert_to_trajectory_format). Only the static helpers and
the file-write logic live here.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def convert_scratchpad_to_think(content: str) -> str:
    """Convert <REASONING_SCRATCHPAD> tags to <think> tags."""
    if not content or "<REASONING_SCRATCHPAD>" not in content:
        return content
    return content.replace("<REASONING_SCRATCHPAD>", "<think>").replace("</REASONING_SCRATCHPAD>", "</think>")


def has_incomplete_scratchpad(content: str) -> bool:
    """Check if content has an opening <REASONING_SCRATCHPAD> without a closing tag.

    Avoids false positives by stripping content inside code blocks and blockquotes
    before checking, since the tag may legitimately appear in those contexts.
    """
    if not content:
        return False

    # Strategy: strip code blocks (fenced and indented) and blockquotes, then check.
    # This prevents false positives when the tag appears in grep output, code
    # discussions, or quoted text rather than as an actual unclosed tag.
    stripped = content

    # Remove fenced code blocks (```...```)
    import re as _re
    stripped = _re.sub(r'```[\s\S]*?```', '', stripped)

    # Remove inline code (`...`)
    stripped = _re.sub(r'`[^`]*`', '', stripped)

    # Remove blockquotes (lines starting with >)
    stripped = _re.sub(r'^>.*$', '', stripped, flags=_re.MULTILINE)

    # Remove indented code (4+ spaces at line start)
    stripped = _re.sub(r'^    .*$', '', stripped, flags=_re.MULTILINE)

    # Now check for the tag in the sanitized content
    open_tag = "<REASONING_SCRATCHPAD>"
    close_tag = "</REASONING_SCRATCHPAD>"

    open_count = stripped.count(open_tag)
    close_count = stripped.count(close_tag)

    # Only flag if there are more opens than closes (genuinely unclosed)
    return open_count > close_count


def save_trajectory(trajectory: List[Dict[str, Any]], model: str,
                    completed: bool, filename: str = None):
    """Append a trajectory entry to a JSONL file.

    Args:
        trajectory: The ShareGPT-format conversation list.
        model: Model name for metadata.
        completed: Whether the conversation completed successfully.
        filename: Override output filename. Defaults to trajectory_samples.jsonl
                  or failed_trajectories.jsonl based on ``completed``.
    """
    if filename is None:
        filename = "trajectory_samples.jsonl" if completed else "failed_trajectories.jsonl"

    entry = {
        "conversations": trajectory,
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "completed": completed,
    }

    import tempfile
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    tmp_dir = os.path.dirname(filename) or "."
    temp_name = None

    try:
        # Atomic write: temp file + rename to avoid partial JSONL corruption
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                        dir=tmp_dir, suffix=".tmp",
                                        newline="", delete=False) as tf:
            tf.write(line)
            tf.flush()
            os.fsync(tf.fileno())
            temp_name = tf.name
        # Rename is atomic on POSIX; on Windows it replaces the target file
        os.replace(temp_name, filename)
        logger.info("Trajectory saved to %s", filename)
    except Exception as e:
        logger.warning("Failed to save trajectory: %s", e)
    finally:
        # Clean up orphaned temp file if rename never happened
        if temp_name is not None and os.path.exists(temp_name):
            try:
                os.unlink(temp_name)
            except Exception:
                pass
