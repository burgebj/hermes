import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


@pytest.fixture
def temp_git_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir)
        (repo_dir / ".git").mkdir()
        yield repo_dir


class TestGitBranch:
    def test_list_branches_success(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="* main\n  feature/test\n  develop",
                returncode=0,
                stderr="",
            )
            from tools.git_branch import git_branch
            output = git_branch(operation="list")
            data = json.loads(output)
            assert data["success"] is True
            assert "branches" in data
            assert data["current_branch"] == "main"

    def test_list_branches_failure(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                returncode=1,
                stderr="fatal: not a git repository",
            )
            from tools.git_branch import git_branch
            output = git_branch(operation="list")
            data = json.loads(output)
            assert data["success"] is False

    def test_create_branch_success(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            from tools.git_branch import git_branch
            output = git_branch(operation="create", branch_name="feature/new")
            data = json.loads(output)
            assert data["success"] is True
            assert data["operation"] == "create"
            assert data["branch"] == "feature/new"

    def test_create_branch_no_name(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        from tools.git_branch import git_branch
        output = git_branch(operation="create")
        data = json.loads(output)
        assert data["success"] is False
        assert "branch_name required" in data["error"]

    def test_create_branch_with_start_point(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            from tools.git_branch import git_branch
            output = git_branch(operation="create", branch_name="feature/new", start_point="main")
            data = json.loads(output)
            assert data["success"] is True

    def test_delete_branch_safe(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            from tools.git_branch import git_branch
            output = git_branch(operation="delete", branch_name="feature/old")
            data = json.loads(output)
            assert data["success"] is True
            assert data["force"] is False

    def test_delete_branch_force(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            from tools.git_branch import git_branch
            output = git_branch(operation="delete", branch_name="feature/old", force=True)
            data = json.loads(output)
            assert data["success"] is True
            assert data["force"] is True

    def test_delete_branch_no_name(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        from tools.git_branch import git_branch
        output = git_branch(operation="delete")
        data = json.loads(output)
        assert data["success"] is False
        assert "branch_name required" in data["error"]

    def test_switch_branch_success(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            from tools.git_branch import git_branch
            output = git_branch(operation="switch", branch_name="feature/switch")
            data = json.loads(output)
            assert data["success"] is True
            assert data["operation"] == "switch"
            assert data["branch"] == "feature/switch"

    def test_switch_branch_no_name(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        from tools.git_branch import git_branch
        output = git_branch(operation="switch")
        data = json.loads(output)
        assert data["success"] is False
        assert "branch_name required" in data["error"]

    def test_unknown_operation(self, temp_git_repo, monkeypatch):
        monkeypatch.chdir(temp_git_repo)
        from tools.git_branch import git_branch
        output = git_branch(operation="invalid_op")
        data = json.loads(output)
        assert data["success"] is False
        assert "Unknown operation" in data["error"]

    def test_with_cwd_parameter(self, temp_git_repo, monkeypatch):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="* main",
                returncode=0,
                stderr="",
            )
            from tools.git_branch import git_branch
            output = git_branch(operation="list", cwd=str(temp_git_repo))
            data = json.loads(output)
            assert data["success"] is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "git"


class TestGitBranchRequirements:
    def test_git_available(self):
        from tools.git_branch import check_git_branch_requirements
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = check_git_branch_requirements()
            assert result is True

    def test_git_not_available(self):
        from tools.git_branch import check_git_branch_requirements
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = check_git_branch_requirements()
            assert result is False


class TestGitBranchSchema:
    def test_schema_has_required_fields(self):
        from tools.git_branch import GIT_BRANCH_SCHEMA
        assert GIT_BRANCH_SCHEMA["name"] == "git_branch"
        assert "parameters" in GIT_BRANCH_SCHEMA
        props = GIT_BRANCH_SCHEMA["parameters"]["properties"]
        assert "operation" in props
        assert "branch_name" in props
        assert "force" in props
        assert "task_id" in props