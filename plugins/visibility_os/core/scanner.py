from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
import json

from . import db
from .connectors.github import GitHubConnector
from .opportunities import upsert_opportunity, list_opportunities, mark_opportunity_resolved_by_source
from .scoring import score_opportunity


def _labels(item: dict[str, Any]) -> set[str]:
    return {str(l.get("name", "")).lower() for l in item.get("labels") or [] if isinstance(l, dict)}


def _has_successful_check(pr: dict[str, Any], workflow_name: str | None = None) -> bool:
    checks = [c for c in pr.get("statusCheckRollup") or [] if isinstance(c, dict)]
    if workflow_name:
        checks = [c for c in checks if str(c.get("name") or c.get("workflowName") or "").lower() == workflow_name.lower()]
    return any(str(c.get("conclusion") or "").upper() == "SUCCESS" for c in checks)


def _run_is_resolved_in_merged_code(run: dict[str, Any], connector: GitHubConnector) -> bool:
    branch = run.get("headBranch")
    if not branch or not hasattr(connector, "prs_for_branch"):
        return False
    try:
        prs = connector.prs_for_branch(str(branch))
    except Exception:
        return False
    for pr in prs:
        if str(pr.get("state") or "").upper() == "MERGED":
            return True
        if _has_successful_check(pr, run.get("workflowName")):
            return True
    return False


def scan_github(connector: GitHubConnector | None = None) -> list[dict[str, Any]]:
    db.init_db()
    connector = connector or GitHubConnector()
    run_id = f"scan_{uuid.uuid4().hex}"
    with db.connect() as conn:
        conn.execute("INSERT INTO scan_runs(id, scanner_name, status) VALUES (?, ?, ?)", (run_id, "github", "running"))
    found: list[dict[str, Any]] = []
    source_errors: dict[str, str] = {}

    def _safe_fetch(source: str, fn):
        try:
            return fn()
        except Exception as exc:
            # Fine-grained GitHub tokens and repos with disabled Issues may deny
            # one surface while PRs/actions are still readable. Keep the scan
            # useful and record the partial failure in scan_runs.
            source_errors[source] = str(exc)
            return []

    try:
        for issue in _safe_fetch("issues", connector.issues):
            labels = _labels(issue)
            title_l = (issue.get("title") or "").lower()
            if labels & {"bug", "test", "flaky", "docs", "documentation"} or any(w in title_l for w in ("flake", "flaky", "ci", "docs", "bug")):
                category = "flaky_tests_and_ci_failures" if any(w in title_l for w in ("flake", "flaky", "ci", "test")) else "small_customer_facing_bug_fixes" if "bug" in labels else "documentation_and_runbooks"
                s = score_opportunity(impact=4 if category != "documentation_and_runbooks" else 3, visibility=4, effort=4, safety=5, risk_penalty=0)
                found.append(upsert_opportunity(
                    source_system="github", source_url=issue.get("url"), title=issue.get("title") or "GitHub issue",
                    description=f"Issue #{issue.get('number')} appears relevant for {category.replace('_', ' ')}.", category=category,
                    impact_score=s.impact, visibility_score=s.visibility, effort_score=s.effort, safety_score=s.safety,
                    risk_penalty=s.risk_penalty, priority_score=s.priority_score,
                    suggested_artifacts=["pull_request", "issue_comment", "slack_update"], metadata=issue,
                ))
        for pr in _safe_fetch("pull_requests", connector.prs):
            checks = pr.get("statusCheckRollup") or []
            title_l = (pr.get("title") or "").lower()
            failing = any((c.get("conclusion") or "").upper() == "FAILURE" for c in checks if isinstance(c, dict))
            review_decision = pr.get("reviewDecision")
            review_required = (not pr.get("isDraft")) and review_decision in {"REVIEW_REQUIRED", "CHANGES_REQUESTED", None, ""}
            wip_but_visible = bool(pr.get("isDraft")) or "wip" in title_l
            if failing or review_required or wip_but_visible:
                category = "flaky_tests_and_ci_failures" if failing else "pr_review_acceleration" if review_required else "stale_wip_handoff"
                s = score_opportunity(impact=4, visibility=4, effort=5 if review_required else 3, safety=5 if review_required else 4, risk_penalty=0)
                found.append(upsert_opportunity(
                    source_system="github", source_url=pr.get("url"), title=pr.get("title") or "GitHub PR",
                    description=f"PR #{pr.get('number')} may need {'CI attention' if failing else 'review acceleration' if review_required else 'WIP clarification or handoff'}.", category=category,
                    impact_score=s.impact, visibility_score=s.visibility, effort_score=s.effort, safety_score=s.safety,
                    risk_penalty=s.risk_penalty, priority_score=s.priority_score,
                    suggested_artifacts=["review_comment", "risk_note", "slack_update"], metadata=pr,
                ))
        for run in _safe_fetch("workflow_runs", connector.runs):
            if run.get("conclusion") != "failure":
                continue
            if _run_is_resolved_in_merged_code(run, connector):
                mark_opportunity_resolved_by_source(
                    "github",
                    run.get("url"),
                    "flaky_tests_and_ci_failures",
                    reason="Linked branch/PR is merged or has a later successful CI check.",
                )
                continue
            s = score_opportunity(impact=4, visibility=4, effort=4, safety=5, risk_penalty=0)
            found.append(upsert_opportunity(
                source_system="github", source_url=run.get("url"), title=f"Failing CI: {run.get('displayTitle') or run.get('workflowName')}",
                description="A recent GitHub Actions run failed and may be a visible unblock opportunity.", category="flaky_tests_and_ci_failures",
                impact_score=s.impact, visibility_score=s.visibility, effort_score=s.effort, safety_score=s.safety,
                risk_penalty=s.risk_penalty, priority_score=s.priority_score,
                suggested_artifacts=["ci_before_after", "pull_request", "issue_comment"], metadata=run,
            ))
        with db.connect() as conn:
            status = "completed" if not source_errors else "partial"
            conn.execute("UPDATE scan_runs SET status = ?, finished_at = ?, result_payload = ? WHERE id = ?", (status, _now(), json.dumps({"count": len(found), "source_errors": source_errors}), run_id))
    except Exception as exc:
        with db.connect() as conn:
            conn.execute("UPDATE scan_runs SET status = ?, finished_at = ?, result_payload = ? WHERE id = ?", ("failed", _now(), json.dumps({"error": str(exc)}), run_id))
        raise
    return sorted(found, key=lambda o: o["priority_score"], reverse=True)


def current_opportunities() -> list[dict[str, Any]]:
    return list_opportunities()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
