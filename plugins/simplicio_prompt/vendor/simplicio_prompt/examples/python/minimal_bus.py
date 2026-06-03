"""
Minimal Linda-style tuple-space bus. See YOOL_TUPLE_HAMT.md §2.4.

Implements `out`, `in_`, `rd`, `eval_` primitives. Single-process reference
impl; multi-process variant swaps the dict for SQLite or Redis.

Pattern matching is by predicate (callable on tuple dict). For production,
prefer indexed lookup by (lane, yool) — see spec §7.
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


Predicate = Callable[[dict[str, Any]], bool]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TupleSpace:
    def __init__(self, log_path: str | Path | None = None, workers: int = 4):
        self._tuples: dict[str, dict[str, Any]] = {}
        self._cond = threading.Condition()
        self._log = Path(log_path).expanduser() if log_path else None
        if self._log:
            self._log.parent.mkdir(parents=True, exist_ok=True)
        self._pool = ThreadPoolExecutor(max_workers=workers)

    def _persist(self, op: str, tup: dict[str, Any]) -> None:
        if not self._log:
            return
        line = json.dumps({"op": op, "at": _now_iso(), "tuple": tup}, ensure_ascii=False)
        with self._log.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def out(self, tup: dict[str, Any]) -> str:
        """Place a tuple into the space. Returns tuple id."""
        tid = tup.get("id") or f"t-{uuid.uuid4().hex[:12]}"
        tup = {**tup, "id": tid, "created_at": tup.get("created_at") or _now_iso()}
        with self._cond:
            self._tuples[tid] = tup
            self._persist("out", tup)
            self._cond.notify_all()
        return tid

    def rd(self, pred: Predicate, timeout: float | None = None) -> dict[str, Any] | None:
        """Non-destructive read. Blocks until a matching tuple appears or timeout."""
        deadline = (time.monotonic() + timeout) if timeout is not None else None
        with self._cond:
            while True:
                for tup in self._tuples.values():
                    if pred(tup):
                        return dict(tup)
                if deadline is None:
                    self._cond.wait()
                else:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return None
                    self._cond.wait(timeout=remaining)

    def in_(self, pred: Predicate, timeout: float | None = None) -> dict[str, Any] | None:
        """Destructive take. Removes the first matching tuple from the space."""
        deadline = (time.monotonic() + timeout) if timeout is not None else None
        with self._cond:
            while True:
                for tid, tup in list(self._tuples.items()):
                    if pred(tup):
                        del self._tuples[tid]
                        self._persist("in", tup)
                        return dict(tup)
                if deadline is None:
                    self._cond.wait()
                else:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return None
                    self._cond.wait(timeout=remaining)

    def eval_(self, fn: Callable[[], dict[str, Any]]) -> Future:
        """Run fn() asynchronously; resulting tuple is placed in the space."""
        def _runner() -> dict[str, Any]:
            result = fn()
            self.out(result)
            return result
        return self._pool.submit(_runner)

    def all(self) -> list[dict[str, Any]]:
        with self._cond:
            return [dict(t) for t in self._tuples.values()]

    def shutdown(self) -> None:
        self._pool.shutdown(wait=True)


def by_yool(yool: str) -> Predicate:
    return lambda t: t.get("yool") == yool


def by_lane(lane: str) -> Predicate:
    return lambda t: t.get("lane") == lane


if __name__ == "__main__":
    bus = TupleSpace(log_path=".catalog/tuples.jsonl")

    bus.out({"yool": "ide.cursor.send", "args": {"file": "x.py"}, "lane": "dev"})
    bus.out({"yool": "op.jira.fetch_sprint", "args": {"sprint": 42}, "lane": "ops"})

    def worker_dev() -> None:
        while True:
            t = bus.in_(by_lane("dev"), timeout=1.0)
            if t is None:
                return
            print(f"[dev] processing {t['yool']} args={t['args']}")
            bus.out({
                "yool": "receipt",
                "lane": "audit",
                "parent_id": t["id"],
                "status": "ok",
            })

    worker_dev()
    print("final state:", bus.all())
    bus.shutdown()
