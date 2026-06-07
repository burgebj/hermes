"""Persistent slash-command worker — one HermesCLI per TUI session.

Protocol: reads JSON lines from stdin {id, command}, writes {id, ok, output|error} to stdout.
"""

import argparse
import contextlib
import io
import json
import os
import sys

import cli as cli_mod
from cli import HermesCLI
from rich.console import Console


def _install_parent_death_signal() -> None:
    """On Linux, terminate this worker when its gateway parent exits.

    The dashboard PTY path can kill the TUI/gateway process abruptly when a
    browser tab or proxy drops the websocket. Installing this in the child
    process avoids using ``preexec_fn`` from the multithreaded gateway parent.
    """
    if not sys.platform.startswith("linux"):
        return
    try:
        import ctypes
        import signal

        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        PR_SET_PDEATHSIG = 1
        libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM, 0, 0, 0)
        # Close the race where the parent exited before prctl was installed.
        if os.getppid() == 1:
            os._exit(0)
    except Exception:
        pass


def _run(cli: HermesCLI, command: str) -> str:
    cmd = (command or "").strip()
    if not cmd:
        return ""
    if not cmd.startswith("/"):
        cmd = f"/{cmd}"

    buf = io.StringIO()

    # Rich Console captures its file handle at construction time, so
    # contextlib.redirect_stdout won't affect it. Swap the console's
    # underlying file to our buffer so self.console.print() is captured.
    cli.console = Console(file=buf, force_terminal=True, width=120)

    old = getattr(cli_mod, "_cprint", None)
    if old is not None:
        cli_mod._cprint = lambda text: print(text)

    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            cli.process_command(cmd)
    finally:
        if old is not None:
            cli_mod._cprint = old

    return buf.getvalue().rstrip()


def main():
    _install_parent_death_signal()

    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--session-key", required=True)
    p.add_argument("--model", default="")
    args = p.parse_args()

    os.environ["HERMES_SESSION_KEY"] = args.session_key
    os.environ["HERMES_INTERACTIVE"] = "1"

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        cli = HermesCLI(model=args.model or None, compact=True, resume=args.session_key, verbose=False)

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue

        rid = None
        try:
            req = json.loads(line)
            rid = req.get("id")
            out = _run(cli, req.get("command", ""))
            sys.stdout.write(json.dumps({"id": rid, "ok": True, "output": out}) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({"id": rid, "ok": False, "error": str(e)}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
