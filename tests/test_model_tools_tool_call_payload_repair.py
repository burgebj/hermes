"""Tests for the structured tool-call argument repair path.

These tests verify that:
- Empty / whitespace / None literal raw args are handled gracefully.
- Malformed JSON gets repaired when possible (trailing commas, missing
  closing braces, etc.).
- Unrepairable args for mutation tools (write_file, patch, execute_code)
  produce a structured result with ``unrepairable_preview`` instead of
  silently collapsing to ``"{}"``.
- Unrepairable args for non-mutation tools continue to return ``"{}"``
  (legacy behaviour).
- The ``repair_tool_call_arguments`` dict contract is respected
  (``repaired_args``, ``unrepairable``, ``unrepairable_preview``,
  ``was_empty`` keys).
"""

import json
import pytest

from agent.message_sanitization import (
    _repair_tool_call_arguments,
    repair_tool_call_arguments,
    _is_mutation_tool,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MUTATION_TOOLS = ("write_file", "patch", "execute_code")
NON_MUTATION_TOOLS = ("read_file", "terminal", "search_files", "skill_view")


@pytest.fixture
def sample_malformed_trailing_comma():
    return '{"path": "/tmp/x.py", "content": "hello",}'


@pytest.fixture
def sample_malformed_missing_brace():
    return '{"path": "/tmp/x.py", "content": "hello"'


@pytest.fixture
def sample_malformed_unclosed_bracket():
    return '{"keys": ["a", "b",}'


@pytest.fixture
def sample_python_none():
    return "None"


@pytest.fixture
def sample_empty_string():
    return ""


@pytest.fixture
def sample_whitespace_only():
    return "   \n\t  "


@pytest.fixture
def sample_valid_json():
    return '{"path": "/tmp/x.py", "content": "hello world"}'


@pytest.fixture
def sample_unrepairable_tool_call():
    """A payload that is neither valid JSON nor repairable."""
    return "\x00\x01\x02\x03\xff\xfe"


@pytest.fixture
def sample_long_unrepairable():
    """A long string that has no parseable JSON structure."""
    return "X" * 5000


# ---------------------------------------------------------------------------
# _is_mutation_tool
# ---------------------------------------------------------------------------

class TestIsMutationTool:
    def test_mutations(self):
        for name in MUTATION_TOOLS:
            assert _is_mutation_tool(name) is True

    def test_non_mutations(self):
        for name in NON_MUTATION_TOOLS:
            assert _is_mutation_tool(name) is False

    def test_unknown_tools_are_not_mutations(self):
        assert _is_mutation_tool("some_random_tool") is False

    def test_case_sensitive(self):
        assert _is_mutation_tool("Write_file") is False
        assert _is_mutation_tool("WRITE_FILE") is False


# ---------------------------------------------------------------------------
# repair_tool_call_arguments — valid JSON passthrough
# ---------------------------------------------------------------------------

class TestValidJsonPassthrough:
    def test_valid_json_repaired_as_is(self, sample_valid_json):
        result = repair_tool_call_arguments(sample_valid_json, "read_file")
        assert result["unrepairable"] is False
        assert json.loads(result["repaired_args"]) == json.loads(sample_valid_json)

    def test_valid_json_empty_object(self):
        result = repair_tool_call_arguments("{}", "read_file")
        assert result["unrepairable"] is False
        assert result["repaired_args"] == "{}"


# ---------------------------------------------------------------------------
# repair_tool_call_arguments — malformed JSON repair
# ---------------------------------------------------------------------------

class TestMalformedJsonRepair:
    def test_trailing_comma_repaired(self, sample_malformed_trailing_comma):
        result = repair_tool_call_arguments(sample_malformed_trailing_comma, "write_file")
        assert result["unrepairable"] is False
        parsed = json.loads(result["repaired_args"])
        assert parsed == {"path": "/tmp/x.py", "content": "hello"}

    def test_missing_closing_brace_repaired(self, sample_malformed_missing_brace):
        result = repair_tool_call_arguments(sample_malformed_missing_brace, "write_file")
        assert result["unrepairable"] is False
        parsed = json.loads(result["repaired_args"])
        assert parsed == {"path": "/tmp/x.py", "content": "hello"}

    def test_unclosed_bracket_repaired(self, sample_malformed_unclosed_bracket):
        result = repair_tool_call_arguments(sample_malformed_unclosed_bracket, "terminal")
        assert result["unrepairable"] is False
        parsed = json.loads(result["repaired_args"])
        assert parsed == {"keys": ["a", "b"]}


# ---------------------------------------------------------------------------
# repair_tool_call_arguments — unrepairable mutation tools
# ---------------------------------------------------------------------------

class TestUnrepairableMutationTools:
    def test_unrepairable_write_file_not_empty(self, sample_unrepairable_tool_call):
        result = repair_tool_call_arguments(
            sample_unrepairable_tool_call, "write_file"
        )
        assert result["unrepairable"] is True
        assert result["repaired_args"] != "{}"
        assert result["unrepairable_preview"] is not None
        assert result["unrepairable_preview"] != ""

    def test_unrepairable_patch_not_empty(self, sample_unrepairable_tool_call):
        result = repair_tool_call_arguments(sample_unrepairable_tool_call, "patch")
        assert result["unrepairable"] is True
        assert result["repaired_args"] != "{}"
        assert result["unrepairable_preview"] is not None

    def test_unrepairable_execute_code_not_empty(self, sample_unrepairable_tool_call):
        result = repair_tool_call_arguments(
            sample_unrepairable_tool_call, "execute_code"
        )
        assert result["unrepairable"] is True
        assert result["repaired_args"] != "{}"
        assert result["unrepairable_preview"] is not None

    def test_unrepairable_long_payload_truncated_preview(self, sample_long_unrepairable):
        result = repair_tool_call_arguments(sample_long_unrepairable, "write_file")
        assert result["unrepairable"] is True
        assert result["unrepairable_preview"] is not None
        # Preview should be truncated (not the full 5000 chars)
        assert len(result["unrepairable_preview"]) < len(sample_long_unrepairable)

    def test_unrepairable_args_do_not_execute_write_file(self, sample_unrepairable_tool_call):
        """Unrepairable write_file args should produce a preview, not '{}'.

        The runtime uses this to emit a structured blocked result instead of
        calling ``write_file`` with empty arguments.
        """
        result = repair_tool_call_arguments(sample_unrepairable_tool_call, "write_file")
        assert result["unrepairable"] is True
        # This is the key contract: repaired_args is NOT "{}" for mutation tools.
        assert result["repaired_args"] != "{}"


# ---------------------------------------------------------------------------
# repair_tool_call_arguments — unrepairable non-mutation tools (legacy)
# ---------------------------------------------------------------------------

class TestUnrepairableNonMutationTools:
    def test_unrepairable_read_file_returns_empty(self, sample_unrepairable_tool_call):
        result = repair_tool_call_arguments(sample_unrepairable_tool_call, "read_file")
        assert result["unrepairable"] is True
        assert result["repaired_args"] == "{}"
        assert result["unrepairable_preview"] is None

    def test_unrepairable_terminal_returns_empty(self, sample_unrepairable_tool_call):
        result = repair_tool_call_arguments(sample_unrepairable_tool_call, "terminal")
        assert result["unrepairable"] is True
        assert result["repaired_args"] == "{}"


# ---------------------------------------------------------------------------
# repair_tool_call_arguments — empty / None literal args
# ---------------------------------------------------------------------------

class TestEmptyAndNoneLiteralArgs:
    def test_empty_string_returns_empty(self, sample_empty_string):
        result = repair_tool_call_arguments(sample_empty_string, "write_file")
        assert result["was_empty"] is True
        assert result["repaired_args"] == "{}"
        assert result["unrepairable"] is False

    def test_whitespace_only_returns_empty(self, sample_whitespace_only):
        result = repair_tool_call_arguments(sample_whitespace_only, "write_file")
        assert result["was_empty"] is True
        assert result["repaired_args"] == "{}"
        assert result["unrepairable"] is False

    def test_python_none_literal_returns_empty(self, sample_python_none):
        result = repair_tool_call_arguments(sample_python_none, "write_file")
        assert result["was_empty"] is True
        assert result["repaired_args"] == "{}"


# ---------------------------------------------------------------------------
# repair_tool_call_arguments — structured result contract
# ---------------------------------------------------------------------------

class TestResultContract:
    def test_result_has_required_keys(self, sample_valid_json):
        result = repair_tool_call_arguments(sample_valid_json, "read_file")
        required_keys = {"repaired_args", "unrepairable", "unrepairable_preview", "was_empty"}
        assert required_keys.issubset(result.keys()), (
            f"Missing keys: {required_keys - set(result.keys())}"
        )

    def test_result_keys_present_for_unrepairable(self, sample_unrepairable_tool_call):
        result = repair_tool_call_arguments(sample_unrepairable_tool_call, "write_file")
        required_keys = {"repaired_args", "unrepairable", "unrepairable_preview", "was_empty"}
        assert required_keys.issubset(result.keys())

    def test_result_keys_present_for_empty(self, sample_empty_string):
        result = repair_tool_call_arguments(sample_empty_string, "write_file")
        required_keys = {"repaired_args", "unrepairable", "unrepairable_preview", "was_empty"}
        assert required_keys.issubset(result.keys())


# ---------------------------------------------------------------------------
# Backward compatibility: legacy _repair_tool_call_arguments still works
# ---------------------------------------------------------------------------

class TestLegacyRepairCompatibility:
    def test_legacy_repair_valid_json(self, sample_valid_json):
        result = _repair_tool_call_arguments(sample_valid_json, "read_file")
        # Legacy _repair_tool_call_arguments normalises JSON via json.dumps,
        # so whitespace may differ — compare parsed dicts instead.
        assert json.loads(result) == json.loads(sample_valid_json)

    def test_legacy_repair_trailing_comma(self, sample_malformed_trailing_comma):
        result = _repair_tool_call_arguments(sample_malformed_trailing_comma, "write_file")
        assert json.loads(result) == {"path": "/tmp/x.py", "content": "hello"}

    def test_legacy_repair_unrepairable_returns_empty(self, sample_unrepairable_tool_call):
        result = _repair_tool_call_arguments(sample_unrepairable_tool_call, "write_file")
        assert result == "{}"


# ---------------------------------------------------------------------------
# Regression: existing tool-call payload repair still passes
# ---------------------------------------------------------------------------

class TestExistingRegression:
    """Smoke tests mirroring the regression test that was already green."""

    def test_trailing_comma_repair(self):
        raw = '{"path": "/tmp/test.py", "content": "print(1)",}'
        result = repair_tool_call_arguments(raw, "write_file")
        assert result["unrepairable"] is False
        assert result["repaired_args"] != "{}"
        parsed = json.loads(result["repaired_args"])
        assert parsed["path"] == "/tmp/test.py"

    def test_missing_brace_repair(self):
        raw = '{"path": "/tmp/test.py", "content": "print(1)"'
        result = repair_tool_call_arguments(raw, "write_file")
        assert result["unrepairable"] is False
        parsed = json.loads(result["repaired_args"])
        assert parsed["content"] == "print(1)"

    def test_empty_args(self):
        result = repair_tool_call_arguments("", "read_file")
        assert result["repaired_args"] == "{}"
        assert result["was_empty"] is True
