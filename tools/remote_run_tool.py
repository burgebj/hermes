#!/usr/bin/env python3
"""
Remote Run Tool — SSH Command Execution via Paramiko

Executes commands on remote hosts over SSH using Paramiko. Returns stdout,
stderr, and exit code. Supports password and key-based authentication,
sudo, custom ports, working directories, and environment variables.

Design:
- Gated on Paramiko being installed (optional dependency)
- Every connection uses a fresh SSHClient (no persistent connection pooling)
  to avoid stale-channel bugs across tool calls
- Key-based auth preferred; password auth supported as fallback
- sudo mode pipes the password automatically if provided
"""

import json
import logging
import os
import re
import stat
import tempfile
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Requirements check
# ---------------------------------------------------------------------------


def check_remote_run_requirements() -> bool:
    """Return True if Paramiko is available."""
    try:
        import paramiko  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

REMOTE_RUN_SCHEMA = {
    "name": "remote_run",
    "description": (
        "Execute a command on a remote host via SSH. "
        "Returns stdout, stderr, and exit code. "
        "Use this to run commands on servers, containers, or any SSH-accessible host.\n\n"
        "Authentication (in order of precedence):\n"
        "1. key_file (recommended) — path to an SSH private key\n"
        "2. password — password-based auth (less secure)\n"
        "3. SSH agent — uses any keys loaded in the local SSH agent\n\n"
        "Examples:\n"
        '  remote_run(host="myserver", command="whoami")\n'
        '  remote_run(host="myserver", command="systemctl status nginx", sudo=True)\n'
        '  remote_run(host="10.0.0.5", command="ls -la /opt", user="admin", port=2222)\n'
        '  remote_run(host="db1", command="./deploy.sh", workdir="/app", timeout=120)\n\n'
        "Note: Each call opens a new SSH connection. "
        "For multiple commands on the same host, make sequential calls — "
        "Paramiko reuses the underlying TCP connection within a single "
        "exec_command() session but each tool call creates a new SSHClient."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "host": {
                "type": "string",
                "description": "Remote hostname or IP address.",
            },
            "command": {
                "type": "string",
                "description": "Command to execute on the remote host.",
            },
            "user": {
                "type": "string",
                "description": (
                    "SSH username. Defaults to the current local user if omitted."
                ),
            },
            "port": {
                "type": "integer",
                "description": "SSH port (default: 22).",
                "default": 22,
            },
            "key_file": {
                "type": "string",
                "description": (
                    "Path to an SSH private key file for authentication. "
                    "E.g., '/home/user/.ssh/id_ed25519'. "
                    "If not provided, attempts agent- and password-based auth."
                ),
            },
            "password": {
                "type": "string",
                "description": (
                    "SSH password. Only use when key-based auth is not available. "
                    "For sudo commands, this password is also used for sudo elevation."
                ),
            },
            "sudo": {
                "type": "boolean",
                "description": "Run the command with sudo (default: false).",
                "default": False,
            },
            "workdir": {
                "type": "string",
                "description": (
                    "Working directory on the remote host. "
                    "The command is prefixed with 'cd <workdir> && '."
                ),
            },
            "env": {
                "type": "object",
                "description": (
                    "Environment variables to set on the remote host, "
                    "passed as KEY: VALUE pairs."
                ),
                "additionalProperties": {"type": "string"},
            },
            "timeout": {
                "type": "integer",
                "description": "Command timeout in seconds (default: 60).",
                "default": 60,
            },
        },
        "required": ["host", "command"],
    },
}


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


def _build_env_export(env: Optional[Dict[str, str]]) -> str:
    """Build shell 'export' preamble from env dict."""
    if not env:
        return ""
    parts = []
    for k, v in env.items():
        escaped = v.replace("'", "'\\''")
        parts.append(f"export {k}='{escaped}'")
    return "; ".join(parts) + "; " if parts else ""


def _build_command(command: str, workdir: Optional[str],
                   env: Optional[Dict[str, str]],
                   sudo: bool, password: Optional[str]) -> str:
    """Build the final command string to execute over SSH."""
    prefix = ""

    if workdir:
        prefix += f"cd {workdir} && "

    env_export = _build_env_export(env)
    if env_export:
        prefix += env_export

    full_cmd = f"{prefix}{command}"

    if sudo:
        # Wrap in sudo. If password is provided, pipe it via stdin.
        if password:
            # Use printf to avoid echo variations, pipe to sudo -S
            escaped_pw = password.replace("'", "'\\''")
            full_cmd = f"printf '%s\\n' '{escaped_pw}' | sudo -S bash -c '{full_cmd}'"
        else:
            full_cmd = f"sudo bash -c '{full_cmd}'"

    return full_cmd


def _build_sftp_command(client, command: str, workdir: Optional[str]) -> str:
    """Build a command that uses cd when SFTP is also in use."""
    # Simple wrapper - for now just the same as _build_command without sudo
    prefix = ""
    if workdir:
        prefix += f"cd {workdir} && "
    return f"{prefix}{command}"


def remote_run_handler(args: Dict[str, Any], **kwargs) -> str:
    """Execute a command on a remote host via SSH using Paramiko.

    Args:
        args: Dictionary with keys matching REMOTE_RUN_SCHEMA parameters.

    Returns:
        JSON string: {"stdout": "...", "stderr": "...", "exit_code": N}
    """
    host = args["host"]
    command = args["command"]
    user = args.get("user")
    port = args.get("port", 22)
    key_file = args.get("key_file")
    password = args.get("password")
    sudo = args.get("sudo", False)
    workdir = args.get("workdir")
    env = args.get("env")
    timeout = args.get("timeout", 60)

    import paramiko

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Build connect kwargs
        connect_kwargs: Dict[str, Any] = {
            "hostname": host,
            "port": port,
            "timeout": timeout,
        }
        if user:
            connect_kwargs["username"] = user
        if key_file:
            connect_kwargs["key_filename"] = os.path.expanduser(key_file)
        if password:
            connect_kwargs["password"] = password

        # Also try SSH agent
        connect_kwargs["allow_agent"] = True
        connect_kwargs["look_for_keys"] = True

        logger.info(
            "remote_run: connecting to %s@%s:%s",
            connect_kwargs.get("username", "default"), host, port,
        )
        client.connect(**connect_kwargs)
        logger.info("remote_run: connected, executing command")

        # Build the command string
        full_cmd = _build_command(command, workdir, env, sudo, password)

        # The max size for the combined command
        stdin, stdout, stderr = client.exec_command(
            full_cmd,
            timeout=timeout,
            get_pty=sudo,  # PTY needed for sudo password prompt
        )

        # Read output
        out_text = stdout.read().decode("utf-8", errors="replace")
        err_text = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()

        result = {
            "stdout": out_text,
            "stderr": err_text,
            "exit_code": exit_code,
            "host": host,
        }

        logger.info(
            "remote_run: exit_code=%s, stdout=%s bytes, stderr=%s bytes",
            exit_code, len(out_text), len(err_text),
        )

        return json.dumps(result)

    except paramiko.AuthenticationException as e:
        return json.dumps({
            "error": f"Authentication failed: {e}",
            "host": host,
            "exit_code": 1,
        })
    except paramiko.SSHException as e:
        return json.dumps({
            "error": f"SSH connection failed: {e}",
            "host": host,
            "exit_code": 1,
        })
    except OSError as e:
        return json.dumps({
            "error": f"Network error: {e}",
            "host": host,
            "exit_code": 1,
        })
    except Exception as e:
        logger.error("remote_run: unexpected error: %s", e, exc_info=True)
        return json.dumps({
            "error": f"Unexpected error: {e}",
            "host": host,
            "exit_code": 1,
        })
    finally:
        try:
            client.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

from tools.registry import registry  # noqa: E402

registry.register(
    name="remote_run",
    toolset="terminal",
    schema=REMOTE_RUN_SCHEMA,
    handler=lambda args, **kw: remote_run_handler(args, **kw),
    check_fn=check_remote_run_requirements,
    emoji="🔗",
)
