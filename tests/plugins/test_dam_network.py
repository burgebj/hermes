"""Tests for Dense Associative Memory network."""
import pytest
import numpy as np

from plugins.context_engine.lcm.dam.network import DenseAssociativeMemory


class TestInitialization:
    def test_weight_matrix_shape(self):
        net = DenseAssociativeMemory(nv=100, nh=10)
        assert net.xi.shape == (100, 10)

    def test_xavier_scale(self):
        net = DenseAssociativeMemory(nv=1000, nh=50)
        expected_std = np.sqrt(2.0 / (1000 + 50))
        assert abs(net.xi.std() - expected_std) < 0.05


class TestHiddenActivations:
    def test_shape_and_binary(self):
        net = DenseAssociativeMemory(nv=100, nh=10)
        v = np.random.randn(100).astype(np.float32)
        v /= np.linalg.norm(v)
        s = net.get_hidden_activations(v)
        assert s.shape == (10,)
        assert set(np.unique(s)).issubset({0.0, 1.0})


class TestRecall:
    def test_convergence(self):
        net = DenseAssociativeMemory(nv=100, nh=10)
        v = np.random.randn(100).astype(np.float32)
        v /= np.linalg.norm(v)
        v_out, s = net.recall(v)
        assert v_out.shape == (100,)

    def test_recall_is_deterministic(self):
        net = DenseAssociativeMemory(nv=100, nh=10)
        v = np.random.randn(100).astype(np.float32)
        v /= np.linalg.norm(v)
        v1, _ = net.recall(v)
        v2, _ = net.recall(v)
        assert np.allclose(v1, v2)


class TestLearning:
    def test_learn_reduces_error(self):
        net = DenseAssociativeMemory(nv=100, nh=10, lr=0.01)
        patterns = np.random.randn(5, 100).astype(np.float32)
        for i in range(5):
            patterns[i] /= np.linalg.norm(patterns[i])
        loss1 = net.learn(patterns, epochs=1)
        loss2 = net.learn(patterns, epochs=10)
        assert loss2 < loss1

    def test_pattern_completion(self):
        """Stored patterns recalled from noisy cues."""
        net = DenseAssociativeMemory(nv=200, nh=20, lr=0.01)
        patterns = []
        for i in range(3):
            v = np.zeros(200, dtype=np.float32)
            v[i*60:(i+1)*60] = np.random.randn(60).astype(np.float32)
            v /= np.linalg.norm(v)
            patterns.append(v)
        net.learn(np.stack(patterns), epochs=50)

        # Noisy cue
        noisy = patterns[0] + 0.3 * np.random.randn(200).astype(np.float32)
        noisy /= np.linalg.norm(noisy)
        recalled, _ = net.recall(noisy)

        sims = [float(np.dot(recalled, p)) for p in patterns]
        assert np.argmax(sims) == 0  # Most similar to pattern 0

    def test_capacity_scales_with_nh(self):
        np.random.seed(42)  # Fix seed for reproducibility
        nv, n_patterns = 200, 20
        patterns = np.random.randn(n_patterns, nv).astype(np.float32)
        for i in range(n_patterns):
            patterns[i] /= np.linalg.norm(patterns[i])

        net_small = DenseAssociativeMemory(nv=nv, nh=8, lr=0.01)
        net_large = DenseAssociativeMemory(nv=nv, nh=32, lr=0.01)
        loss_small = net_small.learn(patterns, epochs=30)
        loss_large = net_large.learn(patterns, epochs=30)
        assert loss_large <= loss_small


class TestSerialization:
    def test_roundtrip(self):
        net = DenseAssociativeMemory(nv=100, nh=10)
        patterns = np.random.randn(3, 100).astype(np.float32)
        for i in range(3):
            patterns[i] /= np.linalg.norm(patterns[i])
        net.learn(patterns, epochs=5)

        state = net.get_state()
        net2 = DenseAssociativeMemory.from_state(state)
        assert np.allclose(net.xi, net2.xi)
        assert net.nv == net2.nv
        assert net.nh == net2.nh