from __future__ import annotations

from typing import Any

from .actions import create_action
from .language_guard import validate_message


def draft_progress_update(*, problem: str, diagnosis: str, action_underway: str, next_step: str, target_location: str, evidence_links: list[dict[str, Any]], target_system: str = "slack") -> dict[str, Any]:
    text = (
        f"Problem: {problem}\n"
        f"Diagnosis: {diagnosis}\n"
        f"Action underway: {action_underway}\n"
        f"Next step: {next_step}"
    )
    validate_message(text, status="queued", evidence_links=evidence_links, team_visible=True)
    return create_action(
        proposed_by_agent="communications_agent",
        action_type="slack_message" if target_system == "slack" else "github_issue_comment",
        target_system=target_system,
        target_location=target_location,
        title=f"Progress update: {problem[:80]}",
        summary="Draft factual progress update with evidence links.",
        proposed_payload={"text" if target_system == "slack" else "body": text},
        evidence_links=evidence_links,
        risk_level="medium" if target_system == "slack" else "low",
        impact_score=3,
        visibility_score=4,
        effort_score=5,
    )


def draft_completion_update(*, problem: str, fix: str, evidence: str, impact: str, follow_up: str, target_location: str, evidence_links: list[dict[str, Any]], target_system: str = "slack") -> dict[str, Any]:
    text = f"Problem: {problem}\nFix: {fix}\nEvidence: {evidence}\nImpact: {impact}\nFollow-up: {follow_up}"
    validate_message(text, status="executed", evidence_links=evidence_links, team_visible=True)
    return create_action(
        proposed_by_agent="communications_agent",
        action_type="slack_message" if target_system == "slack" else "github_issue_comment",
        target_system=target_system,
        target_location=target_location,
        title=f"Completion update: {problem[:80]}",
        summary="Draft completion update with evidence links.",
        proposed_payload={"text" if target_system == "slack" else "body": text},
        evidence_links=evidence_links,
        risk_level="medium",
        impact_score=4,
        visibility_score=5,
        effort_score=5,
    )


def draft_weekly_update(*, text: str, target_location: str, evidence_links: list[dict[str, Any]]) -> dict[str, Any]:
    validate_message(text, status="queued", evidence_links=evidence_links, team_visible=True)
    return create_action(
        proposed_by_agent="communications_agent",
        action_type="weekly_update_draft",
        target_system="slack",
        target_location=target_location,
        title="Draft weekly engineering impact summary",
        summary="Weekly summary based on evidence-backed actions.",
        proposed_payload={"text": text},
        evidence_links=evidence_links,
        risk_level="medium",
        impact_score=3,
        visibility_score=5,
        effort_score=5,
    )
