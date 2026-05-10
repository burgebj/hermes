"""Feishu Task Hierarchy Tool -- tasklist and subtask operations via Feishu Task v2 API.

Provides four tools for managing Feishu task hierarchy:
  - ``feishu_task_list_tasklists``  -- list user's tasklists
  - ``feishu_task_create_tasklist`` -- create a new tasklist
  - ``feishu_task_list_sections``   -- list sections inside a tasklist
  - ``feishu_task_create_subtask``  -- create a subtask under a parent task

Uses FeishuClient.for_user() (UAT) with scope ``task:task``.
"""

import logging

from tools.feishu_oapi_client import (
    AppScopeMissingError,
    FeishuClient,
    NeedAuthorizationError,
    TOOLS_METADATA,
    UserAuthRequiredError,
    UserScopeInsufficientError,
    raise_for_feishu_errcode,
)
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# TOOLS_METADATA entries (scope declarations)
# ---------------------------------------------------------------------------

TOOLS_METADATA["feishu_task_list_tasklists"] = {"identity": "user", "scopes": ["task:tasklist:read"]}
TOOLS_METADATA["feishu_task_create_tasklist"] = {"identity": "user", "scopes": ["task:tasklist:write"]}
TOOLS_METADATA["feishu_task_list_sections"] = {"identity": "user", "scopes": ["task:section:read"]}
TOOLS_METADATA["feishu_task_create_subtask"] = {"identity": "user", "scopes": ["task:task"]}


def _check_feishu():
    try:
        import lark_oapi  # noqa: F401
        return True
    except ImportError:
        return False


def _auth_error_message(exc: Exception) -> str:
    """Format semantic auth exceptions as tool_error strings."""
    if isinstance(exc, NeedAuthorizationError):
        return f"Need Feishu authorization: {exc}. Run 'hermes feishu-uat' to authorize."
    if isinstance(exc, AppScopeMissingError):
        return f"App scope missing: {exc}"
    if isinstance(exc, UserAuthRequiredError):
        return f"User authorization required: {exc}"
    if isinstance(exc, UserScopeInsufficientError):
        return f"User scope insufficient: {exc}"
    return str(exc)


def _get_user_client():
    """Return (client, error_str). error_str is None on success."""
    try:
        return FeishuClient.for_user(), None
    except NeedAuthorizationError as exc:
        return None, _auth_error_message(exc)
    except ValueError as exc:
        return None, f"Feishu configuration error: {exc}"


def _do_request(client, method, uri, *, paths=None, queries=None, body=None):
    """Build and execute a BaseRequest with UAT, return (code, msg, data).

    Supports GET, POST HTTP methods.
    """
    try:
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError as exc:
        raise RuntimeError("lark_oapi not installed") from exc

    import json

    method_upper = method.upper()
    http_method = HttpMethod.GET if method_upper == "GET" else HttpMethod.POST

    builder = (
        BaseRequest.builder()
        .http_method(http_method)
        .uri(uri)
        .token_types({AccessTokenType.USER})
    )
    if paths:
        builder = builder.paths(paths)
    if queries:
        builder = builder.queries(queries)
    if body is not None:
        builder = builder.body(body)

    request = builder.build()

    opt = (
        RequestOption.builder()
        .user_access_token(client.access_token)
        .build()
    )
    response = client.sdk.request(request, opt)

    code = getattr(response, "code", None)
    msg = getattr(response, "msg", "")

    data: dict = {}
    raw = getattr(response, "raw", None)
    if raw and hasattr(raw, "content"):
        try:
            body_json = json.loads(raw.content)
            data = body_json.get("data", {})
            if code is None:
                code = body_json.get("code", -1)
            if not msg:
                msg = body_json.get("msg", "")
        except (json.JSONDecodeError, AttributeError):
            pass
    if not data:
        resp_data = getattr(response, "data", None)
        if isinstance(resp_data, dict):
            data = resp_data
        elif resp_data and hasattr(resp_data, "__dict__"):
            data = vars(resp_data)

    return (code if code is not None else -1), msg, data


# ---------------------------------------------------------------------------
# feishu_task_list_tasklists
# ---------------------------------------------------------------------------

_TASKLIST_LIST_URI = "/open-apis/task/v2/tasklists"

FEISHU_TASK_LIST_TASKLISTS_SCHEMA = {
    "name": "feishu_task_list_tasklists",
    "description": "List the current user's Feishu tasklists.",
    "parameters": {
        "type": "object",
        "properties": {
            "page_size": {
                "type": "integer",
                "description": "Number of tasklists per page (max 100, default 50).",
                "default": 50,
            },
            "page_token": {
                "type": "string",
                "description": "Pagination token for the next page.",
            },
        },
        "required": [],
    },
}


def _handle_task_list_tasklists(args: dict, **kwargs) -> str:
    logger.info("feishu_task_list_tasklists called")
    client, err = _get_user_client()
    if err:
        return tool_error(err)

    queries = [("user_id_type", "open_id")]

    page_size = args.get("page_size", 50)
    queries.append(("page_size", str(page_size)))

    page_token = (args.get("page_token") or "").strip()
    if page_token:
        queries.append(("page_token", page_token))

    code, msg, data = _do_request(client, "GET", _TASKLIST_LIST_URI, queries=queries)
    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu.task.list_tasklists")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("feishu_task_list_tasklists failed: code=%d msg=%s", code, msg)
        return tool_error(f"List tasklists failed: code={code} msg={msg}")

    logger.info("feishu_task_list_tasklists: returned %d items", len((data or {}).get("items", [])))
    return tool_result(data)


# ---------------------------------------------------------------------------
# feishu_task_create_tasklist
# ---------------------------------------------------------------------------

FEISHU_TASK_CREATE_TASKLIST_SCHEMA = {
    "name": "feishu_task_create_tasklist",
    "description": "Create a new Feishu tasklist with an optional member list.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Tasklist name (required).",
            },
            "members": {
                "type": "array",
                "description": (
                    "Optional list of members. Each item must have 'id' and 'type' "
                    "('user' or 'docx')."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Member open_id or docx token."},
                        "type": {"type": "string", "description": "'user' or 'docx'."},
                    },
                    "required": ["id", "type"],
                },
            },
        },
        "required": ["name"],
    },
}


def _handle_task_create_tasklist(args: dict, **kwargs) -> str:
    name = (args.get("name") or "").strip()
    logger.info("feishu_task_create_tasklist: name=%r", name)
    client, err = _get_user_client()
    if err:
        return tool_error(err)

    if not name:
        return tool_error("name is required")

    body: dict = {"name": name, "user_id_type": "open_id"}

    members = args.get("members")
    if members:
        body["members"] = [
            {"id": m.get("id", ""), "type": m.get("type", "user")}
            for m in members
            if m.get("id")
        ]

    code, msg, data = _do_request(
        client, "POST", _TASKLIST_LIST_URI,
        queries=[("user_id_type", "open_id")],
        body=body,
    )
    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu.task.create_tasklist")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("feishu_task_create_tasklist failed: code=%d msg=%s", code, msg)
        return tool_error(f"Create tasklist failed: code={code} msg={msg}")

    logger.info("feishu_task_create_tasklist: created tasklist name=%r", name)
    return tool_result(success=True, data=data)


# ---------------------------------------------------------------------------
# feishu_task_list_sections
# ---------------------------------------------------------------------------

_TASKLIST_SECTIONS_URI = "/open-apis/task/v2/sections"

FEISHU_TASK_LIST_SECTIONS_SCHEMA = {
    "name": "feishu_task_list_sections",
    "description": "List sections inside a Feishu tasklist.",
    "parameters": {
        "type": "object",
        "properties": {
            "tasklist_guid": {
                "type": "string",
                "description": "The GUID of the tasklist whose sections to list.",
            },
            "page_size": {
                "type": "integer",
                "description": "Number of sections per page (max 100, default 50).",
                "default": 50,
            },
            "page_token": {
                "type": "string",
                "description": "Pagination token for the next page.",
            },
        },
        "required": ["tasklist_guid"],
    },
}


def _handle_task_list_sections(args: dict, **kwargs) -> str:
    tasklist_guid = (args.get("tasklist_guid") or "").strip()
    logger.info("feishu_task_list_sections: tasklist_guid=%s", tasklist_guid)
    client, err = _get_user_client()
    if err:
        return tool_error(err)

    if not tasklist_guid:
        return tool_error("tasklist_guid is required")

    queries = [
        ("user_id_type", "open_id"),
        ("resource_type", "tasklist"),
        ("resource_id", tasklist_guid),
    ]

    page_size = args.get("page_size", 50)
    queries.append(("page_size", str(page_size)))

    page_token = (args.get("page_token") or "").strip()
    if page_token:
        queries.append(("page_token", page_token))

    code, msg, data = _do_request(
        client, "GET", _TASKLIST_SECTIONS_URI,
        queries=queries,
    )
    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu.task.list_sections")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("feishu_task_list_sections failed: code=%d msg=%s", code, msg)
        return tool_error(f"List sections failed: code={code} msg={msg}")

    logger.info("feishu_task_list_sections: returned %d items", len((data or {}).get("items", [])))
    return tool_result(data)


# ---------------------------------------------------------------------------
# feishu_task_create_subtask
# ---------------------------------------------------------------------------

_TASK_SUBTASK_URI = "/open-apis/task/v2/tasks/:task_guid/subtasks"

FEISHU_TASK_CREATE_SUBTASK_SCHEMA = {
    "name": "feishu_task_create_subtask",
    "description": "Create a subtask under a parent Feishu task.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_guid": {
                "type": "string",
                "description": "The GUID of the parent task.",
            },
            "summary": {
                "type": "string",
                "description": "Subtask title/summary (required).",
            },
            "completed_at": {
                "type": "string",
                "description": "Completion timestamp (optional, RFC3339 or epoch string).",
            },
            "due": {
                "type": "object",
                "description": "Due date object (optional), e.g. {\"timestamp\": \"...\", \"is_all_day\": false}.",
            },
        },
        "required": ["task_guid", "summary"],
    },
}


def _handle_task_create_subtask(args: dict, **kwargs) -> str:
    task_guid = (args.get("task_guid") or "").strip()
    summary = (args.get("summary") or "").strip()
    logger.info("feishu_task_create_subtask: task_guid=%s summary=%r", task_guid, summary)
    client, err = _get_user_client()
    if err:
        return tool_error(err)

    if not task_guid:
        return tool_error("task_guid is required")
    if not summary:
        return tool_error("summary is required")

    body: dict = {"summary": summary, "user_id_type": "open_id"}

    completed_at = (args.get("completed_at") or "").strip()
    if completed_at:
        body["completed_at"] = completed_at

    due = args.get("due")
    if due and isinstance(due, dict):
        body["due"] = due

    code, msg, data = _do_request(
        client, "POST", _TASK_SUBTASK_URI,
        paths={"task_guid": task_guid},
        queries=[("user_id_type", "open_id")],
        body=body,
    )
    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu.task.create_subtask")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("feishu_task_create_subtask failed: code=%d msg=%s", code, msg)
        return tool_error(f"Create subtask failed: code={code} msg={msg}")

    logger.info("feishu_task_create_subtask: created subtask under task %s", task_guid)
    return tool_result(success=True, data=data)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_task_list_tasklists",
    toolset="feishu_task",
    schema=FEISHU_TASK_LIST_TASKLISTS_SCHEMA,
    handler=_handle_task_list_tasklists,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List the current user's Feishu tasklists",
    emoji="✅",
)

registry.register(
    name="feishu_task_create_tasklist",
    toolset="feishu_task",
    schema=FEISHU_TASK_CREATE_TASKLIST_SCHEMA,
    handler=_handle_task_create_tasklist,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Create a new Feishu tasklist",
    emoji="✅",
)

registry.register(
    name="feishu_task_list_sections",
    toolset="feishu_task",
    schema=FEISHU_TASK_LIST_SECTIONS_SCHEMA,
    handler=_handle_task_list_sections,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List sections inside a Feishu tasklist",
    emoji="✅",
)

registry.register(
    name="feishu_task_create_subtask",
    toolset="feishu_task",
    schema=FEISHU_TASK_CREATE_SUBTASK_SCHEMA,
    handler=_handle_task_create_subtask,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Create a subtask under a parent Feishu task",
    emoji="✅",
)
