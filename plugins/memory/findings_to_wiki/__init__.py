"""
findings_to_wiki — MemoryProvider that saves facts to MEMORY.md AND
detects structured research findings (Prism, ADR, analysis) to save as
wiki artifacts.

Configurable via config.yaml:

  plugins:
    findings-to-wiki:
      wiki_path: ~/wiki                    # default: ~/wiki
      memory_char_limit: 2200              # default: 2200
      detect_patterns:
        prism:
          - "(?i)\\\\b## .*?Findings\\\\b"
          - "(?i)\\\\b## .*?Conservation\\\\b"
          - "(?i)\\\\b## .*?Deepest\\\\b"
        adr:
          - "(?i)\\\\b## (Статус|Контекст|Decision)\\\\b"
        research:
          - "(?i)\\\\b## .*?(Key Findings|Recommendations)\\\\b"

If config section is absent — works with built-in defaults (backward compat).
"""

from __future__ import annotations

import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider
from hermes_constants import get_hermes_home
from hermes_cli.config import cfg_get

logger = logging.getLogger(__name__)

ENTRY_DELIMITER = "\n§\n"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_plugin_config() -> dict:
    """Read config from plugins.findings-to-wiki in config.yaml."""
    try:
        config_path = get_hermes_home() / "config.yaml"
        if not config_path.exists():
            return {}
        import yaml
        with open(config_path) as f:
            full = yaml.safe_load(f) or {}
        return cfg_get(full, "plugins", "findings-to-wiki", default={}) or {}
    except Exception:
        return {}

# ---------------------------------------------------------------------------
# Trivial acknowledgements to skip
# ---------------------------------------------------------------------------

TRIVIAL_PATTERNS = (
    "спасибо", "понял", "ok", "okay", "хорошо", "ладно",
    "понятно", "thanks", "agree", "согласен", "+1", "👍",
    "давай", "окей",
)

# ---------------------------------------------------------------------------
# Default structured patterns (used if config has no detect_patterns)
# ---------------------------------------------------------------------------

DEFAULT_PATTERNS: list[tuple[str, str]] = [
    # Prism analysis
    (r"(?i)## (Findings|Findings Table|Conservation Law|Deepest finding)", "prism"),
    (r"(?i)## (Ключевые находки|Рекомендаци)", "research"),
    (r"(?i)^\| \# \|", "prism"),
    # ADR
    (r"(?i)## (Статус|Контекст|Принятое решение|Declarations?|Decision)", "adr"),
    # Research
    (r"(?i)## (Key Findings|Verification|Actionable Recommendations)", "research"),
]

# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def _read_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, IOError):
        return []
    if not raw.strip():
        return []
    entries = [e.strip() for e in raw.split(ENTRY_DELIMITER)]
    return [e for e in entries if e]


def _write_file(path: Path, entries: list[str]) -> None:
    content = ENTRY_DELIMITER.join(entries) if entries else ""
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent), suffix=".tmp", prefix=".mem_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except (OSError, IOError) as e:
        logger.warning("findings_to_wiki write failed: %s", e)


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:80].strip("-")


# ---------------------------------------------------------------------------
# Config-aware pattern loading
# ---------------------------------------------------------------------------

def _load_patterns(plugin_cfg: dict) -> list[tuple[re.Pattern, str]]:
    """Build pattern list from config or fall back to defaults."""
    custom = plugin_cfg.get("detect_patterns", {})
    if not custom or not isinstance(custom, dict):
        # Fall back to defaults
        return [(re.compile(p), t) for p, t in DEFAULT_PATTERNS]

    result = []
    for ftype, pat_list in custom.items():
        if not isinstance(pat_list, list):
            continue
        for pat_str in pat_list:
            try:
                result.append((re.compile(pat_str), ftype))
            except re.error as e:
                logger.warning("Invalid pattern '%s' for type '%s': %s", pat_str, ftype, e)
    return result


def _detect_finding_type(text: str, patterns: list[tuple[re.Pattern, str]]) -> str | None:
    """Detect structured finding in text using configured patterns."""
    matches: dict[str, int] = {}
    for pattern, ftype in patterns:
        if pattern.search(text):
            matches[ftype] = matches.get(ftype, 0) + 1
    if not matches:
        return None
    total = sum(matches.values())
    if total < 2:
        return None
    return max(matches, key=matches.get)


# ---------------------------------------------------------------------------
# Wiki helpers
# ---------------------------------------------------------------------------

def _get_wiki_paths(plugin_cfg: dict) -> tuple[Path, Path]:
    """Return (wiki_dir, raw_findings_dir) from config or defaults."""
    wiki_str = plugin_cfg.get("wiki_path", "~/wiki")
    wiki_dir = Path(wiki_str).expanduser()
    raw_dir = wiki_dir / "raw" / "auto-findings"
    return wiki_dir, raw_dir


def _extract_title(text: str) -> str:
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("# ") or line.startswith("## "):
            return line.lstrip("#").strip()
    for line in text.split("\n"):
        line = line.strip()
        if line and len(line) > 20:
            return line[:80]
    return "Untitled Finding"


def _generate_frontmatter(ftype: str, title: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    tags = ["auto-generated", f"detected-{ftype}"]
    return f"""---
verification_status: unverified
confidence: low
tags: [{', '.join(tags)}]
---

# {title}

*Auto-generated from conversation on {today}*

"""


def _save_to_raw(text: str, ftype: str, raw_dir: Path) -> bool:
    raw_dir.mkdir(parents=True, exist_ok=True)
    title = _extract_title(text)
    slug = _slugify(title) if title else f"finding-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f"{timestamp}-{slug}.md"
    filepath = raw_dir / filename
    content = f"""---
type: auto-detected-finding
detected_type: {ftype}
detected_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
source: conversation-turn
---

{text.strip()}
"""
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(raw_dir), suffix=".tmp", prefix=f".{slug}_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, filepath)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        logger.info("Saved raw finding: %s (%s)", filename, ftype)
        return True
    except (OSError, IOError) as e:
        logger.warning("Failed to save raw finding %s: %s", filename, e)
        return False


# ---------------------------------------------------------------------------
# Fact extraction (same as before)
# ---------------------------------------------------------------------------

def _extract_fact(user_msg: str, asst_msg: str) -> str | None:
    u = (user_msg or "").strip()
    a = (asst_msg or "").strip()
    if len(u) + len(a) < 60:
        return None
    u_lower = u.lower()
    if len(u) < 20 and any(u_lower.startswith(p) for p in TRIVIAL_PATTERNS):
        return None
    u_line = u.split("\n")[0][:200]
    a_line = a.split("\n")[0][:200]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{timestamp}: Пользователь: {u_line} / Ответ: {a_line}"


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class FindingsToWikiProvider(MemoryProvider):
    """MemoryProvider with configurable patterns and paths."""

    def __init__(self):
        self._mem_path: Path | None = None
        self._raw_dir: Path | None = None
        self._patterns: list[tuple[re.Pattern, str]] = []
        self._memory_char_limit = 2200
        self._initialized = False

    @property
    def name(self) -> str:
        return "findings_to_wiki"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str = "", **kwargs) -> None:
        try:
            cfg = _load_plugin_config()
            self._patterns = _load_patterns(cfg)
            self._memory_char_limit = int(cfg.get("memory_char_limit", 2200))
            _, self._raw_dir = _get_wiki_paths(cfg)
            mem_dir = get_hermes_home() / "memories"
            mem_dir.mkdir(parents=True, exist_ok=True)
            self._mem_path = mem_dir / "MEMORY.md"
            self._initialized = True
            logger.info(
                "findings-to-wiki ready: %d patterns, wiki=%s, limit=%d",
                len(self._patterns), self._raw_dir, self._memory_char_limit,
            )
        except Exception as e:
            logger.warning("findings-to-wiki init failed: %s", e)

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return []

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
    ) -> None:
        if not self._initialized or not self._mem_path or not self._raw_dir:
            return
        try:
            asst = (assistant_content or "").strip()
            user = (user_content or "").strip()

            # 1. Detect structured findings
            if len(asst) > 100 and self._patterns:
                ftype = _detect_finding_type(asst, self._patterns)
                if ftype:
                    saved = _save_to_raw(asst, ftype, self._raw_dir)
                    if saved:
                        logger.info("Auto-saved raw finding: %s", ftype)

            # 2. Save fact to MEMORY.md
            fact = _extract_fact(user, asst)
            if fact:
                entries = _read_file(self._mem_path)
                entries = list(dict.fromkeys(entries))
                if not (entries and entries[-1] == fact):
                    entries.append(fact)
                    joined = ENTRY_DELIMITER.join(entries)
                    while len(joined) > self._memory_char_limit and len(entries) > 1:
                        entries.pop(0)
                        joined = ENTRY_DELIMITER.join(entries)
                    _write_file(self._mem_path, entries)

        except Exception as e:
            logger.warning("findings-to-wiki sync_turn failed: %s", e)

    def on_session_end(self, messages: list[dict[str, Any]]) -> None:
        if not self._initialized or not self._mem_path:
            return
        try:
            if not messages:
                return
            last_user = ""
            last_asst = ""
            for msg in reversed(messages):
                role = msg.get("role", "")
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        p.get("text", "") for p in content if isinstance(p, dict)
                    )
                content = str(content or "").strip()
                if role == "assistant" and not last_asst:
                    last_asst = content[:500]
                elif role == "user" and not last_user:
                    last_user = content[:500]
                if last_user and last_asst:
                    break
            if last_user or last_asst:
                self.sync_turn(last_user, f"[end-of-session] {last_asst}")
        except Exception as e:
            logger.warning("findings-to-wiki on_session_end failed: %s", e)

    def shutdown(self) -> None:
        self._initialized = False
