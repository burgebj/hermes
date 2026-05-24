"""Tests for the order of post_llm_call hook execution and session persistence.

Validates that:
  1. post_llm_call hook runs BEFORE session persistence (_persist_session).
  2. Plugin response overrides returned via post_llm_call are applied to both
     final_response and the last assistant message in the conversation history
     before the session is persisted.
"""

from unittest.mock import MagicMock, call
import pytest

from agent.conversation_loop import run_conversation


def test_post_llm_call_runs_before_persist_and_can_override_response(monkeypatch):
    """Test that post_llm_call runs before _persist_session and overrides response."""
    # Track order of operations
    call_order = []

    # Mock the plugin manager's invoke_hook
    def mock_invoke_hook(hook_name, **kwargs):
        call_order.append(("invoke_hook", hook_name))
        if hook_name == "post_llm_call":
            return [{"override_response": "Plugin Override Response"}]
        return []

    monkeypatch.setattr("hermes_cli.plugins.invoke_hook", mock_invoke_hook)

    # Setup a minimal mock agent
    agent = MagicMock()
    agent.session_id = "test-session-id"
    agent.model = "test-model"
    agent.provider = "test-provider"
    agent.platform = "cli"
    agent.api_mode = "chat_completions"
    agent.max_iterations = 5
    agent.quiet_mode = True
    agent.compression_enabled = False
    agent.valid_tool_names = []
    agent._cached_system_prompt = "System Prompt"
    agent._user_turn_count = 0
    agent._turns_since_memory = 0
    agent._iters_since_skill = 0
    agent._memory_nudge_interval = 0
    agent._skill_nudge_interval = 0
    agent._has_content_after_think_block = lambda val: True
    agent._strip_think_blocks = lambda val: val
    agent._file_mutation_verifier_enabled.return_value = False
    agent._interrupt_requested = False
    agent._budget_grace_call = False
    agent._tool_guardrail_halt_decision = None
    agent._response_was_previewed = False
    agent._interrupt_message = None
    agent._sanitize_tool_call_arguments = lambda *a, **kw: 0
    agent._repair_message_sequence = lambda *a, **kw: 0
    agent._has_stream_consumers = lambda: False
    agent._sanitize_api_messages = lambda x: x
    agent._drop_thinking_only_and_merge_users = lambda x: x
    agent._should_sanitize_tool_calls = lambda: False
    agent._use_prompt_caching = False
    agent._cleanup_dead_connections = lambda: False
    agent._session_db = None
    agent._memory_manager = None
    agent._memory_store = None
    agent._todo_store.has_items.return_value = True
    agent._api_max_retries = 3
    agent.tools = []
    agent.max_tokens = 4096
    agent._ephemeral_max_output_tokens = None
    agent._should_treat_stop_as_truncated = lambda *a, **kw: False
    agent._delegate_depth = 0

    # Mock client and API calls
    mock_response = MagicMock()
    mock_response.usage = None
    
    # We mock _interruptible_api_call so it returns the response on first iteration
    def mock_api_call(*args, **kwargs):
        return mock_response

    agent._interruptible_api_call = mock_api_call

    # Mock the transport returned by agent._get_transport()
    mock_transport = MagicMock()
    mock_assistant_message = MagicMock()
    mock_assistant_message.content = "Original Assistant Response"
    mock_assistant_message.tool_calls = None
    mock_assistant_message.role = "assistant"
    mock_assistant_message.finish_reason = "stop"
    mock_transport.normalize_response.return_value = mock_assistant_message
    mock_transport.validate_response.return_value = True
    agent._get_transport.return_value = mock_transport

    def mock_build_assistant_message(msg, finish_reason):
        return {"role": "assistant", "content": getattr(msg, "content", "")}
    agent._build_assistant_message = mock_build_assistant_message

    # Mock persistence & scaffolding methods
    persisted_messages = []
    def mock_persist_session(messages, history):
        call_order.append(("persist_session",))
        # Capture a copy of the messages at persistence time
        persisted_messages.extend([dict(m) for m in messages])

    agent._persist_session = mock_persist_session
    agent._drop_trailing_empty_response_scaffolding = MagicMock()
    agent._cleanup_task_resources = MagicMock()
    agent._save_trajectory = MagicMock()
    agent._ensure_db_session = MagicMock()
    agent._restore_primary_runtime = MagicMock()

    # Run conversation turn
    result = run_conversation(
        agent=agent,
        user_message="User message",
        conversation_history=[],
    )

    # Check results
    assert result["final_response"] == "Plugin Override Response"
    
    # Verify call order: invoke_hook('post_llm_call') must run before persist_session
    post_llm_call_index = call_order.index(("invoke_hook", "post_llm_call"))
    persist_session_index = call_order.index(("persist_session",))
    assert post_llm_call_index < persist_session_index

    # Verify that the persisted messages include the overridden content
    assert len(persisted_messages) == 2
    assert persisted_messages[0] == {"role": "user", "content": "User message"}
    assert persisted_messages[1] == {"role": "assistant", "content": "Plugin Override Response"}
