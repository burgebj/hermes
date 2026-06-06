"""Tests for API server rate limiting."""
import threading
import time

import pytest


class TestRateLimiter:
    """Rate limiter should restrict requests per API key."""

    def test_allows_requests_within_limit(self):
        """Requests within the rate limit should be allowed."""
        from gateway.platforms.api_server import _RateLimiter

        limiter = _RateLimiter(max_requests=5, window_seconds=60)
        key = "test_key_1"

        for _ in range(5):
            assert limiter.is_allowed(key) is True

    def test_blocks_requests_exceeding_limit(self):
        """Requests exceeding the rate limit should be blocked."""
        from gateway.platforms.api_server import _RateLimiter

        limiter = _RateLimiter(max_requests=3, window_seconds=60)
        key = "test_key_1"

        for _ in range(3):
            assert limiter.is_allowed(key) is True

        # 4th request should be blocked
        assert limiter.is_allowed(key) is False

    def test_different_keys_independent(self):
        """Different API keys should have independent rate limits."""
        from gateway.platforms.api_server import _RateLimiter

        limiter = _RateLimiter(max_requests=2, window_seconds=60)

        # Exhaust key_1
        assert limiter.is_allowed("key_1") is True
        assert limiter.is_allowed("key_1") is True
        assert limiter.is_allowed("key_1") is False

        # key_2 should still be allowed
        assert limiter.is_allowed("key_2") is True

    def test_window_expiry_resets_limit(self):
        """After the window expires, the rate limit should reset."""
        from gateway.platforms.api_server import _RateLimiter

        limiter = _RateLimiter(max_requests=2, window_seconds=1)
        key = "test_key_1"

        assert limiter.is_allowed(key) is True
        assert limiter.is_allowed(key) is True
        assert limiter.is_allowed(key) is False

        # Wait for window to expire
        time.sleep(1.1)

        assert limiter.is_allowed(key) is True

    def test_no_rate_limit_when_disabled(self):
        """When max_requests is 0, no rate limiting should be applied."""
        from gateway.platforms.api_server import _RateLimiter

        limiter = _RateLimiter(max_requests=0, window_seconds=60)
        key = "test_key_1"

        # Should allow unlimited requests
        for _ in range(100):
            assert limiter.is_allowed(key) is True

    def test_thread_safety_exact_count(self):
        """Concurrent requests from multiple threads must not exceed the limit."""
        from gateway.platforms.api_server import _RateLimiter

        max_req = 10
        limiter = _RateLimiter(max_requests=max_req, window_seconds=60)
        key = "shared_key"

        allowed: list[bool] = []
        lock = threading.Lock()

        def worker():
            result = limiter.is_allowed(key)
            with lock:
                allowed.append(result)

        threads = [threading.Thread(target=worker) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(allowed) == 50
        assert allowed.count(True) == max_req, (
            f"Expected exactly {max_req} allowed requests, got {allowed.count(True)}"
        )
        assert allowed.count(False) == 50 - max_req

    def test_retry_after_returns_positive_seconds(self):
        """retry_after should return a positive integer when the key is rate-limited."""
        from gateway.platforms.api_server import _RateLimiter

        limiter = _RateLimiter(max_requests=2, window_seconds=10)
        key = "test_key_ra"

        limiter.is_allowed(key)
        limiter.is_allowed(key)
        assert limiter.is_allowed(key) is False

        ra = limiter.retry_after(key)
        assert isinstance(ra, int)
        assert 1 <= ra <= 10, f"retry_after {ra} is outside expected range [1, 10]"

    def test_retry_after_returns_zero_when_disabled(self):
        """retry_after should return 0 when rate limiting is disabled."""
        from gateway.platforms.api_server import _RateLimiter

        limiter = _RateLimiter(max_requests=0, window_seconds=60)
        assert limiter.retry_after("any_key") == 0

    def test_memory_eviction_after_window_expiry(self):
        """Expired bucket entries should be evicted when the key is next accessed.

        The eviction is lazy (per-key on next access), so only the keys that
        are accessed after their window expires are cleaned up.  This test
        verifies that accessing an expired key does NOT leave a stale empty
        list behind — the key is either removed or carries only the new
        timestamp.
        """
        from gateway.platforms.api_server import _RateLimiter

        limiter = _RateLimiter(max_requests=5, window_seconds=1)
        key = "evict_key"

        # Exhaust the limit
        for _ in range(5):
            limiter.is_allowed(key)
        assert limiter.is_allowed(key) is False

        # Wait for the window to expire
        time.sleep(1.1)

        # After expiry the key should be allowed again (old timestamps pruned)
        assert limiter.is_allowed(key) is True

        # The bucket must contain exactly the one new timestamp — no stale entries
        with limiter._lock:
            bucket = limiter._buckets.get(key, [])
        assert len(bucket) == 1, (
            f"Expected 1 active timestamp after eviction, got {len(bucket)}"
        )

    def test_stale_keys_do_not_accumulate_unboundedly(self):
        """Keys that stop making requests must not permanently grow the bucket dict.

        Eviction is lazy, so stale keys remain until next access.  This test
        confirms that re-accessing a previously-exhausted key after its window
        expires resets the bucket to a single entry rather than accumulating
        all historical timestamps.
        """
        from gateway.platforms.api_server import _RateLimiter

        limiter = _RateLimiter(max_requests=3, window_seconds=1)
        key = "accumulation_key"

        # Drive the key through several full windows
        for _ in range(3):
            for _ in range(3):
                limiter.is_allowed(key)
            time.sleep(1.1)

        # Final access after all windows expired
        limiter.is_allowed(key)

        with limiter._lock:
            bucket = limiter._buckets.get(key, [])
        # Only the single most-recent timestamp should remain
        assert len(bucket) == 1, (
            f"Timestamps accumulated across windows: {len(bucket)} entries"
        )
