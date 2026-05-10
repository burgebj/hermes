"""Feishu Wiki Node Tool -- wiki node creation, movement, and space listing via Feishu/Lark API.

Provides three tools for managing wiki nodes as the signed-in user (UAT):
  - ``feishu_wiki_create_node``  -- create a new wiki node in a space
  - ``feishu_wiki_move_node``    -- move a wiki node to a new parent
  - ``feishu_wiki_list_spaces``  -- list all accessible wiki spaces

All tools use ``FeishuClient.for_user()`` (UAT) and the ``do_request`` helper.
Scope required: ``wiki:wiki`` (write tools) / ``wiki:wiki:readonly`` (list_spaces).
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
# Scopes
# ---------------------------------------------------------------------------

_WIKI_SCOPE = "wiki:wiki"
_WIKI_READONLY_SCOPE = "wiki:wiki:readonly"

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
# feishu_wiki_create_node
# ---------------------------------------------------------------------------

_WIKI_CREATE_NODE_URI = "/open-apis/wiki/v2/spaces/{space_id}/nodes"

FEISHU_WIKI_CREATE_NODE_SCHEMA = {
    "name": "feishu_wiki_create_node",
    "description": (
        "Create a new wiki node (document, sheet, etc.) in a Feishu wiki space. "
        "Returns the created node's node_token and metadata. "
        "Requires scope wiki:wiki."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "space_id": {
                "type": "string",
                "description": "The wiki space ID in which to create the node.",
            },
            "obj_type": {
                "type": "string",
                "description": (
                    "Type of document object to create. "
                    "Common values: 'doc', 'docx', 'sheet', 'mindnote', 'bitable', 'file'."
                ),
            },
            "node_type": {
                "type": "string",
                "description": "Node type: 'origin' (default) for a real node, or 'shortcut' for a shortcut.",
                "default": "origin",
            },
            "parent_node_token": {
                "type": "string",
                "description": "Token of the parent node to nest this node under (optional; root level if omitted).",
            },
            "title": {
                "type": "string",
                "description": "Title for the new node (optional).",
            },
        },
        "required": ["space_id", "obj_type"],
    },
}


def _handle_wiki_create_node(args: dict, **kwargs) -> str:
    """Handler for feishu_wiki_create_node.

    Args:
        args: Tool arguments containing space_id, obj_type, and optional fields.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    space_id = (args.get("space_id") or "").strip()
    obj_type = (args.get("obj_type") or "").strip()
    if not space_id:
        return tool_error("space_id is required")
    if not obj_type:
        return tool_error("obj_type is required")

    node_type = (args.get("node_type") or "origin").strip()
    parent_node_token = (args.get("parent_node_token") or "").strip()
    title = (args.get("title") or "").strip()

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info(
        "wiki_create_node: space_id=%s obj_type=%s node_type=%s",
        space_id, obj_type, node_type,
    )

    body: dict = {
        "obj_type": obj_type,
        "node_type": node_type,
    }
    if parent_node_token:
        body["parent_node_token"] = parent_node_token
    if title:
        body["title"] = title

    uri = _WIKI_CREATE_NODE_URI.format(space_id=space_id)

    try:
        code, msg, data = fc.do_request(
            "POST",
            uri,
            body=body,
            use_uat=True,
        )
    except Exception as exc:
        return tool_error(f"Request failed: {exc}")

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg or "", api_name="feishu_wiki_create_node",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        logger.warning("wiki_create_node failed: code=%d msg=%s", code, msg)
        return tool_error(f"Wiki create node failed: code={code} msg={msg}")

    node = data.get("node", data)
    logger.info("wiki_create_node: created node_token=%s", node.get("node_token") if isinstance(node, dict) else "")
    return tool_result({"node": node})


# ---------------------------------------------------------------------------
# feishu_wiki_move_node
# ---------------------------------------------------------------------------

_WIKI_MOVE_NODE_URI = "/open-apis/wiki/v2/spaces/{space_id}/nodes/{node_token}/move"

FEISHU_WIKI_MOVE_NODE_SCHEMA = {
    "name": "feishu_wiki_move_node",
    "description": (
        "Move a wiki node to a new parent within the same or a different Feishu wiki space. "
        "Requires scope wiki:wiki."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "space_id": {
                "type": "string",
                "description": "The wiki space ID that currently contains the node.",
            },
            "node_token": {
                "type": "string",
                "description": "Token of the wiki node to move.",
            },
            "target_parent_token": {
                "type": "string",
                "description": "Token of the target parent node to move the node under.",
            },
            "target_space_id": {
                "type": "string",
                "description": "Target space ID if moving to a different space (optional; same space if omitted).",
            },
        },
        "required": ["space_id", "node_token", "target_parent_token"],
    },
}


def _handle_wiki_move_node(args: dict, **kwargs) -> str:
    """Handler for feishu_wiki_move_node.

    Args:
        args: Tool arguments containing space_id, node_token, target_parent_token,
              and optional target_space_id.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    space_id = (args.get("space_id") or "").strip()
    node_token = (args.get("node_token") or "").strip()
    target_parent_token = (args.get("target_parent_token") or "").strip()
    if not space_id:
        return tool_error("space_id is required")
    if not node_token:
        return tool_error("node_token is required")
    if not target_parent_token:
        return tool_error("target_parent_token is required")

    target_space_id = (args.get("target_space_id") or "").strip()

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info(
        "wiki_move_node: space_id=%s node_token=%s target_parent_token=%s",
        space_id, node_token, target_parent_token,
    )

    body: dict = {"target_parent_token": target_parent_token}
    if target_space_id:
        body["target_space_id"] = target_space_id

    uri = _WIKI_MOVE_NODE_URI.format(space_id=space_id, node_token=node_token)

    try:
        code, msg, data = fc.do_request(
            "POST",
            uri,
            body=body,
            use_uat=True,
        )
    except Exception as exc:
        return tool_error(f"Request failed: {exc}")

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg or "", api_name="feishu_wiki_move_node",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        logger.warning("wiki_move_node failed: code=%d msg=%s", code, msg)
        return tool_error(f"Wiki move node failed: code={code} msg={msg}")

    node = data.get("node", data)
    logger.info("wiki_move_node: moved node_token=%s", node_token)
    return tool_result({"node": node})


# ---------------------------------------------------------------------------
# feishu_wiki_list_spaces
# ---------------------------------------------------------------------------

_WIKI_LIST_SPACES_URI = "/open-apis/wiki/v2/spaces"

FEISHU_WIKI_LIST_SPACES_SCHEMA = {
    "name": "feishu_wiki_list_spaces",
    "description": (
        "List all Feishu wiki spaces accessible to the signed-in user. "
        "Returns a list of spaces with their IDs, names, and descriptions. "
        "Requires scope wiki:wiki:readonly."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "page_size": {
                "type": "integer",
                "description": "Number of spaces per page (max 50, default 10).",
                "default": 10,
            },
            "page_token": {
                "type": "string",
                "description": "Pagination token from a previous response (optional).",
            },
        },
        "required": [],
    },
}


def _handle_wiki_list_spaces(args: dict, **kwargs) -> str:
    """Handler for feishu_wiki_list_spaces.

    Args:
        args: Tool arguments with optional page_size and page_token.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    page_size = args.get("page_size", 10)
    if not isinstance(page_size, int) or page_size < 1:
        page_size = 10
    if page_size > 50:
        page_size = 50

    page_token = (args.get("page_token") or "").strip()

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info("wiki_list_spaces: page_size=%d", page_size)

    queries = [("page_size", str(page_size))]
    if page_token:
        queries.append(("page_token", page_token))

    try:
        code, msg, data = fc.do_request(
            "GET",
            _WIKI_LIST_SPACES_URI,
            queries=queries,
            use_uat=True,
        )
    except Exception as exc:
        return tool_error(f"Request failed: {exc}")

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg or "", api_name="feishu_wiki_list_spaces",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        logger.warning("wiki_list_spaces failed: code=%d msg=%s", code, msg)
        return tool_error(f"Wiki list spaces failed: code={code} msg={msg}")

    items = data.get("items", [])
    logger.info("wiki_list_spaces: returned %d spaces", len(items))
    return tool_result({
        "spaces": items,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token"),
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_wiki_create_node",
    toolset="feishu_wiki",
    schema=FEISHU_WIKI_CREATE_NODE_SCHEMA,
    handler=_handle_wiki_create_node,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Create a new wiki node (doc, sheet, etc.) in a Feishu wiki space",
    emoji="\U0001f4da",
)

registry.register(
    name="feishu_wiki_move_node",
    toolset="feishu_wiki",
    schema=FEISHU_WIKI_MOVE_NODE_SCHEMA,
    handler=_handle_wiki_move_node,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Move a wiki node to a new parent in the same or a different space",
    emoji="\U0001f4da",
)

registry.register(
    name="feishu_wiki_list_spaces",
    toolset="feishu_wiki",
    schema=FEISHU_WIKI_LIST_SPACES_SCHEMA,
    handler=_handle_wiki_list_spaces,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List all wiki spaces accessible to the signed-in user",
    emoji="\U0001f4da",
)

# Register tool metadata (scopes + identity) in the shared registry
TOOLS_METADATA.update({
    "feishu_wiki_create_node": {
        "scopes": [_WIKI_SCOPE],
        "identity": "user",
    },
    "feishu_wiki_move_node": {
        "scopes": [_WIKI_SCOPE],
        "identity": "user",
    },
    "feishu_wiki_list_spaces": {
        "scopes": [_WIKI_READONLY_SCOPE],
        "identity": "user",
    },
})
