"""Audit signer ABC and the default stdlib-only ``HashChainSigner``.

Every entry is bound to its predecessor via SHA-256, so any truncation or
in-place edit of the JSONL file is detectable by ``verify()``. No external
dependencies — ``HashChainSigner`` is the default shipped with the plugin
and directly implements the design described in #487 (inspired by OpenFang).

Stronger guarantees (Ed25519 signatures, bilateral attestations, offline
verification CLI) are provided by ``SignetSigner`` in ``signet_adapter``,
which lazily imports the optional ``signet`` package.
"""

from __future__ import annotations

import hashlib
import json
import threading
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple


GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class AuditEvent:
    """One signed entry in the tool-call audit chain."""

    sequence: int
    timestamp: str
    session_id: str
    task_id: str
    tool_name: str
    tool_call_id: str
    args_digest: str
    result_digest: str
    prev_hash: str
    hash: str


def canonical_json(obj: Any) -> str:
    """Deterministic JSON for hashing.

    Sorted keys, tightest separators, non-ASCII preserved. Not strictly
    RFC 8785 JCS; ``SignetSigner`` upgrades to JCS when the ``signet``
    package is available.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _now_iso_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


class AuditSigner(ABC):
    """Pluggable audit sink.

    Implementations append a signed ``AuditEvent`` per tool call and
    provide chain verification. The default ``HashChainSigner`` uses
    SHA-256 hash chaining; ``SignetSigner`` adds Ed25519 signatures.
    """

    @abstractmethod
    def append(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        session_id: str,
        task_id: str,
        tool_call_id: str,
    ) -> AuditEvent:
        """Record one tool call and return the signed event."""

    @abstractmethod
    def verify(self) -> Tuple[bool, int, Optional[str]]:
        """Walk the chain.

        Returns ``(ok, verified_count, error)``. ``error`` is ``None`` on
        success; otherwise a human-readable first-failure description.
        """

    @abstractmethod
    def iter_events(self) -> Iterator[AuditEvent]:
        """Yield events in chain order."""

    def close(self) -> None:
        """Release any open resources. Default no-op."""


class HashChainSigner(AuditSigner):
    """SHA-256 hash-chained audit log, one JSONL entry per tool call.

    No signatures — only sequence integrity. An operator with write
    access can rewrite the chain from any point forward (see #487
    discussion). For non-repudiable authorship use ``SignetSigner``,
    which adds Ed25519.
    """

    def __init__(self, path: Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._seq, self._prev_hash = self._load_tail()

    def _load_tail(self) -> Tuple[int, str]:
        if not self._path.exists():
            return 0, GENESIS_HASH
        last_valid: Optional[dict] = None
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    last_valid = json.loads(line)
                except json.JSONDecodeError:
                    continue
        if not last_valid:
            return 0, GENESIS_HASH
        return int(last_valid["sequence"]) + 1, str(last_valid["hash"])

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
        with self._lock:
            body = {
                "sequence": self._seq,
                "timestamp": _now_iso_utc(),
                "session_id": session_id or "",
                "task_id": task_id or "",
                "tool_name": tool_name,
                "tool_call_id": tool_call_id or "",
                "args_digest": sha256_hex(canonical_json(args_dict)),
                "result_digest": sha256_hex(result_str),
                "prev_hash": self._prev_hash,
            }
            h = sha256_hex(canonical_json(body))
            body["hash"] = h
            event = AuditEvent(**body)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event), separators=(",", ":"), ensure_ascii=False))
                f.write("\n")
            self._seq += 1
            self._prev_hash = h
            return event

    def verify(self) -> Tuple[bool, int, Optional[str]]:
        if not self._path.exists():
            return True, 0, None
        expected_seq = 0
        expected_prev = GENESIS_HASH
        count = 0
        with self._path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as e:
                    return False, count, f"line {lineno}: invalid JSON ({e})"
                if entry.get("sequence") != expected_seq:
                    return (
                        False,
                        count,
                        f"line {lineno}: sequence {entry.get('sequence')} != expected {expected_seq}",
                    )
                if entry.get("prev_hash") != expected_prev:
                    return (
                        False,
                        count,
                        f"line {lineno}: prev_hash mismatch (chain broken)",
                    )
                body = {k: entry[k] for k in entry if k != "hash"}
                recomputed = sha256_hex(canonical_json(body))
                if recomputed != entry.get("hash"):
                    return (
                        False,
                        count,
                        f"line {lineno}: hash mismatch (entry tampered)",
                    )
                expected_seq += 1
                expected_prev = entry["hash"]
                count += 1
        return True, count, None

    def iter_events(self) -> Iterator[AuditEvent]:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                yield AuditEvent(
                    sequence=entry["sequence"],
                    timestamp=entry["timestamp"],
                    session_id=entry.get("session_id", ""),
                    task_id=entry.get("task_id", ""),
                    tool_name=entry["tool_name"],
                    tool_call_id=entry.get("tool_call_id", ""),
                    args_digest=entry["args_digest"],
                    result_digest=entry["result_digest"],
                    prev_hash=entry["prev_hash"],
                    hash=entry["hash"],
                )

    @property
    def path(self) -> Path:
        return self._path
