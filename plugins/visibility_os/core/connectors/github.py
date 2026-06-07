from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class GitHubConnector:
    repo: str | None = None
    timeout: int = 30

    def _run_json(self, args: list[str]) -> list[dict[str, Any]]:
        if self.repo and "--repo" not in args:
            args = [*args, "--repo", self.repo]
        res = subprocess.run(args, capture_output=True, text=True, timeout=self.timeout, check=False)
        if res.returncode != 0:
            raise RuntimeError(f"gh command failed: {' '.join(args)}\n{res.stderr}")
        data = json.loads(res.stdout or "[]")
        return data if isinstance(data, list) else [data]

    def issues(self) -> list[dict[str, Any]]:
        return self._run_json(["gh", "issue", "list", "--json", "number,title,url,labels,updatedAt,assignees"])

    def prs(self) -> list[dict[str, Any]]:
        try:
            return self._run_json(["gh", "pr", "list", "--json", "number,title,url,updatedAt,reviewDecision,isDraft,author,statusCheckRollup"])
        except RuntimeError as exc:
            # Some fine-grained tokens can list PRs but cannot read nested
            # status-check rollups. Fall back to the useful metadata rather
            # than losing every open-PR opportunity for that repo.
            if "statusCheckRollup" not in str(exc):
                raise
            return self._run_json(["gh", "pr", "list", "--json", "number,title,url,updatedAt,reviewDecision,isDraft,author"])

    def runs(self) -> list[dict[str, Any]]:
        return self._run_json(["gh", "run", "list", "--json", "databaseId,status,conclusion,displayTitle,workflowName,url,createdAt,headBranch,headSha,event"])

    def prs_for_branch(self, branch: str) -> list[dict[str, Any]]:
        return self._run_json([
            "gh", "pr", "list",
            "--head", branch,
            "--state", "all",
            "--json", "number,title,state,url,headRefName,headRefOid,baseRefName,mergedAt,statusCheckRollup",
        ])
