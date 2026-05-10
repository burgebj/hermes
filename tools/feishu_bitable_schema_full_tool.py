"""Feishu Bitable Schema Full Tool -- field and view CRUD via Feishu/Lark API.

Provides six tools for Feishu Bitable field/view operations:
  - ``feishu_bitable_create_field`` -- create a new field in a table
  - ``feishu_bitable_update_field`` -- update an existing field
  - ``feishu_bitable_delete_field`` -- delete a field by field_id
  - ``feishu_bitable_list_views``   -- list views for a table
  - ``feishu_bitable_create_view``  -- create a new view
  - ``feishu_bitable_delete_view``  -- delete a view by view_id

All tools use UAT (user_access_token) via FeishuClient.for_user() and require
the bitable:app scope.
"""

import json
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
# TOOLS_METADATA — declare scopes and identity for all tools in this module
# ---------------------------------------------------------------------------

_FULL_SCHEMA_TOOLS = [
    "feishu_bitable_create_field",
    "feishu_bitable_update_field",
    "feishu_bitable_delete_field",
    "feishu_bitable_list_views",
    "feishu_bitable_create_view",
    "feishu_bitable_delete_view",
]

for _tool_name in _FULL_SCHEMA_TOOLS:
    TOOLS_METADATA[_tool_name] = {
        "identity": "user",
        "scopes": ["bitable:app"],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_feishu():
    """Check if lark_oapi is available."""
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


def _handle_api_error(code, msg, api_name):
    """Raise semantic error for known codes, return tool_error string otherwise."""
    try:
        raise_for_feishu_errcode(code, msg or "", api_name=api_name)
    except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
        return tool_error(_auth_error_message(e))
    return None


def _do_raw_request(client: FeishuClient, method: str, uri: str, *, paths: dict = None, queries: list = None, body: dict = None) -> tuple:
    """Execute a BaseRequest with any HTTP method (GET/POST/PUT/DELETE/PATCH).

    Args:
        client: FeishuClient with access_token for UAT.
        method: HTTP method string.
        uri: Feishu open-api URI with :param placeholders.
        paths: Path parameter substitution dict.
        queries: List of (key, value) query tuples.
        body: JSON body dict.

    Returns:
        Tuple of (code, msg, data_dict).
    """
    try:
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError as exc:
        raise RuntimeError("lark_oapi not installed") from exc

    method_map = {
        "GET": HttpMethod.GET,
        "POST": HttpMethod.POST,
        "PUT": HttpMethod.PUT,
        "DELETE": HttpMethod.DELETE,
        "PATCH": HttpMethod.PATCH,
    }
    http_method = method_map.get(method.upper(), HttpMethod.POST)

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
            if code is None:
                code = body_json.get("code", -1)
            if not msg:
                msg = body_json.get("msg", "")
            data = body_json.get("data", {})
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
# feishu_bitable_create_field
# ---------------------------------------------------------------------------

_CREATE_FIELD_URI = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/fields"

FEISHU_BITABLE_CREATE_FIELD_SCHEMA = {
    "name": "feishu_bitable_create_field",
    "description": (
        "Create a new field in a Feishu Bitable table. "
        "Returns the created field object including field_id."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "app_token": {
                "type": "string",
                "description": "The bitable app token.",
            },
            "table_id": {
                "type": "string",
                "description": "The data table ID.",
            },
            "field_name": {
                "type": "string",
                "description": "Name of the new field.",
            },
            "type": {
                "type": "integer",
                "description": "Field type integer (e.g. 1=text, 2=number, 3=single_select).",
            },
            "property": {
                "type": "object",
                "description": "Optional field property configuration dict.",
            },
            "description": {
                "type": "string",
                "description": "Optional field description.",
            },
        },
        "required": ["app_token", "table_id", "field_name", "type"],
    },
}


def _handle_bitable_create_field(args: dict, **kwargs) -> str:
    """Handler for feishu_bitable_create_field.

    Args:
        args: Tool arguments containing app_token, table_id, field_name, type,
              and optional property and description.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    app_token = (args.get("app_token") or "").strip()
    table_id = (args.get("table_id") or "").strip()
    field_name = (args.get("field_name") or "").strip()
    field_type = args.get("type")

    if not app_token or not table_id or not field_name or field_type is None:
        return tool_error("app_token, table_id, field_name, and type are required")

    client, err = _get_user_client()
    if err:
        return tool_error(err)

    body: dict = {"field_name": field_name, "type": field_type}
    if args.get("property") is not None:
        body["property"] = args["property"]
    if args.get("description"):
        body["description"] = args["description"]

    logger.info(
        "feishu_bitable_create_field: app_token=%s table_id=%s field_name=%s type=%s",
        app_token, table_id, field_name, field_type,
    )

    code, msg, data = client.do_request(
        "POST", _CREATE_FIELD_URI,
        paths={"app_token": app_token, "table_id": table_id},
        body=body,
        use_uat=True,
    )
    if code != 0:
        err_result = _handle_api_error(code, msg, "feishu.bitable.create_field")
        if err_result:
            return err_result
        logger.warning("feishu_bitable_create_field failed: code=%d msg=%s", code, msg)
        return tool_error(f"Create field failed: code={code} msg={msg}")

    field = data.get("field", data)
    logger.info("feishu_bitable_create_field: created field in app=%s table=%s", app_token, table_id)
    return tool_result(success=True, data={"field": field})


# ---------------------------------------------------------------------------
# feishu_bitable_update_field
# ---------------------------------------------------------------------------

_UPDATE_FIELD_URI = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/fields/:field_id"

FEISHU_BITABLE_UPDATE_FIELD_SCHEMA = {
    "name": "feishu_bitable_update_field",
    "description": (
        "Update an existing field in a Feishu Bitable table. "
        "Returns the updated field object."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "app_token": {
                "type": "string",
                "description": "The bitable app token.",
            },
            "table_id": {
                "type": "string",
                "description": "The data table ID.",
            },
            "field_id": {
                "type": "string",
                "description": "The field ID to update.",
            },
            "field_name": {
                "type": "string",
                "description": "New name for the field.",
            },
            "type": {
                "type": "integer",
                "description": "Field type integer.",
            },
            "property": {
                "type": "object",
                "description": "Optional field property configuration dict.",
            },
            "description": {
                "type": "string",
                "description": "Optional field description.",
            },
        },
        "required": ["app_token", "table_id", "field_id", "field_name", "type"],
    },
}


def _handle_bitable_update_field(args: dict, **kwargs) -> str:
    """Handler for feishu_bitable_update_field.

    Args:
        args: Tool arguments containing app_token, table_id, field_id, field_name,
              type, and optional property and description.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    app_token = (args.get("app_token") or "").strip()
    table_id = (args.get("table_id") or "").strip()
    field_id = (args.get("field_id") or "").strip()
    field_name = (args.get("field_name") or "").strip()
    field_type = args.get("type")

    if not app_token or not table_id or not field_id or not field_name or field_type is None:
        return tool_error("app_token, table_id, field_id, field_name, and type are required")

    client, err = _get_user_client()
    if err:
        return tool_error(err)

    body: dict = {"field_name": field_name, "type": field_type}
    if args.get("property") is not None:
        body["property"] = args["property"]
    if args.get("description"):
        body["description"] = args["description"]

    logger.info(
        "feishu_bitable_update_field: app_token=%s table_id=%s field_id=%s",
        app_token, table_id, field_id,
    )

    code, msg, data = _do_raw_request(
        client, "PUT", _UPDATE_FIELD_URI,
        paths={"app_token": app_token, "table_id": table_id, "field_id": field_id},
        body=body,
    )
    if code != 0:
        err_result = _handle_api_error(code, msg, "feishu.bitable.update_field")
        if err_result:
            return err_result
        logger.warning("feishu_bitable_update_field failed: code=%d msg=%s", code, msg)
        return tool_error(f"Update field failed: code={code} msg={msg}")

    field = data.get("field", data)
    logger.info("feishu_bitable_update_field: updated field_id=%s", field_id)
    return tool_result(success=True, data={"field": field})


# ---------------------------------------------------------------------------
# feishu_bitable_delete_field
# ---------------------------------------------------------------------------

_DELETE_FIELD_URI = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/fields/:field_id"

FEISHU_BITABLE_DELETE_FIELD_SCHEMA = {
    "name": "feishu_bitable_delete_field",
    "description": (
        "Delete a field from a Feishu Bitable table by field_id. "
        "Returns a confirmation that the field was deleted."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "app_token": {
                "type": "string",
                "description": "The bitable app token.",
            },
            "table_id": {
                "type": "string",
                "description": "The data table ID.",
            },
            "field_id": {
                "type": "string",
                "description": "The field ID to delete.",
            },
        },
        "required": ["app_token", "table_id", "field_id"],
    },
}


def _handle_bitable_delete_field(args: dict, **kwargs) -> str:
    """Handler for feishu_bitable_delete_field.

    Args:
        args: Tool arguments containing app_token, table_id, and field_id.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    app_token = (args.get("app_token") or "").strip()
    table_id = (args.get("table_id") or "").strip()
    field_id = (args.get("field_id") or "").strip()

    if not app_token or not table_id or not field_id:
        return tool_error("app_token, table_id, and field_id are required")

    client, err = _get_user_client()
    if err:
        return tool_error(err)

    logger.info(
        "feishu_bitable_delete_field: app_token=%s table_id=%s field_id=%s",
        app_token, table_id, field_id,
    )

    code, msg, data = _do_raw_request(
        client, "DELETE", _DELETE_FIELD_URI,
        paths={"app_token": app_token, "table_id": table_id, "field_id": field_id},
    )
    if code != 0:
        err_result = _handle_api_error(code, msg, "feishu.bitable.delete_field")
        if err_result:
            return err_result
        logger.warning("feishu_bitable_delete_field failed: code=%d msg=%s", code, msg)
        return tool_error(f"Delete field failed: code={code} msg={msg}")

    deleted = data.get("deleted", True)
    logger.info("feishu_bitable_delete_field: deleted field_id=%s", field_id)
    return tool_result(success=True, data={"deleted": deleted, "field_id": field_id})


# ---------------------------------------------------------------------------
# feishu_bitable_list_views
# ---------------------------------------------------------------------------

_LIST_VIEWS_URI = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/views"

FEISHU_BITABLE_LIST_VIEWS_SCHEMA = {
    "name": "feishu_bitable_list_views",
    "description": (
        "List views for a Feishu Bitable table. "
        "Returns view_id, view_name, and view_type for each view."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "app_token": {
                "type": "string",
                "description": "The bitable app token.",
            },
            "table_id": {
                "type": "string",
                "description": "The data table ID.",
            },
            "page_size": {
                "type": "integer",
                "description": "Number of views per page (max 100, default 50).",
                "default": 50,
            },
            "page_token": {
                "type": "string",
                "description": "Pagination token for next page.",
            },
        },
        "required": ["app_token", "table_id"],
    },
}


def _handle_bitable_list_views(args: dict, **kwargs) -> str:
    """Handler for feishu_bitable_list_views.

    Args:
        args: Tool arguments containing app_token, table_id, optional page_size
              and page_token.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    app_token = (args.get("app_token") or "").strip()
    table_id = (args.get("table_id") or "").strip()

    if not app_token or not table_id:
        return tool_error("app_token and table_id are required")

    client, err = _get_user_client()
    if err:
        return tool_error(err)

    page_size = args.get("page_size", 50) or 50
    page_token = (args.get("page_token") or "").strip()

    queries = [("page_size", str(page_size))]
    if page_token:
        queries.append(("page_token", page_token))

    logger.info("feishu_bitable_list_views: app_token=%s table_id=%s", app_token, table_id)

    code, msg, data = client.do_request(
        "GET", _LIST_VIEWS_URI,
        paths={"app_token": app_token, "table_id": table_id},
        queries=queries,
        use_uat=True,
    )
    if code != 0:
        err_result = _handle_api_error(code, msg, "feishu.bitable.list_views")
        if err_result:
            return err_result
        logger.warning("feishu_bitable_list_views failed: code=%d msg=%s", code, msg)
        return tool_error(f"List views failed: code={code} msg={msg}")

    views = data.get("items", [])
    logger.info(
        "feishu_bitable_list_views: app=%s table=%s returned %d views",
        app_token, table_id, len(views),
    )
    return tool_result({
        "views": views,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token", ""),
        "total": data.get("total"),
    })


# ---------------------------------------------------------------------------
# feishu_bitable_create_view
# ---------------------------------------------------------------------------

_CREATE_VIEW_URI = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/views"

FEISHU_BITABLE_CREATE_VIEW_SCHEMA = {
    "name": "feishu_bitable_create_view",
    "description": (
        "Create a new view in a Feishu Bitable table. "
        "Returns the created view object including view_id."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "app_token": {
                "type": "string",
                "description": "The bitable app token.",
            },
            "table_id": {
                "type": "string",
                "description": "The data table ID.",
            },
            "view_name": {
                "type": "string",
                "description": "Name of the new view.",
            },
            "view_type": {
                "type": "string",
                "description": "View type: 'grid', 'kanban', 'gallery', 'gantt', or 'form'.",
                "enum": ["grid", "kanban", "gallery", "gantt", "form"],
            },
        },
        "required": ["app_token", "table_id", "view_name", "view_type"],
    },
}


def _handle_bitable_create_view(args: dict, **kwargs) -> str:
    """Handler for feishu_bitable_create_view.

    Args:
        args: Tool arguments containing app_token, table_id, view_name, and view_type.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    app_token = (args.get("app_token") or "").strip()
    table_id = (args.get("table_id") or "").strip()
    view_name = (args.get("view_name") or "").strip()
    view_type = (args.get("view_type") or "").strip()

    if not app_token or not table_id or not view_name or not view_type:
        return tool_error("app_token, table_id, view_name, and view_type are required")

    client, err = _get_user_client()
    if err:
        return tool_error(err)

    logger.info(
        "feishu_bitable_create_view: app_token=%s table_id=%s view_name=%s view_type=%s",
        app_token, table_id, view_name, view_type,
    )

    code, msg, data = client.do_request(
        "POST", _CREATE_VIEW_URI,
        paths={"app_token": app_token, "table_id": table_id},
        body={"view_name": view_name, "view_type": view_type},
        use_uat=True,
    )
    if code != 0:
        err_result = _handle_api_error(code, msg, "feishu.bitable.create_view")
        if err_result:
            return err_result
        logger.warning("feishu_bitable_create_view failed: code=%d msg=%s", code, msg)
        return tool_error(f"Create view failed: code={code} msg={msg}")

    view = data.get("view", data)
    logger.info("feishu_bitable_create_view: created view in app=%s table=%s", app_token, table_id)
    return tool_result(success=True, data={"view": view})


# ---------------------------------------------------------------------------
# feishu_bitable_delete_view
# ---------------------------------------------------------------------------

_DELETE_VIEW_URI = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/views/:view_id"

FEISHU_BITABLE_DELETE_VIEW_SCHEMA = {
    "name": "feishu_bitable_delete_view",
    "description": (
        "Delete a view from a Feishu Bitable table by view_id. "
        "Returns a confirmation that the view was deleted."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "app_token": {
                "type": "string",
                "description": "The bitable app token.",
            },
            "table_id": {
                "type": "string",
                "description": "The data table ID.",
            },
            "view_id": {
                "type": "string",
                "description": "The view ID to delete.",
            },
        },
        "required": ["app_token", "table_id", "view_id"],
    },
}


def _handle_bitable_delete_view(args: dict, **kwargs) -> str:
    """Handler for feishu_bitable_delete_view.

    Args:
        args: Tool arguments containing app_token, table_id, and view_id.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    app_token = (args.get("app_token") or "").strip()
    table_id = (args.get("table_id") or "").strip()
    view_id = (args.get("view_id") or "").strip()

    if not app_token or not table_id or not view_id:
        return tool_error("app_token, table_id, and view_id are required")

    client, err = _get_user_client()
    if err:
        return tool_error(err)

    logger.info(
        "feishu_bitable_delete_view: app_token=%s table_id=%s view_id=%s",
        app_token, table_id, view_id,
    )

    code, msg, data = _do_raw_request(
        client, "DELETE", _DELETE_VIEW_URI,
        paths={"app_token": app_token, "table_id": table_id, "view_id": view_id},
    )
    if code != 0:
        err_result = _handle_api_error(code, msg, "feishu.bitable.delete_view")
        if err_result:
            return err_result
        logger.warning("feishu_bitable_delete_view failed: code=%d msg=%s", code, msg)
        return tool_error(f"Delete view failed: code={code} msg={msg}")

    logger.info("feishu_bitable_delete_view: deleted view_id=%s", view_id)
    return tool_result(success=True, data={"deleted": True, "view_id": view_id})


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_bitable_create_field",
    toolset="feishu_bitable",
    schema=FEISHU_BITABLE_CREATE_FIELD_SCHEMA,
    handler=_handle_bitable_create_field,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Create a new field in a Feishu Bitable table",
    emoji="📊",
)

registry.register(
    name="feishu_bitable_update_field",
    toolset="feishu_bitable",
    schema=FEISHU_BITABLE_UPDATE_FIELD_SCHEMA,
    handler=_handle_bitable_update_field,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Update an existing field in a Feishu Bitable table",
    emoji="📊",
)

registry.register(
    name="feishu_bitable_delete_field",
    toolset="feishu_bitable",
    schema=FEISHU_BITABLE_DELETE_FIELD_SCHEMA,
    handler=_handle_bitable_delete_field,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Delete a field from a Feishu Bitable table",
    emoji="📊",
)

registry.register(
    name="feishu_bitable_list_views",
    toolset="feishu_bitable",
    schema=FEISHU_BITABLE_LIST_VIEWS_SCHEMA,
    handler=_handle_bitable_list_views,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List views for a Feishu Bitable table",
    emoji="📊",
)

registry.register(
    name="feishu_bitable_create_view",
    toolset="feishu_bitable",
    schema=FEISHU_BITABLE_CREATE_VIEW_SCHEMA,
    handler=_handle_bitable_create_view,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Create a new view in a Feishu Bitable table",
    emoji="📊",
)

registry.register(
    name="feishu_bitable_delete_view",
    toolset="feishu_bitable",
    schema=FEISHU_BITABLE_DELETE_VIEW_SCHEMA,
    handler=_handle_bitable_delete_view,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Delete a view from a Feishu Bitable table",
    emoji="📊",
)
