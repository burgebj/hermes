from plugins.memory.holographic import (
    HolographicMemoryProvider,
    _normalize_prefetch_query,
    _prefetch_candidate_queries,
)


def _provider(tmp_path):
    provider = HolographicMemoryProvider(
        config={
            "db_path": str(tmp_path / "memory_store.db"),
            "hrr_weight": 0.0,
        }
    )
    provider.initialize("test-session")
    return provider


def test_prefetch_normalizes_mixed_language_question(tmp_path):
    provider = _provider(tmp_path)
    provider._store.add_fact(
        "PR1_PREFETCH_SENTINEL_20260527 verification answer is RYAN_CODEX_HOLO_527.",
        category="tool",
        tags="prefetch,test",
    )

    result = provider.prefetch(
        "PR1_PREFETCH_SENTINEL_20260527 verification answer 是什么？"
    )

    assert "## Holographic Memory" in result
    assert "RYAN_CODEX_HOLO_527" in result


def test_prefetch_fallback_handles_hyphenated_and_chinese_question_terms(tmp_path):
    provider = _provider(tmp_path)
    provider._store.add_fact(
        "Northbridge Orange Peel Protocol rollback code is CINDER-PAPAYA-42.",
        category="tool",
        tags="prefetch,test",
    )

    result = provider.prefetch("Northbridge Orange-Peel Protocol 的回滚口令是什么？")

    assert "## Holographic Memory" in result
    assert "CINDER-PAPAYA-42" in result


def test_prefetch_query_candidates_include_cleaned_and_or_fallback():
    candidates = _prefetch_candidate_queries(
        "请问 Northbridge Orange-Peel Protocol 对应的 rollback code 是啥"
    )
    modes = [mode for mode, _query in candidates]
    queries = [query for _mode, query in candidates]

    assert modes[:2] == ["raw", "cleaned"]
    assert "or" in modes
    assert any("Orange Peel Protocol" in query for query in queries)
    assert any(" OR " in query for query in queries)


def test_normalize_prefetch_query_keeps_high_signal_tokens():
    normalized = _normalize_prefetch_query(
        "告诉我 Aflo-9 shadow config 对应的 disable switch name 是什么？"
    )

    assert "Aflo 9" in normalized
    assert "shadow config" in normalized
    assert "disable switch name" in normalized
    assert "是什么" not in normalized
    assert "对应的" not in normalized


def test_normalize_prefetch_query_strips_chinese_control_scaffolding():
    normalized = _normalize_prefetch_query(
        "查看 当前的项目补丁情况，哪些字段当前的状态有影响"
    )

    assert normalized == "项目补丁 字段"
    assert "当前" not in normalized
    assert "情况" not in normalized
    assert "状态" not in normalized
    assert "影响" not in normalized


def test_normalize_prefetch_query_preserves_domain_terms_with_status_inside():
    normalized = _normalize_prefetch_query("项目状态驾驶舱是什么")

    assert normalized == "项目状态驾驶舱"


def test_prefetch_chinese_particle_split_finds_fact(tmp_path):
    provider = _provider(tmp_path)
    provider._store.add_fact(
        "课程平台 支付链路 source of truth lives in the operations note.",
        category="project",
        tags="prefetch,test",
    )

    result = provider.prefetch("课程平台的支付链路是什么？")

    assert "## Holographic Memory" in result
    assert "source of truth" in result
