"""Tool result compaction — LLM-free truncation + local storage for cost reduction.

This module keeps large text tool results out of the conversation history by
saving the full result to local disk and returning a compact JSON reference.
The feature is disabled by default and fails open on any error.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Config defaults (overridable via config.yaml -> tool_result_compaction.*)
DEFAULT_ENABLED = False
DEFAULT_THRESHOLD_TOKENS = 5000
DEFAULT_RAW_RESULT_DIR = ""  # empty = ~/.hermes/raw_results/
DEFAULT_MAX_DISK_MB = 500
DEFAULT_PREVIEW_CHARS = 1000

_TOKEN_CHARS = 4
_SAFE_COMPONENT_RE = re.compile(r"[^a-zA-Z0-9_.-]+")
_BYTES_PER_MB = 1024 * 1024


def get_config() -> dict:
    """Read tool_result_compaction config section, with safe defaults.

    Tests MUST monkeypatch this function rather than relying on the
    real ~/.hermes/config.yaml.
    """
    try:
        from hermes_cli.config import read_raw_config

        cfg = read_raw_config().get("tool_result_compaction", {})
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        logger.debug("Could not read tool_result_compaction config", exc_info=True)
        return {}


def _config_bool(cfg: dict, key: str, default: bool) -> bool:
    value = cfg.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _config_int(cfg: dict, key: str, default: int, *, minimum: int = 0) -> int:
    value = cfg.get(key, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, parsed)


def is_enabled() -> bool:
    """Return True if compaction is enabled in config."""
    return _config_bool(get_config(), "enabled", DEFAULT_ENABLED)


def token_estimate(content: str) -> int:
    """Estimate token count with a dependency-free chars/4 heuristic."""
    return max(1, len(content) // _TOKEN_CHARS) if content else 0


def sanitize_path_component(value: str, *, fallback: str = "unknown") -> str:
    """Return a filesystem-safe path component."""
    cleaned = _SAFE_COMPONENT_RE.sub("_", value).strip("._-")
    return cleaned or fallback


def default_raw_result_dir() -> Path:
    """Return the default raw result storage directory."""
    return Path.home() / ".hermes" / "raw_results"


def resolve_raw_result_dir(cfg: dict) -> Path:
    """Return configured raw result dir, expanding user/env vars."""
    raw_dir = cfg.get("raw_result_dir", DEFAULT_RAW_RESULT_DIR)
    if not isinstance(raw_dir, str) or not raw_dir.strip():
        return default_raw_result_dir()
    return Path(os.path.expandvars(os.path.expanduser(raw_dir)))


def _first_last_preview(content: str, preview_chars: int) -> str:
    """Return a compact first+last preview of content."""
    if preview_chars <= 0:
        return ""
    if len(content) <= preview_chars * 2:
        return content
    omitted = len(content) - (preview_chars * 2)
    return (
        content[:preview_chars]
        + f"\n\n... [omitted {omitted} chars] ...\n\n"
        + content[-preview_chars:]
    )


def _raw_result_path(
    base_dir: Path,
    session_id: str,
    tool_call_id: str,
    tool_name: str,
) -> Path:
    session_component = sanitize_path_component(session_id, fallback="session")
    call_component = sanitize_path_component(tool_call_id, fallback="call")
    tool_component = sanitize_path_component(tool_name, fallback="tool")
    timestamp_ns = time.time_ns()
    filename = f"{call_component}_{tool_component}_{timestamp_ns}.json"
    return base_dir / session_component / filename


def _write_raw_result(path: Path, payload: dict[str, Any]) -> None:
    """Write raw result payload with private filesystem permissions."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        logger.debug("Could not chmod raw result directory", exc_info=True)

    encoded = json.dumps(payload, ensure_ascii=True, indent=2)
    with path.open("w", encoding="utf-8") as fh:
        fh.write(encoded)
    try:
        os.chmod(path, 0o600)
    except OSError:
        logger.debug("Could not chmod raw result file", exc_info=True)


def _iter_raw_result_files(base_dir: Path) -> list[Path]:
    if not base_dir.exists():
        return []
    return [path for path in base_dir.rglob("*.json") if path.is_file() and not path.is_symlink()]


def _directory_size_bytes(base_dir: Path) -> int:
    total = 0
    for path in _iter_raw_result_files(base_dir):
        try:
            total += path.stat().st_size
        except OSError:
            logger.debug("Could not stat raw result file", exc_info=True)
    return total


def _cleanup_empty_dirs(base_dir: Path) -> None:
    if not base_dir.exists():
        return
    for path in sorted(base_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass


def _safe_mtime(path: Path) -> float:
    """Return st_mtime or 0.0 if stat fails (e.g. race with deletion)."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _enforce_disk_quota(
    base_dir: Path,
    max_disk_mb: int,
    *,
    protected_path: Path | None = None,
) -> None:
    """Delete oldest raw result files until usage is under 80% of quota.

    A non-positive max_disk_mb disables quota cleanup. protected_path is never
    deleted, so the compacted message for the current tool result cannot point
    at a file that was immediately removed by cleanup.
    """
    if max_disk_mb <= 0 or not base_dir.exists():
        return

    max_bytes = max_disk_mb * _BYTES_PER_MB
    target_bytes = int(max_bytes * 0.8)
    current_bytes = _directory_size_bytes(base_dir)
    if current_bytes <= max_bytes:
        return

    protected_resolved = None
    if protected_path is not None:
        try:
            protected_resolved = protected_path.resolve()
        except OSError:
            protected_resolved = protected_path

    files = sorted(
        _iter_raw_result_files(base_dir),
        key=lambda path: _safe_mtime(path),
    )
    for path in files:
        if current_bytes <= target_bytes:
            break
        try:
            candidate = path.resolve()
        except OSError:
            candidate = path
        if protected_resolved is not None and candidate == protected_resolved:
            continue
        try:
            size = path.stat().st_size
            path.unlink()
            current_bytes -= size
        except OSError:
            logger.debug("Could not remove old raw result file", exc_info=True)

    _cleanup_empty_dirs(base_dir)


def compact_tool_content_if_needed(
    tool_name: str,
    tool_call_id: str,
    content: str,
    agent: Any,
) -> tuple[str, dict[str, Any] | None]:
    """Compact large tool result content when enabled.

    If enabled and the text content exceeds threshold_tokens, the full result is
    saved to disk and the returned content becomes a compact JSON reference.

    FAIL-OPEN: Any exception returns the original content unchanged.
    """
    try:
        cfg = get_config()
        if not _config_bool(cfg, "enabled", DEFAULT_ENABLED):
            return content, None

        threshold_tokens = _config_int(
            cfg,
            "threshold_tokens",
            DEFAULT_THRESHOLD_TOKENS,
            minimum=1,
        )
        original_token_estimate = token_estimate(content)
        if original_token_estimate < threshold_tokens:
            return content, None

        preview_chars = _config_int(
            cfg,
            "preview_chars",
            DEFAULT_PREVIEW_CHARS,
            minimum=0,
        )
        max_disk_mb = _config_int(
            cfg,
            "max_disk_mb",
            DEFAULT_MAX_DISK_MB,
            minimum=0,
        )
        session_id = str(getattr(agent, "session_id", "session"))
        base_dir = resolve_raw_result_dir(cfg)
        raw_path = _raw_result_path(base_dir, session_id, tool_call_id, tool_name)

        raw_payload: dict[str, Any] = {
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "session_id": session_id,
            "created_at_unix_ns": time.time_ns(),
            "original_char_count": len(content),
            "original_token_estimate": original_token_estimate,
            "content": content,
        }
        _write_raw_result(raw_path, raw_payload)
        _enforce_disk_quota(base_dir, max_disk_mb, protected_path=raw_path)

        compacted_preview = _first_last_preview(content, preview_chars)
        compacted_payload: dict[str, Any] = {
            "type": "compacted_tool_result",
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "original_char_count": len(content),
            "original_token_estimate": original_token_estimate,
            "compacted_preview": compacted_preview,
            "raw_result_path": str(raw_path),
            "note": (
                "Full tool result saved locally as JSON. "
                "Use read_file on raw_result_path and inspect the content field "
                "if exact output is needed."
            ),
        }
        compacted_content = json.dumps(compacted_payload, ensure_ascii=True, indent=2)
        info = {
            "raw_result_path": str(raw_path),
            "original_chars": len(content),
            "original_token_estimate": original_token_estimate,
            "compacted_chars": len(compacted_content),
            "compacted_token_estimate": token_estimate(compacted_content),
        }
        return compacted_content, info
    except Exception:
        logger.debug("Tool result compaction failed; returning original content", exc_info=True)
        return content, None
