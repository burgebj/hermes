"""Regression guard: don't send Anthropic ``thinking`` to StepFun step-3.7-flash.

StepFun's ``step-3.7-flash`` is surfaced over the ``anthropic_messages``
transport (the default for the Nous Portal). It does not speak Anthropic's
manual extended-thinking protocol: it drives reasoning server-side via its own
``reasoning_effort``. When ``build_anthropic_kwargs`` injects
``thinking={type: enabled, budget_tokens: N}`` and forces ``temperature: 1``,
the model degrades and multi-turn tool calls break -- the generic third-party
path strips the (unsigned) thinking blocks on replay while still advertising
``thinking.enabled``.

This is the same failure mode that #17455 fixed for Kimi. step-3.7-flash needs
its own carve-out. See #39124.
"""

from __future__ import annotations

import pytest


class TestStepFunSkipsAnthropicThinking:
    """build_anthropic_kwargs must not inject thinking for step-3.7 models."""

    @pytest.mark.parametrize(
        "model",
        [
            "step-3.7-flash",
            "stepfun/step-3.7-flash",
            "stepfun/step-3.7-flash:free",
            "step-3.7-flash-2506",
        ],
    )
    def test_step_37_omits_thinking(self, model: str) -> None:
        from agent.anthropic_adapter import build_anthropic_kwargs

        kwargs = build_anthropic_kwargs(
            model=model,
            messages=[{"role": "user", "content": "hello"}],
            tools=None,
            max_tokens=4096,
            reasoning_config={"enabled": True, "effort": "medium"},
            base_url="https://inference-api.nousresearch.com/v1",
        )
        assert "thinking" not in kwargs, (
            "Anthropic thinking must not be sent to step-3.7-flash -- the "
            "model doesn't speak the protocol and tool-call replay breaks."
        )
        assert "output_config" not in kwargs

    def test_step_37_does_not_force_temperature(self) -> None:
        from agent.anthropic_adapter import build_anthropic_kwargs

        kwargs = build_anthropic_kwargs(
            model="stepfun/step-3.7-flash:free",
            messages=[{"role": "user", "content": "hello"}],
            tools=None,
            max_tokens=4096,
            reasoning_config={"enabled": True, "effort": "medium"},
            base_url="https://inference-api.nousresearch.com/v1",
        )
        assert kwargs.get("temperature") != 1, (
            "step-3.7-flash must not be force-set to temperature=1; that knob "
            "belongs to Anthropic manual-thinking models only."
        )

    def test_step_37_with_reasoning_disabled_also_omits(self) -> None:
        from agent.anthropic_adapter import build_anthropic_kwargs

        kwargs = build_anthropic_kwargs(
            model="stepfun/step-3.7-flash:free",
            messages=[{"role": "user", "content": "hello"}],
            tools=None,
            max_tokens=4096,
            reasoning_config={"enabled": False},
            base_url="https://inference-api.nousresearch.com/v1",
        )
        assert "thinking" not in kwargs


class TestStepFunGateIsNarrow:
    """The carve-out is anchored on the step-3.7 token, nothing wider."""

    def test_minimax_third_party_still_gets_thinking(self) -> None:
        from agent.anthropic_adapter import build_anthropic_kwargs

        kwargs = build_anthropic_kwargs(
            model="MiniMax-M2.7",
            messages=[{"role": "user", "content": "hello"}],
            tools=None,
            max_tokens=4096,
            reasoning_config={"enabled": True, "effort": "medium"},
            base_url="https://api.minimax.io/anthropic",
        )
        assert "thinking" in kwargs
        assert kwargs["thinking"]["type"] == "enabled"

    def test_native_anthropic_still_gets_thinking(self) -> None:
        from agent.anthropic_adapter import build_anthropic_kwargs

        kwargs = build_anthropic_kwargs(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "hello"}],
            tools=None,
            max_tokens=4096,
            reasoning_config={"enabled": True, "effort": "medium"},
            base_url=None,
        )
        assert "thinking" in kwargs

    def test_bare_version_lookalike_not_matched(self) -> None:
        """A bare ``3.7`` or an unrelated ``step-13.7`` must not trip the gate."""
        from agent.anthropic_adapter import build_anthropic_kwargs

        kwargs = build_anthropic_kwargs(
            model="vendor/step-13.7-flash",
            messages=[{"role": "user", "content": "hello"}],
            tools=None,
            max_tokens=4096,
            reasoning_config={"enabled": True, "effort": "medium"},
            base_url="https://api.example.com/anthropic",
        )
        assert "thinking" in kwargs, (
            "Only the step-3.7 token should be suppressed; step-13.7 must keep "
            "its existing behavior."
        )
