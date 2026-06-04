"""Persistent context anchors for messaging chats and threads."""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from gateway.config import Platform
from gateway.session import SessionSource

_CONTEXT_ANCHOR_RE = re.compile(
    r"\[context:(?P<type>[a-z][a-z0-9_-]{0,63}):(?P<id>[^\]\s][^\]]*?)\]",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


@dataclass(frozen=True)
class ContextAnchor:
    """A durable reference that helps recover context for a chat lane."""

    anchor_type: str
    anchor_id: str
    title: str = ""
    url: str = ""
    source: str = "manual"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.anchor_type,
            "id": self.anchor_id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "ContextAnchor | None":
        if not isinstance(data, dict):
            return None
        anchor_type = str(data.get("type") or data.get("anchor_type") or "").strip().lower()
        anchor_id = str(data.get("id") or data.get("anchor_id") or "").strip()
        if not anchor_type or not anchor_id:
            return None
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        return cls(
            anchor_type=anchor_type,
            anchor_id=anchor_id,
            title=str(data.get("title") or "").strip(),
            url=str(data.get("url") or "").strip(),
            source=str(data.get("source") or "manual").strip() or "manual",
            metadata=dict(metadata),
        )


def parse_context_anchor_marker(text: str | None) -> ContextAnchor | None:
    """Parse a generic ``[context:<type>:<id>]`` marker from text."""

    if not text:
        return None
    match = _CONTEXT_ANCHOR_RE.search(text)
    if not match:
        return None
    anchor_type = (match.group("type") or "").strip().lower()
    anchor_id = (match.group("id") or "").strip()
    if not anchor_type or not anchor_id:
        return None
    return ContextAnchor(anchor_type=anchor_type, anchor_id=anchor_id, source="thread-title")


def infer_anchor_type(anchor_id: str) -> str:
    """Infer a useful type for URL/freeform anchors when users omit one."""

    value = (anchor_id or "").strip()
    if _URL_RE.match(value):
        return "url"
    return "reference"


class ContextAnchorStore:
    """Durable mapping from platform chat/thread lanes to context anchors."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.RLock()

    def bind(
        self,
        source: SessionSource,
        *,
        anchor_type: str,
        anchor_id: str,
        title: str = "",
        url: str = "",
        source_label: str = "manual",
        metadata: dict[str, Any] | None = None,
    ) -> ContextAnchor:
        anchor_type = str(anchor_type or "").strip().lower()
        anchor_id = str(anchor_id or "").strip()
        if not anchor_type:
            raise ValueError("anchor_type is required")
        if not anchor_id:
            raise ValueError("anchor_id is required")
        anchor = ContextAnchor(
            anchor_type=anchor_type,
            anchor_id=anchor_id,
            title=str(title or "").strip(),
            url=str(url or "").strip(),
            source=str(source_label or "manual").strip() or "manual",
            metadata=dict(metadata or {}),
        )
        with self._lock:
            data = self._read()
            data[self._source_key(source)] = anchor.to_dict()
            self._write(data)
        return anchor

    def unbind(self, source: SessionSource) -> ContextAnchor | None:
        with self._lock:
            data = self._read()
            raw = data.pop(self._source_key(source), None)
            if raw is None:
                return None
            self._write(data)
        return ContextAnchor.from_dict(raw)

    def resolve_for_source(self, source: SessionSource) -> ContextAnchor | None:
        with self._lock:
            data = self._read()
            anchor = ContextAnchor.from_dict(data.get(self._source_key(source)))
        if anchor:
            return anchor
        return parse_context_anchor_marker(getattr(source, "chat_name", None)) or parse_context_anchor_marker(
            getattr(source, "chat_topic", None)
        )

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(raw, dict):
            return {}
        anchors = raw.get("anchors", raw)
        if not isinstance(anchors, dict):
            return {}
        return {str(key): value for key, value in anchors.items() if isinstance(value, dict)}

    def _write(self, anchors: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "anchors": anchors}
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
            tmp_path = Path(tmp.name)
        tmp_path.replace(self.path)

    @staticmethod
    def _source_key(source: SessionSource) -> str:
        platform = getattr(getattr(source, "platform", None), "value", None) or str(
            getattr(source, "platform", "") or Platform.LOCAL.value
        )
        parts = [
            platform,
            str(getattr(source, "guild_id", None) or ""),
            str(getattr(source, "parent_chat_id", None) or ""),
            str(getattr(source, "chat_id", "") or ""),
            str(getattr(source, "thread_id", None) or ""),
        ]
        return ":".join(part.replace(":", "%3A") for part in parts)
