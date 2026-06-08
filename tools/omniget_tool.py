"""OmniGet local desktop-app integration tools.

The tool talks to OmniGet's localhost bridge when the desktop app is running.
It deliberately never returns the bearer token from settings.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from tools.registry import registry

DEFAULT_BRIDGE_PORT = 47720
SETTINGS_RELATIVE = Path("wtf.tonho.omniget") / "settings.json"


def _local_appdata() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")


def _appdata() -> Path:
    return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")


def _omniget_exe() -> Path:
    return _local_appdata() / "omniget" / "omniget.exe"


def _settings_path() -> Path:
    return _appdata() / SETTINGS_RELATIVE


def _plugins_path() -> Path:
    return _appdata() / "wtf.tonho.omniget" / "plugins" / "installed.json"


def _load_app_settings() -> dict[str, Any]:
    path = _settings_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    app_settings = data.get("app_settings")
    return app_settings if isinstance(app_settings, dict) else {}


def _bridge_config() -> tuple[str, str, bool]:
    settings = _load_app_settings()
    bridge = settings.get("bridge") if isinstance(settings.get("bridge"), dict) else {}
    port = bridge.get("port") or DEFAULT_BRIDGE_PORT
    endpoint = f"http://127.0.0.1:{port}"
    token = bridge.get("token") if isinstance(bridge.get("token"), str) else ""
    enabled = bool(bridge.get("enabled", False))
    return endpoint, token, enabled


def _json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _request_json(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    endpoint, saved_token, _enabled = _bridge_config()
    auth_token = token if token is not None else saved_token
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    req = urllib.request.Request(
        endpoint + path,
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            text = response.read().decode("utf-8", "replace")
            parsed = json.loads(text) if text else None
            return {"ok": True, "status": response.status, "body": parsed}
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(text) if text else None
        except json.JSONDecodeError:
            parsed = {"text": text}
        return {"ok": False, "status": exc.code, "body": parsed}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "message": str(exc)}


def _load_plugins() -> list[dict[str, Any]]:
    path = _plugins_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        return []
    sanitized: list[dict[str, Any]] = []
    for plugin in plugins:
        if not isinstance(plugin, dict):
            continue
        sanitized.append(
            {
                "id": plugin.get("id"),
                "version": plugin.get("version"),
                "enabled": plugin.get("enabled"),
                "repo": plugin.get("repo"),
                "source_release": plugin.get("source_release"),
            }
        )
    return sanitized


def _build_scheme_url(url: str) -> str:
    trimmed = url.strip()
    if trimmed.startswith("omniget://"):
        return trimmed
    if trimmed.startswith("magnet:") or trimmed.startswith("p2p:"):
        return f"omniget:{trimmed}"
    without_protocol = trimmed.removeprefix("https://").removeprefix("http://")
    return f"omniget://{without_protocol}"


def check_omniget_requirements() -> bool:
    return _omniget_exe().exists() or _settings_path().exists()


def omniget_tool(
    action: str,
    url: str = "",
    title: str = "",
    referer: str = "",
    cookies: list[dict[str, Any]] | None = None,
    task_id: str | None = None,
) -> str:
    """Operate the local OmniGet desktop app bridge."""
    endpoint, token, bridge_enabled = _bridge_config()
    exe = _omniget_exe()
    settings = _load_app_settings()

    if action == "status":
        health = _request_json("GET", "/v1/health", timeout=3.0)
        return _json_response(
            {
                "ok": True,
                "exe_exists": exe.exists(),
                "exe_path": str(exe),
                "settings_exists": _settings_path().exists(),
                "settings_path": str(_settings_path()),
                "bridge_enabled": bridge_enabled,
                "bridge_endpoint": endpoint,
                "bridge_token_configured": bool(token),
                "health": health,
                "download_dir": settings.get("download", {}).get("default_output_dir") if isinstance(settings.get("download"), dict) else None,
                "plugins": _load_plugins(),
            }
        )

    if action == "health":
        return _json_response(_request_json("GET", "/v1/health", timeout=3.0))

    if action == "plugins":
        return _json_response({"ok": True, "plugins": _load_plugins()})

    if action == "enqueue":
        if not url.strip():
            return _json_response({"ok": False, "reason": "missing-url"})
        payload: dict[str, Any] = {
            "type": "enqueue",
            "url": url.strip(),
            "protocolVersion": 1,
        }
        if title.strip():
            payload["title"] = title.strip()
        if referer.strip():
            payload["referer"] = referer.strip()
        if cookies:
            payload["cookies"] = cookies
        result = _request_json(
            "POST",
            "/v1/enqueue",
            body=payload,
            timeout=8.0,
        )
        return _json_response(result)

    if action == "open_url":
        if not url.strip():
            return _json_response({"ok": False, "reason": "missing-url"})
        scheme_url = _build_scheme_url(url)
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "", scheme_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return _json_response({"ok": True, "scheme_url": scheme_url})
        except Exception as exc:
            return _json_response({"ok": False, "error": type(exc).__name__, "message": str(exc), "scheme_url": scheme_url})

    return _json_response(
        {
            "ok": False,
            "reason": "unknown-action",
            "allowed_actions": ["status", "health", "plugins", "enqueue", "open_url"],
        }
    )


registry.register(
    name="omniget",
    toolset="omniget",
    schema={
        "name": "omniget",
        "description": "Operate the local OmniGet desktop app: status, bridge health, plugin list, enqueue URL, or open URL via omniget://.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["status", "health", "plugins", "enqueue", "open_url"],
                    "description": "Operation to perform.",
                },
                "url": {
                    "type": "string",
                    "description": "URL to enqueue/open for action=enqueue or action=open_url.",
                },
                "title": {
                    "type": "string",
                    "description": "Optional page title metadata for action=enqueue.",
                },
                "referer": {
                    "type": "string",
                    "description": "Optional referer/source page URL metadata for action=enqueue.",
                },
                "cookies": {
                    "type": "array",
                    "description": "Optional browser cookie objects for action=enqueue. Do not provide unless explicitly needed.",
                    "items": {"type": "object"},
                },
            },
            "required": ["action"],
        },
    },
    handler=lambda args, **kw: omniget_tool(
        action=args.get("action", "status"),
        url=args.get("url", ""),
        title=args.get("title", ""),
        referer=args.get("referer", ""),
        cookies=args.get("cookies"),
        task_id=kw.get("task_id"),
    ),
    check_fn=check_omniget_requirements,
    description="Control OmniGet through its localhost bridge without exposing its bearer token.",
    emoji="⬇️",
)
