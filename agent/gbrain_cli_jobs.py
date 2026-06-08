from __future__ import annotations

import json
import os
import subprocess
from typing import Any


def build_shell_submit_command(
    *,
    params: dict[str, Any],
    cli_path: str = "gbrain",
    allow_shell_jobs: bool = False,
    follow: bool = False,
    queue: str | None = None,
    timeout_ms: int | None = None,
    max_attempts: int | None = None,
) -> dict[str, Any]:
    command = [cli_path, "jobs", "submit", "shell", "--params", json.dumps(params, ensure_ascii=False)]
    if queue:
        command.extend(["--queue", queue])
    if timeout_ms is not None:
        command.extend(["--timeout-ms", str(timeout_ms)])
    if max_attempts is not None:
        command.extend(["--max-attempts", str(max_attempts)])
    if follow:
        command.append("--follow")
    env = os.environ.copy()
    if allow_shell_jobs:
        env["GBRAIN_ALLOW_SHELL_JOBS"] = "1"
    return {"command": command, "env": env}


def submit_shell_job(
    *,
    params: dict[str, Any],
    cli_path: str = "gbrain",
    allow_shell_jobs: bool = False,
    follow: bool = False,
    queue: str | None = None,
    timeout_ms: int | None = None,
    max_attempts: int | None = None,
    timeout: float = 60,
) -> dict[str, Any]:
    spec = build_shell_submit_command(
        params=params,
        cli_path=cli_path,
        allow_shell_jobs=allow_shell_jobs,
        follow=follow,
        queue=queue,
        timeout_ms=timeout_ms,
        max_attempts=max_attempts,
    )
    proc = subprocess.run(
        spec["command"],
        env=spec["env"],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if proc.returncode != 0:
        raise RuntimeError(stderr or stdout or f"gbrain shell submit failed with exit {proc.returncode}")
    if stdout:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"ok": True, "raw": stdout}
    return {"ok": True}
