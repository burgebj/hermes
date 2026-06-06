from hermes_cli.human_gate_controller import HumanGateController, build_approval_request
from hermes_cli.review_orchestrator import AutomatedReviewResult, CallChainAnalysis, PytestExecution
from hermes_cli.safe_refactor_audit import AuditResult


def _review_result() -> AutomatedReviewResult:
    return AutomatedReviewResult(
        verdict="APPROVE_CANDIDATE",
        stage_order=("m3_audit", "call_chain", "pytest", "report"),
        reasons=("M3 is non-hard, call-chain evidence is positive, and pytest passed",),
        audit_result=AuditResult(
            verdict="APPROVE",
            findings=(),
            changed_paths=("hermes_cli/main.py", "hermes_cli/uninstall.py"),
        ),
        call_chain=CallChainAnalysis(
            changed_python_paths=("hermes_cli/main.py", "hermes_cli/uninstall.py"),
            shared_helpers=("run_uninstall",),
            file_to_helpers={
                "hermes_cli/main.py": ("run_uninstall",),
                "hermes_cli/uninstall.py": ("run_uninstall",),
            },
            dual_implementation_detected=False,
            approval_ready=True,
            summary="Shared helper reuse detected: run_uninstall",
        ),
        pytest=PytestExecution(
            command=("pytest",),
            exit_code=0,
            output="1 passed\n",
            summary="exit=0; 1 passed",
        ),
        report_text="all good",
        report_considered=True,
        report_consistency="CONSISTENT",
        report_scope_flags=(),
        machine_findings=(),
    )


def test_m6_accepts_explicit_y_or_confirm_and_prints_compact_request(capsys):
    prompts: list[str] = []
    controller_y = HumanGateController(input_fn=lambda prompt: prompts.append(prompt) or "Y")
    decision_y = controller_y.require_explicit_approval(_review_result())
    out_y = capsys.readouterr().out

    assert decision_y.approved is True
    assert prompts == ["北冥是否批准进入下一步？[Y/Confirm]: "]
    assert "《北冥裁决请示书》" in out_y
    assert "当前裁决: APPROVE_CANDIDATE" in out_y
    assert "pytest: exit=0" in out_y

    controller_confirm = HumanGateController(input_fn=lambda _prompt: "Confirm")
    decision_confirm = controller_confirm.require_explicit_approval(_review_result())

    assert decision_confirm.approved is True
    assert build_approval_request(_review_result()).startswith("《北冥裁决请示书》")


def test_m6_rejects_non_explicit_inputs():
    controller = HumanGateController(input_fn=lambda _prompt: "yes")
    decision = controller.require_explicit_approval(_review_result())

    assert decision.approved is False
    assert decision.response == "yes"
