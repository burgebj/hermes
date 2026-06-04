"""Search resource-budget soft-truncation behavior.

Ported in spirit from nearai/ironclaw#4211: when a directory walk / search hits
its resource budget, the tool should return the *partial* results collected so
far flagged as truncated, rather than failing hard or poisoning the result.

In hermes-agent the budget is the per-search subprocess timeout. The terminal
backend surfaces a timeout as exit code 124 with the partial stdout collected
so far plus a trailing ``[Command timed out after Ns]`` marker. These tests
verify every search backend (rg-files, rg-content, grep-content, find-fallback)
strips that marker, keeps the partial results, and reports
``truncated=True`` + ``limit_reason="search_timeout"``.
"""

from unittest.mock import MagicMock

import pytest

from tools.file_operations import ShellFileOperations


@pytest.fixture()
def mock_env():
    env = MagicMock()
    env.cwd = "/tmp/test"
    env.execute.return_value = {"output": "", "returncode": 0}
    return env


def _timeout_output(partial_lines, seconds=60):
    """Mimic the backend's timeout payload: partial stdout + trailing marker."""
    body = "\n".join(partial_lines)
    if body:
        body += "\n"
    return body + f"[Command timed out after {seconds}s]"


class TestTimeoutMarkerHelpers:
    def test_hit_budget_true_only_for_124(self, mock_env):
        ops = ShellFileOperations(mock_env)
        from tools.file_operations import ExecuteResult

        assert ops._search_hit_budget(ExecuteResult(stdout="x", exit_code=124)) is True
        assert ops._search_hit_budget(ExecuteResult(stdout="x", exit_code=0)) is False
        assert ops._search_hit_budget(ExecuteResult(stdout="x", exit_code=1)) is False
        assert ops._search_hit_budget(ExecuteResult(stdout="x", exit_code=2)) is False

    def test_strip_marker_removes_trailing_only(self, mock_env):
        ops = ShellFileOperations(mock_env)
        raw = "a.py\nb.py\n[Command timed out after 60s]"
        assert ops._strip_timeout_marker(raw) == "a.py\nb.py"

    def test_strip_marker_handles_no_partial_output(self, mock_env):
        ops = ShellFileOperations(mock_env)
        assert ops._strip_timeout_marker("[Command timed out after 30s]") == ""

    def test_strip_marker_noop_when_absent(self, mock_env):
        ops = ShellFileOperations(mock_env)
        assert ops._strip_timeout_marker("a.py\nb.py") == "a.py\nb.py"


class TestRgFileSearchBudget:
    """target='files' via _search_files_rg."""

    def test_timeout_returns_partial_files_truncated(self, mock_env, monkeypatch):
        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            # rg --files times out with two files already streamed
            return {"output": _timeout_output(["src/a.py", "src/b.py"]), "returncode": 124}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "rg")
        result = ops.search("*.py", path="/big/tree", target="files")

        assert result.error is None
        # The timeout marker must NOT leak in as a bogus file.
        assert all("timed out" not in f for f in result.files)
        assert result.files == ["src/a.py", "src/b.py"]
        assert result.truncated is True
        assert result.limit_reason == "search_timeout"
        d = result.to_dict()
        assert d["truncated"] is True
        assert d["limit_reason"] == "search_timeout"

    def test_timeout_does_not_trigger_unsorted_retry(self, mock_env, monkeypatch):
        """A budget timeout with empty partial output must not be retried as
        if --sortr failed -- the retry would just time out again."""
        calls = {"n": 0}

        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            calls["n"] += 1
            return {"output": _timeout_output([]), "returncode": 124}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "rg")
        result = ops.search("*.py", path="/big/tree", target="files")

        assert calls["n"] == 1  # only the sorted rg --files call, no retry
        assert result.truncated is True
        assert result.limit_reason == "search_timeout"
        assert result.files == []

    def test_no_timeout_keeps_existing_behavior(self, mock_env, monkeypatch):
        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            return {"output": "src/a.py\nsrc/b.py\n", "returncode": 0}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "rg")
        result = ops.search("*.py", path="/tree", target="files")

        assert result.files == ["src/a.py", "src/b.py"]
        assert result.limit_reason is None
        assert "limit_reason" not in result.to_dict()


class TestRgContentSearchBudget:
    """target='content' via _search_with_rg."""

    def test_content_timeout_returns_partial_matches(self, mock_env, monkeypatch):
        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            partial = ["src/a.py:10:foo()", "src/b.py:22:foo()"]
            return {"output": _timeout_output(partial), "returncode": 124}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "rg")
        result = ops.search("foo", path="/big/tree", target="content")

        assert result.error is None
        assert len(result.matches) == 2
        assert {m.path for m in result.matches} == {"src/a.py", "src/b.py"}
        # marker must not have parsed into a phantom match
        assert all("timed out" not in m.content for m in result.matches)
        assert result.truncated is True
        assert result.limit_reason == "search_timeout"

    def test_content_files_only_timeout(self, mock_env, monkeypatch):
        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            return {"output": _timeout_output(["src/a.py", "src/b.py"]), "returncode": 124}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "rg")
        result = ops.search("foo", path="/big", target="content", output_mode="files_only")

        assert result.files == ["src/a.py", "src/b.py"]
        assert result.truncated is True
        assert result.limit_reason == "search_timeout"

    def test_content_count_timeout(self, mock_env, monkeypatch):
        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            return {"output": _timeout_output(["src/a.py:3", "src/b.py:5"]), "returncode": 124}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "rg")
        result = ops.search("foo", path="/big", target="content", output_mode="count")

        assert result.counts == {"src/a.py": 3, "src/b.py": 5}
        assert result.truncated is True
        assert result.limit_reason == "search_timeout"

    def test_real_rg_error_still_hard_fails(self, mock_env, monkeypatch):
        """Exit 2 with no output is a genuine error, not a budget timeout."""
        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            return {"output": "", "returncode": 2}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "rg")
        result = ops.search("foo", path="/big", target="content")

        assert result.error is not None
        assert result.limit_reason is None


class TestGrepContentSearchBudget:
    """target='content' via _search_with_grep (rg unavailable)."""

    def test_grep_timeout_returns_partial_matches(self, mock_env, monkeypatch):
        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            return {"output": _timeout_output(["src/a.py:10:foo()"]), "returncode": 124}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        # rg absent -> grep path
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "grep")
        result = ops.search("foo", path="/big", target="content")

        assert result.error is None
        assert len(result.matches) == 1
        assert result.matches[0].path == "src/a.py"
        assert result.truncated is True
        assert result.limit_reason == "search_timeout"


class TestFindFallbackBudget:
    """target='files' via the find fallback (rg unavailable)."""

    def test_find_timeout_returns_partial_files(self, mock_env, monkeypatch):
        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            # find -printf streams "<mtime> <path>" then times out
            partial = ["1700000000.0 /big/src/a.py", "1700000001.0 /big/src/b.py"]
            return {"output": _timeout_output(partial), "returncode": 124}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "find")
        result = ops.search("*.py", path="/big", target="files")

        assert result.error is None
        assert result.files == ["/big/src/a.py", "/big/src/b.py"]
        assert all("timed out" not in f for f in result.files)
        assert result.truncated is True
        assert result.limit_reason == "search_timeout"

    def test_find_timeout_does_not_trigger_bsd_retry(self, mock_env, monkeypatch):
        """find timeout with marker output must not fall into the BSD retry."""
        calls = {"n": 0}

        def side_effect(command, **kwargs):
            if "test -e" in command:
                return {"output": "exists", "returncode": 0}
            if "command -v" in command:
                return {"output": "yes", "returncode": 0}
            calls["n"] += 1
            return {"output": _timeout_output([]), "returncode": 124}

        mock_env.execute.side_effect = side_effect
        ops = ShellFileOperations(mock_env)
        monkeypatch.setattr(ops, "_has_command", lambda c: c == "find")
        result = ops.search("*.py", path="/big", target="files")

        assert calls["n"] == 1  # primary find only; no BSD-compat retry
        assert result.truncated is True
        assert result.limit_reason == "search_timeout"
