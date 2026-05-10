"""P1.2 follow-up: assert that the refresh daemon is wired into the
FeishuAdapter lifecycle. Architect requested an explicit gateway-runner
test so deployment-path drift cannot silently disable the daemon.

We test the extracted :meth:`_start_refresh_daemon_if_creds` helper rather
than the full ``connect()`` because connect requires real lark.Client / WS
bring-up; the helper is the exact code that connect() now calls, so this
test catches the same drift without needing a Feishu fixture.
"""

from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from gateway.platforms.feishu import FeishuAdapter


class _StubAdapter:
    """Minimal stand-in providing only the attributes the helper reads/writes."""

    _start_refresh_daemon_if_creds = FeishuAdapter._start_refresh_daemon_if_creds

    def __init__(self, loop, app_id: str, app_secret: str):
        self._loop = loop
        self._settings = SimpleNamespace(app_id=app_id, app_secret=app_secret)
        self._refresh_daemon_task = None
        self._refresh_daemon_stop = None


class TestRefreshDaemonStartup(unittest.IsolatedAsyncioTestCase):

    async def test_helper_starts_daemon_when_creds_present(self):
        loop = asyncio.get_event_loop()
        adapter = _StubAdapter(loop, "app", "secret")

        with patch("hermes_cli.feishu_refresh_daemon.start_refresh_daemon") as mock_start:
            mock_start.return_value = (MagicMock(), MagicMock())
            adapter._start_refresh_daemon_if_creds()

        mock_start.assert_called_once_with(loop, "app", "secret")
        self.assertIsNotNone(adapter._refresh_daemon_task)
        self.assertIsNotNone(adapter._refresh_daemon_stop)

    async def test_helper_skips_daemon_when_app_id_missing(self):
        loop = asyncio.get_event_loop()
        adapter = _StubAdapter(loop, "", "secret")

        with patch("hermes_cli.feishu_refresh_daemon.start_refresh_daemon") as mock_start:
            adapter._start_refresh_daemon_if_creds()

        mock_start.assert_not_called()
        self.assertIsNone(adapter._refresh_daemon_task)

    async def test_helper_skips_daemon_when_app_secret_missing(self):
        loop = asyncio.get_event_loop()
        adapter = _StubAdapter(loop, "app", "")

        with patch("hermes_cli.feishu_refresh_daemon.start_refresh_daemon") as mock_start:
            adapter._start_refresh_daemon_if_creds()

        mock_start.assert_not_called()

    async def test_helper_skips_daemon_when_loop_is_none(self):
        adapter = _StubAdapter(None, "app", "secret")

        with patch("hermes_cli.feishu_refresh_daemon.start_refresh_daemon") as mock_start:
            adapter._start_refresh_daemon_if_creds()

        mock_start.assert_not_called()

    async def test_helper_swallows_import_error(self):
        """Daemon-module import failure must not break connect()."""
        loop = asyncio.get_event_loop()
        adapter = _StubAdapter(loop, "app", "secret")

        # Force the inner import to raise. We patch the actual symbol.
        with patch(
            "hermes_cli.feishu_refresh_daemon.start_refresh_daemon",
            side_effect=RuntimeError("simulated import / runtime issue"),
        ):
            adapter._start_refresh_daemon_if_creds()  # must not raise

        self.assertIsNone(adapter._refresh_daemon_task)


if __name__ == "__main__":
    unittest.main()
