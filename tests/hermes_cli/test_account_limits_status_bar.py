from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from agent.account_usage import AccountUsageSnapshot, AccountUsageWindow
from cli import HermesCLI


def _snapshot(provider: str = "openai-codex") -> AccountUsageSnapshot:
    return AccountUsageSnapshot(
        provider=provider,
        source="test",
        fetched_at=datetime.now(timezone.utc),
        windows=(
            AccountUsageWindow(label="Session", used_percent=14.4),
            AccountUsageWindow(label="Weekly", used_percent=2.1),
        ),
    )


def test_format_account_limits_badge_uses_remaining_percentages() -> None:
    assert HermesCLI._format_account_limits_badge(_snapshot()) == "Acct S86% W98%"


def test_account_limits_badge_style_turns_critical_for_depleted_session_or_weekly() -> None:
    assert HermesCLI._account_limits_badge_style("Acct S0% W98%") == "class:status-bar-critical"
    assert HermesCLI._account_limits_badge_style("Acct S86% W0%") == "class:status-bar-critical"
    assert HermesCLI._account_limits_badge_style("Acct S86% W98%") == "class:status-bar-good"


def test_format_account_limits_badge_falls_back_for_generic_provider() -> None:
    assert HermesCLI._format_account_limits_badge(_snapshot("anthropic")) == "Acct S86% W98%"


def test_format_account_limits_badge_ignores_missing_usage() -> None:
    snapshot = AccountUsageSnapshot(
        provider="openai-codex",
        source="test",
        fetched_at=datetime.now(timezone.utc),
        windows=(AccountUsageWindow(label="Session", used_percent=None),),
    )

    assert HermesCLI._format_account_limits_badge(snapshot) == ""


def test_status_bar_text_includes_cached_account_limits(monkeypatch) -> None:
    shell = HermesCLI.__new__(HermesCLI)
    shell.model = "openai-codex/gpt-5.1-codex"
    shell.session_start = datetime.now()
    shell._prompt_start_time = None
    shell._prompt_duration = 0.0
    shell._background_tasks = {}
    shell.agent = SimpleNamespace(
        model="openai-codex/gpt-5.1-codex",
        session_input_tokens=0,
        session_output_tokens=0,
        session_cache_read_tokens=0,
        session_cache_write_tokens=0,
        session_prompt_tokens=0,
        session_completion_tokens=0,
        session_total_tokens=0,
        session_api_calls=0,
        context_compressor=None,
    )
    monkeypatch.setattr(shell, "_maybe_refresh_account_limits_badge", lambda agent: "Acct S86% W98%")

    text = shell._build_status_bar_text(width=100)

    assert "Acct S86% W98%" in text


def test_status_bar_fragments_render_depleted_account_limits_as_critical(monkeypatch) -> None:
    shell = HermesCLI.__new__(HermesCLI)
    shell._status_bar_visible = True
    shell._model_picker_state = None
    monkeypatch.setattr(shell, "_get_tui_terminal_width", lambda: 100)
    monkeypatch.setattr(
        shell,
        "_get_status_bar_snapshot",
        lambda: {
            "model_short": "gpt-5.5-codex",
            "context_percent": 12,
            "context_length": 200_000,
            "context_tokens": 24_000,
            "account_limits": "Acct S0% W42%",
            "account_limits_style": "class:status-bar-critical",
            "compressions": 0,
            "active_background_tasks": 0,
            "duration": "1m",
            "prompt_elapsed": "⏲ 0s",
        },
    )

    frags = shell._get_status_bar_fragments()

    assert ("class:status-bar-critical", "Acct S0% W42%") in frags


def test_status_bar_snapshot_derives_depleted_account_style_from_current_label(monkeypatch) -> None:
    shell = HermesCLI.__new__(HermesCLI)
    shell.model = "openai-codex/gpt-5.5-codex"
    shell.session_start = datetime.now()
    shell._prompt_start_time = None
    shell._prompt_duration = 0.0
    shell._background_tasks = {}
    shell._account_limits_style = "class:status-bar-good"
    shell.agent = SimpleNamespace(
        model="openai-codex/gpt-5.5-codex",
        session_input_tokens=0,
        session_output_tokens=0,
        session_cache_read_tokens=0,
        session_cache_write_tokens=0,
        session_prompt_tokens=0,
        session_completion_tokens=0,
        session_total_tokens=0,
        session_api_calls=0,
        context_compressor=None,
    )
    monkeypatch.setattr(shell, "_maybe_refresh_account_limits_badge", lambda agent: "Acct S0% W42%")

    snapshot = shell._get_status_bar_snapshot()

    assert snapshot["account_limits"] == "Acct S0% W42%"
    assert snapshot["account_limits_style"] == "class:status-bar-critical"


def test_status_bar_overflow_preserves_depleted_account_critical_style(monkeypatch) -> None:
    shell = HermesCLI.__new__(HermesCLI)
    shell._status_bar_visible = True
    shell._model_picker_state = None
    monkeypatch.setattr(shell, "_get_tui_terminal_width", lambda: 76)
    monkeypatch.setattr(
        shell,
        "_get_status_bar_snapshot",
        lambda: {
            "model_short": "gpt-5.5-codex",
            "context_percent": 12,
            "context_length": 200_000,
            "context_tokens": 24_000,
            "account_limits": "Acct S0% W42%",
            "account_limits_style": "class:status-bar-critical",
            "compressions": 0,
            "active_background_tasks": 0,
            "duration": "123m",
            "prompt_elapsed": "⏲ 99s",
        },
    )

    frags = shell._get_status_bar_fragments()

    assert len(frags) == 1
    assert frags[0][0] == "class:status-bar-critical"
    assert "Acct S0%" in frags[0][1]
