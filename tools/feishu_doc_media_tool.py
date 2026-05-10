"""Feishu Doc Media Tool -- upload and download media attached to documents.

Provides two tools for managing media embedded in Feishu docs/sheets as the
signed-in user (UAT):
  - ``feishu_doc_media_upload``   -- upload a local file as doc-embedded media
  - ``feishu_doc_media_download`` -- download doc media by file_token (returns summary)

Both tools use ``FeishuClient.for_user()`` (UAT) and the ``/open-apis/drive/v1/medias/``
endpoints (note: ``medias``, not ``files``). These are DIFFERENT from the standalone
Drive file endpoints in ``feishu_drive_file_tool.py``.

Error codes 99991672 and 99991679 are surfaced as semantic auth exceptions via
``raise_for_feishu_errcode``.
"""

import json
import logging
import os

import requests

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

_DRIVE_SCOPE = "drive:drive"
_DRIVE_READONLY_SCOPE = "drive:drive:readonly"

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


def _get_feishu_client():
    """Build a UAT FeishuClient or return a tool_error string on failure."""
    try:
        return FeishuClient.for_user(), None
    except NeedAuthorizationError as exc:
        return None, tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return None, tool_error(f"Feishu configuration error: {exc}")


# ---------------------------------------------------------------------------
# feishu_doc_media_upload
# ---------------------------------------------------------------------------

_UPLOAD_MEDIA_URI = "/open-apis/drive/v1/medias/upload_all"
_DOCX_CREATE_CHILDREN_URI = "/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children"
_DOCX_BATCH_UPDATE_URI = "/open-apis/docx/v1/documents/{document_id}/blocks/batch_update"

_VALID_PARENT_TYPES = frozenset({
    "docx_image",
    "doc_image",
    "sheet_image",
    "docx_file",
    "doc_file",
    "sheet_file",
    "vc_virtual_background",
    "bitable_image",
    "bitable_file",
    "moments_image",
})


def _is_docx_block_id(value: str) -> bool:
    return value.startswith("doxc")


def _compact_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _upload_media_raw(
    *,
    access_token: str,
    file_name: str,
    parent_type: str,
    parent_node: str,
    file_path: str,
    file_size: int,
    extra: dict | None = None,
) -> tuple[int, str, dict]:
    url = f"https://open.feishu.cn{_UPLOAD_MEDIA_URI}"
    form = {
        "file_name": file_name,
        "parent_type": parent_type,
        "parent_node": parent_node,
        "size": str(file_size),
    }
    if extra:
        form["extra"] = _compact_json(extra)
    with open(file_path, "rb") as fh:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            data=form,
            files={"file": (file_name, fh)},
            timeout=60,
        )
    try:
        body = response.json()
    except ValueError:
        return -1, f"HTTP {response.status_code}: {(response.text or '')[:200]}", {}
    if not isinstance(body, dict):
        return -1, f"HTTP {response.status_code}: non-object JSON response", {}
    return int(body.get("code", -1)), str(body.get("msg", "")), body.get("data") or {}


def _create_docx_image_block(fc, document_id: str) -> tuple[int, str, dict, str]:
    uri = _DOCX_CREATE_CHILDREN_URI.format(document_id=document_id, block_id=document_id)
    code, msg, data = fc.do_request(
        "POST",
        uri,
        queries=[("document_revision_id", "-1")],
        body={"children": [{"block_type": 27, "image": {}}]},
        use_uat=True,
    )
    if code != 0:
        return code, msg, data, ""
    children = data.get("children", []) if isinstance(data, dict) else []
    block = children[0] if children else {}
    block_id = block.get("block_id", "") if isinstance(block, dict) else ""
    if not block_id:
        return -1, "create docx image block returned no block_id", data, ""
    return 0, msg, data, block_id


def _patch_docx_image_block(fc, *, document_id: str, block_id: str, file_token: str) -> tuple[int, str, dict]:
    uri = _DOCX_BATCH_UPDATE_URI.format(document_id=document_id)
    return fc.do_request(
        "PATCH",
        uri,
        queries=[("document_revision_id", "-1")],
        body={
            "requests": [
                {
                    "block_id": block_id,
                    "replace_image": {"token": file_token, "align": 2},
                }
            ]
        },
        use_uat=True,
    )

FEISHU_DOC_MEDIA_UPLOAD_SCHEMA = {
    "name": "feishu_doc_media_upload",
    "description": (
        "Upload a local file as media embedded in a Feishu document, sheet, or bitable "
        "as the signed-in user. Uses the /drive/v1/medias/upload_all endpoint. "
        "Returns the file_token of the newly uploaded media. "
        "This is for doc-embedded media (images in docx, file attachments in sheets, etc.), "
        "NOT for standalone Drive files (use feishu_drive_upload_file for those)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "Display name for the media file (including extension).",
            },
            "parent_type": {
                "type": "string",
                "description": (
                    "Type of the parent document. One of: "
                    "'docx_image', 'doc_image', 'sheet_image', 'docx_file', 'doc_file', "
                    "'sheet_file', 'vc_virtual_background', 'bitable_image', "
                    "'bitable_file', 'moments_image'."
                ),
            },
            "parent_node": {
                "type": "string",
                "description": (
                    "Token of the owner document or sheet "
                    "(e.g. docx token, sheet token, bitable app token)."
                ),
            },
            "file_path": {
                "type": "string",
                "description": "Absolute path to the local file on the agent host to upload.",
            },
        },
        "required": ["file_name", "parent_type", "parent_node", "file_path"],
    },
}


def _handle_doc_media_upload(args: dict, **kwargs) -> str:
    """Handler for feishu_doc_media_upload.

    Args:
        args: Tool arguments with file_name, parent_type, parent_node, file_path.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    file_name = (args.get("file_name") or "").strip()
    parent_type = (args.get("parent_type") or "").strip()
    parent_node = (args.get("parent_node") or "").strip()
    file_path = (args.get("file_path") or "").strip()

    if not file_name:
        return tool_error("file_name is required")
    if not parent_type:
        return tool_error("parent_type is required")
    if parent_type not in _VALID_PARENT_TYPES:
        return tool_error(
            f"parent_type must be one of: {', '.join(sorted(_VALID_PARENT_TYPES))}; got {parent_type!r}"
        )
    if not parent_node:
        return tool_error("parent_node is required")
    if not file_path:
        return tool_error("file_path is required")

    if not os.path.isfile(file_path):
        return tool_error(f"file_path does not exist or is not a file: {file_path}")

    file_size = os.path.getsize(file_path)

    fc, err = _get_feishu_client()
    if err:
        return err

    logger.info(
        "doc_media_upload: file_name=%r parent_type=%r parent_node=%r file_path=%r size=%d",
        file_name, parent_type, parent_node, file_path, file_size,
    )

    document_id = ""
    block_id = parent_node
    if parent_type == "docx_image" and not _is_docx_block_id(parent_node):
        document_id = parent_node
        code, msg, create_data, block_id = _create_docx_image_block(fc, document_id)
        if code != 0:
            try:
                raise_for_feishu_errcode(
                    code, msg, api_name="feishu_doc_media_upload",
                    user_open_id=fc.user_open_id,
                )
            except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
                return tool_error(_auth_error_message(exc))
            return tool_error(f"Create docx image block failed: code={code} msg={msg}")
        logger.info("doc_media_upload: created docx image block_id=%s", block_id)

    code, msg, data = _upload_media_raw(
        access_token=fc.access_token,
        file_name=file_name,
        parent_type=parent_type,
        parent_node=block_id,
        file_path=file_path,
        file_size=file_size,
        extra={"drive_route_token": document_id} if document_id else None,
    )

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_doc_media_upload",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Upload media failed: code={code} msg={msg}")

    file_token = data.get("file_token", "")
    patch_data: dict = {}
    if document_id:
        code, msg, patch_data = _patch_docx_image_block(
            fc,
            document_id=document_id,
            block_id=block_id,
            file_token=file_token,
        )
        if code != 0:
            try:
                raise_for_feishu_errcode(
                    code, msg, api_name="feishu_doc_media_upload",
                    user_open_id=fc.user_open_id,
                )
            except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
                return tool_error(_auth_error_message(exc))
            return tool_error(f"Patch docx image block failed: code={code} msg={msg}")
    logger.info("doc_media_upload: uploaded file_token=%s", file_token)
    result = {"file_token": file_token}
    if document_id:
        result.update({"document_id": document_id, "block_id": block_id, "block": (patch_data.get("blocks") or [{}])[0]})
    return tool_result(result)


# ---------------------------------------------------------------------------
# feishu_doc_media_download
# ---------------------------------------------------------------------------

_DOWNLOAD_MEDIA_URI = "/open-apis/drive/v1/medias/:file_token/download"

FEISHU_DOC_MEDIA_DOWNLOAD_SCHEMA = {
    "name": "feishu_doc_media_download",
    "description": (
        "Download media embedded in a Feishu document by its file_token as the signed-in user. "
        "Uses the /drive/v1/medias/{file_token}/download endpoint. "
        "Returns a summary with the file_token, size, and mime hint — "
        "raw binary bytes are not returned through the tool result. "
        "This is for doc-embedded media, NOT for standalone Drive files "
        "(use feishu_drive_download_file for those)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_token": {
                "type": "string",
                "description": "Token of the doc media to download.",
            },
        },
        "required": ["file_token"],
    },
}


def _handle_doc_media_download(args: dict, **kwargs) -> str:
    """Handler for feishu_doc_media_download.

    Args:
        args: Tool arguments with file_token.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error (summary only, no raw bytes).
    """
    file_token = (args.get("file_token") or "").strip()
    if not file_token:
        return tool_error("file_token is required")

    fc, err = _get_feishu_client()
    if err:
        return err

    logger.info("doc_media_download: file_token=%s", file_token)

    try:
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError:
        return tool_error("lark_oapi not installed")

    request = (
        BaseRequest.builder()
        .http_method(HttpMethod.GET)
        .uri(_DOWNLOAD_MEDIA_URI)
        .token_types({AccessTokenType.USER})
        .paths({"file_token": file_token})
        .build()
    )
    opt = (
        RequestOption.builder()
        .user_access_token(fc.access_token)
        .build()
    )
    response = fc.sdk.request(request, opt)

    code = getattr(response, "code", None)
    msg = getattr(response, "msg", "")
    raw = getattr(response, "raw", None)
    raw_content = b""
    mime = ""
    if raw and hasattr(raw, "content"):
        raw_content = raw.content or b""
        # If response starts with '{' it is a JSON error payload
        if raw_content and raw_content[:1] == b"{":
            try:
                body_json = json.loads(raw_content)
                if code is None:
                    code = body_json.get("code", -1)
                if not msg:
                    msg = body_json.get("msg", "")
            except (json.JSONDecodeError, AttributeError):
                pass
        # Try to sniff MIME from first bytes for informational purposes
        if raw_content and raw_content[:1] != b"{":
            if raw_content[:4] == b"\x89PNG":
                mime = "image/png"
            elif raw_content[:2] == b"\xff\xd8":
                mime = "image/jpeg"
            elif raw_content[:4] == b"GIF8":
                mime = "image/gif"
            elif raw_content[:4] == b"%PDF":
                mime = "application/pdf"

    # A non-JSON response with no error code means successful binary download
    if code is not None and code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_doc_media_download",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Download media failed: code={code} msg={msg}")

    size = len(raw_content) if raw_content else 0
    logger.info("doc_media_download: file_token=%s size=%d bytes mime=%r", file_token, size, mime)
    return tool_result({
        "file_token": file_token,
        "size": size,
        "mime": mime,
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_doc_media_upload",
    toolset="feishu_drive_file",
    schema=FEISHU_DOC_MEDIA_UPLOAD_SCHEMA,
    handler=_handle_doc_media_upload,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Upload a local file as media embedded in a Feishu doc/sheet (medias/upload_all)",
    emoji="📁",
)

registry.register(
    name="feishu_doc_media_download",
    toolset="feishu_drive_file",
    schema=FEISHU_DOC_MEDIA_DOWNLOAD_SCHEMA,
    handler=_handle_doc_media_download,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Download doc-embedded media by file_token and return summary (no raw bytes)",
    emoji="📁",
)

# Register tool metadata (scopes + identity) in the shared registry
TOOLS_METADATA.update({
    "feishu_doc_media_upload": {
        "scopes": [_DRIVE_SCOPE],
        "identity": "user",
    },
    "feishu_doc_media_download": {
        "scopes": [_DRIVE_READONLY_SCOPE, _DRIVE_SCOPE],
        "identity": "user",
    },
})
