"""Tests for LCM deterministic truncation (Level 3)."""
from unittest.mock import patch, MagicMock
from plugins.context_engine.lcm.escalation import deterministic_truncate, first_sentence, escalated_summary

class TestFirstSentence:
    def test_period_boundary(self):
        assert first_sentence("Hello world. This is more.") == "Hello world."

    def test_question_mark(self):
        assert first_sentence("What is Rust? It's a language.") == "What is Rust?"

    def test_exclamation(self):
        assert first_sentence("Great job! Keep going.") == "Great job!"

    def test_no_boundary(self):
        assert first_sentence("Just a fragment") == "Just a fragment"

    def test_empty(self):
        assert first_sentence("") == ""

    def test_multiple_sentences(self):
        result = first_sentence("First. Second. Third.")
        assert result == "First."

    def test_preserves_whitespace_after_boundary(self):
        # Should NOT include trailing whitespace
        result = first_sentence("Hello.   More text.")
        assert result == "Hello."


class TestDeterministicTruncate:
    def test_respects_token_budget(self):
        messages = [
            {"role": "user", "content": "Tell me about Python async patterns and how they work with asyncio library in detail"},
            {"role": "assistant", "content": "Python async uses coroutines with the async/await syntax. The asyncio library provides the event loop."},
            {"role": "user", "content": "What about error handling in async code? How do you catch exceptions?"},
            {"role": "assistant", "content": "You can use try/except blocks within async functions. Gather exceptions can be handled with return_exceptions=True."},
        ]
        result = deterministic_truncate(messages, target_tokens=50)
        # Rough estimate: 50 tokens ≈ 200 chars
        assert len(result) <= 250  # generous char budget

    def test_extracts_from_user_messages(self):
        messages = [
            {"role": "user", "content": "How does garbage collection work in Python? I want details."},
            {"role": "assistant", "content": "Python uses reference counting as its primary mechanism. When references reach zero, memory is freed immediately."},
        ]
        result = deterministic_truncate(messages, target_tokens=100)
        assert "garbage collection" in result.lower() or "python" in result.lower()

    def test_handles_empty_messages(self):
        result = deterministic_truncate([], target_tokens=100)
        assert result == ""

    def test_handles_tool_messages(self):
        messages = [
            {"role": "user", "content": "Read the file."},
            {"role": "tool", "content": '{"file": "main.py", "content": "def hello(): print(\'world\')"}'},
            {"role": "assistant", "content": "The file contains a hello function."},
        ]
        result = deterministic_truncate(messages, target_tokens=100)
        assert len(result) > 0

    def test_very_small_budget(self):
        messages = [
            {"role": "user", "content": "This is a very long message about many topics including databases and APIs."},
            {"role": "assistant", "content": "Here is a detailed response covering all those topics in great depth."},
        ]
        result = deterministic_truncate(messages, target_tokens=10)
        # Should still produce something, just very truncated
        assert len(result) <= 60  # ~10 tokens * ~6 chars

    def test_preserves_message_attribution(self):
        messages = [
            {"role": "user", "content": "Question about Rust."},
            {"role": "assistant", "content": "Rust is a systems language. It focuses on safety."},
        ]
        result = deterministic_truncate(messages, target_tokens=100)
        # Should have role attribution
        assert "user:" in result.lower() or "assistant:" in result.lower()


class TestEscalatedSummary:
    def test_level1_success(self):
        """When LLM returns a good summary shorter than input, use it."""
        messages = [
            {"role": "user", "content": "Tell me about Python " + "x" * 200},
            {"role": "assistant", "content": "Python is great " + "y" * 200},
        ]
        with patch("plugins.context_engine.lcm.escalation._call_summary_llm") as mock_llm:
            mock_llm.return_value = "User asked about Python. Assistant explained it."
            text, level = escalated_summary(messages, target_tokens=100, deterministic_target=50)
            assert level == 1
            assert "Python" in text
            mock_llm.assert_called_once()

    def test_level1_refusal_falls_to_level2(self):
        """If LLM refuses at Level 1, try Level 2."""
        messages = [
            {"role": "user", "content": "Some content " + "x" * 200},
            {"role": "assistant", "content": "Response " + "y" * 200},
        ]
        with patch("plugins.context_engine.lcm.escalation._call_summary_llm") as mock_llm:
            mock_llm.side_effect = [
                "I'm sorry, I cannot summarize that content.",  # L1 refusal
                "- User asked about something\n- Assistant responded",  # L2 success
            ]
            text, level = escalated_summary(messages, target_tokens=100, deterministic_target=50)
            assert level == 2
            assert mock_llm.call_count == 2

    def test_level2_failure_falls_to_level3(self):
        """If both LLM levels fail, use deterministic truncation."""
        messages = [
            {"role": "user", "content": "Content " + "x" * 200},
            {"role": "assistant", "content": "Reply " + "y" * 200},
        ]
        with patch("plugins.context_engine.lcm.escalation._call_summary_llm") as mock_llm:
            mock_llm.side_effect = [
                "I cannot help with that.",  # L1 refusal
                "I'm unable to summarize.",  # L2 refusal
            ]
            text, level = escalated_summary(messages, target_tokens=100, deterministic_target=50)
            assert level == 3
            assert len(text) > 0  # deterministic always produces output

    def test_llm_exception_falls_through(self):
        """If LLM call returns None (signals failure), fall through to Level 3."""
        messages = [
            {"role": "user", "content": "Content " + "x" * 200},
            {"role": "assistant", "content": "Reply " + "y" * 200},
        ]
        with patch("plugins.context_engine.lcm.escalation._call_summary_llm") as mock_llm:
            # _call_summary_llm catches exceptions internally and returns None.
            # Returning None from both L1 and L2 should trigger L3 fallback.
            mock_llm.return_value = None
            text, level = escalated_summary(messages, target_tokens=100, deterministic_target=50)
            assert level == 3  # fell all the way to deterministic

    def test_summary_larger_than_input_rejected(self):
        """If LLM summary is larger than the original, reject and try next level."""
        messages = [{"role": "user", "content": "Short."}]
        with patch("plugins.context_engine.lcm.escalation._call_summary_llm") as mock_llm:
            mock_llm.side_effect = [
                "This is a much longer summary than the original " * 10,  # L1 too long
                "- Short message",  # L2 OK
            ]
            text, level = escalated_summary(messages, target_tokens=100, deterministic_target=50)
            assert level == 2

    def test_vacuous_summary_rejected(self):
        """If L1 summary is < 5% of input tokens, reject as vacuous and fall to L2."""
        messages = [
            {"role": "user", "content": "x " * 500},
            {"role": "assistant", "content": "y " * 500},
        ]
        # Input: ~1000 tokens. L1 floor = 50 tokens, L2 floor = 30 tokens.
        # L2 response must be >= 30 tokens (~120 chars) to pass the 3% vacuous check.
        l2_response = "- User sent a long message with repeated content\n- Assistant responded with repeated content\n- Exchange was uneventful"
        with patch("plugins.context_engine.lcm.escalation._call_summary_llm") as mock_llm:
            mock_llm.side_effect = [
                "Ok.",       # L1 vacuous (< 5% of ~1000 tokens)
                l2_response, # L2 OK (> 3% of ~1000 tokens)
            ]
            text, level = escalated_summary(messages, target_tokens=200, deterministic_target=50)
            assert level == 2

    def test_level2_vacuous_falls_to_level3(self):
        """If L2 summary is also vacuous (< 3% of input), fall through to L3 deterministic."""
        messages = [
            {"role": "user", "content": "x " * 500},
            {"role": "assistant", "content": "y " * 500},
        ]
        with patch("plugins.context_engine.lcm.escalation._call_summary_llm") as mock_llm:
            mock_llm.side_effect = [
                "Ok.",  # L1 vacuous (< 5% of ~250 tokens)
                ".",    # L2 vacuous (< 3% of ~250 tokens)
            ]
            text, level = escalated_summary(messages, target_tokens=200, deterministic_target=50)
            assert level == 3
            assert len(text) > 0  # deterministic always produces output
