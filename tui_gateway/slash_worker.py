"""Persistent slash-command worker — one HermesCLI per TUI session.

Protocol: reads JSON lines from stdin {id, command}, writes {id, ok, output|error} to stdout.
"""

import argparse
import contextlib
import io
import json
import os
import sys
import threading
import time

try:
    import psutil
except ImportError:
    psutil = None

import cli as cli_mod
from cli import HermesCLI
from rich.console import Console


def _start_orphan_watchdog():
    """Start a daemon thread that kills this process if its parent disappears.
    
    This is the L2 safety net (Issue #21370) to prevent zombie processes.
    It uses PID + create_time fingerprinting to ensure cross-platform 
    determinism and prevent PID reuse false-positives on Windows.
    """
    if not psutil:
        return

    ppid = os.getppid()
    try:
        # Capture parent fingerprint at startup
        parent_proc = psutil.Process(ppid)
        parent_started = parent_proc.create_time()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # Parent already gone or inaccessible
        os._exit(0)

    def watchdog():
        # Delay startup slightly to let the main process stabilize
        time.sleep(5)
        while True:
            try:
                # 1. Basic existence check
                if not psutil.pid_exists(ppid):
                    os._exit(0)
                
                # 2. Fingerprint check (Critical for Windows PID reuse)
                current_parent = psutil.Process(ppid)
                if current_parent.create_time() != parent_started:
                    os._exit(0)
                
                # 3. POSIX orphan check (adopted by init)
                if os.name != 'nt' and os.getppid() == 1:
                    os._exit(0)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                os._exit(0)
            except Exception:
                # Fallback: ignore transient errors in psutil calls
                pass
            
            time.sleep(10)

    t = threading.Thread(target=watchdog, daemon=True, name="OrphanWatchdog")
    t.start()


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
    _start_orphan_watchdog()
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
