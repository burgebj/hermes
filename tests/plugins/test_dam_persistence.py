"""Tests for DAM state persistence."""
import pytest
import numpy as np

from plugins.context_engine.lcm.dam.network import DenseAssociativeMemory
from plugins.context_engine.lcm.dam.persistence import save_state, load_state


class MockRetriever:
    """Minimal retriever-like object for persistence tests."""
    def __init__(self, nv=100, nh=10):
        self.network = DenseAssociativeMemory(nv=nv, nh=nh)
        self._pattern_cache = {}
        self._last_indexed_id = -1


class TestSaveLoad:
    def test_save_creates_file(self, tmp_path):
        retriever = MockRetriever()
        path = tmp_path / "dam_state.npz"
        assert save_state(retriever, path) is True
        assert path.exists()

    def test_roundtrip(self, tmp_path):
        retriever = MockRetriever(nv=100, nh=10)
        # Train the network a bit
        patterns = np.random.randn(3, 100).astype(np.float32)
        for i in range(3):
            patterns[i] /= np.linalg.norm(patterns[i])
        retriever.network.learn(patterns, epochs=5)
        retriever._last_indexed_id = 42
        # Add some cached patterns
        retriever._pattern_cache[0] = np.random.randn(100).astype(np.float32)
        retriever._pattern_cache[5] = np.random.randn(100).astype(np.float32)

        path = tmp_path / "dam_state.npz"
        save_state(retriever, path)
        loaded = load_state(path)

        assert loaded is not None
        assert np.allclose(loaded["xi"], retriever.network.xi)
        assert loaded["nv"] == 100
        assert loaded["nh"] == 10
        assert loaded["last_indexed_id"] == 42
        assert loaded["cache_ids"] is not None
        assert len(loaded["cache_ids"]) == 2

    def test_load_nonexistent(self, tmp_path):
        path = tmp_path / "nonexistent.npz"
        assert load_state(path) is None

    def test_empty_cache_roundtrip(self, tmp_path):
        retriever = MockRetriever()
        path = tmp_path / "dam_state.npz"
        save_state(retriever, path)
        loaded = load_state(path)
        assert loaded is not None
        assert loaded["last_indexed_id"] == -1