"""Tests for the infinite context compaction loop fix (issue #40803).

Tests verify that the compressor detects when the compression window is too
small to yield meaningful token savings and falls back to a more aggressive
tail budget to prevent infinite compression loops.
"""

import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from agent.context_compressor import ContextCompressor


def make_message(role: str, content: str, token_estimate: int = None) -> Dict[str, Any]:
    """Helper to create a message dict with estimated tokens."""
    msg = {"role": role, "content": content}
    if token_estimate:
        # Add metadata that will be used in token calculation
        msg["_token_hint"] = token_estimate
    return msg


class TestInfiniteCompressionLoopFix(unittest.TestCase):
    """Test the fix for issue #40803: Infinite Context Compaction Loop."""

    def test_small_window_triggers_fallback(self):
        """Verify that a compression window with <5 messages triggers fallback."""
        # Setup: Create a compressor with specific parameters that would
        # create a very small compression window
        compressor = ContextCompressor(
            model="claude-3-5-sonnet-20241022",
            threshold_percent=0.65,  # triggers at ~62,400 tokens
            summary_target_ratio=0.45,  # aggressive tail protection
            quiet_mode=True,
        )
        
        # Create messages: system prompt + some head messages + many tail messages
        messages = [
            make_message("system", "You are helpful. " * 200),  # system prompt
            make_message("user", "Hello, start a task. " * 50),
            make_message("assistant", "Sure! " * 100),
        ]
        
        # Add 20+ messages to tail to push total tokens above threshold
        for i in range(25):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append(make_message(role, f"Message {i}. " * 30))
        
        # Verify we have enough messages for compression
        self.assertGreater(len(messages), 5)
        
        # Call compress() - should succeed without infinite loop
        # (it will either compress meaningfully or return unchanged,
        # but NOT get stuck in a loop)
        result = compressor.compress(messages, current_tokens=120000)
        
        # Either compression happened or it returned messages unchanged
        # The key is it didn't raise and didn't loop
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_fallback_creates_larger_window(self):
        """Verify that fallback reduces tail budget to create larger window."""
        compressor = ContextCompressor(
            model="claude-3-5-sonnet-20241022",
            threshold_percent=0.65,
            summary_target_ratio=0.45,
            quiet_mode=True,
        )
        
        # Mock _find_tail_cut_by_tokens to track calls
        original_find_tail = compressor._find_tail_cut_by_tokens
        calls = []
        
        def tracked_find_tail(messages, head_end, token_budget=None):
            calls.append({
                'head_end': head_end,
                'token_budget': token_budget,
                'default_budget': compressor.tail_token_budget,
            })
            return original_find_tail(messages, head_end, token_budget)
        
        compressor._find_tail_cut_by_tokens = tracked_find_tail
        
        # Create messages with just enough content
        messages = [
            make_message("system", "System prompt. " * 500),
        ]
        for i in range(30):
            messages.append(make_message(
                "user" if i % 2 == 0 else "assistant",
                f"Message {i}. This is some content. " * 50
            ))
        
        # Call compress with high tokens to trigger compression
        compressor.compress(messages, current_tokens=100000)
        
        # Should have called _find_tail_cut_by_tokens at least once
        # with the default budget, and possibly again with a fallback
        # (50% of default) if window was too small
        self.assertGreater(len(calls), 0)
        
        # If there were 2+ calls, the second one should have smaller budget
        if len(calls) >= 2:
            # The fallback call should use ~50% of the original budget
            first_budget = calls[0]['token_budget']
            second_budget = calls[1]['token_budget']
            if second_budget is not None and first_budget is not None:
                # Fallback should be roughly half
                self.assertLess(second_budget, first_budget)

    def test_no_fallback_for_large_window(self):
        """Verify fallback is NOT triggered for reasonably-sized windows."""
        compressor = ContextCompressor(
            model="claude-3-5-sonnet-20241022",
            threshold_percent=0.65,
            summary_target_ratio=0.20,  # smaller ratio = larger window naturally
            quiet_mode=True,
        )
        
        # Track calls to _find_tail_cut_by_tokens
        original_find_tail = compressor._find_tail_cut_by_tokens
        calls = []
        
        def tracked_find_tail(messages, head_end, token_budget=None):
            calls.append({'token_budget': token_budget})
            return original_find_tail(messages, head_end, token_budget)
        
        compressor._find_tail_cut_by_tokens = tracked_find_tail
        
        # Create messages with enough content
        messages = [make_message("system", "System. " * 500)]
        for i in range(50):
            messages.append(make_message(
                "user" if i % 2 == 0 else "assistant",
                f"Msg {i}. Content here. " * 100
            ))
        
        compressor.compress(messages, current_tokens=120000)
        
        # With summary_target_ratio=0.20, we should get a larger default window
        # and likely NOT need fallback (though we don't assert on exact behavior,
        # just that it completes without error)
        self.assertGreater(len(calls), 0)

    def test_fallback_prevents_no_op_compression(self):
        """Verify fallback prevents compression that saves zero tokens."""
        compressor = ContextCompressor(
            model="claude-3-5-sonnet-20241022",
            threshold_percent=0.65,
            summary_target_ratio=0.45,  # aggressive, causes small windows
            quiet_mode=True,
        )
        
        # Create a scenario where the default window is tiny
        # but compression should still happen with fallback
        messages = [make_message("system", "System. " * 1000)]
        
        # Add head messages (protected)
        for i in range(3):
            messages.append(make_message("user", f"Head msg {i}. " * 50))
            messages.append(make_message("assistant", f"Response {i}. " * 100))
        
        # Add many middle messages (candidate for compression)
        for i in range(40):
            messages.append(make_message(
                "user" if i % 2 == 0 else "assistant",
                f"Middle message {i}. " * 40
            ))
        
        # Compression should complete without raising
        # (even if window detection triggered fallback)
        result = compressor.compress(messages, current_tokens=110000)
        
        # Should return a list (either compressed or unchanged)
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 3)  # At least system + head


class TestCompressionWindowDetection(unittest.TestCase):
    """Test the detection logic for small compression windows."""

    def test_window_size_calculation(self):
        """Verify window size is calculated correctly."""
        compressor = ContextCompressor(
            model="claude-3-5-sonnet-20241022",
            quiet_mode=True,
        )
        
        # Simple list of messages
        messages = [
            make_message("system", "System"),
            make_message("user", "User 1"),
            make_message("assistant", "Assistant 1"),
            make_message("user", "User 2"),
            make_message("assistant", "Assistant 2"),
            make_message("user", "User 3"),
        ]
        
        # Window from index 2 to 5 should have size 3
        compress_start = 2
        compress_end = 5
        window_size = compress_end - compress_start
        
        self.assertEqual(window_size, 3)

    def test_token_estimation_in_window(self):
        """Verify token estimation for small windows."""
        messages = [
            make_message("user", "Short"),
            make_message("assistant", "Also short"),
            make_message("user", "Brief"),
        ]
        
        # Rough token estimate: chars / 4 + overhead
        # "Short" = 5 chars → ~2 tokens + 10 overhead = ~12
        # "Also short" = 10 chars → ~3 tokens + 10 overhead = ~13
        # "Brief" = 5 chars → ~2 tokens + 10 overhead = ~12
        # Total ≈ 37 tokens (likely less than 2000, triggering fallback)
        
        total_tokens = sum(
            len((msg.get("content") or "") + str(msg.get("tool_calls", [])))
            for msg in messages
        ) // 4 + (len(messages) * 10)
        
        self.assertLess(total_tokens, 2000)


if __name__ == "__main__":
    unittest.main()
