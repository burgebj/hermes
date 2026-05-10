"""Feishu IM History Tool -- read message history and fetch media resources via UAT.

Provides three tools for reading IM chat/thread history as the signed-in user:
  - ``feishu_im_get_messages``       -- list messages in a chat (container_id_type=chat)
  - ``feishu_im_get_thread_messages``-- list messages in a thread (container_id_type=thread)
  - ``feishu_im_fetch_resource``     -- fetch a media resource binary and return summary metadata

All tools use ``FeishuClient.for_user()`` (UAT) and the ``do_request`` helper.
Error codes 99991672 and 99991679 are surfaced as semantic auth exceptions via
``raise_for_feishu_errcode``.

Required scopes:
  im:message:readonly  -- get_messages, get_thread_messages
  im:resource          -- fetch_resource
"""

import json
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
# Scopes
# ---------------------------------------------------------------------------

_IM_MESSAGE_READONLY_SCOPE = "im:message:readonly"
_IM_RESOURCE_SCOPE = "im:resource"

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


def _get_fc() -> FeishuClient:
    """Return a UAT FeishuClient, raising NeedAuthorizationError / ValueError on failure."""
    return FeishuClient.for_user()


# ---------------------------------------------------------------------------
# feishu_im_get_messages
# ---------------------------------------------------------------------------

_GET_MESSAGES_URI = "/open-apis/im/v1/messages"

FEISHU_IM_GET_MESSAGES_SCHEMA = {
    "name": "feishu_im_get_messages",
    "description": (
        "List messages in a Feishu chat as the signed-in user. "
        "Returns up to page_size messages in the chat within the optional time range. "
        "Requires scope: im:message:readonly."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "chat_id": {
                "type": "string",
                "description": "The chat ID (oc_xxx) to list messages from.",
            },
            "start_time": {
                "type": "string",
                "description": (
                    "Unix timestamp (seconds) for range start. "
                    "Example: '1672531200'. Optional."
                ),
            },
            "end_time": {
                "type": "string",
                "description": (
                    "Unix timestamp (seconds) for range end. "
                    "Example: '1672617600'. Optional."
                ),
            },
            "page_size": {
                "type": "integer",
                "description": "Maximum number of messages to return (1-50, default 20).",
            },
        },
        "required": ["chat_id"],
    },
}


def _handle_im_get_messages(args: dict, **kwargs) -> str:
    """Handler for feishu_im_get_messages.

    Args:
        args: Tool arguments containing chat_id and optional start_time, end_time, page_size.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    chat_id = (args.get("chat_id") or "").strip()
    if not chat_id:
        return tool_error("chat_id is required")

    start_time = (args.get("start_time") or "").strip()
    end_time = (args.get("end_time") or "").strip()
    page_size = args.get("page_size") or 20

    try:
        fc = _get_fc()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    queries = [
        ("container_id_type", "chat"),
        ("container_id", chat_id),
        ("page_size", str(page_size)),
    ]
    if start_time:
        queries.append(("start_time", start_time))
    if end_time:
        queries.append(("end_time", end_time))

    logger.info(
        "im_get_messages: chat_id=%s start_time=%s end_time=%s page_size=%s",
        chat_id, start_time, end_time, page_size,
    )

    try:
        code, msg, data = fc.do_request(
            "GET",
            _GET_MESSAGES_URI,
            queries=queries,
            use_uat=True,
        )
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except RuntimeError as exc:
        return tool_error(str(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_im_get_messages",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Get messages failed: code={code} msg={msg}")

    items = data.get("items", [])
    logger.info("im_get_messages: returned %d messages", len(items))
    return tool_result({
        "messages": items,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token"),
    })


# ---------------------------------------------------------------------------
# feishu_im_get_thread_messages
# ---------------------------------------------------------------------------

FEISHU_IM_GET_THREAD_MESSAGES_SCHEMA = {
    "name": "feishu_im_get_thread_messages",
    "description": (
        "List messages in a Feishu message thread as the signed-in user. "
        "Returns up to page_size messages in the thread. "
        "Requires scope: im:message:readonly."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "thread_id": {
                "type": "string",
                "description": "The thread ID to list messages from.",
            },
            "page_size": {
                "type": "integer",
                "description": "Maximum number of messages to return (1-50, default 20).",
            },
        },
        "required": ["thread_id"],
    },
}


def _handle_im_get_thread_messages(args: dict, **kwargs) -> str:
    """Handler for feishu_im_get_thread_messages.

    Args:
        args: Tool arguments containing thread_id and optional page_size.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    thread_id = (args.get("thread_id") or "").strip()
    if not thread_id:
        return tool_error("thread_id is required")

    page_size = args.get("page_size") or 20

    try:
        fc = _get_fc()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    queries = [
        ("container_id_type", "thread"),
        ("container_id", thread_id),
        ("page_size", str(page_size)),
    ]

    logger.info(
        "im_get_thread_messages: thread_id=%s page_size=%s", thread_id, page_size
    )

    try:
        code, msg, data = fc.do_request(
            "GET",
            _GET_MESSAGES_URI,
            queries=queries,
            use_uat=True,
        )
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except RuntimeError as exc:
        return tool_error(str(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_im_get_thread_messages",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Get thread messages failed: code={code} msg={msg}")

    items = data.get("items", [])
    logger.info("im_get_thread_messages: returned %d messages", len(items))
    return tool_result({
        "messages": items,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token"),
    })


# ---------------------------------------------------------------------------
# feishu_im_fetch_resource
# ---------------------------------------------------------------------------

_FETCH_RESOURCE_URI = "/open-apis/im/v1/messages/:message_id/resources/:file_key"

FEISHU_IM_FETCH_RESOURCE_SCHEMA = {
    "name": "feishu_im_fetch_resource",
    "description": (
        "Fetch a media resource (image or file) from a Feishu IM message as the signed-in user. "
        "Returns metadata summary (resource_id, size, mime) rather than raw bytes. "
        "Requires scope: im:resource."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "message_id": {
                "type": "string",
                "description": "The message ID that contains the resource (e.g. om_xxxxxxxx).",
            },
            "file_key": {
                "type": "string",
                "description": "The file key of the resource to fetch.",
            },
            "type": {
                "type": "string",
                "description": "Resource type: 'image' or 'file'. Defaults to 'image'.",
            },
        },
        "required": ["message_id", "file_key"],
    },
}


def _handle_im_fetch_resource(args: dict, **kwargs) -> str:
    """Handler for feishu_im_fetch_resource.

    Args:
        args: Tool arguments containing message_id, file_key, and optional type.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error. Returns metadata summary, not raw bytes.
    """
    message_id = (args.get("message_id") or "").strip()
    file_key = (args.get("file_key") or "").strip()
    resource_type = (args.get("type") or "image").strip()

    if not message_id:
        return tool_error("message_id is required")
    if not file_key:
        return tool_error("file_key is required")
    if resource_type not in ("image", "file"):
        return tool_error("type must be 'image' or 'file'")

    try:
        fc = _get_fc()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info(
        "im_fetch_resource: message_id=%s file_key=%s type=%s",
        message_id, file_key, resource_type,
    )

    try:
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError:
        return tool_error("lark_oapi not installed")

    request = (
        BaseRequest.builder()
        .http_method(HttpMethod.GET)
        .uri(_FETCH_RESOURCE_URI)
        .token_types({AccessTokenType.USER})
        .paths({"message_id": message_id, "file_key": file_key})
        .queries([("type", resource_type)])
        .build()
    )
    opt = (
        RequestOption.builder()
        .user_access_token(fc.access_token)
        .build()
    )

    try:
        response = fc.sdk.request(request, opt)
    except Exception as exc:
        return tool_error(f"Request failed: {exc}")

    code = getattr(response, "code", None)
    msg = getattr(response, "msg", "")

    # For binary responses, content is bytes (not JSON). We detect error via code.
    raw = getattr(response, "raw", None)
    raw_content = None
    content_type = ""
    if raw:
        raw_content = getattr(raw, "content", None)
        # Try to read Content-Type from headers if available
        headers = getattr(raw, "headers", None) or {}
        if isinstance(headers, dict):
            content_type = headers.get("content-type", headers.get("Content-Type", ""))

    # If code is non-zero or we got a JSON error body, surface the error.
    if code is not None and code != 0:
        # Try to parse as JSON error
        json_msg = msg
        if raw_content:
            try:
                body_json = json.loads(raw_content)
                if not json_msg:
                    json_msg = body_json.get("msg", "")
                err_code = body_json.get("code", code)
            except (json.JSONDecodeError, UnicodeDecodeError):
                err_code = code
        else:
            err_code = code
        try:
            raise_for_feishu_errcode(
                err_code, json_msg, api_name="feishu_im_fetch_resource",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Fetch resource failed: code={err_code} msg={json_msg}")

    # Check for JSON error body even when code attribute is 0 or None
    if raw_content:
        try:
            body_json = json.loads(raw_content)
            err_code = body_json.get("code", 0)
            if err_code != 0:
                err_msg = body_json.get("msg", "")
                try:
                    raise_for_feishu_errcode(
                        err_code, err_msg, api_name="feishu_im_fetch_resource",
                        user_open_id=fc.user_open_id,
                    )
                except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
                    return tool_error(_auth_error_message(exc))
                return tool_error(f"Fetch resource failed: code={err_code} msg={err_msg}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass  # Binary content — expected for successful resource fetch

    size = len(raw_content) if raw_content else 0
    if not content_type:
        content_type = "image/jpeg" if resource_type == "image" else "application/octet-stream"

    logger.info(
        "im_fetch_resource: fetched %s bytes (mime=%s) for file_key=%s",
        size, content_type, file_key,
    )
    return tool_result({
        "resource_id": file_key,
        "size": size,
        "mime": content_type,
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_im_get_messages",
    toolset="feishu_im_user",
    schema=FEISHU_IM_GET_MESSAGES_SCHEMA,
    handler=_handle_im_get_messages,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List messages in a Feishu chat (im:message:readonly)",
    emoji="💬",
)

registry.register(
    name="feishu_im_get_thread_messages",
    toolset="feishu_im_user",
    schema=FEISHU_IM_GET_THREAD_MESSAGES_SCHEMA,
    handler=_handle_im_get_thread_messages,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List messages in a Feishu thread (im:message:readonly)",
    emoji="💬",
)

registry.register(
    name="feishu_im_fetch_resource",
    toolset="feishu_im_user",
    schema=FEISHU_IM_FETCH_RESOURCE_SCHEMA,
    handler=_handle_im_fetch_resource,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Fetch IM message resource binary, return metadata summary (im:resource)",
    emoji="💬",
)

# Register tool metadata (scopes + identity) in the shared registry
TOOLS_METADATA.update({
    "feishu_im_get_messages": {
        "scopes": [_IM_MESSAGE_READONLY_SCOPE],
        "identity": "user",
    },
    "feishu_im_get_thread_messages": {
        "scopes": [_IM_MESSAGE_READONLY_SCOPE],
        "identity": "user",
    },
    "feishu_im_fetch_resource": {
        "scopes": [_IM_RESOURCE_SCOPE],
        "identity": "user",
    },
})
