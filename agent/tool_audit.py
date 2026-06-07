"""Tool-Execution-Audit Middleware fuer Hermes.

Schreibt Tool-Calls VOR Execution in ~/.hermes/audit_logs/ via externes
audit-logger.sh Skript (siehe Memory: reference_audit_logger_2026_05_22).

Architektur-Vertrag:
- **Fail-Soft im Workflow:** Logger-Fehler blockt Tool-Execution NIE.
- **Fail-Hard im Log:** entweder vollstaendige Zeile oder gar nichts (Skript-Seite).
- **Singleton via Modul-Cache:** ein Pfad-Check beim ersten Call.
- **Secret-Redaction:** Werte sensibler Keys werden vor Serialisierung redacted.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_LOGGER_PATH = Path.home() / ".hermes" / "audit_logs" / "audit-logger.sh"
_TIMEOUT_SECONDS = 2.0
_REDACTED = "<redacted>"

# Sensible Schluessel: substring case-insensitive Match.
# Trade-off: "monkey_var" wuerde "key" matchen → redact. Lieber zu viel als zu wenig.
_SECRET_KEY_PATTERN = re.compile(
    r"(?i)(key|token|secret|password|auth|pwd)"
)


def _redact_secrets(obj: Any) -> Any:
    """Rekursive Redaction: Werte von Keys mit sensiblem Namen → <redacted>.

    Walks dict/list/scalar. Andere Container (set/tuple/...) bleiben unangetastet,
    werden aber durchgereicht (Best-Effort). Keys werden gegen
    _SECRET_KEY_PATTERN gematcht (case-insensitive, substring).
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(k, str) and _SECRET_KEY_PATTERN.search(k):
                out[k] = _REDACTED
            else:
                out[k] = _redact_secrets(v)
        return out
    if isinstance(obj, list):
        return [_redact_secrets(item) for item in obj]
    return obj


class ToolExecutionAudit:
    """Middleware fuer Tool-Call-Audit via externes POSIX-Skript."""

    def __init__(
        self,
        logger_path: Optional[Path] = None,
        timeout: float = _TIMEOUT_SECONDS,
    ):
        self.logger_path = logger_path or _DEFAULT_LOGGER_PATH
        self.timeout = timeout
        self._enabled = self._check_enabled()

    def _check_enabled(self) -> bool:
        """Audit nur aktiv wenn Skript existiert UND ausfuehrbar ist."""
        if not self.logger_path.exists():
            logger.warning(
                "ToolExecutionAudit disabled: %s nicht gefunden",
                self.logger_path,
            )
            return False
        if not os.access(self.logger_path, os.X_OK):
            logger.warning(
                "ToolExecutionAudit disabled: %s nicht ausfuehrbar",
                self.logger_path,
            )
            return False
        return True

    def audit(
        self,
        agent_id: str,
        tool_name: str,
        args: Dict[str, Any],
    ) -> None:
        """Logge Tool-Call. Fail-Soft: blockt Tool-Execution nie.

        Args:
            agent_id: Agent-Identifier (z.B. agent.session_id).
            tool_name: Tool-Funktion-Name.
            args: Tool-Argumente. Sensible Werte werden vorher redacted.
        """
        if not self._enabled:
            return

        # Redact BEFORE serialize — Secrets nie in JSON oder Log
        try:
            safe_args = _redact_secrets(args) if isinstance(args, dict) else args
        except Exception as e:  # Defensive — Redact darf nie blockieren
            logger.error("ToolExecutionAudit redact failed: %s", e)
            safe_args = {"_redact_error": str(e)}

        try:
            payload = json.dumps(
                {"agent_id": agent_id, "tool": tool_name, "args": safe_args},
                separators=(",", ":"),
                ensure_ascii=False,
                default=str,  # nicht-serialisierbare Objekte → str-Fallback
            )
        except (TypeError, ValueError) as e:
            logger.error("ToolExecutionAudit payload-encode failed: %s", e)
            return

        try:
            result = subprocess.run(
                [str(self.logger_path)],
                input=payload,
                text=True,
                capture_output=True,
                timeout=self.timeout,
            )
            if result.returncode != 0:
                logger.error(
                    "ToolExecutionAudit logger rc=%d stderr=%s",
                    result.returncode,
                    result.stderr.strip()[:200],
                )
        except subprocess.TimeoutExpired:
            logger.error(
                "ToolExecutionAudit logger timeout (%.1fs)", self.timeout
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error("ToolExecutionAudit logger spawn failed: %s", e)
        except Exception as e:  # Defensive: NIE durchschlagen lassen
            logger.error("ToolExecutionAudit unexpected error: %s", e)


_singleton: Optional[ToolExecutionAudit] = None


def get_audit() -> ToolExecutionAudit:
    """Lazy-Singleton fuer Modul-weiten Audit-Zugriff."""
    global _singleton
    if _singleton is None:
        _singleton = ToolExecutionAudit()
    return _singleton
