#!/usr/bin/env python3
"""Post-merge verification for a GitHub PR.

After a PR is squash-merged into the base branch, the commit on the base branch
triggers a fresh set of CI / deploy workflow runs. This helper finds those runs
*by the PR's merge commit SHA*, summarizes them, optionally watches until they
finish, and optionally probes deployment URLs for liveness.

It shells out to `gh` (which carries its own auth) and parses JSON in Python —
no `jq` dependency, and no token is ever read or printed by this script. Any
captured text is passed through a redactor before display as defense-in-depth.

Usage:
    python post_merge_verify.py <pr_number> [-R owner/repo]
    python post_merge_verify.py 123 --watch --timeout 900
    python post_merge_verify.py 123 --probe https://app.example.com/healthz
    python post_merge_verify.py 123 --watch --probe https://app.example.com --json

Exit codes:
    0  merge verified — runs succeeded (and probes, if given, returned expected status)
    1  a run concluded in failure, or a probe failed
    2  usage / environment error (gh missing, PR not merged, etc.)
    3  still pending after --timeout (only with --watch)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

# Token shapes GitHub issues. We never print secrets, but redact defensively in
# case a workflow/run name or URL ever echoes one back to us.
_TOKEN_RE = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"
)

# Conclusions that mean "this run is finished and it went badly".
_FAILURE_CONCLUSIONS = {"failure", "timed_out", "startup_failure", "stale"}
# Conclusions that are terminal but not failures.
_OK_CONCLUSIONS = {"success", "neutral", "skipped"}


class GhError(RuntimeError):
    """Raised when a `gh` invocation fails or returns unparseable output."""


def redact(text: str) -> str:
    """Mask anything that looks like a GitHub token."""
    return _TOKEN_RE.sub("***REDACTED***", text)


def run_gh(args, *, timeout=60):
    """Run `gh <args>` and return parsed stdout.

    Returns parsed JSON when stdout looks like JSON, else the raw string.
    Raises GhError on non-zero exit or a JSON parse failure on `--json` output.
    """
    cmd = ["gh", *args]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError as exc:  # gh not installed
        raise GhError(
            "GitHub CLI (`gh`) not found. Install it or use the curl fallback "
            "documented in the github-pr-workflow skill."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise GhError(f"`gh {' '.join(args)}` timed out after {timeout}s") from exc

    if proc.returncode != 0:
        raise GhError(redact((proc.stderr or proc.stdout or "").strip()))

    out = proc.stdout.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def _repo_args(repo):
    """gh `-R owner/repo` flag list, or empty to let gh infer from cwd."""
    return ["-R", repo] if repo else []


def get_merge_info(pr_number, repo=None, *, _runner=run_gh):
    """Return normalized merge metadata for a PR.

    Keys: merged (bool), merge_commit (str|None), base (str), state, title, url.
    """
    data = _runner(
        [
            "pr",
            "view",
            str(pr_number),
            *_repo_args(repo),
            "--json",
            "number,state,mergedAt,mergeCommit,baseRefName,title,url",
        ]
    )
    if not isinstance(data, dict):
        raise GhError(f"Unexpected response for PR #{pr_number}")
    merge_commit = (data.get("mergeCommit") or {}).get("oid")
    # `gh` exposes no boolean `merged` field — derive it from state/mergedAt.
    merged = data.get("state") == "MERGED" or bool(data.get("mergedAt"))
    return {
        "number": data.get("number"),
        "merged": merged,
        "merge_commit": merge_commit,
        "base": data.get("baseRefName"),
        "state": data.get("state"),
        "title": data.get("title"),
        "url": data.get("url"),
    }


def resolve_repo(repo=None, *, _runner=run_gh):
    """Return owner/repo, resolving from the current dir via gh when not given."""
    if repo:
        return repo
    data = _runner(["repo", "view", "--json", "nameWithOwner"])
    if isinstance(data, dict) and data.get("nameWithOwner"):
        return data["nameWithOwner"]
    raise GhError("Could not resolve repository; pass -R owner/repo.")


def parse_runs(payload):
    """Normalize the `actions/runs` API payload into a flat list of run dicts.

    Each item: name, status, conclusion, event, branch, sha, url, created_at.
    Accepts either the raw API object ({"workflow_runs": [...]}) or a bare list.
    """
    if isinstance(payload, dict):
        raw = payload.get("workflow_runs", [])
    elif isinstance(payload, list):
        raw = payload
    else:
        raw = []
    runs = []
    for r in raw:
        runs.append(
            {
                "name": r.get("name") or r.get("display_title") or "(unnamed)",
                "status": r.get("status"),
                "conclusion": r.get("conclusion"),
                "event": r.get("event"),
                "branch": r.get("head_branch"),
                "sha": r.get("head_sha"),
                "url": r.get("html_url"),
                "created_at": r.get("created_at"),
            }
        )
    return runs


def list_runs_for_sha(sha, repo, *, limit=30, _runner=run_gh):
    """Fetch workflow runs whose head commit is `sha` (the merge commit)."""
    payload = _runner(
        [
            "api",
            f"repos/{repo}/actions/runs?head_sha={sha}&per_page={limit}",
        ]
    )
    return parse_runs(payload)


def classify_runs(runs):
    """Reduce a list of runs to an overall state.

    Returns one of: "none", "pending", "failure", "success".
    - failure if any run finished in a failure conclusion
    - pending if any run has not completed
    - success if all runs completed without failure
    """
    if not runs:
        return "none"
    if any(r.get("conclusion") in _FAILURE_CONCLUSIONS for r in runs):
        return "failure"
    if any(r.get("status") != "completed" for r in runs):
        return "pending"
    return "success"


_STATE_ICON = {"success": "✓", "failure": "✗", "pending": "·", "none": "?"}


def format_summary(merge_info, runs):
    """Build a human-readable, secret-free summary block."""
    lines = []
    pr = merge_info
    head = f"PR #{pr.get('number')} → {pr.get('base')}"
    if pr.get("title"):
        head += f"  {pr['title']}"
    lines.append(head)
    lines.append(f"merge commit: {pr.get('merge_commit') or '(none)'}")
    overall = classify_runs(runs)
    lines.append(f"runs: {len(runs)}  overall: {overall} {_STATE_ICON[overall]}")
    for r in runs:
        state = r.get("conclusion") or r.get("status") or "?"
        lines.append(f"  [{state}] {r['name']}  {r.get('url') or ''}")
    return redact("\n".join(lines))


def probe_url(url, *, timeout=10, expect_status=200, _opener=None):
    """HTTP GET a deployment surface; return {url, ok, status, error}."""
    opener = _opener or urllib.request.urlopen
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "hermes-post-merge-verify"})
    try:
        with opener(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
        return {"url": url, "ok": status == expect_status, "status": status, "error": None}
    except urllib.error.HTTPError as exc:
        return {"url": url, "ok": exc.code == expect_status, "status": exc.code, "error": None}
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"url": url, "ok": False, "status": None, "error": redact(str(exc))}


def watch_runs(sha, repo, *, timeout=900, interval=20, _runner=run_gh, _sleep=time.sleep, _clock=time.monotonic):
    """Poll runs for `sha` until all complete or `timeout` seconds elapse.

    Returns (runs, overall_state). overall_state may be "pending" on timeout.
    """
    deadline = _clock() + timeout
    runs = []
    while True:
        runs = list_runs_for_sha(sha, repo, _runner=_runner)
        state = classify_runs(runs)
        if state in ("success", "failure", "none"):
            return runs, state
        if _clock() >= deadline:
            return runs, "pending"
        _sleep(interval)


def build_arg_parser():
    p = argparse.ArgumentParser(
        prog="post_merge_verify.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("pr_number", help="merged PR number")
    p.add_argument("-R", "--repo", default=None, help="owner/repo (default: infer from cwd)")
    p.add_argument("--watch", action="store_true", help="poll until base-branch runs finish")
    p.add_argument("--timeout", type=int, default=900, help="watch timeout seconds (default 900)")
    p.add_argument("--interval", type=int, default=20, help="watch poll interval seconds (default 20)")
    p.add_argument("--probe", action="append", default=[], metavar="URL",
                   help="deployment URL to GET after runs succeed (repeatable)")
    p.add_argument("--expect-status", type=int, default=200, help="expected probe HTTP status (default 200)")
    p.add_argument("--json", action="store_true", help="emit a JSON report instead of text")
    return p


def run(argv=None):
    """Programmatic entry point. Returns (exit_code, report_dict)."""
    args = build_arg_parser().parse_args(argv)
    try:
        repo = resolve_repo(args.repo)
        merge_info = get_merge_info(args.pr_number, repo)
    except GhError as exc:
        return 2, {"error": str(exc)}

    if not merge_info["merged"] or not merge_info["merge_commit"]:
        return 2, {
            "error": f"PR #{args.pr_number} is not merged (state={merge_info['state']}); "
            "nothing to verify.",
            "merge": merge_info,
        }

    sha = merge_info["merge_commit"]
    try:
        if args.watch:
            runs, overall = watch_runs(
                sha, repo, timeout=args.timeout, interval=args.interval
            )
        else:
            runs = list_runs_for_sha(sha, repo)
            overall = classify_runs(runs)
    except GhError as exc:
        return 2, {"error": str(exc), "merge": merge_info}

    probes = []
    if args.probe and overall != "failure":
        probes = [probe_url(u, expect_status=args.expect_status) for u in args.probe]

    report = {
        "merge": merge_info,
        "overall": overall,
        "runs": runs,
        "probes": probes,
        "summary": format_summary(merge_info, runs),
    }

    if overall == "failure":
        code = 1
    elif overall == "pending":
        code = 3
    elif any(not p["ok"] for p in probes):
        code = 1
    else:
        code = 0
    return code, report


def main(argv=None):
    code, report = run(argv)
    if "error" in report:
        print(redact(report["error"]), file=sys.stderr)
        if report.get("merge"):
            print(report["summary"] if "summary" in report else "", file=sys.stderr)
        return code

    args_json = "--json" in (argv if argv is not None else sys.argv[1:])
    if args_json:
        # Drop the pre-rendered text summary from JSON output to avoid duplication.
        out = {k: v for k, v in report.items() if k != "summary"}
        print(json.dumps(out, indent=2))
    else:
        print(report["summary"])
        for p in report.get("probes", []):
            mark = "✓" if p["ok"] else "✗"
            detail = f"status={p['status']}" if p["status"] is not None else f"error={p['error']}"
            print(f"  probe [{mark}] {p['url']}  {detail}")
    return code


if __name__ == "__main__":
    sys.exit(main())
