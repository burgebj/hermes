"""Friendly registry for messaging workspace topics/channels.

The registry is operator-owned config, not platform state.  Entries map a
delivery target like ``telegram:-100123:42`` to a stable alias, display name,
and purpose so diagnostics, send-message listings, and workspace guides can use
human labels without hard-coding a specific group into Hermes.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from hermes_cli.config import get_hermes_home, load_config


_SECRET_KEY_RE = re.compile(
    r"(token|secret|password|api[_-]?key|authorization|credential)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TopicRef:
    platform: str
    chat_id: str
    thread_id: str | None = None

    @classmethod
    def parse(cls, value: str, *, default_platform: str | None = None) -> "TopicRef":
        raw = str(value or "").strip()
        if not raw:
            raise ValueError("empty topic ref")
        if ":" in raw and not raw.startswith("-"):
            platform, rest = raw.split(":", 1)
        elif default_platform:
            platform, rest = default_platform, raw
        else:
            raise ValueError(f"topic ref must include platform: {value!r}")

        platform = platform.strip().lower()
        parts = rest.split(":")
        if len(parts) == 1:
            return cls(platform=platform, chat_id=parts[0].strip(), thread_id=None)
        return cls(
            platform=platform,
            chat_id=parts[0].strip(),
            thread_id=":".join(parts[1:]).strip() or None,
        )

    @property
    def id(self) -> str:
        return self.chat_id if not self.thread_id else f"{self.chat_id}:{self.thread_id}"

    @property
    def full(self) -> str:
        return f"{self.platform}:{self.id}"


@dataclass(frozen=True)
class TopicEntry:
    ref: TopicRef
    alias: str
    name: str
    purpose: str = ""
    prompt: str = ""
    delivery: str = ""
    pinned: bool = True

    @property
    def display_name(self) -> str:
        if self.name:
            return self.name
        if self.alias:
            return f"#{self.alias}"
        return self.ref.full


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_prompt_mapping(value: Any) -> Mapping[str, Any]:
    """Return a channel_prompts mapping, accepting legacy JSON strings."""
    if isinstance(value, Mapping):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        return parsed if isinstance(parsed, Mapping) else {}
    return {}


def _entry_from_dict(key: str, data: Mapping[str, Any]) -> TopicEntry | None:
    try:
        ref_text = str(data.get("target") or data.get("ref") or key)
        ref = TopicRef.parse(ref_text)
    except ValueError:
        return None
    alias = str(data.get("alias") or key.rsplit(":", 1)[-1]).strip().lstrip("#")
    name = str(data.get("name") or data.get("display_name") or "").strip()
    if not name and alias:
        name = f"#{alias}"
    return TopicEntry(
        ref=ref,
        alias=alias,
        name=name,
        purpose=str(data.get("purpose") or "").strip(),
        prompt=str(data.get("prompt") or "").strip(),
        delivery=str(data.get("delivery") or ref.full).strip(),
        pinned=bool(data.get("pinned", True)),
    )


def _iter_registry_config(config: Mapping[str, Any] | None) -> Iterable[TopicEntry]:
    cfg = _as_mapping(config)
    workspace = _as_mapping(cfg.get("workspace"))
    raw_registry = _as_mapping(workspace.get("topic_registry"))
    topics = raw_registry.get("topics", raw_registry)
    if isinstance(topics, list):
        for item in topics:
            if isinstance(item, Mapping):
                entry = _entry_from_dict(str(item.get("alias") or item.get("target") or ""), item)
                if entry:
                    yield entry
        return
    if isinstance(topics, Mapping):
        for key, item in topics.items():
            if isinstance(item, Mapping):
                entry = _entry_from_dict(str(key), item)
                if entry:
                    yield entry


def load_topic_registry(config: Mapping[str, Any] | None = None) -> dict[str, TopicEntry]:
    """Return topic entries keyed by ``platform:chat_id[:thread_id]``."""
    if config is None:
        try:
            config = load_config()
        except Exception:
            config = {}
    entries: dict[str, TopicEntry] = {}
    for entry in _iter_registry_config(config):
        entries[entry.ref.full] = entry
    return entries


def find_topic_entry(
    platform: str,
    chat_id: str | None,
    thread_id: str | None = None,
    *,
    config: Mapping[str, Any] | None = None,
) -> TopicEntry | None:
    if not platform or not chat_id:
        return None
    registry = load_topic_registry(config)
    full = TopicRef(platform.lower(), str(chat_id), str(thread_id) if thread_id else None).full
    return registry.get(full) or registry.get(TopicRef(platform.lower(), str(chat_id), None).full)


def friendly_target_label(
    platform: str,
    chat_id: str | None,
    thread_id: str | None = None,
    *,
    fallback_name: str | None = None,
    config: Mapping[str, Any] | None = None,
) -> str:
    entry = find_topic_entry(platform, chat_id, thread_id, config=config)
    if entry:
        return entry.display_name
    if fallback_name:
        return fallback_name
    if not chat_id:
        return platform
    return str(chat_id) if not thread_id else f"{chat_id}:{thread_id}"


def channel_prompt_keys(config: Mapping[str, Any] | None = None) -> set[str]:
    cfg = _as_mapping(config if config is not None else load_config())
    keys: set[str] = set()
    for platform in ("telegram", "discord", "slack", "mattermost"):
        prompts = _as_prompt_mapping(_as_mapping(cfg.get(platform)).get("channel_prompts"))
        for key in prompts:
            keys.add(f"{platform}:{key}")
    return keys


def describe_current_topic(source: Any, config: Mapping[str, Any] | None = None) -> str:
    platform = getattr(getattr(source, "platform", None), "value", None) or getattr(source, "platform", "")
    chat_id = str(getattr(source, "chat_id", "") or "")
    thread_id = str(getattr(source, "thread_id", "") or "") or None
    chat_name = str(getattr(source, "chat_name", "") or chat_id or "unknown")
    entry = find_topic_entry(platform, chat_id, thread_id, config=config)
    full = TopicRef(platform, chat_id, thread_id).full if platform and chat_id else "unknown"
    prompt_keys = channel_prompt_keys(config)
    prompt_key = full if thread_id else f"{platform}:{chat_id}"

    lines = [
        "Current workspace target:",
        f"- Platform: {platform or 'unknown'}",
        f"- Chat: {chat_name} ({chat_id or 'unknown'})",
        f"- Thread/topic ID: {thread_id or 'none'}",
        f"- Target ref: {full}",
        f"- Alias: {('#' + entry.alias) if entry and entry.alias else 'unconfigured'}",
        f"- Friendly name: {entry.display_name if entry else 'unconfigured'}",
        f"- Purpose: {entry.purpose if entry and entry.purpose else 'unconfigured'}",
        f"- Channel prompt: {'configured' if prompt_key in prompt_keys else 'missing'}",
        f"- Delivery target: {entry.delivery if entry and entry.delivery else full}",
    ]
    return "\n".join(lines)


def generate_workspace_guide(config: Mapping[str, Any] | None = None) -> str:
    registry = sorted(load_topic_registry(config).values(), key=lambda e: (e.ref.platform, e.ref.chat_id, e.ref.thread_id or ""))
    if not registry:
        return "No workspace topics are configured under workspace.topic_registry.topics."
    lines = ["# Hermes Workspace Guide", "", "Known topics:"]
    for entry in registry:
        thread = f" topic {entry.ref.thread_id}" if entry.ref.thread_id else " main chat"
        purpose = f" — {entry.purpose}" if entry.purpose else ""
        lines.append(f"- {entry.display_name} (`{entry.ref.full}`,{thread}){purpose}")
    lines.extend(["", "Use `/whereami` in any chat/topic to verify Hermes sees the intended target."])
    return "\n".join(lines)


def _safe_env_snapshot(env: Mapping[str, str] | None = None) -> dict[str, str]:
    src = env if env is not None else os.environ
    wanted = (
        "TELEGRAM_HOME_CHANNEL",
        "TELEGRAM_HOME_CHANNEL_THREAD_ID",
        "TELEGRAM_CRON_THREAD_ID",
        "HERMES_BACKGROUND_NOTIFICATION_TARGET",
        "HERMES_KANBAN_NOTIFY_TARGET",
        "BLAZEMIND_NOTIFY_TARGET",
    )
    result = {}
    for key in wanted:
        value = src.get(key, "")
        if not value:
            continue
        result[key] = "***" if _SECRET_KEY_RE.search(key) else str(value)
    return result


def _load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def collect_workspace_sources(config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    cfg = _as_mapping(config if config is not None else load_config())
    home = get_hermes_home()
    directory = _load_json_file(home / "channel_directory.json") or {"platforms": {}}
    jobs = _load_json_file(home / "cron" / "jobs.json") or []
    if isinstance(jobs, Mapping):
        raw_jobs = jobs.get("jobs")
        jobs = raw_jobs if isinstance(raw_jobs, list) else list(jobs.values())
    return {
        "registry": load_topic_registry(cfg),
        "channel_prompts": sorted(channel_prompt_keys(cfg)),
        "channel_directory": directory,
        "cron_jobs": jobs if isinstance(jobs, list) else [],
        "env": _safe_env_snapshot(),
        "service_urls": _as_mapping(_as_mapping(cfg.get("workspace")).get("service_urls")),
    }


def check_topic_drift(config: Mapping[str, Any] | None = None) -> list[str]:
    sources = collect_workspace_sources(config)
    registry_refs = set(sources["registry"].keys())
    prompt_refs = set(sources["channel_prompts"])
    issues: list[str] = []

    for ref in sorted(prompt_refs - registry_refs):
        issues.append(f"channel_prompts defines {ref}, but workspace.topic_registry omits it")
    for ref in sorted(registry_refs - prompt_refs):
        issues.append(f"workspace.topic_registry defines {ref}, but channel_prompts has no prompt")

    directory_refs = set()
    for platform, channels in _as_mapping(sources["channel_directory"].get("platforms")).items():
        if isinstance(channels, list):
            for channel in channels:
                if not isinstance(channel, Mapping) or not channel.get("id"):
                    continue
                # Drift checks focus on workspace topics/channels.  Personal DMs
                # discovered by the gateway are not operator-managed group
                # workspaces and should not require aliases.
                if str(channel.get("type") or "").lower() == "dm":
                    continue
                directory_refs.add(f"{platform}:{channel['id']}")
    for ref in sorted(directory_refs - registry_refs):
        issues.append(f"channel_directory discovered {ref}, but registry has no alias")

    for job in sources["cron_jobs"]:
        if not isinstance(job, Mapping):
            continue
        deliver = str(job.get("deliver") or "").strip()
        if ":" not in deliver:
            continue
        for part in [p.strip() for p in deliver.split(",") if p.strip()]:
            if ":" in part and part not in registry_refs:
                issues.append(f"cron job {job.get('id', '?')} delivers to {part}, but registry omits it")

    for key, value in sources["env"].items():
        if key.endswith("_THREAD_ID") and value:
            chat = sources["env"].get("TELEGRAM_HOME_CHANNEL", "")
            if chat and f"telegram:{chat}:{value}" not in registry_refs:
                issues.append(f"{key} points at telegram:{chat}:{value}, but registry omits it")
        if ":" in value:
            try:
                ref = TopicRef.parse(value).full
            except ValueError:
                continue
            if ref not in registry_refs:
                issues.append(f"{key} points at {ref}, but registry omits it")

    return issues


def generate_ops_index(config: Mapping[str, Any] | None = None) -> str:
    sources = collect_workspace_sources(config)
    lines = ["# Hermes Ops Index", ""]
    lines.append("## Topics")
    for entry in sorted(sources["registry"].values(), key=lambda e: e.display_name):
        lines.append(f"- {entry.display_name}: `{entry.ref.full}` — {entry.purpose or 'no purpose configured'}")
    if not sources["registry"]:
        lines.append("- No registry entries configured.")

    lines.extend(["", "## Cron Jobs"])
    jobs = sources["cron_jobs"]
    if jobs:
        for job in jobs:
            if isinstance(job, Mapping):
                lines.append(f"- {job.get('name') or job.get('id')}: deliver `{job.get('deliver', 'local')}`")
    else:
        lines.append("- No cron jobs found.")

    lines.extend(["", "## Alert Routes"])
    env = sources["env"]
    if env:
        for key, value in sorted(env.items()):
            lines.append(f"- {key}: `{value}`")
    else:
        lines.append("- No alert route environment defaults found.")

    lines.extend(["", "## Service URLs"])
    service_urls = sources["service_urls"]
    if service_urls:
        for name, url in sorted(service_urls.items()):
            lines.append(f"- {name}: {url}")
    else:
        lines.append("- No service URLs configured under workspace.service_urls.")
    return "\n".join(lines)


ETERNAL_EXAMPLE_TOPICS: dict[str, dict[str, str]] = {
    "root": {
        "target": "telegram:-1003932124823",
        "name": "Eternal / root",
        "purpose": "group-level chat/routing diagnostics",
    },
    "general": {
        "target": "telegram:-1003932124823:1",
        "name": "Eternal / #general",
        "purpose": "chat/tasks/requests",
    },
    "alerts": {
        "target": "telegram:-1003932124823:14",
        "name": "Eternal / #alerts",
        "purpose": "notifications/alerts",
    },
    "dev-logs": {
        "target": "telegram:-1003932124823:15",
        "name": "Eternal / #dev-logs",
        "purpose": "builds/CI/errors",
    },
    "media": {
        "target": "telegram:-1003932124823:16",
        "name": "Eternal / #media",
        "purpose": "images/video/screenshots",
    },
    "decisions": {
        "target": "telegram:-1003932124823:17",
        "name": "Eternal / #decisions",
        "purpose": "config changes/decisions",
    },
    "briefings-alerts": {
        "target": "telegram:-1003932124823:707",
        "name": "Eternal / Briefings & Alerts",
        "purpose": "briefings, cron output, and ecosystem reports",
    },
    "agent-workbench": {
        "target": "telegram:-1003932124823:708",
        "name": "Eternal / Agent Workbench",
        "purpose": "agent/Codex work and Telegram workspace admin/meta",
    },
}
