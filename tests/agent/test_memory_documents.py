from agent.memory_documents import build_memory_document


def test_chunking_is_header_aware_and_stable_ids():
    text = """# Overview
Intro paragraph about the document.

## Details
This is the first details paragraph.

This is the second details paragraph.

# Appendix
Final note.
"""
    doc = build_memory_document(
        text=text,
        source_kind="note",
        source_id="123",
        source_path="notes/demo.md",
        memory_type="reference",
        scope="workspace",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        tags=["demo", "docs"],
    )

    first = doc.chunk(max_chars=90, min_chars=20)
    second = doc.chunk(max_chars=90, min_chars=20)

    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]
    assert first[0].header_path == ("Overview",)
    assert any(chunk.header_path == ("Overview", "Details") for chunk in first)
    assert first[-1].header_path == ("Appendix",)


def test_chunk_metadata_contains_required_fields():
    doc = build_memory_document(
        text="Short body",
        source_kind="file",
        source_id="abc",
        source_path="docs/a.txt",
        memory_type="summary",
        scope="project",
        created_at="2026-02-01T00:00:00Z",
        updated_at="2026-02-02T00:00:00Z",
        freshness_hint="recent",
        confidence=0.75,
        tags=["tag1"],
        canonical=False,
    )

    chunk = doc.chunk()[0]

    assert chunk.memory_type == "summary"
    assert chunk.scope == "project"
    assert chunk.source_kind == "file"
    assert chunk.source_id == "abc"
    assert chunk.source_path == "docs/a.txt"
    assert chunk.created_at == "2026-02-01T00:00:00Z"
    assert chunk.updated_at == "2026-02-02T00:00:00Z"
    assert chunk.freshness_hint == "recent"
    assert chunk.confidence == 0.75
    assert chunk.tags == ("tag1",)
    assert chunk.canonical is False

    metadata = chunk.metadata()
    for field in (
        "memory_type",
        "scope",
        "source_kind",
        "source_id",
        "source_path",
        "created_at",
        "updated_at",
        "freshness_hint",
        "confidence",
        "tags",
        "canonical",
    ):
        assert field in metadata


def test_chunking_respects_max_chars_even_when_buffer_is_small():
    paragraph_a = "A" * 300
    paragraph_b = "B" * 300
    doc = build_memory_document(
        text=f"# Section\n{paragraph_a}\n\n{paragraph_b}",
        source_kind="note",
        source_id="small-buffer",
        source_path="notes/demo.md",
        memory_type="reference",
        scope="workspace",
        created_at="2026-03-01T00:00:00Z",
        updated_at="2026-03-01T00:00:00Z",
    )

    chunks = doc.chunk(max_chars=500, min_chars=400)

    assert len(chunks) == 2
    assert all(len(chunk.text) <= 500 for chunk in chunks)


def test_header_only_documents_keep_header_path():
    doc = build_memory_document(
        text="# Title",
        source_kind="note",
        source_id="header-only",
        source_path="notes/title.md",
        memory_type="reference",
        scope="workspace",
        created_at="2026-03-01T00:00:00Z",
        updated_at="2026-03-01T00:00:00Z",
    )

    chunks = doc.chunk()

    assert len(chunks) == 1
    assert chunks[0].header_path == ("Title",)
    assert chunks[0].text == "Title"
