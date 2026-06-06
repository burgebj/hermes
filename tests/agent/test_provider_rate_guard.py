"""Tests for agent/provider_rate_guard.py -- provider-agnostic cross-session rate limit guard."""

import json
import os
import time

import pytest


@pytest.fixture
def rate_guard_env(tmp_path, monkeypatch):
    """Isolate rate guard state to a temp directory."""
    hermes_home = str(tmp_path / ".hermes")
    os.makedirs(hermes_home, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", hermes_home)
    return hermes_home


class TestShouldGuard:
    """Unit tests for should_guard()."""

    def test_nous_provider_returns_nous(self):
        from agent.provider_rate_guard import should_guard

        assert should_guard("nous") == "nous"

    def test_openai_provider_returns_openai(self):
        from agent.provider_rate_guard import should_guard

        assert should_guard("openai") == "openai"

    def test_custom_openai_dot_com_returns_openai(self):
        from agent.provider_rate_guard import should_guard

        assert should_guard("custom", base_url="https://api.openai.com/v1") == "openai"

    def test_custom_non_openai_returns_none(self):
        from agent.provider_rate_guard import should_guard

        assert should_guard("custom", base_url="https://api.example.com/v1") is None

    def test_anthropic_returns_none(self):
        from agent.provider_rate_guard import should_guard

        assert should_guard("anthropic") is None

    def test_openrouter_returns_none(self):
        from agent.provider_rate_guard import should_guard

        assert should_guard("openrouter") is None

    def test_empty_provider_returns_none(self):
        from agent.provider_rate_guard import should_guard

        assert should_guard("") is None


class TestRecordRateLimit:
    """Test recording rate limit state."""

    def test_records_with_header_reset(self, rate_guard_env):
        from agent.provider_rate_guard import record_rate_limit, _state_path

        headers = {"x-ratelimit-reset-requests-1h": "1800"}
        record_rate_limit("openai", headers=headers)

        path = _state_path("openai")
        assert os.path.exists(path)
        with open(path) as f:
            state = json.load(f)
        assert state["reset_seconds"] == pytest.approx(1800, abs=2)
        assert state["reset_at"] > time.time()

    def test_records_with_retry_after(self, rate_guard_env):
        from agent.provider_rate_guard import record_rate_limit, _state_path

        headers = {"retry-after": "60"}
        record_rate_limit("openai", headers=headers)

        with open(_state_path("openai")) as f:
            state = json.load(f)
        assert state["reset_seconds"] == pytest.approx(60, abs=2)

    def test_falls_back_to_default_cooldown(self, rate_guard_env):
        from agent.provider_rate_guard import record_rate_limit, _state_path

        record_rate_limit("openai", headers=None)

        with open(_state_path("openai")) as f:
            state = json.load(f)
        assert state["reset_seconds"] == pytest.approx(300, abs=2)

    def test_creates_directory_if_missing(self, rate_guard_env):
        from agent.provider_rate_guard import record_rate_limit, _state_path

        record_rate_limit("openai", headers={"retry-after": "10"})
        assert os.path.exists(_state_path("openai"))


class TestRateLimitRemaining:
    """Test checking remaining rate limit time."""

    def test_returns_none_when_no_file(self, rate_guard_env):
        from agent.provider_rate_guard import rate_limit_remaining

        assert rate_limit_remaining("openai") is None

    def test_returns_remaining_when_active(self, rate_guard_env):
        from agent.provider_rate_guard import record_rate_limit, rate_limit_remaining

        record_rate_limit("openai", headers={"x-ratelimit-reset-requests-1h": "600"})
        remaining = rate_limit_remaining("openai")
        assert remaining is not None
        assert 595 < remaining <= 605

    def test_returns_none_when_expired(self, rate_guard_env):
        from agent.provider_rate_guard import rate_limit_remaining, _state_path

        state_dir = os.path.dirname(_state_path("openai"))
        os.makedirs(state_dir, exist_ok=True)
        with open(_state_path("openai"), "w") as f:
            json.dump({"reset_at": time.time() - 10, "recorded_at": time.time() - 100}, f)

        assert rate_limit_remaining("openai") is None
        assert not os.path.exists(_state_path("openai"))

    def test_handles_corrupt_file(self, rate_guard_env):
        from agent.provider_rate_guard import rate_limit_remaining, _state_path

        state_dir = os.path.dirname(_state_path("openai"))
        os.makedirs(state_dir, exist_ok=True)
        with open(_state_path("openai"), "w") as f:
            f.write("not valid json{{{")

        assert rate_limit_remaining("openai") is None


class TestClearRateLimit:
    """Test clearing rate limit state."""

    def test_clears_existing(self, rate_guard_env):
        from agent.provider_rate_guard import record_rate_limit, clear_rate_limit, rate_limit_remaining, _state_path

        record_rate_limit("openai", headers={"retry-after": "600"})
        assert rate_limit_remaining("openai") is not None

        clear_rate_limit("openai")
        assert rate_limit_remaining("openai") is None
        assert not os.path.exists(_state_path("openai"))

    def test_clear_when_no_file(self, rate_guard_env):
        from agent.provider_rate_guard import clear_rate_limit

        # Must not raise
        clear_rate_limit("openai")


class TestProviderIsolation:
    """Critical: Nous and OpenAI must not share state."""

    def test_nous_and_openai_are_isolated(self, rate_guard_env):
        from agent.provider_rate_guard import record_rate_limit, rate_limit_remaining

        record_rate_limit("nous", headers={"retry-after": "600"})
        assert rate_limit_remaining("openai") is None

    def test_different_providers_write_different_files(self, rate_guard_env):
        from agent.provider_rate_guard import record_rate_limit, _state_path

        record_rate_limit("nous", headers={"retry-after": "600"})
        record_rate_limit("openai", headers={"retry-after": "300"})

        nous_path = _state_path("nous")
        openai_path = _state_path("openai")

        assert os.path.exists(nous_path)
        assert os.path.exists(openai_path)
        assert nous_path != openai_path

        with open(nous_path) as f:
            nous_state = json.load(f)
        with open(openai_path) as f:
            openai_state = json.load(f)

        # Different cooldowns mean different reset_seconds
        assert nous_state["reset_seconds"] != openai_state["reset_seconds"]


class TestFormatRemaining:
    """Test human-readable duration formatting."""

    def test_seconds(self):
        from agent.provider_rate_guard import format_remaining

        assert format_remaining(30) == "30s"

    def test_minutes(self):
        from agent.provider_rate_guard import format_remaining

        assert format_remaining(125) == "2m 5s"

    def test_exact_minutes(self):
        from agent.provider_rate_guard import format_remaining

        assert format_remaining(120) == "2m"

    def test_hours(self):
        from agent.provider_rate_guard import format_remaining

        assert format_remaining(3720) == "1h 2m"
