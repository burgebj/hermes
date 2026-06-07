from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from hermes_constants import get_hermes_home

from .actions import create_action
from .config import get_visibility_config
from .opportunities import get_opportunity


@dataclass(frozen=True)
class PullRequestRef:
    repo: str
    number: int
    url: str


def _parse_pr_url(url: str | None) -> PullRequestRef:
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)(?:[/?#].*)?$", url or "")
    if not match:
        raise ValueError(f"Opportunity source_url is not a GitHub PR URL: {url}")
    repo = match.group(1)
    cfg = get_visibility_config()
    if not cfg.github_repo_allowed(repo):
        raise ValueError(f"Visibility OS PR audit is restricted to configured repositories: {cfg.github_scope_label}")
    return PullRequestRef(repo=repo, number=int(match.group(2)), url=url or "")


def _gh(args: list[str], *, timeout: int = 120) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {' '.join(args)}")
    return result.stdout


def _pr_view(ref: PullRequestRef) -> dict[str, Any]:
    raw = _gh(["gh", "pr", "view", str(ref.number), "--repo", ref.repo, "--json", "headRefOid,title,author,baseRefName,headRefName,url,files,additions,deletions,changedFiles,body"], timeout=60)
    try:
        return json.loads(raw or "{}")
    except Exception:
        return {}


def _pr_diff(ref: PullRequestRef) -> str:
    return _gh(["gh", "pr", "diff", str(ref.number), "--repo", ref.repo], timeout=180)


def _iter_added_lines(diff: str):
    path: str | None = None
    new_line = 0
    for raw in diff.splitlines():
        file_match = re.match(r"diff --git a/(.*?) b/(.*)$", raw)
        if file_match:
            path = file_match.group(2)
            new_line = 0
            continue
        hunk_match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
        if hunk_match:
            new_line = int(hunk_match.group(1))
            continue
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            yield path or "unknown", new_line, raw[1:], "added"
            new_line += 1
        elif raw.startswith("-"):
            continue
        else:
            if new_line:
                yield path or "unknown", new_line, raw[1:] if raw.startswith(" ") else raw, "context"
                new_line += 1


def _without_long_dashes(text: str) -> str:
    """Keep casual review comments free of em/en dashes."""
    return re.sub(r"\s*[—–]\s*", ", ", text).strip()


def _casual_comment(title: str, detail: str, solution: str) -> str:
    lower = title.lower()
    if "sql injection" in lower:
        return _without_long_dashes("Is this SQL injection safe? It looks like we're executing a formatted query here, I think we should switch this to a parameterized call.")
    if "shell" in lower:
        return _without_long_dashes("This looks like it can run through the shell with dynamic input. Can we avoid shell=True and pass args explicitly instead?")
    if "secret" in lower or "credential" in lower:
        return _without_long_dashes("This looks like a real secret might be getting committed. Can we move it into env/secrets and rotate it if needed?")
    if "test" in lower:
        return _without_long_dashes("I think this needs a test before we merge, otherwise it's hard to tell if this path is safe.")
    if "large pr" in lower:
        return _without_long_dashes("This PR is getting pretty big. I think we should either split it or add a reviewer guide so the risky parts don't get missed.")
    return _without_long_dashes(f"I’m flagging this because {detail[:160].rstrip('.')}. I think the fix is: {solution[:160].rstrip('.')}")


def _diff_anchor(path: str, line: int) -> str:
    safe = re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-") or "file"
    return f"diff-{safe}R{line or 1}"


def _finding(*, severity: str, path: str, line: int, title: str, detail: str, solution: str, code: str, source: str = "deterministic", casual_comment: str | None = None) -> dict[str, Any]:
    return {
        "severity": severity,
        "path": path,
        "line": line,
        "title": title,
        "detail": detail,
        "solution": solution,
        "code": code.strip(),
        "source": source,
        "status": "open",
        "casual_comment": _without_long_dashes(casual_comment or _casual_comment(title, detail, solution)),
        "diff_anchor": _diff_anchor(path, line),
    }


def audit_diff(diff: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    pending_sql_fstring: dict[str, Any] | None = None
    changed_files: set[str] = set()
    test_files: set[str] = set()

    for path, line, code, status in _iter_added_lines(diff):
        if status == "added":
            changed_files.add(path)
        if re.search(r"(^|/)(test_|.*_test\.|tests?/)", path):
            test_files.add(path)
        lower = code.lower()

        if status != "added":
            if re.search(r"\bf['\"].*\b(SELECT|INSERT|UPDATE|DELETE)\b", code, re.I):
                pending_sql_fstring = {"path": path, "line": line, "code": code}
            continue
        if re.search(r"\b(api[_-]?key|secret|password|token|private[_-]?key)\b\s*=\s*['\"][^'\"]{6,}['\"]", code, re.I):
            findings.append(_finding(
                severity="critical", path=path, line=line,
                title="Possible hardcoded secret or credential",
                detail="The added line appears to assign a secret-like value directly in source code.",
                solution="Move the value to a secret manager or environment variable, rotate the exposed value if it is real, and add a test/config guard that does not require committing credentials.",
                code=code,
            ))

        if "shell=true" in lower or re.search(r"os\.system\s*\(", code):
            findings.append(_finding(
                severity="critical", path=path, line=line,
                title="Shell injection risk",
                detail="The added line executes through a shell. If any interpolated value is user- or environment-controlled, this can allow command injection.",
                solution="Use subprocess.run([...], shell=False, check=True) with an argument list. Validate or constrain the path/input before passing it to the process.",
                code=code,
            ))

        if re.search(r"\bf['\"].*\b(SELECT|INSERT|UPDATE|DELETE)\b", code, re.I):
            pending_sql_fstring = {"path": path, "line": line, "code": code}

        if re.search(r"\.execute\s*\((query|sql)\)", code) and pending_sql_fstring and pending_sql_fstring["path"] == path:
            findings.append(_finding(
                severity="critical", path=pending_sql_fstring["path"], line=pending_sql_fstring["line"],
                title="SQL injection risk from formatted query",
                detail="A SQL statement is constructed with an f-string and then executed. Interpolated values can alter the query.",
                solution="Use parameterized queries, e.g. cursor.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,)) or the parameter style used by this project's DB adapter.",
                code=pending_sql_fstring["code"],
            ))

        if re.search(r"\bexcept\s+Exception\s*:\s*(pass)?\s*$", code):
            findings.append(_finding(
                severity="warning", path=path, line=line,
                title="Broad exception handling can hide failures",
                detail="Catching Exception without logging or re-raising can suppress production failures.",
                solution="Catch the specific exception type and log or return enough context for operators to diagnose the failure.",
                code=code,
            ))

        if "todo" in lower or "fixme" in lower:
            findings.append(_finding(
                severity="suggestion", path=path, line=line,
                title="TODO/FIXME added in changed code",
                detail="The PR adds unfinished-work markers that may need tracking before merge.",
                solution="Either complete the work now or link the TODO to a tracked issue with owner and expected follow-up.",
                code=code,
            ))

    production_changes = [p for p in changed_files if p not in test_files and not re.search(r"(^|/)(docs?|README|CHANGELOG)", p, re.I)]
    if production_changes and not test_files:
        findings.append(_finding(
            severity="warning",
            path=production_changes[0],
            line=1,
            title="Production code changed without test changes",
            detail="The diff changes production files but does not include an obvious test file change.",
            solution="Add or update tests that exercise the changed behavior, including at least one failure/edge path where applicable.",
            code="",
        ))

    severity_order = {"critical": 0, "warning": 1, "suggestion": 2}
    return sorted(findings, key=lambda f: (severity_order.get(f["severity"], 9), f["path"], f["line"]))


def _verdict(findings: list[dict[str, Any]]) -> str:
    if any(f["severity"] == "critical" for f in findings):
        return "REQUEST_CHANGES"
    if any(f["severity"] == "warning" for f in findings):
        return "COMMENT"
    return "APPROVE"


def _review_body(*, opportunity: dict[str, Any], ref: PullRequestRef, findings: list[dict[str, Any]], verdict: str, depth: str = "standard", review_notes: list[str] | None = None) -> str:
    counts = {sev: sum(1 for f in findings if f["severity"] == sev) for sev in ("critical", "warning", "suggestion")}
    heading = {
        "deep": "Hermes Deep PR Review",
        "agentic": "Hermes Agentic Deep PR Review",
    }.get(depth, "Hermes PR Audit")
    lines = [
        f"## {heading}",
        "",
        f"**Verdict:** {verdict}",
        f"**Depth:** {depth}",
        f"**Scope:** {opportunity.get('title') or ref.url}",
        f"**Findings:** {counts['critical']} critical, {counts['warning']} warning, {counts['suggestion']} suggestion",
        "",
    ]
    if review_notes:
        lines.extend(["### Review context", ""])
        lines.extend([f"- {note}" for note in review_notes])
        lines.append("")
    if not findings:
        lines.extend(["No blocking findings detected by the automated audit heuristics.", "", "Manual reviewer should still validate product intent and domain correctness."])
    else:
        for f in findings:
            location = f"{f['path']}:{f['line']}" if f.get("line") else f["path"]
            lines.extend([
                f"### {f['severity'].upper()} — {location}",
                f"**Comment:** {f.get('casual_comment') or f['title']}",
                f"**Issue:** {f['title']}",
                f"**Detail:** {f['detail']}",
                f"**Suggested fix:** {f['solution']}",
                "",
            ])
    return "\n".join(lines).strip()


def _github_diff_url(ref: PullRequestRef, finding: dict[str, Any]) -> str:
    return f"{ref.url}/files#{finding.get('diff_anchor') or _diff_anchor(finding.get('path') or 'file', int(finding.get('line') or 1))}"


def _finding_comment(finding: dict[str, Any]) -> str:
    location = f"{finding.get('path')}:{finding.get('line')}"
    return f"{finding.get('casual_comment') or finding.get('title')}\n\n{location}\n\nSuggested change: {finding.get('solution')}"


def _enrich_findings_for_pr(findings: list[dict[str, Any]], ref: PullRequestRef, *, default_source: str | None = None) -> list[dict[str, Any]]:
    enriched = []
    for finding in findings:
        item = dict(finding)
        if default_source and not item.get("source"):
            item["source"] = default_source
        item.setdefault("source", "deterministic")
        item.setdefault("status", "open")
        item.setdefault("casual_comment", _casual_comment(str(item.get("title") or ""), str(item.get("detail") or ""), str(item.get("solution") or "")))
        item["casual_comment"] = _without_long_dashes(str(item.get("casual_comment") or ""))
        item.setdefault("diff_anchor", _diff_anchor(str(item.get("path") or "file"), int(item.get("line") or 1)))
        item["github_diff_url"] = _github_diff_url(ref, item)
        item["copy_comment"] = _finding_comment(item)
        enriched.append(item)
    return enriched


def _findings_summary(findings: list[dict[str, Any]]) -> dict[str, int]:
    return {key: sum(1 for f in findings if f.get("severity") == key) for key in ("critical", "warning", "suggestion")}


def _findings_by_file(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        path = str(finding.get("path") or "unknown")
        counts[path] = counts.get(path, 0) + 1
    return counts


def _changed_file_names(diff: str, view: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for item in view.get("files") or []:
        if isinstance(item, dict) and item.get("path"):
            names.add(str(item["path"]))
    for match in re.finditer(r"^diff --git a/(.*?) b/(.*?)$", diff, re.M):
        names.add(match.group(2))
    return names


def _deep_review_findings(*, diff: str, view: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """PR-level review checks that go beyond single-line diff heuristics."""
    findings: list[dict[str, Any]] = []
    notes: list[str] = []
    files = _changed_file_names(diff, view)
    test_files = {p for p in files if re.search(r"(^|/)(test_|.*_test\.|tests?/|__tests__/|specs?/)", p, re.I)}
    production_files = {p for p in files if p not in test_files and not re.search(r"(^|/)(docs?|README|CHANGELOG|package-lock\.json|yarn\.lock|pnpm-lock\.yaml)", p, re.I)}
    changed_count = int(view.get("changedFiles") or len(files) or 0)
    additions = int(view.get("additions") or 0)
    deletions = int(view.get("deletions") or 0)

    if files:
        notes.append(f"Reviewed PR-level context across {changed_count or len(files)} changed file(s), +{additions}/-{deletions} when available.")
    else:
        notes.append("Reviewed diff context; GitHub did not return a changed-file list.")

    if production_files and not test_files:
        findings.append(_finding(
            severity="warning",
            path=sorted(production_files)[0],
            line=1,
            title="Deep review found product code changes without tests",
            detail="The PR changes non-documentation production files, but the changed-file set does not include obvious tests/specs. This should be validated before merge, especially for business logic and regression-prone paths.",
            solution="Add focused tests for the changed behavior or document why existing coverage is sufficient in the PR before approving.",
            code="",
        ))

    risky_patterns = [
        (r"(^|/)(contracts?|src/.*\.sol$|.*\.sol$)", "Smart contract or Solidity changes need domain/security review", "Run the relevant contract tests, review economic/security invariants, and ensure any audit/remediation notes are linked before merge."),
        (r"(^|/)(infra|terraform|pulumi|k8s|helm|charts|\.github/workflows)/", "Infrastructure/CI changes need operational rollback review", "Confirm blast radius, secrets handling, deployment order, and rollback steps before merge."),
        (r"(^|/)(migrations?|prisma/migrations|db/migrations)/", "Database migration changes need rollback/data-safety review", "Confirm forward/backward compatibility, migration runtime, rollback strategy, and data backfill/repair plan."),
    ]
    for pattern, title, solution in risky_patterns:
        matched = sorted(p for p in production_files if re.search(pattern, p, re.I))
        if matched:
            findings.append(_finding(
                severity="warning",
                path=matched[0],
                line=1,
                title=title,
                detail="Deep review identified a changed file in a high-blast-radius area. The automated line-level audit may not catch product, security, or operational regressions here.",
                solution=solution,
                code="",
            ))

    if changed_count >= 20 or additions + deletions >= 800:
        findings.append(_finding(
            severity="suggestion",
            path=sorted(files)[0] if files else "PR",
            line=1,
            title="Large PR may need split or staged review",
            detail="The PR is large enough that reviewers are likely to miss semantic issues, especially around edge cases and integration behavior.",
            solution="Consider splitting into smaller PRs or add a reviewer guide that explains the change graph, test plan, and riskiest areas.",
            code="",
        ))

    body = (view.get("body") or "").lower()
    if production_files and not re.search(r"test plan|testing|validated|verification|how tested", body):
        findings.append(_finding(
            severity="suggestion",
            path="PR description",
            line=1,
            title="PR description does not include an obvious test plan",
            detail="Deep review did not find test-plan language in the PR description. That makes human approval harder to audit later.",
            solution="Add a concise test plan or verification note to the PR description before merge.",
            code="",
        ))

    notes.append("Generated a human-approved GitHub review draft; nothing is posted automatically.")
    return findings, notes


def _extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Agent review output did not contain a JSON object")
    return json.loads(text[start:end + 1])


def _normalize_agent_finding(raw: dict[str, Any]) -> dict[str, Any]:
    severity = str(raw.get("severity") or "suggestion").lower()
    if severity not in {"critical", "warning", "suggestion"}:
        severity = "suggestion"
    try:
        line = int(raw.get("line") or 1)
    except Exception:
        line = 1
    return _finding(
        severity=severity,
        path=str(raw.get("path") or "PR"),
        line=line,
        title=str(raw.get("title") or "Agent review finding")[:180],
        detail=str(raw.get("detail") or raw.get("description") or "The agent flagged this during deep review."),
        solution=str(raw.get("solution") or raw.get("suggested_fix") or "Review and address before merge if applicable."),
        code=str(raw.get("code") or raw.get("snippet") or ""),
        source="agentic",
        casual_comment=str(raw.get("casual_comment") or raw.get("comment") or "") or None,
    )


def _agentic_review_pr(ref: PullRequestRef, *, opportunity: dict[str, Any], view: dict[str, Any], diff: str) -> dict[str, Any]:
    review_root = Path(get_hermes_home()) / "visibility_os_reviews"
    review_root.mkdir(parents=True, exist_ok=True)
    checkout_dir = review_root / ref.repo.replace("/", "__") / f"pr-{ref.number}"
    checkout_dir.parent.mkdir(parents=True, exist_ok=True)

    if not checkout_dir.exists():
        _gh(["gh", "repo", "clone", ref.repo, str(checkout_dir), "--", "--filter=blob:none"], timeout=300)
    result = subprocess.run(
        ["gh", "pr", "checkout", str(ref.number), "--repo", ref.repo],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        cwd=str(checkout_dir),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to checkout PR branch")

    changed_files = sorted(_changed_file_names(diff, view))
    cfg = get_visibility_config()
    prompt = f"""
You are doing a proper agentic deep review for {cfg.company_name} / Visibility OS.

Repository: {ref.repo}
Pull request: {ref.url}
PR title: {view.get('title') or opportunity.get('title')}
Changed files: {', '.join(changed_files[:80])}

You are running inside a local checkout of the PR branch. Inspect the codebase, read surrounding files, and run the most relevant tests or static checks that are practical. Focus on correctness, product/domain behavior, edge cases, security, tests, migrations/infrastructure risk, and regressions. Do not post to GitHub.

Return ONLY a JSON object with this schema:
{{
  "verdict": "REQUEST_CHANGES" | "COMMENT" | "APPROVE",
  "findings": [
    {{
      "severity": "critical" | "warning" | "suggestion",
      "path": "relative/file/path",
      "line": 1,
      "title": "short finding title",
      "detail": "specific explanation grounded in the code",
      "solution": "specific coding or testing fix",
      "casual_comment": "human-sounding review comment with no em dash or en dash characters, e.g. 'Is this SQL injection safe?' or 'this variable gets overwritten below, I think we should split it into abc instead'",
      "code": "optional relevant snippet"
    }}
  ],
  "review_notes": ["commands run, files inspected, or limits encountered"]
}}
""".strip()
    result = subprocess.run(
        ["hermes", "chat", "-Q", "-q", prompt, "--toolsets", "terminal,file"],
        capture_output=True,
        text=True,
        timeout=1200,
        check=False,
        cwd=str(checkout_dir),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Hermes agentic PR review failed")
    payload = _extract_json_object(result.stdout or "")
    findings = [_normalize_agent_finding(f) for f in payload.get("findings") or [] if isinstance(f, dict)]
    verdict = str(payload.get("verdict") or _verdict(findings)).upper()
    if verdict not in {"REQUEST_CHANGES", "COMMENT", "APPROVE"}:
        verdict = _verdict(findings)
    notes = [str(n) for n in (payload.get("review_notes") or [])]
    notes.insert(0, f"Checked out {ref.repo} PR #{ref.number} locally and ran Hermes agentic review in {checkout_dir}.")
    return {"verdict": verdict, "findings": findings, "review_notes": notes, "checkout_dir": str(checkout_dir)}


def audit_pr_from_opportunity(opportunity_id: str, *, actor: str = "visibility_os") -> dict[str, Any]:
    opportunity = get_opportunity(opportunity_id)
    ref = _parse_pr_url(opportunity.get("source_url"))
    view = _pr_view(ref)
    diff = _pr_diff(ref)
    findings = _enrich_findings_for_pr(audit_diff(diff), ref, default_source="deterministic")
    verdict = _verdict(findings)
    body = _review_body(opportunity=opportunity, ref=ref, findings=findings, verdict=verdict)
    return create_action(
        proposed_by_agent=actor,
        action_type="github_pr_review_draft",
        target_system="github",
        target_location=ref.url,
        title=f"PR audit: {opportunity.get('title', ref.url)[:90]}",
        summary=f"Audited PR #{ref.number} with {len(findings)} finding(s); verdict {verdict}.",
        proposed_payload={
            "body": body,
            "verdict": verdict,
            "findings": findings,
            "findings_summary": _findings_summary(findings),
            "findings_by_file": _findings_by_file(findings),
            "review_event": verdict,
            "head_sha": view.get("headRefOid"),
            "repo": ref.repo,
            "pr_number": ref.number,
        },
        evidence_links=[{"type": "pull_request", "url": ref.url}],
        risk_level="medium" if verdict == "REQUEST_CHANGES" else "low",
        opportunity_id=opportunity_id,
        impact_score=opportunity.get("impact_score"),
        visibility_score=opportunity.get("visibility_score"),
        effort_score=opportunity.get("effort_score"),
        approval_reason="PR audit draft; human approval required before posting review feedback.",
    )


def deep_review_pr_from_opportunity(opportunity_id: str, *, actor: str = "visibility_os") -> dict[str, Any]:
    opportunity = get_opportunity(opportunity_id)
    ref = _parse_pr_url(opportunity.get("source_url"))
    view = _pr_view(ref)
    diff = _pr_diff(ref)
    deterministic_findings = audit_diff(diff)
    deep_findings, deterministic_notes = _deep_review_findings(diff=diff, view=view)
    agent_review = _agentic_review_pr(ref, opportunity=opportunity, view=view, diff=diff)

    severity_order = {"critical": 0, "warning": 1, "suggestion": 2}
    findings = sorted(
        deterministic_findings + deep_findings + agent_review["findings"],
        key=lambda f: (severity_order.get(f["severity"], 9), f["path"], f["line"]),
    )
    findings = _enrich_findings_for_pr(findings, ref)
    verdict = agent_review.get("verdict") or _verdict(findings)
    if verdict == "APPROVE" and _verdict(findings) != "APPROVE":
        verdict = _verdict(findings)
    review_notes = deterministic_notes + agent_review["review_notes"]
    body = _review_body(opportunity=opportunity, ref=ref, findings=findings, verdict=verdict, depth="agentic", review_notes=review_notes)
    return create_action(
        proposed_by_agent=actor,
        action_type="github_pr_review_draft",
        target_system="github",
        target_location=ref.url,
        title=f"Agentic deep PR review: {opportunity.get('title', ref.url)[:78]}",
        summary=f"Agentic deep-reviewed PR #{ref.number} with {len(findings)} finding(s); verdict {verdict}.",
        proposed_payload={
            "body": body,
            "verdict": verdict,
            "findings": findings,
            "findings_summary": _findings_summary(findings),
            "findings_by_file": _findings_by_file(findings),
            "review_event": verdict,
            "head_sha": view.get("headRefOid"),
            "repo": ref.repo,
            "pr_number": ref.number,
            "review_depth": "deep",
            "agentic": True,
            "checkout_dir": agent_review.get("checkout_dir"),
            "review_notes": review_notes,
            "changed_files": sorted(_changed_file_names(diff, view)),
        },
        evidence_links=[{"type": "pull_request", "url": ref.url}],
        risk_level="medium" if verdict == "REQUEST_CHANGES" else "low",
        opportunity_id=opportunity_id,
        impact_score=opportunity.get("impact_score"),
        visibility_score=opportunity.get("visibility_score"),
        effort_score=opportunity.get("effort_score"),
        approval_reason="Agentic deep PR review draft; human approval required before posting review feedback.",
    )
