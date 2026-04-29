#!/usr/bin/env python3
from __future__ import annotations

import json


def test_cognee_query_tool_registered_and_available(monkeypatch, tmp_path):
    home = tmp_path / "profile"
    lab = home / "cognee_lab"
    scripts = lab / "scripts"
    py = lab / ".venv" / "bin" / "python"
    scripts.mkdir(parents=True)
    py.parent.mkdir(parents=True)
    py.write_text("#!/bin/sh\nexec python3 \"$@\"\n", encoding="utf-8")
    py.chmod(0o755)
    (scripts / "query.py").write_text("import json\nprint(json.dumps({'ok': True, 'results': []}))\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(home))

    from tools.registry import registry
    import tools.cognee_query_tool as tool

    assert tool.check_cognee_query_requirements() is True
    entry = registry.get_entry("cognee_query")
    assert entry is not None
    assert entry.toolset == "cognee"


def test_cognee_query_rejects_unsupported_search_type(monkeypatch):
    monkeypatch.setenv("HERMES_HOME", "/root/.hermes/profiles/cognee-lab")

    from tools.cognee_query_tool import cognee_query

    payload = json.loads(cognee_query("hello", search_type="TRIPLET_COMPLETION"))
    assert payload["success"] is False
    assert "unsupported search_type" in payload["error"]


def test_cognee_query_invokes_isolated_lab(monkeypatch, tmp_path):
    home = tmp_path / "profile"
    lab = home / "cognee_lab"
    scripts = lab / "scripts"
    py = lab / ".venv" / "bin" / "python"
    scripts.mkdir(parents=True)
    py.parent.mkdir(parents=True)
    py.write_text("#!/bin/sh\nexec python3 \"$@\"\n", encoding="utf-8")
    py.chmod(0o755)
    (scripts / "query.py").write_text(
        "import json, sys\n"
        "print(json.dumps({'ok': True, 'query_meta': {'question': sys.argv[1], 'dataset': 'test', 'only_context': True, 'answer_mode': False, 'search_type': 'CHUNKS', 'all_types': False, 'top_k': 5, 'include_triplets': False}, 'results': ['SOURCE_FILE: sample.md\\nanswer'], 'source_files': ['sample.md'], 'sources': [{'file': 'sample.md', 'mentions': 1, 'first_path': 'result[0]', 'text_preview': 'SOURCE_FILE: sample.md\\nanswer'}], 'source_count': 1, 'result_items': [{'path': 'result[0]', 'source_files': ['sample.md'], 'text_preview': 'SOURCE_FILE: sample.md\\nanswer', 'chars': 29}]}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(home))

    from tools.cognee_query_tool import cognee_query

    payload = json.loads(cognee_query("Who?", search_type="CHUNKS", include_raw=True))
    assert payload["success"] is True
    assert payload["lab_root"] == str(lab)
    assert payload["source_files"] == ["sample.md"]
    assert payload["source_count"] == 1
    assert payload["sources"] == [
        {
            "file": "sample.md",
            "mentions": 1,
            "first_path": "result[0]",
            "text_preview": "SOURCE_FILE: sample.md\nanswer",
        }
    ]
    assert payload["result_items"][0]["path"] == "result[0]"
    assert payload["result_items"][0]["source_files"] == ["sample.md"]
    assert payload["raw"]["query_meta"]["question"] == "Who?"
    assert "answer" in payload["result_text"]


def test_cognee_query_normalizes_source_filenames_from_envelope(monkeypatch, tmp_path):
    home = tmp_path / "profile"
    lab = home / "cognee_lab"
    scripts = lab / "scripts"
    py = lab / ".venv" / "bin" / "python"
    scripts.mkdir(parents=True)
    py.parent.mkdir(parents=True)
    py.write_text("#!/bin/sh\nexec python3 \"$@\"\n", encoding="utf-8")
    py.chmod(0o755)
    (scripts / "query.py").write_text(
        "import json\n"
        "print(json.dumps({'ok': True, 'results': ['Ada North — supported by SOURCE_FILE: project_zephyr.md.'], "
        "'source_files': ['project_zephyr.md.'], "
        "'sources': [{'file': 'project_zephyr.md.', 'mentions': 1, 'first_path': 'result[0]', 'text_preview': 'SOURCE_FILE: project_zephyr.md.'}], "
        "'source_count': 1, "
        "'result_items': [{'path': 'result[0]', 'source_files': ['project_zephyr.md.'], 'text_preview': 'SOURCE_FILE: project_zephyr.md.', 'chars': 31}]}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(home))

    from tools.cognee_query_tool import cognee_query

    payload = json.loads(cognee_query("Who?", search_type="CHUNKS", include_raw=True))

    assert payload["source_files"] == ["project_zephyr.md"]
    assert payload["sources"][0]["file"] == "project_zephyr.md"
    assert payload["result_items"][0]["source_files"] == ["project_zephyr.md"]
    assert payload["raw"]["source_files"] == ["project_zephyr.md"]


def test_source_extraction_handles_nested_results():
    from tools.cognee_query_tool import _extract_source_files, _extract_sources, _flatten_result_items

    value = {
        "CHUNKS": {
            "results": [
                "SOURCE_FILE: alpha.md\nalpha text SOURCE_FILE: beta.md",
                {"nested": "SOURCE_FILE: alpha.md\nmore alpha"},
            ]
        }
    }

    assert _extract_source_files(value) == ["alpha.md", "beta.md"]
    sources = _extract_sources(value)
    assert sources[0]["file"] == "alpha.md"
    assert sources[0]["mentions"] == 2
    assert sources[0]["first_path"] == "result.CHUNKS.results[0]"
    assert sources[1]["file"] == "beta.md"
    items = _flatten_result_items(value)
    assert [item["path"] for item in items] == [
        "result.CHUNKS.results[0]",
        "result.CHUNKS.results[1].nested",
    ]


def test_fallback_source_extraction_strips_trailing_punctuation():
    from tools.cognee_query_tool import _fallback_extract_source_files, _fallback_extract_sources, _fallback_flatten_result_items

    value = [
        "Supported by SOURCE_FILE: project_zephyr.md.",
        "See SOURCE_FILE: memory_policy.md, and SOURCE_FILE: zephyr_runbook.md);",
    ]

    assert _fallback_extract_source_files(value) == [
        "project_zephyr.md",
        "memory_policy.md",
        "zephyr_runbook.md",
    ]
    assert [source["file"] for source in _fallback_extract_sources(value)] == [
        "project_zephyr.md",
        "memory_policy.md",
        "zephyr_runbook.md",
    ]
    assert _fallback_flatten_result_items(value)[0]["source_files"] == ["project_zephyr.md"]


def test_cognee_query_answer_with_sources_combines_answer_and_chunk_sources(monkeypatch, tmp_path):
    home = tmp_path / "profile"
    lab = home / "cognee_lab"
    scripts = lab / "scripts"
    py = lab / ".venv" / "bin" / "python"
    scripts.mkdir(parents=True)
    py.parent.mkdir(parents=True)
    py.write_text("#!/bin/sh\nexec python3 \"$@\"\n", encoding="utf-8")
    py.chmod(0o755)
    (scripts / "query.py").write_text(
        "import json, sys\n"
        "search_type = sys.argv[sys.argv.index('--search-type') + 1]\n"
        "answer_mode = '--answer' in sys.argv\n"
        "if answer_mode and search_type == 'GRAPH_COMPLETION':\n"
        "    payload = {'ok': True, 'query_meta': {'search_type': 'GRAPH_COMPLETION', 'answer_mode': True}, 'results': ['Hermes Lantern; owned by Iris Vale.'], 'source_files': [], 'sources': [], 'source_count': 0, 'result_items': [{'path': 'result[0]', 'source_files': [], 'text_preview': 'Hermes Lantern; owned by Iris Vale.', 'chars': 35}]}\n"
        "else:\n"
        "    payload = {'ok': True, 'query_meta': {'search_type': 'CHUNKS', 'answer_mode': False}, 'results': ['SOURCE_FILE: hermes_ops_pilot.md\\nThe pilot codename is Hermes Lantern and the pilot owner is Iris Vale.'], 'source_files': ['hermes_ops_pilot.md'], 'sources': [{'file': 'hermes_ops_pilot.md', 'mentions': 1, 'first_path': 'result[0]', 'text_preview': 'SOURCE_FILE: hermes_ops_pilot.md\\nThe pilot codename is Hermes Lantern'}], 'source_count': 1, 'result_items': [{'path': 'result[0]', 'source_files': ['hermes_ops_pilot.md'], 'text_preview': 'SOURCE_FILE: hermes_ops_pilot.md\\nThe pilot codename is Hermes Lantern', 'chars': 91}]}\n"
        "print(json.dumps(payload))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(home))

    from tools.cognee_query_tool import cognee_query

    payload = json.loads(cognee_query(
        "What is the codename of the Hermes Ops pilot and who owns it?",
        search_type="GRAPH_COMPLETION",
        answer=True,
        answer_with_sources=True,
        include_raw=True,
    ))

    assert payload["success"] is True
    assert payload["answer_mode"] is True
    assert payload["answer_with_sources"] is True
    assert payload["source_files"] == ["hermes_ops_pilot.md"]
    assert payload["source_count"] == 1
    assert payload["answer_text"] == "Hermes Lantern; owned by Iris Vale."
    assert "source_raw" in payload["raw"]
    assert payload["raw"]["answer_raw"]["source_files"] == []
    assert payload["raw"]["source_raw"]["source_files"] == ["hermes_ops_pilot.md"]
    assert "Hermes Lantern" in payload["result_text"]


def test_cognee_query_loads_source_helpers_by_path_without_mutating_sys_path(monkeypatch, tmp_path):
    home = tmp_path / "profile"
    lab = home / "cognee_lab"
    scripts = lab / "scripts"
    py = lab / ".venv" / "bin" / "python"
    scripts.mkdir(parents=True)
    py.parent.mkdir(parents=True)
    py.write_text("#!/bin/sh\nexec python3 \"$@\"\n", encoding="utf-8")
    py.chmod(0o755)
    (scripts / "query.py").write_text("import json\nprint(json.dumps(['SOURCE_FILE: helper.md\\nanswer']))\n", encoding="utf-8")
    (scripts / "source_envelope.py").write_text(
        "def extract_source_files(value):\n    return ['loaded-helper.md']\n"
        "def extract_sources(value):\n    return [{'file': 'loaded-helper.md', 'mentions': 99, 'first_path': 'helper', 'text_preview': 'loaded'}]\n"
        "def flatten_result_items(value, path='result'):\n    return [{'path': 'helper', 'source_files': ['loaded-helper.md'], 'text_preview': 'loaded', 'chars': 6}]\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(home))

    from tools.cognee_query_tool import cognee_query

    payload = json.loads(cognee_query("Who?", search_type="CHUNKS", include_raw=True))
    assert payload["success"] is True
    assert payload["source_files"] == ["loaded-helper.md"]
    assert payload["sources"][0]["mentions"] == 99
    assert payload["result_items"][0]["path"] == "helper"
