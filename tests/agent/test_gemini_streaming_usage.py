"""Tests for Gemini streaming usageMetadata extraction.

The streaming path must extract token counts from usageMetadata on
the finish chunk, matching the non-streaming translate_gemini_response
behavior.
"""
import unittest

from agent.gemini_native_adapter import translate_stream_event


class TestGeminiStreamingUsageMetadata(unittest.TestCase):
    """Verify usageMetadata is attached to streaming finish chunks."""

    def _finish_event(self, usage_meta=None):
        """Create a Gemini streaming event with finishReason and optional usageMetadata."""
        event = {
            "candidates": [{
                "content": {"parts": [], "role": "model"},
                "finishReason": "STOP",
            }],
        }
        if usage_meta is not None:
            event["usageMetadata"] = usage_meta
        return event

    def _get_usage(self, chunks):
        """Extract usage from a list of chunks, if present."""
        for c in chunks:
            usage = getattr(c, "usage", None)
            if usage is not None:
                return usage
        return None

    def test_usage_attached_on_finish(self):
        """Finish chunk should carry usage from usageMetadata."""
        event = self._finish_event({
            "promptTokenCount": 100,
            "candidatesTokenCount": 50,
            "totalTokenCount": 150,
            "cachedContentTokenCount": 20,
        })
        chunks = translate_stream_event(event, model="gemini-2.5-pro", tool_call_indices={})
        usage = self._get_usage(chunks)
        self.assertIsNotNone(usage, "Finish chunk should have usage")
        self.assertEqual(usage.prompt_tokens, 100)
        self.assertEqual(usage.completion_tokens, 50)
        self.assertEqual(usage.total_tokens, 150)
        self.assertEqual(usage.prompt_tokens_details.cached_tokens, 20)

    def test_no_usage_when_metadata_absent(self):
        """When usageMetadata is missing, finish chunk should not have usage."""
        chunks = translate_stream_event(
            self._finish_event(), model="gemini-2.5-pro", tool_call_indices={}
        )
        self.assertIsNone(self._get_usage(chunks))

    def test_partial_metadata_defaults_to_zero(self):
        """Missing fields in usageMetadata should default to 0."""
        event = self._finish_event({
            "promptTokenCount": 200,
            "totalTokenCount": 200,
            # candidatesTokenCount and cachedContentTokenCount missing
        })
        chunks = translate_stream_event(event, model="gemini-2.5-pro", tool_call_indices={})
        usage = self._get_usage(chunks)
        self.assertIsNotNone(usage)
        self.assertEqual(usage.prompt_tokens, 200)
        self.assertEqual(usage.completion_tokens, 0)
        self.assertEqual(usage.prompt_tokens_details.cached_tokens, 0)

    def test_empty_metadata_no_usage(self):
        """Empty usageMetadata dict should not create usage."""
        chunks = translate_stream_event(
            self._finish_event({}), model="gemini-2.5-pro", tool_call_indices={}
        )
        self.assertIsNone(self._get_usage(chunks))
