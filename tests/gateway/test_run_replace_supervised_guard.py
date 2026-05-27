"""Regression tests for the ``hermes gateway run --replace`` supervisor guard.

When an unrelated process (e.g. ``hermes-web-ui``'s startup hook — see
issue #27041) shells out to ``hermes gateway run --replace`` while a
launchd / systemd managed gateway is already healthy, the SIGTERM the
new instance would otherwise send bounces off the supervisor's KeepAlive
policy and triggers a restart loop.  The guard added in ``gateway.run``
detects that situation and exits cleanly so rogue ``--replace`` callers
become a no-op.
"""

from __future__ import annotations

import sys

import pytest

from gateway import run as gateway_run


# ---------------------------------------------------------------------------
# _existing_pid_is_service_supervised
# ---------------------------------------------------------------------------


class TestExistingPidIsServiceSupervised:
    def test_returns_false_for_non_positive_pid(self, monkeypatch):
        monkeypatch.setattr(
            "hermes_cli.gateway._get_service_pids",
            lambda: {1234},
            raising=False,
        )
        assert gateway_run._existing_pid_is_service_supervised(0) is False
        assert gateway_run._existing_pid_is_service_supervised(-5) is False

    def test_returns_true_when_pid_present_in_supervisor_set(self, monkeypatch):
        monkeypatch.setattr(
            "hermes_cli.gateway._get_service_pids",
            lambda: {4321, 1234},
            raising=False,
        )
        assert gateway_run._existing_pid_is_service_supervised(1234) is True

    def test_returns_false_when_pid_absent_from_supervisor_set(self, monkeypatch):
        monkeypatch.setattr(
            "hermes_cli.gateway._get_service_pids",
            lambda: {9999},
            raising=False,
        )
        assert gateway_run._existing_pid_is_service_supervised(1234) is False

    def test_returns_false_when_service_probe_raises(self, monkeypatch):
        def _boom() -> set:
            raise RuntimeError("launchctl unavailable")

        monkeypatch.setattr(
            "hermes_cli.gateway._get_service_pids",
            _boom,
            raising=False,
        )
        assert gateway_run._existing_pid_is_service_supervised(1234) is False


# ---------------------------------------------------------------------------
# _running_under_service_supervisor
# ---------------------------------------------------------------------------


class TestRunningUnderServiceSupervisor:
    def test_ppid_one_is_service_supervised(self, monkeypatch):
        monkeypatch.setattr(gateway_run.os, "getppid", lambda: 1)
        assert gateway_run._running_under_service_supervisor() is True

    def test_ppid_zero_is_service_supervised(self, monkeypatch):
        # PPID 0 only appears in exotic init configurations, but PID<=1
        # is treated as "init" for safety.
        monkeypatch.setattr(gateway_run.os, "getppid", lambda: 0)
        assert gateway_run._running_under_service_supervisor() is True

    def test_normal_ppid_on_macos_is_not_supervised(self, monkeypatch):
        monkeypatch.setattr(gateway_run.os, "getppid", lambda: 4242)
        monkeypatch.setattr(gateway_run.sys, "platform", "darwin")
        assert gateway_run._running_under_service_supervisor() is False

    def test_normal_ppid_on_linux_with_systemd_user_manager_is_supervised(
        self, monkeypatch, tmp_path
    ):
        ppid = 4242
        monkeypatch.setattr(gateway_run.os, "getppid", lambda: ppid)
        monkeypatch.setattr(gateway_run.sys, "platform", "linux")

        real_open = open

        def _fake_open(path, *args, **kwargs):
            if isinstance(path, str) and path == f"/proc/{ppid}/comm":
                from io import StringIO

                return StringIO("systemd\n")
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr("builtins.open", _fake_open)
        assert gateway_run._running_under_service_supervisor() is True

    def test_normal_ppid_on_linux_with_non_systemd_parent_is_not_supervised(
        self, monkeypatch
    ):
        ppid = 4242
        monkeypatch.setattr(gateway_run.os, "getppid", lambda: ppid)
        monkeypatch.setattr(gateway_run.sys, "platform", "linux")

        real_open = open

        def _fake_open(path, *args, **kwargs):
            if isinstance(path, str) and path == f"/proc/{ppid}/comm":
                from io import StringIO

                return StringIO("node\n")
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr("builtins.open", _fake_open)
        assert gateway_run._running_under_service_supervisor() is False

    def test_proc_comm_missing_falls_back_to_not_supervised(self, monkeypatch):
        monkeypatch.setattr(gateway_run.os, "getppid", lambda: 4242)
        monkeypatch.setattr(gateway_run.sys, "platform", "linux")

        real_open = open

        def _fake_open(path, *args, **kwargs):
            if isinstance(path, str) and path.startswith("/proc/"):
                raise FileNotFoundError(path)
            return real_open(path, *args, **kwargs)

        monkeypatch.setattr("builtins.open", _fake_open)
        assert gateway_run._running_under_service_supervisor() is False


# ---------------------------------------------------------------------------
# _replace_force_env_set
# ---------------------------------------------------------------------------


class TestReplaceForceEnvSet:
    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "Yes", "on", " on ", "  1  "])
    def test_truthy_values_enable_force(self, monkeypatch, value):
        monkeypatch.setenv("HERMES_GATEWAY_REPLACE_FORCE", value)
        assert gateway_run._replace_force_env_set() is True

    @pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "maybe"])
    def test_falsy_values_keep_force_disabled(self, monkeypatch, value):
        monkeypatch.setenv("HERMES_GATEWAY_REPLACE_FORCE", value)
        assert gateway_run._replace_force_env_set() is False

    def test_unset_env_disables_force(self, monkeypatch):
        monkeypatch.delenv("HERMES_GATEWAY_REPLACE_FORCE", raising=False)
        assert gateway_run._replace_force_env_set() is False


# ---------------------------------------------------------------------------
# _should_skip_supervised_replace — the actual decision gate
# ---------------------------------------------------------------------------


class TestShouldSkipSupervisedReplace:
    def test_skips_when_supervised_and_unsupervised_caller(self, monkeypatch):
        monkeypatch.setattr(
            gateway_run, "_existing_pid_is_service_supervised", lambda pid: True
        )
        monkeypatch.setattr(
            gateway_run, "_running_under_service_supervisor", lambda: False
        )
        monkeypatch.setattr(gateway_run, "_replace_force_env_set", lambda: False)
        assert gateway_run._should_skip_supervised_replace(1234) is True

    def test_allows_replace_when_caller_is_supervisor(self, monkeypatch):
        """``launchd_restart`` / ``systemd_restart`` legitimately relaunch
        the gateway under the supervisor, so PPID==1 (or the user systemd
        manager) must still pass through the normal replace path."""
        monkeypatch.setattr(
            gateway_run, "_existing_pid_is_service_supervised", lambda pid: True
        )
        monkeypatch.setattr(
            gateway_run, "_running_under_service_supervisor", lambda: True
        )
        monkeypatch.setattr(gateway_run, "_replace_force_env_set", lambda: False)
        assert gateway_run._should_skip_supervised_replace(1234) is False

    def test_allows_replace_when_existing_not_supervised(self, monkeypatch):
        """Manual ``hermes gateway run --replace`` against a foreground
        sibling (no launchd/systemd unit installed) must keep working."""
        monkeypatch.setattr(
            gateway_run, "_existing_pid_is_service_supervised", lambda pid: False
        )
        monkeypatch.setattr(
            gateway_run, "_running_under_service_supervisor", lambda: False
        )
        monkeypatch.setattr(gateway_run, "_replace_force_env_set", lambda: False)
        assert gateway_run._should_skip_supervised_replace(1234) is False

    def test_force_env_overrides_guard(self, monkeypatch):
        """Power-user escape hatch: ``HERMES_GATEWAY_REPLACE_FORCE=1``
        must bypass the guard even when every other signal says skip."""
        monkeypatch.setattr(
            gateway_run, "_existing_pid_is_service_supervised", lambda pid: True
        )
        monkeypatch.setattr(
            gateway_run, "_running_under_service_supervisor", lambda: False
        )
        monkeypatch.setattr(gateway_run, "_replace_force_env_set", lambda: True)
        assert gateway_run._should_skip_supervised_replace(1234) is False

    def test_zero_pid_never_skips(self, monkeypatch):
        monkeypatch.setattr(
            gateway_run, "_existing_pid_is_service_supervised", lambda pid: True
        )
        monkeypatch.setattr(
            gateway_run, "_running_under_service_supervisor", lambda: False
        )
        monkeypatch.setattr(gateway_run, "_replace_force_env_set", lambda: False)
        assert gateway_run._should_skip_supervised_replace(0) is False


# ---------------------------------------------------------------------------
# Integration: ``start_gateway`` early-returns without terminating the
# supervised PID when the guard fires.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_gateway_bows_out_when_supervised_replace_detected(
    monkeypatch, tmp_path, capsys
):
    """End-to-end: a rogue ``hermes gateway run --replace`` from an
    unsupervised parent (e.g. ``hermes-web-ui``) must NOT SIGTERM the
    launchd/systemd-managed gateway PID — it should log a clear notice
    and return success so the caller doesn't restart-loop."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.delenv("HERMES_GATEWAY_REPLACE_FORCE", raising=False)

    supervised_pid = 4242

    # Pretend a service-managed gateway is alive on ``supervised_pid``.
    monkeypatch.setattr(
        "gateway.status.get_running_pid",
        lambda *a, **kw: supervised_pid,
    )
    monkeypatch.setattr(
        gateway_run, "_existing_pid_is_service_supervised", lambda pid: pid == supervised_pid
    )
    monkeypatch.setattr(
        gateway_run, "_running_under_service_supervisor", lambda: False
    )

    # If the guard misfires and proceeds with the kill path, fail loudly
    # so the regression is impossible to miss.
    def _explode(*args, **kwargs):
        raise AssertionError(
            "terminate_pid must not be called when the supervisor guard fires"
        )

    monkeypatch.setattr("gateway.status.terminate_pid", _explode)

    result = await gateway_run.start_gateway(replace=True)

    assert result is True, "guard should treat the rogue --replace as success"
    captured = capsys.readouterr()
    assert "launchd/systemd" in captured.out
    assert str(supervised_pid) in captured.out


@pytest.mark.asyncio
async def test_start_gateway_respects_force_env_override(
    monkeypatch, tmp_path
):
    """``HERMES_GATEWAY_REPLACE_FORCE=1`` must bypass the guard so power
    users / scripted maintenance can still force a takeover when they
    know what they're doing."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_GATEWAY_REPLACE_FORCE", "1")

    supervised_pid = 4242

    monkeypatch.setattr(
        "gateway.status.get_running_pid",
        lambda *a, **kw: supervised_pid,
    )
    monkeypatch.setattr(
        gateway_run, "_existing_pid_is_service_supervised", lambda pid: True
    )
    monkeypatch.setattr(
        gateway_run, "_running_under_service_supervisor", lambda: False
    )

    terminate_calls: list[tuple] = []

    def _record_terminate(pid, force=False):
        terminate_calls.append((pid, force))
        raise ProcessLookupError("simulated old pid already gone")

    monkeypatch.setattr("gateway.status.terminate_pid", _record_terminate)
    monkeypatch.setattr("gateway.status.get_process_start_time", lambda pid: None)
    monkeypatch.setattr("gateway.status._pid_exists", lambda pid: False)
    # Short-circuit the rest of start_gateway by failing at the very next
    # external dependency — we only care that the guard *did not* fire.
    monkeypatch.setattr(
        "gateway.status.remove_pid_file",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("STOP_AFTER_REPLACE")),
    )

    with pytest.raises(RuntimeError, match="STOP_AFTER_REPLACE"):
        await gateway_run.start_gateway(replace=True)

    assert terminate_calls == [(supervised_pid, False)], (
        "force env override must allow terminate_pid to run on the supervised PID"
    )
