"""Opt-in PCO completion-report runtime gate plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import logging
import os
import re

from . import discovery, gate_state, remediation, validation
from .gate_state import GateRecord

logger = logging.getLogger(__name__)

_RATIFICATION_RE = re.compile(
    r"Source\s+ratifies\s+prompt:(?P<path>\S+)\s+with\s+SHA(?:256)?:(?P<sha>[0-9a-f]{64})"
)
_IN_PROGRESS_MARKER_RE = re.compile(r"(?im)^\s*Gate status:\s*in_progress\s*$")
_IN_PROGRESS_FORBIDDEN_RE = re.compile(
    r"(?i)("
    r"\bcomplet(?:e|ed|ion)\b|"
    r"\bclos(?:e|ed|ure)\b|"
    r"\breleas(?:e|ed|ing)\b|"
    r"\bready\s+for\s+(?:the\s+)?next\s+source\b|"
    r"\bexact\s+next\s+source\s+prompt\b|"
    r"source\s+ratifies\s+prompt:"
    r")"
)


def _session(session_id: str | None) -> str:
    return session_id or "default"


def _record_from_ratification(text: str, session_id: str, repo_root: Path) -> GateRecord | None:
    match = _RATIFICATION_RE.search(text or "")
    if match is None:
        return None
    raw_path = Path(match.group("path"))
    sha = match.group("sha")
    if raw_path.is_absolute():
        rel = discovery.repo_relative(raw_path, repo_root)
        if rel is None:
            return None
        prompt_path = repo_root / rel
        envelope_ref = rel
    else:
        envelope_ref = raw_path.as_posix()
        prompt_path = repo_root / envelope_ref
    actual = discovery.sha256_file(prompt_path)
    if actual != sha:
        return None
    return GateRecord(
        session_id=session_id,
        controller_id=os.environ.get("HERMES_CONTROLLER_ID") or "unknown-controller",
        lane_id="single",
        envelope_ref=envelope_ref,
        envelope_sha256=sha,
        ratified_at=gate_state.utc_now_iso(),
        source="ratification_line_in_user_message",
        required=True,
    )


def _refresh_open_gate(session_id: str, user_message: str = "") -> GateRecord | None:
    repo_root = discovery.find_repo_root()
    if repo_root is None:
        return gate_state.registry.get(session_id)
    record = _record_from_ratification(user_message, session_id, repo_root)
    if record is not None:
        gate_state.registry.set(record)
        return record
    existing = gate_state.registry.get(session_id)
    if existing is not None:
        return existing
    claims = discovery.open_claims(repo_root, session_id=session_id)
    if claims:
        gate_state.registry.set(claims[0])
        return claims[0]
    return None


def _is_explicit_in_progress_response(response_text: str) -> bool:
    """Return true only for narrow, auditable non-terminal gate updates."""
    text = response_text or ""
    if _IN_PROGRESS_MARKER_RE.search(text) is None:
        return False
    if validation.terminal_section_violation(text) is None:
        return False
    return _IN_PROGRESS_FORBIDDEN_RE.search(text) is None


def _evaluate(record: GateRecord, response_text: str) -> str | None:
    if not record.required:
        return None
    if gate_state.is_historical(record):
        logger.info("pco-completion-gate: historical gate advisory only for session %s", record.session_id)
        return None
    if not record.controller_id or record.controller_id == "unknown-controller":
        logger.warning("pco-completion-gate: unknown controller for open gate")
    if _is_explicit_in_progress_response(response_text):
        logger.info(
            "pco-completion-gate: allowing explicit in-progress response for session %s",
            record.session_id,
        )
        return None

    repo_root = discovery.find_repo_root()
    if repo_root is None:
        return "validator_unavailable"
    matches = discovery.matching_reports(repo_root, record)
    reason, report_path, report_record = discovery.select_report(matches)
    if reason:
        return reason
    if report_path is None or report_record is None:
        return "missing_report"
    reason = validation.validate_report(report_record, report_path, repo_root)
    if reason:
        return reason
    if validation.envelope_drift(report_record, repo_root):
        return "envelope_drift"
    reason = validation.terminal_section_violation(response_text or "")
    if reason:
        return reason
    record.cleared_by_report_path = discovery.repo_relative(report_path, repo_root) or str(report_path)
    record.cleared_at = gate_state.utc_now_iso()
    gate_state.registry.set(record)
    return None


def _on_session_start(session_id: str = "", **_: Any) -> None:
    try:
        gate_state.installed_at()
        gate_state.registry.clear_session(_session(session_id))
    except Exception as exc:  # defensive hook boundary
        logger.debug("pco-completion-gate on_session_start failed: %s", exc)


def _on_pre_llm_call(user_message: str = "", session_id: str = "", **_: Any) -> None:
    try:
        gate_state.installed_at()
        _refresh_open_gate(_session(session_id), user_message)
    except Exception as exc:
        logger.debug("pco-completion-gate pre_llm_call failed: %s", exc)


def _on_transform_llm_output(response_text: str = "", session_id: str = "", **_: Any) -> str | None:
    try:
        gate_state.installed_at()
        sid = _session(session_id)
        record = _refresh_open_gate(sid)
        if record is None:
            return None
        reason = _evaluate(record, response_text)
        if reason is None:
            return None
        return remediation.render_block(reason, record)
    except Exception as exc:
        logger.warning("pco-completion-gate transform_llm_output failed open: %s", exc)
        return None


def _on_session_end(session_id: str = "", **_: Any) -> None:
    try:
        gate_state.registry.clear_session(_session(session_id))
    except Exception as exc:
        logger.debug("pco-completion-gate on_session_end failed: %s", exc)


def _handle_status(_raw_args: str = "") -> str:
    records = gate_state.registry.all()
    if not records:
        return "pco-completion-gate: no open in-process gates."
    lines = ["pco-completion-gate: open in-process gates"]
    for record in records:
        lines.append(
            f"- session={record.session_id} envelope_ref={record.envelope_ref} "
            f"lane_id={record.lane_id or 'single'} source={record.source}"
        )
    return "\n".join(lines)


def register(ctx) -> None:
    """Register hook callbacks.

    The manifest declares this plugin's priority intent. Current Hermes loads
    enabled standalone plugins in manifest discovery order and the core loop
    selects the first non-empty transform result; no bundled sibling presently
    registers `transform_llm_output`, so this callback is first among active
    sibling transformers when the plugin is enabled alone for this gate.
    """
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_hook("transform_llm_output", _on_transform_llm_output)
    ctx.register_hook("on_session_end", _on_session_end)
    ctx.register_command(
        "pco-gate",
        handler=_handle_status,
        description="Show PCO completion-report runtime gate state.",
        args_hint="status",
    )
