"""Tests for model_extra type guard in tool call normalization.

Providers like NVIDIA NIM may return model_extra as a string instead
of a dict, causing AttributeError on .get() calls.  The isinstance
guard prevents this crash.
"""
import unittest
from types import SimpleNamespace

from agent.transports.chat_completions import ChatCompletionsTransport
from agent.transports.types import ToolCall


class TestModelExtraTypeGuard(unittest.TestCase):
    """Ensure the isinstance(dict) guard handles all model_extra types."""

    def _extract(self, model_extra):
        """Replicate the guarded extraction pattern used in production."""
        return (model_extra if isinstance(model_extra, dict) else {}).get(
            "extra_content"
        )

    def test_string_no_crash(self):
        """String model_extra must not raise AttributeError."""
        self.assertIsNone(self._extract("unexpected_string"))

    def test_none_no_crash(self):
        self.assertIsNone(self._extract(None))

    def test_dict_extracts_extra_content(self):
        self.assertEqual(
            self._extract({"extra_content": {"key": "val"}}),
            {"key": "val"},
        )

    def test_empty_dict(self):
        self.assertIsNone(self._extract({}))

    def test_integer_no_crash(self):
        self.assertIsNone(self._extract(42))

    def test_list_no_crash(self):
        self.assertIsNone(self._extract(["a", "b"]))

    def test_bool_no_crash(self):
        """Boolean True is truthy but not a dict."""
        self.assertIsNone(self._extract(True))


class TestNormalizeResponseModelExtraGuard(unittest.TestCase):
    """Integration: normalize_response must not crash on non-dict model_extra."""

    def test_string_model_extra_normalize(self):
        """Tool call with string model_extra should normalize without error."""
        transport = ChatCompletionsTransport.__new__(ChatCompletionsTransport)

        tc = SimpleNamespace(
            id="call_1",
            type="function",
            function=SimpleNamespace(name="test_tool", arguments='{"x": 1}'),
            extra_content=None,
            model_extra="nvidia_nim_extra_string",
        )
        choice = SimpleNamespace(
            index=0,
            message=SimpleNamespace(
                role="assistant",
                content=None,
                tool_calls=[tc],
                refusal=None,
            ),
            finish_reason="tool_calls",
        )
        response = SimpleNamespace(
            id="resp_1",
            choices=[choice],
            usage=SimpleNamespace(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
            model="test-model",
        )

        result = transport.normalize_response(response)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0].name, "test_tool")

    def test_dict_model_extra_with_extra_content(self):
        """Dict model_extra with extra_content should be preserved."""
        transport = ChatCompletionsTransport.__new__(ChatCompletionsTransport)

        tc = SimpleNamespace(
            id="call_1",
            type="function",
            function=SimpleNamespace(name="test_tool", arguments='{}'),
            extra_content=None,
            model_extra={"extra_content": {"thought_signature": "abc123"}},
        )
        choice = SimpleNamespace(
            index=0,
            message=SimpleNamespace(
                role="assistant",
                content=None,
                tool_calls=[tc],
                refusal=None,
            ),
            finish_reason="tool_calls",
        )
        response = SimpleNamespace(
            id="resp_1",
            choices=[choice],
            usage=SimpleNamespace(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
            model="test-model",
        )

        result = transport.normalize_response(response)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(
            result.tool_calls[0].provider_data.get("extra_content"),
            {"thought_signature": "abc123"},
        )
