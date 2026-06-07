from gateway.action_journal import ActionJournal, format_recovery_context


def test_recovery_context_reports_unfinished_tool(tmp_path):
    journal = ActionJournal(tmp_path / "action_journal.jsonl")

    journal.record_turn_started(
        session_id="sess-1",
        session_key="key-1",
        platform="slack",
        chat_id="C123",
        thread_id="T456",
        user_text="lets do that",
    )
    journal.record_tool_started(
        session_id="sess-1",
        session_key="key-1",
        tool_call_id="call-1",
        tool_name="terminal",
        args={"command": "hermes update"},
    )

    note = format_recovery_context(
        session_id="sess-1",
        session_key="key-1",
        journal=journal,
    )

    assert "Last user text preview: lets do that" in note
    assert "terminal started" in note
    assert "still unresolved" in note
    assert "do not claim nothing was in progress" in note


def test_recovery_context_reports_completed_and_finished_turn(tmp_path):
    journal = ActionJournal(tmp_path / "action_journal.jsonl")

    journal.record_turn_started(
        session_id="sess-2",
        session_key="key-2",
        user_text="check status",
    )
    journal.record_tool_started(
        session_id="sess-2",
        session_key="key-2",
        tool_call_id="call-2",
        tool_name="terminal",
        args={"command": "git status"},
    )
    journal.record_tool_finished(
        session_id="sess-2",
        session_key="key-2",
        tool_call_id="call-2",
        tool_name="terminal",
        status="completed",
        result="clean",
    )
    journal.record_turn_finished(
        session_id="sess-2",
        session_key="key-2",
        status="completed",
    )

    note = format_recovery_context(
        session_id="sess-2",
        session_key="key-2",
        journal=journal,
    )

    assert "terminal=completed" in note
    assert "recorded a finish" in note
    assert "still unresolved" not in note


def test_action_journal_redacts_secret_values(tmp_path):
    journal = ActionJournal(tmp_path / "action_journal.jsonl")

    secret = "super-secret-value"
    journal.record_turn_started(
        session_id="sess-3",
        session_key="key-3",
        user_text={"api_key": secret},
    )

    text = (tmp_path / "action_journal.jsonl").read_text()
    assert secret not in text
    assert "***" in text or "[REDACTED" in text
