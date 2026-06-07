from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from plugins.visibility_os.core.config import get_visibility_config
from plugins.visibility_os.core.workstreams import add_workstream_artifact, update_stage


def _ensure_allowed_repo(repo: str | None) -> None:
    cfg = get_visibility_config()
    if not cfg.github_repo_allowed(repo):
        raise RuntimeError(f"Visibility OS GitHub actions are restricted to configured repositories: {cfg.github_scope_label}")


def _parse_github_target(target: str, kind: str) -> tuple[str, str | None]:
    """Return (number, repo) from either org/repo/issues/123 or GitHub URL."""
    target = target.rstrip("/")
    parts = target.split("/")
    number = parts[-1]
    repo = None
    if target.startswith("https://github.com/") and len(parts) >= 7:
        repo = f"{parts[3]}/{parts[4]}"
    elif len(parts) >= 4 and parts[-2] in {"issues", "pull"}:
        repo = f"{parts[0]}/{parts[1]}"
    if not number.isdigit():
        raise RuntimeError(f"Could not parse GitHub {kind} number from target_location={target!r}")
    return number, repo


def _execute_push_branch(payload: dict[str, Any]) -> dict[str, Any]:
    repo = payload.get("repo")
    _ensure_allowed_repo(repo)
    branch = payload.get("branch")
    if not branch:
        raise RuntimeError("github_push_branch requires branch")
    workdir = payload.get("workdir")
    if not workdir:
        raise RuntimeError("github_push_branch requires workdir containing the prepared local branch")
    if not Path(workdir).exists():
        raise RuntimeError(f"Prepared branch workdir does not exist: {workdir}")
    push = subprocess.run(["git", "push", "-u", "origin", str(branch)], capture_output=True, text=True, timeout=300, check=False, cwd=workdir)
    if push.returncode != 0:
        raise RuntimeError(push.stderr or push.stdout or "git push failed")
    pr = subprocess.run([
        "gh", "pr", "create",
        "--repo", str(repo),
        "--head", str(branch),
        "--base", str(payload.get("base_branch") or "main"),
        "--title", str(payload.get("pr_title") or payload.get("commit_message") or branch),
        "--body", str(payload.get("pr_body") or "Prepared by Visibility OS Fix CI lane."),
    ], capture_output=True, text=True, timeout=120, check=False, cwd=workdir)
    if pr.returncode != 0:
        raise RuntimeError(pr.stderr or pr.stdout or "gh pr create failed")
    result = {
        "ok": True,
        "repo": repo,
        "branch": branch,
        "pr_url": pr.stdout.strip(),
        "push_stdout": push.stdout.strip(),
        "push_stderr": push.stderr.strip(),
        "command": ["git", "push", "..."],
    }
    workstream_id = payload.get("workstream_id")
    if workstream_id:
        add_workstream_artifact(
            workstream_id,
            artifact_type="github_result",
            title="GitHub PR opened",
            summary=f"Pushed {branch} and opened {result['pr_url']}",
            payload=result,
        )
        update_stage(workstream_id, stage="pushed", status="completed", current_step="Branch pushed and PR opened", progress_percent=100, actor="github", payload=result)
    return result


def execute_github_action(action: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if action["action_type"] == "github_push_branch":
        return _execute_push_branch(payload)
    body = payload.get("body") or payload.get("text")
    if not body:
        raise RuntimeError("GitHub action requires body/text payload")
    target = action["target_location"]
    if action["action_type"] == "github_issue_comment":
        issue, repo = _parse_github_target(target, "issue")
        _ensure_allowed_repo(repo)
        cmd = ["gh", "issue", "comment", issue, "--body", body]
        if repo:
            cmd += ["--repo", repo]
    elif action["action_type"] == "github_pr_comment":
        pr, repo = _parse_github_target(target, "pull request")
        _ensure_allowed_repo(repo)
        cmd = ["gh", "pr", "comment", pr, "--body", body]
        if repo:
            cmd += ["--repo", repo]
    else:
        raise RuntimeError(f"Unsupported GitHub action type {action['action_type']}")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    if res.returncode != 0:
        raise RuntimeError(res.stderr or res.stdout or "gh command failed")
    return {"ok": True, "stdout": res.stdout.strip(), "command": cmd[:4] + ["..."]}
