from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

from hermes_cli.human_gate_controller import HumanGateDecision, HumanGateController
from hermes_cli.review_orchestrator import run_self_correcting_review


_TRACKER_SECTION_RE = re.compile(r"(?ms)^###\s+([^\n]+)\n(.*?)(?=^###\s+|\Z)")
_STATUS_LINE_RE = re.compile(r"^- \*\*状态\*\*：(.*)$", re.M)
_MARKDOWN_PATH_RE = re.compile(r"`((?:docs|\.\.?/docs)/[^`]+\.md)`")
_AR1_TRACKER_HEADER = "AR-1：`safe-refactor-loop` 自动化防爆重构 Skill / 调度器"
_REJECTION_TOKENS = {"n", "no", "reject", "rejected", "deny", "denied"}


@dataclass(frozen=True)
class TrackerBattle:
    battle_name: str
    heading_suffix: str
    status_text: str
    body: str


@dataclass(frozen=True)
class BattleDocumentPaths:
    tracker_path: Path
    task_contract_path: Path
    status_ledger_path: Path
    verification_chain_path: Path
    archive_report_path: Path
    battle_name: str


@dataclass(frozen=True)
class SafeRefactorRuntimeResult:
    battle_name: str
    review_result: Any
    human_gate_decision: HumanGateDecision | None
    entered_m6: bool
    attempts_used: int
    stopped_in_m5: bool


def select_active_battle(tracker_text: str) -> str:
    return select_active_battle_entry(tracker_text).battle_name


def select_active_battle_entry(tracker_text: str) -> TrackerBattle:
    waiting_battle: TrackerBattle | None = None

    for header, body in _TRACKER_SECTION_RE.findall(tracker_text):
        battle_name, heading_suffix = _split_battle_header(header)
        status_match = _STATUS_LINE_RE.search(body)
        if not status_match:
            continue
        status_text = status_match.group(1).strip()
        battle = TrackerBattle(
            battle_name=battle_name,
            heading_suffix=heading_suffix,
            status_text=status_text,
            body=body,
        )
        if "最高优先级活跃战役" in status_text:
            return battle
        if waiting_battle is None and "等待自动化接管" in status_text:
            waiting_battle = battle

    if waiting_battle is not None:
        return waiting_battle
    raise ValueError("未在账本中找到可接管战役")


def discover_battle_document_paths(
    tracker_path: str | Path,
    *,
    battle_entry: TrackerBattle | None = None,
    battle_name: str | None = None,
) -> BattleDocumentPaths:
    tracker = Path(tracker_path)
    tracker_text = tracker.read_text(encoding="utf-8")
    entry = battle_entry or _resolve_tracker_battle_entry(tracker_text, battle_name)

    task_contract_path = _resolve_task_contract_path(tracker=tracker, battle_entry=entry)
    if not task_contract_path.exists():
        raise FileNotFoundError(f"账本指定的任务合同不存在：{task_contract_path}")

    task_contract_text = task_contract_path.read_text(encoding="utf-8")
    status_ledger_path = _resolve_document_path_from_contract(
        tracker=tracker,
        task_contract_text=task_contract_text,
        suffix="status-ledger.md",
        label="状态台账",
    )
    verification_chain_path = _resolve_document_path_from_contract(
        tracker=tracker,
        task_contract_text=task_contract_text,
        suffix="verification-chain.md",
        label="验证链",
    )
    archive_report_path = _resolve_document_path_from_contract(
        tracker=tracker,
        task_contract_text=task_contract_text,
        suffix="acceptance-report.md",
        label="归档结案报告",
    )

    return BattleDocumentPaths(
        tracker_path=tracker,
        task_contract_path=task_contract_path,
        status_ledger_path=status_ledger_path,
        verification_chain_path=verification_chain_path,
        archive_report_path=archive_report_path,
        battle_name=entry.battle_name,
    )


def restore_or_create_battle_documents(paths: BattleDocumentPaths) -> dict[str, str]:
    if not paths.task_contract_path.exists():
        raise FileNotFoundError(f"缺少任务合同，不能自动补造：{paths.task_contract_path}")
    task_contract = paths.task_contract_path.read_text(encoding="utf-8")
    status_ledger = _read_or_create(
        paths.status_ledger_path,
        _default_status_ledger(paths.battle_name, task_contract),
    )
    verification_chain = _read_or_create(
        paths.verification_chain_path,
        _default_verification_chain(paths.battle_name),
    )
    return {
        "task_contract": task_contract,
        "status_ledger": status_ledger,
        "verification_chain": verification_chain,
    }


def run_safe_refactor_pipeline(
    paths: BattleDocumentPaths,
    *,
    diff_text: str,
    review_runner: Callable[..., Any] = run_self_correcting_review,
    human_gate: Callable[[Any], HumanGateDecision] | None = None,
    allow_test_gate_override: bool = False,
    **review_kwargs: Any,
) -> SafeRefactorRuntimeResult:
    _assert_archive_scope(paths)
    _assert_paths_within_repo_docs(paths)
    docs = restore_or_create_battle_documents(paths)
    review_result = review_runner(diff_text=diff_text, **review_kwargs)
    final_review = getattr(review_result, "final_review", review_result)
    attempts_used = len(getattr(review_result, "attempts", ())) or 1
    stopped_after_max_attempts = bool(getattr(review_result, "stopped_after_max_attempts", False))
    entered_m6 = final_review.verdict == "APPROVE_CANDIDATE"

    human_gate_decision: HumanGateDecision | None = None
    if entered_m6:
        if human_gate is not None and not allow_test_gate_override:
            raise ValueError("注入式 human_gate 仅允许用于测试；如确需覆盖，请显式传入 allow_test_gate_override=True")
        if human_gate is None:
            controller = HumanGateController()
            human_gate = controller.require_explicit_approval
        human_gate_decision = human_gate(final_review)

    archive_synced = False
    if _should_archive(entered_m6=entered_m6, human_gate_decision=human_gate_decision):
        _assert_archive_scope(paths)
        _write_acceptance_report(
            paths.archive_report_path,
            battle_name=paths.battle_name,
            objective_line=_extract_objective_line(docs["task_contract"]),
            review_verdict=final_review.verdict,
            attempts_used=attempts_used,
            human_gate_decision=human_gate_decision,
        )
        _update_tracker_for_stage_closure(paths.tracker_path, battle_name=paths.battle_name)
        archive_synced = True

    _write_status_ledger(
        paths.status_ledger_path,
        battle_name=paths.battle_name,
        objective_line=_extract_objective_line(docs["task_contract"]),
        review_verdict=final_review.verdict,
        entered_m6=entered_m6,
        attempts_used=attempts_used,
        stopped_after_max_attempts=stopped_after_max_attempts,
        human_gate_decision=human_gate_decision,
        archive_synced=archive_synced,
    )
    _write_verification_chain(
        paths.verification_chain_path,
        battle_name=paths.battle_name,
        review_verdict=final_review.verdict,
        entered_m6=entered_m6,
        attempts_used=attempts_used,
        stopped_after_max_attempts=stopped_after_max_attempts,
        human_gate_decision=human_gate_decision,
        archive_synced=archive_synced,
    )

    return SafeRefactorRuntimeResult(
        battle_name=paths.battle_name,
        review_result=final_review,
        human_gate_decision=human_gate_decision,
        entered_m6=entered_m6,
        attempts_used=attempts_used,
        stopped_in_m5=not entered_m6,
    )


def launch_safe_refactor_from_tracker(
    *,
    tracker_path: str | Path,
    diff_text: str,
    pipeline_runner: Callable[..., Any] = run_safe_refactor_pipeline,
    path_resolver: Callable[..., BattleDocumentPaths] = discover_battle_document_paths,
    **pipeline_kwargs: Any,
) -> Any:
    tracker = Path(tracker_path)
    battle_entry = select_active_battle_entry(tracker.read_text(encoding="utf-8"))
    battle_paths = path_resolver(tracker, battle_entry=battle_entry)
    return pipeline_runner(battle_paths, diff_text=diff_text, **pipeline_kwargs)


def _resolve_tracker_battle_entry(tracker_text: str, battle_name: str | None) -> TrackerBattle:
    if battle_name is None:
        return select_active_battle_entry(tracker_text)
    for header, body in _TRACKER_SECTION_RE.findall(tracker_text):
        current_name, heading_suffix = _split_battle_header(header)
        if current_name == battle_name:
            status_match = _STATUS_LINE_RE.search(body)
            status_text = status_match.group(1).strip() if status_match else ""
            return TrackerBattle(
                battle_name=current_name,
                heading_suffix=heading_suffix,
                status_text=status_text,
                body=body,
            )
    raise ValueError(f"账本中不存在战役：{battle_name}")


def _split_battle_header(header: str) -> tuple[str, str]:
    if "：" in header:
        battle_name, heading_suffix = header.split("：", 1)
        return battle_name.strip(), heading_suffix.strip()
    return header.strip(), ""


def _resolve_task_contract_path(*, tracker: Path, battle_entry: TrackerBattle) -> Path:
    explicit_paths = [
        _repo_relative_path(tracker, raw_path)
        for raw_path in _MARKDOWN_PATH_RE.findall(battle_entry.body)
        if raw_path.endswith("task-contract.md")
    ]
    if len(explicit_paths) == 1:
        return explicit_paths[0]
    if len(explicit_paths) > 1:
        raise ValueError(f"账本为 {battle_entry.battle_name} 指向了多个任务合同，无法自动接管")
    raise ValueError(f"账本缺少 {battle_entry.battle_name} 的显式任务合同路径，不能自动接管")


def _resolve_document_path_from_contract(
    *,
    tracker: Path,
    task_contract_text: str,
    suffix: str,
    label: str,
) -> Path:
    explicit_paths = [
        _repo_relative_path(tracker, raw_path)
        for raw_path in _MARKDOWN_PATH_RE.findall(task_contract_text)
        if raw_path.endswith(suffix)
    ]
    unique_paths = _dedupe_paths(explicit_paths)
    if len(unique_paths) == 1:
        return unique_paths[0]
    if len(unique_paths) > 1:
        raise ValueError(f"任务合同为 {label} 提供了多个候选路径，无法自动接管")
    raise ValueError(f"任务合同缺少 {label} 路径，不能自动建立或恢复现场")


def _repo_relative_path(tracker: Path, markdown_path: str) -> Path:
    normalized = markdown_path[2:] if markdown_path.startswith("./") else markdown_path
    if not normalized.startswith("docs/"):
        raise ValueError(f"文档路径必须位于 repo 内 docs/ 下，禁止越界：{markdown_path}")
    repo_root = tracker.parents[2].resolve()
    candidate = (repo_root / normalized).resolve(strict=False)
    docs_root = (repo_root / "docs").resolve(strict=False)
    try:
        candidate.relative_to(docs_root)
    except ValueError as exc:
        raise ValueError(f"文档路径必须位于 repo 内 docs/ 下，禁止越界：{markdown_path}") from exc
    return candidate


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique_paths: list[Path] = []
    for path in paths:
        resolved = path.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_paths.append(path)
    return unique_paths


def _is_explicit_rejection(response: str) -> bool:
    return response.strip().lower() in _REJECTION_TOKENS


def _approval_state(entered_m6: bool, human_gate_decision: HumanGateDecision | None) -> str:
    if not entered_m6:
        return "pre_m6"
    if human_gate_decision is None:
        return "waiting_signature"
    if human_gate_decision.approved:
        return "approved"
    if _is_explicit_rejection(human_gate_decision.response):
        return "rejected"
    return "waiting_signature"


def _should_archive(*, entered_m6: bool, human_gate_decision: HumanGateDecision | None) -> bool:
    return _approval_state(entered_m6, human_gate_decision) == "approved"


def _assert_archive_scope(paths: BattleDocumentPaths) -> None:
    if paths.battle_name != "AR-1":
        raise ValueError("第三刀归档同步器当前只允许服务 AR-1，禁止扩展到其他战役")


def _assert_paths_within_repo_docs(paths: BattleDocumentPaths) -> None:
    repo_root = paths.tracker_path.parents[2].resolve(strict=False)
    docs_root = (repo_root / "docs").resolve(strict=False)
    for current in (
        paths.tracker_path,
        paths.task_contract_path,
        paths.status_ledger_path,
        paths.verification_chain_path,
        paths.archive_report_path,
    ):
        resolved = current.resolve(strict=False)
        try:
            resolved.relative_to(docs_root)
        except ValueError as exc:
            raise ValueError(f"BattleDocumentPaths 中存在越界路径，禁止写入 repo docs 外部：{current}") from exc


def _write_acceptance_report(
    path: Path,
    *,
    battle_name: str,
    objective_line: str,
    review_verdict: str,
    attempts_used: int,
    human_gate_decision: HumanGateDecision | None,
) -> None:
    response = human_gate_decision.response if human_gate_decision is not None else ""
    text = (
        f"# {battle_name} 第三刀归档同步器结案报告\n\n"
        "## 1. 结案触发条件\n\n"
        f"- M5 最终裁决：{review_verdict}\n"
        f"- M6 人工闸门：approved={bool(human_gate_decision and human_gate_decision.approved)}\n"
        f"- 北冥签字响应：{response or '未签字'}\n"
        "- 归档放行规则：仅当 `human_gate_decision.approved == True` 时，才允许生成本报告并同步平账。\n\n"
        "## 2. 任务合同目标\n\n"
        f"- {objective_line}\n\n"
        "## 3. 自动归档产物\n\n"
        f"- acceptance report：`{path.as_posix()}`\n"
        "- tracker：已推进为“已完成 / 已收编”。\n"
        "- Status Ledger / Verification Chain：已同步回写为归档完成态。\n\n"
        "## 4. 自动归档事实\n\n"
        f"- M5 自愈尝试次数：{attempts_used}\n"
        "- 归档执行结果：已生成结案报告、已更新 tracker、已回写台账与验证链。\n"
        "- 作用范围：仅针对 AR-1 当前战役；未触碰其他技术债。\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _update_tracker_for_stage_closure(path: Path, *, battle_name: str) -> None:
    tracker_text = path.read_text(encoding="utf-8")
    replacement = (
        f"### {battle_name}：`safe-refactor-loop` 自动化防爆重构 Skill / 调度器\n"
        "- **状态**：已完成 / 已收编\n"
        "- **自动接管入口**：`docs/exec-plans/in-progress/ar-1-engineering-wiring-task-contract.md`\n"
        "- **目标**：将当前成功的人类主控流程固化为可执行状态机。\n"
        "- **当前重点**：AR-1 已完成归档收口。\n"
        "- **归档结案报告**：`docs/exec-plans/completed/ar-1-engineering-wiring-acceptance-report.md`\n"
    )
    header = re.escape(_AR1_TRACKER_HEADER if battle_name == "AR-1" else battle_name)
    pattern = re.compile(rf"(?ms)^###\s+{header}\n.*?(?=^###\s+|\Z)")
    updated, count = pattern.subn(replacement, tracker_text, count=1)
    if count != 1:
        raise ValueError(f"未在 tracker 中找到可更新的战役：{battle_name}")
    path.write_text(updated, encoding="utf-8")


def _read_or_create(path: Path, default_text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(default_text, encoding="utf-8")
        return default_text
    return path.read_text(encoding="utf-8")


def _extract_objective_line(task_contract_text: str) -> str:
    in_objective_block = False
    for line in task_contract_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("**Objective"):
            in_objective_block = True
            continue
        if in_objective_block and stripped.startswith("**"):
            break
        if in_objective_block and stripped:
            return stripped
    return "完成 AR-1 第三刀归档同步器接线。"


def _write_status_ledger(
    path: Path,
    *,
    battle_name: str,
    objective_line: str,
    review_verdict: str,
    entered_m6: bool,
    attempts_used: int,
    stopped_after_max_attempts: bool,
    human_gate_decision: HumanGateDecision | None,
    archive_synced: bool,
) -> None:
    approval_state = _approval_state(entered_m6, human_gate_decision)
    if archive_synced:
        current_stop = "归档同步已完成，AR-1 已结案 / 已收编"
        done_items = f"已从账本接管 {battle_name}，并在 M6 收到北冥显式签字后完成 acceptance report、tracker、Status Ledger、Verification Chain 的归档同步。"
        blocked_items = "无。"
        current_judgment = "可收口"
        evidence_gap = "无。"
        human_gate_text = "approved"
    elif approval_state == "waiting_signature":
        current_stop = "M6 已停机等待北冥签字"
        done_items = f"已从账本接管 {battle_name}，并真实跑通 M3 -> M5 -> M6；当前裁决为 {review_verdict}。"
        blocked_items = "等待北冥签字；未收到显式 `Y / Confirm` 前，禁止归档、禁止平账、禁止合并。"
        current_judgment = "验证中"
        evidence_gap = "缺少北冥显式 `Y / Confirm` 批准信号。"
        human_gate_text = "waiting_signature"
    elif approval_state == "rejected":
        current_stop = "M6 已收到拒绝，归档同步未触发"
        done_items = f"已从账本接管 {battle_name}，并进入 M6；北冥已明确拒绝本轮归档。"
        blocked_items = "北冥已拒绝归档，禁止写 acceptance report、禁止更新 tracker、禁止合并。"
        current_judgment = "未完成"
        evidence_gap = "北冥已明确拒绝，本轮不得平账。"
        human_gate_text = "rejected"
    else:
        retry_text = f"M5-v2 已运行 {attempts_used} 次自愈复审。"
        if stopped_after_max_attempts:
            current_stop = "M5-v2 自愈循环达到 3 次上限后停机"
        else:
            current_stop = "M5-v2 已停机，未达 APPROVE_CANDIDATE"
        done_items = f"已从账本接管 {battle_name}，并完成 M3 -> M5 自动复审；{retry_text} 最终裁决为 {review_verdict}。"
        blocked_items = "未达到 APPROVE_CANDIDATE，禁止进入 M6；更不得归档。"
        current_judgment = "未完成"
        evidence_gap = "当前仍停在 M5-v2 自愈循环或失败态，不能进入 M6。"
        human_gate_text = "not_entered"

    text = (
        "**Task Contract Snapshot (合同快照)**\n"
        f"- 目标：{objective_line}\n"
        "- 范围边界：只处理 AR-1 第三刀归档同步；不改 M3 审计逻辑，不改 M5 复审逻辑，不削弱 M6 物理闸门，不扩展到其他技术债。\n"
        "- 完成标准：只有 `human_gate_decision.approved == True` 才允许写 acceptance report、更新 tracker，并把台账/验证链回写为归档完成态。\n\n"
        "**Current State (当前状态)**\n"
        f"- 当前停点：{current_stop}\n"
        f"- 已完成：{done_items}\n"
        f"- 未完成 / 当前阻塞：{blocked_items}\n"
        f"- 当前判断：{current_judgment}\n\n"
        "**Evidence Logged (证据登记)**\n"
        f"- 已有证据：review_verdict={review_verdict}；entered_m6={'yes' if entered_m6 else 'no'}；m5_attempts={attempts_used}；human_gate={human_gate_text}；archive_synced={'yes' if archive_synced else 'no'}。\n"
        "- 证据对应结论：归档器严格以 M6 明确批准态为前提，不会在等待态或拒绝态误归档。\n"
        f"- 证据缺口：{evidence_gap}\n\n"
        "**Next Handoff (下一步 / 接管指令)**\n"
        "- 接手后第一步：先核对 human_gate、archive_synced 与 tracker / acceptance report 是否一致。\n"
        "- 立即核查：确认任何 waiting / rejected / 未进入 M6 的状态都没有写 acceptance report。\n"
        "- 若受阻先排查：先查任务合同中的 acceptance report 路径、M6 响应文本、以及 tracker 对应战役区块。\n"
    )
    path.write_text(text, encoding="utf-8")


def _write_verification_chain(
    path: Path,
    *,
    battle_name: str,
    review_verdict: str,
    entered_m6: bool,
    attempts_used: int,
    stopped_after_max_attempts: bool,
    human_gate_decision: HumanGateDecision | None,
    archive_synced: bool,
) -> None:
    approval_state = _approval_state(entered_m6, human_gate_decision)

    if archive_synced:
        result3 = "通过"
        result3_reason = "M6 已收到北冥显式 `Y / Confirm`，归档前提成立。"
        result4 = "通过"
        result4_reason = "acceptance report、tracker、Status Ledger、Verification Chain 已全部同步到完成态。"
        gate = "可收口"
        gap = "无。"
    elif approval_state == "waiting_signature":
        result3 = "通过"
        result3_reason = "系统已进入 M6，但仍严格等待北冥显式 `Y / Confirm`，未签字不会放行归档。"
        result4 = "缺证据"
        result4_reason = "当前仍缺少批准信号，因此 acceptance report 与 tracker 均未写入完成态。"
        gate = "验证中"
        gap = "缺少北冥显式 `Y / Confirm`。"
    elif approval_state == "rejected":
        result3 = "通过"
        result3_reason = "M6 已收到明确拒绝，系统未旁路人工闸门。"
        result4 = "通过"
        result4_reason = "拒绝态下未生成 acceptance report，tracker 仍保持未完成战役状态，未把等待态与拒绝态混写。"
        gate = "不通过"
        gap = "北冥已拒绝本轮归档。"
    else:
        result3 = "不通过"
        if stopped_after_max_attempts:
            result3_reason = f"M5-v2 在 {attempts_used} 次自愈后仍未得到 `APPROVE_CANDIDATE`，因此被阻断在 M5。"
        else:
            result3_reason = f"最终裁决为 {review_verdict}，不满足 `APPROVE_CANDIDATE -> M6` 的唯一入口条件。"
        result4 = "未执行"
        result4_reason = "尚未进入 M6，归档同步前提不存在。"
        gate = "不通过"
        gap = "未进入 M6，当前不得归档。"

    text = (
        "## Verification Chain（默认验证链）\n\n"
        "**Verification Target (验证目标)**\n"
        f"- 对应合同项：对应 {battle_name} 第三刀归档同步器的交付物、证据与完成标准。\n"
        "- 目标 1：证明入口仍通过 `tech-debt-tracker.md` 与任务合同恢复当前战役现场，而不是误碰无关战役。\n"
        "- 目标 2：证明归档器只消费当前战役的 Task Contract / Status Ledger / Verification Chain / acceptance report 路径契约。\n"
        "- 目标 3：证明只有 `human_gate_decision.approved == True` 或等价 M6 明确通过态成立时，才允许触发归档。\n"
        "- 目标 4：证明等待批准、已拒绝、已批准三种状态不会混写；只有批准态会平账。\n\n"
        "**Verification Actions (验证动作)**\n"
        "- 动作 1：回读 battle document path contract，确认当前只解析当前战役显式文档路径。\n"
        "- 动作 2：运行 `run_self_correcting_review()` 并仅在 `APPROVE_CANDIDATE` 时进入 M6。\n"
        "- 动作 3：分别验证批准、未签字、已拒绝三类 M6 结果下的 acceptance report / tracker / 台账 / 验证链写回结果。\n\n"
        "**Verification Result (验证结果)**\n"
        "- 目标 1：通过 —— 当前入口仍先读 tracker 与任务合同，不会把归档器变成全局清扫器。\n"
        "- 目标 2：通过 —— 归档写入仅使用当前战役显式提供的 acceptance report 路径与 battle docs 路径。\n"
        f"- 目标 3：{result3} —— {result3_reason}\n"
        f"- 目标 4：{result4} —— {result4_reason}\n\n"
        "**Release / Handoff Gate (放行 / 接管闸门)**\n"
        f"- 当前判断：{gate}\n"
        f"- 当前缺口：{gap}\n"
        "- 接手后第一步：先核对 acceptance report、tracker 与台账/验证链是否与 human_gate 状态一致。\n"
        "- 接手入口：先看任务合同、状态台账、验证链、acceptance report 与 `docs/exec-plans/tech-debt-tracker.md`。\n"
    )
    path.write_text(text, encoding="utf-8")


def _default_status_ledger(battle_name: str, task_contract_text: str) -> str:
    return (
        "**Task Contract Snapshot (合同快照)**\n"
        f"- 目标：{_extract_objective_line(task_contract_text)}\n"
        "- 范围边界：只处理 AR-1 第三刀归档同步；不扩大到其他战役。\n"
        "- 完成标准：只有北冥显式批准后才允许归档平账。\n\n"
        "**Current State (当前状态)**\n"
        "- 当前停点：待进入归档同步验证。\n"
        f"- 已完成：已确认 {battle_name} 的任务合同存在。\n"
        "- 未完成 / 当前阻塞：尚未拿到 M6 明确批准态。\n"
        "- 当前判断：未完成\n\n"
        "**Evidence Logged (证据登记)**\n"
        f"- 已有证据：已恢复 {battle_name} 任务合同。\n"
        "- 证据对应结论：可以进入第三刀归档同步验证。\n"
        "- 证据缺口：缺少 M6 批准结果与归档写回证据。\n\n"
        "**Next Handoff (下一步 / 接管指令)**\n"
        "- 接手后第一步：运行归档同步链。\n"
        "- 立即核查：确认 acceptance report 路径与 tracker 战役区块一致。\n"
        "- 若受阻先排查：先查任务合同实体是否存在。\n"
    )


def _default_verification_chain(battle_name: str) -> str:
    return (
        "## Verification Chain（默认验证链）\n\n"
        "**Verification Target (验证目标)**\n"
        f"- 对应合同项：对应 {battle_name} 第三刀归档同步器的交付物 / 证据与完成标准。\n"
        "- 目标 1：证明只有批准态才会归档。\n"
        "- 目标 2：证明拒绝态与等待态不会被混写。\n\n"
        "**Verification Actions (验证动作)**\n"
        "- 动作 1：运行到 M6。\n"
        "- 动作 2：检查 acceptance report、tracker、状态台账、验证链的写回结果。\n\n"
        "**Verification Result (验证结果)**\n"
        "- 目标 1：未执行 —— 等待流水线结果。\n"
        "- 目标 2：未执行 —— 等待流水线结果。\n\n"
        "**Release / Handoff Gate (放行 / 接管闸门)**\n"
        "- 当前判断：验证中\n"
        "- 当前缺口：缺少 M6 结果与归档写回证据。\n"
        "- 接手后第一步：从账本接管当前战役并运行到 M6。\n"
        "- 接手入口：先看任务合同、状态台账、验证链。\n"
    )
