"""Jira integration plugin — bundled, auto-loaded.

Registers 4 tools (issue, search, project, comment) into the ``jira``
toolset. Each tool's handler is gated by ``_check_jira_available()`` —
when the user has not run ``hermes auth jira``, the tools stay registered
(visible in ``hermes tools``) but dispatch is blocked with a clear error.

Auth flow: ``hermes auth jira`` stores the Jira domain, email, and API
token in ``~/.hermes/auth.json`` under ``providers.jira``. The client
reads these at call time — no token refresh needed (API tokens are
long-lived).
"""

from __future__ import annotations

from plugins.jira.tools import (
    JIRA_COMMENT_SCHEMA,
    JIRA_ISSUE_SCHEMA,
    JIRA_PROJECT_SCHEMA,
    JIRA_SEARCH_SCHEMA,
    _check_jira_available,
    _handle_jira_comment,
    _handle_jira_issue,
    _handle_jira_project,
    _handle_jira_search,
)

_TOOLS = (
    ("jira_issue",   JIRA_ISSUE_SCHEMA,   _handle_jira_issue,   "🎫"),
    ("jira_search",  JIRA_SEARCH_SCHEMA,  _handle_jira_search,  "🔍"),
    ("jira_project", JIRA_PROJECT_SCHEMA, _handle_jira_project, "📁"),
    ("jira_comment", JIRA_COMMENT_SCHEMA, _handle_jira_comment, "💬"),
)


def register(ctx) -> None:
    """Register all Jira tools. Called once by the plugin loader."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="jira",
            schema=schema,
            handler=handler,
            check_fn=_check_jira_available,
            emoji=emoji,
        )
