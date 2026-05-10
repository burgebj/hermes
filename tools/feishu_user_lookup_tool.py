"""Feishu User Lookup Tool -- search and retrieve user details via Feishu/Lark API.

Provides two tools for looking up Feishu users (UAT):
  - ``feishu_search_user``  -- search users by query string
  - ``feishu_get_user``     -- fetch a single user by open_id

Both tools use ``FeishuClient.for_user()`` (UAT) and the ``do_request`` helper.
Requires scope: contact:user.base:readonly
"""

import logging

from tools.feishu_oapi_client import (
    AppScopeMissingError,
    FeishuClient,
    NeedAuthorizationError,
    TOOLS_METADATA,
    UserAuthRequiredError,
    raise_for_feishu_errcode,
)
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

_USER_READONLY_SCOPE = "contact:user.base:readonly"

# ---------------------------------------------------------------------------
# Shared helpers
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
    return str(exc)


# ---------------------------------------------------------------------------
# feishu_search_user
# ---------------------------------------------------------------------------

_SEARCH_USER_URI = "/open-apis/contact/v3/users/search"
_SEARCH_USER_FALLBACK_URI = "/open-apis/search/v1/user"
_USER_INFO_URI = "/open-apis/authen/v1/user_info"
_ERRCODE_USER_SCOPE_INSUFFICIENT = 99991679
_USER_SEARCH_FALLBACK_KEYS = (
    "name",
    "en_name",
    "open_id",
    "user_id",
    "union_id",
    "employee_no",
    "email",
    "enterprise_email",
)

FEISHU_SEARCH_USER_SCHEMA = {
    "name": "feishu_search_user",
    "description": (
        "Search Feishu users by name, email, or employee ID. "
        "Returns a list of matching users with open_id, name, and email. "
        "Directory search requires broader contact directory scopes; if those "
        "are unavailable, a query for the signed-in user falls back to current "
        "user profile lookup."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search keyword (name, email, or employee ID).",
            },
            "page_size": {
                "type": "integer",
                "description": "Number of results per page (default: 20, max: 50).",
                "default": 20,
            },
        },
        "required": ["query"],
    },
}


def _user_matches_query(user: dict, query: str) -> bool:
    needle = query.strip().casefold()
    if not needle:
        return False
    for key in _USER_SEARCH_FALLBACK_KEYS:
        value = str(user.get(key) or "").strip()
        if value and (needle in value.casefold() or value.casefold() in needle):
            return True
    return False


def _current_user_search_fallback(fc: FeishuClient, query: str, original_code: int, original_msg: str) -> str | None:
    """Fallback for tenants that grant only current-user profile scopes.

    ``contact/v3/users/search`` requires broader directory contact scopes. UAT
    smoke tests often search for the signed-in user, which can be answered by
    ``authen/v1/user_info`` without granting full directory access.
    """
    code, msg, data = fc.do_request(
        "GET",
        _USER_INFO_URI,
        use_uat=True,
    )
    if code != 0 or not isinstance(data, dict) or not _user_matches_query(data, query):
        logger.info(
            "feishu_search_user: current-user fallback unavailable code=%s msg=%s",
            code,
            msg,
        )
        return None

    user = {
        key: data[key]
        for key in _USER_SEARCH_FALLBACK_KEYS
        if data.get(key)
    }
    logger.info("feishu_search_user: current-user fallback matched query=%r", query)
    return tool_result({
        "users": [user],
        "has_more": False,
        "page_token": None,
        "fallback": "current_user_info",
        "original_error": {"code": original_code, "msg": original_msg},
    })


def _handle_search_user(args: dict, **kwargs) -> str:
    """Handler for feishu_search_user.

    Args:
        args: Tool arguments containing query and optional page_size.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    query = (args.get("query") or "").strip()
    if not query:
        return tool_error("query is required")

    page_size = args.get("page_size", 20)

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info("feishu_search_user: query=%r page_size=%d", query, page_size)

    try:
        code, msg, data = fc.do_request(
            "POST",
            _SEARCH_USER_URI,
            queries=[("user_id_type", "open_id")],
            body={"query": query, "page_size": page_size},
            use_uat=True,
        )
    except RuntimeError as exc:
        return tool_error(str(exc))

    if code != 0:
        try:
            fallback = _current_user_search_fallback(fc, query, code, msg)
        except RuntimeError as exc:
            logger.info("feishu_search_user: current-user fallback failed: %s", exc)
            fallback = None
        if fallback is not None:
            return fallback
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_search_user",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        logger.warning("feishu_search_user failed: code=%d msg=%s", code, msg)
        return tool_error(f"Search user failed: code={code} msg={msg}")

    users = data.get("users", [])
    logger.info("feishu_search_user: found %d user(s) for query=%r", len(users), query)
    return tool_result({
        "users": users,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token"),
    })


# ---------------------------------------------------------------------------
# feishu_get_user
# ---------------------------------------------------------------------------

_GET_USER_URI = "/open-apis/contact/v3/users/:user_id"

FEISHU_GET_USER_SCHEMA = {
    "name": "feishu_get_user",
    "description": (
        "Fetch detailed information for a single Feishu user by open_id. "
        "Returns user profile including name, email, department, and avatar. "
        "Requires scope: contact:user.base:readonly."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user's open_id (ou_xxx).",
            },
        },
        "required": ["user_id"],
    },
}


def _handle_get_user(args: dict, **kwargs) -> str:
    """Handler for feishu_get_user.

    Args:
        args: Tool arguments containing user_id.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    user_id = (args.get("user_id") or "").strip()
    if not user_id:
        return tool_error("user_id is required")

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info("feishu_get_user: user_id=%s", user_id)

    try:
        code, msg, data = fc.do_request(
            "GET",
            _GET_USER_URI,
            paths={"user_id": user_id},
            queries=[("user_id_type", "open_id")],
            use_uat=True,
        )
    except RuntimeError as exc:
        return tool_error(str(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_get_user",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        logger.warning("feishu_get_user failed: code=%d msg=%s", code, msg)
        return tool_error(f"Get user failed: code={code} msg={msg}")

    logger.info("feishu_get_user: retrieved user %s", user_id)
    return tool_result({"user": data.get("user", data)})


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_search_user",
    toolset="feishu_user_info",
    schema=FEISHU_SEARCH_USER_SCHEMA,
    handler=_handle_search_user,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Search Feishu users by name, email, or employee ID",
    emoji="👤",
)

registry.register(
    name="feishu_get_user",
    toolset="feishu_user_info",
    schema=FEISHU_GET_USER_SCHEMA,
    handler=_handle_get_user,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Fetch detailed information for a single Feishu user by open_id",
    emoji="👤",
)

# Register tool metadata (scopes + identity) in the shared registry
TOOLS_METADATA.update({
    "feishu_search_user": {
        "scopes": [_USER_READONLY_SCOPE],
        "identity": "user",
    },
    "feishu_get_user": {
        "scopes": [_USER_READONLY_SCOPE],
        "identity": "user",
    },
})
