"""Feishu Bitable Schema Tool -- delete record and list fields via Feishu/Lark API.

Provides two tools for Feishu Bitable schema/record operations:
  - ``feishu_bitable_delete_record`` -- delete a record by record_id
  - ``feishu_bitable_list_fields``   -- list field definitions for a table

Both tools use UAT (user_access_token) via FeishuClient.for_user() and require
the bitable:app scope.
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
# TOOLS_METADATA — declare scopes and identity for schema tools
# ---------------------------------------------------------------------------

_SCHEMA_TOOLS = [
    "feishu_bitable_delete_record",
    "feishu_bitable_list_fields",
]

for _tool_name in _SCHEMA_TOOLS:
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


# ---------------------------------------------------------------------------
# feishu_bitable_delete_record
# ---------------------------------------------------------------------------

_DELETE_RECORD_URI = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/:record_id"

FEISHU_BITABLE_DELETE_RECORD_SCHEMA = {
    "name": "feishu_bitable_delete_record",
    "description": (
        "Delete a record from a Feishu Bitable table by record_id. "
        "Returns a confirmation that the record was deleted."
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
            "record_id": {
                "type": "string",
                "description": "The record ID to delete.",
            },
        },
        "required": ["app_token", "table_id", "record_id"],
    },
}


def _handle_bitable_delete_record(args: dict, **kwargs) -> str:
    """Handler for feishu_bitable_delete_record.

    Args:
        args: Tool arguments containing app_token, table_id, and record_id.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    app_token = (args.get("app_token") or "").strip()
    table_id = (args.get("table_id") or "").strip()
    record_id = (args.get("record_id") or "").strip()
    logger.info(
        "feishu_bitable_delete_record: app_token=%s table_id=%s record_id=%s",
        app_token, table_id, record_id,
    )

    if not app_token or not table_id or not record_id:
        return tool_error("app_token, table_id, and record_id are required")

    client, err = _get_user_client()
    if err:
        return tool_error(err)

    code, msg, data = client.do_request(
        "DELETE", _DELETE_RECORD_URI,
        paths={"app_token": app_token, "table_id": table_id, "record_id": record_id},
        use_uat=True,
    )
    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu.bitable.delete_record")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("feishu_bitable_delete_record failed: code=%d msg=%s", code, msg)
        return tool_error(f"Delete record failed: code={code} msg={msg}")

    deleted = data.get("deleted", True)
    logger.info(
        "feishu_bitable_delete_record: app=%s table=%s deleted record %s",
        app_token, table_id, record_id,
    )
    return tool_result(success=True, data={"deleted": deleted, "record_id": record_id})


# ---------------------------------------------------------------------------
# feishu_bitable_list_fields
# ---------------------------------------------------------------------------

_LIST_FIELDS_URI = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/fields"

FEISHU_BITABLE_LIST_FIELDS_SCHEMA = {
    "name": "feishu_bitable_list_fields",
    "description": (
        "List field definitions for a Feishu Bitable table. "
        "Returns field_name, type, and property for each field."
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
                "description": "Number of fields per page (max 100, default 50).",
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


def _handle_bitable_list_fields(args: dict, **kwargs) -> str:
    """Handler for feishu_bitable_list_fields.

    Args:
        args: Tool arguments containing app_token, table_id, optional page_size and page_token.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    app_token = (args.get("app_token") or "").strip()
    table_id = (args.get("table_id") or "").strip()
    logger.info("feishu_bitable_list_fields: app_token=%s table_id=%s", app_token, table_id)

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

    code, msg, data = client.do_request(
        "GET", _LIST_FIELDS_URI,
        paths={"app_token": app_token, "table_id": table_id},
        queries=queries,
        use_uat=True,
    )
    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu.bitable.list_fields")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("feishu_bitable_list_fields failed: code=%d msg=%s", code, msg)
        return tool_error(f"List fields failed: code={code} msg={msg}")

    fields = data.get("items", [])
    logger.info(
        "feishu_bitable_list_fields: app=%s table=%s returned %d fields",
        app_token, table_id, len(fields),
    )
    return tool_result({
        "fields": fields,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token", ""),
        "total": data.get("total"),
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_bitable_delete_record",
    toolset="feishu_bitable",
    schema=FEISHU_BITABLE_DELETE_RECORD_SCHEMA,
    handler=_handle_bitable_delete_record,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Delete a record from a Feishu Bitable table",
    emoji="📊",
)

registry.register(
    name="feishu_bitable_list_fields",
    toolset="feishu_bitable",
    schema=FEISHU_BITABLE_LIST_FIELDS_SCHEMA,
    handler=_handle_bitable_list_fields,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List field definitions for a Feishu Bitable table",
    emoji="📊",
)
