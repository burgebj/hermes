"""Tests for provider-neutral graph-shaped memory recall packet formatting."""

from agent.memory_recall_packet import (
    EntityObservation,
    RecallEntity,
    RecallEvidenceChunk,
    RecallObservation,
    RecallPacket,
    format_recall_packet,
)


def test_empty_packet_returns_no_relevant_memories_message():
    packet = RecallPacket(query="nothing useful")

    assert format_recall_packet(packet) == "No relevant memories found."


def test_format_recall_packet_includes_provenance_handles_and_verification_notice():
    packet = RecallPacket(
        query="memory architecture",
        observations=[
            RecallObservation(
                text="Atlas is authoritative; Hindsight is candidate recall.",
                type="world",
                document_id="session-1-1",
                source_fact_ids=["fact-1", "fact-2"],
                entities=["Atlas", "Hindsight"],
                tags=["hermes", "memory"],
                mentioned_at="2026-06-01T10:00:00Z",
                metadata={
                    "source": "hermes",
                    "session_id": "session-1",
                    "turn_index": "3",
                    "secret_token": "do-not-dump",
                },
            )
        ],
        entities=[
            RecallEntity(
                entity_id="ent-atlas",
                canonical_name="Atlas",
                observations=[
                    EntityObservation(
                        text="source authority layer",
                        mentioned_at="2026-06-01T10:00:00Z",
                    )
                ],
            )
        ],
        chunks=[
            RecallEvidenceChunk(
                id="chunk-1",
                text="source chunk text",
                chunk_index=0,
                truncated=False,
            )
        ],
        source_facts=["fact-1 — Atlas/source files are authority."],
    )

    text = format_recall_packet(packet, compact=False)

    assert "Memory Recall Packet" in text
    assert "Candidate context" in text
    assert "memory architecture" in text
    assert "Atlas is authoritative" in text
    assert "type: `world`" in text
    assert "document_id: `session-1-1`" in text
    assert "source_fact_ids: `fact-1`, `fact-2`" in text
    assert "entities: `Atlas`, `Hindsight`" in text
    assert "tags: `hermes`, `memory`" in text
    assert "mentioned_at: `2026-06-01T10:00:00Z`" in text
    assert "source: `hermes`" in text
    assert "session_id: `session-1`" in text
    assert "metadata_keys: `secret_token`" in text
    assert "do-not-dump" not in text
    assert "ent-atlas" in text
    assert "source authority layer" in text
    assert "chunk-1" in text
    assert "No authority verification performed" in text


def test_compact_packet_is_bounded_and_keeps_key_handles():
    packet = RecallPacket(
        query="memory graph",
        observations=[
            RecallObservation(
                text="Atlas is authority; Hindsight is candidate recall.",
                document_id="session-1-1",
                source_fact_ids=["fact-1"],
                entities=["Atlas", "Hindsight"],
            )
        ],
        entities=[
            RecallEntity(
                entity_id="ent-atlas",
                canonical_name="Atlas",
                observations=[EntityObservation(text="authority layer")],
            )
        ],
        chunks=[RecallEvidenceChunk(id="chunk-1", text="verbose source chunk")],
        source_facts=["fact-1 — Atlas/source files are authority."],
    )

    text = format_recall_packet(packet, compact=True)

    assert text.startswith("# Memory Recall Packet")
    assert "Status: candidate context" in text
    assert "Atlas is authority" in text
    assert "doc: session-1-1" in text
    assert "facts: fact-1" in text
    assert "entities: Atlas, Hindsight" in text
    assert "authority layer" in text
    assert "verbose source chunk" not in text
    assert "Verification: no authority check performed" in text


def test_formatter_caps_evidence_lists():
    packet = RecallPacket(
        query="evidence caps",
        observations=[RecallObservation(text="one", document_id="doc-1")],
        source_facts=["fact-1", "fact-2", "fact-3"],
        chunks=[
            RecallEvidenceChunk(id="chunk-1", text="chunk one"),
            RecallEvidenceChunk(id="chunk-2", text="chunk two"),
            RecallEvidenceChunk(id="chunk-3", text="chunk three"),
        ],
    )

    text = format_recall_packet(packet, compact=False, max_evidence=2)

    assert "fact-1" in text
    assert "fact-2" in text
    assert "fact-3" not in text
    assert "chunk-1" in text
    assert "chunk-2" in text
    assert "chunk-3" not in text
    assert "1 more" in text


def test_missing_source_handles_are_flagged_as_lower_confidence():
    packet = RecallPacket(
        query="missing handles",
        observations=[RecallObservation(text="Unsourced lead")],
    )

    text = format_recall_packet(packet, compact=False)

    assert "Unsourced lead" in text
    assert "Missing source handle" in text
