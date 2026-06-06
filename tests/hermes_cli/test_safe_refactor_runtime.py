from pathlib import Path

from hermes_cli.human_gate_controller import HumanGateDecision
from hermes_cli.review_orchestrator import (
    AutomatedReviewResult,
    CallChainAnalysis,
    PytestExecution,
    ReviewAttempt,
    SelfCorrectionReviewResult,
)
from hermes_cli.safe_refactor_audit import AuditFinding, AuditResult
from hermes_cli.safe_refactor_runtime import (
    BattleDocumentPaths,
    discover_battle_document_paths,
    launch_safe_refactor_from_tracker,
    restore_or_create_battle_documents,
    run_safe_refactor_pipeline,
    select_active_battle,
)


TASK_CONTRACT_TEXT = """## Task Contract（任务合同）

**Objective (目标)**  
完成 AR-1 第二刀：从账本接管战役并自动串起 M3 -> M5 -> M6 的一键启动总控链。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只处理一键启动入口、战时文档恢复、M3 / M5 / M6 接线。  
OUT: 不吸入归档同步器，不改 M3 审计规则，不削弱 M6 物理停机。  
WATCHOUTS: 不得绕过 `APPROVE_CANDIDATE -> M6` 的唯一入口。

**Inputs (输入)**  
- `docs/exec-plans/tech-debt-tracker.md`
- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`
- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`
- `docs/exec-plans/completed/ar-1-engineering-wiring-acceptance-report.md`

**Deliverables / Evidence (交付物 / 证据)**  
交付物：一键启动入口、自动恢复战时文档、M3 / M5 / M6 接线、归档同步器。  
证据：账本接管成功、战时文档回写、只有 `APPROVE_CANDIDATE` 才进入 M6；只有 `approved=true` 才生成 acceptance report 并更新 tracker。

**Done (完成标准)**  
能从账本接管战役并自动恢复战时文档；只有 `APPROVE_CANDIDATE` 才进入 M6；只有 `approved=true` 才归档平账；未达条件时停在 M5-v2 或等待/拒绝态。
"""

STATUS_LEDGER_TEXT = """**Task Contract Snapshot (合同快照)**
- 目标：完成 AR-1 第二刀：从账本接管战役并自动串起 M3 -> M5 -> M6 的一键启动总控链。
- 范围边界：只处理一键启动入口、战时文档恢复、M3 / M5 / M6 接线；不吸入归档同步器。
- 完成标准：能从账本接管战役并自动恢复战时文档；只有 `APPROVE_CANDIDATE` 才进入 M6；未达条件时停在 M5-v2。

**Current State (当前状态)**
- 当前停点：待自动接管。
- 已完成：任务合同已恢复。
- 未完成 / 当前阻塞：尚未运行一键启动总控链。
- 当前判断：未完成

**Evidence Logged (证据登记)**
- 已有证据：已有任务合同。
- 证据对应结论：可以进入 safe-refactor-loop。
- 证据缺口：缺少自动回写与 M6 停机证据。

**Next Handoff (下一步 / 接管指令)**
- 接手后第一步：运行 safe-refactor-loop。
- 立即核查：确认 M6 仍保留物理停机。
- 若受阻先排查：先查战时文档路径是否存在。
"""

VERIFICATION_CHAIN_TEXT = """## Verification Chain（默认验证链）

**Verification Target (验证目标)**
- 对应合同项：对应 AR-1 第二刀交付物 / 证据与完成标准。
- 目标 1：证明入口能从账本选择当前可接管战役。
- 目标 2：证明系统能恢复战时文档。
- 目标 3：证明只有 `APPROVE_CANDIDATE` 才进入 M6。

**Verification Actions (验证动作)**
- 动作 1：运行 safe-refactor-loop 一键启动入口。
- 动作 2：检查状态台账、验证链写回内容。
- 动作 3：核对未达 `APPROVE_CANDIDATE` 时没有进入 M6。

**Verification Result (验证结果)**
- 目标 1：未执行 —— 等待流水线结果。
- 目标 2：未执行 —— 等待流水线结果。
- 目标 3：未执行 —— 等待流水线结果。

**Release / Handoff Gate (放行 / 接管闸门)**
- 当前判断：验证中
- 当前缺口：缺少一键启动链真实运行证据。
- 接手后第一步：从账本接管战役。
- 接手入口：先看任务合同、状态台账、验证链。
"""

TRACKER_TEXT = """# Tech Debt Tracker / 代码层收敛任务候选清单

## 架构级升维战役

### AR-1：`safe-refactor-loop` 自动化防爆重构 Skill / 调度器
- **状态**：最高优先级活跃战役
- **自动接管入口**：`docs/exec-plans/in-progress/ar-1-engineering-wiring-task-contract.md`
- **目标**：将当前成功的人类主控流程固化为可执行状态机。
- **当前重点**：AR-1 第三刀：归档同步器。

### TDB-9：普通技术债
- **状态**：等待自动化接管
- **自动接管入口**：`docs/exec-plans/in-progress/tdb-9-task-contract.md`
- **目标**：等待后续处理。
"""


def _review_result(
    *,
    verdict: str,
    audit_verdict: str,
    approval_ready: bool,
    dual_implementation_detected: bool = False,
) -> AutomatedReviewResult:
    reasons = {
        "APPROVE_CANDIDATE": ("M3 is non-hard, call-chain evidence is positive, and pytest passed",),
        "REJECT_HARD": ("M3 audit returned REJECT_HARD and cannot be overridden",),
        "FAKE_WIN": ("Call-chain analysis is insufficient to approve",),
        "WARN": ("M5-v2 returned WARN and must stay in self-healing loop",),
    }[verdict]
    return AutomatedReviewResult(
        verdict=verdict,
        stage_order=("m3_audit", "call_chain", "pytest", "report"),
        reasons=reasons,
        audit_result=AuditResult(
            verdict=audit_verdict,
            findings=() if audit_verdict == "APPROVE" else (AuditFinding(audit_verdict, "RULE", "blocked", "hermes_cli/main.py"),),
            changed_paths=("hermes_cli/main.py", "hermes_cli/uninstall.py"),
        ),
        call_chain=CallChainAnalysis(
            changed_python_paths=("hermes_cli/main.py", "hermes_cli/uninstall.py"),
            shared_helpers=("run_uninstall",) if approval_ready else (),
            file_to_helpers={
                "hermes_cli/main.py": ("run_uninstall",) if approval_ready else ("main_only",),
                "hermes_cli/uninstall.py": ("run_uninstall",) if approval_ready else ("uninstall_only",),
            },
            dual_implementation_detected=dual_implementation_detected,
            approval_ready=approval_ready,
            summary="stub",
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


def _self_correcting_result(final_review: AutomatedReviewResult, *, attempts: int, stopped_after_max_attempts: bool) -> SelfCorrectionReviewResult:
    review_attempts = tuple(
        ReviewAttempt(
            attempt_number=index,
            review_result=final_review,
            correction_instructions=None,
        )
        for index in range(1, attempts + 1)
    )
    return SelfCorrectionReviewResult(
        verdict=final_review.verdict,
        final_review=final_review,
        attempts=review_attempts,
        correction_history=(),
        stopped_after_max_attempts=stopped_after_max_attempts,
    )


def _write_battle_docs(root: Path) -> BattleDocumentPaths:
    paths = BattleDocumentPaths(
        tracker_path=root / "docs/exec-plans/tech-debt-tracker.md",
        task_contract_path=root / "docs/exec-plans/in-progress/ar-1-engineering-wiring-task-contract.md",
        status_ledger_path=root / "docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md",
        verification_chain_path=root / "docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md",
        archive_report_path=root / "docs/exec-plans/completed/ar-1-engineering-wiring-acceptance-report.md",
        battle_name="AR-1",
    )
    paths.tracker_path.parent.mkdir(parents=True, exist_ok=True)
    paths.task_contract_path.parent.mkdir(parents=True, exist_ok=True)
    paths.status_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    paths.verification_chain_path.parent.mkdir(parents=True, exist_ok=True)
    paths.archive_report_path.parent.mkdir(parents=True, exist_ok=True)
    paths.tracker_path.write_text(TRACKER_TEXT, encoding="utf-8")
    paths.task_contract_path.write_text(TASK_CONTRACT_TEXT, encoding="utf-8")
    paths.status_ledger_path.write_text(STATUS_LEDGER_TEXT, encoding="utf-8")
    paths.verification_chain_path.write_text(VERIFICATION_CHAIN_TEXT, encoding="utf-8")
    return paths


def test_restore_or_create_battle_documents_rebuilds_missing_ledgers(tmp_path):
    paths = _write_battle_docs(tmp_path)
    paths.status_ledger_path.unlink()
    paths.verification_chain_path.unlink()

    restored = restore_or_create_battle_documents(paths)

    assert paths.task_contract_path.exists()
    assert paths.status_ledger_path.exists()
    assert paths.verification_chain_path.exists()
    assert restored["status_ledger"].startswith("**Task Contract Snapshot (合同快照)**")
    assert restored["verification_chain"].startswith("## Verification Chain（默认验证链）")


def test_restore_or_create_battle_documents_requires_existing_task_contract(tmp_path):
    paths = _write_battle_docs(tmp_path)
    paths.task_contract_path.unlink()

    try:
        restore_or_create_battle_documents(paths)
    except FileNotFoundError as exc:
        assert str(paths.task_contract_path) in str(exc)
    else:
        raise AssertionError("缺少任务合同时必须直接失败，不能静默补造默认合同")


def test_discover_battle_document_paths_uses_tracker_and_contract_refs(tmp_path):
    paths = _write_battle_docs(tmp_path)

    resolved = discover_battle_document_paths(paths.tracker_path)

    assert resolved.battle_name == "AR-1"
    assert resolved.task_contract_path == paths.task_contract_path
    assert resolved.status_ledger_path == paths.status_ledger_path
    assert resolved.verification_chain_path == paths.verification_chain_path
    assert resolved.archive_report_path == paths.archive_report_path


def test_discover_battle_document_paths_fails_closed_without_explicit_contract_path(tmp_path):
    paths = _write_battle_docs(tmp_path)
    paths.tracker_path.write_text(
        TRACKER_TEXT.replace(
            "- **自动接管入口**：`docs/exec-plans/in-progress/ar-1-engineering-wiring-task-contract.md`\n",
            "",
        ),
        encoding="utf-8",
    )

    try:
        discover_battle_document_paths(paths.tracker_path)
    except ValueError as exc:
        assert "显式任务合同路径" in str(exc)
    else:
        raise AssertionError("账本缺少显式任务合同路径时必须 fail-closed")


def test_discover_battle_document_paths_fails_closed_without_contract_doc_refs(tmp_path):
    paths = _write_battle_docs(tmp_path)
    paths.task_contract_path.write_text(
        TASK_CONTRACT_TEXT.replace(
            "- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`\n- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`\n",
            "",
        ),
        encoding="utf-8",
    )

    try:
        discover_battle_document_paths(paths.tracker_path)
    except ValueError as exc:
        assert "状态台账" in str(exc)
    else:
        raise AssertionError("任务合同缺少战时文档路径时必须 fail-closed")


def test_pipeline_writes_back_war_docs_and_enters_m6_only_on_approve_candidate(tmp_path):
    paths = _write_battle_docs(tmp_path)
    gate_calls: list[str] = []

    result = run_safe_refactor_pipeline(
        paths,
        diff_text="safe diff",
        review_runner=lambda **_kwargs: _self_correcting_result(
            _review_result(verdict="APPROVE_CANDIDATE", audit_verdict="APPROVE", approval_ready=True),
            attempts=2,
            stopped_after_max_attempts=False,
        ),
        human_gate=lambda review: gate_calls.append(review.verdict) or HumanGateDecision(
            approved=False,
            response="",
            prompt_text="《北冥裁决请示书》",
        ),
        allow_test_gate_override=True,
    )

    status_text = paths.status_ledger_path.read_text(encoding="utf-8")
    verification_text = paths.verification_chain_path.read_text(encoding="utf-8")

    assert result.review_result.verdict == "APPROVE_CANDIDATE"
    assert result.entered_m6 is True
    assert result.stopped_in_m5 is False
    assert result.attempts_used == 2
    assert gate_calls == ["APPROVE_CANDIDATE"]
    assert "M6 已停机等待北冥签字" in status_text
    assert "entered_m6=yes" in status_text
    assert "目标 3：通过" in verification_text
    assert "目标 4：缺证据" in verification_text
    assert "当前判断：验证中" in verification_text


def test_pipeline_stops_in_m5_after_three_attempts_and_never_enters_m6(tmp_path):
    paths = _write_battle_docs(tmp_path)
    gate_calls: list[str] = []

    result = run_safe_refactor_pipeline(
        paths,
        diff_text="unsafe diff",
        review_runner=lambda **_kwargs: _self_correcting_result(
            _review_result(verdict="REJECT_HARD", audit_verdict="REJECT_HARD", approval_ready=False),
            attempts=3,
            stopped_after_max_attempts=True,
        ),
        human_gate=lambda review: gate_calls.append(review.verdict) or HumanGateDecision(
            approved=True,
            response="Confirm",
            prompt_text="《北冥裁决请示书》",
        ),
        allow_test_gate_override=True,
    )

    status_text = paths.status_ledger_path.read_text(encoding="utf-8")
    verification_text = paths.verification_chain_path.read_text(encoding="utf-8")

    assert result.review_result.verdict == "REJECT_HARD"
    assert result.entered_m6 is False
    assert result.stopped_in_m5 is True
    assert result.attempts_used == 3
    assert gate_calls == []
    assert "M5-v2 自愈循环达到 3 次上限后停机" in status_text
    assert "entered_m6=no" in status_text
    assert "目标 3：不通过" in verification_text
    assert "当前判断：不通过" in verification_text


def test_warn_and_fake_win_never_enter_m6(tmp_path):
    for verdict, audit_verdict in [("WARN", "WARN"), ("FAKE_WIN", "WARN")]:
        root = tmp_path / verdict.lower()
        paths = _write_battle_docs(root)

        def review_runner(**_kwargs):
            return _self_correcting_result(
                _review_result(verdict=verdict, audit_verdict=audit_verdict, approval_ready=False),
                attempts=1,
                stopped_after_max_attempts=False,
            )

        result = run_safe_refactor_pipeline(
            paths,
            diff_text=f"{verdict} diff",
            review_runner=review_runner,
            human_gate=lambda _review: HumanGateDecision(
                approved=True,
                response="Confirm",
                prompt_text="《北冥裁决请示书》",
            ),
            allow_test_gate_override=True,
        )

        assert result.entered_m6 is False
        assert result.stopped_in_m5 is True


def test_human_gate_override_requires_explicit_test_flag(tmp_path):
    paths = _write_battle_docs(tmp_path)

    try:
        run_safe_refactor_pipeline(
            paths,
            diff_text="safe diff",
            review_runner=lambda **_kwargs: _self_correcting_result(
                _review_result(verdict="APPROVE_CANDIDATE", audit_verdict="APPROVE", approval_ready=True),
                attempts=1,
                stopped_after_max_attempts=False,
            ),
            human_gate=lambda _review: HumanGateDecision(
                approved=True,
                response="Confirm",
                prompt_text="《北冥裁决请示书》",
            ),
        )
    except ValueError as exc:
        assert "allow_test_gate_override" in str(exc)
    else:
        raise AssertionError("未显式允许时，不应接受注入式 human_gate 覆盖真实审批")


def test_launch_safe_refactor_from_tracker_selects_active_battle_and_runs_pipeline(tmp_path):
    paths = _write_battle_docs(tmp_path)
    launch_calls: list[str] = []

    result = launch_safe_refactor_from_tracker(
        tracker_path=paths.tracker_path,
        diff_text="safe diff",
        pipeline_runner=lambda chosen_paths, **_kwargs: launch_calls.append(chosen_paths.battle_name) or {
            "battle_name": chosen_paths.battle_name,
            "entered_m6": True,
        },
    )

    assert select_active_battle(paths.tracker_path.read_text(encoding="utf-8")) == "AR-1"
    assert launch_calls == ["AR-1"]
    assert result["entered_m6"] is True
    assert result["battle_name"] == "AR-1"


def test_select_active_battle_falls_back_to_waiting_automation_takeover():
    tracker_text = """# tracker

### TDB-9：普通技术债
- **状态**：等待自动化接管
- **自动接管入口**：`docs/exec-plans/in-progress/tdb-9-task-contract.md`
- **目标**：先放着
"""

    assert select_active_battle(tracker_text) == "TDB-9"



def test_pipeline_archives_after_explicit_human_approval(tmp_path):
    paths = _write_battle_docs(tmp_path)

    result = run_safe_refactor_pipeline(
        paths,
        diff_text="safe diff",
        review_runner=lambda **_kwargs: _self_correcting_result(
            _review_result(verdict="APPROVE_CANDIDATE", audit_verdict="APPROVE", approval_ready=True),
            attempts=2,
            stopped_after_max_attempts=False,
        ),
        human_gate=lambda _review: HumanGateDecision(
            approved=True,
            response="Confirm",
            prompt_text="《北冥裁决请示书》",
        ),
        allow_test_gate_override=True,
    )

    acceptance_text = paths.archive_report_path.read_text(encoding="utf-8")
    tracker_text = paths.tracker_path.read_text(encoding="utf-8")
    status_text = paths.status_ledger_path.read_text(encoding="utf-8")
    verification_text = paths.verification_chain_path.read_text(encoding="utf-8")

    assert result.human_gate_decision is not None
    assert result.human_gate_decision.approved is True
    assert "# AR-1 第三刀归档同步器结案报告" in acceptance_text
    assert "- **状态**：已完成 / 已收编" in tracker_text
    assert "- **当前重点**：AR-1 已完成归档收口。" in tracker_text
    assert "归档同步已完成" in status_text
    assert "当前判断：可收口" in verification_text
    assert "目标 4：通过" in verification_text


def test_pipeline_does_not_archive_without_signature_even_if_m6_entered(tmp_path):
    paths = _write_battle_docs(tmp_path)

    result = run_safe_refactor_pipeline(
        paths,
        diff_text="safe diff",
        review_runner=lambda **_kwargs: _self_correcting_result(
            _review_result(verdict="APPROVE_CANDIDATE", audit_verdict="APPROVE", approval_ready=True),
            attempts=1,
            stopped_after_max_attempts=False,
        ),
        human_gate=lambda _review: HumanGateDecision(
            approved=False,
            response="",
            prompt_text="《北冥裁决请示书》",
        ),
        allow_test_gate_override=True,
    )

    tracker_text = paths.tracker_path.read_text(encoding="utf-8")
    status_text = paths.status_ledger_path.read_text(encoding="utf-8")
    verification_text = paths.verification_chain_path.read_text(encoding="utf-8")

    assert result.human_gate_decision is not None
    assert result.human_gate_decision.approved is False
    assert paths.archive_report_path.exists() is False
    assert "- **状态**：最高优先级活跃战役" in tracker_text
    assert "等待北冥签字" in status_text
    assert "当前判断：验证中" in verification_text
    assert "目标 4：缺证据" in verification_text


def test_pipeline_does_not_archive_after_explicit_rejection(tmp_path):
    paths = _write_battle_docs(tmp_path)

    result = run_safe_refactor_pipeline(
        paths,
        diff_text="safe diff",
        review_runner=lambda **_kwargs: _self_correcting_result(
            _review_result(verdict="APPROVE_CANDIDATE", audit_verdict="APPROVE", approval_ready=True),
            attempts=1,
            stopped_after_max_attempts=False,
        ),
        human_gate=lambda _review: HumanGateDecision(
            approved=False,
            response="N",
            prompt_text="《北冥裁决请示书》",
        ),
        allow_test_gate_override=True,
    )

    tracker_text = paths.tracker_path.read_text(encoding="utf-8")
    status_text = paths.status_ledger_path.read_text(encoding="utf-8")
    verification_text = paths.verification_chain_path.read_text(encoding="utf-8")

    assert result.human_gate_decision is not None
    assert result.human_gate_decision.approved is False
    assert result.human_gate_decision.response == "N"
    assert paths.archive_report_path.exists() is False
    assert "- **状态**：最高优先级活跃战役" in tracker_text
    assert "北冥已拒绝归档" in status_text
    assert "当前判断：不通过" in verification_text
    assert "目标 4：通过" in verification_text


def test_pipeline_fails_closed_for_non_ar1_scope_without_writing_docs(tmp_path):
    paths = _write_battle_docs(tmp_path)
    original_status = paths.status_ledger_path.read_text(encoding="utf-8")
    original_verification = paths.verification_chain_path.read_text(encoding="utf-8")
    scoped_paths = BattleDocumentPaths(
        tracker_path=paths.tracker_path,
        task_contract_path=paths.task_contract_path,
        status_ledger_path=paths.status_ledger_path,
        verification_chain_path=paths.verification_chain_path,
        archive_report_path=paths.archive_report_path,
        battle_name="TDB-9",
    )

    try:
        run_safe_refactor_pipeline(
            scoped_paths,
            diff_text="safe diff",
            review_runner=lambda **_kwargs: _self_correcting_result(
                _review_result(verdict="APPROVE_CANDIDATE", audit_verdict="APPROVE", approval_ready=True),
                attempts=1,
                stopped_after_max_attempts=False,
            ),
            human_gate=lambda _review: HumanGateDecision(
                approved=True,
                response="Confirm",
                prompt_text="《北冥裁决请示书》",
            ),
            allow_test_gate_override=True,
        )
    except ValueError as exc:
        assert "只允许服务 AR-1" in str(exc)
    else:
        raise AssertionError("第三刀当前应对非 AR-1 直接 fail-closed")

    assert paths.status_ledger_path.read_text(encoding="utf-8") == original_status
    assert paths.verification_chain_path.read_text(encoding="utf-8") == original_verification
    assert paths.archive_report_path.exists() is False


def test_discover_battle_document_paths_rejects_escape_from_repo_docs(tmp_path):
    paths = _write_battle_docs(tmp_path)
    paths.task_contract_path.write_text(
        TASK_CONTRACT_TEXT.replace(
            "`docs/exec-plans/completed/ar-1-engineering-wiring-acceptance-report.md`",
            "`../docs/exec-plans/completed/ar-1-engineering-wiring-acceptance-report.md`",
        ),
        encoding="utf-8",
    )

    try:
        discover_battle_document_paths(paths.tracker_path)
    except ValueError as exc:
        assert "repo 内 docs/ 下" in str(exc)
    else:
        raise AssertionError("路径越界时必须 fail-closed")


def test_pipeline_rejects_direct_battle_document_paths_outside_repo_docs(tmp_path):
    paths = _write_battle_docs(tmp_path)
    outside_report = tmp_path / "outside" / "acceptance-report.md"
    outside_report.parent.mkdir(parents=True, exist_ok=True)
    scoped_paths = BattleDocumentPaths(
        tracker_path=paths.tracker_path,
        task_contract_path=paths.task_contract_path,
        status_ledger_path=paths.status_ledger_path,
        verification_chain_path=paths.verification_chain_path,
        archive_report_path=outside_report,
        battle_name="AR-1",
    )

    try:
        run_safe_refactor_pipeline(
            scoped_paths,
            diff_text="safe diff",
            review_runner=lambda **_kwargs: _self_correcting_result(
                _review_result(verdict="APPROVE_CANDIDATE", audit_verdict="APPROVE", approval_ready=True),
                attempts=1,
                stopped_after_max_attempts=False,
            ),
            human_gate=lambda _review: HumanGateDecision(
                approved=True,
                response="Confirm",
                prompt_text="《北冥裁决请示书》",
            ),
            allow_test_gate_override=True,
        )
    except ValueError as exc:
        assert "repo docs 外部" in str(exc)
    else:
        raise AssertionError("直接注入越界 BattleDocumentPaths 时必须 fail-closed")

    assert outside_report.exists() is False


def test_pipeline_treats_unknown_nonapproval_input_as_waiting_not_rejected(tmp_path):
    paths = _write_battle_docs(tmp_path)

    result = run_safe_refactor_pipeline(
        paths,
        diff_text="safe diff",
        review_runner=lambda **_kwargs: _self_correcting_result(
            _review_result(verdict="APPROVE_CANDIDATE", audit_verdict="APPROVE", approval_ready=True),
            attempts=1,
            stopped_after_max_attempts=False,
        ),
        human_gate=lambda _review: HumanGateDecision(
            approved=False,
            response="maybe",
            prompt_text="《北冥裁决请示书》",
        ),
        allow_test_gate_override=True,
    )

    status_text = paths.status_ledger_path.read_text(encoding="utf-8")
    verification_text = paths.verification_chain_path.read_text(encoding="utf-8")

    assert result.human_gate_decision is not None
    assert result.human_gate_decision.response == "maybe"
    assert paths.archive_report_path.exists() is False
    assert "等待北冥签字" in status_text
    assert "北冥已拒绝归档" not in status_text
    assert "目标 4：缺证据" in verification_text
    assert "当前判断：验证中" in verification_text
