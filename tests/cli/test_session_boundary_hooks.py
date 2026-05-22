from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from hermes_cli.plugins import VALID_HOOKS, PluginManager
from cli import HermesCLI


def test_session_hooks_in_valid_hooks():
    """Verify on_session_finalize and on_session_reset are registered as valid hooks."""
    assert "on_session_finalize" in VALID_HOOKS
    assert "on_session_reset" in VALID_HOOKS


@patch("hermes_cli.plugins.invoke_hook")
def test_session_finalize_on_reset(mock_invoke_hook):
    """Verify on_session_finalize fires when /new or /reset is used."""
    cli = HermesCLI()
    cli.agent = MagicMock()
    cli.agent.session_id = "test-session-id"

    # Simulate /new command which triggers on_session_finalize for the old session
    cli.new_session(silent=True)

    # Check if on_session_finalize was called for the old session
    assert any(
        c.args == ("on_session_finalize",)
        and c.kwargs["session_id"] == "test-session-id"
        and c.kwargs["platform"] == "cli"
        for c in mock_invoke_hook.call_args_list
    )
    # Check if on_session_reset was called for the new session
    assert any(
        c.args == ("on_session_reset",)
        and c.kwargs["session_id"] == cli.session_id
        and c.kwargs["platform"] == "cli"
        for c in mock_invoke_hook.call_args_list
    )


@patch("hermes_cli.plugins.invoke_hook")
def test_session_finalize_on_cleanup(mock_invoke_hook):
    """Verify on_session_finalize fires during CLI exit cleanup."""
    import cli as cli_mod

    mock_agent = MagicMock()
    mock_agent.session_id = "cleanup-session-id"
    cli_mod._active_agent_ref = mock_agent
    cli_mod._cleanup_done = False

    cli_mod._run_cleanup()

    assert any(
        c.args == ("on_session_finalize",)
        and c.kwargs["session_id"] == "cleanup-session-id"
        and c.kwargs["platform"] == "cli"
        and c.kwargs["reason"] == "shutdown"
        for c in mock_invoke_hook.call_args_list
    )


@patch("hermes_cli.plugins.invoke_hook")
def test_interrupted_session_end_helper_emits_observer_shape(mock_invoke_hook):
    """Verify quiet single-query interruption emits a correlated session end."""
    import cli as cli_mod

    mock_agent = MagicMock()
    mock_agent.session_id = "agent-session-id"
    mock_agent.model = "test-model"
    mock_agent.platform = "cli"
    mock_agent._current_task_id = "task-1"
    mock_agent._current_turn_id = "turn-1"
    mock_agent._current_api_request_id = "api-1"
    cli = SimpleNamespace(agent=mock_agent, session_id="cli-session-id")

    cli_mod._emit_interrupted_session_end(cli, reason="keyboard_interrupt")

    mock_agent.interrupt.assert_called_once_with("keyboard interrupt")
    assert cli.session_id == "agent-session-id"
    mock_invoke_hook.assert_called_once()
    call = mock_invoke_hook.call_args
    assert call.args == ("on_session_end",)
    assert call.kwargs["session_id"] == "agent-session-id"
    assert call.kwargs["task_id"] == "task-1"
    assert call.kwargs["turn_id"] == "turn-1"
    assert call.kwargs["api_request_id"] == "api-1"
    assert call.kwargs["completed"] is False
    assert call.kwargs["interrupted"] is True
    assert call.kwargs["reason"] == "keyboard_interrupt"


@patch("hermes_cli.plugins.invoke_hook")
def test_hook_errors_are_caught(mock_invoke_hook):
    """Verify hook exceptions are caught and don't crash the agent."""
    mgr = PluginManager()

    # Register a hook that raises
    def bad_callback(**kwargs):
        raise Exception("Hook failed")

    mgr._hooks["on_session_finalize"] = [bad_callback]

    # This should not raise
    results = mgr.invoke_hook("on_session_finalize", session_id="test", platform="cli")
    assert results == []


# ── on_session_title hook tests ────────────────────────────────────────────


def test_on_session_title_in_valid_hooks():
    """Verify on_session_title is registered as a valid hook."""
    assert "on_session_title" in VALID_HOOKS


@patch("hermes_cli.plugins.invoke_hook")
def test_title_hook_fires_on_new_session_with_title(mock_invoke_hook):
    """Verify on_session_title fires when a new session is created with a title."""
    cli = HermesCLI()
    cli.agent = MagicMock()
    cli.agent.session_id = "test-session-id"
    cli._session_db = MagicMock()
    cli._session_db.sanitize_title = lambda t: t
    cli._session_db.get_session.return_value = None  # simulate DB empty

    # Simulate /new with a title
    cli.new_session(title="My Test Session", silent=True)

    mock_invoke_hook.assert_any_call(
        "on_session_title", title="My Test Session", session_id=cli.session_id,
    )


@patch("hermes_cli.plugins.invoke_hook")
def test_title_hook_fires_on_explicit_title_command(mock_invoke_hook):
    """Verify _fire_title_hook fires on_session_title."""
    cli = HermesCLI()
    cli.session_id = "test-session-id"

    cli._fire_title_hook("Manual Title")

    mock_invoke_hook.assert_any_call(
        "on_session_title", title="Manual Title", session_id="test-session-id",
    )


@patch("hermes_cli.plugins.invoke_hook")
def test_title_hook_fires_for_default_hermes_on_fresh(mock_invoke_hook):
    """Verify the default 'Hermes' title fires on_session_title in run()."""
    cli = HermesCLI()
    cli._resumed = False
    cli.session_id = "fresh-session"

    # Direct call as the run() startup path does
    cli._fire_title_hook("Hermes")

    mock_invoke_hook.assert_any_call(
        "on_session_title", title="Hermes", session_id="fresh-session",
    )


@patch("hermes_cli.plugins.invoke_hook")
def test_title_hook_fires_on_resume_with_title(mock_invoke_hook):
    """Verify on_session_title fires when resuming a session that has a title."""
    cli = HermesCLI()
    cli._resumed = True
    cli.session_id = "resume-session-id"

    # Build a minimal mock for _preload_resumed_session's title path
    cli._session_db = MagicMock()
    cli._session_db.resolve_resume_session_id.return_value = "resume-session-id"
    session_meta = {"title": "Previous Chat", "id": "resume-session-id"}
    cli._session_db.get_session.return_value = session_meta
    cli._session_db.get_messages_as_conversation.return_value = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    # Disable console output during test
    cli._console_print = MagicMock()
    cli._display_resumed_history = MagicMock()

    # Simulate resume flow — this calls _fire_title_hook inside
    cli._preload_resumed_session()

    mock_invoke_hook.assert_any_call(
        "on_session_title", title="Previous Chat", session_id="resume-session-id",
    )


@patch("hermes_cli.plugins.invoke_hook")
def test_title_hook_fires_on_branch_with_title(mock_invoke_hook):
    """Verify on_session_title fires when branching with a custom title."""
    cli = HermesCLI()
    cli.session_id = "original-session"
    cli._session_db = MagicMock()
    cli._session_db.sanitize_title = lambda t: t

    # Simulate the branch title path: set_session_title + hook
    new_id = "branch-new-id"
    cli._session_db.set_session_title(new_id, "Branch Work")
    cli._fire_title_hook("Branch Work")

    # Verify set_session_title was called
    cli._session_db.set_session_title.assert_called_with(new_id, "Branch Work")
    # Verify the hook fired
    mock_invoke_hook.assert_any_call(
        "on_session_title", title="Branch Work", session_id=cli.session_id,
    )
