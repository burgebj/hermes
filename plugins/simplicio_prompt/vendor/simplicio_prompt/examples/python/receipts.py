"""
Content-addressable receipt store. See YOOL_TUPLE_HAMT.md §2.5, §4.3.

A receipt is the immutable record of a single yool execution: inputs (hashed),
outputs (referenced by sha256), timing, status. The receipt's own sha256 over
its canonical JSON acts as both ID and cache key.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def input_hash(
    yool: str,
    args: dict[str, Any],
    file_shas: list[str] | None = None,
    env_whitelist: dict[str, str] | None = None,
) -> str:
    """Cache key. See spec §4.3."""
    payload = {
        "yool": yool,
        "args": args,
        "files": sorted(file_shas or []),
        "env": dict(sorted((env_whitelist or {}).items())),
    }
    return sha256_text(canonical_json(payload))


@dataclass
class Artifact:
    path: str
    sha256: str
    size_bytes: int
    mime: str = "application/octet-stream"


@dataclass
class Receipt:
    id: str
    yool: str
    input_hash: str
    args: dict[str, Any]
    status: str
    started_at: str
    ended_at: str
    duration_ms: int
    artifacts: list[Artifact] = field(default_factory=list)
    error: str | None = None
    parent_id: str | None = None
    cpu_quota_pct: int = 100
    artifacts_purged_at: str | None = None

    def to_canonical(self) -> str:
        d = asdict(self)
        d.pop("id", None)
        return canonical_json(d)


class ReceiptStore:
    """Stores receipts as .catalog/receipts/<sha>.json. Lookup by input_hash via index."""

    def __init__(self, base_dir: str | Path):
        self.base = Path(base_dir).expanduser()
        self.receipts_dir = self.base / "receipts"
        self.index_path = self.base / "receipts.index.json"
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, str] = {}
        if self.index_path.exists():
            try:
                self._index = json.loads(self.index_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self._index = {}

    def get_by_input_hash(self, ih: str) -> Receipt | None:
        rid = self._index.get(ih)
        if not rid:
            return None
        return self.load(rid)

    def load(self, receipt_id: str) -> Receipt | None:
        p = self.receipts_dir / f"{receipt_id}.json"
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        arts = [Artifact(**a) for a in data.pop("artifacts", [])]
        return Receipt(artifacts=arts, **data)

    def put(self, r: Receipt) -> str:
        if not r.id:
            r.id = sha256_text(r.to_canonical())
        path = self.receipts_dir / f"{r.id}.json"
        data = asdict(r)
        path.write_text(canonical_json(data), encoding="utf-8")
        self._index[r.input_hash] = r.id
        tmp = self.index_path.with_suffix(".json.tmp")
        tmp.write_text(canonical_json(self._index), encoding="utf-8")
        os.replace(tmp, self.index_path)
        return r.id


def make_receipt(
    yool: str,
    args: dict[str, Any],
    status: str,
    started: datetime,
    ended: datetime,
    artifacts: list[Artifact] | None = None,
    error: str | None = None,
    parent_id: str | None = None,
    file_shas: list[str] | None = None,
    env_whitelist: dict[str, str] | None = None,
    cpu_quota_pct: int = 100,
) -> Receipt:
    ih = input_hash(yool, args, file_shas, env_whitelist)
    r = Receipt(
        id="",
        yool=yool,
        input_hash=ih,
        args=args,
        status=status,
        started_at=started.astimezone(timezone.utc).isoformat(),
        ended_at=ended.astimezone(timezone.utc).isoformat(),
        duration_ms=int((ended - started).total_seconds() * 1000),
        artifacts=list(artifacts or []),
        error=error,
        parent_id=parent_id,
        cpu_quota_pct=cpu_quota_pct,
    )
    r.id = sha256_text(r.to_canonical())
    return r
