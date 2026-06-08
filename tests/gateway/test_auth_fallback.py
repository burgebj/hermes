"""Test that AuthError triggers fallback provider resolution (#7230)."""

import logging
from unittest.mock import patch

import pytest


class TestResolveRuntimeAgentKwargsAuthFallback:
    """_resolve_runtime_agent_kwargs should try fallback on AuthError."""

    def test_auth_error_tries_fallback(self, tmp_path, monkeypatch):
        """When primary provider raises AuthError, fallback is attempted."""
        from hermes_cli.auth import AuthError

        # Create a config with fallback
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "model:\n  provider: openai-codex\n"
            "fallback_model:\n  provider: openrouter\n"
            "  model: meta-llama/llama-4-maverick\n"
        )

        monkeypatch.setattr("gateway.run._hermes_home", tmp_path)

        call_count = {"n": 0}

        def _mock_resolve(**kwargs):
            call_count["n"] += 1
            # First call = primary path (gateway reads model.provider from
            # config.yaml internally; we simulate the auth failure here).
            # Second call = fallback path with explicit_api_key + explicit_base_url
            # supplied by gateway from fallback_model config.
            if call_count["n"] == 1:
                raise AuthError("Codex token refresh failed with status 401")
            return {
                "api_key": "fallback-key",
                "base_url": "https://openrouter.ai/api/v1",
                "provider": "openrouter",
                "api_mode": "openai_chat",
                "command": None,
                "args": None,
                "credential_pool": None,
            }

        with patch(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            side_effect=_mock_resolve,
        ):
            from gateway.run import _resolve_runtime_agent_kwargs
            result = _resolve_runtime_agent_kwargs()

        assert result["provider"] == "openrouter"
        assert result["api_key"] == "fallback-key"
        # Should have been called at least twice (primary + fallback)
        assert call_count["n"] >= 2

    def test_auth_error_no_fallback_raises(self, tmp_path, monkeypatch):
        """When primary fails and no fallback configured, RuntimeError is raised."""
        from hermes_cli.auth import AuthError

        config_path = tmp_path / "config.yaml"
        config_path.write_text("model:\n  provider: openai-codex\n")

        monkeypatch.setattr("gateway.run._hermes_home", tmp_path)

        with patch(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            side_effect=AuthError("token expired"),
        ):
            from gateway.run import _resolve_runtime_agent_kwargs
            with pytest.raises(RuntimeError):
                _resolve_runtime_agent_kwargs()

    def test_legacy_fallback_is_appended_after_fallback_providers(self, tmp_path, monkeypatch):
        """When both keys exist, the legacy entry still participates in resolution."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "fallback_providers:\n"
            "  - provider: openrouter\n"
            "    model: anthropic/claude-sonnet-4.6\n"
            "fallback_model:\n"
            "  provider: nous\n"
            "  model: Hermes-4\n"
        )

        monkeypatch.setattr("gateway.run._hermes_home", tmp_path)

        calls = []

        def _mock_resolve(**kwargs):
            requested = kwargs.get("requested")
            calls.append(requested)
            if requested == "openrouter":
                raise RuntimeError("openrouter unavailable")
            return {
                "api_key": "nous-key",
                "base_url": "https://portal.nousresearch.com/v1",
                "provider": "nous",
                "api_mode": "chat_completions",
                "command": None,
                "args": None,
                "credential_pool": None,
            }

        with patch(
            "hermes_cli.runtime_provider.resolve_runtime_provider",
            side_effect=_mock_resolve,
        ):
            from gateway.run import _try_resolve_fallback_provider

            result = _try_resolve_fallback_provider()

        assert calls == ["openrouter", "nous"]
        assert result["provider"] == "nous"
        assert result["model"] == "Hermes-4"


class TestProviderErrorClassification:
    """Transient (rate-limit/quota) resolution failures must not be logged or
    reported as credential failures requiring re-auth (#32790)."""

    def test_transient_auth_error_not_logged_as_auth_failed(
        self, tmp_path, monkeypatch, caplog
    ):
        """A 429/quota AuthError (relogin_required=False) logs as transient."""
        from hermes_cli.auth import AuthError

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "model:\n  provider: openai-codex\n"
            "fallback_model:\n  provider: openrouter\n"
            "  model: meta-llama/llama-4-maverick\n"
        )
        monkeypatch.setattr("gateway.run._hermes_home", tmp_path)

        call_count = {"n": 0}

        def _mock_resolve(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # Upstream usage-limit during a real quota outage: the token is
                # valid, so relogin_required stays False.
                raise AuthError(
                    "Codex token refresh failed with status 429",
                    provider="openai-codex",
                    code="codex_refresh_failed",
                    relogin_required=False,
                )
            return {
                "api_key": "fallback-key",
                "base_url": "https://openrouter.ai/api/v1",
                "provider": "openrouter",
                "api_mode": "openai_chat",
                "command": None,
                "args": None,
                "credential_pool": None,
            }

        with (
            patch(
                "hermes_cli.runtime_provider.resolve_runtime_provider",
                side_effect=_mock_resolve,
            ),
            caplog.at_level(logging.WARNING, logger="gateway.run"),
        ):
            from gateway.run import _resolve_runtime_agent_kwargs

            _resolve_runtime_agent_kwargs()

        messages = [r.getMessage() for r in caplog.records]
        assert any("transient/rate-limit" in m for m in messages), messages
        assert not any("auth failed" in m for m in messages), messages

    def test_credential_auth_error_still_logged_as_auth_failed(
        self, tmp_path, monkeypatch, caplog
    ):
        """A genuine credential failure (relogin_required=True) keeps the
        re-auth wording so operators are still told to run `hermes auth`."""
        from hermes_cli.auth import AuthError

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "model:\n  provider: openai-codex\n"
            "fallback_model:\n  provider: openrouter\n"
            "  model: meta-llama/llama-4-maverick\n"
        )
        monkeypatch.setattr("gateway.run._hermes_home", tmp_path)

        call_count = {"n": 0}

        def _mock_resolve(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise AuthError(
                    "No Codex credentials stored. Run `hermes auth` to authenticate.",
                    provider="openai-codex",
                    code="codex_auth_missing",
                    relogin_required=True,
                )
            return {
                "api_key": "fallback-key",
                "base_url": "https://openrouter.ai/api/v1",
                "provider": "openrouter",
                "api_mode": "openai_chat",
                "command": None,
                "args": None,
                "credential_pool": None,
            }

        with (
            patch(
                "hermes_cli.runtime_provider.resolve_runtime_provider",
                side_effect=_mock_resolve,
            ),
            caplog.at_level(logging.WARNING, logger="gateway.run"),
        ):
            from gateway.run import _resolve_runtime_agent_kwargs

            _resolve_runtime_agent_kwargs()

        messages = [r.getMessage() for r in caplog.records]
        assert any("Primary provider auth failed" in m for m in messages), messages

    def test_fallback_resolution_logs_config_provider_not_category(
        self, tmp_path, monkeypatch, caplog
    ):
        """The fallback-resolved log must name the config `provider` key
        (e.g. ollama), not the normalized runtime category (openrouter)."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "fallback_providers:\n"
            "  - provider: ollama\n"
            "    base_url: http://localhost:11434/v1\n"
            "    model: llama3.1\n"
        )
        monkeypatch.setattr("gateway.run._hermes_home", tmp_path)

        def _mock_resolve(**kwargs):
            # OpenAI-compatible providers normalize to the generic openrouter
            # runtime category internally.
            return {
                "api_key": "",
                "base_url": "http://localhost:11434/v1",
                "provider": "openrouter",
                "api_mode": "openai_chat",
                "command": None,
                "args": None,
                "credential_pool": None,
            }

        with (
            patch(
                "hermes_cli.runtime_provider.resolve_runtime_provider",
                side_effect=_mock_resolve,
            ),
            caplog.at_level(logging.INFO, logger="gateway.run"),
        ):
            from gateway.run import _try_resolve_fallback_provider

            result = _try_resolve_fallback_provider()

        assert result is not None
        resolved_logs = [
            r.getMessage()
            for r in caplog.records
            if "Fallback provider resolved" in r.getMessage()
        ]
        assert resolved_logs, "expected a 'Fallback provider resolved' log line"
        assert any("ollama" in m for m in resolved_logs), resolved_logs
        assert not any("openrouter" in m for m in resolved_logs), resolved_logs
