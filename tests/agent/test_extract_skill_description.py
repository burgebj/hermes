"""Regression tests for ``agent/skill_utils.py::extract_skill_description``.

Before #13944, this helper hard-truncated every skill description to 60
characters, while the runtime ``skills_list()`` tool (``tools/skills_tool.py``)
allowed 1024. The LLM therefore saw a vague prefix in the system prompt —
where the routing decision is actually made — and only got the full text
after deciding to call ``skills_list()``. The fix raises the system-prompt
limit to match the runtime-tool limit and ensures all three paths
(short, boundary, long) behave correctly.
"""

from agent.skill_utils import (
    extract_skill_description,
    SKILL_INDEX_MAX_DESCRIPTION_LENGTH,
)


class TestExtractSkillDescription:
    def test_empty_description_returns_empty_string(self):
        assert extract_skill_description({}) == ""
        assert extract_skill_description({"description": ""}) == ""

    def test_short_description_returned_verbatim(self):
        desc = "Short description"
        assert extract_skill_description({"description": desc}) == desc

    def test_description_at_60_chars_not_truncated(self):
        """Regression: old limit was 60; the 61st char used to be '...'."""
        desc = "x" * 60
        assert extract_skill_description({"description": desc}) == desc

    def test_description_over_60_not_truncated_under_new_limit(self):
        """Main regression guard for #13944."""
        desc = (
            "Complete guide to using and extending Hermes Agent — CLI "
            "tooling, skill authoring, and gateway integration"
        )
        assert len(desc) > 60
        result = extract_skill_description({"description": desc})
        assert result == desc
        assert not result.endswith("...")

    def test_description_at_exact_new_limit_not_truncated(self):
        desc = "x" * SKILL_INDEX_MAX_DESCRIPTION_LENGTH
        result = extract_skill_description({"description": desc})
        assert result == desc
        assert len(result) == SKILL_INDEX_MAX_DESCRIPTION_LENGTH

    def test_description_over_new_limit_is_truncated_with_ellipsis(self):
        desc = "x" * (SKILL_INDEX_MAX_DESCRIPTION_LENGTH + 500)
        result = extract_skill_description({"description": desc})
        assert len(result) == SKILL_INDEX_MAX_DESCRIPTION_LENGTH
        assert result.endswith("...")

    def test_description_strips_surrounding_quotes_and_whitespace(self):
        """Pre-existing behavior; guarded so the fix keeps the strip()."""
        assert (
            extract_skill_description({"description": "  'wrapped'  "})
            == "wrapped"
        )

    def test_new_limit_matches_skills_tool_runtime_limit(self):
        """#13944: the two paths must agree."""
        from tools.skills_tool import MAX_DESCRIPTION_LENGTH as RUNTIME_LIMIT
        assert SKILL_INDEX_MAX_DESCRIPTION_LENGTH == RUNTIME_LIMIT
