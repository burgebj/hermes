"""Gateway agent loop limit config tests."""

from gateway.run import _resolve_gateway_max_iterations


def test_resolve_gateway_max_iterations_prefers_agent_max_turns_over_env(monkeypatch):
    monkeypatch.setenv("HERMES_MAX_ITERATIONS", "200")

    assert _resolve_gateway_max_iterations({"agent": {"max_turns": 600}}) == 600


def test_resolve_gateway_max_iterations_supports_legacy_top_level_max_turns(monkeypatch):
    monkeypatch.setenv("HERMES_MAX_ITERATIONS", "200")

    assert _resolve_gateway_max_iterations({"max_turns": 600}) == 600


def test_resolve_gateway_max_iterations_supports_legacy_env(monkeypatch):
    monkeypatch.setenv("HERMES_MAX_ITERATIONS", "200")

    assert _resolve_gateway_max_iterations({}) == 200


def test_resolve_gateway_max_iterations_falls_back_when_invalid(monkeypatch):
    monkeypatch.setenv("HERMES_MAX_ITERATIONS", "not-a-number")

    assert _resolve_gateway_max_iterations({"agent": {"max_turns": ""}}) == 90
