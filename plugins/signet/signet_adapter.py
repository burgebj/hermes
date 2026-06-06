"""Optional Signet adapter.

Upgrades ``HashChainSigner`` with Ed25519 signatures per receipt and
bilateral attestation support, using the local-first ``signet-auth``
package. The package is imported lazily so the plugin works without it.

Install::

    pip install signet-auth
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

from .audit_signer import (
    AuditEvent,
    AuditSigner,
    _now_iso_utc,
    canonical_json,
    sha256_hex,
)

logger = logging.getLogger(__name__)


class SignetUnavailable(RuntimeError):
    """Raised when ``signet-auth`` is not installed."""


def _load_signet():
    try:
        import signet_auth  # noqa: F401
        from signet_auth import (  # type: ignore
            Action,
            audit_append,
            audit_verify_chain,
            generate_and_save,
            load_signing_key,
            sign,
        )
    except ImportError as e:
        raise SignetUnavailable(
            "signet-auth is not installed. Install with `pip install signet-auth` "
            "or fall back to the default HashChainSigner."
        ) from e
    return {
        "Action": Action,
        "audit_append": audit_append,
        "audit_verify_chain": audit_verify_chain,
        "generate_and_save": generate_and_save,
        "load_signing_key": load_signing_key,
        "sign": sign,
    }


class SignetSigner(AuditSigner):
    """Ed25519-signed audit entries via the Signet Rust core.

    Each tool call becomes a Signet ``Receipt`` (Ed25519-signed,
    canonicalized via RFC 8785 JCS by the Rust core) and is appended to
    Signet's own hash-chained audit store. ``verify()`` walks the store
    using Signet's verifier.

    Key custody lives with Signet: keys are stored under ``dir`` (default
    ``$HERMES_HOME/signet/keys/``) and Hermes never sees raw key bytes —
    only the secret-key handle returned by ``load_signing_key``.
    """

    def __init__(
        self,
        dir: Path,
        key_name: str = "hermes-agent",
        owner: Optional[str] = None,
        passphrase: Optional[str] = None,
    ):
        self._api = _load_signet()
        self._dir = Path(dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._key_name = key_name
        self._lock = threading.Lock()
        try:
            self._secret_key = self._api["load_signing_key"](
                str(self._dir), key_name, passphrase
            )
        except Exception:
            self._api["generate_and_save"](
                str(self._dir), key_name, owner, passphrase
            )
            self._secret_key = self._api["load_signing_key"](
                str(self._dir), key_name, passphrase
            )
        logger.info(
            "Signet signer initialized (dir=%s, key=%s)", self._dir, key_name
        )

    def append(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        session_id: str,
        task_id: str,
        tool_call_id: str,
    ) -> AuditEvent:
        args_dict = args if isinstance(args, dict) else {"_raw": str(args)}
        result_str = result if isinstance(result, str) else canonical_json(result)
        action = self._api["Action"](
            tool=tool_name,
            params={
                "args": args_dict,
                "result_digest": sha256_hex(result_str),
                "session_id": session_id or "",
                "task_id": task_id or "",
                "tool_call_id": tool_call_id or "",
            },
            target=tool_name,
        )
        with self._lock:
            receipt = self._api["sign"](
                self._secret_key, action, self._key_name, None
            )
            record = self._api["audit_append"](str(self._dir), receipt)
        # Signet's ``AuditRecord`` exposes ``prev_hash``, ``receipt``,
        # ``record_hash`` — no sequence/timestamp of its own (the
        # timestamp lives inside the Receipt). We synthesize a local
        # sequence and timestamp for the common ``AuditEvent`` shape.
        prev_hash = getattr(record, "prev_hash", "") or ""
        record_hash = getattr(record, "record_hash", "") or ""
        seq = self._next_sequence()
        return AuditEvent(
            sequence=seq,
            timestamp=_now_iso_utc(),
            session_id=session_id or "",
            task_id=task_id or "",
            tool_name=tool_name,
            tool_call_id=tool_call_id or "",
            args_digest=sha256_hex(canonical_json(args_dict)),
            result_digest=sha256_hex(result_str),
            prev_hash=str(prev_hash),
            hash=str(record_hash),
        )

    def _next_sequence(self) -> int:
        """Local monotonic counter (Signet owns chain hashing, not sequence)."""
        seq = getattr(self, "_seq", 0)
        self._seq = seq + 1
        return seq

    def verify(self) -> Tuple[bool, int, Optional[str]]:
        status = self._api["audit_verify_chain"](str(self._dir))
        ok = bool(getattr(status, "valid", False))
        count = int(getattr(status, "total_records", 0) or 0)
        if ok:
            return True, count, None
        bp = getattr(status, "break_point", None)
        err = f"chain break at record {bp}" if bp is not None else "chain verification failed"
        return False, count, err

    def iter_events(self) -> Iterator[AuditEvent]:
        chain_path = self._dir / "audit.jsonl"
        if not chain_path.exists():
            return
        with chain_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                yield AuditEvent(
                    sequence=int(entry.get("sequence", 0)),
                    timestamp=str(entry.get("timestamp", "")),
                    session_id=str(entry.get("session_id", "")),
                    task_id=str(entry.get("task_id", "")),
                    tool_name=str(entry.get("tool_name", entry.get("action", {}).get("tool", ""))),
                    tool_call_id=str(entry.get("tool_call_id", "")),
                    args_digest=str(entry.get("args_digest", "")),
                    result_digest=str(entry.get("result_digest", "")),
                    prev_hash=str(entry.get("prev_hash", "")),
                    hash=str(entry.get("hash", "")),
                )


