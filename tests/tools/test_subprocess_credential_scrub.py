"""Tests for credential scrubbing of subprocess environments.

Covers the OpenShell-inspired hardening: the encryption passphrase is always
stripped, and credential-shaped vars are swept (config-gated) on top of the
existing provider blocklist.
"""

from __future__ import annotations

from hermes_constants import get_hermes_home


def _set_scrub(enabled: bool) -> None:
    (get_hermes_home() / "config.yaml").write_text(
        f"security:\n  credential_broker:\n    scrub_subprocess_env: {str(enabled).lower()}\n",
        encoding="utf-8",
    )


# ── Terminal backend — tools/environments/local.py ──────────────────────────


def test_encryption_passphrase_always_stripped_from_terminal_env():
    from tools.environments.local import _make_run_env, _sanitize_subprocess_env

    env = {"HERMES_ENCRYPTION_PASSPHRASE": "topsecret", "PATH": "/usr/bin"}
    assert "HERMES_ENCRYPTION_PASSPHRASE" not in _sanitize_subprocess_env(env)
    assert "HERMES_ENCRYPTION_PASSPHRASE" not in _make_run_env(env)


def test_passphrase_stripped_even_with_scrub_disabled():
    # The unconditional strip must ignore the config flag entirely.
    _set_scrub(False)
    from tools.environments.local import _sanitize_subprocess_env

    out = _sanitize_subprocess_env({"HERMES_ENCRYPTION_PASSPHRASE": "x", "PATH": "/usr/bin"})
    assert "HERMES_ENCRYPTION_PASSPHRASE" not in out
    assert out.get("PATH") == "/usr/bin"


def test_shape_sweep_strips_unlisted_credential_var():
    _set_scrub(True)
    from tools.environments.local import _sanitize_subprocess_env

    out = _sanitize_subprocess_env({"ACME_API_KEY": "ak-1", "EDITOR": "vim"})
    assert "ACME_API_KEY" not in out  # caught by the credential-shape sweep
    assert out.get("EDITOR") == "vim"  # ordinary vars preserved


def test_shape_sweep_off_when_disabled():
    _set_scrub(False)
    from tools.environments.local import _sanitize_subprocess_env

    out = _sanitize_subprocess_env({"ACME_API_KEY": "ak-1"})
    # With the sweep off, a var not in the explicit blocklist passes through.
    assert out.get("ACME_API_KEY") == "ak-1"


def test_passthrough_allowlist_still_passes_a_shaped_var():
    _set_scrub(True)
    from tools.env_passthrough import clear_env_passthrough, register_env_passthrough
    from tools.environments.local import _sanitize_subprocess_env

    register_env_passthrough(["ACME_API_KEY"])
    try:
        out = _sanitize_subprocess_env({"ACME_API_KEY": "ak-1"})
        assert out.get("ACME_API_KEY") == "ak-1"
    finally:
        clear_env_passthrough()


# ── Code-execution sandbox — tools/code_execution_tool.py ───────────────────


def test_encryption_passphrase_stripped_from_execute_code_child():
    from tools.code_execution_tool import _scrub_child_env

    child = _scrub_child_env(
        {"HERMES_ENCRYPTION_PASSPHRASE": "topsecret", "PATH": "/usr/bin", "HOME": "/h"},
        is_passthrough=lambda _: False,
        is_windows=False,
    )
    assert "HERMES_ENCRYPTION_PASSPHRASE" not in child
    assert child.get("PATH") and child.get("HOME")
