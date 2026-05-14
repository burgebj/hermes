"""Tests for DAM message encoder."""
import pytest
import numpy as np

from plugins.context_engine.lcm.dam.encoder import MessageEncoder


class TestEncode:
    def test_output_shape(self):
        enc = MessageEncoder(nv=512)
        v = enc.encode({"role": "user", "content": "hello world"})
        assert v.shape == (512,)

    def test_unit_norm(self):
        enc = MessageEncoder(nv=512)
        v = enc.encode({"role": "user", "content": "hello world"})
        assert abs(np.linalg.norm(v) - 1.0) < 1e-6

    def test_deterministic(self):
        enc = MessageEncoder(nv=512)
        v1 = enc.encode({"role": "user", "content": "test message"})
        v2 = enc.encode({"role": "user", "content": "test message"})
        assert np.allclose(v1, v2)

    def test_similar_content_similar_vectors(self):
        enc = MessageEncoder(nv=2048)
        v1 = enc.encode({"role": "user", "content": "Python async error handling"})
        v2 = enc.encode({"role": "user", "content": "Python async exception handling"})
        v3 = enc.encode({"role": "user", "content": "Machine learning neural networks"})
        sim_12 = float(np.dot(v1, v2))
        sim_13 = float(np.dot(v1, v3))
        assert sim_12 > sim_13

    def test_empty_content(self):
        enc = MessageEncoder(nv=512)
        v = enc.encode({"role": "user", "content": ""})
        assert v.shape == (512,)

    def test_role_affects_encoding(self):
        enc = MessageEncoder(nv=512, role_weight=0.5)
        v_user = enc.encode({"role": "user", "content": "hello"})
        v_asst = enc.encode({"role": "assistant", "content": "hello"})
        assert not np.allclose(v_user, v_asst)


class TestEncodeText:
    def test_query_encoding(self):
        enc = MessageEncoder(nv=512)
        v = enc.encode_text("Python error handling")
        assert v.shape == (512,)
        assert abs(np.linalg.norm(v) - 1.0) < 1e-6

    def test_long_text(self):
        enc = MessageEncoder(nv=512)
        v = enc.encode_text("x " * 10000)
        assert v.shape == (512,)
        assert abs(np.linalg.norm(v) - 1.0) < 1e-6