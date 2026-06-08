"""Tests for the 1M-context beta header on AWS Bedrock Claude models.

Claude Opus 4.6/4.7 and Sonnet 4.6 support a 1M context window, but on AWS
Bedrock (and Microsoft Foundry) that window is still gated behind the
``context-1m-2025-08-07`` beta header as of 2026-04. Without it, Bedrock
caps these models at 200K even though ``model_metadata.py`` advertises 1M.

These tests guard the invariant that the header is always emitted on the
Bedrock client path, and that it survives the MiniMax bearer-auth strip.

The ``TestBedrockConverse1MBeta`` and ``TestBedrockContextLength1M``
classes cover the *native* Bedrock Converse adapter
(``agent/bedrock_adapter.py``) — PR #16793 only patched the OpenAI-compat
``AnthropicBedrock`` SDK path; users on the wizard's recommended
``bedrock_converse`` provider were stuck at 200K. Issue #31277.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestBedrockContext1MBeta:
    """``context-1m-2025-08-07`` must reach Bedrock Claude requests."""



    def test_common_betas_strips_1m_for_minimax(self):
        """MiniMax bearer-auth endpoints host their own models — strip 1M beta."""
        from agent.anthropic_adapter import (
            _common_betas_for_base_url,
            _CONTEXT_1M_BETA,
        )

        for url in (
            "https://api.minimax.io/anthropic",
            "https://api.minimaxi.com/anthropic",
        ):
            betas = _common_betas_for_base_url(url)
            assert _CONTEXT_1M_BETA not in betas, (
                f"1M beta must be stripped for MiniMax bearer endpoint {url}"
            )
            # Other betas still present
            assert "interleaved-thinking-2025-05-14" in betas

    def test_build_anthropic_bedrock_client_sends_1m_beta(self):
        """AnthropicBedrock client must carry the 1M beta in default_headers.

        This is the load-bearing assertion for the reported bug:
        without this header Bedrock serves Opus 4.6/4.7 with a 200K cap.
        """
        import agent.anthropic_adapter as adapter

        fake_sdk = MagicMock()
        fake_sdk.AnthropicBedrock = MagicMock()

        with patch.object(adapter, "_anthropic_sdk", fake_sdk):
            adapter.build_anthropic_bedrock_client(region="us-west-2")

        call_kwargs = fake_sdk.AnthropicBedrock.call_args.kwargs
        assert call_kwargs["aws_region"] == "us-west-2"

        default_headers = call_kwargs.get("default_headers") or {}
        beta_header = default_headers.get("anthropic-beta", "")
        assert "context-1m-2025-08-07" in beta_header, (
            "Bedrock client must send context-1m-2025-08-07 or Opus 4.6/4.7 "
            "silently caps at 200K context"
        )
        # Other common betas still present — no regression.
        assert "interleaved-thinking-2025-05-14" in beta_header
        assert "fine-grained-tool-streaming-2025-05-14" in beta_header


# ---------------------------------------------------------------------------
# Native Bedrock Converse adapter — issue #31277
# ---------------------------------------------------------------------------


@pytest.fixture
def bedrock_1m_opt_in(monkeypatch):
    """Set ``HERMES_BEDROCK_1M_CONTEXT=1`` for the duration of the test."""
    monkeypatch.setenv("HERMES_BEDROCK_1M_CONTEXT", "1")


@pytest.fixture
def bedrock_1m_opt_out(monkeypatch):
    """Ensure the opt-in env var is unset (default behavior)."""
    monkeypatch.delenv("HERMES_BEDROCK_1M_CONTEXT", raising=False)


class TestBedrockConverseOptInGate:
    """``HERMES_BEDROCK_1M_CONTEXT`` controls whether the beta is injected."""

    def test_opt_in_truthy_values(self, monkeypatch):
        from agent.bedrock_adapter import bedrock_1m_context_enabled

        for val in ("1", "true", "yes", "on", "TRUE", "Yes"):
            monkeypatch.setenv("HERMES_BEDROCK_1M_CONTEXT", val)
            assert bedrock_1m_context_enabled() is True, val

    def test_opt_out_default_and_falsy(self, monkeypatch):
        from agent.bedrock_adapter import bedrock_1m_context_enabled

        monkeypatch.delenv("HERMES_BEDROCK_1M_CONTEXT", raising=False)
        assert bedrock_1m_context_enabled() is False

        for val in ("0", "false", "no", "off", "", "  "):
            monkeypatch.setenv("HERMES_BEDROCK_1M_CONTEXT", val)
            assert bedrock_1m_context_enabled() is False, val


class TestAnthropicOpus4Capability:
    """``is_anthropic_opus_4_1m_capable`` matches all Bedrock spelling variants."""

    @pytest.mark.parametrize(
        "model_id",
        [
            "anthropic.claude-opus-4-7",
            "us.anthropic.claude-opus-4-7",
            "global.anthropic.claude-opus-4-7-20260101-v1:0",
            "anthropic.claude-opus-4-6",
            "us.anthropic.claude-opus-4-6",
            "anthropic.claude-sonnet-4-6",
            "global.anthropic.claude-sonnet-4-6",
            # Dot-spelling (OpenRouter-style) — unlikely on Bedrock but the
            # lookup table accepts both so the matcher must too.
            "anthropic.claude-opus-4.7",
            "anthropic.claude-sonnet-4.6",
        ],
    )
    def test_capable_models(self, model_id):
        from agent.bedrock_adapter import is_anthropic_opus_4_1m_capable

        assert is_anthropic_opus_4_1m_capable(model_id) is True, model_id

    @pytest.mark.parametrize(
        "model_id",
        [
            "anthropic.claude-opus-4",
            "anthropic.claude-sonnet-4",
            "anthropic.claude-sonnet-4-5",
            "anthropic.claude-haiku-4-5",
            "anthropic.claude-3-5-sonnet",
            "anthropic.claude-3-opus",
            "amazon.nova-pro",
            "meta.llama4-maverick",
            "",
            "claude-opus-4",
        ],
    )
    def test_non_capable_models(self, model_id):
        from agent.bedrock_adapter import is_anthropic_opus_4_1m_capable

        assert is_anthropic_opus_4_1m_capable(model_id) is False, model_id


class TestBedrockConverse1MBeta:
    """``build_converse_kwargs`` injects the 1M beta when capable + opt-in."""

    def test_opt_in_capable_model_injects_beta(self, bedrock_1m_opt_in):
        from agent.bedrock_adapter import build_converse_kwargs

        kwargs = build_converse_kwargs(
            model="us.anthropic.claude-opus-4-7",
            messages=[{"role": "user", "content": "hi"}],
        )

        assert kwargs.get("additionalModelRequestFields") == {
            "anthropic_beta": ["context-1m-2025-08-07"],
        }

    def test_opt_in_capable_sonnet_46(self, bedrock_1m_opt_in):
        from agent.bedrock_adapter import build_converse_kwargs

        kwargs = build_converse_kwargs(
            model="global.anthropic.claude-sonnet-4-6",
            messages=[{"role": "user", "content": "hi"}],
        )

        assert kwargs["additionalModelRequestFields"]["anthropic_beta"] == [
            "context-1m-2025-08-07"
        ]

    def test_opt_out_does_not_inject(self, bedrock_1m_opt_out):
        from agent.bedrock_adapter import build_converse_kwargs

        kwargs = build_converse_kwargs(
            model="us.anthropic.claude-opus-4-7",
            messages=[{"role": "user", "content": "hi"}],
        )

        assert "additionalModelRequestFields" not in kwargs

    def test_opt_in_non_capable_model_does_not_inject(self, bedrock_1m_opt_in):
        """Opus 4.0 / Sonnet 4 / Nova etc. don't get the beta even if opted in.

        AWS rejects the beta on models that don't carry the entitlement, so
        guarding by capability is mandatory — opt-in is necessary but not
        sufficient.
        """
        from agent.bedrock_adapter import build_converse_kwargs

        for model in (
            "anthropic.claude-opus-4",
            "anthropic.claude-sonnet-4-5",
            "amazon.nova-pro",
            "meta.llama4-maverick",
        ):
            kwargs = build_converse_kwargs(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
            )
            assert "additionalModelRequestFields" not in kwargs, model

    def test_caller_supplied_betas_are_merged_not_clobbered(self, bedrock_1m_opt_in):
        """Future callers passing extended-thinking betas must not lose them."""
        from agent.bedrock_adapter import build_converse_kwargs

        kwargs = build_converse_kwargs(
            model="us.anthropic.claude-opus-4-7",
            messages=[{"role": "user", "content": "hi"}],
            additional_model_request_fields={
                "anthropic_beta": ["fine-grained-tool-streaming-2025-05-14"],
                "extra_field": "preserved",
            },
        )

        betas = kwargs["additionalModelRequestFields"]["anthropic_beta"]
        assert "fine-grained-tool-streaming-2025-05-14" in betas
        assert "context-1m-2025-08-07" in betas
        assert kwargs["additionalModelRequestFields"]["extra_field"] == "preserved"

    def test_no_double_injection_when_caller_already_has_1m_beta(self, bedrock_1m_opt_in):
        """Caller-supplied 1M beta isn't duplicated."""
        from agent.bedrock_adapter import build_converse_kwargs

        kwargs = build_converse_kwargs(
            model="us.anthropic.claude-opus-4-7",
            messages=[{"role": "user", "content": "hi"}],
            additional_model_request_fields={
                "anthropic_beta": ["context-1m-2025-08-07"],
            },
        )

        betas = kwargs["additionalModelRequestFields"]["anthropic_beta"]
        assert betas.count("context-1m-2025-08-07") == 1

    def test_opt_out_preserves_caller_supplied_extra_fields(self, bedrock_1m_opt_out):
        """Caller-supplied additional fields survive even when opt-in is OFF."""
        from agent.bedrock_adapter import build_converse_kwargs

        kwargs = build_converse_kwargs(
            model="us.anthropic.claude-opus-4-7",
            messages=[{"role": "user", "content": "hi"}],
            additional_model_request_fields={"some_other_field": 42},
        )

        assert kwargs["additionalModelRequestFields"] == {"some_other_field": 42}


class TestBedrockContextLength1M:
    """``get_bedrock_context_length`` returns 1M only with capability + opt-in."""

    def test_opt_in_capable_returns_1m(self, bedrock_1m_opt_in):
        from agent.bedrock_adapter import get_bedrock_context_length

        for model in (
            "us.anthropic.claude-opus-4-7",
            "anthropic.claude-opus-4-7",
            "anthropic.claude-opus-4-6",
            "anthropic.claude-sonnet-4-6",
        ):
            assert get_bedrock_context_length(model) == 1_000_000, model

    def test_opt_out_capable_returns_200k(self, bedrock_1m_opt_out):
        """Default behavior preserved for accounts without the entitlement."""
        from agent.bedrock_adapter import get_bedrock_context_length

        for model in (
            "us.anthropic.claude-opus-4-7",
            "anthropic.claude-opus-4-6",
            "anthropic.claude-sonnet-4-6",
        ):
            assert get_bedrock_context_length(model) == 200_000, model

    def test_opt_in_non_capable_returns_default(self, bedrock_1m_opt_in):
        """Opt-in does NOT bump non-1M-capable models above their cap."""
        from agent.bedrock_adapter import get_bedrock_context_length

        assert get_bedrock_context_length("anthropic.claude-sonnet-4-5") == 200_000
        assert get_bedrock_context_length("anthropic.claude-3-5-sonnet") == 200_000
        assert get_bedrock_context_length("amazon.nova-pro") == 300_000

    def test_opus_4_7_in_static_table(self):
        """Regression for the missing ``claude-opus-4-7`` table entry from #31277."""
        from agent.bedrock_adapter import BEDROCK_CONTEXT_LENGTHS

        assert "anthropic.claude-opus-4-7" in BEDROCK_CONTEXT_LENGTHS
        assert BEDROCK_CONTEXT_LENGTHS["anthropic.claude-opus-4-7"] == 200_000
