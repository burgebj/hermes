"""Tests for the github-pr-workflow skill.

Covers the post_merge_verify.py helper (pure functions + gh/probe wrappers via
mocks, no network) and validates SKILL.md frontmatter + referenced-file links.
"""

import json
import re
import sys
from pathlib import Path
from unittest import mock

import pytest

SKILL_DIR = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "github"
    / "github-pr-workflow"
)
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import post_merge_verify as pmv  # noqa: E402


# --------------------------------------------------------------------------- #
# redact
# --------------------------------------------------------------------------- #
class TestRedact:
    def test_masks_classic_pat(self):
        s = "token ghp_" + "A" * 36 + " here"
        assert "ghp_" not in pmv.redact(s)
        assert "***REDACTED***" in pmv.redact(s)

    def test_masks_fine_grained_pat(self):
        s = "github_pat_" + "B" * 30
        assert pmv.redact(s) == "***REDACTED***"

    def test_leaves_ordinary_text_untouched(self):
        s = "PR #123 merged into main at deadbeef"
        assert pmv.redact(s) == s


# --------------------------------------------------------------------------- #
# parse_runs
# --------------------------------------------------------------------------- #
class TestParseRuns:
    def test_parses_api_object(self):
        payload = {
            "workflow_runs": [
                {
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "head_branch": "main",
                    "head_sha": "abc123",
                    "html_url": "https://gh/run/1",
                    "created_at": "2026-06-05T00:00:00Z",
                }
            ]
        }
        runs = pmv.parse_runs(payload)
        assert len(runs) == 1
        assert runs[0]["name"] == "CI"
        assert runs[0]["conclusion"] == "success"
        assert runs[0]["sha"] == "abc123"

    def test_accepts_bare_list(self):
        assert pmv.parse_runs([{"name": "X", "status": "queued"}])[0]["name"] == "X"

    def test_unnamed_falls_back(self):
        runs = pmv.parse_runs({"workflow_runs": [{"status": "completed"}]})
        assert runs[0]["name"] == "(unnamed)"

    def test_garbage_returns_empty(self):
        assert pmv.parse_runs(None) == []
        assert pmv.parse_runs("nope") == []


# --------------------------------------------------------------------------- #
# classify_runs
# --------------------------------------------------------------------------- #
class TestClassifyRuns:
    def test_none(self):
        assert pmv.classify_runs([]) == "none"

    def test_failure_takes_precedence(self):
        runs = [
            {"status": "completed", "conclusion": "success"},
            {"status": "in_progress", "conclusion": None},
            {"status": "completed", "conclusion": "failure"},
        ]
        assert pmv.classify_runs(runs) == "failure"

    def test_pending_when_incomplete(self):
        runs = [
            {"status": "completed", "conclusion": "success"},
            {"status": "in_progress", "conclusion": None},
        ]
        assert pmv.classify_runs(runs) == "pending"

    def test_success_all_completed(self):
        runs = [
            {"status": "completed", "conclusion": "success"},
            {"status": "completed", "conclusion": "skipped"},
        ]
        assert pmv.classify_runs(runs) == "success"

    @pytest.mark.parametrize("bad", ["failure", "timed_out", "startup_failure", "stale"])
    def test_failure_conclusions(self, bad):
        assert pmv.classify_runs([{"status": "completed", "conclusion": bad}]) == "failure"


# --------------------------------------------------------------------------- #
# get_merge_info / resolve_repo (mocked runner)
# --------------------------------------------------------------------------- #
class TestGetMergeInfo:
    def test_normalizes_merged_pr(self):
        fake = {
            "number": 7,
            "state": "MERGED",
            "merged": True,
            "mergeCommit": {"oid": "cafe1234"},
            "baseRefName": "main",
            "title": "feat: thing",
            "url": "https://gh/pr/7",
        }
        info = pmv.get_merge_info(7, "o/r", _runner=lambda *a, **k: fake)
        assert info["merged"] is True
        assert info["merge_commit"] == "cafe1234"
        assert info["base"] == "main"

    def test_open_pr_has_no_merge_commit(self):
        fake = {"number": 7, "state": "OPEN", "merged": False, "mergeCommit": None,
                "baseRefName": "main", "title": "t", "url": "u"}
        info = pmv.get_merge_info(7, "o/r", _runner=lambda *a, **k: fake)
        assert info["merged"] is False
        assert info["merge_commit"] is None

    def test_bad_response_raises(self):
        with pytest.raises(pmv.GhError):
            pmv.get_merge_info(7, "o/r", _runner=lambda *a, **k: "not a dict")


class TestResolveRepo:
    def test_passthrough_when_given(self):
        assert pmv.resolve_repo("o/r", _runner=lambda *a, **k: pytest.fail("should not call")) == "o/r"

    def test_infers_from_gh(self):
        assert pmv.resolve_repo(None, _runner=lambda *a, **k: {"nameWithOwner": "a/b"}) == "a/b"

    def test_raises_when_unresolvable(self):
        with pytest.raises(pmv.GhError):
            pmv.resolve_repo(None, _runner=lambda *a, **k: {})


# --------------------------------------------------------------------------- #
# run_gh (subprocess mocked)
# --------------------------------------------------------------------------- #
class TestRunGh:
    def test_parses_json_stdout(self):
        cp = mock.Mock(returncode=0, stdout='{"a": 1}', stderr="")
        with mock.patch("subprocess.run", return_value=cp):
            assert pmv.run_gh(["api", "x"]) == {"a": 1}

    def test_returns_raw_string_when_not_json(self):
        cp = mock.Mock(returncode=0, stdout="hello", stderr="")
        with mock.patch("subprocess.run", return_value=cp):
            assert pmv.run_gh(["x"]) == "hello"

    def test_nonzero_raises_gherror_redacted(self):
        cp = mock.Mock(returncode=1, stdout="", stderr="bad token ghp_" + "Z" * 36)
        with mock.patch("subprocess.run", return_value=cp):
            with pytest.raises(pmv.GhError) as exc:
                pmv.run_gh(["x"])
        assert "ghp_" not in str(exc.value)

    def test_missing_gh_raises(self):
        with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(pmv.GhError):
                pmv.run_gh(["x"])


# --------------------------------------------------------------------------- #
# probe_url (urlopen mocked)
# --------------------------------------------------------------------------- #
class TestProbeUrl:
    def _opener(self, status):
        def _open(req, timeout=None):
            cm = mock.MagicMock()
            cm.__enter__.return_value = mock.Mock(status=status)
            return cm
        return _open

    def test_ok_status(self):
        r = pmv.probe_url("https://x", _opener=self._opener(200))
        assert r["ok"] is True and r["status"] == 200

    def test_unexpected_status(self):
        r = pmv.probe_url("https://x", _opener=self._opener(503))
        assert r["ok"] is False and r["status"] == 503

    def test_custom_expect(self):
        r = pmv.probe_url("https://x", expect_status=204, _opener=self._opener(204))
        assert r["ok"] is True

    def test_connection_error(self):
        import urllib.error

        def _open(req, timeout=None):
            raise urllib.error.URLError("refused")

        r = pmv.probe_url("https://x", _opener=_open)
        assert r["ok"] is False and r["status"] is None and "refused" in r["error"]


# --------------------------------------------------------------------------- #
# watch_runs (runner + clock injected, no real sleep)
# --------------------------------------------------------------------------- #
class TestWatchRuns:
    def test_returns_on_success(self):
        seq = [
            {"workflow_runs": [{"name": "CI", "status": "in_progress", "conclusion": None}]},
            {"workflow_runs": [{"name": "CI", "status": "completed", "conclusion": "success"}]},
        ]
        calls = {"n": 0}

        def runner(args, **k):
            i = min(calls["n"], len(seq) - 1)
            calls["n"] += 1
            return seq[i]

        runs, state = pmv.watch_runs(
            "sha", "o/r", interval=0, _runner=runner, _sleep=lambda s: None,
        )
        assert state == "success"
        assert calls["n"] == 2

    def test_timeout_returns_pending(self):
        runner = lambda *a, **k: {"workflow_runs": [{"name": "CI", "status": "queued", "conclusion": None}]}
        clock = iter([0, 0, 1000])  # start, first check, past-deadline check
        runs, state = pmv.watch_runs(
            "sha", "o/r", timeout=10, interval=0,
            _runner=runner, _sleep=lambda s: None, _clock=lambda: next(clock),
        )
        assert state == "pending"


# --------------------------------------------------------------------------- #
# run() orchestration + exit codes
# --------------------------------------------------------------------------- #
class TestRunEntry:
    def _patch(self, monkeypatch, merge_info, runs):
        monkeypatch.setattr(pmv, "resolve_repo", lambda repo=None, **k: "o/r")
        monkeypatch.setattr(pmv, "get_merge_info", lambda pr, repo, **k: merge_info)
        monkeypatch.setattr(pmv, "list_runs_for_sha", lambda sha, repo, **k: runs)

    def test_unmerged_pr_exit_2(self, monkeypatch):
        self._patch(monkeypatch, {"merged": False, "merge_commit": None, "state": "OPEN"}, [])
        code, report = pmv.run(["7"])
        assert code == 2
        assert "not merged" in report["error"]

    def test_success_exit_0(self, monkeypatch):
        mi = {"merged": True, "merge_commit": "sha", "state": "MERGED", "number": 7,
              "base": "main", "title": "t", "url": "u"}
        self._patch(monkeypatch, mi, [{"status": "completed", "conclusion": "success", "name": "CI"}])
        code, report = pmv.run(["7"])
        assert code == 0
        assert report["overall"] == "success"

    def test_failure_exit_1(self, monkeypatch):
        mi = {"merged": True, "merge_commit": "sha", "state": "MERGED", "number": 7,
              "base": "main", "title": "t", "url": "u"}
        self._patch(monkeypatch, mi, [{"status": "completed", "conclusion": "failure", "name": "CI"}])
        code, report = pmv.run(["7"])
        assert code == 1

    def test_probe_failure_exit_1(self, monkeypatch):
        mi = {"merged": True, "merge_commit": "sha", "state": "MERGED", "number": 7,
              "base": "main", "title": "t", "url": "u"}
        self._patch(monkeypatch, mi, [{"status": "completed", "conclusion": "success", "name": "CI"}])
        monkeypatch.setattr(pmv, "probe_url",
                            lambda u, **k: {"url": u, "ok": False, "status": 500, "error": None})
        code, report = pmv.run(["7", "--probe", "https://x"])
        assert code == 1
        assert report["probes"][0]["ok"] is False

    def test_gh_missing_exit_2(self, monkeypatch):
        def boom(repo=None, **k):
            raise pmv.GhError("gh not found")
        monkeypatch.setattr(pmv, "resolve_repo", boom)
        code, report = pmv.run(["7"])
        assert code == 2
        assert "gh not found" in report["error"]


# --------------------------------------------------------------------------- #
# format_summary never leaks tokens
# --------------------------------------------------------------------------- #
def test_format_summary_redacts():
    mi = {"number": 1, "base": "main", "title": "ghp_" + "Q" * 36, "merge_commit": "deadbeef"}
    out = pmv.format_summary(mi, [{"name": "CI", "status": "completed", "conclusion": "success", "url": "u"}])
    assert "ghp_" not in out
    assert "deadbeef" in out


# --------------------------------------------------------------------------- #
# SKILL.md frontmatter + link validation
# --------------------------------------------------------------------------- #
class TestSkillDoc:
    def _frontmatter(self):
        text = (SKILL_DIR / "SKILL.md").read_text()
        m = re.search(r"^description: (.*)$", text, re.MULTILINE)
        return text, m

    def test_description_under_60_chars(self):
        _, m = self._frontmatter()
        assert m, "no description field"
        desc = m.group(1).strip().strip('"')
        assert len(desc) <= 60, f"description is {len(desc)} chars: {desc!r}"
        assert desc.endswith("."), "description must end with a period"

    def test_required_frontmatter_fields(self):
        text, _ = self._frontmatter()
        for field in ("name:", "version:", "author:", "license:"):
            assert field in text, f"missing {field}"

    def test_referenced_files_exist(self):
        text = (SKILL_DIR / "SKILL.md").read_text()
        # Every scripts/... and references/... path mentioned must exist on disk.
        for rel in re.findall(r"`?(scripts/[\w./-]+\.py)`?", text):
            assert (SKILL_DIR / rel).exists(), f"missing {rel}"
        for rel in re.findall(r"`(references/[\w./-]+\.md)`", text):
            assert (SKILL_DIR / rel).exists(), f"missing {rel}"

    def test_post_merge_script_is_executable_module(self):
        # Import already succeeded at top of file; assert the public surface.
        for fn in ("run", "main", "get_merge_info", "list_runs_for_sha",
                   "classify_runs", "probe_url", "watch_runs"):
            assert hasattr(pmv, fn), f"post_merge_verify.{fn} missing"
