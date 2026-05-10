"""US-007 tests for the per-user UAT refresh daemon."""

from __future__ import annotations

import asyncio
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes_cli.feishu_refresh_daemon import (
    needs_refresh,
    scan_per_user_uat_dir,
    _attempt_refresh,
    _needs_reauth_sidecar_path,
    refresh_daemon_loop,
    start_refresh_daemon,
)


def _write_uat(uat_dir: Path, open_id: str, expires_at_ms: int,
               refresh_token: str = "refresh_xyz") -> Path:
    uat_dir.mkdir(parents=True, exist_ok=True)
    path = uat_dir / f"{open_id}.json"
    path.write_text(json.dumps({
        "app_id": "app",
        "user_open_id": open_id,
        "access_token": "current_tok",
        "refresh_token": refresh_token,
        "expires_at": expires_at_ms,
        "refresh_expires_at": int(time.time() * 1000) + 86400 * 1000,
        "scope": "calendar:calendar",
    }))
    return path


class TestScanAndNeedsRefresh(unittest.TestCase):

    def test_scan_returns_only_json_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "feishu_uat"
            d.mkdir()
            _write_uat(d, "ou_a", 99999999999999)
            (d / "ignored.txt").write_text("nope")
            (d / ".hidden.json").write_text("{}")
            files = scan_per_user_uat_dir(d)
            self.assertEqual(
                sorted(f.name for f in files),
                ["ou_a.json"],
            )

    def test_scan_returns_empty_when_dir_missing(self):
        self.assertEqual(scan_per_user_uat_dir(Path("/nope/nonexistent")), [])

    def test_needs_refresh_true_for_token_expiring_within_headroom(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            now_ms = int(time.time() * 1000)
            # Expires in 100s — within 300s headroom → needs refresh
            p = _write_uat(d, "ou_e", now_ms + 100 * 1000)
            self.assertTrue(needs_refresh(p, headroom_s=300))

    def test_needs_refresh_false_for_fresh_token(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            now_ms = int(time.time() * 1000)
            # Expires in 7200s — well outside 300s headroom
            p = _write_uat(d, "ou_f", now_ms + 7200 * 1000)
            self.assertFalse(needs_refresh(p, headroom_s=300))


class TestAttemptRefresh(unittest.TestCase):

    def test_success_clears_sidecar_if_it_existed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            p = _write_uat(d, "ou_ok", int(time.time() * 1000) + 100 * 1000)
            sidecar = _needs_reauth_sidecar_path(p)
            sidecar.write_text("{}")  # leftover from prior failure

            with patch("hermes_cli.feishu_refresh_daemon.refresh_uat_for_user") as mock_refresh:
                _attempt_refresh(p, "app", "secret")

            mock_refresh.assert_called_once_with("ou_ok", "app", "secret")
            self.assertFalse(sidecar.exists())

    def test_terminal_failure_writes_needs_reauth_sidecar(self):
        from tools.feishu_oapi_client import NeedAuthorizationError
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            p = _write_uat(d, "ou_dead", int(time.time() * 1000) + 100 * 1000)

            with patch(
                "hermes_cli.feishu_refresh_daemon.refresh_uat_for_user",
                side_effect=NeedAuthorizationError(
                    user_open_id="ou_dead",
                    reason="refresh_token rejected",
                ),
            ):
                _attempt_refresh(p, "app", "secret")

            sidecar = _needs_reauth_sidecar_path(p)
            self.assertTrue(sidecar.exists())
            data = json.loads(sidecar.read_text())
            self.assertIn("rejected", data["reason"])

    def test_transient_error_does_not_write_sidecar(self):
        from hermes_cli.feishu_auth import FeishuAuthError
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir)
            p = _write_uat(d, "ou_flap", int(time.time() * 1000) + 100 * 1000)

            with patch(
                "hermes_cli.feishu_refresh_daemon.refresh_uat_for_user",
                side_effect=FeishuAuthError("network error"),
            ):
                _attempt_refresh(p, "app", "secret")

            sidecar = _needs_reauth_sidecar_path(p)
            self.assertFalse(sidecar.exists())


class TestDaemonLoop(unittest.IsolatedAsyncioTestCase):

    async def test_daemon_loop_stops_on_event(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "feishu_uat"
            d.mkdir()
            stop = asyncio.Event()
            stop.set()  # immediate stop
            await refresh_daemon_loop(
                "app", "secret",
                interval_s=0.01,
                uat_dir=d,
                stop_event=stop,
            )

    async def test_daemon_loop_cancels_cleanly(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "feishu_uat"
            d.mkdir()
            task = asyncio.create_task(
                refresh_daemon_loop(
                    "app", "secret",
                    interval_s=10.0,
                    uat_dir=d,
                ),
            )
            await asyncio.sleep(0.01)  # let it enter the loop
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

    async def test_daemon_loop_calls_refresh_for_near_expiry_only(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "feishu_uat"
            d.mkdir()
            now_ms = int(time.time() * 1000)
            # ou_near expires in 100s → needs refresh
            _write_uat(d, "ou_near", now_ms + 100 * 1000)
            # ou_fresh expires in 2h → skip
            _write_uat(d, "ou_fresh", now_ms + 7200 * 1000)

            calls: list = []

            def fake_refresh(open_id, app_id, app_secret):
                calls.append(open_id)

            stop = asyncio.Event()

            async def stopper():
                await asyncio.sleep(0.05)
                stop.set()

            with patch(
                "hermes_cli.feishu_refresh_daemon.refresh_uat_for_user",
                side_effect=fake_refresh,
            ):
                await asyncio.gather(
                    refresh_daemon_loop(
                        "app", "secret",
                        interval_s=0.01,
                        headroom_s=300,
                        uat_dir=d,
                        stop_event=stop,
                    ),
                    stopper(),
                )

            self.assertIn("ou_near", calls)
            self.assertNotIn("ou_fresh", calls)

    async def test_start_refresh_daemon_returns_task_and_stop_event(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            d = Path(tmpdir) / "feishu_uat"
            d.mkdir()
            loop = asyncio.get_event_loop()
            task, stop = start_refresh_daemon(
                loop, "app", "secret",
                interval_s=0.01,
                uat_dir=d,
            )
            self.assertIsInstance(task, asyncio.Task)
            self.assertIsInstance(stop, asyncio.Event)
            stop.set()
            await asyncio.wait_for(task, timeout=1.0)


if __name__ == "__main__":
    unittest.main()
