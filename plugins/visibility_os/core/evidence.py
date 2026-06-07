from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

class EvidenceError(ValueError):
    """Raised when evidence is insufficient for a claim."""

@dataclass
class EvidencePackage:
    problem_statement: str
    affected_users_or_systems: str | None = None
    root_cause: str | None = None
    fix_summary: str | None = None
    before_after_behaviour: str | None = None
    tests_run: str | None = None
    logs_or_screenshots: list[str] = field(default_factory=list)
    risk_assessment: str | None = None
    follow_up_tasks: list[str] = field(default_factory=list)
    evidence_links: list[dict[str, Any]] = field(default_factory=list)
    actual_status: str = "drafted"

    def validate_for_completion(self) -> bool:
        if self.actual_status not in {"executed", "merged", "shipped", "completed"}:
            raise EvidenceError("Completion update requires executed/merged/shipped status")
        if not self.evidence_links:
            raise EvidenceError("Completion update requires PR/issue/evidence link")
        if not self.tests_run:
            raise EvidenceError("Completion update requires tests run or explanation")
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_statement": self.problem_statement,
            "affected_users_or_systems": self.affected_users_or_systems,
            "root_cause": self.root_cause,
            "fix_summary": self.fix_summary,
            "before_after_behaviour": self.before_after_behaviour,
            "tests_run": self.tests_run,
            "logs_or_screenshots": self.logs_or_screenshots,
            "risk_assessment": self.risk_assessment,
            "follow_up_tasks": self.follow_up_tasks,
            "evidence_links": self.evidence_links,
            "actual_status": self.actual_status,
        }
