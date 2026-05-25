import json
import time

from run_agent import AIAgent
from tools import file_state


def _agent():
    agent = object.__new__(AIAgent)
    agent.valid_tool_names = {"verify_task"}
    agent._auto_verify_enabled = True
    agent._auto_verify_max_tool_results_chars = 6000
    agent._last_auto_verification_result = None
    agent._auto_verify_in_progress = False
    return agent


def test_auto_verify_payload_skips_without_explicit_request(monkeypatch, tmp_path):
    """changed_files alone should NOT trigger — only explicit user verify request."""
    monkeypatch.delenv("HERMES_DISABLE_FILE_STATE_GUARD", raising=False)
    file_state.get_registry().clear()
    agent = _agent()
    task_id = "auto-verify-task"
    changed = tmp_path / "example.py"
    changed.write_text("print('ok')\n", encoding="utf-8")
    start = time.time() - 1
    file_state.note_write(task_id, str(changed))

    payload = agent._auto_verify_payload(
        original_user_message="Fix the bug",
        final_response="Implemented the fix.",
        messages=[{"role": "user", "content": "Fix the bug"}],
        current_turn_user_idx=0,
        effective_task_id=task_id,
        turn_start_ts=start,
    )

    assert payload is None


def test_auto_verify_payload_triggers_on_explicit_request(monkeypatch, tmp_path):
    """Only explicit user verification request should trigger verify_task."""
    monkeypatch.delenv("HERMES_DISABLE_FILE_STATE_GUARD", raising=False)
    file_state.get_registry().clear()
    agent = _agent()
    task_id = "auto-verify-task"
    changed = tmp_path / "example.py"
    changed.write_text("print('ok')\n", encoding="utf-8")
    start = time.time() - 1
    file_state.note_write(task_id, str(changed))

    payload = agent._auto_verify_payload(
        original_user_message="Verify the fix",
        final_response="Implemented the fix.",
        messages=[{"role": "user", "content": "Verify the fix"}],
        current_turn_user_idx=0,
        effective_task_id=task_id,
        turn_start_ts=start,
    )

    assert payload is not None
    assert payload["verification_scope"] == "code"
    assert payload["changed_files"] == [str(changed)]
    assert "Changed files satisfy" in "\n".join(payload["claims_to_verify"])


def test_auto_verify_payload_skips_when_verify_task_already_called():
    agent = _agent()
    messages = [
        {"role": "user", "content": "verify this"},
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_1",
                    "function": {"name": "verify_task", "arguments": "{}"},
                }
            ],
        },
    ]

    payload = agent._auto_verify_payload(
        original_user_message="verify this",
        final_response="Verified.",
        messages=messages,
        current_turn_user_idx=0,
        effective_task_id="task",
        turn_start_ts=time.time(),
    )

    assert payload is None


def test_auto_verify_gate_pass_leaves_response_unchanged():
    agent = _agent()
    messages = [
        {"role": "user", "content": "verify this"},
        {"role": "assistant", "content": "The result is verified."},
    ]

    def fake_dispatch(payload):
        return json.dumps({"verdict": "PASS", "verified": True, "results": []})

    agent._dispatch_verify_task = fake_dispatch

    final = agent._apply_auto_verification_gate(
        original_user_message="verify this",
        final_response="The result is verified.",
        messages=messages,
        current_turn_user_idx=0,
        effective_task_id="task",
        turn_start_ts=time.time(),
    )

    assert final == "The result is verified."
    assert agent._last_auto_verification_result["verdict"] == "PASS"


def test_auto_verify_gate_failure_blocks_clean_success_claim():
    agent = _agent()
    messages = [
        {"role": "user", "content": "verify this"},
        {"role": "assistant", "content": "The result is verified."},
    ]

    def fake_dispatch(payload):
        return json.dumps(
            {
                "verdict": "FAIL",
                "verified": False,
                "results": [
                    {
                        "summary": "### Check: evidence\nResult: FAIL\nEvidence: missing\n\nVERDICT: FAIL",
                        "verification": {"failed_checks": ["evidence"]},
                    }
                ],
            }
        )

    agent._dispatch_verify_task = fake_dispatch

    final = agent._apply_auto_verification_gate(
        original_user_message="verify this",
        final_response="The result is verified.",
        messages=messages,
        current_turn_user_idx=0,
        effective_task_id="task",
        turn_start_ts=time.time(),
    )

    assert "Verification did not pass." in final
    assert "Verdict: FAIL" in final
    assert messages[-1]["content"] == final
