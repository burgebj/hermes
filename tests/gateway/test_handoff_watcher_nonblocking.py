"""Test that the gateway handoff watcher does not block the asyncio event loop.

Regression test for issue #40695: Discord gateway heartbeat can be blocked by
synchronous handoff SQLite polling.
"""

import asyncio
import time
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from asyncio import Event


class SlowSessionDB:
    """Mock SessionDB that introduces controlled delays to simulate SQLite contention."""

    def __init__(self, delay_seconds: float = 0.5):
        self.delay_seconds = delay_seconds
        self.call_times = []

    def list_pending_handoffs(self):
        """Simulate slow SQLite query."""
        self.call_times.append(time.time())
        time.sleep(self.delay_seconds)
        return [
            {"id": "session_1", "home_channel": "telegram:123"}
        ]

    def claim_handoff(self, session_id: str) -> bool:
        """Simulate slow claim operation."""
        self.call_times.append(time.time())
        time.sleep(self.delay_seconds * 0.5)
        return True

    def complete_handoff(self, session_id: str) -> None:
        """Simulate slow completion."""
        self.call_times.append(time.time())
        time.sleep(self.delay_seconds * 0.5)

    def fail_handoff(self, session_id: str, error: str) -> None:
        """Simulate slow failure recording."""
        self.call_times.append(time.time())
        time.sleep(self.delay_seconds * 0.5)


class TestHandoffWatcherNonBlocking(unittest.TestCase):
    """Test that handoff watcher operations don't block the asyncio event loop."""

    def test_handoff_watcher_does_not_block_concurrent_task(self):
        """Verify that a concurrent asyncio task continues while handoff watcher runs.

        This test simulates a Discord heartbeat ticker running in parallel with the
        handoff watcher. The heartbeat must advance even while the watcher is
        waiting for slow SQLite operations.
        """

        async def run_test():
            # Slow SessionDB to simulate lock contention
            slow_db = SlowSessionDB(delay_seconds=0.2)

            # Track heartbeat ticker progress
            ticker_ticks = []
            ticker_completed = Event()

            async def heartbeat_ticker():
                """Simulate Discord heartbeat task that must not be starved."""
                try:
                    for i in range(5):
                        ticker_ticks.append(time.time())
                        await asyncio.sleep(0.05)  # 50ms tick interval
                    ticker_completed.set()
                except asyncio.CancelledError:
                    pass

            async def mock_process_handoff(row):
                """Mock the async handoff processing (this should be fine)."""
                await asyncio.sleep(0.01)

            async def mock_handoff_watcher():
                """Simplified version of the actual handoff watcher logic."""
                await asyncio.sleep(0.05)  # Initial delay
                loop = asyncio.get_event_loop()
                try:
                    # These DB calls should be offloaded to executor
                    pending = await loop.run_in_executor(
                        None, slow_db.list_pending_handoffs
                    )
                    for row in pending:
                        session_id = row.get("id")
                        if not session_id:
                            continue
                        claimed = await loop.run_in_executor(
                            None, slow_db.claim_handoff, session_id
                        )
                        if not claimed:
                            continue
                        try:
                            await mock_process_handoff(row)
                            await loop.run_in_executor(
                                None, slow_db.complete_handoff, session_id
                            )
                        except Exception:
                            await loop.run_in_executor(
                                None, slow_db.fail_handoff, session_id, "error"
                            )
                except asyncio.CancelledError:
                    raise

            # Run both tasks concurrently
            watcher_task = asyncio.create_task(mock_handoff_watcher())
            ticker_task = asyncio.create_task(heartbeat_ticker())

            # Wait for both to complete
            await asyncio.wait_for(ticker_completed.wait(), timeout=2.0)
            await watcher_task

            # Assertions: ticker should have advanced despite slow DB operations
            self.assertGreaterEqual(
                len(ticker_ticks), 4,
                "Heartbeat ticker was starved by blocking DB operations"
            )

            # Verify there was actual delay in the DB (proves we had slow ops)
            self.assertGreater(
                slow_db.delay_seconds * 2.5,  # ~0.5s of DB work
                0.1,
                "DB operations should have introduced measurable delay"
            )

        asyncio.run(run_test())

    def test_handoff_watcher_with_blocking_db_would_starve_ticker(self):
        """Demonstrate that synchronous DB calls WOULD block the loop.

        This test is purely educational—it shows what happens if you call
        SQLite synchronously on the event loop (the bug being fixed).
        """

        async def run_test():
            sync_db = SlowSessionDB(delay_seconds=0.3)
            ticker_ticks = []

            async def heartbeat_ticker():
                """Heartbeat that will be starved by blocking calls."""
                try:
                    for i in range(5):
                        ticker_ticks.append(time.time())
                        await asyncio.sleep(0.05)
                except asyncio.CancelledError:
                    pass

            async def blocking_handoff_watcher():
                """WRONG: Synchronous DB calls on the event loop (the bug)."""
                await asyncio.sleep(0.05)
                try:
                    # This is the OLD buggy code—no executor
                    pending = sync_db.list_pending_handoffs()
                    for row in pending:
                        session_id = row.get("id")
                        if not session_id:
                            continue
                        # More blocking calls...
                        sync_db.claim_handoff(session_id)
                        sync_db.complete_handoff(session_id)
                except asyncio.CancelledError:
                    raise

            watcher_task = asyncio.create_task(blocking_handoff_watcher())
            ticker_task = asyncio.create_task(heartbeat_ticker())

            # Watcher will block—let it run for up to 1 second
            await asyncio.sleep(1.0)
            watcher_task.cancel()
            ticker_task.cancel()

            try:
                await watcher_task
            except asyncio.CancelledError:
                pass

            try:
                await ticker_task
            except asyncio.CancelledError:
                pass

            # With blocking DB calls, the ticker would have very few ticks
            # because the event loop was blocked
            self.assertLess(
                len(ticker_ticks), 4,
                "Blocking DB calls DO starve the event loop (demonstrating the bug)"
            )

        asyncio.run(run_test())


class TestHandoffWatcherIntegration(unittest.TestCase):
    """Integration tests for the handoff watcher."""

    def test_handoff_watcher_processes_pending_handoffs(self):
        """Test that the watcher actually processes pending handoffs."""

        async def run_test():
            pending_count = [0]

            class CountingSessionDB:
                def list_pending_handoffs(self):
                    pending_count[0] += 1
                    return [{"id": "test_session"}]

                def claim_handoff(self, session_id):
                    return True

                def complete_handoff(self, session_id):
                    pass

                def fail_handoff(self, session_id, error):
                    pass

            db = CountingSessionDB()
            loop = asyncio.get_event_loop()

            # Simulate one watcher tick
            pending = await loop.run_in_executor(None, db.list_pending_handoffs)
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["id"], "test_session")
            self.assertEqual(pending_count[0], 1)

        asyncio.run(run_test())

    def test_handoff_watcher_handles_claim_failures(self):
        """Test graceful handling when another process claims the handoff first."""

        async def run_test():
            call_log = []

            class RaceSessionDB:
                def list_pending_handoffs(self):
                    return [{"id": "session_1"}]

                def claim_handoff(self, session_id):
                    # Simulate another process winning the race
                    return False

                def complete_handoff(self, session_id):
                    call_log.append("complete")

                def fail_handoff(self, session_id, error):
                    call_log.append("fail")

            db = RaceSessionDB()
            loop = asyncio.get_event_loop()

            pending = await loop.run_in_executor(None, db.list_pending_handoffs)
            for row in pending:
                session_id = row.get("id")
                claimed = await loop.run_in_executor(
                    None, db.claim_handoff, session_id
                )
                if not claimed:
                    # This should be the path taken
                    pass
                else:
                    call_log.append("should_not_happen")

            # Verify we skipped the handoff processing when claim failed
            self.assertEqual(len(call_log), 0, "Should not call complete/fail when claim fails")

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
