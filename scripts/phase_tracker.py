#!/usr/bin/env python3
"""
Phase Tracker — strict multi-template phase enforcement for upstream contributions.

Usage:
    phase_tracker.py start <template> [--issue N]
    phase_tracker.py current              # show current phase
    phase_tracker.py check <N>            # exit 0 if on phase N, 1 if not
    phase_tracker.py advance --evidence "描述"  # submit evidence + advance
    phase_tracker.py skip <N>             # BLOCKED
    phase_tracker.py complete             # mark workflow done
    phase_tracker.py abort                # cancel workflow
    phase_tracker.py phases              # list templates + phases

State file: .dev-workflow/phase-tracker.json

GUARD RAILS:
  - `advance` requires --evidence describing what was done (min 20 chars)
  - Phase 1 (triage) blocks advance if competing PR was found but no decision recorded
  - All evidence is stored and auditable
"""

import json
import os
import sys

STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".dev-workflow")
STATE_FILE = os.path.join(STATE_DIR, "phase-tracker.json")

# Minimum evidence length to prevent empty/generic submissions
MIN_EVIDENCE_LENGTH = 20

TEMPLATES = {
    "github-issue": {
        "total": 13,
        "PHASES": {
            1: "triage", 2: "setup", 3: "understand", 4: "security",
            5: "implement", 6: "test", 7: "review", 8: "preflight",
            9: "pr", 10: "evolve", 11: "insight-feature-request",
            12: "plugin-improve", 13: "cleanup",
        },
        "PHASE_NAMES": {
            1:  "🔍 Deep Triage — 检查竞争 PR、评分、分类",
            2:  "🌿 Branch Setup — 同步上游、创建分支",
            3:  "📖 Code Understanding — 读代码、追踪执行路径",
            4:  "🔒 Security Baseline — 安全基线扫描",
            5:  "✏️ Implementation — 写代码（小 diff）",
            6:  "🧪 Test Suite — 全量测试 + 新增测试（必须全通过）",
            7:  "👀 Code Review — 多角色静态审查（零 ERROR）",
            8:  "✅ PR Readiness Check — 7 项预提交检查",
            9:  "🚀 Create Pull Request — 提交 + 创建 PR",
            10: "🧠 Self Evolution — 萃取经验，同步知识图谱",
            11: "💡 Insight-Driven Feature Request — 发现上游缺口",
            12: "🔧 Plugin Self-Improvement — 改进插件",
            13: "🧹 Cleanup & Handoff — 清理分支，交接",
        },
        # What must the evidence describe for each phase?
        "EVIDENCE_HINTS": {
            1:  "e.g. 'issue #N scored 6/7, no competing PR, author=X, labels=Y'",
            2:  "e.g. 'branch fix/xxx created from origin/main, fetched latest'",
            3:  "e.g. 'root cause: func X does Y instead of Z, traced via file A→B→C'",
            4:  "e.g. 'dwf_security_scan quick: 0 findings, text-only change' or 'scan clean'",
            5:  "e.g. 'modified files X, Y — +N/-M lines, syntax check passed'",
            6:  "e.g. 'N tests passed, 0 failed — new tests in test_X.py'",
            7:  "e.g. 'dwf_review_run: 0 ERROR, N WARNING — all reviewed'",
            8:  "e.g. 'attribution OK, no new competitor, diff +N/-M, 7/7 checks pass'",
            9:  "e.g. 'PR #N created: https://github.com/.../pull/N'",
            10: "e.g. 'extracted 2 patterns: provider-flag-default, conservative-fallback'",
            11: "e.g. 'no upstream gap found' or 'found gap: file X missing Y'",
            12: "e.g. 'no plugin changes needed' or 'updated pr-review-patterns.md'",
            13: "e.g. 'checked out main, branch deleted, state cleaned'",
        },
    },
    "pr-review-response": {
        "total": 12,
        "PHASES": {
            1: "scan-classify", 2: "simple-replies", 3: "worth-check",
            4: "respond", 5: "implement-fixes", 6: "test",
            7: "pre-push", 8: "commit-push", 9: "evolve",
            10: "insight-feature-request", 11: "plugin-improve", 12: "cleanup",
        },
        "PHASE_NAMES": {
            1:  "📋 Scan & Classify — 扫描所有 PR，按路线分类",
            2:  "📬 Simple Replies — 感谢/关闭重复/竞争 PR",
            3:  "💎 Worth Check — 重新评估 PR 是否值得继续",
            4:  "💬 Respond to Reviewers — 回复认可确定改动方向",
            5:  "✏️ Implement Changes — 按 reviewer 要求改代码",
            6:  "🧪 Test Suite — 全量测试（必须通过）",
            7:  "🔍 Pre-Push Re-check — 确认无新竞争/新评论",
            8:  "📤 Commit, Push & Follow-up — 推送+通知 reviewer",
            9:  "🧠 Self Evolution — 萃取经验，同步知识图谱",
            10: "💡 Insight-Driven Feature Request — 发现上游缺口",
            11: "🔧 Plugin Self-Improvement — 改进插件",
            12: "🧹 Cleanup — 清理分支，记录待处理 PR",
        },
        "EVIDENCE_HINTS": {
            1:  "e.g. 'scanned N PRs: A=RouteA, B=RouteB, C=RouteC'",
            2:  "e.g. 'closed #N (duplicate), thanked #M (cherry-pick)'",
            3:  "e.g. 'PR #N worth keeping — reviewer raised valid point'",
            4:  "e.g. 'replied to reviewer X on PR #N, agreed to fix Y'",
            5:  "e.g. 'fixed Y per reviewer feedback, +N/-M lines'",
            6:  "e.g. 'N tests passed, 0 failed'",
            7:  "e.g. 'no new comments on PR #N, no competing PRs'",
            8:  "e.g. 'pushed to PR #N, notified reviewer @X'",
            9:  "e.g. 'extracted pattern: reviewer-priority-matrix'",
            10: "e.g. 'no upstream gap found'",
            11: "e.g. 'no plugin changes needed'",
            12: "e.g. 'branch cleaned, PR status recorded'",
        },
    },
}


def _resolve(state):
    """Return the template definition dict for the current workflow."""
    tname = state.get("template", "github-issue")
    return TEMPLATES.get(tname, TEMPLATES["github-issue"])


def _load():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _now_iso():
    return __import__("datetime").datetime.now().isoformat()


def cmd_start(template, issue=None):
    existing = _load()
    if existing is not None and existing.get("state") == "active":
        print("BLOCKED: A workflow is already active. Complete or abort it first.")
        sys.exit(1)

    if template not in TEMPLATES:
        print(f"Unknown template: {template}")
        print(f"Available: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    tpl = TEMPLATES[template]
    state = {
        "template": template,
        "current_phase": 1,
        "completed_phases": [],
        "issue_number": issue,
        "started_at": _now_iso(),
        "last_advanced_at": None,
        "state": "active",
        "phase_evidence": {},  # {phase_number: {"evidence": str, "timestamp": str}}
    }
    _save(state)
    print(f"✅ Started {template} workflow. Phase 1/{tpl['total']}: {tpl['PHASE_NAMES'][1]}")
    print(f"   State: {STATE_FILE}")
    if template == "github-issue":
        print("⛔ NO-COMMENT RULE: If a competing PR exists, do NOT comment/review it.")
        print("   Only interact with PRs you (atyou2happy) authored. Complete early if competing.")
    hints = tpl.get("EVIDENCE_HINTS", {})
    print(f"\n   📝 Evidence needed to advance: {hints.get(1, 'describe what you did')}")
    print(f"   Usage: phase_tracker.py advance --evidence \"...\"")


def cmd_current():
    state = _load()
    if state is None:
        print("No active workflow.")
        return

    tpl = _resolve(state)
    cp = state["current_phase"]
    done = state["completed_phases"]
    names = tpl["PHASE_NAMES"]

    print(f"📊 Workflow: {state['template']}")
    print(f"   Issue: {state.get('issue_number', 'N/A')}")
    print(f"   State: {state['state']}")
    print(f"   Current phase: {cp}/{tpl['total']} — {names.get(cp, 'unknown')}")
    print(f"   Completed: {', '.join(str(p) for p in done) if done else 'none yet'}")

    # Show evidence for completed phases
    evidence = state.get("phase_evidence", {})
    if evidence:
        print(f"\n   📋 Evidence log:")
        for p in sorted(done):
            ev = evidence.get(str(p), {})
            text = ev.get("evidence", "?")[:80]
            print(f"      Phase {p}: {text}{'...' if len(ev.get('evidence','')) > 80 else ''}")

    if state["state"] == "active":
        hints = tpl.get("EVIDENCE_HINTS", {})
        print(f"\n⚠️  You are on Phase {cp}. Do NOT skip ahead!")
        print(f"   📝 To advance: phase_tracker.py advance --evidence \"{hints.get(cp, 'describe what you did')}\"")


def cmd_check(expected_str):
    state = _load()
    if state is None:
        print("BLOCKED: No active workflow. Call 'phase_tracker.py start <template>' first.")
        sys.exit(1)
    if state["state"] != "active":
        print(f"BLOCKED: Workflow is {state['state']} (not active).")
        sys.exit(1)

    try:
        expected = int(expected_str)
    except ValueError:
        print(f"BLOCKED: Invalid phase number: {expected_str}")
        sys.exit(1)

    tpl = _resolve(state)
    names = tpl["PHASE_NAMES"]
    current = state["current_phase"]

    if current == expected:
        print(f"✅ Phase {current}/{tpl['total']} — {names.get(current, 'unknown')}")
        hints = tpl.get("EVIDENCE_HINTS", {})
        print(f"   📝 To advance: phase_tracker.py advance --evidence \"{hints.get(current, 'describe what you did')}\"")
        sys.exit(0)
    elif current < expected:
        print(f"❌ BLOCKED: Cannot do Phase {expected} yet — you are on Phase {current} ({names.get(current, '')})")
        print(f"   Next expected: Phase {current} — {names.get(current, '')}")
        sys.exit(1)
    else:
        print(f"⚠️  Phase {expected} is already completed. You are on Phase {current}.")
        print(f"   Current: Phase {current} — {names.get(current, '')}")
        sys.exit(1)


def cmd_advance(evidence=None):
    state = _load()
    if state is None:
        print("BLOCKED: No active workflow.")
        sys.exit(1)
    if state["state"] != "active":
        print(f"BLOCKED: Workflow is {state['state']}.")
        sys.exit(1)

    tpl = _resolve(state)
    names = tpl["PHASE_NAMES"]
    total = tpl["total"]
    current = state["current_phase"]

    if current >= total:
        print(f"⚠️  Already at final phase ({current}/{total}). Call 'complete' to finish.")
        sys.exit(1)

    # ── GUARD 1: Evidence required ──────────────────────────────
    if not evidence or len(evidence.strip()) < 20:
        hints = tpl.get("EVIDENCE_HINTS", {})
        print(f"❌ BLOCKED: Evidence required to advance from Phase {current}.")
        print(f"   Phase {current}: {names.get(current, '')}")
        print(f"   Hint: {hints.get(current, 'describe what you did')}")
        print(f"   Usage: phase_tracker.py advance --evidence \"your evidence here (min 20 chars)\"")
        sys.exit(1)

    # ── GUARD 2: Phase-specific checks ──────────────────────────
    # Phase 1 triage: if competing PR found, must acknowledge decision
    if current == 1 and state.get("template") == "github-issue":
        ev_lower = evidence.lower()
        has_competitor = "compet" in ev_lower or "duplicate" in ev_lower or "already" in ev_lower
        if has_competitor and "no-comment" not in ev_lower and "did not comment" not in ev_lower:
            print("⚠️  WARNING: Competing PR detected but no explicit no-comment declaration.")
            print("   Add 'no-comment' or 'did not comment' to evidence if you found a competitor.")
            print("   ⛔ REMINDER: NEVER comment on PRs you did not author.")

    # Record evidence
    if "phase_evidence" not in state:
        state["phase_evidence"] = {}
    state["phase_evidence"][str(current)] = {
        "evidence": evidence.strip(),
        "timestamp": _now_iso(),
    }

    if current not in state["completed_phases"]:
        state["completed_phases"].append(current)

    next_phase = current + 1
    state["current_phase"] = next_phase
    state["last_advanced_at"] = _now_iso()
    state["last_updated"] = _now_iso()
    _save(state)

    print(f"✅ Advanced to Phase {next_phase}/{total}: {names.get(next_phase, 'unknown')}")
    print(f"   Evidence recorded: {evidence.strip()[:100]}{'...' if len(evidence.strip()) > 100 else ''}")
    hints = tpl.get("EVIDENCE_HINTS", {})
    if next_phase <= total:
        print(f"\n   Next: Phase {next_phase} — {names.get(next_phase, '')}")
        print(f"   📝 Evidence needed: {hints.get(next_phase, 'describe what you did')}")
        print(f"   Usage: phase_tracker.py advance --evidence \"...\"")
    if next_phase == total:
        print(f"   🏁 Final phase! Complete with: phase_tracker.py complete")


def cmd_skip(target_str):
    state = _load()
    if state is None:
        print("BLOCKED: No active workflow.")
        sys.exit(1)
    try:
        target = int(target_str)
    except ValueError:
        print(f"Invalid phase: {target_str}")
        sys.exit(1)

    current = state["current_phase"]
    tpl = _resolve(state)
    names = tpl["PHASE_NAMES"]
    print(f"❌ BLOCKED: Skipping disabled. Phase {current} → {target}")
    print(f"   Current: Phase {current} — {names.get(current, '')}")
    print(f"   Use 'advance --evidence \"...\"' to advance properly.")
    sys.exit(1)


def cmd_complete():
    state = _load()
    if state is None:
        print("No active workflow.")
        return
    tpl = _resolve(state)
    total = tpl["total"]
    cp = state["current_phase"]
    done = state["completed_phases"]

    # Auto-mark the final phase as completed (advance blocks on the last phase
    # because there's nowhere to advance to — complete is the only way out).
    if cp == total and cp not in done:
        done.append(cp)

    # Check if all phases were completed
    missing = [p for p in range(1, total + 1) if p not in done]
    if missing:
        print(f"⚠️  WARNING: Phases not completed: {missing}")
        print(f"   These phases were skipped without evidence.")
        evidence = state.get("phase_evidence", {})
        logged = sorted(evidence.keys())
        print(f"   Evidence logged for phases: {logged if logged else 'none'}")
        print(f"   Call 'complete --force' to override, or go back and do the work.")
        # Check for --force flag
        if "--force" not in sys.argv:
            sys.exit(1)
        print("   (--force used, proceeding anyway)")

    state["state"] = "completed"
    if state["current_phase"] not in state["completed_phases"]:
        state["completed_phases"].append(state["current_phase"])
    state["last_updated"] = _now_iso()
    _save(state)
    print(f"✅ Workflow '{state['template']}' COMPLETED.")
    print(f"   Phases completed: {len(done)}/{total}")


def cmd_abort():
    state = _load()
    if state is None:
        print("No active workflow.")
        return
    state["state"] = "aborted"
    state["last_updated"] = _now_iso()
    _save(state)
    tpl = _resolve(state)
    evidence = state.get("phase_evidence", {})
    print(f"⛔ Workflow '{state['template']}' ABORTED at Phase {state['current_phase']}.")
    if evidence:
        print(f"   Evidence recorded for: {sorted(evidence.keys())}")


def cmd_list_phases():
    for tname, tpl in TEMPLATES.items():
        names = tpl["PHASE_NAMES"]
        hints = tpl.get("EVIDENCE_HINTS", {})
        print(f"\n📋 {tname} ({tpl['total']} phases)")
        print("=" * 60)
        for i in range(1, tpl["total"] + 1):
            print(f"  Phase {i:2d}: {names.get(i, '')}")
            if hints.get(i):
                print(f"           Evidence: {hints[i]}")
    print()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage:")
        print("  phase_tracker.py start <template> [--issue N]  — start new workflow")
        print("  phase_tracker.py current                         — show current phase")
        print("  phase_tracker.py check <N>                       — verify on expected phase")
        print("  phase_tracker.py advance --evidence \"text\"       — submit evidence + advance")
        print("  phase_tracker.py skip <N>                        — BLOCKED")
        print("  phase_tracker.py complete [--force]              — mark workflow done")
        print("  phase_tracker.py abort                           — abort workflow")
        print("  phase_tracker.py phases                          — list templates + phases")
        print(f"\nTemplates: {', '.join(TEMPLATES.keys())}")
        return

    cmd = sys.argv[1]

    if cmd == "start":
        template = sys.argv[2] if len(sys.argv) > 2 else "github-issue"
        issue = None
        if "--issue" in sys.argv:
            idx = sys.argv.index("--issue")
            if idx + 1 < len(sys.argv):
                issue = int(sys.argv[idx + 1])
        cmd_start(template, issue)
    elif cmd == "current":
        cmd_current()
    elif cmd == "check":
        if len(sys.argv) < 3:
            print("Usage: phase_tracker.py check <phase_number>")
            sys.exit(1)
        cmd_check(sys.argv[2])
    elif cmd == "advance":
        evidence = None
        if "--evidence" in sys.argv:
            idx = sys.argv.index("--evidence")
            if idx + 1 < len(sys.argv):
                evidence = sys.argv[idx + 1]
        cmd_advance(evidence)
    elif cmd == "skip":
        if len(sys.argv) < 3:
            print("Usage: phase_tracker.py skip <phase_number>")
            sys.exit(1)
        cmd_skip(sys.argv[2])
    elif cmd == "complete":
        cmd_complete()
    elif cmd == "abort":
        cmd_abort()
    elif cmd == "phases":
        cmd_list_phases()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
