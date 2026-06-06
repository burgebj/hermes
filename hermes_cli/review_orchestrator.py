from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable, Iterable, Sequence

from hermes_cli.safe_refactor_audit import AuditFinding, AuditResult, _parse_unified_diff, audit_tdb3_diff

_REVIEW_ORDER = ("m3_audit", "call_chain", "pytest", "report")
_RETRYABLE_M3_VERDICTS = {"REJECT_HARD", "WARN"}
_PYTHON_KEYWORDS = {
    "if",
    "for",
    "while",
    "return",
    "print",
    "with",
    "assert",
    "and",
    "or",
    "not",
}
_CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


@dataclass(frozen=True)
class CallChainAnalysis:
    changed_python_paths: tuple[str, ...]
    shared_helpers: tuple[str, ...]
    file_to_helpers: dict[str, tuple[str, ...]]
    dual_implementation_detected: bool
    approval_ready: bool
    summary: str


@dataclass(frozen=True)
class PytestExecution:
    command: tuple[str, ...]
    exit_code: int
    output: str
    summary: str


@dataclass(frozen=True)
class AutomatedReviewResult:
    verdict: str
    stage_order: tuple[str, ...]
    reasons: tuple[str, ...]
    audit_result: AuditResult
    call_chain: CallChainAnalysis
    pytest: PytestExecution
    report_text: str | None
    report_considered: bool
    report_consistency: str
    report_scope_flags: tuple[str, ...]
    machine_findings: tuple[AuditFinding, ...]


@dataclass(frozen=True)
class CorrectionDispatch:
    diff_text: str
    report_text: str | None = None
    report_path: str | Path | None = None


@dataclass(frozen=True)
class ReviewAttempt:
    attempt_number: int
    review_result: AutomatedReviewResult
    correction_instructions: str | None


@dataclass(frozen=True)
class SelfCorrectionReviewResult:
    verdict: str
    final_review: AutomatedReviewResult
    attempts: tuple[ReviewAttempt, ...]
    correction_history: tuple[str, ...]
    stopped_after_max_attempts: bool


def extract_call_chain_differences(diff_text: str) -> CallChainAnalysis:
    helper_map: dict[str, tuple[str, ...]] = {}
    python_paths: list[str] = []

    for file_diff in _parse_unified_diff(diff_text):
        if not file_diff.path.endswith(".py"):
            continue
        python_paths.append(file_diff.path)
        helpers = sorted(_extract_called_helpers(file_diff.lines))
        helper_map[file_diff.path] = tuple(helpers)

    shared_helpers = _shared_helpers(helper_map.values())
    dual_implementation_detected = len(python_paths) >= 2 and not shared_helpers
    approval_ready = len(python_paths) >= 2 and bool(shared_helpers) and not dual_implementation_detected

    if not python_paths:
        summary = "No changed Python files available for call-chain analysis"
    elif approval_ready:
        summary = f"Shared helper reuse detected: {', '.join(shared_helpers)}"
    elif dual_implementation_detected:
        summary = "Changed Python files do not share helper calls; dual implementation may still exist"
    else:
        summary = "Call-chain evidence is incomplete; cannot approve from call-chain analysis alone"

    return CallChainAnalysis(
        changed_python_paths=tuple(python_paths),
        shared_helpers=tuple(shared_helpers),
        file_to_helpers=helper_map,
        dual_implementation_detected=dual_implementation_detected,
        approval_ready=approval_ready,
        summary=summary,
    )


def run_pytest_command(
    command: Sequence[str],
    *,
    cwd: str | Path | None = None,
) -> PytestExecution:
    completed = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    summary = _summarize_pytest_output(output, completed.returncode)
    return PytestExecution(
        command=tuple(command),
        exit_code=completed.returncode,
        output=output,
        summary=summary,
    )


def read_optional_report(report_path: str | Path | None) -> str | None:
    if report_path is None:
        return None
    path = Path(report_path)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def run_automated_review(
    diff_text: str,
    *,
    pytest_command: Sequence[str] | None = None,
    report_path: str | Path | None = None,
    report_text: str | None = None,
    cwd: str | Path | None = None,
    audit_fn: Callable[[str], AuditResult] = audit_tdb3_diff,
    call_chain_extractor: Callable[[str], CallChainAnalysis] = extract_call_chain_differences,
    pytest_runner: Callable[[Sequence[str]], PytestExecution] | None = None,
    report_reader: Callable[[str | Path | None], str | None] = read_optional_report,
) -> AutomatedReviewResult:
    stage_order: list[str] = []

    stage_order.append("m3_audit")
    audit_result = audit_fn(diff_text)

    stage_order.append("call_chain")
    call_chain = call_chain_extractor(diff_text)

    if pytest_command is None:
        pytest_command = (sys.executable, "-m", "pytest")
    if pytest_runner is None:
        pytest_runner = lambda command: run_pytest_command(command, cwd=cwd)

    stage_order.append("pytest")
    pytest_result = pytest_runner(tuple(pytest_command))

    stage_order.append("report")
    resolved_report_text = report_text if report_text is not None else report_reader(report_path)
    report_consistency, report_scope_flags = _evaluate_report(
        resolved_report_text,
        audit_result,
        call_chain,
        pytest_result,
    )

    verdict, reasons = _synthesize_verdict(
        audit_result=audit_result,
        call_chain=call_chain,
        pytest_result=pytest_result,
        report_consistency=report_consistency,
        report_scope_flags=report_scope_flags,
    )

    return AutomatedReviewResult(
        verdict=verdict,
        stage_order=tuple(stage_order),
        reasons=tuple(reasons),
        audit_result=audit_result,
        call_chain=call_chain,
        pytest=pytest_result,
        report_text=resolved_report_text,
        report_considered=resolved_report_text is not None,
        report_consistency=report_consistency,
        report_scope_flags=tuple(report_scope_flags),
        machine_findings=audit_result.findings,
    )


def run_self_correcting_review(
    diff_text: str,
    *,
    pytest_command: Sequence[str] | None = None,
    report_path: str | Path | None = None,
    report_text: str | None = None,
    cwd: str | Path | None = None,
    audit_fn: Callable[[str], AuditResult] = audit_tdb3_diff,
    call_chain_extractor: Callable[[str], CallChainAnalysis] = extract_call_chain_differences,
    pytest_runner: Callable[[Sequence[str]], PytestExecution] | None = None,
    report_reader: Callable[[str | Path | None], str | None] = read_optional_report,
    correction_dispatcher: Callable[[int, AutomatedReviewResult, str], CorrectionDispatch | str] | None = None,
    max_attempts: int = 3,
) -> SelfCorrectionReviewResult:
    current_diff_text = diff_text
    current_report_path = report_path
    current_report_text = report_text
    attempts: list[ReviewAttempt] = []
    correction_history: list[str] = []

    for attempt_number in range(1, max_attempts + 1):
        review_result = run_automated_review(
            current_diff_text,
            pytest_command=pytest_command,
            report_path=current_report_path,
            report_text=current_report_text,
            cwd=cwd,
            audit_fn=audit_fn,
            call_chain_extractor=call_chain_extractor,
            pytest_runner=pytest_runner,
            report_reader=report_reader,
        )

        should_retry = (
            review_result.verdict != "APPROVE_CANDIDATE"
            and review_result.audit_result.verdict in _RETRYABLE_M3_VERDICTS
            and attempt_number < max_attempts
            and correction_dispatcher is not None
        )

        correction_instructions: str | None = None
        if should_retry:
            correction_instructions = build_correction_instructions(review_result, attempt_number)
            correction_history.append(correction_instructions)

        attempts.append(
            ReviewAttempt(
                attempt_number=attempt_number,
                review_result=review_result,
                correction_instructions=correction_instructions,
            )
        )

        if review_result.verdict == "APPROVE_CANDIDATE":
            return SelfCorrectionReviewResult(
                verdict=review_result.verdict,
                final_review=review_result,
                attempts=tuple(attempts),
                correction_history=tuple(correction_history),
                stopped_after_max_attempts=False,
            )

        if not should_retry:
            return SelfCorrectionReviewResult(
                verdict=review_result.verdict,
                final_review=review_result,
                attempts=tuple(attempts),
                correction_history=tuple(correction_history),
                stopped_after_max_attempts=attempt_number >= max_attempts,
            )

        dispatch = correction_dispatcher(attempt_number, review_result, correction_instructions)
        if isinstance(dispatch, str):
            dispatch = CorrectionDispatch(diff_text=dispatch)
        current_diff_text = dispatch.diff_text
        current_report_path = dispatch.report_path
        current_report_text = dispatch.report_text

    final_review = attempts[-1].review_result
    return SelfCorrectionReviewResult(
        verdict=final_review.verdict,
        final_review=final_review,
        attempts=tuple(attempts),
        correction_history=tuple(correction_history),
        stopped_after_max_attempts=True,
    )


def build_correction_instructions(review_result: AutomatedReviewResult, attempt_number: int) -> str:
    finding_lines = [
        _format_finding(finding)
        for finding in review_result.audit_result.findings
    ]
    if not finding_lines:
        finding_lines = [f"verdict={review_result.audit_result.verdict}"]

    reason_lines = [f"- {reason}" for reason in review_result.reasons] or ["- no synthesized reasons available"]
    joined_findings = "\n".join(f"- {line}" for line in finding_lines)
    joined_reasons = "\n".join(reason_lines)
    return (
        f"Attempt {attempt_number} correction request\n"
        f"M3 verdict: {review_result.audit_result.verdict}\n"
        f"Findings:\n{joined_findings}\n"
        f"Review blockers:\n{joined_reasons}\n"
        "Required action: address every listed finding, keep edits within allowed TDB-3 scope, "
        "then resubmit an updated diff and optional report for a fresh M3->call_chain->pytest->report pass."
    )


def _format_finding(finding: AuditFinding) -> str:
    location = f" @ {finding.path}" if finding.path else ""
    return f"{finding.severity}:{finding.rule_id}{location}: {finding.message}"


def _extract_called_helpers(lines: Iterable[str]) -> set[str]:
    helpers: set[str] = set()
    for line in lines:
        if not line.startswith(("+", "-")):
            continue
        for match in _CALL_RE.finditer(line):
            name = match.group(1)
            if name in _PYTHON_KEYWORDS:
                continue
            helpers.add(name)
    return helpers


def _shared_helpers(helper_groups: Iterable[tuple[str, ...]]) -> list[str]:
    groups = [set(group) for group in helper_groups if group]
    if len(groups) < 2:
        return []
    shared = set.intersection(*groups)
    return sorted(shared)


def _summarize_pytest_output(output: str, exit_code: int) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    tail = lines[-3:] if lines else []
    tail_text = " | ".join(tail)
    if tail_text:
        return f"exit={exit_code}; {tail_text}"
    return f"exit={exit_code}; no pytest output captured"


def _evaluate_report(
    report_text: str | None,
    audit_result: AuditResult,
    call_chain: CallChainAnalysis,
    pytest_result: PytestExecution,
) -> tuple[str, tuple[str, ...]]:
    if report_text is None:
        return "NOT_PROVIDED", ()

    lowered = report_text.lower()
    scope_flags: list[str] = []
    if "out of scope" in lowered:
        scope_flags.append("REPORT_OUT_OF_SCOPE")
    if "shell" in lowered or "path" in lowered:
        scope_flags.append("REPORT_SHELL_PATH")

    inconsistent = False
    if pytest_result.exit_code != 0 and "pass" in lowered:
        inconsistent = True
    if call_chain.dual_implementation_detected and (
        "single helper" in lowered or "unified helper" in lowered or "shared helper" in lowered
    ):
        inconsistent = True
    if any(f.rule_id in {"FILE_SCOPE", "SHELL_PATH_TOUCH"} for f in audit_result.findings) and "in scope" in lowered:
        inconsistent = True

    return ("INCONSISTENT" if inconsistent else "CONSISTENT", tuple(scope_flags))


def _synthesize_verdict(
    *,
    audit_result: AuditResult,
    call_chain: CallChainAnalysis,
    pytest_result: PytestExecution,
    report_consistency: str,
    report_scope_flags: Sequence[str],
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    findings_by_rule = {finding.rule_id for finding in audit_result.findings}

    if audit_result.verdict == "REJECT_HARD":
        reasons.append("M3 audit returned REJECT_HARD and cannot be overridden")
        return "REJECT_HARD", reasons

    if findings_by_rule & {"FILE_SCOPE", "SHELL_PATH_TOUCH"}:
        reasons.append("Audit detected out-of-scope file or shell/PATH touches")
        return "OUT_OF_SCOPE", reasons

    if report_scope_flags:
        reasons.append("Report declares or implies out-of-scope changes")
        return "OUT_OF_SCOPE", reasons

    if pytest_result.exit_code != 0:
        reasons.append("pytest failed")
        return "FAKE_WIN", reasons

    if report_consistency == "INCONSISTENT":
        reasons.append("Report conflicts with machine evidence")
        return "FAKE_WIN", reasons

    if call_chain.dual_implementation_detected:
        reasons.append("Call-chain analysis still indicates dual implementation")
        return "FAKE_WIN", reasons

    if not call_chain.approval_ready:
        reasons.append("Call-chain analysis is insufficient to approve")
        return "FAKE_WIN", reasons

    reasons.append("M3 is non-hard, call-chain evidence is positive, and pytest passed")
    return "APPROVE_CANDIDATE", reasons
