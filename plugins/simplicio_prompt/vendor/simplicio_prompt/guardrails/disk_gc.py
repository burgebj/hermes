"""
Disk garbage collector. See YOOL_TUPLE_HAMT.md §11.2.

Three-tier retention: hot (default 30d) keeps artifact bodies + receipts;
warm (default 365d) keeps receipts only; cold keeps receipts forever
(Merkle chain integrity). Receipts are NEVER deleted, only artifact bodies.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


class DiskPressure(RuntimeError):
    pass


def _du_mb(path: Path) -> float:
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total / (1024 * 1024)


def _parse_iso(ts: str) -> float:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return 0.0


def _purge_artifact_bodies(receipt_path: Path, dry_run: bool) -> tuple[int, int]:
    """Delete artifact files referenced by receipt. Mark receipt as purged.
    Returns (files_deleted, bytes_freed)."""
    try:
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0, 0
    if data.get("artifacts_purged_at"):
        return 0, 0
    deleted = 0
    freed = 0
    for art in data.get("artifacts", []):
        p = Path(art.get("path", ""))
        if not p.is_absolute():
            p = receipt_path.parent.parent / p
        if p.exists() and p.is_file():
            try:
                sz = p.stat().st_size
                if not dry_run:
                    p.unlink()
                deleted += 1
                freed += sz
            except OSError:
                pass
    if deleted and not dry_run:
        data["artifacts_purged_at"] = datetime.now(timezone.utc).isoformat()
        try:
            receipt_path.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass
    return deleted, freed


def _find_oldest_artifact(receipts_dir: Path) -> Path | None:
    oldest_ts = float("inf")
    oldest: Path | None = None
    for rp in receipts_dir.glob("*.json"):
        try:
            data = json.loads(rp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("artifacts_purged_at"):
            continue
        if not data.get("artifacts"):
            continue
        ts = _parse_iso(data.get("ended_at", ""))
        if ts and ts < oldest_ts:
            oldest_ts = ts
            oldest = rp
    return oldest


def _rotate_daily(tuples_log: Path, dry_run: bool) -> bool:
    """Rotate tuples.jsonl daily, gzip yesterday's."""
    if not tuples_log.exists():
        return False
    mtime = tuples_log.stat().st_mtime
    age_days = (time.time() - mtime) / 86400
    if age_days < 1.0:
        return False
    stamp = datetime.fromtimestamp(mtime, timezone.utc).strftime("%Y%m%d")
    rotated = tuples_log.with_name(f"tuples-{stamp}.jsonl.gz")
    if rotated.exists():
        return False
    if dry_run:
        return True
    with tuples_log.open("rb") as src, gzip.open(rotated, "wb") as dst:
        shutil.copyfileobj(src, dst)
    tuples_log.write_bytes(b"")
    return True


def gc_run(
    catalog_dir: str | Path,
    hot_days: int = 30,
    warm_days: int = 365,
    max_total_mb: int = 5000,
    dry_run: bool = False,
) -> dict:
    """Run garbage collection over a .catalog directory.

    Phase 1: purge artifact bodies for receipts older than hot_days.
    Phase 2: enforce size cap by purging oldest artifacts until under max_total_mb.
    Phase 3: rotate tuples.jsonl daily, gzip yesterday's.
    """
    base = Path(catalog_dir).expanduser()
    receipts_dir = base / "receipts"
    tuples_log = base / "tuples.jsonl"

    stats = {
        "phase1_purged_files": 0,
        "phase1_freed_mb": 0.0,
        "phase2_purged_files": 0,
        "phase2_freed_mb": 0.0,
        "rotated": False,
        "size_before_mb": 0.0,
        "size_after_mb": 0.0,
        "dry_run": dry_run,
    }
    if not base.exists():
        return stats

    stats["size_before_mb"] = _du_mb(base)
    now = time.time()
    hot_cutoff = now - hot_days * 86400
    _warm_cutoff = now - warm_days * 86400

    if receipts_dir.exists():
        for rp in receipts_dir.glob("*.json"):
            try:
                data = json.loads(rp.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            ts = _parse_iso(data.get("ended_at", ""))
            if ts and ts < hot_cutoff and not data.get("artifacts_purged_at"):
                d, freed = _purge_artifact_bodies(rp, dry_run)
                stats["phase1_purged_files"] += d
                stats["phase1_freed_mb"] += freed / (1024 * 1024)

    current_mb = _du_mb(base)
    while current_mb > max_total_mb and receipts_dir.exists():
        target = _find_oldest_artifact(receipts_dir)
        if target is None:
            break
        d, freed = _purge_artifact_bodies(target, dry_run)
        if d == 0:
            break
        stats["phase2_purged_files"] += d
        stats["phase2_freed_mb"] += freed / (1024 * 1024)
        current_mb = _du_mb(base)

    stats["rotated"] = _rotate_daily(tuples_log, dry_run)
    stats["size_after_mb"] = _du_mb(base)
    return stats


def check_disk_pressure(catalog_dir: str | Path, free_mb_floor: int = 1000) -> None:
    """Raise DiskPressure if free space on catalog_dir's filesystem drops below floor."""
    base = Path(catalog_dir).expanduser()
    try:
        usage = shutil.disk_usage(base if base.exists() else base.parent)
    except OSError as e:
        raise DiskPressure(f"cannot stat {base}: {e}") from e
    free_mb = usage.free / (1024 * 1024)
    if free_mb < free_mb_floor:
        raise DiskPressure(f"free={free_mb:.0f}MB < floor={free_mb_floor}MB on {base}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run disk GC over a .catalog directory.")
    ap.add_argument("--catalog-dir", required=True, help="Path to .catalog directory")
    ap.add_argument("--hot-days", type=int, default=30)
    ap.add_argument("--warm-days", type=int, default=365)
    ap.add_argument("--max-mb", type=int, default=5000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats = gc_run(
        args.catalog_dir,
        hot_days=args.hot_days,
        warm_days=args.warm_days,
        max_total_mb=args.max_mb,
        dry_run=args.dry_run,
    )
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
