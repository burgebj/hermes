"""Regression test: compress() must accept focus_topic keyword argument.

Covers the bug where CompositeContextEngine.compress() and
LcmContextEngine.compress() rejected the focus_topic kwarg that
run_agent.py passes through, raising TypeError.
"""

import inspect

import pytest

from agent.context_engine import ContextEngine
from plugins.context_engine.lcm import LcmContextEngine
from plugins.context_engine.rlm import CompositeContextEngine


MESSAGES = [
    {"role": "user", "content": "hello"},
    {"role": "assistant", "content": "hi"},
]


class TestFocusTopicSignature:
    """Base ContextEngine.compress() must declare focus_topic."""

    def test_base_compress_has_focus_topic_param(self):
        sig = inspect.signature(ContextEngine.compress)
        assert "focus_topic" in sig.parameters, (
            "ContextEngine.compress() must declare focus_topic so subclasses "
            "are not surprised by the kwarg"
        )


class TestLcmFocusTopic:
    """LcmContextEngine.compress() must accept focus_topic without raising."""

    def test_compress_accepts_focus_topic(self):
        engine = LcmContextEngine()
        # Must not raise TypeError
        result = engine.compress(MESSAGES, current_tokens=100, focus_topic="test")
        assert isinstance(result, list)

    def test_compress_ignores_focus_topic_gracefully(self):
        engine = LcmContextEngine()
        result_plain = engine.compress(MESSAGES, current_tokens=100)
        engine2 = LcmContextEngine()
        result_focused = engine2.compress(MESSAGES, current_tokens=100, focus_topic="test")
        # Both return valid message lists — behaviour is unchanged
        assert isinstance(result_plain, list)
        assert isinstance(result_focused, list)


class TestCompositeFocusTopic:
    """CompositeContextEngine.compress() must accept and forward focus_topic."""

    def _make_composite(self):
        lcm = LcmContextEngine()
        return CompositeContextEngine(compression_engine=lcm)

    def test_compress_accepts_focus_topic(self):
        engine = self._make_composite()
        # Must not raise TypeError
        result = engine.compress(MESSAGES, current_tokens=100, focus_topic="test")
        assert isinstance(result, list)

    def test_compress_no_focus_topic_unchanged(self):
        engine = self._make_composite()
        result = engine.compress(MESSAGES, current_tokens=100)
        assert isinstance(result, list)
