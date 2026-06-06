from hermes_cli.review_orchestrator import (
    AutomatedReviewResult,
    CallChainAnalysis,
    CorrectionDispatch,
    PytestExecution,
    run_automated_review,
    run_self_correcting_review,
)
from hermes_cli.safe_refactor_audit import AuditFinding, AuditResult


def _call_chain(*, approval_ready: bool, dual_implementation_detected: bool) -> CallChainAnalysis:
    return CallChainAnalysis(
        changed_python_paths=("hermes_cli/main.py", "hermes_cli/uninstall.py"),
        shared_helpers=("run_uninstall",) if approval_ready else (),
        file_to_helpers={
            "hermes_cli/main.py": ("run_uninstall",) if approval_ready else ("main_only",),
            "hermes_cli/uninstall.py": ("run_uninstall",) if approval_ready else ("uninstall_only",),
        },
        dual_implementation_detected=dual_implementation_detected,
        approval_ready=approval_ready,
        summary="stub",
    )


def _pytest_ok() -> PytestExecution:
    return PytestExecution(
        command=("pytest", "tests/hermes_cli/test_safe_refactor_audit.py"),
        exit_code=0,
        output="1 passed\n",
        summary="exit=0; 1 passed",
    )


def test_reject_hard_from_m3_blocks_later_success():
    events: list[str] = []

    def audit_fn(_diff: str) -> AuditResult:
        events.append("audit")
        return AuditResult(
            verdict="REJECT_HARD",
            findings=(AuditFinding("REJECT_HARD", "TTY_DOWNGRADE", "blocked", "hermes_cli/main.py"),),
            changed_paths=("hermes_cli/main.py",),
        )

    def call_chain_extractor(_diff: str) -> CallChainAnalysis:
        events.append("call_chain")
        return _call_chain(approval_ready=True, dual_implementation_detected=False)

    def pytest_runner(_command) -> PytestExecution:
        events.append("pytest")
        return _pytest_ok()

    def report_reader(_path):
        events.append("report")
        return "shared helper, tests passed"

    result = run_automated_review(
        "dummy diff",
        pytest_command=("pytest",),
        audit_fn=audit_fn,
        call_chain_extractor=call_chain_extractor,
        pytest_runner=pytest_runner,
        report_reader=report_reader,
    )

    assert result.verdict == "REJECT_HARD"
    assert result.stage_order == ("m3_audit", "call_chain", "pytest", "report")
    assert events == ["audit", "call_chain", "pytest", "report"]
    assert "cannot be overridden" in result.reasons[0]


def test_warn_plus_passing_tests_can_approve_candidate():
    def audit_fn(_diff: str) -> AuditResult:
        return AuditResult(
            verdict="WARN",
            findings=(AuditFinding("WARN", "HIGH_RISK_IO", "token", "hermes_cli/uninstall.py"),),
            changed_paths=("hermes_cli/main.py", "hermes_cli/uninstall.py"),
        )

    result = run_automated_review(
        "dummy diff",
        pytest_command=("pytest",),
        audit_fn=audit_fn,
        call_chain_extractor=lambda _diff: _call_chain(approval_ready=True, dual_implementation_detected=False),
        pytest_runner=lambda _command: _pytest_ok(),
        report_reader=lambda _path: "shared helper; minimal change",
    )

    assert result.verdict == "APPROVE_CANDIDATE"
    assert result.audit_result.verdict == "WARN"
    assert result.pytest.exit_code == 0


def test_call_chain_runs_before_pytest_result_is_interpreted():
    events: list[str] = []

    def audit_fn(_diff: str) -> AuditResult:
        events.append("audit")
        return AuditResult(verdict="APPROVE", findings=(), changed_paths=("hermes_cli/main.py", "hermes_cli/uninstall.py"))

    def call_chain_extractor(_diff: str) -> CallChainAnalysis:
        events.append("call_chain")
        return _call_chain(approval_ready=False, dual_implementation_detected=True)

    def pytest_runner(_command) -> PytestExecution:
        assert events == ["audit", "call_chain"]
        events.append("pytest")
        return _pytest_ok()

    result = run_automated_review(
        "dummy diff",
        pytest_command=("pytest",),
        audit_fn=audit_fn,
        call_chain_extractor=call_chain_extractor,
        pytest_runner=pytest_runner,
        report_reader=lambda _path: None,
    )

    assert result.verdict == "FAKE_WIN"
    assert events == ["audit", "call_chain", "pytest"]
    assert result.stage_order[:3] == ("m3_audit", "call_chain", "pytest")


def test_file_scope_and_shell_path_violations_surface_in_structured_output():
    diff = """
--- a/hermes_cli/profiles.py
+++ b/hermes_cli/profiles.py
@@
+export PATH=\"$HOME/.local/bin:$PATH\"\n
"""

    result = run_automated_review(
        diff,
        pytest_command=("pytest",),
        call_chain_extractor=lambda _diff: _call_chain(approval_ready=False, dual_implementation_detected=False),
        pytest_runner=lambda _command: _pytest_ok(),
        report_reader=lambda _path: None,
    )

    assert result.verdict == "OUT_OF_SCOPE"
    assert {finding.rule_id for finding in result.machine_findings} >= {"FILE_SCOPE", "SHELL_PATH_TOUCH"}
    assert result.report_considered is False


def test_two_failed_attempts_then_third_success_returns_approve_candidate_with_history():
    reviews = [
        AutomatedReviewResult(
            verdict="REJECT_HARD",
            stage_order=("m3_audit", "call_chain", "pytest", "report"),
            reasons=("M3 audit returned REJECT_HARD and cannot be overridden",),
            audit_result=AuditResult(
                verdict="REJECT_HARD",
                findings=(AuditFinding("REJECT_HARD", "TTY_DOWNGRADE", "blocked", "hermes_cli/main.py"),),
                changed_paths=("hermes_cli/main.py",),
            ),
            call_chain=_call_chain(approval_ready=False, dual_implementation_detected=False),
            pytest=_pytest_ok(),
            report_text="attempt 1",
            report_considered=True,
            report_consistency="CONSISTENT",
            report_scope_flags=(),
            machine_findings=(AuditFinding("REJECT_HARD", "TTY_DOWNGRADE", "blocked", "hermes_cli/main.py"),),
        ),
        AutomatedReviewResult(
            verdict="FAKE_WIN",
            stage_order=("m3_audit", "call_chain", "pytest", "report"),
            reasons=("Call-chain analysis is insufficient to approve",),
            audit_result=AuditResult(
                verdict="WARN",
                findings=(AuditFinding("WARN", "HIGH_RISK_IO", "token", "hermes_cli/uninstall.py"),),
                changed_paths=("hermes_cli/uninstall.py",),
            ),
            call_chain=_call_chain(approval_ready=False, dual_implementation_detected=False),
            pytest=_pytest_ok(),
            report_text="attempt 2",
            report_considered=True,
            report_consistency="CONSISTENT",
            report_scope_flags=(),
            machine_findings=(AuditFinding("WARN", "HIGH_RISK_IO", "token", "hermes_cli/uninstall.py"),),
        ),
        AutomatedReviewResult(
            verdict="APPROVE_CANDIDATE",
            stage_order=("m3_audit", "call_chain", "pytest", "report"),
            reasons=("M3 is non-hard, call-chain evidence is positive, and pytest passed",),
            audit_result=AuditResult(
                verdict="APPROVE",
                findings=(),
                changed_paths=("hermes_cli/main.py", "hermes_cli/uninstall.py"),
            ),
            call_chain=_call_chain(approval_ready=True, dual_implementation_detected=False),
            pytest=_pytest_ok(),
            report_text="attempt 3",
            report_considered=True,
            report_consistency="CONSISTENT",
            report_scope_flags=(),
            machine_findings=(),
        ),
    ]
    seen_diffs: list[str] = []
    correction_inputs: list[str] = []

    def audit_fn(diff: str) -> AuditResult:
        seen_diffs.append(diff)
        return reviews[len(seen_diffs) - 1].audit_result

    def call_chain_extractor(_diff: str) -> CallChainAnalysis:
        return reviews[len(seen_diffs) - 1].call_chain

    def pytest_runner(_command) -> PytestExecution:
        return reviews[len(seen_diffs) - 1].pytest

    def report_reader(_path):
        return reviews[len(seen_diffs) - 1].report_text

    def correction_dispatcher(attempt_number: int, review_result: AutomatedReviewResult, instructions: str) -> CorrectionDispatch:
        correction_inputs.append(instructions)
        assert review_result == reviews[attempt_number - 1]
        return CorrectionDispatch(diff_text=f"diff-attempt-{attempt_number + 1}", report_text=f"attempt {attempt_number + 1}")

    result = run_self_correcting_review(
        "diff-attempt-1",
        pytest_command=("pytest",),
        audit_fn=audit_fn,
        call_chain_extractor=call_chain_extractor,
        pytest_runner=pytest_runner,
        report_reader=report_reader,
        correction_dispatcher=correction_dispatcher,
    )

    assert result.verdict == "APPROVE_CANDIDATE"
    assert [attempt.review_result.verdict for attempt in result.attempts] == ["REJECT_HARD", "FAKE_WIN", "APPROVE_CANDIDATE"]
    assert seen_diffs == ["diff-attempt-1", "diff-attempt-2", "diff-attempt-3"]
    assert len(result.correction_history) == 2
    assert "TTY_DOWNGRADE" in result.correction_history[0]
    assert "HIGH_RISK_IO" in result.correction_history[1]
    assert correction_inputs == list(result.correction_history)
    assert result.stopped_after_max_attempts is False


def test_three_failed_attempts_stop_with_failure_verdict():
    diff_counter = {"count": 0}

    def audit_fn(_diff: str) -> AuditResult:
        diff_counter["count"] += 1
        if diff_counter["count"] == 1:
            return AuditResult(
                verdict="WARN",
                findings=(AuditFinding("WARN", "HIGH_RISK_IO", "token", "hermes_cli/uninstall.py"),),
                changed_paths=("hermes_cli/uninstall.py",),
            )
        return AuditResult(
            verdict="REJECT_HARD",
            findings=(AuditFinding("REJECT_HARD", "TTY_DOWNGRADE", "blocked", "hermes_cli/main.py"),),
            changed_paths=("hermes_cli/main.py",),
        )

    def correction_dispatcher(attempt_number: int, _review_result: AutomatedReviewResult, _instructions: str) -> CorrectionDispatch:
        return CorrectionDispatch(diff_text=f"retry-{attempt_number + 1}")

    result = run_self_correcting_review(
        "retry-1",
        pytest_command=("pytest",),
        audit_fn=audit_fn,
        call_chain_extractor=lambda _diff: _call_chain(approval_ready=False, dual_implementation_detected=False),
        pytest_runner=lambda _command: _pytest_ok(),
        report_reader=lambda _path: None,
        correction_dispatcher=correction_dispatcher,
    )

    assert result.verdict == "REJECT_HARD"
    assert len(result.attempts) == 3
    assert [attempt.review_result.audit_result.verdict for attempt in result.attempts] == ["WARN", "REJECT_HARD", "REJECT_HARD"]
    assert len(result.correction_history) == 2
    assert result.stopped_after_max_attempts is True


def test_help_text_only_diff_still_outputs_fake_win():
    diff = """
--- a/hermes_cli/main.py
+++ b/hermes_cli/main.py
@@
-        help="Run hermes uninstall"
+        help="Run hermes uninstall safely"
"""

    result = run_automated_review(
        diff,
        pytest_command=("pytest",),
        call_chain_extractor=lambda _diff: _call_chain(approval_ready=False, dual_implementation_detected=False),
        pytest_runner=lambda _command: _pytest_ok(),
        report_reader=lambda _path: "help text only",
    )

    assert result.verdict == "FAKE_WIN"
    assert result.audit_result.verdict == "WARN"
    assert {finding.rule_id for finding in result.audit_result.findings} == {"CONTRACT_CONSISTENCY"}
