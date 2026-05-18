"""Contract tests for ``docker/entrypoint.sh`` HERMES_HOME preflight.

Rootless Podman / quadlet deployments that pin ``User=%U:%G`` skip the gosu
privilege-drop branch and hit the directory bootstrap as a non-root,
non-hermes UID.  When the bind-mount source on the host is misaligned (e.g.
the user forgot to ``chown`` the host-side dir, or SELinux relabel fails),
``mkdir -p`` would otherwise emit an opaque ``Permission denied`` for every
brace-expanded subdirectory and crash the container under ``set -e``.

The fix adds an early writability check that surfaces the actual problem
plus a host-side remediation hint instead of crashing through ``mkdir``.

See https://github.com/NousResearch/hermes-agent/issues/20377
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = REPO_ROOT / "docker" / "entrypoint.sh"


@pytest.fixture(scope="module")
def entrypoint_text() -> str:
    if not ENTRYPOINT.exists():
        pytest.skip("docker/entrypoint.sh not present in this checkout")
    return ENTRYPOINT.read_text(encoding="utf-8")


def test_entrypoint_has_hermes_home_writable_preflight(entrypoint_text: str):
    """A writable check on ``$HERMES_HOME`` must guard the mkdir bootstrap."""
    # The preflight has to run AFTER the venv activation block (which is the
    # boundary between privileged and unprivileged code), and BEFORE the
    # bootstrap mkdir that brace-expands subdirectories.
    venv_idx = entrypoint_text.find('source "${INSTALL_DIR}/.venv/bin/activate"')
    mkdir_idx = entrypoint_text.find(
        'mkdir -p "$HERMES_HOME"/{cron,sessions,logs,hooks,memories,skills,skins,plans,workspace,home}'
    )
    preflight_idx = entrypoint_text.find('[ ! -w "$HERMES_HOME" ]')

    assert venv_idx != -1, "venv activation marker missing — entrypoint changed shape"
    assert mkdir_idx != -1, "directory bootstrap mkdir missing — entrypoint changed shape"
    assert preflight_idx != -1, (
        "Expected an `[ ! -w \"$HERMES_HOME\" ]` writability preflight before the "
        "mkdir bootstrap so rootless Podman misconfig surfaces a clear error "
        "instead of crashing under set -e (#20377)."
    )
    assert venv_idx < preflight_idx < mkdir_idx, (
        "Writability preflight must run after venv activation and before the "
        "mkdir bootstrap so the user gets diagnostic output before set -e fires."
    )


def test_entrypoint_preflight_message_mentions_uid_and_remediation(entrypoint_text: str):
    """The diagnostic must include uid/gid context plus a host-side fix hint."""
    # Locate the heredoc that follows the writability check.
    preflight_idx = entrypoint_text.find('[ ! -w "$HERMES_HOME" ]')
    block = entrypoint_text[preflight_idx:preflight_idx + 1500]

    # Diagnostic should print uid/gid so users can correlate with `podman top`.
    assert "uid=$(id -u)" in block, "Preflight error should report the running uid"
    assert "gid=$(id -g)" in block, "Preflight error should report the running gid"

    # And should at least hint at the rootless / User=%U:%G interaction.
    lower = block.lower()
    assert "rootless" in lower or "user=%u:%g" in lower, (
        "Preflight should mention rootless / User=%U:%G so users can map the "
        "error to their quadlet config (#20377)."
    )

    # And should include a chown remediation step.
    assert "chown" in block, (
        "Preflight should include a chown-on-host remediation hint."
    )

    # And the script should exit with a non-zero status so the container
    # restarts and the operator sees the error in `journalctl`.
    assert "exit 1" in block, "Preflight must `exit 1` on unwritable HERMES_HOME"


def test_entrypoint_preflight_runtime_behavior(tmp_path):
    """End-to-end: run a stubbed entrypoint and verify exit + diagnostic."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash not available")

    # Make a read-only fake HERMES_HOME so the preflight check trips.
    fake_home = tmp_path / "hermes_home"
    fake_home.mkdir()
    # Strip write bit for owner; we are not running as root so this works.
    fake_home.chmod(stat.S_IRUSR | stat.S_IXUSR)

    # Stub INSTALL_DIR with a no-op activate script and an empty .env.example.
    install_dir = tmp_path / "install"
    (install_dir / ".venv" / "bin").mkdir(parents=True)
    (install_dir / ".venv" / "bin" / "activate").write_text("# stub activate\n")
    (install_dir / ".env.example").write_text("STUB=1\n")
    (install_dir / "cli-config.yaml.example").write_text("stub: true\n")
    (install_dir / "docker").mkdir()
    (install_dir / "docker" / "SOUL.md").write_text("stub\n")

    # We override HERMES_HOME and INSTALL_DIR via env so the script never
    # needs the real container layout.  We also bypass the gosu branch by
    # forcing UID != 0 (the test process is not root).  The privileged
    # branch ends in `exec gosu`, which would crash here.
    env = {
        **os.environ,
        "HERMES_HOME": str(fake_home),
        "INSTALL_DIR": str(install_dir),
        "PATH": os.environ.get("PATH", ""),
    }

    # Run a tiny harness that sources the entrypoint up to (but not past)
    # the preflight.  Easiest portable approach: invoke the script and
    # interrupt with `false` after the writability check via a trap.  We
    # rely on the script's `exit 1` path so we just need to capture stderr.
    proc = subprocess.run(
        [bash, str(ENTRYPOINT)],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    # The privileged branch should not be entered (we're not uid 0), so the
    # script reaches the preflight and exits 1.
    assert proc.returncode != 0, (
        f"Entrypoint should fail when HERMES_HOME is unwritable; got rc={proc.returncode}\n"
        f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    )
    diagnostic = proc.stderr or proc.stdout
    assert "is not writable" in diagnostic, (
        f"Preflight diagnostic missing from output: {diagnostic!r}"
    )
