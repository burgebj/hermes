"""Tests for _repair_tool_call_arguments — malformed JSON repair pipeline."""

import json

from run_agent import _repair_tool_call_arguments
from agent.message_sanitization import _recover_unescaped_tail_string


class TestRepairToolCallArguments:
    """Verify each repair stage in the pipeline."""

    # -- Stage 1: empty / whitespace-only --

    def test_empty_string_returns_empty_object(self):
        assert _repair_tool_call_arguments("", "t") == "{}"

    def test_whitespace_only_returns_empty_object(self):
        assert _repair_tool_call_arguments("   \n\t  ", "t") == "{}"

    def test_none_type_returns_empty_object(self):
        """Non-string input (e.g. None from a broken model response)."""
        assert _repair_tool_call_arguments(None, "t") == "{}"

    # -- Stage 2: Python None literal --

    def test_python_none_literal(self):
        assert _repair_tool_call_arguments("None", "t") == "{}"

    def test_python_none_with_whitespace(self):
        assert _repair_tool_call_arguments("  None  ", "t") == "{}"

    # -- Stage 3: trailing comma repair --

    def test_trailing_comma_in_object(self):
        result = _repair_tool_call_arguments('{"key": "value",}', "t")
        assert json.loads(result) == {"key": "value"}

    def test_trailing_comma_in_array(self):
        result = _repair_tool_call_arguments('{"a": [1, 2,]}', "t")
        parsed = json.loads(result)
        assert parsed == {"a": [1, 2]}

    def test_multiple_trailing_commas(self):
        result = _repair_tool_call_arguments('{"a": 1, "b": 2,}', "t")
        parsed = json.loads(result)
        assert parsed["a"] == 1
        assert parsed["b"] == 2

    # -- Stage 4: unclosed brackets --

    def test_unclosed_brace(self):
        result = _repair_tool_call_arguments('{"key": "value"', "t")
        parsed = json.loads(result)
        assert parsed == {"key": "value"}

    def test_unclosed_bracket_and_brace(self):
        result = _repair_tool_call_arguments('{"a": [1, 2', "t")
        # Bracket counting adds ']' then '}', producing {"a": [1, 2]}
        # which is valid JSON.  But the naive count can't always recover
        # complex nesting — verify we at least get valid JSON.
        json.loads(result)

    # -- Stage 5: excess closing delimiters --

    def test_extra_closing_brace(self):
        result = _repair_tool_call_arguments('{"key": "value"}}', "t")
        parsed = json.loads(result)
        assert parsed == {"key": "value"}

    def test_extra_closing_bracket(self):
        result = _repair_tool_call_arguments('{"a": [1]]}', "t")
        # Should produce valid JSON
        json.loads(result)

    # -- Stage 6: last resort --

    def test_unrepairable_garbage_returns_empty_object(self):
        assert _repair_tool_call_arguments("totally not json", "t") == "{}"

    def test_unrepairable_partial_returns_empty_object(self):
        # Truncated in the middle of a string key — bracket closing won't help
        assert _repair_tool_call_arguments('{"truncated": "val', "t") == "{}"

    # -- Valid JSON passthrough (this path is via except, but still works) --

    def test_already_valid_json_passes_through(self):
        """When json.loads fails for a non-JSON reason (shouldn't normally
        happen), but the repair pipeline still produces valid output."""
        raw = '{"path": "/tmp/foo", "content": "hello"}'
        result = _repair_tool_call_arguments(raw, "t")
        parsed = json.loads(result)
        assert parsed["path"] == "/tmp/foo"

    # -- Combined repairs --

    def test_trailing_comma_plus_unclosed_brace(self):
        result = _repair_tool_call_arguments('{"a": 1, "b": 2,', "t")
        # Trailing comma stripped first, then closing brace added.
        # May or may not fully recover — verify valid JSON at minimum.
        json.loads(result)

    def test_real_world_glm_truncation(self):
        """Simulates GLM-5.1 truncating mid-argument."""
        raw = '{"command": "ls -la /tmp", "timeout": 30, "background":'
        result = _repair_tool_call_arguments(raw, "terminal")
        # Should at least be valid JSON, even if background is lost
        json.loads(result)

    # -- Stage 0: strict=False (literal control chars in strings) --
    # llama.cpp backends sometimes emit literal tabs/newlines inside JSON
    # string values. strict=False accepts these; we re-serialise to the
    # canonical wire form (#12068).

    def test_literal_newline_inside_string_value(self):
        raw = '{"summary": "line one\nline two"}'
        result = _repair_tool_call_arguments(raw, "t")
        parsed = json.loads(result)
        assert parsed == {"summary": "line one\nline two"}

    def test_literal_tab_inside_string_value(self):
        raw = '{"summary": "col1\tcol2"}'
        result = _repair_tool_call_arguments(raw, "t")
        parsed = json.loads(result)
        assert parsed == {"summary": "col1\tcol2"}

    def test_literal_control_char_reserialised_to_wire_form(self):
        """After repair, the output must parse under strict=True."""
        raw = '{"msg": "has\tliteral\ttabs"}'
        result = _repair_tool_call_arguments(raw, "t")
        # strict=True must now accept this
        parsed = json.loads(result)
        assert parsed["msg"] == "has\tliteral\ttabs"

    # -- Stage 4: control-char escape fallback --

    def test_control_chars_with_trailing_comma(self):
        """strict=False fails due to trailing comma, but brace-count pass
        + control-char escape rescues it."""
        raw = '{"msg": "line\none",}'
        result = _repair_tool_call_arguments(raw, "t")
        parsed = json.loads(result)
        assert "line" in parsed["msg"]


class TestUnescapedTailStringRecovery:
    """Stage 5: schema-aware recovery of unescaped quotes/braces inside a
    known free-text tail field (write_file.content, patch.new_string).

    This is the failure class no structural pass can fix: an unescaped ``"``
    is 0x22, invisible to brace-counting and the control-char escaper.  The
    recovery is whitelisted and self-validating — it must never silently
    substitute a value we aren't certain about.
    """

    # -- the core symptom: Python code with unescaped inner quotes --

    def test_dict_access_with_unescaped_quotes(self):
        """env.get("KEY", "default") — quotes break JSON, content must survive."""
        raw = '{"path": "/tmp/a.py", "content": "env.get("KEY", "default")"}'
        result = _repair_tool_call_arguments(raw, "write_file")
        parsed = json.loads(result)
        assert parsed["path"] == "/tmp/a.py"
        assert parsed["content"] == 'env.get("KEY", "default")'

    def test_fstring_with_braces_and_quotes(self):
        """f"Bearer {token}" — the braces (and the value) must be preserved."""
        raw = '{"path": "/tmp/a.py", "content": "f"Bearer {token}""}'
        result = _repair_tool_call_arguments(raw, "write_file")
        parsed = json.loads(result)
        assert parsed["content"] == 'f"Bearer {token}"'

    def test_mixed_quotes_and_braces(self):
        raw = '{"path": "/tmp/a.py", "content": "d = {1: 2}; x = obj["k"]"}'
        result = _repair_tool_call_arguments(raw, "write_file")
        parsed = json.loads(result)
        assert parsed["content"] == 'd = {1: 2}; x = obj["k"]'

    # -- the trailing-field hazard: greedy split must not over-grab --

    def test_trailing_clean_field_after_content(self):
        """A clean field after the messy content must NOT be swallowed into it."""
        raw = ('{"path": "/tmp/a.py", "content": "env.get("KEY")", '
               '"cross_profile": false}')
        result = _repair_tool_call_arguments(raw, "write_file")
        parsed = json.loads(result)
        assert parsed["content"] == 'env.get("KEY")'
        assert parsed["cross_profile"] is False

    def test_content_first_field(self):
        """Recovery works when the messy field is first in the object."""
        raw = '{"content": "print("hi")", "path": "/tmp/a.py"}'
        result = _repair_tool_call_arguments(raw, "write_file")
        parsed = json.loads(result)
        assert parsed["content"] == 'print("hi")'
        assert parsed["path"] == "/tmp/a.py"

    # -- patch.new_string is also whitelisted --

    def test_patch_new_string_recovery(self):
        raw = ('{"path": "/tmp/a.py", "old_string": "x = 1", '
               '"new_string": "x = env.get("K")"}')
        result = _repair_tool_call_arguments(raw, "patch")
        parsed = json.loads(result)
        assert parsed["new_string"] == 'x = env.get("K")'
        assert parsed["old_string"] == "x = 1"

    # -- SAFETY: must fall back to {} rather than mis-recover --

    def test_non_whitelisted_tool_does_not_recover(self):
        """Same malformation on a tool with no free-text tail field → {}.

        We must not invent a recovery for tools whose args aren't this shape.
        """
        raw = '{"command": "echo "hi""}'
        assert _repair_tool_call_arguments(raw, "terminal") == "{}"

    def test_leading_field_also_broken_falls_back(self):
        """If a NON-tail field is also quote-broken, the reparse can't validate
        and we must fall back to {} rather than guess."""
        raw = '{"path": "/tmp/a".py", "content": "env.get("K")"}'
        assert _repair_tool_call_arguments(raw, "write_file") == "{}"

    def test_unknown_tool_name_falls_back(self):
        raw = '{"content": "env.get("K")"}'
        assert _repair_tool_call_arguments(raw, "?") == "{}"

    # -- regression: well-formed content with braces is untouched --

    def test_valid_braces_pass_through_unchanged(self):
        """Properly-escaped braces are valid JSON and never reach recovery."""
        raw = '{"path": "/tmp/a.py", "content": "f\\"Bearer {token}\\""}'
        result = _repair_tool_call_arguments(raw, "write_file")
        parsed = json.loads(result)
        assert parsed["content"] == 'f"Bearer {token}"'

    # -- direct helper-level checks --

    def test_helper_returns_none_for_unknown_tool(self):
        raw = '{"content": "env.get("K")"}'
        assert _recover_unescaped_tail_string(raw, "terminal") is None

    def test_helper_returns_none_when_field_absent(self):
        raw = '{"path": "/tmp/a.py"}'
        assert _recover_unescaped_tail_string(raw, "write_file") is None

    def test_helper_recovers_canonical_json(self):
        raw = '{"path": "/tmp/a.py", "content": "env.get("K")"}'
        recovered = _recover_unescaped_tail_string(raw, "write_file")
        assert recovered is not None
        assert json.loads(recovered)["content"] == 'env.get("K")'

