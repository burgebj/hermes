import subprocess


def _cp1251_readerthread_decode_error():
    return UnicodeDecodeError(
        "charmap",
        b"\x98",
        0,
        1,
        "character maps to <undefined>",
    )


def _fail_like_cp1251_readerthread_without_replace(cmd, **kwargs):
    if kwargs.get("text") is True and kwargs.get("capture_output") is True:
        if kwargs.get("errors") != "replace":
            raise _cp1251_readerthread_decode_error()
    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


def test_windows_force_terminate_decodes_taskkill_output_lossily(monkeypatch):
    """taskkill output can contain bytes that fail under cp1251 (#39029)."""
    import gateway.status as status

    monkeypatch.setattr(status, "_IS_WINDOWS", True)
    monkeypatch.setattr(status.subprocess, "run", _fail_like_cp1251_readerthread_without_replace)

    status.terminate_pid(12345, force=True)


def test_windows_dashboard_kill_decodes_taskkill_output_lossily(monkeypatch, capsys):
    """Dashboard cleanup should not leak taskkill decode errors on localized Windows."""
    import hermes_cli.main as cli_main

    monkeypatch.setattr(cli_main.sys, "platform", "win32")
    monkeypatch.delenv("HERMES_DESKTOP_CHILD_PID", raising=False)
    monkeypatch.setattr(cli_main, "_find_stale_dashboard_pids", lambda exclude_pids=None: [12345])
    monkeypatch.setattr(cli_main.subprocess, "run", _fail_like_cp1251_readerthread_without_replace)

    cli_main._kill_stale_dashboard_processes(reason="test")

    out = capsys.readouterr().out
    assert "✓ stopped PID 12345" in out
