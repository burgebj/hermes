"""US-008: friendly scope-error formatting for the Feishu chat user.

When a UAT tool call hits errcode 99991672 (app scope missing) or 99991679
(user scope insufficient), the gateway can call :func:`format_scope_error`
to turn the raised exception into a human-readable Chinese reply that
includes the missing scopes (with friendly labels) and a re-authorization
hint.

The full interactive-card "[重新授权]" button + click → /feishu_auth flow is
deferred to a later commit (it requires hooking the card_action route to
re-emit a synthetic /feishu_auth COMMAND with the merged scope set; that
plumbing is non-trivial and orthogonal to the mapping itself). The text
reply already tells the user the exact ``/feishu_auth scope1 scope2`` line
to paste, which is functionally equivalent.
"""

from __future__ import annotations

from typing import Iterable

from tools.feishu_oapi_client import (
    AppScopeMissingError,
    UserAuthRequiredError,
    UserScopeInsufficientError,
)


# Mapping from Feishu OAuth scope identifiers to human-friendly Chinese
# labels. Used in the gateway reply when a tool call fails because the
# requesting user has not granted the required scope.
SCOPE_LABELS: dict[str, str] = {
    "calendar:calendar": "日历(读写)",
    "calendar:calendar:readonly": "日历(只读)",
    "calendar:freebusy:readonly": "忙闲查询",
    "drive:drive": "云盘(读写)",
    "drive:drive:readonly": "云盘(只读)",
    "drive:export:readonly": "云盘导出(只读)",
    "docs:document": "文档(读写)",
    "docs:document:readonly": "文档(只读)",
    "docs:document.comment:create": "文档评论(创建)",
    "docs:document.comment:write_only": "文档评论(仅写入)",
    "bitable:app": "多维表",
    "wiki:wiki": "知识库(读写)",
    "wiki:wiki:readonly": "知识库(只读)",
    "sheets:spreadsheet": "电子表格(读写)",
    "sheets:spreadsheet:readonly": "电子表格(只读)",
    "task:task:write": "任务(读写)",
    "task:task:read": "任务(只读)",
    "task:section:write": "任务分组(读写)",
    "task:section:read": "任务分组(只读)",
    "task:comment:write": "任务评论(写入)",
    "task:comment:writeonly": "任务评论(仅写入)",
    "im:message.send_as_user": "用用户身份发消息",
    "im:chat:readonly": "群聊(只读)",
    "im:resource": "IM 资源",
    "search:search": "全局搜索",
    "search:message": "消息搜索",
    "authen:user.employee_id:read": "员工 ID(只读)",
    "contact:user.base:readonly": "通讯录(基本)",
}


def label_for_scope(scope: str) -> str:
    """Return the friendly Chinese label for a scope, falling back to the raw id."""
    if not scope:
        return "(未知权限)"
    return SCOPE_LABELS.get(scope.strip(), scope.strip())


def labels_for_scopes(scopes: Iterable[str]) -> list[str]:
    """Return labels for an iterable of scopes, preserving order, deduped."""
    seen: set[str] = set()
    out: list[str] = []
    for s in scopes:
        s2 = (s or "").strip()
        if not s2 or s2 in seen:
            continue
        seen.add(s2)
        out.append(label_for_scope(s2))
    return out


def build_auth_pending_card(
    verification_uri: str,
    user_code: str,
    expires_in_s: int,
    scope: str = "",
) -> dict:
    """Pending-state card: blue header, button to verification URL, fallback link.

    Mirrors openclaw-lark oauth-card.js buildAuthCard (zh_cn). Sent as the
    first message of the chat-driven device flow; the same message is later
    PATCHed in place to success/error via :func:`build_auth_success_card` /
    :func:`build_auth_error_card`.
    """
    minutes = max(expires_in_s // 60, 1)
    elements = [
        {"tag": "markdown", "content": "**请点击下方按钮完成授权**"},
        {"tag": "markdown", "content": f"🕐 授权请求将在 {minutes} 分钟内过期"},
    ]
    if scope:
        elements.append({"tag": "markdown", "content": f"📋 请求权限: {scope}"})
    elements.extend([
        {"tag": "hr"},
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "打开授权链接"},
                    "type": "primary",
                    "url": verification_uri,
                },
            ],
        },
        {
            "tag": "markdown",
            "content": f"<font color=\"grey\">如果按钮不可用,请打开 {verification_uri} 并输入用户码 {user_code}</font>",
        },
    ])
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "🔐 飞书授权请求"},
            "template": "blue",
        },
        "elements": elements,
    }


def build_auth_success_card(open_id: str, scope: str) -> dict:
    """Success-state card: green header, scope summary, encrypted-storage hint.

    Used to PATCH the pending card in place after a successful token exchange.
    """
    scope_count = len([s for s in scope.split() if s]) if scope else 0
    body = (
        f"已成功授予 {scope_count} 项用户权限"
        if scope_count
        else "授权完成"
    )
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "✅ 飞书授权成功"},
            "template": "green",
        },
        "elements": [
            {"tag": "markdown", "content": f"**{body}**"},
            {"tag": "markdown", "content": f"<font color=\"grey\">用户 ID: {open_id}</font>"},
            {
                "tag": "markdown",
                "content": "<font color=\"grey\">凭据已加密保存,下次直接使用,无需重复授权。</font>",
            },
        ],
    }


def build_auth_error_card(reason: str, scope: str = "") -> dict:
    """Error-state card: red header, truncated reason, retry hint with re-auth button."""
    button_value: dict = {"hermes_action": "feishu_auth"}
    if scope:
        button_value["scope"] = scope
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "❌ 飞书授权失败"},
            "template": "red",
        },
        "elements": [
            {"tag": "markdown", "content": f"**失败原因: {reason[:200]}**"},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "🔄 重试授权"},
                        "type": "primary",
                        "value": button_value,
                    },
                ],
            },
        ],
    }


def build_feishu_auth_card(
    body_text: str,
    button_label: str = "🔐 立即授权",
    scope: str = "",
) -> dict:
    """Build a Feishu interactive card whose primary button triggers /feishu_auth.

    The button payload carries ``hermes_action == "feishu_auth"`` plus the
    optional ``scope`` string. The gateway adapter's
    ``_handle_feishu_auth_card_action`` dispatches the click as a synthetic
    ``/feishu_auth [scope]`` COMMAND on behalf of the clicker, closing the
    last manual step in the onboarding / scope-manager UX flows.

    Args:
        body_text: Markdown text rendered above the button.
        button_label: Visible label for the action button.
        scope: Optional space-separated scopes to pass to /feishu_auth.

    Returns:
        Card dict ready to be JSON-serialized and sent via
        ``_feishu_send_with_retry(msg_type="interactive", payload=...)``.
    """
    button_value: dict = {"hermes_action": "feishu_auth"}
    if scope:
        button_value["scope"] = scope
    return {
        "schema": "2.0",
        "config": {"wide_screen_mode": True},
        "elements": [
            {"tag": "markdown", "content": body_text},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": button_label},
                        "type": "primary",
                        "value": button_value,
                    },
                ],
            },
        ],
    }


def format_scope_error(
    exc: Exception,
    *,
    suggest_command: bool = True,
) -> str:
    """Turn a scope-related auth error into a Feishu chat-ready Chinese reply.

    Recognised exception types:

      - AppScopeMissingError     — app-level scope missing (errcode 99991672)
      - UserScopeInsufficientError — user-level scope not granted (errcode 99991679)
      - UserAuthRequiredError    — alias used by the SDK wrapper

    Returns:
        Multi-line Chinese string suitable for ``adapter.send(chat_id, text)``.
    """
    if isinstance(exc, AppScopeMissingError):
        scopes = list(exc.missing_scopes or [])
        labels = labels_for_scopes(scopes)
        body = (
            f"❌ 应用层权限不足: 需要管理员在飞书开放平台为应用 "
            f"`{exc.app_id}` 申请并通过版本审核以下权限:\n\n"
        )
        body += "\n".join(f"  • {label}" for label in labels) or "  • (未知权限)"
        body += "\n\n这是 app 级权限,只有管理员能操作; 普通用户重新授权也无效。"
        return body

    if isinstance(exc, (UserScopeInsufficientError, UserAuthRequiredError)):
        scopes = list(
            getattr(exc, "missing_scopes", None)
            or getattr(exc, "required_scopes", None)
            or []
        )
        labels = labels_for_scopes(scopes)
        if labels:
            body = "⚠️ 你尚未授权我使用以下权限:\n\n"
            body += "\n".join(f"  • {label}" for label in labels)
        else:
            body = "⚠️ 你尚未完成飞书用户身份授权。"
        if suggest_command:
            scope_arg = " ".join(scopes) if scopes else ""
            cmd = f"/feishu_auth {scope_arg}".rstrip()
            body += (
                f"\n\n请发送 `{cmd}` 重新授权 (扫码 1 次即可)。"
            )
        return body

    # Fallback for any other Feishu auth error: keep it short.
    return f"⚠️ 飞书授权错误: {exc}"
