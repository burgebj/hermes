"""Tests for SecretRef parsing and display-safe behavior."""

import json

import pytest

from agent.secrets import SecretRef, SecretRefError


def test_parse_secret_service_uri_preserves_locator_parts_without_secret_value():
    ref = SecretRef.parse("secret://secret-service/hermes/openrouter/api_key?label=primary")

    assert ref.scheme == "secret"
    assert ref.backend == "secret-service"
    assert ref.path == ("hermes", "openrouter", "api_key")
    assert ref.name == "api_key"
    assert ref.query == {"label": "primary"}
    assert ref.original == "secret://secret-service/hermes/openrouter/api_key?label=primary"
    assert ref.normalized == "secret://secret-service/hermes/openrouter/api_key?label=primary"
    assert ref.display_safe == "secret://secret-service/hermes/openrouter/api_key?label=primary"


def test_parse_systemd_uri_uses_systemd_backend_and_single_name():
    ref = SecretRef.parse("systemd://openrouter_api_key")

    assert ref.scheme == "systemd"
    assert ref.backend == "systemd"
    assert ref.path == ("openrouter_api_key",)
    assert ref.name == "openrouter_api_key"
    assert ref.query == {}
    assert ref.normalized == "systemd://openrouter_api_key"


def test_parse_env_reference_uses_env_backend_without_reading_environment():
    ref = SecretRef.parse("env:OPENROUTER_API_KEY")

    assert ref.scheme == "env"
    assert ref.backend == "env"
    assert ref.path == ("OPENROUTER_API_KEY",)
    assert ref.name == "OPENROUTER_API_KEY"
    assert ref.query == {}
    assert ref.normalized == "env:OPENROUTER_API_KEY"
    assert "sk-" not in ref.display_safe


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "not-a-secret-ref",
        "env:",
        "env:OPEN ROUTER KEY",
        "systemd://",
        "secret://",
        "secret://secret-service",
        "secret://secret-service/../api_key",
        "secret://secret-service/hermes//api_key",
    ],
)
def test_malformed_refs_fail_closed(raw):
    with pytest.raises(SecretRefError):
        SecretRef.parse(raw)


def test_secret_ref_json_serialization_is_locator_only():
    ref = SecretRef.parse("secret://secret-service/hermes/openrouter/api_key")

    encoded = json.dumps(ref.to_public_dict(), sort_keys=True)

    assert "secret-service" in encoded
    assert "openrouter" in encoded
    assert "api_key" in encoded
    assert "sk-" not in encoded
    assert "access_token" not in encoded


def test_secret_ref_errors_do_not_echo_raw_secret_like_input():
    sentinel = "S3NTINEL_DO_NOT_PERSIST_ref_parse_error"

    with pytest.raises(SecretRefError) as excinfo:
        SecretRef.parse(sentinel)
    assert sentinel not in str(excinfo.value)

    with pytest.raises(SecretRefError) as excinfo:
        SecretRef.parse(f"env:BAD VALUE {sentinel}")
    assert sentinel not in str(excinfo.value)


@pytest.mark.parametrize(
    "suffix",
    [
        "?access_token={sentinel}",
        "?key={sentinel}",
        "?jwt={sentinel}",
        "?signature={sentinel}",
        "?label={sentinel}",
        "?{sentinel}=primary",
    ],
)
def test_secret_ref_rejects_secret_like_query_metadata_without_leaking_value(suffix):
    sentinel = "S3NTINEL_DO_NOT_PERSIST_query_value"

    with pytest.raises(SecretRefError) as excinfo:
        SecretRef.parse(
            "secret://secret-service/hermes/openrouter/api_key"
            + suffix.format(sentinel=sentinel)
        )

    assert sentinel not in str(excinfo.value)


def test_secret_ref_repr_is_display_safe():
    ref = SecretRef.parse("secret://secret-service/hermes/openrouter/api_key?label=primary")

    rendered = repr(ref)

    assert "original=" not in rendered
    assert "_query_items" not in rendered
    assert "secret://secret-service/hermes/openrouter/api_key?label=primary" in rendered
