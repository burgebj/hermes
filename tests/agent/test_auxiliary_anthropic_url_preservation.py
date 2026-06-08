"""Regression guard for issue #17705 / #17413 / #17086: auxiliary 404s on
Anthropic-compatible endpoints (MiniMax /anthropic, Kimi /coding,
anthropic_messages custom proxies).

Root cause (fixed in PR #17467): ``_to_openai_base_url()`` rewrites
``…/anthropic`` → ``…/v1`` so the OpenAI SDK hits the right chat.completions
surface, but ``_maybe_wrap_anthropic`` was then passed the *rewritten* URL.
Its ``_endpoint_speaks_anthropic_messages`` detector only matches
``…/anthropic`` or ``api.kimi.com/coding`` — so the detector saw ``/v1``,
returned False, and never wrapped → 404 on every aux call.

Fix: pass the *raw* base URL to ``_maybe_wrap_anthropic`` while still giving
the rewritten URL to the OpenAI client constructor. These tests lock both
the primitive chokepoint behavior and the ``_resolve_api_key_provider``
call-site plumbing so a future narrow fix can't silently break it again.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
from unittest.mock import patch

import pytest

from agent.auxiliary_client import (
    AnthropicAuxiliaryClient,
    _endpoint_speaks_anthropic_messages,
    _maybe_wrap_anthropic,
    _resolve_api_key_provider,
    _to_openai_base_url,
)


# ── Primitive-level guards ────────────────────────────────────────────────


class TestDetectorTrustsRawUrl:
    """_endpoint_speaks_anthropic_messages must return True for the raw URL
    and False for the rewritten URL — so callers MUST pass the raw URL."""

    def test_minimax_anthropic_detected(self):
        assert _endpoint_speaks_anthropic_messages("https://api.minimax.chat/anthropic") is True
        # Rewritten form fails detection — this is WHY raw must be passed through.
        assert _endpoint_speaks_anthropic_messages("https://api.minimax.chat/v1") is False

    def test_minimax_cn_anthropic_detected(self):
        assert _endpoint_speaks_anthropic_messages("https://api.minimaxi.com/anthropic") is True

    def test_kimi_coding_detected(self):
        assert _endpoint_speaks_anthropic_messages("https://api.kimi.com/coding") is True

    def test_trailing_slash_tolerated(self):
        assert _endpoint_speaks_anthropic_messages("https://api.minimax.chat/anthropic/") is True

    def test_native_anthropic_detected(self):
        assert _endpoint_speaks_anthropic_messages("https://api.anthropic.com") is True

    def test_plain_openai_not_detected(self):
        assert _endpoint_speaks_anthropic_messages("https://api.openai.com/v1") is False


class TestMaybeWrapAnthropicOnRawUrl:
    """When given the RAW URL (as the fixed call sites do),
    ``_maybe_wrap_anthropic`` must rewrap a plain OpenAI client into an
    AnthropicAuxiliaryClient so that auxiliary tasks land on the correct
    Anthropic Messages transport."""

    def _make_plain_openai(self, base_url: str):
        from openai import OpenAI
        return OpenAI(api_key="sk-test-regression", base_url=base_url)

    def test_minimax_raw_url_wraps_client(self):
        raw_url = "https://api.minimax.chat/anthropic"
        rewritten = _to_openai_base_url(raw_url)
        assert rewritten == "https://api.minimax.chat/v1"

        plain = self._make_plain_openai(rewritten)
        wrapped = _maybe_wrap_anthropic(plain, "claude-haiku", "sk-test", raw_url)
        assert isinstance(wrapped, AnthropicAuxiliaryClient), (
            "Passing the raw /anthropic URL must trigger Anthropic wrapping "
            "— otherwise auxiliary tasks 404 on /v1/chat/completions."
        )

    def test_minimax_rewritten_url_does_not_wrap(self):
        """The regression shape: if a caller passes the REWRITTEN (/v1) URL,
        wrapping silently fails. Keeping this mechanically visible in the
        test suite makes future call-site drift obvious."""
        rewritten = "https://api.minimax.chat/v1"
        plain = self._make_plain_openai(rewritten)
        not_wrapped = _maybe_wrap_anthropic(plain, "claude-haiku", "sk-test", rewritten)
        assert not isinstance(not_wrapped, AnthropicAuxiliaryClient)

    def test_kimi_coding_raw_url_wraps_client(self):
        raw_url = "https://api.kimi.com/coding"
        plain = self._make_plain_openai(_to_openai_base_url(raw_url))
        wrapped = _maybe_wrap_anthropic(plain, "kimi-for-coding", "sk-test", raw_url)
        assert isinstance(wrapped, AnthropicAuxiliaryClient)

    def test_openai_endpoint_left_alone(self):
        """Plain OpenAI endpoints must never get wrapped — guards against
        over-eager wrapping of non-Anthropic traffic."""
        raw_url = "https://api.openai.com/v1"
        plain = self._make_plain_openai(raw_url)
        result = _maybe_wrap_anthropic(plain, "gpt-5", "sk-test", raw_url)
        assert not isinstance(result, AnthropicAuxiliaryClient)
        assert result is plain


# ── Call-site plumbing guards ─────────────────────────────────────────────
#
# These tests exercise `_resolve_api_key_provider()` with a simulated pool
# entry whose inference_base_url ends in `/anthropic`. They prove that the
# FOUR call sites PR #17467 fixed actually pass the raw URL through to
# `_maybe_wrap_anthropic` — not the rewritten URL. If anyone reverts any of
# those plumbing changes, these tests fail loudly.


@dataclass
class _FakePoolEntry:
    access_token: str = "sk-pool-test-key"
    inference_base_url: str = "https://api.minimax.chat/anthropic"
    portal_base_url: Optional[str] = None
    client_id: Optional[str] = None
    scope: Optional[str] = None
    token_type: str = "Bearer"
    refresh_token: Optional[str] = None
    agent_key: Optional[str] = None


@dataclass
class _FakePConfig:
    name: str = "MiniMax"
    auth_type: str = "api_key"
    inference_base_url: str = "https://api.minimax.chat/anthropic"


def _capture_wrap_calls(monkeypatch):
    """Replace _maybe_wrap_anthropic with a spy that records the base_url
    argument it was called with. Returns the list of calls."""
    import agent.auxiliary_client as ac
    captured: list = []

    def spy(client, model, api_key, base_url, *args, **kwargs):
        captured.append({"model": model, "base_url": base_url})
        # Delegate to the real implementation so we still exercise wrapping.
        return ac.__dict__["_maybe_wrap_anthropic_orig"](
            client, model, api_key, base_url, *args, **kwargs
        )

    monkeypatch.setattr(ac, "_maybe_wrap_anthropic_orig", ac._maybe_wrap_anthropic, raising=False)
    monkeypatch.setattr(ac, "_maybe_wrap_anthropic", spy)
    return captured


class TestResolveApiKeyProviderPlumbsRawUrl:
    """Exercises the 4 fixed call sites in ``_resolve_api_key_provider``:

    - pool path (line ~1034 after fix)
    - explicit-creds path (line ~1061 after fix)

    Both paths must forward the RAW /anthropic URL to _maybe_wrap_anthropic
    so that the detector can wrap into AnthropicAuxiliaryClient.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch):
        # Register one fake api_key provider. We stub the PROVIDER_REGISTRY
        # import at the call site so we don't pollute real provider config.
        import agent.auxiliary_client as ac
        fake_registry: Dict[str, _FakePConfig] = {"minimax": _FakePConfig()}

        fake_auth = type(
            "FakeAuth",
            (),
            {
                "PROVIDER_REGISTRY": fake_registry,
                "resolve_api_key_provider_credentials": staticmethod(
                    lambda pid: {"api_key": "sk-creds-test", "base_url": "https://api.minimax.chat/anthropic"}
                ),
                "is_provider_explicitly_configured": staticmethod(lambda pid: False),
            },
        )
        monkeypatch.setitem(__import__("sys").modules, "hermes_cli.auth", fake_auth)

        # Register a known model for the fake provider so the helper doesn't skip.
        monkeypatch.setitem(
            ac._API_KEY_PROVIDER_AUX_MODELS, "minimax", "claude-3-5-haiku-latest"
        )

    def test_pool_path_forwards_raw_anthropic_url(self, monkeypatch):
        """When the provider has a pool entry, the resolver must pass the raw
        /anthropic URL to _maybe_wrap_anthropic — not the /v1 rewrite."""
        captured = _capture_wrap_calls(monkeypatch)

        import agent.auxiliary_client as ac
        monkeypatch.setattr(
            ac, "_select_pool_entry", lambda pid: (True, _FakePoolEntry())
        )
        monkeypatch.setattr(ac, "_pool_runtime_api_key", lambda e: e.access_token)
        monkeypatch.setattr(
            ac, "_pool_runtime_base_url", lambda e, fallback: e.inference_base_url
        )

        client, model = _resolve_api_key_provider()

        assert client is not None, "resolver should return a client when pool entry present"
        assert model == "claude-3-5-haiku-latest"
        assert len(captured) == 1, "exactly one wrap call expected from pool path"
        assert captured[0]["base_url"] == "https://api.minimax.chat/anthropic", (
            f"Pool path must forward RAW /anthropic URL. Got: {captured[0]['base_url']!r}. "
            "If you see /v1, the call site regressed — PR #17467 split raw_base_url "
            "from the rewritten base_url for exactly this reason."
        )
        # And the client should actually be wrapped.
        assert isinstance(client, AnthropicAuxiliaryClient), (
            "Pool-path minimax client must be wrapped in AnthropicAuxiliaryClient "
            "— if you see a plain OpenAI client here, aux tasks will 404."
        )

    def test_explicit_creds_path_forwards_raw_anthropic_url(self, monkeypatch):
        """When no pool entry, the resolver falls back to resolve_api_key_provider_credentials.
        That branch must also forward the raw /anthropic URL."""
        captured = _capture_wrap_calls(monkeypatch)

        import agent.auxiliary_client as ac
        # Force no pool entry so we take the creds branch.
        monkeypatch.setattr(ac, "_select_pool_entry", lambda pid: (False, None))

        client, model = _resolve_api_key_provider()

        assert client is not None
        assert model == "claude-3-5-haiku-latest"
        assert len(captured) == 1, "exactly one wrap call expected from creds path"
        assert captured[0]["base_url"] == "https://api.minimax.chat/anthropic", (
            f"Explicit-creds path must forward RAW /anthropic URL. Got: {captured[0]['base_url']!r}."
        )
        assert isinstance(client, AnthropicAuxiliaryClient)
