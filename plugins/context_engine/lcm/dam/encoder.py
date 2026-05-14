"""Message encoder: text -> fixed-size vector via character trigram hashing."""
import numpy as np
from typing import Any
import hashlib


class MessageEncoder:
    """Encodes messages as Nv-dimensional unit vectors.

    Uses character trigram hashing for zero-dependency text vectorization.
    Similar texts produce similar vectors (shared trigrams -> shared indices).
    """

    def __init__(self, nv: int = 2048, role_weight: float = 0.3):
        self.nv = nv
        self.role_weight = role_weight

    def _trigram_hash(self, text: str) -> np.ndarray:
        """Hash character trigrams into a Nv-dimensional count vector."""
        v = np.zeros(self.nv, dtype=np.float32)
        text = text.lower()
        if len(text) < 3:
            # For very short text, use character-level
            for ch in text:
                idx = int(hashlib.md5(ch.encode()).hexdigest(), 16) % self.nv
                v[idx] += 1.0
            return v

        for i in range(len(text) - 2):
            trigram = text[i:i + 3]
            # Use md5 for deterministic cross-platform hashing
            idx = int(hashlib.md5(trigram.encode()).hexdigest(), 16) % self.nv
            v[idx] += 1.0
        return v

    def _role_vector(self, role: str) -> np.ndarray:
        """Encode the message role as a sparse vector."""
        v = np.zeros(self.nv, dtype=np.float32)
        role_hash = hashlib.md5(f"role:{role}".encode()).hexdigest()
        # Spread across 4 indices
        for i in range(4):
            chunk = role_hash[i * 8:(i + 1) * 8]
            idx = int(chunk, 16) % self.nv
            v[idx] += 1.0
        return v

    def encode(self, message: dict[str, Any]) -> np.ndarray:
        """Encode a message dict to a unit vector."""
        content = str(message.get("content", "") or "")
        role = str(message.get("role", "unknown"))

        v = self._trigram_hash(content)
        if self.role_weight > 0:
            v += self.role_weight * self._role_vector(role)

        norm = np.linalg.norm(v)
        if norm > 1e-8:
            v /= norm
        return v

    def encode_text(self, text: str) -> np.ndarray:
        """Encode a raw text string (for queries)."""
        v = self._trigram_hash(text)
        norm = np.linalg.norm(v)
        if norm > 1e-8:
            v /= norm
        return v
