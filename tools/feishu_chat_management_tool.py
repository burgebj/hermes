"""Feishu Chat Management Tool -- create chats and manage members via Feishu/Lark API.

Provides three tools for managing group chats as the signed-in user (UAT):
  - ``feishu_chat_create``         -- create a new group chat with optional members
  - ``feishu_chat_add_members``    -- add members to an existing chat
  - ``feishu_chat_remove_members`` -- remove members from an existing chat

All tools use ``FeishuClient.for_user()`` (UAT) and the ``do_request`` helper.
Requires scope: im:chat
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
# Scope
# ---------------------------------------------------------------------------

_CHAT_SCOPE = "im:chat"

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
    if isinstance(exc, UserScopeInsufficientError):
        return f"User scope insufficient: {exc}"
    return str(exc)


# ---------------------------------------------------------------------------
# feishu_chat_create
# ---------------------------------------------------------------------------

_CHAT_CREATE_URI = "/open-apis/im/v1/chats"

FEISHU_CHAT_CREATE_SCHEMA = {
    "name": "feishu_chat_create",
    "description": (
        "Create a new Feishu group chat as the signed-in user. "
        "Returns the new chat_id. "
        "Requires scope: im:chat."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the new group chat.",
            },
            "description": {
                "type": "string",
                "description": "Optional description for the group chat.",
            },
            "user_id_list": {
                "type": "array",
                "description": "List of member open_ids (ou_xxx) to add at creation time.",
                "items": {"type": "string"},
            },
            "chat_mode": {
                "type": "string",
                "description": "Chat mode (default: 'group').",
                "default": "group",
            },
            "chat_type": {
                "type": "string",
                "description": "Chat type: 'private' or 'public' (default: 'private').",
                "enum": ["private", "public"],
                "default": "private",
            },
        },
        "required": ["name"],
    },
}


def _handle_chat_create(args: dict, **kwargs) -> str:
    """Handler for feishu_chat_create.

    Args:
        args: Tool arguments containing name and optional fields.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    name = (args.get("name") or "").strip()
    if not name:
        return tool_error("name is required")

    description = (args.get("description") or "").strip()
    user_id_list = args.get("user_id_list") or []
    chat_mode = (args.get("chat_mode") or "group").strip()
    chat_type = (args.get("chat_type") or "private").strip()

    logger.info(
        "feishu_chat_create: name=%r chat_type=%s members=%d",
        name, chat_type, len(user_id_list),
    )

    try:
        client = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    body: dict = {
        "name": name,
        "chat_mode": chat_mode,
        "chat_type": chat_type,
    }
    if description:
        body["description"] = description
    if user_id_list:
        body["user_id_list"] = user_id_list

    try:
        code, msg, data = client.do_request(
            "POST",
            _CHAT_CREATE_URI,
            queries=[("user_id_type", "open_id")],
            body=body,
            use_uat=True,
        )
    except RuntimeError as exc:
        return tool_error(str(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu_chat_create")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("feishu_chat_create failed: code=%d msg=%s", code, msg)
        return tool_error(f"Create chat failed: code={code} msg={msg}")

    chat_id = data.get("chat_id", "")
    logger.info("feishu_chat_create: created chat_id=%s", chat_id)
    return tool_result({"chat_id": chat_id, "data": data})


# ---------------------------------------------------------------------------
# feishu_chat_add_members
# ---------------------------------------------------------------------------

_CHAT_ADD_MEMBERS_URI = "/open-apis/im/v1/chats/:chat_id/members"

FEISHU_CHAT_ADD_MEMBERS_SCHEMA = {
    "name": "feishu_chat_add_members",
    "description": (
        "Add members to an existing Feishu group chat. "
        "Returns invalid_id_list for any IDs that could not be added. "
        "Requires scope: im:chat."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "chat_id": {
                "type": "string",
                "description": "The chat group ID (e.g. oc_xxx).",
            },
            "id_list": {
                "type": "array",
                "description": "List of member open_ids (ou_xxx) to add.",
                "items": {"type": "string"},
            },
        },
        "required": ["chat_id", "id_list"],
    },
}


def _handle_chat_add_members(args: dict, **kwargs) -> str:
    """Handler for feishu_chat_add_members.

    Args:
        args: Tool arguments containing chat_id and id_list.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    chat_id = (args.get("chat_id") or "").strip()
    if not chat_id:
        return tool_error("chat_id is required")

    id_list = args.get("id_list") or []
    if not id_list:
        return tool_error("id_list is required and must be non-empty")

    logger.info("feishu_chat_add_members: chat_id=%s members=%d", chat_id, len(id_list))

    try:
        client = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    try:
        code, msg, data = client.do_request(
            "POST",
            _CHAT_ADD_MEMBERS_URI,
            paths={"chat_id": chat_id},
            queries=[("member_id_type", "open_id")],
            body={"id_list": id_list},
            use_uat=True,
        )
    except RuntimeError as exc:
        return tool_error(str(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu_chat_add_members")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("feishu_chat_add_members failed: code=%d msg=%s", code, msg)
        return tool_error(f"Add members failed: code={code} msg={msg}")

    invalid_id_list = data.get("invalid_id_list", [])
    logger.info(
        "feishu_chat_add_members: added to chat_id=%s invalid_count=%d",
        chat_id, len(invalid_id_list),
    )
    return tool_result({"invalid_id_list": invalid_id_list})


# ---------------------------------------------------------------------------
# feishu_chat_remove_members
# ---------------------------------------------------------------------------

_CHAT_REMOVE_MEMBERS_URI = "/open-apis/im/v1/chats/:chat_id/members"

FEISHU_CHAT_REMOVE_MEMBERS_SCHEMA = {
    "name": "feishu_chat_remove_members",
    "description": (
        "Remove members from an existing Feishu group chat. "
        "Returns invalid_id_list for any IDs that could not be removed. "
        "Requires scope: im:chat."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "chat_id": {
                "type": "string",
                "description": "The chat group ID (e.g. oc_xxx).",
            },
            "id_list": {
                "type": "array",
                "description": "List of member open_ids (ou_xxx) to remove.",
                "items": {"type": "string"},
            },
        },
        "required": ["chat_id", "id_list"],
    },
}


def _handle_chat_remove_members(args: dict, **kwargs) -> str:
    """Handler for feishu_chat_remove_members.

    Args:
        args: Tool arguments containing chat_id and id_list.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    chat_id = (args.get("chat_id") or "").strip()
    if not chat_id:
        return tool_error("chat_id is required")

    id_list = args.get("id_list") or []
    if not id_list:
        return tool_error("id_list is required and must be non-empty")

    logger.info("feishu_chat_remove_members: chat_id=%s members=%d", chat_id, len(id_list))

    try:
        client = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    # DELETE with body: do_request only supports GET/POST; use raw SDK path
    try:
        import json as _json
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError:
        return tool_error("lark_oapi not installed")

    request = (
        BaseRequest.builder()
        .http_method(HttpMethod.DELETE)
        .uri(_CHAT_REMOVE_MEMBERS_URI)
        .token_types({AccessTokenType.USER})
        .paths({"chat_id": chat_id})
        .queries([("member_id_type", "open_id")])
        .body({"id_list": id_list})
        .build()
    )
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
            body_json = _json.loads(raw.content)
            if code is None:
                code = body_json.get("code", -1)
            if not msg:
                msg = body_json.get("msg", "")
            data = body_json.get("data", {})
        except (_json.JSONDecodeError, AttributeError):
            pass
    if not data:
        resp_data = getattr(response, "data", None)
        if isinstance(resp_data, dict):
            data = resp_data
        elif resp_data and hasattr(resp_data, "__dict__"):
            data = vars(resp_data)

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg or "", api_name="feishu_chat_remove_members",
                user_open_id=client.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("feishu_chat_remove_members failed: code=%d msg=%s", code, msg)
        return tool_error(f"Remove members failed: code={code} msg={msg}")

    invalid_id_list = data.get("invalid_id_list", [])
    logger.info(
        "feishu_chat_remove_members: removed from chat_id=%s invalid_count=%d",
        chat_id, len(invalid_id_list),
    )
    return tool_result({"invalid_id_list": invalid_id_list})


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_chat_create",
    toolset="feishu_chat",
    schema=FEISHU_CHAT_CREATE_SCHEMA,
    handler=_handle_chat_create,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Create a new Feishu group chat with optional members",
    emoji="\U0001f4ac",
)

registry.register(
    name="feishu_chat_add_members",
    toolset="feishu_chat",
    schema=FEISHU_CHAT_ADD_MEMBERS_SCHEMA,
    handler=_handle_chat_add_members,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Add members to a Feishu group chat",
    emoji="\U0001f4ac",
)

registry.register(
    name="feishu_chat_remove_members",
    toolset="feishu_chat",
    schema=FEISHU_CHAT_REMOVE_MEMBERS_SCHEMA,
    handler=_handle_chat_remove_members,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Remove members from a Feishu group chat",
    emoji="\U0001f4ac",
)

# Register tool metadata (scopes + identity)
TOOLS_METADATA.update({
    "feishu_chat_create": {
        "scopes": [_CHAT_SCOPE],
        "identity": "user",
    },
    "feishu_chat_add_members": {
        "scopes": [_CHAT_SCOPE],
        "identity": "user",
    },
    "feishu_chat_remove_members": {
        "scopes": [_CHAT_SCOPE],
        "identity": "user",
    },
})
