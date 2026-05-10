"""Feishu Docx Tool -- document create/update/block operations via Feishu/Lark API.

Provides three tools for managing Feishu documents as the signed-in user (UAT):
  - ``feishu_docx_create``      -- create a new document (optionally in a folder)
  - ``feishu_docx_update``      -- update a single block in a document
  - ``feishu_docx_get_blocks``  -- list all blocks in a document

All tools use ``FeishuClient.for_user()`` (UAT) and the ``do_request`` helper on the
FeishuClient instance.  Auth error codes are surfaced as semantic exceptions via
``raise_for_feishu_errcode``.
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

_DOCX_CREATE_SCOPE = "docx:document:create"
_DOCX_WRITE_SCOPE = "docx:document:write_only"
_DOCX_READONLY_SCOPE = "docx:document:readonly"

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

_DOCX_CREATE_URI = "/open-apis/docx/v1/documents"
_DOCX_UPDATE_BLOCK_URI = "/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}"
_DOCX_CREATE_CHILDREN_URI = "/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children"
_DOCX_GET_BLOCKS_URI = "/open-apis/docx/v1/documents/{document_id}/blocks"

_DEFAULT_TEXT_ELEMENT_STYLE = {
    "bold": False,
    "inline_code": False,
    "italic": False,
    "strikethrough": False,
    "underline": False,
}


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


def _normalize_text_element_patch(element: dict) -> dict:
    if not isinstance(element, dict):
        return element
    if "text_run" in element or "replace" in element or "insert" in element or "delete" in element:
        return element

    text_element = element.get("text_element")
    if not isinstance(text_element, dict):
        return element

    text_run = text_element.get("text_run")
    if isinstance(text_run, dict):
        normalized_run = dict(text_run)
    elif text_element.get("content") is not None:
        normalized_run = {"content": str(text_element["content"])}
    else:
        return element

    normalized_run.setdefault("text_element_style", dict(_DEFAULT_TEXT_ELEMENT_STYLE))
    index = element.get("text_element_index", element.get("index", 0))
    return {
        "text_element_index": index,
        "text_run": normalized_run,
    }


def _normalize_text_elements(elements: list) -> list:
    return [_normalize_text_element_patch(element) for element in elements]


def _text_elements_from_update_body(update_body: dict) -> list | None:
    update_text_elements = update_body.get("update_text_elements")
    if isinstance(update_text_elements, list):
        return _normalize_text_elements(update_text_elements)
    if isinstance(update_text_elements, dict) and isinstance(update_text_elements.get("elements"), list):
        return _normalize_text_elements(update_text_elements["elements"])
    update_text = update_body.get("update_text")
    if isinstance(update_text, dict) and isinstance(update_text.get("elements"), list):
        return _normalize_text_elements(update_text["elements"])
    return None


def _normalize_update_body(update_body: dict) -> dict:
    """Coerce LLM-friendly text element shapes into Feishu's PATCH schema."""
    normalized = dict(update_body)
    raw = normalized.get("update_text_elements")
    if isinstance(raw, list):
        if len(raw) == 1 and isinstance(raw[0], dict) and isinstance(raw[0].get("elements"), list):
            normalized["update_text_elements"] = {"elements": _normalize_text_elements(raw[0]["elements"])}
        else:
            normalized["update_text_elements"] = {"elements": _normalize_text_elements(raw)}
    elif isinstance(raw, dict) and isinstance(raw.get("elements"), list):
        normalized["update_text_elements"] = {"elements": _normalize_text_elements(raw["elements"])}
    return normalized


# ---------------------------------------------------------------------------
# feishu_docx_create
# ---------------------------------------------------------------------------

FEISHU_DOCX_CREATE_SCHEMA = {
    "name": "feishu_docx_create",
    "description": (
        "Create a new Feishu document as the signed-in user. "
        "Optionally places it in a specific Drive folder. "
        "Returns the new document_id and title."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title for the new document (optional; defaults to untitled).",
            },
            "folder_token": {
                "type": "string",
                "description": (
                    "Drive folder token where the document will be created (optional). "
                    "If omitted, the document is created in the user's root folder."
                ),
            },
        },
        "required": [],
    },
}


def _handle_docx_create(args: dict, **kwargs) -> str:
    """Handler for feishu_docx_create.

    Args:
        args: Tool arguments with optional title and folder_token.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    title = (args.get("title") or "").strip()
    folder_token = (args.get("folder_token") or "").strip()

    try:
        fc = FeishuClient.for_user()
    except (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError) as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    body: dict = {}
    if title:
        body["title"] = title
    if folder_token:
        body["folder_token"] = folder_token

    logger.info("docx_create: title=%r folder_token=%r", title, folder_token)

    code, msg, data = fc.do_request(
        "POST",
        _DOCX_CREATE_URI,
        body=body,
        use_uat=True,
    )

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_docx_create", user_open_id=fc.user_open_id
            )
        except (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"docx_create failed: code={code} msg={msg}")

    doc = data.get("document", data)
    document_id = doc.get("document_id", "") if isinstance(doc, dict) else ""
    doc_title = doc.get("title", "") if isinstance(doc, dict) else ""
    logger.info("docx_create: created document_id=%s", document_id)

    return tool_result({
        "document_id": document_id,
        "title": doc_title,
    })


# ---------------------------------------------------------------------------
# feishu_docx_update
# ---------------------------------------------------------------------------

FEISHU_DOCX_UPDATE_SCHEMA = {
    "name": "feishu_docx_update",
    "description": (
        "Update a single block in a Feishu document as the signed-in user. "
        "Supports text element replacement, image replacement, and file replacement "
        "by passing the appropriate update body dict. "
        "Returns the updated block data on success."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "document_id": {
                "type": "string",
                "description": "The document ID containing the block to update.",
            },
            "block_id": {
                "type": "string",
                "description": "The block ID to update within the document.",
            },
            "update_body": {
                "type": "object",
                "description": (
                    "The update payload dict. Supported keys: "
                    "'update_text_elements' (list), 'replace_image' (dict), "
                    "'replace_file' (dict). Pass exactly one of these."
                ),
            },
        },
        "required": ["document_id", "block_id", "update_body"],
    },
}


def _handle_docx_update(args: dict, **kwargs) -> str:
    """Handler for feishu_docx_update.

    Args:
        args: Tool arguments with document_id, block_id, and update_body.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    document_id = (args.get("document_id") or "").strip()
    block_id = (args.get("block_id") or "").strip()
    update_body = args.get("update_body")

    if not document_id:
        return tool_error("document_id is required")
    if not block_id:
        return tool_error("block_id is required")
    if not update_body or not isinstance(update_body, dict):
        return tool_error("update_body is required and must be a dict")

    try:
        fc = FeishuClient.for_user()
    except (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError) as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    if block_id == document_id:
        elements = _text_elements_from_update_body(update_body)
        if elements:
            uri = _DOCX_CREATE_CHILDREN_URI.format(document_id=document_id, block_id=block_id)
            logger.info("docx_update: root block requested, creating first text child document_id=%s", document_id)
            code, msg, data = fc.do_request(
                "POST",
                uri,
                queries=[("document_revision_id", "-1")],
                body={"children": [{"block_type": 2, "text": {"elements": elements}}]},
                use_uat=True,
            )
            if code != 0:
                try:
                    raise_for_feishu_errcode(
                        code,
                        msg,
                        api_name="feishu_docx_update",
                        user_open_id=fc.user_open_id,
                    )
                except (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError) as exc:
                    return tool_error(_auth_error_message(exc))
                return tool_error(f"docx_update create child failed: code={code} msg={msg}")
            children = data.get("children", [])
            block = children[0] if children else {}
            created_block_id = block.get("block_id", block_id) if isinstance(block, dict) else block_id
            logger.info("docx_update: created text child block_id=%s", created_block_id)
            return tool_result({
                "document_id": document_id,
                "block_id": created_block_id,
                "block": block,
            })

    uri = _DOCX_UPDATE_BLOCK_URI.format(document_id=document_id, block_id=block_id)
    logger.info("docx_update: document_id=%s block_id=%s", document_id, block_id)

    code, msg, data = fc.do_request(
        "PATCH",
        uri,
        body=_normalize_update_body(update_body),
        use_uat=True,
    )

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_docx_update", user_open_id=fc.user_open_id
            )
        except (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"docx_update failed: code={code} msg={msg}")

    block = data.get("block", data)
    logger.info("docx_update: updated block_id=%s", block_id)

    return tool_result({
        "document_id": document_id,
        "block_id": block_id,
        "block": block,
    })


# ---------------------------------------------------------------------------
# feishu_docx_get_blocks
# ---------------------------------------------------------------------------

FEISHU_DOCX_GET_BLOCKS_SCHEMA = {
    "name": "feishu_docx_get_blocks",
    "description": (
        "List all blocks in a Feishu document as the signed-in user. "
        "Always reads the latest revision (document_revision_id=-1). "
        "Returns items list and has_more flag for pagination."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "document_id": {
                "type": "string",
                "description": "The document ID whose blocks to retrieve.",
            },
            "page_size": {
                "type": "integer",
                "description": "Number of blocks per page (optional; defaults to 500).",
            },
            "page_token": {
                "type": "string",
                "description": "Pagination token from a previous response (optional).",
            },
        },
        "required": ["document_id"],
    },
}


def _handle_docx_get_blocks(args: dict, **kwargs) -> str:
    """Handler for feishu_docx_get_blocks.

    Args:
        args: Tool arguments with document_id and optional page_size/page_token.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    document_id = (args.get("document_id") or "").strip()
    if not document_id:
        return tool_error("document_id is required")

    page_size = args.get("page_size") or 500
    page_token = (args.get("page_token") or "").strip()

    try:
        fc = FeishuClient.for_user()
    except (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError) as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    uri = _DOCX_GET_BLOCKS_URI.format(document_id=document_id)
    queries = [
        ("page_size", str(page_size)),
        ("document_revision_id", "-1"),
    ]
    if page_token:
        queries.append(("page_token", page_token))

    logger.info("docx_get_blocks: document_id=%s page_size=%s", document_id, page_size)

    code, msg, data = fc.do_request(
        "GET",
        uri,
        queries=queries,
        use_uat=True,
    )

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_docx_get_blocks", user_open_id=fc.user_open_id
            )
        except (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"docx_get_blocks failed: code={code} msg={msg}")

    items = data.get("items", [])
    logger.info("docx_get_blocks: returned %d blocks", len(items))

    return tool_result({
        "document_id": document_id,
        "items": items,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token"),
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_docx_create",
    toolset="feishu_docx",
    schema=FEISHU_DOCX_CREATE_SCHEMA,
    handler=_handle_docx_create,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Create a new Feishu document with optional title and folder",
    emoji="\U0001f4c4",
)

registry.register(
    name="feishu_docx_update",
    toolset="feishu_docx",
    schema=FEISHU_DOCX_UPDATE_SCHEMA,
    handler=_handle_docx_update,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Update a block in a Feishu document (text, image, or file replacement)",
    emoji="\U0001f4c4",
)

registry.register(
    name="feishu_docx_get_blocks",
    toolset="feishu_docx",
    schema=FEISHU_DOCX_GET_BLOCKS_SCHEMA,
    handler=_handle_docx_get_blocks,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List all blocks in a Feishu document (latest revision)",
    emoji="\U0001f4c4",
)

# Register tool metadata (scopes + identity) in the shared registry
TOOLS_METADATA.update({
    "feishu_docx_create": {
        "scopes": [_DOCX_CREATE_SCOPE],
        "identity": "user",
    },
    "feishu_docx_update": {
        "scopes": [_DOCX_WRITE_SCOPE],
        "identity": "user",
    },
    "feishu_docx_get_blocks": {
        "scopes": [_DOCX_READONLY_SCOPE],
        "identity": "user",
    },
})
