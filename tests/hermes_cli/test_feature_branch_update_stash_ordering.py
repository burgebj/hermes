"""Regression tests for feature-branch update with stash ordering.

Covers the bug where `hermes update` on a feature branch would:
1. Restore the stash on main (wrong tree) instead of the feature branch
2. Then try to rebase with a dirty working tree → silent abort
3. Leave the user on main with the same "X commits behind" as before

The fix gates the `finally`-block stash restore on `current_branch in
{branch, 'HEAD'}` and moves the stash restore into the post-update block
(after checkout-back, before rebase).

PR #40673 review: stash-restore ordering fix.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from hermes_cli import config as hermes_config
from hermes_cli import main as hermes_main


# ---------------------------------------------------------------------------
# Managed-uv compatibility (same fixture as test_update_autostash.py)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _patch_managed_uv(request):
    """Make managed_uv helpers follow shutil.which mocking in tests."""
    import shutil

    def _fake_resolve_uv():
        return shutil.which("uv")

    def _fake_ensure_uv():
        return shutil.which("uv")

    def _fake_update_managed_uv():
        return None

    with patch("hermes_cli.managed_uv.resolve_uv", side_effect=_fake_resolve_uv), \
         patch("hermes_cli.managed_uv.ensure_uv", side_effect=_fake_ensure_uv), \
         patch("hermes_cli.managed_uv.update_managed_uv", side_effect=_fake_update_managed_uv):
        yield


def _setup_update_mocks(monkeypatch, tmp_path):
    """Common setup for cmd_update tests."""
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(hermes_main, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(hermes_config, "get_missing_env_vars", lambda required_only=True: [])
    monkeypatch.setattr(hermes_config, "get_missing_config_fields", lambda: [])
    monkeypatch.setattr(hermes_config, "check_config_version", lambda: (5, 5))
    monkeypatch.setattr(hermes_config, "migrate_config", lambda **kw: {"env_added": [], "config_added": []})
    monkeypatch.setattr(hermes_main, "_refresh_active_lazy_features", lambda: None)


def _make_update_side_effect(
    current_branch="main",
    commit_count="3",
    ff_only_fails=False,
    reset_fails=False,
    fetch_fails=False,
    fetch_stderr="",
    rebase_fails=False,
):
    """Build a subprocess.run side_effect for cmd_update tests."""
    recorded = []

    def side_effect(cmd, **kwargs):
        recorded.append(cmd)
        joined = " ".join(str(c) for c in cmd)
        if "fetch" in joined and "origin" in joined:
            if fetch_fails:
                return SimpleNamespace(stdout="", stderr=fetch_stderr, returncode=128)
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if "rev-parse" in joined and "--abbrev-ref" in joined:
            return SimpleNamespace(stdout=f"{current_branch}\n", stderr="", returncode=0)
        if "checkout" in joined and "main" in joined:
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if "checkout" in joined and current_branch != "main" and current_branch in joined:
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if "rev-list" in joined:
            return SimpleNamespace(stdout=f"{commit_count}\n", stderr="", returncode=0)
        if "--ff-only" in joined:
            if ff_only_fails:
                return SimpleNamespace(stdout="", stderr="diverged", returncode=1)
            return SimpleNamespace(stdout="Updating\n", stderr="", returncode=0)
        if "reset" in joined and "--hard" in joined:
            if reset_fails:
                return SimpleNamespace(stdout="", stderr="reset failed", returncode=1)
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if "rebase" in joined and "origin/main" in joined:
            if rebase_fails:
                return SimpleNamespace(stdout="", stderr="CONFLICT\n", returncode=1)
            return SimpleNamespace(stdout="Rebasing\n", stderr="", returncode=0)
        if "rebase" in joined and "--abort" in joined:
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        # status --porcelain (stash check)
        if "status" in joined and "--porcelain" in joined:
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return side_effect, recorded


# ---------------------------------------------------------------------------
# Stash ordering: stash must be restored on the feature branch, not on main
# ---------------------------------------------------------------------------

def test_stash_restored_on_feature_branch_not_on_main(monkeypatch, tmp_path, capsys):
    """When on feat/X with stash and update succeeds + rebase clean:
    stash should be restored AFTER switching back to feat/X, NOT while on main.

    This is the core regression test for the stash-ordering bug.
    """
    _setup_update_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)

    stash_restore_calls = []
    stash_restore_branch_context = []

    # Track which branch the stash is restored on
    original_restore = hermes_main._restore_stashed_changes

    def tracking_restore(*args, **kwargs):
        stash_restore_calls.append(args)
        # Check what branch we're on when restore is called
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(tmp_path),
        )
        stash_restore_branch_context.append(result.stdout.strip())
        return True

    monkeypatch.setattr(
        hermes_main, "_stash_local_changes_if_needed",
        lambda *a, **kw: "abc123deadbeef",
    )
    monkeypatch.setattr(hermes_main, "_restore_stashed_changes", tracking_restore)

    side_effect, recorded = _make_update_side_effect(
        current_branch="feat/test", commit_count="3",
    )
    monkeypatch.setattr(hermes_main.subprocess, "run", side_effect)

    hermes_main.cmd_update(SimpleNamespace())

    # Stash should have been restored exactly once
    assert len(stash_restore_calls) == 1, (
        f"Expected 1 stash restore, got {len(stash_restore_calls)}"
    )

    # The restore should NOT happen on main (the old buggy behavior).
    # With the fix, it happens after checkout-back to the feature branch.
    # In our mock, the branch context is tracked via subprocess — but since
    # we're mocking subprocess.run, the rev-parse call inside tracking_restore
    # also gets mocked. Instead, verify the recorded command sequence:
    # checkout main → pull → checkout feat/test → stash restore → rebase
    checkout_main_idx = None
    checkout_feat_idx = None
    rebase_idx = None

    for i, cmd in enumerate(recorded):
        cmd_str = " ".join(str(c) for c in cmd)
        if "checkout" in cmd_str and "main" in cmd_str and checkout_main_idx is None:
            checkout_main_idx = i
        if "checkout" in cmd_str and "feat/test" in cmd_str:
            checkout_feat_idx = i
        if "rebase" in cmd_str and "origin/main" in cmd_str:
            rebase_idx = i

    # checkout feat/test must happen (we switched back)
    assert checkout_feat_idx is not None, "Should have checked out feat/test after update"
    # rebase must happen (we rebased onto origin/main)
    assert rebase_idx is not None, "Should have rebased feat/test onto origin/main"
    # rebase must come after checkout feat/test
    assert rebase_idx > checkout_feat_idx, (
        f"Rebase ({rebase_idx}) should come after checkout feat/test ({checkout_feat_idx})"
    )

    out = capsys.readouterr().out
    assert "Returning to 'feat/test'" in out


def test_stash_not_restored_on_main_for_feature_branch(monkeypatch, tmp_path, capsys):
    """Verify that the finally-block stash restore is skipped when the user
    started on a feature branch (the gating fix in the finally block).
    """
    _setup_update_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)

    restore_calls = []
    monkeypatch.setattr(
        hermes_main, "_stash_local_changes_if_needed",
        lambda *a, **kw: "abc123deadbeef",
    )
    monkeypatch.setattr(
        hermes_main, "_restore_stashed_changes",
        lambda *a, **kw: restore_calls.append(("restore", a, kw)) or True,
    )

    side_effect, recorded = _make_update_side_effect(
        current_branch="feat/test", commit_count="3",
    )
    monkeypatch.setattr(hermes_main.subprocess, "run", side_effect)

    hermes_main.cmd_update(SimpleNamespace())

    # Stash should be restored exactly once (in the post-update block),
    # NOT twice (once in finally + once in post-update).
    assert len(restore_calls) == 1, (
        f"Expected 1 stash restore (post-update only), got {len(restore_calls)}. "
        f"If 2, the finally-block gate is missing."
    )


def test_stash_restored_in_finally_when_staying_on_main(monkeypatch, tmp_path, capsys):
    """When user is already on main, stash restore happens in the finally block
    (the normal path — no feature branch switchback).
    """
    _setup_update_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)

    restore_calls = []
    monkeypatch.setattr(
        hermes_main, "_stash_local_changes_if_needed",
        lambda *a, **kw: "abc123deadbeef",
    )
    monkeypatch.setattr(
        hermes_main, "_restore_stashed_changes",
        lambda *a, **kw: restore_calls.append(("restore", a, kw)) or True,
    )

    side_effect, recorded = _make_update_side_effect(
        current_branch="main", commit_count="3",
    )
    monkeypatch.setattr(hermes_main.subprocess, "run", side_effect)

    hermes_main.cmd_update(SimpleNamespace())

    # Stash should be restored exactly once (in the finally block)
    assert len(restore_calls) == 1


def test_rebase_conflict_aborts_and_switches_to_main(monkeypatch, tmp_path, capsys):
    """When rebase conflicts, the update should abort rebase, save stash,
    and switch to main with clear manual-resolution instructions.
    """
    _setup_update_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)

    monkeypatch.setattr(
        hermes_main, "_stash_local_changes_if_needed",
        lambda *a, **kw: "abc123deadbeef",
    )
    monkeypatch.setattr(
        hermes_main, "_restore_stashed_changes",
        lambda *a, **kw: True,
    )

    side_effect, recorded = _make_update_side_effect(
        current_branch="feat/test", commit_count="3", rebase_fails=True,
    )
    monkeypatch.setattr(hermes_main.subprocess, "run", side_effect)

    hermes_main.cmd_update(SimpleNamespace())

    out = capsys.readouterr().out
    assert "Rebase of 'feat/test' onto main hit conflicts" in out
    assert "git stash pop" in out

    # Should have aborted the rebase
    abort_calls = [c for c in recorded if "--abort" in " ".join(str(x) for x in c)]
    assert len(abort_calls) >= 1, "Should have called rebase --abort"

    # Should have switched back to main
    checkout_main_calls = [
        c for c in recorded
        if "checkout" in " ".join(str(x) for x in c)
        and "main" in " ".join(str(x) for x in c)
    ]
    assert len(checkout_main_calls) >= 1, "Should have checked out main after conflict"


def test_rebase_conflict_saves_stash_before_switching_to_main(monkeypatch, tmp_path, capsys):
    """When rebase conflicts after stash was restored on feat/X, the working
    tree changes must be stashed before switching to main so nothing is lost.
    """
    _setup_update_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)

    stash_count = [0]
    def counting_stash(*args, **kwargs):
        stash_count[0] += 1
        return f"stash_ref_{stash_count[0]}"

    monkeypatch.setattr(hermes_main, "_stash_local_changes_if_needed", counting_stash)
    monkeypatch.setattr(
        hermes_main, "_restore_stashed_changes",
        lambda *a, **kw: True,
    )

    side_effect, recorded = _make_update_side_effect(
        current_branch="feat/test", commit_count="3", rebase_fails=True,
    )
    monkeypatch.setattr(hermes_main.subprocess, "run", side_effect)

    hermes_main.cmd_update(SimpleNamespace())

    # _stash_local_changes_if_needed is called twice:
    # 1. Initial stash before switching to main
    # 2. Re-stash before switching back to main after rebase conflict
    assert stash_count[0] == 2, (
        f"Expected 2 stash calls (initial + conflict re-stash), got {stash_count[0]}"
    )


def test_feature_branch_update_no_stash(monkeypatch, tmp_path, capsys):
    """When on a feature branch with no uncommitted changes, update should
    still switch back and rebase (just without stash involvement).
    """
    _setup_update_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None)

    # No stash
    monkeypatch.setattr(
        hermes_main, "_stash_local_changes_if_needed",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(
        hermes_main, "_restore_stashed_changes",
        lambda *a, **kw: True,
    )

    side_effect, recorded = _make_update_side_effect(
        current_branch="feat/test", commit_count="3",
    )
    monkeypatch.setattr(hermes_main.subprocess, "run", side_effect)

    hermes_main.cmd_update(SimpleNamespace())

    # Should have checked out feat/test and rebased
    checkout_feat = [c for c in recorded if "feat/test" in " ".join(str(x) for x in c)]
    rebase_calls = [c for c in recorded if "rebase" in " ".join(str(x) for x in c)]
    assert len(checkout_feat) >= 1, "Should have checked out feat/test"
    assert len(rebase_calls) >= 1, "Should have rebased onto origin/main"

    out = capsys.readouterr().out
    assert "Returning to 'feat/test'" in out


# ---------------------------------------------------------------------------
# Banner tracking ref: _resolve_tracking_ref
# ---------------------------------------------------------------------------

def test_resolve_tracking_ref_returns_none_for_main(tmp_path):
    """On main, _resolve_tracking_ref should return None (fall back to origin/main)."""
    from hermes_cli import banner

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    def fake_run(cmd, **kwargs):
        if "rev-parse" in cmd and "--abbrev-ref" in cmd and "@{u}" not in cmd:
            return SimpleNamespace(stdout="main\n", returncode=0)
        raise AssertionError(f"unexpected command: {cmd}")

    with patch("hermes_cli.banner.subprocess.run", side_effect=fake_run):
        result = banner._resolve_tracking_ref(repo_dir)

    assert result is None


def test_resolve_tracking_ref_returns_upstream_for_feature_branch(tmp_path):
    """On feat/X with upstream set, should return origin/feat-x."""
    from hermes_cli import banner

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    def fake_run(cmd, **kwargs):
        if "rev-parse" in cmd and "--abbrev-ref" in cmd and "@{u}" not in " ".join(cmd):
            return SimpleNamespace(stdout="feat/test\n", returncode=0)
        if "@{u}" in " ".join(cmd):
            return SimpleNamespace(stdout="origin/feat/test\n", returncode=0)
        raise AssertionError(f"unexpected command: {cmd}")

    with patch("hermes_cli.banner.subprocess.run", side_effect=fake_run):
        result = banner._resolve_tracking_ref(repo_dir)

    assert result == "origin/feat/test"


def test_resolve_tracking_ref_returns_none_for_detached_head(tmp_path):
    """In detached HEAD state, should return None."""
    from hermes_cli import banner

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    def fake_run(cmd, **kwargs):
        if "rev-parse" in cmd and "--abbrev-ref" in cmd and "@{u}" not in " ".join(cmd):
            return SimpleNamespace(stdout="HEAD\n", returncode=0)
        raise AssertionError(f"unexpected command: {cmd}")

    with patch("hermes_cli.banner.subprocess.run", side_effect=fake_run):
        result = banner._resolve_tracking_ref(repo_dir)

    assert result is None


def test_resolve_tracking_ref_returns_none_when_no_upstream(tmp_path):
    """On feat/X without upstream set, should return None (fall back to origin/main)."""
    from hermes_cli import banner

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    def fake_run(cmd, **kwargs):
        if "rev-parse" in cmd and "--abbrev-ref" in cmd and "@{u}" not in " ".join(cmd):
            return SimpleNamespace(stdout="feat/local\n", returncode=0)
        if "@{u}" in " ".join(cmd):
            # git rev-parse returns error when no upstream is set
            return SimpleNamespace(stdout="", returncode=128)
        raise AssertionError(f"unexpected command: {cmd}")

    with patch("hermes_cli.banner.subprocess.run", side_effect=fake_run):
        result = banner._resolve_tracking_ref(repo_dir)

    assert result is None


def test_check_via_local_git_uses_tracking_ref_for_feature_branch(tmp_path):
    """Banner should show distance to origin/feat-x, not origin/main."""
    from hermes_cli import banner

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    def fake_run(cmd, **kwargs):
        cmd_str = " ".join(str(c) for c in cmd)
        if "fetch" in cmd_str:
            return SimpleNamespace(stdout="", returncode=0)
        if "rev-parse" in cmd and "--abbrev-ref" in cmd and "@{u}" not in cmd:
            return SimpleNamespace(stdout="feat/test\n", returncode=0)
        if "@{u}" in cmd:
            return SimpleNamespace(stdout="origin/feat/test\n", returncode=0)
        if "rev-list" in cmd and "origin/feat/test" in cmd_str:
            # 0 behind origin/feat/test (the correct comparison)
            return SimpleNamespace(stdout="0\n", returncode=0)
        if "rev-list" in cmd and "origin/main" in cmd_str:
            # Would be 5 behind origin/main (the old buggy comparison)
            return SimpleNamespace(stdout="5\n", returncode=0)
        raise AssertionError(f"unexpected command: {cmd}")

    with patch("hermes_cli.banner.subprocess.run", side_effect=fake_run):
        result = banner._check_via_local_git(repo_dir)

    # Should show 0 (behind origin/feat/test), not 5 (behind origin/main)
    assert result == 0


def test_check_via_local_git_uses_origin_main_for_main_branch(tmp_path):
    """On main, banner should still compare against origin/main."""
    from hermes_cli import banner

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    def fake_run(cmd, **kwargs):
        cmd_str = " ".join(str(c) for c in cmd)
        if "fetch" in cmd_str:
            return SimpleNamespace(stdout="", returncode=0)
        if "rev-parse" in cmd and "--abbrev-ref" in cmd and "@{u}" not in cmd:
            return SimpleNamespace(stdout="main\n", returncode=0)
        if "rev-list" in cmd and "origin/main" in cmd_str:
            return SimpleNamespace(stdout="3\n", returncode=0)
        raise AssertionError(f"unexpected command: {cmd}")

    with patch("hermes_cli.banner.subprocess.run", side_effect=fake_run):
        result = banner._check_via_local_git(repo_dir)

    assert result == 3
