from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from hermes_constants import get_hermes_home


_ENV_CACHE: dict[str, str] | None = None


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def env_value(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value
    global _ENV_CACHE
    if _ENV_CACHE is None:
        _ENV_CACHE = _parse_env_file(Path(get_hermes_home()) / ".env")
    return _ENV_CACHE.get(name, default)


def _csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


@dataclass(frozen=True)
class VisibilityConfig:
    company_name: str
    github_orgs: set[str]
    github_repos: list[str]
    default_slack_channel: str

    def github_repo_allowed(self, repo: str | None) -> bool:
        if not repo or "/" not in repo:
            return False
        owner = repo.split("/", 1)[0]
        if self.github_repos and repo not in self.github_repos:
            return False
        return owner in self.github_orgs

    @property
    def github_scope_label(self) -> str:
        if self.github_orgs:
            return ", ".join(sorted(self.github_orgs))
        return "configured GitHub organisations"


def get_visibility_config() -> VisibilityConfig:
    orgs = set(_csv(env_value("VISIBILITY_OS_GITHUB_ORGS") or env_value("VISIBILITY_OS_GITHUB_ORG_ALLOWLIST")))
    return VisibilityConfig(
        company_name=env_value("VISIBILITY_OS_COMPANY_NAME", "your organisation") or "your organisation",
        github_orgs=orgs,
        github_repos=_csv(env_value("VISIBILITY_OS_GITHUB_REPOS")),
        default_slack_channel=env_value("VISIBILITY_OS_DEFAULT_SLACK_CHANNEL", ""),
    )
