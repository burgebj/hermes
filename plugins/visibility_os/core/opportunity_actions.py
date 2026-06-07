from __future__ import annotations

import json
import re
import subprocess
from typing import Any

from .actions import create_action
from .communications import draft_completion_update, draft_progress_update
from .config import get_visibility_config
from .language_guard import validate_message
from .opportunities import get_opportunity
from .workstreams import bind_root_action, create_workstream


def _team_channel_default() -> str:
    return get_visibility_config().default_slack_channel or "#team-updates"


def _source_repo(source_url: str | None) -> str | None:
    if not source_url:
        return None
    match = re.search(r"github\.com/([^/]+/[^/]+)/", source_url)
    return match.group(1) if match else None


def _github_actions_ref(source_url: str | None) -> tuple[str, str] | None:
    match = re.search(r"github\.com/([^/]+/[^/]+)/actions/runs/(\d+)", source_url or "")
    if not match:
        return None
    return match.group(1), match.group(2)


def _github_issue_ref(source_url: str | None) -> tuple[str, int] | None:
    match = re.search(r"github\.com/([^/]+/[^/]+)/issues/(\d+)", source_url or "")
    if not match:
        return None
    return match.group(1), int(match.group(2))


def _gh(args: list[str], *, timeout: int = 120) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {' '.join(args)}")
    return result.stdout


def _evidence_links(opportunity: dict[str, Any]) -> list[dict[str, Any]]:
    links = []
    if opportunity.get("source_url"):
        links.append({"type": opportunity.get("source_system") or "source", "url": opportunity["source_url"], "label": opportunity.get("title")})
    for key in ("url", "html_url"):
        url = (opportunity.get("metadata") or {}).get(key)
        if url and all(item.get("url") != url for item in links):
            links.append({"type": "metadata", "url": url})
    return links


def _score_explanation(opportunity: dict[str, Any]) -> str:
    return (
        "priority_score = impact_score*3 + visibility_score*2 + effort_score + safety_score - risk_penalty "
        f"= {opportunity.get('impact_score')}*3 + {opportunity.get('visibility_score')}*2 + "
        f"{opportunity.get('effort_score')} + {opportunity.get('safety_score')} - {opportunity.get('risk_penalty')} "
        f"= {opportunity.get('priority_score')}"
    )


def _recommended_actions(opportunity: dict[str, Any]) -> list[dict[str, Any]]:
    source_url = opportunity.get("source_url") or ""
    category = opportunity.get("category") or ""
    actions: list[dict[str, Any]] = []
    if _github_actions_ref(source_url):
        actions.append({
            "action_kind": "github_actions_diagnosis",
            "label": "Diagnose CI",
            "risk_level": "low",
            "reason": "Fetch failed GitHub Actions metadata/logs and queue a read-only diagnosis with likely next steps.",
        })
        actions.append({
            "action_kind": "ci_fix_lane",
            "label": "Start Fix CI lane",
            "risk_level": "high",
            "reason": "If diagnosis proves the failure is actionable, queue an approval-gated Hermes repair lane to prepare a local fix branch, commit, PR title/body, and verification evidence for human review before any push.",
        })
    if "/pull/" in source_url or category in {"pr_review_acceleration", "stale_wip_handoff"}:
        actions.append({
            "action_kind": "github_pr_comment",
            "label": "Draft PR coordination comment",
            "risk_level": "low",
            "reason": "Post a factual coordination/handoff note on the PR. This is not a code review.",
        })
    elif _github_issue_ref(source_url):
        actions.append({
            "action_kind": "github_issue_fix_lane",
            "label": "Fix issue",
            "risk_level": "high",
            "reason": "Run a one-click Hermes issue repair lane that prepares a local fix branch, self-audits, runs an independent fresh-session review, then queues a separate Push branch decision.",
        })
        actions.append({
            "action_kind": "github_issue_comment",
            "label": "Draft GitHub issue comment",
            "risk_level": "low",
            "reason": "Add a factual investigation/status note to the issue.",
        })
    actions.append({
        "action_kind": "slack_update",
        "label": "Draft Slack update",
        "risk_level": "medium",
        "reason": "Summarize the opportunity for the team without claiming completion.",
    })
    return actions


def build_opportunity_detail(opportunity_id: str) -> dict[str, Any]:
    opportunity = get_opportunity(opportunity_id)
    detail = dict(opportunity)
    detail["source_repo"] = _source_repo(opportunity.get("source_url"))
    detail["evidence_links"] = _evidence_links(opportunity)
    detail["score_explanation"] = _score_explanation(opportunity)
    detail["recommended_actions"] = _recommended_actions(opportunity)
    detail["why_it_matters"] = (
        f"{opportunity.get('category', 'opportunity').replace('_', ' ').title()} with priority score "
        f"{opportunity.get('priority_score')}. {opportunity.get('description') or ''}"
    ).strip()
    detail["suggested_next_step"] = detail["recommended_actions"][0]["label"] if detail["recommended_actions"] else "Review manually"
    return detail


def _body_for(opportunity: dict[str, Any], *, action_kind: str) -> str:
    url = opportunity.get("source_url") or ""
    title = opportunity.get("title") or "this item"
    description = opportunity.get("description") or "This looks like a visible unblock opportunity."
    if action_kind == "slack_update":
        return (
            f"I found a visible review/unblock opportunity: {title}\n"
            f"Evidence: {url}\n"
            f"Why it matters: {description}\n"
            "Current status: I have identified the opportunity and queued this for review.\n"
            "Next step: review the linked item and decide whether to accelerate, hand off, or close it out."
        )
    return (
        f"Coordination note: this PR looks like a visible review/unblock opportunity: {title}\n\n"
        f"Evidence: {url}\n\n"
        f"Why it matters: {description}\n\n"
        "Suggested next step: confirm whether this is ready for review, needs a handoff, or should be closed. "
        "I have not performed a code review in this comment."
    )


def _pr_context_for_run(repo: str, view: dict[str, Any]) -> dict[str, Any] | None:
    branch = view.get("headBranch")
    if not branch:
        return None
    try:
        raw = _gh([
            "gh", "pr", "list",
            "--repo", repo,
            "--head", str(branch),
            "--state", "all",
            "--json", "number,title,state,url,headRefName,headRefOid,baseRefName,mergedAt,statusCheckRollup",
        ], timeout=90)
        prs = json.loads(raw or "[]")
    except Exception:
        return None
    if not isinstance(prs, list) or not prs:
        return None
    pr = next((p for p in prs if isinstance(p, dict) and p.get("headRefName") == branch), prs[0])
    checks = [c for c in pr.get("statusCheckRollup") or [] if isinstance(c, dict)]
    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "state": pr.get("state"),
        "url": pr.get("url"),
        "branch": pr.get("headRefName") or branch,
        "head_sha": pr.get("headRefOid"),
        "base_branch": pr.get("baseRefName"),
        "merged_at": pr.get("mergedAt"),
        "has_successful_later_check": any(str(c.get("conclusion") or "").upper() == "SUCCESS" for c in checks),
        "status_checks": checks,
    }


def _resolution_status(pr_context: dict[str, Any] | None) -> tuple[str, bool, list[str], str | None]:
    if not pr_context:
        return "unknown", True, [
            "Open the failing job and confirm the first real error above.",
            "Reproduce the failing command locally or in the relevant repo checkout.",
            "If the cause is clear, create a focused fix with before/after CI evidence.",
        ], None
    if str(pr_context.get("state") or "").upper() == "MERGED":
        return "resolved_merged", False, [
            "No new fix branch recommended, the linked PR has already been merged.",
            "Confirm the opportunity can be closed as stale/resolved.",
        ], f"This run belongs to PR #{pr_context.get('number')} on branch {pr_context.get('branch')}, which has already been merged. Treat this failed run as stale unless newer evidence says otherwise."
    if pr_context.get("has_successful_later_check"):
        return "resolved_newer_ci_passed", False, [
            "No new fix branch recommended, a later check on the linked PR passed.",
            "Confirm the opportunity can be closed as stale/resolved.",
        ], f"This run belongs to PR #{pr_context.get('number')} and a later status check on that PR passed. Treat this failed run as stale."
    return "actionable", True, [
        "Open the linked PR/branch and confirm the first real error above.",
        "Reproduce the failing command locally or in the relevant repo checkout.",
        "Create a focused fix branch only if the PR is still open and the latest CI is still failing.",
    ], f"This run correlates to PR #{pr_context.get('number')} on branch {pr_context.get('branch')}. The PR does not appear merged or resolved by a later successful check."


def _diagnose_github_actions(opportunity: dict[str, Any]) -> dict[str, Any]:
    ref = _github_actions_ref(opportunity.get("source_url"))
    if not ref:
        raise ValueError("Opportunity is not a GitHub Actions run URL")
    repo, run_id = ref
    raw_view = _gh([
        "gh", "run", "view", run_id, "--repo", repo,
        "--json", "name,displayTitle,conclusion,status,event,headBranch,headSha,jobs,url",
    ], timeout=90)
    try:
        view = json.loads(raw_view or "{}")
    except Exception:
        view = {}
    try:
        failed_log = _gh(["gh", "run", "view", run_id, "--repo", repo, "--log-failed"], timeout=180)
    except Exception as exc:
        failed_log = f"Could not fetch failed logs: {exc}"
    jobs = [j for j in (view.get("jobs") or []) if isinstance(j, dict)]
    failed_jobs = [str(j.get("name") or "unnamed job") for j in jobs if str(j.get("conclusion") or "").lower() == "failure"]
    failed_steps = []
    for job in jobs:
        for step in job.get("steps") or []:
            if isinstance(step, dict) and str(step.get("conclusion") or "").lower() == "failure":
                failed_steps.append(f"{job.get('name') or 'job'} / {step.get('name') or 'step'}")
    important_lines = _important_log_lines(failed_log)
    likely_cause = important_lines[0] if important_lines else "The run failed, but the failed log output did not include an obvious error line. Open the run logs and inspect the failed job manually."
    pr_context = _pr_context_for_run(repo, view)
    resolution_status, should_create_fix_branch, next_steps, stale_note = _resolution_status(pr_context)
    body = "\n".join([
        f"CI diagnosis for {opportunity.get('title') or 'GitHub Actions run'}",
        f"Run: {opportunity.get('source_url')}",
        f"Repository: {repo}",
        f"Branch: {view.get('headBranch') or 'unknown'}",
        f"Commit: {view.get('headSha') or 'unknown'}",
        f"PR: #{pr_context.get('number')} {pr_context.get('state')} {pr_context.get('url')}" if pr_context else "PR: not found for run branch",
        f"Status: {view.get('status') or 'unknown'} / {view.get('conclusion') or 'unknown'}",
        f"Resolution status: {resolution_status}",
        f"Should create fix branch: {'yes' if should_create_fix_branch else 'no'}",
        f"Failed jobs: {', '.join(failed_jobs) if failed_jobs else 'not identified from metadata'}",
        f"Failed steps: {', '.join(failed_steps) if failed_steps else 'not identified from metadata'}",
        "",
        "Likely cause:",
        likely_cause,
        "",
        "Actionability:",
        stale_note or "No stale/resolved PR evidence found, this may still need investigation.",
        "",
        "Relevant log lines:",
        *(f"- {line}" for line in important_lines[:8]),
        "",
        "Recommended next steps:",
        *(f"{idx}. {step}" for idx, step in enumerate(next_steps, 1)),
    ]).strip()
    return {
        "body": body,
        "repo": repo,
        "run_id": run_id,
        "run_url": opportunity.get("source_url"),
        "diagnosis": {
            "likely_cause": likely_cause,
            "failed_jobs": failed_jobs,
            "failed_steps": failed_steps,
            "important_log_lines": important_lines[:20],
            "metadata": view,
        },
        "pr_context": pr_context,
        "resolution_status": resolution_status,
        "should_create_fix_branch": should_create_fix_branch,
        "next_steps": next_steps,
    }


def _build_ci_fix_lane_payload(opportunity: dict[str, Any]) -> dict[str, Any]:
    diagnosis = _diagnose_github_actions(opportunity)
    if not diagnosis.get("should_create_fix_branch"):
        raise ValueError(
            f"CI run is not actionable for fix lane: {diagnosis.get('resolution_status')}. "
            "Use the diagnosis output to close or save the stale opportunity instead."
        )
    repo = diagnosis["repo"]
    run_id = diagnosis["run_id"]
    pr_context = diagnosis.get("pr_context") or {}
    branch = pr_context.get("branch") or diagnosis.get("diagnosis", {}).get("metadata", {}).get("headBranch") or "unknown"
    cfg = get_visibility_config()
    prompt = "\n".join([
        f"You are running the Visibility OS automated Fix CI lane for {cfg.company_name}.",
        "",
        "Goal: prepare a local CI/CD fix branch with a commit and a proposed PR message. Do not push the branch or open/update a PR yet.",
        "",
        f"Repository: {repo}",
        f"Failed run: {diagnosis.get('run_url')}",
        f"Run id: {run_id}",
        f"Branch: {branch}",
        f"Commit: {diagnosis.get('diagnosis', {}).get('metadata', {}).get('headSha') or 'unknown'}",
        f"PR: #{pr_context.get('number')} {pr_context.get('url')}" if pr_context else "PR: not found",
        f"Resolution status: {diagnosis.get('resolution_status')}",
        "",
        "Likely cause:",
        str(diagnosis.get("diagnosis", {}).get("likely_cause") or "unknown"),
        "",
        "Relevant log lines:",
        *(f"- {line}" for line in diagnosis.get("diagnosis", {}).get("important_log_lines", [])[:12]),
        "",
        "Execution rules:",
        "1. Re-check that the PR/branch is still open and the latest CI is still failing before making changes.",
        "2. Work only inside the named repository and only on the CI fix scope.",
        "3. Create a focused local fix branch and commit the fix locally with a clear commit message.",
        "4. Reproduce the failing command locally when possible, then run the smallest relevant test/typecheck/build command that proves the fix.",
        "5. Perform a self-audit second pass on your own code fixes before committing: inspect the diff, look for regressions, edge cases, security issues, unintended scope creep, and test gaps. Fix any issues the second pass finds.",
        "6. Draft a PR title and PR body using the same evidence-backed summary as the commit message if appropriate.",
        f"7. Do not push the branch, do not open or update a PR, and do not merge. Visibility OS will show the configured approver a separate Push branch button after review.",
        "8. Include before/after CI evidence, commands run, and self-audit findings in the proposed PR body.",
        f"9. Do not deploy, merge, alter production infrastructure, rotate secrets, or touch repositories outside the configured GitHub organisations: {cfg.github_scope_label}.",
        "",
        "Final response must be JSON with: branch, commit_sha, commit_message, pr_title, pr_body, verification, changed_files, self_audit, ready_to_push.",
        "self_audit must be an object with: audit_status, issues_found, fixes_applied, notes.",
    ])
    return {
        "lane": "fix_ci",
        "repo": repo,
        "run_id": run_id,
        "run_url": diagnosis.get("run_url"),
        "pr_context": pr_context,
        "diagnosis": diagnosis.get("diagnosis"),
        "resolution_status": diagnosis.get("resolution_status"),
        "should_create_fix_branch": diagnosis.get("should_create_fix_branch"),
        "prompt": prompt,
        "command": ["hermes", "chat", "--query", "__PROMPT__", "--quiet", "--source", "visibility-os-ci-fix", "--toolsets", "terminal,file"],
        "safety_gates": [
            "stale_ci_recheck",
            "configured_org_only",
            "local_verification_before_push",
            "self_audit_before_push",
            "no_push_until_human_approves",
            "no_deploy_no_merge",
            "final_evidence_required",
        ],
    }


def _build_github_issue_fix_lane_payload(opportunity: dict[str, Any]) -> dict[str, Any]:
    ref = _github_issue_ref(opportunity.get("source_url"))
    if not ref:
        raise ValueError("Opportunity is not a GitHub issue URL")
    repo, issue_number = ref
    cfg = get_visibility_config()
    if not cfg.github_repo_allowed(repo):
        raise ValueError(f"Visibility OS is restricted to configured GitHub repositories: {cfg.github_scope_label}")
    metadata = opportunity.get("metadata") or {}
    labels = [str(label.get("name") or label) for label in metadata.get("labels") or []]
    issue_body = str(metadata.get("body") or metadata.get("description") or opportunity.get("description") or "")
    prompt = "\n".join([
        f"You are running the Visibility OS automated GitHub issue fix lane for {cfg.company_name}.",
        "",
        f"Goal: Fix GitHub issue #{issue_number} by preparing a local code/docs fix branch with a commit and proposed PR message. Do not push the branch or open/update a PR yet.",
        "",
        f"Repository: {repo}",
        f"Issue: #{issue_number}",
        f"Issue URL: {opportunity.get('source_url')}",
        f"Issue title: {metadata.get('title') or opportunity.get('title') or ''}",
        f"Labels: {', '.join(labels) if labels else 'none'}",
        "",
        "Issue body / opportunity description:",
        issue_body[:4000],
        "",
        "Execution rules:",
        "1. Re-check the issue is still open and understand the requested bug fix, documentation change, or implementation task before editing.",
        "2. Work only inside the named repository and only on the scope described by the issue.",
        "3. Create a focused local branch and commit the fix locally with a clear commit message.",
        "4. Add or update the smallest relevant tests/docs and run the smallest relevant verification command that proves the issue fix.",
        "5. Perform a self-audit second pass on your own fix before committing: inspect the diff, look for regressions, edge cases, security issues, unintended scope creep, and test gaps. Fix any issues the second pass finds.",
        "6. Draft a PR title and PR body that references the issue with a closing keyword, for example: Fixes #" + str(issue_number) + ".",
        "7. Do not push the branch, do not open or update a PR, and do not merge. Visibility OS will show the configured approver a separate Push branch button after review.",
        "8. Include commands run, files changed, and self-audit findings in the proposed PR body.",
        f"9. Do not deploy, merge, alter production infrastructure, rotate secrets, or touch repositories outside the configured GitHub organisations: {cfg.github_scope_label}.",
        "",
        "Final response must be JSON with: branch, commit_sha, commit_message, pr_title, pr_body, verification, changed_files, self_audit, ready_to_push.",
        "self_audit must be an object with: audit_status, issues_found, fixes_applied, notes.",
    ])
    return {
        "lane": "fix_github_issue",
        "repo": repo,
        "issue_number": issue_number,
        "issue_url": opportunity.get("source_url"),
        "issue_title": metadata.get("title") or opportunity.get("title"),
        "issue_body": issue_body,
        "prompt": prompt,
        "command": ["hermes", "chat", "--query", "__PROMPT__", "--quiet", "--source", "visibility-os-issue-fix", "--toolsets", "terminal,file"],
        "safety_gates": [
            "issue_open_recheck",
            "configured_org_only",
            "local_verification_before_push",
            "self_audit_before_push",
            "independent_review_before_push",
            "no_push_until_human_approves",
            "no_deploy_no_merge",
            "final_evidence_required",
        ],
    }


def _important_log_lines(log: str) -> list[str]:
    patterns = re.compile(r"(error:|error\b|failed|failure|exception|traceback|assertionerror|npm err|pytest|fatal:|missing|denied)", re.I)
    lines = []
    for raw in (log or "").splitlines():
        line = raw.strip()
        if not line or len(line) > 500:
            continue
        if patterns.search(line):
            lines.append(line)
        if len(lines) >= 20:
            break
    return lines


def draft_action_from_opportunity(opportunity_id: str, *, action_kind: str, target_location: str | None = None, actor: str = "visibility_os") -> dict[str, Any]:
    opportunity = get_opportunity(opportunity_id)
    evidence_links = _evidence_links(opportunity)
    if action_kind == "github_actions_diagnosis":
        payload = _diagnose_github_actions(opportunity)
        return create_action(
            proposed_by_agent=actor,
            action_type="github_actions_diagnosis",
            target_system="github",
            target_location=target_location or opportunity.get("source_url") or "",
            title=f"Diagnose CI: {opportunity.get('title', '')[:90]}",
            summary=f"Diagnosed failed GitHub Actions run for opportunity {opportunity_id}.",
            proposed_payload=payload,
            evidence_links=evidence_links,
            risk_level="low",
            opportunity_id=opportunity_id,
            impact_score=opportunity.get("impact_score"),
            visibility_score=opportunity.get("visibility_score"),
            effort_score=opportunity.get("effort_score"),
            approval_reason="Read-only CI diagnosis queued for human review before any fix work.",
        )
    if action_kind == "ci_fix_lane":
        payload = _build_ci_fix_lane_payload(opportunity)
        title = f"Start Fix CI lane: {opportunity.get('title', '')[:80]}"
        workstream = create_workstream(
            opportunity_id=opportunity_id,
            root_action_id=None,
            lane_kind="ci_fix_lane",
            title=title,
            repo=payload.get("repo"),
            source_url=opportunity.get("source_url"),
            actor=actor,
            summary=f"Agentic CI remediation for {payload.get('repo')} run {payload.get('run_id')}",
        )
        payload["workstream_id"] = workstream["id"]
        action = create_action(
            proposed_by_agent=actor,
            action_type="ci_fix_lane",
            target_system="hermes",
            target_location=target_location or f"{payload.get('repo')}#{payload.get('run_id')}",
            title=title,
            summary=f"Approval-gated Hermes Fix CI lane for opportunity {opportunity_id}.",
            proposed_payload=payload,
            evidence_links=evidence_links,
            risk_level="high",
            opportunity_id=opportunity_id,
            impact_score=opportunity.get("impact_score"),
            visibility_score=opportunity.get("visibility_score"),
            effort_score=opportunity.get("effort_score"),
            approval_reason="Automated CI repair may create local branches and commits, so it requires human approval before execution. Pushing is queued as a separate explicit action.",
        )
        bind_root_action(workstream["id"], action["id"])
        return action
    if action_kind == "github_issue_fix_lane":
        payload = _build_github_issue_fix_lane_payload(opportunity)
        title = f"Fix GitHub issue #{payload.get('issue_number')}: {opportunity.get('title', '')[:80]}"
        workstream = create_workstream(
            opportunity_id=opportunity_id,
            root_action_id=None,
            lane_kind="github_issue_fix_lane",
            title=title,
            repo=payload.get("repo"),
            source_url=opportunity.get("source_url"),
            actor=actor,
            summary=f"Agentic issue remediation for {payload.get('repo')} issue #{payload.get('issue_number')}",
        )
        payload["workstream_id"] = workstream["id"]
        action = create_action(
            proposed_by_agent=actor,
            action_type="github_issue_fix_lane",
            target_system="hermes",
            target_location=target_location or f"{payload.get('repo')}#{payload.get('issue_number')}",
            title=title,
            summary=f"Approval-gated Hermes issue fix lane for opportunity {opportunity_id}.",
            proposed_payload=payload,
            evidence_links=evidence_links,
            risk_level="high",
            opportunity_id=opportunity_id,
            impact_score=opportunity.get("impact_score"),
            visibility_score=opportunity.get("visibility_score"),
            effort_score=opportunity.get("effort_score"),
            approval_reason="Automated issue repair may create local branches and commits, so it requires human approval before execution. Pushing is queued as a separate explicit action.",
        )
        bind_root_action(workstream["id"], action["id"])
        return action
    if action_kind == "github_pr_comment":
        action_type = "github_pr_comment"
        target_system = "github"
        destination = target_location or opportunity.get("source_url")
        payload_key = "body"
        risk_level = "low"
    elif action_kind == "github_issue_comment":
        action_type = "github_issue_comment"
        target_system = "github"
        destination = target_location or opportunity.get("source_url")
        payload_key = "body"
        risk_level = "low"
    elif action_kind == "slack_update":
        action_type = "slack_message"
        target_system = "slack"
        destination = target_location or _team_channel_default()
        payload_key = "text"
        risk_level = "medium"
    else:
        raise ValueError(f"Unsupported opportunity action kind: {action_kind}")

    text = _body_for(opportunity, action_kind=action_kind)
    validate_message(text, status="queued", evidence_links=evidence_links, team_visible=(target_system == "slack"))
    return create_action(
        proposed_by_agent=actor,
        action_type=action_type,
        target_system=target_system,
        target_location=destination or "",
        title=f"{_recommended_label(action_kind)}: {opportunity.get('title', '')[:80]}",
        summary=f"Drafted from opportunity {opportunity_id}: {opportunity.get('description') or opportunity.get('title')}",
        proposed_payload={payload_key: text},
        evidence_links=evidence_links,
        risk_level=risk_level,
        opportunity_id=opportunity_id,
        impact_score=opportunity.get("impact_score"),
        visibility_score=opportunity.get("visibility_score"),
        effort_score=opportunity.get("effort_score"),
        approval_reason="External/reputation-sensitive write drafted from a Visibility OS opportunity.",
    )


def _recommended_label(action_kind: str) -> str:
    return {
        "github_actions_diagnosis": "Diagnose CI",
        "ci_fix_lane": "Start Fix CI lane",
        "github_issue_fix_lane": "Fix issue",
        "github_pr_comment": "Draft PR coordination comment",
        "github_issue_comment": "Draft issue coordination comment",
        "slack_update": "Draft Slack update",
    }.get(action_kind, "Draft action")
