"""Read-only Microsoft OneDrive tools backed by Microsoft Graph."""

import json
import logging
import os
import time
from pathlib import Path
from urllib.parse import quote

import httpx

from hermes_constants import get_hermes_home
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

TOKEN_CACHE_PATH = Path(get_hermes_home()) / "msal_token_cache.bin"
PENDING_FLOW_PATH = Path(get_hermes_home()) / "onedrive_pending_flow.json"
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
MAX_TEXT_CHARS = 50_000


def _get_scopes() -> list[str]:
    scopes = os.getenv(
        "MICROSOFT_SCOPES",
        "User.Read Files.Read offline_access",
    ).split()
    # MSAL always requests offline_access implicitly — strip it from
    # explicit scopes to avoid "reserved scope" errors.
    return [s for s in scopes if s != "offline_access"]


def _get_msal_app():
    """Return ``(app, scopes, cache)`` or ``(None, None, None)`` on setup errors."""
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    if not client_id:
        logger.warning("MICROSOFT_CLIENT_ID is not set")
        return None, None, None

    tenant_id = os.getenv("MICROSOFT_TENANT_ID", "consumers")
    scopes = _get_scopes()

    try:
        import msal
    except ImportError:
        logger.warning("msal is not installed")
        return None, None, None

    try:
        cache = msal.SerializableTokenCache()
        if TOKEN_CACHE_PATH.exists():
            cache.deserialize(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))

        app = msal.PublicClientApplication(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            token_cache=cache,
        )
        return app, scopes, cache
    except Exception as e:
        logger.warning("Failed to initialize MSAL app: %s", e)
        return None, None, None


def _save_cache(cache) -> None:
    try:
        if cache and cache.has_state_changed:
            TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            TOKEN_CACHE_PATH.write_text(cache.serialize(), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to save MSAL token cache: %s", e)


def _save_pending_flow(flow) -> None:
    try:
        PENDING_FLOW_PATH.parent.mkdir(parents=True, exist_ok=True)
        PENDING_FLOW_PATH.write_text(json.dumps(flow), encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to save OneDrive pending device flow: %s", e)


def _load_pending_flow():
    try:
        if not PENDING_FLOW_PATH.exists():
            return None
        flow = json.loads(PENDING_FLOW_PATH.read_text(encoding="utf-8"))
        if not isinstance(flow, dict):
            return None
        expires_at = flow.get("expires_at")
        if expires_at and time.time() > float(expires_at):
            return None
        return flow
    except Exception as e:
        logger.warning("Failed to load OneDrive pending device flow: %s", e)
        return None


def _clear_pending_flow() -> None:
    try:
        PENDING_FLOW_PATH.unlink(missing_ok=True)
    except Exception as e:
        logger.warning("Failed to clear OneDrive pending device flow: %s", e)


def _auth_info_from_flow(flow: dict) -> dict:
    return {
        "needs_auth": True,
        "verification_uri": flow.get("verification_uri")
        or flow.get("verification_uri_complete"),
        "user_code": flow.get("user_code"),
        "message": flow.get("message", "Complete Microsoft device code authentication."),
    }


def _get_access_token():
    """Return an access token string, or a dict describing required auth."""
    app, scopes, cache = _get_msal_app()
    if app is None:
        return {
            "error": "Microsoft OneDrive is not configured. Set MICROSOFT_CLIENT_ID and install msal.",
        }

    try:
        for account in app.get_accounts():
            result = app.acquire_token_silent(scopes, account=account)
            if result and result.get("access_token"):
                _save_cache(cache)
                return result["access_token"]

        flow = _load_pending_flow()
        if flow:
            import urllib.parse as urlparse
            import urllib.error as urlerror
            import urllib.request as urlreq

            device_code = flow.get("device_code")
            if device_code:
                token_url = "https://login.microsoftonline.com/{}/oauth2/v2.0/token".format(
                    os.getenv("MICROSOFT_TENANT_ID", "consumers")
                )
                data = urlparse.urlencode(
                    {
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
                        "device_code": device_code,
                    }
                ).encode()
                req = urlreq.Request(
                    token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                try:
                    with urlreq.urlopen(req, timeout=10) as resp:
                        result = json.loads(resp.read())
                except urlerror.HTTPError as e:
                    # Microsoft returns 400 with authorization_pending in body.
                    result = json.loads(e.read())
                except Exception:
                    return _auth_info_from_flow(flow)
                if result and result.get("access_token"):
                    client_id = os.getenv("MICROSOFT_CLIENT_ID")
                    cache.add(
                        {
                            "client_id": client_id,
                            "scope": scopes,
                            "token_endpoint": token_url,
                            "environment": "login.microsoftonline.com",
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                            "response": result,
                            "data": {"device_code": device_code},
                        }
                    )
                    _clear_pending_flow()
                    _save_cache(cache)
                    return result["access_token"]
                if result and result.get("error") == "expired_token":
                    _clear_pending_flow()
                elif result and result.get("error") not in {"authorization_pending", "slow_down"}:
                    _clear_pending_flow()
                    return {"error": result.get("error_description") or result.get("error")}
                else:
                    return _auth_info_from_flow(flow)

        flow = app.initiate_device_flow(scopes=scopes)
        if not flow or "user_code" not in flow:
            return {
                "error": flow.get("error_description", "Could not start Microsoft device code flow.")
                if isinstance(flow, dict)
                else "Could not start Microsoft device code flow.",
            }

        _save_pending_flow(flow)
        _save_cache(cache)
        return _auth_info_from_flow(flow)
    except Exception as e:
        logger.warning("Microsoft authentication failed: %s", e)
        return {"error": f"Microsoft authentication failed: {type(e).__name__}: {e}"}


def _validate_endpoint(endpoint_path: str) -> bool:
    if endpoint_path in {"/me", "/me/drive/root/children"}:
        return True
    if endpoint_path.startswith("/me/drive/root:/") and endpoint_path.endswith(":/children"):
        inner = endpoint_path[len("/me/drive/root:/") : -len(":/children")]
        return bool(inner) and ".." not in inner.split("/")
    if endpoint_path.startswith("/me/drive/root:/") and endpoint_path.endswith(":/content"):
        inner = endpoint_path[len("/me/drive/root:/") : -len(":/content")]
        return bool(inner) and ".." not in inner.split("/")
    return False


def _encoded_path(path: str) -> str:
    return quote(path.strip().strip("/"), safe="/")


def _get_graph(endpoint_path: str) -> dict:
    if not _validate_endpoint(endpoint_path):
        return {"error": f"Endpoint is not allowed: {endpoint_path}"}

    token = _get_access_token()
    if isinstance(token, dict):
        return token

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(
                f"{GRAPH_BASE_URL}{endpoint_path}",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code >= 400:
            return _graph_error(response)
        if response.headers.get("content-type", "").lower().startswith("application/json"):
            return response.json()
        return {"content": response.text}
    except Exception as e:
        logger.warning("Microsoft Graph request failed: %s", e)
        return {"error": f"Microsoft Graph request failed: {type(e).__name__}: {e}"}


def _graph_error(response: httpx.Response) -> dict:
    raw_text = ""
    try:
        if response.is_stream_consumed:
            raw_text = response.text
        else:
            raw_text = response.read().decode(response.encoding or "utf-8", errors="replace")
        payload = json.loads(raw_text) if raw_text else {}
    except Exception:
        payload = {"message": raw_text[:1000] if raw_text else "Unable to read error response."}
    return {
        "error": "Microsoft Graph request failed",
        "status_code": response.status_code,
        "details": payload,
    }


def _tool_error_from_payload(payload: dict) -> str:
    message = payload.get("error", "Microsoft OneDrive request failed")
    extra = {k: v for k, v in payload.items() if k != "error"}
    return tool_error(message, **extra)


def _drive_items(payload: dict) -> list[dict]:
    return [
        {
            "name": item.get("name"),
            "id": item.get("id"),
            "size": item.get("size"),
            "folder": bool(item.get("folder")),
            "lastModifiedDateTime": item.get("lastModifiedDateTime"),
        }
        for item in payload.get("value", [])
    ]


def _content_endpoint(path: str) -> str:
    encoded = _encoded_path(path)
    if not encoded:
        return ""
    return f"/me/drive/root:/{encoded}:/content"


def _children_endpoint(path: str) -> str:
    encoded = _encoded_path(path)
    if not encoded:
        return ""
    return f"/me/drive/root:/{encoded}:/children"


def _get_content_response(endpoint_path: str):
    if not _validate_endpoint(endpoint_path):
        return {"error": f"Endpoint is not allowed: {endpoint_path}"}

    token = _get_access_token()
    if isinstance(token, dict):
        return token

    client = None
    try:
        client = httpx.Client(timeout=60.0, follow_redirects=True)
        request = client.build_request(
            "GET",
            f"{GRAPH_BASE_URL}{endpoint_path}",
            headers={"Authorization": f"Bearer {token}"},
        )
        return client, client.send(request, stream=True)
    except Exception as e:
        if client is not None:
            client.close()
        logger.warning("Microsoft Graph content request failed: %s", e)
        return {"error": f"Microsoft Graph content request failed: {type(e).__name__}: {e}"}


def list_onedrive_root() -> str:
    payload = _get_graph("/me/drive/root/children")
    if payload.get("needs_auth"):
        return tool_result(payload)
    if "error" in payload:
        return _tool_error_from_payload(payload)
    return tool_result(success=True, items=_drive_items(payload))


def list_onedrive_folder(path: str) -> str:
    path = str(path).strip()
    if not path:
        return tool_error("path is required")

    endpoint = _children_endpoint(path)
    if not endpoint:
        return tool_error("path is required")

    payload = _get_graph(endpoint)
    if payload.get("needs_auth"):
        return tool_result(payload)
    if "error" in payload:
        return _tool_error_from_payload(payload)
    return tool_result(success=True, path=path, items=_drive_items(payload))


def read_onedrive_text_file(path: str) -> str:
    path = str(path).strip()
    endpoint = _content_endpoint(path)
    if not endpoint:
        return tool_error("path is required")

    started_at = time.monotonic()
    result = _get_content_response(endpoint)
    if isinstance(result, dict):
        return tool_result(result) if result.get("needs_auth") else tool_error(result.get("error", result))

    client, response = result
    try:
        if response.status_code >= 400:
            return _tool_error_from_payload(_graph_error(response))

        chunks: list[str] = []
        total = 0
        truncated = False
        for text in response.iter_text():
            remaining = MAX_TEXT_CHARS - total
            if remaining <= 0:
                truncated = True
                break
            chunks.append(text[:remaining])
            total += len(text[:remaining])
            if len(text) > remaining:
                truncated = True
                break

        data = {
            "success": True,
            "path": path,
            "content": "".join(chunks),
            "truncated": truncated,
            "elapsed_seconds": round(time.monotonic() - started_at, 3),
        }
        if truncated:
            data["warning"] = f"File content truncated to {MAX_TEXT_CHARS} characters."
        return tool_result(data)
    except Exception as e:
        logger.warning("Failed to read OneDrive file: %s", e)
        return tool_error(f"Failed to read OneDrive file: {type(e).__name__}: {e}")
    finally:
        response.close()
        client.close()


def download_onedrive_file(path: str, target_path: str) -> str:
    path = str(path).strip()
    target_path = str(target_path).strip()
    endpoint = _content_endpoint(path)
    if not endpoint:
        return tool_error("path is required")
    if not target_path:
        return tool_error("target_path is required")

    result = _get_content_response(endpoint)
    if isinstance(result, dict):
        return tool_result(result) if result.get("needs_auth") else tool_error(result.get("error", result))

    client, response = result
    output_path = Path(target_path).expanduser()
    total = 0
    try:
        if response.status_code >= 400:
            return _tool_error_from_payload(_graph_error(response))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
                total += len(chunk)
        return tool_result(success=True, file_size=total, path=str(output_path))
    except Exception as e:
        logger.warning("Failed to download OneDrive file: %s", e)
        return tool_error(f"Failed to download OneDrive file: {type(e).__name__}: {e}")
    finally:
        response.close()
        client.close()


def _handle_list_root(args: dict, **kwargs) -> str:
    return list_onedrive_root()


def _handle_list_folder(args: dict, **kwargs) -> str:
    return list_onedrive_folder(args.get("path", ""))


def _handle_read_text_file(args: dict, **kwargs) -> str:
    return read_onedrive_text_file(args.get("path", ""))


def _handle_download_file(args: dict, **kwargs) -> str:
    return download_onedrive_file(args.get("path", ""), args.get("target_path", ""))


def _check_onedrive() -> bool:
    if not os.getenv("MICROSOFT_CLIENT_ID"):
        return False
    try:
        import msal  # noqa: F401
    except ImportError:
        return False
    return True


LIST_ONEDRIVE_ROOT_SCHEMA = {
    "name": "list_onedrive_root",
    "description": "List items in the signed-in user's OneDrive root folder.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

LIST_ONEDRIVE_FOLDER_SCHEMA = {
    "name": "list_onedrive_folder",
    "description": "List items in a OneDrive folder by path.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Folder path relative to the OneDrive root.",
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    },
}

READ_ONEDRIVE_TEXT_FILE_SCHEMA = {
    "name": "read_onedrive_text_file",
    "description": "Read a OneDrive text file by path. Content is capped at 50000 characters.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path relative to the OneDrive root.",
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    },
}

DOWNLOAD_ONEDRIVE_FILE_SCHEMA = {
    "name": "download_onedrive_file",
    "description": "Download a OneDrive file by path to a local target path.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path relative to the OneDrive root.",
            },
            "target_path": {
                "type": "string",
                "description": "Local path where the file should be saved.",
            },
        },
        "required": ["path", "target_path"],
        "additionalProperties": False,
    },
}


registry.register(
    name="list_onedrive_root",
    toolset="onedrive",
    schema=LIST_ONEDRIVE_ROOT_SCHEMA,
    handler=_handle_list_root,
    check_fn=_check_onedrive,
    requires_env=["MICROSOFT_CLIENT_ID"],
    description="List OneDrive root folder",
    emoji="\u2601\ufe0f",
)

registry.register(
    name="list_onedrive_folder",
    toolset="onedrive",
    schema=LIST_ONEDRIVE_FOLDER_SCHEMA,
    handler=_handle_list_folder,
    check_fn=_check_onedrive,
    requires_env=["MICROSOFT_CLIENT_ID"],
    description="List OneDrive folder",
    emoji="\u2601\ufe0f",
)

registry.register(
    name="read_onedrive_text_file",
    toolset="onedrive",
    schema=READ_ONEDRIVE_TEXT_FILE_SCHEMA,
    handler=_handle_read_text_file,
    check_fn=_check_onedrive,
    requires_env=["MICROSOFT_CLIENT_ID"],
    description="Read OneDrive text file",
    emoji="\U0001f4d6",
)

registry.register(
    name="download_onedrive_file",
    toolset="onedrive",
    schema=DOWNLOAD_ONEDRIVE_FILE_SCHEMA,
    handler=_handle_download_file,
    check_fn=_check_onedrive,
    requires_env=["MICROSOFT_CLIENT_ID"],
    description="Download OneDrive file",
    emoji="\u2b07\ufe0f",
)
