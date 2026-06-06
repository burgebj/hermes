from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List, Sequence

_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_WHITESPACE_RE = re.compile(r"\s+")
_DEFAULT_MAX_CHARS = 1200
_DEFAULT_MIN_CHARS = 400


@dataclass(frozen=True)
class MemorySourceRef:
    source_kind: str
    source_id: str
    source_path: str = ""


@dataclass(frozen=True)
class MemoryChunk:
    id: str
    document_id: str
    chunk_index: int
    text: str
    header_path: tuple[str, ...]
    memory_type: str
    scope: str
    source_kind: str
    source_id: str
    source_path: str
    created_at: str
    updated_at: str
    freshness_hint: str = "stable"
    confidence: float = 1.0
    tags: tuple[str, ...] = field(default_factory=tuple)
    canonical: bool = True

    def metadata(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "header_path": list(self.header_path),
            "memory_type": self.memory_type,
            "scope": self.scope,
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "source_path": self.source_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "freshness_hint": self.freshness_hint,
            "confidence": self.confidence,
            "tags": list(self.tags),
            "canonical": self.canonical,
        }


@dataclass(frozen=True)
class MemoryDocument:
    source: MemorySourceRef
    text: str
    memory_type: str
    scope: str
    created_at: str
    updated_at: str
    freshness_hint: str = "stable"
    confidence: float = 1.0
    tags: tuple[str, ...] = field(default_factory=tuple)
    canonical: bool = True
    title: str = ""

    @property
    def id(self) -> str:
        payload = "\n".join(
            [
                self.source.source_kind,
                self.source.source_id,
                self.source.source_path,
                self.memory_type,
                self.scope,
                self.title,
                _normalize_text(self.text),
            ]
        )
        return _stable_id("doc", payload)

    def chunk(self, *, max_chars: int = _DEFAULT_MAX_CHARS, min_chars: int = _DEFAULT_MIN_CHARS) -> list[MemoryChunk]:
        sections = _split_sections(self.text)
        assembled: list[tuple[tuple[str, ...], str]] = []
        buffer_parts: list[str] = []
        buffer_headers: tuple[str, ...] = tuple()
        for headers, text in sections:
            parts = _split_bounded(text, max_chars=max_chars)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if not buffer_parts:
                    buffer_headers = headers
                    buffer_parts = [part]
                    continue
                if headers != buffer_headers:
                    assembled.append((buffer_headers, "\n\n".join(buffer_parts).strip()))
                    buffer_headers = headers
                    buffer_parts = [part]
                    continue
                current_buffer = "\n\n".join(buffer_parts)
                candidate = "\n\n".join(buffer_parts + [part])
                if len(candidate) <= max_chars:
                    buffer_parts.append(part)
                    continue
                assembled.append((buffer_headers, current_buffer.strip()))
                buffer_headers = headers
                buffer_parts = [part]
        if buffer_parts:
            assembled.append((buffer_headers, "\n\n".join(buffer_parts).strip()))
        assembled = _merge_small_chunks(assembled, max_chars=max_chars, min_chars=min_chars)

        return [
            MemoryChunk(
                id=_chunk_id(self.id, headers, index, text),
                document_id=self.id,
                chunk_index=index,
                text=text,
                header_path=headers,
                memory_type=self.memory_type,
                scope=self.scope,
                source_kind=self.source.source_kind,
                source_id=self.source.source_id,
                source_path=self.source.source_path,
                created_at=self.created_at,
                updated_at=self.updated_at,
                freshness_hint=self.freshness_hint,
                confidence=self.confidence,
                tags=self.tags,
                canonical=self.canonical,
            )
            for index, (headers, text) in enumerate(assembled)
        ]


def build_memory_document(
    *,
    text: str,
    source_kind: str,
    source_id: str,
    source_path: str = "",
    memory_type: str,
    scope: str,
    created_at: str | None = None,
    updated_at: str | None = None,
    freshness_hint: str = "stable",
    confidence: float = 1.0,
    tags: Sequence[str] | None = None,
    canonical: bool = True,
    title: str = "",
) -> MemoryDocument:
    now = _iso_now()
    return MemoryDocument(
        source=MemorySourceRef(source_kind=source_kind, source_id=source_id, source_path=source_path),
        text=text,
        memory_type=memory_type,
        scope=scope,
        created_at=created_at or now,
        updated_at=updated_at or created_at or now,
        freshness_hint=freshness_hint,
        confidence=confidence,
        tags=tuple(tags or ()),
        canonical=canonical,
        title=title,
    )


def _split_sections(text: str) -> list[tuple[tuple[str, ...], str]]:
    headers: list[str] = []
    sections: list[tuple[tuple[str, ...], str]] = []
    body: list[str] = []

    def flush() -> None:
        content = "\n".join(body).strip()
        if content:
            sections.append((tuple(headers), content))
        body.clear()

    for raw_line in text.splitlines():
        match = _HEADER_RE.match(raw_line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            headers[:] = headers[: level - 1]
            headers.append(title)
            continue
        body.append(raw_line)
    flush()
    if sections:
        return sections
    stripped = text.strip()
    if headers and not body:
        return [(tuple(headers), " ".join(headers).strip())]
    return [(tuple(), stripped)]


def _split_bounded(text: str, *, max_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(paragraph) <= max_chars:
            current = paragraph
            continue
        chunks.extend(_split_long_paragraph(paragraph, max_chars=max_chars))
    if current:
        chunks.append(current)
    return chunks


def _split_long_paragraph(text: str, *, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


def _merge_small_chunks(
    chunks: list[tuple[tuple[str, ...], str]], *, max_chars: int, min_chars: int
) -> list[tuple[tuple[str, ...], str]]:
    if min_chars <= 0 or len(chunks) < 2:
        return chunks
    merged: list[tuple[tuple[str, ...], str]] = []
    for headers, text in chunks:
        text = text.strip()
        if not text:
            continue
        if merged:
            previous_headers, previous_text = merged[-1]
            candidate = f"{previous_text}\n\n{text}"
            if headers == previous_headers and (
                len(previous_text) < min_chars or len(text) < min_chars
            ) and len(candidate) <= max_chars:
                merged[-1] = (headers, candidate)
                continue
        merged.append((headers, text))
    return merged


def _chunk_id(document_id: str, headers: Iterable[str], chunk_index: int, text: str) -> str:
    header_key = " > ".join(headers)
    payload = f"{document_id}\n{chunk_index}\n{header_key}\n{_normalize_text(text)}"
    return _stable_id("chunk", payload)


def _stable_id(prefix: str, payload: str) -> str:
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def _normalize_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.strip())


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
