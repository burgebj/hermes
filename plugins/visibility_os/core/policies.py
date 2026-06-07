from __future__ import annotations

class ActionPolicyError(RuntimeError):
    """Raised when an action violates approval/execution policy."""


WRITE_ACTIONS_REQUIRE_APPROVAL = {
    "slack_message", "slack_thread_reply", "github_issue_comment", "github_pr_comment",
    "github_pr_review_draft", "github_pr_creation", "github_pr_merge", "github_branch_push", "jira_ticket_update",
    "jira_ticket_creation", "docs_publication", "incident_update", "release_note",
    "deployment", "production_config_change", "weekly_update_draft",
}

HARD_BLOCKED_ACTIONS = {
    "merge_pull_request", "github_pr_merge", "production_deploy", "deployment", "delete_branch",
    "close_customer_ticket", "mute_alert", "change_permissions", "send_message_to_executive_channel",
    "production_config_change",
}

VALID_STATUSES = {
    "drafted", "queued", "needs_review", "approved", "rejected", "edited_by_human",
    "executed", "failed", "cancelled", "expired",
}

VALID_TRANSITIONS = {
    "drafted": {"queued", "cancelled"},
    "queued": {"approved", "rejected", "needs_review", "edited_by_human", "cancelled", "expired"},
    "needs_review": {"queued", "rejected", "cancelled"},
    "edited_by_human": {"approved", "queued", "rejected", "cancelled", "edited_by_human"},
    "approved": {"executed", "failed", "cancelled"},
    "rejected": set(), "executed": set(), "failed": set(), "cancelled": set(), "expired": set(),
}


def validate_transition(current: str, new: str) -> None:
    if current not in VALID_TRANSITIONS or new not in VALID_STATUSES:
        raise ActionPolicyError(f"Unknown action status transition {current!r} -> {new!r}")
    if new not in VALID_TRANSITIONS[current]:
        raise ActionPolicyError(f"Invalid action status transition {current!r} -> {new!r}")
