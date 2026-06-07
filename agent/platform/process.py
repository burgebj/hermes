"""
Process management abstraction.
"""
import os
import signal
import subprocess
import logging
from agent.platform.platform_info import platform_info

logger = logging.getLogger(__name__)

try:
    import psutil
except Exception as exc:
    psutil = None
    _PSUTIL_IMPORT_ERROR = exc
else:
    _PSUTIL_IMPORT_ERROR = None

class ProcessManager:
    @staticmethod
    def kill_process_tree(proc: subprocess.Popen, escalate: bool = False):
        """Best-effort process-tree termination with psutil fallback handling."""
        if platform_info.is_windows:
            ProcessManager.kill_process_group(proc, escalate=escalate)
            return

        if psutil is None:
            ProcessManager.kill_process_group(proc, escalate=escalate)
            return

        try:
            parent = psutil.Process(proc.pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            try:
                parent.terminate()
            except psutil.NoSuchProcess:
                pass
        except psutil.NoSuchProcess:
            return
        except (PermissionError, OSError) as exc:
            logger.debug("Could not terminate process tree: %s", exc, exc_info=True)
            try:
                proc.kill()
            except Exception as kill_exc:
                logger.debug("Could not kill process: %s", kill_exc, exc_info=True)

        if escalate:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    parent = psutil.Process(proc.pid)
                    for child in parent.children(recursive=True):
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    try:
                        parent.kill()
                    except psutil.NoSuchProcess:
                        pass
                except psutil.NoSuchProcess:
                    pass
                except (PermissionError, OSError) as exc:
                    logger.debug("Could not kill process tree: %s", exc, exc_info=True)
                    try:
                        proc.kill()
                    except Exception as kill_exc:
                        logger.debug("Could not kill process: %s", kill_exc, exc_info=True)

    @staticmethod
    def kill_process_group(proc: subprocess.Popen, escalate: bool = False):
        """Kill the child and its entire process group."""
        try:
            if platform_info.is_windows:
                subprocess.run(
                    ["taskkill", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                    timeout=10,
                )
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # windows-footgun: ok — POSIX branch only
        except (FileNotFoundError, subprocess.TimeoutExpired, ProcessLookupError, PermissionError, OSError) as e:
            logger.debug("Could not kill process group: %s", e, exc_info=True)
            try:
                proc.kill()
            except Exception as e2:
                logger.debug("Could not kill process: %s", e2, exc_info=True)

        if escalate:
            # Give the process 5s to exit after SIGTERM, then SIGKILL
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    if platform_info.is_windows:
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                            capture_output=True,
                            timeout=10,
                        )
                    else:
                        sigkill = getattr(signal, "SIGKILL", signal.SIGTERM)
                        os.killpg(os.getpgid(proc.pid), sigkill)  # windows-footgun: ok — POSIX branch only
                except (FileNotFoundError, subprocess.TimeoutExpired, ProcessLookupError, PermissionError, OSError) as e:
                    logger.debug("Could not kill process group with SIGKILL: %s", e, exc_info=True)
                    try:
                        proc.kill()
                    except Exception as e2:
                        logger.debug("Could not kill process: %s", e2, exc_info=True)

    @staticmethod
    def kill_pid(pid: int, force: bool = False):
        """Kills a given pid."""
        if platform_info.is_windows:
            if force:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            else:
                subprocess.run(["taskkill", "/T", "/PID", str(pid)], capture_output=True)
        else:
            sig = getattr(signal, "SIGKILL", signal.SIGTERM) if force else signal.SIGTERM
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass

    @staticmethod
    def is_process_alive(pid: int) -> bool:
        """Check if a process is alive."""
        if not pid:
            return False
        if psutil is not None:
            try:
                return bool(psutil.pid_exists(pid))
            except Exception as exc:
                logger.debug("psutil.pid_exists failed: %s", exc, exc_info=True)
        elif _PSUTIL_IMPORT_ERROR is not None:
            logger.debug("psutil unavailable for process liveness checks: %s", _PSUTIL_IMPORT_ERROR)

        if platform_info.is_windows:
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
                logger.debug("tasklist PID check failed: %s", exc, exc_info=True)
                return False
            output = (result.stdout or "").lower()
            return result.returncode == 0 and str(pid) in output and "no tasks" not in output

        try:
            os.kill(pid, 0)  # windows-footgun: ok — POSIX branch only
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False

    @staticmethod
    def setup_new_process_group():
        """Returns the preexec_fn needed to start a new process group."""
        if platform_info.is_windows:
            return None
        return getattr(os, "setsid", None)
