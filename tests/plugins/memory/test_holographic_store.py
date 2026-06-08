"""Tests for holographic memory plugin's _extract_entities.

Covers the four original English rules plus the two CJK-aware rules added
to fix issue #24416 (ASCII-only extraction silently breaks non-English users).
"""

import pytest

from plugins.memory.holographic.store import MemoryStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract(text: str) -> list[str]:
    """Call _extract_entities without a real DB."""
    store = MemoryStore.__new__(MemoryStore)
    return store._extract_entities(text)


# ---------------------------------------------------------------------------
# Original English rules — must remain fully intact
# ---------------------------------------------------------------------------

class TestEnglishRules:
    def test_capitalized_multi_word(self):
        result = _extract("John Doe joined the team today.")
        assert "John Doe" in result

    def test_double_quoted(self):
        result = _extract('She uses "Python" daily.')
        assert "Python" in result

    def test_single_quoted(self):
        result = _extract("Run 'pytest' before merging.")
        assert "pytest" in result

    def test_aka_pattern(self):
        # AKA group 1 captures the left side; group 2 captures greedily to end
        result = _extract("Guido aka BDFL")
        assert "Guido" in result
        assert "BDFL" in result

    def test_dedup_preserves_first_seen_order(self):
        result = _extract('"Alpha" and "alpha" are the same.')
        assert result.count("Alpha") == 1
        assert result[0] == "Alpha"

    def test_empty_string(self):
        assert _extract("") == []

    def test_no_entities(self):
        # Pure lowercase English words with no special chars yield no entities
        assert _extract("nothing here to extract at all today") == []


# ---------------------------------------------------------------------------
# CJK bracket / quote rule (rule 5)
# ---------------------------------------------------------------------------

class TestCjkBracketRule:
    def test_japanese_corner_brackets(self):
        result = _extract("「白兔」App已接入完成。")
        assert "白兔" in result

    def test_double_corner_brackets(self):
        result = _extract("『Coco香港插班』计划已启动。")
        assert "Coco香港插班" in result

    def test_book_title_marks(self):
        result = _extract("参见《项目规划》文档。")
        assert "项目规划" in result

    def test_fullwidth_double_quote(self):
        result = _extract("“白兔控股”是正式名称。")
        assert "白兔控股" in result

    def test_fullwidth_single_quote(self):
        result = _extract("‘IHMS’系统已上线。")
        assert "IHMS" in result

    def test_stopword_inside_brackets_is_filtered(self):
        result = _extract("「的」这是一个测试。")
        assert "的" not in result

    def test_mixed_cjk_english_in_brackets(self):
        result = _extract("「lark-bot v2.1」已部署。")
        assert "lark-bot v2.1" in result

    def test_long_cjk_content_over_40_chars_not_matched(self):
        # CJK bracket pattern caps at 40 chars; 41-char CJK run should not match
        long = "白" * 41
        result = _extract(f"「{long}」")
        assert long not in result

    def test_multiple_brackets_in_one_sentence(self):
        result = _extract("「白兔」和「Kanban」项目合并。")
        assert "白兔" in result
        assert "Kanban" in result


# ---------------------------------------------------------------------------
# Mixed-script identifier rule (rule 6)
# ---------------------------------------------------------------------------

class TestMixedIdentRule:
    def test_hyphenated_tool_name(self):
        result = _extract("The lark-cli tool is used daily.")
        assert "lark-cli" in result

    def test_model_with_version(self):
        result = _extract("We migrated from GPT-5.5 last week.")
        assert "GPT-5.5" in result

    def test_domain_name(self):
        result = _extract("Check baitugroup.com for details.")
        assert "baitugroup.com" in result

    def test_versioned_acronym(self):
        # Pure-alpha acronyms need a non-letter char to be picked up by _RE_MIXED_IDENT
        result = _extract("IHMS-v2 handles hospital management.")
        assert "IHMS-v2" in result


# ---------------------------------------------------------------------------
# CJK context integration — issue #24416 reproduction scenario
# ---------------------------------------------------------------------------

class TestCjkIntegration:
    def test_chinese_fact_yields_entities(self):
        facts = [
            "飞书白兔 App 已于 2026-5-10 接入完成",
            "Coco 香港插班项目计划",
            "用户公司日常用「白兔」/「白兔控股」，不要用工商执照名「成都抖咖」",
        ]
        all_entities: list[str] = []
        for f in facts:
            all_entities.extend(_extract(f))
        assert len(all_entities) > 0, (
            "No entities extracted from Chinese facts (regression of #24416)"
        )

    def test_bracketed_entities_from_issue_example(self):
        text = "用户公司日常用「白兔」/「白兔控股」，不要用工商执照名「成都抖咖」"
        result = _extract(text)
        assert "白兔" in result
        assert "白兔控股" in result
        assert "成都抖咖" in result

    def test_english_behavior_unchanged_with_cjk_present(self):
        text = 'John Doe uses "pytest" and 「白兔」 daily.'
        result = _extract(text)
        assert "John Doe" in result
        assert "pytest" in result
        assert "白兔" in result
