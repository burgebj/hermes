"""ParseThis prompt/output screening for Hermes.

Supports two runtime modes:

- ``pattern-only`` / ``local``: cheap local prompt-injection fixtures only.
- ``paid`` / ``live`` / ``x402``: local normalizer first, then ParseThis HTTP
  screening using Bearer auth when ``PARSE_API_KEY`` is present, with x402
  pay-per-call fallback through ``~/.hermes/x402-client/x402-fetch.mjs``.

Private payer/API material is never printed by this module.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from hermes_constants import get_hermes_home
from hermes_cli.config import cfg_get, load_config

logger = logging.getLogger(__name__)

_BLOCK_MESSAGE = (
    "Parse screening blocked this content before it crossed a Hermes safety "
    "boundary. The content matched prompt-injection / instruction-smuggling "
    "patterns and was not passed through."
)
_PARSE_UNAVAILABLE_MESSAGE = (
    "Parse screening is configured for paid live screening, but the Parse/x402 "
    "backend was unavailable. Because fail_closed is enabled, Hermes blocked "
    "this boundary instead of passing unscreened content."
)

_SAFE_ACTIONS = {"allow", "allowed", "safe", "pass"}
_BLOCK_ACTIONS = {
    "block",
    "blocked",
    "deny",
    "denied",
    "reject",
    "rejected",
    "request_owner_approval",
    "owner_approval",
    "approval_required",
    "sandbox",
    "review",
    "warn",
}
_LIVE_MODES = {"paid", "live", "x402", "parsethis", "parse", "remote"}
_LOCAL_MODES = {"pattern-only", "pattern_only", "local", "offline"}

_SUSPICIOUS_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE | re.DOTALL)
    for pattern in [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|messages)",
        r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|messages)",
        r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|messages)",
        r"you\s+are\s+now\s+(in\s+)?(developer|system|admin|root|god)\s+mode",
        r"act\s+as\s+(the\s+)?(system|developer|admin|root)",
        r"reveal\s+(the\s+)?(system\s+prompt|developer\s+message|hidden\s+instructions|secrets?)",
        r"print\s+(the\s+)?(system\s+prompt|developer\s+message|hidden\s+instructions|secrets?)",
        r"exfiltrat(e|ion)|steal\s+(api\s+keys?|tokens?|credentials?)",
        r"send\s+(api\s+keys?|tokens?|credentials?|secrets?)\s+to\s+https?://",
        r"tool\s*call\s*:\s*\{",
        r"<\s*script\b[^>]*>.*?(ignore|disregard|reveal|exfiltrate)",
        r"<!--.*?(ignore|disregard|reveal|exfiltrate).*?-->",
        r"BEGIN\s+(SYSTEM|DEVELOPER|HIDDEN)\s+(PROMPT|INSTRUCTIONS)",
        r"END\s+(SYSTEM|DEVELOPER|HIDDEN)\s+(PROMPT|INSTRUCTIONS)",
    ]
)

_B64_RE = re.compile(r"(?<![A-Za-z0-9+/=])([A-Za-z0-9+/]{32,}={0,2})(?![A-Za-z0-9+/=])")
_HEX_RE = re.compile(r"(?<![A-Fa-f0-9])([A-Fa-f0-9]{40,})(?![A-Fa-f0-9])")


@dataclass(frozen=True)
class ParseScreeningSettings:
    enabled: bool = False
    auth: str = "auto"
    boundary_mode: str = "risk-gated"
    prompt_enabled: bool = True
    tool_result_enabled: bool = True
    output_enabled: bool = True
    x402_enabled: bool = True
    fail_closed: bool = True
    timeout_seconds: int = 20
    base_url: str = "https://www.parsethis.ai"
    max_usdc: str = "0.02"
    mode: str = "pattern-only"


def load_settings(config: dict[str, Any] | None = None) -> ParseScreeningSettings:
    cfg = config if config is not None else load_config()
    section = cfg_get(cfg, "security", "parse_screening", default={}) or {}
    if not isinstance(section, dict):
        section = {}
    return ParseScreeningSettings(
        enabled=bool(section.get("enabled", False)),
        auth=str(section.get("auth", "auto")),
        boundary_mode=str(section.get("boundary_mode", "risk-gated")),
        prompt_enabled=bool(section.get("prompt_enabled", True)),
        tool_result_enabled=bool(section.get("tool_result_enabled", True)),
        output_enabled=bool(section.get("output_enabled", True)),
        x402_enabled=bool(section.get("x402_enabled", True)),
        fail_closed=bool(section.get("fail_closed", True)),
        timeout_seconds=int(section.get("timeout_seconds", 20) or 20),
        base_url=str(section.get("base_url", "https://www.parsethis.ai")).rstrip("/"),
        max_usdc=str(section.get("max_usdc", "0.02")),
        mode=str(section.get("mode", "pattern-only")).strip().lower(),
    )


def _stringify(value: Any, *, max_chars: int = 20000) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except Exception:
            text = str(value)
    if len(text) > max_chars:
        return text[:max_chars]
    return text


def _decoded_candidates(text: str) -> Iterable[str]:
    yield text
    for match in _B64_RE.finditer(text[:50000]):
        token = match.group(1)
        try:
            padded = token + ("=" * ((4 - len(token) % 4) % 4))
            decoded = base64.b64decode(padded, validate=True)
            out = decoded.decode("utf-8", errors="ignore")
        except (binascii.Error, ValueError):
            continue
        if 8 <= len(out) <= 8000:
            yield out
    for match in _HEX_RE.finditer(text[:50000]):
        token = match.group(1)
        if len(token) % 2:
            continue
        try:
            out = bytes.fromhex(token).decode("utf-8", errors="ignore")
        except ValueError:
            continue
        if 8 <= len(out) <= 8000:
            yield out


def _local_decision(text: str) -> dict[str, Any]:
    hits: list[str] = []
    for candidate in _decoded_candidates(text):
        normalized = candidate.replace("\u200b", "").replace("\ufeff", "")
        for pattern in _SUSPICIOUS_PATTERNS:
            if pattern.search(normalized):
                hits.append(pattern.pattern)
                break
    if hits:
        return {
            "recommended_action": "block",
            "risk_score": 10,
            "attack_detected": True,
            "categories": ["prompt_injection", "instruction_smuggling"],
            "local_patterns": hits[:5],
        }
    return {
        "recommended_action": "allow",
        "risk_score": 0,
        "attack_detected": False,
        "categories": [],
    }


def _extract_action(decision: dict[str, Any]) -> str:
    action = decision.get("recommended_action") or decision.get("suggested_action")
    nested = decision.get("decision")
    if isinstance(nested, dict):
        action = nested.get("action", action)
    return str(action or "allow").strip().lower()


def _is_block_decision(decision: dict[str, Any]) -> bool:
    action = _extract_action(decision)
    if action in _SAFE_ACTIONS:
        return False
    if action in _BLOCK_ACTIONS:
        return True
    if bool(decision.get("attack_detected")):
        return True
    try:
        return float(decision.get("risk_score", 0) or 0) >= 7
    except (TypeError, ValueError):
        return True


def _load_env_once() -> None:
    try:
        from hermes_cli.env_loader import load_hermes_dotenv

        load_hermes_dotenv(hermes_home=get_hermes_home())
    except Exception as exc:
        logger.debug("Parse env load skipped: %s", exc)


def _json_request(
    url: str,
    payload: dict[str, Any],
    *,
    settings: ParseScreeningSettings,
    bearer_token: str | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"content-type": "application/json", "accept": "application/json"}
    if bearer_token:
        headers["authorization"] = f"Bearer {bearer_token}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=settings.timeout_seconds) as res:
            text = res.read().decode("utf-8", errors="replace")
            return json.loads(text) if text.strip() else {"recommended_action": "allow"}
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        if exc.code == 402:
            raise
        try:
            detail = json.loads(text) if text.strip() else {}
        except Exception:
            detail = {"body_preview": text[:300]}
        raise RuntimeError(f"Parse HTTP {exc.code}: {detail}") from exc


def _x402_json(url: str, payload: dict[str, Any], *, settings: ParseScreeningSettings) -> dict[str, Any]:
    wrapper = Path(get_hermes_home()) / "x402-client" / "x402-fetch.mjs"
    if not wrapper.exists():
        wrapper = Path.home() / ".hermes" / "x402-client" / "x402-fetch.mjs"
    if not wrapper.exists():
        raise RuntimeError("x402 wrapper not found")

    cmd = [
        "node",
        str(wrapper),
        url,
        "--method",
        "POST",
        "--body",
        json.dumps(payload, ensure_ascii=False),
        "--header",
        "content-type: application/json",
        "--max-usdc",
        str(settings.max_usdc),
        "--yes",
    ]
    env = os.environ.copy()
    env.setdefault("X402_ENV_FILE", str(Path(get_hermes_home()) / "secrets" / "x402.env"))
    proc = subprocess.run(
        cmd,
        cwd=str(wrapper.parent),
        env=env,
        text=True,
        capture_output=True,
        timeout=max(settings.timeout_seconds + 20, 30),
        check=False,
    )
    if proc.returncode != 0:
        # Do not include stderr; the wrapper is designed not to print secrets,
        # but keeping only the exit code preserves that invariant defensively.
        raise RuntimeError(f"x402 wrapper failed with exit code {proc.returncode}")
    text = proc.stdout.strip()
    if not text:
        return {"recommended_action": "allow"}
    try:
        data = json.loads(text)
    except Exception as exc:
        raise RuntimeError("x402 Parse response was not JSON") from exc
    status = data.get("status")
    code = data.get("code")
    if status == "error" or (isinstance(status, int) and status >= 400) or (isinstance(code, int) and code >= 400):
        raise RuntimeError(f"x402 Parse HTTP {code or status}: {data.get('message') or 'error'}")
    return data


def _payload(text: str, *, boundary: str) -> dict[str, Any]:
    # Parse for Agents currently expects `prompt` on /v1/parse and `output` on
    # /v1/screen-output. Keep text/content aliases for forward compatibility,
    # but make the route-native field first-class so paid calls exercise the
    # production API shape rather than relying on compatibility aliases.
    payload = {
        "text": text,
        "content": text,
        "boundary": boundary,
        "source": "hermes-agent",
    }
    if boundary == "output":
        payload["output"] = text
    else:
        payload["prompt"] = text
    return payload


def _live_decision(text: str, *, boundary: str, settings: ParseScreeningSettings) -> dict[str, Any]:
    endpoint = "/v1/screen-output" if boundary == "output" else "/v1/parse"
    url = settings.base_url.rstrip("/") + endpoint
    payload = _payload(text, boundary=boundary)

    _load_env_once()
    token = os.environ.get("PARSE_API_KEY")
    if token and settings.auth in {"auto", "bearer", "api_key", "paid", "live"}:
        try:
            return _json_request(url, payload, settings=settings, bearer_token=token)
        except urllib.error.HTTPError as exc:
            if exc.code != 402 or not settings.x402_enabled:
                raise RuntimeError(f"Parse bearer HTTP {exc.code}") from exc
            logger.info("Parse bearer request returned 402; falling back to x402")

    if not settings.x402_enabled:
        raise RuntimeError("x402 fallback disabled and no usable Parse bearer auth is configured")
    return _x402_json(url, payload, settings=settings)


def _unavailable_decision(reason: str, *, settings: ParseScreeningSettings) -> dict[str, Any]:
    if settings.fail_closed:
        return {
            "recommended_action": "block",
            "risk_score": 8,
            "attack_detected": True,
            "categories": ["parse_unavailable_fail_closed"],
            "reason": reason,
        }
    decision = _local_decision(reason)
    decision.update({"parse_unavailable": True, "recommended_action": "allow"})
    return decision


def _screen_text(text: str, *, boundary: str, settings: ParseScreeningSettings | None = None) -> dict[str, Any]:
    settings = settings or load_settings()
    if not settings.enabled:
        return {"recommended_action": "allow", "disabled": True}
    if not text.strip():
        return {"recommended_action": "allow", "empty": True}

    local = _local_decision(text)
    if _is_block_decision(local):
        return local

    mode = settings.mode
    if mode in _LOCAL_MODES:
        return local
    if mode in _LIVE_MODES:
        try:
            live = _live_decision(text, boundary=boundary, settings=settings)
            if isinstance(live, dict):
                live.setdefault("parse_live", True)
                return live
            return {"recommended_action": "allow", "parse_live": True, "raw": live}
        except Exception as exc:
            logger.warning("Parse live screening unavailable at %s boundary: %s", boundary, exc)
            return _unavailable_decision(str(exc), settings=settings)

    logger.warning("Unknown Parse screening mode %r; using local screening", mode)
    return local


def screen_prompt_text(text: str, *, settings: ParseScreeningSettings | None = None) -> dict[str, Any]:
    return _screen_text(text, boundary="prompt", settings=settings)


def screen_output_text(text: str, *, settings: ParseScreeningSettings | None = None) -> dict[str, Any]:
    return _screen_text(text, boundary="output", settings=settings)


def pre_tool_call_block_message(tool_name: str, args: dict[str, Any] | None, **_: Any) -> dict[str, str] | None:
    settings = load_settings()
    if not (settings.enabled and settings.prompt_enabled):
        return None
    text = _stringify({"tool_name": tool_name, "args": args or {}})
    decision = screen_prompt_text(text, settings=settings)
    if _is_block_decision(decision):
        message = _PARSE_UNAVAILABLE_MESSAGE if "parse_unavailable_fail_closed" in decision.get("categories", []) else _BLOCK_MESSAGE
        return {"action": "block", "message": message}
    return None


def transform_tool_result(tool_name: str, args: dict[str, Any] | None, result: Any, **_: Any) -> str | None:
    settings = load_settings()
    if not (settings.enabled and settings.tool_result_enabled):
        return None
    text = _stringify(result)
    decision = screen_prompt_text(text, settings=settings)
    if _is_block_decision(decision):
        message = _PARSE_UNAVAILABLE_MESSAGE if "parse_unavailable_fail_closed" in decision.get("categories", []) else _BLOCK_MESSAGE
        return json.dumps({"error": message, "parse_screening": "blocked_tool_result"}, ensure_ascii=False)
    return None


def should_suppress_streaming() -> bool:
    settings = load_settings()
    return bool(settings.enabled and settings.output_enabled)


def screen_final_response(response_text: str, **_: Any) -> str | None:
    settings = load_settings()
    if not (settings.enabled and settings.output_enabled):
        return None
    decision = screen_output_text(response_text or "", settings=settings)
    if _is_block_decision(decision):
        if "parse_unavailable_fail_closed" in decision.get("categories", []):
            return _PARSE_UNAVAILABLE_MESSAGE
        return _BLOCK_MESSAGE
    return None


def x402_credentials_present() -> bool:
    env_file = Path(os.environ.get("X402_ENV_FILE") or Path(get_hermes_home()) / "secrets" / "x402.env")
    if not env_file.exists():
        return False
    try:
        for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("EVM_PRIVATE_KEY=") and line.split("=", 1)[1].strip():
                return True
    except Exception:
        return False
    return False


def status_summary() -> dict[str, Any]:
    settings = load_settings()
    _load_env_once()
    return {
        "enabled": settings.enabled,
        "mode": settings.mode,
        "prompt_enabled": settings.prompt_enabled,
        "tool_result_enabled": settings.tool_result_enabled,
        "output_enabled": settings.output_enabled,
        "fail_closed": settings.fail_closed,
        "base_url": settings.base_url,
        "auth": settings.auth,
        "x402_enabled": settings.x402_enabled,
        "x402_credentials_present": x402_credentials_present(),
        "parse_api_key_present": bool(os.environ.get("PARSE_API_KEY")),
        "max_usdc": settings.max_usdc,
        "timeout_seconds": settings.timeout_seconds,
        "streaming_suppressed": should_suppress_streaming(),
    }
