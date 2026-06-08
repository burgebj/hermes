from __future__ import annotations

import json
import shlex

from agent.cursor.connect_framing import frame_connect_message, parse_connect_frames
from agent.cursor.exec_handlers import CursorExecHandlers
from agent.cursor.proto import agent_pb2
from agent.cursor.stream_client import _consume_connect_stream


def _server_frame(server_message: agent_pb2.AgentServerMessage) -> bytes:
    return frame_connect_message(server_message.SerializeToString())


def _interaction_frame(**kwargs) -> bytes:
    message = agent_pb2.AgentServerMessage(
        interaction_update=agent_pb2.InteractionUpdate(**kwargs)
    )
    return _server_frame(message)


def _decode_client_frame(frame: bytes) -> agent_pb2.AgentClientMessage:
    decoded = list(parse_connect_frames(bytearray(frame)))
    assert len(decoded) == 1
    _, payload = decoded[0]
    message = agent_pb2.AgentClientMessage()
    message.ParseFromString(payload)
    return message


def test_read_converts_hermes_result_to_cursor_proto():
    calls: list[tuple[str, dict]] = []

    def execute_tool(name: str, args: dict, **_kwargs):
        calls.append((name, args))
        return json.dumps(
            {
                "content": "hello\nworld",
                "total_lines": 2,
                "truncated": False,
            }
        )

    handlers = CursorExecHandlers(cwd="/workspace", execute_tool=execute_tool)
    result = handlers.read(agent_pb2.ReadArgs(path="notes.txt", tool_call_id="tc-1"))

    assert calls == [("read_file", {"path": "notes.txt"})]
    assert result.WhichOneof("result") == "success"
    assert result.success.path == "notes.txt"
    assert result.success.content == "hello\nworld"
    assert result.success.total_lines == 2
    assert result.success.truncated is False


def test_mcp_decodes_args_and_calls_named_tool():
    calls: list[tuple[str, dict]] = []

    def execute_tool(name: str, args: dict, **_kwargs):
        calls.append((name, args))
        return {
            "content": [
                {
                    "type": "text",
                    "text": "forecast ready",
                }
            ]
        }

    handlers = CursorExecHandlers(cwd="/workspace", execute_tool=execute_tool)
    result = handlers.mcp(
        agent_pb2.McpArgs(
            name="ignored-name",
            tool_name="mcp__weather",
            tool_call_id="call-1",
            args={
                "city": b'"Paris"',
                "days": b"3",
                "metric": b"true",
            },
        )
    )

    assert calls == [
        (
            "mcp__weather",
            {
                "city": "Paris",
                "days": 3,
                "metric": True,
            },
        )
    ]
    assert result.WhichOneof("result") == "success"
    assert len(result.success.content) == 1
    assert result.success.content[0].WhichOneof("content") == "text"
    assert result.success.content[0].text.text == "forecast ready"


def test_delete_quotes_path_with_shlex():
    calls: list[tuple[str, dict]] = []

    def execute_tool(name: str, args: dict, **_kwargs):
        calls.append((name, args))
        return {"content": "", "error": None}

    handlers = CursorExecHandlers(cwd="/workspace", execute_tool=execute_tool)
    path = '/tmp/file"; echo injected'
    result = handlers.delete(agent_pb2.DeleteArgs(path=path, tool_call_id="del-1"))

    assert calls == [
        (
            "terminal",
            {
                "command": f"rm {shlex.quote(path)}",
                "workdir": "/workspace",
                "timeout": 30,
            },
        )
    ]
    assert result.WhichOneof("result") == "success"


def test_mcp_rejects_unknown_tool_names():
    calls: list[tuple[str, dict]] = []

    def execute_tool(name: str, args: dict, **_kwargs):
        calls.append((name, args))
        return {"content": "should not run"}

    handlers = CursorExecHandlers(
        cwd="/workspace",
        execute_tool=execute_tool,
        allowed_tools={"mcp__weather"},
    )
    result = handlers.mcp(
        agent_pb2.McpArgs(
            name="ignored-name",
            tool_name="mcp__unknown",
            tool_call_id="call-2",
        )
    )

    assert calls == []
    assert result.WhichOneof("result") == "error"
    assert result.error.error == "Unknown MCP tool: mcp__unknown"


def test_consume_connect_stream_uses_cursor_exec_handlers_object():
    writes: list[bytes] = []

    def execute_tool(name: str, args: dict, **_kwargs):
        assert name == "read_file"
        assert args == {"path": "src/app.py"}
        return {"content": "print('hi')\n", "total_lines": 1}

    frames = [
        _server_frame(
            agent_pb2.AgentServerMessage(
                exec_server_message=agent_pb2.ExecServerMessage(
                    id=11,
                    exec_id="exec-read",
                    read_args=agent_pb2.ReadArgs(path="src/app.py"),
                )
            )
        ),
        _interaction_frame(turn_ended=agent_pb2.TurnEndedUpdate()),
    ]

    _consume_connect_stream(
        frames,
        blob_store={},
        request_context_tools=[],
        exec_handlers=CursorExecHandlers(
            cwd="/workspace",
            execute_tool=execute_tool,
        ),
        send_client_frame=writes.append,
    )

    client_message = _decode_client_frame(writes[0])
    assert client_message.WhichOneof("message") == "exec_client_message"
    exec_message = client_message.exec_client_message
    assert exec_message.id == 11
    assert exec_message.exec_id == "exec-read"
    assert exec_message.read_result.WhichOneof("result") == "success"
    assert exec_message.read_result.success.content == "print('hi')\n"


def test_consume_connect_stream_emits_shell_stream_events():
    writes: list[bytes] = []

    def execute_tool(name: str, args: dict, **kwargs):
        assert name == "terminal"
        on_update = kwargs["on_update"]
        on_update({"stdout": "hello "})
        on_update({"stdout": "world\n"})
        return {"output": "hello world\n", "exit_code": 0, "error": None}

    frames = [
        _server_frame(
            agent_pb2.AgentServerMessage(
                exec_server_message=agent_pb2.ExecServerMessage(
                    id=19,
                    exec_id="exec-shell-stream",
                    shell_stream_args=agent_pb2.ShellArgs(
                        command="echo hello",
                        working_directory="/workspace",
                        timeout=30,
                    ),
                )
            )
        ),
        _interaction_frame(turn_ended=agent_pb2.TurnEndedUpdate()),
    ]

    _consume_connect_stream(
        frames,
        blob_store={},
        request_context_tools=[],
        exec_handlers=CursorExecHandlers(
            cwd="/workspace",
            execute_tool=execute_tool,
        ),
        send_client_frame=writes.append,
    )

    decoded = [_decode_client_frame(frame) for frame in writes[:5]]
    message_cases = [msg.exec_client_message.WhichOneof("message") for msg in decoded]
    assert message_cases[:4] == ["shell_stream", "shell_stream", "shell_stream", "shell_stream"]
    assert decoded[0].exec_client_message.shell_stream.WhichOneof("event") == "start"
    assert decoded[1].exec_client_message.shell_stream.stdout.data == "hello "
    assert decoded[2].exec_client_message.shell_stream.stdout.data == "world\n"
    assert decoded[3].exec_client_message.shell_stream.WhichOneof("event") == "exit"
    assert decoded[4].exec_client_message.shell_result.WhichOneof("result") == "success"
    assert decoded[4].exec_client_message.shell_result.success.stdout == "hello world\n"
