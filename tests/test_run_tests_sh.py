"""Regression tests for ``scripts/run_tests.sh`` platform compatibility."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_TESTS_SH = REPO_ROOT / "scripts" / "run_tests.sh"


def _bash_path() -> str | None:
    return shutil.which("bash")


def _copy_run_tests_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Materialize a tiny fake repo around ``run_tests.sh``."""
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy2(RUN_TESTS_SH, scripts_dir / "run_tests.sh")
    output_path = tmp_path / "runner-env.json"
    stub = textwrap.dedent(
        f"""
        import json
        import os
        import sys
        from pathlib import Path

        Path({str(output_path)!r}).write_text(
            json.dumps(
                {{
                    "argv": sys.argv[1:],
                    "env": {{
                        "HOME": os.environ.get("HOME"),
                        "USERPROFILE": os.environ.get("USERPROFILE"),
                        "LOCALAPPDATA": os.environ.get("LOCALAPPDATA"),
                        "APPDATA": os.environ.get("APPDATA"),
                        "TEMP": os.environ.get("TEMP"),
                        "TMP": os.environ.get("TMP"),
                        "HOMEDRIVE": os.environ.get("HOMEDRIVE"),
                        "HOMEPATH": os.environ.get("HOMEPATH"),
                        "PYTHONUTF8": os.environ.get("PYTHONUTF8"),
                        "PYTHONIOENCODING": os.environ.get("PYTHONIOENCODING"),
                    }},
                }},
                indent=2,
                sort_keys=True,
            ) + "\\n",
            encoding="utf-8",
        )
        """
    ).strip()
    (scripts_dir / "run_tests_parallel.py").write_text(stub + "\n", encoding="utf-8")
    return repo, output_path


def _write_windows_scripts_python_shim(repo: Path) -> Path:
    """Create a Git-Bash-friendly ``.venv/Scripts/python`` launcher."""
    scripts_dir = repo / ".venv" / "Scripts"
    scripts_dir.mkdir(parents=True)
    shim = scripts_dir / "python"
    shim.write_text(
        "#!/usr/bin/env bash\n"
        f"exec {shlex.quote(sys.executable)} \"$@\"\n",
        encoding="utf-8",
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
    return shim


def test_run_tests_sh_mentions_windows_python_exe_probe() -> None:
    """Static guard: keep probing the real Windows venv layout."""
    source = RUN_TESTS_SH.read_text(encoding="utf-8")
    assert "Scripts/python.exe" in source, (
        "run_tests.sh must probe Windows virtualenv interpreters under "
        "Scripts/python.exe"
    )


@pytest.mark.skipif(_bash_path() is None, reason="requires bash")
def test_run_tests_sh_accepts_windows_scripts_layout_and_preserves_env(tmp_path: Path) -> None:
    """Behavioral repro: a Windows-style ``.venv/Scripts`` layout must work.

    We use a ``Scripts/python`` shim instead of a real copied ``python.exe`` so
    the test stays cheap and cross-platform while still exercising the Windows
    branch in ``run_tests.sh``.
    """
    repo, output_path = _copy_run_tests_fixture(tmp_path)
    _write_windows_scripts_python_shim(repo)

    home = tmp_path / "home"
    userprofile = tmp_path / "Users" / "alice"
    local_appdata = userprofile / "AppData" / "Local"
    appdata = userprofile / "AppData" / "Roaming"
    temp_dir = tmp_path / "temp"
    for path in (home, userprofile, local_appdata, appdata, temp_dir):
        path.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(userprofile),
            "LOCALAPPDATA": str(local_appdata),
            "APPDATA": str(appdata),
            "TEMP": str(temp_dir),
            "TMP": str(temp_dir),
            "HOMEDRIVE": "C:",
            "HOMEPATH": r"\Users\alice",
        }
    )

    result = subprocess.run(
        [_bash_path(), str(repo / "scripts" / "run_tests.sh"), "--", "-q"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        "run_tests.sh failed to launch a Windows-style Scripts/python venv:\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    assert output_path.exists(), (
        "run_tests_parallel.py stub never ran, so run_tests.sh did not "
        "successfully hand off to the detected interpreter"
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    child_env = payload["env"]
    assert payload["argv"] == ["--", "-q"]
    assert child_env["HOME"] == str(home)
    assert child_env["USERPROFILE"] == str(userprofile)
    assert child_env["LOCALAPPDATA"] == str(local_appdata)
    assert child_env["APPDATA"] == str(appdata)
    assert child_env["TEMP"] == str(temp_dir)
    assert child_env["TMP"] == str(temp_dir)
    assert child_env["HOMEDRIVE"] == "C:"
    assert child_env["HOMEPATH"] == r"\Users\alice"
    assert child_env["PYTHONUTF8"] == "1"
    assert child_env["PYTHONIOENCODING"] == "utf-8"
