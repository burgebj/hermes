"""Narrow rewrite registry for Hermes terminal compaction v1."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Optional


UNSAFE_TOKENS = ("&&", "||", "|", ";", "<<", ">", ">>")
DENY_PREFIXES = (
    "rm ",
    "mv ",
    "cp ",
    "chmod ",
    "chown ",
    "sudo ",
    "git push",
    "git commit",
    "git reset",
    "git clean",
    "docker rm",
    "docker stop",
    "docker kill",
)


@dataclass(frozen=True)
class RewriteResult:
    command: str
    reason: str


def _unsafe(command: str) -> bool:
    stripped = command.strip()
    if not stripped:
        return True
    if any(token in stripped for token in UNSAFE_TOKENS):
        return True
    lowered = stripped.lower()
    return any(lowered.startswith(prefix) for prefix in DENY_PREFIXES)


def _split(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return []


def rewrite_command(command: str) -> Optional[RewriteResult]:
    if _unsafe(command):
        return None

    parts = _split(command)
    if not parts:
        return None

    if parts[:2] == ["git", "status"]:
        return RewriteResult(
            command="git status --short --branch",
            reason="compact git status",
        )

    if parts[:2] == ["git", "diff"]:
        return RewriteResult(
            command="git diff --stat --patch --unified=1",
            reason="compact git diff",
        )

    if parts[:2] == ["git", "log"]:
        return RewriteResult(
            command="git log --oneline --decorate -n 20",
            reason="compact git log",
        )

    if parts[0] == "pytest":
        if "-q" in parts or "--quiet" in parts:
            return None
        return RewriteResult(
            command=f"{command} -q --maxfail=5",
            reason="failure-focused pytest",
        )

    if parts[:2] == ["cargo", "test"]:
        if "--" in parts:
            return None
        return RewriteResult(
            command=f"{command} -- --nocapture",
            reason="cargo test with visible failures",
        )

    if parts[:2] == ["npm", "test"]:
        if "--" in parts:
            return None
        return RewriteResult(
            command="npm test -- --runInBand",
            reason="serialized npm test output",
        )

    if parts[:2] == ["pnpm", "test"]:
        if "--" in parts:
            return None
        return RewriteResult(
            command="pnpm test -- --runInBand",
            reason="serialized pnpm test output",
        )

    if parts[:2] == ["docker", "ps"]:
        return RewriteResult(
            command="docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'",
            reason="compact docker ps",
        )

    if parts[0] == "ls":
        if "-1" in parts:
            return None
        return RewriteResult(
            command=f"{command} -1",
            reason="one-entry-per-line ls",
        )

    if parts[0] == "rg":
        if "--max-count" in parts:
            return None
        return RewriteResult(
            command=f"{command} --max-count 5",
            reason="bound ripgrep output",
        )

    return None
