"""Transport + whitelist for HTTPS JSON-RPC (stdlib urllib). Split for line budget."""

import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel, ConfigDict

ALLOWED_RPC_METHODS: frozenset[str] = frozenset(
    {
        "eth_chainId",
        "eth_blockNumber",
        "eth_gasPrice",
        "eth_getBalance",
        "eth_getTransactionCount",
        "eth_getCode",
        "eth_call",
    }
)

_ETH_CALL_DATA_MAX_CHARS = 20_480
_RPC_TIMEOUT_SEC = float(os.getenv("HERMES_SKILL_EVM_RPC_TIMEOUT_SEC", "45"))
_RPC_MAX_ATTEMPTS = max(1, min(8, int(os.getenv("HERMES_SKILL_EVM_RPC_RETRY_PER_URL", "2"))))


class _Envelope(BaseModel):
    model_config = ConfigDict(extra="ignore")

    jsonrpc: str = "2.0"
    id: int = 1
    method: str
    params: list[Any]


def _enforce_eth_call_guards(payload: dict[str, Any]) -> None | str:
    blob = payload.get("data") or ""

    if isinstance(blob, str) and blob.startswith("0x"):
        nibbles = len(blob) - 2

        if nibbles > _ETH_CALL_DATA_MAX_CHARS:
            return "eth_call data exceeds configured maximum hex length"

    return None


def rpc_call(envelope: _Envelope, rpc_urls: list[str]) -> dict[str, Any]:
    if envelope.method not in ALLOWED_RPC_METHODS:
        return {"success": False, "error": f"disallowed method {envelope.method!r}", "disallowed": True}

    if envelope.method == "eth_call":
        if len(envelope.params) < 1 or not isinstance(envelope.params[0], dict):
            return {
                "success": False,
                "error": "eth_call requires params [ {...call_object}, block_tag]",
            }

        g = _enforce_eth_call_guards(envelope.params[0])

        if g:
            return {"success": False, "error": g}

    body = bytes(envelope.model_dump_json(), "utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": "HermesEVMJsonRpcSkill/1.0"}
    fallback_last: dict[str, Any] | None = None

    for url in rpc_urls:
        backoff = 0.5 + random.random()

        def _attempt(u: str) -> tuple[bool, dict[str, Any]]:
            req = urllib.request.Request(url=u, data=body, headers=headers, method="POST")

            try:
                with urllib.request.urlopen(req, timeout=_RPC_TIMEOUT_SEC) as resp:
                    txt = resp.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as e:
                blob = ""

                try:
                    blob = e.read().decode("utf-8", errors="replace")
                except Exception:  # noqa: BLE001
                    blob = str(e.reason)

                return False, {
                    "success": False,
                    "error": f"http_error:{e.code}",
                    "body": blob[:8192],
                }
            except Exception as exc:  # noqa: BLE001
                return False, {"success": False, "error": str(exc), "transport_exc": repr(exc)}

            try:
                payload = json.loads(txt)
            except json.JSONDecodeError:
                return False, {"success": False, "error": "upstream returned non-json", "snippet": txt[:512]}

            if not isinstance(payload, dict):
                return False, {"success": False, "error": "invalid json-rpc envelope"}

            err = payload.get("error")

            if err is None:
                return True, {"success": True, "result": payload.get("result"), "raw_id": payload.get("id")}

            if isinstance(err, dict):
                return False, {
                    "success": False,
                    "error_code": err.get("code"),
                    "error_message": err.get("message", ""),
                    "upstream": err,
                }

            return False, {"success": False, "error": str(err), "upstream": err}

        for _ in range(_RPC_MAX_ATTEMPTS):
            ok_inner, boxed = _attempt(url)
            fallback_last = boxed

            if ok_inner:
                boxed["endpoint"] = url

                return boxed

            et = boxed.get("error", "")

            if et.startswith("http_error"):
                time.sleep(backoff)

                backoff = min(backoff * 2, 4.0)
            else:
                break

    assert fallback_last is not None

    merged = dict(fallback_last)
    merged.setdefault("fallback_exhausted", True)

    return merged
