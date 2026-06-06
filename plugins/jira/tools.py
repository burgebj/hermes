"""Native Jira tools for Hermes (registered via plugins/jira)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hermes_cli.auth import get_auth_status
from plugins.jira.client import (
    JiraAPIError,
    JiraAuthRequiredError,
    JiraClient,
    JiraError,
    adf_to_text,
)
from tools.registry import tool_error, tool_result


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def _check_jira_available() -> bool:
    try:
        return bool(get_auth_status("jira").get("logged_in"))
    except Exception:
        return False


def _jira_client() -> JiraClient:
    return JiraClient()


def _jira_tool_error(exc: Exception) -> str:
    if isinstance(exc, JiraAuthRequiredError):
        return tool_error(
            str(exc),
            hint="Run `hermes auth jira` to authenticate.",
        )
    if isinstance(exc, JiraAPIError):
        return tool_error(str(exc), status_code=exc.status_code)
    if isinstance(exc, JiraError):
        return tool_error(str(exc))
    return tool_error(f"Jira tool failed: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coerce_int(raw: Any, default: int, minimum: int = 1, maximum: int = 100) -> int:
    try:
        return max(minimum, min(maximum, int(raw)))
    except Exception:
        return default


def _as_list(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(i).strip() for i in raw if str(i).strip()]
    return [str(raw).strip()] if str(raw).strip() else []


def _issue_url(issue: Dict[str, Any]) -> str:
    """Build a browse URL from the issue's self link, guarding against malformed URLs."""
    self_link = issue.get("self") or ""
    key = issue.get("key") or ""
    if not self_link or not key:
        return ""
    parts = self_link.split("/")
    # self link format: https://domain/rest/api/3/issue/ID → parts[2] = domain
    if len(parts) < 3:
        return ""
    return f"https://{parts[2]}/browse/{key}"


def _format_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a Jira issue object for cleaner tool output."""
    fields = issue.get("fields") or {}
    status = (fields.get("status") or {}).get("name") or ""
    assignee = fields.get("assignee") or {}
    priority = (fields.get("priority") or {}).get("name") or ""
    issuetype = (fields.get("issuetype") or {}).get("name") or ""
    raw_desc = fields.get("description")
    description = adf_to_text(raw_desc) if isinstance(raw_desc, dict) else (raw_desc or "")
    return {
        "key": issue.get("key") or "",
        "summary": fields.get("summary") or "",
        "status": status,
        "issuetype": issuetype,
        "priority": priority,
        "assignee": assignee.get("displayName") or assignee.get("emailAddress") or "",
        "assignee_account_id": assignee.get("accountId") or "",
        "labels": fields.get("labels") or [],
        "created": fields.get("created") or "",
        "updated": fields.get("updated") or "",
        "description": description[:500] + "…" if len(description) > 500 else description,
        "url": _issue_url(issue),
    }


# ---------------------------------------------------------------------------
# jira_issue tool
# ---------------------------------------------------------------------------

JIRA_ISSUE_SCHEMA = {
    "name": "jira_issue",
    "description": (
        "Manage Jira issues: get details, create new issues, update fields, "
        "list available status transitions, or transition an issue to a new status. "
        "Requires Jira Cloud authentication (run `hermes auth jira` first)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get", "create", "update", "transitions", "transition"],
                "description": (
                    "get — fetch full issue details by key. "
                    "create — create a new issue. "
                    "update — update fields of an existing issue. "
                    "transitions — list available status transitions for an issue. "
                    "transition — move an issue to a new status by transition ID."
                ),
            },
            "issue_key": {
                "type": "string",
                "description": "Issue key (e.g. PROJ-123). Required for get/update/transitions/transition.",
            },
            "project_key": {
                "type": "string",
                "description": "Project key (e.g. PROJ). Required for create.",
            },
            "issuetype": {
                "type": "string",
                "description": "Issue type name: Bug, Task, Story, Epic, Sub-task, etc. Required for create.",
            },
            "summary": {
                "type": "string",
                "description": "Issue title/summary. Required for create; optional for update.",
            },
            "description": {
                "type": "string",
                "description": "Issue description as plain text. Converted to Atlassian Document Format automatically.",
            },
            "assignee_id": {
                "type": "string",
                "description": "Atlassian account ID of the assignee. Use jira_search to find account IDs.",
            },
            "priority": {
                "type": "string",
                "description": "Priority name: Highest, High, Medium, Low, Lowest.",
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of label strings to apply.",
            },
            "transition_id": {
                "type": "string",
                "description": "Transition ID to apply. Get available IDs from action='transitions'.",
            },
        },
        "required": ["action"],
    },
}


def _handle_jira_issue(args: Dict[str, Any], **kw: Any) -> str:
    action = str(args.get("action") or "get").strip().lower()
    client = _jira_client()

    try:
        if action == "get":
            key = str(args.get("issue_key") or "").strip().upper()
            if not key:
                return tool_error("issue_key is required for action='get'")
            raw = client.get_issue(key)
            return tool_result(_format_issue(raw))

        if action == "create":
            project = str(args.get("project_key") or "").strip()
            issuetype = str(args.get("issuetype") or "Task").strip()
            summary = str(args.get("summary") or "").strip()
            if not project:
                return tool_error("project_key is required for action='create'")
            if not summary:
                return tool_error("summary is required for action='create'")
            result = client.create_issue(
                project,
                issuetype,
                summary,
                description=args.get("description"),
                assignee_id=args.get("assignee_id"),
                priority=args.get("priority"),
                labels=_as_list(args.get("labels")),
            )
            return tool_result({
                "created": True,
                "key": result.get("key") or "",
                "id": result.get("id") or "",
                "self": result.get("self") or "",
            })

        if action == "update":
            key = str(args.get("issue_key") or "").strip().upper()
            if not key:
                return tool_error("issue_key is required for action='update'")
            labels_raw = args.get("labels")
            labels = _as_list(labels_raw) if labels_raw is not None else None
            client.update_issue(
                key,
                summary=args.get("summary"),
                description=args.get("description"),
                assignee_id=args.get("assignee_id"),
                priority=args.get("priority"),
                labels=labels,
            )
            return tool_result({"updated": True, "key": key})

        if action == "transitions":
            key = str(args.get("issue_key") or "").strip().upper()
            if not key:
                return tool_error("issue_key is required for action='transitions'")
            raw = client.get_transitions(key)
            transitions = [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "to_status": (t.get("to") or {}).get("name"),
                }
                for t in (raw.get("transitions") or [])
            ]
            return tool_result({"issue_key": key, "transitions": transitions})

        if action == "transition":
            key = str(args.get("issue_key") or "").strip().upper()
            tid = str(args.get("transition_id") or "").strip()
            if not key:
                return tool_error("issue_key is required for action='transition'")
            if not tid:
                return tool_error("transition_id is required for action='transition'. Use action='transitions' to list options.")
            client.transition_issue(key, tid)
            return tool_result({"transitioned": True, "key": key, "transition_id": tid})

        return tool_error(f"Unknown action '{action}'. Valid actions: get, create, update, transitions, transition.")

    except Exception as exc:
        return _jira_tool_error(exc)


# ---------------------------------------------------------------------------
# jira_search tool
# ---------------------------------------------------------------------------

JIRA_SEARCH_SCHEMA = {
    "name": "jira_search",
    "description": (
        "Search Jira issues using JQL (Jira Query Language). "
        "Examples: 'project=PROJ AND status=\"In Progress\"', "
        "'assignee=currentUser() AND sprint in openSprints()', "
        "'text~\"login bug\" ORDER BY created DESC'. "
        "Returns a compact list of matching issues."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "jql": {
                "type": "string",
                "description": "JQL query string. See https://support.atlassian.com/jira-software-cloud/docs/use-advanced-search-with-jira-query-language-jql/",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (1-50, default 20).",
                "default": 20,
            },
        },
        "required": ["jql"],
    },
}


def _handle_jira_search(args: Dict[str, Any], **kw: Any) -> str:
    jql = str(args.get("jql") or "").strip()
    if not jql:
        return tool_error("jql is required")
    max_results = _coerce_int(args.get("max_results"), default=20, minimum=1, maximum=50)
    client = _jira_client()
    try:
        raw = client.search(jql, max_results=max_results)
        issues = [_format_issue(i) for i in (raw.get("issues") or [])]
        return tool_result({
            "total": raw.get("total") or len(issues),
            "returned": len(issues),
            "jql": jql,
            "issues": issues,
        })
    except Exception as exc:
        return _jira_tool_error(exc)


# ---------------------------------------------------------------------------
# jira_project tool
# ---------------------------------------------------------------------------

JIRA_PROJECT_SCHEMA = {
    "name": "jira_project",
    "description": (
        "List all accessible Jira projects or get details about a specific project. "
        "Use this to discover project keys required for jira_issue create."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "get"],
                "description": "list — list all projects. get — get details for a specific project.",
                "default": "list",
            },
            "project_key": {
                "type": "string",
                "description": "Project key (e.g. PROJ). Required for action='get'.",
            },
            "max_results": {
                "type": "integer",
                "description": "Max projects to return for action='list' (1-100, default 50).",
                "default": 50,
            },
        },
        "required": ["action"],
    },
}


def _handle_jira_project(args: Dict[str, Any], **kw: Any) -> str:
    action = str(args.get("action") or "list").strip().lower()
    client = _jira_client()

    try:
        if action == "list":
            max_results = _coerce_int(args.get("max_results"), default=50, minimum=1, maximum=100)
            raw = client.list_projects(max_results=max_results)
            projects = [
                {
                    "key": p.get("key") or "",
                    "name": p.get("name") or "",
                    "type": p.get("projectTypeKey") or "",
                    "style": p.get("style") or "",
                }
                for p in (raw if isinstance(raw, list) else [])
            ]
            return tool_result({"count": len(projects), "projects": projects})

        if action == "get":
            key = str(args.get("project_key") or "").strip().upper()
            if not key:
                return tool_error("project_key is required for action='get'")
            raw = client.get_project(key)
            return tool_result({
                "key": raw.get("key") or "",
                "name": raw.get("name") or "",
                "type": raw.get("projectTypeKey") or "",
                "description": raw.get("description") or "",
                "lead": ((raw.get("lead") or {}).get("displayName")) or "",
                "url": raw.get("self") or "",
            })

        return tool_error(f"Unknown action '{action}'. Valid: list, get.")

    except Exception as exc:
        return _jira_tool_error(exc)


# ---------------------------------------------------------------------------
# jira_comment tool
# ---------------------------------------------------------------------------

JIRA_COMMENT_SCHEMA = {
    "name": "jira_comment",
    "description": (
        "Read or add comments on a Jira issue. "
        "Use action='list' to fetch existing comments and action='add' to post a new one."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "add"],
                "description": "list — get all comments on an issue. add — post a new comment.",
            },
            "issue_key": {
                "type": "string",
                "description": "Issue key (e.g. PROJ-123).",
            },
            "body": {
                "type": "string",
                "description": "Comment text. Required for action='add'. Plain text is accepted.",
            },
            "max_results": {
                "type": "integer",
                "description": "Max comments to return for action='list' (default 20).",
                "default": 20,
            },
        },
        "required": ["action", "issue_key"],
    },
}


def _handle_jira_comment(args: Dict[str, Any], **kw: Any) -> str:
    action = str(args.get("action") or "list").strip().lower()
    key = str(args.get("issue_key") or "").strip().upper()
    if not key:
        return tool_error("issue_key is required")
    client = _jira_client()

    try:
        if action == "list":
            max_results = _coerce_int(args.get("max_results"), default=20, minimum=1, maximum=100)
            raw = client.get_comments(key, max_results=max_results)
            comments = [
                {
                    "id": c.get("id") or "",
                    "author": ((c.get("author") or {}).get("displayName")) or "",
                    "created": c.get("created") or "",
                    "updated": c.get("updated") or "",
                    "body": adf_to_text(c.get("body")) if isinstance(c.get("body"), dict) else str(c.get("body") or ""),
                }
                for c in (raw.get("comments") or [])
            ]
            return tool_result({
                "issue_key": key,
                "total": raw.get("total") or len(comments),
                "comments": comments,
            })

        if action == "add":
            body = str(args.get("body") or "").strip()
            if not body:
                return tool_error("body is required for action='add'")
            result = client.add_comment(key, body)
            return tool_result({
                "added": True,
                "issue_key": key,
                "comment_id": result.get("id") or "",
                "created": result.get("created") or "",
            })

        return tool_error(f"Unknown action '{action}'. Valid: list, add.")

    except Exception as exc:
        return _jira_tool_error(exc)
