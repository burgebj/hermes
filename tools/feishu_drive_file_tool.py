"""Feishu Drive File Tool -- file listing, upload, and download via Feishu/Lark Drive API.

Provides three tools for managing Drive files as the signed-in user (UAT):
  - ``feishu_drive_list_files``    -- list files/folders under a given folder token
  - ``feishu_drive_upload_file``   -- upload a local file to Drive (upload_all endpoint)
  - ``feishu_drive_download_file`` -- download a file by token (returns summary, not raw bytes)

All tools use ``FeishuClient.for_user()`` (UAT) and the ``do_request`` helper on the
FeishuClient instance.  Error codes 99991672 and 99991679 are surfaced as semantic
auth exceptions via ``raise_for_feishu_errcode``.
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
# feishu_drive_list_files
# ---------------------------------------------------------------------------

_LIST_FILES_URI = "/open-apis/drive/v1/files"

FEISHU_DRIVE_LIST_FILES_SCHEMA = {
    "name": "feishu_drive_list_files",
    "description": (
        "List files and folders under a given Drive folder token as the signed-in user. "
        "Returns a page of items with their tokens, names, and types. "
        "Pass the folder_token of the target folder; use an empty string for the root."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "folder_token": {
                "type": "string",
                "description": (
                    "Token of the folder to list. Leave empty to list the root My Drive folder."
                ),
            },
            "page_size": {
                "type": "integer",
                "description": "Number of items per page (1-200, default 50).",
            },
            "page_token": {
                "type": "string",
                "description": "Pagination token from a previous response (optional).",
            },
        },
        "required": [],
    },
}


def _handle_drive_list_files(args: dict, **kwargs) -> str:
    """Handler for feishu_drive_list_files.

    Args:
        args: Tool arguments with optional folder_token, page_size, page_token.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    folder_token = (args.get("folder_token") or "").strip()
    page_size = args.get("page_size") or 50
    page_token = (args.get("page_token") or "").strip()

    fc, err = _get_feishu_client()
    if err:
        return err

    queries = [
        ("user_id_type", "open_id"),
        ("page_size", str(page_size)),
    ]
    if folder_token:
        queries.append(("folder_token", folder_token))
    if page_token:
        queries.append(("page_token", page_token))

    logger.info(
        "drive_list_files: folder_token=%r page_size=%s", folder_token, page_size
    )

    code, msg, data = fc.do_request(
        "GET",
        _LIST_FILES_URI,
        queries=queries,
        use_uat=True,
    )

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_drive_list_files",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"List files failed: code={code} msg={msg}")

    files = data.get("files", [])
    logger.info("drive_list_files: returned %d item(s)", len(files))
    return tool_result({
        "files": files,
        "has_more": data.get("has_more", False),
        "next_page_token": data.get("next_page_token"),
    })


# ---------------------------------------------------------------------------
# feishu_drive_upload_file
# ---------------------------------------------------------------------------

_UPLOAD_FILE_URI = "/open-apis/drive/v1/files/upload_all"


def _upload_file_raw(
    *,
    access_token: str,
    file_name: str,
    parent_node: str,
    file_path: str,
    file_size: int,
) -> tuple[int, str, dict]:
    url = f"https://open.feishu.cn{_UPLOAD_FILE_URI}"
    with open(file_path, "rb") as fh:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            data={
                "file_name": file_name,
                "parent_type": "explorer",
                "parent_node": parent_node,
                "size": str(file_size),
            },
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

FEISHU_DRIVE_UPLOAD_FILE_SCHEMA = {
    "name": "feishu_drive_upload_file",
    "description": (
        "Upload a local file to Feishu Drive as the signed-in user. "
        "Uses the upload_all endpoint (suitable for files under 20 MB). "
        "Returns the file_token of the newly uploaded file."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "Display name for the file in Drive (including extension).",
            },
            "parent_node": {
                "type": "string",
                "description": "Folder token of the destination folder in Drive. Defaults to root.",
            },
            "file_path": {
                "type": "string",
                "description": "Absolute path to the local file on the agent host to upload.",
            },
        },
        "required": ["file_name", "file_path"],
    },
}


def _handle_drive_upload_file(args: dict, **kwargs) -> str:
    """Handler for feishu_drive_upload_file.

    Args:
        args: Tool arguments with file_name, parent_node, file_path.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    file_name = (args.get("file_name") or "").strip()
    parent_node = (args.get("parent_node") or "root").strip()
    file_path = (args.get("file_path") or "").strip()

    if not file_name:
        return tool_error("file_name is required")
    if not file_path:
        return tool_error("file_path is required")

    if not os.path.isfile(file_path):
        return tool_error(f"file_path does not exist or is not a file: {file_path}")

    file_size = os.path.getsize(file_path)

    fc, err = _get_feishu_client()
    if err:
        return err

    logger.info(
        "drive_upload_file: file_name=%r parent_node=%r file_path=%r size=%d",
        file_name, parent_node, file_path, file_size,
    )

    if parent_node == "root":
        parent_node = ""

    code, msg, data = _upload_file_raw(
        access_token=fc.access_token,
        file_name=file_name,
        parent_node=parent_node,
        file_path=file_path,
        file_size=file_size,
    )

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_drive_upload_file",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Upload file failed: code={code} msg={msg}")

    file_token = data.get("file_token", "")
    logger.info("drive_upload_file: uploaded file_token=%s", file_token)
    return tool_result({"file_token": file_token})


# ---------------------------------------------------------------------------
# feishu_drive_download_file
# ---------------------------------------------------------------------------

_DOWNLOAD_FILE_URI = "/open-apis/drive/v1/files/:file_token/download"

FEISHU_DRIVE_DOWNLOAD_FILE_SCHEMA = {
    "name": "feishu_drive_download_file",
    "description": (
        "Download a Drive file by its file_token as the signed-in user. "
        "Returns a summary with the file_token, a download_url hint, and content size — "
        "raw binary bytes are not returned through the tool result."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_token": {
                "type": "string",
                "description": "Token of the Drive file to download.",
            },
        },
        "required": ["file_token"],
    },
}


def _handle_drive_download_file(args: dict, **kwargs) -> str:
    """Handler for feishu_drive_download_file.

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

    logger.info("drive_download_file: file_token=%s", file_token)

    try:
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError:
        return tool_error("lark_oapi not installed")

    request = (
        BaseRequest.builder()
        .http_method(HttpMethod.GET)
        .uri(_DOWNLOAD_FILE_URI)
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
    if raw and hasattr(raw, "content"):
        raw_content = raw.content or b""
        # If response is JSON (error), parse it; otherwise it's binary file data
        if raw_content and raw_content[:1] == b"{":
            try:
                body_json = json.loads(raw_content)
                if code is None:
                    code = body_json.get("code", -1)
                if not msg:
                    msg = body_json.get("msg", "")
            except (json.JSONDecodeError, AttributeError):
                pass

    # A non-JSON response with no error code means successful binary download
    if code is not None and code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_drive_download_file",
                user_open_id=fc.user_open_id,
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Download file failed: code={code} msg={msg}")

    size = len(raw_content) if raw_content else 0
    download_url = f"/open-apis/drive/v1/files/{file_token}/download"
    logger.info("drive_download_file: file_token=%s size=%d bytes", file_token, size)
    return tool_result({
        "file_token": file_token,
        "download_url": download_url,
        "size": size,
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_drive_list_files",
    toolset="feishu_drive_file",
    schema=FEISHU_DRIVE_LIST_FILES_SCHEMA,
    handler=_handle_drive_list_files,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List files and folders under a Drive folder token",
    emoji="📁",
)

registry.register(
    name="feishu_drive_upload_file",
    toolset="feishu_drive_file",
    schema=FEISHU_DRIVE_UPLOAD_FILE_SCHEMA,
    handler=_handle_drive_upload_file,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Upload a local file to Feishu Drive (upload_all endpoint)",
    emoji="📁",
)

registry.register(
    name="feishu_drive_download_file",
    toolset="feishu_drive_file",
    schema=FEISHU_DRIVE_DOWNLOAD_FILE_SCHEMA,
    handler=_handle_drive_download_file,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Download a Drive file by token and return summary (no raw bytes)",
    emoji="📁",
)

# Register tool metadata (scopes + identity) in the shared registry
TOOLS_METADATA.update({
    "feishu_drive_list_files": {
        "scopes": [_DRIVE_SCOPE],
        "identity": "user",
    },
    "feishu_drive_upload_file": {
        "scopes": [_DRIVE_SCOPE],
        "identity": "user",
    },
    "feishu_drive_download_file": {
        "scopes": [_DRIVE_SCOPE],
        "identity": "user",
    },
})
