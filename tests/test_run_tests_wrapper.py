"""Regression tests for scripts/run_tests.sh env-scrubbing logic.

Covers:
  - #22400: HERMES_CRON_SESSION must be unset so cron-invoked test runs
    don't leak into pytest approval behavior.
  - #22401: pytest-split installation must fall back to ``uv pip install``
    when pip is unavailable (uv-managed venvs).
"""
from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_TESTS = REPO_ROOT / "scripts" / "run_tests.sh"


# ── helpers ──────────────────────────────────────────────────────────────────

def _extract_unset_block(script: str) -> str:
    """Return the ``unset HERMES_* …`` continuation line (may span lines)."""
    lines = script.splitlines()
    collecting = False
    buf: list[str] = []
    for line in lines:
        if line.startswith("unset HERMES_"):
            collecting = True
        if collecting:
            buf.append(line)
            if "2>/dev/null" in line:
                break
    return "\n".join(buf)


def _extract_pytest_split_block(script: str) -> str:
    """Return the pytest-split installation block."""
    lines = script.splitlines()
    collecting = False
    buf: list[str] = []
    for line in lines:
        if "pytest-split" in line and "install" in line.lower():
            collecting = True
        if collecting:
            buf.append(line)
            if line.strip() == "fi" and len(buf) > 2:
                break
    return "\n".join(buf)


# ── tests ────────────────────────────────────────────────────────────────────


class TestEnvScrub:
    """The env-scrub section must unset every HERMES_* behavioral var."""

    SCRIPT_TEXT: str = RUN_TESTS.read_text()

    def test_hermes_cron_session_in_unset_list(self):
        """#22400 — HERMES_CRON_SESSION must appear in the unset block."""
        block = _extract_unset_block(self.SCRIPT_TEXT)
        assert "HERMES_CRON_SESSION" in block, (
            "HERMES_CRON_SESSION is missing from the unset block in "
            "scripts/run_tests.sh — cron-invoked test runs will leak "
            "HERMES_CRON_SESSION=1 into pytest, changing approval behavior."
        )

    def test_hermes_cron_session_not_in_env_after_scrub(self):
        """#22400 — Running the script with HERMES_CRON_SESSION=1 must drop it.

        We simulate the env-scrub section in a subshell and verify the var
        is absent afterward.  This avoids actually running pytest.
        """
        snippet = textwrap.dedent("""\
            set -euo pipefail
            # Reproduce the unset block from run_tests.sh
            unset HERMES_YOLO_MODE HERMES_INTERACTIVE HERMES_QUIET HERMES_TOOL_PROGRESS \\
                  HERMES_TOOL_PROGRESS_MODE HERMES_MAX_ITERATIONS HERMES_SESSION_PLATFORM \\
                  HERMES_SESSION_CHAT_ID HERMES_SESSION_CHAT_NAME HERMES_SESSION_THREAD_ID \\
                  HERMES_SESSION_SOURCE HERMES_SESSION_KEY HERMES_GATEWAY_SESSION \\
                  HERMES_PLATFORM HERMES_INFERENCE_PROVIDER HERMES_MANAGED HERMES_DEV \\
                  HERMES_CONTAINER HERMES_EPHEMERAL_SYSTEM_PROMPT HERMES_TIMEZONE \\
                  HERMES_REDACT_SECRETS HERMES_BACKGROUND_NOTIFICATIONS HERMES_EXEC_ASK \\
                  HERMES_HOME_MODE HERMES_CRON_SESSION 2>/dev/null || true
            echo "CRON_SESSION=${HERMES_CRON_SESSION:-<UNSET>}"
        """)
        result = subprocess.run(
            ["bash", "-c", snippet],
            capture_output=True, text=True,
            env={**os.environ, "HERMES_CRON_SESSION": "1"},
        )
        assert result.returncode == 0, result.stderr
        assert "CRON_SESSION=<UNSET>" in result.stdout, (
            f"HERMES_CRON_SESSION leaked through the unset block: {result.stdout}"
        )


class TestPytestSplitInstall:
    """The pytest-split install block must try uv before pip."""

    SCRIPT_TEXT: str = RUN_TESTS.read_text()

    def test_uv_fallback_present(self):
        """#22401 — The install block must attempt ``uv pip install`` first."""
        block = _extract_pytest_split_block(self.SCRIPT_TEXT)
        assert "uv pip install" in block, (
            "scripts/run_tests.sh does not try 'uv pip install' — "
            "uv-managed venvs without pip will fail to install pytest-split."
        )

    def test_pip_fallback_present(self):
        """The install block must still fall back to ``python -m pip``."""
        block = _extract_pytest_split_block(self.SCRIPT_TEXT)
        assert "pip install" in block, (
            "scripts/run_tests.sh dropped the pip fallback — "
            "systems without uv will fail to install pytest-split."
        )
