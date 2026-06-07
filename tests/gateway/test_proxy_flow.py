"""Tests for gateway relay outbound proxy helpers (WSL / env proxy edge cases)."""

import pytest

from gateway import outbound_proxy


def test_timeout_multiplier_default():
    assert outbound_proxy.gateway_relay_timeout_multiplier() == 1.0


def test_timeout_multiplier_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERMES_PROXY_TIMEOUT_MULTIPLIER", "not-a-float")
    assert outbound_proxy.gateway_relay_timeout_multiplier() == 1.0


def test_timeout_multiplier_non_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERMES_PROXY_TIMEOUT_MULTIPLIER", "0")
    assert outbound_proxy.gateway_relay_timeout_multiplier() == 1.0


def test_sock_read_scaled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERMES_PROXY_TIMEOUT_MULTIPLIER", "2")
    assert outbound_proxy.gateway_relay_sock_read_seconds(100.0) == 200.0


def test_outbound_no_proxy_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERMES_GATEWAY_OUTBOUND_NO_PROXY", "1")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    te, sk, rk = outbound_proxy.relay_client_session_proxy_bundle()
    assert te is False
    assert sk == {}
    assert rk == {}


def test_bundle_with_https_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HERMES_GATEWAY_OUTBOUND_NO_PROXY", raising=False)
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:8888")
    te, sk, rk = outbound_proxy.relay_client_session_proxy_bundle()
    assert te is True
    assert sk == {}
    assert rk == {"proxy": "http://127.0.0.1:8888"}


def test_is_wsl_by_distro(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")
    assert outbound_proxy.is_wsl_environment() is True
