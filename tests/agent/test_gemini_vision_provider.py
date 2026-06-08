"""Tests for explicit gemini vision provider resolution.

Regression tests for #33389: when auxiliary.vision.provider is explicitly
set to gemini, the vision routing should honor it instead of falling through
to the generic _get_cached_client path.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestGeminiVisionExplicitProvider:
    """Explicit ``auxiliary.vision.provider: gemini`` must route correctly."""

    def test_explicit_gemini_vision_returns_client(self, monkeypatch):
        """_resolve_strict_vision_backend('gemini') must return a client,
        not (None, None)."""
        from agent.auxiliary_client import _resolve_strict_vision_backend

        fake_client = MagicMock(name="gemini_client")
        monkeypatch.setattr(
            "agent.auxiliary_client.resolve_provider_client",
            lambda provider, model=None, **kw: (fake_client, "gemini-3.5-flash")
            if provider == "gemini"
            else (None, None),
        )

        client, default_model = _resolve_strict_vision_backend("gemini")
        assert client is fake_client
        assert default_model == "gemini-3.5-flash"

    def test_explicit_gemini_vision_passes_is_vision(self, monkeypatch):
        """_resolve_strict_vision_backend('gemini') must pass is_vision=True
        to resolve_provider_client so the client is flagged correctly."""
        from agent.auxiliary_client import _resolve_strict_vision_backend

        rpc_calls = []
        fake_client = MagicMock(name="gemini_client")

        def fake_rpc(provider, model=None, **kwargs):
            rpc_calls.append((provider, kwargs))
            return (fake_client, "gemini-3.5-flash") if provider == "gemini" else (None, None)

        monkeypatch.setattr(
            "agent.auxiliary_client.resolve_provider_client",
            fake_rpc,
        )

        _resolve_strict_vision_backend("gemini")
        assert len(rpc_calls) == 1
        assert rpc_calls[0][0] == "gemini"
        assert rpc_calls[0][1].get("is_vision") is True

    def test_explicit_gemini_vision_with_model_override(self, monkeypatch):
        """When caller passes a model, it should flow through."""
        from agent.auxiliary_client import _resolve_strict_vision_backend

        fake_client = MagicMock(name="gemini_client")
        captured = {}

        def fake_rpc(provider, model=None, **kwargs):
            captured["model"] = model
            return (fake_client, model or "gemini-3.5-flash") if provider == "gemini" else (None, None)

        monkeypatch.setattr(
            "agent.auxiliary_client.resolve_provider_client",
            fake_rpc,
        )

        client, model = _resolve_strict_vision_backend("gemini", model="gemini-2.5-pro")
        assert client is fake_client
        assert captured["model"] == "gemini-2.5-pro"

    def test_explicit_gemini_vision_no_credentials(self, monkeypatch):
        """When Gemini has no API key, _resolve_strict_vision_backend
        should return (None, None) gracefully."""
        from agent.auxiliary_client import _resolve_strict_vision_backend

        monkeypatch.setattr(
            "agent.auxiliary_client.resolve_provider_client",
            lambda provider, model=None, **kw: (None, None),
        )

        client, model = _resolve_strict_vision_backend("gemini")
        assert client is None
        assert model is None

    def test_resolve_vision_provider_client_explicit_gemini(self, monkeypatch):
        """End-to-end: resolve_vision_provider_client(provider='gemini')
        should return a gemini client, not fall through to generic path."""
        from agent.auxiliary_client import resolve_vision_provider_client

        fake_client = MagicMock(name="gemini_client")

        monkeypatch.setattr(
            "agent.auxiliary_client._resolve_task_provider_model",
            lambda *a, **kw: ("gemini", "gemini-3.5-flash", None, None, None),
        )
        monkeypatch.setattr(
            "agent.auxiliary_client.resolve_provider_client",
            lambda *args, **kwargs: (fake_client, "gemini-3.5-flash")
            if args and args[0] == "gemini"
            else (None, None),
        )

        provider, client, model = resolve_vision_provider_client(provider="gemini")
        assert provider == "gemini"
        assert client is fake_client
        assert model == "gemini-3.5-flash"

    def test_gemini_aliases_normalize_to_gemini(self, monkeypatch):
        """Provider aliases like 'google' and 'google-gemini' should
        normalize to 'gemini' and still work."""
        from agent.auxiliary_client import _resolve_strict_vision_backend

        fake_client = MagicMock(name="gemini_client")
        monkeypatch.setattr(
            "agent.auxiliary_client.resolve_provider_client",
            lambda provider, model=None, **kw: (fake_client, "gemini-3.5-flash")
            if provider == "gemini"
            else (None, None),
        )

        for alias in ("google", "google-gemini", "google-ai-studio"):
            client, model = _resolve_strict_vision_backend(alias)
            assert client is fake_client, f"alias {alias!r} failed"
