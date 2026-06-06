"""Jira REST API v3 client used by Hermes native tools."""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Optional

import httpx

# Imported at module level so tests can monkeypatch it without going through the
# hermes_cli.auth import chain inside _resolve_runtime.
try:
    from hermes_cli.auth import resolve_jira_runtime_credentials
except ImportError:
    def resolve_jira_runtime_credentials():  # type: ignore[misc]
        raise RuntimeError("hermes_cli not available")


class JiraError(RuntimeError):
    """Base Jira tool error."""


class JiraAuthRequiredError(JiraError):
    """Raised when the user needs to run `hermes auth jira` first."""


class JiraAPIError(JiraError):
    """Structured Jira API failure."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class JiraClient:
    def __init__(self) -> None:
        self._runtime = self._resolve_runtime()

    def _resolve_runtime(self) -> Dict[str, Any]:
        try:
            return resolve_jira_runtime_credentials()
        except Exception as exc:
            raise JiraAuthRequiredError(str(exc)) from exc

    @property
    def base_url(self) -> str:
        return str(self._runtime.get("base_url") or "").rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Basic {self._runtime['basic_token']}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        response = httpx.request(
            method,
            url,
            headers=self._headers(),
            params={k: v for k, v in (params or {}).items() if v is not None},
            json=json_body,
            timeout=30.0,
        )
        if response.status_code == 401:
            raise JiraAuthRequiredError(
                "Jira authentication failed or token expired. Run `hermes auth jira` again."
            )
        if response.status_code >= 400:
            self._raise_api_error(response, method=method, path=path)
        if response.status_code == 204 or not response.content:
            return {"success": True, "status_code": response.status_code}
        return response.json()

    def _raise_api_error(
        self, response: httpx.Response, *, method: str, path: str
    ) -> None:
        try:
            body = response.json()
            msgs: List[str] = body.get("errorMessages") or []
            errs: Dict[str, str] = body.get("errors") or {}
            detail = (
                "; ".join(msgs)
                or "; ".join(f"{k}: {v}" for k, v in errs.items())
                or response.text.strip()
            )
        except Exception:
            detail = response.text.strip()
        raise JiraAPIError(
            f"Jira API error {response.status_code} [{method} {path}]: {detail}",
            status_code=response.status_code,
            response_body=response.text,
        )

    # -------------------------------------------------------------------------
    # Issue operations
    # -------------------------------------------------------------------------

    def get_issue(self, issue_key: str, *, fields: Optional[str] = None) -> Any:
        return self.request(
            "GET",
            f"/issue/{issue_key}",
            params={"fields": fields or "summary,status,assignee,priority,issuetype,description,created,updated,labels,components"},
        )

    def create_issue(
        self,
        project_key: str,
        issuetype: str,
        summary: str,
        *,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Any:
        fields: Dict[str, Any] = {
            "project": {"key": project_key.upper()},
            "issuetype": {"name": issuetype},
            "summary": summary,
        }
        if description:
            fields["description"] = text_to_adf(description)
        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}
        if priority:
            fields["priority"] = {"name": priority}
        if labels:
            fields["labels"] = labels
        return self.request("POST", "/issue", json_body={"fields": fields})

    def update_issue(
        self,
        issue_key: str,
        *,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Any:
        fields: Dict[str, Any] = {}
        if summary is not None:
            fields["summary"] = summary
        if description is not None:
            fields["description"] = text_to_adf(description)
        if assignee_id is not None:
            fields["assignee"] = {"accountId": assignee_id} if assignee_id else None
        if priority is not None:
            fields["priority"] = {"name": priority}
        if labels is not None:
            fields["labels"] = labels
        return self.request("PUT", f"/issue/{issue_key}", json_body={"fields": fields})

    def get_transitions(self, issue_key: str) -> Any:
        return self.request("GET", f"/issue/{issue_key}/transitions")

    def transition_issue(self, issue_key: str, transition_id: str) -> Any:
        return self.request(
            "POST",
            f"/issue/{issue_key}/transitions",
            json_body={"transition": {"id": str(transition_id)}},
        )

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def search(
        self,
        jql: str,
        *,
        max_results: int = 20,
        fields: Optional[str] = None,
    ) -> Any:
        return self.request(
            "GET",
            "/search",
            params={
                "jql": jql,
                "maxResults": max_results,
                "fields": fields or "summary,status,assignee,priority,issuetype,created,updated",
            },
        )

    # -------------------------------------------------------------------------
    # Projects
    # -------------------------------------------------------------------------

    def list_projects(self, *, max_results: int = 50) -> Any:
        return self.request(
            "GET",
            "/project",
            params={"maxResults": max_results, "orderBy": "name"},
        )

    def get_project(self, project_key: str) -> Any:
        return self.request("GET", f"/project/{project_key.upper()}")

    # -------------------------------------------------------------------------
    # Comments
    # -------------------------------------------------------------------------

    def get_comments(self, issue_key: str, *, max_results: int = 20) -> Any:
        return self.request(
            "GET",
            f"/issue/{issue_key}/comment",
            params={"maxResults": max_results},
        )

    def add_comment(self, issue_key: str, body: str) -> Any:
        return self.request(
            "POST",
            f"/issue/{issue_key}/comment",
            json_body={"body": text_to_adf(body)},
        )

    # -------------------------------------------------------------------------
    # User / connectivity
    # -------------------------------------------------------------------------

    def get_myself(self) -> Any:
        return self.request("GET", "/myself")


# ---------------------------------------------------------------------------
# Atlassian Document Format helpers
# ---------------------------------------------------------------------------

def text_to_adf(text: str) -> Dict[str, Any]:
    """Convert plain text to Atlassian Document Format (ADF).

    Splits on double newlines to create separate paragraphs.
    Code blocks (``` delimited) are preserved as codeBlock nodes.
    """
    content = []
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if para.startswith("```") and para.endswith("```"):
            inner = para[3:-3]
            lang = ""
            if "\n" in inner:
                first_line, rest = inner.split("\n", 1)
                if first_line.strip() and " " not in first_line.strip():
                    lang = first_line.strip()
                    inner = rest
            content.append({
                "type": "codeBlock",
                "attrs": {"language": lang} if lang else {},
                "content": [{"type": "text", "text": inner}],
            })
        else:
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": para}],
            })
    if not content:
        content = [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]
    return {"version": 1, "type": "doc", "content": content}


def adf_to_text(adf: Any) -> str:
    """Extract plain text from an ADF document for display."""
    if not isinstance(adf, dict):
        return str(adf) if adf else ""
    parts: List[str] = []

    def _extract(node: Any) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") == "text":
            parts.append(str(node.get("text") or ""))
        for child in node.get("content") or []:
            _extract(child)
        if node.get("type") in ("paragraph", "heading", "codeBlock", "bulletList", "orderedList"):
            if parts and not parts[-1].endswith("\n"):
                parts.append("\n")

    _extract(adf)
    return "".join(parts).strip()


def make_basic_token(email: str, api_token: str) -> str:
    """Return the Base64-encoded Basic Auth token for Jira API."""
    raw = f"{email}:{api_token}"
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")
