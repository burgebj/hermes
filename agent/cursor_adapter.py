"""Adapter between Hermes' standard API kwargs and the Cursor Agent API."""

from __future__ import annotations

import uuid
from typing import Any

from agent.cursor.exec_handlers import CursorExecHandlers
from agent.cursor.stream_client import run_cursor_agent_turn


def _flatten_tool(tool: dict[str, Any]) -> dict[str, Any]:
    if tool.get("type") == "function" and isinstance(tool.get("function"), dict):
        function = tool["function"]
        return {
            "name": function.get("name", ""),
            "description": function.get("description", ""),
            "parameters": function.get("parameters")
            or {"type": "object", "properties": {}, "required": []},
        }
    return tool


def build_cursor_api_kwargs(agent, api_kwargs: dict[str, Any]) -> dict[str, Any]:
    """Extract Cursor run-turn kwargs from Hermes' standard api_kwargs."""
    raw_messages = list(api_kwargs.get("messages") or [])
    system_prompt: list[str] = []
    messages: list[dict[str, Any]] = []
    for message in raw_messages:
        if not isinstance(message, dict):
            continue
        if message.get("role") == "system":
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                system_prompt.append(content)
            continue
        messages.append(message)

    tools = [_flatten_tool(tool) for tool in (api_kwargs.get("tools") or [])]
    conversation_id = getattr(agent, "_cursor_conversation_id", None)
    if not conversation_id:
        conversation_id = getattr(agent, "session_id", None) or str(uuid.uuid4())
        agent._cursor_conversation_id = conversation_id

    return {
        "model_id": api_kwargs.get("model") or getattr(agent, "model", ""),
        "messages": messages,
        "system_prompt": system_prompt or None,
        "tools": tools or None,
        "conversation_id": conversation_id,
    }


def run_cursor_turn(
    agent,
    api_kwargs: dict[str, Any],
    on_first_delta=None,
    on_text_delta=None,
):
    """Execute a single Cursor Agent API turn with Hermes tool handlers."""
    cursor_kwargs = build_cursor_api_kwargs(agent, api_kwargs)

    first_delta_sent = False

    def _on_text_delta(delta: str) -> None:
        nonlocal first_delta_sent
        if delta and not first_delta_sent:
            first_delta_sent = True
            if on_first_delta:
                on_first_delta()
        if on_text_delta:
            on_text_delta(delta)

    response = run_cursor_agent_turn(
        api_key=getattr(agent, "api_key", ""),
        base_url=getattr(agent, "base_url", None) or "https://api2.cursor.sh",
        model_id=cursor_kwargs["model_id"],
        messages=cursor_kwargs["messages"],
        system_prompt=cursor_kwargs["system_prompt"],
        tools=cursor_kwargs["tools"],
        conversation_id=cursor_kwargs["conversation_id"],
        blob_store=getattr(agent, "_cursor_blob_store", None),
        conversation_state=getattr(agent, "_cursor_conversation_state", None),
        exec_handlers=CursorExecHandlers(agent=agent),
        on_text_delta=_on_text_delta if (on_first_delta or on_text_delta) else None,
        interrupt_event=getattr(agent, "_interrupt_event", None),
    )
    agent._cursor_blob_store = getattr(response, "blob_store", None)
    agent._cursor_conversation_state = getattr(response, "conversation_state", None)
    if not getattr(response, "model", None):
        response.model = cursor_kwargs["model_id"]
    return response
