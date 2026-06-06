from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence

ALLOWED_PATHS = {
    "hermes_cli/main.py",
    "hermes_cli/uninstall.py",
    "tests/hermes_cli/test_uninstall.py",
    "tests/hermes_cli/test_safe_refactor_audit.py",
}

HIGH_RISK_TOKENS: tuple[str, ...] = (
    "rmtree(",
    "unlink(",
    "remove(",
    "write_text(",
)

SHELL_PATH_TOKENS: tuple[str, ...] = (
    ".bashrc",
    ".zshrc",
    ".profile",
    "PATH=",
    "export PATH",
    "find_shell_configs",
    "remove_path_from_shell_configs",
)

TTY_REJECT_PATTERNS = (
    re.compile(r'^[+-].*_require_tty\("uninstall"\)'),
    re.compile(r'^\+.*isatty\('),
    re.compile(r'^\+.*(?:--yes|args\.yes|assume_yes|non[-_ ]?tty|non[-_ ]?interactive)'),
)

INDIRECT_TTY_POLICY_PATTERNS = (
    re.compile(r'^[+-].*\b(DEFAULT|ASSUME|YES|CONFIRM|INTERACTIVE|NON_INTERACTIVE|NONINTERACTIVE)[A-Z0-9_]*\b'),
    re.compile(r'^[+-].*\b(default_yes|assume_yes|confirm_required|interactive_only|non_interactive)\b'),
    re.compile(r'^[+-].*def .*\((?:[^\n]*=\s*(?:True|False))'),
    re.compile(r'^[+-].*@dataclass'),
)

HELP_TEXT_PATTERNS = (
    re.compile(r'^[+-].*hermes uninstall'),
    re.compile(r'^[+-].*help='),
    re.compile(r'^[+-].*add_argument\('),
)

CONTROL_FLOW_PATTERNS = (
    re.compile(r'^[+-].*_require_tty\("uninstall"\)'),
    re.compile(r'^[+-].*run_uninstall'),
    re.compile(r'^[+-].*\bif\b'),
    re.compile(r'^[+-].*\belif\b'),
    re.compile(r'^[+-].*\breturn\b'),
    re.compile(r'^[+-].*sys\.exit'),
    re.compile(r'^[+-].*input\('),
)

ARG_ALIAS_PATTERNS = (
    re.compile(r'^[+-].*add_argument\('),
    re.compile(r'^[+-].*--yes'),
    re.compile(r'^[+-].*--full'),
    re.compile(r'^[+-].*dest='),
    re.compile(r'^[+-].*action='),
    re.compile(r'^[+-].*aliases?='),
)

ARG_FLOW_PATTERNS = (
    re.compile(r'^[+-].*args\.yes'),
    re.compile(r'^[+-].*args\.full'),
    re.compile(r'^[+-].*run_uninstall\('),
    re.compile(r'^[+-].*\bif\b'),
    re.compile(r'^[+-].*\belif\b'),
    re.compile(r'^[+-].*\breturn\b'),
)

UNINSTALL_TARGET_FILES = {"hermes_cli/main.py", "hermes_cli/uninstall.py"}
_DIFF_HEADER_RE = re.compile(r"^\+\+\+\s+(?:b/)?(.+)$")


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    rule_id: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class AuditResult:
    verdict: str
    findings: tuple[AuditFinding, ...]
    changed_paths: tuple[str, ...]


@dataclass(frozen=True)
class _FileDiff:
    path: str
    lines: tuple[str, ...]


def audit_tdb3_diff(diff_text: str) -> AuditResult:
    file_diffs = tuple(_parse_unified_diff(diff_text))
    changed_paths = tuple(fd.path for fd in file_diffs)
    findings: list[AuditFinding] = []

    findings.extend(_check_whitelist(changed_paths))
    findings.extend(_check_tty_rules(file_diffs))
    findings.extend(_check_indirect_tty_relaxation(file_diffs))
    findings.extend(
        _scan_tokens(
            file_diffs,
            HIGH_RISK_TOKENS,
            "WARN",
            "HIGH_RISK_IO",
            "High-risk delete/write token detected",
        )
    )
    findings.extend(
        _scan_tokens(
            file_diffs,
            SHELL_PATH_TOKENS,
            "WARN",
            "SHELL_PATH_TOUCH",
            "Shell/PATH touch detected",
        )
    )
    findings.extend(_check_contract_consistency(file_diffs))
    findings.extend(_check_argument_alias_semantic_drift(file_diffs))

    verdict = "APPROVE"
    if any(f.severity == "REJECT_HARD" for f in findings):
        verdict = "REJECT_HARD"
    elif findings:
        verdict = "WARN"

    return AuditResult(verdict=verdict, findings=tuple(findings), changed_paths=changed_paths)


def _parse_unified_diff(diff_text: str) -> Iterable[_FileDiff]:
    current_path: str | None = None
    current_lines: list[str] = []

    for raw_line in diff_text.splitlines():
        match = _DIFF_HEADER_RE.match(raw_line)
        if match:
            if current_path is not None:
                yield _FileDiff(path=current_path, lines=tuple(current_lines))
            current_path = match.group(1)
            current_lines = []
            continue
        if current_path is not None:
            current_lines.append(raw_line)

    if current_path is not None:
        yield _FileDiff(path=current_path, lines=tuple(current_lines))


def _check_whitelist(changed_paths: Iterable[str]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for path in changed_paths:
        if path in ALLOWED_PATHS:
            continue
        message = "Non-whitelisted file touched"
        if path == "hermes_cli/profiles.py":
            message = "profiles.py touch is out of scope for TDB-3 audits"
        elif path.startswith("docs/"):
            message = "docs/ changes are out of scope for TDB-3 audits"
        findings.append(AuditFinding("WARN", "FILE_SCOPE", message, path))
    return findings


def _check_tty_rules(file_diffs: Iterable[_FileDiff]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for file_diff in file_diffs:
        if file_diff.path not in UNINSTALL_TARGET_FILES:
            continue
        for line in file_diff.lines:
            if any(pattern.search(line) for pattern in TTY_REJECT_PATTERNS):
                findings.append(
                    AuditFinding(
                        "REJECT_HARD",
                        "TTY_DOWNGRADE",
                        "Potential uninstall TTY/confirmation downgrade detected",
                        file_diff.path,
                    )
                )
                break
    return findings


def _check_indirect_tty_relaxation(file_diffs: Sequence[_FileDiff]) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for file_diff in file_diffs:
        if file_diff.path not in UNINSTALL_TARGET_FILES:
            continue
        for line in file_diff.lines:
            if not line.startswith(("+", "-")):
                continue
            if any(pattern.search(line) for pattern in INDIRECT_TTY_POLICY_PATTERNS):
                severity = "WARN"
                if "yes" in line.lower() or "confirm" in line.lower() or "interactive" in line.lower():
                    severity = "REJECT_HARD"
                findings.append(
                    AuditFinding(
                        severity,
                        "TTY_POLICY_INDIRECT_RELAXATION",
                        "Potential uninstall TTY/confirmation policy relaxation via constants/defaults detected",
                        file_diff.path,
                    )
                )
                break
    return findings


def _scan_tokens(
    file_diffs: Iterable[_FileDiff],
    tokens: Iterable[str],
    severity: str,
    rule_id: str,
    message: str,
) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    seen: set[tuple[str, str]] = set()
    for file_diff in file_diffs:
        for line in file_diff.lines:
            if not line.startswith(("+", "-")):
                continue
            for token in tokens:
                if token in line:
                    key = (file_diff.path, token)
                    if key in seen:
                        continue
                    seen.add(key)
                    findings.append(AuditFinding(severity, rule_id, f"{message}: {token}", file_diff.path))
    return findings


def _check_contract_consistency(file_diffs: Iterable[_FileDiff]) -> list[AuditFinding]:
    uninstall_help_changed = False
    uninstall_control_changed = False

    for file_diff in file_diffs:
        if file_diff.path != "hermes_cli/main.py":
            continue
        for line in file_diff.lines:
            if "uninstall" not in line.lower() or not line.startswith(("+", "-")):
                continue
            if any(pattern.search(line) for pattern in HELP_TEXT_PATTERNS):
                uninstall_help_changed = True
            if any(pattern.search(line) for pattern in CONTROL_FLOW_PATTERNS):
                uninstall_control_changed = True

    if uninstall_help_changed and not uninstall_control_changed:
        return [
            AuditFinding(
                "WARN",
                "CONTRACT_CONSISTENCY",
                "Uninstall help/args text changed without corresponding control-flow change",
                "hermes_cli/main.py",
            )
        ]
    return []


def _check_argument_alias_semantic_drift(file_diffs: Sequence[_FileDiff]) -> list[AuditFinding]:
    alias_or_arg_changed = False
    flow_changed = False

    for file_diff in file_diffs:
        if file_diff.path != "hermes_cli/main.py":
            continue
        for line in file_diff.lines:
            if not line.startswith(("+", "-")):
                continue
            if any(pattern.search(line) for pattern in ARG_ALIAS_PATTERNS):
                alias_or_arg_changed = True
            if any(pattern.search(line) for pattern in ARG_FLOW_PATTERNS):
                flow_changed = True

    if alias_or_arg_changed and not flow_changed:
        return [
            AuditFinding(
                "REJECT_HARD",
                "ARG_ALIAS_SEMANTIC_DRIFT",
                "Argument names/aliases changed without corresponding uninstall control-flow change",
                "hermes_cli/main.py",
            )
        ]
    return []
