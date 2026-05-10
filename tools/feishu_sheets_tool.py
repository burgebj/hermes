"""Feishu Sheets Tool -- spreadsheet read/write/append via Feishu/Lark API.

Provides three tools for operating on Feishu spreadsheets:
  - ``feishu_sheets_read_range``   -- read cell values from a range
  - ``feishu_sheets_write_range``  -- overwrite cell values in a range
  - ``feishu_sheets_append_rows``  -- append rows after existing data

Uses FeishuClient.for_user() (UAT) for all operations; scope: sheets:spreadsheet.
"""

import logging
import re

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

TOOLS_METADATA["feishu_sheets_read_range"] = {
    "identity": "user",
    "scopes": ["sheets:spreadsheet"],
}
TOOLS_METADATA["feishu_sheets_write_range"] = {
    "identity": "user",
    "scopes": ["sheets:spreadsheet"],
}
TOOLS_METADATA["feishu_sheets_append_rows"] = {
    "identity": "user",
    "scopes": ["sheets:spreadsheet"],
}


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
    """Return a UAT FeishuClient, or None on auth failure (logs reason)."""
    try:
        return FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        logger.warning("Feishu UAT unavailable: %s", exc)
        return None
    except ValueError as exc:
        logger.error("Feishu env vars missing: %s", exc)
        return None


_SHEETS_QUERY_URI = "/open-apis/sheets/v3/spreadsheets/:spreadsheet_token/sheets/query"


def _column_letter(index: int) -> str:
    result = ""
    while index > 0:
        index -= 1
        result = chr(ord("A") + (index % 26)) + result
        index //= 26
    return result or "A"


def _looks_like_cell_range(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]+[0-9]+(?::[A-Za-z]+[0-9]+)?$", value.strip()))


def _query_sheets(client: FeishuClient, spreadsheet_token: str, api_name: str) -> list[dict]:
    code, msg, data = client.do_request(
        "GET",
        _SHEETS_QUERY_URI,
        paths={"spreadsheet_token": spreadsheet_token},
        use_uat=True,
    )
    if code != 0:
        raise_for_feishu_errcode(
            code,
            msg or "",
            api_name=api_name,
            user_open_id=getattr(client, "user_open_id", "unknown"),
        )
        raise RuntimeError(f"Query sheets failed: code={code} msg={msg}")
    sheets = data.get("sheets") or []
    if not sheets:
        raise RuntimeError("spreadsheet has no worksheets")
    return sheets


def _sheet_ref_to_id(ref: str, sheets: list[dict]) -> str | None:
    target = ref.strip()
    if not target:
        return None
    target_lower = target.lower()
    for sheet in sheets:
        sheet_id = str(sheet.get("sheet_id") or sheet.get("sheetId") or "").strip()
        title = str(sheet.get("title") or "").strip()
        index = sheet.get("index")
        if target == sheet_id or target_lower == title.lower() or target == str(index):
            return sheet_id or None
    return None


def _resolve_sheet_range(
    client: FeishuClient,
    spreadsheet_token: str,
    range_val: str,
    *,
    api_name: str,
    values: list | None = None,
) -> str:
    """Resolve friendly sheet titles and A1-only ranges to Feishu sheet IDs."""
    range_val = (range_val or "").strip()
    sheets: list[dict] | None = None

    def ensure_sheets() -> list[dict]:
        nonlocal sheets
        if sheets is None:
            sheets = _query_sheets(client, spreadsheet_token, api_name)
        return sheets

    def first_sheet_id() -> str:
        sheet_id = _sheet_ref_to_id("", ensure_sheets())
        if sheet_id:
            return sheet_id
        first = ensure_sheets()[0]
        resolved = str(first.get("sheet_id") or first.get("sheetId") or "").strip()
        if not resolved:
            raise RuntimeError("spreadsheet has no worksheets")
        return resolved

    if not range_val:
        sheet_id = first_sheet_id()
        if values:
            rows = len(values)
            columns = max((len(row) for row in values if isinstance(row, list)), default=1)
            return f"{sheet_id}!A1:{_column_letter(columns)}{rows}"
        return sheet_id

    if "!" in range_val:
        prefix, suffix = range_val.split("!", 1)
        sheets_list = ensure_sheets()
        sheet_id = _sheet_ref_to_id(prefix, sheets_list) or prefix.strip()
        return f"{sheet_id}!{suffix.strip()}"

    if _looks_like_cell_range(range_val):
        return f"{first_sheet_id()}!{range_val}"

    sheets_list = ensure_sheets()
    return _sheet_ref_to_id(range_val, sheets_list) or range_val


# ---------------------------------------------------------------------------
# feishu_sheets_read_range
# ---------------------------------------------------------------------------

_READ_URI = "/open-apis/sheets/v2/spreadsheets/:spreadsheet_token/values/:range"

FEISHU_SHEETS_READ_RANGE_SCHEMA = {
    "name": "feishu_sheets_read_range",
    "description": (
        "Read cell values from a Feishu spreadsheet range. "
        "range format: <sheetId>!A1:D10 or just <sheetId> for the whole sheet. "
        "Requires sheets:spreadsheet scope."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "spreadsheet_token": {
                "type": "string",
                "description": "The spreadsheet token (from the URL or Drive API).",
            },
            "range": {
                "type": "string",
                "description": (
                    "Cell range to read. Format: <sheetId>!A1:D10 or <sheetId>. "
                    "Use feishu_sheets_read_range with the sheet's sheet_id from info."
                ),
            },
            "value_render_option": {
                "type": "string",
                "description": (
                    "How cell values are rendered: ToString (default), "
                    "FormattedValue, Formula, or UnformattedValue."
                ),
                "default": "ToString",
            },
        },
        "required": ["spreadsheet_token"],
    },
}


def _handle_sheets_read_range(args: dict, **kwargs) -> str:
    """Handler for feishu_sheets_read_range.

    Args:
        args: Tool arguments from user/model.
        **kwargs: Additional keyword arguments.

    Returns:
        JSON string (tool_error or tool_result).
    """
    spreadsheet_token = args.get("spreadsheet_token", "").strip()
    range_val = args.get("range", "").strip()

    if not spreadsheet_token:
        return tool_error("spreadsheet_token is required")

    value_render_option = args.get("value_render_option", "ToString") or "ToString"

    logger.info(
        "sheets_read_range: token=%s range=%s render=%s",
        spreadsheet_token, range_val, value_render_option,
    )

    client = _get_user_client()
    if client is None:
        return tool_error(
            "Feishu user token not available. Run 'hermes feishu-uat' to authorize."
        )
    try:
        range_val = _resolve_sheet_range(
            client,
            spreadsheet_token,
            range_val,
            api_name="feishu.sheets.read_range",
        )
    except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
        return tool_error(_auth_error_message(e))
    except RuntimeError as e:
        return tool_error(str(e))

    queries = [
        ("valueRenderOption", value_render_option),
        ("dateTimeRenderOption", "FormattedString"),
    ]

    code, msg, data = client.do_request(
        "GET",
        _READ_URI,
        paths={"spreadsheet_token": spreadsheet_token, "range": range_val},
        queries=queries,
        use_uat=True,
    )

    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu.sheets.read_range")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("sheets_read_range failed: code=%d msg=%s", code, msg)
        return tool_error(f"Read range failed: code={code} msg={msg}")

    value_range = data.get("valueRange", {})
    logger.info(
        "sheets_read_range: returned range=%s", value_range.get("range")
    )
    return tool_result(
        success=True,
        data={
            "range": value_range.get("range"),
            "values": value_range.get("values", []),
        },
    )


# ---------------------------------------------------------------------------
# feishu_sheets_write_range
# ---------------------------------------------------------------------------

_WRITE_URI = "/open-apis/sheets/v2/spreadsheets/:spreadsheet_token/values"

FEISHU_SHEETS_WRITE_RANGE_SCHEMA = {
    "name": "feishu_sheets_write_range",
    "description": (
        "Overwrite cell values in a Feishu spreadsheet range. "
        "WARNING: this is a destructive operation -- existing data in the range "
        "will be replaced. range format: <sheetId>!A1:D10. "
        "Requires sheets:spreadsheet scope."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "spreadsheet_token": {
                "type": "string",
                "description": "The spreadsheet token.",
            },
            "range": {
                "type": "string",
                "description": (
                    "Cell range to write. Format: <sheetId>!A1:D10. "
                    "Must match the dimensions of values."
                ),
            },
            "values": {
                "type": "array",
                "description": (
                    "2D array of values to write. Each inner array is one row. "
                    "Example: [[\"Name\",\"Age\"],[\"Alice\",30]]"
                ),
                "items": {
                    "type": "array",
                    "items": {},
                },
            },
        },
        "required": ["spreadsheet_token", "values"],
    },
}


def _handle_sheets_write_range(args: dict, **kwargs) -> str:
    """Handler for feishu_sheets_write_range.

    Args:
        args: Tool arguments from user/model.
        **kwargs: Additional keyword arguments.

    Returns:
        JSON string (tool_error or tool_result).
    """
    spreadsheet_token = args.get("spreadsheet_token", "").strip()
    range_val = args.get("range", "").strip()
    values = args.get("values")

    if not spreadsheet_token:
        return tool_error("spreadsheet_token is required")
    if not isinstance(values, list) or not values:
        return tool_error("values must be a non-empty 2D array")

    logger.info(
        "sheets_write_range: token=%s range=%s rows=%d",
        spreadsheet_token, range_val, len(values),
    )

    client = _get_user_client()
    if client is None:
        return tool_error(
            "Feishu user token not available. Run 'hermes feishu-uat' to authorize."
        )
    try:
        range_val = _resolve_sheet_range(
            client,
            spreadsheet_token,
            range_val,
            api_name="feishu.sheets.write_range",
            values=values,
        )
    except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
        return tool_error(_auth_error_message(e))
    except RuntimeError as e:
        return tool_error(str(e))

    body = {"valueRange": {"range": range_val, "values": values}}

    code, msg, data = client.do_request(
        "PUT",
        _WRITE_URI,
        paths={"spreadsheet_token": spreadsheet_token},
        body=body,
        use_uat=True,
    )

    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu.sheets.write_range")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("sheets_write_range failed: code=%d msg=%s", code, msg)
        return tool_error(f"Write range failed: code={code} msg={msg}")

    logger.info(
        "sheets_write_range: updated %d cells", data.get("updatedCells", 0)
    )
    return tool_result(
        success=True,
        data={
            "updated_range": data.get("updatedRange"),
            "updated_rows": data.get("updatedRows"),
            "updated_columns": data.get("updatedColumns"),
            "updated_cells": data.get("updatedCells"),
            "revision": data.get("revision"),
        },
    )


# ---------------------------------------------------------------------------
# feishu_sheets_append_rows
# ---------------------------------------------------------------------------

_APPEND_URI = "/open-apis/sheets/v2/spreadsheets/:spreadsheet_token/values_append"

FEISHU_SHEETS_APPEND_ROWS_SCHEMA = {
    "name": "feishu_sheets_append_rows",
    "description": (
        "Append rows after existing data in a Feishu spreadsheet. "
        "Data is inserted after the last non-empty row in the range. "
        "range format: <sheetId>!A1:D10 or just <sheetId>. "
        "Requires sheets:spreadsheet scope."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "spreadsheet_token": {
                "type": "string",
                "description": "The spreadsheet token.",
            },
            "range": {
                "type": "string",
                "description": (
                    "Range to append into. Format: <sheetId>!A1:D10 or <sheetId>. "
                    "Rows are appended after the last occupied row in this range."
                ),
            },
            "values": {
                "type": "array",
                "description": (
                    "2D array of rows to append. Each inner array is one row. "
                    "Example: [[\"Bob\",25],[\"Carol\",28]]"
                ),
                "items": {
                    "type": "array",
                    "items": {},
                },
            },
        },
        "required": ["spreadsheet_token", "values"],
    },
}


def _handle_sheets_append_rows(args: dict, **kwargs) -> str:
    """Handler for feishu_sheets_append_rows.

    Args:
        args: Tool arguments from user/model.
        **kwargs: Additional keyword arguments.

    Returns:
        JSON string (tool_error or tool_result).
    """
    spreadsheet_token = args.get("spreadsheet_token", "").strip()
    range_val = args.get("range", "").strip()
    values = args.get("values")

    if not spreadsheet_token:
        return tool_error("spreadsheet_token is required")
    if not isinstance(values, list) or not values:
        return tool_error("values must be a non-empty 2D array")

    logger.info(
        "sheets_append_rows: token=%s range=%s rows=%d",
        spreadsheet_token, range_val, len(values),
    )

    client = _get_user_client()
    if client is None:
        return tool_error(
            "Feishu user token not available. Run 'hermes feishu-uat' to authorize."
        )
    try:
        range_val = _resolve_sheet_range(
            client,
            spreadsheet_token,
            range_val,
            api_name="feishu.sheets.append_rows",
        )
    except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
        return tool_error(_auth_error_message(e))
    except RuntimeError as e:
        return tool_error(str(e))

    body = {"valueRange": {"range": range_val, "values": values}}

    code, msg, data = client.do_request(
        "POST",
        _APPEND_URI,
        paths={"spreadsheet_token": spreadsheet_token},
        body=body,
        use_uat=True,
    )

    if code != 0:
        try:
            raise_for_feishu_errcode(code, msg or "", api_name="feishu.sheets.append_rows")
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as e:
            return tool_error(_auth_error_message(e))
        logger.warning("sheets_append_rows failed: code=%d msg=%s", code, msg)
        return tool_error(f"Append rows failed: code={code} msg={msg}")

    updates = data.get("updates", {})
    logger.info(
        "sheets_append_rows: updated %d cells", updates.get("updatedCells", 0)
    )
    return tool_result(
        success=True,
        data={
            "table_range": data.get("tableRange"),
            "updated_range": updates.get("updatedRange"),
            "updated_rows": updates.get("updatedRows"),
            "updated_columns": updates.get("updatedColumns"),
            "updated_cells": updates.get("updatedCells"),
            "revision": updates.get("revision"),
        },
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_sheets_read_range",
    toolset="feishu_sheets",
    schema=FEISHU_SHEETS_READ_RANGE_SCHEMA,
    handler=_handle_sheets_read_range,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Read cell values from a spreadsheet range",
    emoji="\U0001f4ca",
)

registry.register(
    name="feishu_sheets_write_range",
    toolset="feishu_sheets",
    schema=FEISHU_SHEETS_WRITE_RANGE_SCHEMA,
    handler=_handle_sheets_write_range,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Overwrite cell values in a spreadsheet range",
    emoji="✏️",
)

registry.register(
    name="feishu_sheets_append_rows",
    toolset="feishu_sheets",
    schema=FEISHU_SHEETS_APPEND_ROWS_SCHEMA,
    handler=_handle_sheets_append_rows,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Append rows after existing data in a spreadsheet",
    emoji="➕",
)
