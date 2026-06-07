"""Provider-neutral formatting for graph-shaped memory recall packets.

The dataclasses in this module intentionally avoid importing any concrete
memory provider types. Hindsight, Atlas, session search, or another provider
can map their native response objects into this small contract and then render
bounded, provenance-forward text for context injection or tool output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

_METADATA_ALLOWLIST = (
    "source",
    "session_id",
    "platform",
    "chat_name",
    "thread_id",
    "turn_index",
    "retained_at",
    "agent_identity",
)


@dataclass
class EntityObservation:
    """A short observation attached to a canonical entity."""

    text: str
    mentioned_at: str | None = None


@dataclass
class RecallEntity:
    """Canonical entity plus supporting observations."""

    entity_id: str | None = None
    canonical_name: str = ""
    observations: list[EntityObservation] = field(default_factory=list)


@dataclass
class RecallObservation:
    """One top-level memory observation/snippet returned by recall."""

    text: str
    type: str | None = None
    entities: list[str] = field(default_factory=list)
    context: str | None = None
    occurred_start: str | None = None
    occurred_end: str | None = None
    mentioned_at: str | None = None
    document_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_id: str | None = None
    tags: list[str] = field(default_factory=list)
    source_fact_ids: list[str] = field(default_factory=list)


@dataclass
class RecallEvidenceChunk:
    """A bounded source chunk handle associated with recall."""

    id: str
    text: str = ""
    chunk_index: int | None = None
    truncated: bool | None = None


@dataclass
class RecallPacket:
    """Provider-neutral graph recall packet."""

    query: str
    observations: list[RecallObservation] = field(default_factory=list)
    entities: list[RecallEntity] = field(default_factory=list)
    chunks: list[RecallEvidenceChunk] = field(default_factory=list)
    source_facts: list[Any] = field(default_factory=list)
    trace: Any | None = None


def format_recall_packet(
    packet: RecallPacket,
    *,
    compact: bool = False,
    max_observations: int = 6,
    max_entities: int = 8,
    max_entity_observations: int = 3,
    max_evidence: int = 6,
    show_metadata: bool = False,
) -> str:
    """Render *packet* as bounded Markdown/text.

    ``compact=True`` is intended for automatic context injection. ``compact=False``
    keeps more provenance detail for explicit tool calls. Both modes preserve
    the same trust semantics: this is candidate memory, not verified truth.
    """
    max_observations = _positive_or_default(max_observations, 6)
    max_entities = _positive_or_default(max_entities, 8)
    max_entity_observations = _positive_or_default(max_entity_observations, 3)
    max_evidence = _positive_or_default(max_evidence, 6)

    if not (packet.observations or packet.entities or packet.source_facts or packet.chunks):
        return "No relevant memories found."

    if compact:
        return _format_compact(
            packet,
            max_observations=max_observations,
            max_entities=max_entities,
            max_entity_observations=max_entity_observations,
        )

    return _format_full(
        packet,
        max_observations=max_observations,
        max_entities=max_entities,
        max_entity_observations=max_entity_observations,
        max_evidence=max_evidence,
        show_metadata=show_metadata,
    )


def _format_compact(
    packet: RecallPacket,
    *,
    max_observations: int,
    max_entities: int,
    max_entity_observations: int,
) -> str:
    lines: list[str] = [
        "# Memory Recall Packet",
        "Status: candidate context; verify important claims before acting.",
        f"Query: {_inline(packet.query)}",
    ]

    if packet.observations:
        lines.append("Observations:")
        shown, omitted = _cap(packet.observations, max_observations)
        for observation in shown:
            handles = _compact_observation_handles(observation)
            suffix = f" [{handles}]" if handles else ""
            warning = "; warning: missing source handle" if _missing_source_handle(observation) else ""
            lines.append(f"- {_truncate(_one_line(observation.text), 260)}{suffix}{warning}")
        if omitted:
            lines.append(f"- … {omitted} more observation(s) omitted.")

    if packet.entities:
        lines.append("Entities:")
        shown_entities, omitted_entities = _cap(packet.entities, max_entities)
        for entity in shown_entities:
            name = _one_line(entity.canonical_name or entity.entity_id or "unknown entity")
            obs_text = ""
            observations, obs_omitted = _cap(entity.observations, max_entity_observations)
            if observations:
                obs_text = ": " + "; ".join(
                    _truncate(_one_line(obs.text), 140) for obs in observations if obs.text
                )
                if obs_omitted:
                    obs_text += f"; … {obs_omitted} more"
            lines.append(f"- {name}{obs_text}")
        if omitted_entities:
            lines.append(f"- … {omitted_entities} more entit(y/ies) omitted.")

    lines.append("Verification: no authority check performed.")
    return "\n".join(lines).strip()


def _format_full(
    packet: RecallPacket,
    *,
    max_observations: int,
    max_entities: int,
    max_entity_observations: int,
    max_evidence: int,
    show_metadata: bool,
) -> str:
    lines: list[str] = [
        "## Memory Recall Packet",
        "",
        "**Status:** Candidate context from memory retrieval. Verify against source evidence before acting on high-impact facts.",
        f"**Query:** `{_code(packet.query)}`",
    ]

    if packet.observations:
        lines.extend(["", "### Top observations"])
        shown, omitted = _cap(packet.observations, max_observations)
        for index, observation in enumerate(shown, 1):
            lines.append(f"{index}. {_truncate(_one_line(observation.text), 700)}")
            lines.extend(_observation_detail_lines(observation, show_metadata=show_metadata))
        if omitted:
            lines.append(f"- … {omitted} more observation(s) omitted.")

    if packet.entities:
        lines.extend(["", "### Entities"])
        shown_entities, omitted_entities = _cap(packet.entities, max_entities)
        for entity in shown_entities:
            name = _one_line(entity.canonical_name or "unknown entity")
            if entity.entity_id:
                lines.append(f"- **{name}** (`{_code(entity.entity_id)}`)")
            else:
                lines.append(f"- **{name}**")
            observations, obs_omitted = _cap(entity.observations, max_entity_observations)
            for observation in observations:
                suffix = f" (`{_code(observation.mentioned_at)}`)" if observation.mentioned_at else ""
                lines.append(f"  - {_truncate(_one_line(observation.text), 280)}{suffix}")
            if obs_omitted:
                lines.append(f"  - … {obs_omitted} more observation(s) omitted.")
        if omitted_entities:
            lines.append(f"- … {omitted_entities} more entit(y/ies) omitted.")

    if packet.source_facts or packet.chunks:
        lines.extend(["", "### Evidence handles"])
        source_facts, source_omitted = _cap(packet.source_facts, max_evidence)
        for fact in source_facts:
            lines.append(f"- source_fact: {_evidence_text(fact)}")
        if source_omitted:
            lines.append(f"- … {source_omitted} more source_fact(s) omitted.")

        chunks, chunk_omitted = _cap(packet.chunks, max_evidence)
        for chunk in chunks:
            detail_parts = [f"chunk: `{_code(chunk.id)}`"]
            if chunk.chunk_index is not None:
                detail_parts.append(f"index: `{chunk.chunk_index}`")
            if chunk.truncated is not None:
                detail_parts.append(f"truncated: `{str(chunk.truncated).lower()}`")
            detail = "; ".join(detail_parts)
            text = _truncate(_one_line(chunk.text), 240)
            lines.append(f"- {detail}" + (f" — {text}" if text else ""))
        if chunk_omitted:
            lines.append(f"- … {chunk_omitted} more chunk(s) omitted.")

    lines.extend(["", "### Verification notes"])
    lines.append("- No authority verification performed in this recall packet.")
    if any(_missing_source_handle(observation) for observation in packet.observations):
        lines.append("- Missing source handle on one or more observations; treat those as lower-confidence leads.")
    elif packet.observations:
        lines.append("- Listed observations include source handles; still verify high-impact claims against authority sources.")

    return "\n".join(lines).strip()


def _observation_detail_lines(observation: RecallObservation, *, show_metadata: bool) -> list[str]:
    lines: list[str] = []

    detail_map: list[tuple[str, Any]] = [
        ("type", observation.type),
        ("entities", observation.entities),
        ("context", observation.context),
        ("document_id", observation.document_id),
        ("chunk_id", observation.chunk_id),
        ("source_fact_ids", observation.source_fact_ids),
        ("occurred_start", observation.occurred_start),
        ("occurred_end", observation.occurred_end),
        ("mentioned_at", observation.mentioned_at),
        ("tags", observation.tags),
    ]
    for key, value in detail_map:
        rendered = _render_value(value)
        if rendered:
            lines.append(f"   - {key}: {rendered}")

    metadata_lines = _metadata_lines(observation.metadata, show_metadata=show_metadata)
    lines.extend(f"   - {line}" for line in metadata_lines)

    if _missing_source_handle(observation):
        lines.append("   - warning: Missing source handle.")
    return lines


def _metadata_lines(metadata: dict[str, Any], *, show_metadata: bool) -> list[str]:
    if not metadata:
        return []

    lines: list[str] = []
    unknown_keys: list[str] = []
    for key in sorted(metadata):
        value = metadata[key]
        if key in _METADATA_ALLOWLIST or show_metadata:
            rendered = _render_value(value)
            if rendered:
                lines.append(f"{key}: {rendered}")
        else:
            unknown_keys.append(str(key))
    if unknown_keys and not show_metadata:
        lines.append("metadata_keys: " + _render_sequence(unknown_keys))
    return lines


def _compact_observation_handles(observation: RecallObservation) -> str:
    handles: list[str] = []
    if observation.document_id:
        handles.append(f"doc: {_one_line(observation.document_id)}")
    if observation.chunk_id:
        handles.append(f"chunk: {_one_line(observation.chunk_id)}")
    if observation.source_fact_ids:
        handles.append(f"facts: {', '.join(_one_line(x) for x in observation.source_fact_ids[:3])}")
    if observation.entities:
        handles.append(f"entities: {', '.join(_one_line(x) for x in observation.entities[:4])}")
    return "; ".join(handles)


def _missing_source_handle(observation: RecallObservation) -> bool:
    return not (observation.document_id or observation.chunk_id or observation.source_fact_ids)


def _evidence_text(value: Any) -> str:
    if isinstance(value, dict):
        fact_id = value.get("id") or value.get("fact_id") or value.get("source_fact_id")
        text = value.get("text") or value.get("content") or value.get("summary") or ""
        if fact_id:
            if text:
                return f"`{_code(fact_id)}` — {_truncate(_one_line(text), 280)}"
            return f"`{_code(fact_id)}`"
    return _truncate(_one_line(value), 320)


def _render_value(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, (list, tuple, set)):
        return _render_sequence(value)
    return f"`{_code(value)}`"


def _render_sequence(value: Iterable[Any]) -> str:
    items = [_one_line(item) for item in value if item is not None and str(item).strip()]
    if not items:
        return ""
    return ", ".join(f"`{_code(item)}`" for item in items)


def _inline(value: Any) -> str:
    return _one_line(value)


def _code(value: Any) -> str:
    return _one_line(value).replace("`", "'")


def _one_line(value: Any) -> str:
    text = "" if value is None else str(value)
    text = "".join(ch if (ch >= " " or ch in "\t\n\r") else " " for ch in text)
    return " ".join(text.split())


def _truncate(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _cap(items: Sequence[Any], limit: int) -> tuple[list[Any], int]:
    shown = list(items[:limit])
    omitted = max(0, len(items) - len(shown))
    return shown, omitted


def _positive_or_default(value: int, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
