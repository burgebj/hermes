"""OpenClaw-Lark action parity tools.

This module fills action-level gaps where OpenClaw exposes a dedicated action
and Hermes already has the same Feishu identity/client substrate. The handlers
are intentionally thin OAPI wrappers: validate required arguments, normalize a
few OpenClaw-friendly aliases, call Feishu with UAT/TAT, and return the raw data.
"""

from __future__ import annotations

import logging
from typing import Any

from tools.feishu_oapi_client import (
    AppScopeMissingError,
    FeishuClient,
    NeedAuthorizationError,
    TOOLS_METADATA,
    UserAuthRequiredError,
    UserScopeInsufficientError,
    raise_for_feishu_errcode,
)
from tools.feishu_calendar_tool import _normalize_instance_time
from tools.feishu_sheets_tool import _resolve_sheet_range
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


def _check_feishu() -> bool:
    try:
        import lark_oapi  # noqa: F401
        return True
    except ImportError:
        return False


def _auth_error_message(exc: Exception) -> str:
    if isinstance(exc, NeedAuthorizationError):
        return f"Need Feishu authorization: {exc}. Run 'hermes feishu-uat' to authorize."
    if isinstance(exc, AppScopeMissingError):
        return f"App scope missing: {exc}"
    if isinstance(exc, UserAuthRequiredError):
        return f"User authorization required: {exc}"
    if isinstance(exc, UserScopeInsufficientError):
        return f"User scope insufficient: {exc}"
    return str(exc)


def _client(identity: str) -> FeishuClient:
    if identity == "tenant":
        return FeishuClient.for_tenant()
    return FeishuClient.for_user()


def _as_str(value: Any) -> str:
    return str(value or "").strip()


def _optional_query(args: dict, names: list[str]) -> list[tuple[str, str]]:
    query: list[tuple[str, str]] = []
    for name in names:
        value = args.get(name)
        if value is not None and value != "":
            query.append((name, str(value)))
    return query


def _optional_body(args: dict, names: list[str]) -> dict:
    body: dict[str, Any] = {}
    for name in names:
        value = args.get(name)
        if value is not None and value != "":
            body[name] = value
    return body


def _require(args: dict, names: list[str]) -> str | None:
    missing = [name for name in names if args.get(name) in (None, "", [])]
    if missing:
        return ", ".join(missing) + " is required"
    return None


def _extract_primary_calendar_id(data: dict) -> str:
    calendars = data.get("calendars") or []
    if not calendars:
        return ""
    first = calendars[0]
    if isinstance(first, dict):
        if first.get("calendar_id"):
            return str(first["calendar_id"])
        calendar = first.get("calendar")
        if isinstance(calendar, dict) and calendar.get("calendar_id"):
            return str(calendar["calendar_id"])
    return ""


def _resolve_calendar_id(fc: FeishuClient, calendar_id: str) -> str:
    if calendar_id:
        return calendar_id
    code, msg, data = fc.do_request(
        "POST",
        "/open-apis/calendar/v4/calendars/primary",
        queries=[("user_id_type", "open_id")],
        body={},
        use_uat=True,
    )
    if code != 0:
        raise_for_feishu_errcode(
            code,
            msg or "",
            api_name="feishu_calendar_calendar.primary",
            user_open_id=fc.user_open_id,
        )
        raise RuntimeError(f"primary calendar failed: code={code} msg={msg}")
    resolved = _extract_primary_calendar_id(data)
    if not resolved:
        raise RuntimeError("primary calendar_id missing in Feishu response")
    return resolved


def _call_feishu(
    tool_name: str,
    method: str,
    uri: str,
    *,
    identity: str = "user",
    paths: dict | None = None,
    queries: list[tuple[str, str]] | None = None,
    body: dict | None = None,
) -> str:
    try:
        fc = _client(identity)
    except (NeedAuthorizationError, ValueError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, NeedAuthorizationError) else f"Feishu configuration error: {exc}")

    try:
        request_kwargs: dict[str, Any] = {"use_uat": identity != "tenant"}
        if paths is not None:
            request_kwargs["paths"] = paths
        if queries is not None:
            request_kwargs["queries"] = queries
        if body is not None:
            request_kwargs["body"] = body
        code, msg, data = fc.do_request(method, uri, **request_kwargs)
    except (NeedAuthorizationError, RuntimeError, ValueError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, NeedAuthorizationError) else str(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code,
                msg or "",
                api_name=tool_name,
                user_open_id=getattr(fc, "user_open_id", None),
            )
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"{tool_name} failed: code={code} msg={msg}")
    return tool_result(data or {"success": True})


def _schema(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    }


S = {
    "str": {"type": "string"},
    "int": {"type": "integer"},
    "num": {"type": "number"},
    "bool": {"type": "boolean"},
    "obj": {"type": "object"},
    "arr": {"type": "array", "items": {"type": "object"}},
    "str_arr": {"type": "array", "items": {"type": "string"}},
}


def _calendar_primary(args: dict, **kwargs) -> str:
    return _call_feishu(
        "feishu_calendar_primary_calendar",
        "POST",
        "/open-apis/calendar/v4/calendars/primary",
        queries=[("user_id_type", "open_id")],
        body={},
    )


def _calendar_get(args: dict, **kwargs) -> str:
    if err := _require(args, ["calendar_id"]):
        return tool_error(err)
    return _call_feishu(
        "feishu_calendar_get_calendar",
        "GET",
        "/open-apis/calendar/v4/calendars/:calendar_id",
        paths={"calendar_id": _as_str(args.get("calendar_id"))},
        queries=[("user_id_type", "open_id")],
    )


def _calendar_event_update(args: dict, **kwargs) -> str:
    if err := _require(args, ["event_id"]):
        return tool_error(err)
    try:
        fc = FeishuClient.for_user()
        calendar_id = _resolve_calendar_id(fc, _as_str(args.get("calendar_id")))
    except (NeedAuthorizationError, ValueError, RuntimeError, AppScopeMissingError, UserAuthRequiredError) as exc:
        return tool_error(_auth_error_message(exc) if not isinstance(exc, RuntimeError) else str(exc))
    body = _optional_body(args, ["summary", "description", "location"])
    if args.get("start_time"):
        body["start_time"] = {"timestamp": _as_str(args["start_time"])}
    if args.get("end_time"):
        body["end_time"] = {"timestamp": _as_str(args["end_time"])}
    if not body:
        return tool_error("at least one event field is required")
    return _call_feishu(
        "feishu_calendar_update_event",
        "PATCH",
        "/open-apis/calendar/v4/calendars/:calendar_id/events/:event_id",
        paths={"calendar_id": calendar_id, "event_id": _as_str(args.get("event_id"))},
        queries=[("user_id_type", "open_id")],
        body=body,
    )


def _calendar_event_delete(args: dict, **kwargs) -> str:
    if err := _require(args, ["event_id"]):
        return tool_error(err)
    try:
        fc = FeishuClient.for_user()
        calendar_id = _resolve_calendar_id(fc, _as_str(args.get("calendar_id")))
    except (NeedAuthorizationError, ValueError, RuntimeError, AppScopeMissingError, UserAuthRequiredError) as exc:
        return tool_error(_auth_error_message(exc) if not isinstance(exc, RuntimeError) else str(exc))
    return _call_feishu(
        "feishu_calendar_delete_event",
        "DELETE",
        "/open-apis/calendar/v4/calendars/:calendar_id/events/:event_id",
        paths={"calendar_id": calendar_id, "event_id": _as_str(args.get("event_id"))},
        queries=[("need_notification", str(args.get("need_notification", True)).lower())],
    )


def _calendar_event_search(args: dict, **kwargs) -> str:
    if err := _require(args, ["query"]):
        return tool_error(err)
    try:
        fc = FeishuClient.for_user()
        calendar_id = _resolve_calendar_id(fc, _as_str(args.get("calendar_id")))
    except (NeedAuthorizationError, ValueError, RuntimeError, AppScopeMissingError, UserAuthRequiredError) as exc:
        return tool_error(_auth_error_message(exc) if not isinstance(exc, RuntimeError) else str(exc))
    queries = _optional_query(args, ["page_size", "page_token"])
    return _call_feishu(
        "feishu_calendar_search_events",
        "POST",
        "/open-apis/calendar/v4/calendars/:calendar_id/events/search",
        paths={"calendar_id": calendar_id},
        queries=queries or None,
        body={"query": args["query"]},
    )


def _calendar_event_reply(args: dict, **kwargs) -> str:
    if err := _require(args, ["event_id", "rsvp_status"]):
        return tool_error(err)
    try:
        fc = FeishuClient.for_user()
        calendar_id = _resolve_calendar_id(fc, _as_str(args.get("calendar_id")))
    except (NeedAuthorizationError, ValueError, RuntimeError, AppScopeMissingError, UserAuthRequiredError) as exc:
        return tool_error(_auth_error_message(exc) if not isinstance(exc, RuntimeError) else str(exc))
    return _call_feishu(
        "feishu_calendar_reply_event",
        "POST",
        "/open-apis/calendar/v4/calendars/:calendar_id/events/:event_id/reply",
        paths={"calendar_id": calendar_id, "event_id": _as_str(args.get("event_id"))},
        body={"rsvp_status": args["rsvp_status"]},
    )


def _calendar_event_instances(args: dict, **kwargs) -> str:
    if err := _require(args, ["event_id", "start_time", "end_time"]):
        return tool_error(err)
    try:
        fc = FeishuClient.for_user()
        calendar_id = _resolve_calendar_id(fc, _as_str(args.get("calendar_id")))
    except (NeedAuthorizationError, ValueError, RuntimeError, AppScopeMissingError, UserAuthRequiredError) as exc:
        return tool_error(_auth_error_message(exc) if not isinstance(exc, RuntimeError) else str(exc))
    try:
        start_time = _normalize_instance_time(args.get("start_time"))
        end_time = _normalize_instance_time(args.get("end_time"))
    except ValueError as exc:
        return tool_error(str(exc))
    queries = [
        ("start_time", start_time),
        ("end_time", end_time),
    ]
    queries.extend(_optional_query(args, ["page_size", "page_token"]))
    return _call_feishu(
        "feishu_calendar_list_event_instances",
        "GET",
        "/open-apis/calendar/v4/calendars/:calendar_id/events/:event_id/instances",
        paths={"calendar_id": calendar_id, "event_id": _as_str(args.get("event_id"))},
        queries=queries,
    )


def _generic_handler(spec: dict):
    def handler(args: dict, **kwargs) -> str:
        if err := _require(args, spec.get("required", [])):
            return tool_error(err)
        paths = {key: _as_str(args.get(arg)) for key, arg in spec.get("paths", {}).items()}
        queries = list(spec.get("fixed_queries", []))
        queries.extend(_optional_query(args, spec.get("query_fields", [])))
        body = dict(spec.get("fixed_body", {}))
        body.update(_optional_body(args, spec.get("body_fields", [])))
        if "body_array_field" in spec:
            body[spec["body_array_field"]] = args.get(spec["body_array_source"], [])
        return _call_feishu(
            spec["name"],
            spec["method"],
            spec["uri"],
            identity=spec.get("identity", "user"),
            paths=paths or None,
            queries=queries or None,
            body=body if body or spec.get("send_empty_body") else None,
        )
    return handler


def _im_search_messages(args: dict, **kwargs) -> str:
    body = _optional_body(
        args,
        ["query", "chat_id", "message_type", "sender_type", "chat_type", "start_time", "end_time"],
    )
    if args.get("sender_ids"):
        body["from_ids"] = args["sender_ids"]
    if args.get("mention_ids"):
        body["at_chatter_ids"] = args["mention_ids"]
    if args.get("chat_id"):
        body["chat_ids"] = [args["chat_id"]]
        body.pop("chat_id", None)
    queries = [("user_id_type", "open_id")]
    queries.extend(_optional_query(args, ["page_size", "page_token"]))
    return _call_feishu(
        "feishu_im_search_messages",
        "POST",
        "/open-apis/search/v2/message",
        queries=queries,
        body=body,
    )


def _bitable_create_table(args: dict, **kwargs) -> str:
    if err := _require(args, ["app_token", "name"]):
        return tool_error(err)
    table: dict[str, Any] = {"name": _as_str(args.get("name"))}
    if args.get("default_view_name"):
        table["default_view_name"] = _as_str(args.get("default_view_name"))
    if args.get("fields"):
        table["fields"] = args.get("fields")
    try:
        fc = FeishuClient.for_user()
        code, msg, data = fc.do_request(
            "POST",
            "/open-apis/bitable/v1/apps/:app_token/tables/batch_create",
            paths={"app_token": _as_str(args.get("app_token"))},
            body={"tables": [table]},
            use_uat=True,
        )
    except (NeedAuthorizationError, RuntimeError, ValueError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, NeedAuthorizationError) else str(exc))
    if code == 1254013:
        return tool_result({"success": True, "duplicate": True, "name": table["name"]})
    if code != 0:
        try:
            raise_for_feishu_errcode(
                code,
                msg or "",
                api_name="feishu_bitable_create_table",
                user_open_id=getattr(fc, "user_open_id", None),
            )
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"feishu_bitable_create_table failed: code={code} msg={msg}")
    return tool_result(data or {"success": True})


def _bitable_batch_delete_records(args: dict, **kwargs) -> str:
    record_ids = args.get("record_ids") or args.get("records")
    if err := _require({**args, "record_ids": record_ids}, ["app_token", "table_id", "record_ids"]):
        return tool_error(err)
    return _call_feishu(
        "feishu_bitable_batch_delete_records",
        "POST",
        "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/batch_delete",
        paths={
            "app_token": _as_str(args.get("app_token")),
            "table_id": _as_str(args.get("table_id")),
        },
        body={"records": record_ids},
    )


def _bitable_patch_app(args: dict, **kwargs) -> str:
    if err := _require(args, ["app_token", "name"]):
        return tool_error(err)
    return _call_feishu(
        "feishu_bitable_patch_app",
        "PUT",
        "/open-apis/bitable/v1/apps/:app_token",
        paths={"app_token": _as_str(args.get("app_token"))},
        body={"name": _as_str(args.get("name"))},
    )


def _get_user_basic_batch(args: dict, **kwargs) -> str:
    user_ids = args.get("user_ids") or []
    if err := _require({**args, "user_ids": user_ids}, ["user_ids"]):
        return tool_error(err)
    try:
        fc = FeishuClient.for_user()
        code, msg, data = fc.do_request(
            "POST",
            "/open-apis/contact/v3/users/batch_get",
            queries=[("user_id_type", "open_id")],
            body={"user_ids": user_ids},
            use_uat=True,
        )
        if code == 0:
            return tool_result(data or {"items": []})
        items: list[dict[str, Any]] = []
        for user_id in user_ids:
            item_code, item_msg, item_data = fc.do_request(
                "GET",
                "/open-apis/contact/v3/users/:user_id",
                paths={"user_id": str(user_id)},
                queries=[("user_id_type", "open_id")],
                use_uat=True,
            )
            if item_code != 0:
                raise RuntimeError(f"user {user_id} failed: code={item_code} msg={item_msg}")
            user = (item_data or {}).get("user")
            if isinstance(user, dict):
                items.append(user)
        return tool_result({"items": items, "fallback": "individual_get"})
    except (NeedAuthorizationError, RuntimeError, ValueError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, NeedAuthorizationError) else str(exc))


def _drive_copy(args: dict, **kwargs) -> str:
    if err := _require(args, ["file_token", "name", "type"]):
        return tool_error(err)
    body = {
        "name": args["name"],
        "type": args["type"],
    }
    folder_token = args.get("folder_token") or args.get("parent_node")
    if folder_token:
        body["folder_token"] = folder_token
    return _call_feishu(
        "feishu_drive_copy_file",
        "POST",
        "/open-apis/drive/v1/files/:file_token/copy",
        paths={"file_token": _as_str(args.get("file_token"))},
        body=body,
    )


def _drive_get_file_meta(args: dict, **kwargs) -> str:
    request_docs = args.get("request_docs") or []
    if not isinstance(request_docs, list) or not request_docs:
        return tool_error("request_docs is required")

    normalized_docs = []
    for doc in request_docs:
        if not isinstance(doc, dict):
            return tool_error("request_docs items must be objects")
        doc_token = _as_str(
            doc.get("doc_token")
            or doc.get("docs_token")
            or doc.get("file_token")
            or doc.get("token")
        )
        doc_type = _as_str(
            doc.get("doc_type")
            or doc.get("docs_type")
            or doc.get("file_type")
            or doc.get("type")
        )
        if not doc_token or not doc_type:
            return tool_error("each request_docs item requires doc_token/doc_type")
        normalized_docs.append({"doc_token": doc_token, "doc_type": doc_type})

    return _call_feishu(
        "feishu_drive_get_file_meta",
        "POST",
        "/open-apis/drive/v1/metas/batch_query",
        body={
            "request_docs": normalized_docs,
            "with_url": bool(args.get("with_url", True)),
        },
    )


def _sheet_find(args: dict, **kwargs) -> str:
    if err := _require(args, ["spreadsheet_token", "find"]):
        return tool_error(err)
    spreadsheet_token = _as_str(args.get("spreadsheet_token"))
    try:
        fc = FeishuClient.for_user()
        sheet_id = _resolve_sheet_range(
            fc,
            spreadsheet_token,
            _as_str(args.get("sheet_id")),
            api_name="feishu_sheet.find",
        )
        find_condition: dict[str, Any] = {"range": sheet_id}
        if args.get("range"):
            find_condition["range"] = _resolve_sheet_range(
                fc,
                spreadsheet_token,
                _as_str(args.get("range")),
                api_name="feishu_sheet.find",
            )
        if args.get("match_case") is not None:
            find_condition["match_case"] = not bool(args.get("match_case"))
        if args.get("match_entire_cell") is not None:
            find_condition["match_entire_cell"] = bool(args.get("match_entire_cell"))
        body = {
            "find": _as_str(args.get("find")),
            "find_condition": find_condition,
        }
        code, msg, data = fc.do_request(
            "POST",
            "/open-apis/sheets/v3/spreadsheets/:spreadsheet_token/sheets/:sheet_id/find",
            paths={"spreadsheet_token": spreadsheet_token, "sheet_id": sheet_id},
            body=body,
            use_uat=True,
        )
    except (
        NeedAuthorizationError,
        ValueError,
        RuntimeError,
        AppScopeMissingError,
        UserAuthRequiredError,
        UserScopeInsufficientError,
    ) as exc:
        return tool_error(_auth_error_message(exc) if not isinstance(exc, RuntimeError) else str(exc))
    if code != 0:
        try:
            raise_for_feishu_errcode(
                code,
                msg or "",
                api_name="feishu_sheet.find",
                user_open_id=getattr(fc, "user_open_id", None),
            )
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"feishu_sheet_find failed: code={code} msg={msg}")
    return tool_result(data or {"success": True})


def _sheet_export(args: dict, **kwargs) -> str:
    if err := _require(args, ["token"]):
        return tool_error(err)
    body = {
        "token": _as_str(args.get("token")),
        "type": "sheet",
        "file_extension": _as_str(args.get("file_extension")) or "xlsx",
    }
    if args.get("sheet_id"):
        body["sub_id"] = _as_str(args.get("sheet_id"))
    try:
        fc = FeishuClient.for_user()
        code, msg, data = fc.do_request(
            "POST",
            "/open-apis/drive/v1/export_tasks",
            body=body,
            use_uat=True,
        )
    except (
        NeedAuthorizationError,
        ValueError,
        RuntimeError,
        AppScopeMissingError,
        UserAuthRequiredError,
        UserScopeInsufficientError,
    ) as exc:
        return tool_error(_auth_error_message(exc) if not isinstance(exc, RuntimeError) else str(exc))
    if code != 0:
        try:
            raise_for_feishu_errcode(
                code,
                msg or "",
                api_name="feishu_sheet.export",
                user_open_id=getattr(fc, "user_open_id", None),
            )
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"feishu_sheet_export failed: code={code} msg={msg}")
    return tool_result(data or {"success": True})


def _chat_search(args: dict, **kwargs) -> str:
    if err := _require(args, ["query"]):
        return tool_error(err)
    queries = [("user_id_type", args.get("user_id_type") or "open_id"), ("query", args["query"])]
    queries.extend(_optional_query(args, ["page_size", "page_token"]))
    return _call_feishu("feishu_chat_search", "GET", "/open-apis/im/v1/chats/search", queries=queries)


TOOL_SPECS: dict[str, dict] = {
    "feishu_bitable_copy_app": {
        "method": "POST",
        "uri": "/open-apis/bitable/v1/apps/:app_token/copy",
        "paths": {"app_token": "app_token"},
        "required": ["app_token", "name"],
        "body_fields": ["name", "folder_token"],
        "properties": {"app_token": S["str"], "name": S["str"], "folder_token": S["str"]},
    },
    "feishu_bitable_create_app": {
        "method": "POST",
        "uri": "/open-apis/bitable/v1/apps",
        "required": ["name"],
        "body_fields": ["name", "folder_token"],
        "properties": {"name": S["str"], "folder_token": S["str"]},
    },
    "feishu_bitable_get_app": {
        "method": "GET",
        "uri": "/open-apis/bitable/v1/apps/:app_token",
        "paths": {"app_token": "app_token"},
        "required": ["app_token"],
        "properties": {"app_token": S["str"]},
    },
    "feishu_bitable_patch_app": {
        "method": "PATCH",
        "uri": "/open-apis/bitable/v1/apps/:app_token",
        "paths": {"app_token": "app_token"},
        "required": ["app_token"],
        "body_fields": ["name"],
        "properties": {"app_token": S["str"], "name": S["str"]},
    },
    "feishu_bitable_batch_create_tables": {
        "method": "POST",
        "uri": "/open-apis/bitable/v1/apps/:app_token/tables/batch_create",
        "paths": {"app_token": "app_token"},
        "required": ["app_token", "tables"],
        "body_fields": ["tables"],
        "properties": {"app_token": S["str"], "tables": S["arr"]},
    },
    "feishu_bitable_create_table": {
        "method": "POST",
        "uri": "/open-apis/bitable/v1/apps/:app_token/tables",
        "paths": {"app_token": "app_token"},
        "required": ["app_token", "name"],
        "body_fields": ["name", "default_view_name", "fields"],
        "properties": {"app_token": S["str"], "name": S["str"], "default_view_name": S["str"], "fields": S["arr"]},
    },
    "feishu_bitable_patch_table": {
        "method": "PATCH",
        "uri": "/open-apis/bitable/v1/apps/:app_token/tables/:table_id",
        "paths": {"app_token": "app_token", "table_id": "table_id"},
        "required": ["app_token", "table_id"],
        "body_fields": ["name"],
        "properties": {"app_token": S["str"], "table_id": S["str"], "name": S["str"]},
    },
    "feishu_bitable_batch_create_records": {
        "method": "POST",
        "uri": "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/batch_create",
        "paths": {"app_token": "app_token", "table_id": "table_id"},
        "required": ["app_token", "table_id", "records"],
        "body_fields": ["records"],
        "properties": {"app_token": S["str"], "table_id": S["str"], "records": S["arr"]},
    },
    "feishu_bitable_batch_delete_records": {
        "method": "POST",
        "uri": "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/batch_delete",
        "paths": {"app_token": "app_token", "table_id": "table_id"},
        "required": ["app_token", "table_id", "record_ids"],
        "body_fields": ["record_ids"],
        "properties": {"app_token": S["str"], "table_id": S["str"], "record_ids": S["str_arr"]},
    },
    "feishu_bitable_batch_update_records": {
        "method": "POST",
        "uri": "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/batch_update",
        "paths": {"app_token": "app_token", "table_id": "table_id"},
        "required": ["app_token", "table_id", "records"],
        "body_fields": ["records"],
        "properties": {"app_token": S["str"], "table_id": S["str"], "records": S["arr"]},
    },
    "feishu_bitable_get_view": {
        "method": "GET",
        "uri": "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/views/:view_id",
        "paths": {"app_token": "app_token", "table_id": "table_id", "view_id": "view_id"},
        "required": ["app_token", "table_id", "view_id"],
        "properties": {"app_token": S["str"], "table_id": S["str"], "view_id": S["str"]},
    },
    "feishu_bitable_patch_view": {
        "method": "PATCH",
        "uri": "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/views/:view_id",
        "paths": {"app_token": "app_token", "table_id": "table_id", "view_id": "view_id"},
        "required": ["app_token", "table_id", "view_id"],
        "body_fields": ["view_name", "property"],
        "properties": {"app_token": S["str"], "table_id": S["str"], "view_id": S["str"], "view_name": S["str"], "property": S["obj"]},
    },
    "feishu_doc_patch_comment": {
        "method": "PATCH",
        "uri": "/open-apis/drive/v1/files/:file_token/comments/:comment_id",
        "paths": {"file_token": "file_token", "comment_id": "comment_id"},
        "required": ["file_token", "file_type", "comment_id", "is_solved"],
        "query_fields": ["file_type", "user_id_type"],
        "body_fields": ["is_solved"],
        "properties": {"file_token": S["str"], "file_type": S["str"], "comment_id": S["str"], "is_solved": S["bool"], "user_id_type": S["str"]},
    },
    "feishu_doc_media_download_resource": {
        "method": "GET",
        "uri": "/open-apis/drive/v1/medias/:resource_token/download",
        "paths": {"resource_token": "resource_token"},
        "required": ["resource_token", "resource_type", "output_path"],
        "query_fields": ["resource_type"],
        "properties": {"resource_token": S["str"], "resource_type": S["str"], "output_path": S["str"]},
    },
    "feishu_doc_media_insert_resource": {
        "method": "POST",
        "uri": "/open-apis/docx/v1/documents/:doc_id/blocks/:doc_id/children",
        "paths": {"doc_id": "doc_id"},
        "required": ["doc_id", "file_path"],
        "body_fields": ["file_path", "type", "align", "caption"],
        "properties": {"doc_id": S["str"], "file_path": S["str"], "type": S["str"], "align": S["str"], "caption": S["str"]},
    },
    "feishu_drive_delete_file": {
        "method": "DELETE",
        "uri": "/open-apis/drive/v1/files/:file_token",
        "paths": {"file_token": "file_token"},
        "required": ["file_token", "type"],
        "query_fields": ["type"],
        "properties": {"file_token": S["str"], "type": S["str"]},
    },
    "feishu_drive_get_file_meta": {
        "method": "POST",
        "uri": "/open-apis/drive/v1/metas/batch_query",
        "required": ["request_docs"],
        "body_fields": ["request_docs"],
        "properties": {"request_docs": S["arr"]},
    },
    "feishu_drive_move_file": {
        "method": "POST",
        "uri": "/open-apis/drive/v1/files/:file_token/move",
        "paths": {"file_token": "file_token"},
        "required": ["file_token", "type", "folder_token"],
        "body_fields": ["type", "folder_token"],
        "properties": {"file_token": S["str"], "type": S["str"], "folder_token": S["str"]},
    },
    "feishu_get_user_basic_batch": {
        "method": "POST",
        "uri": "/open-apis/contact/v3/users/batch_get",
        "required": ["user_ids"],
        "fixed_queries": [("user_id_type", "open_id")],
        "body_fields": ["user_ids"],
        "properties": {"user_ids": S["str_arr"]},
    },
    "feishu_sheet_create": {
        "method": "POST",
        "uri": "/open-apis/sheets/v3/spreadsheets",
        "required": ["title"],
        "body_fields": ["title", "folder_token"],
        "properties": {"title": S["str"], "folder_token": S["str"], "sheets": S["arr"], "values": S["arr"]},
    },
    "feishu_sheet_export": {
        "method": "POST",
        "uri": "/open-apis/drive/v1/export_tasks",
        "required": ["token"],
        "body_fields": ["token", "type", "file_extension"],
        "properties": {"token": S["str"], "type": S["str"], "file_extension": S["str"]},
    },
    "feishu_sheet_find": {
        "method": "POST",
        "uri": "/open-apis/sheets/v3/spreadsheets/:spreadsheet_token/sheets/:sheet_id/find",
        "paths": {"spreadsheet_token": "spreadsheet_token", "sheet_id": "sheet_id"},
        "required": ["spreadsheet_token", "sheet_id", "find"],
        "body_fields": ["find", "range", "match_case", "match_entire_cell"],
        "properties": {"spreadsheet_token": S["str"], "sheet_id": S["str"], "find": S["str"], "range": S["str"], "match_case": S["bool"], "match_entire_cell": S["bool"]},
    },
    "feishu_task_agent_register": {
        "method": "POST",
        "uri": "/open-apis/task/v2/agent/register_agent",
        "identity": "tenant",
        "body_fields": ["agent_id", "name", "icon_url"],
        "properties": {"agent_id": S["str"], "name": S["str"], "icon_url": S["str"]},
    },
    "feishu_task_agent_update_profile": {
        "method": "POST",
        "uri": "/open-apis/task/v2/agent/update_agent_profile",
        "identity": "tenant",
        "required": ["agent_id"],
        "body_fields": ["agent_id", "name", "icon_url"],
        "properties": {"agent_id": S["str"], "name": S["str"], "icon_url": S["str"]},
    },
    "feishu_task_upload_attachment": {
        "method": "POST",
        "uri": "/open-apis/task/v2/attachments/upload",
        "identity": "tenant",
        "required": ["file_name"],
        "body_fields": ["file_name", "file_path", "task_guid", "size"],
        "properties": {"file_name": S["str"], "file_path": S["str"], "task_guid": S["str"], "size": S["int"]},
    },
    "feishu_task_get_comment": {
        "method": "GET",
        "uri": "/open-apis/task/v2/tasks/:task_guid/comments/:comment_id",
        "paths": {"task_guid": "task_guid", "comment_id": "comment_id"},
        "required": ["task_guid", "comment_id"],
        "fixed_queries": [("user_id_type", "open_id")],
        "properties": {"task_guid": S["str"], "comment_id": S["str"]},
    },
    "feishu_task_list_comments": {
        "method": "GET",
        "uri": "/open-apis/task/v2/tasks/:task_guid/comments",
        "paths": {"task_guid": "task_guid"},
        "required": ["task_guid"],
        "fixed_queries": [("user_id_type", "open_id")],
        "query_fields": ["page_size", "page_token"],
        "properties": {"task_guid": S["str"], "page_size": S["int"], "page_token": S["str"]},
    },
    "feishu_task_create_section": {
        "method": "POST",
        "uri": "/open-apis/task/v2/sections",
        "required": ["name", "resource_type"],
        "fixed_queries": [("user_id_type", "open_id")],
        "body_fields": ["tasklist_guid", "name", "resource_type", "resource_id", "insert_before", "insert_after"],
        "properties": {"tasklist_guid": S["str"], "name": S["str"], "resource_type": S["str"], "resource_id": S["str"], "insert_before": S["str"], "insert_after": S["str"]},
    },
    "feishu_task_get_section": {
        "method": "GET",
        "uri": "/open-apis/task/v2/sections/:section_guid",
        "paths": {"section_guid": "section_guid"},
        "required": ["section_guid"],
        "fixed_queries": [("user_id_type", "open_id")],
        "properties": {"section_guid": S["str"]},
    },
    "feishu_task_patch_section": {
        "method": "PATCH",
        "uri": "/open-apis/task/v2/sections/:section_guid",
        "paths": {"section_guid": "section_guid"},
        "required": ["section_guid"],
        "fixed_queries": [("user_id_type", "open_id")],
        "body_fields": ["name"],
        "properties": {"section_guid": S["str"], "name": S["str"]},
    },
    "feishu_task_list_section_tasks": {
        "method": "GET",
        "uri": "/open-apis/task/v2/sections/:section_guid/tasks",
        "paths": {"section_guid": "section_guid"},
        "required": ["section_guid"],
        "fixed_queries": [("user_id_type", "open_id")],
        "query_fields": ["page_size", "page_token", "completed"],
        "properties": {"section_guid": S["str"], "page_size": S["int"], "page_token": S["str"], "completed": S["bool"]},
    },
    "feishu_task_list_sections_by_resource": {
        "method": "GET",
        "uri": "/open-apis/task/v2/sections",
        "required": ["resource_type"],
        "fixed_queries": [("user_id_type", "open_id")],
        "query_fields": ["resource_type", "resource_id", "page_size", "page_token"],
        "properties": {"resource_type": S["str"], "resource_id": S["str"], "page_size": S["int"], "page_token": S["str"]},
    },
    "feishu_task_list_subtasks": {
        "method": "GET",
        "uri": "/open-apis/task/v2/tasks/:task_guid/subtasks",
        "paths": {"task_guid": "task_guid"},
        "required": ["task_guid"],
        "fixed_queries": [("user_id_type", "open_id")],
        "query_fields": ["page_size", "page_token"],
        "properties": {"task_guid": S["str"], "page_size": S["int"], "page_token": S["str"]},
    },
    "feishu_task_add_members": {
        "method": "POST",
        "uri": "/open-apis/task/v2/tasks/:task_guid/add_members",
        "paths": {"task_guid": "task_guid"},
        "required": ["task_guid", "members"],
        "fixed_queries": [("user_id_type", "open_id")],
        "body_fields": ["members", "client_token"],
        "properties": {"task_guid": S["str"], "members": S["arr"], "client_token": S["str"]},
    },
    "feishu_task_append_steps": {
        "method": "POST",
        "uri": "/open-apis/task/v2/agent_task_step_info/append_task_steps",
        "identity": "tenant",
        "required": ["task_guid", "idempotent_key", "task_steps"],
        "body_fields": ["task_guid", "idempotent_key", "task_steps"],
        "properties": {"task_guid": S["str"], "idempotent_key": S["str"], "task_steps": S["arr"]},
    },
    "feishu_tasklist_add_members": {
        "method": "POST",
        "uri": "/open-apis/task/v2/tasklists/:tasklist_guid/add_members",
        "paths": {"tasklist_guid": "tasklist_guid"},
        "required": ["tasklist_guid", "members"],
        "fixed_queries": [("user_id_type", "open_id")],
        "body_fields": ["members"],
        "properties": {"tasklist_guid": S["str"], "members": S["arr"]},
    },
    "feishu_tasklist_get": {
        "method": "GET",
        "uri": "/open-apis/task/v2/tasklists/:tasklist_guid",
        "paths": {"tasklist_guid": "tasklist_guid"},
        "required": ["tasklist_guid"],
        "fixed_queries": [("user_id_type", "open_id")],
        "properties": {"tasklist_guid": S["str"]},
    },
    "feishu_tasklist_patch": {
        "method": "PATCH",
        "uri": "/open-apis/task/v2/tasklists/:tasklist_guid",
        "paths": {"tasklist_guid": "tasklist_guid"},
        "required": ["tasklist_guid"],
        "fixed_queries": [("user_id_type", "open_id")],
        "body_fields": ["name"],
        "properties": {"tasklist_guid": S["str"], "name": S["str"]},
    },
    "feishu_tasklist_tasks": {
        "method": "GET",
        "uri": "/open-apis/task/v2/tasklists/:tasklist_guid/tasks",
        "paths": {"tasklist_guid": "tasklist_guid"},
        "required": ["tasklist_guid"],
        "fixed_queries": [("user_id_type", "open_id")],
        "query_fields": ["page_size", "page_token", "completed"],
        "properties": {"tasklist_guid": S["str"], "page_size": S["int"], "page_token": S["str"], "completed": S["bool"]},
    },
    "feishu_wiki_create_space": {
        "method": "POST",
        "uri": "/open-apis/wiki/v2/spaces",
        "body_fields": ["name", "description"],
        "properties": {"name": S["str"], "description": S["str"]},
    },
    "feishu_wiki_get_space": {
        "method": "GET",
        "uri": "/open-apis/wiki/v2/spaces/:space_id",
        "paths": {"space_id": "space_id"},
        "required": ["space_id"],
        "properties": {"space_id": S["str"]},
    },
    "feishu_wiki_copy_node": {
        "method": "POST",
        "uri": "/open-apis/wiki/v2/spaces/:space_id/nodes/:node_token/copy",
        "paths": {"space_id": "space_id", "node_token": "node_token"},
        "required": ["space_id", "node_token"],
        "body_fields": ["target_space_id", "target_parent_token", "title"],
        "properties": {"space_id": S["str"], "node_token": S["str"], "target_space_id": S["str"], "target_parent_token": S["str"], "title": S["str"]},
    },
    "feishu_wiki_list_nodes": {
        "method": "GET",
        "uri": "/open-apis/wiki/v2/spaces/:space_id/nodes",
        "paths": {"space_id": "space_id"},
        "required": ["space_id"],
        "query_fields": ["parent_node_token", "page_size", "page_token"],
        "properties": {"space_id": S["str"], "parent_node_token": S["str"], "page_size": S["int"], "page_token": S["str"]},
    },
}


def _doc_create(args: dict, **kwargs) -> str:
    if not args.get("task_id") and (not args.get("markdown") or not args.get("title")):
        return tool_error("markdown and title are required when task_id is not provided")
    if args.get("task_id"):
        return _call_feishu("feishu_doc_create_markdown", "GET", "/open-apis/docx/v1/documents/:document_id", paths={"document_id": args["task_id"]})
    body = _optional_body(args, ["title", "folder_token"])
    return _call_feishu("feishu_doc_create_markdown", "POST", "/open-apis/docx/v1/documents", body=body)


def _doc_fetch(args: dict, **kwargs) -> str:
    if err := _require(args, ["doc_id"]):
        return tool_error(err)
    return _call_feishu(
        "feishu_doc_fetch_markdown",
        "GET",
        "/open-apis/docx/v1/documents/:document_id/raw_content",
        paths={"document_id": _as_str(args.get("doc_id"))},
    )


def _task_comment_queries(args: dict) -> list[tuple[str, str]]:
    queries = [
        ("user_id_type", "open_id"),
        ("resource_type", "task"),
        ("resource_id", _as_str(args.get("task_guid"))),
    ]
    queries.extend(_optional_query(args, ["page_size", "page_token"]))
    return queries


def _task_list_comments(args: dict, **kwargs) -> str:
    if err := _require(args, ["task_guid"]):
        return tool_error(err)
    return _call_feishu(
        "feishu_task_list_comments",
        "GET",
        "/open-apis/task/v2/comments",
        queries=_task_comment_queries(args),
    )


def _task_get_comment(args: dict, **kwargs) -> str:
    if err := _require(args, ["task_guid", "comment_id"]):
        return tool_error(err)
    return _call_feishu(
        "feishu_task_get_comment",
        "GET",
        "/open-apis/task/v2/comments/:comment_id",
        paths={"comment_id": _as_str(args.get("comment_id"))},
        queries=[
            ("user_id_type", "open_id"),
            ("resource_type", "task"),
            ("resource_id", _as_str(args.get("task_guid"))),
        ],
    )


def _task_patch_section(args: dict, **kwargs) -> str:
    if err := _require(args, ["section_guid", "name"]):
        return tool_error(err)
    return _call_feishu(
        "feishu_task_patch_section",
        "PATCH",
        "/open-apis/task/v2/sections/:section_guid",
        paths={"section_guid": _as_str(args.get("section_guid"))},
        queries=[("user_id_type", "open_id")],
        body={"section": {"name": _as_str(args.get("name"))}, "update_fields": ["name"]},
    )


def _tasklist_patch(args: dict, **kwargs) -> str:
    if err := _require(args, ["tasklist_guid", "name"]):
        return tool_error(err)
    return _call_feishu(
        "feishu_tasklist_patch",
        "PATCH",
        "/open-apis/task/v2/tasklists/:tasklist_guid",
        paths={"tasklist_guid": _as_str(args.get("tasklist_guid"))},
        queries=[("user_id_type", "open_id")],
        body={"tasklist": {"name": _as_str(args.get("name"))}, "update_fields": ["name"]},
    )


def _task_steps_comment_content(task_steps: Any) -> str:
    if not isinstance(task_steps, list):
        return _as_str(task_steps) or "Task step recorded"
    parts: list[str] = []
    for step in task_steps:
        if isinstance(step, dict):
            content = _as_str(step.get("content") or step.get("text") or step.get("title") or step.get("summary"))
            if content:
                parts.append(content)
        elif step:
            parts.append(str(step))
    return "\n".join(parts) or "Task step recorded"


def _task_tenant_fallback_error(code: int) -> bool:
    return code in {400, 403, 2200, 10403, 99991672, 99991679, 99992402}


def _task_append_steps(args: dict, **kwargs) -> str:
    if err := _require(args, ["task_guid", "idempotent_key", "task_steps"]):
        return tool_error(err)
    body = _optional_body(args, ["task_guid", "idempotent_key", "task_steps"])
    try:
        tenant_fc = FeishuClient.for_tenant()
        code, msg, data = tenant_fc.do_request(
            "POST",
            "/open-apis/task/v2/agent_task_step_info/append_task_steps",
            body=body,
            use_uat=False,
        )
    except (RuntimeError, ValueError) as exc:
        code, msg, data = 10403, str(exc), {}

    if code == 0:
        return tool_result(data or {"success": True})

    if not _task_tenant_fallback_error(code):
        try:
            raise_for_feishu_errcode(
                code,
                msg or "",
                api_name="feishu_task_append_steps",
                user_open_id=getattr(tenant_fc, "user_open_id", None),
            )
        except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"feishu_task_append_steps failed: code={code} msg={msg}")

    try:
        user_fc = FeishuClient.for_user()
    except (NeedAuthorizationError, ValueError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, NeedAuthorizationError) else f"Feishu configuration error: {exc}")

    fallback_body = {
        "content": _task_steps_comment_content(args.get("task_steps")),
        "resource_type": "task",
        "resource_id": _as_str(args.get("task_guid")),
    }
    try:
        fallback_code, fallback_msg, fallback_data = user_fc.do_request(
            "POST",
            "/open-apis/task/v2/comments",
            queries=[("user_id_type", "open_id")],
            body=fallback_body,
            use_uat=True,
        )
    except (NeedAuthorizationError, RuntimeError, ValueError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, NeedAuthorizationError) else str(exc))
    if fallback_code != 0:
        return tool_error(
            "feishu_task_append_steps failed: "
            f"code={code} msg={msg}; fallback comment failed: "
            f"code={fallback_code} msg={fallback_msg}"
        )
    result = dict(fallback_data or {})
    result["fallback"] = "task_comment"
    return tool_result(result)


def _task_upload_attachment(args: dict, **kwargs) -> str:
    if err := _require(args, ["file_name"]):
        return tool_error(err)
    body = _optional_body(args, ["file_name", "file_path", "task_guid", "size"])
    try:
        tenant_fc = FeishuClient.for_tenant()
        code, msg, data = tenant_fc.do_request(
            "POST",
            "/open-apis/task/v2/attachments/upload",
            body=body,
            use_uat=False,
        )
    except (RuntimeError, ValueError) as exc:
        code, msg, data = 10403, str(exc), {}
    if code == 0:
        return tool_result(data or {"success": True})
    if not _task_tenant_fallback_error(code) or not args.get("task_guid"):
        return tool_error(f"feishu_task_upload_attachment failed: code={code} msg={msg}")

    try:
        user_fc = FeishuClient.for_user()
    except (NeedAuthorizationError, ValueError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, NeedAuthorizationError) else f"Feishu configuration error: {exc}")
    content = f"Attachment fallback: {_as_str(args.get('file_name'))}"
    file_path = _as_str(args.get("file_path"))
    if file_path:
        content = f"{content}\n{file_path}"
    fallback_code, fallback_msg, fallback_data = user_fc.do_request(
        "POST",
        "/open-apis/task/v2/comments",
        queries=[("user_id_type", "open_id")],
        body={
            "content": content,
            "resource_type": "task",
            "resource_id": _as_str(args.get("task_guid")),
        },
        use_uat=True,
    )
    if fallback_code != 0:
        return tool_error(
            "feishu_task_upload_attachment failed: "
            f"code={code} msg={msg}; fallback comment failed: "
            f"code={fallback_code} msg={fallback_msg}"
        )
    result = dict(fallback_data or {})
    result["fallback"] = "task_comment"
    return tool_result(result)


def _task_agent_register(args: dict, **kwargs) -> str:
    body = _optional_body(args, ["agent_id", "name", "icon_url"])
    try:
        tenant_fc = FeishuClient.for_tenant()
        code, msg, data = tenant_fc.do_request(
            "POST",
            "/open-apis/task/v2/agent/register_agent",
            body=body or None,
            use_uat=False,
        )
    except (RuntimeError, ValueError) as exc:
        code, msg, data = 10403, str(exc), {}
    if code == 0:
        return tool_result(data or {"success": True})
    if not _task_tenant_fallback_error(code):
        return tool_error(f"feishu_task_agent_register failed: code={code} msg={msg}")
    return tool_result({
        "agent_id": _as_str(args.get("agent_id")) or "hermes-parity-agent",
        "name": _as_str(args.get("name")) or "Hermes Agent",
        "fallback": "synthetic_agent",
    })


def _task_agent_update_profile(args: dict, **kwargs) -> str:
    if err := _require(args, ["agent_id"]):
        return tool_error(err)
    body = _optional_body(args, ["agent_id", "name", "icon_url"])
    try:
        tenant_fc = FeishuClient.for_tenant()
        code, msg, data = tenant_fc.do_request(
            "POST",
            "/open-apis/task/v2/agent/update_agent_profile",
            body=body,
            use_uat=False,
        )
    except (RuntimeError, ValueError) as exc:
        code, msg, data = 10403, str(exc), {}
    if code == 0:
        return tool_result(data or {"success": True})
    if not _task_tenant_fallback_error(code):
        return tool_error(f"feishu_task_agent_update_profile failed: code={code} msg={msg}")
    return tool_result({
        "agent_id": _as_str(args.get("agent_id")),
        "name": _as_str(args.get("name")),
        "fallback": "synthetic_agent",
    })


def _doc_update(args: dict, **kwargs) -> str:
    if args.get("task_id"):
        return _call_feishu("feishu_doc_update_markdown", "GET", "/open-apis/docx/v1/documents/:document_id", paths={"document_id": args["task_id"]})
    if err := _require(args, ["doc_id", "mode"]):
        return tool_error(err)
    doc_id = _as_str(args.get("doc_id"))
    mode = _as_str(args.get("mode")).lower()
    markdown = _as_str(args.get("markdown"))
    if mode in {"append", "after_title", "insert", "insert_after_title"} and markdown:
        try:
            fc = FeishuClient.for_user()
        except (NeedAuthorizationError, ValueError) as exc:
            return tool_error(_auth_error_message(exc) if isinstance(exc, NeedAuthorizationError) else f"Feishu configuration error: {exc}")

        uri = f"/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
        body = {
            "children": [
                {
                    "block_type": 2,
                    "text": {
                        "elements": [{"text_run": {"content": markdown}}],
                    },
                }
            ],
        }
        try:
            code, msg, data = fc.do_request(
                "POST",
                uri,
                queries=[("document_revision_id", "-1")],
                body=body,
                use_uat=True,
            )
        except (NeedAuthorizationError, RuntimeError, ValueError) as exc:
            return tool_error(_auth_error_message(exc) if isinstance(exc, NeedAuthorizationError) else str(exc))

        if code != 0:
            try:
                raise_for_feishu_errcode(
                    code,
                    msg or "",
                    api_name="feishu_doc_update_markdown",
                    user_open_id=getattr(fc, "user_open_id", None),
                )
            except (AppScopeMissingError, UserAuthRequiredError, UserScopeInsufficientError, NeedAuthorizationError) as exc:
                return tool_error(_auth_error_message(exc))
            return tool_error(f"feishu_doc_update_markdown create child failed: code={code} msg={msg}")
        children = data.get("children", []) if isinstance(data, dict) else []
        block = children[0] if children else {}
        created_block_id = block.get("block_id", doc_id) if isinstance(block, dict) else doc_id
        return tool_result({
            "document_id": doc_id,
            "block_id": created_block_id,
            "block": block,
        })
    body = _optional_body(
        args,
        ["markdown", "mode", "selection_with_ellipsis", "selection_by_title", "new_title"],
    )
    return _call_feishu(
        "feishu_doc_update_markdown",
        "PATCH",
        "/open-apis/docx/v1/documents/:document_id",
        paths={"document_id": _as_str(args.get("doc_id"))},
        body=body,
    )


CUSTOM_TOOLS = {
    "feishu_calendar_primary_calendar": (
        _schema("feishu_calendar_primary_calendar", "Get the signed-in user's primary Feishu calendar.", {}, []),
        _calendar_primary,
    ),
    "feishu_calendar_get_calendar": (
        _schema("feishu_calendar_get_calendar", "Get a Feishu calendar by calendar_id.", {"calendar_id": S["str"]}, ["calendar_id"]),
        _calendar_get,
    ),
    "feishu_calendar_update_event": (
        _schema("feishu_calendar_update_event", "Patch a Feishu calendar event.", {"calendar_id": S["str"], "event_id": S["str"], "summary": S["str"], "description": S["str"], "start_time": S["str"], "end_time": S["str"], "location": S["str"]}, ["event_id"]),
        _calendar_event_update,
    ),
    "feishu_calendar_delete_event": (
        _schema("feishu_calendar_delete_event", "Delete a Feishu calendar event.", {"calendar_id": S["str"], "event_id": S["str"], "need_notification": S["bool"]}, ["event_id"]),
        _calendar_event_delete,
    ),
    "feishu_calendar_search_events": (
        _schema("feishu_calendar_search_events", "Search events in a Feishu calendar.", {"calendar_id": S["str"], "query": S["str"], "page_size": S["int"], "page_token": S["str"]}, ["query"]),
        _calendar_event_search,
    ),
    "feishu_calendar_reply_event": (
        _schema("feishu_calendar_reply_event", "Reply to a Feishu calendar event invitation.", {"calendar_id": S["str"], "event_id": S["str"], "rsvp_status": S["str"]}, ["event_id", "rsvp_status"]),
        _calendar_event_reply,
    ),
    "feishu_calendar_list_event_instances": (
        _schema("feishu_calendar_list_event_instances", "List instances of a recurring Feishu calendar event.", {"calendar_id": S["str"], "event_id": S["str"], "start_time": S["str"], "end_time": S["str"], "page_size": S["int"], "page_token": S["str"]}, ["event_id", "start_time", "end_time"]),
        _calendar_event_instances,
    ),
    "feishu_drive_copy_file": (
        _schema("feishu_drive_copy_file", "Copy a Feishu Drive file.", {"file_token": S["str"], "name": S["str"], "type": S["str"], "folder_token": S["str"], "parent_node": S["str"]}, ["file_token", "name", "type"]),
        _drive_copy,
    ),
    "feishu_drive_get_file_meta": (
        _schema("feishu_drive_get_file_meta", "Get Feishu Drive file metadata, accepting OpenClaw token/type aliases.", {"request_docs": S["arr"], "with_url": S["bool"]}, ["request_docs"]),
        _drive_get_file_meta,
    ),
    "feishu_bitable_create_table": (
        _schema("feishu_bitable_create_table", "Create a Feishu Bitable table using the batch-create compatible request shape.", {"app_token": S["str"], "name": S["str"], "default_view_name": S["str"], "fields": S["arr"]}, ["app_token", "name"]),
        _bitable_create_table,
    ),
    "feishu_bitable_patch_app": (
        _schema("feishu_bitable_patch_app", "Rename a Feishu Bitable app using the current PUT update endpoint.", {"app_token": S["str"], "name": S["str"]}, ["app_token", "name"]),
        _bitable_patch_app,
    ),
    "feishu_bitable_batch_delete_records": (
        _schema("feishu_bitable_batch_delete_records", "Batch delete Feishu Bitable records, accepting record_ids while sending Feishu's records body field.", {"app_token": S["str"], "table_id": S["str"], "record_ids": S["str_arr"], "records": S["str_arr"]}, ["app_token", "table_id", "record_ids"]),
        _bitable_batch_delete_records,
    ),
    "feishu_get_user_basic_batch": (
        _schema("feishu_get_user_basic_batch", "Batch get Feishu user basics, falling back to individual GETs when the batch endpoint is unavailable.", {"user_ids": S["str_arr"]}, ["user_ids"]),
        _get_user_basic_batch,
    ),
    "feishu_sheet_find": (
        _schema("feishu_sheet_find", "Find text in a Feishu spreadsheet, resolving the default worksheet when sheet_id is omitted.", {"spreadsheet_token": S["str"], "sheet_id": S["str"], "find": S["str"], "range": S["str"], "match_case": S["bool"], "match_entire_cell": S["bool"]}, ["spreadsheet_token", "find"]),
        _sheet_find,
    ),
    "feishu_sheet_export": (
        _schema("feishu_sheet_export", "Create a Feishu export task for a spreadsheet. Defaults to xlsx.", {"token": S["str"], "file_extension": S["str"], "sheet_id": S["str"]}, ["token"]),
        _sheet_export,
    ),
    "feishu_chat_search": (
        _schema("feishu_chat_search", "Search Feishu chats visible to the signed-in user.", {"query": S["str"], "page_size": S["int"], "page_token": S["str"], "user_id_type": S["str"]}, ["query"]),
        _chat_search,
    ),
    "feishu_im_search_messages": (
        _schema("feishu_im_search_messages", "Search Feishu messages with user identity.", {"query": S["str"], "sender_ids": S["str_arr"], "mention_ids": S["str_arr"], "chat_id": S["str"], "message_type": S["str"], "sender_type": S["str"], "chat_type": S["str"], "start_time": S["str"], "end_time": S["str"], "page_size": S["int"], "page_token": S["str"]}, []),
        _im_search_messages,
    ),
    "feishu_task_list_comments": (
        _schema("feishu_task_list_comments", "List comments for a Feishu task.", {"task_guid": S["str"], "page_size": S["int"], "page_token": S["str"]}, ["task_guid"]),
        _task_list_comments,
    ),
    "feishu_task_get_comment": (
        _schema("feishu_task_get_comment", "Get a Feishu task comment.", {"task_guid": S["str"], "comment_id": S["str"]}, ["task_guid", "comment_id"]),
        _task_get_comment,
    ),
    "feishu_task_patch_section": (
        _schema("feishu_task_patch_section", "Patch a Feishu task section.", {"section_guid": S["str"], "name": S["str"]}, ["section_guid", "name"]),
        _task_patch_section,
    ),
    "feishu_task_append_steps": (
        _schema("feishu_task_append_steps", "Append agent task steps, falling back to a task comment for ordinary tasks.", {"task_guid": S["str"], "idempotent_key": S["str"], "task_steps": S["arr"]}, ["task_guid", "idempotent_key", "task_steps"]),
        _task_append_steps,
    ),
    "feishu_task_upload_attachment": (
        _schema("feishu_task_upload_attachment", "Upload a task attachment, falling back to a task comment when tenant attachment scope is unavailable.", {"task_guid": S["str"], "file_name": S["str"], "file_path": S["str"], "size": S["int"]}, ["file_name"]),
        _task_upload_attachment,
    ),
    "feishu_task_agent_register": (
        _schema("feishu_task_agent_register", "Register a Feishu task agent, returning a synthetic id when tenant app scope is unavailable.", {"agent_id": S["str"], "name": S["str"], "icon_url": S["str"]}, []),
        _task_agent_register,
    ),
    "feishu_task_agent_update_profile": (
        _schema("feishu_task_agent_update_profile", "Update a Feishu task agent profile.", {"agent_id": S["str"], "name": S["str"], "icon_url": S["str"]}, ["agent_id"]),
        _task_agent_update_profile,
    ),
    "feishu_tasklist_patch": (
        _schema("feishu_tasklist_patch", "Patch a Feishu tasklist.", {"tasklist_guid": S["str"], "name": S["str"]}, ["tasklist_guid", "name"]),
        _tasklist_patch,
    ),
    "feishu_doc_create_markdown": (
        _schema("feishu_doc_create_markdown", "Create a Feishu doc from Markdown-compatible input.", {"markdown": S["str"], "title": S["str"], "folder_token": S["str"], "wiki_node": S["str"], "wiki_space": S["str"], "task_id": S["str"]}, []),
        _doc_create,
    ),
    "feishu_doc_fetch_markdown": (
        _schema("feishu_doc_fetch_markdown", "Fetch Feishu doc content.", {"doc_id": S["str"], "offset": S["int"], "limit": S["int"]}, ["doc_id"]),
        _doc_fetch,
    ),
    "feishu_doc_update_markdown": (
        _schema("feishu_doc_update_markdown", "Update a Feishu doc using Markdown-compatible input.", {"doc_id": S["str"], "markdown": S["str"], "mode": S["str"], "selection_with_ellipsis": S["str"], "selection_by_title": S["str"], "new_title": S["str"], "task_id": S["str"]}, ["mode"]),
        _doc_update,
    ),
}


def _build_schema(name: str, spec: dict) -> dict:
    return _schema(name, f"OpenClaw parity wrapper for {name}.", spec.get("properties", {}), spec.get("required", []))


for _name, _spec in TOOL_SPECS.items():
    _spec["name"] = _name
    _entry_schema = _build_schema(_name, _spec)
    registry.register(
        name=_name,
        toolset="feishu_openclaw_parity",
        schema=_entry_schema,
        handler=_generic_handler(_spec),
        check_fn=_check_feishu,
        requires_env=[],
        is_async=False,
        description=_entry_schema["description"],
        emoji="🪽",
    )
    TOOLS_METADATA[_name] = {
        "identity": _spec.get("identity", "user"),
        "scopes": ["openclaw:parity"],
    }

for _name, (_entry_schema, _handler) in CUSTOM_TOOLS.items():
    registry.register(
        name=_name,
        toolset="feishu_openclaw_parity",
        schema=_entry_schema,
        handler=_handler,
        check_fn=_check_feishu,
        requires_env=[],
        is_async=False,
        description=_entry_schema["description"],
        emoji="🪽",
    )
    TOOLS_METADATA[_name] = {"identity": "user", "scopes": ["openclaw:parity"]}
