from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path


def _load_stress_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "stress_test_feishu_pipeline.py"
    spec = importlib.util.spec_from_file_location("stress_test_feishu_pipeline", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_read_new_log_lines_merges_root_and_profile_logs(monkeypatch, tmp_path: Path):
    stress = _load_stress_module()

    root_log = tmp_path / "logs" / "agent.log"
    profile_log = tmp_path / "profiles" / "coder" / "logs" / "agent.log"
    root_log.parent.mkdir(parents=True)
    profile_log.parent.mkdir(parents=True)
    root_log.write_text("old root\n", encoding="utf-8")
    profile_log.write_text("old profile\n", encoding="utf-8")

    monkeypatch.setattr(stress, "LOG_FILE", root_log)
    monkeypatch.setattr(stress, "GATEWAY_LOG_FILES", [])
    monkeypatch.setattr(stress, "PROFILES_DIR", tmp_path / "profiles")

    positions = stress.get_log_position()
    root_log.write_text("old root\nnew root\n", encoding="utf-8")
    profile_log.write_text("old profile\nnew profile\n", encoding="utf-8")

    assert stress.read_new_log_lines(positions) == ["new root", "new profile"]


def test_read_new_log_lines_recovers_from_truncated_log(monkeypatch, tmp_path: Path):
    stress = _load_stress_module()

    root_log = tmp_path / "logs" / "agent.log"
    root_log.parent.mkdir(parents=True)
    root_log.write_text("old line that will be rotated away\n", encoding="utf-8")

    monkeypatch.setattr(stress, "LOG_FILE", root_log)
    monkeypatch.setattr(stress, "GATEWAY_LOG_FILES", [])
    monkeypatch.setattr(stress, "PROFILES_DIR", tmp_path / "profiles")

    positions = stress.get_log_position()
    root_log.write_text("[Feishu] streaming_card.finalized message_id=om_test\n", encoding="utf-8")

    assert stress.read_new_log_lines(positions) == [
        "[Feishu] streaming_card.finalized message_id=om_test"
    ]


def test_read_new_log_lines_filters_old_rotated_errors(monkeypatch, tmp_path: Path):
    stress = _load_stress_module()

    root_log = tmp_path / "logs" / "agent.log"
    root_log.parent.mkdir(parents=True)
    root_log.write_text("old marker\n", encoding="utf-8")

    monkeypatch.setattr(stress, "LOG_FILE", root_log)
    monkeypatch.setattr(stress, "GATEWAY_LOG_FILES", [])
    monkeypatch.setattr(stress, "PROFILES_DIR", tmp_path / "profiles")

    positions = stress.get_log_position()
    root_log.write_text(
        "\n".join(
            [
                "2026-04-29 03:28:28,169 ERROR old websocket failure",
                "Traceback (most recent call last):",
                "  File \"/old/path.py\", line 1, in old_error",
                "[Lark] [2026-04-30 00:22:54,482] [ERROR] old lark websocket failure",
                "Traceback (most recent call last):",
                "2026-05-04 12:04:43,517 INFO gateway.platforms.feishu: [Feishu] streaming_card.finalized message_id=om_test",
                "current continuation line without timestamp",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    since_ts = time.mktime(time.strptime("2026-05-04 12:03:39", "%Y-%m-%d %H:%M:%S"))

    assert stress.read_new_log_lines(positions, since_ts=since_ts) == [
        "2026-05-04 12:04:43,517 INFO gateway.platforms.feishu: [Feishu] streaming_card.finalized message_id=om_test",
        "current continuation line without timestamp",
    ]


def test_select_cases_filters_by_id():
    stress = _load_stress_module()

    cases = stress.select_cases("smoke", ["C1", "T1"])

    assert [case["id"] for case in cases] == ["C1", "T1"]


def test_select_cases_exposes_complete_openclaw_suites():
    stress = _load_stress_module()

    assert len(stress.select_cases("base")) == 64
    assert len(stress.select_cases("all")) == 64
    assert len(stress.select_cases("sheets")) == 7
    assert len(stress.select_cases("deep")) == 51
    assert len(stress.select_cases("integration")) == 5
    assert len(stress.select_cases("multitenant")) == 3
    assert len(stress.select_cases("failure")) == 3
    assert len(stress.select_cases("ux")) == 13
    assert len(stress.select_cases("channel")) == 22
    assert len(stress.select_cases("full")) == 168


def test_select_cases_exposes_exact_parity_suites():
    stress = _load_stress_module()

    expected_counts = {
        "exact-inventory": 2,
        "exact-auth": 4,
        "exact-policy": 6,
        "exact-card": 7,
        "exact-inbound": 5,
        "exact-outbound": 2,
        "exact-diagnose": 2,
        "exact": 28,
    }

    for suite, count in expected_counts.items():
        assert len(stress.select_cases(suite)) == count

    assert [case["id"] for case in stress.select_cases("exact-inventory")] == ["E0-1", "E0-2"]
    assert [case["id"] for case in stress.select_cases("exact-diagnose")] == ["E2-11", "E2-12"]


def test_static_inventory_reports_openclaw_actions_missing_from_hermes(tmp_path: Path):
    stress = _load_stress_module()

    openclaw_repo = tmp_path / "openclaw-lark"
    hermes_repo = tmp_path / "hermes"
    (openclaw_repo / "src" / "core").mkdir(parents=True)
    (hermes_repo / "tools").mkdir(parents=True)

    (openclaw_repo / "src" / "core" / "tool-scopes.ts").write_text(
        "\n".join(
            [
                "/*",
                " * export type ToolActionKey =",
                " *   | \"feishu_comment_example.only\";",
                " */",
                "export type ToolActionKey =",
                "  | 'feishu_calendar_event.list'",
                "  | 'feishu_missing.default';",
            ]
        ),
        encoding="utf-8",
    )
    (hermes_repo / "tools" / "feishu_calendar_tool.py").write_text(
        'ToolDefinition(name="feishu_calendar_list_events")\n',
        encoding="utf-8",
    )

    result = stress.run_static_check(
        {"id": "E0-1", "static_check": "openclaw_action_inventory"},
        openclaw_repo=openclaw_repo,
        hermes_repo=hermes_repo,
    )

    assert result["passed"] is False
    assert result["openclaw_actions"] == 2
    assert "feishu_calendar_event.list" in result["covered_actions"]
    assert result["missing_actions"] == ["feishu_missing.default"]


def test_static_schema_inventory_compares_required_params(tmp_path: Path):
    stress = _load_stress_module()

    openclaw_repo = tmp_path / "openclaw-lark"
    hermes_repo = tmp_path / "hermes"
    (openclaw_repo / "src" / "tools" / "oapi" / "calendar").mkdir(parents=True)
    (openclaw_repo / "src" / "core").mkdir(parents=True)
    (hermes_repo / "tools").mkdir(parents=True)

    (openclaw_repo / "src" / "core" / "tool-scopes.ts").write_text(
        "export type ToolActionKey =\n"
        "  | 'feishu_calendar_event.patch'\n"
        "  | 'feishu_calendar_event.search';\n",
        encoding="utf-8",
    )
    (openclaw_repo / "src" / "tools" / "oapi" / "calendar" / "event.ts").write_text(
        "\n".join(
            [
                "const FeishuCalendarEventSchema = Type.Union([",
                "  Type.Object({",
                "    action: Type.Literal('patch'),",
                "    event_id: Type.String({ description: 'Event ID' }),",
                "    summary: Type.Optional(Type.String({ description: 'title' })),",
                "  }),",
                "  Type.Object({",
                "    action: Type.Literal('search'),",
                "    query: Type.String({ description: 'keyword' }),",
                "  }),",
                "]);",
            ]
        ),
        encoding="utf-8",
    )
    (hermes_repo / "tools" / "feishu_openclaw_parity_tool.py").write_text(
        "\n".join(
            [
                "FEISHU_CALENDAR_UPDATE_EVENT_SCHEMA = {",
                '    "name": "feishu_calendar_update_event",',
                '    "parameters": {',
                '        "type": "object",',
                '        "properties": {"event_id": {"type": "string"}, "summary": {"type": "string"}},',
                '        "required": ["event_id"],',
                "    },",
                "}",
                "FEISHU_CALENDAR_SEARCH_EVENTS_SCHEMA = {",
                '    "name": "feishu_calendar_search_events",',
                '    "parameters": {',
                '        "type": "object",',
                '        "properties": {"query": {"type": "string"}},',
                '        "required": ["query"],',
                "    },",
                "}",
                'registry.register(name="feishu_calendar_update_event", schema=FEISHU_CALENDAR_UPDATE_EVENT_SCHEMA)',
                'registry.register(name="feishu_calendar_search_events", schema=FEISHU_CALENDAR_SEARCH_EVENTS_SCHEMA)',
            ]
        ),
        encoding="utf-8",
    )
    original = stress.OPENCLAW_ACTION_EQUIVALENTS.copy()
    stress.OPENCLAW_ACTION_EQUIVALENTS.update(
        {
            "feishu_calendar_event.patch": ["feishu_calendar_update_event"],
            "feishu_calendar_event.search": ["feishu_calendar_search_events"],
        }
    )
    try:
        result = stress.run_static_check(
            {"id": "E0-2", "static_check": "openclaw_schema_inventory"},
            openclaw_repo=openclaw_repo,
            hermes_repo=hermes_repo,
        )
    finally:
        stress.OPENCLAW_ACTION_EQUIVALENTS.clear()
        stress.OPENCLAW_ACTION_EQUIVALENTS.update(original)

    assert result["passed"] is True
    assert result["schema_actions"] == 2
    assert result["schema_mismatches"] == []


def test_static_schema_inventory_reports_missing_required_param(tmp_path: Path):
    stress = _load_stress_module()

    openclaw_repo = tmp_path / "openclaw-lark"
    hermes_repo = tmp_path / "hermes"
    (openclaw_repo / "src" / "tools" / "oapi" / "calendar").mkdir(parents=True)
    (openclaw_repo / "src" / "core").mkdir(parents=True)
    (hermes_repo / "tools").mkdir(parents=True)

    (openclaw_repo / "src" / "core" / "tool-scopes.ts").write_text(
        "export type ToolActionKey =\n  | 'feishu_calendar_event.search';\n",
        encoding="utf-8",
    )
    (openclaw_repo / "src" / "tools" / "oapi" / "calendar" / "event.ts").write_text(
        "const S = Type.Union([\n"
        "  Type.Object({\n"
        "    action: Type.Literal('search'),\n"
        "    query: Type.String({ description: 'keyword' }),\n"
        "  }),\n"
        "]);\n",
        encoding="utf-8",
    )
    (hermes_repo / "tools" / "feishu_gap.py").write_text(
        "FEISHU_CALENDAR_SEARCH_EVENTS_SCHEMA = {\n"
        '  "name": "feishu_calendar_search_events",\n'
        '  "parameters": {"type": "object", "properties": {}, "required": []},\n'
        "}\n"
        'registry.register(name="feishu_calendar_search_events", schema=FEISHU_CALENDAR_SEARCH_EVENTS_SCHEMA)\n',
        encoding="utf-8",
    )

    original = stress.OPENCLAW_ACTION_EQUIVALENTS.copy()
    stress.OPENCLAW_ACTION_EQUIVALENTS["feishu_calendar_event.search"] = [
        "feishu_calendar_search_events"
    ]
    try:
        result = stress.run_static_check(
            {"id": "E0-2", "static_check": "openclaw_schema_inventory"},
            openclaw_repo=openclaw_repo,
            hermes_repo=hermes_repo,
        )
    finally:
        stress.OPENCLAW_ACTION_EQUIVALENTS.clear()
        stress.OPENCLAW_ACTION_EQUIVALENTS.update(original)

    assert result["passed"] is False
    assert result["schema_mismatches"] == [
        {
            "action": "feishu_calendar_event.search",
            "tool": "feishu_calendar_search_events",
            "missing_required_params": ["query"],
        }
    ]


def test_render_case_input_requires_missing_fixtures():
    stress = _load_stress_module()

    rendered = stress.render_case_input(
        {"id": "X", "input": "读取文档 {doc_token}"},
        {"doc_token": "doc_123"},
    )
    assert rendered == "读取文档 doc_123"

    try:
        stress.render_case_input({"id": "X", "input": "读取文档 {doc_token}"}, {})
    except stress.MissingFixtureError as exc:
        assert exc.case_id == "X"
        assert exc.missing == ["doc_token"]
    else:
        raise AssertionError("render_case_input should require missing fixtures")


def test_bitable_mutation_cases_require_table_fixture():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}

    for case_id in ("B9", "B13"):
        try:
            stress.render_case_input(cases[case_id], {})
        except stress.MissingFixtureError as exc:
            assert "table_id" in exc.missing
        else:
            raise AssertionError(f"{case_id} should require table_id fixture")


def test_check_case_result_accepts_openclaw_equivalent_tool_logs():
    stress = _load_stress_module()

    result = stress.check_case_result(
        [
            "[multitenancy] running AIAgent for sender=ou_test_sender_1234567890abcdef profile=coder",
            "[multitenancy] Feishu UAT lookup sender=ou_test_sender_1234567890abcdef dir=/Users/kite/.hermes/feishu_uat",
            "[om_1] [multitenancy] tool.started feishu_sheet_create preview=",
            "[om_1] [multitenancy] tool.completed feishu_sheet_create duration=0.68s error=False",
        ],
        {"id": "Sh6", "expect_logs": ["feishu_sheet.create"]},
        "ou_test_sender_1234567890abcdef",
    )

    assert result["log_matched"] is True
    assert result["tool_dispatched"] is True
    assert result["tool_returned"] is True


def test_im_history_cases_use_explicit_chat_and_thread_fixtures():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}

    i3 = stress.render_case_input(
        cases["I3"],
        {"target_chat_id": "oc_target_chat"},
    )
    i4 = stress.render_case_input(
        cases["I4"],
        {"thread_id": "omt_thread_123"},
    )

    assert "oc_target_chat" in i3
    assert "chat" in i3.lower()
    assert "omt_thread_123" in i4


def test_pc7_uses_recurring_event_fixture_not_generic_event():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}

    try:
        stress.render_case_input(cases["PC7"], {"event_id": "evt_single_0"})
    except stress.MissingFixtureError as exc:
        assert exc.missing == ["recurring_event_id"]
    else:
        raise AssertionError("PC7 should require a dedicated recurring_event_id fixture")

    rendered = stress.render_case_input(
        cases["PC7"],
        {
            "event_id": "evt_single_0",
            "recurring_event_id": "evt_repeat_0",
        },
    )

    assert "evt_repeat_0" in rendered
    assert "evt_single_0" not in rendered


def test_doc_and_task_comment_cases_use_distinct_fixtures():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}

    for case_id in ("PR3", "PR5", "PD5"):
        try:
            stress.render_case_input(
                cases[case_id],
                {
                    "comment_id": "task_cmt",
                    "doc_token": "doc_1",
                },
            )
        except stress.MissingFixtureError as exc:
            assert exc.missing == ["doc_comment_id"]
        else:
            raise AssertionError(f"{case_id} should require doc_comment_id")

    try:
        stress.render_case_input(cases["PT4"], {"comment_id": "doc_cmt"})
    except stress.MissingFixtureError as exc:
        assert exc.missing == ["task_comment_id", "task_id"]
    else:
        raise AssertionError("PT4 should require task_id and task_comment_id")


def test_doc_comment_reply_and_patch_cases_include_doc_token():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}
    fixtures = {"doc_token": "doc_1", "doc_comment_id": "doc_cmt"}

    rendered_reply = stress.render_case_input(cases["PR3"], fixtures)
    rendered_patch = stress.render_case_input(cases["PD5"], fixtures)

    assert "doc_1" in rendered_reply
    assert "doc_cmt" in rendered_reply
    assert "doc_1" in rendered_patch
    assert "doc_cmt" in rendered_patch
    assert "标记为已解决" in rendered_patch


def test_task_agent_update_case_uses_agent_fixture():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}

    rendered = stress.render_case_input(cases["PT16"], {"agent_id": "agent_1"})

    assert "agent_1" in rendered


def test_task_update_case_is_not_completed_state_dependent():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}

    rendered = stress.render_case_input(cases["T4"], {"task_id": "task_1"})

    assert "标题改为" in rendered
    assert "已完成" not in rendered


def test_docx_update_case_uses_explicit_block_fixture():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}

    rendered = stress.render_case_input(
        cases["D2"],
        {"doc_id": "doc_1", "doc_block_id": "block_1"},
    )

    assert "doc_1" in rendered
    assert "block_1" in rendered
    assert "第 0 个文本元素" in rendered


def test_bitable_table_cases_include_app_token_context():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}
    fixtures = {
        "app_token": "app_1",
        "table_id": "tbl_1",
        "record_id": "rec_1",
        "field_id": "fld_1",
        "view_id": "vew_1",
        "bitable_search_field": "单选",
        "bitable_search_value": "重要",
        "bitable_create_value": "普通",
        "bitable_update_value": "普通",
    }

    for case_id in ("B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12", "B13", "B14", "PB6"):
        rendered = stress.render_case_input(cases[case_id], fixtures)
        assert "app_1" in rendered
        assert "tbl_1" in rendered

    assert "单选=重要" in stress.render_case_input(cases["B4"], fixtures)
    assert "Hermes auto" in stress.render_case_input(cases["B7"], fixtures)
    assert "Hermes UAT scratch field" in stress.render_case_input(cases["B9"], fixtures)
    assert "Hermes UAT scratch view" in stress.render_case_input(cases["B13"], fixtures)


def test_bitable_batch_record_cases_use_explicit_record_ids():
    stress = _load_stress_module()
    cases = {case["id"]: case for case in stress.select_cases("full")}
    fixtures = {
        "app_token": "app_1",
        "table_id": "tbl_1",
        "batch_record_ids": "rec_1, rec_2, rec_3",
    }

    for case_id in ("PB9", "PB10"):
        rendered = stress.render_case_input(cases[case_id], fixtures)
        assert "app_1" in rendered
        assert "tbl_1" in rendered
        assert "rec_1" in rendered


def test_ensure_uat_valid_for_post_refreshes_expiring_token(monkeypatch, tmp_path: Path):
    stress = _load_stress_module()
    uat_path = tmp_path / "ou_test.json"
    data = {"access_token": "old", "expires_at": 1}

    def fake_refresh(path, payload):
        assert path == uat_path
        assert payload["access_token"] == "old"
        return {"access_token": "new", "expires_at": 9999999999999}

    monkeypatch.setattr(stress, "refresh_uat_file", fake_refresh)

    refreshed = stress.ensure_uat_valid_for_post(uat_path, data)

    assert refreshed is data
    assert data["access_token"] == "new"


def test_token_expired_post_error_detects_feishu_code():
    stress = _load_stress_module()

    assert stress._is_token_expired_post_error(Exception("HTTP 401: code 99991677"))
    assert stress._is_token_expired_post_error(Exception("Authentication token expired"))


def test_checkpoint_keeps_latest_passed_case_ids(tmp_path: Path):
    stress = _load_stress_module()

    checkpoint = tmp_path / "stress.jsonl"
    checkpoint.write_text(
        "\n".join(
            [
                '{"id":"C1","passed":true}',
                '{"id":"C2","passed":false}',
                '{"id":"C2","passed":true}',
                '{"id":"bad",',
            ]
        ),
        encoding="utf-8",
    )

    assert stress.load_checkpoint(checkpoint) == {
        "C1": {"id": "C1", "passed": True},
        "C2": {"id": "C2", "passed": True},
    }
    assert stress.passed_checkpoint_ids(checkpoint) == {"C1", "C2"}


def test_record_checkpoint_appends_jsonl(tmp_path: Path):
    stress = _load_stress_module()

    checkpoint = tmp_path / "nested" / "stress.jsonl"
    stress.record_checkpoint(checkpoint, {"id": "C1", "passed": True, "elapsed": 1.2})

    saved = checkpoint.read_text(encoding="utf-8")
    assert '"id":"C1"' in saved
    assert '"passed":true' in saved
    assert '"recorded_at"' in saved


def test_checkpoint_recording_skips_dry_run_results():
    stress = _load_stress_module()

    assert stress.should_record_checkpoint({"id": "C1", "passed": True}, dry_run=False) is True
    assert stress.should_record_checkpoint({"id": "C1", "passed": False, "skipped": True}, dry_run=True) is False


def test_resolve_uat_path_selects_default_self_by_richest_valid_uat(tmp_path: Path):
    stress = _load_stress_module()

    lean = tmp_path / "ou_lean.json"
    rich = tmp_path / "ou_rich.json"
    lean.write_text(
        '{"user_open_id":"ou_lean","scope":"a b","expires_at":4102444800000}',
        encoding="utf-8",
    )
    rich.write_text(
        '{"user_open_id":"ou_rich","name":"美元本袁","scope":"a b c d","expires_at":4102444800000}',
        encoding="utf-8",
    )

    assert stress.resolve_uat_path(None, uat_dir=tmp_path) == rich
    assert stress.resolve_uat_path("默认本人", uat_dir=tmp_path) == rich
    assert stress.resolve_uat_path("美元本袁", uat_dir=tmp_path) == rich
    assert stress.resolve_uat_path("ou_lean", uat_dir=tmp_path) == lean


def test_load_uat_allows_expired_token_for_dry_run(tmp_path: Path):
    stress = _load_stress_module()

    expired = tmp_path / "ou_expired.json"
    expired.write_text(
        '{"user_open_id":"ou_expired","access_token":"tok","expires_at":1000,"scope":"a b"}',
        encoding="utf-8",
    )

    data = stress.load_uat(expired, require_valid=False)

    assert data["open_id"] == "ou_expired"
    assert data["access_token"] == "tok"


def test_load_uat_refreshes_expired_token_with_refresh_token(tmp_path: Path, monkeypatch):
    stress = _load_stress_module()

    expired = tmp_path / "ou_refresh.json"
    expired.write_text(
        json.dumps(
            {
                "user_open_id": "ou_refresh",
                "access_token": "old_access",
                "refresh_token": "old_refresh",
                "expires_at": 1000,
                "refresh_expires_at": int(time.time() * 1000) + 3600 * 1000,
                "scope": "calendar:calendar offline_access",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("FEISHU_APP_ID", "cli_refresh")
    monkeypatch.setenv("FEISHU_APP_SECRET", "sec_refresh")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "code": 0,
                    "access_token": "new_access",
                    "expires_in": 7200,
                    "refresh_token": "new_refresh",
                    "refresh_token_expires_in": 604800,
                    "token_type": "Bearer",
                    "scope": "calendar:calendar offline_access",
                }
            ).encode("utf-8")

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(stress.urllib.request, "urlopen", fake_urlopen)
    before_ms = int(time.time() * 1000)

    data = stress.load_uat(expired)

    assert captured["url"] == "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    assert captured["method"] == "POST"
    assert captured["body"] == {
        "grant_type": "refresh_token",
        "client_id": "cli_refresh",
        "client_secret": "sec_refresh",
        "refresh_token": "old_refresh",
    }
    assert data["access_token"] == "new_access"
    assert data["refresh_token"] == "new_refresh"
    persisted = json.loads(expired.read_text(encoding="utf-8"))
    assert persisted["access_token"] == "new_access"
    assert before_ms + 604800 * 1000 <= persisted["refresh_expires_at"] < before_ms + 604801 * 1000


def test_check_case_result_accepts_multitenancy_uat_lookup_log():
    stress = _load_stress_module()

    result = stress.check_case_result(
        [
            "[multitenancy] running AIAgent for sender=ou_test_sender profile=coder",
            "[multitenancy] Feishu UAT lookup sender=ou_test_sender dir=/tmp/.hermes/feishu_uat",
            "[multitenancy] tool.started feishu_calendar_list_events preview=",
        ],
        {"expect_tool": "feishu_calendar_list_events"},
        "ou_test_sender",
    )

    assert result["profile_routed"] is True
    assert result["tool_dispatched"] is True
    assert result["uat_used"] is True


def test_check_case_result_accepts_tool_completed_success_log():
    stress = _load_stress_module()

    result = stress.check_case_result(
        [
            "[multitenancy] running AIAgent for sender=ou_test_sender profile=coder",
            "[multitenancy] tool.started feishu_docx_create preview=",
            "[multitenancy] tool.completed feishu_docx_create duration=1.22s error=False",
        ],
        {"expect_tool": "feishu_docx_create"},
        "ou_test_sender",
    )

    assert result["tool_returned"] is True


def test_check_case_result_flags_tool_completed_error():
    stress = _load_stress_module()

    result = stress.check_case_result(
        [
            "[multitenancy] running AIAgent for sender=ou_test_sender profile=coder",
            "[multitenancy] tool.started feishu_search_user preview=Alice",
            "[multitenancy] tool.completed feishu_search_user duration=0.17s error=True",
        ],
        {"expect_tool": "feishu_search_user"},
        "ou_test_sender",
    )

    assert result["tool_returned"] is False
    assert any("feishu_search_user" in err for err in result["errors"])


def test_check_case_result_ignores_recovered_expected_tool_error():
    stress = _load_stress_module()

    result = stress.check_case_result(
        [
            "[multitenancy] running AIAgent for sender=ou_test_sender profile=coder",
            "[multitenancy] tool.started feishu_task_create preview=",
            "[multitenancy] tool.completed feishu_task_create duration=0.17s error=True",
            "[multitenancy] tool.started feishu_task_create preview=",
            "[multitenancy] tool.completed feishu_task_create duration=0.44s error=False",
        ],
        {"expect_tool": "feishu_task_create"},
        "ou_test_sender",
    )

    assert result["tool_returned"] is True
    assert result["errors"] == []


def test_required_checks_require_tool_return_for_expected_tool():
    stress = _load_stress_module()

    assert stress._required_checks({"expect_tool": "feishu_search_user"}, False) == [
        "tool_dispatched",
        "profile_routed",
        "tool_returned",
        "assistant_finalized",
    ]


def test_required_checks_can_target_direct_route():
    stress = _load_stress_module()

    assert stress._required_checks(
        {"expect_tool": "feishu_search_user"},
        False,
        route_mode="direct",
    ) == [
        "tool_dispatched",
        "direct_routed",
        "tool_returned",
        "assistant_finalized",
    ]


def test_required_checks_can_require_card_finalization():
    stress = _load_stress_module()

    assert stress._required_checks(
        {"expect_tool": "feishu_search_user"},
        False,
        route_mode="any",
        require_card_final=True,
    ) == [
        "tool_dispatched",
        "route_matched",
        "tool_returned",
        "assistant_finalized",
        "card_finalized",
    ]


def test_check_case_result_accepts_direct_gateway_logs():
    stress = _load_stress_module()

    result = stress.check_case_result(
        [
            "[feishu] _load_uat for_user access_token sender=ou_test_sender path=ou_test_sender.json",
            "tool feishu_calendar_list_events completed (0.42s, 200 chars)",
            "Turn ended: reason=assistant_final model=test api_calls=1/90 budget=1/90 tool_turns=1 last_msg_role=assistant response_len=20 session=s1",
        ],
        {"expect_tool": "feishu_calendar_list_events"},
        "ou_test_sender",
    )

    assert result["tool_dispatched"] is True
    assert result["tool_returned"] is True
    assert result["direct_routed"] is True
    assert result["route_matched"] is True
    assert result["uat_used"] is True
    assert result["assistant_finalized"] is True


def test_check_case_result_detects_streaming_card_finalization():
    stress = _load_stress_module()

    result = stress.check_case_result(
        [
            "[session] [multitenancy] running AIAgent for sender=ou_test_sender profile=coder",
            "[session] _load_uat for_user access_token sender=ou_test_sender",
            "[session] tool.started feishu_wiki_search",
            "[session] tool.completed feishu_wiki_search duration=0.00s error=False",
            "[session] feishu_wiki_search: success returned",
            "[session] assistant.finalized content_len=123",
            "[Feishu] streaming_card.finalized message_id=om_test",
        ],
        {"expect_tool": "feishu_wiki_search"},
        "ou_test_sender",
    )

    assert result["card_finalized"] is True


def test_check_case_result_waits_for_final_assistant_after_tool_return():
    stress = _load_stress_module()

    result = stress.check_case_result(
        [
            "[session] [multitenancy] running AIAgent for sender=ou_test_sender profile=coder",
            "[session] _load_uat for_user access_token sender=ou_test_sender",
            "[session] tool.started feishu_drive_list_files",
            "[session] tool.completed feishu_drive_list_files duration=0.00s error=False",
            "[session] feishu_drive_list_files: success returned",
        ],
        {"expect_tool": "feishu_drive_list_files"},
        "ou_test_sender",
    )

    assert result["tool_returned"] is True
    assert result["assistant_finalized"] is False


def test_required_checks_for_slash_log_only_cases_do_not_require_profile_route():
    stress = _load_stress_module()

    assert stress._required_checks(
        {"identity": "slash", "expect_logs": ["Received raw message"]},
        True,
    ) == ["log_matched"]


def test_check_case_result_accepts_expected_log_fragments_without_tool():
    stress = _load_stress_module()

    result = stress.check_case_result(
        [
            "[multitenancy] running AIAgent for sender=ou_test_sender profile=coder",
            "card entity created card_id=c_123",
            "cardElement.content: streaming chunk",
            "card.update: final card",
        ],
        {
            "id": "MC2",
            "expect_logs": ["card entity created", "cardElement.content", "card.update"],
        },
        "ou_test_sender",
    )

    assert result["tool_dispatched"] is True
    assert result["log_matched"] is True


def test_session_evidence_lines_recover_when_log_window_misses_message(monkeypatch, tmp_path: Path):
    stress = _load_stress_module()
    sessions = tmp_path / "profiles" / "coder" / "sessions"
    sessions.mkdir(parents=True)
    (sessions / "session_om_test.json").write_text(
        json.dumps(
            {
                "messages": [
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "feishu_bitable_batch_delete_records",
                                    "arguments": "{}",
                                }
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "content": json.dumps(
                            {
                                "records": [
                                    {"record_id": "rec_1", "deleted": True},
                                ]
                            }
                        ),
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(stress, "PROFILES_DIR", tmp_path / "profiles")

    lines = stress.read_session_evidence_lines("om_test", "ou_test_sender")

    result = stress.check_case_result(
        lines,
        {"expect_logs": ["feishu_bitable_app_table_record.batch_delete"]},
        "ou_test_sender",
    )
    assert result["tool_dispatched"] is True
    assert result["tool_returned"] is True
    assert result["log_matched"] is True
    assert result["profile_routed"] is True
    assert result["uat_used"] is True
