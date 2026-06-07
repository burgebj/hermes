"""Tests for SecretResolver policy gates and SecretValue redaction."""

import json

import pytest

from agent.secrets import (
    CallerBoundary,
    EnvSecretProvider,
    RuntimeMode,
    SecretAccessDenied,
    SecretProviderStatus,
    SecretRequestContext,
    SecretResolver,
    SecretResolutionError,
    SecretValue,
)

SENTINEL = "S3NTINEL_DO_NOT_PERSIST_secret_provider_core"


def first_party_context(**overrides):
    data = {
        "provider": "openrouter",
        "purpose": "provider_api_key",
        "runtime_mode": RuntimeMode.CLI,
        "profile": "default",
        "caller_boundary": CallerBoundary.CORE,
        "local_unlock_allowed": False,
        "audit_label": "test-openrouter",
    }
    data.update(overrides)
    return SecretRequestContext(**data)


def test_secret_value_requires_explicit_reveal_and_redacts_common_string_paths():
    value = SecretValue(SENTINEL, source="env:OPENROUTER_API_KEY")

    assert value.reveal() == SENTINEL
    with value.reveal_temporarily() as revealed:
        assert revealed == SENTINEL

    rendered = [str(value), repr(value), f"{value}", json.dumps({"secret": value}, default=str)]
    for text in rendered:
        assert SENTINEL not in text
        assert "<redacted" in text or "SecretValue" in text

    public = value.to_public_dict()
    assert SENTINEL not in json.dumps(public, sort_keys=True)
    assert public["redacted"] is True
    assert public["source"] == "env:OPENROUTER_API_KEY"


def test_secret_value_redacts_source_and_metadata_if_provider_supplies_secret_material():
    value = SecretValue(
        SENTINEL,
        source=SENTINEL,
        metadata={"raw": SENTINEL, "nested": ["prefix", SENTINEL]},
    )

    rendered = [
        str(value),
        repr(value),
        json.dumps({"secret": value}, default=str),
        json.dumps(value.to_public_dict(), sort_keys=True),
    ]

    for text in rendered:
        assert SENTINEL not in text


def test_env_provider_resolves_registered_env_ref_for_core_context(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL)
    resolver = SecretResolver()
    resolver.register(EnvSecretProvider())

    value = resolver.resolve("env:OPENROUTER_API_KEY", first_party_context())

    assert isinstance(value, SecretValue)
    assert value.reveal() == SENTINEL
    assert SENTINEL not in repr(value)


def test_resolver_denies_tool_plugin_and_subprocess_boundaries_by_default(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL)
    resolver = SecretResolver([EnvSecretProvider()])

    for boundary in (CallerBoundary.TOOL, CallerBoundary.PLUGIN, CallerBoundary.SUBPROCESS):
        with pytest.raises(SecretAccessDenied):
            resolver.resolve(
                "env:OPENROUTER_API_KEY",
                first_party_context(caller_boundary=boundary),
            )


def test_resolver_denies_wrong_provider_or_purpose_even_for_core_boundary(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL)
    resolver = SecretResolver([EnvSecretProvider()])

    with pytest.raises(SecretAccessDenied):
        resolver.resolve(
            "env:OPENROUTER_API_KEY",
            first_party_context(provider="anthropic"),
        )

    with pytest.raises(SecretAccessDenied):
        resolver.resolve(
            "env:OPENROUTER_API_KEY",
            first_party_context(purpose="debug_dump"),
        )


def test_resolver_denies_wrong_provider_for_refresh_token_secret_refs():
    class DummySecretServiceProvider:
        backend = "secret-service"

        def status(self):
            return SecretProviderStatus.AVAILABLE

        def resolve(self, ref, context):
            return SecretValue(SENTINEL, source=ref.display_safe)

    resolver = SecretResolver([DummySecretServiceProvider()])

    with pytest.raises(SecretAccessDenied):
        resolver.resolve(
            "secret://secret-service/hermes/openrouter/refresh_token",
            first_party_context(
                provider="anthropic",
                purpose="provider_refresh_token",
            ),
        )


def test_resolver_fails_closed_for_missing_backend():
    resolver = SecretResolver()

    with pytest.raises(SecretResolutionError) as excinfo:
        resolver.resolve("secret://secret-service/hermes/openrouter/api_key", first_party_context())

    assert "No secret provider registered" in str(excinfo.value)


def test_env_provider_missing_value_fails_closed_without_plaintext_fallback(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    resolver = SecretResolver([EnvSecretProvider()])

    with pytest.raises(SecretResolutionError) as excinfo:
        resolver.resolve("env:OPENROUTER_API_KEY", first_party_context())

    assert "OPENROUTER_API_KEY" in str(excinfo.value)
    assert SENTINEL not in str(excinfo.value)


def test_resolver_fails_closed_when_provider_status_not_available(monkeypatch):
    class LockedProvider(EnvSecretProvider):
        def status(self):
            return SecretProviderStatus.LOCKED

    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL)
    resolver = SecretResolver([LockedProvider()])

    with pytest.raises(SecretResolutionError) as excinfo:
        resolver.resolve("env:OPENROUTER_API_KEY", first_party_context())

    assert "locked" in str(excinfo.value).lower()
    assert SENTINEL not in str(excinfo.value)


def test_resolver_fails_closed_for_invalid_provider_status(monkeypatch):
    class BadStatusProvider(EnvSecretProvider):
        def status(self):  # type: ignore[override]
            return "surprising"

    monkeypatch.setenv("OPENROUTER_API_KEY", SENTINEL)
    resolver = SecretResolver([BadStatusProvider()])

    with pytest.raises(SecretResolutionError) as excinfo:
        resolver.resolve("env:OPENROUTER_API_KEY", first_party_context())

    assert "invalid status" in str(excinfo.value).lower()
    assert SENTINEL not in str(excinfo.value)
