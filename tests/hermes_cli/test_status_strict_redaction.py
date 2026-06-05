import os

from hermes_cli import status


def test_redact_key_default_preserves_masked_fragments(monkeypatch):
    monkeypatch.delenv("HERMES_STATUS_STRICT_REDACTION", raising=False)
    masked = status.redact_key("sk-test-abcdefghijklmnopqrstuvwxyz")
    assert "..." in masked
    assert "abcdefghijklmnopqrstuvwxyz" not in masked


def test_redact_key_strict_hides_all_fragments(monkeypatch):
    monkeypatch.setenv("HERMES_STATUS_STRICT_REDACTION", "true")
    secret = "sk-test-abcdefghijklmnopqrstuvwxyz"
    masked = status.redact_key(secret)
    assert "[configured]" in masked
    assert "sk-test" not in masked
    assert "wxyz" not in masked
    assert "..." not in masked


def test_redact_key_strict_keeps_empty_placeholder(monkeypatch):
    monkeypatch.setenv("HERMES_STATUS_STRICT_REDACTION", "true")
    masked = status.redact_key("")
    assert "not set" in masked
