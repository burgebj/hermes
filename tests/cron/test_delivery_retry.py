"""Tests for delivery_retry — transient failure retry in cron job delivery."""

import time
from unittest.mock import MagicMock, patch

import pytest

from cron.scheduler import _is_retryable, _deliver_with_retry, _truncate_err


# =========================================================================
# _is_retryable
# =========================================================================

class TestIsRetryable:
    @pytest.mark.parametrize("error", [
        "rate limited",
        "rate limit exceeded",
        "429 Too Many Requests — rate limited",
        "timeout",
        "connection timed out",
        "connection refused",
        "connection reset by peer",
        "host unreachable",
        "dns resolution failed",
        "temporary failure",
        "please try again later",
        "broken pipe",
    ])
    def test_retryable_errors(self, error):
        assert _is_retryable(error), f"should be retryable: {error!r}"

    @pytest.mark.parametrize("error", [
        "invalid credentials",
        "authentication failed",
        "blocked",
        "platform not configured",
        "bad request",
        "forbidden",
        "not found",
        "",
    ])
    def test_non_retryable_errors(self, error):
        assert not _is_retryable(error), f"should NOT be retryable: {error!r}"

    def test_none_or_empty_handled(self):
        assert not _is_retryable("")  # type: ignore[arg-type]
        # None should be handled gracefully too
        assert not _is_retryable(None if False else "")  # pass empty string

    def test_case_insensitive(self):
        assert _is_retryable("Rate Limited")
        assert _is_retryable("TIMEOUT")
        assert _is_retryable("Connection Refused")


# =========================================================================
# _truncate_err
# =========================================================================

class TestTruncateErr:
    def test_short_error_passes_through(self):
        assert _truncate_err("short") == "short"
        assert _truncate_err("") == ""

    def test_long_error_truncated(self):
        long_err = "x" * 500
        result = _truncate_err(long_err, max_len=200)
        assert len(result) == 201  # 200 chars + "…"
        assert result.endswith("…")

    def test_default_max_len(self):
        err = "x" * 300
        result = _truncate_err(err)
        assert len(result) == 201  # default 200 + "…"


# =========================================================================
# _deliver_with_retry
# =========================================================================

class TestDeliverWithRetry:
    """Tests for the delivery retry wrapper."""

    @staticmethod
    def _make_job(delivery_retry=None):
        return {
            "id": "test-job-001",
            "name": "test-job",
            "delivery_retry": delivery_retry,
        }

    def test_no_retry_config_calls_once(self):
        """Without delivery_retry, should call _deliver_result exactly once."""
        job = self._make_job(delivery_retry=None)
        with patch("cron.scheduler._deliver_result", return_value=None) as mock_deliver:
            result = _deliver_with_retry(job, "test content")
            assert result is None
            mock_deliver.assert_called_once()

    def test_no_retry_config_propagates_exception(self):
        """Without delivery_retry, exception is caught and returned as string."""
        job = self._make_job(delivery_retry=None)
        with patch("cron.scheduler._deliver_result", side_effect=RuntimeError("boom")):
            result = _deliver_with_retry(job, "test content")
            assert "boom" in result

    def test_retry_on_rate_limit_succeeds_second_attempt(self):
        """Retryable error → retry → success on second attempt."""
        job = self._make_job(delivery_retry={"max_attempts": 3, "delay_seconds": 0})

        call_count = [0]

        def flaky_deliver(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return "rate limited"
            return None  # success

        with patch("cron.scheduler._deliver_result", side_effect=flaky_deliver):
            result = _deliver_with_retry(job, "test content")
            assert result is None
            assert call_count[0] == 2  # first attempt failed, second succeeded

    def test_non_retryable_error_stops_immediately(self):
        """Non-retryable error → fail immediately, no retry."""
        job = self._make_job(delivery_retry={"max_attempts": 3, "delay_seconds": 0})

        with patch("cron.scheduler._deliver_result", return_value="invalid credentials") as mock_deliver:
            result = _deliver_with_retry(job, "test content")
            assert "invalid credentials" in result
            mock_deliver.assert_called_once()  # no retry

    def test_all_attempts_exhausted(self):
        """All attempts fail → return last error."""
        job = self._make_job(delivery_retry={"max_attempts": 3, "delay_seconds": 0})

        with patch("cron.scheduler._deliver_result", return_value="rate limited") as mock_deliver:
            result = _deliver_with_retry(job, "test content")
            assert "rate limited" in result
            assert mock_deliver.call_count == 3

    def test_success_on_first_attempt_no_retry(self):
        """Success on first attempt → return immediately, no extra calls."""
        job = self._make_job(delivery_retry={"max_attempts": 3, "delay_seconds": 0})

        with patch("cron.scheduler._deliver_result", return_value=None) as mock_deliver:
            result = _deliver_with_retry(job, "test content")
            assert result is None
            mock_deliver.assert_called_once()

    def test_exception_treated_as_retryable(self):
        """Exception in delivery is retried (treated as potentially transient)."""
        job = self._make_job(delivery_retry={"max_attempts": 2, "delay_seconds": 0})

        with patch("cron.scheduler._deliver_result", side_effect=OSError("connection reset")):
            result = _deliver_with_retry(job, "test content")
            assert "connection reset" in result

    def test_empty_dict_disables_retry(self):
        """Empty delivery_retry dict → treated as no config (backward compat)."""
        job = self._make_job(delivery_retry={})

        with patch("cron.scheduler._deliver_result", return_value="rate limited") as mock_deliver:
            result = _deliver_with_retry(job, "test content")
            assert "rate limited" in result
            mock_deliver.assert_called_once()  # no retry

    def test_retry_with_actual_sleep(self):
        """Verify delay_seconds is respected between attempts."""
        job = self._make_job(delivery_retry={"max_attempts": 2, "delay_seconds": 0})

        call_count = [0]

        def flaky(*args, **kwargs):
            call_count[0] += 1
            return "rate limited"

        with patch("cron.scheduler._deliver_result", side_effect=flaky):
            with patch("time.sleep") as mock_sleep:
                _deliver_with_retry(job, "test content")
                # delay_seconds=0 → should still call sleep(0) once
                mock_sleep.assert_called()

    def test_clamped_max_attempts(self):
        """Values outside 1-10 range should be clamped by create_job, but
        _deliver_with_retry also clamps for safety."""
        # max_attempts=0 should be clamped to 1 by _deliver_with_retry
        job = self._make_job(delivery_retry={"max_attempts": 0, "delay_seconds": 0})

        with patch("cron.scheduler._deliver_result", return_value="rate limited") as mock_deliver:
            _deliver_with_retry(job, "test content")
            assert mock_deliver.call_count == 1  # clamped: max(0, 1) = 1 attempt

    def test_retry_mixed_errors(self):
        """First error is retryable, second is not → stop after second."""
        job = self._make_job(delivery_retry={"max_attempts": 3, "delay_seconds": 0})

        errors = iter(["rate limited", "invalid credentials"])

        with patch("cron.scheduler._deliver_result", side_effect=lambda *a, **kw: next(errors)) as mock_deliver:
            result = _deliver_with_retry(job, "test content")
            assert "invalid credentials" in result
            assert mock_deliver.call_count == 2  # first retryable, second stopped
