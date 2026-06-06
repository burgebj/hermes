from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


PLUGIN_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PLUGIN_DIR / "pawrtal_config.json"
_relay_server: ThreadingHTTPServer | None = None
_job_titles: dict[str, str] = {}


def _companions_dir() -> Path:
    env = os.environ.get("PAWRTAL_PACKS_DIR") or os.environ.get("HERMES_PAWRTAL_PACKS_DIR")
    if env:
        return Path(env).expanduser()
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if data.get("companionsDir"):
            return Path(data["companionsDir"]).expanduser()
    return Path(os.environ.get("PAWRTAL_HOME", "~/.pawrtal")).expanduser() / "packs"


def _state_dir() -> Path:
    return Path(os.environ.get("PAWRTAL_HOME", "~/.pawrtal")).expanduser() / "state" / "hermes"


def _activity_dir() -> Path:
    return _state_dir() / "activity"


def _relay_path() -> Path:
    return _state_dir() / "relay.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compact(value: Any, limit: int = 96) -> str:
    text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _tool_line(tool_name: str, args: dict[str, Any] | None) -> str:
    args = args or {}
    for key in ("cmd", "command", "query", "path", "url", "q"):
        if key in args and args[key]:
            return f"{tool_name}: {_compact(args[key], 92)}"
    if args:
        return f"{tool_name}: {_compact(args, 92)}"
    return f"Calling {tool_name}"


def _title_from_message(value: Any) -> str:
    text = _compact(value or "Hermes task", 72)
    if not text:
        return "Hermes task"
    return text[0].upper() + text[1:]


def _answer_text(kwargs: dict[str, Any]) -> str:
    for key in ("assistant_response", "assistant_message", "response", "message", "content"):
        value = kwargs.get(key)
        if not value:
            continue
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for nested_key in ("content", "text", "message"):
                nested = value.get(nested_key)
                if nested:
                    return str(nested)
        return str(value)
    return "Finished"


def _session(kwargs: dict[str, Any]) -> str:
    return str(kwargs.get("session_id") or kwargs.get("task_id") or "current")


def _looks_failed(result: Any) -> bool:
    if isinstance(result, dict):
        return bool(result.get("error") or result.get("success") is False)
    text = str(result).lower()
    return '"error"' in text or '"success": false' in text or "traceback" in text


def _write_activity(session: str, phase: str, message: str, animation: str, **extra: Any) -> None:
    title = extra.pop("title", None) or _job_titles.get(session) or "Hermes task"
    status = extra.pop("status", phase)
    activity = {
        "target": "hermes",
        "session": session,
        "phase": phase,
        "status": status,
        "title": title,
        "message": message,
        "animation": animation,
        "updatedAt": _now(),
        **extra,
    }
    root = _activity_dir()
    root.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(activity, indent=2) + "\n"
    (root / f"{session}.json").write_text(payload, encoding="utf-8")
    (root / "current.json").write_text(payload, encoding="utf-8")


def _read_pack(path: Path) -> dict[str, Any]:
    data = json.loads((path / "pawrtal.json").read_text(encoding="utf-8"))
    data["packDir"] = str(path)
    data["spritesheetPath"] = str(path / data["assets"]["spritesheet"])
    return data


def pawrtal_list(params: dict[str, Any] | None = None, **kwargs: Any) -> str:
    del params, kwargs
    packs = []
    root = _companions_dir()
    if root.exists():
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "pawrtal.json").exists():
                pack = _read_pack(child)
                packs.append({
                    "id": pack["id"],
                    "displayName": pack.get("displayName", pack["id"]),
                    "description": pack.get("description", ""),
                    "packDir": pack["packDir"],
                })
    return json.dumps({"companions": packs}, indent=2)


def pawrtal_use(params: dict[str, Any], **kwargs: Any) -> str:
    del kwargs
    pet_id = params["pet_id"]
    session = params.get("session") or "current"
    pack_dir = _companions_dir() / pet_id
    pack = _read_pack(pack_dir)
    state = {
        "target": "hermes",
        "session": session,
        "activePetId": pack["id"],
        "displayName": pack.get("displayName", pack["id"]),
        "packDir": str(pack_dir),
        "manifestPath": str(pack_dir / "pawrtal.json"),
        "spritesheetPath": pack["spritesheetPath"],
    }
    state_dir = _state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / f"{session}.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    (state_dir / "current.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    _write_activity(
        session,
        "selected",
        f"{pack.get('displayName', pack['id'])} linked",
        "waving",
        title="Pawrtal companion",
        status="done",
    )
    return json.dumps({"selected": pack["id"], "state": state}, indent=2)


def pawrtal_status(params: dict[str, Any] | None = None, **kwargs: Any) -> str:
    del kwargs
    session = (params or {}).get("session") or "current"
    path = _state_dir() / f"{session}.json"
    if not path.exists():
        return json.dumps({"active": None, "message": "No Pawrtal companion selected."}, indent=2)
    return path.read_text(encoding="utf-8")


def _run_pawrtal(args: list[str]) -> str:
    binary = shutil.which("pawrtal")
    if not binary:
        return json.dumps(
            {
                "ok": False,
                "error": "pawrtal CLI was not found on PATH. Install Pawrtal first, then try again.",
            },
            indent=2,
        )

    command = [binary, *args]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    except subprocess.TimeoutExpired:
        return json.dumps(
            {
                "ok": False,
                "command": " ".join(command),
                "error": "Timed out while running Pawrtal.",
            },
            indent=2,
        )

    ok = proc.returncode == 0
    return json.dumps(
        {
            "ok": ok,
            "command": " ".join(command),
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "message": "Done." if ok else "Pawrtal command failed.",
        },
        indent=2,
    )


def pawrtal_update(params: dict[str, Any] | None = None, **kwargs: Any) -> str:
    del params, kwargs
    result = json.loads(_run_pawrtal(["update", "hermes"]))
    if result.get("ok"):
        result["restartRequired"] = True
        result["message"] = "Restart Hermes to load changed plugin code."
    return json.dumps(result, indent=2)


def pawrtal_spawn(params: dict[str, Any] | None = None, **kwargs: Any) -> str:
    del kwargs
    params = params or {}
    session = params.get("session") or "current"
    pet_id = params.get("pet_id")
    args = ["spawn"]
    if pet_id:
        args.append(str(pet_id))
    args.extend(["--target", "hermes", "--session", str(session)])
    return _run_pawrtal(args)


def pawrtal_vanish(params: dict[str, Any] | None = None, **kwargs: Any) -> str:
    del kwargs
    params = params or {}
    session = params.get("session") or "current"
    pet_id = params.get("pet_id")
    args = ["vanish"]
    if pet_id:
        args.append(str(pet_id))
    args.extend(["--target", "hermes", "--session", str(session)])
    return _run_pawrtal(args)


def _slash_help() -> str:
    return (
        "Usage:\n"
        "  /pawrtal list\n"
        "  /pawrtal use <pet_id> [session]\n"
        "  /pawrtal spawn [pet_id] [session]\n"
        "  /pawrtal vanish [pet_id] [session]\n"
        "  /pawrtal status [session]\n"
        "  /pawrtal update\n"
    )


def pawrtal_slash(raw_args: str) -> str:
    try:
        parts = shlex.split(raw_args or "")
    except ValueError as exc:
        return f"Invalid /pawrtal args: {exc}\n\n{_slash_help()}"

    if not parts or parts[0] in {"help", "-h", "--help"}:
        return _slash_help()

    command = parts[0].lower()
    if command == "list":
        return pawrtal_list()
    if command == "use":
        if len(parts) < 2:
            return _slash_help()
        return pawrtal_use({"pet_id": parts[1], "session": parts[2] if len(parts) > 2 else "current"})
    if command == "spawn":
        return pawrtal_spawn({"pet_id": parts[1] if len(parts) > 1 else None, "session": parts[2] if len(parts) > 2 else "current"})
    if command == "vanish":
        return pawrtal_vanish({"pet_id": parts[1] if len(parts) > 1 else None, "session": parts[2] if len(parts) > 2 else "current"})
    if command == "status":
        return pawrtal_status({"session": parts[1] if len(parts) > 1 else "current"})
    if command == "update":
        return pawrtal_update()

    return f"Unknown /pawrtal command: {command}\n\n{_slash_help()}"


def on_pre_llm_call(**kwargs: Any) -> None:
    session = _session(kwargs)
    title = _title_from_message(kwargs.get("user_message"))
    _job_titles[session] = title
    _job_titles["current"] = title
    _write_activity(
        session,
        "thinking",
        "Thinking",
        "waiting",
        title=title,
        status="running",
        detail=_compact(kwargs.get("user_message", ""), 140),
    )


def on_post_llm_call(**kwargs: Any) -> None:
    session = _session(kwargs)
    answer = _answer_text(kwargs)
    _write_activity(
        session,
        "answered",
        _compact(answer, 150),
        "waving",
        status="done",
        detail=_compact(answer, 900),
    )


def on_pre_tool_call(tool_name: str, args: dict[str, Any] | None = None, **kwargs: Any) -> None:
    session = _session(kwargs)
    line = _tool_line(tool_name, args)
    detail = _compact(args or {}, 180)
    _write_activity(
        session,
        "tool_running",
        line,
        "review",
        status="running",
        toolName=tool_name,
        detail=detail,
    )


def on_post_tool_call(tool_name: str, args: dict[str, Any] | None = None, result: Any = None, **kwargs: Any) -> None:
    session = _session(kwargs)
    failed = _looks_failed(result)
    _write_activity(
        session,
        "tool_failed" if failed else "tool_done",
        f"{tool_name} failed" if failed else f"Finished {tool_name}",
        "failed" if failed else "waving",
        status="failed" if failed else "done",
        toolName=tool_name,
        detail=_compact(result, 220),
        durationMs=kwargs.get("duration_ms"),
    )


def _start_relay(ctx: Any) -> None:
    global _relay_server
    if _relay_server is not None:
        return

    class RelayHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path != "/reply":
                self.send_response(404)
                self.end_headers()
                return

            length = int(self.headers.get("content-length", "0") or "0")
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
                message = _compact(payload.get("message", ""), 4000)
                session = str(payload.get("session") or "current")
                if not message:
                    raise ValueError("message is required")
                ok = bool(ctx.inject_message(message, role="user"))
                _write_activity(
                    session,
                    "reply_sent" if ok else "reply_failed",
                    "Reply sent" if ok else "Could not send reply",
                    "waving" if ok else "failed",
                    title=_job_titles.get(session) or "Hermes task",
                    status="done" if ok else "failed",
                    detail=message,
                )
                body = json.dumps({"ok": ok}).encode("utf-8")
                self.send_response(200 if ok else 503)
            except Exception as exc:
                body = json.dumps({"ok": False, "error": str(exc)}).encode("utf-8")
                self.send_response(400)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    _relay_server = ThreadingHTTPServer(("127.0.0.1", 0), RelayHandler)
    host, port = _relay_server.server_address
    _state_dir().mkdir(parents=True, exist_ok=True)
    _relay_path().write_text(json.dumps({"host": host, "port": port}, indent=2) + "\n", encoding="utf-8")
    thread = threading.Thread(target=_relay_server.serve_forever, name="pawrtal-reply-relay", daemon=True)
    thread.start()


PAWRTAL_LIST_SCHEMA = {
    "name": "pawrtal_list",
    "description": "List Pawrtal companions available to Hermes.",
    "parameters": {
    "type": "object",
    "properties": {},
    "required": [],
    },
}

PAWRTAL_USE_SCHEMA = {
    "name": "pawrtal_use",
    "description": "Select a Pawrtal companion for this Hermes session.",
    "parameters": {
    "type": "object",
    "properties": {
        "pet_id": {"type": "string", "description": "Pawrtal companion id to activate."},
        "session": {"type": "string", "description": "Hermes session id. Defaults to current."},
    },
    "required": ["pet_id"],
    },
}

PAWRTAL_STATUS_SCHEMA = {
    "name": "pawrtal_status",
    "description": "Show the active Pawrtal companion for this Hermes session.",
    "parameters": {
    "type": "object",
    "properties": {
        "session": {"type": "string", "description": "Hermes session id. Defaults to current."},
    },
    "required": [],
    },
}

PAWRTAL_UPDATE_SCHEMA = {
    "name": "pawrtal_update",
    "description": "Update the installed Pawrtal Hermes plugin from the local Pawrtal CLI.",
    "parameters": {
    "type": "object",
    "properties": {},
    "required": [],
    },
}

PAWRTAL_SPAWN_SCHEMA = {
    "name": "pawrtal_spawn",
    "description": "Spawn the Pawrtal desktop companion for this Hermes session.",
    "parameters": {
    "type": "object",
    "properties": {
        "pet_id": {"type": "string", "description": "Optional Pawrtal companion id to activate before spawning."},
        "session": {"type": "string", "description": "Hermes session id. Defaults to current."},
    },
    "required": [],
    },
}

PAWRTAL_VANISH_SCHEMA = {
    "name": "pawrtal_vanish",
    "description": "Vanish the Pawrtal desktop companion for this Hermes session.",
    "parameters": {
    "type": "object",
    "properties": {
        "pet_id": {"type": "string", "description": "Optional companion id to vanish if it is active."},
        "session": {"type": "string", "description": "Hermes session id. Defaults to current."},
    },
    "required": [],
    },
}


def register(ctx) -> None:
    _start_relay(ctx)
    ctx.register_tool(
        name="pawrtal_list",
        toolset="pawrtal",
        schema=PAWRTAL_LIST_SCHEMA,
        handler=pawrtal_list,
        description="List Pawrtal companions available to Hermes.",
        emoji="🐾",
    )
    ctx.register_tool(
        name="pawrtal_use",
        toolset="pawrtal",
        schema=PAWRTAL_USE_SCHEMA,
        handler=pawrtal_use,
        description="Select a Pawrtal companion for this Hermes session.",
        emoji="🐾",
    )
    ctx.register_tool(
        name="pawrtal_status",
        toolset="pawrtal",
        schema=PAWRTAL_STATUS_SCHEMA,
        handler=pawrtal_status,
        description="Show the active Pawrtal companion for this Hermes session.",
        emoji="🐾",
    )
    ctx.register_tool(
        name="pawrtal_spawn",
        toolset="pawrtal",
        schema=PAWRTAL_SPAWN_SCHEMA,
        handler=pawrtal_spawn,
        description="Spawn the Pawrtal desktop companion for this Hermes session.",
        emoji="🐾",
    )
    ctx.register_tool(
        name="pawrtal_vanish",
        toolset="pawrtal",
        schema=PAWRTAL_VANISH_SCHEMA,
        handler=pawrtal_vanish,
        description="Vanish the Pawrtal desktop companion for this Hermes session.",
        emoji="🐾",
    )
    ctx.register_tool(
        name="pawrtal_update",
        toolset="pawrtal",
        schema=PAWRTAL_UPDATE_SCHEMA,
        handler=pawrtal_update,
        description="Update the installed Pawrtal Hermes plugin from the local CLI.",
        emoji="🐾",
    )
    ctx.register_command(
        "pawrtal",
        handler=pawrtal_slash,
        description="Manage Pawrtal companions for this session.",
        args_hint="list | use <pet_id> [session] | spawn [pet_id] [session] | vanish [pet_id] [session] | status [session] | update",
    )
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("post_llm_call", on_post_llm_call)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
