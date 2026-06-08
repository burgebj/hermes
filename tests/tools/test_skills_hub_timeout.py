"""
Test that parallel_search_sources respects the overall_timeout even when
source threads block on network calls (ThreadPoolExecutor shutdown hang).
"""
import time
from typing import List

import pytest

from tools.skills_hub import (
    SkillSource,
    SkillMeta,
    SkillBundle,
    parallel_search_sources,
)


class BlockingSource(SkillSource):
    """A source that blocks forever in search(), simulating a network hang."""

    def source_id(self) -> str:
        return "blocking"

    def search(self, query: str, limit: int = 10) -> List[SkillMeta]:
        # Simulate a hanging network call — blocks indefinitely
        time.sleep(9999)
        return []

    def fetch(self, identifier: str) -> SkillBundle | None:
        return None

    def inspect(self, identifier: str) -> SkillMeta | None:
        return None


class FastSource(SkillSource):
    """A fast source that returns results immediately."""

    def source_id(self) -> str:
        return "fast"

    def search(self, query: str, limit: int = 10) -> List[SkillMeta]:
        return [
            SkillMeta(
                name="test-skill",
                description="A test skill",
                source="fast",
                identifier="fast/test-skill",
                trust_level="community",
            )
        ]

    def fetch(self, identifier: str) -> SkillBundle | None:
        return None

    def inspect(self, identifier: str) -> SkillMeta | None:
        return None


class TestParallelSearchSourcesTimeout:
    """Verify that parallel_search_sources returns within the overall_timeout,
    even when some source threads are blocked on network I/O."""

    def test_returns_within_timeout_when_source_hangs(self):
        """A hanging source must not block shutdown past overall_timeout."""
        sources = [BlockingSource(), FastSource()]
        overall_timeout = 2.0  # seconds

        start = time.monotonic()
        all_results, source_counts, timed_out_ids = parallel_search_sources(
            sources,
            query="test",
            overall_timeout=overall_timeout,
        )
        elapsed = time.monotonic() - start

        # Must return within a reasonable margin above the timeout
        # (2s timeout + 2s grace for thread cleanup)
        assert elapsed < overall_timeout + 2.0, (
            f"parallel_search_sources took {elapsed:.1f}s, "
            f"expected < {overall_timeout + 2.0}s"
        )

        # The fast source should have completed
        assert "fast" in source_counts
        assert source_counts["fast"] >= 1

        # The blocking source should be in timed_out_ids
        assert "blocking" in timed_out_ids

    def test_all_sources_fast_returns_full_results(self):
        """When all sources are fast, all results should be returned."""
        sources = [FastSource(), FastSource()]
        overall_timeout = 5.0

        start = time.monotonic()
        all_results, source_counts, timed_out_ids = parallel_search_sources(
            sources,
            query="test",
            overall_timeout=overall_timeout,
        )
        elapsed = time.monotonic() - start

        assert elapsed < 2.0, "Should complete quickly when sources are fast"
        assert len(timed_out_ids) == 0
        assert len(all_results) == 2  # one from each FastSource
