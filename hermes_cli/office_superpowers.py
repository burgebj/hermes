"""Agent Office diagnostics, watchdog, reporting, and evidence contracts.

The helpers in this module are deliberately Python-stdlib first and side-effect
free unless a caller explicitly writes an artifact. They are safe for scripts,
unit tests, and future CLI integration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from hermes_cli import agent_office
from hermes_cli import kanban_db as kb
from hermes_constants import get_hermes_home

POLICY_VERSION = "office-superpowers-v1"
SCORECARD_SCHEMA_VERSION = 1
REPORT_SCHEMA_VERSION = 1
WATCHDOG_SCHEMA_VERSION = 1
DOCTOR_SCHEMA_VERSION = 1

VERDICTS = {"PASS", "FAIL", "PARTIAL", "BLOCKED", "NOT_APPLICABLE", "PASS_WITH_CAVEAT"}
HEAVY_CLAIM_RE = re.compile(
    r"\b(benchmark|performance|latency|throughput|qps|rps|gpu|cuda|colab|release|deploy|production|model metric|accuracy|f1|auc|speedup)\b",
    re.I,
)

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)", re.I | re.S),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+\-/=]{12,}\b", re.I),
    re.compile(r"\b(api[_-]?key|token|secret|password|passwd|pwd|bot[_-]?token|client[_-]?secret|cookie)\b\s*[:=]\s*['\"]?[^'\"\s,;]{8,}", re.I),
    re.compile(r"\b(api[_-]?key|token|secret|password|passwd|pwd|bot[_-]?token|client[_-]?secret|cookie)\b\s+['\"]?[A-Za-z0-9._~+\-/=]{12,}", re.I),
    re.compile(r"\b(sessionid|sid|auth|authorization)=([^;\s]{8,})", re.I),
    re.compile(r"\b(sk-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9_]{10,}|xox[baprs]-[A-Za-z0-9-]{10,})\b", re.I),
)

_BLOCKER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("credentials", re.compile(r"\b(credential|credentials|api key|token|login|oauth|password|secret)\b", re.I)),
    ("paid_cloud_permission", re.compile(r"\b(paid|billing|payment|cloud permission|colab pro|pro account|quota purchase)\b", re.I)),
    ("destructive_irreversible_action", re.compile(r"\b(delete production|irreversible|destructive|wipe|drop database|rm -rf)\b", re.I)),
    ("legal_license_ambiguity", re.compile(r"\b(legal|license|licence|compliance|copyright)\b", re.I)),
    ("missing_runtime_or_hardware", re.compile(r"\b(gpu|cuda|hardware|runtime|driver|local gpu|missing runtime)\b", re.I)),
    ("unverifiable_claim", re.compile(r"\b(unverifiable|cannot verify|no evidence|no artifact)\b", re.I)),
    ("explicit_approval_mode", re.compile(r"\b(approval required|ask akhil|keep me in the loop|do not yolo|manual approval|take my permission)\b", re.I)),
    ("unsafe_secret_or_pii", re.compile(r"\b(secret leak|pii|private key|cookie leak|token leak)\b", re.I)),
    ("human_login_or_browser_profile_required", re.compile(r"\b(browser profile|human login|captcha|2fa|two-factor|manual login)\b", re.I)),
)


class RedactionStatus(Enum):
    CHECKED = "checked"
    REDACTED = "redacted"
    UNSAFE_BLOCKED = "unsafe_blocked"


@dataclass(frozen=True)
class ScorecardValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    redaction_status: str


@dataclass(frozen=True)
class OfficeBoundaryDecision:
    """Policy decision for Office superpowers access to sensitive resources.

    This is intentionally a deterministic fixture/helper rather than a runtime
    bypass: callers still need to wire it into the permission gateway or tool
    dispatcher before executing a tool action.
    """

    decision: str
    reason: str
    category: str
    matched_rule_id: str
    risk_level: str
    residual_risk: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_now(now: str | datetime | None = None) -> datetime:
    if isinstance(now, datetime):
        return now.astimezone(timezone.utc) if now.tzinfo else now.replace(tzinfo=timezone.utc)
    parsed = _parse_utc_timestamp(now)
    return parsed if parsed is not None else datetime.now(timezone.utc)


def redact_text(text: str | None) -> tuple[str, RedactionStatus]:
    """Return text with token/secret/cookie/private-key-looking values masked."""
    if text is None:
        return "", RedactionStatus.CHECKED
    redacted = str(text)
    changed = False
    for pattern in _SECRET_PATTERNS:
        new = pattern.sub("[REDACTED]", redacted)
        if new != redacted:
            changed = True
            redacted = new
    return redacted, RedactionStatus.REDACTED if changed else RedactionStatus.CHECKED


def redact_obj(obj: Any) -> tuple[Any, RedactionStatus]:
    changed = False
    def walk(value: Any) -> Any:
        nonlocal changed
        if isinstance(value, str):
            out, status = redact_text(value)
            changed = changed or status is RedactionStatus.REDACTED
            return out
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, tuple):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {str(k): walk(v) for k, v in value.items()}
        return value
    return walk(obj), RedactionStatus.REDACTED if changed else RedactionStatus.CHECKED


def blocker_type_for_text(text: str | None) -> str | None:
    if not text:
        return None
    # Routine review is explicitly not a human/external blocker.
    if re.search(r"\broutine\s+(review|reviewer|qa|security)\b", text, re.I):
        return None
    for label, pattern in _BLOCKER_PATTERNS:
        if pattern.search(text):
            return label
    return None


def _safe_resolve(path: str | os.PathLike[str]) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _path_parts_lower(path: Path) -> tuple[str, ...]:
    return tuple(part.lower() for part in path.parts)


def _classify_office_boundary_target(target: str | os.PathLike[str], *, workspace: str | os.PathLike[str] | None = None, hermes_home: str | os.PathLike[str] | None = None) -> tuple[str, str]:
    """Return (category, rule_id) for protected Office-superpowers paths.

    The classifier is path-only by design so it can be reused in tests, CLIs,
    and a future permission-gateway hook without importing tool internals.
    """
    p = _safe_resolve(target)
    home = _safe_resolve(hermes_home or get_hermes_home())
    ws = _safe_resolve(workspace) if workspace is not None else None
    parts = _path_parts_lower(p)
    name = p.name.lower()

    if "browser" in parts or "chrome" in parts or name in {"cookies", "cookies.sqlite", "login data", "web data"}:
        return "browser_profile_state", "office-boundary-browser-profile"
    if name in {".env", "auth.json", "credentials.json"} or re.search(r"(?i)(secret|token|cookie|credential|private[_-]?key)", p.name):
        return "secret_bearing_artifact", "office-boundary-secret-artifact"
    if name == "soul.md":
        return "protected_profile_artifact", "office-boundary-profile-soul"
    if name in {"config.yaml", "config.yml"} and "profiles" in parts:
        return "protected_profile_artifact", "office-boundary-profile-config"
    if any(part in {"memory", "memories", "active_memory", "user_profile"} for part in parts):
        return "active_memory", "office-boundary-active-memory"
    if any(part in {"approvals", "approval_records", "approval-records"} for part in parts):
        return "approval_records", "office-boundary-approval-records"
    if any(part in {"audit", "audits", "audit_logs", "audit-logs"} for part in parts):
        return "audit_logs", "office-boundary-audit-logs"
    if any(part in {"permission", "permissions", "policies", "policy"} for part in parts):
        return "permission_policy", "office-boundary-permission-policy"
    if any(part in {"production", "prod", "deployments", "releases"} for part in parts):
        return "production_state", "office-boundary-production-state"
    if ws is not None and _is_relative_to(p, ws):
        return "workspace", "office-boundary-workspace"
    if _is_relative_to(p, home):
        return "hermes_home_unclassified", "office-boundary-hermes-home-default"
    return "external_path", "office-boundary-external-path"


def evaluate_office_boundary_decision(
    *,
    action: str,
    target: str | os.PathLike[str],
    workspace: str | os.PathLike[str] | None = None,
    hermes_home: str | os.PathLike[str] | None = None,
    source_trust: str = "model_generated",
) -> OfficeBoundaryDecision:
    """Evaluate whether an Office superpowers action should be allowed.

    Decisions are fail-closed for protected artifacts and browser/secret state.
    This provides an enforceable policy fixture for permission-gateway/tooling
    integration and for tests that distinguish protected resources from normal
    workspace files.
    """
    action_l = action.strip().lower()
    category, rule_id = _classify_office_boundary_target(target, workspace=workspace, hermes_home=hermes_home)
    write_like = action_l in {"write", "append", "patch", "edit", "delete", "move", "rename", "publish", "deploy"}
    read_like = action_l in {"read", "list", "inspect", "stat"}

    if category == "workspace" and action_l in {"read", "list", "inspect", "stat", "write", "append", "patch", "edit"}:
        return OfficeBoundaryDecision("allow", "workspace-scoped Office operation", category, rule_id, "low")
    if category == "external_path":
        return OfficeBoundaryDecision("requires_approval", "target is outside the authorized workspace", category, rule_id, "high")
    if category == "hermes_home_unclassified":
        return OfficeBoundaryDecision("allow_read_only" if read_like else "requires_approval", "Hermes home state is not general workspace state", category, rule_id, "medium")
    if category == "browser_profile_state":
        return OfficeBoundaryDecision("requires_approval" if read_like else "deny", "browser cookies/profile state require human login/privacy approval and must not be mutated by Office automation", category, rule_id, "critical", "Visible page text/screenshots can still contain PII after tool-level approval.")
    if category == "secret_bearing_artifact":
        return OfficeBoundaryDecision("requires_approval" if read_like else "deny", "secret-bearing artifacts must not be read or written by broad Office automation without credential-owner approval", category, rule_id, "critical", "Regex redaction is a backstop, not a DLP boundary.")
    if category in {"approval_records", "audit_logs"}:
        return OfficeBoundaryDecision("allow_read_only" if read_like else "deny", "approval and audit records are append-only protected evidence", category, rule_id, "high")
    if category in {"protected_profile_artifact", "active_memory", "permission_policy", "production_state"}:
        decision = "requires_approval" if read_like or write_like else "deny"
        return OfficeBoundaryDecision(decision, f"{category} requires specialist/human approval before Office automation can touch it", category, rule_id, "high")
    return OfficeBoundaryDecision("requires_approval", "unknown Office boundary category fails closed", category, rule_id, "high")


def _normalize_artifact_path(path: str, workspace: Path | None) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute() and workspace is not None:
        p = workspace / p
    return p


def load_scorecard(path: str | os.PathLike[str]) -> dict[str, Any]:
    source = Path(path).read_text(encoding="utf-8")
    stripped = source.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    m = re.search(r"```(?:json)?\s*(?:office_gate_scorecard|gate_scorecard|scorecard)?\s*(\{.*?\})\s*```", source, re.S | re.I)
    if not m:
        raise ValueError("no JSON scorecard object found")
    return json.loads(m.group(1))


def validate_scorecard(scorecard: dict[str, Any], *, workspace: str | os.PathLike[str] | None = None) -> ScorecardValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    workspace_path = Path(workspace).expanduser().resolve() if workspace is not None else None

    redacted, status = redact_obj(scorecard)
    if status is RedactionStatus.REDACTED:
        warnings.append("secret-like values were redacted before validation")
    if not isinstance(redacted, dict):
        return ScorecardValidationResult(False, ["scorecard must be a JSON object"], warnings, status.value)

    if int(redacted.get("schema_version") or 0) != SCORECARD_SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if not str(redacted.get("task_id") or "").strip():
        errors.append("task_id is required")
    gates = redacted.get("gates")
    if not isinstance(gates, list):
        errors.append("gates must be a list")
        gates = []

    for idx, gate in enumerate(gates):
        if not isinstance(gate, dict):
            errors.append(f"gates[{idx}] must be an object")
            continue
        for key in ("gate", "command_or_check", "exit_code_or_artifact", "verdict", "rationale"):
            if not str(gate.get(key) or "").strip():
                errors.append(f"gates[{idx}].{key} is required")
        verdict = str(gate.get("verdict") or "").upper()
        if verdict not in VERDICTS:
            errors.append(f"gates[{idx}].verdict must be one of {sorted(VERDICTS)}")
        artifacts = gate.get("artifact_paths") or []
        if not isinstance(artifacts, list):
            errors.append(f"gates[{idx}].artifact_paths must be a list")
            artifacts = []
        heavy_blob = " ".join(str(gate.get(k) or "") for k in ("gate", "command_or_check", "exit_code_or_artifact", "rationale"))
        if HEAVY_CLAIM_RE.search(heavy_blob) and not artifacts:
            errors.append(f"gates[{idx}] heavy claim requires at least one artifact path")
        if HEAVY_CLAIM_RE.search(heavy_blob) and verdict == "PASS" and re.search(r"\b(dry[-_ ]?run|would[-_ ]?send|queued[-_ ]?only|template[-_ ]?only)\b", heavy_blob, re.I):
            errors.append(f"gates[{idx}] dry-run/queued-only evidence cannot be marked PASS for live delivery, deploy, release, or benchmark claims")
        for artifact in artifacts:
            if not isinstance(artifact, str) or not artifact.strip():
                errors.append(f"gates[{idx}] artifact path must be a non-empty string")
                continue
            if ".." in Path(artifact).parts:
                errors.append(f"gates[{idx}] artifact path must not contain '..': {artifact}")
                continue
            p = _normalize_artifact_path(artifact, workspace_path)
            if workspace_path and p.exists() is False:
                errors.append(f"gates[{idx}] artifact does not exist: {artifact}")
    return ScorecardValidationResult(not errors, errors, warnings, status.value)


def build_report_payload(
    *,
    report_type: str,
    task_id: str,
    title: str,
    state: str,
    assignee: str | None,
    evidence_summary: str,
    artifact_paths: Iterable[str] = (),
    next_owner_or_action: str | None = None,
    blocker_type: str | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "report_type": report_type,
        "task_id": task_id,
        "title": title,
        "state": state,
        "assignee": assignee,
        "evidence_summary": evidence_summary,
        "artifact_paths": [str(p) for p in artifact_paths],
        "next_owner_or_action": next_owner_or_action,
        "blocker_type": blocker_type,
        "created_at": utc_now(),
        "redaction_status": "checked",
    }
    redacted, status = redact_obj(payload)
    redacted["redaction_status"] = status.value
    return redacted


def _payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_report_outbox_records(outbox_path: str | os.PathLike[str]) -> list[dict[str, Any]]:
    """Load valid outbox JSONL records, normalizing legacy records to v1 state fields."""
    path = Path(outbox_path).expanduser()
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            records.append(_normalize_outbox_record(item))
    return records


def _normalize_outbox_record(item: dict[str, Any]) -> dict[str, Any]:
    record = dict(item)
    record["schema_version"] = int(record.get("schema_version") or 1)
    record["status"] = str(record.get("status") or "pending")
    record["attempts"] = int(record.get("attempts") or 0)
    record.setdefault("last_error", None)
    record.setdefault("next_attempt_at", utc_now() if record["status"] in {"pending", "failed"} else None)
    record.setdefault("sent_at", None)
    record.setdefault("delivery_result", None)
    return record


def _write_report_outbox_records(outbox_path: str | os.PathLike[str], records: list[dict[str, Any]]) -> None:
    path = Path(outbox_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    tmp.replace(path)


def enqueue_report_outbox(
    outbox_path: str | os.PathLike[str],
    payload: dict[str, Any],
    *,
    board: str,
    run_id: int | str | None = None,
) -> dict[str, Any]:
    """Append a redacted report send intent unless already present."""
    path = Path(outbox_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_payload, redaction_status = redact_obj(payload)
    key_material = {
        "board": board,
        "task_id": safe_payload.get("task_id"),
        "run_id": run_id,
        "report_type": safe_payload.get("report_type"),
        "payload_hash": _payload_hash(safe_payload),
    }
    idem = hashlib.sha256(json.dumps(key_material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    existing = load_report_outbox_records(path)
    for item in existing:
        if item.get("idempotency_key") == idem:
            return {"created": False, "idempotency_key": idem, "status": item.get("status", "pending"), "path": str(path)}
    now = utc_now()
    record = {
        "schema_version": 1,
        "idempotency_key": idem,
        "board": board,
        "run_id": run_id,
        "status": "pending",
        "attempts": 0,
        "created_at": now,
        "last_error": None,
        "next_attempt_at": now,
        "sent_at": None,
        "delivery_result": None,
        "redaction_status": redaction_status.value,
        "payload": safe_payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    return {"created": True, "idempotency_key": idem, "status": "pending", "path": str(path)}


def _is_outbox_record_due(record: dict[str, Any], now_dt: datetime) -> bool:
    due_at = _parse_utc_timestamp(record.get("next_attempt_at"))
    return due_at is None or due_at <= now_dt


def send_due_report_outbox(
    outbox_path: str | os.PathLike[str],
    *,
    sender,
    retry_failed: bool = False,
    now: str | datetime | None = None,
    base_backoff_seconds: int = 300,
    max_records: int | None = None,
) -> dict[str, Any]:
    """Send due outbox records through an injected sender with durable state transitions.

    The caller supplies the sender so CLI surfaces can stay explicitly dry-run unless
    a reviewed gateway sender is wired in. The sender is called at most once per
    due pending/failed record and should raise on delivery failure.
    """
    path = Path(outbox_path).expanduser()
    now_dt = _coerce_now(now)
    now_text = _format_utc_timestamp(now_dt)
    records = load_report_outbox_records(path)
    summary = {
        "ok": True,
        "path": str(path),
        "retry_failed": retry_failed,
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
        "processed_idempotency_keys": [],
    }
    processed = 0
    for record in records:
        status = record.get("status")
        eligible_statuses = {"pending", "failed"} if retry_failed else {"pending"}
        if status not in eligible_statuses or (status == "failed" and not _is_outbox_record_due(record, now_dt)):
            summary["skipped"] += 1
            continue
        if max_records is not None and processed >= max_records:
            summary["skipped"] += 1
            continue
        processed += 1
        record["attempts"] = int(record.get("attempts") or 0) + 1
        try:
            result = sender(dict(record))
        except Exception as exc:
            backoff = max(1, int(base_backoff_seconds)) * (2 ** max(0, record["attempts"] - 1))
            record["status"] = "failed"
            record["last_error"] = redact_text(str(exc))[0]
            record["next_attempt_at"] = _format_utc_timestamp(now_dt + timedelta(seconds=backoff))
            record["sent_at"] = None
            record["delivery_result"] = None
            summary["failed"] += 1
            summary["errors"].append({"idempotency_key": record.get("idempotency_key"), "error": record["last_error"]})
        else:
            safe_result, _ = redact_obj(result if isinstance(result, dict) else {"result": str(result)})
            record["status"] = "sent"
            record["last_error"] = None
            record["next_attempt_at"] = None
            record["sent_at"] = now_text
            record["delivery_result"] = safe_result
            summary["sent"] += 1
        summary["processed_idempotency_keys"].append(record.get("idempotency_key"))
    if records:
        _write_report_outbox_records(path, records)
    return summary


def preview_due_report_outbox(
    outbox_path: str | os.PathLike[str],
    *,
    retry_failed: bool = False,
    now: str | datetime | None = None,
) -> dict[str, Any]:
    now_dt = _coerce_now(now)
    records = load_report_outbox_records(outbox_path)
    due = 0
    skipped = 0
    eligible_statuses = {"pending", "failed"} if retry_failed else {"pending"}
    for record in records:
        status = record.get("status")
        if status in eligible_statuses and (status == "pending" or _is_outbox_record_due(record, now_dt)):
            due += 1
        else:
            skipped += 1
    return {"path": str(Path(outbox_path).expanduser()), "would_send": due, "skipped": skipped, "total": len(records), "retry_failed": retry_failed}


def load_report_outbox_status(outbox_path: str | os.PathLike[str]) -> dict[str, Any]:
    path = Path(outbox_path).expanduser()
    counts: dict[str, int] = {}
    total = 0
    oldest: str | None = None
    corrupt = 0
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except Exception:
                counts["corrupt"] = counts.get("corrupt", 0) + 1
                corrupt += 1
                total += 1
                continue
            item = _normalize_outbox_record(item) if isinstance(item, dict) else {"status": "corrupt"}
            status = str(item.get("status") or "pending")
            counts[status] = counts.get(status, 0) + 1
            total += 1
            created = item.get("created_at")
            if isinstance(created, str) and (oldest is None or created < oldest):
                oldest = created
    return {"schema_version": 1, "path": str(path), "exists": path.exists(), "total": total, "counts": counts, "oldest_created_at": oldest, "corrupt": corrupt}


def _section(id_: str, status: str, summary: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    redacted, _ = redact_obj(details or {})
    return {"id": id_, "status": status, "summary": redact_text(summary)[0], "details": redacted}


def _gateway_pid() -> int | None:
    try:
        from gateway.status import get_running_pid  # type: ignore
        pid = get_running_pid()
        return int(pid) if pid else None
    except Exception:
        return None


def _safe_config_presence() -> dict[str, Any]:
    config_path = get_hermes_home() / "config.yaml"
    env_path = get_hermes_home() / ".env"
    return {
        "config_path": str(config_path),
        "config_exists": config_path.exists(),
        "env_path": str(env_path),
        "env_exists": env_path.exists(),
        "telegram_configured": bool(os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_ALLOWED_USERS")),
    }


def build_doctor_report(*, board: str | None = None, include_log_tail: bool = False) -> dict[str, Any]:
    cfg = agent_office.office_config()
    board_slug = board or str(cfg.get("board") or "default")
    sections: list[dict[str, Any]] = []
    now = int(time.time())
    try:
        with kb.connect(board=board_slug) as conn:
            tasks = kb.list_tasks(conn, include_archived=False, limit=500)
        board_ok = True
        task_counts: dict[str, int] = {}
        for task in tasks:
            task_counts[task.status] = task_counts.get(task.status, 0) + 1
    except Exception as exc:
        board_ok = False
        task_counts = {}
        board_error = str(exc)
    else:
        board_error = None

    profiles = agent_office.validate_office_profiles()
    gateway_pid = _gateway_pid()
    hermes_home = get_hermes_home()
    log_dir = hermes_home / "logs"
    log_details: dict[str, Any] = {
        "log_dir": str(log_dir),
        "agent_log": str(log_dir / "agent.log"),
        "gateway_log": str(log_dir / "gateway.log"),
        "errors_log": str(log_dir / "errors.log"),
    }
    if include_log_tail:
        tails = {}
        for name in ("agent.log", "gateway.log", "errors.log"):
            p = log_dir / name
            if p.exists():
                tail = "\n".join(p.read_text(encoding="utf-8", errors="replace").splitlines()[-20:])
                tails[name] = redact_text(tail)[0]
        log_details["redacted_tail"] = tails

    sections.append(_section("runtime", "pass", "Local runtime inspected", {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "hermes_home": str(hermes_home),
        "created_at_epoch": now,
    }))
    sections.append(_section("gateway", "pass" if gateway_pid else "warn", "Gateway detected" if gateway_pid else "Gateway pid not detected", {"gateway_pid": gateway_pid, "dispatch_in_gateway": True}))
    sections.append(_section("messaging", "pass" if _safe_config_presence()["telegram_configured"] else "warn", "Messaging config presence checked without printing credentials", _safe_config_presence()))
    sections.append(_section("kanban_board", "pass" if board_ok else "fail", "Kanban board readable" if board_ok else "Kanban board read failed", {"board": board_slug, "task_counts": task_counts, "error": board_error}))
    sections.append(_section("workers_profiles", "pass" if not profiles.get("missing") else "fail", "Office worker profiles inspected", profiles))
    sections.append(_section("notifications", "warn", "Telegram reporting contract is available; live delivery is conditional on gateway config", {"contract": "report payload schema_version 1", "outbox_default": str(hermes_home / "office" / "report-outbox.jsonl")}))
    sections.append(_section("evidence_gates", "pass", "Evidence gate schema and scorecard validator available", {"verdicts": sorted(VERDICTS), "heavy_claims_require_artifacts": True}))
    sections.append(_section("logs", "pass" if log_dir.exists() else "warn", "Log paths listed; tails redacted only when requested", log_details))
    sections.append(_section("browser_dashboard", "warn", "Browser/dashboard access is documented as operator-bounded and not probed destructively", {"dashboard_checks": ["local route availability", "logs route", "kanban board route"], "cookie_policy": "do not print or persist cookies"}))
    rec_status = "pass" if board_ok and not profiles.get("missing") else "warn"
    sections.append(_section("recommendations", rec_status, "Run office watchdog for board-specific findings", {"command": "python3 scripts/office_watchdog.py --dry-run --json", "approval_needed_for_persistent_cron": True}))
    report = {
        "schema_version": DOCTOR_SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "created_at": utc_now(),
        "board": board_slug,
        "overall_status": "fail" if any(s["status"] == "fail" for s in sections) else ("warn" if any(s["status"] == "warn" for s in sections) else "pass"),
        "sections": sections,
    }
    return redact_obj(report)[0]


def _task_rows(conn) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM tasks WHERE status != 'archived'").fetchall()
    return [dict(r) for r in rows]


def _latest_run_metadata(conn, task_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT metadata FROM task_runs WHERE task_id = ? ORDER BY id DESC LIMIT 1",
        (task_id,),
    ).fetchone()
    if not row or not row["metadata"]:
        return None
    try:
        parsed = json.loads(row["metadata"])
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def build_watchdog_report(*, board: str | None = None, dry_run: bool = True, outbox_path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    board_slug = board or str(agent_office.office_config().get("board") or "default")
    now = int(time.time())
    findings: list[dict[str, Any]] = []
    try:
        with kb.connect(board=board_slug) as conn:
            tasks = _task_rows(conn)
            for task in tasks:
                tid = task["id"]
                if task.get("status") == "running" and task.get("claim_expires") and int(task["claim_expires"]) < now:
                    findings.append({
                        "issue_type": "stale_running_claim",
                        "severity": "error",
                        "task_id": tid,
                        "recommendation": "dispatcher can reclaim stale claim; verify worker is not live before forceful action",
                        "safe_auto_repair": "ping_or_reclaim_if_dispatcher_policy_allows",
                    })
                if int(task.get("consecutive_failures") or 0) >= 3:
                    findings.append({
                        "issue_type": "repeated_failure_cluster",
                        "severity": "critical" if int(task.get("consecutive_failures") or 0) >= 5 else "error",
                        "task_id": tid,
                        "assignee": task.get("assignee"),
                        "last_failure_error": redact_text(task.get("last_failure_error"))[0],
                        "recommendation": "route to supervisor/devops; fix nonspawnable profile or runtime loop before retrying",
                        "safe_auto_repair": "audit_comment_only",
                    })
                if task.get("status") == "ready" and not task.get("assignee"):
                    findings.append({
                        "issue_type": "ready_task_not_spawning",
                        "severity": "warning",
                        "task_id": tid,
                        "recommendation": "assign to a concrete Office profile seat",
                        "safe_auto_repair": "assign_if_role_policy_maps_cleanly",
                    })
                if task.get("assignee") and task.get("assignee") not in agent_office.office_profiles():
                    findings.append({
                        "issue_type": "nonspawnable_assignee",
                        "severity": "error",
                        "task_id": tid,
                        "assignee": task.get("assignee"),
                        "recommendation": "reassign to configured concrete profile seat",
                        "safe_auto_repair": "reassign_to_configured_equivalent_only",
                    })
                if task.get("status") == "blocked" and not blocker_type_for_text(str(task.get("result") or task.get("body") or "")):
                    findings.append({
                        "issue_type": "blocked_protocol_violation",
                        "severity": "warning",
                        "task_id": tid,
                        "recommendation": "confirm this is a real external blocker; routine review should use handoff metadata instead",
                        "safe_auto_repair": "comment_only",
                    })
                if task.get("status") == "done":
                    meta = _latest_run_metadata(conn, tid) or {}
                    has_scorecard = bool(meta.get("gate_scorecard") or meta.get("gate_scorecard_path") or meta.get("verification_report"))
                    if not has_scorecard:
                        findings.append({
                            "issue_type": "missing_gate_scorecard",
                            "severity": "warning",
                            "task_id": tid,
                            "recommendation": "request evidence gate scorecard before final closeout aggregation",
                            "safe_auto_repair": "route_qa_child_task",
                        })
    except Exception as exc:
        findings.append({"issue_type": "kanban_read_failed", "severity": "critical", "recommendation": "run Office Doctor and inspect board path", "error": redact_text(str(exc))[0]})

    if outbox_path:
        p = Path(outbox_path).expanduser()
        if p.exists():
            lines = [ln for ln in p.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
            if len(lines) > 10:
                findings.append({"issue_type": "outbox_backlog", "severity": "warning", "recommendation": "run report outbox send-due dry-run and verify gateway config", "count": len(lines)})
            blob = "\n".join(lines[-20:])
            if redact_text(blob)[1] is RedactionStatus.REDACTED:
                findings.append({"issue_type": "secret_risk_payload", "severity": "critical", "recommendation": "redact outbox payload before delivery"})
    report = {
        "schema_version": WATCHDOG_SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "created_at": utc_now(),
        "board": board_slug,
        "dry_run": dry_run,
        "findings": findings,
        "summary": {"count": len(findings), "critical": sum(1 for f in findings if f.get("severity") == "critical"), "error": sum(1 for f in findings if f.get("severity") == "error"), "warning": sum(1 for f in findings if f.get("severity") == "warning")},
        "mutations_performed": [],
    }
    return redact_obj(report)[0]


def format_doctor_text(report: dict[str, Any]) -> str:
    lines = [f"Office Doctor ({report.get('overall_status')})", f"board: {report.get('board')}"]
    for section in report.get("sections", []):
        lines.append(f"\n[{section['id']}] {section['status']}: {section['summary']}")
        for k, v in (section.get("details") or {}).items():
            if isinstance(v, (dict, list)):
                v = json.dumps(v, sort_keys=True)
            lines.append(f"  {k}: {v}")
    return "\n".join(lines) + "\n"


def format_watchdog_text(report: dict[str, Any]) -> str:
    lines = [f"Office Watchdog board={report.get('board')} dry_run={report.get('dry_run')}", f"findings: {report.get('summary', {}).get('count', 0)}"]
    for f in report.get("findings", []):
        lines.append(f"- {f.get('severity')} {f.get('issue_type')} task={f.get('task_id', '-')}: {f.get('recommendation')}")
    return "\n".join(lines) + "\n"


def _exit_for_report(report: dict[str, Any]) -> int:
    status = report.get("overall_status")
    if status == "fail":
        return 1
    if any(f.get("severity") == "critical" for f in report.get("findings", [])):
        return 2
    if report.get("findings"):
        return 1
    return 0


def doctor_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Office Doctor diagnostics for Hermes Agent Office")
    parser.add_argument("--board", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--include-log-tail", action="store_true")
    args = parser.parse_args(argv)
    report = build_doctor_report(board=args.board, include_log_tail=args.include_log_tail)
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else format_doctor_text(report))
    return _exit_for_report(report)


def watchdog_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Office Watchdog for stale/risky Hermes Agent Office states")
    parser.add_argument("--board", default=None)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--repair-routine", action="store_true")
    parser.add_argument("--confirm-routine-policy", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--outbox-path", default=None)
    args = parser.parse_args(argv)
    if args.repair_routine and not args.confirm_routine_policy:
        print("--repair-routine requires --confirm-routine-policy; no mutation performed")
        return 2
    report = build_watchdog_report(board=args.board, dry_run=not args.repair_routine, outbox_path=args.outbox_path)
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else format_watchdog_text(report))
    return _exit_for_report(report)


def scorecard_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Agent Office gate scorecards")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--json-file")
    src.add_argument("--markdown-file")
    src.add_argument("--stdin", action="store_true")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.stdin:
        scorecard = json.loads(os.sys.stdin.read())
    else:
        scorecard = load_scorecard(args.json_file or args.markdown_file)
    result = validate_scorecard(scorecard, workspace=args.workspace)
    payload = {"ok": result.ok, "errors": result.errors, "warnings": result.warnings, "redaction_status": result.redaction_status}
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else ("PASS" if result.ok else "FAIL: " + "; ".join(result.errors)))
    if result.redaction_status == RedactionStatus.UNSAFE_BLOCKED.value:
        return 2
    return 0 if result.ok else 1


def report_outbox_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent Office redacted queued/dry-run report outbox")
    parser.add_argument("--outbox", default=str(get_hermes_home() / "office" / "report-outbox.jsonl"))
    sub = parser.add_subparsers(dest="command", required=True)
    st = sub.add_parser("status")
    st.add_argument("--json", action="store_true")
    enq = sub.add_parser("enqueue")
    enq.add_argument("--payload-file", required=True)
    enq.add_argument("--board", default="default")
    enq.add_argument("--run-id", default=None)
    enq.add_argument("--json", action="store_true")
    send = sub.add_parser("send-due")
    send.add_argument("--dry-run", action="store_true", default=True, help="Preview queued records only; live delivery is explicitly deferred")
    send.add_argument("--json", action="store_true")
    retry = sub.add_parser("retry-failed")
    retry.add_argument("--dry-run", action="store_true", default=True, help="Preview failed due records only; live delivery is explicitly deferred")
    retry.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "status":
        status = load_report_outbox_status(args.outbox)
        print(json.dumps(status, indent=2, sort_keys=True) if args.json else f"outbox {status['path']}: {status['total']} records {status['counts']}")
        return 0
    if args.command == "enqueue":
        payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
        result = enqueue_report_outbox(args.outbox, payload, board=args.board, run_id=args.run_id)
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else f"{'created' if result['created'] else 'exists'} {result['idempotency_key']}")
        return 0
    retry_failed = args.command == "retry-failed"
    preview = preview_due_report_outbox(args.outbox, retry_failed=retry_failed)
    # Live Telegram/gateway send is explicitly deferred for this CLI surface. The
    # state-machine helper supports reviewed sender injection, but this command
    # must not imply delivery until credentials/target policy and smoke artifacts exist.
    result = {
        "ok": True,
        "dry_run": True,
        "live_delivery": "deferred",
        "message": "report outbox is queued/dry-run only; no Telegram/gateway message was sent",
        **preview,
        "status": load_report_outbox_status(args.outbox),
    }
    print(json.dumps(result, indent=2, sort_keys=True) if getattr(args, "json", False) else result["message"])
    return 0
