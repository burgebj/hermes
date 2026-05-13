from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli.office_superpowers import (
    RedactionStatus,
    blocker_type_for_text,
    build_doctor_report,
    build_report_payload,
    build_watchdog_report,
    enqueue_report_outbox,
    evaluate_office_boundary_decision,
    load_report_outbox_records,
    load_report_outbox_status,
    load_scorecard,
    report_outbox_cli,
    send_due_report_outbox,
    redact_text,
    validate_scorecard,
    watchdog_cli,
)



@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb.init_db()
    return home


def test_redact_text_masks_tokens_cookies_and_private_keys():
    fake_key = "sk-" + "test1234567890abcdef"
    fake_cookie = "sessionid=" + "abcdef123456"
    fake_bearer = "Bearer " + "abcdef1234567890abcdef"
    fake_private = "-----BEGIN " + "PRIVATE KEY-----x"
    raw = f"api_key='{fake_key}' cookie={fake_cookie} bearer={fake_bearer} {fake_private}"
    redacted, status = redact_text(raw)
    assert status is RedactionStatus.REDACTED
    assert "sk-test" not in redacted
    assert "sessionid=abcdef" not in redacted
    assert "Bearer abcdef" not in redacted
    assert "PRIVATE KEY" not in redacted
    assert redacted.count("[REDACTED]") >= 4


def test_scorecard_accepts_complete_evidence_and_rejects_heavy_claim_without_artifact(tmp_path):
    good_artifact = tmp_path / "bench.json"
    good_artifact.write_text('{"latency_ms": 12}', encoding="utf-8")
    scorecard = {
        "schema_version": 1,
        "task_id": "t_demo",
        "gates": [
            {
                "gate": "benchmark claim",
                "command_or_check": "pytest tests/test_demo.py",
                "exit_code_or_artifact": "0",
                "artifact_paths": [str(good_artifact)],
                "verdict": "PASS",
                "rationale": "Benchmark result is backed by JSON artifact.",
            }
        ],
    }
    result = validate_scorecard(scorecard, workspace=tmp_path)
    assert result.ok is True
    assert result.errors == []

    scorecard["gates"][0]["artifact_paths"] = []
    result = validate_scorecard(scorecard, workspace=tmp_path)
    assert result.ok is False
    assert any("heavy claim" in e.lower() for e in result.errors)


def test_scorecard_rejects_dry_run_or_queued_only_pass_for_heavy_live_claims(tmp_path):
    artifact = tmp_path / "outbox-preview.json"
    artifact.write_text('{"live_delivery":"deferred","would_send":1}', encoding="utf-8")
    scorecard = {
        "schema_version": 1,
        "task_id": "t_demo",
        "gates": [
            {
                "gate": "Telegram live delivery smoke",
                "command_or_check": "office_report_outbox send-due --dry-run",
                "exit_code_or_artifact": "0; queued-only; would_send=1",
                "artifact_paths": [str(artifact)],
                "verdict": "PASS",
                "rationale": "Dry-run deploy/release/benchmark/live delivery preview only.",
            }
        ],
    }

    result = validate_scorecard(scorecard, workspace=tmp_path)

    assert result.ok is False
    assert any("dry-run/queued-only" in e for e in result.errors)

    scorecard["gates"][0]["verdict"] = "PARTIAL"
    result = validate_scorecard(scorecard, workspace=tmp_path)
    assert result.ok is True


def test_scorecard_loader_extracts_markdown_json_block(tmp_path):
    path = tmp_path / "scorecard.md"
    path.write_text(
        "before\n```json office_gate_scorecard\n"
        + json.dumps({"schema_version": 1, "task_id": "t_demo", "gates": []})
        + "\n```\nafter\n",
        encoding="utf-8",
    )
    assert load_scorecard(path)["task_id"] == "t_demo"


def test_blocker_taxonomy_only_marks_real_external_blockers():
    assert blocker_type_for_text("Need routine reviewer eyes before merge") is None
    assert blocker_type_for_text("Blocked on missing credentials for Telegram") == "credentials"
    assert blocker_type_for_text("Need paid cloud permission for Colab Pro") == "paid_cloud_permission"
    assert blocker_type_for_text("Need local GPU runtime") == "missing_runtime_or_hardware"


def test_office_boundary_allows_workspace_operations_and_denies_protected_writes(tmp_path):
    hermes_home = tmp_path / ".hermes"
    workspace = tmp_path / "workspace"
    hermes_home.mkdir()
    workspace.mkdir()

    allowed = evaluate_office_boundary_decision(
        action="write",
        target=workspace / "docs" / "report.md",
        workspace=workspace,
        hermes_home=hermes_home,
    )
    assert allowed.decision == "allow"
    assert allowed.category == "workspace"

    other_soul = evaluate_office_boundary_decision(
        action="write",
        target=hermes_home / "profiles" / "coder" / "SOUL.md",
        workspace=workspace,
        hermes_home=hermes_home,
    )
    assert other_soul.decision == "requires_approval"
    assert other_soul.category == "protected_profile_artifact"

    approval_record = evaluate_office_boundary_decision(
        action="patch",
        target=hermes_home / "approvals" / "records.jsonl",
        workspace=workspace,
        hermes_home=hermes_home,
    )
    assert approval_record.decision == "deny"
    assert approval_record.category == "approval_records"


def test_office_boundary_secrets_browser_memory_policy_and_external_paths_fail_closed(tmp_path):
    hermes_home = tmp_path / ".hermes"
    workspace = tmp_path / "workspace"
    hermes_home.mkdir()
    workspace.mkdir()

    cases = [
        ("read", hermes_home / ".env", "requires_approval", "secret_bearing_artifact"),
        ("write", hermes_home / ".env", "deny", "secret_bearing_artifact"),
        ("read", hermes_home / "browser" / "Default" / "Cookies", "requires_approval", "browser_profile_state"),
        ("write", hermes_home / "profiles" / "security" / "memory" / "active.json", "requires_approval", "active_memory"),
        ("write", hermes_home / "policies" / "permissions.yaml", "requires_approval", "permission_policy"),
        ("deploy", hermes_home / "production" / "state.json", "requires_approval", "production_state"),
        ("read", tmp_path / "outside" / "notes.md", "requires_approval", "external_path"),
    ]
    for action, target, decision, category in cases:
        result = evaluate_office_boundary_decision(action=action, target=target, workspace=workspace, hermes_home=hermes_home)
        assert result.decision == decision
        assert result.category == category
        assert result.matched_rule_id.startswith("office-boundary-")


def test_doctor_report_contains_required_sections_and_redacts_config(kanban_home):
    config = kanban_home / "config.yaml"
    config.write_text("telegram:\n  bot_token: secret-token-value\n", encoding="utf-8")
    report = build_doctor_report(board="default", include_log_tail=False)
    sections = {s["id"] for s in report["sections"]}
    assert {
        "runtime",
        "gateway",
        "messaging",
        "kanban_board",
        "workers_profiles",
        "notifications",
        "evidence_gates",
        "logs",
        "browser_dashboard",
        "recommendations",
    } <= sections
    serialized = json.dumps(report)
    assert "secret-token-value" not in serialized
    assert report["schema_version"] == 1


def test_watchdog_flags_stale_claim_repeated_failure_and_missing_scorecard(kanban_home):
    with kb.connect() as conn:
        stale = kb.create_task(conn, title="stale", assignee="coder")
        kb.claim_task(conn, stale, claimer="host:worker")
        conn.execute("UPDATE tasks SET claim_expires = ? WHERE id = ?", (int(time.time()) - 60, stale))

        failing = kb.create_task(conn, title="failing", assignee="ghost")
        conn.execute(
            "UPDATE tasks SET consecutive_failures = 3, last_failure_error = ? WHERE id = ?",
            ("Profile 'ghost' does not exist", failing),
        )

        done = kb.create_task(conn, title="done without scorecard", assignee="coder")
        kb.complete_task(conn, done, metadata={"changed_files": ["x.py"]})

    report = build_watchdog_report(board="default", dry_run=True)
    findings = {(f["issue_type"], f.get("task_id")) for f in report["findings"]}
    assert ("stale_running_claim", stale) in findings
    assert ("repeated_failure_cluster", failing) in findings
    assert ("missing_gate_scorecard", done) in findings
    assert report["dry_run"] is True
    assert "Profile 'ghost'" in json.dumps(report)


def test_watchdog_race_windows_blocked_taxonomy_and_safe_repair_semantics(kanban_home, capsys):
    now = int(time.time())
    with kb.connect() as conn:
        fresh = kb.create_task(conn, title="fresh running", assignee="coder")
        kb.claim_task(conn, fresh, claimer="host:worker", ttl_seconds=600)

        expired = kb.create_task(conn, title="expired running", assignee="coder")
        kb.claim_task(conn, expired, claimer="host:worker")
        conn.execute("UPDATE tasks SET claim_expires = ? WHERE id = ?", (now - 1, expired))

        credentials_blocked = kb.create_task(conn, title="real blocker", assignee="coder")
        conn.execute(
            "UPDATE tasks SET status = 'blocked', result = ? WHERE id = ?",
            ("Blocked on missing credentials for Telegram live smoke", credentials_blocked),
        )

        routine_review_blocked = kb.create_task(conn, title="routine review", assignee="coder")
        conn.execute(
            "UPDATE tasks SET status = 'blocked', result = ? WHERE id = ?",
            ("routine reviewer eyes needed", routine_review_blocked),
        )

        missing_scorecard = kb.create_task(conn, title="done no scorecard", assignee="qa")
        kb.complete_task(conn, missing_scorecard, metadata={"changed_files": ["test.py"]})
        conn.commit()

    dry_report = build_watchdog_report(board="default", dry_run=True)
    findings = {(f["issue_type"], f.get("task_id")): f for f in dry_report["findings"]}

    assert ("stale_running_claim", expired) in findings
    assert ("stale_running_claim", fresh) not in findings
    assert ("blocked_protocol_violation", credentials_blocked) not in findings
    assert ("blocked_protocol_violation", routine_review_blocked) in findings
    assert findings[("missing_gate_scorecard", missing_scorecard)]["safe_auto_repair"] == "route_qa_child_task"
    assert dry_report["mutations_performed"] == []

    denied_exit = watchdog_cli(["--board", "default", "--repair-routine", "--json"])
    denied_out = capsys.readouterr().out
    assert denied_exit == 2
    assert "requires --confirm-routine-policy" in denied_out

    confirmed_exit = watchdog_cli(["--board", "default", "--repair-routine", "--confirm-routine-policy", "--json"])
    confirmed_payload = json.loads(capsys.readouterr().out)
    assert confirmed_exit == 1
    assert confirmed_payload["dry_run"] is False
    assert confirmed_payload["mutations_performed"] == []


def test_report_payload_contract_redacts_and_has_required_fields():
    payload = build_report_payload(
        report_type="completed",
        task_id="t_demo",
        title="Ship token abcdef1234567890abcdef",
        state="done",
        assignee="coder",
        evidence_summary="benchmark artifact docs/bench.json",
        artifact_paths=["docs/bench.json"],
        next_owner_or_action="qa",
    )
    assert payload["schema_version"] == 1
    assert payload["report_type"] == "completed"
    assert payload["artifact_paths"] == ["docs/bench.json"]
    assert "abcdef1234567890abcdef" not in json.dumps(payload)
    assert payload["redaction_status"] in {"checked", "redacted"}


def test_report_outbox_enqueue_is_idempotent_and_redacted(tmp_path):
    outbox = tmp_path / "outbox.jsonl"
    payload = build_report_payload(
        report_type="completed",
        task_id="t_demo",
        title="Ship token abcdef1234567890abcdef",
        state="done",
        assignee="coder",
        evidence_summary="done",
        artifact_paths=[],
        next_owner_or_action="qa",
    )
    first = enqueue_report_outbox(outbox, payload, board="default", run_id=7)
    second = enqueue_report_outbox(outbox, payload, board="default", run_id=7)
    assert first["idempotency_key"] == second["idempotency_key"]
    assert first["created"] is True
    assert second["created"] is False
    text = outbox.read_text(encoding="utf-8")
    assert len(text.splitlines()) == 1
    assert "abcdef1234567890abcdef" not in text
    status = load_report_outbox_status(outbox)
    assert status["counts"]["pending"] == 1
    assert status["total"] == 1
    record = load_report_outbox_records(outbox)[0]
    assert record["status"] == "pending"
    assert record["attempts"] == 0
    assert record["last_error"] is None
    assert record["sent_at"] is None
    assert record["next_attempt_at"]


def test_report_outbox_send_due_marks_sent_and_skips_duplicate_sends(tmp_path):
    outbox = tmp_path / "outbox.jsonl"
    payload = build_report_payload(
        report_type="completed",
        task_id="t_demo",
        title="Done",
        state="done",
        assignee="coder",
        evidence_summary="done",
    )
    enqueue_report_outbox(outbox, payload, board="default", run_id=7)
    calls = []

    def sender(record):
        calls.append(record["idempotency_key"])
        return {"delivery_id": "telegram-message-1"}

    first = send_due_report_outbox(outbox, sender=sender, now="2026-05-13T00:00:00Z")
    second = send_due_report_outbox(outbox, sender=sender, now="2026-05-13T00:01:00Z")

    assert first["sent"] == 1
    assert first["failed"] == 0
    assert second["sent"] == 0
    assert second["skipped"] == 1
    assert calls == [load_report_outbox_records(outbox)[0]["idempotency_key"]]
    record = load_report_outbox_records(outbox)[0]
    assert record["status"] == "sent"
    assert record["attempts"] == 1
    assert record["last_error"] is None
    assert record["sent_at"] == "2026-05-13T00:00:00Z"
    assert record["next_attempt_at"] is None
    assert record["delivery_result"] == {"delivery_id": "telegram-message-1"}


def test_report_outbox_failed_send_records_error_and_retry_backoff(tmp_path):
    outbox = tmp_path / "outbox.jsonl"
    payload = build_report_payload(
        report_type="blocked",
        task_id="t_demo",
        title="Blocked",
        state="blocked",
        assignee="coder",
        evidence_summary="blocked",
    )
    enqueue_report_outbox(outbox, payload, board="default", run_id=8)

    def failing_sender(_record):
        raise RuntimeError("gateway unavailable")

    result = send_due_report_outbox(outbox, sender=failing_sender, now="2026-05-13T00:00:00Z", base_backoff_seconds=60)

    assert result["sent"] == 0
    assert result["failed"] == 1
    record = load_report_outbox_records(outbox)[0]
    assert record["status"] == "failed"
    assert record["attempts"] == 1
    assert record["last_error"] == "gateway unavailable"
    assert record["sent_at"] is None
    assert record["next_attempt_at"] == "2026-05-13T00:01:00Z"


def test_report_outbox_retry_failed_respects_due_time_and_succeeds(tmp_path):
    outbox = tmp_path / "outbox.jsonl"
    payload = build_report_payload(
        report_type="completed",
        task_id="t_demo",
        title="Done",
        state="done",
        assignee="coder",
        evidence_summary="done",
    )
    enqueue_report_outbox(outbox, payload, board="default", run_id=9)

    send_due_report_outbox(
        outbox,
        sender=lambda _record: (_ for _ in ()).throw(RuntimeError("temporary outage")),
        now="2026-05-13T00:00:00Z",
        base_backoff_seconds=60,
    )
    too_early = send_due_report_outbox(outbox, sender=lambda _record: {"ok": True}, retry_failed=True, now="2026-05-13T00:00:30Z")
    due = send_due_report_outbox(outbox, sender=lambda _record: {"ok": True}, retry_failed=True, now="2026-05-13T00:01:00Z")

    assert too_early["sent"] == 0
    assert too_early["skipped"] == 1
    assert due["sent"] == 1
    record = load_report_outbox_records(outbox)[0]
    assert record["status"] == "sent"
    assert record["attempts"] == 2
    assert record["last_error"] is None
    assert record["sent_at"] == "2026-05-13T00:01:00Z"


def test_report_outbox_cli_is_explicitly_dry_run_by_default(tmp_path, capsys):
    outbox = tmp_path / "outbox.jsonl"
    payload = build_report_payload(
        report_type="completed",
        task_id="t_demo",
        title="Done",
        state="done",
        assignee="coder",
        evidence_summary="done",
    )
    enqueue_report_outbox(outbox, payload, board="default", run_id=10)

    exit_code = report_outbox_cli(["--outbox", str(outbox), "send-due", "--json"])
    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert exit_code == 0
    assert result["dry_run"] is True
    assert result["live_delivery"] == "deferred"
    assert result["would_send"] == 1
    assert "queued/dry-run only" in result["message"]
    assert load_report_outbox_records(outbox)[0]["status"] == "pending"
