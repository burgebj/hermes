"""
CPU throttle guardrail. See YOOL_TUPLE_HAMT.md §11.1.

Soft throttle via process niceness. For hard throttle, use cgroups (Linux)
or taskpolicy (macOS) at process launch — see spec §11.1.
"""

from __future__ import annotations

import contextlib
import os
import time

DEFAULT_CPU_QUOTA_PCT = 95
DEFAULT_LANE_CONCURRENCY = 32
DEFAULT_MAX_LANE_CONCURRENCY = 64


def _positive_int_from_env(names: tuple[str, ...], default: int) -> int:
    for name in names:
        value = os.getenv(name)
        if value is None or not value.strip():
            continue
        try:
            parsed = int(value)
        except ValueError:
            return default
        return parsed if parsed > 0 else default
    return default


def cpu_quota_from_env(default: int = DEFAULT_CPU_QUOTA_PCT) -> int:
    """Return CPU quota from env aliases, clamped to [1, 100]."""
    quota = _positive_int_from_env(
        ("YOOL_TUPLE_CPU_QUOTA_PCT", "YOOL_CPU_QUOTA_PCT"), default
    )
    return max(1, min(100, quota))


def lane_concurrency_from_env(default: int = DEFAULT_LANE_CONCURRENCY) -> int:
    """Return preferred workers per lane for high-throughput runtimes."""
    return _positive_int_from_env(
        ("YOOL_TUPLE_LANE_CONCURRENCY", "YOOL_LANE_CONCURRENCY"),
        default,
    )


def max_lane_concurrency_from_env(default: int = DEFAULT_MAX_LANE_CONCURRENCY) -> int:
    """Return the per-lane worker ceiling used by high-throughput runtimes."""
    return _positive_int_from_env(
        ("YOOL_TUPLE_MAX_LANE_CONCURRENCY", "YOOL_MAX_LANE_CONCURRENCY"),
        default,
    )


@contextlib.contextmanager
def cpu_throttle(quota_pct: int):
    """
    Reduce CPU pressure by raising process niceness for the duration.
    quota_pct in [1, 100]. quota=100 -> no-op.
    """
    if quota_pct >= 100:
        yield
        return
    if quota_pct < 1:
        quota_pct = 1

    nice_delta = max(0, min(19, int(round((100 - quota_pct) / 5.2))))
    applied = False
    try:
        os.nice(nice_delta)
        applied = True
    except OSError:
        pass
    try:
        yield
    finally:
        if applied:
            try:
                os.nice(-nice_delta)
            except OSError:
                pass


def cooperative_yield(quota_pct: int, last_yield: list[float]) -> None:
    """In-loop cooperative throttle. Caller passes mutable single-element list as state."""
    if quota_pct >= 100:
        return
    now = time.monotonic()
    elapsed = now - last_yield[0]
    sleep_for = elapsed * (100 - quota_pct) / max(1, quota_pct)
    if sleep_for > 0.001:
        time.sleep(min(sleep_for, 1.0))
    last_yield[0] = time.monotonic()


class DiskQuotaExceeded(RuntimeError):
    pass


def disk_quota_check(path: str, max_mb: int) -> None:
    """Raise DiskQuotaExceeded if `path` exceeds max_mb."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    mb = total / (1024 * 1024)
    if mb > max_mb:
        raise DiskQuotaExceeded(f"{path} = {mb:.1f}MB > limit {max_mb}MB")


@contextlib.contextmanager
def disk_quota(max_mb: int, path: str = "."):
    """Context-manager wrapper around disk_quota_check."""
    yield
    disk_quota_check(path, max_mb)
