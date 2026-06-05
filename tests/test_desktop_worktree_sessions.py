"""Tests for the desktop "new session in a worktree" feature.

Covers the three backend pieces:
  * ``SessionDB.set_session_worktree`` persistence + read-back (hermes_state).
  * ``tui_gateway.server._git_is_repo`` / ``_create_session_worktree`` — worktree
    creation wired into ``session.create``, with eager DB-row persistence.
  * ``hermes_cli.web_server._cleanup_session_worktree`` — archive-time cleanup
    that honours the unpushed-commits guard.

The worktree machinery itself lives in ``cli.py`` and is exercised here against
a real temporary git repo (no mocks) so the create/cleanup round-trip is proven
end-to-end, not just in unit isolation.
"""

import os
import subprocess

import pytest

from hermes_state import SessionDB


def _init_git_repo(path: str, *, with_commit: bool = True, with_remote: bool = False) -> None:
    """Initialise a real git repo at *path* for worktree tests."""
    subprocess.run(["git", "init", "-q", path], check=True)
    subprocess.run(["git", "-C", path, "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", path, "config", "user.name", "Tester"], check=True)
    if with_commit:
        readme = os.path.join(path, "README.md")
        with open(readme, "w", encoding="utf-8") as f:
            f.write("hello\n")
        subprocess.run(["git", "-C", path, "add", "."], check=True)
        subprocess.run(["git", "-C", path, "commit", "-qm", "init"], check=True)
    if with_remote:
        # A bare "remote" so unpushed-commit detection has a baseline to compare
        # against (without a remote, _worktree_has_unpushed_commits treats the
        # worktree as having nothing unpushed).
        remote = path + "-remote.git"
        subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
        subprocess.run(["git", "-C", path, "remote", "add", "origin", remote], check=True)
        subprocess.run(["git", "-C", path, "push", "-q", "origin", "HEAD"], check=True)


class TestSetSessionWorktree:
    def test_persists_and_reads_back(self, tmp_path):
        db = SessionDB(db_path=tmp_path / "state.db")
        try:
            db.create_session("s1", source="tui", cwd="/repo/.worktrees/hermes-abc")
            assert db.set_session_worktree(
                "s1", "/repo/.worktrees/hermes-abc", "hermes/hermes-abc", "/repo"
            )
            row = db.get_session("s1")
            assert row["worktree_path"] == "/repo/.worktrees/hermes-abc"
            assert row["worktree_branch"] == "hermes/hermes-abc"
            assert row["worktree_repo_root"] == "/repo"
        finally:
            db.close()

    def test_clear_mapping(self, tmp_path):
        db = SessionDB(db_path=tmp_path / "state.db")
        try:
            db.create_session("s1", source="tui")
            db.set_session_worktree("s1", "/wt", "hermes/x", "/repo")
            assert db.set_session_worktree("s1", None)
            row = db.get_session("s1")
            assert row["worktree_path"] is None
            assert row["worktree_branch"] is None
            assert row["worktree_repo_root"] is None
        finally:
            db.close()

    def test_missing_row_returns_false(self, tmp_path):
        db = SessionDB(db_path=tmp_path / "state.db")
        try:
            assert db.set_session_worktree("nope", "/wt") is False
        finally:
            db.close()


class TestGitIsRepo:
    def test_true_for_repo(self, tmp_path):
        from tui_gateway import server

        repo = str(tmp_path / "repo")
        _init_git_repo(repo)
        assert server._git_is_repo(repo) is True

    def test_true_for_repo_without_commits(self, tmp_path):
        # A freshly `git init`-ed repo (no commits, no current branch) is still a
        # repo — this is the case a branch-name probe would get wrong.
        from tui_gateway import server

        repo = str(tmp_path / "fresh")
        _init_git_repo(repo, with_commit=False)
        assert server._git_is_repo(repo) is True

    def test_false_for_plain_dir(self, tmp_path):
        from tui_gateway import server

        plain = str(tmp_path / "plain")
        os.makedirs(plain)
        assert server._git_is_repo(plain) is False

    def test_false_for_empty_or_missing(self, tmp_path):
        from tui_gateway import server

        assert server._git_is_repo("") is False
        assert server._git_is_repo(str(tmp_path / "does-not-exist")) is False


class TestCreateSessionWorktree:
    def test_creates_worktree_and_persists_row(self, tmp_path, monkeypatch):
        from tui_gateway import server

        repo = str(tmp_path / "repo")
        _init_git_repo(repo)

        db = SessionDB(db_path=tmp_path / "state.db")
        monkeypatch.setattr(server, "_db", db)
        try:
            session = {"session_key": "KEY1", "cwd": repo, "explicit_cwd": True}
            info = server._create_session_worktree(session, repo)

            assert info is not None
            # cwd repointed into the worktree, on a hermes/ branch.
            assert ".worktrees" in info["path"]
            assert info["branch"].startswith("hermes/")
            assert os.path.isdir(info["path"])
            assert session["cwd"] == info["path"]
            assert session["worktree"] == info

            # Row persisted EAGERLY (not lazily) with the worktree mapping.
            row = db.get_session("KEY1")
            assert row is not None
            assert row["cwd"] == info["path"]
            assert row["worktree_path"] == info["path"]
            assert row["worktree_branch"] == info["branch"]
        finally:
            db.close()

    def test_non_repo_returns_none(self, tmp_path, monkeypatch):
        from tui_gateway import server

        plain = str(tmp_path / "plain")
        os.makedirs(plain)
        db = SessionDB(db_path=tmp_path / "state.db")
        monkeypatch.setattr(server, "_db", db)
        try:
            session = {"session_key": "KEY2", "cwd": plain, "explicit_cwd": True}
            assert server._create_session_worktree(session, plain) is None
            # cwd unchanged, no row stamped with a worktree.
            assert session["cwd"] == plain
            assert "worktree" not in session
        finally:
            db.close()


class TestCleanupSessionWorktree:
    def test_removes_clean_worktree_and_clears_mapping(self, tmp_path, monkeypatch):
        from tui_gateway import server
        from hermes_cli import web_server

        repo = str(tmp_path / "repo")
        _init_git_repo(repo, with_remote=True)  # remote => unpushed detection active

        db = SessionDB(db_path=tmp_path / "state.db")
        monkeypatch.setattr(server, "_db", db)
        try:
            session = {"session_key": "KEY3", "cwd": repo, "explicit_cwd": True}
            info = server._create_session_worktree(session, repo)
            assert info and os.path.isdir(info["path"])

            # No commits made in the worktree => nothing unpushed => removable.
            preserved = web_server._cleanup_session_worktree(db, "KEY3")
            assert preserved is False
            assert not os.path.isdir(info["path"])
            # Mapping cleared so a repeat archive is a no-op.
            row = db.get_session("KEY3")
            assert row["worktree_path"] is None
        finally:
            db.close()

    def test_preserves_worktree_with_unpushed_commits(self, tmp_path, monkeypatch):
        from tui_gateway import server
        from hermes_cli import web_server

        repo = str(tmp_path / "repo")
        _init_git_repo(repo, with_remote=True)

        db = SessionDB(db_path=tmp_path / "state.db")
        monkeypatch.setattr(server, "_db", db)
        try:
            session = {"session_key": "KEY4", "cwd": repo, "explicit_cwd": True}
            info = server._create_session_worktree(session, repo)
            assert info and os.path.isdir(info["path"])

            # Make an unpushed commit on the worktree branch — the guard must
            # then refuse to delete it.
            wt = info["path"]
            with open(os.path.join(wt, "work.txt"), "w", encoding="utf-8") as f:
                f.write("unpushed work\n")
            subprocess.run(["git", "-C", wt, "add", "."], check=True)
            subprocess.run(["git", "-C", wt, "commit", "-qm", "wip"], check=True)

            preserved = web_server._cleanup_session_worktree(db, "KEY4")
            assert preserved is True
            assert os.path.isdir(wt)  # still there — guard kept it
            # Mapping retained so a later (post-push) archive can retry.
            row = db.get_session("KEY4")
            assert row["worktree_path"] == wt
        finally:
            db.close()

    def test_no_worktree_returns_none(self, tmp_path):
        from hermes_cli import web_server

        db = SessionDB(db_path=tmp_path / "state.db")
        try:
            db.create_session("plain", source="tui")
            assert web_server._cleanup_session_worktree(db, "plain") is None
        finally:
            db.close()
