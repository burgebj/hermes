from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from ..actions import create_action
from ..config import get_visibility_config
from ..workstreams import add_workstream_artifact, update_stage


def _ensure_allowed_repo(repo: str | None) -> None:
    cfg = get_visibility_config()
    if not cfg.github_repo_allowed(repo):
        raise RuntimeError(f"Visibility OS Hermes lanes are restricted to configured repositories: {cfg.github_scope_label}")


def _command_with_prompt(command: list[Any], prompt: str, *, source: str = "visibility-os-ci-fix") -> list[str]:
    if not command:
        return [
            "hermes",
            "chat",
            "--query",
            prompt,
            "--quiet",
            "--source",
            source,
            "--toolsets",
            "terminal,file",
        ]
    return [prompt if str(part) == "__PROMPT__" else str(part) for part in command]


def _parse_json_object(text: str, error_message: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise RuntimeError(error_message)
    candidates: list[dict[str, Any]] = []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            parsed, _ = decoder.raw_decode(text[match.start():])
        except Exception:
            continue
        if isinstance(parsed, dict):
            candidates.append(parsed)
    if not candidates:
        raise RuntimeError(error_message)
    return candidates[-1]


def _parse_prepared_fix(stdout: str) -> dict[str, Any]:
    parsed = _parse_json_object(stdout, "Hermes Fix CI lane must return JSON describing the prepared branch")
    if not isinstance(parsed, dict):
        raise RuntimeError("Hermes Fix CI lane JSON must be an object")
    missing = [key for key in ("branch", "commit_message", "pr_title", "pr_body", "self_audit") if not parsed.get(key)]
    if missing:
        raise RuntimeError(f"Prepared Fix CI payload missing required field(s): {', '.join(missing)}")
    self_audit = parsed.get("self_audit")
    if not isinstance(self_audit, dict) or not self_audit.get("audit_status"):
        raise RuntimeError("Prepared Fix CI payload requires self_audit.audit_status from the second-pass review")
    if parsed.get("ready_to_push") is False:
        raise RuntimeError("Hermes Fix CI lane did not mark the prepared branch ready to push")
    return parsed


def _parse_independent_review(stdout: str) -> dict[str, Any]:
    parsed = _parse_json_object(stdout, "Independent Fix CI review must return JSON")
    if not isinstance(parsed, dict) or not parsed.get("review_status"):
        raise RuntimeError("Independent Fix CI review requires review_status")
    status = str(parsed.get("review_status")).lower()
    if status not in {"passed", "approved", "no_blockers"}:
        raise RuntimeError(f"Independent Fix CI review did not pass: {parsed.get('review_status')}")
    return parsed


def _build_independent_review_prompt(repo: str, prepared: dict[str, Any], *, lane_label: str = "CI fix", issue_number: int | None = None) -> str:
    context = [f"Repository: {repo}"]
    if issue_number is not None:
        context.append(f"Issue: #{issue_number}")
    return "\n".join([
        f"You are a fresh session independent reviewer for a prepared {lane_label}.",
        "You were not involved in the fix. Do not assume the fix is correct.",
        "Review only the current local repository state, branch, commit/diff, proposed PR text, and verification evidence.",
        "Do not use or rely on the original fixing prompt or the fixing agent's reasoning.",
        "Look for regressions, unintended scope creep, security issues, missing tests, brittle logic, and PR description inaccuracies.",
        "Do not push, merge, deploy, rotate secrets, or touch production infrastructure.",
        *context,
        f"Prepared branch: {prepared.get('branch')}",
        f"Commit: {prepared.get('commit_sha') or 'unknown'}",
        f"Commit message: {prepared.get('commit_message')}",
        f"PR title: {prepared.get('pr_title')}",
        "Changed files: " + json.dumps(prepared.get("changed_files") or []),
        "Verification evidence: " + json.dumps(prepared.get("verification") or []),
        "PR body:",
        str(prepared.get("pr_body") or ""),
        "Return JSON only with: review_status, findings, fixes_required, notes.",
        "Use review_status='passed' only if there are no blockers to pushing this prepared branch for PR creation.",
    ])


def _stage(workstream_id: str | None, stage: str, current_step: str, progress: int, *, actor: str = "visibility_os", payload: dict[str, Any] | None = None) -> None:
    if not workstream_id:
        return
    update_stage(workstream_id, stage=stage, current_step=current_step, progress_percent=progress, actor=actor, payload=payload or {})


def _artifact(workstream_id: str | None, artifact_type: str, title: str, *, summary: str = "", payload: dict[str, Any] | None = None) -> None:
    if not workstream_id:
        return
    add_workstream_artifact(workstream_id, artifact_type=artifact_type, title=title, summary=summary, payload=payload or {})


def execute_hermes_action(action: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    action_type = action["action_type"]
    lane = payload.get("lane")
    if action_type == "ci_fix_lane":
        expected_lane = "fix_ci"
        source = "visibility-os-ci-review"
        lane_label = "CI fix"
        default_workspace = "ci-fix-workspaces"
        push_title = "Push prepared CI fix branch"
        if payload.get("should_create_fix_branch") is False:
            raise RuntimeError("Refusing to execute Fix CI lane because diagnosis marked it non-actionable")
    elif action_type == "github_issue_fix_lane":
        expected_lane = "fix_github_issue"
        source = "visibility-os-issue-review"
        lane_label = "GitHub issue fix"
        default_workspace = "issue-fix-workspaces"
        push_title = "Push prepared issue fix branch"
    else:
        raise RuntimeError(f"Unsupported Hermes action type {action_type}")
    if lane != expected_lane:
        raise RuntimeError(f"Hermes action payload must declare lane='{expected_lane}'")
    repo = payload.get("repo")
    workstream_id = payload.get("workstream_id")
    _stage(workstream_id, "agent_starting", f"Starting {lane_label} agent", 10, payload={"action_id": action.get("id")})
    _ensure_allowed_repo(repo)
    prompt = payload.get("prompt")
    if not prompt:
        raise RuntimeError(f"{lane_label} lane requires a prompt")
    workdir = payload.get("workdir") or str(Path.home() / ".hermes" / "visibility-os" / default_workspace / str(repo).replace("/", "__"))
    Path(workdir).mkdir(parents=True, exist_ok=True)
    _stage(workstream_id, "gathering_context", "Prepared repo context and agent prompt", 20, payload={"workdir": workdir, "repo": repo})
    cmd = _command_with_prompt(payload.get("command") or [], str(prompt), source="visibility-os-issue-fix" if action_type == "github_issue_fix_lane" else "visibility-os-ci-fix")
    _stage(workstream_id, "editing", f"Agent is preparing a local {lane_label} branch", 35, payload={"command": cmd[:3] + ["..."]})
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=int(payload.get("timeout_seconds") or 3600), check=False, cwd=workdir)
    if res.returncode != 0:
        _stage(workstream_id, "failed", res.stderr.strip() or res.stdout.strip() or f"Hermes {lane_label} lane failed", 100, payload={"stdout": res.stdout.strip(), "stderr": res.stderr.strip()})
        raise RuntimeError(res.stderr.strip() or res.stdout.strip() or f"Hermes {lane_label} lane failed")
    _stage(workstream_id, "verifying", "Agent returned prepared branch and verification evidence", 55)
    prepared = _parse_prepared_fix(res.stdout)
    _stage(workstream_id, "self_auditing", "Self-audit completed inside fixing session", 65, payload={"self_audit": prepared.get("self_audit") or {}})
    review_prompt = _build_independent_review_prompt(str(repo), prepared, lane_label=lane_label, issue_number=payload.get("issue_number"))
    review_cmd = _command_with_prompt(payload.get("review_command") or [], review_prompt, source=source)
    _stage(workstream_id, "independent_reviewing", "Fresh independent review session is checking the prepared branch", 75, payload={"command": review_cmd[:3] + ["..."]})
    review_res = subprocess.run(review_cmd, capture_output=True, text=True, timeout=int(payload.get("review_timeout_seconds") or 1800), check=False, cwd=workdir)
    if review_res.returncode != 0:
        _stage(workstream_id, "failed", review_res.stderr.strip() or review_res.stdout.strip() or f"Independent {lane_label} review failed", 100, payload={"stdout": review_res.stdout.strip(), "stderr": review_res.stderr.strip()})
        raise RuntimeError(review_res.stderr.strip() or review_res.stdout.strip() or f"Independent {lane_label} review failed")
    independent_review = _parse_independent_review(review_res.stdout)
    push_payload = {
        "repo": repo,
        "branch": prepared["branch"],
        "base_branch": (payload.get("pr_context") or {}).get("base_branch") or prepared.get("base_branch") or "main",
        "workdir": workdir,
        "commit_sha": prepared.get("commit_sha"),
        "commit_message": prepared.get("commit_message"),
        "pr_title": prepared.get("pr_title") or prepared.get("commit_message"),
        "pr_body": prepared.get("pr_body"),
        "verification": prepared.get("verification") or [],
        "changed_files": prepared.get("changed_files") or [],
        "self_audit": prepared.get("self_audit") or {},
        "independent_review": independent_review,
        "source_run_id": payload.get("run_id"),
        "source_run_url": payload.get("run_url"),
        "issue_number": payload.get("issue_number"),
        "issue_url": payload.get("issue_url"),
        "workstream_id": workstream_id,
    }
    _artifact(
        workstream_id,
        "proposed_pr",
        prepared.get("pr_title") or prepared.get("commit_message") or "Proposed PR",
        summary=f"Prepared branch {prepared.get('branch')} with {len(prepared.get('changed_files') or [])} changed file(s).",
        payload=push_payload,
    )
    _artifact(
        workstream_id,
        "diff_summary",
        "Changed files",
        summary="Agent-reported changed files for the prepared local branch.",
        payload={
            "branch": prepared.get("branch"),
            "files": [{"path": path} for path in (prepared.get("changed_files") or [])],
            "changed_files": prepared.get("changed_files") or [],
        },
    )
    push_action = create_action(
        proposed_by_agent="visibility_os",
        action_type="github_push_branch",
        target_system="github",
        target_location=f"{repo}#{prepared['branch']}",
        title=f"{push_title}: {prepared['branch']}",
        summary=f"Review and optionally push local branch {prepared['branch']} and create a PR for {repo}.",
        proposed_payload=push_payload,
        evidence_links=action.get("evidence_links") or [],
        risk_level="high",
        opportunity_id=action.get("opportunity_id"),
        impact_score=action.get("impact_score"),
        visibility_score=action.get("visibility_score"),
        effort_score=action.get("effort_score"),
        approval_reason="Pushes a prepared local branch and creates a GitHub PR, so a human approver must explicitly choose Push branch.",
    )
    _stage(workstream_id, "ready_for_push", "Prepared PR passed independent review and is waiting for Push branch approval", 90, payload={"push_action_id": push_action["id"]})
    return {
        "ok": True,
        "lane": lane,
        "mode": "prepared_local_branch_only",
        "repo": repo,
        "run_id": payload.get("run_id"),
        "issue_number": payload.get("issue_number"),
        "issue_url": payload.get("issue_url"),
        "prepared_branch": prepared["branch"],
        "commit_sha": prepared.get("commit_sha"),
        "commit_message": prepared.get("commit_message"),
        "pr_title": prepared.get("pr_title"),
        "pr_body": prepared.get("pr_body"),
        "verification": prepared.get("verification") or [],
        "changed_files": prepared.get("changed_files") or [],
        "self_audit": prepared.get("self_audit") or {},
        "independent_review": independent_review,
        "push_action_id": push_action["id"],
        "stdout": res.stdout.strip(),
        "stderr": res.stderr.strip(),
        "command": cmd[:3] + ["..."],
        "workdir": workdir,
    }
