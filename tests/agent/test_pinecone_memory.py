import logging

import pytest

from agent.pinecone_memory import PineconeMemoryClient


class FakeIndex:
    def __init__(self):
        self.upserts = []
        self.queries = []
        self.deletes = []
        self.matches = []
        self.raise_upsert = None

    def upsert(self, **kwargs):
        if self.raise_upsert:
            raise self.raise_upsert
        self.upserts.append(kwargs)

    def query(self, **kwargs):
        self.queries.append(kwargs)
        return {"matches": self.matches}

    def delete(self, **kwargs):
        self.deletes.append(kwargs)


class FakePineconeModule:
    def __init__(self, index):
        self.index = index
        self.calls = []

    def Pinecone(self, api_key):
        self.calls.append(api_key)
        index = self.index

        class Client:
            def Index(self, name=None, host=None):
                if host is not None:
                    return index
                return index

        return Client()


def test_is_configured_requires_api_key_and_index():
    client = PineconeMemoryClient(config={"api_key": "k", "index_name": "idx", "fail_open": False})
    assert client.is_configured() is True
    assert PineconeMemoryClient(config={"api_key": "k", "fail_open": False}).is_configured() is False


def test_upsert_normalizes_records_and_query_normalizes_matches():
    index = FakeIndex()
    module = FakePineconeModule(index)
    client = PineconeMemoryClient(
        config={"api_key": "k", "index_name": "idx", "fail_open": False},
        pinecone_module=module,
    )

    written = client.upsert_records(
        [
            {"id": 42, "values": (0.1, 0.2), "metadata": {"source_id": "doc-1"}},
        ],
        namespace="memories",
    )
    index.matches = [{"id": 99, "values": (0.3, 0.4), "metadata": {"source_kind": "file"}, "score": 0.91}]
    results = client.query(vector=[1.0, 2.0], top_k=3, namespace="memories")

    assert written == 1
    assert index.upserts == [{"vectors": [{"id": "42", "values": [0.1, 0.2], "metadata": {"source_id": "doc-1"}}], "namespace": "memories"}]
    assert results == [{"id": "99", "values": [0.3, 0.4], "metadata": {"source_kind": "file"}, "score": 0.91}]


def test_delete_by_source_uses_metadata_filter():
    index = FakeIndex()
    module = FakePineconeModule(index)
    client = PineconeMemoryClient(
        config={"api_key": "***", "index_name": "idx", "fail_open": False},
        pinecone_module=module,
    )

    ok = client.delete_by_source(source_kind="file", source_id="abc", source_path="docs/a.md", namespace="memories")

    assert ok is True
    assert index.deletes == [{"filter": {"source_kind": {"$eq": "file"}, "source_id": {"$eq": "abc"}, "source_path": {"$eq": "docs/a.md"}}, "namespace": "memories"}]


def test_configured_namespace_is_used_by_default():
    index = FakeIndex()
    client = PineconeMemoryClient(
        config={"api_key": "***", "index_name": "idx", "namespace": "configured", "fail_open": False},
        pinecone_module=FakePineconeModule(index),
    )

    client.upsert_records([{"id": "1", "values": [0.1], "metadata": {}}])
    client.query(vector=[0.1])
    client.delete_by_source(source_kind="file", source_id="abc")

    assert index.upserts[0]["namespace"] == "configured"
    assert index.queries[0]["namespace"] == "configured"
    assert index.deletes[0]["namespace"] == "configured"


def test_fail_open_skips_missing_configuration_with_warning(caplog):
    client = PineconeMemoryClient(config={"fail_open": True})

    with caplog.at_level(logging.WARNING, logger="agent.pinecone_memory"):
        upserted = client.upsert_records([{"id": "1", "values": [0.1], "metadata": {}}])
        queried = client.query(vector=[0.1])

    assert upserted == 0
    assert queried == []
    assert "fail-open enabled" in caplog.text
    assert "missing Pinecone configuration" in caplog.text


def test_fail_open_swallows_sdk_exceptions(caplog):
    index = FakeIndex()
    index.raise_upsert = RuntimeError("sdk boom")
    client = PineconeMemoryClient(
        config={"api_key": "k", "index_name": "idx", "fail_open": True},
        pinecone_module=FakePineconeModule(index),
    )

    with caplog.at_level(logging.WARNING, logger="agent.pinecone_memory"):
        result = client.upsert_records([{"id": "1", "values": [0.2], "metadata": {}}])

    assert result == 0
    assert "sdk boom" in caplog.text


def test_fail_closed_raises_on_sdk_error():
    index = FakeIndex()
    index.raise_upsert = RuntimeError("sdk boom")
    client = PineconeMemoryClient(
        config={"api_key": "***", "index_name": "idx", "fail_open": False},
        pinecone_module=FakePineconeModule(index),
    )

    with pytest.raises(RuntimeError, match="sdk boom"):
        client.upsert_records([{"id": "1", "values": [0.2], "metadata": {}}])


def test_delete_missing_configuration_respects_fail_open_and_fail_closed(caplog):
    fail_open_client = PineconeMemoryClient(config={"fail_open": True})
    with caplog.at_level(logging.WARNING, logger="agent.pinecone_memory"):
        assert fail_open_client.delete_by_source(source_kind="file", source_id="abc") is False
    assert "missing Pinecone configuration" in caplog.text

    fail_closed_client = PineconeMemoryClient(config={"fail_open": False})
    with pytest.raises(RuntimeError, match="missing Pinecone configuration"):
        fail_closed_client.delete_by_source(source_kind="file", source_id="abc")
