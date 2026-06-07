"""Regression tests for _apply_profile_override HERMES_HOME guard (issue #22502).

When HERMES_HOME is set to the hermes root (e.g. systemd hardcodes
HERMES_HOME=/root/.hermes), _apply_profile_override must still read
active_profile and update HERMES_HOME to the profile directory.

When HERMES_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path



def _run_apply_profile_override(
    tmp_path, monkeypatch, *, hermes_home: str | None, active_profile: str | None,
    argv: list[str] | None = None, hermes_profile: str | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["HERMES_HOME"] after the call,
    or None if unset.
    """
    hermes_root = tmp_path / ".hermes"
    hermes_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (hermes_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (hermes_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    if hermes_profile and hermes_profile != "default":
        (hermes_root / "profiles" / hermes_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if hermes_home is not None:
        monkeypatch.setenv("HERMES_HOME", hermes_home)
    else:
        monkeypatch.delenv("HERMES_HOME", raising=False)
    if hermes_profile is not None:
        monkeypatch.setenv("HERMES_PROFILE", hermes_profile)
    else:
        monkeypatch.delenv("HERMES_PROFILE", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["hermes", "gateway", "start"])

    from hermes_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("HERMES_HOME")


class TestApplyProfileOverrideHermesHomeGuard:
    """Regression guard for issue #22502.

    Verifies that HERMES_HOME pointing to the hermes root does NOT suppress
    the active_profile check, while HERMES_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_hermes_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """HERMES_HOME=/root/.hermes + active_profile=coder must redirect
        HERMES_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets HERMES_HOME to the hermes root
        and the user switches to a profile via `hermes profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        hermes_root = tmp_path / ".hermes"
        hermes_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=str(hermes_root),
            active_profile="coder",
        )

        assert result is not None, "HERMES_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected HERMES_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected HERMES_HOME to end with 'coder', got: {result!r}"
        )

    def test_hermes_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """HERMES_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with HERMES_HOME already set to a specific profile must stay in that
        profile.
        """
        hermes_root = tmp_path / ".hermes"
        profile_dir = hermes_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (hermes_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["hermes", "gateway", "start"])

        from hermes_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("HERMES_HOME") == str(profile_dir), (
            "HERMES_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_hermes_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: HERMES_HOME unset + active_profile=coder must set
        HERMES_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_hermes_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect HERMES_HOME."""
        hermes_root = tmp_path / ".hermes"
        hermes_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("HERMES_HOME", raising=False)
        monkeypatch.delenv("HERMES_PROFILE", raising=False)
        monkeypatch.setattr(sys, "argv", ["hermes", "gateway", "start"])
        (hermes_root / "active_profile").write_text("default")

        from hermes_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("HERMES_HOME") is None


class TestApplyProfileOverrideHermesProfileEnv:
    """Regression guard for issue #29948.

    HERMES_PROFILE env var must select the profile dir when HERMES_HOME and
    -p flag are unset.  Without this, sibling gateways launched as
    ``HERMES_PROFILE=alice hermes telegram --replace`` and
    ``HERMES_PROFILE=bob hermes telegram --replace`` from the same $HOME both
    fall through to ``active_profile`` and resolve to the same
    ``gateway.pid`` — ``--replace`` then SIGKILLs the sibling.
    """

    def test_hermes_profile_env_selects_profile(self, tmp_path, monkeypatch):
        """HERMES_PROFILE=alice (no HERMES_HOME, no -p flag) must resolve
        HERMES_HOME to .../profiles/alice.
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=None,
            active_profile=None,
            hermes_profile="alice",
        )

        assert result is not None
        assert "profiles" in result
        assert result.endswith("alice")

    def test_hermes_profile_env_distinct_pidfiles_for_siblings(
        self, tmp_path, monkeypatch
    ):
        """Two gateways with distinct HERMES_PROFILE values must resolve to
        distinct profile directories — the actual repro from issue #29948.
        """
        alice_home = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=None,
            active_profile=None,
            hermes_profile="alice",
        )

        bob_home = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=None,
            active_profile=None,
            hermes_profile="bob",
        )

        assert alice_home != bob_home, (
            f"alice and bob must resolve to distinct profile dirs, got "
            f"alice={alice_home!r} bob={bob_home!r}"
        )
        assert alice_home and alice_home.endswith("alice")
        assert bob_home and bob_home.endswith("bob")

    def test_hermes_profile_env_beats_active_profile(self, tmp_path, monkeypatch):
        """When both HERMES_PROFILE and active_profile are set, HERMES_PROFILE wins.

        Active_profile is the sticky default; HERMES_PROFILE is explicit per-process
        intent. The explicit env var must take precedence so an operator can run
        ``HERMES_PROFILE=alice hermes telegram`` without first switching the
        sticky default.
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=None,
            active_profile="coder",
            hermes_profile="alice",
        )

        assert result is not None
        assert result.endswith("alice"), (
            f"HERMES_PROFILE=alice must override active_profile=coder, got {result!r}"
        )

    def test_p_flag_beats_hermes_profile_env(self, tmp_path, monkeypatch):
        """-p flag is the highest-priority selector and must beat HERMES_PROFILE."""
        hermes_root = tmp_path / ".hermes"
        hermes_root.mkdir(parents=True, exist_ok=True)
        (hermes_root / "profiles" / "alice").mkdir(parents=True, exist_ok=True)
        (hermes_root / "profiles" / "bob").mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("HERMES_HOME", raising=False)
        monkeypatch.setenv("HERMES_PROFILE", "bob")
        monkeypatch.setattr(sys, "argv", ["hermes", "-p", "alice", "gateway", "start"])

        from hermes_cli.main import _apply_profile_override
        _apply_profile_override()

        result = os.environ.get("HERMES_HOME")
        assert result is not None
        assert result.endswith("alice"), (
            f"-p flag must beat HERMES_PROFILE, got {result!r}"
        )

    def test_hermes_home_profile_path_beats_hermes_profile_env(
        self, tmp_path, monkeypatch
    ):
        """HERMES_HOME already pointing at a profile dir is already-resolved
        and must be trusted over a stale HERMES_PROFILE inherited from the parent.
        """
        hermes_root = tmp_path / ".hermes"
        alice_dir = hermes_root / "profiles" / "alice"
        alice_dir.mkdir(parents=True, exist_ok=True)
        (hermes_root / "profiles" / "bob").mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(alice_dir))
        monkeypatch.setenv("HERMES_PROFILE", "bob")
        monkeypatch.setattr(sys, "argv", ["hermes", "gateway", "start"])

        from hermes_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("HERMES_HOME") == str(alice_dir), (
            "HERMES_HOME pointing to a profile dir must be trusted as-is"
        )

    def test_invalid_hermes_profile_env_is_ignored(self, tmp_path, monkeypatch):
        """An invalid HERMES_PROFILE value (e.g. uppercase, special chars) must
        not abort or be passed through to resolve_profile_env. Falls through
        to active_profile / default.
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=None,
            active_profile=None,
            hermes_profile="Not Valid!",  # spaces + uppercase + punctuation
        )

        assert result is None, (
            "Invalid HERMES_PROFILE should be silently ignored, not cause a "
            f"redirect or abort. Got HERMES_HOME={result!r}"
        )

    def test_hermes_profile_default_does_not_redirect(self, tmp_path, monkeypatch):
        """HERMES_PROFILE=default is a no-op — there is no profiles/default/ dir;
        the default profile IS ~/.hermes itself. Must leave HERMES_HOME unset.
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=None,
            active_profile=None,
            hermes_profile="default",
        )

        assert result is None, (
            f"HERMES_PROFILE=default should not redirect, got HERMES_HOME={result!r}"
        )

    def test_empty_hermes_profile_env_is_ignored(self, tmp_path, monkeypatch):
        """HERMES_PROFILE='' or whitespace-only must be treated as unset."""
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=None,
            active_profile=None,
            hermes_profile="   ",
        )

        assert result is None
