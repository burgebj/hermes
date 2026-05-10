"""Background refresh daemon for per-user Feishu UAT tokens (US-007).

A long-running asyncio task that periodically scans
``~/.hermes/feishu_uat/<open_id>.json`` and refreshes any UAT whose
``access_token`` is within :data:`REFRESH_HEADROOM_S` of expiry. Failures
are logged and a sidecar ``<open_id>.needs_reauth`` flag file is written
so the gateway can surface a "please re-authorize" card to the user
(handled by the scope manager / onboarding flows).

The daemon is process-scoped — multiple gateway processes pointing at the
same ~/.hermes will race; deployments doing that should coordinate via
file locking or run a single owning process. For the typical 1-bot /
N-users scenario there is exactly one process so no extra locking is
needed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

from hermes_cli.feishu_auth import (
    FEISHU_UAT_DIR,
    FeishuAuthError,
    refresh_uat_for_user,
)
from tools.feishu_oapi_client import NeedAuthorizationError

logger = logging.getLogger(__name__)

# Scan / refresh tunables. Kept as module-level constants so tests can
# monkey-patch them rather than threading parameters through every call.
SCAN_INTERVAL_S = 60.0
REFRESH_HEADROOM_S = 300  # treat tokens as near-expiry within 5 minutes


def _needs_reauth_sidecar_path(user_uat_path: Path) -> Path:
    """Path to the sidecar flag file written when refresh fails terminally."""
    return user_uat_path.with_suffix(".needs_reauth")


def scan_per_user_uat_dir(uat_dir: Path = FEISHU_UAT_DIR) -> list[Path]:
    """Return per-user UAT files in ``uat_dir`` (skips sidecars/junk)."""
    if not uat_dir.exists():
        return []
    out: list[Path] = []
    for entry in uat_dir.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix != ".json":
            continue
        if entry.name.startswith("."):
            continue
        out.append(entry)
    return out


def needs_refresh(uat_path: Path, headroom_s: int = REFRESH_HEADROOM_S) -> bool:
    """Return True if the UAT file at ``uat_path`` is within headroom of expiry."""
    try:
        with open(uat_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return False
    expires_at_ms = int(data.get("expires_at", 0))
    if expires_at_ms <= 0:
        return False
    now_ms = int(time.time() * 1000)
    return now_ms >= expires_at_ms - headroom_s * 1000


def _open_id_from_uat_path(uat_path: Path) -> str:
    """Extract open_id from filename ``<open_id>.json``."""
    return uat_path.stem


def _attempt_refresh(uat_path: Path, app_id: str, app_secret: str) -> None:
    """Refresh one UAT file. Marks needs_reauth on terminal failure."""
    open_id = _open_id_from_uat_path(uat_path)
    sidecar = _needs_reauth_sidecar_path(uat_path)
    try:
        refresh_uat_for_user(open_id, app_id, app_secret)
    except NeedAuthorizationError as exc:
        # Terminal — refresh_token rejected or token file missing.
        logger.warning(
            "[refresh-daemon] %s needs re-auth: %s", open_id, exc.reason
        )
        try:
            sidecar.write_text(
                json.dumps({"reason": exc.reason, "ts": int(time.time())}),
                encoding="utf-8",
            )
        except OSError:
            pass
        return
    except FeishuAuthError as exc:
        # Transient — log and let the next tick retry.
        logger.info("[refresh-daemon] transient refresh error for %s: %s", open_id, exc)
        return
    except Exception:
        logger.exception("[refresh-daemon] unexpected refresh error for %s", open_id)
        return
    # Success — clear the sidecar if it existed
    try:
        sidecar.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


async def refresh_daemon_loop(
    app_id: str,
    app_secret: str,
    *,
    interval_s: float = SCAN_INTERVAL_S,
    headroom_s: int = REFRESH_HEADROOM_S,
    uat_dir: Optional[Path] = None,
    stop_event: Optional[asyncio.Event] = None,
) -> None:
    """Run the refresh daemon loop until ``stop_event`` is set or task is cancelled.

    Args:
        app_id: Feishu app ID used by ``refresh_uat_for_user``.
        app_secret: Feishu app secret.
        interval_s: Seconds between scans (default 60).
        headroom_s: Treat tokens within this many seconds of expiry as
            "needs refresh" (default 300).
        uat_dir: Override the per-user UAT directory (defaults to
            :data:`FEISHU_UAT_DIR`); useful for tests.
        stop_event: Optional asyncio.Event the caller can set to stop the
            loop gracefully (in addition to plain task cancellation).
    """
    target_dir = uat_dir or FEISHU_UAT_DIR
    logger.info(
        "[refresh-daemon] starting (interval=%ss, headroom=%ss, dir=%s)",
        interval_s, headroom_s, target_dir,
    )
    try:
        while True:
            if stop_event is not None and stop_event.is_set():
                break
            try:
                files = scan_per_user_uat_dir(target_dir)
                for f in files:
                    if stop_event is not None and stop_event.is_set():
                        break
                    if needs_refresh(f, headroom_s):
                        # Run the (sync) refresh in a worker thread so we
                        # do not block the event loop on HTTP I/O.
                        await asyncio.to_thread(
                            _attempt_refresh, f, app_id, app_secret,
                        )
            except Exception:
                logger.exception("[refresh-daemon] scan tick failed")
            try:
                await asyncio.sleep(interval_s)
            except asyncio.CancelledError:
                raise
    except asyncio.CancelledError:
        logger.info("[refresh-daemon] cancelled")
        raise


def start_refresh_daemon(
    loop: asyncio.AbstractEventLoop,
    app_id: str,
    app_secret: str,
    *,
    interval_s: float = SCAN_INTERVAL_S,
    headroom_s: int = REFRESH_HEADROOM_S,
    uat_dir: Optional[Path] = None,
) -> tuple[asyncio.Task, asyncio.Event]:
    """Schedule the refresh daemon on ``loop`` and return its (task, stop_event).

    The returned event can be set to stop the loop gracefully; the task can
    also be cancelled directly. Both are safe to call from any thread (set()
    via ``loop.call_soon_threadsafe(stop_event.set)`` if needed).
    """
    stop_event = asyncio.Event()
    task = loop.create_task(
        refresh_daemon_loop(
            app_id, app_secret,
            interval_s=interval_s,
            headroom_s=headroom_s,
            uat_dir=uat_dir,
            stop_event=stop_event,
        ),
        name="feishu-refresh-daemon",
    )
    return task, stop_event
