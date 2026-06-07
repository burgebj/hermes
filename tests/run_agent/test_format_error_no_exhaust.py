"""D1 regression guard: malformed-conversation 400 must route to format_error
and must NEVER exhaust a credential.

Invariant pinned:
  HTTP 400 with body "messages.2: tool_use ids found without tool_result blocks
  immediately after: toolu_..." classifies to FailoverReason.format_error
  (not billing, not rate_limit) AND recover_with_credential_pool returns
  (False, has_retried_429) without calling mark_exhausted_and_rotate,
  try_refresh_current, or _refresh_entry.

Background: Hana's credential was incorrectly marked exhausted after this
exact error.  The classifier catches it via fall-through (no billing/rate_limit
pattern matches), but future wording changes to Anthropic's API messages could
silently re-classify it and resume exhausting credentials.  This test is the
permanent executable guard against that regression.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agent.error_classifier import FailoverReason, classify_api_error
from agent.agent_runtime_helpers import recover_with_credential_pool


# ── shared fixture ────────────────────────────────────────────────────────────

MALFORMED_CONV_BODY = (
    "messages.2: tool_use ids found without tool_result blocks immediately after: "
    "toolu_01ABCdefGHIJklmNOPQrstuVW"
)


class _FakeApiError(Exception):
    """Minimal stand-in for openai.BadRequestError with status_code + body."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.body = {"error": {"message": message}}
        self.response = None


# ── Part A: classifier ────────────────────────────────────────────────────────


class TestMalformedConvClassification:
    """_classify_400 must route the orphan-tool-use error to format_error."""

    def test_routes_to_format_error(self):
        err = _FakeApiError(status_code=400, message=MALFORMED_CONV_BODY)
        result = classify_api_error(err, provider="anthropic", model="claude-sonnet-4-6")
        assert result.reason == FailoverReason.format_error, (
            f"Expected format_error, got {result.reason}. "
            "A billing/rate_limit pattern may have matched the body — check _BILLING_PATTERNS "
            "and _RATE_LIMIT_PATTERNS in error_classifier.py."
        )

    def test_not_retryable(self):
        """format_error is non-retryable — do not spin on a broken conversation."""
        err = _FakeApiError(status_code=400, message=MALFORMED_CONV_BODY)
        result = classify_api_error(err, provider="anthropic", model="claude-sonnet-4-6")
        assert result.retryable is False, (
            f"format_error must not be retryable, got retryable={result.retryable}"
        )

    def test_not_billing_and_not_rate_limit(self):
        """Explicit negative: reason must be neither billing nor rate_limit."""
        err = _FakeApiError(status_code=400, message=MALFORMED_CONV_BODY)
        result = classify_api_error(err, provider="anthropic", model="claude-sonnet-4-6")
        assert result.reason not in (FailoverReason.billing, FailoverReason.rate_limit), (
            f"Malformed-conv 400 must not be billing or rate_limit — got {result.reason}. "
            "This would cause credential exhaustion."
        )


# ── Part B: recovery — no pool mutation ──────────────────────────────────────


class TestFormatErrorNoCredentialExhaust:
    """recover_with_credential_pool with format_error must be fully non-destructive."""

    def _make_mock_agent(self) -> tuple:
        mock_pool = MagicMock()
        mock_pool.mark_exhausted_and_rotate = MagicMock(return_value=None)
        mock_pool.try_refresh_current = MagicMock(return_value=None)
        mock_pool._refresh_entry = MagicMock(return_value=None)

        mock_agent = MagicMock()
        mock_agent._credential_pool = mock_pool
        mock_agent._is_entitlement_failure = MagicMock(return_value=False)

        return mock_agent, mock_pool

    def test_returns_false_false(self):
        """Must return (False, False) — no recovery, has_retried_429 unchanged."""
        mock_agent, _ = self._make_mock_agent()
        result = recover_with_credential_pool(
            mock_agent,
            status_code=400,
            has_retried_429=False,
            classified_reason=FailoverReason.format_error,
        )
        assert result == (False, False), (
            f"Expected (False, False) for format_error, got {result}"
        )

    def test_mark_exhausted_and_rotate_never_called(self):
        """pool.mark_exhausted_and_rotate must have zero calls for format_error."""
        mock_agent, mock_pool = self._make_mock_agent()
        recover_with_credential_pool(
            mock_agent,
            status_code=400,
            has_retried_429=False,
            classified_reason=FailoverReason.format_error,
        )
        assert mock_pool.mark_exhausted_and_rotate.call_count == 0, (
            f"mark_exhausted_and_rotate was called {mock_pool.mark_exhausted_and_rotate.call_count} "
            "time(s) — this would incorrectly exhaust a credential for a format error."
        )

    def test_try_refresh_current_never_called(self):
        """pool.try_refresh_current must have zero calls for format_error."""
        mock_agent, mock_pool = self._make_mock_agent()
        recover_with_credential_pool(
            mock_agent,
            status_code=400,
            has_retried_429=False,
            classified_reason=FailoverReason.format_error,
        )
        assert mock_pool.try_refresh_current.call_count == 0, (
            f"try_refresh_current was called {mock_pool.try_refresh_current.call_count} "
            "time(s) — unexpected for format_error path."
        )

    def test_refresh_entry_never_called(self):
        """pool._refresh_entry must have zero calls for format_error."""
        mock_agent, mock_pool = self._make_mock_agent()
        recover_with_credential_pool(
            mock_agent,
            status_code=400,
            has_retried_429=False,
            classified_reason=FailoverReason.format_error,
        )
        assert mock_pool._refresh_entry.call_count == 0, (
            f"_refresh_entry was called {mock_pool._refresh_entry.call_count} "
            "time(s) — unexpected for format_error path."
        )

    def test_has_retried_429_preserved_when_true(self):
        """has_retried_429=True must be returned unchanged (False, True)."""
        mock_agent, _ = self._make_mock_agent()
        result = recover_with_credential_pool(
            mock_agent,
            status_code=400,
            has_retried_429=True,
            classified_reason=FailoverReason.format_error,
        )
        assert result == (False, True), (
            f"Expected (False, True) when has_retried_429=True, got {result}"
        )
